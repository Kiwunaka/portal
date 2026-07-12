# Email OTP And Account Recovery Slice

Date: 2026-07-12
Status: repository implemented; deploy not requested

## Scope

This slice closes the repository-side recovery dependency that followed the
device-bound rotating-session work:

- six-digit email OTP with an exact five-minute lifetime;
- fresh authentication for an existing device session;
- one-time `PKR-XXXX-XXXX-XXXX` recovery code rotation and exchange;
- a 15-minute device-bound limited recovery session;
- `vpn_credentials` and `account_lockdown` reissue modes;
- server-enforced recovery-scope restrictions;
- per-IP and hashed-subject endpoint rate limits.

Password registration, login and reset remain compatibility behavior. The
90-day password sunset starts only from an owner-approved production cutover;
no repository date is presented as if that deployment happened.

## Implemented Contract

- OTP start is enumeration resistant and never echoes the code in API JSON.
  Only a verified identity receives mail. OTP storage is a keyed digest bound
  to identity and code; successful consume is one-time and row-locked.
- OTP finish can set `fresh_auth_at` on a matching current session. Supplying
  device metadata creates or reauthenticates a real `account_devices` row,
  revokes prior sessions for that device and returns a new rotating pair.
- Recovery-code rotation requires recent fresh auth, revokes older active
  codes and returns the raw code once. The database stores only versioned HMAC
  and a masked hint.
- Recovery exchange locks and rechecks the account and code, consumes it once,
  and returns a session with both access and refresh expiry fixed at 15 minutes.
- Recovery scope cannot read subscription or managed-profile material, link a
  persistent identity or create payment ownership. The allowlist is limited to
  account status, support tickets, device actions, logout and audited reissue.
- Reissue rotates every legacy account projection's public subscription token,
  preserves entitlement dates and queues managed access-key rotation.
  `account_lockdown` additionally increments account auth epoch and revokes all
  other devices and sessions.
- `vpn_credentials` refuses promotion while the active-device count exceeds
  the tariff limit. The user must revoke an old device or choose lockdown.
- The recovery session is revoked as part of reissue, so replay cannot mint a
  second normal session.
- An append-only antiabuse event records mode, queued rotation count and revoked
  device count without raw recovery, refresh or subscription material.

## Compatibility And Limits

- Existing browser, Telegram, password-email and stateless bearer families
  continue unchanged. Password login responses are explicitly labelled
  `password_compatibility`.
- Provider key rotation is queued, not falsely reported as complete. The
  existing provisioning queue still needs a proven worker completion path in a
  later slice; `provisioning_status=pending` is not node evidence.
- Initial recovery-code display after server-confirmed first connect belongs to
  the entitlement/node-evidence workstream and is not manufactured from the
  client `connect` event.
- Client recovery, atomic refresh replacement and UI are not part of this
  platform commit.
- No production deploy, secret creation, external email delivery, device test,
  merge, push or release was performed.

## Automated Evidence

- `tests/test_account_recovery.py` covers OTP hashing/TTL/replay, fresh auth,
  HMAC-only recovery rotation, replacement, exchange, limited-session expiry,
  VPN reissue, queued key rotation, entitlement preservation, replay rejection
  and account lockdown.
- `portal_bot/tests/test_email_auth.py` covers generic OTP start, real email
  delivery handoff, one-time finish, password compatibility labelling,
  app-session fresh auth, code rotation, exchange, recovery-scope denial and
  reissue through the public HTTP contract.
- Existing device/session and app-first suites remain required regression.

## Verification Status

All Python API checks used the repository-local compatible virtual environment;
the workstation global FastAPI/Starlette installation was not modified.

- release pytest matrix: `PASS`, `189 passed, 12 subtests passed`;
- account/recovery/session/ticket security regression: `PASS`, `100 passed`;
- Python compile check: `PASS`;
- public link contract check: `PASS`;
- `git diff --check`: `PASS` (line-ending conversion warnings only);
- independent final P0/P1 review: `PASS`, no remaining P0/P1 findings.

The workstation global environment remains `BLOCKED_BY_ENVIRONMENT` for API
imports because it pairs `fastapi 0.115.11` with incompatible
`starlette 1.3.1`. That environment was not changed and is not used as release
evidence.

## Manual Gates

- `MANUAL_OWNER_TEST`: configure a dedicated recovery-code HMAC secret and
  retain prior version keys during rotation. Secrets must remain outside git.
- `MANUAL_OWNER_TEST`: prove SMTP/provider delivery timing, resend behavior and
  no raw OTP in API/proxy/error/security logs.
- `MANUAL_OWNER_TEST`: real PostgreSQL concurrent OTP consume, code exchange,
  refresh versus revoke and reissue versus revoke with no deadlock.
- `MANUAL_OWNER_TEST`: exact Android and Windows clients atomically replace
  refresh credentials, recover after reinstall and enforce recovery scope.
- `MANUAL_OWNER_TEST`: prove queued access-key rotations complete on every
  assigned node before presenting credential reissue as finished.
- `MANUAL_OWNER_TEST`: configure the password compatibility sunset from the
  actual cutover date and remove password entry after 90 days.

## Rollback

- Do not delete OTP, recovery, session or antiabuse rows during code rollback.
- A rollback to the stateless API cannot enforce recovery/session revoke state.
  Stop bootstrap, refresh, OTP and recovery issuance, drain new instances and
  wait at least the maximum access TTL before routing to the old revision.
- Recovery-code consume, account epoch increments, device credential increments
  and security revokes are retained security state and must not be reversed by
  routine rollback.

## Next Slice

Raw-IP/HMAC retention and migration rehearsal, followed by entitlement
authority and server-confirmed trial activation. Economy work must not treat
client `clicked_connect` or `connected_ok` as activation evidence.
