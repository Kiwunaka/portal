# Release Gate Report

- Generated at: `2026-07-07 18:01:55`
- Status: `FAIL`
- Gate set: `quick`
- Brain IP supplied: `yes`
- Client platform gates: `none`
- Android audit required by selected gates: `no`

## Summary

| Gate | Exit code | Duration (s) |
|---|---:|---:|
| Node predeploy readiness | 1 | 39.09 |
| Critical worker regression | 0 | 13.63 |
| Client security smoke | 0 | 0.11 |
| Client portal Flutter tests | 0 | 39.75 |
| API lifecycle smoke | 0 | 14.24 |
| Public link checks | 0 | 0.12 |
| Marketing production build | 0 | 22.69 |
| AdminApp production build | 0 | 22.73 |
| Admin webapp smoke | 0 | 0.19 |
| WebApp production build | 0 | 24.26 |
| WebApp Playwright E2E | 0 | 80.75 |
| UI visual smoke | 0 | 0.11 |

## Evidence Classification

| Evidence | Scope | Status | Notes |
|---|---|---|---|
| current-origin check | local quick gate set | FAIL | Runs on the operator workstation; does not prove brain-origin or RU-origin reachability. |
| brain-origin check | `scripts/verify_brain_ready.py` / predeploy readiness | FAIL | Requires `--brain-ip` and live SSH/API access; keep separate from current-origin results. |
| RU-origin check | external RU probe (`mini` or replacement) | BLOCKED_BY_ACCESS | Not run by this local gate; requires an external RU probe host and redacted report. |
| Android physical audit | release-build localhost/control-surface audit | BLOCKED_BY_ACCESS | Public Android remains blocked unless this is run on physical hardware with the release build. |
| Runtime app-download smoke | `/api/client/apps` and provider checks | SKIPPED_NO_LIVE_TOKEN | Requires `TELEGRAM_INIT_DATA`; omit raw token values from evidence. |
| Client platform builds | none requested | NOT_REQUESTED | Repo/static gates alone do not create Android or Windows beta artifacts. |

## Command Tails

### Node predeploy readiness

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/predeploy_node_readiness.py --brain-ip 82.21.114.104 --web-domain pokrov.space --ssh-user root --ssh-port 29374 --passwords C:\Users\kiwun\Documents\ai\VPN\VPN NODE SSH KEYS\PASSWORDS.txt`
- Exit: `1`

```text
    raise SSHException(
paramiko.ssh_exception.SSHException: Error reading SSH protocol banner

Exception (client): Error reading SSH protocol banner
Traceback (most recent call last):
  File "C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\paramiko\transport.py", line 2363, in _check_banner
    buf = self.packetizer.readline(timeout)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\paramiko\packet.py", line 395, in readline
    buf += self._read_timeout(timeout)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\paramiko\packet.py", line 665, in _read_timeout
    raise EOFError()
EOFError

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\paramiko\transport.py", line 2179, in run
    self._check_banner()
  File "C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\paramiko\transport.py", line 2367, in _check_banner
    raise SSHException(
paramiko.ssh_exception.SSHException: Error reading SSH protocol banner

Traceback (most recent call last):
  File "C:\Users\kiwun\Documents\ai\VPN\scripts\predeploy_node_readiness.py", line 532, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "C:\Users\kiwun\Documents\ai\VPN\scripts\predeploy_node_readiness.py", line 502, in main
    drift_payload = _collect_drift_payload(rows, ssh_user=args.ssh_user, ssh_port=int(args.ssh_port), passwords=passwords)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\kiwun\Documents\ai\VPN\scripts\predeploy_node_readiness.py", line 413, in _collect_drift_payload
    inspected = _inspect_runtime_inbound(row, ssh_user=ssh_user, ssh_port=ssh_port, passwords=passwords)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\kiwun\Documents\ai\VPN\scripts\predeploy_node_readiness.py", line 372, in _inspect_runtime_inbound
    ssh, auth_method = connect_node(code=row.code, host=row.host, user=<redacted> port=ssh_port, passwords_path=passwords)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\kiwun\Documents\ai\VPN\scripts\node_access.py", line 278, in connect_node
    raise RuntimeError(f"SSH auth failed for node {code}: {last_error}")
RuntimeError: SSH auth failed for node it: Error reading SSH protocol banner
```

### Critical worker regression

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest tests/test_worker_retention.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-o9n3mfoa`
- Exit: `0`

```text
..........                                                               [100%]
10 passed in 12.69s
```

### Client security smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/client_security_smoke.py`
- Exit: `0`

```text
[check] product contract: C:\Users\kiwun\Documents\ai\POKROV-app\config\product-contract.seed.json
[check] runtime profile: C:\Users\kiwun\Documents\ai\POKROV-app\config\runtime-profile.seed.json
[check] runtime artifacts: C:\Users\kiwun\Documents\ai\POKROV-app\config\runtime-artifacts.seed.json
[check] Android manifest: C:\Users\kiwun\Documents\ai\POKROV-app\apps\android_shell\android\app\src\main\AndroidManifest.xml
[check] Android build.gradle: C:\Users\kiwun\Documents\ai\POKROV-app\apps\android_shell\android\app\build.gradle
[check] Windows release seed: C:\Users\kiwun\Documents\ai\POKROV-app\config\windows-release.seed.json
[pass] client security smoke checks passed
```

### Client portal Flutter tests

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/run_client_release_gate.py test --suite portal`
- Exit: `0`

```text
  material_color_utilities 0.11.1 (0.13.0 available)
  meta 1.17.0 (1.18.3 available)
  path_provider 2.1.5 (2.1.6 available)
  path_provider_android 2.2.15 (2.3.1 available)
  path_provider_foundation 2.4.1 (2.6.0 available)
  path_provider_linux 2.2.1 (2.2.2 available)
  path_provider_platform_interface 2.1.2 (2.1.3 available)
  source_span 1.10.0 (1.10.2 available)
  string_scanner 1.2.0 (1.4.1 available)
  term_glyph 1.2.1 (1.2.2 available)
  test_api 0.7.7 (0.7.13 available)
  url_launcher 6.3.1 (6.3.2 available)
  url_launcher_android 6.3.14 (6.3.32 available)
  url_launcher_ios 6.3.3 (6.4.1 available)
  url_launcher_linux 3.2.1 (3.2.2 available)
  url_launcher_macos 3.2.2 (3.2.5 available)
  url_launcher_web 2.3.3 (2.4.3 available)
  url_launcher_windows 3.1.4 (3.1.5 available)
  vector_math 2.2.0 (2.4.0 available)
  vm_service 14.2.5 (15.2.0 available)
  win32 5.10.1 (6.3.0 available)
Got dependencies!
31 packages have newer versions incompatible with dependency constraints.
Try `flutter pub outdated` for more information.
00:00 +0: loading C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/test/android_manifest_test.dart
00:00 +0: C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/test/android_manifest_test.dart: android manifest declares special-use foreground service permission
00:00 +1: C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/test/android_manifest_test.dart: android runtime service source hardens foreground start failures
00:00 +2: C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/test/widget_test.dart: android shell boots the shared protection surface
00:01 +3: C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/test/widget_test.dart: android shell keeps raw runtime diagnostics out of first layer
00:01 +4: All tests passed!
00:00 +0: loading C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/test/widget_test.dart
00:00 +0: C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/test/widget_test.dart: windows tray show window restores minimized windows before focusing
00:00 +1: C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/test/widget_test.dart: windows tray show window skips restore when already visible
00:00 +2: C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/test/widget_test.dart: windows shell boots the shared protection surface
00:00 +3: C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/test/widget_test.dart: windows shell boots the shared protection surface
00:01 +4: All tests passed!
[client-gate] C:\Program Files\PowerShell\7\pwsh.EXE -NoProfile -ExecutionPolicy Bypass -File C:\Users\kiwun\Documents\ai\POKROV-app\scripts\bootstrap-workspace.ps1 (cwd=C:\Users\kiwun\Documents\ai\POKROV-app)
[client-gate] C:\Users\kiwun\AppData\Roaming\npm\flutter.CMD test (cwd=C:\Users\kiwun\Documents\ai\POKROV-app\packages\app_shell)
[client-gate] C:\Users\kiwun\AppData\Roaming\npm\flutter.CMD test (cwd=C:\Users\kiwun\Documents\ai\POKROV-app\apps\android_shell)
[client-gate] C:\Users\kiwun\AppData\Roaming\npm\flutter.CMD test (cwd=C:\Users\kiwun\Documents\ai\POKROV-app\apps\windows_shell)
```

### API lifecycle smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/api_lifecycle_smoke.py`
- Exit: `0`

```text
.
----------------------------------------------------------------------
Ran 1 test in 13.268s

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
[PASS] marketing\src\app\page.tsx: Public marketing CTA no longer routes to connect host
[PASS] marketing\src\components\layout\page-shell.tsx: Public cabinet CTA points to webapp host
[PASS] marketing\src\components\home\pricing.tsx: Pricing CTA routes through public checkout gateway
[PASS] marketing\src\components\layout\footer.tsx: Marketing footer exposes canonical news channel
[PASS] marketing\src\app\layout.tsx: Layout includes `metadataBase` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `manifest` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `icons` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `apple` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `/favicon.ico` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `/apple-icon.png` metadata wiring
[PASS] marketing\src\lib\marketing-site.ts: Marketing metadata declares `alternates`
[PASS] marketing\src\lib\marketing-site.ts: Marketing metadata declares `canonical`
[PASS] marketing\src\lib\marketing-site.ts: Marketing metadata declares `twitter`
[PASS] marketing\src\lib\marketing-site.ts: Marketing metadata declares `images`
[PASS] marketing\src\app\page.tsx: Home page wires `buildMarketingMetadata`
[PASS] marketing\src\app\page.tsx: Home page wires `buildSoftwareApplicationJsonLd`
[PASS] marketing\src\app\page.tsx: Home page wires `buildFaqJsonLd`
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

▲ Next.js 16.1.6 (Turbopack)
- Experiments (use with caution):
  ✓ externalDir

  Creating an optimized production build ...
✓ Compiled successfully in 2.6s
  Running TypeScript ...
  Collecting page data using 19 workers ...
  Generating static pages using 19 workers (0/16) ...
  Generating static pages using 19 workers (4/16)
  Generating static pages using 19 workers (8/16)
  Generating static pages using 19 workers (12/16)
✓ Generating static pages using 19 workers (16/16) in 873.7ms
  Finalizing page optimization ...

Route (app)
┌ ○ /
├ ○ /_not-found
├ ○ /checkout
├ ○ /devices
├ ○ /install
├ ○ /manifest.webmanifest
├ ○ /mobile
├ ○ /offer
├ ○ /privacy
├ ○ /robots.txt
├ ○ /sitemap.xml
├ ○ /telegram
├ ○ /tiktok
├ ○ /vpn
└ ○ /youtube


○  (Static)  prerendered as static content
```

### AdminApp production build

- Command: `npm.cmd run build`
- Exit: `0`

```text
> pokrov-adminapp@0.1.0 build
> next build

▲ Next.js 16.2.10 (Turbopack)
- Experiments (use with caution):
  ✓ externalDir

  Creating an optimized production build ...
✓ Compiled successfully in 2.9s
  Running TypeScript ...
  Finished TypeScript in 3.2s ...
  Collecting page data using 5 workers ...
  Generating static pages using 5 workers (0/16) ...
  Generating static pages using 5 workers (4/16)
  Generating static pages using 5 workers (8/16)
  Generating static pages using 5 workers (12/16)
✓ Generating static pages using 5 workers (16/16) in 859ms
  Finalizing page optimization ...

Route (app)
┌ ○ /
├ ○ /_not-found
└ ● /[section]
  ├ /nodes
  ├ /traffic
  ├ /free-tier
  └ [+10 more paths]


○  (Static)  prerendered as static content
●  (SSG)     prerendered as static HTML (uses generateStaticParams)
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
  Finalizing page optimization ...

Route (app)
┌ ○ /
├ ○ /_not-found
├ ○ /admin
├ ○ /admin/bonuses
├ ○ /admin/broadcast
├ ○ /admin/dashboard
├ ○ /admin/funnel
├ ○ /admin/network
├ ○ /admin/nodes
├ ○ /admin/payments
├ ○ /admin/promos
├ ○ /admin/referrals
├ ○ /admin/release
├ ○ /admin/tickets
├ ○ /admin/users
├ ○ /dashboard
├ ○ /dashboard/downloads
├ ○ /devices
├ ○ /downloads
├ ○ /icon.svg
├ ○ /pricing
├ ○ /profile
├ ○ /recover
├ ○ /redeem
├ ○ /settings
├ ○ /statistics
├ ○ /subscription
├ ○ /subscription/checkout
├ ○ /support
├ ○ /support/legal
├ ○ /support/thread
└ ○ /verify


○  (Static)  prerendered as static content

[fix-export-segment-paths] created 72 dot-joined segment payload copies
```

### WebApp Playwright E2E

- Command: `npm.cmd run test:e2e`
- Exit: `0`

```text
  ok  9 e2e\admin-gate.spec.ts:1210:7 › Admin gate › lets admin search, sort, and paginate the users table (2.1s)
  ok 10 e2e\admin-gate.spec.ts:1240:7 › Admin gate › keeps the users filters synced into the URL and restores them on reload (1.4s)
  ok 11 e2e\admin-gate.spec.ts:1267:7 › Admin gate › lets admin safely delete only manual or test users (1.5s)
  ok 12 e2e\admin-gate.spec.ts:1305:7 › Admin gate › shows observer-lite badges, filters, and detail diagnostics (1.1s)
  ok 13 e2e\admin-gate.spec.ts:1347:7 › Admin gate › shows observer-lite empty state instead of misleading zero-only activity (793ms)
  ok 14 e2e\admin-gate.spec.ts:1363:7 › Admin gate › keeps admin pages clickable and inside the viewport on mobile (1.8s)
  ok 15 e2e\admin-gate.spec.ts:1420:7 › Admin gate › shows node alert labels and probe failure details (1.4s)
  ok 16 e2e\admin-gate.spec.ts:1500:7 › Admin gate › shows node context with separate panel, dataplane, and transport detail (910ms)
  ok 17 e2e\admin-gate.spec.ts:1577:7 › Admin gate › keeps rollout targeting fields and feed objects intact across save and reload (1.3s)
  ok 18 e2e\admin-gate.spec.ts:1617:7 › Admin gate › lets admin triage a ticket and send a reply using stable status codes (2.7s)
  ok 19 e2e\admin-gate.spec.ts:1651:7 › Admin gate › shows payment ledger and requires an audit note for manual reconciliation (1.1s)
  ok 20 e2e\cabinet-flow.spec.ts:409:7 › Cabinet session persistence › exchanges an app handoff token once and removes it from the URL (981ms)
  ok 21 e2e\cabinet-flow.spec.ts:424:7 › Cabinet session persistence › uses the exchanged cabinet target path (836ms)
  ok 22 e2e\cabinet-flow.spec.ts:438:7 › Cabinet session persistence › explains a reused app handoff link and removes it from the URL (673ms)
  ok 23 e2e\cabinet-flow.spec.ts:453:7 › Cabinet session persistence › reuses an email web session from the cookie fallback (969ms)
  ok 24 e2e\cabinet-flow.spec.ts:473:7 › Cabinet flow › shows shared POKROV cabinet branding and a site return link (1.0s)
  ok 25 e2e\cabinet-flow.spec.ts:492:7 › Cabinet flow › uses desktop navigation at 1280px instead of the mobile bottom menu (1.1s)
  ok 26 e2e\cabinet-flow.spec.ts:503:7 › Cabinet flow › shows email and Telegram entry on the root auth entry (769ms)
  ok 27 e2e\cabinet-flow.spec.ts:518:7 › Cabinet flow › keeps the email entry available alongside Telegram (673ms)
  ok 28 e2e\cabinet-flow.spec.ts:530:7 › Cabinet flow › reuses an existing web session and lands in the cabinet without showing auth entry again (926ms)
  ok 29 e2e\cabinet-flow.spec.ts:538:7 › Cabinet flow › shows a human reauth CTA when the browser session is expired (662ms)
  ok 30 e2e\cabinet-flow.spec.ts:556:7 › Cabinet flow › maps raw Telegram deprecated auth errors to a reauth CTA (1.0s)
  ok 31 e2e\cabinet-flow.spec.ts:573:7 › Cabinet flow › keeps the dashboard on consumer-safe access actions (918ms)
  ok 32 e2e\cabinet-flow.spec.ts:591:7 › Cabinet flow › shows the compact mobile cabinet shell and one dashboard action (1.2s)
  ok 33 e2e\cabinet-flow.spec.ts:618:7 › Cabinet flow › keeps cabinet navigation usable with left-click browser routing (1.2s)
  ok 34 e2e\cabinet-flow.spec.ts:632:7 › Cabinet flow › shows branded root and cabinet not-found recovery screens (925ms)
  ok 35 e2e\cabinet-flow.spec.ts:644:7 › Cabinet flow › shows subscription manual connection only as an explicit fallback (1.2s)
  ok 36 e2e\cabinet-flow.spec.ts:665:7 › Cabinet flow › keeps manual setup closed from a direct hash when no active link exists (841ms)
  ok 37 e2e\cabinet-flow.spec.ts:679:7 › Cabinet flow › keeps paid plan cards selectable for a free monthly account (815ms)
  ok 38 e2e\cabinet-flow.spec.ts:742:7 › Cabinet flow › renders runtime connections on devices and keeps statistics as its own safe-summary page (1.5s)
  ok 39 e2e\cabinet-flow.spec.ts:763:7 › Cabinet flow › keeps redeem as a compact activation task (888ms)
  ok 40 e2e\cabinet-flow.spec.ts:777:7 › Cabinet flow › keeps cabinet copy human and hides node internals (1.0s)
  ok 41 e2e\cabinet-flow.spec.ts:791:7 › Cabinet flow › settings exposes clear Telegram bonus actions without raw account details (2.5s)
  ok 42 e2e\cabinet-flow.spec.ts:809:7 › Cabinet flow › shows honest payment history and Russian checkout continuation copy (1.1s)
  ok 43 e2e\cabinet-flow.spec.ts:847:7 › Cabinet flow › keeps downloads and support flows usable without the app (2.2s)
  ok 44 e2e\cabinet-flow.spec.ts:881:7 › Cabinet flow › renders support thread attachments without exposing private access data (863ms)
  ok 45 e2e\cabinet-flow.spec.ts:899:7 › Cabinet flow › keeps legal documents as compact support rows (810ms)
  ok 46 e2e\cabinet-flow.spec.ts:912:7 › Cabinet flow › stays inside a narrow mobile viewport for core cabinet pages (1.0s)

  46 passed (59.4s)
```

### UI visual smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/ui_visual_smoke.py`
- Exit: `0`

```text
UI visual smoke passed.
```
