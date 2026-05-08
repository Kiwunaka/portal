# Runtime Link Sync Guard Evidence

- Generated: `2026-05-08`
- Scope: runtime `APP_*` handoff guard for GitHub Releases APK/EXE distribution
- Decision: `NO RUNTIME SYNC`
- Classification: `BLOCKED_BY_ACCESS`

## What Was Checked

Dry-run command:

```powershell
python scripts\remote_brain_apply_release_handoff.py --brain-ip 82.21.114.104 --metadata-file docs\audit-artifacts\staged-client-apps-2026-05-07.json --dry-run
```

Result:

- `APP_ANDROID_PLAY_URL`: empty
- `APP_ANDROID_APK_URL`: `https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-android-universal.apk`
- `APP_WINDOWS_EXE_URL`: `https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-windows-setup-x64.exe`
- `APP_DOCS_URL`: `https://pokrov.space/install/`
- No SSH connection, env write, or service restart was performed.

Blocked mutation command:

```powershell
python scripts\remote_brain_apply_release_handoff.py --brain-ip 82.21.114.104 --metadata-file docs\audit-artifacts\staged-client-apps-2026-05-07.json
```

Result:

- Exit: non-zero
- Message: `GO evidence file is required for runtime APP_* sync`
- No runtime `APP_*` sync was authorized.

## Required Operator Input Before Sync

Runtime sync may only proceed after a dated evidence file explicitly contains:

- `RUNTIME LINK SYNC GO FOR APP-DOWNLOAD SMOKE`
- `OPERATOR_APPROVED_RUNTIME_LINK_SYNC=true`
- `STAGED GITHUB ASSET REACHABILITY GREEN`
- `NO PUBLIC ANNOUNCEMENT`
- `PAID CHECKOUT REMAINS CLOSED`

The evidence file must not contain:

- `NO RUNTIME SYNC OR ANNOUNCEMENT`

Public announcement and paid checkout remain blocked after any narrow runtime-link sync until their own gates are green.
