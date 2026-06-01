# WO-007 Android/Windows Public Beta Client

Status: historical work order; current beta decision synced 2026-05-26
Owner: W07
Repo: POKROV-app worktree

## Scope

- `C:/Users/kiwun/.config/superpowers/worktrees/POKROV-app/open-beta-v4`.
- Android and Windows builds, checksums, release handoff, client UI, runtime diagnostics, and client docs.

## Acceptance

- Client tests pass.
- Android release build is generated when signing/build prerequisites allow.
- Windows release bundle is generated when local toolchain allows.
- Checksums and release-handoff manifest are updated for any generated artifact.
- Android physical audit passes on real hardware before any public Android claim.
- Known limitations are documented when gates remain blocked.

## Verification

```powershell
python scripts/run_client_release_gate.py preflight
python scripts/run_client_release_gate.py test --suite full
set ANDROID_AUDIT_SERIAL=<physical-device-serial>
python scripts/android_localhost_audit.py --serial %ANDROID_AUDIT_SERIAL% --connect-wait-sec 30 --disconnect-wait-sec 15
```
