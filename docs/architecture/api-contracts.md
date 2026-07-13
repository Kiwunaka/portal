# API Contracts

Last updated: 2026-07-12

This page captures release-critical API contract expectations for Open Beta v4.

## Client Apps

`GET /api/client/apps` must return only approved runtime links. Empty Android or Windows URLs mean the corresponding public download is not available and must be presented as gated/support-routed.

### Device Sessions

The repository candidate implements the following Android/Windows session
contract. It is not production evidence until the deployment and client gates
in the active work order are complete.

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
- Recovery scope is checked on every authenticated request. It can reach only
  account status, support tickets, device list/revoke, logout and audited
  reissue. It cannot link a new identity, create payment ownership, read
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

- Signed `POST /api/internal/observer/batches` observations resolved to a
  canonical account are the activation source. Each accepted observation adds
  append-only `connection_evidence` with account, optional device, node,
  evidence kind, observed timestamp, and a unique stable evidence key.
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
  `connected_ok`, funnel events, and other client-authored telemetry are never
  activation evidence.
- The worker expires unactivated reservations after `7 days` and updates only
  the legacy compatibility projection to `free_monthly` when no paid or
  unrelated active grant or current `User` projection survives. This projection
  guard remains required while payment and bonus paths have not all cut over to
  grants. Panel synchronization remains retryable and cannot fabricate evidence.

### Free Profile Provisioning

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
  `rotate_access_key` job contract. Errors persist only stable redacted codes.
- Target profile ensure and exact confirmation happen before source disable.
  Reset additionally clears standard traffic before soft disable. A payment or
  entitlement projection that supersedes an in-flight free job must not be
  overwritten during finalization. The worker compensates a superseded panel
  mutation by disabling the free target and restoring the paid source, or the
  last confirmed standard source when paid provisioning is not yet visible;
  failed compensation goes directly to manual review.
- Expiry/revocation re-entry uses the same durable reset job: it confirms and
  clears standard first, then disables every configured paid source and a stale
  soft source. Merely changing `sub_type` or `current_plan_code` is not panel
  synchronization proof.
- `free_standard`, `free_soft`, `paid`, and `operator_lab` are explicit node
  roles with positive non-duplicated inbound bindings. Missing free roles never
  fall back to paid or operator-only nodes.
- Public locations, subscription rendering, legacy control-panel helpers, and
  admin resync all resolve the persisted free role. Transition/error states
  cannot be force-resynced by legacy admin actions. Expiry monitors only queue
  the durable re-entry job and do not mutate panel profiles directly.
- A confirmed reset starts a fresh full 30-day cycle. Migration retains any
  prior invalid node role in `access_role_legacy` before heuristic backfill so
  an application rollback can restore the old value without deleting evidence.

## Payment Providers

`GET /api/payments/providers` must expose provider availability and enough unavailable-state detail for checkout to avoid presenting blocked payment paths as live.

## Support

Support ticket APIs must avoid exposing private attachments or session data in public logs. Attachment privacy remains a beta hardening item.

## Admin

Admin APIs must keep payment, download, node, ticket, and user states audit-friendly. Telegram admin remains fallback-only; web admin is the primary operator surface.
