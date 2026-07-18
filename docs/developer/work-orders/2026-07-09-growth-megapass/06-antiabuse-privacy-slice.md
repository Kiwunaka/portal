# Antiabuse Privacy Slice

Date: 2026-07-12

Status: repository candidate implemented; not deployed.

## Scope

This slice activates the additive antiabuse ledger for first-install and API
security signals while enforcing the approved data-minimization windows. It
does not activate automatic trial denial, referral denial, account lock or any
production acquisition rule.

## Implemented Contract

- `record_antiabuse_event` normalizes valid IPv4/IPv6 input and writes canonical
  account, device and session references when they are known.
- Raw `install_id` is never stored in `antiabuse_events`; a domain-separated
  HMAC is used instead.
- Code caps raw-IP retention at 72 hours, full-IP HMAC at seven days and IPv4
  `/24` or IPv6 `/64` prefix HMAC at 90 days. New raw-IP deadlines and legacy
  cutoffs include a one-hour early-sweep margin, larger than the maximum
  15-minute cadence.
- Retention settings can shorten but cannot extend those hard caps.
- HMAC input is purpose- and version-separated. New rows use the current
  dedicated secret; explicit previous-version secrets can produce both IP and
  install-ID comparison candidates during a guarded rotation window.
- Missing HMAC configuration degrades signal quality without blocking a user
  request. Raw-IP expiration still applies, but production readiness remains
  blocked until the dedicated secret is configured outside git.
- API security audit and antiabuse rows commit together. Sensitive metadata
  keys are redacted.
- Successful first-device reservation and its `trial_reserved` ledger row
  commit atomically with canonical account/device IDs. Session issuance then
  fills the canonical session ID. A legacy projected install without session
  history writes `trial_session_issued` instead.
- A dedicated worker runs every 60-900 seconds. Cleanup executes in a worker
  thread rather than the shared asyncio event loop, takes PostgreSQL
  `FOR UPDATE SKIP LOCKED` batches and commits each batch. One chunk is capped
  by `ANTIABUSE_RETENTION_MAX_BATCHES_PER_RUN`; remaining backlog is retried
  after one second. It clears covered fields from
  `antiabuse_events`, `security_events.client_ip` and `users.app_last_ip` while
  retaining audit rows.
- `scripts/cleanup_antiabuse_retention.py` is the rollback/incident one-shot
  path. It is read-only by default and mutates only with explicit `--apply`.
- Hard lock enable/disable is exposed only as an operator service action. A
  positive operator Telegram ID and non-empty reason are mandatory, and the
  change writes `antiabuse_actions`.

## Configuration

- `ANTIABUSE_HMAC_SECRET`
- `ANTIABUSE_HMAC_VERSION`
- `ANTIABUSE_HMAC_SECRET_V<n>` during controlled rotation
- `ANTIABUSE_RAW_IP_RETENTION_HOURS` capped at 72
- `ANTIABUSE_FULL_IP_HMAC_RETENTION_DAYS` capped at 7
- `ANTIABUSE_PREFIX_HMAC_RETENTION_DAYS` capped at 90
- `ANTIABUSE_RETENTION_BATCH_LIMIT` capped at 10000
- `ANTIABUSE_RETENTION_MAX_BATCHES_PER_RUN` clamped to 1-100
- `ANTIABUSE_RETENTION_INTERVAL_SECONDS` clamped to 60-900

No production values belong in git.

## Automated Evidence

- Focused IPv4/IPv6, redaction, rotation, exact-boundary, drain and hard-lock
  contract, start-trial/API integration, worker and release-matrix guard suite:
  `PASS`, `74 passed, 7 subtests passed`.
- Full final account/recovery/session/app-first/worker/observer/release regression:
  `PASS`, `206 passed, 12 subtests passed`.
- Python bytecode compile for all changed Python runtime/scripts: `PASS`.
- `scripts/check-links.py`: `PASS`.
- `git diff --check`: `PASS`; Git reports only existing Windows LF-to-CRLF
  checkout warnings.
- Independent final security/privacy review: `CLEAN`, no open P0/P1.

Residual P2: exact post-chunk backlog counts can be expensive on production-size
tables, especially the unindexed legacy `users.app_last_seen_at` path. Measure
that cost in the PostgreSQL volume gate before changing exact operator counts
to cheaper worker-only existence probes.

The compatible repository environment is `.tmp/venv-auth-sessions`. The global
Python environment remains `BLOCKED_BY_ENVIRONMENT` because its FastAPI and
Starlette versions are incompatible; no global dependency was changed.

## Manual Gates

- `MANUAL_OWNER_TEST`: generate and install the dedicated backend-only HMAC
  secret and retain prior versions only for active comparison windows.
- `MANUAL_OWNER_TEST`: prove `portal-worker` schedule, `SKIP LOCKED` concurrency,
  drain throughput and zero overdue backlog against PostgreSQL with
  production-like row volume. Alert when the worker is stopped or backlog is
  non-zero after a drain.
- `MANUAL_OWNER_TEST`: these deadlines are an operational SLO, not PostgreSQL
  TTL. Prove monitoring and incident response for worker outage or persistent
  backlog before claiming the 72-hour/seven-day/90-day caps in production.
- `MANUAL_OWNER_TEST`: inspect reverse-proxy, application and infrastructure
  logs for independent raw-IP retention. This slice covers only the named
  first-party database columns.
- `MANUAL_OWNER_TEST`: confirm raw/recent IP detail is restricted to an
  individual investigation view before exposing ledger data in adminapp.
- `MANUAL_OWNER_TEST`: approve any soft antiabuse thresholds. Automatic hard
  lock remains forbidden.

## Rollback

- Do not drop or truncate antiabuse, security or action rows during routine
  code rollback.
- Before routing back to a worker revision without this job, inspect backlog:
  `python scripts/cleanup_antiabuse_retention.py`. Drain it explicitly with
  `python scripts/cleanup_antiabuse_retention.py --apply`, retain the sanitized
  JSON output, and provide an equivalent scheduled cleanup in the rollback
  revision. Stopping the new worker without replacement is not an approved
  rollback.
- Rotating or removing the HMAC secret makes retained hashes unavailable for
  comparison; it does not anonymize raw fields before their cleanup deadline.
- Operator hard-lock audit rows are retained security state and are not undone
  by code rollback.

## Next Slice

Run the additive SQLite-to-PostgreSQL migration rehearsal on synthetic data,
including idempotency, sequence synchronization, invariant reporting and a
local backup/restore path. A redacted production snapshot remains an explicit
owner gate.
