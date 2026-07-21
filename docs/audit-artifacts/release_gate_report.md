# Release Gate Report

- Generated at: `2026-07-21 03:57:44`
- Status: `PASS`
- Gate set: `default`
- Brain IP supplied: `no`
- Client platform gates: `none`
- Android audit required by selected gates: `no`

## Summary

| Gate | Exit code | Duration (s) |
|---|---:|---:|
| Release pytest matrix | 0 | 1320.96 |
| Admin/auth regressions | 0 | 273.60 |
| Client security smoke | 0 | 0.20 |
| Client Flutter tests | 0 | 127.55 |
| API lifecycle smoke | 0 | 4.82 |
| Public link checks | 0 | 0.09 |
| Marketing production build | 0 | 18.44 |
| AdminApp production build | 0 | 21.30 |
| Admin webapp smoke | 0 | 0.17 |
| WebApp production build | 0 | 23.96 |
| WebApp Playwright E2E | 0 | 99.15 |
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

- Command: `C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe -m pytest tests/test_account_foundation.py tests/test_antiabuse_privacy.py tests/test_antiabuse_retention_script.py tests/test_sqlite_postgres_rehearsal.py tests/test_account_recovery.py tests/test_auth_sessions.py portal_bot/tests/test_app_first_service.py portal_bot/tests/test_app_first_api.py portal_bot/tests/test_email_auth.py portal_bot/tests/test_economy_bonus_referral_service.py portal_bot/tests/test_economy_trial_service.py portal_bot/tests/test_channel_bonus_service.py tests/test_free_soft_profile_contract.py tests/test_free_soft_profile_migrations.py tests/test_node_provisioning_service.py tests/test_panel_client_free_profiles.py tests/test_free_soft_inbound_shaper.py tests/test_free_cycle_service.py tests/test_key_pressure_scoring.py tests/test_admin_ops_api.py tests/test_plan_policies.py tests/test_bot_paywall.py tests/test_api_payments_callbacks.py tests/test_portal_api.py tests/test_worker_retention.py tests/test_observer_service.py tests/test_observer_api.py tests/test_collect_xray_observer.py tests/test_predeploy_node_readiness.py tests/test_admin_webapp_smoke.py tests/test_public_copy_guardrails.py tests/test_reviews_username_masking.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.worktrees\final-platform-integration\.tmp\pytest-basetemp\release-gate-uhztnmcg`
- Exit: `0`

```text
........................................................................ [ 12%]
........................................................................ [ 25%]
........................................................................ [ 38%]
........................................................................ [ 51%]
................................................................... [ 63%]
.............................................................. [ 74%]
............................................................ [ 85%]
............................................................. [ 96%]
....................                                                     [100%]
============================== warnings summary ===============================
tests/test_api_payments_callbacks.py::ApiPaymentCallbacksTests::test_admin_plan_key_then_real_payment_still_starts_first_referral_hold
  C:\Users\kiwun\Documents\ai\VPN\.worktrees\final-platform-integration\tests\test_api_payments_callbacks.py:1032: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    ref_expiry = datetime.utcnow() + timedelta(days=20)

tests/test_api_payments_callbacks.py::ApiPaymentCallbacksTests::test_admin_plan_key_then_real_payment_still_starts_first_referral_hold
  C:\Users\kiwun\Documents\ai\VPN\.worktrees\final-platform-integration\tests\test_api_payments_callbacks.py:1046: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    invited_expiry = datetime.utcnow() + timedelta(days=5)

tests/test_api_payments_callbacks.py::ApiPaymentCallbacksTests::test_admin_plan_key_then_real_payment_still_starts_first_referral_hold
  C:\Users\kiwun\Documents\ai\VPN\.worktrees\final-platform-integration\tests\test_api_payments_callbacks.py:1062: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    now=datetime.utcnow(),

tests/test_api_payments_callbacks.py::ApiPaymentCallbacksTests::test_admin_plan_key_then_real_payment_still_starts_first_referral_hold
  C:\Users\kiwun\Documents\ai\VPN\.worktrees\final-platform-integration\tests\test_api_payments_callbacks.py:1134: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    self.assertTrue(bool(referrer.expiry_at and referrer.expiry_at < datetime.utcnow() + timedelta(days=30)))

tests/test_api_payments_callbacks.py: 13 warnings
  C:\Users\kiwun\Documents\ai\VPN\.venv\Lib\site-packages\httpx\_models.py:408: DeprecationWarning: Use 'content=<...>' to upload raw bytes/text content.
    headers, stream = encode_request(

tests/test_api_payments_callbacks.py::ApiPaymentCallbacksTests::test_create_public_order_applies_referral_first_purchase_discount
  C:\Users\kiwun\Documents\ai\VPN\.worktrees\final-platform-integration\tests\test_api_payments_callbacks.py:1333: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    expiry_at=datetime.utcnow() + timedelta(days=30),

tests/test_api_payments_callbacks.py::ApiPaymentCallbacksTests::test_start99_public_order_ignores_referral_and_pending_discounts
  C:\Users\kiwun\Documents\ai\VPN\.worktrees\final-platform-integration\tests\test_api_payments_callbacks.py:1522: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    expiry_at=datetime.utcnow() + timedelta(days=30),

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
558 passed, 19 warnings, 38 subtests passed in 1314.54s (0:21:54)
```

### Admin/auth regressions

- Command: `C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe -m pytest tests/test_api_auth_and_tickets.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.worktrees\final-platform-integration\.tmp\pytest-basetemp\release-gate-54xsq5l4`
- Exit: `0`

```text
...................................................................... [ 79%]
..................                                                       [100%]
88 passed, 2 subtests passed in 271.94s (0:04:31)
```

### Client security smoke

- Command: `C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe scripts/client_security_smoke.py`
- Exit: `0`

```text
[check] product contract: C:\Users\kiwun\Documents\ai\POKROV-app\.worktrees\final-client-integration\config\product-contract.seed.json
[check] runtime profile: C:\Users\kiwun\Documents\ai\POKROV-app\.worktrees\final-client-integration\config\runtime-profile.seed.json
[check] runtime artifacts: C:\Users\kiwun\Documents\ai\POKROV-app\.worktrees\final-client-integration\config\runtime-artifacts.seed.json
[check] Android manifest: C:\Users\kiwun\Documents\ai\POKROV-app\.worktrees\final-client-integration\apps\android_shell\android\app\src\main\AndroidManifest.xml
[check] Android build.gradle: C:\Users\kiwun\Documents\ai\POKROV-app\.worktrees\final-client-integration\apps\android_shell\android\app\build.gradle
[check] Windows release seed: C:\Users\kiwun\Documents\ai\POKROV-app\.worktrees\final-client-integration\config\windows-release.seed.json
[pass] client security smoke checks passed
```

### Client Flutter tests

- Command: `C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe scripts/run_client_release_gate.py test --suite full`
- Exit: `0`

```text
UrlLauncherTest > openWebView_opensUrlInCustomTabs PASSED

UrlLauncherTest > canLaunch_returnsFalseForEmulatorFallbackComponent PASSED

UrlLauncherTest > openWebView_handlesEnableJavaScript PASSED

UrlLauncherTest > canLaunch_createsIntentWithPassedUrl PASSED

UrlLauncherTest > launch_returnsTrue PASSED

UrlLauncherTest > openWebView_handlesEnableDomStorage PASSED

UrlLauncherTest > openWebView_handlesEnableShowTitle PASSED

UrlLauncherTest > canLaunch_returnsFalse PASSED

UrlLauncherTest > launch_throwsForNoCurrentActivity PASSED

UrlLauncherTest > openWebView_returnsFalse PASSED

UrlLauncherTest > closeWebView_closes PASSED

UrlLauncherTest > canLaunch_returnsTrue PASSED

UrlLauncherTest > openWebView_handlesHeaders PASSED

UrlLauncherTest > openWebView_opensUrlInCustomTabsWithCORSAllowedHeader PASSED

UrlLauncherTest > launch_returnsFalse PASSED

UrlLauncherTest > openWebView_opensUrlInWebViewIfRequested PASSED

UrlLauncherTest > launch_createsIntentWithPassedUrl PASSED

WebViewActivityTest > extractHeaders_returnsEmptyMapWhenHeadersBundleNull PASSED

BUILD SUCCESSFUL in 1m 2s
137 actionable tasks: 6 executed, 131 up-to-date
Workspace Flutter and Android unit tests passed.
[client-gate] C:\Program Files\PowerShell\7\pwsh.EXE -NoProfile -ExecutionPolicy Bypass -File C:\Users\kiwun\Documents\ai\POKROV-app\.worktrees\final-client-integration\scripts\run-tests.ps1 (cwd=C:\Users\kiwun\Documents\ai\POKROV-app\.worktrees\final-client-integration)
```

### API lifecycle smoke

- Command: `C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe scripts/api_lifecycle_smoke.py`
- Exit: `0`

```text
.
----------------------------------------------------------------------
Ran 1 test in 3.960s

OK
```

### Public link checks

- Command: `C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe scripts/check-links.py`
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
[PASS] portal_bot\api.py: Numeric subscription fallback is explicit compatibility and defaults off

Link check passed.
```

### Marketing production build

- Command: `npm.cmd run build`
- Exit: `0`

```text

  Creating an optimized production build ...
✓ Compiled successfully in 2.3s
  Running TypeScript ...
  Collecting page data using 19 workers ...
  Generating static pages using 19 workers (0/25) ...
  Generating static pages using 19 workers (6/25)
  Generating static pages using 19 workers (12/25)
  Generating static pages using 19 workers (18/25)
✓ Generating static pages using 19 workers (25/25) in 629.8ms
  Finalizing page optimization ...

Route (app)
┌ ○ /
├ ○ /_not-found
├ ○ /android
├ ○ /billing/no-autosubscription
├ ○ /checkout
├ ○ /compare/free-vpn
├ ○ /devices
├ ○ /install
├ ○ /install/android
├ ○ /install/windows
├ ○ /manifest.webmanifest
├ ○ /mobile
├ ○ /offer
├ ○ /privacy
├ ○ /robots.txt
├ ○ /sitemap.xml
├ ○ /support/install
├ ○ /telegram
├ ○ /tiktok
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
✓ Compiled successfully in 2.9s
  Running TypeScript ...
  Finished TypeScript in 4.9s ...
  Collecting page data using 5 workers ...
  Generating static pages using 5 workers (0/17) ...
  Generating static pages using 5 workers (4/17)
  Generating static pages using 5 workers (8/17)
  Generating static pages using 5 workers (12/17)
✓ Generating static pages using 5 workers (17/17) in 711ms
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

- Command: `C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe scripts/admin_webapp_smoke.py`
- Exit: `0`

```text
Admin WebApp smoke passed.
```

### WebApp production build

- Command: `npm.cmd run build`
- Exit: `0`

```text

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

[fix-export-segment-paths] created 74 dot-joined segment payload copies
```

### WebApp Playwright E2E

- Command: `npm.cmd run test:e2e`
- Exit: `0`

```text
  ok 30 e2e\cabinet-flow.spec.ts:655:7 › Cabinet flow › reuses an existing web session and lands in the cabinet without showing auth entry again (792ms)
  ok 31 e2e\cabinet-flow.spec.ts:663:7 › Cabinet flow › shows a human reauth CTA when the browser session is expired (577ms)
  ok 32 e2e\cabinet-flow.spec.ts:681:7 › Cabinet flow › maps raw Telegram deprecated auth errors to a reauth CTA (617ms)
  ok 33 e2e\cabinet-flow.spec.ts:698:7 › Cabinet flow › keeps the dashboard on consumer-safe access actions (701ms)
  ok 34 e2e\cabinet-flow.spec.ts:716:7 › Cabinet flow › uses the side drawer as the only mobile cabinet navigation (1.5s)
  ok 35 e2e\cabinet-flow.spec.ts:754:7 › Cabinet flow › keeps cabinet navigation usable with left-click browser routing (1.1s)
  ok 36 e2e\cabinet-flow.spec.ts:768:7 › Cabinet flow › shows branded root and cabinet not-found recovery screens (686ms)
  ok 37 e2e\cabinet-flow.spec.ts:780:7 › Cabinet flow › shows subscription manual connection only as an explicit fallback (968ms)
  ok 38 e2e\cabinet-flow.spec.ts:801:7 › Cabinet flow › builds the Happ URL without leaking it to third parties (703ms)
  ok 39 e2e\cabinet-flow.spec.ts:829:7 › Cabinet flow › keeps manual setup closed from a direct hash when no active link exists (670ms)
  ok 40 e2e\cabinet-flow.spec.ts:843:7 › Cabinet flow › keeps paid plan cards selectable for a free monthly account (655ms)
  ok 41 e2e\cabinet-flow.spec.ts:906:7 › Cabinet flow › renders runtime connections on devices and keeps statistics as its own safe-summary page (1.1s)
  ok 42 e2e\cabinet-flow.spec.ts:927:7 › Cabinet flow › keeps redeem as a compact activation task (789ms)
  ok 43 e2e\cabinet-flow.spec.ts:941:7 › Cabinet flow › keeps cabinet copy human and hides node internals (902ms)
  ok 44 e2e\cabinet-flow.spec.ts:955:7 › Cabinet flow › settings exposes clear Telegram bonus actions without raw account details (2.1s)
  ok 45 e2e\cabinet-flow.spec.ts:973:7 › Cabinet flow › shows honest payment history and Russian checkout continuation copy (974ms)
  ok 46 e2e\cabinet-flow.spec.ts:1011:7 › Cabinet flow › keeps downloads and support flows usable without the app (1.7s)
  ok 47 e2e\cabinet-flow.spec.ts:1045:7 › Cabinet flow › renders support thread attachments without exposing private access data (2.0s)
  ok 48 e2e\cabinet-flow.spec.ts:1102:7 › Cabinet flow › sends staged attachment id without the private media triplet (4.4s)
  ok 49 e2e\cabinet-flow.spec.ts:1184:7 › Cabinet flow › keeps legal documents as compact support rows (834ms)
  ok 50 e2e\cabinet-flow.spec.ts:1197:7 › Cabinet flow › stays inside a narrow mobile viewport for core cabinet pages (907ms)
  ok 51 e2e\rewards.spec.ts:235:7 › rewards fail-closed cabinet surface › keeps calendar usable when wheel state fails (753ms)
  ok 52 e2e\rewards.spec.ts:243:7 › rewards fail-closed cabinet surface › keeps wheel usable when calendar state fails (623ms)
  ok 53 e2e\rewards.spec.ts:251:7 › rewards fail-closed cabinet surface › does not invent sectors or animate an unknown committed reward (870ms)
  ok 54 e2e\rewards.spec.ts:261:7 › rewards fail-closed cabinet surface › renders one sector as a guaranteed reward card (615ms)
  ok 55 e2e\rewards.spec.ts:276:9 › rewards fail-closed cabinet surface › fails closed for missing sectors (637ms)
  ok 56 e2e\rewards.spec.ts:276:9 › rewards fail-closed cabinet surface › fails closed for duplicate sectors (630ms)
  ok 57 e2e\rewards.spec.ts:276:9 › rewards fail-closed cabinet surface › fails closed for non-positive sectors (629ms)
  ok 58 e2e\rewards.spec.ts:276:9 › rewards fail-closed cabinet surface › fails closed for too many sectors (642ms)
  ok 59 e2e\rewards.spec.ts:276:9 › rewards fail-closed cabinet surface › fails closed for excessive reward (608ms)
  ok 60 e2e\rewards.spec.ts:286:9 › rewards fail-closed cabinet surface › keeps FREE rewards ineligible (625ms)
  ok 61 e2e\rewards.spec.ts:286:9 › rewards fail-closed cabinet surface › keeps TRIAL rewards ineligible (643ms)
  ok 62 e2e\rewards.spec.ts:286:9 › rewards fail-closed cabinet surface › keeps BONUS rewards ineligible (636ms)
  ok 63 e2e\rewards.spec.ts:296:7 › rewards fail-closed cabinet surface › keeps expired rewards ineligible (623ms)
  ok 64 e2e\rewards.spec.ts:304:7 › rewards fail-closed cabinet surface › renders disabled features without mutation controls (673ms)
  ok 65 e2e\rewards.spec.ts:314:7 › rewards fail-closed cabinet surface › accepts the server same-day calendar response (877ms)
  ok 66 e2e\rewards.spec.ts:323:7 › rewards fail-closed cabinet surface › refetches wheel state and entitlement after committed reward (882ms)
  ok 67 e2e\rewards.spec.ts:336:7 › rewards fail-closed cabinet surface › refetches calendar state and entitlement after check-in (844ms)

  67 passed (1.3m)
```

### UI visual smoke

- Command: `C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe scripts/ui_visual_smoke.py`
- Exit: `0`

```text
UI visual smoke passed.
```
