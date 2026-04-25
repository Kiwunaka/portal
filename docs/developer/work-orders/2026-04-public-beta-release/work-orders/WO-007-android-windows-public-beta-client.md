# WO-007 Android/Windows Public Beta Client

Status: draft
Agent: W07
Lane: client
Priority: P0/P1

## Goal

Prepare the active `POKROV-app/main` client lane for truthful Android/Windows public beta status, with release metadata, artifact checks, warnings, and explicit blockers.

## Write Scope

- `C:/Users/kiwun/Documents/ai/POKROV-app/**`
- platform wrapper files only when needed:
  - `scripts/run_client_release_gate.py`
  - `scripts/client_security_smoke.py`
  - `docs/operations/publishing-and-signing-guide.md`
  - `docs/developer/work-orders/2026-04-public-beta-release/**`

## Acceptance

- Android remains blocked/internal-only unless signing plus physical audit evidence exists.
- Windows beta artifact has metadata, checksum path, and unsigned warning when applicable.
- Public version label stays `0.x.x-beta`.
- Client docs reflect active lane truth.
- Release handoff metadata is not split across ad hoc folders.

## Validation

```powershell
cd C:/Users/kiwun/Documents/ai/POKROV-app
powershell -ExecutionPolicy Bypass -File ./scripts/validate-seed.ps1
powershell -ExecutionPolicy Bypass -File ./scripts/run-tests.ps1

cd C:/Users/kiwun/.config/superpowers/worktrees/VPN/public-beta-release-wave
python scripts/client_security_smoke.py
python scripts/run_client_release_gate.py test --suite full
python scripts/run_client_release_gate.py build --target windows
python scripts/run_client_release_gate.py build --target android-apk
python scripts/run_client_release_gate.py build --target android-aab
```

