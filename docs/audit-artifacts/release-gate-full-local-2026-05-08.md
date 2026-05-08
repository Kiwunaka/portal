# Release Gate Report

- Generated at: `2026-05-08 11:45:24`
- Status: `PASS`
- Gate set: `default`
- Brain IP supplied: `no`
- Client platform gates: `none`
- Android audit required by selected gates: `no`

## Summary

| Gate | Exit code | Duration (s) |
|---|---:|---:|
| Release pytest matrix | 0 | 276.42 |
| Admin/auth regressions | 0 | 73.26 |
| Client preflight | 0 | 0.09 |
| Client security smoke | 0 | 0.06 |
| Client Flutter tests | 0 | 36.86 |
| API lifecycle smoke | 0 | 8.13 |
| Public link checks | 0 | 0.10 |
| Marketing production build | 0 | 13.31 |
| Admin webapp smoke | 0 | 0.14 |
| WebApp production build | 0 | 10.84 |
| WebApp Playwright E2E | 0 | 102.68 |
| UI visual smoke | 0 | 0.10 |

## Evidence Classification

| Evidence | Scope | Status | Notes |
|---|---|---|---|
| current-origin check | local default gate set | PASS | Runs on the operator workstation; does not prove brain-origin or RU-origin reachability. |
| brain-origin check | `scripts/verify_brain_ready.py` plus node predeploy readiness | BLOCKED_BY_ACCESS | Requires `--brain-ip` and live SSH/API access; includes control-plane/static probes and node readiness. |
| RU-origin check | external RU probe (`mini` or replacement) | SKIPPED_BY_OPERATOR | Not run by this local gate; requires an external RU probe host and redacted report unless explicitly skipped by operator. |
| Android physical audit | release-build localhost/control-surface audit | BLOCKED_BY_ACCESS | Public Android remains blocked unless this is run on physical hardware with the release build. |
| Runtime app-download smoke | `/api/client/apps` and provider checks | SKIPPED_NO_LIVE_TOKEN | Requires `TELEGRAM_INIT_DATA`; omit raw token values from evidence. |
| Client platform builds | none requested | NOT_REQUESTED | Repo/static gates alone do not create Android or Windows beta artifacts. |

## Command Tails

### Release pytest matrix

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest portal_bot/tests/test_app_first_api.py tests/test_portal_api.py tests/test_worker_retention.py tests/test_observer_service.py tests/test_observer_api.py tests/test_collect_xray_observer.py tests/test_predeploy_node_readiness.py tests/test_smart_connect_api.py tests/test_network_rollout_api.py tests/test_client_security_smoke.py tests/test_smoke_client_apps.py tests/test_admin_webapp_smoke.py tests/test_bot_paywall.py tests/test_marketing_release_readiness.py tests/test_live_probe_scripts.py tests/test_public_beta_post_deploy_probe.py tests/test_public_beta_external_access_preflight.py tests/test_validate_android_physical_audit_evidence.py tests/test_paid_checkout_launch_evidence_check.py tests/test_freekassa_api_probe.py tests/test_freekassa_staging_smoke.py tests/test_prepare_github_release_plan.py tests/test_publish_github_release_assets.py tests/test_public_beta_launch_decision.py tests/test_public_copy_guardrails.py tests/test_reviews_username_masking.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-g1ht3au5`
- Exit: `0`

```text
..................................................................... [ 31%]
........................................................................ [ 63%]
........................................................................ [ 96%]
........                                                                 [100%]
221 passed, 3 subtests passed in 274.87s (0:04:34)
```

### Admin/auth regressions

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest tests/test_api_auth_and_tickets.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-5jt1v95n`
- Exit: `0`

```text
................................................................         [100%]
64 passed in 72.29s (0:01:12)
```

### Client preflight

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/run_client_release_gate.py preflight`
- Exit: `0`

```text
[client-root] path: C:\Users\kiwun\Documents\ai\POKROV-app
[client-root] android shell: C:\Users\kiwun\Documents\ai\POKROV-app\apps\android_shell
[client-root] windows shell: C:\Users\kiwun\Documents\ai\POKROV-app\apps\windows_shell
[client-root] validate seed: C:\Users\kiwun\Documents\ai\POKROV-app\scripts\validate-seed.ps1
[client-root] bootstrap workspace: C:\Users\kiwun\Documents\ai\POKROV-app\scripts\bootstrap-workspace.ps1
[client-root] run tests: C:\Users\kiwun\Documents\ai\POKROV-app\scripts\run-tests.ps1
[client-root] build windows release: C:\Users\kiwun\Documents\ai\POKROV-app\scripts\build-windows-release.ps1
[ok] POKROV-app gate root is present
```

### Client security smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/client_security_smoke.py`
- Exit: `0`

```text
[check] product contract: C:\Users\kiwun\Documents\ai\POKROV-app\config\product-contract.seed.json
[check] runtime profile: C:\Users\kiwun\Documents\ai\POKROV-app\config\runtime-profile.seed.json
[check] runtime artifacts: C:\Users\kiwun\Documents\ai\POKROV-app\config\runtime-artifacts.seed.json
[check] Android manifest: C:\Users\kiwun\Documents\ai\POKROV-app\apps\android_shell\android\app\src\main\AndroidManifest.xml
[check] Android build.gradle: C:\Users\kiwun\Documents\ai\POKROV-app\apps\android_shell\android\app\build.gradle
[check] Windows release seed: C:\Users\kiwun\Documents\ai\POKROV-app\config\windows-release.seed.json
[pass] client security smoke checks passed
```

### Client Flutter tests

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/run_client_release_gate.py test --suite full`
- Exit: `0`

```text
io.flutter.plugins.urllauncher.UrlLauncherTest > canLaunch_createsIntentWithPassedUrl PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > launch_returnsTrue PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > openWebView_handlesEnableDomStorage PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > openWebView_handlesEnableShowTitle PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > canLaunch_returnsFalse PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > launch_throwsForNoCurrentActivity PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > openWebView_returnsFalse PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > closeWebView_closes PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > canLaunch_returnsTrue PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > openWebView_handlesHeaders PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > openWebView_opensUrlInCustomTabsWithCORSAllowedHeader PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > launch_returnsFalse PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > openWebView_opensUrlInWebViewIfRequested PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > launch_createsIntentWithPassedUrl PASSED

io.flutter.plugins.urllauncher.WebViewActivityTest > extractHeaders_returnsEmptyMapWhenHeadersBundleNull PASSED

Deprecated Gradle features were used in this build, making it incompatible with Gradle 9.0.

You can use '--warning-mode all' to show the individual deprecation warnings and determine if they come from your own scripts or plugins.

For more on this, please refer to https://docs.gradle.org/8.3/userguide/command_line_interface.html#sec:command_line_warnings in the Gradle documentation.

BUILD SUCCESSFUL in 7s
87 actionable tasks: 5 executed, 82 up-to-date
Workspace Flutter and Android unit tests passed.
[client-gate] C:\Windows\System32\WindowsPowerShell\v1.0\powershell.EXE -NoProfile -ExecutionPolicy Bypass -File C:\Users\kiwun\Documents\ai\POKROV-app\scripts\run-tests.ps1 (cwd=C:\Users\kiwun\Documents\ai\POKROV-app)
```

### API lifecycle smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/api_lifecycle_smoke.py`
- Exit: `0`

```text
.
----------------------------------------------------------------------
Ran 1 test in 7.310s

OK
```

### Public link checks

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/check-links.py`
- Exit: `0`

```text
[PASS] marketing\src\app\robots.ts: Marketing SEO route is present
[PASS] marketing\src\app\sitemap.ts: Marketing SEO route is present
[PASS] marketing\src\app\manifest.ts: Marketing SEO route is present
[PASS] marketing\public\opengraph-image.png: Marketing SEO route is present
[PASS] marketing\public\twitter-image.png: Marketing SEO route is present
[PASS] marketing\public\favicon.ico: Marketing SEO route is present
[PASS] marketing\public\apple-icon.png: Marketing SEO route is present
[PASS] marketing\src\components\marketing-landing.tsx: Public marketing CTA no longer routes to connect host
[PASS] marketing\src\components\marketing-landing.tsx: Public cabinet CTA points to webapp host
[PASS] marketing\src\components\marketing-landing.tsx: Pricing CTA stays gated to install/status while release is NO-GO
[PASS] marketing\src\components\marketing-landing.tsx: Marketing footer exposes canonical news channel
[PASS] marketing\src\app\layout.tsx: Layout includes `metadataBase` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `manifest` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `icons` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `apple` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `/favicon.ico` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `/apple-icon.png` metadata wiring
[PASS] marketing\src\components\marketing-landing.tsx: Marketing metadata declares `alternates`
[PASS] marketing\src\components\marketing-landing.tsx: Marketing metadata declares `canonical`
[PASS] marketing\src\components\marketing-landing.tsx: Marketing metadata declares `twitter`
[PASS] marketing\src\components\marketing-landing.tsx: Marketing metadata declares `images`
[PASS] marketing\src\app\checkout\checkout-client.tsx: Checkout gateway uses cabinet-safe fallback instead of connect host
[PASS] marketing\src\app\offer\page.tsx: Legal page avoids direct checkout CTA
[PASS] marketing\src\app\privacy\page.tsx: Legal page avoids direct checkout CTA
[PASS] webapp\src\app\(dashboard)\support\legal\page.tsx: Webapp legal links use absolute marketing URLs
[PASS] portal_bot\api.py: Admin campaign link builder marks public checkout as safe fallback
[PASS] portal_bot\api.py: Compat env-flag for numeric subscription fallback is present

Link check passed.
```

### Marketing production build

- Command: `npm.cmd run build`
- Exit: `0`

```text
> pokrov-marketing@0.1.0 build
> next build

  ▲ Next.js 14.2.35

   Creating an optimized production build ...
 ✓ Compiled successfully
   Linting and checking validity of types ...
   Collecting page data ...
   Generating static pages (0/16) ...
   Generating static pages (4/16)
   Generating static pages (8/16)
   Generating static pages (12/16)
 ✓ Generating static pages (16/16)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                              Size     First Load JS
┌ ○ /                                    37.1 kB         133 kB
├ ○ /_not-found                          873 B          88.3 kB
├ ○ /checkout                            8.67 kB         105 kB
├ ○ /devices                             193 B          96.4 kB
├ ○ /install                             193 B          96.4 kB
├ ○ /manifest.webmanifest                0 B                0 B
├ ○ /mobile                              193 B          96.4 kB
├ ○ /offer                               193 B          96.4 kB
├ ○ /privacy                             193 B          96.4 kB
├ ○ /robots.txt                          0 B                0 B
├ ○ /sitemap.xml                         0 B                0 B
├ ○ /telegram                            193 B          96.4 kB
├ ○ /tiktok                              193 B          96.4 kB
└ ○ /youtube                             193 B          96.4 kB
+ First Load JS shared by all            87.5 kB
  ├ chunks/117-c48652218eca60f1.js       31.9 kB
  ├ chunks/fd9d1056-1f1f859026f5f0fa.js  53.6 kB
  └ other shared chunks (total)          1.96 kB


○  (Static)  prerendered as static content
```

### Admin webapp smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/admin_webapp_smoke.py`
- Exit: `0`

```text
Admin WebApp smoke passed.
```

### WebApp production build

- Command: `npm.cmd run build`
- Exit: `0`

```text
  Generating static pages using 19 workers (0/31) ...
  Generating static pages using 19 workers (7/31)
  Generating static pages using 19 workers (15/31)
  Generating static pages using 19 workers (23/31)
✓ Generating static pages using 19 workers (31/31) in 393.1ms
  Finalizing page optimization ...

Route (app)
┌ ○ /
├ ○ /_not-found
├ ○ /admin
├ ○ /admin/bonuses
├ ○ /admin/broadcast
├ ○ /admin/dashboard
├ ○ /admin/network
├ ○ /admin/nodes
├ ○ /admin/payments
├ ○ /admin/promos
├ ○ /admin/referrals
├ ○ /admin/release
├ ○ /admin/tickets
├ ○ /admin/users
├ ○ /dashboard
├ ○ /dashboard/downloads
├ ○ /devices
├ ○ /downloads
├ ○ /icon.svg
├ ○ /pricing
├ ○ /profile
├ ○ /redeem
├ ○ /settings
├ ○ /statistics
├ ○ /subscription
├ ○ /subscription/checkout
├ ○ /support
├ ○ /support/legal
└ ○ /support/thread


○  (Static)  prerendered as static content
```

### WebApp Playwright E2E

- Command: `npm.cmd run test:e2e`
- Exit: `0`

```text
  ok 10 e2e\admin-gate.spec.ts:1172:7 › Admin gate › lets admin search, sort, and paginate the users table (1.4s)
  ok 11 e2e\admin-gate.spec.ts:1202:7 › Admin gate › keeps the users filters synced into the URL and restores them on reload (2.3s)
  ok 12 e2e\admin-gate.spec.ts:1229:7 › Admin gate › lets admin safely delete only manual or test users (1.3s)
  ok 13 e2e\admin-gate.spec.ts:1267:7 › Admin gate › shows observer-lite badges, filters, and detail diagnostics (1.2s)
  ok 14 e2e\admin-gate.spec.ts:1308:7 › Admin gate › shows observer-lite empty state instead of misleading zero-only activity (1.9s)
  ok 15 e2e\admin-gate.spec.ts:1324:7 › Admin gate › keeps admin pages clickable and inside the viewport on mobile (3.4s)
  ok 16 e2e\admin-gate.spec.ts:1381:7 › Admin gate › shows node alert labels and probe failure details (1.1s)
  ok 17 e2e\admin-gate.spec.ts:1461:7 › Admin gate › shows node context with separate panel, dataplane, and transport detail (1.6s)
  ok 18 e2e\admin-gate.spec.ts:1538:7 › Admin gate › keeps rollout targeting fields and feed objects intact across save and reload (2.2s)
  ok 19 e2e\admin-gate.spec.ts:1578:7 › Admin gate › lets admin triage a ticket and send a reply using stable status codes (2.6s)
  ok 20 e2e\admin-gate.spec.ts:1612:7 › Admin gate › shows payment ledger and requires an audit note for manual reconciliation (2.4s)
  ok 21 e2e\admin-gate.spec.ts:1647:7 › Admin gate › shows access-key email fulfillment and resends with an audit note (3.0s)
  ok 22 e2e\cabinet-flow.spec.ts:480:7 › Cabinet flow › shows shared POKROV cabinet branding and a site return link (1.6s)
  ok 23 e2e\cabinet-flow.spec.ts:495:7 › Cabinet flow › shows an honest email-unavailable state on the root auth entry (816ms)
  ok 24 e2e\cabinet-flow.spec.ts:508:7 › Cabinet flow › keeps the email entry truthful when live delivery is not configured (775ms)
  ok 25 e2e\cabinet-flow.spec.ts:521:7 › Cabinet flow › keeps the email entry unavailable when the relay secret is missing (824ms)
  ok 26 e2e\cabinet-flow.spec.ts:547:7 › Cabinet flow › supports enabled email register verify login and recovery from the auth entry (10.6s)
  ok 27 e2e\cabinet-flow.spec.ts:602:7 › Cabinet flow › keeps email verification and recovery tokens separate (5.1s)
  ok 28 e2e\cabinet-flow.spec.ts:622:7 › Cabinet flow › reuses an existing web session and lands in the cabinet without showing auth entry again (1.1s)
  ok 29 e2e\cabinet-flow.spec.ts:631:7 › Cabinet flow › stores a silently refreshed web session returned from Telegram auth (1.0s)
  ok 30 e2e\cabinet-flow.spec.ts:650:7 › Cabinet flow › shows a human reauth CTA when the browser session is expired (658ms)
  ok 31 e2e\cabinet-flow.spec.ts:668:7 › Cabinet flow › keeps the dashboard on consumer-safe access actions (1.0s)
  ok 32 e2e\cabinet-flow.spec.ts:684:7 › Cabinet flow › keeps cabinet navigation on native Next.js routing (1.1s)
  ok 33 e2e\cabinet-flow.spec.ts:705:7 › Cabinet flow › shows branded root and cabinet not-found recovery screens (1.2s)
  ok 34 e2e\cabinet-flow.spec.ts:717:7 › Cabinet flow › shows subscription manual connection only as an explicit fallback (1.4s)
  ok 35 e2e\cabinet-flow.spec.ts:734:7 › Cabinet flow › renders runtime connections on devices and keeps statistics as its own safe-summary page (1.4s)
  ok 36 e2e\cabinet-flow.spec.ts:752:7 › Cabinet flow › keeps cabinet copy human and hides node internals (1.5s)
  ok 37 e2e\cabinet-flow.spec.ts:766:7 › Cabinet flow › settings exposes clear Telegram bonus actions without raw account details (2.0s)
  ok 38 e2e\cabinet-flow.spec.ts:781:7 › Cabinet flow › shows honest payment history and Russian checkout continuation copy (1.2s)
  ok 39 e2e\cabinet-flow.spec.ts:799:7 › Cabinet flow › keeps checkout disabled when payment providers are configured but launch evidence is blocked (1.1s)
  ok 40 e2e\cabinet-flow.spec.ts:841:7 › Cabinet flow › keeps checkout start failures public and Russian (1.7s)
  ok 41 e2e\cabinet-flow.spec.ts:886:7 › Cabinet flow › checks and redeems access keys from the cabinet redeem route (2.9s)
  ok 42 e2e\cabinet-flow.spec.ts:951:7 › Cabinet flow › keeps downloads and support flows usable without the app (4.2s)
  ok 43 e2e\cabinet-flow.spec.ts:979:7 › Cabinet flow › loads protected support attachments through authenticated blob fetch (1.6s)
  ok 44 e2e\cabinet-flow.spec.ts:999:7 › Cabinet flow › stays inside a narrow mobile viewport for core cabinet pages (1.7s)
  ok 45 e2e\telegram-login-refresh.spec.ts:8:5 › flags stale Telegram widget payloads before the backend rejects them (1ms)
  ok 46 e2e\telegram-login-refresh.spec.ts:25:5 › keeps fresh Telegram widget payloads on the direct widget login path (0ms)
  ok 47 e2e\telegram-login-refresh.spec.ts:42:5 › treats expired or deprecated Telegram widget errors as refreshable auth (1ms)

  47 passed (1.5m)
```

### UI visual smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/ui_visual_smoke.py`
- Exit: `0`

```text
UI visual smoke passed.
```
