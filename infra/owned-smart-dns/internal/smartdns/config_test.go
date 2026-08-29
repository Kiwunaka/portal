package smartdns

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func TestPolicyUsesExactOrChildDomainMatching(t *testing.T) {
	policy := loadTestPolicy(t)
	for _, name := range []string{
		"openai.com",
		"api.openai.com.",
		"gemini.google.com",
		"preview.gemini.google.com.",
		"XBOX.COM",
		"presence-heartbeat.xboxlive.com",
	} {
		if !policy.Allows(name) {
			t.Fatalf("expected %q to be allowed", name)
		}
	}
	for _, name := range []string{"evilopenai.com", "openai.com.example", "localhost", "192.0.2.1"} {
		if policy.Allows(name) {
			t.Fatalf("expected %q to be refused", name)
		}
	}
}

func TestPolicyRejectsRecursiveMode(t *testing.T) {
	path := filepath.Join(t.TempDir(), "policy.json")
	raw := readCanonicalPolicy(t)
	var document map[string]any
	if err := json.Unmarshal(raw, &document); err != nil {
		t.Fatal(err)
	}
	document["recursive_dns"] = true
	modified, err := json.Marshal(document)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, modified, 0o600); err != nil {
		t.Fatal(err)
	}
	if _, err := loadPolicy(path); err == nil {
		t.Fatal("recursive policy must be rejected")
	}
}

func TestPublicAddressRejectsPrivateAndDocumentationRanges(t *testing.T) {
	for _, value := range []string{"10.0.0.1", "100.64.0.1", "127.0.0.1", "169.254.1.1", "192.0.2.1", "198.51.100.1", "203.0.113.1", "2001:db8::1"} {
		address := mustAddress(t, value)
		if isPublicAddress(address) {
			t.Fatalf("expected %s to be rejected", value)
		}
	}
	for _, value := range []string{"1.1.1.1", "8.8.8.8", "2606:4700:4700::1111"} {
		if !isPublicAddress(mustAddress(t, value)) {
			t.Fatalf("expected %s to be accepted", value)
		}
	}
}

func TestConfigRejectsSelfReferencedDoTEndpoint(t *testing.T) {
	config := Config{
		Listen:             "0.0.0.0:443",
		DoHHostname:        "dns.example.com",
		ProxyIPv4:          "1.1.1.1",
		PolicyPath:         filepath.Join(t.TempDir(), "policy.json"),
		TLSCertificatePath: filepath.Join(t.TempDir(), "cert.pem"),
		TLSPrivateKeyPath:  filepath.Join(t.TempDir(), "key.pem"),
		UpstreamDoT: UpstreamConfig{
			Address:    "1.1.1.1:853",
			ServerName: "cloudflare-dns.com",
		},
		Limits: Limits{
			MaxConcurrentConnections: 16,
			MaxConnectionsPerIP:      1,
			MaxDoHRequestsPerMinute:  1,
			MaxTrackedSourceIPs:      64,
			MaxDNSMessageBytes:       512,
			MaxClientHelloBytes:      1024,
			HandshakeTimeoutSeconds:  1,
			ConnectTimeoutSeconds:    1,
			IdleTimeoutSeconds:       5,
			MaxConnectionSeconds:     30,
			MaxBytesPerDirection:     1 << 20,
		},
	}
	if err := config.validate(); err == nil {
		t.Fatal("DoT upstream equal to the proxy IP must fail closed")
	}
}

func loadTestPolicy(t *testing.T) *Policy {
	t.Helper()
	path := filepath.Join(t.TempDir(), "policy.json")
	if err := os.WriteFile(path, readCanonicalPolicy(t), 0o600); err != nil {
		t.Fatal(err)
	}
	policy, err := loadPolicy(path)
	if err != nil {
		t.Fatal(err)
	}
	return policy
}

func readCanonicalPolicy(t *testing.T) []byte {
	t.Helper()
	path := filepath.Join("..", "..", "..", "..", "shared", "contracts", "network", "smart-dns-policy.v1.json")
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	return raw
}
