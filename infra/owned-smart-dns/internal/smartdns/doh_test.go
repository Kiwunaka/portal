package smartdns

import (
	"bytes"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/miekg/dns"
)

func TestDoHReturnsProxyOnlyForAllowlistedAQuestion(t *testing.T) {
	handler := testDoHHandler(t)
	allowed := exchangeDoH(t, handler, "api.openai.com.", dns.TypeA)
	if allowed.Rcode != dns.RcodeSuccess || len(allowed.Answer) != 1 {
		t.Fatalf("unexpected allowed response: rcode=%d answers=%d", allowed.Rcode, len(allowed.Answer))
	}
	record, ok := allowed.Answer[0].(*dns.A)
	if !ok || record.A.String() != "8.8.8.8" {
		t.Fatalf("unexpected synthetic answer: %#v", allowed.Answer)
	}

	refused := exchangeDoH(t, handler, "evilopenai.com.", dns.TypeA)
	if refused.Rcode != dns.RcodeRefused || len(refused.Answer) != 0 {
		t.Fatalf("unexpected refused response: rcode=%d answers=%d", refused.Rcode, len(refused.Answer))
	}
}

func TestDoHSuppressesAlternateAddressAndHTTPSHints(t *testing.T) {
	handler := testDoHHandler(t)
	for _, queryType := range []uint16{dns.TypeAAAA, dns.TypeHTTPS, dns.TypeSVCB, dns.TypeTXT} {
		response := exchangeDoH(t, handler, "chatgpt.com.", queryType)
		if response.Rcode != dns.RcodeSuccess || len(response.Answer) != 0 {
			t.Fatalf("type %d must return NOERROR/NODATA", queryType)
		}
	}
}

func testDoHHandler(t *testing.T) http.Handler {
	t.Helper()
	policy := loadTestPolicy(t)
	config := Config{ProxyIPv4: "8.8.8.8", Limits: Limits{MaxDNSMessageBytes: 4096}}
	return newDoHHandler(config, policy, newSourceLimiter(64, 100, time.Minute))
}

func exchangeDoH(t *testing.T, handler http.Handler, name string, queryType uint16) *dns.Msg {
	t.Helper()
	query := new(dns.Msg)
	query.SetQuestion(name, queryType)
	wire, err := query.Pack()
	if err != nil {
		t.Fatal(err)
	}
	request := httptest.NewRequest(http.MethodPost, "https://resolver.example/dns-query", bytes.NewReader(wire))
	request.Header.Set("Content-Type", "application/dns-message")
	request.RemoteAddr = "198.51.100.10:12345"
	response := httptest.NewRecorder()
	handler.ServeHTTP(response, request)
	if response.Code != http.StatusOK {
		t.Fatalf("unexpected HTTP status: %d", response.Code)
	}
	var message dns.Msg
	if err := message.Unpack(response.Body.Bytes()); err != nil {
		t.Fatal(err)
	}
	return &message
}
