package smartdns

import (
	"crypto/tls"
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
