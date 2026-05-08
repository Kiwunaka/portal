# Release Gate Report

- Generated at: `2026-05-07 22:06:44`
- Status: `PASS`
- Gate set: `quick`
- Brain IP supplied: `no`
- Client platform gates: `none`
- Android audit required by selected gates: `no`

## Summary

| Gate | Exit code | Duration (s) |
|---|---:|---:|
| Critical worker regression | 0 | 6.61 |
| Payment and marketing release honesty | 0 | 36.41 |
| Paid checkout launch evidence tooling | 0 | 1.10 |
| GitHub release tooling | 0 | 1.19 |
| Client preflight | 0 | 0.09 |
| Client security smoke | 0 | 0.06 |
| Client portal Flutter tests | 0 | 19.68 |
| API lifecycle smoke | 0 | 8.20 |
| Public link checks | 0 | 0.09 |
| Marketing production build | 0 | 35.89 |
| Admin webapp smoke | 0 | 0.15 |
| WebApp production build | 0 | 17.43 |
| WebApp Playwright E2E | 0 | 98.85 |
| UI visual smoke | 0 | 0.09 |

## Evidence Classification

| Evidence | Scope | Status | Notes |
|---|---|---|---|
| current-origin check | local quick gate set | PASS | Runs on the operator workstation; does not prove brain-origin or RU-origin reachability. |
| brain-origin check | `scripts/verify_brain_ready.py` plus node predeploy readiness | BLOCKED_BY_ACCESS | Requires `--brain-ip` and live SSH/API access; includes control-plane/static probes and node readiness. |
| RU-origin check | external RU probe (`mini` or replacement) | BLOCKED_BY_ACCESS | Not run by this local gate; requires an external RU probe host and redacted report. |
| Android physical audit | release-build localhost/control-surface audit | BLOCKED_BY_ACCESS | Public Android remains blocked unless this is run on physical hardware with the release build. |
| Runtime app-download smoke | `/api/client/apps` and provider checks | SKIPPED_NO_LIVE_TOKEN | Requires `TELEGRAM_INIT_DATA`; omit raw token values from evidence. |
| Client platform builds | none requested | NOT_REQUESTED | Repo/static gates alone do not create Android or Windows beta artifacts. |

## Command Tails

### Critical worker regression

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest tests/test_worker_retention.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-_lqxgznx`
- Exit: `0`

```text
.........                                                                [100%]
9 passed in 5.96s
```

### Payment and marketing release honesty

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest tests/test_bot_paywall.py tests/test_marketing_release_readiness.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-36vuzw8x`
- Exit: `0`

```text
......................................................................   [100%]
70 passed in 35.42s
```

### Paid checkout launch evidence tooling

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest tests/test_paid_checkout_launch_evidence_check.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-28ibvegi`
- Exit: `0`

```text
...                                                                      [100%]
3 passed in 0.58s
```

### GitHub release tooling

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest tests/test_prepare_github_release_plan.py tests/test_publish_github_release_assets.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-59grqcc7`
- Exit: `0`

```text
.........                                                                [100%]
9 passed in 0.67s
```

### Client preflight

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/run_client_release_gate.py preflight`
- Exit: `0`

```text
[client-root] path: C:\Users\kiwun\Documents\ai\POKROV-app
[client-root] android shell: C:\Users\kiwun\Documents\ai\POKROV-app\apps\android_shell
[client-root] windows shell: C:\Users\kiwun\Documents\ai\POKROV-app\apps\windows_shell
[client-root] validate seed: C:\Users\kiwun\Documents\ai\POKROV-app\scripts\validate-seed.ps1
[client-root] bootstrap workspace: C:\Users\kiwun\Documents\ai\POKROV-app\scripts\bootstrap-workspace.ps1
[client-root] run tests: C:\Users\kiwun\Documents\ai\POKROV-app\scripts\run-tests.ps1
[client-root] build windows release: C:\Users\kiwun\Documents\ai\POKROV-app\scripts\build-windows-release.ps1
[ok] POKROV-app gate root is present
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
00:00 +4: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/app_first_runtime_bootstrap_test.dart: android materialization excludes desktop loopback listener inbounds
00:00 +5: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/app_first_runtime_bootstrap_test.dart: preserves a runtime-ready managed config on desktop hosts
00:00 +6: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: android seed app context keeps smoke profile free of desktop route keys
00:00 +7: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/app_first_runtime_bootstrap_test.dart: android preserves managed routing semantics while removing desktop-only DNS surfaces
00:00 +8: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: renders app-first protection shell with redeem actions
00:00 +9: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: renders app-first protection shell with redeem actions
00:00 +10: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: renders app-first protection shell with redeem actions
00:00 +11: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: renders app-first protection shell with redeem actions
00:00 +12: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: renders app-first protection shell with redeem actions
00:00 +13: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: renders app-first protection shell with redeem actions
00:00 +14: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: renders app-first protection shell with redeem actions
00:00 +15: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: renders app-first protection shell with redeem actions
00:00 +16: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: renders app-first protection shell with redeem actions
00:01 +17: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: profile handoffs open safe external destinations
00:01 +18: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: selected apps status is explicit beta MVP copy
00:01 +19: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: android protection surface keeps degraded runtime messaging consumer friendly
00:01 +20: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: android protection surface hides raw top-level host diagnostics
00:01 +21: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: shows a single logical location in locations
00:01 +22: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: primary connect action auto-prepares and starts host runtime
00:01 +23: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: android reconnect refreshes the managed profile even when one is already staged
00:02 +24: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: primary connect action is disabled when live connect is unavailable
00:02 +25: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: primary connect action keeps the host bridge message until runtime is running
00:02 +26: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: primary connect action polls the host bridge until runtime is running
00:02 +27: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: android shell refreshes runtime snapshot when the app resumes
00:02 +28: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: builds seed app context for public and readiness-only host lanes
00:02 +29: All tests passed!
00:00 +0: loading C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/test/android_manifest_test.dart
00:00 +0: C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/test/android_manifest_test.dart: android manifest declares special-use foreground service permission
00:00 +1: C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/test/android_manifest_test.dart: android runtime service source hardens foreground start failures
00:00 +2: C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/test/widget_test.dart: android shell boots the shared protection surface
00:00 +3: C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/test/widget_test.dart: android shell keeps raw runtime diagnostics out of first layer
00:00 +4: All tests passed!
00:00 +0: loading C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/test/widget_test.dart
00:00 +0: C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/test/widget_test.dart: windows shell boots the shared protection surface
00:00 +1: C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/test/widget_test.dart: windows shell boots the shared protection surface
00:00 +2: All tests passed!
[client-gate] C:\Windows\System32\WindowsPowerShell\v1.0\powershell.EXE -NoProfile -ExecutionPolicy Bypass -File C:\Users\kiwun\Documents\ai\POKROV-app\scripts\bootstrap-workspace.ps1 (cwd=C:\Users\kiwun\Documents\ai\POKROV-app)
[client-gate] C:\Users\kiwun\tools\flutter\git-3.24.3\bin\flutter.bat test (cwd=C:\Users\kiwun\Documents\ai\POKROV-app\packages\app_shell)
[client-gate] C:\Users\kiwun\tools\flutter\git-3.24.3\bin\flutter.bat test (cwd=C:\Users\kiwun\Documents\ai\POKROV-app\apps\android_shell)
[client-gate] C:\Users\kiwun\tools\flutter\git-3.24.3\bin\flutter.bat test (cwd=C:\Users\kiwun\Documents\ai\POKROV-app\apps\windows_shell)
```

### API lifecycle smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/api_lifecycle_smoke.py`
- Exit: `0`

```text
.
----------------------------------------------------------------------
Ran 1 test in 7.412s

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
[PASS] marketing\src\components\marketing-landing.tsx: Pricing CTA stays gated to install/status while release is NO-GO
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
   Creating an optimized production build ...
request to https://fonts.googleapis.com/css2?family=Manrope:wght@200..800&display=swap failed, reason: connect ETIMEDOUT 172.217.23.234:443

Retrying 1/3...
request to https://fonts.gstatic.com/s/manrope/v20/xn7gYHE41ni1AdIRggixSvfedN62Zw.woff2 failed, reason: connect ETIMEDOUT 172.217.171.99:443

Retrying 1/3...
 ✓ Compiled successfully
   Linting and checking validity of types ...
   Collecting page data ...
   Generating static pages (0/16) ...
   Generating static pages (4/16)
   Generating static pages (8/16)
   Generating static pages (12/16)
 ✓ Generating static pages (16/16)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                              Size     First Load JS
┌ ○ /                                    37.1 kB         133 kB
├ ○ /_not-found                          873 B          88.3 kB
├ ○ /checkout                            8.66 kB         105 kB
├ ○ /devices                             193 B          96.4 kB
├ ○ /install                             193 B          96.4 kB
├ ○ /manifest.webmanifest                0 B                0 B
├ ○ /mobile                              193 B          96.4 kB
├ ○ /offer                               193 B          96.4 kB
├ ○ /privacy                             193 B          96.4 kB
├ ○ /robots.txt                          0 B                0 B
├ ○ /sitemap.xml                         0 B                0 B
├ ○ /telegram                            193 B          96.4 kB
├ ○ /tiktok                              193 B          96.4 kB
└ ○ /youtube                             193 B          96.4 kB
+ First Load JS shared by all            87.5 kB
  ├ chunks/004092b4-49d726e311669ea8.js  53.6 kB
  ├ chunks/645-577ae345534d59cb.js       31.9 kB
  └ other shared chunks (total)          1.96 kB


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
  Generating static pages using 19 workers (0/31) ...
  Generating static pages using 19 workers (7/31)
  Generating static pages using 19 workers (15/31)
  Generating static pages using 19 workers (23/31)
✓ Generating static pages using 19 workers (31/31) in 371.4ms
  Finalizing page optimization ...

Route (app)
┌ ○ /
├ ○ /_not-found
├ ○ /admin
├ ○ /admin/bonuses
├ ○ /admin/broadcast
├ ○ /admin/dashboard
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
├ ○ /redeem
├ ○ /settings
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
  ok  3 e2e\admin-gate.spec.ts:991:7 › Admin gate › keeps an explicit path back to the cabinet from admin (1.9s)
  ok  4 e2e\admin-gate.spec.ts:1002:7 › Admin gate › groups admin routes by operational category and keeps Telegram as fallback only (1.2s)
  ok  5 e2e\admin-gate.spec.ts:1017:7 › Admin gate › shows release cockpit no-go state with runtime gates and external blockers (1.0s)
  ok  6 e2e\admin-gate.spec.ts:1037:7 › Admin gate › keeps release cockpit email gate blocked when public email mode is disabled (1.0s)
  ok  7 e2e\admin-gate.spec.ts:1052:7 › Admin gate › keeps admin dashboard stable when summary omits optional blocks (1.1s)
  ok  8 e2e\admin-gate.spec.ts:1072:7 › Admin gate › shows clean Russian copy across admin surfaces (1.7s)
  ok  9 e2e\admin-gate.spec.ts:1094:7 › Admin gate › lets admin search, sort, and paginate the users table (2.3s)
  ok 10 e2e\admin-gate.spec.ts:1124:7 › Admin gate › keeps the users filters synced into the URL and restores them on reload (1.7s)
  ok 11 e2e\admin-gate.spec.ts:1151:7 › Admin gate › lets admin safely delete only manual or test users (3.1s)
  ok 12 e2e\admin-gate.spec.ts:1189:7 › Admin gate › shows observer-lite badges, filters, and detail diagnostics (2.7s)
  ok 13 e2e\admin-gate.spec.ts:1230:7 › Admin gate › shows observer-lite empty state instead of misleading zero-only activity (1.3s)
  ok 14 e2e\admin-gate.spec.ts:1246:7 › Admin gate › keeps admin pages clickable and inside the viewport on mobile (3.4s)
  ok 15 e2e\admin-gate.spec.ts:1303:7 › Admin gate › shows node alert labels and probe failure details (1.1s)
  ok 16 e2e\admin-gate.spec.ts:1383:7 › Admin gate › shows node context with separate panel, dataplane, and transport detail (1.3s)
  ok 17 e2e\admin-gate.spec.ts:1460:7 › Admin gate › keeps rollout targeting fields and feed objects intact across save and reload (2.3s)
  ok 18 e2e\admin-gate.spec.ts:1500:7 › Admin gate › lets admin triage a ticket and send a reply using stable status codes (3.4s)
  ok 19 e2e\admin-gate.spec.ts:1534:7 › Admin gate › shows payment ledger and requires an audit note for manual reconciliation (1.1s)
  ok 20 e2e\cabinet-flow.spec.ts:475:7 › Cabinet flow › shows shared POKROV cabinet branding and a site return link (1.2s)
  ok 21 e2e\cabinet-flow.spec.ts:490:7 › Cabinet flow › shows an honest email-soon state on the root auth entry (777ms)
  ok 22 e2e\cabinet-flow.spec.ts:503:7 › Cabinet flow › keeps the email entry truthful when live delivery is not configured (779ms)
  ok 23 e2e\cabinet-flow.spec.ts:516:7 › Cabinet flow › supports enabled email register verify login and recovery from the auth entry (11.0s)
  ok 24 e2e\cabinet-flow.spec.ts:571:7 › Cabinet flow › keeps email verification and recovery tokens separate (5.1s)
  ok 25 e2e\cabinet-flow.spec.ts:591:7 › Cabinet flow › reuses an existing web session and lands in the cabinet without showing auth entry again (1.0s)
  ok 26 e2e\cabinet-flow.spec.ts:600:7 › Cabinet flow › stores a silently refreshed web session returned from Telegram auth (996ms)
  ok 27 e2e\cabinet-flow.spec.ts:619:7 › Cabinet flow › shows a human reauth CTA when the browser session is expired (631ms)
  ok 28 e2e\cabinet-flow.spec.ts:637:7 › Cabinet flow › keeps the dashboard on consumer-safe access actions (1.0s)
  ok 29 e2e\cabinet-flow.spec.ts:653:7 › Cabinet flow › keeps cabinet navigation on native Next.js routing (1.1s)
  ok 30 e2e\cabinet-flow.spec.ts:674:7 › Cabinet flow › shows branded root and cabinet not-found recovery screens (1.2s)
  ok 31 e2e\cabinet-flow.spec.ts:686:7 › Cabinet flow › shows subscription manual connection only as an explicit fallback (2.8s)
  ok 32 e2e\cabinet-flow.spec.ts:703:7 › Cabinet flow › renders runtime connections on devices and keeps statistics as its own safe-summary page (1.5s)
  ok 33 e2e\cabinet-flow.spec.ts:721:7 › Cabinet flow › keeps cabinet copy human and hides node internals (1.4s)
  ok 34 e2e\cabinet-flow.spec.ts:735:7 › Cabinet flow › settings exposes clear Telegram bonus actions without raw account details (1.7s)
  ok 35 e2e\cabinet-flow.spec.ts:750:7 › Cabinet flow › shows honest payment history and Russian checkout continuation copy (1.4s)
  ok 36 e2e\cabinet-flow.spec.ts:768:7 › Cabinet flow › keeps checkout disabled when payment providers are configured but launch evidence is blocked (1.1s)
  ok 37 e2e\cabinet-flow.spec.ts:802:7 › Cabinet flow › checks and redeems access keys from the cabinet redeem route (2.8s)
  ok 38 e2e\cabinet-flow.spec.ts:867:7 › Cabinet flow › keeps downloads and support flows usable without the app (4.2s)
  ok 39 e2e\cabinet-flow.spec.ts:894:7 › Cabinet flow › loads protected support attachments through authenticated blob fetch (1.0s)
  ok 40 e2e\cabinet-flow.spec.ts:914:7 › Cabinet flow › stays inside a narrow mobile viewport for core cabinet pages (1.7s)

  40 passed (1.4m)
```

### UI visual smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/ui_visual_smoke.py`
- Exit: `0`

```text
UI visual smoke passed.
```
