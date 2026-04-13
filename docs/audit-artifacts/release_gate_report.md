# Release Gate Report

- Generated at: `2026-04-13 18:10:05`
- Status: `PASS`

## Summary

| Gate | Exit code | Duration (s) |
|---|---:|---:|
| Release pytest matrix | 0 | 132.39 |
| Admin/auth regressions | 0 | 64.02 |
| Client security smoke | 0 | 0.22 |
| Client Flutter tests | 0 | 60.92 |
| API lifecycle smoke | 0 | 8.71 |
| Public link checks | 0 | 0.22 |
| Marketing production build | 0 | 68.42 |
| Admin webapp smoke | 0 | 0.71 |
| WebApp production build | 0 | 55.29 |
| WebApp Playwright E2E | 0 | 111.44 |
| UI visual smoke | 0 | 0.29 |

## Command Tails

### Release pytest matrix

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest portal_bot/tests/test_app_first_api.py tests/test_portal_api.py tests/test_worker_retention.py tests/test_observer_service.py tests/test_observer_api.py tests/test_collect_xray_observer.py tests/test_predeploy_node_readiness.py tests/test_admin_webapp_smoke.py tests/test_public_copy_guardrails.py tests/test_reviews_username_masking.py -q`
- Exit: `0`

```text
    now = datetime.utcnow().replace(microsecond=0)

tests/test_observer_service.py::ObserverServiceTests::test_recompute_user_observer_state_marks_overlap_as_suspicious
  C:\Users\kiwun\Documents\ai\VPN\tests\test_observer_service.py:115: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    now = datetime.utcnow().replace(microsecond=0)

tests/test_observer_api.py::ObserverApiTests::test_internal_observer_batch_ingests_watch_state_and_exposes_admin_payloads
tests/test_observer_api.py::ObserverApiTests::test_internal_observer_batch_is_idempotent_for_replayed_batch_ids
tests/test_observer_api.py::ObserverApiTests::test_internal_observer_batch_rejects_stale_push_and_tracks_unmatched_and_parse_errors
  C:\Users\kiwun\Documents\ai\VPN\tests\test_observer_api.py:127: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    expiry_at=datetime.utcnow() + timedelta(days=30),

tests/test_observer_api.py::ObserverApiTests::test_internal_observer_batch_ingests_watch_state_and_exposes_admin_payloads
tests/test_observer_api.py::ObserverApiTests::test_internal_observer_batch_is_idempotent_for_replayed_batch_ids
tests/test_observer_api.py::ObserverApiTests::test_internal_observer_batch_rejects_stale_push_and_tracks_unmatched_and_parse_errors
  C:\Users\kiwun\Documents\ai\VPN\tests\test_observer_api.py:137: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    expiry_at=datetime.utcnow() + timedelta(days=30),

tests/test_observer_api.py::ObserverApiTests::test_internal_observer_batch_ingests_watch_state_and_exposes_admin_payloads
  C:\Users\kiwun\Documents\ai\VPN\tests\test_observer_api.py:197: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    now = datetime.utcnow().replace(microsecond=0)

tests/test_observer_api.py::ObserverApiTests::test_internal_observer_batch_is_idempotent_for_replayed_batch_ids
  C:\Users\kiwun\Documents\ai\VPN\tests\test_observer_api.py:263: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    now = datetime.utcnow().replace(microsecond=0)

tests/test_observer_api.py::ObserverApiTests::test_internal_observer_batch_rejects_stale_push_and_tracks_unmatched_and_parse_errors
  C:\Users\kiwun\Documents\ai\VPN\tests\test_observer_api.py:292: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    {"occurred_at": datetime.utcnow().replace(microsecond=0).isoformat(), "client_email": "panel-alice", "source_ip": "8.8.8.8"},

tests/test_observer_api.py::ObserverApiTests::test_internal_observer_batch_rejects_stale_push_and_tracks_unmatched_and_parse_errors
  C:\Users\kiwun\Documents\ai\VPN\tests\test_observer_api.py:307: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    now = datetime.utcnow().replace(microsecond=0)

tests/test_collect_xray_observer.py::CollectXrayObserverTests::test_run_pushes_heartbeat_even_without_valid_observations
  C:\Users\kiwun\Documents\ai\VPN\scripts\collect_xray_observer.py:27: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    return datetime.utcnow().replace(microsecond=0)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
48 passed, 833 warnings in 131.18s (0:02:11)
```

### Admin/auth regressions

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest tests/test_api_auth_and_tickets.py -q`
- Exit: `0`

```text
    user.expiry_at = datetime.utcnow() - timedelta(days=1)

tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_dashboard_marks_free_soft_mode_after_monthly_quota
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:821: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    user.expiry_at = datetime.utcnow() + timedelta(days=365)

tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_dashboard_marks_free_soft_mode_after_monthly_quota
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:824: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    user.free_cycle_next_reset_at = datetime.utcnow() + timedelta(days=11)

tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_dashboard_uses_runtime_summary_for_usage_and_connections
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:506: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    user.expiry_at = datetime.utcnow() + timedelta(days=30)

tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_subscription_endpoint_accepts_sub_token_and_tg_id_fallback
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:1956: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    user.expiry_at = datetime.utcnow() + timedelta(days=10)

tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_subscription_endpoint_blocks_numeric_fallback_when_flag_disabled
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:1983: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    user.expiry_at = datetime.utcnow() + timedelta(days=10)

tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_subscription_endpoint_defaults_to_smart_profile_on_connect_host
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:2072: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    user.expiry_at = datetime.utcnow() + timedelta(days=10)

tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_subscription_endpoint_supports_explicit_smart_and_plain_formats
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:2037: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    user.expiry_at = datetime.utcnow() + timedelta(days=10)

tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_subscription_endpoint_supports_head_for_plain_and_hiddify_clients
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:2003: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    user.expiry_at = datetime.utcnow() + timedelta(days=10)

tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_user_data_exposes_runtime_traffic_and_connections_without_app_install
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:653: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    user.expiry_at = datetime.utcnow() + timedelta(days=14)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
55 passed, 2023 warnings in 62.78s (0:01:02)
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
[pass] client security smoke checks passed
```

### Client Flutter tests

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/run_client_release_gate.py test --suite full`
- Exit: `0`

```text
00:16 +47: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/data/direct_package_catalog_test.dart: catalog exposes canonical public version and categories
00:16 +48: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/data/direct_package_catalog_test.dart: catalog keeps high-signal RU apps available for one-tap direct presets
00:17 +49: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/overview/per_app_proxy_page_test.dart: adds a curated preset without dropping manual selections
00:17 +50: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/overview/per_app_proxy_page_test.dart: adds a curated preset without dropping manual selections
00:17 +51: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/overview/per_app_proxy_page_test.dart: adds a curated preset without dropping manual selections
00:17 +52: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/overview/per_app_proxy_page_test.dart: adds a curated preset without dropping manual selections
00:17 +53: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/overview/per_app_proxy_page_test.dart: adds a curated preset without dropping manual selections
00:18 +54: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/overview/per_app_proxy_page_test.dart: adds a curated preset without dropping manual selections
00:18 +55: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/overview/per_app_proxy_page_test.dart: adds a curated preset without dropping manual selections
00:18 +56: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/overview/per_app_proxy_page_test.dart: adds a curated preset without dropping manual selections
00:18 +57: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/overview/per_app_proxy_page_test.dart: adds a curated preset without dropping manual selections
00:18 +58: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/overview/per_app_proxy_page_test.dart: adds a curated preset without dropping manual selections
00:18 +59: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/per_app_proxy/overview/per_app_proxy_page_test.dart: adds a curated preset without dropping manual selections
00:18 +60: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/data/portal_session_store_test.dart: ensureInstallId generates and reuses a persisted install id
00:18 +61: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/data/portal_session_store_test.dart: saveSessionToken persists runtime auth for future requests
00:18 +62: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/data/portal_trial_activator_test.dart: activateTrial builds app-first request and silently imports subscription
00:19 +63: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/router/portal_routes_test.dart: portal routes use canonical names and preserve legacy aliases
00:19 +64: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/devices_page_test.dart: shows consumer device overview with current device name
00:20 +65: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/empty_profiles_home_body_test.dart: shows the premium empty home state in English
00:20 +66: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/empty_profiles_home_body_test.dart: shows the premium empty home state in English
00:20 +67: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/empty_profiles_home_body_test.dart: shows the premium empty home state in English
00:20 +68: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/empty_profiles_home_body_test.dart: shows the premium empty home state in English
00:21 +69: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/locations_page_test.dart: shows auto-select and available locations
00:21 +70: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/locations_page_test.dart: shows auto-select and available locations
00:21 +71: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/locations_page_test.dart: shows an activation gate before a real subscription exists
00:21 +72: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/premium_visuals_golden_test.dart: quick connect panel premium layout stays stable
00:22 +73: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/profile_page_test.dart: shows profile rewards and telegram bonus entry point
00:22 +74: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/profile_page_test.dart: shows profile rewards and telegram bonus entry point
00:22 +75: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/quick_connect_panel_test.dart: shows premium quick connect summary for an active trial
00:23 +76: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/subscription_page_test.dart: shows browser checkout entry as the primary purchase action
00:23 +77: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/subscription_page_test.dart: shows browser checkout entry as the primary purchase action
00:23 +78: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/subscription_page_test.dart: shows browser checkout entry as the primary purchase action
00:23 +79: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/support_page_test.dart: shows in-app support composer and device context
00:23 +80: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/support_page_test.dart: shows in-app support composer and device context
00:23 +81: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/support_page_test.dart: shows in-app support composer and device context
00:23 +82: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/support_page_test.dart: shows in-app support composer and device context
00:23 +83: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/portal/widget/support_page_test.dart: shows in-app support composer and device context
00:24 +84: C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/test/features/profile/data/profile_repository_test.dart: fetch keeps subscription downloads on the app default user agent
00:24 +85: All tests passed!
[client-gate] flutter test (cwd=C:\Users\kiwun\Documents\ai\VPN\external\client-fork\app)
```

### API lifecycle smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/api_lifecycle_smoke.py`
- Exit: `0`

```text
C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\sqlalchemy\engine\default.py:952: DeprecationWarning: The default datetime adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute(statement, parameters)
C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\sqlalchemy\sql\schema.py:3624: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  return util.wrap_callable(lambda ctx: fn(), fn)  # type: ignore
C:\Users\kiwun\Documents\ai\VPN\tests\test_api_lifecycle_smoke.py:263: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  expiry_at=datetime.utcnow() + timedelta(days=20),
.
----------------------------------------------------------------------
Ran 1 test in 7.454s

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
[PASS] marketing\src\components\marketing-landing.tsx: Public marketing CTA no longer routes to connect host
[PASS] marketing\src\components\marketing-landing.tsx: Public cabinet CTA points to webapp host
[PASS] marketing\src\components\marketing-landing.tsx: Pricing CTA routes through public checkout gateway
[PASS] marketing\src\components\marketing-landing.tsx: Marketing footer exposes canonical news channel
[PASS] marketing\src\app\layout.tsx: Layout includes `metadataBase` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `manifest` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `icons` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `apple` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `favicon.ico` metadata wiring
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

   Creating an optimized production build ...
request to https://fonts.gstatic.com/s/playfairdisplay/v40/nuFiD-vYSZviVYUb_rj3ij__anPXDTPYgEM86xRbPQ.woff2 failed, reason: connect ETIMEDOUT 142.250.120.94:443

Retrying 1/3...
 ✓ Compiled successfully
   Linting and checking validity of types ...
   Collecting page data ...
   Generating static pages (0/19) ...
   Generating static pages (4/19) 
   Generating static pages (9/19) 
   Generating static pages (14/19) 
 ✓ Generating static pages (19/19)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                              Size     First Load JS
┌ ○ /                                    197 B          96.3 kB
├ ○ /_not-found                          873 B          88.3 kB
├ ○ /apple-icon.png                      0 B                0 B
├ ○ /bystryy-vpn-na-telefon              197 B          96.3 kB
├ ○ /checkout                            13.5 kB         110 kB
├ ○ /icon.png                            0 B                0 B
├ ○ /install                             197 B          96.3 kB
├ ○ /manifest.webmanifest                0 B                0 B
├ ○ /offer                               197 B          96.3 kB
├ ○ /privacy                             197 B          96.3 kB
├ ○ /robots.txt                          0 B                0 B
├ ○ /sitemap.xml                         0 B                0 B
├ ○ /vpn-dlya-tiktok                     197 B          96.3 kB
├ ○ /vpn-dlya-youtube                    197 B          96.3 kB
├ ○ /vpn-na-iphone-android-windows       197 B          96.3 kB
└ ○ /vpn-telegram-bot                    197 B          96.3 kB
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
- Experiments (use with caution):
  ✓ externalDir

  Creating an optimized production build ...
✓ Compiled successfully in 2.6s
  Running TypeScript ...
  Collecting page data using 19 workers ...
  Generating static pages using 19 workers (0/24) ...
  Generating static pages using 19 workers (6/24) 
  Generating static pages using 19 workers (12/24) 
  Generating static pages using 19 workers (18/24) 
✓ Generating static pages using 19 workers (24/24) in 668.7ms
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
> pokrov-webapp@0.1.0 test:e2e
> powershell -NoProfile -ExecutionPolicy Bypass -Command "$port=3102; Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }; exit 0" && set E2E_PORT=3102&& set PLAYWRIGHT_FRESH_SERVER=1&& playwright test e2e/admin-gate.spec.ts e2e/cabinet-flow.spec.ts


Running 19 tests using 1 worker

  ok  1 e2e\admin-gate.spec.ts:737:7 › Admin gate › redirects non-admin from /admin/* to /dashboard (2.4s)
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
  ok  2 e2e\admin-gate.spec.ts:743:7 › Admin gate › allows admin to open all admin sections (19.5s)
  ok  3 e2e\admin-gate.spec.ts:765:7 › Admin gate › keeps admin dashboard stable when summary omits optional blocks (3.4s)
  ok  4 e2e\admin-gate.spec.ts:785:7 › Admin gate › shows clean Russian copy across admin surfaces (7.2s)
  ok  5 e2e\admin-gate.spec.ts:807:7 › Admin gate › lets admin search, sort, and paginate the users table (6.0s)
  ok  6 e2e\admin-gate.spec.ts:837:7 › Admin gate › keeps the users filters synced into the URL and restores them on reload (4.7s)
  ok  7 e2e\admin-gate.spec.ts:864:7 › Admin gate › lets admin safely delete only manual or test users (5.1s)
  ok  8 e2e\admin-gate.spec.ts:902:7 › Admin gate › shows observer-lite badges, filters, and detail diagnostics (3.6s)
  ok  9 e2e\admin-gate.spec.ts:943:7 › Admin gate › shows observer-lite empty state instead of misleading zero-only activity (2.3s)
  ok 10 e2e\admin-gate.spec.ts:959:7 › Admin gate › keeps admin pages clickable and inside the viewport on mobile (7.8s)
  ok 11 e2e\admin-gate.spec.ts:1016:7 › Admin gate › shows node alert labels and probe failure details (1.7s)
  ok 12 e2e\admin-gate.spec.ts:1084:7 › Admin gate › lets admin triage a ticket and send a reply using stable status codes (2.2s)
  ok 13 e2e\cabinet-flow.spec.ts:323:7 › Cabinet flow › shows a single connect link flow on the dashboard (3.7s)
  ok 14 e2e\cabinet-flow.spec.ts:337:7 › Cabinet flow › keeps cabinet navigation on native Next.js routing (4.1s)
  ok 15 e2e\cabinet-flow.spec.ts:353:7 › Cabinet flow › shows branded root and cabinet not-found recovery screens (3.7s)
  ok 16 e2e\cabinet-flow.spec.ts:365:7 › Cabinet flow › keeps the subscription page on one public connection link plus QR (2.2s)
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
  ok 17 e2e\cabinet-flow.spec.ts:378:7 › Cabinet flow › renders runtime connections on devices and keeps statistics actionable (5.4s)
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
  ok 18 e2e\cabinet-flow.spec.ts:396:7 › Cabinet flow › keeps downloads and support flows usable without the app (6.8s)
  ok 19 e2e\cabinet-flow.spec.ts:412:7 › Cabinet flow › stays inside a narrow mobile viewport for core cabinet pages (4.9s)

  19 passed (1.8m)
```

### UI visual smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/ui_visual_smoke.py`
- Exit: `0`

```text
UI visual smoke passed.
```
