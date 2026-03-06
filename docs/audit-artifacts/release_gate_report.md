# Release Gate Report

- Generated at: `2026-03-07 02:22:45`
- Status: `PASS`

## Summary

| Gate | Exit code | Duration (s) |
|---|---:|---:|
| Critical worker regression | 0 | 5.37 |
| Public link checks | 0 | 0.22 |
| Marketing production build | 0 | 47.05 |
| Admin webapp smoke | 0 | 0.24 |
| WebApp production build | 0 | 48.06 |
| UI visual smoke | 0 | 0.22 |

## Command Tails

### Critical worker regression

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_worker_retention`
- Exit: `0`

```text
C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\sqlalchemy\engine\default.py:952: DeprecationWarning: The default datetime adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute(statement, parameters)
....C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\sqlalchemy\sql\schema.py:3624: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  return util.wrap_callable(lambda ctx: fn(), fn)  # type: ignore
...
----------------------------------------------------------------------
Ran 7 tests in 4.289s

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
> portal-marketing@0.1.0 build
> next build

  ▲ Next.js 14.2.35

   Creating an optimized production build ...
 ✓ Compiled successfully
   Linting and checking validity of types ...
   Collecting page data ...
   Generating static pages (0/7) ...
   Generating static pages (1/7) 
   Generating static pages (3/7) 
   Generating static pages (5/7) 
 ✓ Generating static pages (7/7)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                              Size     First Load JS
┌ ○ /                                    8.88 kB        96.3 kB
├ ○ /_not-found                          873 B          88.3 kB
├ ○ /checkout                            4.79 kB        92.2 kB
├ ○ /offer                               142 B          87.6 kB
└ ○ /privacy                             142 B          87.6 kB
+ First Load JS shared by all            87.4 kB
  ├ chunks/117-885da3afc9dd5396.js       31.9 kB
  ├ chunks/fd9d1056-5d0c434f4506d830.js  53.6 kB
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
> next build

▲ Next.js 16.1.6 (Turbopack)

  Creating an optimized production build ...
✓ Compiled successfully in 4.5s
  Running TypeScript ...
  Collecting page data using 19 workers ...
  Generating static pages using 19 workers (0/23) ...
  Generating static pages using 19 workers (5/23) 
  Generating static pages using 19 workers (11/23) 
  Generating static pages using 19 workers (17/23) 
✓ Generating static pages using 19 workers (23/23) in 1034.4ms
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

### UI visual smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/ui_visual_smoke.py`
- Exit: `0`

```text
UI visual smoke passed.
```
