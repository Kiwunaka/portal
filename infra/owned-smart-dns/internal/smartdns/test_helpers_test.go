package smartdns

import (
	"net/netip"
	"testing"
)

func mustAddress(t *testing.T, value string) netip.Addr {
	t.Helper()
	address, err := netip.ParseAddr(value)
	if err != nil {
		t.Fatal(err)
	}
	return address
}
