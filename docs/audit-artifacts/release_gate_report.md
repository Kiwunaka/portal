# Release Gate Report

- Generated at: `2026-03-08 00:36:47`
- Status: `FAIL`

## Summary

| Gate | Exit code | Duration (s) |
|---|---:|---:|
| Backend unit tests | 1 | 81.91 |
| Admin/auth regressions | 0 | 37.00 |
| Public link checks | 0 | 0.09 |
| Marketing production build | 0 | 34.44 |
| Admin webapp smoke | 0 | 0.10 |
| WebApp production build | 0 | 43.08 |
| UI visual smoke | 1 | 0.09 |

## Command Tails

### Backend unit tests

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m unittest discover tests`
- Exit: `1`

```text
Traceback (most recent call last):
  File "C:\Users\kiwun\Documents\ai\VPN\tests\test_plan_policies.py", line 74, in test_panel_policy_defaults
    free_client = PanelClient(self._node("pl_free"))
                              ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\kiwun\Documents\ai\VPN\tests\test_plan_policies.py", line 45, in _node
    return NodeRuntime(
           ^^^^^^^^^^^^
TypeError: NodeRuntime.__init__() missing 2 required positional arguments: 'accepting_new_clients' and 'is_draining'

======================================================================
ERROR: test_panel_policy_node_overrides (test_plan_policies.PlanPolicyTests.test_panel_policy_node_overrides)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\kiwun\Documents\ai\VPN\tests\test_plan_policies.py", line 95, in test_panel_policy_node_overrides
    free_client = PanelClient(self._node("pl_free"))
                              ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\kiwun\Documents\ai\VPN\tests\test_plan_policies.py", line 45, in _node
    return NodeRuntime(
           ^^^^^^^^^^^^
TypeError: NodeRuntime.__init__() missing 2 required positional arguments: 'accepting_new_clients' and 'is_draining'

======================================================================
ERROR: test_nodes_for_user_excludes_brain_from_paid_pool (test_portal_api.PortalApiTests.test_nodes_for_user_excludes_brain_from_paid_pool)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\kiwun\Documents\ai\VPN\tests\test_portal_api.py", line 147, in test_nodes_for_user_excludes_brain_from_paid_pool
    out = api._nodes_for_user(user, nodes)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\kiwun\Documents\ai\VPN\portal_bot\api.py", line 7637, in _nodes_for_user
    mapped = _mapped_nodes_for_user(s, user, nodes)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\kiwun\Documents\ai\VPN\portal_bot\api.py", line 7548, in _mapped_nodes_for_user
    .filter(UserNode.tg_id == int(user.tg_id))
                                  ^^^^^^^^^^
AttributeError: 'types.SimpleNamespace' object has no attribute 'tg_id'

----------------------------------------------------------------------
Ran 133 tests in 80.650s

FAILED (errors=9)
```

### Admin/auth regressions

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m unittest tests.test_api_auth_and_tickets`
- Exit: `0`

```text
C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\sqlalchemy\engine\default.py:952: DeprecationWarning: The default datetime adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute(statement, parameters)
C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\sqlalchemy\sql\schema.py:3624: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  return util.wrap_callable(lambda ctx: fn(), fn)  # type: ignore
..C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:847: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  user.created_at = datetime.utcnow() - timedelta(days=45)
..C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:1044: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  now = datetime.utcnow().replace(microsecond=0)
......C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:1150: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  now = datetime.utcnow().replace(microsecond=0)
.C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:1183: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  now = datetime.utcnow().replace(microsecond=0)
............C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:971: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  user.expiry_at = datetime.utcnow() + timedelta(days=10)
subscription fallback detected token_fp=fe675fe7aaee tg_id=1001 action=notify_admin_once_per_day
.C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:998: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  user.expiry_at = datetime.utcnow() + timedelta(days=10)
subscription numeric fallback disabled token_fp=fe675fe7aaee token_len=4
subscription lookup failed token_fp=fe675fe7aaee token_len=4
.C:\Users\kiwun\Documents\ai\VPN\tests\test_api_auth_and_tickets.py:1018: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  user.expiry_at = datetime.utcnow() + timedelta(days=10)
.......
----------------------------------------------------------------------
Ran 32 tests in 35.976s

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
┌ ○ /                                    8.87 kB        96.3 kB
├ ○ /_not-found                          873 B          88.3 kB
├ ○ /checkout                            6.64 kB        94.1 kB
├ ○ /offer                               142 B          87.6 kB
└ ○ /privacy                             142 B          87.6 kB
+ First Load JS shared by all            87.4 kB
  ├ chunks/004092b4-fb7a74995ea98db8.js  53.6 kB
  ├ chunks/645-9f6b6af1d0e5a2b8.js       31.9 kB
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
✓ Compiled successfully in 2.5s
  Running TypeScript ...
  Collecting page data using 19 workers ...
  Generating static pages using 19 workers (0/23) ...
  Generating static pages using 19 workers (5/23) 
  Generating static pages using 19 workers (11/23) 
  Generating static pages using 19 workers (17/23) 
✓ Generating static pages using 19 workers (23/23) in 509.9ms
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
- Exit: `1`

```text
[FAIL] marketing-checkout-gateway: missing `����������� ����� Telegram` in marketing\src\app\checkout\page.tsx
[FAIL] marketing-checkout-gateway: missing `���������� � Telegram` in marketing\src\app\checkout\page.tsx
[FAIL] marketing-checkout-gateway: missing `������� � ������` in marketing\src\app\checkout\page.tsx
```
