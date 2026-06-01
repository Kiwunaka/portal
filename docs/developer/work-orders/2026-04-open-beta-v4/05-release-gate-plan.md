# Release Gate Plan

Status: active  
Date: 2026-05-26

## Scope Rule

This plan verifies Open Beta v4 and later release-candidate handoffs.

Current decision:

- The outside-store Android + Windows public beta is authorized as `GO` from the `2026-05-15` evidence pack.
- Future stable, store, trusted-signing, RU-origin, and raw Android-device claims require fresh exact-candidate evidence.
- For the current local agent goal, checks that require owner hardware/accounts, real Telegram/WebApp users, provider dashboards, signing identities, store access, live deploy approval, or RU probe access are recorded as explicit manual/skip/block labels instead of stopping docs/code synchronization.

## Local Platform Gates

```powershell
python -m pytest tests/test_public_copy_guardrails.py -q
python -m pytest tests/test_release_gate_check.py -q
python scripts/client_security_smoke.py
python scripts/api_lifecycle_smoke.py
python scripts/check-links.py
python scripts/admin_webapp_smoke.py
python scripts/ui_visual_smoke.py
```

## Frontend Gates

```powershell
Push-Location marketing
npm.cmd run build
Pop-Location

Push-Location webapp
npm.cmd run build
npm.cmd run test:e2e
Pop-Location
```

## Client Gates

```powershell
$env:POKROV_APP_ROOT="C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\open-beta-v4"
python scripts/run_client_release_gate.py preflight
python scripts/run_client_release_gate.py test --suite full
```

## Physical Android Gate

Run only with a physical device and a release-installed build:

```powershell
$env:ANDROID_AUDIT_SERIAL="<physical-device-serial>"
$env:ANDROID_AUDIT_PACKAGE="space.pokrov.pokrov_android_shell"
python scripts/android_localhost_audit.py --serial $env:ANDROID_AUDIT_SERIAL --package $env:ANDROID_AUDIT_PACKAGE --connect-wait-sec 30 --disconnect-wait-sec 15
python scripts/release_gate_check.py --client-platform-gates android-apk,android-aab
```

## External Evidence Gates

| Gate | Required proof | Current label |
| --- | --- | --- |
| Payment provider | Lava.top order, webhook auth, replay, invalid auth, failure states | PASS for beta; production refund/chargeback/reconciliation follow-up |
| Telegram download | `runtime_app_download_smoke.py --redact` with env-only init data | PASS with brain-signed synthetic init data; real-user Telegram WebApp opening is `MANUAL_OWNER_TEST` |
| RU-origin | external RU probe report for POKROV and Telegram split | SKIPPED_BY_OPERATOR for beta; do not claim RU readiness |
| Android physical audit | `android_localhost_audit.py` on physical release-installed build | OPERATOR_ATTESTED for beta; raw evidence is `MANUAL_OWNER_TEST` |
| Brain-origin | predeploy or brain network probe with redacted access | PASS for 2026-05-15 beta evidence pack |
| Store/trusted release | Google Play / Microsoft Store / trusted Windows signing evidence | NOT_REQUESTED for beta; blocked for store or trusted claims |

## Evidence Rules

- Store only redacted logs under `evidence/`.
- Never paste provider API keys, Telegram init data, SSH material, raw session tokens, QR codes, or subscription links into markdown.
- Every remote result must identify origin as `current-origin`, `brain-origin`, or `RU-origin`.
- A blocked gate is an honest result, not a failure to hide.
- An accepted skip or owner attestation is an honest beta label, not a stable-release pass.
