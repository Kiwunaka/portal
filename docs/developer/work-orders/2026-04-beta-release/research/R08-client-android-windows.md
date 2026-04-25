# R08 Client Android Windows

Status: researched - beta blocked

Last researched: 2026-04-25

Claim labels used below: `confirmed`, `probable`, `unknown`, `needs local run`, `blocked by missing access`.

## Scope

Android and Windows paid beta readiness in `C:/Users/kiwun/Documents/ai/POKROV-app`, with platform release gates from `C:/Users/kiwun/Documents/ai/VPN`.

Read-only boundary: no client files were edited. Secrets and sensitive local evidence were not read or printed. The only edited file is this R08 markdown.

## Files/docs inspected

- `confirmed` Platform anchors: `docs/README.md`, `docs/product/portal-vpn-product.md`, `docs/architecture/system-overview.md`, `docs/architecture/app-first-and-bonus-flows.md`, `docs/operations/deployment-and-access.md`, `docs/operations/monitoring-and-visibility.md`, `docs/developer/developer-guide.md`, `docs/developer/repository-map.md`, `docs/operations/publishing-and-signing-guide.md`.
- `confirmed` Client anchors: `POKROV-app/README.md`, `POKROV-app/docs/README.md`, `POKROV-app/docs/operations/cutover-readiness.md`, `POKROV-app/docs/implementation/client-release-backlog.md`, `POKROV-app/docs/product/client-product-contract.md`, `POKROV-app/docs/architecture/app-first-onboarding-flow.md`.
- `confirmed` Client source/config inventory: `POKROV-app/apps/android_shell/**`, `POKROV-app/apps/windows_shell/**`, `POKROV-app/packages/**`, `POKROV-app/config/*.seed.json`, release handoff JSON under `POKROV-app/artifacts/releases/**`.
- `blocked by missing access` `ops-local/*` audit evidence contents were intentionally not read because the task forbids secrets/sensitive local evidence printing.

## Current state

- `confirmed` Shared shell implements the four public tabs: `Protection`, `Locations`, `Rules`, `Profile`.
- `confirmed` Profile contains nested surfaces for subscription, Telegram bonus, devices, settings, redeem, and support.
- `confirmed` Managed profile fetch exists: app-first session/trial creation, route-policy sync, then `GET /api/client/profile/managed` with `singbox-json` materialization.
- `confirmed` Connect/disconnect paths exist in shared shell, Android `VpnService`, and Windows desktop FFI runtime.
- `confirmed` Android runtime materialization uses a TUN-only inbound and does not materialize the desktop loopback `mixed` or `direct` inbounds on Android.
- `confirmed` Android native service is declared `exported=false`, uses `android.permission.BIND_VPN_SERVICE`, and gates debug intent handling behind the debuggable application flag.
- `confirmed` Windows runtime currently packages/runs as a desktop libcore FFI shell with system proxy options, `enable-clash-api=false`, and `allow-connection-from-lan=false`.
- `confirmed` Route modes exist in code and seed configs: `All except RU`, `Full tunnel`, and `Only selected apps`.
- `confirmed` All-except-RU and full-tunnel materialization paths exist, including RU suffix/rule-set direct routing and Android direct-bypass sanitization.
- `confirmed` Safe runtime health/diagnostics models exist for connection status, DNS health, uplink health, route counts, and host diagnostics summaries.
- `probable` First-layer app UI mostly avoids raw managed profile/config/control details; a local UI run is still needed to verify all screens, snackbars, overflow states, and failure states.

## Gaps against beta

- `confirmed` Public labels are still seed labels such as `0.1.0-seed.1`, `0.1.0-seed.2`, `pokrov_windows_seed.exe`, and `pokrov-next-windows-seed-*`, not `0.x.x-beta`.
- `confirmed` The first-run target is not implemented as specified. The shell has a `Turn protection on` CTA, but no first-layer `Try free` CTA and no explicit route-mode onboarding choice phrased as `Optimize everything on this device` / `Only selected apps`.
- `confirmed` Checkout, cabinet, support, community, feedback, and redeem actions are mostly snack-bar handoffs. They do not yet launch a real external browser flow or complete a backend redeem/support action from the client shell.
- `confirmed` Redeem UX uses a hardcoded demo-looking hint code, `POKROV-START-2026`.
- `confirmed` Selected apps MVP is not implemented. The UI exposes only a route card, there is no Android package picker or Windows app/process picker, route-policy sync sends `selected_apps: []`, and Android TUN `include_package` receives an empty list.
- `confirmed` The client sends caller-controlled `trial_days: 5` in `start-trial`, which conflicts with the canonical app-first contract that the backend owns trial duration.
- `confirmed` Route-policy sync swallows non-session failures, so backend-owned route-mode persistence can silently fail before managed profile fetch.
- `needs local run` Full tunnel and All-except-RU need release-build DNS/leak verification on Android and Windows before public claims.
- `needs local run` Windows local listener and system proxy behavior need a signed/local bundle smoke to verify bind addresses, proxy rollback, DNS behavior, and first-run behavior.
- `unknown` Download/install UX cannot be confirmed as beta-ready because public artifact URLs are blank and the visible release state is still engineering alpha.

## P0 blockers

1. `confirmed` Android release signing is not production-ready. The release build currently falls back to the debug signing config.
2. `needs local run` Android physical-device release-build localhost/control-surface audit is not proven in this read-only pass. Platform docs make this a hard public release gate.
3. `confirmed` Windows public artifact is not ready: the available lane is an unsigned seed ZIP/binary, not a signed public EXE/installer handoff.
4. `confirmed` Release handoff JSON exists, but it is marked `engineering_alpha_not_public` and public Android/Windows URLs are blank.
5. `confirmed` Public version/artifact labels are seed/dev lineage, not `0.x.x-beta`.
6. `confirmed` Selected apps MVP is incomplete on both Android and Windows.
7. `confirmed` App-first trial contract is violated by sending `trial_days` from the client.
8. `confirmed` First-run paid beta UX is incomplete: no explicit `Try free` first-layer flow, no required onboarding route-mode choice, and handoffs are still mostly local snackbars.

## P1 beta polish

- `confirmed` Replace demo/seed copy and artifact names, including `POKROV-START-2026`, `0.1.0-seed.*`, `pokrov_windows_seed.exe`, and `pokrov-next-windows-seed-*`.
- `confirmed` Implement real redeem flow or clearly remove redeem from beta first layer.
- `confirmed` Implement real checkout/cabinet/support external handoff behavior where intended by product docs.
- `confirmed` Align Windows bundle naming and install surface to the public release contract, or keep it explicitly internal-alpha only.
- `probable` Review any public-visible `VPN profile` wording. It may be an OS permission compatibility label, but it should not become direct public product copy.
- `probable` Clean or explicitly exclude stale Windows runtime helper residue such as `HiddifyCli.exe` from public packaging evidence.

## P2 defer

- `confirmed` iOS/macOS remain readiness-only and are outside this paid beta public scope.
- `confirmed` XHTTP and fallback transport details should remain advanced/internal until public copy and runtime support are proven.
- `probable` Multi-device management can stay lightweight for beta if the support/device surfaces do not over-promise enforcement.

## Technical debt

- `confirmed` Seed configs still carry next-client/engineering-alpha lineage and should be normalized before a public beta train.
- `confirmed` Android Gradle TODOs remain around application id and release signing.
- `confirmed` Runtime provenance is pinned to upstream libcore seed metadata, but this read-only audit did not independently verify checksums or artifact custody.
- `confirmed` Route-policy failure handling needs stricter behavior before route modes are public-facing.
- `confirmed` Selected-apps data model exists only as an empty payload path; app discovery, selection persistence, and OS-specific enforcement are missing.

## Security/privacy risks

- `needs local run` Android release-installed localhost/control-surface exposure remains the central security gate.
- `needs local run` Windows loopback listener reachability, proxy rollback, and DNS behavior must be verified from a local bundle before public release.
- `confirmed` Android debug-only intent paths appear gated by the debuggable flag, but this still needs release-build validation.
- `confirmed` Android logs include staged config path and route counts, but no raw config payload was observed in source review.
- `confirmed` Shared UI does not intentionally expose raw managed config bodies in the first layer.
- `unknown` Failure-mode privacy for all runtime errors, snackbars, and platform exceptions needs screenshot/log review from local runs.

## Required implementation WOs

1. Android release signing and version-label work order: production signing inputs, package identity confirmation, `0.x.x-beta` labels, and release build artifacts.
2. Android physical audit work order: install the signed release build on a physical device and run localhost/control-surface audit with captured evidence.
3. Windows release packaging work order: signed public EXE/installer or explicitly approved beta bundle, public artifact naming, runtime custody, and install/uninstall smoke.
4. App-first contract work order: remove client-sent `trial_days`, make route-policy sync failures visible/blocking, and keep backend-owned trial/routing authority.
5. Onboarding/activation UX work order: implement `Try free`, route-mode choice, checkout handoff, redeem behavior, and beta-safe empty/error states.
6. Selected apps MVP work order: Android package picker/enforcement, Windows app/process selection contract, persistence, backend sync, and negative tests.
7. Release handoff work order: populate public URLs only after signed artifacts and gates pass; keep engineering-alpha handoff separate from beta handoff.

## Validation commands

- `needs local run` `python scripts/run_client_release_gate.py preflight`
- `needs local run` `python scripts/run_client_release_gate.py test --suite portal`
- `needs local run` `python scripts/run_client_release_gate.py test --suite full`
- `needs local run` `python scripts/run_client_release_gate.py build --target android-apk`
- `needs local run` `python scripts/run_client_release_gate.py build --target android-aab`
- `needs local run` `python scripts/run_client_release_gate.py build --target windows`
- `needs local run` `python scripts/client_security_smoke.py`
- `needs local run` `python scripts/android_localhost_audit.py --serial <physical-device-serial> --connect-wait-sec 30 --disconnect-wait-sec 15` against a signed release-installed Android build.
- `needs local run` `python scripts/release_gate_check.py --client-platform-gates windows,android-apk,android-aab` with `ANDROID_AUDIT_SERIAL` set to a physical device serial.
- `needs local run` Windows signed-bundle smoke: install/run, connect/disconnect, listener bind/reachability, system proxy rollback, DNS/leak checks for Full tunnel and All-except-RU.

## Evidence links

- `confirmed` `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/lib/app_shell.dart`
- `confirmed` `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/lib/app_first_runtime_bootstrap.dart`
- `confirmed` `C:/Users/kiwun/Documents/ai/POKROV-app/packages/core_domain/lib/core_domain.dart`
- `confirmed` `C:/Users/kiwun/Documents/ai/POKROV-app/packages/runtime_engine/lib/runtime_engine.dart`
- `confirmed` `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/android/app/build.gradle`
- `confirmed` `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/android/app/src/main/AndroidManifest.xml`
- `confirmed` `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/android/app/src/main/kotlin/space/pokrov/pokrov_android_shell/PokrovRuntimeVpnService.kt`
- `confirmed` `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/android/app/src/main/kotlin/space/pokrov/pokrov_android_shell/RuntimeHostBridge.kt`
- `confirmed` `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/pubspec.yaml`
- `confirmed` `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/windows/CMakeLists.txt`
- `confirmed` `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/windows/runner/Runner.rc`
- `confirmed` `C:/Users/kiwun/Documents/ai/POKROV-app/config/product-contract.seed.json`
- `confirmed` `C:/Users/kiwun/Documents/ai/POKROV-app/config/runtime-profile.seed.json`
- `confirmed` `C:/Users/kiwun/Documents/ai/POKROV-app/config/platform-matrix.seed.json`
- `confirmed` `C:/Users/kiwun/Documents/ai/POKROV-app/config/windows-release.seed.json`
- `confirmed` `C:/Users/kiwun/Documents/ai/POKROV-app/config/release-handoff.seed.json`
- `confirmed` `C:/Users/kiwun/Documents/ai/POKROV-app/config/runtime-artifacts.seed.json`
- `confirmed` `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/release-handoff.json`
