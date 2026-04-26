# R10 Docs, Launch, Growth, And Support Readiness

Status: research complete  
Date: 2026-04-26  
Agent: R10  
Scope: public/user docs, launch copy, SEO/schema, ASO/store metadata, support readiness

## Executive Summary

POKROV has a strong documentation foundation for an honest beta: the platform docs, client docs, install page, user guide, and cabinet support/download surfaces consistently describe an app-first Android + Windows beta with Telegram as a secondary reward/recovery/support path. The current copy also avoids the biggest unsafe claims: Android public safety, Apple release, production signing, and raw subscription-link-first onboarding.

Open Beta v4 is not ready for broad public launch copy that implies open downloads or public store availability. The current release decision placeholder says not to release publicly, the client cutover docs mark public cutover as blocked, Android and Windows public approval are blocked, and the stable release handoff keeps public Android/Windows URLs blank. The right launch posture today is either "do not announce" or "limited/gated beta with explicit waitlist/support handoff," not a mass public beta announcement.

SEO fundamentals are present: canonical metadata, Open Graph/Twitter metadata, robots, sitemap, manifest, Organization/WebSite/SoftwareApplication/Breadcrumb/FAQ JSON-LD, and canonical SEO landing routes. The biggest SEO/growth gap is that the primary public checkout route is not in the marketing sitemap, and structured data is still generic rather than store-ready. ASO is mostly a backlog: there is no complete Google Play/Microsoft Store metadata pack, screenshot set, feature graphic, localized store copy, or store release-note set in the inspected client release metadata.

Support readiness is better than launch readiness. Web cabinet support is ticket-backed, has attachments, and admin tickets exist; public docs correctly set expectations as best-effort/asynchronous. What is missing is an operator-ready support macro pack and launch known-issues page that everyone can reuse without improvising.

## Evidence Table

| ID | Label | Evidence | Readiness meaning |
| --- | --- | --- | --- |
| E01 | confirmed | `docs/developer/work-orders/2026-04-open-beta-v4/00-orchestrator-context.md` says `1.0.0` is blocked until P0 gates have direct evidence and lists missing payment, Telegram runtime, RU-origin, Android physical audit, and signing dependencies. | Broad public release and stable-release copy are blocked. |
| E02 | confirmed | `docs/developer/work-orders/2026-04-open-beta-v4/13-launch-decision.md` currently says `Decision: Do not release publicly.` | Launch decision is not ready for announcement. |
| E03 | confirmed | `POKROV-app/docs/operations/cutover-readiness.md` marks cutover state as paid beta evidence, public cutover blocked, public store readiness not approved, Android blocked on signing plus physical audit, and Windows blocked on trusted signing and handoff. | Public beta copy must stay gated and limitation-forward. |
| E04 | confirmed | `POKROV-app/artifacts/releases/release-handoff.json` keeps `APP_ANDROID_*` and `APP_WINDOWS_*` URLs blank, with only `APP_DOCS_URL=https://pokrov.space/install/`. | Runtime public downloads are not approved. |
| E05 | confirmed | `POKROV-app/artifacts/releases/pokrov-app/0.2.0-beta.1+20260425/release-handoff.json` is metadata-only, has no artifact URLs, and sets `public_cutover_allowed=false`. | `0.2.0-beta.1` is evidence, not public distribution. |
| E06 | confirmed | `marketing/src/app/install/page.tsx` is noindex, routes users to cabinet/support, and says public direct downloads are not issued when artifacts are unavailable. | Install clarity is good, but it is not an indexable acquisition route. |
| E07 | confirmed | `webapp/src/components/cabinet/downloads-surface.tsx` reads `/api/client/apps` plus env fallback, displays only real links, and warns about Android audit/signing and unsigned Windows SmartScreen. | Cabinet download UX is honest enough for gated beta. |
| E08 | confirmed | `marketing/src/lib/marketing-site.ts` defines robots/sitemap/schema helpers, but `MARKETING_SITEMAP_ROUTES` omits `/checkout/` and `/install/`. | Primary checkout SEO discovery is incomplete. |
| E09 | confirmed | `marketing/src/components/marketing-landing.tsx` emits SoftwareApplication JSON-LD and FAQ JSON-LD for home, plus canonical/Open Graph/Twitter metadata. | Core SEO/schema foundation exists. |
| E10 | confirmed | `docs/user/portal-vpn-user-guide-ru.md` documents official hosts, 5-day trial, +10-day Telegram reward, app-first start, support routes, route modes, and safe diagnostics. | User-guide substance is ready, pending final link/download state. |
| E11 | confirmed | `webapp/src/app/(dashboard)/support/page.tsx` creates tickets, lists ticket history, supports attachments, and links Telegram fallback. | Support flow is real, not decorative. |
| E12 | unknown | No complete store listing metadata pack or screenshot/feature-graphic inventory was found under inspected `POKROV-app/docs`, `POKROV-app/config`, or `POKROV-app/artifacts`. | ASO/store launch materials remain backlog. |

## P0 Issues

1. Public launch decision and release evidence are not green.
   - Evidence: E01, E02, E03, E05.
   - Impact: any broad "Open Beta is live" announcement would overclaim. The current safe position is no public release or a tightly gated beta.
   - Required work: replace `13-launch-decision.md` only after P0 gate evidence is attached; keep decision downgraded if any gate remains blocked by missing access.

2. Public download handoff is not approved.
   - Evidence: E04, E05, E07.
   - Impact: public install/download copy cannot promise immediately available Android or Windows files.
   - Required work: publish approved artifacts, write client-owned release handoff, sync runtime `APP_*`, rebuild static marketing if public URLs change, and verify app/bot/webapp downloads from runtime.

3. Android cannot be presented as public-safe.
   - Evidence: E01, E03, E10.
   - Impact: Android copy must remain internal beta/gated until signing and physical release-build localhost/control-surface audit pass.
   - Required work: run physical-device audit against release-installed build, store redacted evidence, and update launch copy only after pass.

4. Store/ASO readiness is not release-ready.
   - Evidence: E03, E12.
   - Impact: Google Play/Microsoft Store launch and store-traffic growth are not ready.
   - Required work: create a store metadata pack with title, short/full descriptions, screenshots, feature graphic, content/data-safety notes, release notes, and approval status.

## P1 Issues

1. The primary public checkout route is missing from the sitemap.
   - Evidence: E08.
   - Impact: the checkout-first acquisition surface is not represented in the canonical marketing sitemap.
   - Proposed fix: add `/checkout/` to `MARKETING_SITEMAP_ROUTES` with appropriate priority. Decide separately whether `/install/` remains `noIndex` as a support/gated-help page.

2. Schema is present but not launch-complete.
   - Evidence: E09.
   - Impact: SoftwareApplication schema currently points `screenshot` to the generic share image and lacks store URLs, real screenshots, aggregate rating, and platform-specific offer/download details.
   - Proposed fix: keep generic schema until public URLs exist, then update JSON-LD to use real app screenshots and approved download/store URLs.

3. Release notes and public launch copy are not stored as canonical launch artifacts.
   - Evidence: E02 plus no current R10/launch copy artifact before this report.
   - Impact: operators could improvise inconsistent launch/support language.
   - Proposed fix: W10 should convert the drafts below into canonical launch notes only after final gate decision.

4. Support macros are not centralized for operators.
   - Evidence: E11 shows support system exists; no inspected canonical macro pack exists.
   - Impact: support answers may drift under launch pressure.
   - Proposed fix: add a support macro page/runbook or admin canned responses using the template set below.

5. `/install/` is useful but noindex.
   - Evidence: E06.
   - Impact: acceptable if it is only a gated/help fallback, weak if growth expects it to rank for installation queries.
   - Proposed fix: decide launch intent. If `/install/` is public SEO, remove `noIndex` after direct artifact/handoff proof; if gated, keep noindex and link it from high-trust pages.

## P2 Issues

1. Store screenshot/caption strategy is absent.
   - Evidence: E12.
   - Impact: ASO conversion will be weak even after technical release approval.

2. FAQ is homepage-focused and should be mirrored in support macros.
   - Evidence: E09, E11.
   - Impact: users get answers on the site, but operators need the same wording in replies.

3. Growth measurement checklist is implicit.
   - Evidence: docs mention funnel events, but launch-specific analytics acceptance was not found in the inspected launch artifacts.
   - Impact: launch learnings may be anecdotal.

4. Press/partner copy is not ready.
   - Evidence: publishing guide recommends `press@pokrov.space`, but no press kit/partner note was found in inspected materials.
   - Impact: borrowed-channel launch is premature.

## Proposed Implementation Work

1. Final launch decision hardening:
   - Update `13-launch-decision.md` to one explicit outcome only after P0 evidence is attached.
   - Keep "do not release publicly" if runtime downloads, Android audit, signing, or RU-origin checks remain blocked.

2. Runtime download and docs alignment:
   - Publish approved Android/Windows artifacts or keep URLs intentionally blank.
   - Update `POKROV-app/artifacts/releases/.../release-handoff.json`.
   - Sync runtime env and verify `/api/client/apps`.
   - Rebuild/redeploy marketing after any public download URL change.

3. SEO/schema pass:
   - Add `/checkout/` to sitemap.
   - Decide `/install/` indexation.
   - Add store/download URLs and real screenshot references to SoftwareApplication schema only after approved URLs exist.
   - Validate metadata through rendered output, not just static grep.

4. ASO/store metadata pack:
   - Create a client-owned store metadata folder with Google Play and Microsoft Store drafts.
   - Include screenshots, captions, feature graphic, icon, release notes, data safety/privacy notes, support email, content rating inputs, and approval checklist.

5. Launch/support operations:
   - Promote support macros below into a canonical support runbook or admin canned-response source.
   - Create a known-issues page for beta limitations.
   - Prepare one Telegram channel launch post, one follow-up update, and one "downloads paused" fallback post.

## Exact Verification Commands

Run from `C:/Users/kiwun/.config/superpowers/worktrees/VPN/open-beta-v4`:

```powershell
python -m pytest tests/test_marketing_release_readiness.py tests/test_public_copy_guardrails.py -q
Push-Location marketing; npm.cmd run check:seo; npm.cmd run build; Pop-Location
python scripts/check-links.py
python scripts/ui_visual_smoke.py
python scripts/release_gate_check.py --quick
python scripts/release_orchestrator.py --gates-only
```

Run client release checks from the same platform worktree when client gates are in scope:

```powershell
python scripts/run_client_release_gate.py preflight
python scripts/run_client_release_gate.py test --suite portal
python scripts/run_client_release_gate.py test --suite full
python scripts/run_client_release_gate.py build --target windows
python scripts/run_client_release_gate.py build --target android-apk
python scripts/run_client_release_gate.py build --target android-aab
```

Run only with a physical Android device and release-installed build:

```powershell
$env:ANDROID_AUDIT_SERIAL="<physical-device-serial>"
python scripts/android_localhost_audit.py --serial $env:ANDROID_AUDIT_SERIAL --connect-wait-sec 30 --disconnect-wait-sec 15
python scripts/release_gate_check.py --client-platform-gates windows,android-apk,android-aab
```

Runtime/download verification after handoff sync:

```powershell
python scripts/remote_brain_apply_release_handoff.py --brain-ip 82.21.114.104 --metadata-file "C:/Users/kiwun/.config/superpowers/worktrees/POKROV-app/open-beta-v4/artifacts/releases/pokrov-app/<version>/release-handoff.json"
python scripts/verify_brain_ready.py --brain-ip 82.21.114.104
python scripts/api_lifecycle_smoke.py
```

Manual/rendered SEO checks:

```powershell
Push-Location marketing
npm.cmd run build
Pop-Location
python scripts/check-links.py
```

Then verify rendered pages in a browser or Rich Results Test:

- `https://pokrov.space/`
- `https://pokrov.space/checkout/`
- `https://pokrov.space/install/`
- `https://pokrov.space/sitemap.xml`
- `https://pokrov.space/robots.txt`
- `https://pokrov.space/manifest.webmanifest`

## Public Beta Launch Checklist

- [ ] Final decision in `13-launch-decision.md` is updated and not contradictory.
- [ ] Every P0 gate is `PASS`, or launch scope is downgraded to limited/gated beta.
- [ ] Android physical release-build localhost/control-surface audit has redacted evidence.
- [ ] Android signing state is confirmed or Android remains internal only.
- [ ] Windows signing state is confirmed or Windows copy includes SmartScreen/unknown-publisher warning.
- [ ] `release-handoff.json` has approved URLs or intentionally blank blocked state.
- [ ] `/api/client/apps` returns the same approved URLs.
- [ ] Marketing `/install/` and cabinet `/downloads/` agree on download availability.
- [ ] Public checkout route works and is included in sitemap if indexable.
- [ ] Robots, sitemap, manifest, favicon, apple icon, Open Graph, Twitter, and JSON-LD are verified from rendered output.
- [ ] Legal offer/privacy pages are reachable.
- [ ] Support bot, feedback bot, support email, and cabinet tickets are verified.
- [ ] Support macros are available to operators.
- [ ] Telegram channel launch post is approved.
- [ ] Known issues are published or ready for support use.
- [ ] Store/ASO metadata pack exists or store launch is explicitly out of scope.
- [ ] Current-origin, brain-origin, and RU-origin checks are labeled separately.

## Release-Note Draft

Title: POKROV `0.10.0-open-beta.N`

POKROV is opening a careful Android + Windows beta.

What is ready:

- App-first start: open the app, tap `Try free`, get 5 days of premium-grade access.
- Telegram remains optional for first start and daily use.
- Telegram can add `+10 days` after account linking and channel membership.
- Cabinet support, downloads, subscription, devices, and basic statistics stay in one place.
- Windows beta may be available as a gated build with a clear unsigned/SmartScreen warning.

Known limits:

- Android public release remains blocked until production signing and physical release-build audit are complete.
- Windows public trust depends on signing and approved handoff.
- iOS and macOS are readiness tracks only in this wave.
- Downloads may be limited to approved beta users.
- Support is best-effort during beta, with a target response window up to 24 hours.

Next step:

- Open `https://pokrov.space/install/` or your cabinet at `https://app.pokrov.space/`.
- If a file is not available for your account yet, contact `@pokrov_supportbot`.

## Telegram And Community Launch Copy

### Use Only If P0 Gates Are Green For The Announced Scope

POKROV beta is opening carefully.

Android and Windows are the focus of this wave. The app-first path is simple: install POKROV, tap `Try free`, get 5 days of access, then connect.

Telegram is optional for the first start. It stays useful for support, recovery, community updates, and the `+10 days` channel bonus.

Start here: https://pokrov.space/install/  
Cabinet: https://app.pokrov.space/  
Support: @pokrov_supportbot

Beta note: some downloads may be available only to approved testers. If your file is not visible yet, write to support and we will route you calmly.

### Limited/Gated Beta Copy

POKROV is in a gated beta stage.

We are testing Android and Windows carefully before broad public release. If you have beta access, open the cabinet and check Downloads. If a file is not visible, write to support instead of searching for mirrors.

Cabinet: https://app.pokrov.space/  
Install help: https://pokrov.space/install/  
Support: @pokrov_supportbot

Important: Android is not public-safe until signing and the physical release-build audit are complete. Windows beta builds may show an unknown-publisher warning until trusted signing is finished.

### Downloads Paused Copy

POKROV beta downloads are temporarily paused while we verify the release handoff.

Your existing access is not replaced by this post. Please use the app or cabinet first, and contact support if you need recovery.

Support: @pokrov_supportbot  
Cabinet: https://app.pokrov.space/

We will post again when the next approved build is visible.

## SEO/ASO Backlog

### SEO

- Add `/checkout/` to marketing sitemap if checkout remains the primary public acquisition page.
- Decide whether `/install/` should stay `noIndex` or become an indexable install-help page after public URLs exist.
- Replace generic SoftwareApplication `screenshot` with real app screenshots when approved.
- Add app store/download URLs to schema only after they are live and approved.
- Add aggregate rating only after moderated, policy-safe review data exists.
- Render-test JSON-LD with a browser or Rich Results Test.
- Keep public copy free of direct product-use `VPN` wording except legacy identifiers.
- Add a launch/known-issues page only if it can stay truthful and maintained.

### ASO And Store Metadata

- Google Play title candidate: `POKROV`
- Google Play short description candidate: `App-first access for Android with a 5-day beta start.`
- Google Play full description backlog:
  - first 3 lines explain app-first start, 5-day trial, Android scope, and support
  - include support email `support@pokrov.space`
  - avoid public Android safety claims until audit passes
  - explain Telegram as optional reward/recovery, not required login
- Google Play visual backlog:
  - 8 phone screenshots
  - feature graphic `1024x500`
  - icon regenerated from current brand master
  - screenshot captions for: Try free, Protection, Rules, Profile/Support, Telegram bonus, Cabinet handoff
- Microsoft Store backlog:
  - product name `POKROV`
  - short description for Windows beta
  - screenshots for install, Protection, Rules, Profile/Support, cabinet/download handoff
  - privacy/support URLs
  - signed package identity verification
- Apple backlog:
  - metadata drafts only; do not publish as live release in this wave
  - mark iOS/macOS as readiness only
- Cross-store backlog:
  - release notes per platform
  - content rating inputs
  - data safety/privacy answers
  - support contact and website URLs
  - screenshot source files and export sizes
  - localization plan for Russian first, English secondary

## Support Macro And Template Set

### Trial Did Not Start

Hi. Please try this order:

1. Open POKROV again.
2. Tap `Try free`.
3. Check that your internet connection is active.
4. If it still does not start, send us your device platform, app version, and what you see on the screen.

The trial is created by the backend, so we will check the account state rather than asking you to paste technical links.

### Download Not Visible

Your account may not have an approved beta file yet.

Open the cabinet: https://app.pokrov.space/  
Then check Downloads.

If the file is still missing, reply here and we will check whether your beta access is ready. Please do not use unofficial mirrors.

### Android Beta Limitation

Android is currently limited to approved beta users.

Public Android release still waits for production signing and a physical release-build security audit. If you are in the beta group, use only the file shown in the cabinet or sent by support.

### Windows SmartScreen Warning

The current Windows beta may show a Microsoft Defender SmartScreen or unknown-publisher warning while trusted signing is not complete.

If you are not expecting a beta build, stop and ask support first. If you are an approved tester, use only the link from the cabinet or support.

### Cannot Connect

Please try:

1. Refresh the profile in the app.
2. Change location or use Auto-select.
3. Reconnect.
4. If you are in Russia, use `All except RU` first.

If it still fails, send the app version, platform, route mode, and approximate time of the issue. Do not send private connection links or QR codes in public chats.

### Telegram Bonus Missing

Please check:

1. Telegram is linked to the same POKROV account.
2. You are subscribed to `@pokrov_vpn`.
3. You tapped the bonus claim/check action again in the app or cabinet.

If it still does not apply, send support the approximate time of the claim attempt.

### Payment Or Key Issue

Please send:

- payment time
- plan selected
- whether you received an activation key
- where you tried to redeem it: app or cabinet

Do not send card details. We only need the payment route and key/redeem state.

### Old App Or Old Link

POKROV is the current app line.

Install the new app first, confirm it connects, and only then remove the old app if you no longer need it. Old `kiwunaka.space` links may continue temporarily for compatibility, but new support and downloads should use `pokrov.space`.

### User Asks For iOS Or macOS

iOS and macOS are not part of this public beta release.

They are readiness tracks only right now. The current beta focus is Android and Windows.

### Escalation Template For Operators

Use this when handing a case to engineering:

```text
User issue:
Platform:
App version:
Account/session state:
Telegram linked:
Route mode:
Download/source used:
Payment/key state:
Last successful connect:
Observed error:
Current-origin evidence:
Brain-origin evidence:
RU-origin evidence:
Sensitive data redacted: yes
```

## Final Readiness Verdict

Docs and support copy are close enough for a truthful gated beta. Growth and launch materials are not ready for broad public announcement. The safest next step is to keep the launch decision blocked or limited until download handoff, signing/audit evidence, and store/ASO materials catch up.
