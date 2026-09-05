package smartdns

import (
	"crypto/ecdh"
	"crypto/rand"
	"crypto/tls"
	"encoding/binary"
	"net"
	"testing"
	"time"
)

func TestSniffClientHelloExtractsCanonicalSNIAndPreservesBytes(t *testing.T) {
	clientSide, serverSide := net.Pipe()
	done := make(chan error, 1)
	go func() {
		client := tls.Client(clientSide, &tls.Config{
			ServerName:         "API.OpenAI.com",
			InsecureSkipVerify: true, // No server handshake is completed in this parser test.
		})
		done <- client.Handshake()
	}()
	prefix, name, err := sniffClientHello(serverSide, 65535, time.Second)
	if err != nil {
		t.Fatal(err)
	}
	if name != "api.openai.com" || len(prefix) < 5 || prefix[0] != 22 {
		t.Fatalf("unexpected sniff result: name=%q bytes=%d", name, len(prefix))
	}
	_ = serverSide.Close()
	_ = clientSide.Close()
	<-done
}

func TestSniffClientHelloRejectsMissingSNI(t *testing.T) {
	clientSide, serverSide := net.Pipe()
	done := make(chan error, 1)
	go func() {
		client := tls.Client(clientSide, &tls.Config{InsecureSkipVerify: true})
		done <- client.Handshake()
	}()
	if _, _, err := sniffClientHello(serverSide, 65535, time.Second); err == nil {
		t.Fatal("ClientHello without SNI must be rejected")
	}
	_ = serverSide.Close()
	_ = clientSide.Close()
	<-done
}

func TestSniffClientHelloRejectsECHWithAllowedOuterSNI(t *testing.T) {
	// Produce a real ECH ClientHello locally; no application connection is made.
	publicName := "api.openai.com"
	key, err := ecdh.X25519().GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	contents := []byte{0}                                      // config_id
	contents = binary.BigEndian.AppendUint16(contents, 0x0020) // X25519
	publicKey := key.PublicKey().Bytes()
	contents = binary.BigEndian.AppendUint16(contents, uint16(len(publicKey)))
	contents = append(contents, publicKey...)
	contents = append(contents, 0, 4, 0, 1, 0, 1) // HKDF-SHA256, AES-128-GCM
	contents = append(contents, 0, byte(len(publicName)))
	contents = append(contents, publicName...)
	contents = append(contents, 0, 0) // no config extensions
	config := binary.BigEndian.AppendUint16(nil, 0xfe0d)
	config = binary.BigEndian.AppendUint16(config, uint16(len(contents)))
	config = append(config, contents...)
	configList := binary.BigEndian.AppendUint16(nil, uint16(len(config)))
	configList = append(configList, config...)

	clientSide, serverSide := net.Pipe()
	done := make(chan error, 1)
	go func() {
		client := tls.Client(clientSide, &tls.Config{
			ServerName:                     "hidden.example",
			MinVersion:                     tls.VersionTLS13,
			EncryptedClientHelloConfigList: configList,
		})
		done <- client.Handshake()
	}()
	defer func() {
		_ = serverSide.Close()
		_ = clientSide.Close()
		<-done
	}()
	_, name, err := sniffClientHello(serverSide, 65535, time.Second)
	if err == nil {
		t.Fatalf("ECH with allowed outer SNI must be rejected, accepted name %q", name)
	}
}
