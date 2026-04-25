# R08 Client Android Windows Public Beta

Status: [confirmed] researched - public beta blocked

Last researched: 2026-04-25

Claim labels used below: `confirmed`, `probable`, `unknown`, `needs local run`, `blocked by missing access`.

## Scope

- [confirmed] Research scope: Android/Windows client public beta readiness, Android public block, physical audit, signing, Windows artifact metadata/checksum/warnings, version labels, release handoff, and client tests/build gates.
- [confirmed] Workspace: `C:/Users/kiwun/.config/superpowers/worktrees/VPN/public-beta-release-wave`.
- [confirmed] Active client lane inspected read-only: `C:/Users/kiwun/Documents/ai/POKROV-app`.
- [confirmed] Only this assigned research file was created in this pass.
- [confirmed] The active client repo is currently dirty on `codex/beta-release-client`; this pass treats those changes as inherited/in-flight evidence and does not modify them.

## Files/docs inspected

- [confirmed] `AGENTS.md`.
- [confirmed] Root canonical docs: `docs/README.md`, `docs/product/portal-vpn-product.md`, `docs/architecture/system-overview.md`, `docs/architecture/app-first-and-bonus-flows.md`, `docs/operations/deployment-and-access.md`, `docs/operations/monitoring-and-visibility.md`, `docs/developer/developer-guide.md`, `docs/developer/repository-map.md`.
- [confirmed] Publishing docs: `docs/operations/publishing-and-signing-guide.md`, `docs/operations/android-production-signing-handoff.md`, `docs/operations/android-physical-device-audit-handoff.md`.
- [confirmed] Client docs: `C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md`, `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md`.
- [confirmed] Client scripts/config/source: `scripts/run_client_release_gate.py`, `scripts/client_security_smoke.py`, `POKROV-app/config/*.seed.json`, Android Gradle/manifest/pubspec, Windows pubspec/release seed/build scripts, app bootstrap and shell sources.
- [confirmed] Prior paid-beta inherited evidence only: `2026-04-beta-release/research/R08-client-android-windows.md`, `evidence/logs/WO-007-client-android-windows-beta.md`, and `evidence/release-gates/W10-final-gate-summary.md`.

## Current confirmed state

- [confirmed] `python scripts/run_client_release_gate.py preflight` passed and found the active `POKROV-app` gate root, host shells, seed configs, and wrapper scripts.
- [confirmed] `python scripts/client_security_smoke.py` passed in this pass.
- [confirmed] `powershell -ExecutionPolicy Bypass -File C:/Users/kiwun/Documents/ai/POKROV-app/scripts/validate-seed.ps1` passed in this pass.
- [confirmed] Current Android and Windows pubspecs use `version: 0.2.0-beta.1`.
- [confirmed] `config/product-contract.seed.json` sets `client_version_line` to `0.2.0-beta.1`.
- [confirmed] W07 inherited evidence says the client no longer sends caller-controlled `trial_days`; current source confirms the `start-trial` body omits `trial_days`.
- [confirmed] W07 inherited evidence says Android APK and AAB local builds passed and Windows build passed post-W10; this R08 did not rerun build-producing gates to avoid creating or changing artifacts.
- [confirmed] The latest default `docs/audit-artifacts/release_gate_report.md` is `PASS`, but explicitly marks Android physical audit `BLOCKED_BY_ACCESS`, runtime app-download smoke `SKIPPED_NO_LIVE_TOKEN`, client platform builds `NOT_REQUESTED`, brain-origin `BLOCKED_BY_ACCESS`, and RU-origin `BLOCKED_BY_ACCESS`.

## Android readiness

- [confirmed] Android public release remains blocked by canonical policy until production signing and a physical-device release-build localhost/control-surface audit pass.
- [confirmed] Current Android `build.gradle` release block still uses `signingConfig = signingConfigs.debug`, with comments saying public Android remains blocked until trusted signing and physical audit pass.
- [confirmed] Current Android app id and namespace are `space.pokrov.pokrov_android_shell`.
- [confirmed] The Android physical-audit handoff defaults to package `space.pokrov.vpn` and says to pass `--package` if different. The current package identity therefore needs explicit release/audit command alignment.
- [confirmed] Android manifest declares `android:label="POKROV"`, `PokrovRuntimeVpnService`, `android:exported="false"`, `android.permission.BIND_VPN_SERVICE`, and `foregroundServiceType="specialUse"`.
- [needs local run] No physical-device audit was run in this pass. Prior W10 evidence says `adb devices -l` had no attached device and the physical audit was not run.
- [needs local run] Public Android still requires release-installed checks before connect, after connect, and after disconnect for proxy, DNS, command-server, Clash API, and equivalent control surfaces.
- [blocked by missing access] Production Android signing inputs were not available or verified in this pass.

## Windows readiness

- [confirmed] Current Windows seed declares `channel: gated_beta`, `artifact_status: unsigned_beta`, `public_approved: false`, and `binary_name: pokrov_windows_beta.exe`.
- [confirmed] Current Windows pubspec version is `0.2.0-beta.1`.
- [confirmed] `apps/windows_shell/build/release_bundle/` contains a local `pokrov-windows-beta-x64-0.2.0-beta.1.zip` and matching manifest from 2026-04-25.
- [confirmed] The Windows manifest records required-file SHA256 values for `pokrov_windows_beta.exe`, `flutter_windows.dll`, `libcore.dll`, `data/app.so`, and `data/icudtl.dat`.
- [confirmed] The Windows seed and manifest both state the bundle is unsigned and may be shared only as gated beta with a Microsoft Defender SmartScreen or unknown-publisher warning.
- [confirmed] No trusted Windows signing proof, timestamping service, installer flow, MSIX publication path, public hosting, or runtime URL handoff approval was verified.
- [probable] The local Windows beta ZIP is useful engineering evidence, but it is not a trusted public artifact until signing, hosting, and runtime download smoke are complete.

## Release handoff and artifacts

- [confirmed] `POKROV-app/artifacts/releases/pokrov-app/0.2.0-beta.1+20260425/` exists but is metadata-only: `README.md` plus `release-handoff.json`; it does not contain newly retained binaries or checksums.
- [confirmed] The 0.2.0 beta metadata marks Android `internal_beta_only`, Windows `gated_unsigned_beta`, `public_cutover_allowed: false`, and artifact URLs as `null`.
- [confirmed] `config/release-handoff.seed.json` points latest repo-backed release metadata to `0.2.0-beta.1+20260425`, but `checksums` is `null`.
- [confirmed] The stable client-owned `artifacts/releases/release-handoff.json` currently points at older `0.1.0-seed.1+20260423`, marks `engineering_alpha_not_public`, and leaves Android/Windows public URLs blank.
- [confirmed] Older `0.1.0-seed.1+20260423` retained artifacts have `SHA256SUMS.txt`; the 0.2.0 beta metadata folder does not.
- [confirmed] Public canonical artifact names in the publishing guide are `pokrov-android-universal.apk`, `pokrov-android-market.aab`, `pokrov-windows-setup-x64.exe`, `pokrov-windows-setup-x64.msix`, and `pokrov-windows-portable-x64.zip`; the current Windows beta bundle uses beta ZIP naming instead and remains gated/unsigned.

## Gate interpretation

- [confirmed] Current local read-only checks passed: preflight, `client_security_smoke.py`, and client `validate-seed.ps1`.
- [confirmed] The default release gate report is useful local evidence only; it did not request client platform builds and did not close Android physical audit, live runtime app-download smoke, brain-origin, or RU-origin evidence.
- [needs local run] Before public artifact approval, rerun the client platform build gates intentionally: `python scripts/run_client_release_gate.py build --target windows`, `android-apk`, and `android-aab`.
- [needs local run] Public release evidence must include `python scripts/release_gate_check.py --client-platform-gates windows,android-apk,android-aab` with `ANDROID_AUDIT_SERIAL` set to physical hardware when Android gates are in scope.
- [needs local run] Windows needs install/run/connect/disconnect smoke, listener/bind checks, proxy rollback, DNS/leak checks, and signed or explicitly accepted unsigned-beta download UX.

## Highest-risk findings

1. [confirmed] Android is still public-blocked: release signing falls back to debug signing, production signing proof is missing, and the physical-device localhost/control-surface audit is not complete.
2. [confirmed] Release handoff is inconsistent: 0.2.0 beta metadata exists, but the stable `artifacts/releases/release-handoff.json` still points at `0.1.0-seed.1+20260423` with blank public URLs.
3. [confirmed] Windows has a local 0.2.0 beta ZIP and checksum-bearing manifest, but it is unsigned, not publicly approved, and not copied into the 0.2.0 retained release metadata folder with final checksums/handoff.
4. [confirmed] The latest green default release gate did not request client platform builds and still marks Android physical audit, runtime app-download smoke, brain-origin, and RU-origin evidence as blocked/skipped/not requested.
5. [confirmed] Android package identity/audit defaults are not aligned: current Gradle uses `space.pokrov.pokrov_android_shell`, while the physical-audit runbook defaults to `space.pokrov.vpn`; the release command and public package decision must be explicit.

## Public beta recommendation

- [confirmed] Do not open Android public beta from this state.
- [confirmed] Windows can remain a gated unsigned beta candidate only if users see the SmartScreen/unknown-publisher warning before download and operators accept the unsigned limitation.
- [confirmed] Do not populate public Android/Windows URLs or sync runtime `APP_*` values until signed/approved artifacts, checksums, release handoff, and runtime download smoke are complete.
- [probable] The next useful R08 action is not more static review; it is a controlled local run with a physical Android device, signing inputs, and explicit artifact-retention/handoff steps.
