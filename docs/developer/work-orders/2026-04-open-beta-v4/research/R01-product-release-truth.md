# R01 Product Release Truth

Date: 2026-04-26

Scope: POKROV Open Beta v4 product truth, release claims, public availability states, and version decision.

## Executive Summary

POKROV can honestly launch only as an open beta, not `1.0.0`. The public product promise is an app-first, consumer-first connectivity product for Android and Windows, with a 5-day real trial, optional Telegram linking, a +10 day Telegram reward, one canonical account, one public connection link, and calm beta-labeled copy governed by shared facts and catalog copy.

The current evidence supports platform/web/cabinet readiness and Windows beta artifact readiness with caveats. It does not support a full public paid checkout claim or public Android availability. The safest version decision is: launch wave as `Open Beta v4`, keep public client version in the `0.x.x-beta` line, and do not call this `1.0.0`. If new binaries are stamped for this wave, use `0.4.0-beta.4`; if the current built artifacts are distributed unchanged, label them as the existing `0.2.0-beta.1` evidence build and make "Open Beta v4" the release wave name, not the binary version.

## Evidence Table

| Evidence | Label | What it proves | What it does not prove |
| --- | --- | --- | --- |
| `AGENTS.md`, `docs/product/portal-vpn-product.md`, `shared/product-facts.json` | confirmed | Brand is `POKROV`; public wording must avoid direct-meaning `VPN`; public scope is Android + Windows; trial is 5 days; Telegram reward is +10 days; default core is `sing-box`; xray is advanced fallback only. | That all client binaries and live public surfaces currently match those facts. |
| `docs/architecture/system-overview.md`, `docs/architecture/app-first-and-bonus-flows.md` | confirmed | App-first session, managed profile, key-first checkout/redeem, Telegram linking/bonus, ticket support, and smart-connect contracts are the intended source of truth. | That every live path has been smoke-tested from production with real auth and payment credentials. |
| `copy/catalog.ru.json`, `shared/copy.ts` | confirmed | Shared copy already says paid beta, Android/Windows, cabinet-gated downloads, email soon, and blocks direct-meaning `VPN` in public-safe catalog items. | That rendered deployed pages cannot drift through hard-coded text outside the catalog. |
| `shared/public-urls.json`, `shared/portal-config.ts` | confirmed | Canonical surfaces are `pokrov.space`, `app.pokrov.space`, `api.pokrov.space`, `connect.pokrov.space`, and `pay.pokrov.space/checkout/`. | That runtime env on every deployed surface currently uses these exact values. |
| `docs/audit-artifacts/public_beta_release_gate_report.md` | confirmed | Local default repo/static/web/client tests passed on 2026-04-25. | Brain-origin, RU-origin, Android physical audit, runtime app download smoke, or platform builds. |
| `docs/audit-artifacts/public_beta_release_gate_report_brain.md` | confirmed | Quick gate with `--brain-ip` passed on 2026-04-26; brain-origin predeploy readiness passed. | Full default gate with platform builds or Android physical audit. |
| `docs/audit-artifacts/client_platform_builds_2026-04-26.md` | confirmed | Windows beta zip/manifest and Android APK/AAB were built; result is `PASS_WITH_RELEASE_GATES_REMAINING`. | Public signing, public hosting, Android safety, or production handoff approval. |
| `docs/audit-artifacts/android_physical_audit_2026-04-26.md` | blocked by missing access | Android physical audit was attempted but blocked because no physical device / `ANDROID_AUDIT_SERIAL` was available. | Public Android safety. |
| `docs/audit-artifacts/payment_provider_probe_2026-04-26.md` | blocked by missing access | Brain can reach FreeKassa provider API, but provider returned `Merchant not activated`. | Live public paid checkout or successful activation-key purchase. |
| `docs/audit-artifacts/runtime_app_download_smoke_2026-04-26.md` | blocked by missing access | `https://api.pokrov.space/api/health` returned 200. | `/api/client/apps`, provider list, and release-handoff download URLs because live `TELEGRAM_INIT_DATA` was missing. |
| `docs/audit-artifacts/ru_probe_2026-04-26.md` | probable | RU-origin host `mini` reached Google, canonical POKROV surfaces, and node TCP/443 endpoints. | Telegram reachability from `mini`; reserve xhttp/hysteria readiness; repeated RU stability. |
| `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md` | confirmed | Client repo is canonical, but public cutover remains blocked; Android public release is blocked; Windows is unsigned beta only. | That a public cutover is approved. |
| Fresh final gate rerun after Open Beta v4 implementation | needs local run | Nothing in this R01 research file changes runtime behavior. | Final release-captain approval still needs the selected gate pack rerun after all R/W work lands. |
| Live production payment success | unknown | No evidence of successful live paid order in this research set. | Any claim that payment works publicly end to end. |
| Production Android install on physical device | unknown | No physical-device localhost/control-surface pass exists here. | Android public readiness. |
| Email browser continuation | deferred | Docs and copy consistently mark email as `soon`. | Email as a live default sign-in, recovery, or checkout path. |

Allowed evidence labels used: confirmed, probable, unknown, needs local run, blocked by missing access, deferred.

## Public Promise Today

POKROV publicly promises:

- Brand/product: `POKROV`, not direct-meaning `VPN` copy except legacy identifiers and `@pokrov_vpn`.
- Platforms: Android + Windows as the public product scope; iOS/macOS are readiness-only.
- Status: beta, with public client version line `0.x.x-beta`.
- Onboarding: open app, tap `Try free`, receive a real working subscription, tap connect.
- Trial: 5 days of premium-grade access for a valid first device account.
- After trial: `free_monthly` with 5 GB / 30 days, 1 device, dedicated `NL-free` node, then soft mode after quota exhaustion.
- Paid: unlimited traffic, up to 5 devices, all enabled non-free nodes.
- Telegram: optional for first launch; used for linking, +10 day reward, recovery, community, support fallback, and bot-side fallback commerce.
- Checkout model: buy activation key, redeem key, refresh managed premium. Raw subscription links are recovery/manual-only.
- Routing: public modes are `All except RU` and `Full tunnel`; `Blocked only` stays hidden/internal until DNS/geo/leak checks are complete.
- Support: app, cabinet, `@pokrov_supportbot`, and `support@pokrov.space`; cabinet support is ticket-based, not a live chat promise.

## Open Beta Versus 1.0.0

Open Beta may be true when:

- Public copy says beta and uses `0.x.x-beta` versioning.
- Android is either hidden, invite/internal only, or clearly blocked if the physical audit is missing.
- Windows download is gated to approved beta users and warns if unsigned/unknown publisher.
- Checkout surfaces can show plans and route users to cabinet/support, but cannot promise live payment while the provider says merchant not activated.
- Marketing, cabinet, support, Telegram fallback, trial, redeem, and download routes are honest about which paths are live.
- Release handoff separates current-origin, brain-origin, and RU-origin evidence.

`1.0.0` requires all Open Beta conditions plus:

- Public Android release-build localhost/control-surface audit passes on physical hardware.
- Android production signing and public artifact handoff are complete.
- Windows trusted signing and public installer/MSIX/hosting handoff are complete.
- Runtime app-download smoke passes with live auth and no secret leakage in evidence.
- Paid checkout succeeds end to end through an activated provider, signed callbacks, activation-key issuance, redeem, and dashboard refresh.
- Current-origin, brain-origin, and RU-origin checks are green or explicitly accepted with documented degraded states.
- RU routing/DNS claims are backed by release-mode smoke and leak checks.
- Public copy and deployed pages pass direct-meaning `VPN` guardrails and do not promise Apple, email, raw subscription sharing, or public Android before gates close.

## P0 Issues

1. Public Android is still blocked.
   Evidence: `android_physical_audit_2026-04-26.md` is `BLOCKED_NO_PHYSICAL_DEVICE`; docs require release-installed physical-device audit before public Android.
   Impact: Android must not be promoted as publicly available or safe.

2. Paid checkout is blocked by provider status.
   Evidence: FreeKassa returned `Merchant not activated` from brain-origin provider probe.
   Impact: Do not claim "pay now", "instant purchase", or live paid activation until provider activation or another approved active provider is green.

3. Runtime app-download smoke is blocked without live token.
   Evidence: `/api/health` passed, but `/api/client/apps` was not run because `TELEGRAM_INIT_DATA` was missing.
   Impact: Do not claim app/bot/cabinet download URLs are live-synced until the smoke passes with redacted evidence.

4. Current client artifacts are beta evidence, not public release handoff.
   Evidence: Windows/Android builds exist, but report says release gates remain; Windows unsigned, Android unaudited.
   Impact: Public distribution must stay gated and beta-labeled.

## P1 Issues

1. RU-origin probe is mixed.
   Evidence: canonical POKROV surfaces and nodes are reachable from `mini`, but Telegram is unreachable and reserve checks fail.
   Impact: Do not claim Telegram reliability from RU-origin or reserve readiness.

2. Documentation conflict risk: platform docs still say public scope Android + Windows, while active evidence says Android blocked and Windows gated beta.
   Impact: Release copy must express scope separately from availability.

3. Email continuation exists as endpoints/copy but is not public default.
   Impact: Keep email marked `soon`; hide or disable verify/recovery as public promise until sender and webhook evidence is green.

4. Pricing plans are public-safe only as beta/catalog previews while payment is blocked.
   Impact: Pricing can exist, but the CTA must become waitlist/cabinet/support/redeem, not a false paid checkout.

## P2 Issues

1. Existing user guide and some generated report text show mojibake in this checkout; use shared catalog keys and browser screenshots for final copy review.
2. Apple install copy says "soon"; this is acceptable only if visually secondary and not presented as launch availability.
3. `VPN` appears in legacy filenames and Telegram handle; guardrails must continue allowing only those legacy contexts.
4. Windows unsigned warnings are a product-support burden; prepare support macros before widening beta.

## Proposed Implementation Work

1. Add a release-state switch for public surfaces:
   - `checkout_state`: `disabled`, `manual_support`, `live`
   - `android_state`: `blocked`, `internal_beta`, `public_beta`, `public_release`
   - `windows_state`: `blocked`, `gated_unsigned_beta`, `public_beta_signed`, `public_release`

2. Gate CTAs from those states:
   - If checkout is not `live`, replace pay CTAs with cabinet, support, Telegram fallback, or redeem-only paths.
   - If Android is `blocked`, hide direct APK/Play buttons from public pages and show cabinet/support/install-help language only.
   - If Windows is `gated_unsigned_beta`, show only cabinet-gated download with unknown-publisher warning.

3. Update shared copy keys for blocked states:
   - Payment blocked: "Plans are visible; payment is opened manually after confirmation/support."
   - Android blocked: "Android APK is internal beta only until physical audit and signing finish."
   - Windows unsigned: "Windows beta may show unknown publisher warning."

4. Add automated copy checks:
   - No direct-meaning `VPN` on public-safe catalog or rendered pages.
   - No `1.0.0`, "stable", "public Android", "live payment", "App Store", "TestFlight live", or "email login ready" claims unless matching release-state flags are green.

5. Close P0 gates before widening:
   - Activate provider or configure approved live provider.
   - Run Android physical audit.
   - Run runtime app-download smoke with env-only live token.
   - Produce release handoff metadata for distributed artifacts.

## Exact Verification Commands

Local platform and web gates:

```powershell
python scripts/release_gate_check.py
python scripts/release_gate_check.py --quick --brain-ip 82.21.114.104
python scripts/client_security_smoke.py
python scripts/api_lifecycle_smoke.py
python scripts/check-links.py
python scripts/admin_webapp_smoke.py
python scripts/ui_visual_smoke.py
```

Frontend gates:

```powershell
Push-Location marketing
npm.cmd run build
Pop-Location

Push-Location webapp
npm.cmd run build
npm.cmd run test:e2e
Pop-Location
```

Client gates:

```powershell
python scripts/run_client_release_gate.py preflight
python scripts/run_client_release_gate.py test --suite full
python scripts/run_client_release_gate.py build --target windows
python scripts/run_client_release_gate.py build --target android-apk
python scripts/run_client_release_gate.py build --target android-aab
```

Android public-release gate:

```powershell
$env:ANDROID_AUDIT_SERIAL="<physical-device-serial>"
python scripts/android_localhost_audit.py --serial $env:ANDROID_AUDIT_SERIAL
python scripts/release_gate_check.py --client-platform-gates android-apk --output docs/audit-artifacts/public_beta_release_gate_android_required.md
```

Runtime app-download smoke:

```powershell
$env:TELEGRAM_INIT_DATA="<redacted-live-init-data>"
python scripts/smoke_client_apps.py --base-url https://api.pokrov.space --check-providers --require-release-handoff --init-data $env:TELEGRAM_INIT_DATA
```

Payment provider live smoke:

```powershell
python scripts/freekassa_api_probe.py --base-url https://api.pokrov.space --source site --method orders/create
python scripts/freekassa_api_probe.py --base-url https://api.pokrov.space --source bot --method orders/create
```

RU-origin probe:

```powershell
python scripts/ru_probe_runner.py --probe-host mini --out ops-local/ru-probe.json
python scripts/render_ru_probe_report.py --input ops-local/ru-probe.json
```

Release handoff URL check:

```powershell
python external/client-fork/scripts/check_release_urls.py --env-file "C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/<version>/release-links.env"
python scripts/remote_brain_apply_release_handoff.py --brain-ip 82.21.114.104 --env-file "C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/<version>/release-links.env"
```

## Final Version Recommendation

Recommendation: do not ship `1.0.0`.

Use:

- Release wave name: `POKROV Open Beta v4`
- Public product status: `beta`
- Public client version line: `0.x.x-beta`
- New wave binary version, only if rebuilt/stamped for this wave: `0.4.0-beta.4`
- Existing built artifact version, if distributed unchanged from current evidence: `0.2.0-beta.1`

Do not mix these. If the artifact filename/manifest says `0.2.0-beta.1`, release notes can say "Open Beta v4 wave, build 0.2.0-beta.1." If binaries are rebuilt as v4, stamp all app metadata, filenames, manifests, and handoff JSON as `0.4.0-beta.4`.

## Release Copy Constraints

- Say `POKROV`, not direct-meaning `VPN`.
- Say "beta", "test access", "cabinet-gated beta", or "internal Android beta" where appropriate.
- Say Android + Windows are the release-wave scope, but only Windows is allowed as gated beta if Android physical audit is missing.
- Do not say Android is public, safe, ready, or available to everyone until physical audit and signing pass.
- Do not say payment is live, instant, automatic, or public until provider activation and callback/redeem smoke pass.
- Keep email as `soon`.
- Keep Apple as readiness-only / soon, not launch scope.
- Keep `connect.pokrov.space` as connection delivery, not a marketing CTA target.
- Keep raw subscription links hidden from first-layer UI.
- Do not claim RU routing is fully solved; say `All except RU` is the recommended beta mode, pending DNS/leak release evidence.
- Do not promise live chat; say support ticket or support bot.

## P0 Claim Audit

| Claim | Decision | Reason |
| --- | --- | --- |
| "POKROV is available for Android and Windows." | risky | Scope is Android + Windows, but Android public release is blocked and Windows is unsigned gated beta. |
| "POKROV Open Beta v4 is live." | allowed with caveats | Allowed only if public copy says beta and hides blocked payment/Android paths. |
| "Try 5 days free." | allowed | Confirmed by product docs and shared facts; must be a real trial, not decorative UI. |
| "Pay now and get instant access." | false now | Provider probe is blocked by `Merchant not activated`. |
| "Buy activation key and redeem in app/cabinet." | allowed as model, not live claim | Architecture confirms model; live paid purchase remains blocked. |
| "Android APK is public." | false now | Physical audit is blocked. |
| "Android APK is internal beta for approved users." | allowed | Shared catalog and audit evidence support this. |
| "Windows beta is available." | allowed with gate | Only cabinet/support-gated and with unsigned/unknown publisher warning unless signing closes. |
| "Email login/recovery is ready." | false now | Docs require `soon` until sender/delivery path is green. |
| "Telegram bonus gives +10 days." | allowed | Confirmed live flow; still depends on linking and channel membership. |
| "Works from Russia / RU-ready." | risky | RU probe reached POKROV surfaces/nodes, but Telegram failed; repeated RU evidence and leak checks still needed. |
| "Apple coming soon." | allowed if secondary | Apple is readiness-only; no store/TestFlight claim. |
| "1.0.0 release." | false now | P0 gates remain open. |

## Allowed Launch If Checkout Disabled

Allowed launch shape:

- Public status: `Open Beta v4`, not stable.
- Homepage CTA: start from app/cabinet/install help, not direct pay.
- Checkout page: plan preview, beta access explanation, manual support/cabinet continuation, redeem if user already has a key.
- Cabinet: allow trial, redeem existing key, support, downloads where account is approved.
- Bot: support, bonus, recovery, manual payment continuation only.
- Copy: "Payment is being opened manually / through support while the provider is activated" or equivalent calm wording.

Required hidden/disabled flows:

- Public "pay now" buttons.
- Automatic paid access extension from provider callback unless a real signed `paid` callback is verified.
- Any countdown/urgency/discount flow that implies immediate payment completion.
- Public claim that activation keys can currently be purchased automatically.

## Allowed Launch If Android Blocked

Allowed launch shape:

- Public status: `Open Beta v4`.
- Platform availability:
  - Windows: gated beta if artifact and warning are available.
  - Android: internal beta only / approval required / temporarily not public.
  - iOS/macOS: soon/readiness only.
- Marketing downloads: route Android users to cabinet/support/install help, not direct APK.
- Cabinet downloads: show Android only for approved beta accounts; otherwise show blocked-state copy and support.
- Release notes: explicitly say Android public availability waits for physical-device safety audit and signing.

Required hidden/disabled flows:

- Public APK/Play buttons.
- "Android available to everyone" cards.
- Store badges or Play claims without live store URL.
- Any safety claim based on emulator-only or static-only checks.
- Any claim that split tunneling, Private Space, Knox, Shelter, or similar tooling mitigates unauthenticated localhost/control-surface exposure.

## Public Platform Availability States

Allowed public states:

- `available_public_beta`: passed release gates, beta-labeled, public artifact/link live.
- `gated_beta`: artifact exists, but account/support approval or warning is required.
- `internal_beta_only`: artifact exists, but public distribution is blocked.
- `coming_soon`: planned/readiness-only, no artifact promise.
- `temporarily_unavailable`: known blocker, no CTA except support/cabinet.
- `legacy_compatibility`: old profiles or hosts work only for migration.

Current recommended state:

- Android: `internal_beta_only`
- Windows: `gated_beta`
- iOS/macOS: `coming_soon`
- Checkout/payment: `temporarily_unavailable` for automatic public purchase; `manual_support` for approved beta continuation
- Trial: `available_public_beta` only if the app/cabinet path used in launch has a real start-trial route and working profile
- Telegram bonus/support: `available_public_beta` with normal dependency caveats
