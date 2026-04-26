# Release Gate Plan

Status: active  
Date: 2026-04-26

## Scope Rule

This plan verifies Open Beta v4 preparation. It does not authorize public release until external evidence gates move from `blocked by missing access` to `pass`.

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
| Payment provider | Lava.top order, webhook auth, replay, invalid auth, failure states | blocked by missing access |
| Telegram download | `runtime_app_download_smoke.py --redact` with env-only init data | blocked by missing access |
| RU-origin | external RU probe report for POKROV and Telegram split | blocked by missing access |
| Android physical audit | `android_localhost_audit.py` on physical release-installed build | blocked by missing access |
| Brain-origin | predeploy or brain network probe with redacted access | blocked by missing access |

## Evidence Rules

- Store only redacted logs under `evidence/`.
- Never paste provider API keys, Telegram init data, SSH material, raw session tokens, QR codes, or subscription links into markdown.
- Every remote result must identify origin as `current-origin`, `brain-origin`, or `RU-origin`.
- A blocked gate is an honest result, not a failure to hide.
