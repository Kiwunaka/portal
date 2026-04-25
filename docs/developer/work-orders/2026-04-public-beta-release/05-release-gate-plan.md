# Release Gate Plan

Status: active-release-blocked

## P0 Core Gates

- public site builds
- public checkout works or is honestly disabled
- payment provider accepted or beta risk explicitly signed
- successful payment creates exactly one entitlement
- duplicate webhook does not double-extend access
- failed payment does not create access
- manual_review works
- admin can reconcile payment
- trial works or is consistently disabled
- redeem key works
- managed profile delivery works
- at least one public client path works
- Android not public unless audit/signing pass
- Windows artifact metadata/checksum exists
- cabinet downloads show truthful state
- cabinet support ticket works
- admin auth gate works
- admin critical modules are real
- emergency controls work
- node metrics show real data or explicit unavailable state
- public copy guardrails pass
- no fake modules/counters/actions
- no raw secrets/config/local-control surfaces in user UI
- deploy rollback path known
- production deploy smoke passes

## Minimum Platform Gates

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

## Marketing Gates

```powershell
cd marketing
npm.cmd run build
npm.cmd run check:seo
```

## WebApp Gates

```powershell
cd webapp
npm.cmd run build
npm.cmd run test:e2e
npm.cmd run test:e2e:admin
```

## Client Gates

```powershell
cd C:/Users/kiwun/Documents/ai/POKROV-app
powershell -ExecutionPolicy Bypass -File ./scripts/run-tests.ps1

cd C:/Users/kiwun/.config/superpowers/worktrees/VPN/public-beta-release-wave
python scripts/run_client_release_gate.py test --suite full
python scripts/run_client_release_gate.py build --target windows
python scripts/run_client_release_gate.py build --target android-apk
python scripts/run_client_release_gate.py build --target android-aab
```

## Android Physical Audit

```powershell
set ANDROID_AUDIT_SERIAL=<physical-device-serial>
python scripts/android_localhost_audit.py --serial %ANDROID_AUDIT_SERIAL% --connect-wait-sec 30 --disconnect-wait-sec 15
```

Without a physical serial and release-installed build, Android public release remains blocked.

2026-04-26 result: blocked because `adb devices` showed no physical device and `ANDROID_AUDIT_SERIAL` was not set. Evidence: `docs/audit-artifacts/android_physical_audit_2026-04-26.md`.

## Full Gate Report

```powershell
python scripts/release_gate_check.py --output docs/audit-artifacts/public_beta_release_gate_report.md
```

With platform build gates:

```powershell
set ANDROID_AUDIT_SERIAL=<physical-device-serial>
python scripts/release_gate_check.py --client-platform-gates windows,android-apk,android-aab --output docs/audit-artifacts/public_beta_release_gate_report.md
```

## Current Evidence Snapshot

| Gate | 2026-04-26 status | Evidence |
|---|---|---|
| current-origin default gate | PASS | `docs/audit-artifacts/public_beta_release_gate_report.md` |
| brain-origin quick gate | PASS | `docs/audit-artifacts/public_beta_release_gate_report_brain.md` |
| RU-origin canonical hosts / delivery nodes | PASS | `docs/audit-artifacts/ru_probe_2026-04-26.md` |
| RU-origin Telegram targets | FAIL | `docs/audit-artifacts/ru_probe_2026-04-26.md` |
| FreeKassa live order create | BLOCKED_BY_PROVIDER_STATUS | `docs/audit-artifacts/payment_provider_probe_2026-04-26.md` |
| Windows beta build | PASS | `docs/audit-artifacts/client_platform_builds_2026-04-26.md` |
| Android release APK/AAB build | PASS | `docs/audit-artifacts/client_platform_builds_2026-04-26.md` |
| Android physical release audit | BLOCKED_NO_PHYSICAL_DEVICE | `docs/audit-artifacts/android_physical_audit_2026-04-26.md` |
| runtime app download smoke | BLOCKED_NO_LIVE_TOKEN | `docs/audit-artifacts/runtime_app_download_smoke_2026-04-26.md` |

Do not promote or deploy public beta while any `BLOCKED` or `FAIL` row remains unresolved or explicitly de-scoped.
