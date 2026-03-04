# Release Gate Report

- Generated at: `2026-03-05 00:49:12`
- Status: `PASS`

## Summary

| Gate | Exit code | Duration (s) |
|---|---:|---:|
| Backend unit tests | 0 | 44.14 |
| Admin/auth regressions | 0 | 16.92 |
| WebApp production build | 0 | 34.80 |

## Command Tails

### Backend unit tests

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m unittest discover tests`
- Exit: `0`

```text
..C:\Users\kiwun\Documents\ai\VPN\portal_bot\bot.py:643: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  return datetime.utcnow().replace(tzinfo=None)
C:\Users\kiwun\Documents\ai\VPN\portal_bot\events_service.py:44: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  created_at=datetime.utcnow(),
.........C:\Users\kiwun\Documents\ai\VPN\tests\test_free_cycle_service.py:64: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  now = datetime.utcnow()
C:\Users\kiwun\Documents\ai\VPN\tests\test_free_cycle_service.py:136: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  ts = datetime.utcnow()
.C:\Users\kiwun\Documents\ai\VPN\tests\test_free_cycle_service.py:127: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  self.assertGreater(u.free_cycle_next_reset_at, datetime.utcnow())
.......C:\Users\kiwun\Documents\ai\VPN\portal_bot\pay_attempts_service.py:26: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  now = datetime.utcnow()
C:\Users\kiwun\Documents\ai\VPN\tests\test_p0_services.py:111: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  db_row.started_at = datetime.utcnow() - timedelta(minutes=70)
C:\Users\kiwun\Documents\ai\VPN\portal_bot\pay_attempts_service.py:186: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  cutoff = datetime.utcnow() - timedelta(minutes=max(1, int(older_than_minutes)))
C:\Users\kiwun\Documents\ai\VPN\portal_bot\pay_attempts_service.py:93: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  now = datetime.utcnow()
.C:\Users\kiwun\Documents\ai\VPN\portal_bot\pay_attempts_service.py:210: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  now = datetime.utcnow()
C:\Users\kiwun\Documents\ai\VPN\portal_bot\pay_attempts_service.py:67: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  now = datetime.utcnow()
.C:\Users\kiwun\Documents\ai\VPN\portal_bot\points_service.py:42: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  return datetime.utcnow()
..C:\Users\kiwun\Documents\ai\VPN\portal_bot\pay_attempts_service.py:149: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  cutoff = datetime.utcnow() - timedelta(hours=max(1, int(within_hours)))
.2026-03-05 00:48:15,348 [INFO] cleaned cross-inbound conflict node=pl from_inbound=2 client_uuid=u-2
2026-03-05 00:48:15,348 [INFO] cleaned cross-inbound conflict node=pl from_inbound=3 client_uuid=u-3
..............C:\Users\kiwun\Documents\ai\VPN\portal_bot\migrations.py:95: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  {"key": key, "text": value, "created_at": datetime.utcnow()},
2026-03-05 00:48:17,717 [INFO] HTTP Request: GET http://testserver/api/reviews "HTTP/1.1 200 OK"
.C:\Users\kiwun\Documents\ai\VPN\portal_bot\migrations.py:95: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  {"key": key, "text": value, "created_at": datetime.utcnow()},
........C:\Users\kiwun\Documents\ai\VPN\portal_bot\worker.py:154: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  now = datetime.utcnow()
.
----------------------------------------------------------------------
Ran 91 tests in 42.966s

OK
```

### Admin/auth regressions

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_api_auth_and_tickets`
- Exit: `0`

```text
  now = datetime.utcnow()
.C:\Users\kiwun\Documents\ai\VPN\portal_bot\gift_cards_service.py:25: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  return datetime.utcnow()
C:\Users\kiwun\Documents\ai\VPN\portal_bot\events_service.py:44: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  created_at=datetime.utcnow(),
.C:\Users\kiwun\Documents\ai\VPN\portal_bot\api.py:4302: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  now = datetime.utcnow()
C:\Users\kiwun\Documents\ai\VPN\portal_bot\api.py:4344: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  row.updated_at = datetime.utcnow()
C:\Users\kiwun\Documents\ai\VPN\portal_bot\api.py:4362: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  row.updated_at = datetime.utcnow()
C:\Users\kiwun\Documents\ai\VPN\portal_bot\api.py:301: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  now = datetime.utcnow()
.....C:\Users\kiwun\Documents\ai\VPN\portal_bot\api.py:3282: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  now = datetime.utcnow()
C:\Users\kiwun\Documents\ai\VPN\portal_bot\api.py:1176: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  s.add(CampaignSend(tg_id=int(tg_id), campaign_key=str(campaign_key), sent_at=datetime.utcnow()))
C:\Users\kiwun\Documents\ai\VPN\portal_bot\points_service.py:42: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  return datetime.utcnow()
.C:\Users\kiwun\Documents\ai\VPN\portal_bot\api.py:3146: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  checked_at=datetime.utcnow().isoformat(),
.C:\Users\kiwun\Documents\ai\VPN\portal_bot\api.py:3374: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  user.pending_discount_set_at = datetime.utcnow()
.C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:487: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  user.expiry_at = datetime.utcnow() + timedelta(days=10)
C:\Users\kiwun\Documents\ai\VPN\portal_bot\api.py:796: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  if user.expiry_at >= datetime.utcnow():
...C:\Users\kiwun\Documents\ai\VPN\portal_bot\free_cycle_service.py:16: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  return datetime.utcnow()
C:\Users\kiwun\Documents\ai\VPN\portal_bot\api.py:1123: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  n = now or datetime.utcnow()
C:\Users\kiwun\Documents\ai\VPN\portal_bot\api.py:1146: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  now = datetime.utcnow()
C:\Users\kiwun\Documents\ai\VPN\portal_bot\offers_service.py:52: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  now = datetime.utcnow()
.
----------------------------------------------------------------------
Ran 17 tests in 16.064s

OK
```

### WebApp production build

- Command: `npm.cmd run build`
- Exit: `0`

```text
> next build

▲ Next.js 16.1.6 (Turbopack)

  Creating an optimized production build ...
✓ Compiled successfully in 2.1s
  Running TypeScript ...
  Collecting page data using 19 workers ...
  Generating static pages using 19 workers (0/23) ...
  Generating static pages using 19 workers (5/23) 
  Generating static pages using 19 workers (11/23) 
  Generating static pages using 19 workers (17/23) 
✓ Generating static pages using 19 workers (23/23) in 495.3ms
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
