# PostgreSQL Rehearsal Slice

Date: 2026-07-12

Status: synthetic repository candidate implemented; no real PostgreSQL or
production data used.

## Scope

This slice turns the existing one-shot SQLite copier into a testable migration
engine and adds a separate fail-closed `rehearse` command. It does not run the
production cutover, access a redacted production snapshot, create credentials,
or claim backup/restore proof.

## Implemented Contract

- `snapshot_sqlite` uses the SQLite backup API against a read-only source,
  verifies the snapshot with `PRAGMA quick_check`, applies restrictive file
  permissions where supported and records SHA-256/size without row content.
- Existing snapshot paths are never overwritten.
- The read-only `inventory` subcommand records every source table count for
  owner review. Rehearsal requires that manifest, required core tables and an
  exact snapshot count match before target reset.
- Rehearsal target URL is read only from the named environment variable. The
  database must be PostgreSQL, exactly match `--confirm-target`, end in
  `_rehearsal`, and have explicit `--reset-target` intent.
- Schema `create_all` takes the canonical `pokrov_schema_bootstrap` advisory
  lock before additive runtime migrations run.
- An explicit dependency manifest replaces misleading alphabetical
  `Base.metadata.sorted_tables` ordering in this no-FK metadata model.
- Source rows stream through `fetchmany`; `chunk_size` bounds source and target
  memory instead of only bounding inserts after `.all()`.
- Target reset, streaming copy, account-foundation backfill and invariant checks
  run in one target data transaction. A postprocess/invariant failure rolls the
  reset and copied rows back together.
- The account completion marker is rewritten from the actual rehearsal
  backfill report, including `users_seen` and mutation counters.
- Invariants cover null canonical user ownership and account/device/session,
  antiabuse event/case/action, merge-review, email-token, support, node/key,
  provisioning, observer-facing key state and composite external-payment order
  chains. Reports contain violation counts, never row identifiers or values.
- Owned integer PostgreSQL sequences are discovered with
  `pg_get_serial_sequence`. They synchronize after explicit copy and before
  generated backfill inserts, then again to final empty/populated state after a
  successful data commit. Sequence state is explicitly not described as
  transactional rollback evidence.
- `--rerun-check` uses one fixed rehearsal timestamp, repeats the deterministic
  replace and compares normalized report plus streamed target-content digests.
- JSON reports are written atomically and rejected if they contain a database
  URL or secret-like field. Unexpected SQL/runtime exceptions emit only a
  generic error type; `DETAIL`, parameters and row values are discarded.
- The legacy no-subcommand CLI remains available for compatibility but now uses
  streaming copy, transactional reset/copy, canonical schema preparation and
  owned-sequence synchronization.

## Automated Evidence

- Consistent snapshot, disposable target guard, dependency order, streaming,
  transactional rollback, account backfill/marker, invariants, deterministic
  content rerun digest, sequence ordering, source manifest, schema preparation
  and report redaction: `PASS`, `22 passed`.
- Migration/operator/account-foundation focused regression: `PASS`, `79 passed,
  8 subtests passed`.
- Full final release pytest matrix: `PASS`, `228 passed, 12 subtests passed`.
- Changed Python bytecode compile: `PASS`.
- `scripts/check-links.py`: `PASS`.
- `git diff --check`: `PASS`; only expected Windows LF-to-CRLF checkout
  warnings remain.
- Independent final migration security/correctness review: `CLEAN`, no open
  P0/P1/P2.
- All fixtures use synthetic SQLite databases. No customer row or production
  credential is test input.

## Current Environment Limits

- `psql`: `SKIPPED_TOOL_UNAVAILABLE`.
- `pg_dump`: `SKIPPED_TOOL_UNAVAILABLE`.
- `pg_restore`: `SKIPPED_TOOL_UNAVAILABLE`.
- Docker CLI: present; Docker Desktop Linux daemon: unavailable during the
  read-only environment audit.
- Real PostgreSQL execution and concurrent connections: `MANUAL_OWNER_TEST`.

These labels cannot be promoted to `PASS` from SQLite tests.

## Manual Gates

- `MANUAL_OWNER_TEST`: take an owner-approved consistent/redacted production
  snapshot during the cutover quiescence window and keep it outside git.
- `MANUAL_OWNER_TEST`: create or select a disposable PostgreSQL database whose
  name ends in `_rehearsal`; provide credentials only through a local secret
  environment.
- `MANUAL_OWNER_TEST`: run the exact rehearsal command, retain its sanitized
  JSON, investigate every failed invariant and review account merge rows.
- `MANUAL_OWNER_TEST`: execute `pg_dump` plus restore into a second disposable
  database and rerun invariants against the restored copy.
- `MANUAL_OWNER_TEST`: verify legacy public auth, entitlement, payments,
  support, bonuses, numeric compatibility and stateless bearer before/after.
- `MANUAL_OWNER_TEST`: prove two-connection PostgreSQL projection/link/startup
  lock behavior; local SQL ordering is not live deadlock proof.
- `MANUAL_OWNER_TEST`: approve source read-only/quiescence, maximum 15-minute
  cutover window, service drain order and rollback position.

## Rollback And Failure

- Data reset/copy/backfill/invariant failure rolls back that target transaction.
- Schema creation/additive migration happens before data replace and is not
  undone by data rollback.
- PostgreSQL `setval` is not rollback proof. The pre-backfill sync is
  intentionally early enough to avoid generated-ID collisions and can survive
  a later data rollback; final sync follows the successful data commit. Any
  failed sequence/data phase blocks promotion and requires target disposal or
  explicit sequence repair.
- The rehearsal target is disposable. Drop/recreate it through an approved
  operator path rather than trying to transform a failed rehearsal into
  production.
- Do not delete source/snapshot/backup evidence until restore and rollback gates
  are approved. Do not commit those database files.
- `remote_postgres_cutover.py` remains outside this slice and must not be run
  merely because synthetic rehearsal tests pass.

## Next Slice

Implement canonical entitlement/trial activation and the approved referral/free
economy. Client `clicked_connect` and `connected_ok` remain UX telemetry and
cannot activate trial or referral grants without node/control-plane evidence.
