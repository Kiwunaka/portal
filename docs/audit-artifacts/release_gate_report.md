# Release Gate Report

- Generated at: `2026-04-09 05:25:06`
- Status: `FAIL`

## Summary

| Gate | Exit code | Duration (s) |
|---|---:|---:|
| Node predeploy readiness | 0 | 42.00 |
| Release pytest matrix | 1 | 20.52 |
| Admin/auth regressions | 1 | 44.82 |
| Client security smoke | 0 | 0.06 |
| API lifecycle smoke | 1 | 1.78 |
| Public link checks | 0 | 0.10 |
| Marketing production build | 0 | 45.74 |
| Admin webapp smoke | 0 | 0.57 |
| WebApp production build | 0 | 42.16 |
| WebApp Playwright E2E | 0 | 78.16 |
| UI visual smoke | 0 | 0.10 |

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
        "82.21.92.142"
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

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest portal_bot/tests/test_app_first_api.py tests/test_portal_api.py tests/test_worker_retention.py tests/test_observer_service.py tests/test_observer_api.py tests/test_collect_xray_observer.py tests/test_predeploy_node_readiness.py tests/test_admin_webapp_smoke.py tests/test_public_copy_guardrails.py tests/test_reviews_username_masking.py -q`
- Exit: `1`

```text
tests/test_observer_service.py::ObserverServiceTests::test_cleanup_observer_retention_prunes_old_rows_and_downgrades_state
tests/test_observer_service.py::ObserverServiceTests::test_normalize_source_ip_scores_ipv4_and_ipv6_but_excludes_private
tests/test_observer_service.py::ObserverServiceTests::test_recompute_user_observer_state_marks_overlap_as_suspicious
  C:\Users\kiwun\Documents\ai\VPN\tests\test_observer_service.py:78: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    expiry_at=datetime.utcnow() + timedelta(days=30),

tests/test_observer_service.py::ObserverServiceTests::test_cleanup_observer_retention_prunes_old_rows_and_downgrades_state
  C:\Users\kiwun\Documents\ai\VPN\tests\test_observer_service.py:221: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    now = datetime.utcnow().replace(microsecond=0)

tests/test_observer_service.py::ObserverServiceTests::test_recompute_user_observer_state_marks_overlap_as_suspicious
  C:\Users\kiwun\Documents\ai\VPN\tests\test_observer_service.py:115: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    now = datetime.utcnow().replace(microsecond=0)

tests/test_collect_xray_observer.py::CollectXrayObserverTests::test_run_pushes_heartbeat_even_without_valid_observations
  C:\Users\kiwun\Documents\ai\VPN\scripts\collect_xray_observer.py:27: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    return datetime.utcnow().replace(microsecond=0)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ===========================
FAILED portal_bot/tests/test_app_first_api.py::test_start_trial_returns_session_and_real_device_payload
FAILED portal_bot/tests/test_app_first_api.py::test_start_trial_reuses_existing_install_id
FAILED portal_bot/tests/test_app_first_api.py::test_app_session_can_create_support_ticket
FAILED portal_bot/tests/test_app_first_api.py::test_app_session_can_request_telegram_link
FAILED portal_bot/tests/test_app_first_api.py::test_channel_bonus_claim_uses_linked_telegram_identity_for_app_account
FAILED tests/test_portal_api.py::PortalApiTests::test_free_config_split_routing_and_youtube_direct
FAILED tests/test_portal_api.py::PortalApiTests::test_generate_vless_link_contains_reality_params
FAILED tests/test_portal_api.py::PortalApiTests::test_node_labels_include_nl_and_nl_free
FAILED tests/test_portal_api.py::PortalApiTests::test_nodes_for_user_excludes_brain_from_paid_pool
FAILED tests/test_portal_api.py::PortalApiTests::test_singbox_config_has_selector
FAILED tests/test_portal_api.py::PortalApiTests::test_singbox_config_keeps_unique_tags_for_poland_canary_nodes
FAILED tests/test_portal_api.py::PortalApiTests::test_verify_telegram_data - ...
FAILED tests/test_portal_api.py::PortalApiTests::test_verify_telegram_data_uses_runtime_bot_token_when_settings_were_cached
FAILED tests/test_observer_api.py::ObserverApiTests::test_internal_observer_batch_ingests_watch_state_and_exposes_admin_payloads
FAILED tests/test_observer_api.py::ObserverApiTests::test_internal_observer_batch_is_idempotent_for_replayed_batch_ids
FAILED tests/test_observer_api.py::ObserverApiTests::test_internal_observer_batch_rejects_stale_push_and_tracks_unmatched_and_parse_errors
FAILED tests/test_reviews_username_masking.py::ReviewsUsernameMaskingTests::test_api_reviews_masks_username_values
FAILED tests/test_reviews_username_masking.py::ReviewsUsernameMaskingTests::test_api_reviews_only_returns_featured_rows
FAILED tests/test_reviews_username_masking.py::ReviewsUsernameMaskingTests::test_mask_public_username_cases
19 failed, 25 passed, 705 warnings in 19.64s
```

### Admin/auth regressions

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest tests/test_api_auth_and_tickets.py -q`
- Exit: `1`

```text
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_admin_nodes_health_preserves_missing_ram_and_disk_as_null
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_admin_promos_templates_and_gift_codes_crud
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_admin_safe_delete_only_removes_explicit_test_users
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_admin_start_links_and_wheel_config
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_admin_summary_includes_bonus_event_breakdown
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_admin_summary_includes_retention_cohorts_and_pings
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_admin_summary_uses_effective_active_status
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_admin_user_card_exposes_online_now_summary_and_current_nodes
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_admin_users_support_effective_status_origin_filters_and_search
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_admin_users_supports_effective_status_origin_and_extended_search
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_api_events_accept_extended_funnel_event_names
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_api_events_accepts_extended_user_metric_events
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_channel_bonus_claim_blocked_by_opening_promo_claim
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_channel_bonus_claim_does_not_persist_points_when_outer_commit_fails
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_channel_bonus_claim_requires_membership
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_channel_bonus_claim_requires_tos
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_channel_bonus_claim_treats_left_as_not_member
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_channel_bonus_claim_upgrades_free_to_paid
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_dashboard_and_profile_payloads_use_canonical_connect_host
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_dashboard_downgrades_expired_premium_to_free_monthly
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_dashboard_marks_free_soft_mode_after_monthly_quota
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_dashboard_uses_runtime_summary_for_usage_and_connections
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_gift_redeem_tracks_denied_attempt
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_mark_campaign_once_returns_false_on_duplicate_insert_race
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_nodes_diagnostics_rate_limit
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_promo_redeem_rejects_zero_value_without_burning_usage
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_promo_redeem_supports_unlimited_uses_flag
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_subscription_endpoint_accepts_sub_token_and_tg_id_fallback
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_subscription_endpoint_blocks_numeric_fallback_when_flag_disabled
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_subscription_endpoint_defaults_to_smart_profile_on_connect_host
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_subscription_endpoint_supports_explicit_smart_and_plain_formats
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_subscription_endpoint_supports_head_for_plain_and_hiddify_clients
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_ticket_lifecycle_with_media_metadata
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_ticket_upload_returns_attachment_metadata_and_serves_file
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_user_data_exposes_runtime_traffic_and_connections_without_app_install
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_user_data_filters_legacy_free_and_brain_mappings_for_paid_user
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_user_data_prefers_mapped_nodes_for_paid_user
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_web_login_rejects_invalid_signature
FAILED tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_web_login_session_flow
55 failed, 1542 warnings in 44.01s
```

### Client security smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/client_security_smoke.py`
- Exit: `0`

```text
[check] config options: external\client-fork\app\lib\features\config_option\data\config_option_repository.dart
[check] routing enum: external\client-fork\app\lib\singbox\model\singbox_config_enum.dart
[check] android control surfaces: external\client-fork\app\android\app\src\main\kotlin\com\hiddify\hiddify\bg\BoxService.kt
[check] android method handler: external\client-fork\app\android\app\src\main\kotlin\com\hiddify\hiddify\MethodHandler.kt
[check] core service transport: external\client-fork\app\lib\singbox\service\core_singbox_service.dart
[observe] android libbox CommandServer is present and requires release-build localhost audit
[observe] android/libbox standalone command client calls are present
[observe] localhost gRPC channel is present in core sing-box service
[pass] client security smoke checks passed
```

### API lifecycle smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/api_lifecycle_smoke.py`
- Exit: `1`

```text
C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\sqlalchemy\engine\default.py:952: DeprecationWarning: The default datetime adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute(statement, parameters)
E
======================================================================
ERROR: test_api_only_lifecycle_covers_trial_connect_support_bonuses_and_purchase (tests.test_api_lifecycle_smoke.ApiLifecycleSmokeTests.test_api_only_lifecycle_covers_trial_connect_support_bonuses_and_purchase)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\kiwun\Documents\ai\VPN\tests\test_api_lifecycle_smoke.py", line 88, in setUp
    self.api = importlib.import_module("api")
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py", line 90, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1387, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1360, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1331, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 935, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 995, in exec_module
  File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
  File "C:\Users\kiwun\Documents\ai\VPN\portal_bot\api.py", line 1228, in <module>
    app = FastAPI(title="POKROV API", version="2.0.0")
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\fastapi\applications.py", line 896, in __init__
    ] = webhooks or routing.APIRouter()
                    ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\fastapi\routing.py", line 837, in __init__
    super().__init__(
TypeError: Router.__init__() got an unexpected keyword argument 'on_startup'

----------------------------------------------------------------------
Ran 1 test in 0.897s

FAILED (errors=1)
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
> pokrov-marketing@0.1.0 build
> next build

  ▲ Next.js 14.2.35

   Creating an optimized production build ...
 ✓ Compiled successfully
   Linting and checking validity of types ...
   Collecting page data ...
   Generating static pages (0/18) ...
   Generating static pages (4/18) 
   Generating static pages (8/18) 
   Generating static pages (13/18) 
 ✓ Generating static pages (18/18)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                              Size     First Load JS
┌ ○ /                                    195 B          96.3 kB
├ ○ /_not-found                          873 B          88.3 kB
├ ○ /apple-icon.png                      0 B                0 B
├ ○ /bystryy-vpn-na-telefon              195 B          96.3 kB
├ ○ /checkout                            9.46 kB         106 kB
├ ○ /icon.png                            0 B                0 B
├ ○ /manifest.webmanifest                0 B                0 B
├ ○ /offer                               195 B          96.3 kB
├ ○ /privacy                             195 B          96.3 kB
├ ○ /robots.txt                          0 B                0 B
├ ○ /sitemap.xml                         0 B                0 B
├ ○ /vpn-dlya-tiktok                     195 B          96.3 kB
├ ○ /vpn-dlya-youtube                    195 B          96.3 kB
├ ○ /vpn-na-iphone-android-windows       195 B          96.3 kB
└ ○ /vpn-telegram-bot                    195 B          96.3 kB
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
▲ Next.js 16.1.6 (Turbopack)
- Experiments (use with caution):
  ✓ externalDir

  Creating an optimized production build ...
✓ Compiled successfully in 2.5s
  Running TypeScript ...
  Collecting page data using 19 workers ...
  Generating static pages using 19 workers (0/23) ...
  Generating static pages using 19 workers (5/23) 
  Generating static pages using 19 workers (11/23) 
  Generating static pages using 19 workers (17/23) 
✓ Generating static pages using 19 workers (23/23) in 535.2ms
  Finalizing page optimization ...

Route (app)
┌ ○ /
├ ○ /_not-found
├ ○ /admin
├ ○ /admin/bonuses
├ ○ /admin/broadcast
├ ○ /admin/dashboard
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
> playwright test e2e/admin-gate.spec.ts e2e/cabinet-flow.spec.ts


Running 16 tests using 1 worker

  ok  1 e2e\admin-gate.spec.ts:733:7 › Admin gate › redirects non-admin from /admin/* to /dashboard (1.7s)
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
  ok  2 e2e\admin-gate.spec.ts:739:7 › Admin gate › allows admin to open all admin sections (15.1s)
  ok  3 e2e\admin-gate.spec.ts:761:7 › Admin gate › keeps admin dashboard stable when summary omits optional blocks (1.9s)
  ok  4 e2e\admin-gate.spec.ts:781:7 › Admin gate › shows clean Russian copy across admin surfaces (5.4s)
  ok  5 e2e\admin-gate.spec.ts:803:7 › Admin gate › lets admin search, sort, and paginate the users table (2.1s)
  ok  6 e2e\admin-gate.spec.ts:833:7 › Admin gate › lets admin safely delete only manual or test users (2.3s)
  ok  7 e2e\admin-gate.spec.ts:871:7 › Admin gate › shows observer-lite badges, filters, and detail diagnostics (3.5s)
  ok  8 e2e\admin-gate.spec.ts:912:7 › Admin gate › shows observer-lite empty state instead of misleading zero-only activity (2.1s)
  ok  9 e2e\admin-gate.spec.ts:923:7 › Admin gate › keeps admin pages clickable and inside the viewport on mobile (4.8s)
  ok 10 e2e\admin-gate.spec.ts:980:7 › Admin gate › shows node alert labels and probe failure details (2.0s)
  ok 11 e2e\admin-gate.spec.ts:1048:7 › Admin gate › lets admin triage a ticket and send a reply using stable status codes (2.3s)
  ok 12 e2e\cabinet-flow.spec.ts:319:7 › Cabinet flow › shows a single connect link flow on the dashboard (3.0s)
  ok 13 e2e\cabinet-flow.spec.ts:332:7 › Cabinet flow › keeps the subscription page on one public connection link plus QR (2.9s)
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
  ok 14 e2e\cabinet-flow.spec.ts:345:7 › Cabinet flow › renders runtime connections on devices and keeps statistics actionable (4.7s)
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
  ok 15 e2e\cabinet-flow.spec.ts:361:7 › Cabinet flow › keeps downloads and support flows usable without the app (5.9s)
  ok 16 e2e\cabinet-flow.spec.ts:377:7 › Cabinet flow › stays inside a narrow mobile viewport for core cabinet pages (4.0s)

  16 passed (1.2m)
```

### UI visual smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/ui_visual_smoke.py`
- Exit: `0`

```text
UI visual smoke passed.
```
