# Release Gate Report

- Generated at: `2026-05-08 11:59:43`
- Status: `PASS`
- Gate set: `quick`
- Brain IP supplied: `yes`
- Client platform gates: `none`
- Android audit required by selected gates: `no`

## Summary

| Gate | Exit code | Duration (s) |
|---|---:|---:|
| Brain-origin runtime/static verify | 0 | 6.20 |
| Node predeploy readiness | 0 | 89.42 |
| Critical worker regression | 0 | 6.27 |
| Payment and marketing release honesty | 0 | 39.18 |
| Paid checkout launch evidence tooling | 0 | 1.33 |
| GitHub release tooling | 0 | 1.09 |
| External access preflight tooling | 0 | 1.19 |
| Client preflight | 0 | 0.09 |
| Client security smoke | 0 | 0.06 |
| Client portal Flutter tests | 0 | 28.15 |
| API lifecycle smoke | 0 | 8.58 |
| Public link checks | 0 | 0.09 |
| Marketing production build | 0 | 12.98 |
| Admin webapp smoke | 0 | 0.15 |
| WebApp production build | 0 | 10.90 |
| WebApp Playwright E2E | 0 | 107.34 |
| UI visual smoke | 0 | 0.09 |

## Evidence Classification

| Evidence | Scope | Status | Notes |
|---|---|---|---|
| current-origin check | local quick gate set | PASS | Runs on the operator workstation; does not prove brain-origin or RU-origin reachability. |
| brain-origin check | `scripts/verify_brain_ready.py` plus node predeploy readiness | PASS | Requires `--brain-ip` and live SSH/API access; includes control-plane/static probes and node readiness. |
| RU-origin check | external RU probe (`mini` or replacement) | SKIPPED_BY_OPERATOR | Not run by this local gate; requires an external RU probe host and redacted report unless explicitly skipped by operator. |
| Android physical audit | release-build localhost/control-surface audit | BLOCKED_BY_ACCESS | Public Android remains blocked unless this is run on physical hardware with the release build. |
| Runtime app-download smoke | `/api/client/apps` and provider checks | SKIPPED_NO_LIVE_TOKEN | Requires `TELEGRAM_INIT_DATA`; omit raw token values from evidence. |
| Client platform builds | none requested | NOT_REQUESTED | Repo/static gates alone do not create Android or Windows beta artifacts. |

## Command Tails

### Brain-origin runtime/static verify

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/verify_brain_ready.py --brain-ip 82.21.114.104 --web-domain pokrov.space --api-domain api.pokrov.space --connect-domain connect.pokrov.space --ssh-user root --ssh-port 29374 --passwords <redacted>`
- Exit: `0`

```text
[caddy] active
[portal-api] active
[portal-bot] active
[portal-helpbot] active
[portal-feedbackbot] active
[listen] LISTEN 0      4096         0.0.0.0:443        0.0.0.0:*    users:(("haproxy",pid=854,fd=6))
LISTEN 0      4096               *:8444             *:*    users:(("caddy",pid=830,fd=7))
[health443] {"status":"ok","ts":"2026-05-08T08:54:14.510998"}
[webapp443] <!DOCTYPE html><!--WBEflHwSfEWS7qze03PyW--><html lang="ru" class="scroll-smooth"><head><meta charSet="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><link rel="stylesheet
[mkt443] <!DOCTYPE html><html lang="ru"><head><meta charSet="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><link rel="preload" as="image" href="/pokrov-logo.svg"/><link rel="styl
[mktCabinet443] <!DOCTYPE html><html lang="ru"><head><meta charSet="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><link rel="preload" as="image" href="/pokrov-logo.svg"/><link rel="styl
[offer443] <!DOCTYPE html><html lang="ru"><head><meta charSet="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><link rel="preload" as="image" href="/pokrov-logo.svg"/><link rel="styl
[checkout443] <!DOCTYPE html><html lang="ru"><head><meta charSet="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><link rel="preload" as="image" href="/pokrov-logo.svg"/><link rel="styl
[legacyPaymentVerifyAbsent443] /fk-verify.html absent_or_fallback status=200
[legacyPaymentThemeAbsent443] /fk-payment-theme.css absent_or_fallback status=200
sub_fetch_1 user=<redacted> mode=token fmt=base64 lines=4 hosts=4 connect_json=1 outbounds=8
sub_fetch_2 user=<redacted> mode=token fmt=base64 lines=4 hosts=4 connect_json=1 outbounds=8
sub_fetch_3 user=<redacted> mode=token fmt=base64 lines=4 hosts=4 connect_json=1 outbounds=8
sub_fetch_4 user=<redacted> mode=token fmt=base64 lines=4 hosts=4 connect_json=1 outbounds=8
sub_fetch_5 user=<redacted> mode=token fmt=base64 lines=4 hosts=4 connect_json=1 outbounds=8
```

### Node predeploy readiness

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/predeploy_node_readiness.py --brain-ip 82.21.114.104 --web-domain pokrov.space --ssh-user root --ssh-port 29374 --passwords <redacted>`
- Exit: `0`

```text
      "dns_ok": true,
      "tcp_ok": true,
      "tls_ok": true,
      "target_tls_ok": true,
      "dns_records": [
        "82.24.195.93"
      ],
      "error_kind": "",
      "error_message": ""
    },
    {
      "code": "pl",
      "host": "pl.kiwunaka.space",
      "dns_ok": true,
      "tcp_ok": true,
      "tls_ok": true,
      "target_tls_ok": true,
      "dns_records": [
        "82.40.38.84"
      ],
      "error_kind": "",
      "error_message": ""
    },
    {
      "code": "us",
      "host": "us.kiwunaka.space",
      "dns_ok": true,
      "tcp_ok": true,
      "tls_ok": true,
      "target_tls_ok": true,
      "dns_records": [
        "82.21.92.181"
      ],
      "error_kind": "",
      "error_message": ""
    }
  ],
  "failures": [],
  "ok": true
}
```

### Critical worker regression

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest tests/test_worker_retention.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-x22od017`
- Exit: `0`

```text
.........                                                                [100%]
9 passed in 5.61s
```

### Payment and marketing release honesty

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest tests/test_bot_paywall.py tests/test_marketing_release_readiness.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-mr9q51od`
- Exit: `0`

```text
........................................................................ [ 90%]
........                                                                 [100%]
80 passed in 38.19s
```

### Paid checkout launch evidence tooling

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest tests/test_paid_checkout_launch_evidence_check.py tests/test_live_probe_scripts.py tests/test_public_beta_post_deploy_probe.py tests/test_freekassa_api_probe.py tests/test_freekassa_staging_smoke.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-k_ao97q9`
- Exit: `0`

```text
.................                                                        [100%]
17 passed in 0.76s
```

### GitHub release tooling

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest tests/test_prepare_github_release_plan.py tests/test_publish_github_release_assets.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-undctde3`
- Exit: `0`

```text
............                                                             [100%]
12 passed in 0.54s
```

### External access preflight tooling

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe -m pytest tests/test_public_beta_external_access_preflight.py tests/test_public_beta_launch_decision.py -q --basetemp C:\Users\kiwun\Documents\ai\VPN\.tmp\pytest-basetemp\release-gate-_0p9nm_6`
- Exit: `0`

```text
......................                                                   [100%]
22 passed in 0.65s
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
00:02 +21: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: shows a single logical location in locations
00:02 +22: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: primary connect action auto-prepares and starts host runtime
00:02 +23: C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/test/pokrov_seed_app_test.dart: android reconnect refreshes the managed profile even when one is already staged
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
Ran 1 test in 7.794s

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
> pokrov-marketing@0.1.0 build
> next build

  ▲ Next.js 14.2.35

   Creating an optimized production build ...
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
├ ○ /checkout                            8.67 kB         105 kB
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
  ├ chunks/117-c48652218eca60f1.js       31.9 kB
  ├ chunks/fd9d1056-1f1f859026f5f0fa.js  53.6 kB
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
✓ Generating static pages using 19 workers (31/31) in 378.7ms
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
  ok 10 e2e\admin-gate.spec.ts:1172:7 › Admin gate › lets admin search, sort, and paginate the users table (1.4s)
  ok 11 e2e\admin-gate.spec.ts:1202:7 › Admin gate › keeps the users filters synced into the URL and restores them on reload (1.2s)
  ok 12 e2e\admin-gate.spec.ts:1229:7 › Admin gate › lets admin safely delete only manual or test users (1.3s)
  ok 13 e2e\admin-gate.spec.ts:1267:7 › Admin gate › shows observer-lite badges, filters, and detail diagnostics (2.2s)
  ok 14 e2e\admin-gate.spec.ts:1308:7 › Admin gate › shows observer-lite empty state instead of misleading zero-only activity (1.8s)
  ok 15 e2e\admin-gate.spec.ts:1324:7 › Admin gate › keeps admin pages clickable and inside the viewport on mobile (3.5s)
  ok 16 e2e\admin-gate.spec.ts:1381:7 › Admin gate › shows node alert labels and probe failure details (1.1s)
  ok 17 e2e\admin-gate.spec.ts:1461:7 › Admin gate › shows node context with separate panel, dataplane, and transport detail (1.1s)
  ok 18 e2e\admin-gate.spec.ts:1538:7 › Admin gate › keeps rollout targeting fields and feed objects intact across save and reload (1.2s)
  ok 19 e2e\admin-gate.spec.ts:1578:7 › Admin gate › lets admin triage a ticket and send a reply using stable status codes (2.6s)
  ok 20 e2e\admin-gate.spec.ts:1612:7 › Admin gate › shows payment ledger and requires an audit note for manual reconciliation (2.0s)
  ok 21 e2e\admin-gate.spec.ts:1647:7 › Admin gate › shows access-key email fulfillment and resends with an audit note (3.0s)
  ok 22 e2e\cabinet-flow.spec.ts:480:7 › Cabinet flow › shows shared POKROV cabinet branding and a site return link (1.2s)
  ok 23 e2e\cabinet-flow.spec.ts:495:7 › Cabinet flow › shows an honest email-unavailable state on the root auth entry (852ms)
  ok 24 e2e\cabinet-flow.spec.ts:508:7 › Cabinet flow › keeps the email entry truthful when live delivery is not configured (817ms)
  ok 25 e2e\cabinet-flow.spec.ts:521:7 › Cabinet flow › keeps the email entry unavailable when the relay secret is missing (832ms)
  ok 26 e2e\cabinet-flow.spec.ts:547:7 › Cabinet flow › supports enabled email register verify login and recovery from the auth entry (10.7s)
  ok 27 e2e\cabinet-flow.spec.ts:602:7 › Cabinet flow › keeps email verification and recovery tokens separate (5.3s)
  ok 28 e2e\cabinet-flow.spec.ts:622:7 › Cabinet flow › reuses an existing web session and lands in the cabinet without showing auth entry again (1.0s)
  ok 29 e2e\cabinet-flow.spec.ts:631:7 › Cabinet flow › stores a silently refreshed web session returned from Telegram auth (999ms)
  ok 30 e2e\cabinet-flow.spec.ts:650:7 › Cabinet flow › shows a human reauth CTA when the browser session is expired (647ms)
  ok 31 e2e\cabinet-flow.spec.ts:668:7 › Cabinet flow › keeps the dashboard on consumer-safe access actions (1.1s)
  ok 32 e2e\cabinet-flow.spec.ts:684:7 › Cabinet flow › keeps cabinet navigation on native Next.js routing (1.1s)
  ok 33 e2e\cabinet-flow.spec.ts:705:7 › Cabinet flow › shows branded root and cabinet not-found recovery screens (1.6s)
  ok 34 e2e\cabinet-flow.spec.ts:717:7 › Cabinet flow › shows subscription manual connection only as an explicit fallback (2.9s)
  ok 35 e2e\cabinet-flow.spec.ts:734:7 › Cabinet flow › renders runtime connections on devices and keeps statistics as its own safe-summary page (1.4s)
  ok 36 e2e\cabinet-flow.spec.ts:752:7 › Cabinet flow › keeps cabinet copy human and hides node internals (1.8s)
  ok 37 e2e\cabinet-flow.spec.ts:766:7 › Cabinet flow › settings exposes clear Telegram bonus actions without raw account details (5.1s)
  ok 38 e2e\cabinet-flow.spec.ts:781:7 › Cabinet flow › shows honest payment history and Russian checkout continuation copy (1.2s)
  ok 39 e2e\cabinet-flow.spec.ts:799:7 › Cabinet flow › keeps checkout disabled when payment providers are configured but launch evidence is blocked (1.1s)
  ok 40 e2e\cabinet-flow.spec.ts:841:7 › Cabinet flow › keeps checkout start failures public and Russian (2.1s)
  ok 41 e2e\cabinet-flow.spec.ts:886:7 › Cabinet flow › checks and redeems access keys from the cabinet redeem route (3.5s)
  ok 42 e2e\cabinet-flow.spec.ts:951:7 › Cabinet flow › keeps downloads and support flows usable without the app (4.5s)
  ok 43 e2e\cabinet-flow.spec.ts:979:7 › Cabinet flow › loads protected support attachments through authenticated blob fetch (1.2s)
  ok 44 e2e\cabinet-flow.spec.ts:999:7 › Cabinet flow › stays inside a narrow mobile viewport for core cabinet pages (1.9s)
  ok 45 e2e\telegram-login-refresh.spec.ts:8:5 › flags stale Telegram widget payloads before the backend rejects them (1ms)
  ok 46 e2e\telegram-login-refresh.spec.ts:25:5 › keeps fresh Telegram widget payloads on the direct widget login path (0ms)
  ok 47 e2e\telegram-login-refresh.spec.ts:42:5 › treats expired or deprecated Telegram widget errors as refreshable auth (1ms)

  47 passed (1.5m)
```

### UI visual smoke

- Command: `C:\Users\kiwun\AppData\Local\Programs\Python\Python312\python.exe scripts/ui_visual_smoke.py`
- Exit: `0`

```text
UI visual smoke passed.
```
