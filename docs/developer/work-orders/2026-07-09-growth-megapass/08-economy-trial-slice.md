# Economy Trial Reservation And Server Evidence Slice

Date: 2026-07-12

Status: repository candidate implemented; not deployed.

## Completed Scope

- Added one idempotent account/device premium-trial reservation for `7 days`.
- Kept the provisional compatibility credential usable without starting the
  `5-day` trial clock.
- Added append-only, account-owned `connection_evidence` without raw
  subscription URLs, bearer tokens, provider secrets, source IPs, or traffic
  payloads.
- Activated a reservation exactly once from signed internal observer evidence
  at the observation timestamp, with expiry exactly `activated_at + 5 days`.
- Kept `/api/connect/confirm`, `clicked_connect`, `connected_ok`, and funnel
  telemetry outside activation authority.
- Added observer batch/evidence replay idempotency, stale-reservation worker
  sweep, additive SQLite/PostgreSQL migration contracts, and migration
  rehearsal ordering/orphan invariants.
- Preserved legacy entitlement snapshots as compatibility fallback and kept
  `User.sub_type`, `User.current_plan_code`, `User.expiry_at`, and current API
  fields as compatibility projections.
- Preserved paid and unrelated active grants when stale trial reservations
  expire to ordinary `free_monthly` projection.

## Review Fix Loop

- Stale reservation expiry now preserves live paid/bonus authority held only in
  the current `User` compatibility projection as well as grant-backed access.
- Account merge deterministically keeps one trial authority (`active` before
  `reserved`, then earliest effective timestamp and grant ID), marks duplicates
  `premium_trial_superseded`, retains winner/account provenance, and is
  rerunnable.
- Observer batch unique races now converge to the committed replay response;
  unrelated integrity failures remain HTTP `500`.
- Public trial authority is fixed at exactly `5 days`; environment values cannot
  change API output or grant duration.
- `activated_trial_count` now comes from the row-locked activation result's
  `activated_now` flag rather than a stale grant pre-read.

Review evidence:

- Combined projection/env/merge/batch-race RED: `PASS`, expected
  `4 failed, 1 passed`.
- Atomic activation-result RED: `PASS`, expected `1 failed`.
- Focused review GREEN: `PASS`, `6 passed`.
- Reviewer-required economy/app-first/account/observer files: `PASS`,
  `68 passed`.
- Final economy/app-first/account/session/observer/migration/release-gate
  matrix: `PASS`, `127 passed, 8 subtests passed`.

## Second Review Fix Loop

- Merge reconciliation now covers every row in the account unique-index source
  set, including expired, reversed, superseded, and unknown statuses. Exactly
  one deterministic canonical row remains `source=premium_trial`; every loser
  retains prior status/reversal and winner provenance outside that source set.
- Offset-aware observer timestamps normalize to naive UTC, never server-local
  time, before activation and `+5 days` expiry.
- Evidence key v2 uses owned node, immutable resolved legacy user identity,
  evidence kind, and canonical UTC timestamp. Mutable account UUID is excluded,
  so different-batch replay after account merge remains one evidence row.
- No schema column changed; the existing unique `evidence_key` contract stores
  the v2 digest additively.

## Third Review Fix Loop

- The owned Xray collector now converts `Z`, positive-offset, and
  negative-offset timestamps to canonical UTC `Z` before minute aggregation or
  observer submission.
- A naive Xray timestamp requires `PORTAL_OBSERVER_SOURCE_TIMEZONE` or
  `--source-timezone`, using only `UTC`, `Z`, or a strict fixed offset such as
  `+03:00` or `-04:00`. IANA names and missing, ambiguous, invalid, or
  out-of-bounds settings fail closed per line and retain existing batch
  `parse_error_count` accounting.
- Deployment proof remains `MANUAL_OWNER_TEST`: compare retained source time,
  emitted UTC evidence, activation, and exact `+5 days` expiry for the deployed
  candidate, then prove a naive line without valid timezone configuration is
  skipped and counted.

Second review evidence:

- Full-status merge/UTC/post-merge replay RED: `PASS`, expected `3 failed`.
- Focused second-review GREEN: `PASS`, `3 passed`.
- Economy/app-first/account/session/observer/migration/release matrix: `PASS`,
  `129 passed, 8 subtests passed`.
- Documentation tests: `PASS`, `6 passed`; link check, changed Python compile,
  `git diff --check`, and scoped secret scan: `PASS`.

## Automated Evidence

- Required RED: `PASS`, seven expected failures for missing economy service,
  additive schema, response fields, and observer activation.
- Focused economy GREEN: `PASS`, `7 passed`.
- App-first, observer, and migration focused regression: `PASS`, `53 passed`.
- Rehearsal dependency/invariant regression: `PASS`, `23 passed`.
- Final account/session/observer/worker/migration/release-gate matrix: `PASS`,
  `135 passed, 8 subtests passed`.
- Documentation contract tests: `PASS`, `6 passed`; link check, changed Python
  compile, and `git diff --check`: `PASS`.

All tests use synthetic SQLite fixtures and the repository-compatible isolated
Python environment. No production data, provider credential, raw subscription
material, or customer payload was used.

## Manual Gates

- `MANUAL_OWNER_TEST`: real two-connection PostgreSQL concurrency and unique
  race-guard proof for reservation, evidence, and activation.
- `MANUAL_OWNER_TEST`: owner-approved additive PostgreSQL rehearsal against a
  redacted snapshot with retained sanitized report and rollback evidence.
- `MANUAL_OWNER_TEST`: deployed node observer signature, real first connection,
  panel provisioning/retry, and post-activation expiry proof for the exact
  candidate.
- `MANUAL_OWNER_TEST`: current-origin, brain-origin, and RU-origin checks remain
  separate; none is claimed by local tests.
- `NOT_REQUESTED`: merge, push, deploy, production mutation, payment, referral,
  Telegram grant, free soft-inbound runtime, notices, UI, signing, store, and
  active-client changes.

## Rollback And Limits

- The schema change is additive. Rollback stops new reservation/evidence writes
  and restores the prior code; evidence and legacy snapshots remain retained.
- Panel failure does not activate a trial. Provisioning remains retryable after
  the ledger transaction.
- Local SQLite replay proves deterministic idempotency, not live PostgreSQL
  lock scheduling or node deployment.
