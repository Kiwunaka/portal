# Release Gate Report

- Generated at: `2026-04-03 20:45:22`
- Status: `PASS`

## Summary

| Gate | Exit code | Duration (s) |
|---|---:|---:|
| Release pytest matrix | 0 | 46.60 |
| Admin/auth regressions | 0 | 61.03 |
| API lifecycle smoke | 0 | 8.37 |
| Public link checks | 0 | 0.09 |
| Marketing production build | 0 | 34.37 |
| Admin webapp smoke | 0 | 0.10 |
| WebApp production build | 0 | 41.65 |
| WebApp Playwright E2E | 0 | 69.84 |
| UI visual smoke | 0 | 0.09 |

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
44 passed, 765 warnings in 45.68s
```

### Admin/auth regressions

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest tests/test_api_auth_and_tickets.py -q`
- Exit: `0`

```text
    user.expiry_at = datetime.utcnow() - timedelta(days=1)

tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_dashboard_marks_free_soft_mode_after_monthly_quota
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:791: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    user.expiry_at = datetime.utcnow() + timedelta(days=365)

tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_dashboard_marks_free_soft_mode_after_monthly_quota
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:794: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    user.free_cycle_next_reset_at = datetime.utcnow() + timedelta(days=11)

tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_dashboard_uses_runtime_summary_for_usage_and_connections
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:506: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    user.expiry_at = datetime.utcnow() + timedelta(days=30)

tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_subscription_endpoint_accepts_sub_token_and_tg_id_fallback
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:1908: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    user.expiry_at = datetime.utcnow() + timedelta(days=10)

tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_subscription_endpoint_blocks_numeric_fallback_when_flag_disabled
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:1935: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    user.expiry_at = datetime.utcnow() + timedelta(days=10)

tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_subscription_endpoint_defaults_to_smart_profile_on_connect_host
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:2024: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    user.expiry_at = datetime.utcnow() + timedelta(days=10)

tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_subscription_endpoint_supports_explicit_smart_and_plain_formats
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:1989: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    user.expiry_at = datetime.utcnow() + timedelta(days=10)

tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_subscription_endpoint_supports_head_for_plain_and_hiddify_clients
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:1955: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    user.expiry_at = datetime.utcnow() + timedelta(days=10)

tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_user_data_exposes_runtime_traffic_and_connections_without_app_install
  C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:638: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    user.expiry_at = datetime.utcnow() + timedelta(days=14)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
55 passed, 2020 warnings in 59.97s
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
Ran 1 test in 7.359s

OK
```

### Public link checks

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/check-links.py`
- Exit: `0`

```text
[PASS] marketing\src\app\page.tsx: Cold CTA ���������� �� bot-first ��������
[PASS] marketing\src\app\offer\page.tsx: Legal CTA �������� � ���������� Telegram flow
[PASS] marketing\src\app\privacy\page.tsx: Legal CTA �������� � ���������� Telegram flow
[PASS] webapp\src\app\(dashboard)\support\legal\page.tsx: ����������� ������ webapp ��������� �� marketing absolute URL
[PASS] portal_bot\api.py: Admin campaign link builder ��������� public checkout � safe fallback
[PASS] portal_bot\api.py: Compat env-flag ��� numeric subscription fallback ���������
[PASS] marketing\src\app\checkout\page.tsx: Checkout heading ��������� ������� ���������

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
   Generating static pages (0/12) ...
   Generating static pages (3/12) 
   Generating static pages (6/12) 
   Generating static pages (9/12) 
 ✓ Generating static pages (12/12)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                              Size     First Load JS
┌ ○ /                                    189 B          96.3 kB
├ ○ /_not-found                          873 B          88.3 kB
├ ○ /bystryy-vpn-na-telefon              189 B          96.3 kB
├ ○ /checkout                            9.44 kB        96.9 kB
├ ○ /offer                               142 B          87.6 kB
├ ○ /privacy                             142 B          87.6 kB
├ ○ /vpn-dlya-tiktok                     189 B          96.3 kB
├ ○ /vpn-dlya-youtube                    189 B          96.3 kB
├ ○ /vpn-na-iphone-android-windows       189 B          96.3 kB
└ ○ /vpn-telegram-bot                    189 B          96.3 kB
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
✓ Compiled successfully in 1956.9ms
  Running TypeScript ...
  Collecting page data using 19 workers ...
  Generating static pages using 19 workers (0/23) ...
  Generating static pages using 19 workers (5/23) 
  Generating static pages using 19 workers (11/23) 
  Generating static pages using 19 workers (17/23) 
✓ Generating static pages using 19 workers (23/23) in 500.3ms
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

  ok  1 e2e\admin-gate.spec.ts:733:7 › Admin gate › redirects non-admin from /admin/* to /dashboard (2.0s)
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
  ok  2 e2e\admin-gate.spec.ts:739:7 › Admin gate › allows admin to open all admin sections (14.9s)
  ok  3 e2e\admin-gate.spec.ts:761:7 › Admin gate › keeps admin dashboard stable when summary omits optional blocks (1.8s)
  ok  4 e2e\admin-gate.spec.ts:781:7 › Admin gate › shows clean Russian copy across admin surfaces (5.6s)
  ok  5 e2e\admin-gate.spec.ts:803:7 › Admin gate › lets admin search, sort, and paginate the users table (2.0s)
  ok  6 e2e\admin-gate.spec.ts:833:7 › Admin gate › lets admin safely delete only manual or test users (2.1s)
  ok  7 e2e\admin-gate.spec.ts:871:7 › Admin gate › shows observer-lite badges, filters, and detail diagnostics (3.0s)
  ok  8 e2e\admin-gate.spec.ts:912:7 › Admin gate › shows observer-lite empty state instead of misleading zero-only activity (2.0s)
  ok  9 e2e\admin-gate.spec.ts:923:7 › Admin gate › keeps admin pages clickable and inside the viewport on mobile (4.6s)
  ok 10 e2e\admin-gate.spec.ts:980:7 › Admin gate › shows node alert labels and probe failure details (1.8s)
  ok 11 e2e\admin-gate.spec.ts:1048:7 › Admin gate › lets admin triage a ticket and send a reply using stable status codes (2.3s)
  ok 12 e2e\cabinet-flow.spec.ts:319:7 › Cabinet flow › shows a single connect link flow on the dashboard (3.2s)
  ok 13 e2e\cabinet-flow.spec.ts:332:7 › Cabinet flow › keeps the subscription page on one public connection link plus QR (2.7s)
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
  ok 14 e2e\cabinet-flow.spec.ts:345:7 › Cabinet flow › renders runtime connections on devices and keeps statistics actionable (4.4s)
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
  ok 15 e2e\cabinet-flow.spec.ts:361:7 › Cabinet flow › keeps downloads and support flows usable without the app (5.5s)
  ok 16 e2e\cabinet-flow.spec.ts:377:7 › Cabinet flow › stays inside a narrow mobile viewport for core cabinet pages (3.9s)

  16 passed (1.1m)
```

### UI visual smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/ui_visual_smoke.py`
- Exit: `0`

```text
UI visual smoke passed.
```
