# CyberGhost — Mobile App Competitor Profile

**Snapshot date:** 2026-07-22<br>
**Status:** `DEEP PASS COMPLETE WITH BLOCKERS`<br>
**Android package:** `de.mobileconcepts.cyberghost`<br>
**Installed version:** 8.40.0<br>
**Install source:** Google Play

Evidence root: `raw/cyberghost/2026-07-22/`

## Runtime isolation

- Only CyberGhost was launched for this pass; no other VPN app was started.
- Cold launch of `de.mobileconcepts.cyberghost/.view.app.AppActivity` completed in about 0.8 s.
- First observed memory sample was about 105 MB PSS / 213 MB RSS, with no swap.
- No `tun0` interface was present before onboarding interaction.
- Android Chrome is opened only when an app link requires it and is force-stopped before continuing in the VPN app.
- End-state hygiene: CyberGhost and Chrome were force-stopped, no audited competitor process remained, `tun0` was absent, Android always-on/lockdown VPN settings were unset, and the emulator's original rotation was restored.

## First-run screen

Evidence: [screenshot](raw/cyberghost/2026-07-22/screenshots/01-isolated-launch.png), [UI dump](raw/cyberghost/2026-07-22/ui/01-isolated-launch.xml).

- Full-screen dark navy onboarding with a large yellow CyberGhost illustration and one full-width yellow `Continue` CTA.
- Copy: `Welcome to CyberGhost`.
- The app states `I hereby confirm I have read and accept the Terms of Service.` There is no separate checkbox: continuing is the acceptance action.
- Privacy block: `We value your privacy`; it says collected data improves the experience and that nonessential collection can later be disabled in Profile settings.
- Both legal references are inline links, not separate controls.

## First-run outbound links

Both links opened a full Android Chrome tab rather than an in-app webview/custom tab.

| Source | Destination observed | Evidence | Notes |
|---|---|---|---|
| Terms of Service | `https://www.cyberghostvpn.com/terms?utm_medium=client&utm_source=android_app` | [screen](raw/cyberghost/2026-07-22/screenshots/02-terms-destination.png), [UI](raw/cyberghost/2026-07-22/ui/02-terms-destination.xml) | Page exposes Terms and Conditions, Refer A Friend Terms, Imprint and General Business Terms; visible revision date was 2025-09-10 and the page carries a US binding-arbitration notice. |
| Privacy Policy | `https://www.cyberghostvpn.com/privacypolicy?utm_medium=client&utm_source=android_app` | [screen](raw/cyberghost/2026-07-22/screenshots/03-privacy-destination.png), [UI](raw/cyberghost/2026-07-22/ui/03-privacy-destination.xml) | Hero claims Privacy by Design and says traffic data and connection logs are not monitored/stored; page includes a persistent Live Chat control. |

Both destinations keep explicit Android-client attribution in UTM parameters. The website also places a promotional banner above the legal content, so a compliance link doubles as a commercial surface.

## Immediate product takeaways

- Strong branded first impression: mascot, security metaphor, strict yellow/navy system and one dominant action.
- Consent is low-friction but bundled: the user cannot continue without implicitly accepting terms, while analytics/data collection is described as configurable only later.
- Legal pages retain growth surfaces (promo banner and live chat) and client-source attribution rather than acting as sterile documents.

## Paywall, account and Russia payment path

Evidence: [paywall](raw/cyberghost/2026-07-22/screenshots/04-after-continue.png), [login](raw/cyberghost/2026-07-22/screenshots/05-existing-user.png), [Google Play block](raw/cyberghost/2026-07-22/screenshots/34-annual-checkout.png).

- The first post-consent screen is a hard paywall; no free/guest route is shown.
- Annual offer: three-day free trial, then `3,590 RUB/year`.
- Monthly offer: `699 RUB/month`, with no trial stated on that button.
- Benefits above the price: 38M+ customers, encryption, servers in 100+ countries, seven devices and 24/7 support.
- Renewal copy says the Google Play plan renews automatically until cancelled and must be cancelled one day before renewal.
- `Existing user?` opens an email-or-username plus password login, account recovery and a pre-login settings gear.
- `New user?` returns to the subscription paywall; there is no separate no-purchase registration form in the app.
- Opening the annual checkout did not start a trial or purchase. Google Play returned: payments are currently suspended in Russia. The paid product and authenticated home/server experience are therefore `BLOCKED_BY_PAYMENT_RAIL` in this environment.

## Pre-login settings and privacy controls

Evidence: [General](raw/cyberghost/2026-07-22/screenshots/06-prelogin-settings.png), [privacy defaults](raw/cyberghost/2026-07-22/screenshots/07-privacy-preferences.png), [privacy opt-out](raw/cyberghost/2026-07-22/screenshots/08-privacy-optout-selected.png), [VPN](raw/cyberghost/2026-07-22/screenshots/10-prelogin-settings-vpn.png), [Wi-Fi](raw/cyberghost/2026-07-22/screenshots/18-prelogin-settings-wifi.png).

### General

- Domain substitution/domain-fronting setting: off by default.
- Share network data for troubleshooting: off by default.
- Haptic feedback: on by default.
- Links: Privacy preferences, article catalog, report a problem, user agreement, privacy policy and imprint.
- Full build label: `8.40.0.4232 (Google Play)`.

### Privacy preferences

- `Essential` is mandatory and locked on.
- `Analytics` was on by default and names Google Analytics for Firebase.
- `Marketing` was on by default and names AppsFlyer plus Firebase.
- Separate `Confirm Selection` and `Accept All` actions are provided. Analytics and Marketing were switched off and the selection was confirmed for the remainder of the audit.
- This substantiates the onboarding copy that nonessential collection can be disabled later, but the default path activates both optional categories until the user finds this nested page.

### VPN

- Connection check, dedicated IP token entry, protocol picker, small-MTU mode, random port, content blocker and application split tunneling.
- Protocol picker exposes `Auto`, `OpenVPN` and `WireGuard`.
- Small packet size is off; random port is on; content blocker is off.
- Content blocker copy says it blocks domains used for advertising, tracking and malicious software.
- Split tunneling is bypass-based: selected applications are allowed outside the encrypted VPN tunnel. The app shows a full installed-app picker with checkboxes.

### Wi-Fi automation

- Wi-Fi protection is visually on by default and unknown networks default to `Ask`.
- Unknown-network actions: Ask, Protect, automatic stop and Ignore.
- Automation cannot operate without location access/location services; the app explicitly says all other VPN features continue working without that permission.
- Android notification permission appeared while this area was explored and was denied. Location access was not granted.

## Education and support surfaces

Evidence: [catalog](raw/cyberghost/2026-07-22/screenshots/24-article-catalog.png), [article unavailable state](raw/cyberghost/2026-07-22/screenshots/25-article-streaming.png), [support form](raw/cyberghost/2026-07-22/screenshots/26-report-problem.png). The unredacted lower-form screenshot/UI dump contained a prefilled diagnostic instance identifier and was quarantined outside the worktree.

- The in-app catalog has six acquisition/retention articles: bypass streaming restrictions, save money with CyberGhost, public-Wi-Fi safety, VPN benefits for gamers, bypass school-network restrictions and online freedom at work.
- Opening the first article returned the branded unavailable-content state `Try again later`; its body was not treated as captured.
- `Report a problem` opens a Chrome Custom Tab on CyberGhost's Zendesk support domain, unlike the onboarding legal links that opened full Chrome tabs.
- Support form fields include email, optional device/OS/country, subject, rich-text description, reference number, optional diagnostic identifier and attachments.
- The page says the message data will be collected and analysed by a service partner under the linked terms/privacy policy. No form was submitted.

## Imprint and commercial layering

Evidence: [imprint](raw/cyberghost/2026-07-22/screenshots/30-imprint-destination.png), [imprint details and upsell](raw/cyberghost/2026-07-22/screenshots/31-imprint-scroll.png).

- App imprint link opens a Chrome Custom Tab on `cyberghostvpn.com`.
- Named operator: `CyberGhost S.R.L.`, Bucharest, Romania.
- Visible registration identifiers: trade register `J40/1278/2011`, VAT `RO28003392`, EUID `ROONRC.J40/1278/2011`.
- The imprint page is also a conversion page: a `2.19 EUR/month` / `save 82%` banner, live chat, cookie-consent banner, 45-day money-back CTA and a visible Trustpilot `4/5` claim surround the legal data.

## Installed package/static observations

Full notes: [static-package-notes.md](raw/cyberghost/2026-07-22/logs/static-package-notes.md).

- Installed candidate is version `8.40.0` / code `4232`, min SDK 32 and target SDK 36.
- Base plus x86_64/xhdpi splits all pass signature verification and share one signer; fingerprints are intentionally omitted.
- Native OpenVPN and WireGuard-Go libraries corroborate the visible protocol options.
- App deep links reveal first-class destinations for countries, streaming, favorites, best server and last-used server, plus signup/recovery/settings/help routes.
- Permissions cover VPN/networking, location-based Wi-Fi automation, notifications, billing, push, install attribution, Advertising ID and Android AdServices attribution.
- Static components/resources include Firebase/Google Analytics, AppsFlyer, Iterable, Sentry and Zendesk. Sentry replay classes and older Mixpanel-labelled backup exclusions exist in the artifact, but presence is not evidence that those paths were active during this session.
- Cleartext traffic is disabled. Application backup is disabled; granular rules also exclude keys/certificates, caches, logs, encrypted preferences, telemetry, attribution purchase data and support identity.

## Store positioning and creatives

Full notes: [store-surface-notes.md](raw/cyberghost/2026-07-22/logs/store-surface-notes.md).

- Google Play positions CyberGhost around a three-day trial, 100 countries and seven devices; the Apple route advertises a seven-day trial.
- Both stores reuse essentially the same six-step narrative: privacy, encryption, no logs/Wi-Fi automation, server breadth, one-tap connection and press/social proof.
- The campaign system is visually strong and scalable across phone, tablet and Android TV, with real UI states rather than generic shield art.
- Store evidence is not fully synchronized: creatives contain stale renewal/account data and device limits above the current seven-device claim. Exact usernames and public IP values were intentionally not transcribed.
- Visible recommendation graphs place CyberGhost beside NordVPN, Proton VPN, Speedify, Blokada, VyprVPN, UltraVPN and a long tail of generic proxy/VPN utilities. Publisher adjacency also cross-promotes Private Browser and Secret Photo Vault.
- Apple version history shows a roughly monthly iOS cadence in spring/summer 2026, but both stores lean on generic maintenance notes instead of a transparent feature changelog.

## Public company, product and release surface

Full notes: [public-surface-notes.md](raw/cyberghost/2026-07-22/logs/public-surface-notes.md).

- Operator is CyberGhost S.R.L. in Romania; its privacy policy names Kape Technologies PLC as ultimate holding company, and Kape publicly groups CyberGhost with ExpressVPN, Private Internet Access, Intego and Webselenese.
- Public product breadth is materially larger than the paid-gated Android shell: 120+ locations/100 countries, purpose-built streaming/P2P/gaming routes, NoSpy infrastructure, token-based Dedicated IP, Smart DNS, browser proxy/Cookie Cleaner extensions, Windows Security Suite and Identity Guard.
- The account dashboard acts as a cross-device product hub for downloads, devices, manual configurations, add-ons and breach/password tools.
- Referral program is double-sided: a paid qualifying friend and the referrer each receive 30 days, capped at three friends/90 referrer days.
- CyberGhost uses quarterly transparency reports plus repeated Deloitte no-logs engagements as trust infrastructure. The public announcement describes a third ISAE 3000 (Revised) engagement covering servers, operations and Dedicated IP separation; the full report sits behind a restricted-use acknowledgement that was not accepted during this audit.
- Current public surfaces expose synchronization debt: stale Private Browser cross-sell after its 2024 sunset, conflicting legal addresses/age thresholds, an `unlimited devices` Terms relic against the current seven-device plan and stale store entitlement/account data.
- Release distribution is broad and frequent, but public release notes are mostly generic maintenance text and there is no clear cross-platform feature changelog.

## Evidence coverage and blockers

- Retained set: 104 files — 38 accepted runtime screenshots, 38 non-sensitive UI dumps, 23 store creatives and five notes/package logs; zero empty files.
- Authenticated home/server/specialty screens and a live tunnel are `BLOCKED_BY_PAYMENT_RAIL`: Google Play payments are suspended in Russia and no free/guest entitlement exists.
- Deep links to Countries and Streaming were delivered to the app but did not bypass the paywall.
- No purchase, trial, account registration, support submission, review or public action was completed.
- The lower Zendesk form artifact containing a prefilled diagnostic instance identifier was quarantined outside the worktree. APKs and signature details also remain only in the sensitive temporary audit directory.
- Runtime, static package, store, public/legal/company, pricing/referral and release/distribution scope is complete. Any paid-only UI claim in this profile is sourced from official support/store material and is distinguished from direct runtime observation.
