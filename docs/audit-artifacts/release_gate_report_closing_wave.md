# Release Gate Report

- Generated at: `2026-04-01 03:27:59`
- Status: `PASS`

## Summary

| Gate | Exit code | Duration (s) |
|---|---:|---:|
| Critical worker regression | 0 | 4.91 |
| API lifecycle smoke | 0 | 7.96 |
| Public link checks | 0 | 0.08 |
| Marketing production build | 0 | 34.33 |
| Admin webapp smoke | 0 | 0.09 |
| WebApp production build | 0 | 41.34 |
| WebApp Playwright E2E | 0 | 56.23 |
| UI visual smoke | 0 | 0.08 |

## Command Tails

### Critical worker regression

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_worker_retention`
- Exit: `0`

```text
C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\sqlalchemy\engine\default.py:952: DeprecationWarning: The default datetime adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute(statement, parameters)
......C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\sqlalchemy\sql\schema.py:3624: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  return util.wrap_callable(lambda ctx: fn(), fn)  # type: ignore
...
----------------------------------------------------------------------
Ran 9 tests in 4.517s

OK
```

### API lifecycle smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/api_lifecycle_smoke.py`
- Exit: `0`

```text
C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\sqlalchemy\engine\default.py:952: DeprecationWarning: The default datetime adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute(statement, parameters)
C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\sqlalchemy\sql\schema.py:3624: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  return util.wrap_callable(lambda ctx: fn(), fn)  # type: ignore
panel credentials missing for node=default (set NODE_DEFAULT_PANEL_USER/NODE_DEFAULT_PANEL_PASS)
panel credentials missing for node=default (set NODE_DEFAULT_PANEL_USER/NODE_DEFAULT_PANEL_PASS)
panel credentials missing for node=default (set NODE_DEFAULT_PANEL_USER/NODE_DEFAULT_PANEL_PASS)
panel credentials missing for node=default (set NODE_DEFAULT_PANEL_USER/NODE_DEFAULT_PANEL_PASS)
panel credentials missing for node=default (set NODE_DEFAULT_PANEL_USER/NODE_DEFAULT_PANEL_PASS)
panel credentials missing for node=default (set NODE_DEFAULT_PANEL_USER/NODE_DEFAULT_PANEL_PASS)
panel credentials missing for node=default (set NODE_DEFAULT_PANEL_USER/NODE_DEFAULT_PANEL_PASS)
panel credentials missing for node=default (set NODE_DEFAULT_PANEL_USER/NODE_DEFAULT_PANEL_PASS)
panel credentials missing for node=default (set NODE_DEFAULT_PANEL_USER/NODE_DEFAULT_PANEL_PASS)
panel credentials missing for node=default (set NODE_DEFAULT_PANEL_USER/NODE_DEFAULT_PANEL_PASS)
panel credentials missing for node=default (set NODE_DEFAULT_PANEL_USER/NODE_DEFAULT_PANEL_PASS)
panel credentials missing for node=default (set NODE_DEFAULT_PANEL_USER/NODE_DEFAULT_PANEL_PASS)
panel credentials missing for node=default (set NODE_DEFAULT_PANEL_USER/NODE_DEFAULT_PANEL_PASS)
C:\Users\kiwun\Documents\ai\VPN\tests\test_api_lifecycle_smoke.py:249: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  expiry_at=datetime.utcnow() + timedelta(days=20),
panel credentials missing for node=default (set NODE_DEFAULT_PANEL_USER/NODE_DEFAULT_PANEL_PASS)
panel credentials missing for node=default (set NODE_DEFAULT_PANEL_USER/NODE_DEFAULT_PANEL_PASS)
.
----------------------------------------------------------------------
Ran 1 test in 7.138s

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
✓ Compiled successfully in 1911.6ms
  Running TypeScript ...
  Collecting page data using 19 workers ...
  Generating static pages using 19 workers (0/23) ...
  Generating static pages using 19 workers (5/23) 
  Generating static pages using 19 workers (11/23) 
  Generating static pages using 19 workers (17/23) 
✓ Generating static pages using 19 workers (23/23) in 499.6ms
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
> portal-next-mockupv5@0.1.0 test:e2e
> playwright test e2e/admin-gate.spec.ts e2e/cabinet-flow.spec.ts


Running 15 tests using 2 workers

  ok  2 e2e\admin-gate.spec.ts:707:7 › Admin gate › redirects non-admin from /admin/* to /dashboard (2.2s)
[2m[WebServer] [22m[33m[1m⚠[22m[39m Cross origin request detected from 127.0.0.1 to /_next/* resource. In a future major version of Next.js, you will need to explicitly configure "allowedDevOrigins" in next.config to allow this.
[2m[WebServer] [22mRead more: https://nextjs.org/docs/app/api-reference/config/next-config-js/allowedDevOrigins
  ok  1 e2e\cabinet-flow.spec.ts:293:7 › Cabinet flow › shows a single connect link flow on the dashboard (3.4s)
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
  ok  4 e2e\cabinet-flow.spec.ts:306:7 › Cabinet flow › keeps the subscription page on one public connection link plus QR (3.2s)
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
  ok  5 e2e\cabinet-flow.spec.ts:319:7 › Cabinet flow › renders runtime connections on devices and keeps statistics actionable (5.5s)
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
[2m[WebServer] [22m[33m[1m⚠[22m[39m Fast Refresh had to perform a full reload. Read more: https://nextjs.org/docs/messages/fast-refresh-reload
  ok  6 e2e\cabinet-flow.spec.ts:333:7 › Cabinet flow › keeps downloads and support flows usable without the app (7.9s)
  ok  3 e2e\admin-gate.spec.ts:713:7 › Admin gate › allows admin to open all admin sections (22.4s)
  ok  7 e2e\cabinet-flow.spec.ts:349:7 › Cabinet flow › stays inside a narrow mobile viewport for core cabinet pages (6.3s)
  ok  8 e2e\admin-gate.spec.ts:735:7 › Admin gate › keeps admin dashboard stable when summary omits optional blocks (1.8s)
  ok  9 e2e\admin-gate.spec.ts:755:7 › Admin gate › shows clean Russian copy across admin surfaces (5.3s)
  ok 10 e2e\admin-gate.spec.ts:777:7 › Admin gate › lets admin search, sort, and paginate the users table (2.1s)
  ok 11 e2e\admin-gate.spec.ts:807:7 › Admin gate › lets admin safely delete only manual or test users (2.1s)
  ok 12 e2e\admin-gate.spec.ts:845:7 › Admin gate › shows observer-lite badges, filters, and detail diagnostics (3.0s)
  ok 13 e2e\admin-gate.spec.ts:886:7 › Admin gate › keeps admin pages clickable and inside the viewport on mobile (4.7s)
  ok 14 e2e\admin-gate.spec.ts:943:7 › Admin gate › shows node alert labels and probe failure details (1.7s)
  ok 15 e2e\admin-gate.spec.ts:1011:7 › Admin gate › lets admin triage a ticket and send a reply using stable status codes (2.2s)

  15 passed (54.7s)
```

### UI visual smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/ui_visual_smoke.py`
- Exit: `0`

```text
UI visual smoke passed.
```
