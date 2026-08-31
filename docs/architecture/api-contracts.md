# API Contracts

Last updated: 2026-08-31

This page captures release-critical API contract expectations for the current
repository candidate. It is also a concise router to the canonical domain
owners; implemented behavior here is not production evidence by itself.

## Domain Owners

- Identity, account linking, username sync, sessions, recovery, and bonus
  flows: [App-First And Bonus Flows](app-first-and-bonus-flows.md).
- Payment lifecycle and entitlement transitions:
  [Payment State Machine](payment-state-machine.md); product-facing purchase,
  activation-key, and access rules live in
  [Payment And Access Key Contract](../product/payment-and-access-key-contract.md).
- Approved client binaries, runtime links, and update metadata:
  [Client Downloads Flow](client-downloads-flow.md).
- Support tickets, private attachments, feedback, and moderation:
  [Support And Feedback Flow](support-feedback-flow.md).
- Backend and admin responsibility boundaries:
  [System Overview](system-overview.md). `adminapp` is the primary operator
  surface, the web admin is a parity fallback, and Telegram admin is
  fallback-only.
- Active Android and Windows client contracts:
  [POKROV App Docs Index](C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md).

## Account Identity Boundary

### Controlled Error Header

Every controlled HTTP error returned by the FastAPI public surface carries a
bounded `X-POKROV-Auth-Error` response header. An explicitly supplied header is
authoritative. Otherwise the server uses a normalized structured `detail.code`
only when it matches `[a-z0-9_]{1,64}`; it never derives a header value from
free-form detail or an exception. Plain errors use stable fallbacks:
`401 auth_required`, `403 forbidden`, `404 resource_not_found`, `409 conflict`,
`429 rate_limited`, and controlled `5xx service_unavailable`. The header is
additive: it does not change the status or FastAPI error body. FastAPI's
standard request-validation `422` response uses `request_invalid` without
parsing validation detail, and the header is exposed to configured CORS origins.

### Request Correlation And Unhandled Errors

Every HTTP request receives `X-Request-ID` as a new canonical UUIDv4. A client
may also send `X-Correlation-ID`; the server retains it only when it is a
canonical lowercase RFC 4122 UUIDv4, otherwise it
creates a replacement UUIDv4 and never reflects the unsafe input. Both headers
are returned on success, controlled errors and unhandled errors and are exposed
to configured CORS origins. Typed service calls receive the immutable request
context rather than reading arbitrary headers.

An unhandled exception maps to catalog code `API-007`, status `500`, and the
server request ID. The response and release log do not include the exception,
request body, query, `Authorization`, `Cookie`, or arbitrary header values.

### Commercial Revision And Public Catalog

Every FastAPI response carries `X-Pokrov-Commercial-Revision`. Its value is the
validated `commercial_revision` from `shared/commercial-contract.json`; backend
startup fails if that generated manifest or either bound source digest is stale.
The header is exposed to configured CORS origins so browser consumers can
validate it. It is a repository/runtime compatibility marker, not deployed-CDN
or public-readback evidence.

`GET /api/public/catalog` returns the same revision and manifest SHA-256 plus
`effective_from`, `terms_revision`, `price_authority`, `promo_authority`, the
scalar legal-launch gate and the active plan projection. `GET /api/public/plans`
returns the revision, manifest SHA-256 and the same active plan projection. Both
routes return `503` when DB plan code, base RUB price, duration or device limit
differs from the generated contract.

Marketing and cabinet checkout must match both response body and revision header
to the build-time manifest before enabling order creation. A static catalog is
display-only fallback. Clients always submit promo input to the server and must
not calculate a final discounted amount from a bundled code table. Current
`promo_authority=server_offer_preview_only` is implemented by the public offer
preview contract below. Payment order binding remains a later boundary and a
preview token alone cannot create access or prove payment.

### Campaign Policy And Admin Mutation

`GET /api/admin/campaigns` returns the current commercial revision/SHA,
entitlement-capacity snapshot and each `IncentiveCampaign` with stable public
ID, objective, lifecycle/campaign revision, legal/channel/seller/terms bindings,
paid cap/counter, capacity band, state reason and a closed policy decision. A
stored `is_active` flag is not sufficient: readback and actual promo/gift lookup
re-evaluate the current commercial contract and active-entitlement projection.

`POST /api/admin/campaigns`, `PATCH /api/admin/campaigns/{campaign_id}` and the
retained compatibility `DELETE` route are available only through the existing
action-intent preview/confirmation/idempotency/audit boundary. Create is
server-assigned a content/version-bound `cmp_*` ID; update may provide
`expected_revision` and always revalidates the row, contract and capacity at
confirm. `DELETE` performs an idempotent irreversible kill (`lifecycle_status`
`killed`, `state_reason=owner_killed`) rather than deleting evidence. A requested
`live` transition returns `409 campaign_policy_blocked` unless every legal,
revision, channel, finite-cap and applicable capacity gate is ready.

The active capacity unit is one distinct account with a non-reversed active or
grace `EntitlementGrant` at server time. This projection is the only automation
authority; node telemetry, clicks, reservations and campaign counters can warn
or forecast but cannot grant/revoke access or open acquisition. The supervised
worker evaluates the same 300-unit contract. It locks auto-managed
`acquisition`/`winback` campaigns, pauses `live` rows at ratio `>=0.70`, holds a
capacity-paused row through the `[0.65,0.70)` hysteresis interval, and resumes
only below `0.65` when every current legal/revision/channel/cap/time gate also
passes. Renewal and recovery are capacity-exempt. Owner-paused, ended or killed
campaigns are never auto-resumed.

Every pause/hold/resume increments campaign revision and stores one bounded
`AdminAudit` record under `commercial-capacity-owner-policy-v1`; a failed
transaction changes neither campaign nor audit. `GET /api/admin/campaigns`
remains read-only and adds `pokrov-commercial-capacity-automation-v1` readback:
exact contract revision/SHA, active limit/ratio/band, pause and strict resume
unit thresholds, pending-reservation forecast, gate reasons, lifecycle totals,
per-campaign paid cap/count and reservation counts, and last evaluation/
transition time. A pending-reservation forecast is conservative planning data,
not entitlement or acquisition authority.

The repository commercial manifest currently declares legal launch blocked and
no allowed launch channels. Therefore local previews/readback must remain
blocked; no response from these routes is legal approval, external campaign
launch, spend authorization, deployed-capacity proof or production readback.

### Public Offer Preview And Signed Hold

`POST /api/public/offers/preview` is the only public temporary-price preview.
The request carries a plan, optional promo code or stable `off_*` selector,
closed channel, and exactly one server-issued subject source: a valid checkout
ticket, a live unconsumed checkout acquisition handoff, or valid Telegram init
data. The service never accepts email, raw Telegram/account/install identity,
client-computed price, discount percent, deadline or quota as authority.

Every response is `Cache-Control: no-store, private` and contains server time,
the exact manifest base price, server final price, integer benefit, absolute
offer/hold deadlines, conservative remaining-quota lower bound, canonical offer
terms URL and exact commercial revision. Invalid preview is a successful typed
response with `valid=false`, a closed reason, base price repeated as final price,
zero benefit and no token. Stable blocks cover unknown/invalid/expired/depleted
promo, stale revision or terms, non-live/not-started/ended offer or campaign,
price mismatch, non-stackable base saving, legal/channel/capacity/audience gate,
quota, invalid subject and expired/conflicting reservation.

`commercial_offers`, `commercial_creatives`, `commercial_assignments` and
`commercial_reservations` are additive children of the existing
`incentive_campaigns` root. Preview never auto-enrols an audience: an eligible,
unexpired assignment with an active channel-matched creative must already bind
the campaign-scoped subject HMAC. The unique assignment-to-reservation owner makes refresh an
idempotent read of the same hold. An expired, released, consumed, foreign or
drifted reservation cannot be replaced by refresh. Browser cache, client clock,
offline replay or opening a new browser context cannot extend an existing
assignment deadline; a context without a valid server-issued subject or its own
eligible assignment remains blocked.

A valid response may include a `pokrov-commercial-offer-token-v2` value signed
with the dedicated `COMMERCIAL_OFFER_HMAC_SECRET`. Its versioned exact field set
binds only the opaque subject HMAC, plan, campaign/revision, creative/variant,
assignment, server-issued impression/click IDs, offer, base/final RUB price,
currency, commercial/terms revisions, reservation and integer issue/hold/offer
deadlines. Checkout acquisition handoffs own the same stable impression/click
IDs; authenticated preview creates equally opaque IDs on the reservation. It contains no email,
Telegram ID, account ID, install ID, checkout URL or provider secret. Signature,
shape, binding and deadline verification fail closed; only the token SHA-256 is
stored. The hold TTL is bounded to 60–900 seconds.

`POST /api/payments/orders/create` and
`POST /api/payments/orders/create-public` accept the token only as optional
`offer_token`; the retained FreeKassa wrappers carry the same field. The client
cannot submit authoritative price, discount, commercial IDs, deadline or quota.
Inside the pre-provider transaction the backend verifies the token signature
and exact field set, derives the subject only from authenticated Telegram or a
server-issued acquisition handoff, locks campaign/offer/creative/assignment/
reservation rows and revalidates current manifest price, commercial/terms and
campaign revisions, schedule, legal/channel/capacity policy and paid caps.

First acceptance changes the reservation from `held` to `bound`, gives it one
unique local order ID, and stores `pokrov-payment-order-intent-v2`. Its nested
`pokrov-commercial-order-lineage-v2` contains only stable commercial IDs,
opaque subject HMAC, exact price/currency/revisions/deadlines and token SHA-256;
the raw token and identity are not stored there. Exact retry with the same
valid token/provider/owner returns that order ID. Signature, subject, provider,
plan, price, revision, deadline, legal/capacity, quota, foreign reservation or
immutable-intent drift fails before provider I/O.

Provider I/O remains outside the transaction. A provider error leaves the
immutable `created` order and bounded reservation retryable through its absolute
hold. Once due, only a reservation whose local provider-checkout evidence is
`error` may be expired/released; a ready checkout is retained for a delayed
authenticated callback. Account and emailed-access-key fulfillment consume the
same bound reservation once in the entitlement transaction and increment its
campaign/offer/assignment paid counters once. Callback fields cannot add or
repair commercial lineage. Refund and chargeback keep the original v2 intent
and consumed reservation unchanged while the payment/entitlement reversal state
moves independently.

Every successfully consumed commercial order creates one identity-free
`commercial_conversions` row at stage `paid`, unique by provider/order/stage,
inside the same payment/entitlement transaction. It carries campaign, offer,
creative, variant, assignment, reservation, impression and click IDs, exact
integer RUB amount, commercial/campaign revisions, capacity-cost units and a
bounded evidence reference. It never stores subject HMAC, Telegram/account/
device identity, raw token, callback body, checkout destination or entitlement
secret. Refund or chargeback adds the idempotent `reversed` stage in the same
authoritative reversal transaction; it does not edit the original paid row.

`first_verified_connect`, `retained_d7` and `retained_d30` can be written only
while processing durable `connection_evidence` with
`evidence_kind=observer_connection` for the payment grant account. Client
success/funnel events and offer clicks are not connection or payment truth.
The named retention windows are `paid_at+[7d,14d)` and
`paid_at+[30d,37d)`. A later provider-payment grant for the same account adds a
`renewal` stage to that later order. `GET /api/admin/payments/summary` exposes a
read-only `commercial_attribution` projection with gross/refund/net RUB,
paid/first-connect/D7/D30/renewal counts grouped by campaign/revisions/capacity
unit, authority labels and explicit source freshness.

This is local repository proof. The checked-in legal manifest still blocks a
live external offer, and deployed consumer/provider/public-origin evidence
remains required before displaying temporary pricing as production-ready.

### Provider Capability And Payment Return

`GET /api/payments/providers` is the server owner for payment-method
capabilities. Each provider returns an ordered `payment_methods` list with a
closed code, display label/hint, `available` flag and closed unavailable reason.
Marketing and cabinet render only this list; an unavailable method remains
visible but disabled with its reason. A frontend table or inferred provider
feature is never availability authority.

Successful authenticated and public order creation returns an identity-free
`pokrov-payment-return-token-v1` capability alongside the provider checkout
URL. The HMAC token binds only provider, local order, consumer surface
(`marketing` or `cabinet`) and integer issue/expiry times. It contains no email,
Telegram/account/device identity, commercial offer token, checkout URL or
provider credential. Consumers store it in versioned `sessionStorage` before
leaving the origin. Provider success/failure redirects carry only provider and
return-surface hints; the return token is never placed in a URL, query, log or
analytics event.

`POST /api/payments/orders/status` accepts only that token and is public,
read-only, rate-limited and `Cache-Control: no-store`. It returns exactly one
closed consumer state: `processing`, `paid`, `failed`, `cancelled`,
`manual_review` or `expired`, plus a closed reason, safe polling delay and
terminal/support/retry flags. It never returns the local order ID or mutates
payment, reservation or entitlement state. Token signature/shape/binding fail
closed; token expiry is evaluated before order lookup, and a commercial hold is
revalidated from immutable order lineage on every read.

Marketing and cabinet strip provider return hints from the address bar before
polling. They stop only on a terminal state and render the server state; a
missing local token produces a support-safe message, not a guessed success or
an order lookup. This is local consumer-contract proof, not deployed provider
or public-origin evidence.

### Aggregate Release-health Ingest

Authenticated `POST /api/client/observability/release-health/batches` accepts
`application/json` with identity encoding up to `256 KiB`, or one complete gzip
member up to `64 KiB` whose decoded size is at most `256 KiB`. The batch schema
version is `1`, contains `1..100` events, and accepts only the
`privacy_class=release_health` projection of Operational Event Envelope V1:
event UUID/time, closed component/subsystem/stage/name/severity/outcome, exact
build identity, and either a catalog-backed code/origin pair or `null` error.
Unknown or duplicate JSON fields, schema versions, enums, error codes,
compression tails/bombs, arbitrary attributes, correlation trees, account,
install, device, session, destination, address, domain, package, credential,
raw-config and request-material fields fail closed.

The Android and Windows app-first shells persist the full allowlisted event
locally first, then best-effort this reduced projection only when an existing
app session is already available. Telemetry delivery never creates a trial or
session. The request carries a canonical `X-Correlation-ID` for transport
diagnosis, while the projection body and stored row contain no correlation or
identity field.

Success is `202` with accepted and duplicate counts. `event_id` is unique, so
an identical retry cannot inflate release-health aggregates; reuse with a
different projection fails as `409 event_id_conflict`. Storage
contains no account/install/session/device/correlation field. A rejected batch
stores only a bounded `quarantine.<reason>` counter, never the payload. This
telemetry path has separate rate limiting and cannot authorize payment,
entitlement, trial activation, compensation, incident creation or support-case
state.

Authenticated
`GET /api/client/observability/release-health/baseline` accepts only the exact
build identity fields from that same closed contract. Its response conforms to
`release-health-baseline.v1.schema.json`. Accepted events contribute to a
weekly cohort through `RELEASE_HEALTH_COHORT_SECRET`: the server HMAC maps one
authenticated account to one of 4096 build-and-week-scoped buckets, then
discards the account value. It persists no account/install/device/session value
or stable contributor hash. A bucket is capped at 64 total events and 32 events
for each crash/connection/update family, so retries and one noisy account cannot
dominate the client comparison.

The projection returns `insufficient_cohort` until at least ten distinct bucket
indexes exist and does not reveal the observed subminimum count. Ten buckets
require at least ten authenticated accounts; collisions only undercount. It
returns `insufficient_samples` until at least 30 capped observations exist.
Only then may `baseline` contain closed sample-size and failure-rate bands;
exact counts, exact rates, bucket indexes and error-code distributions are not
part of the client contract. Missing/short privacy secret is `503
baseline_privacy_unavailable`, never a lower threshold. The read is
observational and cannot mutate release, incident, entitlement or support state.

The repository candidate implements an additive account foundation: UUID `accounts.id`
is persisted and `users.account_id` is a nullable projection. The
public numeric `account_id` remains a compatibility projection. Device sessions
use persisted rotating sessions; legacy browser, Telegram, and email tokens retain
a stateless bearer compatibility path, not account or payment authority.
Rotating sessions, recovery exchange, durable provider-payment grants,
account-owned fulfillment, and entitlement-ledger authority exist in this
repository candidate. Production deployment of account foundation is not proven.
A completed production cutover, mixed-fleet safety, and full migration must not be claimed without exact current evidence.

## Client Apps

`GET /api/client/apps` is authenticated and must return only approved runtime
links for app, bot, and cabinet consumers. `GET /api/public/client-apps` is the
anonymous marketing projection of the same runtime release source. The public
projection is cacheable, contains no account data, accepts only the exact
versioned GitHub Release filenames owned by POKROV, and publishes an artifact
only when its SHA-256 and positive byte size are present. Empty Android or
Windows URLs mean that download is unavailable; public install pages must show
that state explicitly and must not substitute a login or cabinet redirect.

When runtime values came from a strict schema-v2 `release-handoff.json`, both
responses also expose the bounded `release_manifest` identity: schema version,
candidate label, SHA-256 of the exact handoff bytes, artifact-set SHA-256, Core
version, desktop ABI and Android package. The field is `null` unless every
identity value is complete and valid; legacy or partially configured runtime
state must not look manifest-bound.

### First-party acquisition handoff

`POST /api/funnel/events` accepts only the bounded acquisition fields used to
answer source, next step, completed action, and drop-off. The browser-generated
session value is SHA-256 hashed with a domain separator before persistence; the
raw value, raw URL/query, IP address, user agent, VPN destination history,
message text, credentials, and provider payloads are not stored. First touch is
immutable, last touch is updated by later accepted events, and the session
expires after `180 days` from its latest touch.

`POST /api/acquisition/handoffs` issues a random opaque handle for exactly one
allowlisted purpose: Android install, Windows install, account continuation,
checkout, or Telegram continuation. The database stores only the token hash;
the handle expires after `72 hours`, is consumed once, grants no authentication
or product access, and rejects wrong-purpose, replay, expiry, or cross-account
binding. A missing handoff remains `unknown`; the platform must not infer a
browser/device/account relationship from timestamps, IP, or user agent.

`POST /api/acquisition/handoffs/consume` may bind the acquisition session to a
known Telegram/account/order lineage. External orders and Telegram Stars
`pay_attempts` retain the exact acquisition-session foreign key available when
checkout starts; signed provider callbacks remain payment authority and cannot
rewrite first/last-touch attribution.

`GET /api/client/locations` keeps its existing country/city shape and adds a
deterministic `variants` list to every returned city. The first item is always
`{"id":"direct","label":"Обычный","description":"Прямое подключение"}`.
Enabled `ru_bridge_relay.endpoints[]` follow in rollout order only when the
bridge is globally enabled, the endpoint has valid material, the node passes
bridge allowlist/exclusion rules, the node's required delivery transport is
enabled, and the endpoint does not identify that exact delivery node by stable
id or configured host. Each bridge item exposes only stable endpoint `id`,
short operator label, and the fixed consumer description `Для ограниченных сетей`; it never
contains endpoint host/port, Reality keys or short IDs, sing-box tags, or raw
config. US and any other excluded or non-allowlisted node remain direct-only.
The additive list and existing `profileRevision` let clients cache the safe
catalog without breaking readers that ignore unknown fields.

### Device Sessions

The repository candidate implements the following Android/Windows session
contract. It is not production evidence until the deployment and client gates
in the active work order are complete.

Route-policy updates use `POST /api/client/route-policy`. The
`selected_apps` mode requires at least one normalized package/process
identifier; an empty selection is rejected as HTTP `422` with stable code
`selected_apps_required` and does not replace the existing persisted policy.

- `POST /api/client/session/start-trial` creates the account/device session only
  when that real device has no session history. It returns the existing
  compatibility `session_token` field plus the same value as `access_token`, a
  one-time `refresh_token`, expiry fields, canonical account UUID, registry
  device UUID, session UUID and refresh-family UUID.
- A repeated bootstrap for the same `install_id` does not issue another
  credential. It returns HTTP `409` and
  `X-POKROV-Auth-Error: device_recovery_required`. A client that still has its
  refresh credential must call the refresh endpoint; a client that lost it
  must use the recovery contract below.
- The first account/device creates one idempotent `7-day` premium-trial
  reservation. `access.trial_state` distinguishes `reserved` and `active`;
  `reserved_at`, `reservation_expires_at`, and `activated_at` expose lifecycle
  timestamps. The compatibility credential remains available during
  reservation, while `access.trial_days` remains exactly `5`; environment
  configuration cannot override that public authority.
- `POST /api/client/session/refresh` rotates the refresh token once. The raw
  refresh token is returned only in the response; the database stores its
  SHA-256 digest. The refresh-family expiry is absolute and is not extended by
  rotation.
- Bootstrap and refresh keep compatibility `account_id` numeric. The canonical
  account UUID is always additive under `canonical_account_id`, including the
  nested `session` payload.
- Reusing a consumed refresh token returns HTTP `401` with
  `refresh_reuse_detected` and revokes every access/refresh row in that family.
- `POST /api/client/session/revoke` logs out the current persisted session by
  revoking its refresh family without revoking the device.
- `GET /api/client/devices` reads `account_devices`. Compatibility field `id`
  remains the install ID while `registryId` is the canonical device UUID.
- `PATCH /api/client/devices/current` updates only the device bound to the
  authenticated session. It accepts a bounded human-safe label and platform
  metadata, never a serial number, hardware ID or arbitrary target device ID.
  A redundant client prefix such as `POKROV Android`/`POKROV Windows` is
  removed when a real model or computer name follows it, so compact device
  lists lead with `Samsung SM-S9110` or `Surface Laptop` instead of clipping
  the useful identity behind a generic product label.
- `DELETE /api/client/devices/{device_id}` accepts either identifier, requires a
  recent `fresh_auth_at`, increments `credential_version`, marks the device
  revoked and revokes all sessions bound to that device.
- Bootstrap possession is not fresh authentication. Email OTP or a one-time
  recovery exchange can set `fresh_auth_at`; otherwise device revoke returns
  `409 fresh_auth_required`.
- App cabinet handoff and the exchanged cabinet bearer inherit the source
  session/account/device/epoch/credential claims. They remain invalid after
  source-family logout, reuse detection or device revoke instead of becoming a
  detached stateless bearer.

Access tokens are short-lived signed bearer tokens containing `session_id`,
`account_id`, `device_id`, `auth_epoch`, `device_credential_version` and
`scope`. Every token with `session_id` is checked against the database on each
authenticated request. Legacy browser/Telegram/email bearer tokens without
that claim retain their existing compatibility verification path.

Defaults are `APP_ACCESS_TOKEN_TTL_SECONDS=900`,
`APP_REFRESH_TOKEN_TTL_SECONDS=2592000`,
`APP_FRESH_AUTH_MAX_AGE_SECONDS=600`, and
`API_RATE_LIMIT_SESSION_REFRESH_PER_MINUTE=10` per hashed refresh credential.
`API_RATE_LIMIT_SESSION_REFRESH_IP_PER_MINUTE=600` is the separate coarse IP
ceiling for random-token abuse without making ordinary mobile CGNAT users share
one small bucket.

Session cutover cannot use a mixed old/new API fleet: the previous stateless
revision accepts signed access tokens without checking database revoke state.
Old instances must be drained before new session issuance. Rollback must first
stop bootstrap/refresh issuance and wait at least the configured maximum access
TTL after the final issuance before routing app access back to the old revision.

### Email OTP And Recovery

- `POST /api/auth/email/otp/start` accepts an email address and always returns
  the same generic accepted shape for syntactically valid known and unknown
  addresses. A verified identity receives a six-digit code valid for exactly
  five minutes. The code is never returned in API JSON.
- `POST /api/auth/email/otp/finish` consumes the email/code pair once. Without
  device metadata it issues the compatibility browser session and, when the
  request carries a matching persisted device session, marks it freshly
  authenticated. With device metadata it returns a new bound access/refresh
  pair subject to the device limit.
- Password login remains under `/api/auth/email/login` only as a labelled
  compatibility path. Its response carries
  `auth_method=password_compatibility`; the deployment owner must configure and
  execute the approved 90-day sunset separately.
- `POST /api/client/recovery-code/rotate` requires a persisted client session
  with recent fresh auth. It revokes previous active codes and returns one
  `PKR-XXXX-XXXX-XXXX` code exactly once. The database stores only a versioned
  HMAC and masked four-character hint.
- `POST /api/client/recovery/exchange` consumes an active code once, registers
  or reauthenticates the supplied device, and returns a device-bound
  `scope=recovery` session whose access and refresh expiry are both 15 minutes.
- Recovery scope is checked on every authenticated request against the exact
  HTTP method plus FastAPI `request.scope["route"].path` template. Missing or
  unknown route templates fail closed. The complete allowlist is
  `GET /api/auth/session`, `POST /api/client/session/revoke`,
  `POST /api/client/access/reissue`, `GET /api/client/devices`,
  `DELETE /api/client/devices/{device_id}`, `GET|POST /api/tickets`,
  `GET /api/tickets/{ticket_id}`, and
  `POST /api/tickets/{ticket_id}/messages`.
- Recovery support is text-only. Ticket create/message returns
  `403 recovery_scope_forbidden` when any `media_type`, `media_file_id`, or
  `media_payload` value is nonempty. Recovery ticket list/get/create/message
  responses omit all three media keys from every message, including historical
  messages. Upload, attachment download, standalone support AI, subscription,
  managed-profile, and normal client networking routes are outside the
  allowlist. Normal client and admin ticket attachment contracts are unchanged.
- Recovery scope cannot link a new identity, create payment ownership, read
  subscription URLs or managed profiles, or access normal client networking
  surfaces before reissue.
- `POST /api/client/access/reissue` accepts `vpn_credentials` or
  `account_lockdown` exactly once per recovery session. Both rotate public
  subscription material and enqueue managed-key rotation. Lockdown additionally
  increments `accounts.auth_epoch`, revokes other devices and invalidates other
  sessions. Entitlement and paid expiry are preserved.
- `vpn_credentials` cannot promote the recovery device while the active-device
  count exceeds the tariff limit. The user must revoke an old device or choose
  `account_lockdown`, which leaves only the recovered device active.
- A queued provider-key rotation is not proof that node credentials have
  changed. Clients and operators must treat `provisioning_status=pending` as
  incomplete until the provisioning worker records completion.

### Antiabuse Privacy Ledger

- A successful `POST /api/client/session/start-trial` writes an additive
  `trial_reserved` signal with canonical account, device and session IDs. Raw
  `install_id` is not copied into the ledger; it is represented by a
  domain-separated HMAC.
- Its independent panel convergence is limited to four seconds. Incomplete
  convergence returns `provisioning.status=pending_sync`; it does not roll back
  the committed trial/session authority or become connection evidence.
- API security events retain the compatibility `security_events` audit row and
  write a matching `antiabuse_events` signal in the same transaction. Metadata
  keys that indicate tokens, secrets, passwords or authorization material are
  redacted before either JSON payload is persisted.
- Valid IPv4 and IPv6 addresses are canonicalized before storage. Code caps the
  raw-IP deadline at 72 hours, full-IP HMAC at seven days, and IPv4 `/24` or
  IPv6 `/64` prefix HMAC at 90 days. Configuration may shorten but cannot extend
  those caps. Stored deadlines and cleanup cutoffs include a one-hour early
  sweep margin, larger than the maximum 15-minute worker cadence.
- HMAC-SHA256 uses `ANTIABUSE_HMAC_SECRET`, purpose separation and
  `ANTIABUSE_HMAC_VERSION`. Explicit previous secrets use
  `ANTIABUSE_HMAC_SECRET_V<n>` and remain query candidates only below the
  current version. Auth, recovery, payment and Telegram secrets are not
  fallbacks.
- If the dedicated secret is absent, customer requests continue and raw IP
  still expires, but HMAC fields remain empty. That state is not production
  antiabuse readiness and must stay a manual deployment gate.
- The dedicated antiabuse worker nulls overdue sensitive fields in bounded
  `SKIP LOCKED` batches and commits each batch. Each thread chunk has a batch
  cap; backlog triggers another chunk after one second instead of blocking the
  worker event loop. It does not delete security, antiabuse or user audit rows.
  Worker outage or persistent backlog can exceed the operational target and is
  a release-blocking incident, not a database TTL. Hard account lock changes
  require an explicit operator identity and reason and create an
  `antiabuse_actions` audit row.

### Trial Connection Evidence

- `GET /api/user/{tg_id}` includes an additive account UX snapshot:
  `experience.onboarding` (`version`, `status`, `should_show`, `updated_at`),
  `experience.first_connection` (`state`, `reported_at`, `verified_at`), and
  `experience.next_step` (`install`, `connect`, or `complete`). Compatibility
  mirrors `sync.connected_once` and `sync.first_connected_at` remain additive.
- Authenticated `POST /api/account/experience/onboarding` accepts only
  `{"status":"completed"}` or `{"status":"skipped"}` and returns the updated
  snapshot. This is account-scoped UX state; it does not mutate access.
- `POST /api/client/runtime/stats` with `connected=true` records the earliest
  account-scoped `reported_at`. It remains client-authored telemetry and cannot
  activate a trial, extend expiry, grant a reward, or become observer evidence.
- Signed `POST /api/internal/observer/batches` observations resolved to a
  canonical account are the activation source. Each accepted observation adds
  append-only `connection_evidence` with account, optional device, node,
  evidence kind, observed timestamp, and a unique stable evidence key.
- The same accepted observation records the earliest account UX
  `verified_at`. `verified` is derived from server evidence even if a legacy row
  predates the UX state table; this projection cannot weaken the evidence or
  entitlement ledgers.
- Offset-aware observation timestamps are converted to naive UTC before
  evidence storage, activation, expiry calculation, and key derivation. `Z`,
  positive offsets, and negative offsets representing the same instant produce
  the same canonical timestamp.
- Evidence key v2 is derived from the owned node, immutable resolved legacy user
  identity, evidence kind, and canonical UTC observation timestamp. It excludes
  mutable canonical account IDs, so replay after account merge and in another
  batch converges to the existing row.
- Evidence rows never contain a raw subscription URL, bearer token, provider
  secret, source IP, or traffic payload. Existing observer response fields stay
  compatible; `activated_trial_count` is additive and reports only newly
  activated reservations.
- Activation is row-locked on PostgreSQL where available and guarded by unique
  trial/evidence keys. Replay returns `activated_trial_count=0` and cannot move
  `activated_at` or `expires_at`; effective expiry is exactly the first valid
  observation timestamp plus `5 days`. The counter comes from the locked
  activation transition result, never from a pre-read of grant state.
- A concurrent insert conflict on the observer batch unique key rolls back the
  losing transaction and returns the committed winner as a replay response.
  Other integrity failures still fail the request.
- `POST /api/connect/confirm`, `/api/events`, `clicked_connect`,
  `connected_ok`, runtime stats, funnel events, and other client-authored
  telemetry are never activation evidence.
- Authenticated app-first telemetry accepted by `POST /api/events` includes
  `app_first_open`, `acquisition_handoff_received`,
  `acquisition_handoff_failed`, `trial_start_selected`,
  `existing_access_selected`, `vpn_permission_explainer_shown`,
  `vpn_permission_result`, `first_home_seen`, and
  `first_verified_connect`; `connect_requested` remains the shared connect
  event. The route resolves `account_id` and `device_id` exclusively from the
  validated bearer session. Client bodies use bounded platform/version,
  surface=`first_session`, subsystem=`onboarding`, stage/result, safe error
  code, and retryability fields. Acquisition handles, access/refresh tokens,
  managed profiles, endpoints, provider payloads and raw host error text are
  forbidden from the event envelope.
- The worker expires unactivated reservations after `5 days` and updates only
  the legacy compatibility projection to `expired_or_blocked` when no paid or
  unrelated active grant or current `User` projection survives. This projection
  guard remains required while payment and bonus paths have not all cut over to
  grants. Panel synchronization remains retryable and cannot fabricate evidence.

### Legacy Free Profile Provisioning (Disabled)

`FREE_TIER_ENABLED=false` is the fail-closed production default. The API returns
`expired_or_blocked`, selects no free node, and cancels queued legacy free jobs.
The rules below are retained solely for rollback compatibility when an operator
explicitly enables the legacy contour.

- Free quota authority is exactly `5 * 1024^3` bytes on `free_standard`; an
  environment override cannot change the credential hard cap.
- Internal node observations and server-read panel runtime may queue the
  transition, but traffic bytes alone do not change the projected access state.
  The additive dashboard/user payload fields are `free_profile_state`,
  `free_profile_active_role`, `free_profile_job_id`, and
  `free_profile_error_code`; `free_caps` exposes the same transition state.
- `soft_mode_active=true` requires persisted `free_profile_active_role=free_soft`
  and a confirmed compatible state. During `soft_transition_pending`, the API
  remains `free_monthly`; confirmed soft mode reports zero standard-quota
  remaining instead of interpreting the fresh soft counter as another 5 GiB.
- Provisioning jobs are idempotent per account cycle, row-locked on PostgreSQL,
  bounded on retry/stale recovery, and preserve the pre-existing
  `rotate_access_key` job contract. Every running claim carries a fresh fencing
  token and renews its lease through panel work; a worker that loses ownership
  cannot continue panel mutation, finalize the database, or run compensation.
  Errors persist only stable redacted codes.
- A pooled legacy key (`node_code=NULL`) rotates only panel copies already
  found in the enabled inventory: every copy must still hold the exact old
  credential or the exact persisted replacement from an interrupted attempt;
  absent nodes are never provisioned. The first safe claim persists the old
  credential fingerprint and scope in the job's desired state. Duplicate rows
  on the canonical inbound or any same-account row on another managed inbound
  are ambiguous and block before mutation. Every ambiguous panel write
  receives an exact guarded readback; unknown state or failed compensation is
  manual review, never a blind retry. Finalization compares the locked snapshot
  and, for the primary/legacy subscription identity, atomically replaces
  matching `User.uuid` and `UserNode.client_uuid` values before the job can
  succeed. A failed DB finalize triggers guarded panel rollback and is retryable
  only while the canonical DB still matches that original snapshot.
- UUID rollback converges every affected panel copy, including rows whose
  durable value is already the old UUID: each affected panel receives the
  runtime apply/restart sequence and an exact post-apply row readback before
  compensation can be reported as complete.
- Target profile ensure and exact confirmation happen before source disable.
  Reset additionally clears standard traffic before soft disable. A payment or
  entitlement projection that supersedes an in-flight free job must not be
  overwritten during finalization. The worker compensates a superseded panel
  mutation by restoring the exact recorded target preimage (`enabled`,
  `disabled`, or `absent`) with live readback, then restoring the paid source,
  or the last confirmed standard source when paid provisioning is not yet
  visible. Compensation is fenced by a durable pending marker; an unsupported
  removal, ambiguous readback, or failed compensation goes directly to manual
  review instead of guessing that the target should be disabled.
- An ordinary source-disable failure also compensates before retry or terminal
  failure. The worker durably records the exact target/source panel preimage and
  a fenced compensation-pending marker, restores every binding through the
  current claim lease, and confirms each restored state by readback. A lost
  panel or database acknowledgement is accepted only when that exact readback
  proves the intended state; stale or uncertain compensation is manual review.
- Expiry/revocation re-entry uses the same durable reset job: it confirms and
  clears standard first, then disables every configured paid source and a stale
  soft source. Revocation updates every matching managed inbound; only a
  successful exhaustive panel read may treat absence as idempotent success,
  while a panel read error remains failure. Merely changing `sub_type` or
  `current_plan_code` is not panel synchronization proof.
- Panel inbound reads distinguish a successful empty list from authentication,
  HTTP, payload, and network failure with bounded typed error kinds. Lookup,
  revocation, preimage capture, and compensation propagate those failures and
  never reinterpret them as an absent client or successful cleanup.
- `free_standard`, `free_soft`, `paid`, and `operator_lab` are explicit node
  roles with positive non-duplicated inbound bindings. Uniqueness covers every
  enabled or disabled transport-catalog profile sharing the same normalized
  panel identity, not only each node's canonical inbound. Missing free roles
  never fall back to paid or operator-only nodes.
- Control-panel network awaits run only after their database sessions close;
  user data crossing that boundary is an immutable scalar snapshot rather than
  a live ORM object.
- Public locations, subscription rendering, legacy control-panel helpers, and
  admin resync all resolve the persisted free role. Transition/error states
  cannot be force-resynced by legacy admin actions. Expiry monitors only queue
  the durable re-entry job and do not mutate panel profiles directly.
- The native locations catalog exposes `latencyMs` as dataplane RTT when the
  collector has it; panel-control latency is used only as a compatibility
  fallback and must not be presented as the user's route ping.
- The automatic Smart Connect shortlist remains bounded, but an explicit
  manual location choice may promote any currently eligible catalog node into
  the managed-profile shortlist. Disabled, unhealthy, stale, overloaded, or
  transport-incompatible nodes remain fail-closed.
- The owner-only `awg2_lab` transport is not a node-catalog or public
  subscription profile. Its typed endpoint is stored per user/install in
  `awg2_lab_materials` as authenticated ciphertext and is decrypted only while
  constructing an authenticated `GET /api/client/profile/managed` response.
  The managed response binds `pokrov.awg2.endpoint.v1`, the exact Core contract
  SHA-256, endpoint revision, generation and `useIntegratedTun=false`.
- Owner-only `awg2_lab` and `awg31_lab` managed issuance bypasses Smart Connect
  and the ordinary node shortlist because those profiles are backed by typed
  per-device endpoint material rather than catalog nodes. The response returns
  `smart_connect: null`, ignores `selected_node_code`, and remains governed by
  the exact device, rollout, server-record and material gates below.
- Node-backed `GET /api/client/profile/managed` runs independent panel sync and
  runtime reads concurrently inside a shared eight-second budget. Panel sync
  gets a seven-second sub-budget so its own timeout can settle before the outer
  request budget. Sync timeout
  keeps `provisioning.status=pending_sync`; runtime-read timeout uses a zeroed
  unknown-state fallback without downgrading a completed sync. Neither creates
  connection evidence. Device-bound `awg2_lab`, `awg31_lab`, and `hy2_lab`
  skip this unrelated legacy panel path entirely.
- Both owned AWG profiles currently route only `0.0.0.0/0`; their managed DNS
  strategy is therefore `ipv4_only`. An IPv6 answer must not be selected until
  the endpoint contract also owns and proves an IPv6 routed prefix.
- AWG2 issuance requires the disabled-by-default rollout gate to be enabled,
  its kill switch to be clear, exact user/install/platform/node allowlists, a
  current ready POKROV-owned server record and fresh device material. Missing,
  stale or unknown state falls back to `legacy_reality_fallback` before profile
  issuance. Token subscriptions, previews, Happ/Clash/manual exports and
  locations never return AWG2 material.
- `PUT /api/admin/client/awg2-lab/material` is an L3 action-intent route. It
  replaces material for one device and stores only endpoint/install
  fingerprints in intent, preview, audit and result payloads. Raw endpoint,
  keys and install ID are forbidden outside the encrypted request-to-storage
  boundary.
- A confirmed reset starts a fresh full 30-day cycle. Migration retains any
  prior invalid node role in `access_role_legacy` before heuristic backfill so
  an application rollback can restore the old value without deleting evidence.

## Rewards

All reward endpoints require the normal authenticated account context. The
server, not the client, owns eligibility, random outcome, cooldown, calendar
position, grant duration, and synchronization state.

- `GET /api/bonuses` is the compact compatibility summary. Its nested
  `channel` object exposes `offer_days`, `claimed_days`, `claimed`,
  `claimed_at`, and `channel_username`; UI must use `offer_days` for a current
  offer and retain an actual historical `claimed_days` value separately.
- `GET /api/bonuses/summary` adds nested `referral`, `channel_bonus`,
  `opening_bonus`, `promo`, `history`, `wheel`, `calendar`, and `achievements`
  plus `reward_access` with the canonical paid gate for wheel/calendar/referral
  rewards. `channel_bonus.eligible` and `channel_bonus.can_claim` are separate:
  the one-time Telegram `+5 days` offer is available before the first payment,
  without exposing a canonical account UUID, private subscription URL, raw
  random weights, or internal job metadata.
- `GET /api/bonuses/wheel/state` returns `enabled`, `eligible`, `reason`,
  public `state`, flag name/state, `can_spin`, `last_spin_at`, `next_spin_at`,
  `cooldown_hours`, `last_reward_days`, `last_discount_pct`, safe ordered day
  and discount sectors, `sync_state`, `ledger_ready`, and `config_preset`.
  Sectors are labels, not probability
  evidence; missing, empty, invalid, or unknown sectors must fail closed.
- `GET /api/bonuses/calendar` returns `enabled`, `eligible`, `reason`, public
  `state`, flag name/state, `checked_in_today`, `can_checkin`, cycle dates/day,
  `next_milestone`, safe checked dates, achievements, and `sync_state`.
- `POST /api/bonuses/wheel/spin` returns the server-selected reward kind/value,
  `reward_days` or `discount_pct`, `grant_id` when a day grant exists,
  `sync_state`, fresh wheel `state`, `expiry_at`, `sync_ok`, and a
  fresh summary. `POST /api/bonuses/calendar/checkin` returns the equivalent
  grant/sync fields plus `already_checked_in`, cycle position, state, and
  summary. A repeat calendar check-in on the same day is idempotent and may
  return zero newly awarded days.

Stable mutation errors are:

| HTTP | `detail.code` | Additional fields | Meaning |
| --- | --- | --- | --- |
| `403` | `bonus_feature_disabled` | `feature` | The independent rollout flag is off. |
| `403` | `active_paid_required` | none | The exact active-paid predicate failed, including a bonus-only tail after paid expiry. |
| `409` | `wheel_cooldown_active` | `next_spin_at`, `last_reward_days`, `last_discount_pct` | The 336-hour wheel cooldown has not elapsed. |
| `503` | `reward_state_unavailable` | none | State/config/integrity could not be safely resolved; clients must not invent a result. |

An eligible mutation atomically writes canonical `RewardAccountState`, a typed
`EntitlementGrant`, and one idempotent `reward_entitlement_sync` job. Public
`sync_state` is one of `not_required`, `sync_pending`, `synced`, or
`manual_review`. `sync_pending` does not revoke the committed grant, while
`manual_review` must remain operator-visible and must never be presented as a
successful panel synchronization.

`GET /api/client/promo-slots?surface=app` returns only active assignments for
the caller's access context and schedule plus `server_time` for countdown
alignment. An app slot may carry optional title/body/badge, layout
`logo|banner|media_only`, first-party `image|animated_image|video` media,
dimensions/bytes/MIME, video poster and static fallback, CTA, safe HTTPS/TG
target, `#RRGGBB` colors, placement, priority, dismissibility and whole-card
click behavior. `media_only` needs no copy or CTA; a video requires both poster
and fallback. Countdown `ends_at` expires fail-closed without an app update.
Server normalization rejects unsupported slots, content/context combinations,
external media hosts, URL schemes, layouts, colors, incomplete video, empty
enabled creatives and malformed/reversed schedules. The client remembers a
dismissal by slot/content/schedule; changing that campaign identity permits a
new impression.

`POST /api/admin/promo-media` accepts an authenticated raw asset body up to the
configured limit (24 MiB by default), detects PNG/APNG/JPEG/WebP/GIF/MP4/WebM
from file magic rather than filename, stores it under an opaque content hash,
and returns safe metadata. `GET /api/public/promo-media/{asset_id}` serves only
those known suffixes with immutable caching, `nosniff`, and inline disposition.
SVG/HTML/script and third-party media URLs are not campaign inputs. Promo
events remain first-party and may contain only slot/content/placement identity,
never advertising IDs, installed-app lists or browsing history.

## Payment Providers

`GET /api/payments/providers` must expose provider availability and enough unavailable-state detail for checkout to avoid presenting blocked payment paths as live.

Payment order, callback, reversal, delivery-evidence, start-99 and historical
FreeKassa DB use cases run through Starlette/AnyIO's bounded threadpool. Each
use case creates, commits or rolls back, and closes its own synchronous
SQLAlchemy session in one worker thread. A session, query, lazy relationship or
ORM row must not cross an `await`; only immutable intent objects, scalars and
plain bounded dictionaries return to async transport orchestration. Provider I/O
remains between the committed order-intent and provider-result transactions.
`/api/health.payment_db` exposes integer-only active/max-active, started,
completed, failed, queue-wait and duration counters; it contains no SQL,
parameters, row identity or exception. This is a scoped payment transition, not
a claim that the remaining async API ORM inventory has been migrated.

Anonymous public order creation persists `ExternalOrder` and one
`PaymentEntitlementClaim` in the same local transaction. The claim is unique by
provider and provider order ID, stores only normalized claim ownership data,
and supports both paid-before-attach and attach-before-paid processing. This
slice exposes no new public claim or OTP endpoint; verified-email attachment is
an internal service contract for the next workstream slice.

Paid fulfillment requires an existing `ExternalOrder` and is bound to that
row's saved account owner. Callback identity fields never replace a persisted
`tg_id`; a conflicting callback owner produces terminal manual-review receipt
evidence without a grant. An anonymous order whose saved `tg_id` is null stays
in claim/fallback fulfillment even when callback data supplies a Telegram ID.

Signed paid callbacks are receipts, not completion proof. A paid event remains
`processed_ok=false` until either its attached claim has one durable
order-idempotent entitlement grant or its unclaimed claim has one linked
fallback GiftCard. For email fallback, the receipt remains incomplete until a
delivery attempt and its bounded evidence are stored; delivery failure is
retryable while the durable claim/card commit remains intact. A crash before
delivery therefore retries. A crash after transport success but before evidence
may send the same key again, so this boundary is at-least-once rather than an
at-most-once no-delivery risk. Telegram notification and panel synchronization
remain downstream and cannot roll back durable entitlement fulfillment.
If refund/chargeback commits while fallback email transport is in flight,
delivery evidence cannot replace the reversal fulfillment state. Paid receipt
completion locks and rechecks the current order after evidence persistence;
reversal wins terminally as `claim_reversed`, reports no ready access, and the
processed paid receipt does not resend on replay.

Signed terminal outcomes such as reversal, manual review, definition/type/
ownership/redeemed conflicts, and verified ownership conflict are completed and
deduplicated with `activated=false` and fixed safe evidence. Retryability is
reserved for transient incomplete paid/reversal/delivery persistence and for a
later valid-signature upgrade. Claim processing
errors use fixed safe codes with `last_error_at`; successful retries retain the
last error code and timestamp as audit evidence. Delivery evidence stores only
bounded status, mode, HTTP status, and a fixed error code, never relay detail,
message body, buyer email, or activation key.

The initial signed refund/chargeback receipt transaction marks the order as
pending reversal reconciliation before the separate reconciliation transaction
starts. A crash or exception between those commits therefore remains visible to
operators. Only an explicit successful `reversed`/`already_reversed` result
clears attention; refunded/chargeback rows without that evidence are treated as
unreconciled. Missing linked fallback or grant rows are fixed-code terminal
manual-review outcomes: the receipt deduplicates without a retry storm, no
access is granted or reported as reversed, and the order remains in attention.

Payment order state is monotonic after `paid`: later pending, failed, cancelled,
or manual-review results do not downgrade it. Refund and chargeback events may
supersede paid, reverse the linked claim and grant once, rebuild the canonical
account projection, and block the linked fallback card. Different external
event IDs for one provider order remain idempotent at the claim, grant, and
fallback-card layers.

Receipt persistence serializes every callback for the same provider/order on
the shared `ExternalOrder` row with `FOR UPDATE`, even when external event IDs
differ. The locked row is refreshed before applying the transition, so stale
paid/refund/chargeback writers cannot overwrite the monotonic state or pending
reversal evidence. Successful reversal reconciliation explicitly retains the
order's `refunded`/`chargeback` status. Paid fulfillment rechecks that locked
status after receipt persistence; if reversal won the inter-commit race, the
paid receipt completes terminally as `order_reversed` without a grant or key.
If account bootstrap requires a transaction rollback, fulfillment reacquires
and refreshes the provider/order row under `FOR UPDATE` before any account or
grant mutation. A reversal committed during that bootstrap window remains
authoritative and cannot be replaced by paid metadata or a historical
provider-payment grant.

Payment-linked fallback cards redeem through claim ownership rules and use the
claim's saved plan code and duration even if the current catalog no longer
contains that plan/card type. Redeeming after an automatic same-account claim is
idempotent and cannot add another paid period. A wrong-account redemption returns
a conflict without changing the claim to manual review, so it cannot block the
rightful owner; verified-email attachment conflict remains an operator-review
state. A fallback is durable only after its GiftCard row exists and is linked to
the claim. Legacy GiftCards that are not linked to a payment claim retain their
catalog-dependent behavior.

Paid callback fulfillment also resolves an existing claim before consulting
the current catalog. The claim's normalized buyer email, plan code, and duration
snapshot remain authoritative for repeated and new provider event IDs after a
plan is removed, renamed, or changes duration. A matching live catalog entry may
provide a display label only. Orders without a claim still require a supported
current plan definition.

The linked `GiftCard` plus claim is the canonical fallback-key store. Newly
issued raw keys are not copied into `ExternalOrder.meta_json`; a legacy
`fulfillment.access_key` is removed after its matching card is durably linked.
Retry delivery reconstructs the key from the linked card. Payment-linked redeem
status and response metadata use the claim's saved plan code and duration, not
the current catalog.

Payment callback audit JSON is structurally bounded before serialization.
`ExternalOrder.meta_json` preserves authoritative fulfillment, reversal,
pricing, buyer/order fields, and fixed safe evidence; oversized callback detail
is replaced with a valid redacted summary and fingerprint. Every
`ExternalPaymentEvent.payload_json` write uses the same valid bounded approach
and retains `_pokrov_processing_error` when present. Neither column is bounded
by slicing serialized JSON, so persisted values remain parseable within their
application limits.

Delivery evidence locks the order row and is monotonic: `sent`/`email_sent`
cannot be downgraded by a later failure, while an earlier failure may still be
upgraded to success. Bot gift redemption analytics never stores the raw code;
success and denial events store only last-four preview, a SHA-256 fingerprint
prefix, code length, and bounded non-secret outcome fields.

For a pre-claim paid order whose fulfillment metadata already references an
existing GiftCard, callback recovery links that row instead of inserting the
same code again only when the card is unredeemed, its type exactly matches the
claim plan, it was system-created (`created_by == 0`), and no other claim links
it. User/admin-created, redeemed, type-mismatched, or other-claim-owned cards put
the new claim into manual review with a fixed safe error code and never grant or
transfer access. Previously recorded successful email delivery is not repeated
while establishing this durable link.

Additive claim migrations give newly added required columns constant `NOT
NULL` defaults and PostgreSQL enforces `NOT NULL` after backfill only when
column metadata still reports nullable. SQLite cannot
add a constraint to a column that already existed as nullable without rebuilding
the table; this slice does not perform that destructive rebuild. Such incomplete
rows are backfilled to `manual_review` with timestamped migration error evidence,
and claim/payment/fallback service operations keep them quarantined.

Transactions that touch both account and claim lock the canonical account
before taking the claim row lock, after an initial non-locking claim lookup and
with revalidation. The attached paid-callback path composes mark-paid and grant
fulfillment under that same account-first order; an unattached race releases its
claim transaction before entering the attached path. Outstanding reversal
attention is global rather than bounded by the selected revenue period. Problem
rows from ordinary states and reversals share one descending created/id ordering
before the final display limit; reversal recency uses its safely parsed
`reversal.recorded_at` and falls back to purchase creation time. Reconciled
reversals are excluded. The global candidate query uses the additive
`external_orders(status, created_at, id)` index to select refund/chargeback
rows, then applies the conservative Python verifier to every candidate. This
avoids whole-blob substring filtering that could confuse nested callback data
with authoritative root reversal state. The residual cost scales with the
number of refund/chargeback rows, not all orders; a normalized reconciliation
column remains deferred rather than added destructively in this slice. Invalid
or out-of-range reversal timestamps safely fall back to purchase creation time. Live
PostgreSQL attach/merge/fulfill/redeem/reverse concurrency remains
`MANUAL_OWNER_TEST`; SQLite and unit lock-order tests are not production
deadlock evidence.

## Support

Support tickets and uploads are internally owned by nullable canonical account
UUID fields while retaining their legacy Telegram fields for attribution and
delivery compatibility. Public ticket and message payloads do not expose those
UUIDs. New writes persist canonical ownership when the authenticated account or
exact Telegram identity evidence resolves unambiguously.

User reads and authorization are account-first: an exact account match wins,
while exact Telegram-ID fallback applies only to rows whose canonical owner is
`NULL`. A matching Telegram ID never bypasses a different non-null owner, and
read-only requests never mutate ownership. A continuing user write may claim a
`NULL` legacy ticket only for its exact historical Telegram actor and that
actor's unambiguous canonical account. Linked identities of one account may
list, open, reply to, and download the same normal-session history; admin access
is unchanged. Active continuation chooses `updated_at DESC, id DESC` without
coalescing or deleting duplicate tickets.

Support ticket APIs must avoid exposing private attachments or session data in
public logs. `portal_bot/support_ai_service.py` applies one sanitizer before
length truncation to both outbound user text and inbound model text. Sanitizer
input and output are bounded to 65,536 characters and three percent-decode
passes plus one non-recursive decoded URL rescan. Residual nested percent-encoded
URL signatures fail closed through a linear structural probe instead of further
decoding. NFKC is applied incrementally and fails closed before its output can
exceed the bound; JSON escapes, HTML entities, zero-width characters, IDNA
separators, and Unicode compatibility forms are normalized within the same
bound. Provider model chunks are sliced before concatenation. Provider response
bodies are limited to 262,144 bytes by declared length and incremental stream
reads before JSON parsing.

Stable category placeholders cover Unicode email, proxy/private subscription
URLs, recovery and activation codes, hyphenated or compact UUIDs,
refresh/session credentials, common API and private-key forms, English or
Russian labelled credentials, Basic/Bearer authorization, and long digit
forms. Telegram init data is recognized only with a realistic numeric
`auth_date` and 64-hex `hash`; `query_id`, `user`, and `signature` are optional.
Recognized labelled or raw data is redacted through the end of its line so a
top-level pipe or HTML-entity separator cannot leave optional fields behind.
Mere `initData: empty` prose and placeholder documentation are not classified
as Telegram data.

After bounded normalization and Telegram handling, one scanner emits
alternating non-URL and URL spans. Generic credential/PII matching runs only on
non-URL spans. A safe URL is emitted directly and a private URL is replaced
directly; there are no internal shield markers or restoration pass. The
public-reference host allowlist is exact (`github.com`, `pokrov.space`,
`www.pokrov.space`, `docs.pokrov.space`, and `status.pokrov.space`), and leading
or trailing host dots are not stripped. Authority is validated before host
trust on every supported decode layer; malformed ports, encoded delimiters, and
quote/space userinfo confusion fail closed. Userinfo, canonical sensitive
query/fragment keys, semicolon or quoted nested assignments, keyless session
tokens, nested proxy/subscription URLs, POKROV endpoint tokens, subscription
token paths, and ticket UUIDs make the whole URL private. Genuine GitHub commit
and public docs reference URLs remain readable. Scan work, nested URL depth,
and output are bounded linearly.

Sanitized model text is the only model text returned for ticket storage.
Provider failure logging contains only a bounded status and fixed code; response
bodies and exception detail are not logged. Support-reply database failures in
API/helpbot log only `support_reply_persist_error`; rollback failures are
contained without exception detail. Session-close failures are also contained
and use only `support_reply_cleanup_error`. SQLAlchemy exception rendering hides
statement parameters.

`POST /api/client/support/assistant` is authenticated and normal-session only.
Its request uses `scope="support"`, a nonempty `message`, optional owned
`ticketId`, optional opaque `assistantSessionId`, and optional
`safeDiagnostics`. Snake-case aliases remain accepted during client migration.
The response always includes `reply`, `assistantSessionId`,
`suggestedActions`, `shouldEscalate`, and `source`. Public `source` is one of
`support_ai`, `support_agent`, or `local_fallback`; model output cannot choose
it.

The server generates an opaque 16--64 character session ID when one is absent
or malformed and returns the accepted ID on every response. It binds that
visible ID to the authenticated owner and the `app` surface before deriving an
internal key, so the same visible value submitted by another owner cannot join
the first owner's memory. Continuity is process-local RAM with a 60-minute TTL
and at most six safe messages; it is neither stored in the ticket nor persisted
across process restart. An optional `ticketId` is authorized before any model
or tool call.

Client-authored diagnostics enter through a fixed allowlist. Before the harness
call, the authenticated endpoint adds an identifier-free, same-account snapshot:
access state and days left, normalized plan code, active-device count, whether
Telegram is linked, Telegram-bonus state, and bounded panel runtime facts
(online/offline/unavailable, active-connection count, last-online age). Server
facts override colliding client keys. The model receives those scalar facts only
for the current synthesis request; they are not added to agent memory. Raw
account/Telegram/device IDs, usernames, email, node hosts, subscription URLs,
keys, configs, payment data, and panel payloads are never admitted. Event
metadata records diagnostic key names, not values. The harness is limited to six
requests per authenticated owner per rolling minute even if the client rotates
session IDs. Failure, missing support knowledge, and agent escalation still
return a safe `local_fallback` response with `shouldEscalate=true`; they do not
turn an API error into an unsafe provider-body echo.

Authenticated normal client/admin attachment behavior remains available under
the owner/admin contract. The limited recovery projection is text-only and
cannot upload, download, submit, or receive attachment metadata.

The release 1.2 encrypted support-bundle key set and extended collection policy
are defined under `shared/contracts/support/`. Normal authenticated sessions may
read the signed public key set at `GET /api/client/support/bundles/key-set`,
create or reuse a case-bound upload at
`POST /api/client/support/bundles/upload-tickets`, send sequential resumable
ciphertext chunks to `PUT /api/client/support/bundles/uploads/{upload_id}/chunks`,
read the server-authoritative offset/status with the matching `GET`, and queue
completion with the matching `POST .../complete`. Recovery scope is denied.

Temporary support mode is case-bound and separate from upload. An operator with
`support.write` prepares and executes the L2 `support.mode.issue` action through
`/api/admin/v2/support/action-intents`; the payload has an exact expected ticket
version, environment, platform/app/build audience, TTL, category/collector
allowlists and per-bundle/cumulative caps. The database retains only the
activation-code SHA-256. The initial result returns one `PSM1-*` code; an
idempotent action replay can deterministically recover it only while the policy
is still issued and unexpired.

A normal authenticated owner redeems that code once at
`POST /api/client/support/mode/redeem` with exact platform, app version and build
number. The server rechecks owner, audience, status and expiry, consumes the
code and returns an Ed25519-signed v2 collection policy. Audience mismatch does
not consume it; replay does not reactivate it. Recovery scope is denied. The
closed payload contains no command or mutation field and grants only bounded
diagnostic collection; it cannot change VPN/routes/DNS, read user files,
capture traffic/destinations, expose tokens/configuration, hide its indicator
or self-extend.

The client-local `PSD1-*` support code is decoded without upload by
`GET /api/admin/v2/support/diagnostic-codes/{code}` with `support.read`. The
response is limited to platform, route/connection class, app/build,
issue/expiry date and a short diagnostic hash prefix. It has no owner,
account/device/install identity or arbitrary metadata and is not evidence that
a support bundle exists.

The upload ticket is HMAC-signed, short lived, and bound to the canonical
account (or server-owned anonymous nonce), support case, upload/bundle ID,
declared byte size, SHA-256, exact encrypted-envelope MIME and expiry. Ticket
creation, chunk replay and completion are idempotent; conflicting replay fails
closed. The web process stores bounded opaque ciphertext only and never imports
the decrypt/ingest service. An opt-in isolated worker verifies the complete
layout, decrypts with a mounted private recipient key, validates the closed
manifest/file/redaction schemas and hostile corpus in memory, and retains only
the original encrypted object in accepted storage. Rejected material remains
encrypted in private quarantine. No production key custody, deployed storage,
worker schedule or successful real upload is claimed without exact `I4`
evidence. A plaintext prepared bundle must never use the legacy upload API.

Authenticated admins may read the bounded release-health aggregate at
`GET /api/admin/observability/release-health` and the version/candidate-scoped
known-issue registry under `/api/admin/observability/known-issues`. These views
contain only closed build/platform/count/code fields. Incident and release
references are observational strings: neither endpoint creates incidents,
compensation, entitlements, payments, support cases, or release authority.

Every admin is support L1 and may read only
`GET /api/admin/support/bundles/{upload_id}/summary`: phase, safe code, attempt
count, build, proof outcome, byte progress, hold flag, and a bounded timeline.
It does not return owner/account binding, object path/name, token hash, raw
bundle content, domains, IPs, package names, or configuration. Ciphertext
download and retention-hold mutation require the actor's numeric Telegram ID in
the explicit `POKROV_SUPPORT_BUNDLE_L2_TG_IDS` allowlist. L2/SRE first issues a
case/upload-bound, fixed-reason, audited grant valid for at most 15 minutes,
then supplies it once in `X-Pokrov-Support-Grant` to the content endpoint. The
API verifies the private canonical filename, byte length, and SHA-256 before
returning the original encrypted envelope; it never decrypts it.

`portal-worker` applies bounded-batch retention to release-health rows,
accepted encrypted objects, rejected/incomplete quarantine chunks, upload rows,
and access-audit rows. Explicit bundle/audit holds are skipped and counted.
Deletion reports contain integer counters only. Local tests prove selection,
path ownership, holds, and counters; production execution/backlog/permissions
and real-user RBAC remain `I4` evidence.

`POST /api/tickets/uploads` stages a private file and preserves the legacy
`attachment` plus `attachment_payload` response while adding an opaque
`attachment_id` equal to the stored server identifier. New rows expire after
`SUPPORT_PENDING_UPLOAD_TTL_HOURS` (default 24). Account-first pending quotas
count only unexpired, unbound rows and default to
`SUPPORT_PENDING_UPLOAD_MAX_COUNT=5` and
`SUPPORT_PENDING_UPLOAD_MAX_BYTES=52428800`; without a canonical account, only
the exact legacy Telegram owner is counted. Upload admission may remove only
that same owner's expired rows with non-null `expires_at` while both `ticket_id`
and `message_id` remain null. Legacy null-expiry, bound rows, and other owners'
rows are never swept by admission.

Ticket create/reply accepts optional `attachment_id`. It cannot be mixed with
nonempty media fields (`400 support_attachment_invalid`). Missing, foreign, or
expired staged IDs return `404 support_attachment_not_found`; a previously
bound row returns `409 support_attachment_already_bound`. Admin ticket access
does not permit an operator to bind another owner's staged upload. The server
loads canonical media metadata from the persisted row, flushes the message,
then conditionally sets `ticket_id`, unique `message_id`, `attached_at`, and a
null `expires_at` in the same transaction. A concurrent loser rolls back its
message and ticket mutation.

Rolling clients may omit `attachment_id` and send the exact historical
`support/{stored_name}` private triplet. The server resolves ownership and
semantic metadata before canonicalizing and binding it. Forged or mismatched
`support/*` references fail closed. Non-private Telegram/client triplets remain
unchanged. Bound download authorization follows the bound ticket; unbound and
legacy rows retain exact owner/admin fallback. Recovery scope remains denied
even when its synthetic actor ID numerically equals the configured admin ID. An
unbound row with an explicit `expires_at <= now` returns `404` to both owner and
admin; bound history and legacy null-expiry rows retain their existing access.

Upload finalization fsyncs the exclusive temporary file, atomically renames it,
and fsyncs the containing directory on POSIX before attempting the attachment
row commit. Once rename succeeds, any persistence or commit-acknowledgement
exception preserves the final file. A durable committed row therefore is not
turned into a missing-file row by error cleanup; a verified rowless final is
left for grace-period reconciliation. Temporary paths are still cleaned.

The supervised support-attachment cleanup job defaults to a 900-second interval,
3600-second orphan safety grace, 100 expired rows per batch, 500 selected file
candidates, and 500 DB-row observations per run. It conditionally deletes only
explicit-expiry unbound rows, uses PostgreSQL `SKIP LOCKED`, removes old temp and rowless
canonical files after grace, and checks the exact canonical basename and DB row
again before unlink. Its DB missing-file query and file candidate processing are
bounded, deterministic, and non-destructive across bound, unexpired, and legacy
rows. At the start of each cycle, one worker-held cursor freezes a DB max-ID
high-water and a filesystem mtime cutoff; bounded windows then advance by row ID
and filename without admitting newer entries into that active cycle. Integer
wrap flags report cycle completion without logging names, IDs, cutoffs, or
cursors. The process-local snapshot resets after worker restart. File candidate
selection uses bounded memory but enumerates the whole upload directory once per
run, so large-directory latency remains an operational measurement gate.

The schema change is additive for SQLite and PostgreSQL: nullable indexed
`ticket_id`, nullable unique/indexed `message_id`, nullable `attached_at`, and
nullable indexed `expires_at`. Runtime migration is rerunnable and creates no
physical foreign key or destructive table rebuild. Rehearsal checks report
counts/status for missing tickets, missing messages, and attachment/message
ticket mismatch.

Notification routing does not grant access. Operator replies use a bounded,
deterministic target order: explicit linked Telegram, enabled Telegram identity,
then the historical ticket ID only when it is a real Telegram target. With no
real target, delivery is skipped and logged without content or provider data.

## Admin

Admin APIs must keep payment, download, node, ticket, and user states audit-friendly. Telegram admin remains fallback-only; `adminapp` is the primary operator surface, while webapp admin routes are a temporary parity fallback.

### Admin API v2 identity envelope

`/api/admin/*` remains a compatibility contract. New Operator Center contracts
live under `/api/admin/v2/*` and use the bounded top-level shape `data`, `meta`,
`sources`, `warnings`. Missing deployment evidence is represented as `null`
plus a machine-readable warning; the server must not invent a commit, release,
schema, source or freshness value.

`GET /api/admin/v2/meta` returns:

- `data.app = pokrov-operator-api`, `data.api_schema = admin-v2.1`, the expected
  frontend app, and optional portal commit, deployment time, DB schema, active
  client release and core release;
- `meta.generated_at`, optional `trace_id`, `schema_version` and bounded
  `query_ms`;
- an empty `sources` list until source-bearing read models are migrated;
- one `deployment_identity_missing` warning per absent optional identity field.

The matching static candidate declares `pokrov-operator-center`, expected API
schema `admin-v2.1`, its exact route-manifest hash and its exact cutover-matrix
hash in `__build.json` and `__routes.json`. A frontend/API or build/route/cutover
identity mismatch is a hard candidate failure.

`WO-009B` adds the persistent operator security boundary, and the `OC-100`
closure adds the primary OIDC entry:

- `GET /api/admin/v2/auth/oidc/start` creates a purpose-specific Telegram OIDC
  Authorization Code + PKCE request. The public state omits the verifier; a
  separate `__Host-pokrov_admin_oidc` Secure/HttpOnly/Strict cookie retains the
  verifier; both values are signed by the dedicated operator-session secret
  and matched on CSRF nonce, redirect URI and login/step-up purpose;
- `POST /api/admin/v2/auth/oidc/finish` accepts only an already provisioned,
  active Telegram-linked operator with at least one active role in the exact
  environment. It never creates an operator or grants `superadmin`;
- `POST /api/admin/v2/auth/bootstrap` first runs the existing verified legacy
  admin resolver and exchanges that identity for an opaque session. The raw
  48-byte token is returned only in the
  `__Host-pokrov_admin_session` cookie with `Secure`, `HttpOnly`,
  `SameSite=Strict`, `Path=/` and no `Domain`; the JSON body never contains it;
- the database stores only the domain-separated HMAC of the token. Sessions
  have bounded idle and absolute expiry, environment scope, last-seen,
  optional step-up time and explicit revoke state;
- `GET /api/admin/v2/auth/me` returns the current operator, active roles,
  effective permissions, expiry fields and the CSRF token derived for the
  current session. `GET /api/admin/v2/auth/sessions` lists at most 50 sessions
  for that operator/environment; `POST .../{session_id}/revoke` cannot target
  another operator;
- `POST /api/admin/v2/auth/logout` revokes the current session, deletes the
  cookie and returns `Clear-Site-Data: "cookies", "storage"`;
- unsafe methods require the derived `X-Pokrov-Admin-CSRF` value and reject a
  supplied Origin outside `ADMIN_OPERATOR_TRUSTED_ORIGINS`. Missing or invalid
  session configuration, environment, role, permission, CSRF, expiry and
  revocation fail closed;
- the role registry enumerates permissions; unknown roles grant nothing.
  Active role rows are re-read on every request. The v2 dependencies check an
  explicit permission and may additionally require a fresh step-up;
- OIDC login, bootstrap, session revoke and both step-up methods write an additive audit
  record with operator/session, environment, result/reason, safe correlation
  ID and the exact role/permission snapshot used for the decision.

The primary step-up repeats the purpose-bound OIDC flow and requires the
verified Telegram identity to match the current session. Compatibility
bootstrap and initData step-up can be disabled together with
`ADMIN_OPERATOR_LEGACY_BOOTSTRAP_ENABLED=false`; while enabled, they remain
explicitly weaker cutover paths. The
frozen legacy `/api/admin/*` routes may temporarily accept the v2 cookie only
with `legacy.admin.access`; unsafe legacy calls still require the v2 CSRF. The
v2 frontend no longer calls `/api/admin/auth/session`, persists no bearer or
raw initData, and reads raw initData only from the live Telegram runtime for
bootstrap/step-up exchange. The legacy bearer endpoint remains available to
the frozen fallback during the strangler cycle.

Live provider, exact-candidate and public-origin proof remains an I4 gate; local
tests do not claim BotFather registration or production identity migration.

### Operator work and incident boundary

`WO-009D` adds the first server-owned work read models under `/api/admin/v2`:

- `GET /shift` returns the current environment/operator/team context plus
  mine/team/unassigned tasks and bounded queues for failed commands, tickets,
  active incident work, payment review, release blockers and source failures;
- `GET /tasks` returns operator tasks with owner/team/status/priority/due time,
  next action, source, optional linked entity and optimistic `version`;
- `GET /incidents` and `GET /incidents/{incident_id}` return the existing
  `ServiceIncident` authority with additive workflow fields. Detail includes the
  append-only timeline, typed linked entities, linked alerts and follow-up tasks;
- `POST /shift/action-intents` and `POST /incidents/action-intents` prepare a
  version-bound preview. Their `.../{intent_id}/execute` routes execute only the
  stored canonical action/target/payload with normal intent expiry,
  confirmation, idempotency and audit rules.

Task and incident transitions reject a mismatched `expected_version`. Alert
acknowledge, false-positive, link-existing-incident and create-incident are
explicit actions with alert version checks; linking also checks the target
incident version. Resolve/cancel update the same incident root used by public
status. `incident.compensate` is L3, requires the high-risk permission and fresh
step-up, and delegates to the pre-existing idempotent compensation service.
Read projections do not expose user/account identifiers from ticket or payment
queues, and none of these routes creates a second ticket, payment, alert,
incident, compensation or entitlement authority.

### Operator support work boundary

`portal_bot/support_work_service.py` owns the environment-scoped Support Inbox,
ticket detail, User 360 and attempt projections. `SupportTicket` remains the
single ticket authority and is extended additively with priority, queue,
assignment/team, waiting-on, SLA, escalation, incident/attempt links and an
optimistic integer version. Existing user/helpbot/admin entry points continue
to use `tickets_repo`; there is no second support database or dual write.

The modular routes are:

- `GET /api/admin/v2/support/tickets` and `GET .../tickets/{ticket_id}` with
  `support.read`;
- `GET /api/admin/v2/support/macros` and
  `GET /api/admin/v2/support/users/{tg_id}` with `support.read`;
- `GET /api/admin/v2/support/attempts` with `support.sensitive.read`;
- prepare/execute under `/api/admin/v2/support/action-intents` with
  `support.write`.

Claim, assignment and workflow update are native v2 action-intent policies.
Reply/status and internal-note compatibility routes resolve the same stored
intent and recheck the expected ticket version before mutation. Internal notes
are stored with `visibility=internal`, returned to the operator projection and
excluded by default from every user ticket/message read.

User 360 never serializes `Event.meta_json`. The adapter allowlists bounded
client/core fields, replaces raw account/install/device/session/attempt/trace
identity with purpose-scoped opaque references, and groups correlated attempts
and diagnostic fingerprints server-side. Support-bundle data remains a bounded
summary with TTL, retention and access-audit facts; observer state remains a
trusted read-only projection. None of these reads grants entitlement, exposes
raw IP/token/config/URL material, or changes support-bundle custody.

### Operator network work boundary

`WO-009F1` moves the network vertical to `/api/admin/v2/network/*` without
creating another node, probe, alert, provider, traffic or emergency authority:

- `GET /fleet` returns a bounded fleet projection from Node 360 with explicit
  inventory, brain/runtime, RU and alert sources;
- `GET /nodes/{node_code}` returns lifecycle, capacity, independent source
  freshness, bounded network health, safe transport summaries, RU state and
  active alerts;
- `GET /traffic` accepts ISO `from`/`to`, rejects reversed intervals and bounds
  the interval to 120 days; it reads existing usage rollups only;
- `GET /alerts` is environment-scoped and has no alert refresh or delivery side
  effect; `GET /providers` reads quota configuration/status without polling a
  provider, and replaces notes with `notes_present`, `notes_length` and
  `notes_sha256`;
- `GET /ru/latest`, `GET /ru/runs` and `GET /ru/uploader` expose the signed
  RU-origin evidence pipeline and uploader health as separate read models;
- `GET /emergency` exposes the existing bounded emergency catalog admin status.

All read routes require `network.read`. Fleet/Node 360 omit host, panel URL and
credentials, subnet, raw endpoint material, signatures, keys and provider note
text. If RU manifest configuration is invalid, fleet and Node 360 keep the
other authorities available with `ru_origin.status=failed` and
`reason_code=ru_configuration_invalid`; the dedicated latest endpoint returns
`503` with `error.code=ru_configuration_invalid`.

`POST /network/action-intents` and
`POST /network/action-intents/{intent_id}/execute` require `network.write` and
reuse the one stored Action Intent registry. Allowed actions are the existing
node, provider-quota and emergency-catalog commands plus version-bound
`alert.silence`. `provider_quota.delete`, `node.sync_global`, `node.disable`,
`emergency_catalog.promote`, `emergency_catalog.disable` and
`emergency_catalog.rollback` additionally require `command.high_risk` and a
fresh step-up. The execute route always rechecks the stored action, target,
payload, entity version, confirmation hash, expiry and idempotency key; the
browser never executes the old network mutation route for a migrated action.

### Operator money and growth work boundary

`WO-009F2` moves money/access and the bounded bonus/program capabilities to
explicit v2 projections. Admin API v2 remains a BFF: orders, signed callbacks,
payment claims, entitlement grants, provisioning outbox, promos, AppSetting and
program applications keep their existing owners. Every route below fails with
`409 money_environment_unavailable` outside the production commerce
environment instead of fabricating empty operational truth.

Money reads require `money.read`:

- `GET /api/admin/v2/money/payments/summary?period=today|7d|30d` returns revenue,
  order/callback state counts and separate mismatch queues. In particular,
  `paid_without_entitlement`, `callback_failed`, `grant_failed` and outbox
  attention remain distinct;
- `GET /api/admin/v2/money/payments/orders` is a bounded, filtered order list;
  `GET .../orders/{provider}/{order_id}` joins redacted order, callback, claim,
  grant and outbox lineage without returning raw payloads, buyer email, provider
  event identity, tokens or secrets;
- `GET /api/admin/v2/money/access` returns grant/outbox/key aggregates, recent
  grants, the shared tariff catalog and redacted gift-code hints. Its authority
  explicitly sets `telemetry_confirms_payment=false`;
- `GET /api/admin/v2/money/free-archive` is a read-only projection of raw legacy
  `FREE` rows and shared retirement facts; `GET /api/admin/v2/money/promos`
  returns only bounded promo fields.

Growth reads require `growth.read`:

- `GET /api/admin/v2/growth/bonuses` returns allowlisted wheel and loyalty
  configuration. Stored Action Intent previews expose only current metadata and
  before/after fingerprints for JSON configuration;
- `GET /api/admin/v2/growth/programs` filters the existing application queue and
  replaces account/grant primary keys with purpose-scoped opaque references.

Prepare/execute use `/api/admin/v2/{money|growth}/action-intents` and their
workspace write permissions. Payment reconcile, promo changes, access-key/gift
issuance, bonus configuration and program review reuse the single stored Action
Intent registry. L3 issuance and program review require the existing high-risk
permission and fresh step-up. A generated gift/access code is returned only in
the successful execute response and is not added to later read models.
`program_application.review` rechecks the application version and calls the
existing program service; approval with reward and its idempotent entitlement
grant commit atomically, so replay cannot create a second grant.

### Operator release and messaging boundary

`WO-009F3` moves the release cockpit and operator messaging onto explicit v2
contracts without introducing a release, telemetry, support or publication
authority. Release reads require `releases.read`:

- `GET /api/admin/v2/releases/candidates` lists the existing imported release
  candidates;
- `GET .../candidates/{candidate_id}/cockpit?hours=1..168` binds the candidate
  to every imported component with the same version, exact revision,
  artifact/descriptor SHA-256, current/brain/RU readiness, an eleven-check
  diagnostic gate matrix, aggregate version adoption, release-health delta,
  version-bound support-bundle delta and candidate-scoped known issues;
- `GET /api/admin/v2/releases/adoption?days=1..90` groups active device rows by
  platform/version and distinct installation count. It returns no account,
  install, device, session, IP or destination identity.

Release writes require `releases.write` and use only
`POST /api/admin/v2/releases/action-intents` plus execute. The allowlist is
`release.rollout.start`, `change`, `pause`, `rollback`, `min_supported.set` and
`observation.close`. Start/change/rollback/minimum-version are L3 and require
`command.high_risk` plus fresh step-up; the other two are L2. Start fails until
the exact candidate has complete origin and diagnostic gates. Observation close
fails until its bounded window ends and the version-specific health deltas are
inside the stored thresholds. Every execute rechecks the candidate and rollout
registry snapshot.

The rollout registry is the versioned `AppSetting.release_rollout_v1` document;
it is an operator policy pointer, not an artifact store. Rollback activates a
retained registry state and returns `external_artifact_switch=NOT_PERFORMED`.
The public/client app-list APIs therefore fail closed to `rollout_percent=0`
when rollout is paused, rollback is requested, the registry is invalid, or the
active candidate version differs from configured artifact metadata. They do
not claim that an external download pointer was switched.

Growth messaging reads require `growth.read`: delivery aggregate by broadcast
intent, bounded news-draft/run state, live updates with `source_draft_id`, and
intent status. `broadcast.send` and `live_update.create|update|delete` use the
single growth action-intent prepare/execute boundary; broadcast remains L3.
Delivery output contains aggregate counts, reason categories and timing only,
never recipient ids or raw Telegram responses. News collection still cannot
publish autonomously.

### Operator governance, audit and privacy boundary

`WO-009F4` adds the server-owned governance work model under
`/api/admin/v2/governance/*`. It extends the existing operator, role, session,
Action Intent, `AdminAudit`, support-bundle audit and retention authorities; it
does not create a parallel identity provider, entitlement system or event store.

Operator, role, session and operator-audit reads are environment-scoped and
deny by default:

- `GET /roles` returns the static role/permission registry and temporal-access
  rules. Unknown roles grant nothing;
- `GET /operators` and `GET /operators/{operator_id}` return bounded operator,
  role and session projections. Raw session tokens, token hashes and CSRF values
  are never serialized;
- an active role must be unreleased and either have no `expires_at` or expire in
  the future. Effective permissions are recomputed from active rows on every
  request, so expired JIT/break-glass access fails on the next authorization;
- `GET /audit` is bounded to 1000 rows and filters by actor, role, permission,
  action, result, resource, command intent and time. `GET /audit/export` exports
  the same allowlisted fields as UTF-8 CSV and neutralizes spreadsheet formula
  cells;
- `GET /audit/commands/{intent_id}` joins the canonical Action Intent, the
  compatibility `AdminAudit` and the operator audit rows. It returns hashes,
  outcome and safe snapshots, not stored payload/result JSON;
- `GET /sensitive-access` projects retained support-bundle access decisions
  without grant token hash or bundle contents. Sensitive-log reads and CSV
  exports write their own operator audit row in the same request. The retained
  support-bundle authority has no environment column, so the response labels
  that source explicitly as global legacy scope;
- `GET /privacy` reports configured raw-telemetry and support-bundle retention,
  current database counts/holds and the allowlisted/excluded field inventory.
  It is local runtime state, not hosted-worker or production cleanup proof.

Governance writes require `governance.operators.manage`, current step-up, CSRF,
trusted Origin and the stored Action Intent lifecycle. Allowed actions are
`operator.role.grant|revoke`, `operator.suspend|activate`,
`operator.session.revoke` and `operator.access.review`. Grant supports standing,
JIT (15--1440 minutes) and break-glass (5--60 minutes); temporal grants require
reason and later review. Self role/status changes, temporal superadmin, regrant
before pending review, and removal/suspension of the last active superadmin fail
closed. Suspension revokes every active session for that operator. Every
successful v2 command writes the compatibility and operator audit records in
the same transaction, linked by intent and audit IDs with the exact
role/permission decision snapshot.

### Operator role usability and field-redaction boundary

`WO-009I` closes the local `OC-110` implementation gap without granting broad
legacy administrator access. The retained bridge is an exact deny-by-default
matrix over `method + FastAPI route pattern`: user list/card use
`support.read`, investigation uses `support.sensitive.read`, promo-slot read
uses `money.read`, staged promo-media upload uses `money.write`, and global
search accepts any support/network/money read permission. Every unlisted
legacy route still requires `legacy.admin.access`.

Search is projected by effective permission: support can receive user/key,
network can receive node, and money can receive order results. L1 support does
not query email, install, device or linked-identity search fields. User list and
card responses include explicit field-access states. Without the relevant
permission the service does not query Event, payment-order or administrator
audit rows and returns redacted identity fields plus empty protected
collections labelled with the required permission. Safe user, ticket, key,
risk and observer projections remain available.

`GET /api/admin/v2/support/users/{tg_id}` follows the same rule. It returns the
safe entity/ticket/observer projection with `support.read`; installation,
session, attempt and fingerprint collections require
`support.sensitive.read`. The lower-level service requires an explicit boolean
from the authenticated route, so a new caller cannot silently default to the
sensitive projection. The AdminApp renders redaction as a permission state and
does not present protected empty arrays as proof that no data exists.

Domain roles that own L3 actions (`sre`, network, payments, growth, releases
and incident command) now carry `command.high_risk` alongside their domain
write permission and `session.step_up`. Authorization still requires all three
conditions: action-specific domain write, high-risk permission and a fresh
step-up. Readonly, support and security-auditor roles receive no high-risk
command permission. Promo-slot updates use the native money Action Intent
boundary; the retained write route receives no new direct capability.

These are local role-matrix and route tests. External IdP, production role
assignment/readback and exact-candidate authenticated proof remain unclaimed.

### Generated Admin API v2 contract boundary

`WO-009H` makes the live `/api/admin/v2/*` router the source of one deterministic
OpenAPI artifact instead of maintaining a parallel handwritten schema. The
generator imports the composed FastAPI application, selects only v2 paths and
requires exact one-to-one coverage with the canonical `ROUTE_PERMISSIONS`
matrix. The retained artifact is
`shared/contracts/admin/admin-v2.openapi.json`; the generated browser consumer
is `adminapp/src/lib/admin-api/generated/admin-v2.ts`.

The local contract currently contains 73 unique method/path operations. Every
operation has a stable method/path-derived `operationId`, exact permission,
session-cookie security declaration and explicit CSRF requirement. Seventy-one
JSON operations use a Pydantic response model with the exact top-level
`data/meta/sources/warnings` success envelope and common structured error
responses. Governance CSV export and encrypted support-attachment download are
the two explicit binary operations. List limits are bounded to at most 1000;
the two offset parameters are bounded to `0..100000`.

The generated TypeScript table supplies path/query/body types, response kind,
permission and CSRF metadata for all 73 operations. The browser client matches
every v2 request against that table and rejects an unknown method/path with
`admin_v2_contract_mismatch`. A successful JSON response is rejected with
`admin_v2_envelope_invalid` unless its top-level keys and meta shape match the
generated envelope. Legacy `/api/admin/*` compatibility reads are deliberately
outside this contract and receive no new capability through generation.

`python scripts/generate_admin_v2_openapi.py --check` and
`npm --prefix adminapp run check:sdk` are the clean generation gates; the SDK
check is also part of the AdminApp prebuild. These are local source checks, not
evidence that the schema was published for an exact candidate or that an
authenticated staging/production consumer read it back.

### Operator Center local cutover boundary

`operator-center.cutover.json` covers all 28 canonical routes in seven
capability groups and records their read authorities, action boundary and
redaction check. The browser-facing compatibility projections for overview,
online state, funnel and referrals are exposed through permissioned v2 routes:
`GET /shift/overview`, `GET /support/online`, `GET /growth/funnel` and
`GET /growth/referrals`. `referral.process` uses the growth Action Intent path.
Those projections are production-only and fail closed in another operator
environment.

Five older user/search/promo API patterns remain explicitly read-only. Unsafe
compatibility calls still require stored Action Intent and the single owning
domain executor; promo media upload stages a content-addressed asset but does
not publish slot configuration. Local parity does not authorize canonical
redirects or public-shell removal. Authenticated staging/production smoke,
exact served fingerprints and an executed static rollback remain separate
candidate-bound evidence.

## Marketing pilot surfaces and decision readback

`GET /api/dashboard` and `GET /api/client/promo-slots?surface=app|webapp`
may return at most one dynamic `winback_offer` for an already eligible exposed
assignment. The server re-evaluates the campaign legal/capacity policy and
requires exact pilot digest, channel, subject HMAC, live offer/creative,
audience status, schedule, price and paid-cap bindings. App uses
`app.home.banner`; cabinet uses `webapp.subscription.contextual`. A missing or
blocked assignment produces no dynamic slot and never blocks normal product
access.

The slot carries exact price, absolute end time, terms URL, conservative
remaining quota and the closed pilot/commercial/campaign/offer/creative/
variant/assignment/impression/click lineage. Checkout uses a signed ticket
containing the same impression/click IDs. `POST /api/events` accepts commercial
`promo_*` telemetry only when the complete lineage resolves to the authenticated
subject; partial, stale, unknown or conflicting lineage returns 400. Telemetry
is advisory and cannot grant access, consume quota or select a winner.

`GET /api/admin/campaigns/{campaign_id}/pilot-decision` is admin-authenticated
and winback-only. It returns the identity-free attribution projection,
legal/capacity/quota/payment/support/incident guardrails, mature
`net_revenue_30d_per_capacity_unit`, holdout state, recommendation, related
Action Intent rows and a postmortem projection. Missing D30/holdout evidence is
`insufficient_data`; it is never fabricated as zero. The endpoint is read-only
and cannot launch, stop or scale a campaign.

## Selected Feature API Additions (2026-07-23)

- `GET /api/public/status` returns current/recent operator-owned incidents and a
  bounded checked timestamp; it is public read-only state, not a client-side
  outage detector.
- `POST|GET|DELETE /api/client/device-pairing/codes*` require a normal
  authenticated client session. Only the creation response contains the full
  eight-character code; storage uses a dedicated HMAC and list responses expose
  only the last-four hint.
- `POST /api/client/device-pairing/claim` is unauthenticated by design but
  rate-limited by IP and code/install fingerprints. A valid unexpired one-time
  code creates a normal device session, enforces the account device limit, and
  cannot move an existing install between accounts.
- Every authenticated client route that persists or signs device-scoped state
  resolves `install_id` from the token's active `AccountDevice`. The legacy
  `users.app_install_id` fallback applies only to compatibility bearers without
  a `device_id` claim; a paired phone never inherits the owner's old install.
- `GET /api/client/programs` returns public capabilities and owned
  applications. Application create/cancel is account-scoped; switch, research,
  and team-pack submissions require manual review, while affiliate is disabled.
- `GET /api/bonuses/summary` additionally returns anonymized referral
  conversion/history, evidence-backed achievements, and useful quest progress.
  `routing_lesson_completed` is an allowed bounded client event.
- admin incident create/resolve/compensate and program review routes remain
  admin-authenticated and audited. Incident compensation is idempotent per
  incident/account ledger key.

New tables are additive through the repository's `create_all` startup path:
`service_incidents`, `incident_compensations`, `device_pairing_codes`, and
`program_applications`. No endpoint returns stored code HMACs, operator notes to
normal clients, or invited-user identity.

## Emergency offline bundle

`POST /api/client/emergency-network/offline-bundle` requires a normal app
session and JSON `{ "manual_limited_network": boolean, "precache_only"?:
boolean }`. `precache_only=true` may issue the signed device-bound bundle for
an active trial/paid account before RU/manual network confirmation, but the
catalog is marked `entitlement_precache` and remains activation-gated in the
client. Older requests without that flag keep the RU/manual gate. It returns
`pokrov-emergency-offline-bundle-v1` with one signed safe catalog and the exact
signed profile envelope for every fresh or still-valid signed last-known-good
reserve and advertised chain mode.
The response is `Cache-Control: no-store`, contains 4–20 reserves selected from
the rolling 24-hour exact-verified pool and no more than 36 profiles, and fails closed on entitlement, activation eligibility,
catalog, crypto, topology, or profile errors. Each envelope is bound to the
current install and expires no later than the active access, catalog,
eligibility, or seven-day offline lease.
Current-revision successes are ordered first; remaining slots may reuse recent
exact successes from retained revisions only when their stable material identity
matches and the host is not already represented. Probe age remains visible as `working` versus `stale`, but it does not shorten
an already signed catalog lease. Expired, unhealthy, unauthenticated, or
unsigned material still fails closed.
