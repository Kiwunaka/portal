# Release Gate Report

- Generated at: `2026-08-13 12:34:05`
- Status: `FAIL`
- Gate set: `quick`
- Brain IP supplied: `no`
- Client platform gates: `none`
- Android audit required by selected gates: `no`

## Summary

| Gate | Exit code | Duration (s) |
|---|---:|---:|
| Critical worker regression | 0 | 33.97 |
| Client security smoke | 0 | 0.51 |
| Client portal Flutter tests | 1 | 70.37 |
| API lifecycle smoke | 1 | 3.30 |
| Public link checks | 0 | 0.10 |
| Marketing production build | 0 | 27.43 |
| AdminApp production build | 0 | 26.41 |
| Admin webapp smoke | 0 | 0.18 |
| WebApp production build | 0 | 29.95 |
| WebApp Playwright E2E | 1 | 2.57 |
| UI visual smoke | 0 | 0.09 |

## Evidence Classification

| Evidence | Scope | Status | Notes |
|---|---|---|---|
| current-origin check | local quick gate set | FAIL | Runs on the operator workstation; does not prove brain-origin or RU-origin reachability. |
| brain-origin check | `scripts/verify_brain_ready.py` / predeploy readiness | BLOCKED_BY_ACCESS | Requires `--brain-ip` and live SSH/API access; keep separate from current-origin results. |
| RU-origin check | external RU probe (`mini` or replacement) | BLOCKED_BY_ACCESS | Not run by this local gate; requires an external RU probe host and redacted report. |
| Android physical audit | release-build localhost/control-surface audit | BLOCKED_BY_ACCESS | Public Android remains blocked unless this is run on physical hardware with the release build. |
| Runtime app-download smoke | `/api/client/apps` and provider checks | SKIPPED_NO_LIVE_TOKEN | Requires `TELEGRAM_INIT_DATA`; omit raw token values from evidence. |
| Client platform builds | none requested | NOT_REQUESTED | Repo/static gates alone do not create Android or Windows beta artifacts. |

## Command Tails

### Critical worker regression

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest tests/test_worker_retention.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-qmij0ri_`
- Exit: `0`

```text
....................                                                     [100%]
20 passed in 33.04s
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
- Exit: `1`

```text

Warning: A call to tap() with finder "Found 1 widget with key [<'locations-catalog-city-nl-ams-01'>]: [
  Padding-[<'locations-catalog-city-nl-ams-01'>](padding: EdgeInsets(0.0, 8.0, 0.0, 8.0), dependencies: [Directionality], renderObject: RenderPadding#5a21e relayoutBoundary=up25),
]" derived an Offset (Offset(640.0, 461.0)) that would not hit test on the specified widget.
Maybe the widget is actually off-screen, or another widget is obscuring it, or the widget cannot receive pointer events.
The finder corresponds to this RenderBox: RenderPadding#5a21e relayoutBoundary=up25
The hit test result at that offset is: HitTestResult(RenderPointerListener#a978e@Offset(428.0, 33.0), RenderSemanticsAnnotations#9dbcd@Offset(428.0, 33.0), RenderMouseRegion#66eeb@Offset(428.0, 33.0), RenderSemanticsAnnotations#2e2e5@Offset(428.0, 33.0), _RenderInkFeatures#05cd8@Offset(428.0, 33.0), RenderCustomPaint#de61e@Offset(428.0, 33.0), RenderClipPath#bfc3e@Offset(428.0, 33.0), RenderPadding#73a3b@Offset(429.0, 34.0), RenderDecoratedBox#42bad@Offset(429.0, 34.0), RenderPointerListener#018a6@Offset(429.0, 34.0), RenderSemanticsGestureHandler#4beeb@Offset(429.0, 34.0), RenderMouseRegion#57192@Offset(429.0, 34.0), RenderSemanticsAnnotations#917d7@Offset(429.0, 34.0), RenderFlex#d8db0@Offset(429.0, 34.0), RenderFlex#38d08@Offset(429.0, 67.0), RenderPadding#6ba03@Offset(449.0, 87.0), RenderPadding#3911b@Offset(450.0, 88.0), RenderDecoratedBox#6a33a@Offset(450.0, 88.0), RenderPadding#cb00e@Offset(450.0, 88.0), RenderRepaintBoundary#333ea@Offset(450.0, 88.0), RenderIndexedSemantics#7d564@Offset(450.0, 88.0), RenderSliverList@(mainAxis: 445.0, crossAxis: 450.0), RenderSliverPadding@(mainAxis: 461.0, crossAxis: 640.0), RenderViewport#e94e4@Offset(640.0, 461.0), RenderIgnorePointer#fab0f@Offset(640.0, 461.0), RenderSemanticsAnnotations#a0d38@Offset(640.0, 461.0), RenderPointerListener#83e3a@Offset(640.0, 461.0), RenderSemanticsGestureHandler#d0362@Offset(640.0, 461.0), RenderPointerListener#5f525@Offset(640.0, 461.0), _RenderScrollSemantics#9961d@Offset(640.0, 461.0), _RenderLayoutBuilder#b5059@Offset(640.0, 461.0), RenderRepaintBoundary#21f02@Offset(640.0, 461.0), RenderOffstage#ea5f9@Offset(640.0, 461.0), RenderStack#bfa01@Offset(640.0, 461.0), RenderOpacity#c2577@Offset(640.0, 461.0), RenderFlex#6646e@Offset(640.0, 461.0), RenderStack#fd08b@Offset(640.0, 461.0), RenderPadding#faa8e@Offset(640.0, 461.0), RenderStack#e3a64@Offset(640.0, 461.0), RenderDecoratedBox#8ce42@Offset(640.0, 461.0), _RenderLayoutBuilder#13494@Offset(640.0, 461.0), RenderCustomMultiChildLayoutBox#678e9@Offset(640.0, 461.0), _RenderInkFeatures#9f843@Offset(640.0, 461.0), RenderPhysicalModel#3756b@Offset(640.0, 461.0), RenderAnnotatedRegion<SystemUiOverlayStyle>#b8007@Offset(640.0, 461.0), RenderSemanticsAnnotations#deb4e@Offset(640.0, 461.0), RenderSemanticsAnnotations#51e43@Offset(640.0, 461.0), RenderSemanticsAnnotations#40a66@Offset(640.0, 461.0), RenderRepaintBoundary#ab355@Offset(640.0, 461.0), RenderIgnorePointer#33f20@Offset(640.0, 461.0), RenderStack#6d467@Offset(640.0, 461.0), RenderDecoratedBox#24c77@Offset(640.0, 461.0), RenderRepaintBoundary#c00f2@Offset(640.0, 461.0), RenderSemanticsAnnotations#aa437@Offset(640.0, 461.0), RenderOffstage#3f5b2@Offset(640.0, 461.0), RenderSemanticsAnnotations#24bd5@Offset(640.0, 461.0), _RenderTheater#0f989@Offset(640.0, 461.0), RenderAbsorbPointer#679f1@Offset(640.0, 461.0), RenderPointerListener#b4a3d@Offset(640.0, 461.0), RenderSemanticsAnnotations#87c7e@Offset(640.0, 461.0), RenderSemanticsAnnotations#7b29e@Offset(640.0, 461.0), RenderSemanticsAnnotations#fa82f@Offset(640.0, 461.0), RenderTapRegionSurface#f6f87@Offset(640.0, 461.0), RenderSemanticsAnnotations#aca81@Offset(640.0, 461.0), RenderSemanticsAnnotations#702c3@Offset(640.0, 461.0), RenderSemanticsAnnotations#9c726@Offset(640.0, 461.0), HitTestEntry<HitTestTarget>#bcc34(_ReusableRenderView#c9008), HitTestEntry<HitTestTarget>#25bd7(<AutomatedTestWidgetsFlutterBinding>))
#0      WidgetController._getElementPoint (package:flutter_test/src/controller.dart:2081:25)
#1      WidgetController.getCenter (package:flutter_test/src/controller.dart:1865:12)
#2      WidgetController.tap (package:flutter_test/src/controller.dart:1045:7)
#3      main.<anonymous closure> (file:///C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart:7936:18)
<asynchronous suspension>
#4      testWidgets.<anonymous closure>.<anonymous closure> (package:flutter_test/src/widget_tester.dart:192:15)
<asynchronous suspension>
#5      TestWidgetsFlutterBinding._runTestBody (package:flutter_test/src/binding.dart:1059:5)
<asynchronous suspension>
#6      StackZoneSpecification._registerCallback.<anonymous closure> (package:stack_trace/src/stack_zone_specification.dart:114:42)
<asynchronous suspension>
To silence this warning, pass "warnIfMissed: false" to "tap()".
To make this warning fatal, set WidgetController.hitTestWarningShouldBeFatal to true.

00:26 +238 -6: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: profile keeps cached notifications when refresh is offline
00:26 +239 -6: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: primary connect action auto-prepares and starts host runtime
00:26 +240 -6: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: first route scope blocks an empty selected-apps list
00:27 +241 -6: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: late client-experience restore cannot replace first-connect route choice
00:27 +242 -6: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: first route scope confirmation survives a shell restart
00:27 +243 -6: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: primary connect activates once from pointer and keyboard
00:27 +244 -6: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: bootstrap failures surface as a calm recovery banner
00:27 +245 -6: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: unexpected runtime errors surface as redacted recovery feedback
00:27 +246 -6: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: android reconnect refreshes the managed profile even when one is already staged
00:28 +247 -6: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: primary connect action is disabled when live connect is unavailable
00:28 +248 -6: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: first Android consent converges after delayed native running without lifecycle resume
00:28 +249 -6: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: primary connect action polls the host bridge until runtime is running
00:28 +250 -6: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: android shell refreshes runtime snapshot when the app resumes
00:28 +251 -6: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: tab changes animate through the shared tab transition wrapper
00:28 +252 -6: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: profile and rewards hub expose accent pull-to-refresh
00:28 +253 -6: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: builds seed app context for public and readiness-only host lanes
00:28 +254 -6: Some tests failed.
[client-gate] C:\Program Files\PowerShell\7\pwsh.EXE -NoProfile -ExecutionPolicy Bypass -File C:\Users\kiwun\Documents\ai\POKROV-app\scripts\bootstrap-workspace.ps1 (cwd=C:\Users\kiwun\Documents\ai\POKROV-app)
[client-gate] C:\Users\kiwun\AppData\Roaming\npm\flutter.CMD test (cwd=C:\Users\kiwun\Documents\ai\POKROV-app\packages\app_shell)
```

### API lifecycle smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/api_lifecycle_smoke.py`
- Exit: `1`

```text
  File "<frozen importlib._bootstrap_external>", line 995, in exec_module
  File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
  File "C:\Users\kiwun\Documents\ai\VPN\portal_bot\api.py", line 2001, in <module>
    app = FastAPI(title="POKROV API", version="2.0.0")
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\fastapi\applications.py", line 896, in __init__
    ] = webhooks or routing.APIRouter()
                    ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\site-packages\fastapi\routing.py", line 837, in __init__
    super().__init__(
TypeError: Router.__init__() got an unexpected keyword argument 'on_startup'

======================================================================
ERROR: test_api_only_lifecycle_covers_trial_connect_support_bonuses_and_purchase (test_api_lifecycle_smoke.ApiLifecycleSmokeTests.test_api_only_lifecycle_covers_trial_connect_support_bonuses_and_purchase)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\shutil.py", line 633, in _rmtree_unsafe
    os.unlink(fullname)
PermissionError: [WinError 32] \ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd \ufffd\ufffd \ufffd\ufffd\ufffd\ufffd\ufffd \ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd \ufffd\ufffd\ufffd\ufffd\ufffd\ufffd \ufffd \ufffd\ufffd\ufffd\ufffd\ufffd, \ufffd\ufffd\ufffd \ufffd\ufffd\ufffd \ufffd\ufffd\ufffd\ufffd \ufffd\ufffd\ufffd\ufffd \ufffd\ufffd\ufffd\ufffd\ufffd \ufffd\ufffd\ufffd\ufffd\ufffd\ufffd \ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd: 'E:\\CodexCaches\\temp\\tmpmh11dsqu\\portal_api_test_6a96b28e9e704563aa4c433f4770fdec.db'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\tempfile.py", line 950, in cleanup
    self._rmtree(self.name, ignore_errors=self._ignore_cleanup_errors)
  File "C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\tempfile.py", line 930, in _rmtree
    _shutil.rmtree(name, onexc=onexc)
  File "C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\shutil.py", line 781, in rmtree
    return _rmtree_unsafe(path, onexc)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\shutil.py", line 635, in _rmtree_unsafe
    onexc(os.unlink, fullname, err)
  File "C:\Users\kiwun\AppData\Local\Programs\Python\Python312\Lib\tempfile.py", line 905, in onexc
    _os.unlink(path)
PermissionError: [WinError 32] \ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd \ufffd\ufffd \ufffd\ufffd\ufffd\ufffd\ufffd \ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd \ufffd\ufffd\ufffd\ufffd\ufffd\ufffd \ufffd \ufffd\ufffd\ufffd\ufffd\ufffd, \ufffd\ufffd\ufffd \ufffd\ufffd\ufffd \ufffd\ufffd\ufffd\ufffd \ufffd\ufffd\ufffd\ufffd \ufffd\ufffd\ufffd\ufffd\ufffd \ufffd\ufffd\ufffd\ufffd\ufffd\ufffd \ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd\ufffd: 'E:\\CodexCaches\\temp\\tmpmh11dsqu\\portal_api_test_6a96b28e9e704563aa4c433f4770fdec.db'

----------------------------------------------------------------------
Ran 1 test in 2.403s

FAILED (errors=2)
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
✓ Generating static pages using 19 workers (32/32) in 480.0ms
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
✓ Compiled successfully in 5.4s
  Running TypeScript ...
  Finished TypeScript in 5.3s ...
  Collecting page data using 5 workers ...
  Generating static pages using 5 workers (0/17) ...
  Generating static pages using 5 workers (4/17)
  Generating static pages using 5 workers (8/17)
  Generating static pages using 5 workers (12/17)
✓ Generating static pages using 5 workers (17/17) in 652ms
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
- Exit: `1`

```text
> pokrov-webapp@0.1.0 test:e2e
> node ./scripts/run-e2e.mjs full


> pokrov-webapp@0.1.0 build
> next build && node ./scripts/fix-export-segment-paths.mjs

'next' is not recognized as an internal or external command,
operable program or batch file.
```

### UI visual smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/ui_visual_smoke.py`
- Exit: `0`

```text
UI visual smoke passed.
```
