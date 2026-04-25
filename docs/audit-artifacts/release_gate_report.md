# Release Gate Report

- Generated at: `2026-04-25 02:12:51`
- Status: `PASS`
- Gate set: `default`
- Brain IP supplied: `no`
- Client platform gates: `none`
- Android audit required by selected gates: `no`

## Summary

| Gate | Exit code | Duration (s) |
|---|---:|---:|
| Release pytest matrix | 0 | 148.80 |
| Admin/auth regressions | 0 | 66.10 |
| Client security smoke | 0 | 0.10 |
| Client Flutter tests | 0 | 50.97 |
| API lifecycle smoke | 0 | 8.03 |
| Public link checks | 0 | 0.13 |
| Marketing production build | 0 | 67.64 |
| Admin webapp smoke | 0 | 0.12 |
| WebApp production build | 0 | 43.04 |
| WebApp Playwright E2E | 0 | 94.26 |
| UI visual smoke | 0 | 0.09 |

## Evidence Classification

| Evidence | Scope | Status | Notes |
|---|---|---|---|
| current-origin check | local default gate set | PASS | Runs on the operator workstation; does not prove brain-origin or RU-origin reachability. |
| brain-origin check | `scripts/verify_brain_ready.py` / predeploy readiness | BLOCKED_BY_ACCESS | Requires `--brain-ip` and live SSH/API access; keep separate from current-origin results. |
| RU-origin check | external RU probe (`mini` or replacement) | BLOCKED_BY_ACCESS | Not run by this local gate; requires an external RU probe host and redacted report. |
| Android physical audit | release-build localhost/control-surface audit | BLOCKED_BY_ACCESS | Public Android remains blocked unless this is run on physical hardware with the release build. |
| Runtime app-download smoke | `/api/client/apps` and provider checks | SKIPPED_NO_LIVE_TOKEN | Requires `TELEGRAM_INIT_DATA`; omit raw token values from evidence. |
| Client platform builds | none requested | NOT_REQUESTED | Repo/static gates alone do not create Android or Windows beta artifacts. |

## Command Tails

### Release pytest matrix

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest portal_bot/tests/test_app_first_api.py tests/test_portal_api.py tests/test_worker_retention.py tests/test_observer_service.py tests/test_observer_api.py tests/test_collect_xray_observer.py tests/test_predeploy_node_readiness.py tests/test_admin_webapp_smoke.py tests/test_public_copy_guardrails.py tests/test_reviews_username_masking.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-3_ldt1hi`
- Exit: `0`

```text
....................................................                     [100%]
52 passed in 147.34s (0:02:27)
```

### Admin/auth regressions

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest tests/test_api_auth_and_tickets.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-caucbrwh`
- Exit: `0`

```text
.........................................................                [100%]
57 passed in 65.16s (0:01:05)
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

### Client Flutter tests

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/run_client_release_gate.py test --suite full`
- Exit: `0`

```text
io.flutter.plugins.urllauncher.UrlLauncherTest > canLaunch_createsIntentWithPassedUrl PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > launch_returnsTrue PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > openWebView_handlesEnableDomStorage PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > openWebView_handlesEnableShowTitle PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > canLaunch_returnsFalse PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > launch_throwsForNoCurrentActivity PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > openWebView_returnsFalse PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > closeWebView_closes PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > canLaunch_returnsTrue PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > openWebView_handlesHeaders PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > openWebView_opensUrlInCustomTabsWithCORSAllowedHeader PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > launch_returnsFalse PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > openWebView_opensUrlInWebViewIfRequested PASSED

io.flutter.plugins.urllauncher.UrlLauncherTest > launch_createsIntentWithPassedUrl PASSED

io.flutter.plugins.urllauncher.WebViewActivityTest > extractHeaders_returnsEmptyMapWhenHeadersBundleNull PASSED

Deprecated Gradle features were used in this build, making it incompatible with Gradle 9.0.

You can use '--warning-mode all' to show the individual deprecation warnings and determine if they come from your own scripts or plugins.

For more on this, please refer to https://docs.gradle.org/8.3/userguide/command_line_interface.html#sec:command_line_warnings in the Gradle documentation.

BUILD SUCCESSFUL in 17s
87 actionable tasks: 10 executed, 77 up-to-date
Workspace Flutter and Android unit tests passed.
[client-gate] C:\Windows\System32\WindowsPowerShell\v1.0\powershell.EXE -NoProfile -ExecutionPolicy Bypass -File C:\Users\kiwun\Documents\ai\POKROV-app\scripts\run-tests.ps1 (cwd=C:\Users\kiwun\Documents\ai\POKROV-app)
```

### API lifecycle smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/api_lifecycle_smoke.py`
- Exit: `0`

```text
.
----------------------------------------------------------------------
Ran 1 test in 7.112s

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
[PASS] marketing\src\components\marketing-landing.tsx: Public marketing CTA no longer routes to connect host
[PASS] marketing\src\components\marketing-landing.tsx: Public cabinet CTA points to webapp host
[PASS] marketing\src\components\marketing-landing.tsx: Pricing CTA routes through public checkout gateway
[PASS] marketing\src\components\marketing-landing.tsx: Marketing footer exposes canonical news channel
[PASS] marketing\src\app\layout.tsx: Layout includes `metadataBase` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `manifest` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `icons` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `apple` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `/favicon.ico` metadata wiring
[PASS] marketing\src\app\layout.tsx: Layout includes `/apple-icon.png` metadata wiring
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

  в–І Next.js 14.2.35

   Creating an optimized production build ...
request to https://fonts.gstatic.com/s/manrope/v20/xn7gYHE41ni1AdIRggSxSvfedN62Zw.woff2 failed, reason: connect ETIMEDOUT 142.250.130.94:443

Retrying 1/3...
 вњ“ Compiled successfully
   Linting and checking validity of types ...
   Collecting page data ...
   Generating static pages (0/16) ...
   Generating static pages (4/16)
   Generating static pages (8/16)
   Generating static pages (12/16)
 вњ“ Generating static pages (16/16)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                              Size     First Load JS
в”Њ в—‹ /                                    1.52 kB        97.7 kB
в”њ в—‹ /_not-found                          873 B          88.3 kB
в”њ в—‹ /checkout                            8.05 kB         104 kB
в”њ в—‹ /devices                             193 B          96.4 kB
в”њ в—‹ /install                             193 B          96.4 kB
в”њ в—‹ /manifest.webmanifest                0 B                0 B
в”њ в—‹ /mobile                              193 B          96.4 kB
в”њ в—‹ /offer                               193 B          96.4 kB
в”њ в—‹ /privacy                             193 B          96.4 kB
в”њ в—‹ /robots.txt                          0 B                0 B
в”њ в—‹ /sitemap.xml                         0 B                0 B
в”њ в—‹ /telegram                            193 B          96.4 kB
в”њ в—‹ /tiktok                              193 B          96.4 kB
в”” в—‹ /youtube                             193 B          96.4 kB
+ First Load JS shared by all            87.5 kB
  в”њ chunks/004092b4-fb7a74995ea98db8.js  53.6 kB
  в”њ chunks/645-9f6b6af1d0e5a2b8.js       31.9 kB
  в”” other shared chunks (total)          1.96 kB


в—‹  (Static)  prerendered as static content
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
  Collecting page data using 19 workers ...
  Generating static pages using 19 workers (0/30) ...
  Generating static pages using 19 workers (7/30)
  Generating static pages using 19 workers (14/30)
  Generating static pages using 19 workers (22/30)
вњ“ Generating static pages using 19 workers (30/30) in 455.3ms
  Finalizing page optimization ...

Route (app)
в”Њ в—‹ /
в”њ в—‹ /_not-found
в”њ в—‹ /admin
в”њ в—‹ /admin/bonuses
в”њ в—‹ /admin/broadcast
в”њ в—‹ /admin/dashboard
в”њ в—‹ /admin/network
в”њ в—‹ /admin/nodes
в”њ в—‹ /admin/payments
в”њ в—‹ /admin/promos
в”њ в—‹ /admin/referrals
в”њ в—‹ /admin/tickets
в”њ в—‹ /admin/users
в”њ в—‹ /dashboard
в”њ в—‹ /dashboard/downloads
в”њ в—‹ /devices
в”њ в—‹ /downloads
в”њ в—‹ /icon.svg
в”њ в—‹ /pricing
в”њ в—‹ /profile
в”њ в—‹ /redeem
в”њ в—‹ /settings
в”њ в—‹ /statistics
в”њ в—‹ /subscription
в”њ в—‹ /subscription/checkout
в”њ в—‹ /support
в”њ в—‹ /support/legal
в”” в—‹ /support/thread


в—‹  (Static)  prerendered as static content
```

### WebApp Playwright E2E

- Command: `npm.cmd run test:e2e`
- Exit: `0`

```text


в—‹  (Static)  prerendered as static content


Running 31 tests using 1 worker

  ok  1 e2e\admin-gate.spec.ts:900:7 вЂє Admin gate вЂє redirects non-admin from /admin/* to /dashboard (499ms)
  ok  2 e2e\admin-gate.spec.ts:906:7 вЂє Admin gate вЂє allows admin to open all admin sections (4.2s)
  ok  3 e2e\admin-gate.spec.ts:930:7 вЂє Admin gate вЂє keeps an explicit path back to the cabinet from admin (1.1s)
  ok  4 e2e\admin-gate.spec.ts:941:7 вЂє Admin gate вЂє groups admin routes by operational category and keeps Telegram as fallback only (1.3s)
  ok  5 e2e\admin-gate.spec.ts:956:7 вЂє Admin gate вЂє keeps admin dashboard stable when summary omits optional blocks (814ms)
  ok  6 e2e\admin-gate.spec.ts:976:7 вЂє Admin gate вЂє shows clean Russian copy across admin surfaces (2.3s)
  ok  7 e2e\admin-gate.spec.ts:998:7 вЂє Admin gate вЂє lets admin search, sort, and paginate the users table (2.6s)
  ok  8 e2e\admin-gate.spec.ts:1028:7 вЂє Admin gate вЂє keeps the users filters synced into the URL and restores them on reload (1.5s)
  ok  9 e2e\admin-gate.spec.ts:1055:7 вЂє Admin gate вЂє lets admin safely delete only manual or test users (3.1s)
  ok 10 e2e\admin-gate.spec.ts:1093:7 вЂє Admin gate вЂє shows observer-lite badges, filters, and detail diagnostics (1.7s)
  ok 11 e2e\admin-gate.spec.ts:1134:7 вЂє Admin gate вЂє shows observer-lite empty state instead of misleading zero-only activity (1.7s)
  ok 12 e2e\admin-gate.spec.ts:1150:7 вЂє Admin gate вЂє keeps admin pages clickable and inside the viewport on mobile (3.6s)
  ok 13 e2e\admin-gate.spec.ts:1207:7 вЂє Admin gate вЂє shows node alert labels and probe failure details (1.3s)
  ok 14 e2e\admin-gate.spec.ts:1287:7 вЂє Admin gate вЂє shows node context with separate panel, dataplane, and transport detail (1.3s)
  ok 15 e2e\admin-gate.spec.ts:1364:7 вЂє Admin gate вЂє keeps rollout targeting fields and feed objects intact across save and reload (2.6s)
  ok 16 e2e\admin-gate.spec.ts:1404:7 вЂє Admin gate вЂє lets admin triage a ticket and send a reply using stable status codes (3.1s)
  ok 17 e2e\admin-gate.spec.ts:1438:7 вЂє Admin gate вЂє shows payment ledger and requires an audit note for manual reconciliation (1.1s)
  ok 18 e2e\cabinet-flow.spec.ts:347:7 вЂє Cabinet flow вЂє shows shared POKROV cabinet branding and a site return link (1.1s)
  ok 19 e2e\cabinet-flow.spec.ts:362:7 вЂє Cabinet flow вЂє shows an honest email-soon state on the root auth entry (836ms)
  ok 20 e2e\cabinet-flow.spec.ts:377:7 вЂє Cabinet flow вЂє keeps the email entry truthful when live delivery is not configured (873ms)
  ok 21 e2e\cabinet-flow.spec.ts:392:7 вЂє Cabinet flow вЂє reuses an existing web session and lands in the cabinet without showing auth entry again (1.1s)
  ok 22 e2e\cabinet-flow.spec.ts:401:7 вЂє Cabinet flow вЂє keeps the dashboard on consumer-safe access actions (1.1s)
  ok 23 e2e\cabinet-flow.spec.ts:417:7 вЂє Cabinet flow вЂє keeps cabinet navigation on native Next.js routing (1.8s)
  ok 24 e2e\cabinet-flow.spec.ts:438:7 вЂє Cabinet flow вЂє shows branded root and cabinet not-found recovery screens (1.1s)
  ok 25 e2e\cabinet-flow.spec.ts:450:7 вЂє Cabinet flow вЂє keeps the subscription page on renewal and support instead of raw connection sharing (1.1s)
  ok 26 e2e\cabinet-flow.spec.ts:462:7 вЂє Cabinet flow вЂє renders runtime connections on devices and keeps statistics as its own safe-summary page (1.3s)
  ok 27 e2e\cabinet-flow.spec.ts:480:7 вЂє Cabinet flow вЂє keeps cabinet copy human and hides node internals (1.5s)
  ok 28 e2e\cabinet-flow.spec.ts:494:7 вЂє Cabinet flow вЂє settings exposes clear Telegram bonus actions without raw account details (1.9s)
  ok 29 e2e\cabinet-flow.spec.ts:509:7 вЂє Cabinet flow вЂє shows honest payment history and Russian checkout continuation copy (1.2s)
  ok 30 e2e\cabinet-flow.spec.ts:526:7 вЂє Cabinet flow вЂє keeps downloads and support flows usable without the app (1.6s)
  ok 31 e2e\cabinet-flow.spec.ts:553:7 вЂє Cabinet flow вЂє stays inside a narrow mobile viewport for core cabinet pages (1.7s)

  31 passed (55.0s)
```

### UI visual smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/ui_visual_smoke.py`
- Exit: `0`

```text
UI visual smoke passed.
```
