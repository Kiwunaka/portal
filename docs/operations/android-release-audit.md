# Android Release Audit

Last updated: 2026-05-26

Android outside-store public beta uses the retained `2026-05-15` owner attestation for the physical release-build localhost/control-surface audit. A fresh raw physical-device PASS remains a manual owner test before stronger Android safety, store, stable, or raw-audited claims.

Run only with a physical device:

```powershell
$env:ANDROID_AUDIT_SERIAL="<physical-device-serial>"
$env:ANDROID_AUDIT_PACKAGE="space.pokrov.pokrov_android_shell"
$env:ANDROID_AUDIT_RELEASE_EVIDENCE="<artifact/version/checksum>"
python scripts/android_localhost_audit.py --serial $env:ANDROID_AUDIT_SERIAL --package $env:ANDROID_AUDIT_PACKAGE --release-evidence $env:ANDROID_AUDIT_RELEASE_EVIDENCE --require-release-build --connect-wait-sec 30 --disconnect-wait-sec 15
```

The release gate will also pass `ANDROID_AUDIT_PACKAGE` and require `ANDROID_AUDIT_RELEASE_EVIDENCE` when Android platform gates are requested.

Evidence must include package name, build type, serial label, and redacted output. Do not use emulator evidence for trusted, store, stable, or raw-audited Android approval.
