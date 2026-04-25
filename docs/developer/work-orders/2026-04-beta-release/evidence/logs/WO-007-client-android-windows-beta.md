# WO-007 Client Android Windows Beta

Status: W07 implementation pass complete with accepted gate limitations; post-W10 local tooling resolved
Agent: W07
Date: 2026-04-25

## What I checked

- Read the orchestrator context, release index, synthesis, R08 client research, W01 visual evidence, W09 security baseline, and WO-007 brief.
- Read the active client docs index and cutover readiness docs in `C:/Users/kiwun/Documents/ai/POKROV-app`.
- Checked the active client branch `codex/beta-release-client` and avoided unrelated untracked release/archive material.
- Searched the W07 write scope for seed/dev/Hiddify residue, `trial_days`, raw/local diagnostics labels, Windows release names, and beta metadata.

## What I found

- The app bootstrapper still sent caller-controlled `trial_days: 5` to `POST /api/client/session/start-trial`.
- Client package versions and Windows release metadata still used `0.1.0-seed.*`, `pokrov_windows_seed.exe`, and `pokrov-next-windows-seed-*`.
- The first-layer shell no longer rendered the older runtime-health controls in source, but host widget tests and docs still expected `Runtime health`, `Prime runtime`, and `Stage local smoke profile`.
- Selected apps existed as a route-mode path, but needed explicit beta MVP wording.
- Android remains internal-only/public-blocked because there is no physical-device release-build localhost/control-surface audit evidence in this pass.
- Windows remains public-blocked because the beta lane is unsigned and must warn about SmartScreen/unknown-publisher prompts.

## What I changed

- Removed `trial_days` from the client start-trial request and set the app version line to `0.2.0-beta.1`.
- Added external safe handoff launching for checkout, cabinet downloads, support bot, community channel, feedback bot, and redeem flow.
- Removed the demo activation-key hint from the shared shell default context.
- Labeled selected apps as beta-limited route sync while picker and OS enforcement remain open.
- Updated Android host comments/docs to mark release output internal beta only and public blocked until trusted signing plus physical audit pass.
- Renamed Windows beta metadata/build identity to `pokrov_windows_beta.exe` and `pokrov-windows-beta-x64-{version}`.
- Added unsigned Windows beta metadata and required SmartScreen/unknown-publisher warning text.
- Added metadata-only beta evidence under `POKROV-app/artifacts/releases/pokrov-app/0.2.0-beta.1+20260425/`.
- Updated active client docs for beta status, selected-apps MVP status, safe handoffs, and release blockers.

## How I verified

- RED first:
  - `flutter test test\app_first_runtime_bootstrap_test.dart` failed because `trial_days` was still present.
  - `flutter test test\pokrov_seed_app_test.dart` failed because `handoffLauncher` did not exist yet.
  - `flutter test test\windows_release_contract_test.dart` failed because Windows metadata was still seed-named.
- GREEN/focused:
  - `flutter test` in `packages/app_shell`: passed, 29 tests.
  - `flutter test` in `apps/android_shell`: passed, 4 tests.
  - `flutter test` in `apps/windows_shell`: passed, 2 tests.
  - `flutter test test\windows_release_contract_test.dart` in `apps/windows_shell`: passed.
  - `powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1` in `POKROV-app`: exited 0; Android Gradle emitted an SDK XML version warning and a Kotlin daemon connection-reset stack trace before completing successfully.
  - JSON validation passed for edited client config and beta handoff JSON.
  - `adb devices -l` showed no attached device, so physical Android audit remains blocked.
  - `git diff --check` in `POKROV-app`: exited 0.

## What remains / risk

- Post-W10 follow-up resolved the stale Windows beta metadata expectations in `validate-seed.ps1` and platform `client_security_smoke.py`.
- `flutter analyze` in `packages/app_shell` still reports existing dead-code warnings in `test/app_first_runtime_bootstrap_test.dart`; focused tests pass.
- Android physical release-build localhost/control-surface audit was not run because no physical device serial is attached.
- Android is still internal beta only/public blocked.
- Windows is still unsigned gated beta only/public blocked.
- Old `0.1.0-seed.1+20260423` artifact evidence remains retained archive material and was not renamed or deleted.

## Post-W10 Orchestrator Follow-Up

- `powershell -ExecutionPolicy Bypass -File .\scripts\validate-seed.ps1` in `POKROV-app`: `PASS`.
- `python scripts/client_security_smoke.py` from the platform repo: `PASS`.
- `python scripts/run_client_release_gate.py build --target windows`: `PASS`, producing and staging `pokrov_windows_beta.exe`.

## Changed file paths

- `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/README.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/android/app/build.gradle`
- `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/android/app/src/main/kotlin/space/pokrov/pokrov_android_shell/PokrovRuntimeVpnService.kt`
- `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/pubspec.lock`
- `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/pubspec.yaml`
- `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/test/widget_test.dart`
- `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/README.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/pubspec.lock`
- `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/pubspec.yaml`
- `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/test/widget_test.dart`
- `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/test/windows_release_contract_test.dart`
- `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/windows/CMakeLists.txt`
- `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/windows/flutter/generated_plugin_registrant.cc`
- `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/windows/flutter/generated_plugins.cmake`
- `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/windows/runner/Runner.rc`
- `C:/Users/kiwun/Documents/ai/POKROV-app/config/cutover-readiness.seed.json`
- `C:/Users/kiwun/Documents/ai/POKROV-app/config/product-contract.seed.json`
- `C:/Users/kiwun/Documents/ai/POKROV-app/config/release-handoff.seed.json`
- `C:/Users/kiwun/Documents/ai/POKROV-app/config/windows-release.seed.json`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/architecture/app-first-onboarding-flow.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/architecture/bootstrap-workflow.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/implementation/client-release-backlog.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/windows-release-readiness.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/product/client-product-contract.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/lib/app_first_runtime_bootstrap.dart`
- `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/lib/app_shell.dart`
- `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/pubspec.lock`
- `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/pubspec.yaml`
- `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/app_first_runtime_bootstrap_test.dart`
- `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart`
- `C:/Users/kiwun/Documents/ai/POKROV-app/packages/core_domain/pubspec.yaml`
- `C:/Users/kiwun/Documents/ai/POKROV-app/packages/platform_contracts/pubspec.lock`
- `C:/Users/kiwun/Documents/ai/POKROV-app/packages/platform_contracts/pubspec.yaml`
- `C:/Users/kiwun/Documents/ai/POKROV-app/packages/runtime_engine/pubspec.lock`
- `C:/Users/kiwun/Documents/ai/POKROV-app/packages/runtime_engine/pubspec.yaml`
- `C:/Users/kiwun/Documents/ai/POKROV-app/packages/support_context/pubspec.lock`
- `C:/Users/kiwun/Documents/ai/POKROV-app/packages/support_context/pubspec.yaml`
- `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/0.2.0-beta.1+20260425/README.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/0.2.0-beta.1+20260425/release-handoff.json`
- `C:/Users/kiwun/Documents/ai/VPN/docs/developer/work-orders/2026-04-beta-release/evidence/logs/WO-007-client-android-windows-beta.md`
