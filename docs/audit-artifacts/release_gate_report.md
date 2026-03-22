# Release Gate Report

- Generated at: `2026-03-22 20:17:46`
- Status: `PASS`

## Summary

| Gate | Exit code | Duration (s) |
|---|---:|---:|
| Critical worker regression | 0 | 3.81 |
| Public link checks | 0 | 0.10 |
| Marketing production build | 0 | 45.66 |
| Admin webapp smoke | 0 | 0.11 |
| WebApp production build | 0 | 42.44 |
| UI visual smoke | 0 | 0.10 |

## Command Tails

### Critical worker regression

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_worker_retention`
- Exit: `0`

```text
C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\sqlalchemy\engine\default.py:952: DeprecationWarning: The default datetime adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute(statement, parameters)
.....C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\sqlalchemy\sql\schema.py:3624: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  return util.wrap_callable(lambda ctx: fn(), fn)  # type: ignore
...
----------------------------------------------------------------------
Ran 8 tests in 3.271s

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
├ ○ /checkout                            9.64 kB        97.1 kB
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
✓ Compiled successfully in 3.3s
  Running TypeScript ...
  Collecting page data using 19 workers ...
  Generating static pages using 19 workers (0/23) ...
  Generating static pages using 19 workers (5/23) 
  Generating static pages using 19 workers (11/23) 
  Generating static pages using 19 workers (17/23) 
✓ Generating static pages using 19 workers (23/23) in 521.7ms
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
