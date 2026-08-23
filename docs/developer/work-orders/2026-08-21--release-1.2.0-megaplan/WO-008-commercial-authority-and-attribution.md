# WO-008 — Commercial Authority And Revenue Attribution

Status: `COMPLETE_LOCAL_I2`
Classification: `ACTIVE_EXECUTION`
Phase: `06`
Lane: platform backend/shared contracts/marketing/webapp first; active-client
consumer only after the server contract is frozen
Depends on: `WO-007`
Production/external actions: `NOT_AUTHORIZED`

## Outcome

Build one server-authoritative commercial path for product facts, offer
preview, signed price holds, atomic quota/order binding and first-party
campaign attribution. Marketing, cabinet, bot, payment and structured-data
consumers must agree on one `commercial_revision`; stale, expired, legally
blocked or capacity-blocked offers fail closed.

This WO implements repository and local-candidate controls. It does not publish
seller details, make a legal determination, launch a campaign, spend money,
enable a provider, purge production CDN, deploy, or claim production readback.

## Authority and collision decisions

- `shared/product-facts.json` owns stable product/legal paths and
  `shared/tariff-catalog.json` owns the base tariff catalog. A generated
  commercial manifest binds both through one revision/digest; frontend code
  cannot own promo prices.
- Existing `Offer`/`offers_service.py` is a legacy account-bound Telegram Stars
  one-time-offer mechanism. It is not renamed or repurposed in this WO.
- Existing `IncentiveCampaign` remains the single mutable campaign root.
  Commercial fields are added compatibly; no parallel `marketing_campaigns`
  truth is created.
- Campaign offers, creatives, assignments, reservations and conversions are
  child records of that campaign root. Payment orders remain the money truth;
  commercial conversion rows are projections/lineage and cannot grant access.
- `ExternalOrder` captures the accepted offer/campaign lineage and the exact
  commercial revision in its immutable order intent. Callback payloads cannot
  add or repair those fields.
- Capacity policy is server-owned and defaults fail closed for acquisition.
  Renewals and existing entitlement recovery remain exempt from acquisition
  pause. Live capacity and production auto-pause proof stay separate.
- Legal/channel decisions are data gates, not inferred law. An absent seller,
  offer terms revision, legal profile approval, or allowed channel blocks
  campaign activation/preview. An owner-approved legal record is required for
  any later external launch.

## Current baseline

- shared base tariff facts exist, but no commercial revision/effective/terms or
  capacity-cost contract is frozen;
- frontend checkout still contains a static promo-code preview table;
- backend pricing is stronger than frontend preview but has no signed offer
  token or reservation/quota owner;
- acquisition sessions retain coarse first/last touch, while payment orders
  retain only a campaign string and cannot prove creative/variant/assignment;
- existing campaign CRUD is guarded by action intents but represents only
  promo/gift targeting and does not enforce legal, capacity, offer or revision
  gates;
- production/public version, CDN, provider, seller and legal evidence are not
  established by this repository state.

## Owned ledger rows

Primary Phase 06 rows:

- `REL/CONTRACT-001`;
- `FE/P12-011`, `P12-012`, `P12-013`, `P12-014`, `P12-024`, `P12-120`,
  `P12-129`, `P12-210`;
- `FE_PR/PR-05`;
- `MKT/MKT-100`, `MKT-200`, `MKT-400`, `MKT-600`;
- `FRKN_ADOPT/ADOPT-07`.

Supporting implementation may strengthen `MKT/MKT-000` and `MKT/MKT-300`,
but those rows cannot reach local completion until the legal/capacity WO owns
their full acceptance matrix. No row advances from this document alone.

## WO-008A — Commercial manifest and consumer gate

Deliver:

- versioned schema for commercial facts with `commercial_revision`,
  `effective_from`, `terms_revision`, seller/legal readiness state,
  `capacity_cost_units`, renewal policy and explicit base versus campaign
  savings;
- deterministic generated manifest/digest from shared product and tariff facts;
- TypeScript/Python adapters and generated reference documentation;
- consistency gate proving backend catalog, marketing, webapp, bot-facing
  projections and JSON-LD consume the same revision/base prices;
- `X-Pokrov-Commercial-Revision` on applicable API responses and an integer/
  string-only health projection, without claiming deployed HTML or CDN state;
- remove static frontend promo codes as commercial authority. A static catalog
  may remain only as a base-price/unavailable fallback.

Eligible rows after proof: `REL/CONTRACT-001`, `FE/P12-024`, `P12-129`,
`P12-210`, `MKT/MKT-600`, `FRKN_ADOPT/ADOPT-07`.

### 008A closure — `COMPLETE_LOCAL_I2`

Implemented for commercial revision `2026-08-21.1`, manifest SHA-256
`1d4b295a5ce9003345a2d32d8374852a144477659064fab8de8958be4f018f02`:

- deterministic generator, closed schema, generated JSON/reference document,
  Python/TypeScript adapters and stale-source digest rejection;
- explicit seller/offer/RF advertising blocked states, empty allowed-channel
  set, base/campaign saving split, manual renewal policy and 300-unit capacity
  policy with hysteresis;
- FastAPI startup validation, scalar health projection, revision response
  header and fail-closed `/api/public/catalog` plus `/api/public/plans` DB
  projection checks;
- marketing, JSON-LD, cabinet and Telegram bot base-price consumers bound to the
  manifest. Checkout remains disabled until server body/header revision matches;
  bundled plans are display-only fallback;
- removed the static frontend promo table and backend catalog-preview fallback.
  Promo input is retained and evaluated only by the server PromoCode/order path.

Evidence for the current local source:

- generator `--check`: `PASS`;
- contract/shared/marketing/UI/support-KB focused suite: `41 passed`;
- catalog/plans/health and CORS revision-header proof: `2 passed`;
- callback/order/outbox/action-intent/admin-payment regression:
  `127 passed`, `12 subtests passed`, `19 warnings`;
- marketing Webpack production build, SEO, responsive smoke and ESLint: `PASS`;
- webapp Webpack production build, export-path fix and ESLint: `PASS`;
- focused Ruff for the new generator/adapter/tests: `PASS`.

The normal Turbopack command was `BLOCKED_BY_LOCAL_DEPENDENCY_LAYOUT` because
this isolated worktree used temporary dependency junctions outside Turbopack's
configured root. Webpack production builds and responsive smoke passed; the
temporary junctions and launch override were removed. This is not deployment,
CDN, seller/legal, provider, capacity-runtime, public-readback or active-client
evidence. Eligible broad ledger rows advance only to `I2`; later 008B–008G work
and external/exact-candidate gates remain open.

## WO-008B — Campaign/legal/capacity policy root

Deliver:

- compatible `IncentiveCampaign` extension for stable public campaign ID,
  objective, lifecycle status, revision, legal profile, channel matrix,
  seller/terms binding, paid cap, capacity guard and kill/pause reason;
- focused campaign policy service with closed status/reason enums;
- fail-closed activation/readback: missing approval, terms, seller, channel,
  revision or permitted capacity band cannot become live;
- capacity policy baseline of 300 units with explicit bands and hysteresis;
  acquisition is blocked in forbidden bands while renewal/recovery is exempt;
- action-intent preview/confirm/audit remains the only admin mutation route;
  create/update/kill/readback are idempotent and revision-bound;
- no external legal conclusion or campaign launch is inferred.

Eligible support: implementation evidence for `MKT/MKT-000` and
`MKT/MKT-300`; final row index remains bounded by external/legal/runtime proof.

### 008B closure — `COMPLETE_LOCAL_I2`

Implemented on the existing `IncentiveCampaign` root without a parallel
campaign table:

- additive SQLite/PostgreSQL columns and stable server-assigned `cmp_*` public
  ID for objective, closed lifecycle, campaign/commercial revision,
  legal/channel/seller/terms bindings, finite paid cap/counter, capacity guard,
  band, policy-evaluation time and closed pause/kill reason;
- focused `commercial_campaign_policy.py` with closed objective, lifecycle,
  legal, channel, state and rejection vocabularies;
- policy revalidation at action-intent preview, confirm, admin readback and
  actual API/bot promo or gift lookup. A legacy `is_active` bit is no longer
  authority; additive migration deactivates unclassified rows without public
  IDs;
- exact commercial-revision/terms binding, owner-approved legal profile,
  manifest seller/offer/channel readiness, finite paid cap and current
  entitlement-capacity projection are required for `live`;
- distinct-account active/grace non-reversed entitlement projection, the
  manifest 300-unit bands, 70% pause/65% resume hysteresis, acquisition block
  and renewal/recovery exemption;
- guarded create/update/compatibility-delete-as-kill remain action-intent only.
  Exact replay is idempotent, update accepts `expected_revision`, confirm
  rechecks row/contract/capacity, and killed campaigns are immutable.

Local evidence for the current source:

- policy/enums/capacity/hysteresis/entitlement/migration tests: `6 passed`;
- admin create/update/kill replay, stale revision, blocked-live preview and
  readback plus bot/API/support regressions: `18 passed`;
- commercial/shared/admin action-policy/action-intent/route regression:
  `50 passed` after classifying the existing content-addressed audited
  promo-media upload as explicitly low-risk;
- focused Ruff for the new service/tests and Python compilation: `PASS`.

The manifest still declares seller, offer review and RF advertising blocked and
allows no launch channels. No campaign was launched, no legal conclusion was
made, no spend/provider/deploy occurred, and no deployed capacity/auto-pause or
public readback was proved. `MKT/MKT-000` and `MKT/MKT-300` therefore advance
only to `I2`. Live automation/forecast/readback remains in 008G; external legal
qualification and pilot execution remain in WO-011.

## WO-008C — Server-authoritative offer preview and signed hold

Deliver:

- focused commercial offer, creative, assignment and reservation models with
  one campaign parent;
- `POST /api/public/offers/preview` with closed valid/invalid reason codes,
  exact base/final price, benefit, server time, absolute end/hold deadlines,
  remaining quota lower bound, terms URL and commercial revision;
- HMAC-signed, versioned, short-lived offer token binding subject, plan,
  campaign/creative/variant/assignment/offer, price/currency, revision,
  reservation and deadlines;
- token contains no email, Telegram ID, account ID, install ID, checkout URL or
  provider secret; subject binding is an opaque server HMAC;
- promo input is always evaluated by the server. Expired, unknown, stale,
  non-stackable, audience-blocked, capacity-blocked and legal-blocked paths
  return stable reason codes and standard base price without a usable token;
- countdown is derived from absolute server deadlines; refresh, incognito,
  client-clock changes or offline cache cannot extend it.

Eligible rows after proof: `MKT/MKT-100`, `MKT/MKT-400`, `FE/P12-011`,
`P12-013`, `P12-014`.

### 008C closure — `COMPLETE_LOCAL_I2`

Implemented as additive children of the existing campaign root:

- `commercial_offers` binds stable `off_*` ID, plan, exact manifest base/final
  RUB price, currency, commercial/terms revision, stackability, finite global
  and per-subject paid caps, lifecycle and absolute schedule;
- `commercial_creatives` binds stable `crv_*` variant/content/channel identity;
  `commercial_assignments` binds stable `asg_*` identity to a dedicated subject
  campaign-scoped HMAC and an explicit eligible/blocked audience decision; every child carries
  the same `IncentiveCampaign` parent;
- `commercial_reservations` has one unique owner per assignment, stable `rsv_*`
  ID, exact price/revision snapshot, absolute offer/hold deadlines and closed
  held/bound/consumed/expired/released states. Refresh reuses the same hold;
  expiry or drift cannot mint a replacement reservation for that assignment;
- additive SQLite/PostgreSQL DDL creates all four tables, foreign keys, unique
  owners, checks and lookup indexes without renaming the legacy Telegram Stars
  `Offer` table;
- `POST /api/public/offers/preview` is a separate bounded route slice. It
  accepts only a valid checkout ticket, live unconsumed checkout acquisition
  handoff or valid Telegram init data as subject authority, applies a bounded
  server rate limit, returns no-store responses and never accepts a client
  price/discount/deadline/quota;
- the response carries exact base/final price and benefit, server time,
  absolute offer/hold deadlines, conservative remaining-quota lower bound,
  canonical terms URL, commercial revision and closed reason. Unknown,
  invalid, expired or depleted promo; stale price/revision/terms; non-stackable,
  legal, channel, capacity, audience, quota or reservation failure repeats the
  base price and emits no token;
- valid preview signs an exact-field `pokrov-commercial-offer-token-v1` with the
  dedicated `COMMERCIAL_OFFER_HMAC_SECRET`. It binds opaque subject HMAC, plan,
  campaign/revision, creative/variant, assignment, offer, price/currency,
  commercial/terms revision, reservation and integer deadlines. It contains no
  email, Telegram/account/install ID, checkout URL or provider secret; only its
  SHA-256 is persisted. TTL is bounded to 60–900 seconds.

Local evidence for the current source:

- offer model/migration/price/token/subject/deadline/block suite: `7 passed`;
- combined commercial, shared, API-route, exact payment callback/order and
  module regression: `132 passed`, `12 subtests passed`, `21 warnings` (existing
  Python/sqlite/httpx deprecations only);
- isolated API reload/temporary-DB regression: `82 passed`;
- focused Ruff and Python compilation: `PASS`.

The checked-in legal manifest still blocks seller/offer launch and allows no
channels, so no valid external offer is issued by current repository truth. The
token is not accepted by payment order creation yet; atomic revalidation, quota
consumption and immutable order binding remain 008D. Frontend adoption remains
008F. `MKT/MKT-100` and `MKT/MKT-400` therefore advance only to `I2`. The
preview supplies a backend prerequisite for `FE/P12-011`, `P12-013` and
`P12-014`, but those rows remain `I0`: no state-aware subscription UI,
payment-return state machine or order-side stale checkout revalidation was
implemented in 008C. No campaign, payment, provider, deploy, public readback or
production deadline behavior is claimed.

## WO-008D — Atomic reservation, order revalidation and quota

Deliver:

- payment order creation accepts an offer token but never trusts client price,
  discount, IDs or remaining quota;
- one DB transaction locks/revalidates campaign, offer, assignment,
  reservation, subject, revision, deadlines, legal/capacity policy and quota,
  then binds the reservation and immutable order intent;
- concurrent requests cannot exceed global/per-subject paid caps; exact retry
  returns the same binding, while drift/stale token/reused foreign reservation
  fails closed;
- provider I/O remains outside the transaction. Provider failure leaves a
  bounded reservation state that can expire/release without mutating order
  truth; authenticated payment consumes the same reservation once;
- callback cannot introduce attribution, and refund/chargeback cannot erase
  the original lineage.

Eligible rows after proof: `MKT/MKT-100`, `FE/P12-012`, `P12-013`, `P12-014`,
`FE_PR/PR-05`.

### 008D closure — `COMPLETE_LOCAL_I2`

Implemented at the existing local RUB order boundary:

- authenticated/public order schemas and retained FreeKassa wrappers accept an
  optional signed `offer_token`; no request field accepts authoritative price,
  discount, commercial IDs, deadline or remaining quota;
- focused `commercial_order_service.py` verifies the exact v1 token, derives
  only server-issued Telegram/acquisition subjects, locks campaign, offer,
  creative, assignment and reservation, and revalidates manifest price,
  commercial/terms/campaign revision, schedule, legal/channel/capacity policy
  and global/per-subject paid caps in the pre-provider transaction;
- first acceptance changes one reservation `held -> bound`, enforces one unique
  order owner and stores `pokrov-payment-order-intent-v2` with an exact
  identity-free `pokrov-commercial-order-lineage-v1`. Only token SHA-256 is
  retained; exact valid retry reuses the original order ID and immutable intent;
- serialized campaign locking plus bound/consumed quota accounting makes an
  oversubscribed second bind fail closed. Wrong subject/provider, hostile or
  expired token, foreign/missing lineage, stale price/revision/policy and intent
  drift stop before provider I/O;
- commercial retry, callback consume and failed-checkout cleanup take the
  campaign lock before the payment order/reservation locks. This deterministic
  order removes the retry-versus-callback PostgreSQL lock inversion; current
  local concurrency proof remains below live two-connection PostgreSQL proof;
- provider I/O remains outside the transaction. Provider failure stays
  non-fulfilling and bound until the absolute hold; due cleanup expires only
  rows with local bounded provider-checkout `error` evidence, not ready delayed
  callbacks, and never edits order truth;
- account and email/access-key paid fulfillment consume the same reservation in
  the durable entitlement transaction and increment campaign/offer/assignment
  paid counters once. Callback replay is idempotent; callbacks cannot introduce
  attribution. Refund/chargeback retains the consumed reservation and original
  order lineage.

Local evidence for the current source:

- offer/order/intent/model/migration/quota/retry/expiry/consume/refund focused
  suite: `24 passed`;
- exact endpoint -> fake provider -> callback -> replay -> refund integration:
  `1 passed`; adjacent direct-promo regression: `1 passed`;
- final payment/provider/callback/API/entitlement/outbox regression, including
  the exact commercial scenario: `154 passed`, `12 subtests passed`, `20
  warnings` (existing deprecations only);
- focused Ruff for the new/changed service, model, migration and focused tests,
  plus Python compilation: `PASS`.

The provider used by the exact scenario was a local fake. The checked-in legal
manifest remains launch-blocked, and no external offer, provider request,
payment, campaign, deploy or public readback occurred. `FE/P12-014` advances
`I0 -> I2` for server-side stale checkout revalidation. `MKT/MKT-100` remains
`I2` with stronger atomic redemption evidence. `FE/P12-012`, `P12-013` and
`FE_PR/PR-05` remain `I0` because provider-capability UI, payment-return state
machine and end-to-end checkout consumer work remain 008F. The distribution is
now 112 rows at `I3`, 20 at `I2`, 4 at `I1`, and 241 at `I0`; 136 of 377 rows
are at least `I1`. WO-008E is active next.

## WO-008E — Campaign-to-revenue lineage

Deliver:

- stable campaign/creative/variant/assignment/impression/click identifiers
  propagate through acquisition handoff, offer token, order, payment,
  entitlement, first verified connect, retention and reversal projections;
- commercial conversion rows are idempotent projections keyed by order and
  stage; they retain bounded IDs, amounts and timestamps but no raw identity,
  destinations, provider callback or entitlement secret;
- payment success/reversal updates projection in the same authoritative payment
  transaction or via its transactional outbox; telemetry is never payment
  truth;
- first-connect comes only from verified connection authority, not click or
  client success telemetry. D7/D30/renewal are server projections with named
  evidence windows;
- operator read model exposes gross/refund/net revenue, paid conversions, first
  connect and retention by campaign/revision/capacity unit with explicit
  freshness and no mutation side effects.

Eligible row after proof: `MKT/MKT-200`.

### 008E closure — `COMPLETE_LOCAL_I2`

Implemented without adding a second payment or campaign truth:

- offer/token and immutable order lineage advance to exact-field v2 by adding
  stable server-issued `imp_*` and `clk_*` IDs. Checkout acquisition handoffs
  own those IDs before preview; reservation, signed token, order intent and all
  later stages retain the same values. Historical 008C/008D v1 evidence remains
  a dated record of those phases, not the current contract;
- additive SQLite/PostgreSQL migrations create identity-free
  `commercial_conversions` plus unique provider/order/stage ownership and
  indexes. Rows retain bounded commercial IDs, revisions, integer RUB amounts,
  capacity-cost units, timestamps and bounded evidence references, but no
  subject/account/Telegram/email/device/node identity, offer token, callback
  body, checkout destination or entitlement secret;
- successful commercial reservation consume inserts/reuses `paid` inside the
  same durable payment/entitlement transaction. The existing deterministic
  campaign-before-order lock order is preserved. Refund/chargeback inserts or
  upgrades one `reversed` stage in its authoritative reversal transaction and
  keeps the paid row, reservation and immutable order lineage unchanged;
- `record_connection_evidence` projects only durable
  `observer_connection` authority. It may create/reuse
  `first_verified_connect`, D7 in `paid_at+[7d,14d)` and D30 in
  `paid_at+[30d,37d)` through the provider-payment grant. Client/funnel success,
  impression and click are never payment or verified-connect truth;
- a later account-owned provider-payment grant creates/reuses `renewal` on the
  later commercial order. Anonymous paid access remains attributable to paid
  order/reversal but cannot gain account retention or renewal without a durable
  account grant;
- the existing admin payment summary now embeds read-only
  `pokrov-commercial-attribution-read-model-v1`: gross/refund/net RUB,
  paid/first-connect/D7/D30/renewal and paid capacity units grouped by campaign,
  campaign/commercial revision and unit cost, with source authority and explicit
  freshness.

Local evidence for the current source:

- token/order/lineage/projection/migration/read-model focused suite:
  `28 passed`;
- combined commercial/economy/observer/admin/exact callback regression:
  `120 passed`, `2 warnings` (existing SQLite datetime deprecations only);
- exact endpoint -> fake provider -> paid callback/replay -> refund projection is
  included in that passing matrix;
- focused Ruff, Python compilation, docs/contracts and diff hygiene: `PASS`.

The checked-in legal manifest remains launch-blocked. No external offer,
provider request, payment, campaign, deploy, public/admin readback or production
observer flow occurred. Local SQLite proof does not replace PostgreSQL
two-connection concurrency, deployed freshness or exact-candidate evidence.
`MKT/MKT-200` advances `I0 -> I2`; it remains below I3/I4 until a candidate and
deployed, redacted campaign/payment/observer/readback chain are proved. The
distribution is now 112 rows at `I3`, 21 at `I2`, 4 at `I1`, and 240 at `I0`;
137 of 377 rows are at least `I1`. WO-008F is active next.

## WO-008F — Checkout and consumer integration

Deliver:

- marketing checkout fetches catalog/provider/offer preview in parallel where
  dependency order allows, always sends promo input to preview, renders only
  server price/reason/deadlines/terms and submits the signed token;
- cabinet payment return uses a closed state machine (`processing`, `paid`,
  `failed`, `cancelled`, `manual_review`, `expired`) and revalidates stale state
  server-side;
- provider capability mapping controls visible payment methods; unavailable
  combinations remain disabled with a reason;
- frontend removes duplicated price/promo facts and does not reset countdown or
  imply quota certainty from a cached value;
- generated commercial-contract documentation and consumer contract tests cover
  marketing, webapp and backend. Active-client adapter work is deferred until
  this server contract is frozen, then stays in the client repo.

Eligible rows after proof: `FE/P12-011..014`, `P12-120`, `P12-129`,
`P12-210`, `FE_PR/PR-05`.

### 008F closure — `COMPLETE_LOCAL_I2`

Implemented one backend-owned checkout/return contract without adding client
payment or price authority:

- `payment_return_service.py` issues and verifies exact-field, identity-free
  `pokrov-payment-return-token-v1` capabilities. The token binds provider,
  local order, `marketing`/`cabinet` surface and bounded issue/expiry only; it
  is read-only and cannot fulfill, reverse or mutate an order/reservation;
- public token-only `POST /api/payments/orders/status` is rate-limited,
  `no-store`, omits local order/identity and returns only `processing`, `paid`,
  `failed`, `cancelled`, `manual_review` or `expired`. Signature/shape/expiry,
  pending age and commercial hold are revalidated server-side on every read;
- the provider catalog owns ordered SBP/card capability rows. Both consumers
  keep unavailable methods disabled with the server reason, and order creation
  rejects a disabled method even if a client submits it directly;
- marketing and cabinet fetch independent initial inputs concurrently, always
  preview selected plan/promo on the server, render only returned final/base
  price, reason, deadlines and terms, and submit the signed offer token. A
  non-empty invalid promo blocks checkout;
- both consumers store the return capability in versioned `sessionStorage`
  before provider navigation. Success/failure redirect URLs contain only
  provider/surface hints; marketing `/success` and `/fail` return to checkout,
  which strips the query before polling and renders the closed server state;
- the marketing acquisition handoff now receives the runtime API base. A local
  override can no longer silently post to the canonical production API;
- canonical API/payment/product/reconciliation/deploy/module docs and static
  consumer contracts describe the same capability, return and server-price
  boundaries. The active Android/Windows adapter remains a later client-repo
  consumer after this contract freeze.

Local evidence for the current source:

- exact full payment callback/order matrix: `88 passed`, `12 subtests passed`,
  with `19` existing deprecation warnings only;
- commercial/offer/order/payment-return/route/marketing/cabinet combined matrix:
  `68 passed`; focused return/provider API slice: `16 passed`;
- module-slice contract: `3 passed`; focused Ruff and Python compilation:
  `PASS`;
- webapp lint and production build: `PASS` (`40` routes); marketing lint and
  production build: `PASS` (`35` routes, including `/success` and `/fail`);
- in-app browser proof used local HttpListener fixtures only after the runtime
  API-base fix: catalog/provider/offer rendered server values, card stayed
  disabled with its reason, promo `POKROV10` displayed server `215 ₽` from base
  `239 ₽`, hold/terms were server-derived, and a return hint was stripped before
  a safe missing-token support state. No purchase action was invoked.

The checked-in legal manifest remains launch-blocked. No external offer,
provider payment, campaign mutation, deploy, CDN purge, public/admin readback or
active-client device flow is claimed. Local SQLite and mock-browser proof does
not replace PostgreSQL concurrency, deployed provider redirect, exact-candidate
origin or device evidence. `FE/P12-011`, `P12-012`, `P12-013`, `P12-120` and
`FE_PR/PR-05` advance `I0 -> I2`; `P12-014`, `P12-129` and `P12-210` remain
`I2` with stronger consumer proof. The distribution is now 112 rows at `I3`,
26 at `I2`, 4 at `I1`, and 235 at `I0`; 142 of 377 rows are at least `I1`.
WO-008G is active next.

## WO-008G — Capacity automation and rollback/readback

Deliver:

- deterministic capacity snapshot from active entitlement authority and
  configured safe limits; no telemetry counter grants or revokes access;
- active acquisition campaigns auto-pause at the forbidden threshold and may
  resume only across hysteresis with an auditable owner policy. Renewal and
  recovery remain available;
- admin forecast/readback shows exact revision, capacity band, gate reasons,
  caps/reservations/paid counts and last evaluation time;
- repository dry-run/readback and rollback bundle restore one complete
  commercial revision. Production deploy, CDN purge and public readback remain
  separate authorized evidence.

Eligible rows: strengthen `MKT/MKT-300` and `MKT/MKT-600`; production and legal
gates remain open.

### 008G closure — `COMPLETE_LOCAL_I2`

Implemented one entitlement-owned capacity controller and one complete
repository rollback contract:

- `commercial_capacity_service.py` counts distinct non-reversed active/grace
  entitlement accounts at server time. This is the only unit authority;
  reservations, paid counters, node telemetry and funnel events are forecast or
  diagnostics only and cannot grant/revoke access or open acquisition;
- the supervised worker locks auto-managed `acquisition`/`winback` campaign
  roots and transactionally pauses at `>=70%`, records the hysteresis hold in
  `[65%,70%)`, and resumes only at `<65%` after current legal, seller, channel,
  revision, terms, cap and time gates pass. Renewal/recovery and owner-paused,
  ended/killed campaigns are never changed by that resume path;
- pause/hold/resume increments campaign revision and commits one bounded
  identity-free `AdminAudit` row under
  `commercial-capacity-owner-policy-v1`. A failed transaction rolls back both;
- read-only `GET /api/admin/campaigns.capacity_automation` now returns exact
  revision/SHA, capacity authority/units/limit/ratio/band, 210-unit pause and
  strict 194-unit resume ceiling, pending-reservation projection, gate reasons,
  lifecycle counts, campaign caps/paid/reservation counts and last evaluation/
  transition timestamps;
- `commercial_revision_bundle.py` snapshots exactly eight fact/catalog/
  generated contract files into a deterministic ZIP, verifies source semantic
  digests, contract digest, generated-document identity and every byte. Restore
  defaults to dry-run; apply requires expected current revision plus exact
  bundle SHA, uses same-directory atomic replacements, performs byte readback
  and restores already-replaced preimages after a planted later-file failure;
- worker enable/interval settings are explicit, the script is in the active
  manifest, and API/product/monitoring/deploy/developer/repository owners carry
  the same authority, hysteresis, evidence and rollback limits.

Local evidence for the current source:

- commercial contract/policy/capacity/offer/order/rollback/module matrix:
  `42 passed` (`2` existing SQLite adapter deprecation warnings);
- admin guarded policy and campaign route matrix: `11 passed`; admin/client
  readback matrix: `39 passed`;
- worker/economy/migration boundary matrix: `24 passed`;
- exact full payment regression: `88 passed`, `12 subtests passed`, with `19`
  existing deprecation warnings only;
- focused capacity/rollback suite: `8 passed`; Ruff, Python compilation,
  generated-commercial stale check and script-manifest check: `PASS`;
- current repository snapshot/readback/dry-run: revision `2026-08-21.1`,
  contract SHA
  `1d4b295a5ce9003345a2d32d8374852a144477659064fab8de8958be4f018f02`,
  deterministic 8-file bundle SHA
  `712ee1e9a2c33ca914b4d5d4b130c2c15b3814ba7be01511653b70f30914732a`,
  `changed_file_count=0`; no apply was executed on the worktree.

The checked-in legal contract remains launch-blocked and has no allowed channel.
No deployed worker, live campaign transition, provider/payment, production DB,
admin/public readback, deploy, CDN purge or production rollback was executed.
The locally tested apply/compensation used isolated temporary repositories only.
`MKT/MKT-300` and `MKT/MKT-600` remain `I2` with stronger evidence; they cannot
advance until exact-candidate deployed freshness/readback and an authorized
rollback rehearsal exist. Totals stay 112 rows at `I3`, 26 at `I2`, 4 at `I1`
and 235 at `I0`; 142 of 377 rows are at least `I1`. WO-008 is locally complete.

## WO-008H follow-up — Active-client product facts adoption

`WO-008H-client-product-facts-adoption.md` closes the client-repository follow-up
left by 008A. Platform product/public/commercial/tariff owners now generate a
digest-pinned typed client projection; the active runtime consumes it and the
standard seed gate rejects drift read-only. Prices, promo terms, referral
account state, orders, payments and entitlements remain server authority.

`REL/CONTRACT-001` advances `I2 -> I3`. The current megaplan distribution after
the later intervening WOs is `I3=278`, `I2=34`, `I1=45`, `I0=20`; `99` rows
remain below `I3`, split `29/32/17/21`. See WO-008H and its machine evidence;
the historical 008A–008G closure counts above are not rewritten.

## Verification

Minimum local gates, expanded only where a changed owner requires it:

```powershell
python -B -m pytest -p no:cacheprovider tests/test_commercial_contracts.py tests/test_shared_surface_facts.py -q
python -B -m pytest -p no:cacheprovider tests/test_commercial_offer_service.py tests/test_commercial_order_binding.py tests/test_commercial_attribution.py -q
python -B -m pytest -p no:cacheprovider tests/test_api_payments_callbacks.py tests/test_payment_order_service.py tests/test_payment_entitlement_outbox.py -q
python -B -m pytest -p no:cacheprovider tests/test_admin_action_intent_service.py tests/test_admin_payments_api.py -q
python -B -m pytest -p no:cacheprovider tests/test_frontend_text_integrity.py tests/test_public_copy_guardrails.py -q
pushd marketing; npm.cmd run build; npm.cmd run check:seo; npm.cmd run check:responsive; popd
pushd webapp; npm.cmd run build; npm.cmd run lint; popd
python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q
python -B scripts/agent_context_packet_audit.py --platform-context-root .
python -B scripts/check-links.py
python -B scripts/check_script_manifest.py
git diff --check
```

Required focused tests include hostile token mutation/expiry, concurrent quota,
exact retry, stale revision, legal/capacity block, reservation release/consume,
callback attribution non-authority, refund lineage, server-time countdown and
cross-consumer revision/price equality.

## Exit and evidence honesty

WO-008 is locally complete only when 008A–008H pass for the current source and
the ledger/docs name every remaining external gate. `I3` means verified local
candidate only. Seller publication, legal opinion, channel/ERID decision,
production provider/payment, deployed capacity, live campaign auto-pause,
public HTML/CDN revision, app-device behavior, rollback rehearsal and any pilot
remain `I4`/later-WO evidence.
