package smartdns

import (
	"encoding/base64"
	"fmt"
	"io"
	"net"
	"net/http"
	"strings"

	"github.com/miekg/dns"
)

type dohHandler struct {
	policy    *Policy
	proxyIPv4 string
	maxBytes  int64
	limiter   *sourceLimiter
}

func newDoHHandler(config Config, policy *Policy, limiter *sourceLimiter) http.Handler {
	return &dohHandler{
		policy:    policy,
		proxyIPv4: config.ProxyIPv4,
		maxBytes:  int64(config.Limits.MaxDNSMessageBytes),
		limiter:   limiter,
	}
}

func (h *dohHandler) ServeHTTP(response http.ResponseWriter, request *http.Request) {
	response.Header().Set("X-Content-Type-Options", "nosniff")
	response.Header().Set("Cache-Control", "no-store")
	if request.URL.Path != "/dns-query" {
		http.NotFound(response, request)
		return
	}
	source := remoteHost(request.RemoteAddr)
	if source == "" || !h.limiter.allowRequest(source) {
		http.Error(response, "rate limited", http.StatusTooManyRequests)
		return
	}
	wire, err := h.readMessage(response, request)
	if err != nil {
		http.Error(response, "invalid DNS request", http.StatusBadRequest)
		return
	}
	var query dns.Msg
	if err := query.Unpack(wire); err != nil {
		http.Error(response, "invalid DNS request", http.StatusBadRequest)
		return
	}
	reply := new(dns.Msg)
	reply.SetReply(&query)
	reply.Authoritative = false
	reply.RecursionAvailable = false
	if query.Opcode != dns.OpcodeQuery || len(query.Question) != 1 || query.Question[0].Qclass != dns.ClassINET {
		reply.Rcode = dns.RcodeFormatError
		h.writeMessage(response, reply)
		return
	}
	question := query.Question[0]
	if !h.policy.Allows(question.Name) {
		reply.Rcode = dns.RcodeRefused
		h.writeMessage(response, reply)
		return
	}
	if question.Qtype == dns.TypeA {
		record, err := dns.NewRR(fmt.Sprintf("%s %d IN A %s", question.Name, h.policy.DNSAnswers.TTLSeconds, h.proxyIPv4))
		if err != nil {
			reply.Rcode = dns.RcodeServerFailure
		} else {
			reply.Answer = []dns.RR{record}
			response.Header().Set("Cache-Control", fmt.Sprintf("max-age=%d", h.policy.DNSAnswers.TTLSeconds))
		}
	}
	h.writeMessage(response, reply)
}

func (h *dohHandler) readMessage(response http.ResponseWriter, request *http.Request) ([]byte, error) {
	switch request.Method {
	case http.MethodGet:
		encoded := request.URL.Query().Get("dns")
		if encoded == "" || len(encoded) > base64.RawURLEncoding.EncodedLen(int(h.maxBytes)) {
			return nil, io.ErrUnexpectedEOF
		}
		wire, err := base64.RawURLEncoding.DecodeString(encoded)
		if err != nil || int64(len(wire)) > h.maxBytes {
			return nil, io.ErrUnexpectedEOF
		}
		return wire, nil
	case http.MethodPost:
		if mediaType := strings.ToLower(strings.TrimSpace(strings.Split(request.Header.Get("Content-Type"), ";")[0])); mediaType != "application/dns-message" {
			return nil, io.ErrUnexpectedEOF
		}
		reader := http.MaxBytesReader(response, request.Body, h.maxBytes)
		defer reader.Close()
		wire, err := io.ReadAll(reader)
		if err != nil || len(wire) == 0 {
			return nil, io.ErrUnexpectedEOF
		}
		return wire, nil
	default:
		return nil, io.ErrUnexpectedEOF
	}
}

func (h *dohHandler) writeMessage(response http.ResponseWriter, message *dns.Msg) {
	wire, err := message.Pack()
	if err != nil {
		http.Error(response, "DNS response failed", http.StatusInternalServerError)
		return
	}
	response.Header().Set("Content-Type", "application/dns-message")
	response.WriteHeader(http.StatusOK)
	_, _ = response.Write(wire)
}

func remoteHost(address string) string {
	host, _, err := net.SplitHostPort(address)
	if err != nil {
		return ""
	}
	return host
}
