# Client Build Evidence

Generated: 2026-05-07 22:47 MSK

## Verdict

Local client build evidence refreshed. This does not make the public beta `GO`.

`python scripts/release_gate_check.py --client-platform-gates windows,android-apk --output docs/audit-artifacts/release-gate-client-builds-2026-05-07.md` stopped before writing a report because `ANDROID_AUDIT_SERIAL` is absent. That gate intentionally requires a physical Android device when Android platform gates are requested, so the combined platform-gate status remains `BLOCKED_BY_ACCESS`.

## Commands

- `python -B scripts/run_client_release_gate.py build --target windows` -> PASS.
- `python -B scripts/run_client_release_gate.py build --target android-apk` -> PASS.
- `Get-FileHash -Algorithm SHA256 ...app-release.apk` -> PASS.
- `Get-FileHash -Algorithm SHA256 ...pokrov-windows-beta-x64-0.2.0-beta.1-setup.exe` -> PASS.
- `Get-AuthenticodeSignature ...pokrov-windows-beta-x64-0.2.0-beta.1-setup.exe` -> `NotSigned`.
- `python scripts/prepare_github_release_plan.py --tag v0.2.0-beta.1 --title "POKROV 0.2.0-beta.1"` -> PASS dry-run after the fresh builds.
- `python scripts/publish_github_release_assets.py --tag v0.2.0-beta.1 --title "POKROV 0.2.0-beta.1"` -> PASS dry-run after the fresh builds.

## Artifacts

- Android APK: `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/build/app/outputs/flutter-apk/app-release.apk`
  - Last write: `2026-05-07 22:46:58 MSK`
  - Size: `143259872`
  - SHA256: `1A369891641964A9A30A296E7D47111A07B6DDAAD5ABC293F7EF938A654DADB0`
- Windows setup EXE: `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/build/release_bundle/pokrov-windows-beta-x64-0.2.0-beta.1-setup.exe`
  - Last write: `2026-05-07 22:46:24 MSK`
  - Size: `27455488`
  - SHA256: `E340F36EC10149649373E0E7816C81B8C6873E9B95C7A85DC0F6AD708DB2C70D`
  - Authenticode: `NotSigned`
  - Unsigned beta risk accepted: `Accepted`
  - Note: operator instruction on 2026-05-08 says trusted Windows signing is not required for this outside-store beta pass. Keep public copy honest about the unsigned Windows build; trusted signing remains a future external dependency.

## Remaining Blockers

- Android physical release-build localhost/control-surface audit: `BLOCKED_BY_ACCESS`, because no physical device / `ANDROID_AUDIT_SERIAL` is available.
- Runtime app-download smoke: `BLOCKED_BY_ACCESS`, because live `TELEGRAM_INIT_DATA` and published/staged GitHub URLs are still unavailable.
- GitHub Releases: not published; dry-run tooling only.
- Windows trusted signing: `NOT_REQUIRED_FOR_THIS_BETA_BY_OPERATOR_ACCEPTANCE`; Authenticode remains `NotSigned`.
