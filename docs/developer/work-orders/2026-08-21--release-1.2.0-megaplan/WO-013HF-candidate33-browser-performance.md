# WO-013HF — candidate.33 headless browser performance

Status: `PARTIAL_EXACT_CANDIDATE33_BROWSER_LAB_MARKETING_4_OF_4_PASS; WEBAPP_BLOCKED_BY_ACCESS; REQUIRED_SCOPE_FAIL; GATE_F_BLOCKED`

Observed: `2026-09-04`

Production/public mutation: `NONE`

## Outcome

The clean exact candidate.33 platform source builds fresh production static
exports for marketing and cabinet with pinned Node `22.14.0`, npm `11.7.0`
and Next.js `16.3.2`. A headless Playwright `1.61.1` / Chromium
`149.0.7827.55` localhost lab then retains three discarded warmups and twenty
numeric samples for each marketing browser budget.

All four measured marketing budgets pass their stop thresholds: home LCP p75
is `136 ms <= 2500 ms`, checkout LCP p75 is `96 ms <= 2800 ms`, CLS p75 is
`0 <= 0.1`, and TBT p75 is `8 ms <= 200 ms`. The local render is non-blank,
has the expected title and main content, exposes visible controls, contains no
framework overlay or page error, and a visible internal control responds.

The cabinet export also builds and renders, but `/dashboard/` correctly stops
at the account-login screen without an integrated API/auth fixture. External
requests were deliberately blocked during rendered QA; attempting Telegram
login therefore reports `Received app shell instead of API response`. That
screen is not authenticated dashboard content, so
`page.webapp_route_content_ms` is retained as `BLOCKED_BY_ACCESS` with zero
samples. The required whole `browser_lab` scope consequently fails closed on
the missing cabinet metric; no full browser-lab PASS is claimed.

## Exact boundary

| Fact | Exact value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.33`, app `1.2.0+4053` |
| Platform / client / Core / index | `f530005...5bc1` / `6ab1bca...735e` / `cd8f0f4...884d` / `63993fb...c43c` |
| Source state | exact platform source worktree clean before and after collection |
| Browser lab | Windows 11 Pro build `26100`; ASUS host; headless Chromium `149.0.7827.55`; localhost loopback; reduced motion; service workers blocked |
| Collector | canonical `pokrov.browser-performance` v`1.0.0`; 3 warmups; 20 retained samples per measured metric |
| Browser tool fallback | Browser plugin unavailable; regular Playwright used headlessly |
| Marketing gate | `PASS 4/4`, no baseline comparison |
| Full required scope | `FAIL`, missing `page.webapp_route_content_ms` |
| Cabinet classification | `BLOCKED_BY_ACCESS_NO_INTEGRATED_API_AUTH_FIXTURE` |
| Verification | fresh static exports `2/2`; performance gate/normalizer tests `14/14`; `git diff --check` PASS |
| Cleanup | temporary localhost ports `43120/43121` closed; source worktree clean |

## Evidence

External raw samples, normalized records, validator summaries and screenshots
are indexed at:

```text
E:/POKROV-tools/release-evidence/1.2.0-candidate33-browser-performance-2026-09-04/candidate33-browser-performance-evidence-index.json
SHA-256 4096fea9cab987d6ab5a3c9cb4466d710c207630076b82525c765eb1f92ff71c
```

The retained normalized summary is
`evidence/013HF-candidate33-browser-performance/013HF-candidate33-browser-performance.json`,
SHA-256 `2f51c940838daefefc8c45d83dd3c181b361257fc65945d125eb5a2f9f3c0257`.

The metric flow under test was exactly: `app loads -> first meaningful screen
renders -> primary visible controls respond without runtime errors`. Because
the Browser plugin is unavailable in this environment, the documented regular
Playwright fallback was used. All browser work was headless; no host input or
host network state changed.

## Release impact

`REL/PERF-001`, Gate E, `REL_DOD/DOD-13` and `FE_PR/PR-09` gain stronger
exact-candidate browser evidence without level change. Marketing closes its
bounded localhost budget subset, but the whole browser-lab scope, authenticated
cabinet, selected network/browser matrix, comparable baseline/regression,
physical Android/Windows performance and post-promotion proof remain open.
Gate F stays `BLOCKED 2/17/0`.

No candidate bytes, deploy, public asset, Store object, stable pointer,
production account, control-plane state, host input or host network changed.
