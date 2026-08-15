# POKROV Direct Release Readiness Tracker

Last updated: 2026-08-14

Last compaction reconciliation: 2026-08-14. The active Codex goal, this ledger,
the current platform/client diffs and retained runtime evidence were compared;
no accepted reward, AI, advertising, selected-screen, distribution or cleanup
requirement was dropped. Device identity/admin, bot Apple fallback,
campaign-entry, bonus/roulette, AI, remote-ad and full-path work remain
explicit below until their own evidence closes them.

Document class: `ACTIVE_EXECUTION`

Scope: the next direct, outside-store POKROV release for Android and Windows.
This tracker coordinates platform and client work but does not replace the
canonical owners named below. It must stay current until the exact candidate is
published or explicitly rejected.

## Objective

Ship POKROV as a coherent mobile-first product whose real user path works from
the first advertising touch through installation, connection, support and
purchase continuation. Promotion is allowed only for an exact production-signed
candidate with current evidence. A local build, an older release, an emulator
screen, an operator statement or a skipped gate must not be relabelled as a
release pass.

The target release is direct distribution, not Google Play, App Store or
Microsoft Store. Android and Windows are in scope. Apple remains deferred until
the native client, signing and store lanes are deliberately reopened.

## How To Use This Tracker

- Update the status and evidence link whenever a work item changes state.
- Add newly discovered release work here before implementing it so it survives
  session compaction and handoff.
- Product truth still belongs to the canonical product/architecture documents;
  client implementation truth belongs to `POKROV-app/docs/`.
- Candidate observations belong in dated evidence, not in unchecked boxes.
- Keep current-origin, brain-origin and RU-origin evidence separate.

Status vocabulary:

- `DONE_LOCAL`: implemented and verified locally, not production proof.
- `IN_PROGRESS`: implementation or verification is active.
- `TODO`: accepted work not started or not yet rechecked.
- `MANUAL_OWNER_TEST`: requires an owner-controlled device, account or service.
- `BLOCKED_BY_ACCESS`: cannot be tested without missing access or external state.
- `NOT_REQUESTED`: deliberately outside this release.
- `PASS_EXACT_CANDIDATE`: passed for the exact named release artifact only.

## Frozen Owner Decisions

- [x] The public first-month acquisition offer remains `99 ₽` for the full first
  month. It is intentionally aggressive marketing, but its one-time nature must
  be disclosed before payment.
- [x] Standard one-month renewal is `239 ₽`.
- [x] Longer plans are `3 / 6 / 9 / 12 months = 669 / 1199 / 1699 / 1999 ₽`.
- [x] Consumer free-node service is cancelled. Trial expiry must not place free
  users on paid infrastructure or advertise a free fallback.
- [x] The premium trial is exactly `5 days`; no hidden seven-day reservation or
  conflicting date may appear to users.
- [x] Trial accounts may claim the one-time Telegram channel reward; roulette,
  calendar and referral rewards remain unavailable until the first payment. The
  UI must name that split instead of showing a network error.
- [x] Telegram channel reward is `+5 days`, once, including before payment.
  Existing larger historical grants remain readable and are not clawed back.
- [x] Referral reward is `+10 days` for the referrer only after the friend's
  first successful payment survives the configured hold. Install, registration
  and trial do not grant referral days.
- [x] The roulette is paid-only, conservative and enabled as a real feature; it
  must not become a high-volume free-subscription generator.
- [x] Home visual direction is the owner-selected 2026-08-13 reference: one large
  centered connect control, no glowing perimeter, a smaller clean button,
  premium-duration pill, two concise quick controls, WARP row and a remote ad
  card above bottom navigation.
- [x] Remote in-app advertising is operator-controlled without an app update and
  may use logo/image, text, CTA, colors, schedule, audience, full-card link and a
  dismiss action. Disabled advertising must leave no empty gap.
- [x] Android per-app routing and system VPN behavior are tested on a physical
  device; LDPlayer is for UI/API regression only, not tunnel-core proof.
- [x] Apple is `NOT_REQUESTED` for this release. Until reopened, bot/site may
  offer honest compatible-client instructions and a key, never a native POKROV
  Apple app claim.

## Compaction-Safe Requirement Ledger

This ledger is the loss-prevention index for the current long-running session.
An item remains part of the release even if chat context is compacted again. A
checked owner decision is not a release pass; the linked workstream and its
exact-candidate evidence still have to close.

| Requirement that must not be lost | Owner/workstream | Current release state |
| --- | --- | --- |
| Trial is exactly five days; no rewards on trial; paid, expired and grandfathered states are distinct | 1, 7, 13 | `IN_PROGRESS`; the shared Android/Windows shell hides dead trial Telegram/referral actions and states the paid gate explicitly, production-backed paid QA passes, expired/grandfathered matrix remains open |
| Telegram `+5`, referral `+10` only after the friend's held first payment, conservative paid-only roulette, promo/history/idempotency | 1 | `IN_PROGRESS`; local 132-test matrix, two production-backed paid QA spins, persisted 14-day production preset and exact `beta.2` first-load Rewards Hub pass; promo/replay edge matrix remains open |
| Real achievements and statistics, restrained Xbox-like success/reward motion, no invented ad-block numbers or vague Activity filler | 1 | `DONE_LOCAL`; reward reveal passed production-backed LDPlayer visual QA, achievement unlock and exact final-candidate QA remain open |
| Owner-selected centered Home, duration pill to checkout, finite wait animation and no glowing/heavy vector | 2 | `PARTIAL`; production-signed `1.0.4` passed exact Huawei Home and connection-state UI, but the duration-pill tap into checkout lacks exact-final retained evidence |
| Remote ad can be enabled without an app update and configured with image/logo/text/CTA/colors/link/schedule/audience/dismiss | 2, 9 | `DONE_LOCAL`; production operation, image fallback and campaign lifecycle remain open |
| Honest locations, flags, five initial choices, manual refresh, real measurement origin, current load/health and no fake geographic ping claim | 3 | `PARTIAL`; exact Huawei final sheet fits and persists four returned variants, but the required five-option first layer and exact-final egress repetition remain open |
| WARP and manual country selection work through UI, profile, Core, DNS and real egress rather than only showing green state | 3, 13 | `PASS_SUPPORTING_SAME_VERSION_PRE_FINAL_UI_HASH`; exact-final-hash repetition remains `MANUAL_OWNER_TEST` |
| Full/Smart/RU-direct/per-app routes, real AdGuard toggle, Chrome and Yandex in both directions, `2ip.ru`, Wi-Fi/LTE and separate RU-origin probe | 4, 13 | `PASS_SUPPORTING_SAME_VERSION_PRE_FINAL_UI_HASH` for Chrome/Yandex reverse routing and Wi-Fi/LTE; RU-origin and exact-final repetition remain manual |
| Thin correctly scaled branded Quick Settings tile plus useful, uncut and configurable notification with status/country/mode/speed/actions | 5, 13 | exact-final notification `PASS`; tile start/stop `PASS_SUPPORTING_SAME_VERSION_PRE_FINAL_UI_HASH` |
| Native support chat and diagnostics; AI first, useful escalation only when needed; exact `deepseek/deepseek-v4-flash-0731`, one request, 65-second assistant timeout, no hard output cap | 6 | `PARTIAL`; exact Huawei live WARP happy path and production model route pass, while provider/local source, disabled/error/fallback and cabinet/bot continuation remain open |
| `99 ₽` first full month once, then `239 ₽`; `669/1199/1699/1999 ₽`; one compact checkout rather than a text wall | 7 | `PASS_PRODUCTION_ROUTE`; catalog, compact cabinet checkout and Home continuation are deployed; real payment creation was deliberately not triggered |
| Mobile-first site, help, cabinet and bot use concise primary actions with details in sheets/accordions/tooltips | 8, 11 | `PASS_PRODUCTION_ROUTE` for responsive build/E2E and deployed static routes; real Telegram button journey remains manual |
| Campaign destinations, Telegram-vs-site entry, UTM/deep links, promotions and safe no-store continuation are intentional and measurable | 9 | `TODO` |
| Admin shows a privacy-safe account/device identity instead of only generic `POKROV App` or an opaque UID | 10 | `DONE_LOCAL`; linked Telegram plus normalized device/model/platform now lead the UI, linked-email projection and deployed visual QA remain open |
| Bot serves current ARM64/ARMv7/universal Android and setup/portable Windows artifacts; Apple gives only an honest compatible-client/key path | 11 | `PASS_PRODUCTION_ROUTE`; signed-session API returns exact `v1.0.4-beta.1` split APK/setup metadata; fresh/linked Telegram button and Apple-compatible-client UX remain manual |
| Direct Android release includes split APKs, production signing, hashes and encrypted keystore recovery; Windows includes setup and portable | 12, 14 | `PARTIAL`; public `1.0.4+13` Android and `1.0.4-beta.1+13` Windows packaging passes, while encrypted offline keystore recovery remains `MANUAL_OWNER_TEST` |
| All screens and the complete ad-to-support-to-checkout path are retested on the exact published candidate; LDPlayer does not substitute for Huawei/Core | 8, 13, 15 | `TODO` exact-candidate QA |
| Light/dark/system theme, large text and reduced motion keep readable brand, status, navigation and action hierarchy | 2, 8, 13 | `IN_PROGRESS`; fresh LDPlayer dark/1.3x audit found and locally closed brand, muted-text, location-metadata, AI-card and status overflow defects; final versioned candidate QA remains open |
| Inspect dirty/untracked material, keep important artifacts, remove only proven trash; backup before prod; delete only identified QA users/data after QA | 14, 15 | `PASS`; backup/restore, repository classification and secret scan pass; guarded cleanup found no safe disposable production accounts, so none were deleted |
| Deploy, exact asset publication, anonymous download verification, scoped commits and pushes for both repositories, then an evidence-labelled handoff | 15 | `PASS_EXACT_CANDIDATE`; `v1.0.4-beta.1` assets, runtime sync, backend/static deploy, brain verify, anonymous full-download hashes, feature pushes and fast-forward `master/main` promotion pass |

## Current Repositories And Branches

| Lane | Repository | Promotion branch | Active working branch | Current state |
| --- | --- | --- | --- | --- |
| Platform, site, bot, cabinet, admin | `C:/Users/kiwun/Documents/ai/VPN` | `master` | `codex/platform-product-readiness-20260804` | candidate `d364230` is committed, pushed, fast-forwarded to `master`, deployed and verified; this final tracker-only follow-up records closure |
| Android, Windows, shared client | `C:/Users/kiwun/Documents/ai/POKROV-app` | `main` | `codex/product-readiness-20260804` | final handoff commit `e172d4b` is pushed and fast-forwarded to `main`; release tag remains `v1.0.4-beta.1` |
| VPN core | `C:/Users/kiwun/Documents/ai/POKROV-core` | independent `v1.0.3` release | `codex/core-1.0.2-egress-probe` | clean, committed, tagged, pushed and publicly released |

Untracked files must be inspected and classified. Keep source, tests, evidence
and required assets; remove only proven disposable build/QA trash, with exact
paths reviewed first.

## Release Workstreams

### 1. Reward Economy, Trial And Promotions — `IN_PROGRESS`

- [x] `DONE_LOCAL` Backend summary exposes explicit paid-reward eligibility.
- [x] `DONE_LOCAL` New trial accounts are blocked from new Telegram rewards with
  human copy; grandfathered claims remain readable.
- [x] `DONE_LOCAL` Referral default is `+10 days`, awarded only from canonical
  first-payment evidence after the hold.
- [x] `DONE_LOCAL` Automatic friend/invitee grant from connection or trial
  activation is removed.
- [x] `DONE_LOCAL` Roulette preset uses a 14-day cooldown and conservative
  weighted outcomes; expected value and long-tail prizes are documented in the
  backend configuration.
- [x] `DONE_LOCAL` Client parses server `eligible`, `can_spin`, `can_checkin`,
  cooldown and next-action fields instead of guessing readiness.
- [x] `DONE_LOCAL` Rewards Hub puts roulette first, explains the paid gate,
  fixes the squeezed Telegram card and removes the vague Activity grid.
- [x] `DONE_LOCAL` Referral copy states that the friend must pay first.
- [x] `DONE_LOCAL` Retire the old bot-side friend gift and direct referral-day
  mutation: a referred friend receives only the standard five-day trial, while
  the referrer receives `+10 days` only through canonical held-payment evidence.
- [x] `DONE_LOCAL` Align current bot, cabinet, app, marketing and public-guide
  copy with Telegram `+5`, the 14-day roulette and the paid referral rule; keep
  explicit legacy migration support only for old recorded friend grants.
- [x] `DONE_LOCAL` Fail closed in the Rewards Hub when an older server omits
  `reward_access`: the live subscription lane still disables Telegram claims
  and shows one clear paid gate. Compact the trial sheet so it no longer repeats
  the same paid warning in the header, roulette detail and action row.
- [x] `DONE_LOCAL` Profile shows confirmed traffic/connection statistics and
  does not invent ad-block counts.
- [x] `DONE_LOCAL` Achievements use real Material icons and restrained entrance
  motion with reduced-motion support.
- [x] `DONE_LOCAL` Move all trial gates ahead of conflicting campaign checks so
  every unclaimed trial receives the same paid-required explanation.
- [x] `DONE_LOCAL` Verify reward contracts against the focused backend matrix
  (`132 passed`) and the compact Flutter Rewards Hub test (`PASS`), including
  trial gates, held referral payment, cooldown/idempotency, history and legacy
  migration compatibility.
- [x] `PASS_PRODUCTION_EQUIVALENT` The exact currently installed LDPlayer session
  was mapped to its real production-backed QA account, granted an idempotent
  `qa_premium` entitlement, and reloaded as paid rather than trial. Home and
  Profile show `Премиум · 5 дней`; the paid reward gate is open.
- [x] `PASS_PRODUCTION_EQUIVALENT` Two controlled paid QA roulette requests each
  produced one server-side `bonus_wheel` grant of `+1 day`. For the second visual
  pass only the QA account's wheel cooldown markers were reset; the first grant
  was retained. This is not a distribution-frequency proof.
- [x] `DONE_LOCAL` The roulette modal now stays open after success and shows an
  animated, haptic, accessibility-live reward card. The exact production-backed
  LDPlayer flow visibly rendered `Награда получена · +1 день`; reduced-motion
  behavior and focused Flutter tests pass.
- [x] `DONE_LOCAL` Replace the raw ISO last-action timestamp with localized
  `ДД.ММ в ЧЧ:ММ` copy. Focused Flutter test and `flutter analyze` pass; this last
  source change requires one final Android rebuild before publication.
- [x] `PASS_EXACT_CANDIDATE` `v1.0.3-beta.2` fixes the startup ordering that
  previously let subscription refresh and bonus summary reconcile the same
  expired session concurrently. The 118-test app-shell file passes; the exact
  installed x86_64 APK opens roulette/history immediately with no generic error,
  shows the 14-day cooldown, Telegram `+5` and referral `+10`, and no longer
  repeats the cooldown label as a dead action.
- [x] `PASS_PRODUCTION_ROUTE` The persisted production wheel configuration was
  migrated transactionally from `paid_weekly_v1` / `168` hours to
  `paid_fortnightly_discounts_v3` / `336` hours. Exact database readback returned
  seven outcomes with a total weight of `10000`; the controlled QA device now
  receives `Следующая попытка: 27.08 в 10:40` after its 13.08 spin. Before/after
  configuration hashes are retained in the operator evidence without storing
  account identifiers or reward payloads here.
- [x] `PASS_PRODUCTION_ROUTE` A fresh production-backed paid Rewards Hub audit exposed a
  missing referral code/link. The client no longer invents the unusable
  placeholder `POKROV` or renders disabled icon actions: it shows an honest
  refresh state until a real link exists, then only `Пригласить` and
  `Скопировать ссылку`. Final production-signed LDPlayer readback shows both
  live actions and no pseudo-code; the compact Profile summary also no longer
  exposes the account referral code.
- [x] `PASS_PRODUCTION_ROUTE` Paid accounts that predate referral-code provisioning now get
  one unique legacy-compatible code lazily from bonus/referral summary reads;
  repeated reads return the same code/link and trial reads remain mutation-free.
  Focused API tests cover trial, first paid read and stable replay. Backend
  deploy, paid-account readback and repeat client refresh pass.
- [x] `DONE_LOCAL` Fresh Windows visual QA exposed a shared trial-state mismatch:
  Home offered a dead `+5 дней за Telegram` card and the Rewards Hub rendered a
  refresh-style unavailable referral link instead of the paid gate. The shared
  Android/Windows shell now hides the Home reward action on trial, shows
  both Telegram and referral rewards as locked without active CTAs, shows
  `Ссылка появится автоматически после первой оплаты`, and keeps the real
  actions for paid accounts. The full shared widget file passes `120/120`.
- [ ] `TODO` Verify replay/idempotency, distribution boundaries, achievement
  unlock and complete bonus history in LDPlayer.
- [ ] `TODO` Verify promo-code success, invalid, already-used, expired and
  campaign-restricted states without a real payment.

Acceptance: trial never receives a reward and never sees a generic connection
failure for that policy; paid users can use enabled rewards; no path grants
unexpected days; history and dates remain consistent across app, cabinet, bot
and admin.

### 2. Home, Connection UX And Remote Advertising — `IN_PROGRESS`

- [x] Owner selected the target Home reference at
  `C:/Users/kiwun/.codex/generated_images/019ff112-6e26-7c62-ad23-652addbf4791/exec-c0de2e11-f37e-4d84-89f9-c21f3cc61673.png`.
- [x] `DONE_LOCAL` Implement the selected hierarchy using the existing POKROV design system
  and real brand/icon assets.
- [x] `DONE_LOCAL` Make the premium-duration pill open the compact checkout continuation.
- [x] `DONE_LOCAL` Distinguish `disconnected`, `connecting`, `connected`,
  `disconnecting` and actionable `error` copy. Busy Home no longer repeats
  `Подключаемся` in both the primary label and the status line.
- [x] `DONE_LOCAL` Use a restrained finite waiting/hourglass animation; no broken clock,
  infinite spinner or malformed concentric vector.
- [x] `DONE_LOCAL` Preserve one obvious primary action and prevent duplicate buttons from
  competing with it.
- [x] `DONE_LOCAL` Add remote ad placement above bottom navigation with image/logo/text/CTA,
  full-card safe link, dismiss X, schedule, audience, colors and no-layout-gap
  disabled state.
- [x] `DONE_LOCAL` Add compact operator configuration and preview in the primary
  admin surface; the server validates URL schemes, schedule and color syntax.
- [ ] Verify final campaign image dimensions, fit, real contrast and fallback
  behavior in both admin preview and the exact Android candidate.
- [x] `DONE_LOCAL` Compare the chosen reference and the production-signed
  LDPlayer Home in one visual input, fix visible spacing/type/radius and repeat
  the comparison. The retained comparison normalizes both images to the same
  height and disconnected state without distorting the taller source reference.
- [x] `PASS_EXACT_CANDIDATE` The exact published `1.0.4` ARM64 APK renders the
  centered Home; installed `base.apk` SHA-256 equals the published candidate.
  The duration-pill checkout tap still needs retained exact-final evidence.
- [x] `PASS_EXACT_CANDIDATE` The production-signed final build uses
  the dark mint accent for the raster brand mark and raises muted text from
  `#78857E` to `#83908A`. The new muted token measures `5.16:1` on the dark
  surface; LDPlayer dark Home visibly keeps both brand marks and navigation
  readable. These shared-UI changes are included in public `v1.0.4-beta.1`.

Acceptance: the selected Home is recognizable in the running app, all visible
controls work, the banner can appear/disappear without a client update, and the
connect state is understandable without reading a paragraph.

### 3. Locations, Measurements And WARP — `IN_PROGRESS`

- [x] `DONE_LOCAL` Manual selection may promote a healthy visible location into
  the bounded managed profile instead of being silently rejected by shortlist
  size.
- [x] `DONE_LOCAL` Device-side latency probe and compact location label work are
  present in the client working tree.
- [ ] Show five honest location options first, then the complete eligible list.
- [x] `DONE_LOCAL` Add explicit refresh plus compact measured/stale states.
- [x] `DONE_LOCAL` Define and disclose measurement origins in an adjacent info
  sheet. Device RTT is measured from the
  current device to the candidate endpoint; backend load/health has its own
  timestamp. Never present synthetic or server-to-server `1 ms` as device ping.
- [x] `DONE_LOCAL` Show real country flags/names and a compact
  `ping · load · freshness` row without the observed truncation. Exact-device
  plausibility and duplicate/availability checks remain candidate QA.
- [x] `PASS_LOCAL_SIGNED_BUILD` At Android `1.3x`, country/quality and
  `ping · load · freshness` now wrap to two lines instead of reducing the
  evidence to fragments such as `От…` and `сей…`. Fresh before/after LDPlayer
  captures are retained; publication and exact final-candidate QA remain open.
- [ ] Verify automatic, manual, favorite, recent, reconnect and restart paths.
- [ ] Prove manual UI selection reaches managed profile, outbound selection and
  final egress; UI selection alone is not a pass.
- [ ] Prove WARP through state/consent, materialization, Core, DNS and egress;
  surface `applied`, `pending`, `unavailable` and actionable `error` honestly.
- [ ] Test connect/reconnect/location/restart/Wi-Fi/LTE/rollback on the exact
  physical candidate when the phone is returned.

Acceptance: no unavailable location looks selectable, measurements disclose
what was measured and when, and both manual location and WARP change real
traffic on the physical candidate.

### 4. Routing, Per-App Selection And Protection Controls — `IN_PROGRESS`

- [x] `DONE_LOCAL` The explicit direct-region label is `Россия напрямую`.
- [x] `DONE_LOCAL` A real `Блокировать рекламу` toggle selects AdGuard DNS;
  it is not a fake counter or cosmetic switch.
- [x] `DONE_LOCAL` Keep the normal routing screen focused on mode, selected
  applications and DNS/ad blocking. Purpose routes, custom rules, trusted
  Wi-Fi and Always-on guidance live under one `Дополнительно` disclosure.
- [x] `DONE_LOCAL` Android app selection reads installed launcher apps off the
  UI thread, includes bounded real app icons and uses short readable metadata.
- [ ] Add concise adjacent help affordances for Smart mode, direct RU, selected
  apps, WARP, DNS/ad blocking and LAN behavior.
- [ ] Verify Full tunnel, Smart/All except RU, Only selected apps and Android
  Except selected apps.
- [ ] Verify Chrome and Yandex Browser in both per-app directions, empty
  selection fail-closed behavior and persistence after restart/update.
- [ ] Verify Russian destinations including `2ip.ru` take the intended direct
  lane while non-Russian destinations take the tunnel lane.
- [ ] Verify DNS/country without storing or publishing raw user IP.
- [ ] Keep RU-origin probe separate from current-origin and device routing
  evidence.

Acceptance: every routing control changes an observable policy and egress; the
app explains it briefly; no UI-only success state is accepted.

### 5. Android System Surfaces — `IN_PROGRESS`

- [x] `DONE_LOCAL` Quick Settings and foreground-notification source changes and
  focused JVM tests exist in the client worktree.
- [x] `DONE_LOCAL` The monochrome Quick Settings brand mark is visually
  comparable in size and stroke to neighboring LDPlayer system tiles; the
  installed production-signed APK contains the intended vector and tile
  metadata.
- [ ] `MANUAL_OWNER_TEST` Verify the same mark on the exact candidate on Huawei;
  the earlier physical-device evidence predates the final candidate.
- [ ] Verify tile unavailable/off/connecting/on/error states stay synchronized
  with service reality and survive process restart. LDPlayer 14 leaves both the
  POKROV tile and an independently installed Hiddify tile in Android's
  `STATE_UNAVAILABLE` without binding either service, so it cannot prove this
  system path; Huawei remains authoritative.
- [ ] Verify Huawei collapsed/expanded/lock-screen/light/dark notification
  layouts without cropped country, route, status or speed.
- [ ] Notification quick actions must open, connect/disconnect and reach useful
  settings without duplicated controls.
- [ ] Let users choose compact/full notification content and whether speed is
  shown, within Android foreground-service constraints.
- [ ] Physical candidate: background, lock, kill, reboot, battery saver and
  twenty connect cycles.

Acceptance: system surfaces are legible, branded, synchronized and useful on
the physical production candidate.

### 6. Support And AI Agent — `IN_PROGRESS`

- [x] `DONE_LOCAL` Target provider model is
  `deepseek/deepseek-v4-flash-0731` with sufficient reasoning budget and no
  destructive output cap.
- [x] `DONE_LOCAL` Support knowledge now explains no free lane, five-day trial,
  paid-only rewards, referral first-payment rule, direct RU and AdGuard DNS.
- [x] `DONE_LOCAL` A direct bounded probe against the deployed provider route
  returned a diagnostic answer from the exact target model. The production app
  request still requires exact-candidate recheck after the client timeout fix.
- [x] `DONE_LOCAL` Root cause of the in-app fallback was a 15-second client
  response deadline while the exact model completed near 43 seconds. Only the
  assistant POST now gets one 65-second window; no retry, `max_tokens` or
  reduced reasoning was added.
- [x] `DONE_LOCAL` Keep native bubbles, composer/keyboard, loading, retry,
  restored human history and diagnostics; add a prominent `Сначала спросить
  ИИ` entry and label the ticket composer as a message to a human.
- [x] `DONE_LOCAL` A fresh signed LDPlayer session received a real assistant
  answer through the in-app flow after the timeout change, rather than
  immediately handing the question to a human. This proves the client/API path,
  but not yet that every answer came from the configured provider rather than a
  grounded local response.
- [x] `PASS_EXACT_CANDIDATE` The retained production session used the native
  assistant sheet for a WARP problem and received a bounded Russian diagnostic
  answer without immediately opening a human ticket. Production configuration
  readback still resolves `deepseek/deepseek-v4-flash-0731`, reasoning `medium`.
- [x] `PASS_PRODUCTION_ROUTE` The deployed provider route is enabled for both
  support AI and the support agent and resolves the exact model identifier
  `deepseek/deepseek-v4-flash-0731`, reasoning `medium`, without a client or
  provider `max_tokens` cap. Direct bounded provider and in-app requests both
  returned useful answers; the source/fallback matrix below remains open.
- [x] `DONE_LOCAL` Preserve the deterministic assistant answer's paragraph and
  numbered-step structure instead of collapsing it into one text wall. The
  provider prompt already requests one short result and two to four steps; both
  paths still require deployed phone-size visual verification.
- [x] `PASS_LOCAL_SIGNED_BUILD` At Android `1.3x`, the AI-first card gets a
  third description line and visibly preserves the complete `Если не поможет —
  человек` promise. Shared status pills and chat lifecycle hints now flex and
  wrap; focused widget QA reproduces no overflow. Publication and exact
  final-candidate QA remain open.
- [x] `DONE_LOCAL` Fresh production-backed LDPlayer QA asked why bonuses are not
  available in trial. The in-app assistant returned the correct five-day
  trial/paid-reward explanation after bounded waits of 8–16 seconds and did not
  create or open a human ticket.
- [x] `DONE_LOCAL` Support now has one prominent AI entry; secondary Telegram
  support lives under a labelled `Ещё варианты поддержки` menu. Structured
  assistant replies render as native `Коротко` and `Что сделать` sections,
  collapse secondary sentences behind a TalkBack-reachable `Подробности`
  control, and avoid repeating the always-visible human escalation action.
- [ ] Make provider, local-grounding and human-fallback sources operationally
  distinguishable without exposing internals or confusing the user.
- [ ] AI must diagnose WARP/location/routing/notification/trial/reward issues
  before escalating when safe diagnostic steps exist.
- [ ] Verify redaction, one-request semantics, timeout, provider error, disabled
  AI and human fallback.
- [ ] Check every support answer/action within the app, plus cabinet and bot
  continuation.

Acceptance: a real production-session question gets a relevant bounded answer
from the configured model, common issues are not immediately dumped on a human,
and failures retain an honest human-support path.

### 7. Checkout, Pricing And Purchase Continuation — `IN_PROGRESS`

- [x] `DONE_LOCAL` Pricing values are synchronized in the active working tree.
- [x] `DONE_LOCAL` Compact checkout redesign work exists in platform web/cabinet
  files.
- [ ] Verify every site, cabinet, app, bot, promo and renewal surface uses the
  same plan catalog and one-time `99 ₽` qualification.
- [ ] Build one visually strong checkout card/box: selected plan, exact total,
  effective monthly price, renewal behavior and one primary CTA.
- [ ] Move explanations into concise disclosures/tooltips/FAQ instead of a wall
  of text; retain all legal/payment facts.
- [ ] Verify the Home premium-duration pill and expired/trial/paywall states open
  the intended plan selection/checkout page.
- [ ] Verify mobile keyboard, back/cancel, provider error, return, paid callback,
  history and idempotency without making an unauthorized real charge.
- [ ] Confirm 99 ₽ cannot stack with referral/promo discounts; standard plans
  may use only backend-approved discounts.
- [x] `PASS_PRODUCTION_ROUTE` Mobile production checkout at `390x844` keeps one
  selected-plan card with the six prices behind its picker. Selecting the
  12-month plan updates the card and payment summary to `1999 ₽`,
  `≈ 167 ₽/мес`, `365 дней` and `5 устройств`; disclosures open in place and
  the page has no horizontal overflow. No order or payment was submitted.
- [x] `PASS_PRODUCTION_ROUTE` Empty-email validation remains on the checkout,
  exposes `aria-invalid`, `aria-errormessage` and a live alert, and now keeps
  the complete field plus error visible below the fixed mobile header. The
  production measurement after static deploy `20260813131024` is input top
  `208.875`, header bottom `64.8`, input bottom `252.875`, with a `96px`
  scroll margin. Email autocomplete and mobile email input mode are enabled.

Acceptance: exact prices and terms match everywhere, the mobile checkout is
short and understandable, and no payment-success claim is made without current
provider evidence.

### 8. Site, Cabinet, Help And End-To-End Acquisition — `IN_PROGRESS`

- [ ] Walk advertising link -> mobile landing -> Telegram bot or site -> login ->
  cabinet -> download -> onboarding/trial -> connection -> support -> checkout
  continuation, capturing exact-candidate screenshots.
- [ ] Review all mobile-first pages because mobile is the dominant audience.
- [ ] Replace text walls with a short promise, one next action and expandable
  details; do not delete necessary help or disclosures.
- [ ] Check account, subscription, devices, downloads, payments, rewards,
  support, settings, logout, recovery and update surfaces.
- [ ] Verify touch targets, keyboard, TalkBack, large text, contrast, dark mode
  and reduced motion.
- [ ] Compare the full user journey with current VPN competitors and current
  mobile checkout/help patterns using source links and dated evidence.
- [x] `PASS_PRODUCTION_ROUTE` `/guides` is now task/search-first: 46 long guides
  remain discoverable but collapsed, while one search also returns matching
  entries from the 20-screen POKROV atlas. Atlas hash links open and scroll the
  exact screen. Chrome mobile QA at `390x844` found no horizontal overflow; the
  WARP search and `#protection-home` disclosure both pass after production
  deploy `20260813124114`.

Acceptance: a new mobile user always knows the next action and can reach a
working client without a store, Telegram is optional where the product contract
says so, and detailed help remains discoverable rather than dumped on screen.

### 9. Advertising Entry Points And Campaign Operations — `IN_PROGRESS`

- [x] `DONE_LOCAL` Decide and document campaign destination by intent: broad product traffic,
  Android install, Windows install, returning user, promo/referral and support.
  The canonical policy is in `docs/product/portal-vpn-product.md`: broad and
  install intent start on the mobile site, while promo/referral and other
  account-bound intent use the sanitized admin-generated Telegram path.
- [ ] Keep both direct site and Telegram bot entry viable. Test whether the bot's
  transparency/convenience improves conversion without making Telegram a
  mandatory account wall.
- [x] `DONE_LOCAL` Define links/UTM/deep-link/app-handoff behavior and safe fallback when the
  app is absent.
- [x] `DONE_LOCAL` Ensure campaign links preserve attribution without leaking tokens or raw
  account identifiers.
- [ ] Define promotion lifecycle: audience, eligibility, start/end, impression,
  dismiss, click, conversion and rollback; never fake counters.
- [ ] Verify app remote banners and public campaigns share truthful pricing and
  eligibility rules.

Acceptance: every ad has an intentional destination and measurable, safe
continuation; no-store users can install, recover and buy without guessing.

### 10. Account And Device Identity In Admin — `IN_PROGRESS`

- [x] `DONE_LOCAL` Audit the current admin user/device lists and API payloads
  before changing schema or copy.
- [x] `DONE_LOCAL` Replace generic `POKROV App` labels with the best safe display identity:
  verified email or linked Telegram name for the account, plus user-editable or
  OS-provided device name/model for each device. The current slice implements
  linked Telegram plus device/model/platform; linked verified email remains a
  later projection rather than being guessed from synthetic legacy email.
- [x] `DONE_LOCAL` Android may use manufacturer/model and an optional friendly device name;
  Windows may use the machine/device name only with clear normalization and
  privacy boundaries.
- [x] `DONE_LOCAL` Keep immutable canonical account/device UUIDs as secondary operator detail,
  never as the only human label and never as public marketing identifiers.
- [x] `DONE_LOCAL` Handle missing, duplicated, very long, Unicode and changed names; retain
  stable identifiers for support/audit.
- [ ] Verify the same identity context improves support tickets and diagnostics
  without exposing raw credentials or connection material.

Acceptance: an operator can recognize the right account/device without relying
on an opaque UID, while account linking and audit authority remain canonical and
privacy-safe.

### 11. Bot Downloads And Platform Matrix — `IN_PROGRESS`

- [ ] Test a fresh and linked user through bot download/help actions.
- [x] `DONE_LOCAL` Android action returns/recommends the current ARM64 APK,
  offers ARMv7 for old devices and universal only as fallback; explain ABI
  briefly. x86_64 stays in the cabinet/API for emulators instead of cluttering
  the normal phone path. Focused bot and public-copy tests pass.
- [x] `PASS_PRODUCTION_ROUTE` Brain-origin synthetic signed-session smoke reads
  the live bot token without returning it and confirms `/api/client/apps`
  exposes `v1.0.4-beta.1`: ARM64 primary, ARMv7, x86_64, universal and Windows
  setup with exact size/SHA-256. This is API/runtime proof, not a real Telegram
  user button pass.
- [ ] Windows action returns the current setup and exposes portable download as
  a secondary option with honest SmartScreen/unsigned status.
- [ ] Apple action must not claim a native POKROV app. Until Apple work resumes,
  provide supported compatible-client choices, import instructions and the
  account-owned key/manual continuation.
- [ ] Verify expired links, missing artifact, wrong platform, update available,
  anonymous download and safe retry.

Acceptance: every bot platform button returns a current usable artifact or an
honest supported alternative, never an old/wrong binary or a false store claim.

### 12. Packaging And Direct Distribution — `IN_PROGRESS`

- [x] `PASS_EXACT_CANDIDATE` Version is `1.0.4+13`; published prerelease tag is
  `v1.0.4-beta.1`.
- [x] `PASS_EXACT_CANDIDATE` Production-signed Android split APKs are public:
  `arm64-v8a` primary, `armeabi-v7a` legacy, `x86_64` emulator and universal
  fallback.
- [x] `PASS_EXACT_CANDIDATE` Signature, version, package, non-debuggable state,
  ABI contents, install identity, exact installed-file SHA-256, launch and
  ordinary tunnel cycles were verified on Huawei.
- [x] `PASS_EXACT_CANDIDATE` Windows x64 setup, portable ZIP, manifest and hashes
  were built and published.
- [ ] Test Windows shared UX paths beyond the exact launch/UI smoke: connection, locations,
  routing/WARP support, account/trial and checkout continuation.
- [x] Preserve honest unsigned/SmartScreen wording until trusted Windows signing
  is actually available.
- [x] `PASS_PRODUCTION_ROUTE` Website/bot/client delivery metadata recommends
  ARM64 and exposes platform/ABI choices. Live runtime sync, backend/static
  deploy and brain-origin signed-session readback all return `v1.0.4-beta.1` links.
- [x] `PASS_EXACT_CANDIDATE` Exact published Windows setup SHA-256 is
  `AD93F7F307552210BE4A8E6263382D4D221E993D8D743CEB6809D774DA007095`;
  portable ZIP SHA-256 is
  `E25A3E7CAF900D8B8DFE14A4AE58DCDB40B3EBC61B2C631916E7F3BD42B28ADD`.
  It remains an explicitly unsigned outside-store beta.

Acceptance: direct users download the smallest correct artifact by default;
every public file matches the exact tested candidate and published hash.

### 13. Exact-Candidate QA — `IN_PROGRESS`

- [ ] LDPlayer: clean install/update, every screen, trial and canonical paid UI,
  bonuses, banner, checkout continuation, support and API error states. Do not
  claim tunnel-core proof from LDPlayer.
- [x] `PASS_EXACT_CANDIDATE_PARTIAL` `beta.2` update-install, installed-file
  SHA-256 equality, centered Home/busy motion, premium state, locations and
  flags, per-app policy, native AI response, bonus first-load, roulette/history
  and profile-state restore pass in LDPlayer. Banner/checkout/error-state and
  exhaustive every-screen coverage remain open; tunnel/core is not claimed.
- [ ] Huawei: clean install/update, permissions, onboarding, all screens,
  connect cycles, auto/manual locations, WARP, all routing modes, per-app,
  tile/notification, background/lock/kill/reboot/battery saver and
  Wi-Fi -> LTE -> Wi-Fi.
- [ ] Browser traffic checks: direct RU and tunneled non-RU, DNS/country and
  split-routing behavior without retaining raw IP.
- [ ] Capture performance, crash and foreground-service evidence.
- [ ] Check fresh node metrics and reject stale/loadless production status.

Acceptance: exact-candidate evidence records each gate as PASS, MANUAL, SKIPPED
or BLOCKED. Prior versions and partial operator attestations cannot prove the
new candidate.

### 14. Data Cleanup, Signing Recovery And Production Safety — `IN_PROGRESS`

- [x] `PASS_PRODUCTION_ROUTE` Fresh encrypted PostgreSQL backup and destructive
  restore rehearsal passed for all 89 tables; the rehearsal database and
  encrypted retained archive are outside Git.
- [ ] Identify QA users by retained test evidence; delete only explicitly
  authorized QA users/keys/tickets/sessions/orphans after backup and exact target
  review.
- [x] Inspect dirty/untracked artifacts in both repositories. Important source,
  exact-candidate evidence and release artifacts were retained; duplicate QA
  screenshots, disposable build output and incomplete LFS transfers were
  removed only after exact-path review.
- [x] Validate no secrets, raw tokens, private keys, customer data or provider
  payloads enter commits/releases/evidence. Exact added-line and release-asset
  scans passed before commit/publication.
- [x] `DONE_LOCAL` Production Android keystore and password recovery material are
  protected locally with DPAPI.
- [ ] Create an encrypted offline recovery copy on owner-provided removable
  media. This remains `MANUAL_OWNER_TEST` until that media exists.
- [x] Prepare rollback for platform, client metadata and published assets; prior
  public release metadata and Git history remain retained.

Acceptance: backups and rollback precede destructive production work; cleanup is
targeted and auditable; signing recovery exists without exposing the key.

### 15. Verification, Deploy, Git And Release — `PASS_EXACT_CANDIDATE`

- [x] Backend focused tests for changed account, rewards, referral, promo,
  support, download and admin contracts.
- [x] `DONE_LOCAL` Flutter analyze and focused/full tests for shared app shell,
  runtime engine, Android and Windows hosts.
- [x] Android JVM/Gradle tests and split release builds.
- [x] Windows release build/package smoke.
- [x] Marketing, cabinet and admin production builds pass. The changed marketing
  guide slice also passes lint, SEO and responsive checks; Chrome production
  mobile QA covers guide search, atlas deeplink and install entry.
- [x] Documentation link/contract checks and `git diff --check` pass; exact
  release files pass SHA256SUMS and GitHub digest verification. Changed-file
  secret scans found no private key, OpenRouter/GitHub/Telegram token or bearer
  credential pattern.
- [x] Review canonical docs and this tracker against implemented behavior.
- [x] Deploy platform only after backups and scoped production preflight.
- [x] Run deployed current-origin and brain-origin checks; run RU-origin
  independently when access exists.
- [x] Stage only authorized files, self-review both diffs, commit and push both
  working branches. Platform candidate `d364230` and client final handoff
  `e172d4b` are pushed.
- [x] Promote through platform `master` and client `main` with the owner's
  explicit release authorization; both promotions were fast-forward only.
- [x] Publish exact Android/Windows assets and verify anonymous downloads match
  size and SHA-256.
- [x] Produce final release handoff with commits, URLs, hashes, backups, deployed
  version, PASS/MANUAL/BLOCKED matrix and remaining risks.

## Current Local Evidence

- The long-session compaction audit is retained in the requirement ledger above;
  rewards, AI, selected Home, remote advertising, admin identity, bot/platform
  downloads, campaign entry points and dirty-tree cleanup all remain explicit
  release work rather than chat-only notes.
- The post-compaction reconciliation also retains the exact paid QA account
  correction, both roulette grants, the new in-modal reward reveal, the localized
  reward timestamp, exact DeepSeek model routing, Quick Settings diagnosis, final
  Android/Windows rebuild requirement and QA-account cleanup after evidence.
- POKROV Core `v1.0.3` is a clean, reproducible, tagged and public release at
  commit `69a74545101708e56183c92e31f2b4c7b2509884`. Full Core tests and focused
  Cloudflare/WARP/daemon/libbox/WireGuard packages pass. Published artifact
  identities: Android AAR `6E6F3B688FE415C9392E19AA4F8660885316897CFC369CF8C3FF3D01100EE14F`
  (`106861671` bytes), Windows DLL
  `7CC83854FC4022B759E9DE3D0942B90A24C859CFD51E3231D04E7C7A6B7D5054`
  (`55134208` bytes), and `libcronet.dll`
  `8EF1F8BBDE77F954AF1AE47BEE1819AC8DC2354BB0E1D4BABA3DAD9E58D7A6F7`
  (`8596992` bytes). GitHub release:
  `https://github.com/Kiwunaka/pokrov-core/releases/tag/v1.0.3`.
- The client runtime manifest now pins those exact `v1.0.3` artifacts and the
  Android/Windows bundles contain the synced published binaries. Seed and docs
  contracts pass. The exact Windows DLL also passes the real 100-cycle
  start/stop runtime backtest.
- The canonical client command `scripts/run-tests.ps1 -OfflinePubGet` passes for
  the current workspace: all Flutter packages plus Android Gradle/JVM tests;
  Gradle finished `BUILD SUCCESSFUL` with 137 tasks. Five stale UI assertions
  were corrected to the selected centered Home and current explanatory-copy
  contract; focused reruns pass as well.
- Support knowledge preflight caught a real fail-closed startup issue before
  deploy: the expanded 65-topic index was 8,275 characters against an old 8,000
  character local-only ceiling. The bounded ceiling is now 10,000; the global
  index is not sent to the provider. Knowledge/grounding/context/safety/provider/
  harness/service regression: `206 passed` under the repository `.venv`.
- Deterministic WARP help now retains paragraphs and numbered steps on the phone
  instead of flattening them into one wall. Focused Flutter assistant-sheet test
  `PASS`; `flutter analyze lib/app_shell.dart` reports no issues.
- Backend Python compilation for the current reward changes: `DONE_LOCAL`.
- Complete reward backend matrix under the repository `.venv` with test temp on
  `E:`: `132 passed in 117.64s`. It covers reward services, Telegram channel
  bonus, trial/paid/legacy referral economy, migrations and rollout preset.
- The post-Core release reward recheck passes `82 + 43` focused reward tests;
  support/DeepSeek grounding, harness, provider and knowledge pass `92` tests.
  The broader API matrix exposed and fixed an atomicity defect where channel
  points used a second database session: a failed outer commit could retain the
  channel-claim marker on SQLite. Points and the five-day entitlement now share
  the request transaction, and SQLite explicitly owns the SAVEPOINT inside the
  outer transaction. Ordered/single failure regressions pass, and the complete
  auth/ticket file now passes `93` tests plus `8` subtests.
- Compact Flutter Rewards Hub test `profile loads compact bonus summary with
  reward preview`: `PASS`. It confirms the current sheet omits the retired
  Activity/quest filler and referral `Активировано` counter while retaining
  wheel, Telegram, referral conversion/history and achievement surfaces.
- Production-backed LDPlayer paid-account QA now passes the premium entitlement
  and reward path. Two controlled spins returned `+1 day`; the second showed the
  new in-modal animated reward card and live-region semantics. The raw ISO
  timestamp is fixed locally. The exposed seven-day cooldown was traced to the
  persisted production `paid_weekly_v1` configuration, migrated to the approved
  14-day preset, and verified through exact API/UI readback showing `27.08`.
- The old bot friend-gift/direct referral mutations are fail-closed; current bot
  and public copy now state the standard five-day friend trial and referrer
  `+10 days` only after the first payment survives the 72-hour hold.
- Fresh production-signed x86_64 LDPlayer QA exposed that the currently deployed
  API still returns the retired referral value `+15 days` and omits the new
  `reward_access` contract. The post-fix client now uses the trial subscription
  lane as a fail-closed compatibility gate: the Telegram claim is absent, one
  paid notice is visible and the channel action is clearly labelled. Retained
  screenshot and UI tree: `docs/audit-artifacts/2026-08-13-direct-release/android-rewards-trial-compact.*`.
- The later paid-account Rewards Hub pass confirms the production service now
  exposes the approved `+10 days` rule and 14-day roulette cooldown, but also
  found that this account had no provisioned referral link. The local backend
  and client fixes above are retained for deploy/readback; pre-fix screenshot
  `E:/POKROV-ops-evidence/2026-08-13-goal-continuation/ldplayer-app-audit/42-rewards-paid.png`
  contains no account identifier or raw credential.
- Fresh support evidence in the same directory records the simplified support
  menu, the real bonus/trial assistant exchange, compact structured reply and
  expanded-details state as `29-support-fixed.png`, `31-ai-sheet.png`,
  `35-ai-compact.png`, and `36-ai-details.png`.
- Final local regression for the referral/support slice passes `169/169`
  backend app-first/reward/referral/migration/rollout tests and `146/146`
  combined Flutter design/app-shell tests. `flutter analyze`, Python compilation
  and both repository `git diff --check` checks pass. The intentionally broader
  backend router matrix exceeded its 10-minute local limit without a retained
  result, so it is not counted as a pass.
- Backend deploy retained rollback snapshot
  `/root/portal_bot.deploy-backups/20260813T144318Z-18128`; Caddy, API, bot,
  helpbot, feedbackbot and worker are active. Brain-origin verification passed
  health/static checks and three subscription fetches (`7` hosts, `27`
  outbounds each).
- Final production-signed Android `1.0.3+11` local artifacts: universal
  `20B69DBA14D74F0E55B07DEFF07929EED63084C347A949E339FEBF52B043DBE6`,
  ARM64 `CED2219E0A387EB671F321139E25BAEE731621591567A5CB6232CF45EB1CA939`,
  ARMv7 `194B62856F8A5EEBB55C3A3EEB20AFBCEDAC4F2671E5369A0C5C0F2701AFA04B`,
  x86_64 `C03B451B0A2DBC3D420A76372AC72BD211E821F2D3CDA3AC9BE5E731DDCDAD13`;
  certificate SHA-256 remains
  `0A0602A7DF5D96A0B427909D004F3DDF26DEF86587634BF16694DA8D654B2500`.
  The exact x86_64 artifact update-installed in LDPlayer and retained the paid
  session. Evidence `49-profile-no-code.*` and `50-rewards-final.*` proves the
  compact Profile omits the code while Rewards exposes the two live link
  actions. XML containing an earlier raw referral code was deleted; no retained
  XML evidence contains it. This same-version local build is not published over
  public `v1.0.3-beta.2`.
- Current post-reward-fix Android local candidate passed production signing,
  package/version, non-debuggable and ABI verification. SHA-256: universal
  `04455331DA42AFBCE95EF50A26726FC63324A39FCD225991494C271AAFC73A2E`,
  ARM64 `2196E19E7EA64F7066FBCAC3BC18CDC147ACF34A74C206F29FFD9E414063DC43`,
  ARMv7 `A45C378860975B73C552FE32A317180991D1F4E39C9800653112F6806B9DDB4D`,
  x86_64 `24612B18EDC33EE5178821E67EDC2E8B15568E23EE74F1721CCB27C0790B72FF`;
  signer certificate remains
  `0A0602A7DF5D96A0B427909D004F3DDF26DEF86587634BF16694DA8D654B2500`.
- Broader API tests under the global Python environment are blocked before test
  collection by a local FastAPI/Starlette version mismatch. Re-run using the
  repository `.venv` before judging behavior.
- `packages/app_shell` Flutter analyze after the reward/profile/routing slice:
  `DONE_LOCAL`, no issues found.
- Primary `adminapp` remote-campaign editor: targeted ESLint `PASS`; production
  `next build` `PASS` with all 17 static routes generated.
- Fresh production builds after the transactional fix pass for marketing (32
  static routes), web cabinet/admin fallback (40 routes), and primary admin (17
  routes). Public link checks pass; docs/copy/client-security contracts pass
  `46` tests; `git diff --check` passes in platform and client repositories.
- Focused Flutter Home checks: compact premium hierarchy, single connect action,
  checkout continuation, remote campaign dismissal and unsafe CTA handling
  `PASS`. Persisted dismissal lookup now fails open after 400 ms instead of
  leaving the banner invisibly blocked by slow local storage.
- Focused promo-slot API check under the repository `.venv`: `1 passed`; Python
  compilation and `shared/promo-slots.json` parse also passed.
- Recovered 49.75 GB in the first pass by removing 871 incomplete Git LFS temp
  files. A later full-disk recurrence was traced to 1,482 incomplete transfers
  occupying 68.14 GiB in the same resolved client `.git/lfs/tmp` directory. The
  directory was confirmed inside `.git/lfs`, no Git LFS process was active, only
  that temporary directory was cleared and recreated, and `C:` recovered about
  70.45 GiB free. Source, tracked LFS objects and release artifacts were retained.
- A third recurrence came from repeated Git status polling of the two modified
  large LFS runtime binaries and left 1,602 incomplete temporary files
  (`76,769,532,110` bytes). After the same resolved-path and no-active-LFS-process
  checks, only those temporary files were deleted. The exact published Core
  `v1.0.3` AAR and Windows DLL hashes were rechecked and those two intended LFS
  changes were staged, preventing further clean-filter polling while preserving
  source and release evidence; `C:` recovered about 76.77 GB.
- A later full `C:` condition zeroed the large Flutter shell test during a write.
  It was reconstructed from Git plus the retained Codex session patch journal;
  `dart analyze packages/app_shell/test/pokrov_seed_app_test.dart` and the
  focused Rewards Hub test now pass. Interim signed APKs were copied to
  `E:/CodexReleaseBackup/POKROV-pre-final-20260813-0516/` before `flutter clean`.
  An old 4.77 GB temporary client worktree was preserved, not deleted, under
  `E:/CodexTempArchive/`; Gradle caches were moved reversibly to `E:` behind a
  junction, leaving more than 20 GB free on `C:`.
- Production-signed pre-freeze Android artifacts for the current source passed
  the build script's package/version/debuggable/signature/ABI checks. SHA-256:
  universal `1C7EDBC503CB0F365D05EEA553F35C9D754E85D1509A225D6F95817F18802F63`,
  ARM64 `2B9AFAC659E1035B82BFE41909AD216B1AF96028EFA52D5E5D0ACC6B5AB623F6`,
  ARMv7 `F03AF51B6976B6EC3BACC217ED41D3858B9761DE7DC330760BF68E0306557C22`,
  x86_64 `5BB472E43A63CEF5960E565D7C60E5627BCAC8460185BA49D75AC5741A577561`;
  certificate SHA-256
  `0A0602A7DF5D96A0B427909D004F3DDF26DEF86587634BF16694DA8D654B2500`.
- LDPlayer 14 is Android 14 at `1080x1920`, 480 dpi. The current production-signed
  x86_64 APK passed update install and launch. The final Home has one centered
  action, complete quick-control labels and an untruncated `Премиум · 5 дней`
  checkout pill. Retained screenshot, combined reference comparison and signing
  manifests are under `docs/audit-artifacts/2026-08-13-direct-release/`.
- A clean LDPlayer app session proved fresh five-day onboarding, pre-connect
  country/city loading, manual Frankfurt selection, location refresh and Chrome
  selection. It also exposed the pre-fix trial-as-premium label, truncated
  metrics/app metadata and the AI client timeout above. LDPlayer's `1-6 ms`
  readings and failed Core start are explicitly not geography or tunnel proof.
- Focused post-fix client checks pass for the assistant's single long request,
  narrow location layout, compact metrics, paid/trial Home labels, native app
  catalog/icon rendering, advanced-route disclosure and the AI-first support
  entry. `flutter analyze lib/app_shell.dart` and Android
  `:app:compileDebugKotlin` pass.
- The physical phone is currently unavailable; all physical-client gates remain
  pending until it is returned.
- Exact release Android build `1.0.3+11` is production-signed with certificate
  SHA-256 `0A0602A7DF5D96A0B427909D004F3DDF26DEF86587634BF16694DA8D654B2500`.
  Published SHA-256 values are ARM64
  `1FDA394624ACB2DAD59A629DF23A5D92F621FD75C346EFB81B31AAA4745CEDF6`,
  ARMv7 `58919AF2820A649200086116687754FCA20ECB44AD69F9C8C511FD9299AA69D4`,
  x86_64 `F993DAEAEEBB01049E11FFC8E4CD93BA9B41873F417FBC70F7A61391A9C8D52E`
  and universal
  `6A8803001F2517F26FB2B28EF3CD9AEE949B93581F7978B6D8FDD02C48F851B9`.
- Exact Windows setup SHA-256 is
  `7EE28D1FF058E3E09FEF05EDB496E6C44B2783235FFB1A4C25A3925E523CF70A`;
  portable ZIP is
  `66D2081D1674C96F3E9F24EDE4CB3F0909397C49C3CD167FE00241141A97B7A8`.
  Both remain unsigned beta artifacts with mandatory SmartScreen copy.
- Public GitHub prerelease `v1.0.3-beta.2` contains four Android APKs, Windows
  setup, portable ZIP, manifest, checksums and release handoff. A fresh
  anonymous full download of all nine assets matched exact size and SHA-256.
- Client source/release commits `78ab9f394a7581cf0f1a0c22fe448bbe1e94b089`
  and `cdb8a755a471bcfc167b3c0d81ef491182b3a16c` are pushed to
  `codex/product-readiness-20260804`; production-sync metadata commit
  `521b6bf` is pushed on the same branch.
- The final Quick Gate rerun produced valid production builds for marketing,
  WebApp and AdminApp. Its app-shell failures were six leaked picker timeout
  timers; native installed-app/process discovery is now lazy and the complete
  118-test file passes. API lifecycle passes in the repository `.venv` after
  applying the project Starlette constraint. The owner-selected Chrome browser
  now also passes production mobile guide search, atlas deeplink and install
  entry QA without horizontal overflow.
- Disk cleanup moved client release artifacts, Core distributions, generated
  images, frontend outputs, build directories, dependency caches, project
  venv, Pub cache and the client Git LFS store to `E:`. Stable paths on `C:` use
  junctions. Only reproducible outputs and `89,916,381,184` bytes of incomplete
  LFS temporary transfers were deleted. `C:` increased from approximately
  `0.10 GB` to `94.23 GB` free; Git source, history, tracked LFS objects,
  signing material and exact-candidate evidence were retained.
- The remaining tracked client release archive (`artifacts/releases/pokrov-app`,
  about 2 GB including history) is now physically on `E:` behind a verified
  junction at its stable repository path. Android/Windows build trees remain on
  `E:` as well; current `C:` free space stayed above 90 GB during the `beta.2`
  rebuild and publication.
- A follow-up workspace sweep moved the 9.3 GB Android SDK, global Gradle home,
  video-ad/OpenCode dependency trees and future npm/Pub caches to `E:` while
  preserving stable paths through junctions. It also removed 133 stale
  POKROV/Flutter/Kotlin temp trees and reproducible project caches from `C:` into
  the recoverable `E:/POKROV-trash-staging/2026-08-13/` quarantine. Free space
  increased from 93.83 GB to 106.41 GB. `adb`, `sdkmanager`, Gradle and Flutter
  pass after the move. The three Next dependency trees remain local because the
  proven cross-drive Next/Turbopack failure makes them a build-critical
  exception; their local Next binaries pass after restoration.
- The retained legacy Hiddify client reference is now on `E:` behind a verified
  junction; its ignored April `out`, `dist` and `.gradle` outputs were removed.
  Marketing static output remains reproducible and was deleted after deploy.
  Next/Turbopack rejects `.next` or `node_modules` junctions outside its
  filesystem root; Webpack also fails when the dependency junction crosses
  drives. The three required Next dependency trees therefore stay local on
  `C:` as the only build-critical exception. Reproducible `.next`/`out` output
  is deleted after each production deploy; Android/Windows/Core/LFS/release
  archives and other genuinely heavy material remain on `E:`.
- Post-cleanup verification passed against the junctioned environment: client
  Git resolves its LFS object and temp directories on `E:`, platform lifecycle
  smoke is `1/1`, the P0/client sequence is `27/27`, the paywall sequence is
  `90/91` plus 12 subtests with its sole stale roulette assertion then fixed and
  rechecked `1/1`, API composition-root helpers survive `20/20` repeated imports,
  docs contract is `26/26`, link check and `git diff --check` pass. The selected
  changed-file secret scan found no private key, OpenRouter key, Telegram bot
  token or bearer token; remaining generic matches are explicit redaction and
  fake-secret test fixtures. Retained visual/signing evidence totals only
  `3,633,026` bytes and is not a discarded build cache.
- Platform commit `48709207def5d34515db6ed52a7805072d5dd5f5` and client
  runtime-metadata commit `cef44149dab283f5c9d5a28774b077b07417a612`
  are pushed. Production release handoff sync, backend deploy, static deploy and
  post-deploy verification pass; Caddy plus portal API/bot/helpbot/feedbackbot/
  worker are active and the backend rollback snapshot is retained. Live public
  pricing is exactly `99/239/669/1199/1699/1999 RUB`, `/install` contains the
  exact ARM64 and Windows setup links, and the refreshed public GitHub handoff
  SHA-256 matches the client-owned file.
- `beta.2` runtime handoff and backend/static redeploy pass. Brain release
  snapshot `/root/portal_bot.deploy-backups/20260813T123454Z-34940` is retained;
  static release `20260813124114` is live. Caddy, API, bot, helpbot,
  feedbackbot and worker are active. Brain-origin signed-session smoke returns
  the exact split APK and Windows setup URLs/hashes, and a no-credential full
  download of every public asset matches `SHA256SUMS.txt`. The final public
  production-sync handoff is `8775` bytes with GitHub digest
  `84417b6630543faf589a5d2c3a61a870224d8626e8601ece0a2e60e46ee05caa`.
- Production checkout static deploy `20260813131024` fixes the mobile
  validation scroll trap. Current in-app-browser evidence at `390x844` proves
  the selected-plan picker, all six public prices, 12-month summary,
  disclosures, empty-email recovery, error semantics and zero horizontal
  overflow without creating an order or starting a payment.
- Dark/large-text local signed Android validation uses certificate SHA-256
  `0A0602A7DF5D96A0B427909D004F3DDF26DEF86587634BF16694DA8D654B2500`;
  the latest x86_64 APK SHA-256 is
  `8815298C3A3F7F2FB26AD5BA9D0E6417264502A0D6D53138B826AB6F378782CF`.
  The combined design/app-shell suite passes `145/145`; Flutter analyze and
  seed validation pass. Fresh LDPlayer evidence under
  `E:/POKROV-ops-evidence/2026-08-13-goal-continuation/ldplayer-app-audit/`
  records dark Home and the `1.3x` Locations/Profile/Support before/after
  states. This same-version local build is not published over `beta.2`.
- Static release `20260813134637` deploys the aligned dark muted token to
  marketing/WebApp/admin. All three production builds and lint pass; brain
  verification passes three subscription fetches and reports Caddy, API, bot,
  helpbot, feedbackbot and worker active. All six local `.next`/`out` trees and
  three obsolete `E:` static-output copies were then deleted as reproducible
  artifacts. The required Next dependency exception leaves `C:` with about
  about `94 GB` free.
- Platform task-first guide source commit
  `d7929a221c03f3ca1c377f83ae3eb4be4d7c4115` and client production-sync
  metadata commit `521b6bff009cac51b94f3fe62cfe396fc732b6e9` are pushed.
- Post-backup production account cleanup was fail-closed. The one install with
  an explicit Codex QA marker is already linked to an identity and therefore is
  not eligible for guarded test-user deletion; the owner-linked support/Huawei
  profile is also retained. The inactive-user audit reports `safe_garbage_total
  = 0`, so no production account or related data was deleted and no guard was
  bypassed.
- Fresh source-newer Windows evidence under
  `E:/POKROV-ops-evidence/2026-08-13-goal-continuation/windows-app-audit/`
  records the old trial Home with the dead Telegram reward card, the rebuilt
  Home without that card, and the current trial Profile. The first packaging
  attempt correctly failed because the inspected app was still resident in the
  tray and held a plugin DLL; after stopping that exact local process, packaging
  succeeded. This does not upgrade the unsigned setup or untested Windows
  tunnel paths to release passes.

## 1.0.4 Beta.1 Owner-accepted Goal Closure

- Public prerelease: `https://github.com/Kiwunaka/pokrov/releases/tag/v1.0.4-beta.1`.
  All four Android APKs, Windows setup, portable ZIP, manifest and checksum
  asset are public. Anonymous full downloads match exact size and SHA-256.
- Android primary ARM64 SHA-256:
  `48EAC0BE655D4D85D31134908E7A8CAEC881ED91AAE049FB7CF72206EFD99E6C`.
  Universal fallback SHA-256:
  `7B7688185D03ED3E54A7D1EE0B15D774F97AD66C25C221135B895421146068B9`.
  Every APK uses the production certificate SHA-256
  `0A0602A7DF5D96A0B427909D004F3DDF26DEF86587634BF16694DA8D654B2500`.
- Windows setup SHA-256:
  `AD93F7F307552210BE4A8E6263382D4D221E993D8D743CEB6809D774DA007095`;
  portable ZIP SHA-256:
  `E25A3E7CAF900D8B8DFE14A4AE58DCDB40B3EBC61B2C631916E7F3BD42B28ADD`.
  Trusted Windows signing remains an accepted beta limitation, not a pass.
- Exact platform full release gate generated at `2026-08-14 00:40:39` is
  `PASS`: backend/API matrix, auth/admin regression, client security/Flutter,
  lifecycle/link/UI smoke, three production web builds and Playwright E2E all
  exited zero.
- Production release-handoff sync, backend deploy, static deploy and five-pass
  post-deploy verification succeeded. Caddy, API, bot, helpbot, feedbackbot and
  worker are active. A brain-origin synthetic signed session returned the exact
  `1.0.4` Android variants and Windows setup metadata. This is not relabelled as
  a real Telegram-user WebApp button test.
- Platform release commit `d364230` is pushed to the feature branch and
  fast-forwarded to `master`. Client source/artifact/publication/runtime-cutover
  commits culminate in `e172d4b`, pushed to the feature branch and
  fast-forwarded to `main`. Annotated tag `v1.0.4-beta.1` identifies the staged
  artifact candidate.
- Exact-final Huawei evidence proves installed ARM64 identity, centered Home,
  variant-sheet fit/persistence, useful live AI recovery, notification actions
  and three ordinary tunnel stop/start cycles. Same-version supporting evidence
  before final Flutter-only UI edits proves WARP, per-app reverse routing,
  Quick Settings and Wi-Fi/LTE continuity; exact-final repetition stays
  `MANUAL_OWNER_TEST`.
- On 2026-08-14 the owner accepted the direct Android+Windows release goal as
  complete on the published `v1.0.4-beta.1` prerelease and production cutover.
  This is an owner scope/acceptance decision, not a fabricated runtime `PASS`
  for checks that were not executed.
- The remaining stronger-claim gates were moved intact to
  `docs/developer/work-orders/2026-08-14--postrelease-manual-proof/`: Huawei
  endurance and exact-final WARP/per-app/lifecycle, Wi-Fi/LTE continuity,
  isolated Windows TUN/DNS, a real Telegram-user journey, an independent
  RU-origin probe and encrypted keystore recovery on external owner media.
  Until run, each stays `MANUAL_OWNER_TEST` in that follow-up.

## Canonical Owners And Evidence Pointers

- Product: `docs/product/portal-vpn-product.md`
- Identity/reward/API flow: `docs/architecture/app-first-and-bonus-flows.md`
- Payment: `docs/product/payment-and-access-key-contract.md`
- Public delivery: `docs/architecture/client-downloads-flow.md`
- Deployment/signing: `docs/operations/deployment-and-access.md` and
  `docs/operations/publishing-and-signing-guide.md`
- Platform release runbook: `docs/operations/public-beta-release-runbook.md`
- Client product: `C:/Users/kiwun/Documents/ai/POKROV-app/docs/product/client-product-contract.md`
- Client design: `C:/Users/kiwun/Documents/ai/POKROV-app/docs/design/2026-06-13-pokrov-product-ui-direction.md`
- Client execution: `C:/Users/kiwun/Documents/ai/POKROV-app/docs/implementation/client-release-backlog.md`
- Android evidence: `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/android-release-audit.md`
- Windows evidence: `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/windows-release-readiness.md`
- Exact new candidate evidence: create a dated directory under
  `docs/audit-artifacts/` and client-local evidence as required; never overwrite
  evidence from `1.0.2+9` or another prior artifact.
