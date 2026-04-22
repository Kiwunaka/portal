# Release Gate Report

- Generated at: `2026-04-23 01:25:35`
- Status: `PASS`

## Summary

| Gate | Exit code | Duration (s) |
|---|---:|---:|
| Node predeploy readiness | 0 | 98.28 |
| Release pytest matrix | 0 | 147.99 |
| Admin/auth regressions | 0 | 64.41 |
| Client security smoke | 0 | 0.07 |
| Client Flutter tests | 0 | 18.06 |
| API lifecycle smoke | 0 | 8.04 |
| Public link checks | 0 | 0.09 |
| Marketing production build | 0 | 45.56 |
| Admin webapp smoke | 0 | 0.12 |
| WebApp production build | 0 | 44.28 |
| WebApp Playwright E2E | 0 | 92.07 |
| UI visual smoke | 0 | 0.09 |

## Command Tails

### Node predeploy readiness

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/predeploy_node_readiness.py --brain-ip 82.21.114.104 --web-domain pokrov.space --ssh-user root --ssh-port 29374 --passwords C:\Users\kiwun\Documents\ai\VPN\VPN NODE SSH KEYS\PASSWORDS.txt`
- Exit: `0`

```text
      "dns_ok": true,
      "tcp_ok": true,
      "tls_ok": true,
      "target_tls_ok": true,
      "dns_records": [
        "82.24.195.93"
      ],
      "error_kind": "",
      "error_message": ""
    },
    {
      "code": "pl",
      "host": "pl.kiwunaka.space",
      "dns_ok": true,
      "tcp_ok": true,
      "tls_ok": true,
      "target_tls_ok": true,
      "dns_records": [
        "82.40.38.84"
      ],
      "error_kind": "",
      "error_message": ""
    },
    {
      "code": "us",
      "host": "us.kiwunaka.space",
      "dns_ok": true,
      "tcp_ok": true,
      "tls_ok": true,
      "target_tls_ok": true,
      "dns_records": [
        "82.21.92.181"
      ],
      "error_kind": "",
      "error_message": ""
    }
  ],
  "failures": [],
  "ok": true
}
```

### Release pytest matrix

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest portal_bot/tests/test_app_first_api.py tests/test_portal_api.py tests/test_worker_retention.py tests/test_observer_service.py tests/test_observer_api.py tests/test_collect_xray_observer.py tests/test_predeploy_node_readiness.py tests/test_admin_webapp_smoke.py tests/test_public_copy_guardrails.py tests/test_reviews_username_masking.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-k80kbxbv`
- Exit: `0`

```text
..................................................                       [100%]
50 passed in 146.93s (0:02:26)
```

### Admin/auth regressions

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest tests/test_api_auth_and_tickets.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-m17l68jb`
- Exit: `0`

```text
.........................................................                [100%]
57 passed in 63.51s (0:01:03)
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
00:07 +72: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/overview/per_app_proxy_page_test.dart: adds a curated preset without dropping manual selections
00:07 +73: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/overview/per_app_proxy_page_test.dart: adds a curated preset without dropping manual selections
00:07 +74: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/overview/per_app_proxy_page_test.dart: adds a curated preset without dropping manual selections
00:07 +75: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/overview/per_app_proxy_page_test.dart: adds a curated preset without dropping manual selections
00:07 +76: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/data/portal_session_store_test.dart: ensureInstallId generates and reuses a persisted install id
00:07 +77: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/data/portal_session_store_test.dart: saveSessionToken persists runtime auth for future requests
00:07 +78: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/data/portal_trial_activator_test.dart: activateTrial fetches managed manifest first and imports content
00:07 +79: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/data/portal_trial_activator_test.dart: activateTrial falls back to subscription url when managed manifest fetch fails
00:07 +80: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/router/portal_routes_test.dart: portal routes use canonical names and preserve legacy aliases
00:08 +81: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/devices_page_test.dart: shows consumer device overview with current device name
00:08 +82: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/empty_profiles_home_body_test.dart: shows the premium empty home state in English
00:09 +83: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/empty_profiles_home_body_test.dart: shows the premium empty home state in English
00:09 +84: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/empty_profiles_home_body_test.dart: shows the premium empty home state in English
00:09 +85: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/empty_profiles_home_body_test.dart: shows the premium empty home state in English
00:09 +86: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/locations_page_test.dart: shows auto-select and available locations
00:09 +87: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/locations_page_test.dart: shows auto-select and available locations
00:09 +88: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/premium_visuals_golden_test.dart: quick connect panel premium layout stays stable
00:09 +89: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/premium_visuals_golden_test.dart: quick connect panel premium layout stays stable
00:10 +90: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/profile_page_test.dart: shows profile rewards and telegram bonus entry point
00:10 +91: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/profile_page_test.dart: shows profile rewards and telegram bonus entry point
00:10 +92: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/quick_connect_panel_test.dart: shows premium quick connect summary for an active trial
00:10 +93: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/subscription_page_test.dart: shows browser checkout entry as the primary purchase action
00:10 +94: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/subscription_page_test.dart: shows browser checkout entry as the primary purchase action
00:10 +95: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/subscription_page_test.dart: shows browser checkout entry as the primary purchase action
00:11 +96: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/support_page_test.dart: shows in-app support composer and device context
00:11 +97: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/support_page_test.dart: shows in-app support composer and device context
00:11 +98: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/support_page_test.dart: shows in-app support composer and device context
00:11 +99: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/support_page_test.dart: shows in-app support composer and device context
00:11 +100: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/support_page_test.dart: shows in-app support composer and device context
00:11 +101: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/profile/data/profile_repository_test.dart: fetch keeps subscription downloads on the app default user agent
00:11 +102: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/settings/overview/settings_overview_page_test.dart: shows a consumer-first preferences shell with hidden compatibility tools
00:12 +103: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/settings/overview/settings_overview_page_test.dart: shows a consumer-first preferences shell with hidden compatibility tools
00:12 +104: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/settings/overview/settings_overview_page_test.dart: shows a consumer-first preferences shell with hidden compatibility tools
00:12 +105: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/settings/overview/settings_overview_page_test.dart: shows a consumer-first preferences shell with hidden compatibility tools
00:12 +106: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/settings/route_mode/route_mode_page_test.dart: lets the user choose optimize everything for this device
00:12 +107: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/settings/route_mode/route_mode_page_test.dart: lets the user choose optimize everything for this device
00:12 +108: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/settings/route_mode/route_mode_page_test.dart: uses a Windows executable entry flow for selected apps
00:13 +109: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/settings/route_mode/route_mode_page_test.dart: stores selected apps mode with the chosen packages
00:13 +110: All tests passed!
[client-gate] C:\Users\kiwun\tools\flutter\git-3.24.3\bin\flutter.bat test (cwd=C:\Users\kiwun\Documents\ai\VPN\external\client-fork\app)
```

### API lifecycle smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/api_lifecycle_smoke.py`
- Exit: `0`

```text
.
----------------------------------------------------------------------
Ran 1 test in 7.166s

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
┌ ○ /                                    198 B          96.4 kB
├ ○ /_not-found                          873 B          88.3 kB
├ ○ /checkout                            7.39 kB         104 kB
├ ○ /devices                             198 B          96.4 kB
├ ○ /install                             198 B          96.4 kB
├ ○ /manifest.webmanifest                0 B                0 B
├ ○ /mobile                              198 B          96.4 kB
├ ○ /offer                               198 B          96.4 kB
├ ○ /privacy                             198 B          96.4 kB
├ ○ /robots.txt                          0 B                0 B
├ ○ /sitemap.xml                         0 B                0 B
├ ○ /telegram                            198 B          96.4 kB
├ ○ /tiktok                              198 B          96.4 kB
└ ○ /youtube                             198 B          96.4 kB
+ First Load JS shared by all            87.5 kB
  ├ chunks/004092b4-fb7a74995ea98db8.js  53.6 kB
  ├ chunks/645-9f6b6af1d0e5a2b8.js       31.9 kB
  └ other shared chunks (total)          1.95 kB


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

  Creating an optimized production build ...
✓ Compiled successfully in 2.2s
  Running TypeScript ...
  Collecting page data using 19 workers ...
  Generating static pages using 19 workers (0/26) ...
  Generating static pages using 19 workers (6/26) 
  Generating static pages using 19 workers (12/26) 
  Generating static pages using 19 workers (19/26) 
✓ Generating static pages using 19 workers (26/26) in 424.7ms
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
├ ○ /redeem
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
├ ○ /support
├ ○ /support/legal
└ ○ /support/thread


○  (Static)  prerendered as static content


Running 28 tests using 1 worker

  ok  1 e2e\admin-gate.spec.ts:830:7 › Admin gate › redirects non-admin from /admin/* to /dashboard (1.2s)
  ok  2 e2e\admin-gate.spec.ts:836:7 › Admin gate › allows admin to open all admin sections (5.1s)
  ok  3 e2e\admin-gate.spec.ts:859:7 › Admin gate › keeps an explicit path back to the cabinet from admin (1.3s)
  ok  4 e2e\admin-gate.spec.ts:870:7 › Admin gate › groups admin routes by operational category and keeps Telegram as fallback only (1.4s)
  ok  5 e2e\admin-gate.spec.ts:885:7 › Admin gate › keeps admin dashboard stable when summary omits optional blocks (1.3s)
  ok  6 e2e\admin-gate.spec.ts:905:7 › Admin gate › shows clean Russian copy across admin surfaces (2.5s)
  ok  7 e2e\admin-gate.spec.ts:927:7 › Admin gate › lets admin search, sort, and paginate the users table (2.1s)
  ok  8 e2e\admin-gate.spec.ts:957:7 › Admin gate › keeps the users filters synced into the URL and restores them on reload (1.5s)
  ok  9 e2e\admin-gate.spec.ts:984:7 › Admin gate › lets admin safely delete only manual or test users (1.4s)
  ok 10 e2e\admin-gate.spec.ts:1022:7 › Admin gate › shows observer-lite badges, filters, and detail diagnostics (2.6s)
  ok 11 e2e\admin-gate.spec.ts:1063:7 › Admin gate › shows observer-lite empty state instead of misleading zero-only activity (1.6s)
  ok 12 e2e\admin-gate.spec.ts:1079:7 › Admin gate › keeps admin pages clickable and inside the viewport on mobile (3.9s)
  ok 13 e2e\admin-gate.spec.ts:1136:7 › Admin gate › shows node alert labels and probe failure details (1.3s)
  ok 14 e2e\admin-gate.spec.ts:1216:7 › Admin gate › shows node context with separate panel, dataplane, and transport detail (1.3s)
  ok 15 e2e\admin-gate.spec.ts:1293:7 › Admin gate › keeps rollout targeting fields and feed objects intact across save and reload (1.6s)
  ok 16 e2e\admin-gate.spec.ts:1333:7 › Admin gate › lets admin triage a ticket and send a reply using stable status codes (1.4s)
  ok 17 e2e\cabinet-flow.spec.ts:323:7 › Cabinet flow › shows shared POKROV cabinet branding and a site return link (1.3s)
  ok 18 e2e\cabinet-flow.spec.ts:336:7 › Cabinet flow › supports additive email states on the root auth entry (1.3s)
  ok 19 e2e\cabinet-flow.spec.ts:348:7 › Cabinet flow › shows a truthful unavailable state when live email delivery is not configured (1.5s)
  ok 20 e2e\cabinet-flow.spec.ts:386:7 › Cabinet flow › reuses an existing web session and lands in the cabinet without showing auth entry again (1.3s)
  ok 21 e2e\cabinet-flow.spec.ts:437:7 › Cabinet flow › keeps the dashboard on consumer-safe access actions (1.4s)
  ok 22 e2e\cabinet-flow.spec.ts:452:7 › Cabinet flow › keeps cabinet navigation on native Next.js routing (1.5s)
  ok 23 e2e\cabinet-flow.spec.ts:468:7 › Cabinet flow › shows branded root and cabinet not-found recovery screens (1.3s)
  ok 24 e2e\cabinet-flow.spec.ts:480:7 › Cabinet flow › keeps the subscription page on renewal and support instead of raw connection sharing (1.3s)
  ok 25 e2e\cabinet-flow.spec.ts:492:7 › Cabinet flow › renders runtime connections on devices and keeps statistics actionable (1.8s)
  ok 26 e2e\cabinet-flow.spec.ts:510:7 › Cabinet flow › keeps cabinet copy human and hides node internals (2.2s)
  ok 27 e2e\cabinet-flow.spec.ts:524:7 › Cabinet flow › keeps downloads and support flows usable without the app (2.2s)
  ok 28 e2e\cabinet-flow.spec.ts:540:7 › Cabinet flow › stays inside a narrow mobile viewport for core cabinet pages (1.8s)

  28 passed (53.1s)
```

### UI visual smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/ui_visual_smoke.py`
- Exit: `0`

```text
UI visual smoke passed.
```
