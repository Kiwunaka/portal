# Paid Beta Signoff

Status: `blocked`
Date: 2026-04-25
Captain: W10

## Decision

POKROV is not approved for paid beta onboarding in this pass.

Do not:

- deploy this candidate
- push as release-ready
- open paid checkout
- distribute Android or Windows beta artifacts
- onboard paid beta users
- announce payment availability

## Summary

The current candidate has strong local progress across backend, webapp, admin, marketing, payment regression tests, client tests, and local Android/Windows builds. A post-W10 orchestrator follow-up reconciled stale gate expectations and the default local release gate is now green.

Paid beta remains blocked because several P0 live/operator proofs required by the beta gate plan are still missing.

Final decision: `blocked`.

## Gate Evidence

| Area | Status | Evidence |
|---|---|---|
| Full local release report | `PASS` | `docs/audit-artifacts/release_gate_report.md` generated 2026-04-25 02:12:51 |
| Quick local release report | `PASS` | `docs/audit-artifacts/release_gate_quick_report.md` generated 2026-04-25 02:04:24 |
| Backend release matrix | `PASS` | `52 passed` in full release report |
| Admin/auth regression | `PASS` | `57 passed` in full release report |
| Supplemental payment/auth regression | `PASS` | `79 passed` in W10 run |
| API lifecycle smoke | `PASS` | full release report |
| Public link checks | `PASS` | full release report |
| Marketing build | `PASS` | full release report |
| Admin webapp smoke | `PASS` | full release report |
| WebApp build | `PASS` | full release report |
| WebApp Playwright E2E | `PASS` | `31 passed` in full release report |
| Client Flutter tests | `PASS` | full release report |
| Client security smoke | `PASS` | beta Windows metadata expectation reconciled |
| UI visual smoke | `PASS` | webapp entry/dashboard expectations reconciled |
| Android APK build | `PASS` | local build command completed |
| Android AAB build | `PASS` | local build command completed |
| Windows build | `PASS` | `pokrov_windows_beta.exe` built and staged locally |
| Android physical audit | `BLOCKED_BY_ACCESS` | no attached device |
| Runtime app-download smoke | `SKIPPED_NO_LIVE_TOKEN` | no live beta token used |
| brain-origin check | `BLOCKED_BY_ACCESS` | no approved live access used |
| RU-origin check | `BLOCKED_BY_ACCESS` | no external RU probe run |

## Platform Status

Marketing, cabinet, and admin surfaces have local build, browser, public-copy, link-check, and visual-smoke evidence. This is local evidence only and does not prove live production deployment.

Backend local regression evidence is substantially green, including payment callback state handling. Live Postgres migration/profile delivery and provider webhook behavior remain unproven.

## Payment Status

Local payment callback/idempotency regression passed. This does not prove live paid beta readiness.

Still blocked:

- provider category/product acceptance
- live signed webhook behavior
- controlled low-volume payment or sandbox proof
- refund/chargeback operational path beyond admin-visible records
- decision on manual-risk acceptance if provider proof remains unavailable

## Android Status

Status: `internal evidence only / public blocked`

Local APK and AAB builds completed. Android remains blocked for public or paid-beta distribution because:

- no physical release-build localhost/control-surface audit ran
- no trusted signing proof was captured
- no runtime download handoff proof was captured
- no live connect/routing/DNS proof was captured

## Windows Status

Status: `unsigned gated beta artifact built / public blocked`

Windows local build now produces and stages `pokrov_windows_beta.exe`. It may only be distributed as a gated beta artifact after download authorization/handoff is verified, with a clear SmartScreen or unknown-publisher warning.

## Current-Origin Check

Read-only public host checks from the operator workstation passed:

- `https://pokrov.space/` returned `200`
- `https://app.pokrov.space/` returned `200`
- `https://api.pokrov.space/api/health` returned `200`
- `https://connect.pokrov.space/` returned `308`
- `https://pay.pokrov.space/checkout/` returned `200`

This is not deploy proof and does not replace brain-origin or RU-origin checks.

## Accepted Limitations

No new paid-beta limitations are accepted by W10 because P0 blockers remain.

Already-known limitations that remain true:

- Android is not public-ready.
- Windows is not trusted-signed.
- Email continuation remains not live by default.
- Support target is best-effort within 24h, not an SLA.
- Beta remains invite-limited to a maximum of 25 active users after approval.

## Blockers

1. Android physical release-build localhost/control-surface audit is missing.
2. Live provider acceptance and signed webhook proof are missing.
3. Runtime app-download smoke is skipped because no live token was used.
4. brain-origin and RU-origin checks are blocked.
5. Backup, deploy, rollback, and emergency-switch evidence are missing.
6. Trusted Android and Windows signing/public cutover proof is missing.

## Rollback Plan

No deploy was performed, so no runtime rollback is needed from W10.

Before a future deploy:

- capture current deployed commit/package path
- capture DB backup timestamp if migrations are included
- capture static-site rollback source
- capture release-handoff rollback source for artifact URLs
- verify emergency switches for checkout, trials, downloads, bonus claims, and webhook fulfillment
- document exact rollback commands and post-rollback checks

## Support Checklist Before Reattempt

- Cabinet ticket flow verified with a live beta account.
- Telegram support fallback copy ready.
- Admin can inspect payment, access, device, and ticket context.
- Admin manual reconciliation requires an audit note.
- Support does not ask users to paste raw configs or secrets.
- Evidence redaction rules are enforced for screenshots, logs, payment IDs, Telegram IDs, and connection links.

## Final Decision

`blocked`

## Post-W10 Orchestrator Follow-Up

After W10 signoff, the orchestrator fixed stale gate expectations for the beta Windows binary name and updated content-aware UI smoke expectations for the current cabinet implementation.

Commands now green:

- `python scripts/client_security_smoke.py`
- `powershell -ExecutionPolicy Bypass -File .\scripts\validate-seed.ps1` in `C:\Users\kiwun\Documents\ai\POKROV-app`
- `python scripts/ui_visual_smoke.py`
- `python scripts/run_client_release_gate.py build --target windows`
- `python scripts/release_gate_check.py --quick --output docs/audit-artifacts/release_gate_quick_report.md`
- `python scripts/release_gate_check.py --output docs/audit-artifacts/release_gate_report.md`

This changes the local gate state from red to green, but does not change the final paid-beta decision because live/operator P0 proofs remain missing.
