# WO-001 — Audit Reconciliation And Owner Decisions

Status: `COMPLETE`

## Purpose

Reconcile the following owner-supplied material with the exact pushed product
before creating a new implementation goal:

1. `POKROV — conversion-first acquisition refactor`;
2. `P0 — что реально надо починить до любых новых улучшений`;
3. the inline site recommendations supplied on 2026-08-14;
4. `POKROV_FULL_AUDIT_AGENT.md`.

The documents were read completely. Their useful direction is retained below;
stale facts and out-of-scope ideas are explicitly rejected so a compacted chat
cannot silently reintroduce them.

## Classification Legend

- `STILL_PRESENT`: current code still has the reported gap.
- `PARTIALLY_FIXED`: the main path improved, but the named contract is not
  complete.
- `ALREADY_FIXED_PUSHED`: current pushed code already satisfies the useful part.
- `SUPERSEDED_BY_BETTER_IMPLEMENTATION`: current product chose a safer or
  clearer implementation; do not regress it to the supplied proposal.
- `NOT_APPLICABLE`: explicitly outside this wave.

## Non-negotiable Current Truth

| Fact | Current truth | Consequence |
| --- | --- | --- |
| Trial | 5 premium days, activated through the current first-connect/account flow | Reject old 7-day text and any permanent free-node proposal |
| Telegram reward | 5 days; grandfathered 10-day grants remain historical | Do not advertise a new 10-day Telegram reward |
| Referral economics | Current code says friend +5, referrer +15 after hold; support knowledge already says referrer +10 | Reconcile to the owner's recorded decision before deploy |
| Prices | `start_99` 99 ₽; 1/3/6/9/12 months 239/669/1199/1699/1999 ₽ | Reject 249/699/1399/1644 from stale audits |
| `start_99` | One welcome month, one device, available once | Keep the deliberate “от 99 ₽ за полный месяц” marketing hook |
| Main paid plans | Five devices, no traffic cap, no tariff speed cap | Never imply that the 99 ₽ plan has five devices |
| Free tier | Disabled in production; guarded legacy compatibility remains | Do not add a free node and do not mass-delete compatibility code |
| Public release | `v1.0.4-beta.1`; Android `1.0.4+2013`; Windows `1.0.4-beta.1+13` | Old `1.0.0-beta` owner docs are stale, not release truth |
| Public platforms | Android and Windows | Apple/stores remain a separate later project |

## Reconciled Findings

### 1. Branches And Local State

Status: `ALREADY_FIXED_PUSHED`

- Platform `codex/platform-product-readiness-20260804`, its remote and
  `origin/master` all point to `bf79d3d` (`0/0` divergence).
- Client `codex/product-readiness-20260804`, its remote and `origin/main` all
  point to `e172d4b` (`0/0` divergence).
- Both worktrees were clean at discovery start.
- Local `master` is 26 commits behind `origin/master`; local `main` is 16 commits
  behind `origin/main`. This is a stale local ref, not unmerged product work.

Decision for the next wave: fast-forward local promotion refs, then implement
on new scoped `codex/...` branches. Do not manufacture empty merge commits and
do not develop directly on the protected promotion lines.

### 2. Product Truth, Pricing, Trial And Versions

Status: `PARTIALLY_FIXED`

What is already correct:

- shared tariff catalog and current UI use the six approved prices;
- trial is five days;
- permanent free access is disabled in production;
- release metadata and the public GitHub release describe `v1.0.4-beta.1`.

What still conflicts:

- platform product/operations docs still contain `1.0.0-beta` as a current
  distributed version;
- `shared/pokrov-screen-atlas.ts` still carries `1.0.0-beta.4` capture text;
- `shared/product-facts.json` grants the referrer 15 days while
  `shared/support-ai-knowledge.json` promises 10 days after the friend's first
  payment;
- some legacy free-plan labels remain in compatibility and operator-only code.

Required scope: reconcile current canonical owners and consumer/support copy;
preserve historical evidence and guarded compatibility rather than rewriting
history or deleting old schemas.

### 3. Public Downloads And The Authentication Wall

Status: `PARTIALLY_FIXED`

Already fixed in the current production path:

- `/install/` shows direct Android and Windows buttons;
- deployed build-time download URLs point at approved GitHub release assets;
- the bot exposes ARM64, ARMv7, universal and Windows downloads before ToS;
- the install copy says that account use happens after installation.

Remaining gap:

- marketing gets download URLs only from build-time public environment values;
- if those values are absent, public CTAs fall back to authenticated cabinet
  `/downloads/`, recreating the auth wall;
- only authenticated `/api/client/apps` exists; there is no bounded public
  runtime catalog containing version, variant, size, SHA-256 and approved URL;
- download links and analytics are duplicated across site/bot/cabinet rather
  than resolved through one safe public contract.

Recommended scope: add one safe public client-release endpoint or equivalent
runtime artifact, reuse it in a public download resolver, keep the authenticated
client endpoint private, and fail closed to a verified release URL rather than
to login.

### 4. Marketing Homepage Conversion Hierarchy

Status: `STILL_PRESENT`

- H1 is still “Открывайте привычные сервисы”; service outcomes only appear in
  the subtitle.
- Hero/topbar/final CTAs add an `/install/` hop instead of selecting a direct
  platform download when that choice is safe.
- First trust strip shows support instead of the stronger first-layer privacy
  boundary.
- Homepage pricing renders all six active plans.
- Trial/start price/five-device facts are individually qualified, but their
  adjacency still makes the 99 ₽ and five-device relationship easy to misread.
- Telegram bonus remains a homepage section after pricing; it is not in the
  hero, but it still competes with the purchase decision.

Recommended first layer:

- explicit outcome-led H1;
- Android-aware direct primary action, with Windows/platform chooser available;
- trust strip: five days, no card/autopay, Releases + SHA-256, no browsing
  history stored;
- three catalog-driven cards: `start_99`, `6_months`, `12_months`, then “Все
  тарифы”;
- keep all six plans in checkout;
- move bonus mechanics out of the cold conversion layer.

### 5. SEO Claims

Status: `STILL_PRESENT`

`marketing/src/lib/seo-pages.ts` and several intent pages repeatedly claim
“лучший VPN”, “лучший VPN 2026” and “лучший VPN для ...”. These absolute claims
conflict with the chosen trust posture. Replace them with descriptive intent
phrasing without removing the pages or their useful content structure.

### 6. Trust And Privacy

Status: `PARTIALLY_FIXED`

- `/privacy/` already states the correct boundary: browsing history is not
  stored, while necessary account/technical/payment fields exist.
- Repository dependency/source scan found no Firebase, AppsFlyer, Adjust,
  Mixpanel, Amplitude, Meta Pixel or comparable advertising SDK integration in
  the current web surfaces.
- Releases/checksums and support links already exist.
- The concise privacy promise is not surfaced in the homepage's first trust
  strip.
- Current-version trust pages still inherit stale platform documentation in
  places.

Allowed public wording after an exact release dependency/network audit:

- “Не храним историю посещённых сайтов.”
- “Без рекламных SDK и сторонних маркетинговых трекеров.”

Do not claim that POKROV collects nothing or provides absolute anonymity.

### 7. Public Checkout

Status: `ALREADY_FIXED_PUSHED` for layout; `STILL_PRESENT` for attribution.

Already fixed:

- compact plan picker;
- one primary `Оплатить N ₽` action;
- payment-method choice;
- promo code and activation/help behind disclosures;
- exact plan device limits and total amount;
- all six plans remain available.

Remaining:

- the public checkout sends a hard-coded `source: "site"`, losing campaign
  attribution;
- browser acquisition context is not retained through order creation.

Do not redesign this checkout again. Extend its existing compact implementation.

### 8. Authenticated Cabinet Checkout

Status: `STILL_PRESENT`

- the authenticated checkout defaults to `start_99` and displays it for every
  account;
- the backend correctly returns HTTP 409 after any successful provider payment;
- the UI does not know eligibility in advance, so an existing paid user can
  select an impossible plan and only learn after pressing Pay.

Required scope: return/derive authoritative plan eligibility, hide or disable
`start_99` with a plain explanation, and default an ineligible account to the
normal one-month or owner-approved renewal plan.

### 9. First-party Attribution

Status: `STILL_PRESENT`

Existing infrastructure already records anonymous funnel sessions and known
account events, but the current marketing tracker:

- stores only one session source;
- reads `utm_source` and a referrer fallback, but not `ref` or `utm_content`;
- does not preserve first touch and last touch;
- records install-page intent, not an actual APK/EXE `download_click`;
- loses source at public and cabinet checkout boundaries.

Recommended P0: generic first-party `utm_source`, `utm_campaign`,
`utm_content`, `ref`, first/last touch, actual download click, checkout and
paid-order attribution. Do not add third-party analytics SDKs and do not pretend
an anonymous browser session is the same identity as a newly installed app.

### 10. Admin Funnel Semantics

Status: `STILL_PRESENT`

The admin funnel exists, but its aggregate combines distinct anonymous browser
sessions with distinct Telegram users, sums overlapping checkout sources and
labels the result as one linear “site → cabinet/bot → payment → connected”
funnel. This can produce non-cohort conversion and double counting.

Required scope: keep the current admin surface, but split semantics into:

- acquisition: visit → actual download/bot intent → checkout start → paid;
- product: account/install open → trial activation → first confirmed connect →
  returning connect/paid conversion.

Cross-boundary conversion must be marked partial/unknown unless a legitimate
handoff token exists. Raw events and identities remain hidden from the visual
aggregate.

### 11. Telegram Bot

Status: `ALREADY_FIXED_PUSHED` for the core recommendation.

- new and returning `/start` paths are distinct;
- new user reaches a platform chooser and direct binaries;
- public binaries are available before ToS;
- ToS remains at payment, key redemption and account-sensitive actions;
- manual links are a secondary recovery path;
- Android variants and Windows download are present.

Possible polish remains in copy and measurement, but the stale audit's proposed
bot rebuild is not justified. Do not add a Kira/content campaign flow.

### 12. Client Onboarding, Home, Rules, Profile And Rewards

Status: `SUPERSEDED_BY_BETTER_IMPLEMENTATION` for most stale UI proposals.

Current pushed client already has:

- a compact new/returning welcome choice;
- a staged home reveal and one-time connect hint;
- a central connect control with honest busy/egress states;
- location and route chips plus WARP as a compact secondary control;
- one first-connect device-scope decision;
- route-mode summaries, selected/excluded app counts and a help sheet;
- advanced routes/Wi-Fi/system controls behind “Дополнительно”;
- a compact profile, real traffic/connection statistics, devices, notification
  controls and support diagnostics;
- explicit “bonuses are unavailable during trial” copy;
- roulette, referral/Telegram cards, history and animated icon achievements;
- safe remote promo card rendering with dismiss state.

Do not apply the old audit as a broad app redesign. The next goal may include a
fresh exact-build visual/device audit and small fixes, but it must preserve the
current hierarchy and runtime behavior.

### 13. Lifecycle Notifications

Status: `PARTIALLY_FIXED`

- the app has a cached server notification inbox for incidents, releases,
  compensation, programs and current access;
- Android VPN notification/quick-settings preferences exist;
- the current server does not schedule user lifecycle reminders for trial
  one-day-left, trial expiry, paid three-day/one-day expiry, or expiry recovery;
- there is no exact proof of local OS scheduling and cancellation for those
  lifecycle states.

Required P0 decision: implement state-derived lifecycle messages separately
from manually configured promo. Local OS delivery can remain P1 if the owner
wants a smaller first release.

### 14. Remote Promo Infrastructure

Status: `PARTIALLY_FIXED`

- safe remote slots, approved placements, text/image/banner variants, colors,
  CTA, whole-card click and dismiss are implemented;
- the home client renders one approved card without an app update;
- production had no active `promo_slots_config_v1` campaign during the latest
  readback, so live targeting/dismiss/frequency behavior is not proven;
- lifecycle priority, frequency cap and scheduling arbitration remain weak or
  absent.

This wave may preserve the infrastructure and add arbitration only. Content,
Kira creatives, social ad production and partner campaign strategy are out.

### 15. Admin Safety And Release Chain

Status: `PARTIALLY_FIXED`, audit before change.

- destructive actions already use preview/challenge/intent patterns in the
  current admin architecture;
- release metadata, split APKs, Windows assets, hashes and production runtime
  were exact for `v1.0.4-beta.1`;
- stale current-version prose remains in platform canonical/operations docs;
- do not build a new admin system or republish binaries merely to reconcile
  documentation.

## Explicitly Out Of Scope

- Kira, content ads, social creatives, influencer pages and personalized
  `/r/kira` behavior;
- legal entities, corporate structure and business-registration work;
- Apple/iOS implementation, app stores and store acquisition;
- a permanent free tier or any paid infrastructure for free users;
- new VPN protocols, transport rewrites or node architecture;
- new analytics vendors or advertising SDKs;
- a new payment provider, recurring billing or checkout redesign;
- broad client redesign, new rewards mechanics or speculative gamification;
- rewriting or deleting historical audit/release evidence;
- the separate post-release Huawei/Windows/Telegram/RU-origin/keystore proof
  wave already retained under `2026-08-14--postrelease-manual-proof`.

## Recorded Owner Decisions From The Current Thread

- `start_99` stays as the deliberate “от 99 ₽ за полный месяц” acquisition
  hook; do not make it look like a partial month.
- permanent free node is rejected;
- current prices remain 99 / 239 / 669 / 1199 / 1699 / 1999;
- content advertising/Kira and legal-entity material are skipped;
- Apple/stores are later;
- the current checkout should be one compact “wow” box, not a text wall;
- remote promo infrastructure is useful, but content creation is not part of
  this wave;
- referral reward should not remain 15 days; the owner's stated acceptable
  direction is 10 days after the invited user's successful payment.

## Owner Decisions Required Before Building The Detailed Goal

Resolved on 2026-08-14:

1. **Homepage H1 and CTA — approved.** Use the service-led H1 “YouTube,
   TikTok и ChatGPT — одной кнопкой” and an Android-aware direct primary
   download, with Windows/platform choice secondary.
2. **Homepage pricing — approved.** Show `start_99`, `6_months` and
   `12_months` on the homepage; keep all six plans in checkout. Copy must state
   that 99 ₽ is the one-time first full month and the normal next monthly plan
   is 239 ₽. There is no recurring charge or automatic conversion.
3. **Attribution — full implementation approved.** Do not defer the legitimate
   browser → download → install/account handoff or leave an intentional
   attribution debt. Preserve first/last touch, actual asset download, checkout,
   paid and first-connect lineage with bounded first-party identifiers and no
   third-party tracking SDK.
4. **Lifecycle and delivery — approved across channels.** Include server and
   in-app lifecycle messages, Android/Windows local OS scheduling and
   cancellation, careful Telegram lifecycle/promotional delivery, and existing
   in-app discount/promo notifications. Exact channel arbitration and opt-out,
   quiet-hours and rate-limit behavior belong in acceptance criteria.
5. **Promo arbitration — approved.** Use one deterministic arbiter across
   first-party app, OS and Telegram delivery. Critical incident and access
   lifecycle messages outrank onboarding and promo; promos respect opt-out,
   quiet hours, frequency caps and durable deduplication. A lower-priority
   campaign waits instead of replacing or duplicating a higher-priority item.
6. **Referral policy — approved.** Bonuses are released only after a successful
   paid purchase: friend +5 days, referrer +10 days after the existing 72-hour
   anti-fraud hold. Installation, trial activation and first connection do not
   release referral days.

## Next Action

Reconciliation is complete. Execution continues from `WO-002` through the
acceptance-driven queue in [INDEX.md](INDEX.md).
