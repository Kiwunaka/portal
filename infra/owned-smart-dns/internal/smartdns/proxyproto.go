package smartdns

import (
	"bytes"
	"encoding/binary"
	"errors"
	"io"
	"net"
	"time"
)

var proxyV2Signature = [12]byte{0x0d, 0x0a, 0x0d, 0x0a, 0x00, 0x0d, 0x0a, 0x51, 0x55, 0x49, 0x54, 0x0a}

const (
	proxyV2HeaderBytes  = 16
	proxyV2TCP4Payload  = 12
	proxyV2TCP6Payload  = 36
	proxyV2CommandProxy = 0x21
	proxyV2FamilyTCP4   = 0x11
	proxyV2FamilyTCP6   = 0x21
)

func acceptProxyProtocolV2(connection net.Conn, timeout time.Duration) (net.Conn, error) {
	if err := connection.SetReadDeadline(time.Now().Add(timeout)); err != nil {
		return nil, err
	}
	defer connection.SetReadDeadline(time.Time{})

	header := make([]byte, proxyV2HeaderBytes)
	if _, err := io.ReadFull(connection, header); err != nil {
		return nil, errors.New("read PROXY protocol v2 header")
	}
	if !bytes.Equal(header[:len(proxyV2Signature)], proxyV2Signature[:]) {
		return nil, errors.New("invalid PROXY protocol v2 signature")
	}
	if header[12] != proxyV2CommandProxy {
		return nil, errors.New("PROXY protocol v2 requires the PROXY command")
	}

	payloadBytes := int(binary.BigEndian.Uint16(header[14:16]))
	expectedBytes := 0
	sourceAddressBytes := 0
	sourcePortOffset := 0
	switch header[13] {
	case proxyV2FamilyTCP4:
		expectedBytes = proxyV2TCP4Payload
		sourceAddressBytes = net.IPv4len
		sourcePortOffset = 8
	case proxyV2FamilyTCP6:
		expectedBytes = proxyV2TCP6Payload
		sourceAddressBytes = net.IPv6len
		sourcePortOffset = 32
	default:
		return nil, errors.New("PROXY protocol v2 requires a TCP IPv4 or TCP IPv6 address family")
	}
	if payloadBytes != expectedBytes {
		return nil, errors.New("PROXY protocol v2 address payload length is invalid")
	}

	payload := make([]byte, payloadBytes)
	if _, err := io.ReadFull(connection, payload); err != nil {
		return nil, errors.New("read PROXY protocol v2 address payload")
	}
	sourceIP := net.IP(append([]byte(nil), payload[:sourceAddressBytes]...))
	if sourceIP.IsUnspecified() || sourceIP.IsMulticast() {
		return nil, errors.New("PROXY protocol v2 source address is invalid")
	}
	sourcePort := int(binary.BigEndian.Uint16(payload[sourcePortOffset : sourcePortOffset+2]))
	return &proxyV2Conn{
		Conn: connection,
		remote: &net.TCPAddr{
			IP:   sourceIP,
			Port: sourcePort,
		},
	}, nil
}

type proxyV2Conn struct {
	net.Conn
	remote net.Addr
}

func (c *proxyV2Conn) RemoteAddr() net.Addr { return c.remote }
