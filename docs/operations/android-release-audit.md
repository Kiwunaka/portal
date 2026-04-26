# Android Release Audit

Last updated: 2026-04-26

Android public release is blocked until a physical release-installed build passes the localhost/control-surface audit.

Run only with a physical device:

```powershell
$env:ANDROID_AUDIT_SERIAL="<physical-device-serial>"
$env:ANDROID_AUDIT_PACKAGE="space.pokrov.pokrov_android_shell"
$env:ANDROID_AUDIT_RELEASE_EVIDENCE="<artifact/version/checksum>"
python scripts/android_localhost_audit.py --serial $env:ANDROID_AUDIT_SERIAL --package $env:ANDROID_AUDIT_PACKAGE --release-evidence $env:ANDROID_AUDIT_RELEASE_EVIDENCE --require-release-build --connect-wait-sec 30 --disconnect-wait-sec 15
```

The release gate will also pass `ANDROID_AUDIT_PACKAGE` and require `ANDROID_AUDIT_RELEASE_EVIDENCE` when Android platform gates are requested.

Evidence must include package name, build type, serial label, and redacted output. Do not use emulator evidence for public Android approval.
