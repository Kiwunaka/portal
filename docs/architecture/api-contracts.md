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
  must use recovery once that follow-up slice is enabled.
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
- Bootstrap possession is not fresh authentication. Until the OTP/recovery
  slice can set `fresh_auth_at`, public device revoke intentionally returns
  `409 fresh_auth_required`; tests may seed that timestamp only to prove the
  post-auth revoke primitive.
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

## Payment Providers

`GET /api/payments/providers` must expose provider availability and enough unavailable-state detail for checkout to avoid presenting blocked payment paths as live.

## Support

Support ticket APIs must avoid exposing private attachments or session data in public logs. Attachment privacy remains a beta hardening item.

## Admin

Admin APIs must keep payment, download, node, ticket, and user states audit-friendly. Telegram admin remains fallback-only; web admin is the primary operator surface.
