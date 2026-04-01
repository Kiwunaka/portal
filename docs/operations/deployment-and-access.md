# Deployment And Access

Last updated: 2026-03-31

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
python scripts/remote_deploy_brain_portal_code.py --brain-ip 82.21.114.104 --restart portal-api,portal-bot,portal-helpbot
```

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

### API-only lifecycle smoke

- [api_lifecycle_smoke.py](C:/Users/kiwun/Documents/ai/VPN/scripts/api_lifecycle_smoke.py)

### Observer-lite node install

- [remote_install_node_observer.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_install_node_observer.py)

### Publishing and signing guide

- [publishing-and-signing-guide.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/publishing-and-signing-guide.md)

### Monitoring and visibility guide

- [monitoring-and-visibility.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/monitoring-and-visibility.md)

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
- when observer-lite is enabled on any node, `portal-node-observer.timer` freshness on that node plus `/api/admin/metrics/status` and `/api/admin/nodes/health` observer fields

Release gate rule:

- full release gate should include backend tests, `api_lifecycle_smoke.py`, marketing/webapp builds, and browser E2E from `webapp/e2e/`
- `verify_brain_ready.py` should validate both the canonical connect host and the legacy API compatibility path before a release is considered healthy

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

- `out/` inside the client repo
- Android APK
- Windows EXE / portable ZIP / MSIX

Do not delete release artifacts if they are still being distributed or verified.

Related guide:

- [Publishing And Signing Guide](C:/Users/kiwun/Documents/ai/VPN/docs/operations/publishing-and-signing-guide.md)

## POKROV Client Release Path

Canonical client release workflow:

- `external/client-fork/app/.github/workflows/fork-android-windows-release.yml`

Default release slug in this repo:

- `pokrov-vpn`

Default artifact names:

- `pokrov-vpn-android-universal.apk`
- `pokrov-vpn-android-market.aab`
- `pokrov-vpn-windows-setup-x64.exe`
- `pokrov-vpn-windows-setup-x64.msix`
- `pokrov-vpn-windows-portable-x64.zip`

Local build-smoke commands:

```powershell
cd external/client-fork/app
flutter build windows --release
$env:PATH = "$PWD\build\windows\x64\runner\Release;$env:PATH"
flutter test
flutter build apk --release
flutter build appbundle --release
```

Windows note:

- local `flutter test` for this client expects `sqlite3.dll` from the Windows runner output, so build `windows --release` first and prepend `build\windows\x64\runner\Release` to `PATH` before running the full suite

Signed release path:

- Android signing requires `ANDROID_SIGNING_KEY`, `ANDROID_SIGNING_STORE_PASSWORD`, `ANDROID_SIGNING_KEY_PASSWORD`, `ANDROID_SIGNING_KEY_ALIAS`
- Windows signing requires `WINDOWS_SIGNING_KEY`, `WINDOWS_SIGNING_PASSWORD`
- without those secrets, local builds are valid only as unsigned smoke artifacts
- keep Android `applicationId` on `space.pokrov.vpn`, but keep Gradle `namespace` on `com.hiddify.hiddify` until the Kotlin package tree is migrated too

Release handoff after publishing artifacts:

```powershell
pwsh external/client-fork/scripts/release_handoff.ps1 `
  -AndroidApkUrl "https://github.com/<org>/<repo>/releases/download/<tag>/pokrov-vpn-android-universal.apk" `
  -WindowsExeUrl "https://github.com/<org>/<repo>/releases/download/<tag>/pokrov-vpn-windows-setup-x64.exe"
python external/client-fork/scripts/check_release_urls.py --env-file external/client-fork/release-links.env
```

Then copy the resulting URLs into runtime env:

- `APP_ANDROID_PLAY_URL`
- `APP_ANDROID_APK_URL`
- `APP_ANDROID_MIRROR_URL`
- `APP_WINDOWS_EXE_URL`
- `APP_WINDOWS_MIRROR_URL`
- `APP_DOCS_URL`

Distribution rule until store URLs are live:

- GitHub release artifacts are the canonical Android and Windows binary source
- app, webapp, and bot download surfaces must read from the same release handoff URLs

## Existing User Cutover

Release communication for existing users must explicitly say:

- `POKROV VPN` is the new official app line
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
POKROV VPN is now the official app.

If you used the old app, install the new POKROV VPN release as a separate app.
Do not delete the old app first.

1. Install POKROV VPN
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
- download links across app, webapp, and bot point to the same current Android and Windows artifacts
