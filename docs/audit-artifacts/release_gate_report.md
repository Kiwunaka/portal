# Release Gate Report

- Generated at: `2026-04-15 18:32:59`
- Status: `PASS`

## Summary

| Gate | Exit code | Duration (s) |
|---|---:|---:|
| Release pytest matrix | 0 | 157.43 |
| Admin/auth regressions | 0 | 65.95 |
| Client security smoke | 0 | 0.11 |
| Client Flutter tests | 0 | 25.49 |
| API lifecycle smoke | 0 | 8.37 |
| Public link checks | 0 | 0.14 |
| Marketing production build | 0 | 68.25 |
| Admin webapp smoke | 0 | 0.17 |
| WebApp production build | 0 | 56.28 |
| WebApp Playwright E2E | 0 | 137.06 |
| UI visual smoke | 0 | 0.15 |

## Command Tails

### Release pytest matrix

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest portal_bot/tests/test_app_first_api.py tests/test_portal_api.py tests/test_worker_retention.py tests/test_observer_service.py tests/test_observer_api.py tests/test_collect_xray_observer.py tests/test_predeploy_node_readiness.py tests/test_admin_webapp_smoke.py tests/test_public_copy_guardrails.py tests/test_reviews_username_masking.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-amyqoemw`
- Exit: `0`

```text
.................................................                        [100%]
49 passed in 156.27s (0:02:36)
```

### Admin/auth regressions

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest tests/test_api_auth_and_tickets.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-j6mkvpwi`
- Exit: `0`

```text
.........................................................                [100%]
57 passed in 64.90s (0:01:04)
```

### Client security smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/client_security_smoke.py`
- Exit: `0`

```text
[check] config options: external\client-fork\app\lib\features\config_option\data\config_option_repository.dart
[check] config options page: external\client-fork\app\lib\features\config_option\overview\config_options_page.dart
[check] routing enum: external\client-fork\app\lib\singbox\model\singbox_config_enum.dart
[check] android control surfaces: external\client-fork\app\android\app\src\main\kotlin\com\hiddify\hiddify\bg\BoxService.kt
[check] android method handler: external\client-fork\app\android\app\src\main\kotlin\com\hiddify\hiddify\MethodHandler.kt
[check] libcore defaults: external\client-fork\app\libcore\config\hiddify_option.go
[check] analytics defaults: external\client-fork\app\lib\core\analytics\analytics_controller.dart
[check] app identity: external\client-fork\app\lib\core\model\app_info_entity.dart
[check] profile identity: external\client-fork\app\lib\features\profile\data\profile_repository.dart
[check] Android manifest: external\client-fork\app\android\app\src\main\AndroidManifest.xml
[check] Windows exe package: external\client-fork\app\windows\packaging\exe\make_config.yaml
[check] Windows msix package: external\client-fork\app\windows\packaging\msix\make_config.yaml
[check] Windows runner resources: external\client-fork\app\windows\runner\Runner.rc
[check] Windows main window: external\client-fork\app\windows\runner\main.cpp
[pass] client security smoke checks passed
```

### Client Flutter tests

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/run_client_release_gate.py test --suite full`
- Exit: `0`

```text
00:11 +72: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/overview/per_app_proxy_page_test.dart: adds a curated preset without dropping manual selections
00:11 +73: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/overview/per_app_proxy_page_test.dart: adds a curated preset without dropping manual selections
00:11 +74: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/overview/per_app_proxy_page_test.dart: adds a curated preset without dropping manual selections
00:11 +75: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/overview/per_app_proxy_page_test.dart: adds a curated preset without dropping manual selections
00:11 +76: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/overview/per_app_proxy_page_test.dart: adds a curated preset without dropping manual selections
00:11 +77: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/overview/per_app_proxy_page_test.dart: adds a curated preset without dropping manual selections
00:12 +78: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/data/portal_trial_activator_test.dart: activateTrial fetches managed manifest first and imports content
00:12 +79: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/data/portal_trial_activator_test.dart: activateTrial falls back to subscription url when managed manifest fetch fails
00:12 +80: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/router/portal_routes_test.dart: portal routes use canonical names and preserve legacy aliases
00:12 +81: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/devices_page_test.dart: shows consumer device overview with current device name
00:13 +82: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/empty_profiles_home_body_test.dart: shows the premium empty home state in English
00:14 +83: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/empty_profiles_home_body_test.dart: shows the premium empty home state in English
00:14 +84: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/empty_profiles_home_body_test.dart: shows the premium empty home state in English
00:14 +85: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/empty_profiles_home_body_test.dart: shows the premium empty home state in English
00:14 +86: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/locations_page_test.dart: shows auto-select and available locations
00:14 +87: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/locations_page_test.dart: shows auto-select and available locations
00:14 +88: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/premium_visuals_golden_test.dart: quick connect panel premium layout stays stable
00:14 +89: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/premium_visuals_golden_test.dart: quick connect panel premium layout stays stable
00:15 +90: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/profile_page_test.dart: shows profile rewards and telegram bonus entry point
00:15 +91: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/profile_page_test.dart: shows profile rewards and telegram bonus entry point
00:15 +92: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/quick_connect_panel_test.dart: shows premium quick connect summary for an active trial
00:16 +93: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/subscription_page_test.dart: shows browser checkout entry as the primary purchase action
00:16 +94: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/subscription_page_test.dart: shows browser checkout entry as the primary purchase action
00:16 +95: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/subscription_page_test.dart: shows browser checkout entry as the primary purchase action
00:16 +96: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/support_page_test.dart: shows in-app support composer and device context
00:16 +97: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/support_page_test.dart: shows in-app support composer and device context
00:16 +98: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/support_page_test.dart: shows in-app support composer and device context
00:16 +99: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/support_page_test.dart: shows in-app support composer and device context
00:16 +100: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/support_page_test.dart: shows in-app support composer and device context
00:17 +101: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/profile/data/profile_repository_test.dart: fetch keeps subscription downloads on the app default user agent
00:17 +102: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/settings/overview/settings_overview_page_test.dart: shows a consumer-first preferences shell with hidden compatibility tools
00:18 +103: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/settings/overview/settings_overview_page_test.dart: shows a consumer-first preferences shell with hidden compatibility tools
00:18 +104: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/settings/overview/settings_overview_page_test.dart: shows a consumer-first preferences shell with hidden compatibility tools
00:18 +105: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/settings/overview/settings_overview_page_test.dart: shows a consumer-first preferences shell with hidden compatibility tools
00:18 +106: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/settings/route_mode/route_mode_page_test.dart: lets the user choose optimize everything for this device
00:18 +107: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/settings/route_mode/route_mode_page_test.dart: lets the user choose optimize everything for this device
00:19 +108: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/settings/route_mode/route_mode_page_test.dart: uses a Windows executable entry flow for selected apps
00:19 +109: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/settings/route_mode/route_mode_page_test.dart: stores selected apps mode with the chosen packages
00:19 +110: All tests passed!
[client-gate] C:\Users\kiwun\tools\flutter\git-3.24.3\bin\flutter.bat test (cwd=C:\Users\kiwun\Documents\ai\VPN\external\client-fork\app)
```

### API lifecycle smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/api_lifecycle_smoke.py`
- Exit: `0`

```text
.
----------------------------------------------------------------------
Ran 1 test in 7.315s

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
[PASS] marketing\src\components\marketing-landing.tsx: Pricing CTA routes through public checkout gateway
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
Retrying 1/3...
request to https://fonts.gstatic.com/s/jetbrainsmono/v24/tDbV2o-flEEny0FZhsfKu5WU4xD0OwGtT0rU3BE.woff2 failed, reason: connect ETIMEDOUT 142.251.98.94:443

Retrying 1/3...
request to https://fonts.gstatic.com/s/playfairdisplay/v40/nuFiD-vYSZviVYUb_rj3ij__anPXDTzYgEM86xQ.woff2 failed, reason: connect ETIMEDOUT 142.251.98.94:443

Retrying 1/3...
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
┌ ○ /                                    198 B          96.3 kB
├ ○ /_not-found                          873 B          88.3 kB
├ ○ /checkout                            13.8 kB         110 kB
├ ○ /devices                             198 B          96.3 kB
├ ○ /install                             198 B          96.3 kB
├ ○ /manifest.webmanifest                0 B                0 B
├ ○ /mobile                              198 B          96.3 kB
├ ○ /offer                               198 B          96.3 kB
├ ○ /privacy                             198 B          96.3 kB
├ ○ /robots.txt                          0 B                0 B
├ ○ /sitemap.xml                         0 B                0 B
├ ○ /telegram                            198 B          96.3 kB
├ ○ /tiktok                              198 B          96.3 kB
└ ○ /youtube                             198 B          96.3 kB
+ First Load JS shared by all            87.4 kB
  ├ chunks/004092b4-fb7a74995ea98db8.js  53.6 kB
  ├ chunks/645-292c8134570c70af.js       31.9 kB
  └ other shared chunks (total)          1.92 kB


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
  ✓ externalDir

  Creating an optimized production build ...
✓ Compiled successfully in 2.7s
  Running TypeScript ...
  Collecting page data using 19 workers ...
  Generating static pages using 19 workers (0/25) ...
  Generating static pages using 19 workers (6/25) 
  Generating static pages using 19 workers (12/25) 
  Generating static pages using 19 workers (18/25) 
✓ Generating static pages using 19 workers (25/25) in 712.1ms
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
├ ○ /admin/promos
├ ○ /admin/referrals
├ ○ /admin/tickets
├ ○ /admin/users
├ ○ /dashboard
├ ○ /dashboard/downloads
├ ○ /devices
├ ○ /icon.svg
├ ○ /pricing
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
  ok  1 e2e\admin-gate.spec.ts:826:7 › Admin gate › redirects non-admin from /admin/* to /dashboard (3.6s)
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
  ok  2 e2e\admin-gate.spec.ts:832:7 › Admin gate › allows admin to open all admin sections (22.8s)
  ok  3 e2e\admin-gate.spec.ts:855:7 › Admin gate › keeps an explicit path back to the cabinet from admin (2.4s)
  ok  4 e2e\admin-gate.spec.ts:866:7 › Admin gate › groups admin routes by operational category and keeps Telegram as fallback only (4.4s)
  ok  5 e2e\admin-gate.spec.ts:881:7 › Admin gate › keeps admin dashboard stable when summary omits optional blocks (2.1s)
  ok  6 e2e\admin-gate.spec.ts:901:7 › Admin gate › shows clean Russian copy across admin surfaces (7.3s)
  ok  7 e2e\admin-gate.spec.ts:923:7 › Admin gate › lets admin search, sort, and paginate the users table (2.8s)
  ok  8 e2e\admin-gate.spec.ts:953:7 › Admin gate › keeps the users filters synced into the URL and restores them on reload (3.5s)
  ok  9 e2e\admin-gate.spec.ts:980:7 › Admin gate › lets admin safely delete only manual or test users (5.2s)
  ok 10 e2e\admin-gate.spec.ts:1018:7 › Admin gate › shows observer-lite badges, filters, and detail diagnostics (3.0s)
  ok 11 e2e\admin-gate.spec.ts:1059:7 › Admin gate › shows observer-lite empty state instead of misleading zero-only activity (2.1s)
  ok 12 e2e\admin-gate.spec.ts:1075:7 › Admin gate › keeps admin pages clickable and inside the viewport on mobile (5.5s)
  ok 13 e2e\admin-gate.spec.ts:1132:7 › Admin gate › shows node alert labels and probe failure details (2.0s)
  ok 14 e2e\admin-gate.spec.ts:1212:7 › Admin gate › shows node context with separate panel, dataplane, and transport detail (2.1s)
  ok 15 e2e\admin-gate.spec.ts:1289:7 › Admin gate › keeps rollout targeting fields and feed objects intact across save and reload (3.4s)
  ok 16 e2e\admin-gate.spec.ts:1329:7 › Admin gate › lets admin triage a ticket and send a reply using stable status codes (5.9s)
  ok 17 e2e\cabinet-flow.spec.ts:323:7 › Cabinet flow › shows shared POKROV cabinet branding and a site return link (2.0s)
  ok 18 e2e\cabinet-flow.spec.ts:336:7 › Cabinet flow › supports additive email states on the root auth entry (2.0s)
  ok 19 e2e\cabinet-flow.spec.ts:348:7 › Cabinet flow › shows a truthful unavailable state when live email delivery is not configured (2.5s)
  ok 20 e2e\cabinet-flow.spec.ts:386:7 › Cabinet flow › reuses an existing web session and lands in the cabinet without showing auth entry again (2.0s)
  ok 21 e2e\cabinet-flow.spec.ts:437:7 › Cabinet flow › keeps the dashboard on consumer-safe access actions (2.0s)
  ok 22 e2e\cabinet-flow.spec.ts:452:7 › Cabinet flow › keeps cabinet navigation on native Next.js routing (5.9s)
  ok 23 e2e\cabinet-flow.spec.ts:468:7 › Cabinet flow › shows branded root and cabinet not-found recovery screens (4.5s)
  ok 24 e2e\cabinet-flow.spec.ts:480:7 › Cabinet flow › keeps the subscription page on renewal and support instead of raw connection sharing (2.0s)
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
  ok 25 e2e\cabinet-flow.spec.ts:492:7 › Cabinet flow › renders runtime connections on devices and keeps statistics actionable (6.1s)
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
  ok 26 e2e\cabinet-flow.spec.ts:510:7 › Cabinet flow › keeps cabinet copy human and hides node internals (6.4s)
  ok 27 e2e\cabinet-flow.spec.ts:524:7 › Cabinet flow › keeps downloads and support flows usable without the app (5.9s)
  ok 28 e2e\cabinet-flow.spec.ts:540:7 › Cabinet flow › stays inside a narrow mobile viewport for core cabinet pages (4.9s)

  28 passed (2.2m)
```

### UI visual smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/ui_visual_smoke.py`
- Exit: `0`

```text
UI visual smoke passed.
```
