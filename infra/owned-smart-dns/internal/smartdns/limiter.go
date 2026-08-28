package smartdns

import (
	"sync"
	"time"
)

type sourceLimiter struct {
	mu          sync.Mutex
	entries     map[string]*sourceLimitEntry
	maxEntries  int
	maxRequests int
	window      time.Duration
	now         func() time.Time
}

type sourceLimitEntry struct {
	windowStart time.Time
	requests    int
	connections int
	lastSeen    time.Time
}

func newSourceLimiter(maxEntries, maxRequests int, window time.Duration) *sourceLimiter {
	return &sourceLimiter{
		entries:     make(map[string]*sourceLimitEntry),
		maxEntries:  maxEntries,
		maxRequests: maxRequests,
		window:      window,
		now:         time.Now,
	}
}

func (l *sourceLimiter) allowRequest(source string) bool {
	l.mu.Lock()
	defer l.mu.Unlock()
	now := l.now()
	entry := l.entryLocked(source, now)
	if entry == nil {
		return false
	}
	if now.Sub(entry.windowStart) >= l.window {
		entry.windowStart = now
		entry.requests = 0
	}
	entry.lastSeen = now
	if entry.requests >= l.maxRequests {
		return false
	}
	entry.requests++
	return true
}

func (l *sourceLimiter) acquireConnection(source string, maximum int) bool {
	l.mu.Lock()
	defer l.mu.Unlock()
	now := l.now()
	entry := l.entryLocked(source, now)
	if entry == nil {
		return false
	}
	entry.lastSeen = now
	if entry.connections >= maximum {
		return false
	}
	entry.connections++
	return true
}

func (l *sourceLimiter) releaseConnection(source string) {
	l.mu.Lock()
	defer l.mu.Unlock()
	if entry := l.entries[source]; entry != nil && entry.connections > 0 {
		entry.connections--
		entry.lastSeen = l.now()
	}
}

func (l *sourceLimiter) entryLocked(source string, now time.Time) *sourceLimitEntry {
	if entry := l.entries[source]; entry != nil {
		return entry
	}
	if len(l.entries) >= l.maxEntries {
		var oldestKey string
		var oldestTime time.Time
		for key, candidate := range l.entries {
			if candidate.connections != 0 {
				continue
			}
			if oldestKey == "" || candidate.lastSeen.Before(oldestTime) {
				oldestKey, oldestTime = key, candidate.lastSeen
			}
		}
		if oldestKey != "" {
			delete(l.entries, oldestKey)
		} else {
			return nil
		}
	}
	entry := &sourceLimitEntry{windowStart: now, lastSeen: now}
	l.entries[source] = entry
	return entry
}
