package smartdns

import (
	"context"
	"crypto/tls"
	"errors"
	"fmt"
	"net"
	"net/netip"
	"strings"
	"sync/atomic"
	"time"

	"github.com/miekg/dns"
)

type originResolver interface {
	Resolve(context.Context, string) ([]netip.Addr, error)
}

type dotResolver struct {
	address      string
	blockedProxy netip.Addr
	client       *dns.Client
	next         atomic.Uint64
}

func newDoTResolver(config Config) *dotResolver {
	return &dotResolver{
		address:      config.UpstreamDoT.Address,
		blockedProxy: netip.MustParseAddr(config.ProxyIPv4),
		client: &dns.Client{
			Net:     "tcp-tls",
			Timeout: config.Limits.connectTimeout(),
			TLSConfig: &tls.Config{
				MinVersion: tls.VersionTLS12,
				ServerName: config.UpstreamDoT.ServerName,
			},
		},
	}
}

func (r *dotResolver) Resolve(ctx context.Context, name string) ([]netip.Addr, error) {
	current, err := normalizeDomain(name)
	if err != nil {
		return nil, err
	}
	seen := make(map[string]bool)
	for hop := 0; hop < 8; hop++ {
		if seen[current] {
			return nil, errors.New("origin DNS CNAME loop")
		}
		seen[current] = true
		message := new(dns.Msg)
		message.SetQuestion(dns.Fqdn(current), dns.TypeA)
		message.RecursionDesired = true
		response, _, err := r.client.ExchangeContext(ctx, message, r.address)
		if err != nil {
			return nil, fmt.Errorf("origin DNS request failed: %w", err)
		}
		if response == nil || response.Truncated || response.Rcode != dns.RcodeSuccess {
			return nil, errors.New("origin DNS response rejected")
		}
		var addresses []netip.Addr
		var canonical string
		for _, answer := range response.Answer {
			switch record := answer.(type) {
			case *dns.A:
				owner := strings.TrimSuffix(strings.ToLower(record.Hdr.Name), ".")
				if owner != current {
					continue
				}
				address, ok := netip.AddrFromSlice(record.A)
				if ok && isPublicAddress(address.Unmap()) && address.Unmap() != r.blockedProxy {
					addresses = append(addresses, address.Unmap())
				}
			case *dns.CNAME:
				owner := strings.TrimSuffix(strings.ToLower(record.Hdr.Name), ".")
				if owner == current {
					canonical, _ = normalizeDomain(record.Target)
				}
			}
		}
		if len(addresses) != 0 {
			start := int(r.next.Add(1)-1) % len(addresses)
			return append(addresses[start:], addresses[:start]...), nil
		}
		if canonical == "" {
			return nil, errors.New("origin DNS returned no public IPv4 address")
		}
		current = canonical
	}
	return nil, errors.New("origin DNS CNAME limit exceeded")
}

func dialOrigin(ctx context.Context, resolver originResolver, name string, timeout time.Duration) (net.Conn, error) {
	addresses, err := resolver.Resolve(ctx, name)
	if err != nil {
		return nil, err
	}
	dialer := net.Dialer{Timeout: timeout, KeepAlive: 30 * time.Second}
	var lastErr error
	for _, address := range addresses {
		if !isPublicAddress(address) {
			continue
		}
		connection, err := dialer.DialContext(ctx, "tcp", net.JoinHostPort(address.String(), "443"))
		if err == nil {
			return connection, nil
		}
		lastErr = err
	}
	if lastErr == nil {
		lastErr = errors.New("origin has no eligible address")
	}
	return nil, lastErr
}
