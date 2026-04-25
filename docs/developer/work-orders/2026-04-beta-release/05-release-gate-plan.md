# Release Gate Plan

Status: W10 executed; post-W10 local gate follow-up completed. Final paid beta decision remains `blocked` until live/operator blockers below are resolved or explicitly accepted by the orchestrator.

## W10 Gate Result

Final local gate evidence from `2026-04-25`:

| Check | Result | Evidence |
|---|---|---|
| Quick release report | `PASS` | `docs/audit-artifacts/release_gate_quick_report.md` generated 2026-04-25 02:04:24 |
| Default/full local release report | `PASS` | `docs/audit-artifacts/release_gate_report.md` generated 2026-04-25 02:12:51 |
| Supplemental auth/payment regression | `PASS`, `79 passed` | `evidence/release-gates/W10-final-gate-summary.md` |
| Android APK build | `PASS`, local release APK built | `evidence/release-gates/W10-final-gate-summary.md` |
| Android AAB build | `PASS`, local release AAB built | `evidence/release-gates/W10-final-gate-summary.md` |
| Windows build | `PASS` | post-W10 build staged `pokrov_windows_beta.exe` |
| Android physical audit | `BLOCKED_BY_ACCESS` | no attached device from `adb devices -l` |
| current-origin public host check | `PASS` | `pokrov.space`, `app.pokrov.space`, `api.pokrov.space/api/health`, `connect.pokrov.space`, and `pay.pokrov.space/checkout/` responded from the operator workstation |
| brain-origin check | `BLOCKED_BY_ACCESS` | live SSH/API access not used in this pass |
| RU-origin check | `BLOCKED_BY_ACCESS` | no healthy external RU probe run in this pass |

Local gate follow-up completed:

- `python scripts/client_security_smoke.py` passes after beta Windows metadata expectation update.
- `python scripts/ui_visual_smoke.py` passes after current cabinet structure expectation update.
- `python scripts/run_client_release_gate.py build --target windows` passes and stages `pokrov_windows_beta.exe`.

Decision implication:

- Do not deploy.
- Do not push.
- Do not onboard paid beta users.
- Android may remain internal-test artifact evidence only; public Android remains blocked.
- Windows beta distribution remains blocked until cabinet-gated handoff is verified and the unsigned warning remains in place.

## Quick Gate

Use for inner-loop beta readiness triage:

```powershell
python scripts/release_gate_check.py --quick --output docs/audit-artifacts/release_gate_quick_report.md
```

Supplement quick gate for paid beta payment risk:

```powershell
python -m pytest tests/test_api_payments_callbacks.py -q
```

## Full Gate

Use before beta decision:

```powershell
python scripts/release_gate_check.py --output docs/audit-artifacts/release_gate_report.md
```

Required supplemental paid beta gates:

```powershell
python -m pytest portal_bot/tests/test_app_first_api.py -q
python -m pytest tests/test_portal_api.py tests/test_api_auth_and_tickets.py tests/test_api_payments_callbacks.py -q
python -m pytest tests/test_worker_retention.py tests/test_free_cycle_service.py -q
python -m pytest tests/test_public_copy_guardrails.py tests/test_ui_visual_smoke.py -q
python scripts/check-links.py
python scripts/admin_webapp_smoke.py
python scripts/client_security_smoke.py
python scripts/api_lifecycle_smoke.py
```

The default full gate is not sufficient for paid beta signoff unless payment callback/idempotency, admin reconciliation, and copy guardrail evidence are included.

## Client Platform Gates

```powershell
python scripts/run_client_release_gate.py test --suite full
python scripts/run_client_release_gate.py build --target windows
python scripts/run_client_release_gate.py build --target android-apk
```

Android publication-level gate requires a physical serial:

```powershell
set ANDROID_AUDIT_SERIAL=<physical-device-serial>
python scripts/android_localhost_audit.py --serial %ANDROID_AUDIT_SERIAL% --connect-wait-sec 30 --disconnect-wait-sec 15
```

Android public approval is blocked until the physical-device audit passes with a release build. Android internal APK can be accepted only as a marked, cabinet-gated beta limitation.

## Marketing And WebApp Gates

```powershell
cd marketing
npm.cmd run build
npm.cmd run check:seo

cd ..\webapp
npm.cmd run build
npm.cmd run test:e2e
npm.cmd run test:e2e:admin
```

These must be run after W01-W04 and W06 update public copy, cabinet continuation, admin, checkout, and artifact states.

## P0 Payment Gates

- Tariff catalog matches checkout UI.
- Successful payment creates exactly one entitlement.
- Duplicate webhook does not double-extend access.
- Failed payment does not create access.
- Refunded/cancelled payment is visible to admin.
- Unknown provider event goes to `manual_review`, not silent success.
- Payment record is visible in user profile/admin.
- Admin can manually reconcile low-volume beta payments with audit note.
- User receives a clear next step after payment.
- Payment logs do not expose secrets, tokens, card data, private webhook payloads, or full identifiers.
- Provider category acceptance and webhook verification are confirmed or explicitly accepted as manual beta risk.

## Manual Gates

- Invite list capped at 25 active users.
- Checkout disable switch verified.
- Trial disable switch verified.
- Artifact download disable switch verified.
- Telegram bonus pause verified.
- Payment webhook fulfillment pause verified.
- Manual extend/revoke beta access verified in admin.
- Maintenance/unavailable UI verified.
- Support best-effort 24h wording verified.
- Cabinet download states verified as available, coming soon, blocked, or internal-only.
- Android internal APK warning verified.
- Windows unsigned/SmartScreen warning verified.
- Support ticket creation and continuation verified.
- Telegram fallback support instructions verified.

## Live Checks Policy

- Live production-domain checks are read-only unless the WO explicitly authorizes a low-volume write test.
- Payment live test must use a controlled beta account and minimal real/sandbox amount where supported.
- All live evidence must be redacted.
- Do not print secrets, tokens, private webhook payloads, personal payment data, raw subscription links, private IPs, or full user identifiers.
- Screenshots must hide emails, Telegram IDs, payment IDs, and personal connection links unless stored in a protected internal evidence location.

## Deploy And Rollback Gate

Deploy is allowed only after:

- Core gates are green or explicitly classified.
- DB backup is completed if migrations are included.
- Rollback command/path is documented.
- Current deployed version is captured.
- New version/artifact identifiers are captured.
- Low-volume payment/webhook test is run or explicitly deferred with risk.
- Admin can disable checkout/downloads after deploy.
- Emergency controls are verified.

If migration is included:

- Backup timestamp is recorded.
- Migration command is documented.
- Migration result is captured.
- Post-migration smoke is run.
- Rollback feasibility is recorded.
- Destructive schema changes are prohibited unless separately approved by the orchestrator.

If deploy fails:

- Mark the wave blocked or RC-only.
- Do not onboard paid beta users.
- Record the exact failed gate and rollback state.

## Promotion Safety

- Before push/deploy, capture current local HEAD and remote HEAD.
- If platform branch is behind `origin/master`, do not force-push or overwrite remote changes.
- If client branch is behind `origin/main`, do not force-push or overwrite remote changes.
- Orchestrator must decide merge/rebase/cherry-pick strategy after gates.
- Deploy may use a local dirty beta candidate only if the exact commit/patch state is captured and rollback is documented.

## Visual Gates

Required screenshots before signoff:

- marketing homepage
- checkout
- install
- cabinet overview
- tariffs/payment
- devices/downloads
- support/diagnostics
- admin users/subscriptions
- admin nodes/routes
- admin tickets/incidents/SLA
- Android shell
- Windows shell

## Security Gates

- Payment logs redacted.
- Screenshots redacted.
- No secrets in evidence.
- No raw subscription links in normal user UI.
- Admin auth gate green.
- Android local-control audit classified.
- Support diagnostics safe.
- Activation/redeem links do not leak raw secrets through public URLs.
- Admin-only sensitive details are not visible in normal user UI.
- Dependency/security audit findings are classified.

## Required Evidence

- `evidence/logs/*`
- `evidence/release-gates/*`
- `evidence/screenshots/*`
- `evidence/visual-audit/*`
- `evidence/security-audit/*`
- `docs/audit-artifacts/release_gate_report.md`
- local and remote HEAD capture before push/deploy
- DB backup and migration evidence when applicable
- redacted live check notes
- artifact metadata: platform, version, build number, build type, created time, source branch/commit, signing status, checksum, limitations, URL, rollback URL if available

## Go / No-Go Thresholds

`beta-ready` requires all P0 gates green, payment/support/admin/downloads/emergency controls verified, and docs/copy matching beta limitations.

`beta-ready with accepted limitations` requires core flows green, noncore failures classified, Android public cutover blocked but internal APK acceptable, Windows unsigned warning accepted, and no fake modules or fake claims.

`blocked` applies if payment grants wrong/double access, activation fails, managed profile delivery fails, both client connect paths are blocked, admin auth fails, support ticket flow fails, production deploy fails, rollback is unknown, or public UI contains unsafe claims/fake availability.
