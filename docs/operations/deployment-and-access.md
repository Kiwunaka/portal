# Deployment And Access

Last updated: 2026-04-15

## Document Status

This file is living source of truth for deployment entrypoints, runtime access, and sensitive material locations.

## Control Plane

Canonical control-plane host:

- `brain`: `82.21.114.104`

Key services expected there:

- `portal-api`
- `portal-bot`
- `portal-helpbot`
- `portal-feedbackbot`
- `caddy`
- `x-ui`

RF auxiliary hosts:

- `mini`
  dedicated external RU probe origin
- `rf1`
  reserve RF ingress for operator and VIP/manual access

RF access rule:

- do not place control-plane services on `mini` or `rf1`
- do not add `rf1` to the normal runtime delivery pool in phase 1
- keep a hard kill switch for the `rf1` VIP/manual contour so it can be withdrawn without touching the standard consumer path
- RU ingress / RF reserve work is currently backlog-only
- do not resume `mini` ingress experiments, do not provision `rf1`, and do not treat this contour as active work unless the product owner explicitly asks to return to it
- `mini` may be unavailable and must not be treated as a guaranteed RU probe origin
- RU probe readiness itself is a tracked operational dependency for release confidence

## Operator Shell Policy

- prefer `bash` when it is the simplest reliable operator path
- use `powershell` when quoting, Windows path handling, SSH invocation, or local tooling behavior is more reliable there
- pick the shell that reduces operator error for the exact command rather than forcing one shell everywhere

## Sensitive Material Locations

These locations are intentionally preserved and must not be deleted during cleanup:

- `portal_bot/.env`
- `VPN NODE SSH KEYS/`
- `secrets for merchant/`
- `ops-local/`
- `external/client-fork/app/windows/sign.pfx`
- `external/client-fork/app/windows/sign.cer`

Rules:

- do not duplicate secret values into documentation
- do not print raw secrets into commit messages or reports
- document locations and usage only

## Canonical Deploy Scripts

### Backend code deploy

- [remote_deploy_brain_portal_code.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_deploy_brain_portal_code.py)

Typical use:

```powershell
python scripts/remote_deploy_brain_portal_code.py --brain-ip 82.21.114.104 --restart portal-api,portal-bot,portal-helpbot,portal-feedbackbot
```

Repo-side deploy rule:

- the default restart set is `portal-api`, `portal-bot`, `portal-helpbot`, and `portal-feedbackbot`
- the deploy step should be treated as failed if any requested unit does not become `active` after restart

Observer-lite canary install:

```powershell
python scripts/remote_install_node_observer.py --brain-ip 82.21.114.104 --node-code pl --run-now
```

### Static sites deploy

- [remote_deploy_brain_static_sites.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_deploy_brain_static_sites.py)

### Bot token / username switch

- [remote_switch_bot_tokens.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_switch_bot_tokens.py)

### Release orchestration

- [release_orchestrator.py](C:/Users/kiwun/Documents/ai/VPN/scripts/release_orchestrator.py)

### Release handoff sync

- [remote_brain_apply_release_handoff.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_brain_apply_release_handoff.py)

### API-only lifecycle smoke

- [api_lifecycle_smoke.py](C:/Users/kiwun/Documents/ai/VPN/scripts/api_lifecycle_smoke.py)

### Observer-lite node install

- [remote_install_node_observer.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_install_node_observer.py)

### Publishing and signing guide

- [publishing-and-signing-guide.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/publishing-and-signing-guide.md)

### Monitoring and visibility guide

- [monitoring-and-visibility.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/monitoring-and-visibility.md)

## Operator Handoff Runbooks

Use these when the release is blocked on one narrow operational step and the next person needs a simple checklist instead of the full guide:

- [Android Production Signing Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-production-signing-handoff.md)
- [Android Physical Device Audit Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-physical-device-audit-handoff.md)
- [Email Delivery Webhook Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/email-delivery-webhook-handoff.md)
- [Release Links And Final Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/release-links-and-final-handoff.md)
- [RU Origin Probe Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/ru-origin-probe-handoff.md)

### External RU probe runner

- [ru_probe_runner.py](C:/Users/kiwun/Documents/ai/VPN/scripts/ru_probe_runner.py)

Typical use from the external RU host:

```powershell
python scripts/ru_probe_runner.py --reserve-host rf1.pokrov.space --probe-host mini --out ops-local/ru-probe.json
python scripts/render_ru_probe_report.py --input ops-local/ru-probe.json
```

### RF Reserve Note

- [remote_install_mini_canary_stack.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_install_mini_canary_stack.py)

Status:

- previous `mini` canary experiments and the `rf1` reserve-bridge idea are now in backlog
- keep the script as historical/operator tooling only
- do not run this script, do not continue the experiment, and do not evolve the contour unless the product owner explicitly requests a return to this work

### Feedback bot service install

- [remote_install_feedbackbot_service.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_install_feedbackbot_service.py)

## Transport Rollout And Node Shaping

The transport rollout stays additive: the current Reality path remains in place while app-first cohorts are moved to `grpc_443_primary` through rollout policy and per-node transport catalogs.

Transport policy rule:

- `nodes.transport_profiles_json` is the canonical per-node transport catalog for rollout and should carry the fixed profile set `legacy_reality_fallback`, `grpc_443_primary`, `reserve_xhttp_cdn`, and `operator_lab`
- legacy node fields such as `inbound_id`, `vless_port`, and `reality_*` remain compatibility input and should synthesize `legacy_reality_fallback` when the transport catalog is empty
- `AppSetting.network_rollout_config` is the operator-controlled rollout source of truth for `transport_profile`, `dns_policy`, `routing_mode_default`, and `ip_version_preference`
- `network_rollout_config` is a JSON policy blob with `version`, `defaults`, `carrier_overrides`, `cohort_overrides`, `reserve_xhttp_cdn`, `operator_lab`, `package_catalog_feed`, `routing_rules_feed`, and `support_recovery_order`
- `defaults` pin `routing_mode_default=all_except_ru`, `transport_profile=legacy_reality_fallback`, and `dns_policy=ru_direct_split` until canary cohorts are explicitly approved
- `carrier_overrides` and `cohort_overrides` may only change `transport_profile`, `dns_policy`, `routing_mode_default`, and `ip_version_preference`
- `reserve_xhttp_cdn` stays opt-in, disabled by default, and is intended only as a reserve path on eligible nodes until a later rollout wave promotes it explicitly
- `operator_lab` remains allowlist-only, carries `enabled`, `allowlist_install_ids`, `allowlist_tg_ids`, `allowlist_node_codes`, and `expires_at`, and must stay hidden from public UI and mass session/profile payloads
- app-managed session and profile delivery should use the rollout-selected transport profile, while manual/export compatibility links stay on `legacy_reality_fallback` until the share-link parity wave lands
- `GET /api/client/profile/managed` is the primary app-managed provisioning endpoint; `subscription_url` stays manual/import fallback only

Rollout order:

1. Wave 0, code-first
   - migrate `nodes.transport_profiles_json`
   - backfill `legacy_reality_fallback` from the legacy node fields
   - seed `reserve_xhttp_cdn` metadata on eligible nodes without enabling it for public cohorts
   - ship backend changes for multi-inbound sync and `network_rollout_config`
   - expose rollout config and node transport health in admin/web surfaces
   - update the canonical docs in this task
2. Wave 1, deploy-first
   - run local tests and smokes
   - run `release_orchestrator.py --gates-only`
   - deploy the brain portal code
   - deploy static sites if the admin surface or public visibility changed
   - run `verify_brain_ready.py`
3. Wave 2, infra canary
   - choose one premium node as the canary
   - install the node-local transport front on public `:443` with `scripts/remote_apply_transport_front.py`
   - move the live `legacy_reality_fallback` listener behind the transport front on a loopback backend port
   - add the `grpc_443_primary` inbound on its loopback backend port behind the same transport front
   - prepare the reserve backend `reserve_xhttp_cdn` on its loopback port and SNI mapping, but keep the rollout flag disabled unless the explicit reserve test is requested
   - seed the node transport catalog with `legacy_reality_fallback`, `grpc_443_primary`, and reserve metadata
   - run `scripts/remote_transport_front_smoke.py` against the canary SNI names before cohort enablement
   - apply the qdisc profile and run the saturation smoke
   - enable `grpc_443_primary` only for a small RU-risk allowlist through `network_rollout_config`
4. Wave 3, fleet expansion
   - repeat inbound and qdisc rollout on the remaining premium nodes
   - move failover by `subnet`, then by `hoster_family`, then by country
   - after parity, switch `defaults.transport_profile` to `grpc_443_primary` for the RU-risk cohort
5. Wave 4, operator lab
   - add `operator_lab` on one controlled node only
   - open it through allowlist entries only
   - keep it out of public UI and non-operator payloads

Rollback shape:

- restore `defaults.transport_profile` to `legacy_reality_fallback`
- set `operator_lab.enabled=false`
- run `scripts/remote_apply_node_qdisc.py rollback`
- keep `nodes.transport_profiles_json` in place as dormant metadata instead of deleting it

Reserve-path rule:

- `reserve_xhttp_cdn` is prepared for operator-directed fallback only
- current reserve SNI is `cdn.connect.pokrov.space`
- the current transport-front template maps that reserve SNI to the loopback reserve backend
- when the reserve profile is selected, the client uses `transport_kind=xhttp` and `engine_hint=xray`; this does not change the default public `sing-box` path

Node shaping repo truth:

- `infra/node-qdisc-profiles.json` records `node_code`, `iface`, `uplink_mbps`, `target_rate_mbps`, and `preferred_qdisc`
- `target_rate_mbps` is fixed at `85%` of the confirmed sustainable uplink for each live node
- `scripts/remote_apply_node_qdisc.py` supports `install`, `apply`, `show`, `disable`, `rollback`, and `uninstall`
- `install` and `disable` control reboot persistence through `infra/portal-node-qdisc.service`; `rollback` removes the active qdisc without deleting the repo-truth profile
- node selection must come from explicit `NODE_CODE` provisioning or the built-in alias normalization such as `PLnode -> pl` and `FREENLnode -> free`
- if `sch_cake` is present, the script applies `CAKE nat triple-isolate`
- if `sch_cake` is unavailable, the script falls back to `fq_codel` and must report that fallback explicitly
- `scripts/remote_node_qdisc_smoke.py` runs one heavy egress flow plus parallel small HTTPS probes, records p95 latency / TTFB, and fails the gate if the heavy flow never materializes or starvation exceeds the configured thresholds
- `infra/portal-node-qdisc.service` restores the configured qdisc after reboot

## Current Local Build Matrix

Canonical repo-local build and packaging commands for this wave:

- `python scripts/run_client_release_gate.py preflight`
- `python scripts/run_client_release_gate.py build --target windows`
- `python scripts/run_client_release_gate.py build --target android-apk`
- `python scripts/run_client_release_gate.py build --target android-aab`
- `dart pub global run msix:create --build-windows false`
- `Push-Location external/client-fork/app; powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\package_windows.ps1"; Pop-Location`

Current local-build notes:

- Android public promotion is still blocked until `python scripts/android_localhost_audit.py` is run against a release-installed build on physical hardware
- raw Android release artifacts are produced under `external/client-fork/app/build/app/outputs/...`; their presence alone does not prove production signing or publication readiness
- local Android builds may fall back to the debug keystore when the production release keystore is unavailable; that is valid for local smoke only, not for publication
- production Android signing still requires the local `android/key.properties` path or equivalent secret injection outside git
- raw Windows release outputs are produced under `external/client-fork/app/build/windows/x64/runner/Release/...`
- client `out/` is the canonical packaged Windows bundle layout, but it is populated only by `external/client-fork/app/scripts/package_windows.ps1`; an empty `out/` does not mean raw build outputs are missing
- after the final green rerun, retain the canonical packaged bundle in `external/client-fork/app/out/` and clean raw `build/` and `dist/` outputs as disposable local artifacts
- the repo-local MSIX smoke path is intentionally unsigned by default through `sign_msix: false`; signing still belongs to the release handoff
- public Windows and Android labels, Windows package identity, executable naming, installer names, and protocol activation must read as `POKROV` / `pokrov`
- explicit legacy compatibility handlers such as hidden Android import continuity may remain only where separately documented and not as the Windows packaged identity truth
- `external/client-fork/app/scripts/package_windows.ps1` uses the client repo root as its working directory and now inspects the packaged `MSIX` via a temporary `.zip` copy because `Expand-Archive` cannot read `.msix` directly

Current brand-source rule for release assets:

- start raster regeneration from [external/logogo.png](C:/Users/kiwun/Documents/ai/VPN/external/logogo.png)
- start vector regeneration from [logo/logoclear.svg](C:/Users/kiwun/Documents/ai/VPN/logo/logoclear.svg) and [logo/logowithtext.svg](C:/Users/kiwun/Documents/ai/VPN/logo/logowithtext.svg)
- do not ship stale derived launcher, splash, tray, favicon, or share-preview assets after those masters change

## Current Unclosed Release Blockers

As of `2026-04-15`, the documented local green gate snapshot is not the same thing as a finished public release handoff.

Still required before public promotion or node enablement:

- live deploy of the released backend and static surfaces
- live node enablement where the rollout depends on new node state
- separate `current-origin check`, `brain-origin check`, and `RU-origin check` evidence lines
- Android production signing instead of debug-keystore fallback
- confirmation that the final signed Android artifacts are actually production-ready
- physical-device `python scripts/android_localhost_audit.py` on the release-installed Android build
- live Windows and Android scenario evidence on real devices and in a real network after the current UI pass
- live transactional sender readiness for public email registration or recovery mail, including real mailbox or provider credentials and webhook configuration
- final release handoff with published URLs, runtime sync, and redeployed static download surfaces

Release handoff shortcuts:

- Android signing: [android-production-signing-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-production-signing-handoff.md)
- Android physical-device audit: [android-physical-device-audit-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-physical-device-audit-handoff.md)
- email sender and webhook: [email-delivery-webhook-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/email-delivery-webhook-handoff.md)
- release URL sync: [release-links-and-final-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/release-links-and-final-handoff.md)
- RU-origin evidence: [ru-origin-probe-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/ru-origin-probe-handoff.md)

## Release Rule

For release-oriented work, default completion includes:

- code or config change
- tests or smoke checks
- push
- deploy

If deploy is blocked, record:

- what changed
- what was verified
- what remains blocked
- rollback-safe state

## Current Deploy Contour

The documented full release wrapper can currently chain:

- local gates
- optional `APP_*` runtime handoff sync
- backend deploy to `brain`
- static marketing and webapp deploy
- optional qdisc or observer rollout helpers
- brain-local readiness verification

Current contour rule:

- `scripts/release_orchestrator.py` does not publish Android or Windows binaries, does not create final signed artifacts, and does not by itself close the public release handoff
- `scripts/verify_brain_ready.py` is brain-local verification, not a replacement for separate `current-origin` or `RU-origin` evidence
- transport or node rollout helpers can support enablement, but they do not by themselves prove live node enablement unless the runtime pool and smoke evidence are also updated

Current product release scope:

- full public `v1`: `Android + Windows`
- `iOS` and `macOS`: readiness-only in this wave

## Post-Deploy Checks

At minimum, verify:

- backend health endpoint
- app-first `start-trial`
- support ticket creation
- canonical `connect.pokrov.space` subscription endpoint availability
- legacy `api.pokrov.space` subscription compatibility
- `GET /api/client/apps`
- `GET /api/payments/providers`
- checkout continuation from session or ticket
- Telegram linking / channel bonus path
- API-only lifecycle smoke for bonuses, checkout order creation, callback success, and post-payment dashboard state
- `portal-api`, `portal-bot`, and `portal-helpbot` service status
- `portal-feedbackbot` service status
- `verify_brain_ready.py` should fail the repo-side handoff if any required control-plane unit is inactive, if required listeners on `443` or `8444` are missing, or if the built-in HTTP and subscription probes fail
- transport rollout verification on the canary node with `scripts/remote_apply_node_qdisc.py show`
- transport front verification with `scripts/remote_transport_front_smoke.py`
- `tc -s qdisc` on the shaped interface
- `scripts/remote_node_qdisc_smoke.py` results for heavy-flow saturation and small-probe latency
- when observer-lite is enabled on any node, `portal-node-observer.timer` freshness on that node plus `/api/admin/metrics/status` and `/api/admin/nodes/health` observer fields
- after any REALITY target rotation, verify the node inbound `dest/serverNames`, the `brain` `nodes.reality_sni` row, and `python scripts/predeploy_node_readiness.py --brain-ip 82.21.114.104` in the same handoff

Release gate rule:

- full `release_gate_check.py` should stay green; by default that means the release `pytest` matrix, admin/auth regression, `client_security_smoke.py`, `python scripts/run_client_release_gate.py test --suite full`, `api_lifecycle_smoke.py`, link checks, marketing/webapp production builds, admin webapp smoke, browser E2E from `webapp/e2e/`, and `ui_visual_smoke.py`
- `python scripts/run_client_release_gate.py preflight` should be green before trusting any Flutter gate result; a dirty or drifted `libcore` checkout is a release blocker even if other repo-local tests happen to pass
- marketing release readiness also requires `python scripts/check-links.py` and `python scripts/ui_visual_smoke.py` to stay green after every CTA, legal, SEO, or branding change
- `verify_brain_ready.py` should validate both the canonical connect host and the legacy API compatibility path before a release is considered healthy
- the default full backend deploy and verify contour should include `portal-feedbackbot`, not just `portal-api`, `portal-bot`, and `portal-helpbot`
- `client_security_smoke.py` is the static repo-level gate for default local-surface settings, routing preset groundwork, and known localhost control paths; it does not replace the Android release-build port and reachability audit
- set `ANDROID_AUDIT_SERIAL=<device-serial>` when running `release_gate_check.py` if you want the opt-in adb localhost audit folded into the same markdown report
- set `ANDROID_AUDIT_CONNECT_WAIT_SEC` and `ANDROID_AUDIT_DISCONNECT_WAIT_SEC` when the adb localhost audit needs non-default timing in the same report
- add `--client-platform-gates windows,android-apk,android-aab` or set `CLIENT_PLATFORM_GATES` when you want the same markdown report to include artifact-producing client builds
- the latest documented `release_orchestrator.py --gates-only` success is a local-only proof and does not replace live deploy, live node enablement, or three-origin network evidence
- Android public release must also include a release-build localhost-listener audit covering proxy, DNS, command-server, and admin/control surfaces before connect, after connect, and after disconnect; green repo/static gates are necessary but not sufficient
- the Android release gate fails if an unauthenticated local SOCKS, HTTP proxy, Clash API, command, or similar admin surface remains reachable
- public client release validation must include routing preset smoke for `Full tunnel` and `All except RU`, plus DNS split and leak checks on Android and Windows
- `Blocked only` remains internal or compatibility-only until geo assets and DNS behavior are complete enough for honest public verification

Current local gate entrypoints:

```powershell
python scripts/release_gate_check.py
python scripts/release_gate_check.py --client-platform-gates windows,android-apk,android-aab
python scripts/release_orchestrator.py --gates-only
```

Notes:

- `release_gate_check.py` is the canonical local report generator for the public-v1 gate set.
- `release_gate_check.py --quick` swaps the default full client Flutter suite for `python scripts/run_client_release_gate.py test --suite portal`.
- on Windows, `release_gate_check.py` injects a repo-local disposable `--basetemp` for its `python -m pytest ...` gates so a broken workstation-level `%TEMP%\\pytest-of-<user>\\pytest-current` symlink does not pollute the release handoff tail.
- `release_orchestrator.py --gates-only` is the one-command wrapper for the same gate pack, but it intentionally exits before release handoff sync, backend deploy, static deploy, and post-deploy verify.
- latest verified local run: `python scripts/release_orchestrator.py --gates-only` exited `0` on `2026-04-13`; see `docs/audit-artifacts/release_gate_report.md` for the current local gate snapshot
- pass `--brain-ip 82.21.114.104` to either command when you also want `predeploy_node_readiness.py` folded into the same run.
- `--release-env-file` cannot be combined with `--gates-only`; use the full `release_orchestrator.py` flow when you need runtime `APP_*` download URLs synced onto brain before deploy or verify.
- the full `release_orchestrator.py` flow uses the same default backend restart set as `remote_deploy_brain_portal_code.py`, including `portal-feedbackbot`
- `--brain-ip` is required for the full remote contour, including release handoff sync, backend deploy, post-deploy verify, observer-timer ensure, metrics-timer ensure, and qdisc rollout lanes
- without `ANDROID_AUDIT_SERIAL`, a green gate report does not replace the required on-device Android localhost audit
- emulator-backed adb audits are preflight only and do not clear public Android release
- when node reachability is part of a release handoff, report `current-origin`, `brain-origin`, and `RU-origin` results separately instead of collapsing them into one verdict

## Telegram OAuth / OIDC Runtime

`POKROV` now supports Telegram OAuth / OIDC for web login.

Runtime env on `brain` must include:

- `TELEGRAM_OAUTH_CLIENT_ID`
- `TELEGRAM_OAUTH_CLIENT_SECRET`
- `TELEGRAM_OAUTH_REDIRECT_URI`

Current canonical redirect URI:

- `https://app.pokrov.space/`

Current trusted origins in `BotFather` should include:

- `https://pokrov.space/`
- `https://app.pokrov.space/`

Current official public surfaces:

- marketing and public site: `https://pokrov.space/`
- user cabinet and web login: `https://app.pokrov.space/`
- public API host: `https://api.pokrov.space/`

Hostname role policy:

- `pokrov.space` is the canonical public hostname family
- `kiwunaka.space` remains compatibility-only for migration and older subscriptions
- support, onboarding, release notes, and new links must always prefer `pokrov.space`

Web runtime rule:

- `https://api.pokrov.space/` is the canonical API base for browser flows
- `app.pokrov.space` may host the UI, but it must not be treated as an API origin when it returns HTML

Migration-only legacy note:

- `kiwunaka.space` hosts remain compatibility surfaces for older subscriptions during cutover
- do not use `kiwunaka.space` in new release copy, onboarding copy, or fresh distribution links

Monitoring note:

- the external RU probe runbook, hostname migration visibility, and device or Telegram visibility rules live in [Monitoring And Visibility](C:/Users/kiwun/Documents/ai/VPN/docs/operations/monitoring-and-visibility.md)

Safe deploy note:

- use local env injection for the client secret
- do not write raw OAuth secrets into docs, commits, or terminal summaries

## Client Build Artifacts

Current client workspace:

- [external/client-fork/app](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app)

Important outputs:

- raw Android outputs under `external/client-fork/app/build/app/outputs/...`
- raw Windows outputs under `external/client-fork/app/build/windows/x64/runner/Release/...`
- packaged Windows bundle in client `out/` after `external/client-fork/app/scripts/package_windows.ps1`

Do not delete release artifacts if they are still being distributed or verified.

Related guide:

- [Publishing And Signing Guide](C:/Users/kiwun/Documents/ai/VPN/docs/operations/publishing-and-signing-guide.md)

## POKROV Client Release Path

Canonical client release workflow:

- `external/client-fork/app/.github/workflows/fork-android-windows-release.yml`

Default release slug in this repo:

- `pokrov`

Default artifact names:

- `pokrov-android-universal.apk`
- `pokrov-android-market.aab`
- `pokrov-windows-setup-x64.exe`
- `pokrov-windows-setup-x64.msix`
- `pokrov-windows-portable-x64.zip`

Current public download surfaces expose only:

- Android `Play` / `APK` / mirror URL
- Windows `EXE` / mirror URL
- install/docs fallback via `APP_DOCS_URL`

Treat `AAB`, `MSIX`, and portable `ZIP` as release/store/operator artifacts unless a later runtime payload and public surface explicitly expose them.

Canonical local client verification commands:

```powershell
python scripts/run_client_release_gate.py preflight
python scripts/run_client_release_gate.py test --suite portal
python scripts/run_client_release_gate.py test --suite full
python scripts/run_client_release_gate.py build --target windows
python scripts/run_client_release_gate.py build --target android-apk
python scripts/run_client_release_gate.py build --target android-aab
```

Client verification notes:

- `run_client_release_gate.py` is the canonical root-level wrapper for client release verification and enters `external/client-fork/app` automatically.
- `python scripts/run_client_release_gate.py preflight` is the fastest repo-local proof that `external/client-fork/app/libcore` is present, pinned to the parent repo SHA, and clean before Flutter work begins.
- on Windows, `python scripts/run_client_release_gate.py test --suite full` bootstraps `flutter build windows --release` first when `sqlite3.dll` is missing, so the full Flutter suite does not rely on a manual `PATH` step.
- if `preflight` fails, inspect `git -C external/client-fork/app/libcore status --short` and `git -C external/client-fork/app/libcore diff --stat`; that fix belongs in the canonical client repo instead of as an ad hoc root-repo override.
- direct `flutter` commands inside `external/client-fork/app` remain useful for focused inner-loop work, but the wrapper commands above are the release-workflow truth documented for operators and CI.

Signed release path:

- Android signing requires `ANDROID_SIGNING_KEY`, `ANDROID_SIGNING_STORE_PASSWORD`, `ANDROID_SIGNING_KEY_PASSWORD`, `ANDROID_SIGNING_KEY_ALIAS`
- Windows signing requires `WINDOWS_SIGNING_KEY`, `WINDOWS_SIGNING_PASSWORD`
- without those secrets, local builds are valid only as unsigned smoke artifacts
- keep Android `applicationId` on `space.pokrov.vpn`, but keep Gradle `namespace` on `com.hiddify.hiddify` until the Kotlin package tree is migrated too

Android release-block rule:

- do not publish Android as a trusted public release until the release-build audit proves that localhost proxy, local DNS, libbox command, Clash API, and equivalent control surfaces are either unavailable to other apps or protected to an acceptable standard
- if that proof is missing, keep Android in blocked state even if the app otherwise builds and signs correctly

Release handoff after publishing artifacts:

```powershell
pwsh external/client-fork/scripts/release_handoff.ps1 `
  -AndroidApkUrl "https://github.com/<org>/<repo>/releases/download/<tag>/pokrov-android-universal.apk" `
  -WindowsExeUrl "https://github.com/<org>/<repo>/releases/download/<tag>/pokrov-windows-setup-x64.exe"
python external/client-fork/scripts/check_release_urls.py --env-file external/client-fork/release-links.env
```

Then copy the resulting URLs into runtime env:

- `APP_ANDROID_PLAY_URL`
- `APP_ANDROID_APK_URL`
- `APP_ANDROID_MIRROR_URL`
- `APP_WINDOWS_EXE_URL`
- `APP_WINDOWS_MIRROR_URL`
- `APP_DOCS_URL`

Preferred automation path:

```powershell
python scripts/remote_brain_apply_release_handoff.py `
  --brain-ip 82.21.114.104 `
  --env-file external/client-fork/release-links.env
```

Or as part of the main rollout:

```powershell
python scripts/release_orchestrator.py `
  --brain-ip 82.21.114.104 `
  --release-env-file external/client-fork/release-links.env
```

Distribution rule until store URLs are live:

- GitHub release artifacts are the canonical Android and Windows binary source
- runtime app, bot, and authenticated WebApp download surfaces must read from the same release handoff URLs
- `remote_brain_apply_release_handoff.py` updates backend runtime env on brain; it does not rebuild static exports by itself
- if public Android or Windows URLs changed, rebuild and redeploy static marketing outputs so `NEXT_PUBLIC_APP_*` stays aligned with the same release handoff values

## Existing User Cutover

Release communication for existing users must explicitly say:

- `POKROV` is the official public app line
- Android and Windows should be treated as a fresh install path
- existing `kiwunaka.space` profiles stay temporarily compatible during migration, but they are legacy compatibility hosts rather than current public entrypoints
- users should install the new app, connect successfully, and only then remove the old app

Recommended migration order:

1. publish new Android and Windows artifacts
2. update runtime download URLs from release handoff
3. post migration notice in `@pokrov_vpn`
4. answer support with the same canonical instructions
5. keep old `kiwunaka.space` subscription hosts active until most users rotate to new profiles

Operator message template:

```text
POKROV is now the official app.

If you used the old app, install the new POKROV release as a separate app.
Do not delete the old app first.

1. Install POKROV
2. Open it and activate or import your access
3. Confirm that the new app connects successfully
4. Only after that remove the old app if you want

Old subscription links continue to work temporarily during migration.
If you need help, contact @pokrov_supportbot.
```

## Current Telegram Runtime Alignment

Current operational state:

- active public channel: `@pokrov_vpn`
- `@pokrov_vpnbot` is an administrator in that channel
- `@pokrov_feedbackbot` handles feedback intake for reviews and product suggestions
- production env should keep `PUBLIC_CHANNEL=pokrov_vpn`
- production env should keep `NEWS_CHANNEL_ID=@pokrov_vpn`

Post-deploy checks should also confirm:

- the public review feed loads with masked usernames
- featured review cards on the public homepage use the approved review copy
- download links across app, bot, and authenticated WebApp point to the same current Android and Windows artifacts
- marketing homepage download CTA point to the current built release URL or the install/docs fallback, never directly to `connect.pokrov.space`
- public `Открыть кабинет` CTA on `pokrov.space` points to `https://app.pokrov.space/`
- public pricing CTA enter through `https://pokrov.space/checkout/` with plan context, then continue via personal cabinet or Telegram route
- `robots.txt`, `sitemap.xml`, `manifest.webmanifest`, `favicon.ico`, and `apple-icon.png` return dedicated content instead of homepage HTML
- public homepage and SEO landing pages emit canonical, Open Graph, Twitter, and JSON-LD metadata
- node health findings are reported with explicit `current-origin`, `brain-origin`, and `RU-origin` check labels
