# API Contracts

Last updated: 2026-08-14

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
bridge allowlist/exclusion rules, and the node's required delivery transport is
enabled. Each bridge item exposes only stable endpoint `id`, short operator
label, and the fixed consumer description `Для ограниченных сетей`; it never
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
session and exact JSON `{ "manual_limited_network": boolean }`. It returns
`pokrov-emergency-offline-bundle-v1` with one signed safe catalog and the exact
signed profile envelope for every fresh or still-valid signed last-known-good
reserve and advertised chain mode.
The response is `Cache-Control: no-store`, contains 4–12 reserves and no more
than 36 profiles, and fails closed on entitlement, RU/manual eligibility,
catalog, crypto, topology, or profile errors. Each envelope is bound to the
current install and expires no later than the active access, catalog,
eligibility, or seven-day offline lease.
Probe age remains visible as `working` versus `stale`, but it does not shorten
an already signed catalog lease. Expired, unhealthy, unauthenticated, or
unsigned material still fails closed.
