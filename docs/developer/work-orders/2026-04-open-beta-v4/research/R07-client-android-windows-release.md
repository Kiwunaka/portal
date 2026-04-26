# R07 - Client Android/Windows Release Readiness

Date: 2026-04-26
Role: R07, POKROV Open Beta v4 research wave
Scope: Android and Windows client release readiness across the platform repo and active `POKROV-app` worktree.
Write scope: this file only.

## Executive Summary

The active `POKROV-app` lane is a real client engineering lane, but it is not public-release ready for Android or Windows.

Android is blocked at P0 on trusted signing and physical release-build proof. The client code has useful safety work: non-exported `VpnService`, Android-specific config materialization that removes desktop loopback inbounds, explicit disconnect/revoke handling, self-package bypass rules, DNS/routing safeguards, and consumer-safe diagnostic summaries. However, none of that clears the required physical-device localhost/control-surface audit. There is also a command-contract mismatch: the platform audit script defaults to the legacy package `space.pokrov.vpn`, while the active Android shell uses `space.pokrov.pokrov_android_shell`; final verification must pass `--package space.pokrov.pokrov_android_shell`, and the platform gate should be fixed so it cannot audit the wrong package.

Windows is suitable only as a gated unsigned beta lane. The repo has a Windows release-seed contract, libcore-only runtime expectation, bundle helper, and SmartScreen/unknown-publisher warning copy. But the current `0.2.0-beta.1` handoff is metadata-only, public URLs are empty, no trusted signing/timestamping evidence is present, and no signed EXE/MSIX/portable bundle manifest exists for the active beta version.

The runtime and UI are directionally aligned with the consumer-first shell, but the release story should stay cautious: `All except RU` has implementation and tests, `Full tunnel` has Android sanitization coverage, and `Selected apps` is explicitly a beta MVP with route sync only. First-run route choice is not yet enforced before the first live connection, Android selected-apps reports elevated-privilege need even though that concept is desktop-specific, and Windows currently starts libcore with system proxy enabled and TUN disabled, which needs product signoff or implementation work before "device-wide" claims.

## Evidence Table

| Label | Evidence | Finding |
| --- | --- | --- |
| E01 | `docs/product/portal-vpn-product.md`, `docs/architecture/app-first-and-bonus-flows.md`, `docs/operations/publishing-and-signing-guide.md` | Public scope is Android + Windows. Android remains blocked until production signing plus physical release-build localhost/control-surface audit. Windows public release requires trusted signing and handoff. |
| E02 | `POKROV-app/docs/operations/cutover-readiness.md`, `docs/implementation/client-release-backlog.md` | Client lane status is blocked/not cutover ready; Android is internal beta only; Windows is gated unsigned beta only. |
| E03 | `POKROV-app/config/product-contract.seed.json` | Product facts are aligned on POKROV, 5-day trial, +10-day Telegram reward, Android/Windows public scope, and selected-apps beta-MVP status. |
| E04 | `POKROV-app/apps/android_shell/android/app/build.gradle` | Android release build is explicitly debug-signed, so any APK/AAB from this lane is internal-smoke material only. |
| E05 | `POKROV-app/apps/android_shell/android/app/src/main/AndroidManifest.xml` | Android service is non-exported and protected by `android.permission.BIND_VPN_SERVICE`; app id is `space.pokrov.pokrov_android_shell`. |
| E06 | `POKROV-app/.../RuntimeHostBridge.kt`, `PokrovRuntimeVpnService.kt`, `AndroidRuntimeState.kt` | Runtime bridge supports initialize/stage/connect/disconnect, foreground notification disconnect, permission revoke stop reason, resume reconciliation, and safe structured runtime diagnostics. |
| E07 | `POKROV-app/packages/app_shell/test/app_first_runtime_bootstrap_test.dart` | Tests cover no caller-controlled `trial_days`, managed profile fetch, Android loopback inbound removal, DNS final rewrite, `All except RU` rule-set injection/fallback, Android self-bypass, and selected-apps route-sync-only behavior. |
| E08 | `POKROV-app/packages/runtime_engine/lib/runtime_engine.dart` and tests | Windows desktop lane loads `libcore.dll`, has no helper binary, stages managed config, and starts with `set-system-proxy=true` / `enable-tun=false`. |
| E09 | `POKROV-app/artifacts/releases/pokrov-app/0.2.0-beta.1+20260425/release-handoff.json` | Active beta handoff is metadata-only; Android and Windows public approval are false; artifact URLs are null. |
| E10 | `POKROV-app/artifacts/releases/release-handoff.json` | Stable handoff pointer still references `0.1.0-seed.1+20260423` with blank public Android/Windows URLs. |
| E11 | `VPN/scripts/android_localhost_audit.py` | Audit script checks baseline, after launch, after connect, and after disconnect localhost listeners plus unauthenticated probes, but defaults to package `space.pokrov.vpn`. |
| E12 | `VPN/scripts/release_gate_check.py` | Android build gates require `ANDROID_AUDIT_SERIAL` and reject emulator serials, but the gate path does not expose the active app package override. |
| E13 | `POKROV-app/docs/design/DESIGN.md`, `POKROV-app/DESIGN.md`, app shell UI | Screenshot/evidence plan is draft only; current shell is functional but still seed-like and needs visual target verification. |

## P0 Issues

1. Android public release is blocked by signing and physical audit.
   Evidence: E01, E02, E04, E09, E11, E12.
   The active Android shell release build still uses debug signing, and no physical release-installed audit result is present. Public Android must remain blocked until a production-signed build passes localhost/control-surface audit before connect, after connect, and after disconnect on physical hardware.

2. The mandatory Android audit can target the wrong package.
   Evidence: E05, E11, E12.
   The active shell application id is `space.pokrov.pokrov_android_shell`, but `android_localhost_audit.py` defaults to `space.pokrov.vpn`. A direct `release_gate_check.py --client-platform-gates android-apk,android-aab` path has no obvious package override, so the gate can fail against the wrong app or accidentally exercise a legacy install on a tester device. Fix the gate to use the active package or add a `ANDROID_AUDIT_PACKAGE` / pass-through option.

3. Windows is not public-release ready without trusted signing and release handoff.
   Evidence: E01, E02, E09, E10.
   The current allowed state is gated unsigned beta only. Public Windows needs a trusted code-signing certificate, timestamping URL, signed installer/MSIX or approved direct installer path, checksums, public hosting URLs, and handoff sync.

## P1 Issues

1. No fresh active `0.2.0-beta.1` binaries are retained in the active `pokrov-app` artifact folder.
   Evidence: E09, E10.
   `0.2.0-beta.1+20260425` is metadata-only. The latest stable pointer references `0.1.0-seed.1+20260423`, while bridge artifacts exist only as retained archive material. Build fresh Android APK/AAB and Windows bundle artifacts for the active beta version before tester handoff.

2. First-run route choice is not enforced before first live activation.
   Evidence: E01, E02, app shell implementation.
   The shell defaults to `All except RU` and lets the user start from Protection. Product canon says the app must ask how this device should work before the first live route activation. Implement a first-run route decision gate or record explicit acceptance of the default before connect.

3. Selected apps is not an enforceable split-tunnel feature yet.
   Evidence: E03, E07.
   Android selected-apps sends `selected_apps=[]`, produces an empty `include_package`, and is documented as route-sync-only. Windows process selection is also not proven. Keep public copy beta-limited and do not claim package/process selection works until picker, persistence, backend round-trip, and OS enforcement are green.

4. Android selected-apps reports `requires_elevated_privileges=true`.
   Evidence: E07 and `app_first_runtime_bootstrap.dart`.
   Elevation is a desktop concept in the product contract. Android selected-apps should require Android package selection and VpnService permission, not elevated privileges. Adjust route-policy payload semantics per platform.

5. Windows "device-wide" behavior needs product/runtime confirmation.
   Evidence: E08.
   The Windows runtime options set `set-system-proxy=true` and `enable-tun=false`. That may be acceptable for gated beta, but it does not prove a TUN-first, device-wide route. Either implement the intended Windows route mode or label Windows beta behavior precisely.

6. Consumer-safe diagnostics are promising but not physically proven.
   Evidence: E06, E07.
   UI tests hide raw diagnostic labels and expose safe summaries, while native code records DNS/uplink/route counts. Physical Android logcat/UI inspection is still required to prove no raw config, personal links, tokens, or local-control details leak during failures.

## P2 Issues

1. UI polish and visual target evidence are incomplete.
   Evidence: E13.
   The app shell is usable and consumer-first, but screenshot plans are draft-only. Current UI has a seed-like warm palette, large rounded cards/orb controls, and no checked screenshot set for Android small/common phones or Windows compact/wide windows.

2. Minor visible encoding residue exists.
   Evidence: app shell Profile device/free-fallback copy.
   Some UI strings use mojibake separators such as `В·`. Clean these before screenshots, release notes, or public beta builds.

3. Archive artifact names still contain seed/next residue.
   Evidence: active artifacts list.
   The current `0.2.0-beta.1` metadata fixes Windows naming, but older retained `0.1.0-seed` artifacts still include `pokrov-next-windows-seed...`. Do not surface those as current downloads.

## Proposed Implementation Work

1. Fix Android audit package targeting.
   Add an `ANDROID_AUDIT_PACKAGE` environment variable or release-gate CLI option and wire it through `release_gate_check.py` to `android_localhost_audit.py --package space.pokrov.pokrov_android_shell`.

2. Wire production signing paths.
   Android: replace debug signing for public builds with injected keystore inputs and fail public artifact packaging if production signing inputs are absent.
   Windows: add trusted signing and timestamping steps for EXE/MSIX, then verify Authenticode status before handoff.

3. Produce active beta artifacts.
   Build and retain `0.2.0-beta.1` Android APK/AAB plus Windows EXE/MSIX/ZIP or approved gated subset under `POKROV-app/artifacts/releases/pokrov-app/0.2.0-beta.1+<date>/` with SHA256 and handoff JSON.

4. Add first-run route-mode gate.
   Before first live connect, show `Optimize everything on this device` and `Only selected apps`; persist choice through backend-owned route policy. Default acceptance should be explicit.

5. Correct route-policy platform semantics.
   Android selected-apps should not set `requires_elevated_privileges=true`; Windows selected-apps may require elevation if the implementation actually needs it. Add tests for both.

6. Finish selected-apps enforcement or keep it gated.
   Implement Android installed-package picker and Windows executable/process picker, persist identifiers, apply include/exclude rules, and prove package bypass behavior. Until then, keep selected-apps beta-limited and away from broad public claims.

7. Confirm Windows routing mode.
   Decide whether the beta intentionally uses system proxy or must be TUN-first. Update runtime options, UI copy, support diagnostics, and release notes together.

8. Complete visual QA.
   Capture Android small/common phone screenshots and Windows compact/wide screenshots for Protection, Rules, Profile, Support, Subscription, and error/degraded states. Fix overflow, mojibake, and over-rounded seed styling as needed.

## Exact Verification Commands

Use these from a fresh PowerShell session. They are written for the assigned worktrees, not the default local checkouts.

```powershell
$env:POKROV_APP_ROOT = 'C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\open-beta-v4'
Set-Location 'C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4'
python scripts\run_client_release_gate.py preflight
python scripts\client_security_smoke.py
```

```powershell
$env:POKROV_APP_ROOT = 'C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\open-beta-v4'
Set-Location 'C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4'
python scripts\run_client_release_gate.py test --suite portal
python scripts\run_client_release_gate.py test --suite full
```

```powershell
$env:POKROV_APP_ROOT = 'C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\open-beta-v4'
Set-Location 'C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4'
python scripts\run_client_release_gate.py build --target windows
python scripts\run_client_release_gate.py build --target android-apk
python scripts\run_client_release_gate.py build --target android-aab
```

```powershell
$env:POKROV_APP_ROOT = 'C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\open-beta-v4'
$env:ANDROID_AUDIT_SERIAL = '<physical-device-serial>'
Set-Location 'C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4'
python scripts\android_localhost_audit.py --serial $env:ANDROID_AUDIT_SERIAL --package space.pokrov.pokrov_android_shell --connect-wait-sec 30 --disconnect-wait-sec 15 --out ops-local/android-localhost-audit-open-beta-v4.json
```

```powershell
$env:POKROV_APP_ROOT = 'C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\open-beta-v4'
$env:ANDROID_AUDIT_SERIAL = '<physical-device-serial>'
Set-Location 'C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4'
python scripts\release_gate_check.py --client-platform-gates windows,android-apk,android-aab
```

Note: the last command should not be treated as valid for Android until the package-targeting mismatch is fixed or the gate is proven to pass `--package space.pokrov.pokrov_android_shell` into the audit script.

## Android Physical Test Matrix

| Area | Test | Pass condition |
| --- | --- | --- |
| Install identity | Install the production-signed release APK on a clean physical device. | Package is `space.pokrov.pokrov_android_shell`, app label is `POKROV`, release is not debuggable, and version shows `0.2.0-beta.1` or current beta line. |
| First launch | Open app from launcher. | No Telegram wall, no raw config, no fake locations before setup. |
| Trial bootstrap | Tap first setup/connect path. | Client calls start-trial without `trial_days`, receives session, persists app-first state, and fetches managed profile. |
| First-run route choice | Start before any live connection. | App asks how the device should work, or records explicit default acceptance, before live connect. |
| All except RU | Choose/default `All except RU`. | RU suffix/ruleset and private/local paths are direct; non-RU traffic uses managed path; DNS behavior matches policy. |
| Full tunnel | Switch to `Full tunnel`. | Direct RU bypass rules are removed; DNS final is not a direct/local bootstrap lane except for resolver bootstrap as designed. |
| Selected apps | Choose selected-apps beta. | UI clearly says beta-limited if picker/enforcement are absent; no false package-isolation claim. |
| Connect | Turn protection on. | Android permission flow appears if needed; service starts; notification appears; status becomes protected or actionable warning. |
| Disconnect in app | Turn protection off in app. | Runtime stops; TUN closes; status returns to ready/staged; no stale protected state. |
| Disconnect from notification | Tap notification disconnect. | Runtime stops and UI reconciles after resume. |
| Permission revoke | Revoke Android connection permission while running. | `onRevoke` stops runtime, records `vpn_permission_revoked`, and UI shows safe recovery messaging. |
| Relaunch while connected | Kill/reopen app while service is active. | UI reconciles active runtime, avoids duplicate service start, and does not lose disconnect control. |
| Rapid reconnect | Toggle off/on repeatedly. | No duplicate TUN, no stale `running` state after stop, no crash. |
| Offline/DNS failure | Disable network or force resolver failure. | User sees safe "needs attention" style message; logcat has no raw tokens/configs. |
| Localhost audit | Run the audit with package override. | No new unauthenticated localhost listener or reachable local control surface after launch/connect/disconnect. |
| External local-client attempt | From adb shell, probe discovered localhost ports. | Any proxy/DNS/control/command surface is absent or rejects unauthenticated access. |
| Package bypass | Verify self-package direct bypass and selected-app include/exclude behavior. | App's own control/API path is not trapped by its TUN; selected-apps does not overclaim enforcement. |
| Small screen | Test common small phone viewport/font scale. | No text overlap, clipped CTA, raw diagnostics, or unusable nav. |
| Uninstall/reinstall | Remove and reinstall release build. | Runtime state and local staged configs are cleaned or safely regenerated; no stale session causes unsafe connect. |

## Windows Artifact Checklist

- Build active beta from `POKROV-app/open-beta-v4`, not retained bridge archive.
- Verify `apps/windows_shell/pubspec.yaml` version aligns with public beta line.
- Run Flutter analyze/tests for `packages/app_shell`, `packages/runtime_engine`, and `apps/windows_shell`.
- Run `scripts\build-windows-release.ps1 -SyncRuntime -SkipTests -SkipAnalyze` only after tests have passed elsewhere.
- Verify release bundle contains `pokrov_windows_beta.exe`, `flutter_windows.dll`, `libcore.dll`, `data/app.so`, and `data/icudtl.dat`.
- Verify release bundle does not require `HiddifyCli.exe` on Windows.
- Generate SHA256 for EXE/MSIX/ZIP and manifest.
- Sign EXE and MSIX with trusted certificate when moving beyond gated beta.
- Timestamp signatures with approved timestamping service.
- Verify Authenticode signature status.
- Verify MSIX identity fields are `POKROV` / `pokrov` and do not expose legacy `Pokrov.Vpn`, `POKROV VPN`, or inherited upstream identity.
- Verify Windows runtime behavior: connect, disconnect, relaunch, stale state, DNS warning, and route-mode behavior.
- Confirm whether Windows beta is system-proxy or TUN-first; align UI/support copy accordingly.
- Retain final artifacts under `POKROV-app/artifacts/releases/pokrov-app/<version>/`.

## Release-Handoff Manifest Checklist

- `schema_version`.
- `client_lane`.
- `release_version`.
- `source_commit` or source branch plus commit.
- `artifact_dir`.
- `release_state`.
- Android object: `play_url`, `apk_url`, `mirror_url`, artifact names, SHA256, signing status, physical-audit evidence path.
- Windows object: `exe_url`, `mirror_url`, optional `msix_url`, optional `portable_zip_url`, artifact names, SHA256, signing status, timestamping status.
- `docs_url` pointing to `https://pokrov.space/install/`.
- Runtime env values: `APP_ANDROID_PLAY_URL`, `APP_ANDROID_APK_URL`, `APP_ANDROID_MIRROR_URL`, `APP_WINDOWS_EXE_URL`, `APP_WINDOWS_MIRROR_URL`, `APP_DOCS_URL`.
- Origin evidence fields: `current-origin check`, `brain-origin check`, `RU-origin check`, each with status or `BLOCKED_BY_ACCESS`.
- Notes that Android is blocked unless signed and physical audit is green.
- Notes that Windows unsigned builds are gated beta only.
- No secrets, raw subscription links, bearer tokens, payment IDs, personal URLs, Telegram IDs, or private keys.

## App UI Polish Backlog

- Enforce first-run route question before first live connect.
- Add Android package picker and Windows process/executable picker or keep selected-apps visibly beta-limited.
- Replace mojibake separators such as `В·`.
- Confirm Russian copy quality before public beta screenshots.
- Reduce seed-like visual treatment if the target visual direction is calmer and more utilitarian: large 28-32 px card radii and orb-style control should be reviewed.
- Capture Android small/common phone and Windows compact/wide screenshot sets.
- Verify text does not overlap or clip at high font scale.
- Keep raw paths, config payloads, local-control details, public IPs, and tokens out of all normal UI and screenshot evidence.
- Add a visible but calm warning state for Windows unsigned beta downloads.

## Signing/Secrets Requirements

Do not put signing secrets in docs or work-order evidence.

Android public/beta-public requirements:

- Production keystore material provided through secure local/CI secret storage.
- `ANDROID_SIGNING_KEY`.
- `ANDROID_SIGNING_STORE_PASSWORD`.
- `ANDROID_SIGNING_KEY_PASSWORD`.
- `ANDROID_SIGNING_KEY_ALIAS`.
- Release build must not use `signingConfigs.debug`.
- Google Play AAB and direct APK must be signed with the approved key path.

Windows public/beta-public requirements:

- Trusted code-signing certificate or secure signing service.
- `WINDOWS_SIGNING_KEY`.
- `WINDOWS_SIGNING_PASSWORD`.
- Timestamping service URL.
- Authenticode verification output.
- MSIX identity/signing verification if MSIX is included.

Shared requirements:

- Keep public artifact URLs in release handoff/runtime env only after hosting is approved.
- Keep checksums public; keep credentials private.
- Redact any logs containing tokens, personal connection URLs, full user identifiers, payment payloads, or signing material.

## Final Commands

Minimum research-safe preflight after implementation changes:

```powershell
$env:POKROV_APP_ROOT = 'C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\open-beta-v4'
Set-Location 'C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4'
python scripts\run_client_release_gate.py preflight
python scripts\client_security_smoke.py
python scripts\run_client_release_gate.py test --suite portal
```

Full release-candidate gate after signing/audit prerequisites are available:

```powershell
$env:POKROV_APP_ROOT = 'C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\open-beta-v4'
$env:ANDROID_AUDIT_SERIAL = '<physical-device-serial>'
Set-Location 'C:\Users\kiwun\.config\superpowers\worktrees\VPN\open-beta-v4'
python scripts\run_client_release_gate.py test --suite full
python scripts\run_client_release_gate.py build --target windows
python scripts\run_client_release_gate.py build --target android-apk
python scripts\run_client_release_gate.py build --target android-aab
python scripts\android_localhost_audit.py --serial $env:ANDROID_AUDIT_SERIAL --package space.pokrov.pokrov_android_shell --connect-wait-sec 30 --disconnect-wait-sec 15 --out ops-local/android-localhost-audit-open-beta-v4.json
python scripts\release_gate_check.py --client-platform-gates windows,android-apk,android-aab
```

## Research Notes

- I did not run builds or tests in this research pass because the assignment allowed writing only this output file, and the relevant commands would create build/test/cache artifacts outside the allowed write scope.
- Existing untracked or modified files in both worktrees were treated as other-agent work and were not altered.
- No secrets were read, printed, or copied into this memo.
