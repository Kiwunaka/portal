# Release Gate Report

- Generated at: `2026-08-14 08:36:47`
- Status: `PASS`
- Gate set: `quick`
- Brain IP supplied: `no`
- Client platform gates: `none`
- Android audit required by selected gates: `no`

## Summary

| Gate | Exit code | Duration (s) |
|---|---:|---:|
| Critical worker regression | 0 | 50.73 |
| Client security smoke | 0 | 0.51 |
| Client portal Flutter tests | 0 | 52.06 |
| API lifecycle smoke | 0 | 26.47 |
| Public link checks | 0 | 0.10 |
| Marketing production build | 0 | 23.97 |
| AdminApp production build | 0 | 24.92 |
| Admin webapp smoke | 0 | 0.18 |
| WebApp production build | 0 | 28.33 |
| WebApp Playwright E2E | 0 | 82.49 |
| UI visual smoke | 0 | 0.10 |

## Evidence Classification

| Evidence | Scope | Status | Notes |
|---|---|---|---|
| current-origin check | local quick gate set | PASS | Runs on the operator workstation; does not prove brain-origin or RU-origin reachability. |
| brain-origin check | `scripts/verify_brain_ready.py` / predeploy readiness | BLOCKED_BY_ACCESS | Requires `--brain-ip` and live SSH/API access; keep separate from current-origin results. |
| RU-origin check | external RU probe (`mini` or replacement) | BLOCKED_BY_ACCESS | Not run by this local gate; requires an external RU probe host and redacted report. |
| Android physical audit | release-build localhost/control-surface audit | BLOCKED_BY_ACCESS | Public Android remains blocked unless this is run on physical hardware with the release build. |
| Runtime app-download smoke | `/api/client/apps` and provider checks | SKIPPED_NO_LIVE_TOKEN | Requires `TELEGRAM_INIT_DATA`; omit raw token values from evidence. |
| Client platform builds | none requested | NOT_REQUESTED | Repo/static gates alone do not create Android or Windows beta artifacts. |

## Command Tails

### Critical worker regression

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest tests/test_worker_retention.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-7mpjkqta`
- Exit: `0`

```text
.........................                                                [100%]
25 passed in 49.85s
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
  screen_retriever_linux 0.2.0 (0.2.2 available)
  screen_retriever_macos 0.2.0 (0.2.2 available)
  screen_retriever_platform_interface 0.2.0 (0.2.2 available)
  screen_retriever_windows 0.2.0 (0.2.2 available)
  source_span 1.10.0 (1.10.2 available)
  string_scanner 1.2.0 (1.4.1 available)
  term_glyph 1.2.1 (1.2.2 available)
  test_api 0.7.7 (0.7.13 available)
  tray_manager 0.5.2 (0.5.3 available)
  url_launcher 6.3.1 (6.3.2 available)
  url_launcher_android 6.3.14 (6.3.32 available)
  url_launcher_ios 6.3.3 (6.4.1 available)
  url_launcher_linux 3.2.1 (3.2.2 available)
  url_launcher_macos 3.2.2 (3.2.5 available)
  url_launcher_web 2.3.3 (2.4.3 available)
  url_launcher_windows 3.1.4 (3.1.5 available)
  vector_math 2.2.0 (2.4.2 available)
  vm_service 14.2.5 (15.2.0 available)
  win32 5.10.1 (6.4.0 available)
  window_manager 0.5.1 (0.5.2 available)
  xml 6.6.1 (7.0.1 available)
Got dependencies!
42 packages have newer versions incompatible with dependency constraints.
Try `flutter pub outdated` for more information.
00:00 +0: loading C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/test/widget_test.dart
00:00 +0: C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/test/widget_test.dart: windows minimum size keeps the compact drawer lane reachable
00:00 +1: C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/test/widget_test.dart: windows tray connection label reports actionable state
00:00 +2: C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/test/widget_test.dart: windows tray show window restores minimized windows before focusing
00:00 +3: C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/test/widget_test.dart: windows tray show window skips restore when already visible
00:00 +4: C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/test/widget_test.dart: windows close hides to tray while prevent-close is active
00:00 +5: C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/test/widget_test.dart: windows close leaves the window alone when prevent-close is off
00:00 +6: C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/test/widget_test.dart: windows tray exit destroys tray before the native window
00:00 +7: C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/test/widget_test.dart: windows shell boots the shared protection surface
00:00 +8: C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/test/widget_test.dart: windows shell boots the shared protection surface
00:00 +9: C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/test/widget_test.dart: windows shell boots the shared protection surface
00:00 +10: All tests passed!
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
Ran 1 test in 25.592s

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
[PASS] portal_bot\api_admin_routes.py: Admin campaign link builder marks public checkout as safe fallback
[PASS] portal_bot\api.py: Numeric subscription fallback is explicit compatibility and defaults off

Link check passed.
```

### Marketing production build

- Command: `npm.cmd run build`
- Exit: `0`

```text
  Generating static pages using 19 workers (16/32)
  Generating static pages using 19 workers (24/32)
✓ Generating static pages using 19 workers (32/32) in 464.9ms
  Finalizing page optimization ...

Route (app)
┌ ○ /
├ ○ /_not-found
├ ○ /android
├ ○ /best-vpn
├ ○ /billing/no-autosubscription
├ ○ /checkout
├ ○ /compare/free-vpn
├ ○ /devices
├ ○ /fallback
├ ○ /guides
├ ○ /guides/pokrov-app
├ ○ /install
├ ○ /install/android
├ ○ /install/windows
├ ○ /manifest.webmanifest
├ ○ /mobile
├ ○ /offer
├ ○ /privacy
├ ○ /programs
├ ○ /robots.txt
├ ○ /sitemap.xml
├ ○ /status
├ ○ /support/install
├ ○ /telegram
├ ○ /tiktok
├ ○ /transparency
├ ○ /trial/no-card
├ ○ /trust/github-releases
├ ○ /vpn
├ ○ /windows
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
✓ Compiled successfully in 4.3s
  Running TypeScript ...
  Finished TypeScript in 5.4s ...
  Collecting page data using 5 workers ...
  Generating static pages using 5 workers (0/17) ...
  Generating static pages using 5 workers (4/17)
  Generating static pages using 5 workers (8/17)
  Generating static pages using 5 workers (12/17)
✓ Generating static pages using 5 workers (17/17) in 599ms
  Finalizing page optimization ...

Route (app)
┌ ○ /
├ ○ /_not-found
└ ● /[section]
  ├ /nodes
  ├ /traffic
  ├ /alerts
  └ [+11 more paths]


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
├ ○ /admin/bonuses
├ ○ /admin/broadcast
├ ○ /admin/dashboard
├ ○ /admin/funnel
├ ○ /admin/network
├ ○ /admin/nodes
├ ○ /admin/payments
├ ○ /admin/programs
├ ○ /admin/promos
├ ○ /admin/referrals
├ ○ /admin/release
├ ○ /admin/tickets
├ ○ /admin/users
├ ○ /dashboard
├ ○ /dashboard/downloads
├ ○ /devices
├ ○ /downloads
├ ○ /guides
├ ○ /guides/pokrov-app
├ ○ /icon.svg
├ ○ /pricing
├ ○ /profile
├ ○ /programs
├ ○ /protection
├ ○ /recover
├ ○ /redeem
├ ○ /rewards
├ ○ /settings
├ ○ /statistics
├ ○ /subscription
├ ○ /subscription/checkout
├ ○ /support
├ ○ /support/legal
├ ○ /support/thread
└ ○ /verify


○  (Static)  prerendered as static content

[fix-export-segment-paths] created 86 dot-joined segment payload copies
```

### WebApp Playwright E2E

- Command: `npm.cmd run test:e2e`
- Exit: `0`

```text
  ok 40 e2e\cabinet-flow.spec.ts:971:7 › Cabinet flow › keeps download instructions compact until requested (1.3s)
  ok 41 e2e\cabinet-flow.spec.ts:982:7 › Cabinet flow › links a trial entitlement to compact checkout (514ms)
  ok 42 e2e\cabinet-flow.spec.ts:1019:7 › Cabinet flow › shows branded root and cabinet not-found recovery screens (497ms)
  ok 43 e2e\cabinet-flow.spec.ts:1031:7 › Cabinet flow › shows subscription manual connection only as an explicit fallback (793ms)
  ok 44 e2e\cabinet-flow.spec.ts:1052:7 › Cabinet flow › builds the Happ URL without leaking it to third parties (579ms)
  ok 45 e2e\cabinet-flow.spec.ts:1080:7 › Cabinet flow › keeps manual setup closed from a direct hash when no active link exists (492ms)
  ok 46 e2e\cabinet-flow.spec.ts:1094:7 › Cabinet flow › keeps paid plan cards selectable for a free monthly account (684ms)
  ok 47 e2e\cabinet-flow.spec.ts:1158:7 › Cabinet flow › renders runtime connections on devices and keeps statistics as its own safe-summary page (962ms)
  ok 48 e2e\cabinet-flow.spec.ts:1179:7 › Cabinet flow › issues a one-time device code without exposing the subscription URL (718ms)
  ok 49 e2e\cabinet-flow.spec.ts:1188:7 › Cabinet flow › searches fallback guides and the POKROV screen atlas on mobile (1.4s)
  ok 50 e2e\cabinet-flow.spec.ts:1221:7 › Cabinet flow › submits a competitor-switch application without automatic reward (1.3s)
  ok 51 e2e\cabinet-flow.spec.ts:1243:7 › Cabinet flow › keeps redeem as a compact activation task (649ms)
  ok 52 e2e\cabinet-flow.spec.ts:1257:7 › Cabinet flow › keeps cabinet copy human and hides node internals (799ms)
  ok 53 e2e\cabinet-flow.spec.ts:1271:7 › Cabinet flow › settings exposes clear Telegram bonus actions without raw account details (2.1s)
  ok 54 e2e\cabinet-flow.spec.ts:1289:7 › Cabinet flow › shows honest payment history and a compact Russian checkout (976ms)
  ok 55 e2e\cabinet-flow.spec.ts:1331:7 › Cabinet flow › keeps downloads and support flows usable without the app (1.5s)
  ok 56 e2e\cabinet-flow.spec.ts:1365:7 › Cabinet flow › renders support thread attachments without exposing private access data (1.8s)
  ok 57 e2e\cabinet-flow.spec.ts:1422:7 › Cabinet flow › sends staged attachment id without the private media triplet (3.6s)
  ok 58 e2e\cabinet-flow.spec.ts:1504:7 › Cabinet flow › keeps legal documents as compact support rows (640ms)
  ok 59 e2e\cabinet-flow.spec.ts:1517:7 › Cabinet flow › stays inside a narrow mobile viewport for core cabinet pages (801ms)
  ok 60 e2e\rewards.spec.ts:268:7 › rewards fail-closed cabinet surface › shows anonymized referral conversion and history (665ms)
  ok 61 e2e\rewards.spec.ts:286:7 › rewards fail-closed cabinet surface › keeps calendar usable when wheel state fails (457ms)
  ok 62 e2e\rewards.spec.ts:294:7 › rewards fail-closed cabinet surface › keeps wheel usable when calendar state fails (457ms)
  ok 63 e2e\rewards.spec.ts:302:7 › rewards fail-closed cabinet surface › does not invent sectors or animate an unknown committed reward (712ms)
  ok 64 e2e\rewards.spec.ts:312:7 › rewards fail-closed cabinet surface › renders one sector as a guaranteed reward card (475ms)
  ok 65 e2e\rewards.spec.ts:327:9 › rewards fail-closed cabinet surface › fails closed for missing sectors (457ms)
  ok 66 e2e\rewards.spec.ts:327:9 › rewards fail-closed cabinet surface › fails closed for duplicate sectors (484ms)
  ok 67 e2e\rewards.spec.ts:327:9 › rewards fail-closed cabinet surface › fails closed for non-positive sectors (467ms)
  ok 68 e2e\rewards.spec.ts:327:9 › rewards fail-closed cabinet surface › fails closed for too many sectors (466ms)
  ok 69 e2e\rewards.spec.ts:327:9 › rewards fail-closed cabinet surface › fails closed for excessive reward (473ms)
  ok 70 e2e\rewards.spec.ts:337:9 › rewards fail-closed cabinet surface › keeps FREE rewards ineligible (468ms)
  ok 71 e2e\rewards.spec.ts:337:9 › rewards fail-closed cabinet surface › keeps TRIAL rewards ineligible (486ms)
  ok 72 e2e\rewards.spec.ts:337:9 › rewards fail-closed cabinet surface › keeps BONUS rewards ineligible (495ms)
  ok 73 e2e\rewards.spec.ts:347:7 › rewards fail-closed cabinet surface › keeps expired rewards ineligible (492ms)
  ok 74 e2e\rewards.spec.ts:355:7 › rewards fail-closed cabinet surface › renders disabled features without mutation controls (525ms)
  ok 75 e2e\rewards.spec.ts:365:7 › rewards fail-closed cabinet surface › accepts the server same-day calendar response (751ms)
  ok 76 e2e\rewards.spec.ts:374:7 › rewards fail-closed cabinet surface › refetches wheel state and entitlement after committed reward (825ms)
  ok 77 e2e\rewards.spec.ts:387:7 › rewards fail-closed cabinet surface › refetches calendar state and entitlement after check-in (722ms)

  77 passed (1.1m)
```

### UI visual smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/ui_visual_smoke.py`
- Exit: `0`

```text
UI visual smoke passed.
```
