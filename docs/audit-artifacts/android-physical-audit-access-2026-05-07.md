# Android Physical Audit Access

Generated: 2026-05-07 19:31 MSK

## Verdict

BLOCKED_BY_ACCESS.

The Android release-build localhost/control-surface audit could not run because no physical adb device is available in the current workspace session.

## What I Checked

- `ANDROID_AUDIT_SERIAL`: absent.
- `ANDROID_HOME`: `C:\Users\kiwun\AppData\Local\Android\Sdk`.
- `ANDROID_SDK_ROOT`: `C:\Users\kiwun\AppData\Local\Android\Sdk`.
- PATH `adb`: `C:\Windows\adb.exe`, version metadata `0.0.0.0`; `adb devices -l` returned no usable device rows.
- SDK adb: `C:\Users\kiwun\AppData\Local\Android\Sdk\platform-tools\adb.exe`; first run restarted the server because the server/client versions differed, then `devices -l` returned only `List of devices attached` with no devices.
- `python scripts\android_localhost_audit.py --require-release-build --release-evidence "local app-release.apk built by scripts/run_client_release_gate.py build --target android-apk on 2026-05-07" --output docs\audit-artifacts\android-localhost-audit-2026-05-07.json` failed before collecting an audit report with: `Expected exactly one connected adb device or pass --serial explicitly`.

## Classification

- Android physical release-build localhost/control-surface audit: `BLOCKED_BY_ACCESS`.
- Missing input needed to unblock: a connected physical Android device visible to SDK adb, or an explicit `ANDROID_AUDIT_SERIAL` / `--serial` for an already connected device.
