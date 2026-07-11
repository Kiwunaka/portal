# Account Foundation Slice

Date: 2026-07-10
Status: implemented on `codex/market-ready-cis-integration`; not deployed

## Scope

This slice is the additive ownership foundation for the Market-Ready CIS plan.
It does not switch public auth or entitlement authority yet.

Implemented:

- `accounts` plus nullable `users.account_id` compatibility projection;
- typed `account_identities` and real `account_devices`;
- foundation schema for `auth_sessions`, `recovery_codes`,
  `entitlement_grants`, `antiabuse_events`, `antiabuse_cases`,
  `antiabuse_actions`, and `account_merge_reviews`;
- deterministic UUIDv5 backfill for legacy users and installs, guarded by a
  durable completion marker so each service startup does not repeat a full
  user-table scan; an indexed NULL check repairs any legacy writer missed by
  runtime projection;
- one PostgreSQL schema-bootstrap serialization key shared by `create_all` and
  additive migrations, preventing their separate first-start transactions from
  overlapping across API, bots and worker;
- automatic merge only across explicit `linked_telegram_id` edges;
- deterministic reverse-edge convergence when the direct Telegram row arrives
  after an app row already points to it;
- preserved absorbed account rows with `status=merged` and
  `merged_into_account_id`;
- legacy entitlement snapshots keyed once per source user;
- PostgreSQL transaction locks and component-scoped runtime synchronization for
  app trial, email identity, Telegram first-touch, and the actual Telegram bind;
- one lock order for runtime, bind and backfill: affected user rows, per-user
  advisory locks, then the global projection lock; startup marker coordination
  uses a separate advisory key, and no transaction upgrades a shared global
  projection lock to exclusive;
- two-phase legacy-component locking: discover the full closure without locks,
  lock all IDs in one numeric `FOR UPDATE`, then recheck closure before the
  global lock;
- `FOR UPDATE` consumption for the one-time Telegram link and its app/Telegram
  user rows;
- link consumption requires both app and direct-Telegram `users` endpoints;
  a missing endpoint leaves the one-time link active;
- explicit rejection of transitive Telegram identity chains before the global
  merge lock; rejected links remain unused for operator/support review;
- conflict queue instead of silent ownership replacement;
- operator `blocked` status and the highest `auth_epoch` survive backfill and
  account merge.

## Compatibility

- `users.tg_id` remains the live adapter key.
- Existing `start-trial` response fields are unchanged.
- Existing panel UUID, subscription token, payment, support and bonus rows are
  not deleted or rewritten.
- The current stateless bearer remains live. Presence of `auth_sessions` does
  not mean rotation or revoke is implemented.
- `legacy_snapshot` grants preserve migration evidence but do not replace the
  current access calculation yet.

## Backfill Rules

1. Every legacy user receives a deterministic canonical account unless it is
   already mapped.
2. A direct Telegram row and an app row merge only when an explicit
   `linked_telegram_id` edge connects them.
3. Existing canonical IDs are preserved where possible. Absorbed accounts are
   retained and point at the selected canonical account.
4. Typed identity collisions do not overwrite ownership; they create one
   idempotent `account_merge_reviews` row.
5. Account-owned foundation rows move to the canonical account during an
   explicit late merge.
6. Backfill is idempotent, protected by a Postgres transaction advisory lock,
   and records a completion marker only after the projection flushes. SQLite
   relies on its write transaction serialization.
7. A late merge carries restrictive account status and the highest
   `auth_epoch` into the canonical target before the absorbed row is marked
   `merged`.

## Rollback

The change is additive. Code rollback can stop reading/writing the new tables
while all legacy rows continue to exist. Do not drop the new tables during an
incident. A data rollback may clear `users.account_id` only after preserving a
backfill report; merged account and review rows remain audit evidence.

## Verification

- `tests/test_account_foundation.py` covers schema, idempotency, the one-time
  startup marker and late-write repair, component-scoped runtime sync, explicit
  linking, late merge, preserved grants, blocked/auth-epoch state, advisory
  and schema-bootstrap locking, reverse-edge arrival order, review conflicts
  and legacy SQLite column migration.
- the default release pytest matrix now executes
  `portal_bot/tests/test_app_first_service.py`,
  `portal_bot/tests/test_email_auth.py`, `tests/test_bot_paywall.py` and
  `tests/test_account_foundation.py`; the existing separate admin/auth gate
  continues to execute `tests/test_api_auth_and_tickets.py`.
- repo-local focused tests prove SQL ordering contracts and compatibility
  behavior only. They do not prove live two-connection PostgreSQL concurrency
  or deployment readiness.

## Predeploy Manual Gates

- PostgreSQL rehearsal/backfill report: `MANUAL_OWNER_TEST` against a redacted
  production snapshot, retaining row, merge and review counts.
- two-connection PostgreSQL concurrency proof: `MANUAL_OWNER_TEST` for runtime
  projection, Telegram bind and concurrent first startup.
- rollback approval: `MANUAL_OWNER_TEST` for backup/restore evidence, code
  rollback and the additive-table retention decision.
- compatibility preservation: `MANUAL_OWNER_TEST` for public auth,
  entitlement, payments, support, bonus, `users.tg_id` and the current
  stateless bearer before and after rehearsal.
- deploy: `NOT_REQUESTED`; this task makes no production mutation.

Local API-import gate status is `BLOCKED_BY_ENVIRONMENT`: the workstation has
`fastapi 0.115.11` with `starlette 1.3.1`, while the repository pin is
`starlette<1.0`. Do not install or mutate global packages to reinterpret that
environment as release proof.

## Next Slice

- rotating refresh families and access-token sessions;
- device-bound revoke and fresh-auth rules;
- email OTP and one-time `PKR-XXXX-XXXX-XXXX` recovery;
- migration report/rehearsal against a redacted production snapshot;
- entitlement-ledger authority and server-confirmed activation evidence.
