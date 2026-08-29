package smartdns

import (
	"encoding/binary"
	"io"
	"net"
	"testing"
	"time"
)

func TestAcceptProxyProtocolV2RestoresIPv4SourceAndLeavesTLSBytes(t *testing.T) {
	server, client := net.Pipe()
	defer server.Close()
	defer client.Close()

	header := proxyV2Header(t, proxyV2FamilyTCP4, net.ParseIP("198.51.100.10"), net.ParseIP("203.0.113.20"), 43123, 443)
	go func() {
		_, _ = client.Write(append(header, []byte("tls-client-hello")...))
	}()

	connection, err := acceptProxyProtocolV2(server, time.Second)
	if err != nil {
		t.Fatal(err)
	}
	if got := connection.RemoteAddr().String(); got != "198.51.100.10:43123" {
		t.Fatalf("unexpected restored source: %s", got)
	}
	remaining := make([]byte, len("tls-client-hello"))
	if _, err := io.ReadFull(connection, remaining); err != nil {
		t.Fatal(err)
	}
	if string(remaining) != "tls-client-hello" {
		t.Fatalf("unexpected remaining payload: %q", remaining)
	}
}

func TestAcceptProxyProtocolV2RestoresIPv6Source(t *testing.T) {
	server, client := net.Pipe()
	defer server.Close()
	defer client.Close()

	header := proxyV2Header(t, proxyV2FamilyTCP6, net.ParseIP("2001:db8::10"), net.ParseIP("2001:db8::20"), 43123, 443)
	go func() { _, _ = client.Write(header) }()

	connection, err := acceptProxyProtocolV2(server, time.Second)
	if err != nil {
		t.Fatal(err)
	}
	if got := connection.RemoteAddr().String(); got != "[2001:db8::10]:43123" {
		t.Fatalf("unexpected restored source: %s", got)
	}
}

func TestAcceptProxyProtocolV2RejectsMissingHeader(t *testing.T) {
	server, client := net.Pipe()
	defer server.Close()
	defer client.Close()

	go func() { _, _ = client.Write(make([]byte, proxyV2HeaderBytes)) }()
	if _, err := acceptProxyProtocolV2(server, time.Second); err == nil {
		t.Fatal("missing PROXY protocol v2 signature must fail closed")
	}
}

func TestAcceptProxyProtocolV2RejectsTLVs(t *testing.T) {
	server, client := net.Pipe()
	defer server.Close()
	defer client.Close()

	header := proxyV2Header(t, proxyV2FamilyTCP4, net.ParseIP("198.51.100.10"), net.ParseIP("203.0.113.20"), 43123, 443)
	binary.BigEndian.PutUint16(header[14:16], proxyV2TCP4Payload+1)
	go func() { _, _ = client.Write(append(header, 0)) }()
	if _, err := acceptProxyProtocolV2(server, time.Second); err == nil {
		t.Fatal("unexpected PROXY protocol v2 TLVs must fail closed")
	}
}

func proxyV2Header(t *testing.T, family byte, source, destination net.IP, sourcePort, destinationPort uint16) []byte {
	t.Helper()
	header := make([]byte, proxyV2HeaderBytes)
	copy(header, proxyV2Signature[:])
	header[12] = proxyV2CommandProxy
	header[13] = family

	var payload []byte
	switch family {
	case proxyV2FamilyTCP4:
		payload = make([]byte, proxyV2TCP4Payload)
		copy(payload[0:4], source.To4())
		copy(payload[4:8], destination.To4())
		binary.BigEndian.PutUint16(payload[8:10], sourcePort)
		binary.BigEndian.PutUint16(payload[10:12], destinationPort)
	case proxyV2FamilyTCP6:
		payload = make([]byte, proxyV2TCP6Payload)
		copy(payload[0:16], source.To16())
		copy(payload[16:32], destination.To16())
		binary.BigEndian.PutUint16(payload[32:34], sourcePort)
		binary.BigEndian.PutUint16(payload[34:36], destinationPort)
	default:
		t.Fatalf("unsupported test family: %x", family)
	}
	binary.BigEndian.PutUint16(header[14:16], uint16(len(payload)))
	return append(header, payload...)
}
