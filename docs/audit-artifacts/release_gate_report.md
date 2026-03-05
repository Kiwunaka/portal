# Release Gate Report

- Generated at: `2026-03-05 04:06:43`
- Status: `PASS`

## Summary

| Gate | Exit code | Duration (s) |
|---|---:|---:|
| Backend unit tests | 0 | 43.41 |
| Admin/auth regressions | 0 | 16.78 |
| Admin webapp smoke | 0 | 0.10 |
| WebApp production build | 0 | 34.88 |

## Command Tails

### Backend unit tests

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m unittest discover tests`
- Exit: `0`

```text
...C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:508: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  now = datetime.utcnow().replace(microsecond=0)
..........C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:488: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  user.expiry_at = datetime.utcnow() + timedelta(days=10)
subscription fallback detected token_fp=fe675fe7aaee tg_id=1001 action=notify_admin_once_per_day
....C:\Users\kiwun\Documents\ai\VPN\tests\test_api_p0_extensions.py:104: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  expiry_at=(datetime.utcnow() + timedelta(days=15)).replace(microsecond=0),
C:\Users\kiwun\Documents\ai\VPN\tests\test_api_p0_extensions.py:110: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  sampled_at=datetime.utcnow(),
............C:\Users\kiwun\Documents\ai\VPN\tests\test_api_payments_callbacks.py:463: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  expiry_at=datetime.utcnow() + timedelta(days=30),
...C:\Users\kiwun\Documents\ai\VPN\tests\test_api_payments_callbacks.py:232: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  ref_expiry = datetime.utcnow() + timedelta(days=20)
C:\Users\kiwun\Documents\ai\VPN\tests\test_api_payments_callbacks.py:293: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  self.assertTrue(bool(referrer.expiry_at and referrer.expiry_at > datetime.utcnow() + timedelta(days=30)))
.payment callback signature invalid: provider=freekassa event=result reason=invalid_signature order_id=order-3002 external_id=tx-fk-2
..C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\httpx\_models.py:408: DeprecationWarning: Use 'content=<...>' to upload raw bytes/text content.
  headers, stream = encode_request(
payment callback signature invalid: provider=freekassa event=result reason=invalid_signature order_id=order-2001 external_id=tx-abc-2
.....C:\Users\kiwun\Documents\ai\VPN\portal_bot\bot.py:1416: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  now_ts = int(datetime.utcnow().timestamp())
...2026-03-05 04:05:41,099 [WARNING] check_subscription verify-fail user=1001 channel=@portal_news_channel err=api unavailable
..C:\Users\kiwun\Documents\ai\VPN\portal_bot\bot.py:643: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  return datetime.utcnow().replace(tzinfo=None)
.........C:\Users\kiwun\Documents\ai\VPN\tests\test_free_cycle_service.py:64: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  now = datetime.utcnow()
C:\Users\kiwun\Documents\ai\VPN\tests\test_free_cycle_service.py:136: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  ts = datetime.utcnow()
.C:\Users\kiwun\Documents\ai\VPN\tests\test_free_cycle_service.py:127: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  self.assertGreater(u.free_cycle_next_reset_at, datetime.utcnow())
.......C:\Users\kiwun\Documents\ai\VPN\tests\test_p0_services.py:111: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  db_row.started_at = datetime.utcnow() - timedelta(minutes=70)
.....2026-03-05 04:05:46,814 [INFO] cleaned cross-inbound conflict node=pl from_inbound=2 client_uuid=u-2
2026-03-05 04:05:46,814 [INFO] cleaned cross-inbound conflict node=pl from_inbound=3 client_uuid=u-3
..............2026-03-05 04:05:49,160 [INFO] HTTP Request: GET http://testserver/api/reviews "HTTP/1.1 200 OK"
..........
----------------------------------------------------------------------
Ran 91 tests in 42.165s

OK
```

### Admin/auth regressions

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_api_auth_and_tickets`
- Exit: `0`

```text
C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\sqlalchemy\engine\default.py:952: DeprecationWarning: The default datetime adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute(statement, parameters)
C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\sqlalchemy\sql\schema.py:3624: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  return util.wrap_callable(lambda ctx: fn(), fn)  # type: ignore
...C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:508: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  now = datetime.utcnow().replace(microsecond=0)
..........C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:488: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  user.expiry_at = datetime.utcnow() + timedelta(days=10)
subscription fallback detected token_fp=fe675fe7aaee tg_id=1001 action=notify_admin_once_per_day
....
----------------------------------------------------------------------
Ran 17 tests in 15.927s

OK
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
> next build

▲ Next.js 16.1.6 (Turbopack)

  Creating an optimized production build ...
✓ Compiled successfully in 2.3s
  Running TypeScript ...
  Collecting page data using 19 workers ...
  Generating static pages using 19 workers (0/23) ...
  Generating static pages using 19 workers (5/23) 
  Generating static pages using 19 workers (11/23) 
  Generating static pages using 19 workers (17/23) 
✓ Generating static pages using 19 workers (23/23) in 529.6ms
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
