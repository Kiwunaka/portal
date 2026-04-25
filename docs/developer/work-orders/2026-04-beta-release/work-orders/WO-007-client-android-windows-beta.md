# WO-007 Android/Windows Beta Client

Status: draft
Lane: client

## Scope

Make `POKROV-app/main` beta-ready for Android internal APK and Windows gated beta artifact.

## Assigned Paths

- `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/**`
- `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/**`
- `C:/Users/kiwun/Documents/ai/POKROV-app/packages/**`
- `C:/Users/kiwun/Documents/ai/POKROV-app/config/**`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/**`
- `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/**` for beta evidence only

## Required Behavior

- App-first onboarding: try free, login/link, redeem, checkout handoff.
- Runtime: managed profile fetch, connect/disconnect, runtime health, safe diagnostics.
- Routing: `All except RU`, `Full tunnel`, selected apps MVP status explicit.
- UX: no protocol/raw config/local-control first layer.
- Version label: `0.x.x-beta`.
- Support/download handoff safe and beta-labeled.

## Artifact Policy

- Android APK may be shown only to approved beta users and must be labeled internal beta.
- If physical localhost audit is missing, Android status is `internal test only / public blocked`.
- AAB/Play path must not be shown as live unless approved.
- Unsigned Windows build may be shown only to approved beta users.
- Windows UI must warn about SmartScreen/unknown publisher.
- Public approved remains `no` until trusted signing/handoff is ready.

## Validation

```powershell
cd C:\Users\kiwun\Documents\ai\POKROV-app
powershell -ExecutionPolicy Bypass -File .\scripts\validate-seed.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-workspace.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\fetch-libcore-assets.ps1 -Platforms @('windows','android') -SyncToHosts -Force
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1
```

From platform root:

```powershell
python scripts/client_security_smoke.py
python scripts/run_client_release_gate.py test --suite full
python scripts/run_client_release_gate.py build --target windows
python scripts/run_client_release_gate.py build --target android-apk
```

Physical Android publication gate requires explicit serial and is not optional for public cutover.

## Handoff Format

- What I checked
- What I found
- What I changed
- How I verified
- What remains / risk

