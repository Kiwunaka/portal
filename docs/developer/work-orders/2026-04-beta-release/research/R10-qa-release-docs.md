# R10 QA Release Docs

Status: complete

## Scope

QA matrix, release gates, docs consistency, tech debt, and final paid-beta readiness evidence requirements across:

- platform root: `C:/Users/kiwun/Documents/ai/VPN`
- active client repo: `C:/Users/kiwun/Documents/ai/POKROV-app`

Constraint honored: read-only research except this file. I did not read or print env files, key directories, merchant secrets, or raw operational secrets.

Claim labels used below: `confirmed`, `probable`, `unknown`, `needs local run`, `blocked by missing access`.

## Files/docs inspected

Confirmed:

- `docs/README.md`
- `docs/product/portal-vpn-product.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/app-first-and-bonus-flows.md`
- `docs/operations/deployment-and-access.md`
- `docs/operations/monitoring-and-visibility.md`
- `docs/operations/publishing-and-signing-guide.md`
- `docs/developer/developer-guide.md`
- `docs/developer/repository-map.md`
- `docs/developer/work-orders/2026-04-beta-release/00-orchestrator-context.md`
- `docs/developer/work-orders/2026-04-beta-release/02-beta-scope.md`
- `docs/developer/work-orders/2026-04-beta-release/03-tech-debt-register.md`
- `docs/developer/work-orders/2026-04-beta-release/04-risk-register.md`
- `docs/developer/work-orders/2026-04-beta-release/05-release-gate-plan.md`
- `docs/developer/work-orders/2026-04-beta-release/work-orders/WO-006-payments-keys-bonuses-support.md`
- `docs/developer/work-orders/2026-04-beta-release/work-orders/WO-007-client-android-windows-beta.md`
- `docs/developer/work-orders/2026-04-beta-release/work-orders/WO-008-infra-nodes-observability-deploy.md`
- `docs/developer/work-orders/2026-04-beta-release/work-orders/WO-010-paid-beta-release-captain.md`
- `docs/audit-artifacts/release_gate_report.md`
- `scripts/release_gate_check.py`
- `scripts/release_orchestrator.py`
- `scripts/run_client_release_gate.py`
- `scripts/client_security_smoke.py`
- `scripts/android_localhost_audit.py`
- `scripts/api_lifecycle_smoke.py`
- `scripts/admin_webapp_smoke.py`
- `scripts/check-links.py`
- `scripts/ui_visual_smoke.py`
- `webapp/README.md`
- `webapp/package.json`
- `marketing/package.json`
- `tests/test_release_gate_check.py`
- `tests/test_run_client_release_gate.py`
- `tests/test_api_lifecycle_smoke.py`
- `tests/test_api_payments_callbacks.py`
- `tests/test_marketing_release_readiness.py`
- `tests/test_public_copy_guardrails.py`
- `tests/test_ui_visual_smoke.py`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/product/client-product-contract.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/architecture/app-first-onboarding-flow.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/implementation/client-release-backlog.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/windows-release-readiness.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/scripts/README.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/scripts/bootstrap-local.ps1`
- `C:/Users/kiwun/Documents/ai/POKROV-app/scripts/bootstrap-workspace.ps1`
- `C:/Users/kiwun/Documents/ai/POKROV-app/scripts/build-windows-release.ps1`
- `C:/Users/kiwun/Documents/ai/POKROV-app/scripts/fetch-libcore-assets.ps1`
- `C:/Users/kiwun/Documents/ai/POKROV-app/scripts/run-tests.ps1`
- `C:/Users/kiwun/Documents/ai/POKROV-app/scripts/validate-seed.ps1`

## Current state

Confirmed:

- The canonical local release report generator is `python scripts/release_gate_check.py`.
- The one-command gates-only wrapper is `python scripts/release_orchestrator.py --gates-only`.
- `release_gate_check.py` writes a markdown report to `docs/audit-artifacts/release_gate_report.md` by default.
- Default `release_gate_check.py` gates include release pytest subset, admin/auth regression, client security smoke, full client tests, API lifecycle smoke, link checks, marketing build, admin webapp smoke, webapp build, Playwright E2E, and UI visual smoke.
- Quick `release_gate_check.py --quick` swaps the release pytest matrix for `tests/test_worker_retention.py` and swaps full client tests for the portal client suite.
- Optional client platform build gates are added with `--client-platform-gates windows,android-apk,android-aab` or `CLIENT_PLATFORM_GATES`.
- Android build gates require `ANDROID_AUDIT_SERIAL` and reject emulator serials when Android APK/AAB gates are requested.
- Without Android build gates, `ANDROID_AUDIT_SERIAL` is optional and folds the adb localhost audit into the same report only when set.
- The active root wrapper `scripts/run_client_release_gate.py` now targets `C:/Users/kiwun/Documents/ai/POKROV-app` by default.
- The active client repo has scripts for seed validation, workspace bootstrap, tests, libcore fetch/sync, and unsigned Windows release bundle staging.
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md` classifies the client lane as engineering green but public cutover blocked.
- `docs/audit-artifacts/release_gate_report.md` records a PASS generated at `2026-04-23 01:25:35`.

Probable:

- The saved PASS report is not current enough for a paid-beta decision, because its client-security and client-test tails still reference `external/client-fork/app`, while current scripts and docs say the active client truth is `POKROV-app`.
- The gate pack has drifted after the latest saved report and needs a fresh run before final beta signoff.

Needs local run:

- Fresh default gate: `python scripts/release_gate_check.py --output docs/audit-artifacts/release_gate_report.md`.
- Fresh platform build gates where intended: `python scripts/release_gate_check.py --client-platform-gates windows,android-apk,android-aab --output docs/audit-artifacts/release_gate_report.md`.
- Fresh release-orchestrator gates-only proof: `python scripts/release_orchestrator.py --gates-only`.

Blocked by missing access:

- Live provider acceptance, live webhook delivery, real payment capture/refund/cancel, production deploy, Android physical device audit, production signing, and live current/brain/RU origin evidence were not verified in this read-only pass.

## Release readiness matrix

| Area | Command / evidence | Automation status | Current beta status |
| --- | --- | --- | --- |
| Backend pytest | `python -m pytest portal_bot/tests/test_app_first_api.py tests/test_portal_api.py tests/test_worker_retention.py tests/test_observer_service.py tests/test_observer_api.py tests/test_collect_xray_observer.py tests/test_predeploy_node_readiness.py tests/test_admin_webapp_smoke.py tests/test_public_copy_guardrails.py tests/test_reviews_username_masking.py -q` | confirmed in default gate | needs local run; saved PASS is stale against active client lane |
| Broader backend/API | `tests/test_api_p0_extensions.py`, `tests/test_smart_connect_api.py`, `tests/test_network_rollout_api.py`, node/panel tests | confirmed tests exist | probable gap: not all are in default gate |
| Worker tests | `tests/test_worker_retention.py`; `tests/test_free_cycle_service.py` | `test_worker_retention` confirmed in default/quick gate | probable gap: free-cycle test is WO-006 validation but not in default gate |
| Payment tests | `python -m pytest tests/test_api_payments_callbacks.py -q` | confirmed test exists and WO-006 requires it | P0 needs local run; not included in `release_gate_check.py` default gate |
| Payment lifecycle smoke | `python scripts/api_lifecycle_smoke.py` | confirmed in default gate | needs local run; covers one API-only trial/support/bonus/purchase contour |
| Admin/auth regression | `python -m pytest tests/test_api_auth_and_tickets.py -q` | confirmed in default gate | needs local run |
| Admin static smoke | `python scripts/admin_webapp_smoke.py` | confirmed in default gate | needs local run; structural/static smoke only |
| Public copy guardrails | `tests/test_public_copy_guardrails.py` | confirmed in release pytest matrix | needs local run |
| Marketing release readiness | `tests/test_marketing_release_readiness.py` | confirmed test exists | probable gap: not in default gate, partly covered by link/UI smoke |
| Redesign spine status | `shared/redesign-spine.json`, `tests/test_redesign_spine.py` | confirmed absent | P1/P0 by design decision; no formal spine gate exists |
| UI visual smoke | `python scripts/ui_visual_smoke.py` | confirmed in default gate | needs local run; string/content smoke, not screenshot visual review |
| Required screenshots | `05-release-gate-plan.md` screenshot list | confirmed manual requirement | needs local run/manual evidence |
| Marketing build | `npm.cmd run build` in `marketing/` | confirmed in default gate | needs local run |
| Marketing SEO check | `npm.cmd run check:seo` | confirmed package script | probable gap: not in default gate |
| Public link checks | `python scripts/check-links.py` | confirmed in default gate | needs local run |
| WebApp build | `npm.cmd run build` in `webapp/` | confirmed in default gate | needs local run |
| WebApp Playwright E2E | `npm.cmd run test:e2e` | confirmed in default gate; runs admin and cabinet specs | needs local run |
| Admin Playwright E2E | `npm.cmd run test:e2e:admin` | confirmed package script | probable gap: default gate uses broader `test:e2e`; dedicated admin command useful for admin-only signoff |
| Client preflight | `python scripts/run_client_release_gate.py preflight` | confirmed wrapper exists | needs local run before trusting client gates |
| Client release gate | `python scripts/run_client_release_gate.py test --suite full` | confirmed in default gate | needs local run against `POKROV-app` |
| Client platform builds | `python scripts/run_client_release_gate.py build --target windows/android-apk/android-aab` | confirmed optional | needs local run with prerequisites |
| Client security smoke | `python scripts/client_security_smoke.py` | confirmed in default gate | needs local run against `POKROV-app`; saved report reflects old fork path |
| Android localhost audit | `python scripts/android_localhost_audit.py --serial <physical-device-serial> --connect-wait-sec 30 --disconnect-wait-sec 15` | confirmed script and release-gate integration | P0 blocked by missing physical-device release-installed evidence |
| Full release gate report | `python scripts/release_gate_check.py --output docs/audit-artifacts/release_gate_report.md` | confirmed | P0 needs fresh local run |
| Deploy/verify | `python scripts/release_orchestrator.py --brain-ip 82.21.114.104 ...` | confirmed wrapper | blocked by missing access / outside read-only scope |
| Origin evidence | current-origin, brain-origin, RU-origin checks | confirmed required by docs | blocked by missing access; RU readiness may be degraded |

## Gaps against beta

P0 confirmed:

- Android public release remains blocked until a release-installed build on physical hardware passes localhost/control-surface audit before connect, after connect, and after disconnect.
- Production Android signing and trusted Windows signing are not proven by the local scripts or saved report.
- Payment provider research remains pending in `R07`; WO-006 says provider category acceptance and webhook verification must be confirmed or explicitly risk-accepted before paid beta.
- The saved release report is stale for the active client lane because it records `external/client-fork/app` client evidence while current canon is `POKROV-app/main`.
- `tests/test_api_payments_callbacks.py` is not part of `release_gate_check.py` default or quick gates, despite payment idempotency being a paid-beta blocker.
- Live deploy, final runtime handoff, and separate `current-origin`, `brain-origin`, and `RU-origin` evidence are not present in the inspected release report.

P0 probable:

- The default release gate can pass without exercising the dedicated payment callback/idempotency suite; this could let a paid-beta blocker escape if only the default report is used.
- The default release gate can pass without artifact-producing client builds unless `--client-platform-gates` is provided; this is fine for repo/static gates, but insufficient for beta artifact handoff.

P1 confirmed:

- `shared/redesign-spine.json` and `tests/test_redesign_spine.py` are absent, while the beta orchestrator context calls that out as a known starting fact.
- UI visual smoke is a string/content assertion script, not a browser screenshot or layout inspection gate.
- `marketing` has `npm.cmd run check:seo`, but the canonical full gate runs `scripts/check-links.py` and `npm.cmd run build`, not the package SEO script.
- `tests/test_ui_visual_smoke.py` appears stale against `scripts/ui_visual_smoke.py`: the test expects older strings such as `POKROV VPN` / `secure Telegram login`, while the script checks newer `POKROV` / `secure sign-in` wording.

P1 probable:

- The release report may need a schema/version marker or "active client root" line so stale bridge/fork evidence is obvious.
- The work-order research files R01-R09 are still placeholders in this checkout, so final synthesis cannot yet claim complete research coverage.

Unknown:

- Whether live payment provider webhooks, retries, refund/cancel events, and category acceptance are ready.
- Whether current production `APP_*` runtime URLs match the final beta artifacts.
- Whether the current Android and Windows release-mode builds connect successfully on real networks.

## P0 blockers

1. confirmed: Fresh full release gate report is required because the latest saved PASS is stale against the current `POKROV-app` lane.
2. confirmed: Payment callback/idempotency suite must be run and included in paid-beta evidence.
3. confirmed: Android physical-device localhost/control-surface audit evidence is missing.
4. confirmed: Android production signing and Windows trusted signing/public warning posture are not proven.
5. confirmed: Payment provider acceptance and webhook verification are pending R07 or explicit risk acceptance.
6. confirmed: Live deploy/runtime handoff and current/brain/RU-origin evidence are missing from the inspected beta evidence set.

## P1 beta polish

- confirmed: Add or intentionally defer a redesign-spine gate. Current visual checks do not prove design-system consistency.
- confirmed: Run or fold `npm.cmd run check:seo` into the release evidence when marketing SEO changes.
- confirmed: Refresh `tests/test_ui_visual_smoke.py` so the script self-test matches current copy policy.
- probable: Include `tests/test_marketing_release_readiness.py` in a broader release-test pack or document why link/UI smoke is sufficient.
- probable: Add a report field to `release_gate_check.py` showing `POKROV_APP_ROOT` / active client root and whether client platform gates were included.

## P2 defer

- confirmed: Apple iOS/macOS release gates remain readiness-only and do not block Android+Windows paid beta.
- confirmed: Public `Blocked only` routing remains deferred until geo assets, DNS behavior, and leak checks are complete.
- probable: Full BI dashboard can remain deferred if admin support/payment/access views cover the paid-beta operating needs.

## Technical debt

| ID | Label | Debt | Impact | Suggested owner |
| --- | --- | --- | --- | --- |
| R10-TD-001 | confirmed | Saved `release_gate_report.md` contains retired `external/client-fork/app` client evidence while active wrappers target `POKROV-app`. | Can mislead go/no-go. | WO-010 |
| R10-TD-002 | confirmed | Payment callback/idempotency tests are not in default `release_gate_check.py`. | Paid beta can pass local gates without the dedicated payment blocker suite. | WO-006 / WO-010 |
| R10-TD-003 | confirmed | Redesign spine file and test are absent. | No formal design-contract gate. | WO-001 |
| R10-TD-004 | confirmed | `tests/test_ui_visual_smoke.py` appears stale against `scripts/ui_visual_smoke.py`. | The smoke script has weaker self-test confidence. | WO-001 / WO-002 / WO-003 |
| R10-TD-005 | confirmed | UI visual smoke is static string checking, not screenshot/browser visual QA. | Required visual evidence remains manual. | WO-010 |
| R10-TD-006 | probable | Default gate omits some broader backend, payment, free-cycle, and marketing readiness tests. | Release report may be narrower than beta-risk register implies. | WO-010 |
| R10-TD-007 | probable | Release report does not prominently declare active client root, platform build gates, Android audit serial class, or origin-evidence status. | Gate readers must infer what was not run. | WO-010 |

## Security/privacy risks

Confirmed:

- Android local-control exposure remains the main client security blocker until the physical release-build audit passes.
- A green repo/static gate does not prove no unauthenticated SOCKS, HTTP proxy, DNS, Clash API, command, or admin/control surface is reachable.
- Evidence and screenshots must not contain secrets, raw subscription links, payment IDs, Telegram IDs, emails, or private webhook payloads.
- Live payment logs must be redacted.
- Admin auth gates are covered by Playwright E2E and static smoke, but still need fresh local evidence.

Probable:

- If payment provider tests are not folded into the final gate evidence, duplicate webhook or manual reconciliation regressions remain a paid-beta risk.
- If UI screenshots are not collected, raw-link or unsafe-copy regressions may escape string-based guardrails.

Blocked by missing access:

- Live provider signature/webhook verification.
- Live deploy and runtime environment inspection.
- Physical Android device release-build audit.

## Required implementation WOs

Confirmed mapping:

- WO-001: design-system/brand assets; should own redesign-spine decision and visual evidence standard.
- WO-002: marketing checkout/install; should own marketing build, SEO, link checks, and public CTA evidence.
- WO-003: user cabinet; should own webapp build, cabinet Playwright, downloads/support/redeem evidence.
- WO-004: admin console; should own admin smoke, admin Playwright, manual extend/revoke, pause switches, and support/payment/admin visibility.
- WO-006: payments/keys/bonuses/support; should own payment callback/idempotency tests and provider readiness.
- WO-007: Android/Windows beta client; should own client preflight/tests/builds, signing status, and Android audit evidence.
- WO-008: infra/observability/deploy; should own deploy, rollback, node health, metrics, and origin checks.
- WO-009: security/privacy/abuse/compliance; should own evidence redaction, raw-link leakage checks, and audit policy.
- WO-010: release captain; should own final gate report and go/no-go synthesis.

## Validation commands

Run from `C:/Users/kiwun/Documents/ai/VPN` unless noted.

Core default beta gate:

```powershell
python scripts/release_gate_check.py --output docs/audit-artifacts/release_gate_report.md
```

Quick triage gate:

```powershell
python scripts/release_gate_check.py --quick --output docs/audit-artifacts/release_gate_quick_report.md
```

Payment blocker gate:

```powershell
python -m pytest tests/test_api_payments_callbacks.py -q
```

Payment/support/bonus adjacent gates:

```powershell
python -m pytest tests/test_bot_paywall.py tests/test_tickets_repo.py tests/test_reviews_username_masking.py -q
python -m pytest tests/test_worker_retention.py tests/test_free_cycle_service.py -q
python scripts/api_lifecycle_smoke.py
```

Client preflight and tests:

```powershell
python scripts/client_security_smoke.py
python scripts/run_client_release_gate.py preflight
python scripts/run_client_release_gate.py test --suite full
```

Client artifact gates:

```powershell
python scripts/run_client_release_gate.py build --target windows
python scripts/run_client_release_gate.py build --target android-apk
python scripts/run_client_release_gate.py build --target android-aab
```

Full report with platform build gates, only when physical Android hardware is ready:

```powershell
set ANDROID_AUDIT_SERIAL=<physical-device-serial>
python scripts/release_gate_check.py --client-platform-gates windows,android-apk,android-aab --output docs/audit-artifacts/release_gate_report.md
```

Standalone Android physical-device audit:

```powershell
python scripts/android_localhost_audit.py --serial <physical-device-serial> --connect-wait-sec 30 --disconnect-wait-sec 15
```

Frontend focused gates:

```powershell
cd C:\Users\kiwun\Documents\ai\VPN\marketing
npm.cmd run check:seo
npm.cmd run build
cd C:\Users\kiwun\Documents\ai\VPN
python scripts/check-links.py
python scripts/ui_visual_smoke.py
cd C:\Users\kiwun\Documents\ai\VPN\webapp
npm.cmd run build
npm.cmd run test:e2e
npm.cmd run test:e2e:admin
```

Release orchestrator local gate:

```powershell
python scripts/release_orchestrator.py --gates-only
```

Deploy/verify contour, only after release captain approval and access:

```powershell
python scripts/release_orchestrator.py --brain-ip 82.21.114.104 --release-metadata-file <POKROV-app release-handoff.json>
```

## Evidence links

Confirmed existing evidence:

- `docs/audit-artifacts/release_gate_report.md` - PASS generated `2026-04-23 01:25:35`; stale for active client-lane decision because it contains retired `external/client-fork/app` client evidence.
- `docs/developer/work-orders/2026-04-beta-release/05-release-gate-plan.md` - required gate and evidence structure.
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md` - client lane public cutover status.
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/implementation/client-release-backlog.md` - client public-release blockers.

Needed evidence before beta decision:

- Fresh `docs/audit-artifacts/release_gate_report.md` from current scripts and current active client root.
- Dedicated payment test output for `tests/test_api_payments_callbacks.py`.
- Client preflight output proving `POKROV-app` is the active gate root.
- Android physical-device localhost audit JSON, redacted and retained only in approved evidence locations.
- Signed/unsigned artifact status with beta limitations clearly labeled.
- Runtime handoff proof for app, bot, webapp, and marketing download surfaces.
- Redacted current-origin, brain-origin, and RU-origin check lines.
- Manual switch evidence: checkout disable, trial disable, download disable, Telegram bonus pause, payment webhook fulfillment pause.
- Required screenshots from the release gate plan, with sensitive data redacted.
