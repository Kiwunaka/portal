package smartdns

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/netip"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"
)

const policySchemaVersion = "pokrov-smart-dns-policy-v1"

type Config struct {
	Listen                string         `json:"listen"`
	AcceptProxyProtocolV2 bool           `json:"accept_proxy_protocol_v2"`
	DoHHostname           string         `json:"doh_hostname"`
	ProxyIPv4             string         `json:"proxy_ipv4"`
	PolicyPath            string         `json:"policy_path"`
	TLSCertificatePath    string         `json:"tls_certificate_path"`
	TLSPrivateKeyPath     string         `json:"tls_private_key_path"`
	UpstreamDoT           UpstreamConfig `json:"upstream_dot"`
	Limits                Limits         `json:"limits"`
}

type UpstreamConfig struct {
	Address    string `json:"address"`
	ServerName string `json:"server_name"`
}

type Limits struct {
	MaxConcurrentConnections int   `json:"max_concurrent_connections"`
	MaxConnectionsPerIP      int   `json:"max_connections_per_ip"`
	MaxDoHRequestsPerMinute  int   `json:"max_doh_requests_per_minute"`
	MaxTrackedSourceIPs      int   `json:"max_tracked_source_ips"`
	MaxDNSMessageBytes       int   `json:"max_dns_message_bytes"`
	MaxClientHelloBytes      int   `json:"max_client_hello_bytes"`
	HandshakeTimeoutSeconds  int   `json:"handshake_timeout_seconds"`
	ConnectTimeoutSeconds    int   `json:"connect_timeout_seconds"`
	IdleTimeoutSeconds       int   `json:"idle_timeout_seconds"`
	MaxConnectionSeconds     int   `json:"max_connection_seconds"`
	MaxBytesPerDirection     int64 `json:"max_bytes_per_direction"`
}

func (l Limits) handshakeTimeout() time.Duration {
	return time.Duration(l.HandshakeTimeoutSeconds) * time.Second
}

func (l Limits) connectTimeout() time.Duration {
	return time.Duration(l.ConnectTimeoutSeconds) * time.Second
}

func (l Limits) idleTimeout() time.Duration {
	return time.Duration(l.IdleTimeoutSeconds) * time.Second
}

func (l Limits) maxConnectionLifetime() time.Duration {
	return time.Duration(l.MaxConnectionSeconds) * time.Second
}

type Policy struct {
	SchemaVersion   string              `json:"schema_version"`
	State           string              `json:"state"`
	Groups          map[string][]string `json:"groups"`
	DNSAnswers      DNSAnswerPolicy     `json:"dns_answers"`
	Matching        string              `json:"matching"`
	ApplicationTLS  string              `json:"application_tls"`
	RecursiveDNS    bool                `json:"recursive_dns"`
	allowedSuffixes []string
	sha256          string
}

type DNSAnswerPolicy struct {
	A                string `json:"a"`
	AAAA             string `json:"aaaa"`
	HTTPS            string `json:"https"`
	SVCB             string `json:"svcb"`
	Other            string `json:"other"`
	OutsideAllowlist string `json:"outside_allowlist"`
	TTLSeconds       uint32 `json:"ttl_seconds"`
}

func (p *Policy) Allows(name string) bool {
	normalized, err := normalizeDomain(name)
	if err != nil {
		return false
	}
	for _, suffix := range p.allowedSuffixes {
		if normalized == suffix || strings.HasSuffix(normalized, "."+suffix) {
			return true
		}
	}
	return false
}

func (p *Policy) SHA256() string { return p.sha256 }

func (p *Policy) AllowedSuffixes() []string {
	return append([]string(nil), p.allowedSuffixes...)
}

func LoadRuntime(configPath string) (Config, *Policy, error) {
	config, err := loadConfig(configPath)
	if err != nil {
		return Config{}, nil, err
	}
	policy, err := loadPolicy(config.PolicyPath)
	if err != nil {
		return Config{}, nil, err
	}
	return config, policy, nil
}

func loadConfig(path string) (Config, error) {
	if !filepath.IsAbs(path) {
		return Config{}, errors.New("configuration path must be absolute")
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return Config{}, fmt.Errorf("read configuration: %w", err)
	}
	var config Config
	if err := decodeStrict(raw, &config); err != nil {
		return Config{}, fmt.Errorf("decode configuration: %w", err)
	}
	if err := config.validate(); err != nil {
		return Config{}, err
	}
	return config, nil
}

func (c *Config) validate() error {
	host, port, err := net.SplitHostPort(c.Listen)
	if err != nil {
		return errors.New("listen must be an explicit TCP address")
	}
	portNumber, err := strconv.Atoi(port)
	if err != nil {
		return errors.New("listen port must be numeric")
	}
	if portNumber < 1 || portNumber > 65535 {
		return errors.New("listen port is out of range")
	}
	if c.AcceptProxyProtocolV2 {
		addr, parseErr := netip.ParseAddr(host)
		if parseErr != nil || !addr.IsLoopback() || portNumber < 1024 {
			return errors.New("PROXY protocol v2 listener must use an explicit loopback address and unprivileged port")
		}
	} else if port != "443" {
		return errors.New("direct listener must use port 443")
	}
	if !c.AcceptProxyProtocolV2 && host != "0.0.0.0" && host != "::" {
		addr, parseErr := netip.ParseAddr(host)
		if parseErr != nil || addr.IsLoopback() || addr.IsUnspecified() {
			return errors.New("direct listen host must be a concrete non-loopback IP or an unspecified address")
		}
	}
	normalizedHost, err := normalizeDomain(c.DoHHostname)
	if err != nil {
		return fmt.Errorf("invalid DoH hostname: %w", err)
	}
	c.DoHHostname = normalizedHost
	proxyAddr, err := netip.ParseAddr(c.ProxyIPv4)
	if err != nil || !proxyAddr.Is4() || !isPublicAddress(proxyAddr) {
		return errors.New("proxy_ipv4 must be a public IPv4 address")
	}
	c.ProxyIPv4 = proxyAddr.String()
	for label, path := range map[string]string{
		"policy_path":          c.PolicyPath,
		"tls_certificate_path": c.TLSCertificatePath,
		"tls_private_key_path": c.TLSPrivateKeyPath,
	} {
		if !filepath.IsAbs(path) {
			return fmt.Errorf("%s must be absolute", label)
		}
	}
	upstreamHost, upstreamPort, err := net.SplitHostPort(c.UpstreamDoT.Address)
	if err != nil || upstreamPort != "853" {
		return errors.New("upstream_dot.address must be an explicit IP on port 853")
	}
	upstreamAddr, err := netip.ParseAddr(upstreamHost)
	if err != nil || !isPublicAddress(upstreamAddr) {
		return errors.New("upstream_dot.address must use a public IP")
	}
	if upstreamAddr.Unmap() == proxyAddr.Unmap() {
		return errors.New("upstream_dot.address must differ from proxy_ipv4")
	}
	upstreamName, err := normalizeDomain(c.UpstreamDoT.ServerName)
	if err != nil {
		return fmt.Errorf("invalid upstream_dot.server_name: %w", err)
	}
	c.UpstreamDoT.ServerName = upstreamName
	if err := c.Limits.validate(); err != nil {
		return err
	}
	return nil
}

func (l Limits) validate() error {
	checks := []struct {
		name    string
		value   int
		minimum int
		maximum int
	}{
		{"max_concurrent_connections", l.MaxConcurrentConnections, 16, 65536},
		{"max_connections_per_ip", l.MaxConnectionsPerIP, 1, 256},
		{"max_doh_requests_per_minute", l.MaxDoHRequestsPerMinute, 1, 6000},
		{"max_tracked_source_ips", l.MaxTrackedSourceIPs, 64, 1_000_000},
		{"max_dns_message_bytes", l.MaxDNSMessageBytes, 512, 65535},
		{"max_client_hello_bytes", l.MaxClientHelloBytes, 1024, 65535},
		{"handshake_timeout_seconds", l.HandshakeTimeoutSeconds, 1, 30},
		{"connect_timeout_seconds", l.ConnectTimeoutSeconds, 1, 30},
		{"idle_timeout_seconds", l.IdleTimeoutSeconds, 5, 600},
		{"max_connection_seconds", l.MaxConnectionSeconds, 30, 86400},
	}
	for _, check := range checks {
		if check.value < check.minimum || check.value > check.maximum {
			return fmt.Errorf("%s must be between %d and %d", check.name, check.minimum, check.maximum)
		}
	}
	if l.MaxConnectionsPerIP > l.MaxConcurrentConnections {
		return errors.New("max_connections_per_ip cannot exceed max_concurrent_connections")
	}
	if l.MaxBytesPerDirection < 1<<20 || l.MaxBytesPerDirection > 16<<30 {
		return errors.New("max_bytes_per_direction must be between 1 MiB and 16 GiB")
	}
	return nil
}

func loadPolicy(path string) (*Policy, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read policy: %w", err)
	}
	var policy Policy
	if err := decodeStrict(raw, &policy); err != nil {
		return nil, fmt.Errorf("decode policy: %w", err)
	}
	if policy.SchemaVersion != policySchemaVersion || policy.State != "owner_lab_default_off" {
		return nil, errors.New("unsupported Smart DNS policy identity or state")
	}
	if policy.RecursiveDNS {
		return nil, errors.New("recursive DNS is forbidden")
	}
	if policy.Matching != "exact_or_child_domain" || policy.ApplicationTLS != "opaque_passthrough" {
		return nil, errors.New("unsupported matching or TLS policy")
	}
	if policy.DNSAnswers != (DNSAnswerPolicy{
		A:                "owned_proxy_ipv4",
		AAAA:             "noerror_nodata",
		HTTPS:            "noerror_nodata",
		SVCB:             "noerror_nodata",
		Other:            "noerror_nodata",
		OutsideAllowlist: "refused",
		TTLSeconds:       60,
	}) {
		return nil, errors.New("unsupported DNS answer policy")
	}
	if len(policy.Groups) != 2 {
		return nil, errors.New("policy must define exactly ai and gaming_services groups")
	}
	allowedGroups := map[string]bool{"ai": true, "gaming_services": true}
	seen := make(map[string]bool)
	for group, suffixes := range policy.Groups {
		if !allowedGroups[group] || len(suffixes) == 0 || len(suffixes) > 64 {
			return nil, fmt.Errorf("invalid policy group %q", group)
		}
		for _, suffix := range suffixes {
			normalized, err := normalizeDomain(suffix)
			if err != nil || normalized != suffix {
				return nil, fmt.Errorf("invalid canonical suffix in group %q", group)
			}
			if seen[normalized] {
				return nil, fmt.Errorf("duplicate policy suffix %q", normalized)
			}
			seen[normalized] = true
			policy.allowedSuffixes = append(policy.allowedSuffixes, normalized)
		}
	}
	sort.Strings(policy.allowedSuffixes)
	digest := sha256.Sum256(raw)
	policy.sha256 = hex.EncodeToString(digest[:])
	return &policy, nil
}

func decodeStrict(raw []byte, target any) error {
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(target); err != nil {
		return err
	}
	if err := decoder.Decode(&struct{}{}); !errors.Is(err, io.EOF) {
		return errors.New("trailing JSON data")
	}
	return nil
}

func normalizeDomain(raw string) (string, error) {
	value := strings.ToLower(strings.TrimSuffix(strings.TrimSpace(raw), "."))
	if len(value) == 0 || len(value) > 253 || net.ParseIP(value) != nil {
		return "", errors.New("domain length or type is invalid")
	}
	labels := strings.Split(value, ".")
	if len(labels) < 2 {
		return "", errors.New("domain must have at least two labels")
	}
	for _, label := range labels {
		if len(label) == 0 || len(label) > 63 || label[0] == '-' || label[len(label)-1] == '-' {
			return "", errors.New("domain label is invalid")
		}
		for _, char := range []byte(label) {
			if (char < 'a' || char > 'z') && (char < '0' || char > '9') && char != '-' {
				return "", errors.New("domain must be canonical ASCII")
			}
		}
	}
	return value, nil
}

func isPublicAddress(addr netip.Addr) bool {
	addr = addr.Unmap()
	if !addr.IsValid() || !addr.IsGlobalUnicast() || addr.IsPrivate() || addr.IsLoopback() ||
		addr.IsLinkLocalUnicast() || addr.IsLinkLocalMulticast() || addr.IsMulticast() || addr.IsUnspecified() {
		return false
	}
	for _, prefix := range forbiddenPublicPrefixes {
		if prefix.Contains(addr) {
			return false
		}
	}
	return true
}

var forbiddenPublicPrefixes = []netip.Prefix{
	netip.MustParsePrefix("0.0.0.0/8"),
	netip.MustParsePrefix("100.64.0.0/10"),
	netip.MustParsePrefix("192.0.0.0/24"),
	netip.MustParsePrefix("192.0.2.0/24"),
	netip.MustParsePrefix("192.88.99.0/24"),
	netip.MustParsePrefix("198.18.0.0/15"),
	netip.MustParsePrefix("198.51.100.0/24"),
	netip.MustParsePrefix("203.0.113.0/24"),
	netip.MustParsePrefix("240.0.0.0/4"),
	netip.MustParsePrefix("2001::/23"),
	netip.MustParsePrefix("2001:db8::/32"),
}
