# Performance and Local Quality Gate

- Status: active for release `1.2.0`
- Contract version: `1.0.0`
- Last reconciled: 2026-08-29

This document owns the platform performance method and the bounded local
quality gate. It does not own Android/Windows runtime implementation or turn a
local worktree into an exact release candidate.

## Authority

- Budgets: `shared/contracts/performance/performance-budgets.v1.json`.
- Offline validator: `scripts/performance_budget_gate.py`.
- Static web collector: `scripts/collect_web_performance.py`.
- Browser collector: `marketing/scripts/collect-browser-performance.mjs`.
- API collector: `scripts/api_latency_probe.py`.
- Generic sample normalizer: `scripts/new_performance_evidence.py`.
- Client capture procedure: `POKROV-app/docs/operations/client-motion-performance-checklist.md`.
- Local aggregate gate: `scripts/release_1_2_local_quality_gate.py`.

The contract is append/version only. A threshold or sampling change requires a
new contract version and a new comparable baseline; editing old evidence is not
allowed.

## Method

The gate uses nearest-rank percentiles. A measured record must bind the contract
version and SHA-256, release version, candidate label, 40-character source
revision, clean/dirty state, collector version, UTC time, platform, OS, device,
architecture, build mode, origin, network and toolchain. Metric-specific fields
such as artifact SHA-256, power mode, interaction scenario and idle window are
mandatory where the budget declares them.

Cold start/connect/rollback use at least 3 discarded warmups and 20 retained
samples. API latency uses at least 5 and 50. Client frames discard 60 and retain
600. Idle CPU/memory stabilizes for 30 and retains 60. Static build metrics use
one deterministic export observation. Regression is
`((candidate - baseline) / baseline) * 100` and is valid only when the gate
environment fingerprints match.

`target_lte` is the intended optimization target. `stop_lte` is the promotion
boundary. A stop PASS with `target_met=false` is reported exactly that way; it
is not rewritten as target compliance. Memory and client artifact size begin as
observations: the first valid run records a baseline, and following comparable
runs stop at more than 10% growth.

## Budget groups

| Group | Scope | Stop rule |
| --- | --- | --- |
| Android/Windows useful cold start | exact candidate/device | Android p95 <= 2.5s; Windows p95 <= 3.5s; target <= 2.0s |
| Verified connect/reconnect/rollback | exact candidate/device | p95 <= 15s / 8s / 2s; connect target <= 5s |
| Flutter frame build/raster | exact candidate/device profile mode | p95 <= 16.7ms with 600 retained frames |
| Idle CPU | exact candidate/device | Windows p95 <= 1%; Android p95 <= 1.5% |
| Idle memory and client artifact size | exact candidate/device or artifact | first baseline, then <= 10% comparable growth |
| Public API latency | controlled named origin | health 100ms, catalog 200ms, start-trial 700ms, profile 800ms, redeem 1000ms p95 |
| Page latency | named browser/network lab | home LCP 2.5s, checkout LCP 2.8s, CLS 0.1, TBT 200ms, cabinet route content 3s |
| Static export assets | local source gate | per-surface critical-route gzip JS, total images and total fonts |

The complete metric list and units live only in the JSON contract.

## Evidence states

Raw evidence can state `MEASURED`, `MANUAL_OWNER_TEST`, `BLOCKED_BY_ACCESS` or
`NOT_REQUESTED`. Only the validator computes `PASS`, `FAIL` or
`BASELINE_RECORDED`. A non-measured record cannot contain samples, warmups or a
baseline. Insufficient samples, an unknown unit/metric, a wrong contract digest,
non-finite values, a different baseline fingerprint or missing environment data
fail closed.

`BASELINE_RECORDED` is not a regression PASS. It only creates the first point
for an observation metric.

## Collection

Validate the contract without network access:

```powershell
python scripts/performance_budget_gate.py
```

After fresh `next build` outputs exist for marketing, webapp and adminapp:

```powershell
python scripts/collect_web_performance.py `
  --candidate-label local-working-tree `
  --output <evidence-dir>\web-assets.json
python scripts/performance_budget_gate.py `
  --evidence <evidence-dir>\web-assets.json `
  --required-scope local_static `
  --output <evidence-dir>\web-assets-gate.json
```

The collector hashes every measured input file and reports a dirty worktree as
dirty. It computes the maximum gzip-compressed JavaScript referenced by the
allowlisted critical routes plus unique exported image/font bytes. `.next`
cache contents, server bundles and duplicate HTML references do not inflate the
metric.

For a running owned marketing or cabinet surface, the browser collector emits a
numeric sample array. Start the selected static server separately, record its
exact origin/network/browser environment, then run, for example:

```powershell
cd marketing
npm.cmd run collect:performance -- `
  --metric page.marketing_home_lcp_ms `
  --base-url https://<owned-environment> `
  --warmups 3 --samples 20 `
  --output <temporary-path>\home-lcp.json
```

It uses a new reduced-motion Chromium context per run, blocks service workers,
and records only numeric LCP/CLS/TBT or route-content values. Normalize the
array with `new_performance_evidence.py`, supplying an environment JSON object,
then validate it. Headless local output does not replace the selected Phase 11
browser/network matrix.

The API collector allows only the five contract endpoints, never prints bodies
or authorization, requires HTTPS except explicitly allowed localhost, and
rejects state-changing probes unless the operator supplies both the explicit
flag and JSON body. Do not run trial/redeem probes against production without a
separate authorization and isolated fixture:

```powershell
python scripts/api_latency_probe.py `
  --budget-id api.health.current_origin_ms `
  --base-url https://<owned-current-origin> `
  --origin current --network-profile <profile> `
  --candidate-label <candidate> --output <evidence-dir>\api-health.json
```

One HTTP/1.1 client is shared by the discarded warmups and retained samples.
This makes the declared warmup method real: the first connection/TLS setup is
discarded, while retained samples measure request-to-first-response-byte over
the persistent session used by normal API clients. Each response is drained
without logging its body so the connection can return to the pool. The client
may reconnect when the peer closes an idle connection, and any failed sample
still fails the run. Evidence records `persistent_http1_keep_alive` as the
connection policy so legacy cold-connection results cannot be compared as the
same environment.

If an ambient VPN/TUN route would capture a probe that must represent the
owned direct operator origin, pass a locally assigned literal address with
`--source-address <IPv4-or-IPv6>`. The collector validates that the address is
assigned, disables URL proxy discovery and binds every request socket to that
address without changing the route table or stopping the VPN. Record the
physical interface and route readback in the handoff. A missing or unassigned
address fails closed; a source-bound local result still does not prove
brain-origin, RU-origin or an exact candidate by itself.

No live endpoint was called while establishing this contract.

## Local aggregate gate

The aggregate gate runs the performance contract/tests, app-shell analysis and
widget suite, client seed/docs contracts, cabinet lint/build/E2E, marketing
build/SEO/responsive/reduced-motion checks, a fresh admin build for static
budget input, and the static performance collector/gate:

```powershell
python scripts/release_1_2_local_quality_gate.py `
  --client-root C:\path\to\POKROV-app-worktree `
  --core-root C:\path\to\POKROV-core-worktree `
  --evidence-dir C:\path\to\local-evidence
```

The output binds all three repository revisions and dirty states. It always
sets `candidate_proven=false` and `promotion_status=MANUAL_OWNER_TEST`. The
report retains separate non-PASS lanes for candidate-device performance,
artifact-size comparison, browser lab, controlled-origin API performance and
exact-candidate signing/device/origin proof. Evidence output under
`artifacts/releases/` is rejected.

The 2026-08-22 retained dirty-worktree run under the megaplan evidence folder
passed all 15 local steps. Fresh static stop budgets passed `9/9`: marketing
critical-route JS/images/fonts were `246707`/`7848431`/`96848` bytes; webapp
`302597`/`5390960`/`182880`; adminapp `455270`/`0`/`0`. Marketing, webapp and
adminapp route-JS targets plus marketing/webapp image targets remain unmet and
are recorded as `target_met=false`. This run is local `I3` evidence, not a
clean baseline or candidate proof.

The 2026-08-29 clean pre-candidate convergence rerun also passed all `15/15`
steps against platform `882f287...`, client `55e7d5c...` and Core
`3c2b114...`, using pinned Node `22.14.0` and lockfile-exact frontend
dependencies. Static stops passed `9/9`; several optimization targets remain
honestly `target_met=false`. The report SHA-256 is
`ca84626431041a0d29bef42d7d7132475baf066a16f900ed8a8149fc3e27dd26`.
It retains `candidate_proven=false` and promotion `MANUAL_OWNER_TEST`, so this
clean run closes only the local source-quality slice.

## Phase 11 handoff

Before promotion, Phase 11 must attach clean exact-candidate evidence for every
required scope, compare memory/artifact observations with a matching approved
baseline, run the selected Android/Windows and browser/network matrices, and
capture current-origin API measurements. Brain-origin and RU-origin remain
separate evidence; neither substitutes for current origin. Signing, physical
device, payment/provider and post-promotion checks remain manual until actually
executed and retained.

Any stop-threshold or regression failure blocks promotion. Roll back the code or
active pointer to the last proved candidate; do not weaken the contract or
relabel missing/manual evidence as PASS.
