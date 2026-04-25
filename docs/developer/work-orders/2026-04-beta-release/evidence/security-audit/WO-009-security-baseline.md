# WO-009 Security Baseline

Status: first-pass baseline
Agent: W09
Last updated: 2026-04-25
Scope: paid beta security, privacy, abuse, and compliance evidence for the platform repo and active `POKROV-app` client lane.

## Scope Guardrails

- Write scope honored: this file only.
- No edits were made to `portal_bot/api.py`, webapp code, marketing code, or client code.
- Secret-bearing files and folders were not read or printed: `portal_bot/.env`, `VPN NODE SSH KEYS/`, `secrets for merchant/`, signing keys, and sensitive `ops-local/` material.
- `rg` was unavailable on this workstation with `Access is denied`; tracked-source searches used `git grep`.
- Claims below use repository evidence, required research artifacts, and local non-secret validation commands only.

## Sources Checked

- `docs/developer/work-orders/2026-04-beta-release/00-orchestrator-context.md`
- `docs/developer/work-orders/2026-04-beta-release/INDEX.md`
- `docs/developer/work-orders/2026-04-beta-release/01-research-synthesis.md`
- `docs/developer/work-orders/2026-04-beta-release/research/R09-infra-observability-security.md`
- `docs/developer/work-orders/2026-04-beta-release/research/R10-qa-release-docs.md`
- `docs/developer/work-orders/2026-04-beta-release/work-orders/WO-009-security-privacy-abuse-compliance.md`
- Canonical platform docs: `docs/README.md`, `docs/product/portal-vpn-product.md`, `docs/architecture/system-overview.md`, `docs/architecture/app-first-and-bonus-flows.md`, `docs/operations/deployment-and-access.md`, `docs/operations/monitoring-and-visibility.md`, `docs/operations/publishing-and-signing-guide.md`, `docs/developer/developer-guide.md`, `docs/developer/repository-map.md`
- Active client docs: `C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md`, `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md`
- Read-only source searches over tracked platform and active client files.

## P0 Findings

| ID | Finding | Evidence | Proposed owner WO | Recommended validation |
| --- | --- | --- | --- | --- |
| W09-P0-001 | Android public release remains blocked until a release-installed physical device proves there is no unauthenticated localhost proxy, DNS, command, Clash/API, or admin/control surface reachable before connect, after connect, and after disconnect. The static client smoke passed, but it is explicitly not the release-build audit. | `research/R09-infra-observability-security.md` Key Blockers 2 and Local Control Surfaces; `research/R10-qa-release-docs.md` P0 blockers 3-4; `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md:48-50`; `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/android/app/build.gradle:36-39`; `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/android/app/src/main/AndroidManifest.xml:42-44`; local `python scripts/client_security_smoke.py` passed on 2026-04-25. | WO-007 primary, WO-009 audit, WO-010 signoff | `python scripts/client_security_smoke.py`; with release build installed on physical hardware: `python scripts/android_localhost_audit.py --serial <physical-device-serial> --connect-wait-sec 30 --disconnect-wait-sec 15`; final report: `set ANDROID_AUDIT_SERIAL=<physical-device-serial>` then `python scripts/release_gate_check.py --client-platform-gates windows,android-apk,android-aab --output docs/audit-artifacts/release_gate_report.md` |
| W09-P0-002 | Payment integrity evidence is not green for paid beta. Signature and idempotency code/tests exist, but the local W09 run of `tests/test_api_auth_and_tickets.py tests/test_api_payments_callbacks.py` failed in the payment callback suite, so paid-beta evidence cannot treat the payment gate as passed. | `research/R07-payments-telegram-support.md` referenced by synthesis as provider/webhook blocker; `research/R10-qa-release-docs.md` P0 blockers 2 and Security/privacy risks; `portal_bot/api.py:2771-2835`, `portal_bot/api.py:3153-3180`, `tests/test_api_payments_callbacks.py:146`, `tests/test_api_payments_callbacks.py:189`, `tests/test_api_payments_callbacks.py:200`, `tests/test_api_payments_callbacks.py:266`; local validation on 2026-04-25: `1 failed, 75 passed` with failure in `tests/test_api_payments_callbacks.py::ApiPaymentCallbacksTests::test_generic_create_public_order_uses_selected_provider` due a plan-description expectation mismatch at `tests/test_api_payments_callbacks.py:678-687`. | WO-006 primary, WO-005 backend contract, WO-010 release gate | `python -m pytest tests/test_api_auth_and_tickets.py tests/test_api_payments_callbacks.py -q`; add/retain this suite in final paid-beta evidence; live provider webhook proof remains blocked until provider dashboard/access is available. |
| W09-P0-003 | Fresh full release-gate evidence is missing for the current dirty candidate and active client lane. Existing green evidence is stale and not enough for security signoff because the active client truth moved to `C:/Users/kiwun/Documents/ai/POKROV-app`. | `research/R09-infra-observability-security.md` Key Blocker 1; `research/R10-qa-release-docs.md` Current state and P0 blockers 1; `docs/audit-artifacts/release_gate_report.md` is historical only per R09/R10; platform `git status --short --branch` showed current branch `codex/beta-release-platform` with concurrent dirty changes; client `git status --short --branch` showed `codex/beta-release-client` plus untracked release-handoff artifacts. | WO-010 primary, all implementation WOs feed evidence | `python scripts/release_gate_check.py --output docs/audit-artifacts/release_gate_report.md`; `python scripts/release_orchestrator.py --gates-only`; after release-captain approval, collect redacted current-origin, brain-origin, and RU-origin evidence separately. |

## P1 Findings

| ID | Finding | Evidence | Proposed owner WO | Recommended validation |
| --- | --- | --- | --- | --- |
| W09-P1-001 | Web sessions use a browser bearer token in `localStorage`. This is probably acceptable only for invite-limited beta with strong XSS discipline and short-lived tokens; it should be hardened before broader public paid traffic. | `research/R09-infra-observability-security.md` Admin/API Auth And Web Session Security; `webapp/src/lib/api.ts:5`, `webapp/src/lib/api.ts:1234`, `webapp/src/lib/api.ts:1276`, `webapp/src/lib/api.ts:1302`; `portal_bot/web_auth_service.py:126-166`, `portal_bot/web_auth_service.py:238-267`; `tests/test_api_auth_and_tickets.py:1218`. | WO-003 webapp, WO-005 auth contract, WO-009 audit | `python -m pytest tests/test_api_auth_and_tickets.py -q`; targeted browser review for token persistence, logout clearing, XSS sinks, and session expiry; consider HttpOnly Secure SameSite cookie migration or explicit beta acceptance. |
| W09-P1-002 | CORS is configured with wildcard origins. With bearer-token authorization this is a hardening gap, especially as more browser continuation paths go live. | `portal_bot/api.py:1367-1368`; canonical hosts listed in `docs/operations/monitoring-and-visibility.md` Canonical Hostname Policy; web API bearer behavior at `webapp/src/lib/api.ts:1259`. | WO-005 backend, WO-003 webapp, WO-009 audit | Add/confirm CORS allowlist tests for `https://pokrov.space`, `https://app.pokrov.space`, Telegram WebView contexts if required, and rejection of arbitrary origins; run `python -m pytest tests/test_api_auth_and_tickets.py -q`. |
| W09-P1-003 | Support uploads are authenticated at upload time, but uploaded files are mounted as static bearerless URLs once the generated filename is known. This is a privacy risk for screenshots/logs and should be tightened or explicitly limited for beta. | `research/R09-infra-observability-security.md` Privacy-Safe Diagnostics; `portal_bot/api.py:303-305`, `portal_bot/api.py:1374`, `portal_bot/api.py:3468`, `portal_bot/api.py:7117-7126`; `webapp/src/app/(dashboard)/support/thread/page.tsx:41`; `tests/test_api_auth_and_tickets.py:1262-1279`. | WO-003 support UI, WO-005 backend, WO-009 audit | `python -m pytest tests/test_api_auth_and_tickets.py -q`; manual negative check that an unauthenticated request cannot fetch another user's attachment after upload, or document the beta limitation and retention/redaction rules. |
| W09-P1-004 | SSH helper scripts broadly use Paramiko `AutoAddPolicy()`, which accepts unknown host keys. This is an operator-path hardening issue before routine paid-beta deploy and incident workflows. | `research/R09-infra-observability-security.md` Secrets, SSH, And Sensitive Material; `scripts/node_access.py:117`; `scripts/verify_brain_ready.py:57`; many `scripts/remote_*` helpers also matched `AutoAddPolicy()` via tracked-source search. | WO-008 infra, WO-009 audit | Add known-hosts or pinned-host-key mode to shared SSH helper path; run `python -m pytest tests/test_node_access.py -q` and a non-secret operator known-hosts validation that does not print keys. |
| W09-P1-005 | Broad abuse throttling is not visible across auth, trial issuance, payment initiation, support upload, and ticket flows. Tracked evidence shows a diagnostics-only in-memory limiter, not a platform-wide abuse posture. | `research/R09-infra-observability-security.md` Rate Limiting, Abuse, And Fraud Basics; `research/R06-backend-api-data.md` referenced by synthesis for install-id trial abuse risk; `portal_bot/api.py:3908`, `portal_bot/api.py:6610-6613`; `tests/test_api_auth_and_tickets.py:1424-1429`. | WO-005 backend, WO-006 payments, WO-009 audit | Add focused abuse tests for start-trial, auth attempts, payment order creation, support upload, and ticket creation; run `python -m pytest portal_bot/tests/test_app_first_api.py tests/test_api_auth_and_tickets.py tests/test_api_payments_callbacks.py -q`. |
| W09-P1-006 | Evidence redaction is a release requirement, not just a reporting preference. Screenshots, logs, payment callbacks, support uploads, Android audit JSON, and origin reports can contain personal identifiers or connection material. | `00-orchestrator-context.md` Live Checks Policy; `01-research-synthesis.md` Security/Privacy Gaps; `research/R09-infra-observability-security.md` Metrics/Logs and Privacy-Safe Diagnostics; `scripts/remote_xui_logs.py:46`; `docs/operations/publishing-and-signing-guide.md` Android artifact-location note. | WO-009 primary, WO-010 evidence gate, all WOs producing evidence | Before final signoff, run a redaction review on promoted evidence only. Do not store raw secrets, raw subscription links, Telegram IDs, payment IDs, private webhook payloads, or full user identifiers in general docs. |

## Positive Evidence

- `python scripts/client_security_smoke.py` passed on 2026-04-25 and checked the active `POKROV-app` product contract, runtime profile, runtime artifacts, Android manifest, Android Gradle config, and Windows release seed.
- `python -m pytest tests/test_public_copy_guardrails.py -q` passed on 2026-04-25 with `5 passed`.
- Tracked secret-path scan found no tracked entries matching obvious local secret/signing patterns in the platform repo.
- Tracked secret-path scan in `POKROV-app` found only signing config placeholders: `apps/ios_shell/ios/Flutter/AppleSigning.xcconfig` and `apps/macos_shell/macos/Runner/Configs/AppleSigning.xcconfig`; no key material was printed.
- Payment callback code rejects invalid signatures by default when `PAYMENT_CALLBACK_TOLERANT_MODE=false`; example config also sets it false at `portal_bot/.env.example:56`.
- Android VPN service is non-exported and protected by `android.permission.BIND_VPN_SERVICE` in `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/android/app/src/main/AndroidManifest.xml:42-44`.

## Recommended Validation Commands

Run from `C:/Users/kiwun/Documents/ai/VPN` unless noted.

```powershell
python scripts/client_security_smoke.py
python -m pytest tests/test_api_auth_and_tickets.py tests/test_api_payments_callbacks.py -q
python -m pytest tests/test_public_copy_guardrails.py -q
python -m pytest portal_bot/tests/test_app_first_api.py tests/test_api_auth_and_tickets.py tests/test_api_payments_callbacks.py -q
python -m pytest tests/test_node_access.py tests/test_node_dataplane_probe.py tests/test_ru_probe_runner.py tests/test_render_ru_probe_report.py -q
python scripts/release_gate_check.py --output docs/audit-artifacts/release_gate_report.md
python scripts/release_orchestrator.py --gates-only
```

Physical Android hardware required:

```powershell
python scripts/android_localhost_audit.py --serial <physical-device-serial> --connect-wait-sec 30 --disconnect-wait-sec 15
set ANDROID_AUDIT_SERIAL=<physical-device-serial>
python scripts/release_gate_check.py --client-platform-gates windows,android-apk,android-aab --output docs/audit-artifacts/release_gate_report.md
```

Access-gated production/origin checks:

```powershell
python scripts/verify_brain_ready.py --brain-ip 82.21.114.104
python scripts/ru_probe_runner.py --reserve-host rf1.pokrov.space --probe-host mini --out ops-local/ru-probe.json
python scripts/render_ru_probe_report.py --input ops-local/ru-probe.json
```

## Validation Run In This Pass

| Command | Result | Notes |
| --- | --- | --- |
| `python scripts/client_security_smoke.py` | PASS | Static client security smoke passed against active `POKROV-app` paths. |
| `python -m pytest tests/test_api_auth_and_tickets.py tests/test_api_payments_callbacks.py -q` | FAIL | `1 failed, 75 passed`; failure is in the payment callback suite, `test_generic_create_public_order_uses_selected_provider`, due plan-description assertion drift. |
| `python -m pytest tests/test_public_copy_guardrails.py -q` | PASS | `5 passed`. |

## Release Decision Notes

- W09 should not mark security/privacy/abuse green while any P0 above remains open.
- Android may be considered only as an internal beta artifact until W09-P0-001 is closed or explicitly accepted as an internal-only limitation.
- Payment flows should not be considered paid-beta ready until W09-P0-002 is green and live provider webhook/signature behavior is verified or explicitly risk-accepted.
- Browser/session, CORS, support-upload, SSH host-key, and abuse-throttling items are P1 for an invite-limited beta only if the release captain accepts the limitation and the support/evidence redaction rules are enforced.
