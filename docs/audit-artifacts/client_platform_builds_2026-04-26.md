# Client Platform Builds

- timestamp_local: `2026-04-26`
- client repo: `C:/Users/kiwun/Documents/ai/POKROV-app`
- client branch: `codex/beta-release-client`
- result: `PASS_WITH_RELEASE_GATES_REMAINING`

## Commands

- `python scripts/run_client_release_gate.py build --target windows`
- `python scripts/run_client_release_gate.py build --target android-apk`
- `python scripts/run_client_release_gate.py build --target android-aab`

## Artifacts

- Windows zip: `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/build/release_bundle/pokrov-windows-beta-x64-0.2.0-beta.1.zip`
- Windows manifest: `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/build/release_bundle/pokrov-windows-beta-x64-0.2.0-beta.1.manifest.json`
- Android APK: `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/build/app/outputs/flutter-apk/app-release.apk`
- Android AAB: `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/build/app/outputs/bundle/release/app-release.aab`

## Notes

- Windows build completed and produced the beta zip plus manifest.
- Android release APK build completed.
- Android release AAB build completed.
- Android public distribution remains blocked until a physical-device release-build localhost/control-surface audit passes.
- Windows remains beta/unsigned unless a trusted signing and public handoff decision is explicitly completed.
