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

## Payment Providers

`GET /api/payments/providers` must expose provider availability and enough unavailable-state detail for checkout to avoid presenting blocked payment paths as live.

## Support

Support ticket APIs must avoid exposing private attachments or session data in public logs. Attachment privacy remains a beta hardening item.

## Admin

Admin APIs must keep payment, download, node, ticket, and user states audit-friendly. Telegram admin remains fallback-only; web admin is the primary operator surface.
