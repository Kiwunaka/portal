# R09 Performance, Infra, Observability, Deploy Readiness

Date: 2026-04-26

Scope: POKROV Open Beta v4 performance optimization priorities, backend/web/app/node budgets, node metrics freshness and actionability, admin incident telemetry, deploy and rollback clarity, and production probes after deploy.

## Executive Summary

The platform has a solid local and brain-origin readiness base, but it does not yet have a closed performance and observability release gate. Local default gates passed on 2026-04-25, and the quick gate with `--brain-ip 82.21.114.104` passed on 2026-04-26 with node predeploy readiness green. The web surfaces also fit the current draft JS budget: marketing build output shows `/` at `97.7 kB` first-load JS and `/checkout` at `104 kB`, under the existing `<= 120 kB` target.

The main deploy-readiness gap is not "can the repo build"; it is "can production stay observable and recoverable after beta users arrive." The current evidence still leaves runtime app-download smoke blocked by missing live auth, Android public release blocked by missing physical-device localhost/control-surface audit, payment blocked by provider activation, and RU-origin telemetry mixed because `mini` reaches POKROV surfaces and node TCP/443 but cannot reach Telegram endpoints. Also, the stable client release handoff pointer still names `0.1.0-seed.1+20260423`, while the latest beta metadata is `0.2.0-beta.1+20260425` and contains no newly built binaries.

Priority for Open Beta v4 should be: close live-origin smoke evidence, add p95 latency instrumentation and gates, turn node telemetry into alertable capacity decisions, and keep rollback steps tied to rollout config, qdisc state, and static/backend deploy artifacts. I did not run builds or tests in this research pass because the assigned write scope allowed only this report file.

## Evidence Table

Allowed labels: `confirmed`, `probable`, `unknown`, `needs local run`, `blocked by missing access`, `blocked by provider`, `mixed`, `deferred`.

| Evidence | Label | What it proves | What it does not prove |
| --- | --- | --- | --- |
| `docs/audit-artifacts/public_beta_release_gate_report.md` | confirmed | Local default gate passed on 2026-04-25: pytest matrix, admin/auth regressions, client security smoke, full client Flutter tests, API lifecycle smoke, link checks, marketing build, webapp build, Playwright E2E, UI visual smoke. | Brain-origin, RU-origin, Android physical audit, runtime app-download smoke, or client platform builds. |
| `docs/audit-artifacts/public_beta_release_gate_report_brain.md` | confirmed | Quick gate with `--brain-ip` passed on 2026-04-26; node predeploy readiness returned `ok: true`; brain-origin evidence was green for that run. | Full default gate plus platform builds, Android physical safety, live payment, or live download auth. |
| `docs/audit-artifacts/client_platform_builds_2026-04-26.md` | confirmed | Windows, Android APK, and Android AAB build commands completed with `PASS_WITH_RELEASE_GATES_REMAINING`. | Public signing, Android physical audit, public hosting, or production handoff approval. |
| `C:/Users/kiwun/.config/superpowers/worktrees/POKROV-app/open-beta-v4/artifacts/releases/pokrov-app/0.2.0-beta.1+20260425/README.md` | confirmed | `0.2.0-beta.1+20260425` is metadata-only paid beta evidence; Android public release and Windows public release remain blocked. | It does not contain newly built binaries. |
| `C:/Users/kiwun/.config/superpowers/worktrees/POKROV-app/open-beta-v4/artifacts/releases/release-handoff.json` | confirmed | Stable handoff pointer still references `0.1.0-seed.1+20260423` and intentionally blank public URLs. | It does not prove the latest `0.2.0-beta.1` metadata is the live runtime download source. |
| `portal_bot/api.py:5055`, `:5167`, `:5977`, `:7358`, `:10243` | confirmed | Backend exposes managed profile, client latency sample upload, admin metrics status, admin summary, and admin node health endpoints. | No p95, error budget, or request-duration SLO is currently evidenced from production traffic. |
| `webapp/src/app/(admin)/admin/dashboard/page.tsx` and `webapp/src/app/(admin)/admin/nodes/page.tsx` | confirmed | Admin dashboard fetches summary, metrics status, timeseries, users, tickets; node page fetches health, metrics status, 7d traffic, drift, and action APIs. | No evidence that operators have an always-on external dashboard or alerting outside the web admin UI. |
| `webapp/e2e/admin-gate.spec.ts` | confirmed | Browser E2E covers admin route access, mobile clickability, node alert labels, probe failure details, separate panel/dataplane context, and rollout config save/reload. | It uses mocked API contracts; it does not prove live production telemetry freshness. |
| `infra/portal-node-metrics.timer` and `infra/portal-node-observer.timer` | confirmed | Metrics and observer timers are configured every 60 seconds. | It does not prove every host has the units installed, enabled, current, and successfully pushing. |
| `scripts/collect_node_metrics.py` | confirmed | Collector records panel latency, CPU, memory, disk, network RX/TX Mbps, dataplane probe stage/error/classification, IPv4/IPv6 health, transport health, and node score. | It does not by itself enforce alert routing or operator acknowledgement. |
| `infra/node-qdisc-profiles.json` | confirmed | Repo-truth qdisc rates exist: brain/pl at 850 Mbps, us/it/free at 425 Mbps, nl at 637 Mbps; all are 85 percent or near 85 percent of configured uplink. | It does not prove qdisc is currently applied on each live node or survives reboot. |
| `scripts/remote_node_qdisc_smoke.py` | confirmed | Saturation smoke exists with heavy flow plus HTTPS probes and defaults of connect p95 <= 1.0s, TTFB p95 <= 1.0s, total p95 <= 2.0s. | No latest qdisc smoke artifact was found for this worktree. |
| `packages/app_shell/lib/app_first_runtime_bootstrap.dart` in client worktree | confirmed | App bootstrap has `connectionTimeout=8s`, `requestTimeout=15s`, `maxRequestAttempts=3`, Android direct bootstrap address for `api.pokrov.space`, and managed profile fetch flow. | No cold-start, bootstrap p95, or connect-to-stable telemetry is persisted yet. |
| `packages/runtime_engine/lib/runtime_engine.dart` in client worktree | confirmed | Runtime phases distinguish artifact missing, artifact ready, initialized, config staged, running, and degraded host diagnostics. | No release-device latency series or failure-rate budget is evidenced. |
| `docs/audit-artifacts/ru_probe_2026-04-26.md` | mixed | RU-origin `mini` reached Google, canonical POKROV web/API surfaces, and node TCP/443 endpoints. | Telegram endpoints failed from `mini`; reserve xhttp and hysteria checks failed; repeated RU stability is not proven. |
| `docs/audit-artifacts/runtime_app_download_smoke_2026-04-26.md` | blocked by missing access | Production `/api/health` returned HTTP 200. | `/api/client/apps`, provider list, and release handoff URL validation did not run because live `TELEGRAM_INIT_DATA` was missing. |
| `docs/audit-artifacts/payment_provider_probe_2026-04-26.md` | blocked by provider | Brain reached FreeKassa API for site and bot request paths. | Live payment cannot close because provider returned `Merchant not activated`. |
| Assigned platform and client worktrees build output directories | needs local run | `webapp/.next`, `webapp/out`, `marketing/.next`, `marketing/out`, `apps/android_shell/build`, and `apps/windows_shell/build` are absent in the assigned worktrees. | Existing audit artifacts are retained evidence, not current generated output in this worktree. |

## P0 Issues

1. Live download and release-handoff verification is not closed.
   Evidence: `runtime_app_download_smoke_2026-04-26.md` is blocked without live token; stable client `release-handoff.json` still references `0.1.0-seed.1+20260423` while latest beta metadata is `0.2.0-beta.1+20260425`.
   Impact: after deploy, cabinet/app/bot download surfaces could point to old, blank, or non-public artifacts without a green runtime smoke catching it.

2. Android public readiness remains blocked.
   Evidence: `android_physical_audit_2026-04-26.md` says no physical device / no `ANDROID_AUDIT_SERIAL`; client builds exist but physical release-installed localhost/control-surface audit is missing.
   Impact: Android must stay internal beta or hidden from public download claims.

3. No production p95 performance gate exists for critical backend and client flows.
   Evidence: API lifecycle smoke passes functionally, and backend endpoints exist, but there is no reported p95 for `start-trial`, managed profile fetch, access-key redeem, admin summary, metrics status, or app connect-to-stable.
   Impact: beta can widen into latency regressions without failing the release gate.

4. Payment deploy readiness is blocked by provider status.
   Evidence: brain-origin provider probe reached FreeKassa but got `Merchant not activated`.
   Impact: public paid checkout cannot be called production-ready, and payment incident telemetry cannot be fully proven end to end.

## P1 Issues

1. RU-origin observability is mixed.
   Evidence: `mini` reached POKROV canonical surfaces and node TCP/443, but Telegram `api.telegram.org` and `t.me` failed; reserve checks failed.
   Impact: RU-specific release handoff must say "canonical POKROV reachable, Telegram path degraded from mini" rather than a single green verdict.

2. Metrics freshness thresholds are split across layers.
   Evidence: systemd timers run every 60s; admin metrics status defaults stale after 900s; predeploy readiness defaults stale after 1800s and observer stale after 180s.
   Impact: operators can see different freshness conclusions depending on endpoint or script. That is acceptable only if the dashboard labels each threshold clearly.

3. Node capacity telemetry exists but is not yet a release decision loop.
   Evidence: collector stores CPU, RAM, disk, network Mbps, 24h peak via API, online keys/connections, and qdisc profiles. No latest artifact proves qdisc smoke, per-node saturation headroom, or purchase/drain decisions.
   Impact: beta growth can saturate a node before the team has an explicit "drain/add capacity" threshold.

4. Lighthouse and browser performance artifacts are missing.
   Evidence: Next build size output exists in audit reports, but no Lighthouse/WebPageTest result is present for Open Beta v4.
   Impact: LCP/CLS/TBT/INP are budgeted but not measured.

5. Admin incident telemetry is visible but not incident-managed.
   Evidence: admin dashboard shows stale metrics, unhealthy nodes, payment callback failures, numeric subscription fallback, single-point risk, and tickets. There is no evidence of alert routing, owner, acknowledgement, or post-deploy watch checklist.
   Impact: critical signals may stay passive unless an operator is watching the web admin.

## P2 Issues

1. Client bootstrap retry budget can exceed the desired connect UX if every request hits timeout.
   Evidence: `connectionTimeout=8s`, `requestTimeout=15s`, `maxRequestAttempts=3`.
   Impact: timeout paths can outlive a `<= 15s` connect-to-stable p95 target unless retries are staged, cancellable, and measured.

2. Admin and report text shows mojibake in several local outputs.
   Evidence: current PowerShell reads of frontend/report text display garbled Russian text in some files.
   Impact: this is not a runtime proof by itself, but final operator artifacts and dashboards need UTF-8 validation so incident copy remains readable.

3. `rg.exe` was unavailable due `Access is denied` in this environment.
   Evidence: command failed during research; PowerShell `Select-String` was used as fallback.
   Impact: no product impact, but future agents may need the same fallback for repeatable research.

## Proposed Implementation Work

1. Add a performance gate script in the platform repo:
   - `scripts/api_latency_probe.py`
   - Inputs: base URL, endpoint list, method, auth from env only, sample count, warmup count, timeout, output path.
   - Outputs: p50, p95, p99, max, error rate, status-code histogram, redacted endpoint labels.
   - Gate failures: p95 above budget, error rate above budget, timeout count above budget.

2. Add app runtime telemetry in the client repo:
   - Record cold start to first frame.
   - Record bootstrap state load, start-trial, route-policy sync, managed profile fetch, materialization, runtime initialize, connect, and stable state.
   - Store locally as redacted rolling diagnostics and upload only aggregate event timings if a privacy-safe endpoint is approved.
   - Add release-device manual capture template for Android and Windows.

3. Add web performance measurement:
   - Use Lighthouse CI or plain Lighthouse JSON for marketing, cabinet, and admin routes.
   - Store artifacts under `docs/audit-artifacts/` only in deliberate release runs.
   - Fail release if marketing LCP/CLS or JS budgets regress beyond threshold.

4. Harden runtime app-download handoff:
   - Update the stable client `release-handoff.json` only after the orchestrator-approved beta artifact decision.
   - Add a post-deploy smoke that checks `/api/client/apps`, docs fallback, provider list, and generated download CTA behavior using env-only live auth.
   - Treat blank public URLs as expected only while state is explicitly blocked/gated.

5. Make node observability actionable:
   - Add an admin "Incident" panel with current-origin, brain-origin, RU-origin, node freshness, observer freshness, payment provider, and runtime download smoke.
   - Add severity: `page_now`, `same_day`, `watch`.
   - Add runbook link and "last checked by / at" metadata.

6. Close qdisc and capacity loop:
   - Run `remote_apply_node_qdisc.py show` plus `remote_node_qdisc_smoke.py` per live delivery node.
   - Store a compact per-node capacity report with current Mbps, 24h peak, port utilization, online keys, online connections, CPU/RAM/disk, and qdisc status.
   - Use drain/resync before disable for nodes over capacity or failing dataplane checks.

7. Clarify rollback:
   - Backend rollback: redeploy previous backend revision and restart `portal-api`, `portal-bot`, `portal-helpbot`, `portal-feedbackbot`.
   - Static rollback: redeploy previous `marketing/out` and `webapp/out` or previous build artifact.
   - Network rollback: set `defaults.transport_profile=legacy_reality_fallback`, disable `operator_lab`, run qdisc rollback only if shaping caused degradation.
   - Client rollback: keep public URLs pointed at last approved gated artifact; never publish Android without the physical audit.

## Exact Verification Commands

Run these from the platform worktree unless a command says otherwise:

```powershell
Set-Location C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4
python scripts/release_gate_check.py
python scripts/release_gate_check.py --quick --brain-ip 82.21.114.104
python scripts/predeploy_node_readiness.py --brain-ip 82.21.114.104 --web-domain pokrov.space --ssh-user root --ssh-port 29374
python scripts/verify_brain_ready.py --brain-ip 82.21.114.104
python scripts/api_lifecycle_smoke.py
python scripts/smoke_client_apps.py --base-url https://api.pokrov.space --check-providers --require-release-handoff --init-data $env:TELEGRAM_INIT_DATA
```

Client build and audit commands:

```powershell
Set-Location C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4
python scripts/run_client_release_gate.py preflight
python scripts/run_client_release_gate.py test --suite portal
python scripts/run_client_release_gate.py test --suite full
python scripts/run_client_release_gate.py build --target windows
python scripts/run_client_release_gate.py build --target android-apk
python scripts/run_client_release_gate.py build --target android-aab
$env:ANDROID_AUDIT_SERIAL="<physical-device-serial>"
python scripts/android_localhost_audit.py --serial $env:ANDROID_AUDIT_SERIAL --connect-wait-sec 30 --disconnect-wait-sec 15
```

Frontend and browser commands:

```powershell
Set-Location C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4\marketing
npm.cmd run build
npm.cmd run check:seo

Set-Location C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4\webapp
npm.cmd run build
npm.cmd run test:e2e
npm.cmd run test:e2e:admin
```

Lighthouse commands after starting local production servers:

```powershell
Set-Location C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4\marketing
npm.cmd run build
Start-Process -FilePath npm.cmd -ArgumentList @("run","start","--","-p","3103") -WorkingDirectory (Get-Location)
npx lighthouse http://127.0.0.1:3103/ --preset=desktop --output=json --output-path=..\docs\audit-artifacts\lighthouse-marketing-home-desktop.json
npx lighthouse http://127.0.0.1:3103/checkout/ --form-factor=mobile --screenEmulation.mobile=true --output=json --output-path=..\docs\audit-artifacts\lighthouse-marketing-checkout-mobile.json

Set-Location C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4\webapp
npm.cmd run build
Start-Process -FilePath npm.cmd -ArgumentList @("run","start","--","-p","3104") -WorkingDirectory (Get-Location)
npx lighthouse http://127.0.0.1:3104/ --form-factor=mobile --screenEmulation.mobile=true --output=json --output-path=..\docs\audit-artifacts\lighthouse-webapp-entry-mobile.json
npx lighthouse http://127.0.0.1:3104/admin/dashboard/ --preset=desktop --output=json --output-path=..\docs\audit-artifacts\lighthouse-webapp-admin-dashboard-desktop.json
```

Node observability and qdisc commands:

```powershell
Set-Location C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4
python scripts/node_observability_gate.py --out docs/audit-artifacts/node_observability_gate_2026-04-26.json
python scripts/remote_apply_node_qdisc.py show --profiles infra/node-qdisc-profiles.json --node-code pl --host <node-host> --ssh-port 29374
python scripts/remote_node_qdisc_smoke.py --profiles infra/node-qdisc-profiles.json --node-code pl --host <node-host> --ssh-port 29374 --probe-url https://1.1.1.1/cdn-cgi/trace --heavy-url "https://speed.cloudflare.com/__down?bytes=50000000"
python scripts/remote_transport_front_smoke.py --host <node-host> --ssh-port 29374
```

RU-origin commands from the external RU probe host:

```powershell
Set-Location C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4
python scripts/ru_probe_runner.py --probe-host mini --out ops-local\ru-probe-open-beta-v4.json
python scripts/render_ru_probe_report.py --input ops-local\ru-probe-open-beta-v4.json
```

Quick public endpoint timing command from current origin:

```powershell
$urls = @(
  "https://api.pokrov.space/api/health",
  "https://api.pokrov.space/api/public/catalog",
  "https://pokrov.space/",
  "https://app.pokrov.space/"
)
foreach ($url in $urls) {
  $samples = 1..50 | ForEach-Object {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    try {
      Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 15 | Out-Null
      [pscustomobject]@{ ok = $true; ms = $sw.Elapsed.TotalMilliseconds }
    } catch {
      [pscustomobject]@{ ok = $false; ms = $sw.Elapsed.TotalMilliseconds }
    }
  }
  $ok = @($samples | Where-Object ok | Sort-Object ms)
  $p95Index = [Math]::Min($ok.Count - 1, [Math]::Max(0, [Math]::Ceiling($ok.Count * 0.95) - 1))
  [pscustomobject]@{ url = $url; count = $samples.Count; ok = $ok.Count; p95_ms = [Math]::Round($ok[$p95Index].ms, 1) }
}
```

## Performance Budget

| Surface | Budget | Gate |
| --- | ---:| --- |
| Marketing home mobile LCP | <= 2.5s | Lighthouse mobile on `/` |
| Marketing checkout mobile LCP | <= 2.8s | Lighthouse mobile on `/checkout/` |
| Marketing CLS | <= 0.10 | Lighthouse plus visual smoke |
| Marketing TBT | <= 200ms | Lighthouse |
| Marketing first-load JS | <= 120 kB target | `npm.cmd run build`; current evidence: `/` 97.7 kB, `/checkout` 104 kB |
| Webapp entry first-load JS | <= 150 kB target | `npm.cmd run build` route output |
| Admin dashboard first useful render | <= 3.0s on mocked API, <= 5.0s on live API | Playwright trace plus API p95 |
| API `/api/health` | <= 100ms p95 from current origin, <= 250ms p95 from brain | API latency probe |
| API `/api/public/catalog` | <= 200ms p95 current origin | API latency probe |
| API `POST /api/client/session/start-trial` | <= 700ms p95 excluding network from device | Authenticated beta load probe |
| API `GET /api/client/profile/managed` | <= 800ms p95 excluding network from device | Authenticated beta load probe |
| API `POST /api/access-keys/redeem` | <= 1000ms p95 | Authenticated beta load probe |
| Admin `/api/admin/summary` | <= 1000ms p95 | Admin API latency probe |
| Admin `/api/admin/metrics/status` | <= 750ms p95 | Admin API latency probe |
| Node metrics freshness | timer every 60s; admin ok <= 900s; predeploy ok <= 1800s | `/api/admin/metrics/status`, predeploy readiness |
| Observer freshness | ok <= 180s when configured | predeploy readiness and admin node cards |
| App cold start Android | <= 2.5s p95 to first useful Protection screen | physical release build capture |
| App cold start Windows | <= 3.5s p95 to first useful Protection screen | release build capture |
| App bootstrap to managed profile | <= 5.0s p95 on normal network | client telemetry |
| Connect tap to stable running | <= 15s p95 beta, <= 8s p50 | client telemetry and manual smoke |
| Reconnect with profile staged | <= 8s p95 | client telemetry |
| Node CPU | warn >= 75%, reject smart-connect >= 90% | collector and shortlist |
| Node RAM | warn >= 80%, critical >= 90% | collector/admin |
| Node disk | warn free < 15%, critical free < 8% | collector/admin |
| Node port utilization | warn >= 70%, critical >= 85% of uplink | current/24h peak Mbps |
| Qdisc small probe under load | connect p95 <= 1s, TTFB p95 <= 1s, total p95 <= 2s | `remote_node_qdisc_smoke.py` |

## Lighthouse Plan

1. Measure marketing public routes:
   - `/`
   - `/checkout/`
   - `/install/`
   - `/mobile/`
   - `/telegram/`

2. Measure webapp continuation routes with mocked or safe session state where required:
   - `/`
   - `/dashboard/`
   - `/subscription/`
   - `/downloads/`
   - `/support/`

3. Measure admin routes with mocked API first, live admin only in a secured operator run:
   - `/admin/dashboard/`
   - `/admin/nodes/`
   - `/admin/network/`
   - `/admin/tickets/`

4. Required Lighthouse assertions:
   - Performance score >= 0.85 for marketing mobile.
   - LCP within budget for home and checkout.
   - CLS <= 0.10 on every measured route.
   - TBT <= 200ms for public routes and <= 350ms for admin routes.
   - No route increases first-load JS by more than 10 percent versus the last accepted release artifact.

5. Artifact policy:
   - Store JSON and a short markdown summary only for deliberate release runs.
   - Do not store cookies, auth headers, Telegram init data, or screenshots with personal identifiers.

## Backend p95 Plan

1. Add or run an API latency probe against these endpoint classes:
   - Public: `/api/health`, `/api/public/catalog`.
   - App-first authenticated: `/api/client/session/start-trial`, `/api/client/profile/managed`, `/api/client/nodes/latency-samples`.
   - Commerce: `/api/access-keys/status/{key}`, `/api/access-keys/redeem`, provider start endpoint once provider is active.
   - Admin: `/api/admin/summary`, `/api/admin/metrics/status`, `/api/admin/nodes/health`, `/api/admin/metrics/timeseries`.

2. Capture:
   - p50, p95, p99, max.
   - HTTP status histogram.
   - timeout count.
   - request label, not raw URLs containing private keys or tokens.
   - origin: current, brain, RU when available.

3. Gate:
   - Fail if public endpoint error rate > 1 percent.
   - Fail if authenticated critical endpoint p95 exceeds budget by > 20 percent.
   - Fail if admin metrics endpoints return missing/stale data while collector is expected healthy.

4. Production hardening:
   - Add FastAPI middleware for server-side request duration histograms by route template.
   - Add slow-query logging for admin summary, metrics status, nodes health, and managed profile generation.
   - Keep raw user IDs, tokens, payment payloads, and subscription URLs out of logs.

## App Cold Start and Connect Latency Plan

1. Android release build:
   - Capture app process start to first useful Protection screen.
   - Capture tap `Try free` to access payload received.
   - Capture managed profile fetch start/end.
   - Capture route-policy sync start/end.
   - Capture connect tap to runtime `running` or user-visible failure.
   - Capture disconnect and reconnect with profile already staged.

2. Windows release build:
   - Capture process start to first useful Protection screen.
   - Capture runtime artifact resolve, libcore load, profile staging, connect, stable running, disconnect.
   - Capture elevated-rights warning path where applicable.

3. Acceptance:
   - At least 10 clean samples per platform before public beta expansion.
   - Include one constrained network run and one normal broadband run.
   - Report p50 and p95, not only "works".

4. Instrumentation constraints:
   - Do not upload raw config payloads.
   - Do not log subscription URLs, Telegram IDs, personal IPs, or provider tokens.
   - Use install-scoped aggregate labels only when upload is approved.

## Node Capacity Plan

1. Current repo-truth capacity:
   - `brain`: 1000 Mbps uplink, 850 Mbps qdisc target.
   - `pl`: 1000 Mbps uplink, 850 Mbps qdisc target.
   - `nl`: 750 Mbps uplink, 637 Mbps qdisc target.
   - `us`: 500 Mbps uplink, 425 Mbps qdisc target.
   - `it`: 500 Mbps uplink, 425 Mbps qdisc target.
   - `free`: 500 Mbps uplink, 425 Mbps qdisc target, preferred `fq_codel`.

2. Capacity thresholds:
   - Watch when 24h peak reaches 60 percent of qdisc target.
   - Warn when 24h peak reaches 70 percent of qdisc target.
   - Drain new assignments when sustained throughput reaches 85 percent of qdisc target or CPU >= 90 percent.
   - Add capacity before two nodes in the same hoster family or subnet both exceed 70 percent.

3. Smart-connect policy:
   - Keep `cpu_percent >= 90` as reject.
   - Penalize `75-84` and `85-89` CPU bands as already documented.
   - Never cross the paid-pool versus `NL-free` access boundary because of ping.

4. Required per-node report:
   - Enabled/draining/accepting-new-clients.
   - Metrics status and age.
   - Observer status and age when configured.
   - Online keys and online connections now.
   - Current RX/TX/total Mbps and 24h peak Mbps.
   - CPU/RAM/disk.
   - Panel state, dataplane state, last probe stage, last error kind.
   - RU-origin status when available.
   - qdisc active state and latest smoke result.

## Monitoring Dashboard Checklist

- [ ] Header shows release state: local gate, brain-origin, RU-origin, Android audit, payment provider, runtime download smoke.
- [ ] Admin summary shows active non-free accounts, trial accounts, bonus accounts, unique installs 24h/7d, observer-seen accounts 24h, and data quality badges.
- [ ] Node cards separate panel state, dataplane state, metrics freshness, observer freshness, and RU-origin evidence.
- [ ] Node cards show CPU, RAM, disk, current Mbps, 24h peak Mbps, online keys, online connections, hoster family, ASN, subnet.
- [ ] Probe details show stage, error kind, error message, classification, IPv4 health, IPv6 health, transport health.
- [ ] `reality_target_mismatch` has operator-readable explanation.
- [ ] Metrics values distinguish real `0` from missing/unavailable telemetry.
- [ ] Incident panel groups alerts by `page_now`, `same_day`, and `watch`.
- [ ] Payment provider status shows last provider probe result and blocked reason without secrets.
- [ ] Runtime app-download smoke shows last run, auth source label, release handoff version, and URL state without token values.
- [ ] RU-origin panel shows probe host, timestamp, Google reachability, Telegram app/web path, canonical hosts, nodes, reserve xhttp/hysteria.
- [ ] Deploy panel shows latest backend deploy, static deploy, release handoff sync, service restart statuses, and rollback target.
- [ ] Qdisc panel shows desired profile, active qdisc, smoke p95 results, and rollback command.
- [ ] Links to runbooks: deployment, monitoring, RU origin probe, Android physical audit, release links, payment provider.
- [ ] Every alert has owner, last checked at, and next action.

## Deploy and Rollback Readiness

Open Beta v4 deploy should be considered ready only when this sequence is green or explicitly accepted as degraded:

1. Local default gate.
2. Brain quick/predeploy gate.
3. Client platform build evidence for intended artifacts.
4. Android physical audit if Android is public or downloadable outside controlled internal beta.
5. Runtime app-download smoke with env-only live auth.
6. Payment provider smoke or public checkout disabled/gated.
7. RU-origin report with separate Telegram and POKROV conclusions.
8. Post-deploy `verify_brain_ready.py`.
9. Admin dashboard confirms metrics freshness and no critical node alerts.
10. Rollback target is named before deploy.

Rollback commands should restore user safety first:

```powershell
# Backend rollback shape: redeploy previous known-good revision/artifact, then restart runtime units.
python scripts/remote_deploy_brain_portal_code.py --brain-ip 82.21.114.104 --restart portal-api,portal-bot,portal-helpbot,portal-feedbackbot

# Static rollback shape: redeploy previous known-good static bundle.
python scripts/remote_deploy_brain_static_sites.py --brain-ip 82.21.114.104

# Network rollback shape: restore rollout defaults to legacy fallback, disable operator lab, then verify.
python scripts/verify_brain_ready.py --brain-ip 82.21.114.104
```

## Production Probes After Deploy

Run immediately after deploy:

1. `current-origin check`: local public web/API URLs, webapp entry, marketing entry, `/api/health`, public catalog, link checks.
2. `brain-origin check`: `verify_brain_ready.py`, predeploy readiness, provider API probe, node metrics status, service active states.
3. `RU-origin check`: RU probe from `mini` or replacement host, with Telegram and canonical POKROV surfaces separated.
4. Runtime smoke: `/api/client/apps` with live env-only Telegram init data and release handoff requirement.
5. Admin smoke: dashboard, nodes, network rollout, tickets, payments.
6. Client smoke: Windows connect/disconnect and Android physical audit if Android distribution is in scope.
7. Capacity smoke: qdisc show plus saturation smoke on at least the canary node and any recently changed node.

## Final Recommendation

Do not widen Open Beta v4 based only on the current local/brain gate reports. The next release captain should first close runtime app-download smoke, resolve or explicitly gate payment, update/confirm release handoff metadata, capture Lighthouse and API p95 artifacts, and produce one per-node capacity snapshot with qdisc evidence. After that, beta can widen with a much cleaner operational spine: a user issue can be traced through app timing, API p95, node freshness, provider status, and origin-specific reachability instead of guesswork.
