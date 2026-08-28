package smartdns

import (
	"testing"
	"time"
)

func TestSourceLimiterBoundsRequestsConnectionsAndCardinality(t *testing.T) {
	clock := time.Unix(1000, 0)
	limiter := newSourceLimiter(1, 2, time.Minute)
	limiter.now = func() time.Time { return clock }
	if !limiter.allowRequest("one") || !limiter.allowRequest("one") || limiter.allowRequest("one") {
		t.Fatal("request window limit was not enforced")
	}
	if !limiter.acquireConnection("one", 1) || limiter.acquireConnection("one", 1) {
		t.Fatal("per-source connection limit was not enforced")
	}
	if limiter.allowRequest("two") {
		t.Fatal("tracked-source cardinality must fail closed while all entries are active")
	}
	limiter.releaseConnection("one")
	if !limiter.allowRequest("two") {
		t.Fatal("inactive oldest source should be evicted")
	}
}
