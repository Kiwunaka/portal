# Device-Bound Rotating Session Slice

Date: 2026-07-12
Status: repository implemented; deploy not requested

## Scope

This slice activates only the `auth_sessions` and real-device portion of
Workstream A:

- short-lived device-bound access tokens;
- one-time rotating refresh families with absolute expiry;
- consumed-refresh reuse detection and family revoke;
- persisted session logout;
- real device listing and fresh-auth revoke;
- compatibility validation for existing bearer families.

Email OTP, `PKR-XXXX-XXXX-XXXX` recovery, reissue modes, antiabuse retention,
entitlement authority, client implementation, deploy and release are outside
this commit.

## Implemented Contract

- `POST /api/client/session/start-trial` first persists the additive
  account/device projection, prepares panel/client-policy/public payload, then
  creates the first session in a short final transaction only after the full
  response is assembled in memory. A failed payload build leaves no unreturned
  refresh credential in `auth_sessions`, so the same install can retry.
  Existing response fields remain; access/refresh/session/family/canonical IDs
  and expiry fields are additive.
- Any session history for that real device makes a later bootstrap fail with
  `409 device_recovery_required`. The install ID is lookup context, never an
  authentication credential. The guard runs before upsert, IP/metadata writes
  and panel synchronization.
- `POST /api/client/session/refresh` rotates the refresh credential once. The
  family keeps its original expiry. A consumed credential replay revokes every
  row in that family and returns `401 refresh_reuse_detected`.
- `POST /api/client/session/revoke` revokes the current family without revoking
  the device.
- Compatibility `account_id` stays numeric through bootstrap and refresh;
  `canonical_account_id` carries the UUID separately at root and nested session
  levels.
- App cabinet handoff/exchange propagates persisted source-session claims. The
  derived cabinet scope keeps browser token TTL semantics while account epoch,
  device credential and family revoke remain authoritative.
- `GET /api/client/devices` reads `account_devices`; `id=install_id` remains for
  compatibility and `registryId` exposes the canonical UUID.
- `DELETE /api/client/devices/{device_id}` accepts either ID, requires recent
  fresh auth, increments credential version and revokes all device sessions.
- Access validation checks persisted revoke/expiry state, account status and
  `auth_epoch`, device status and `credential_version`, scope and account/user
  ownership. Replaced access tokens may finish their short overlap window until
  expiry unless reuse or an explicit revoke invalidates the family.
- Mutating session operations use the shared PostgreSQL lock order
  `account -> device (when applicable) -> auth_session -> refresh family`.
  Refresh performs a non-locking indexed hash discovery first, then repeats and
  validates the session lookup under that lock order. This avoids the prior
  refresh/device-revoke lock inversion.
- Raw refresh credentials are response-only. The database stores SHA-256 of a
  high-entropy random credential; request handling does not use the raw value in
  rate-limit identity, diagnostics or logs.
- Refresh throttling uses a per-hashed-credential bucket plus a separate coarse
  IP ceiling, avoiding one small shared CGNAT bucket while retaining a cap for
  random-token database pressure.

## Compatibility And Cutover

- Existing browser, Telegram, email, admin and handoff bearers do not carry
  `session_id` and continue through the legacy signed-token path.
- Existing app response key `session_token` is the new access token; new clients
  also receive explicit `access_token` and `refresh_token`.
- Numeric response `account_id` remains for old clients. New code receives
  `canonical_account_id` separately.
- Device bootstrap is deliberately not fresh auth. Device `DELETE` remains
  `409 fresh_auth_required` until the next OTP/recovery slice can set
  `fresh_auth_at`; no test-only DB mutation is presented as a live user path.
- This branch is not production truth. Production remains stateless until an
  owner-approved deploy after account migration, client and recovery gates.

## Migration And Rollback

- No new schema migration is required beyond the preceding additive account
  foundation; this slice writes previously empty `auth_sessions` rows.
- Code rollback must retain those rows as evidence. Do not drop or truncate
  `auth_sessions` during rollback.
- A rollback to the prior API can still verify an unexpired signed access token
  without consulting persisted revoke state, and it cannot rotate refresh.
  Mixed old/new API instances are therefore forbidden during cutover. Before
  rollback, stop session bootstrap/refresh, wait at least
  `APP_ACCESS_TOKEN_TTL_SECONDS` after the final issuance, then route app access
  to the old revision. Updated clients still need tested recovery.
- Session-family revoke and device credential increments are security state and
  must not be undone by routine rollback. Restoring them requires an explicit,
  audited owner decision.

## Automated Evidence

- `tests/test_auth_sessions.py` covers issue, hash-only storage, duplicate
  bootstrap guard, rotation, replay-family revoke, access invalidation, account
  epoch, device credential drift, first forensic timestamps, fresh-auth device
  revoke, orphan-session reconciliation and logout.
- `portal_bot/tests/test_app_first_api.py` covers the same public HTTP contract,
  error headers, response-safe bootstrap commit, early duplicate guard, numeric
  compatibility, CGNAT-safe limiting, bound cabinet handoff and real device
  registry behavior.
- `tests/test_release_gate_check.py` requires the session suite in the default
  release pytest matrix.
- A repository-local `.tmp/venv-auth-sessions` was created from
  `portal_bot/requirements.txt`, `requirements-ops.txt`, `pytest` and `httpx`
  for compatible API tests. The pre-existing unpinned `puttykeys` import used
  by node readiness was installed only in that temporary venv. This is
  untracked test infrastructure, not a release artifact; the missing ops pin is
  separate dependency debt.
- The workstation global environment remains `BLOCKED_BY_ENVIRONMENT` for API
  imports because `fastapi 0.115.11` is paired with incompatible
  `starlette 1.3.1`. Global dependencies were not changed.

## Manual Gates

- `MANUAL_OWNER_TEST`: PostgreSQL concurrency for two simultaneous first
  bootstraps, two rotations of one refresh token and concurrent refresh versus
  device/session revoke; retain row/family evidence and prove no deadlock.
- `MANUAL_OWNER_TEST`: Android and Windows secure storage writes the new refresh
  before discarding the old one and survives restart/update/reinstall scenarios.
- `MANUAL_OWNER_TEST`: email OTP and one-time recovery are complete before the
  repeated-bootstrap guard is deployed.
- `MANUAL_OWNER_TEST`: no mixed stateless/database-aware API fleet; prove old
  instance drain and the full access-TTL rollback wait in staging.
- `MANUAL_OWNER_TEST`: exact clients cover lost refresh, expired refresh,
  replay, logout, self/other-device revoke, offline refresh and clock skew.
- `MANUAL_OWNER_TEST`: verify no raw refresh value appears in API/proxy/error/
  security logs or support diagnostics.
- deploy, push, merge and production mutation: `NOT_REQUESTED`.

## Verification Status

All commands below used the repository-local compatible venv; no global
dependency was changed.

- release pytest matrix from `scripts/release_gate_check.py`: `PASS`,
  `178 passed, 12 subtests passed`;
- cross-surface auth/ticket/OIDC/lifecycle regression: `PASS`, `72 passed`;
- focused session/app-first/service/email/client-UI regression: `PASS`,
  `58 passed`;
- release-gate contract: `PASS`, `18 passed, 4 subtests passed`;
- Python compile check: `PASS`;
- public link check with report under `.tmp`: `PASS`;
- app/bot/cabinet parity smoke with explicit canonical client root: `PASS`,
  `7 passed, 0 failed, 2 MANUAL_OWNER_TEST`;
- `git diff --check`: `PASS` (line-ending conversion warnings only);
- static raw-refresh logger/print scan: `PASS`, no sink found.

Two independent read-only reviews reported no P0. Their actionable findings
were resolved with tests: account-first lock order, serialized family reuse,
response-safe bootstrap commit, early history guard, numeric `account_id`,
bound cabinet continuation, unique handoff token IDs and CGNAT-safe refresh
limits. Fresh-auth reachability and stateless-revision rollback remain explicit
manual gates above rather than being mislabeled as implemented user flows.

## Next Slice

Email OTP, one-time recovery-code exchange/rotation and the two controlled
access reissue modes. Do not start economy or entitlement authority before that
account-security path is closed.
