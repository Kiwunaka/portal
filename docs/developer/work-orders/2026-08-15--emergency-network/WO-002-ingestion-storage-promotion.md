# WO-002 — Ingestion, Storage And Promotion

## Metadata

| Field | Value |
| --- | --- |
| WO id | `WO-002-ingestion-storage-promotion` |
| Title | Signed emergency catalog has safe snapshots, probes, LKG and rollback |
| Ceremony | `bounded_wo` |
| WO status | `done` |
| Orchestrator | `/root` |
| Repository lane | `platform` |
| Working branch or worktree | scoped platform branch after WO-001 |
| Intended promotion state | platform `master` after review; deploy only in WO-007 |
| Created / updated | `2026-08-15` / `2026-08-16` |

## Goal

Implement versioned catalog snapshots and normalized endpoint records, scheduled
ingestion from approved mirrors, controlled auth/payload probes, signing,
staging→active promotion, last-known-good retention and one-step rollback.

## Non-Goals

- Client UI or managed-profile chain selection.
- Claiming real БС from a normal server probe.
- Running code supplied by the source repository.

## Write Scope

- `portal_bot/models.py` and exact migration owner
- focused `portal_bot/emergency_catalog_*.py`
- `portal_bot/worker.py` wiring kept thin
- platform tests and canonical backend/API docs

## No-Touch Scope

- user payment/entitlement ledger semantics
- public raw endpoint API
- production mutation before reviewed dry-run and backup gates

## Authority Anchors

Current platform models/worker patterns, WO-001 parser contract, system overview,
API contracts and production deployment playbook.

## Acceptance Oracle

- Authoritative boundary: active signed snapshot read by API materialization.
- Success observation: a staging revision plus recent exact successes form an
  atomic 4–12 unique-host pool and can roll back to one of three retained
  predecessors without contaminating the restored set with newer history.
- Negative cases: fewer than four fresh exact successes across the bounded
  pool, >50% automatic churn below a saturated 12-member pool, stale signature,
  stale/future probe, material mismatch or partial write never replaces active.
- Proof mechanism: migration/model tests, worker integration tests, signature
  tamper tests, deterministic payload/auth probe fixture and rollback smoke.
- Limitations: backend probe is not physical-device or RU-BS proof.
- Triggered proof blocks: MREP, risk proof, promotion evidence.

## Docs Impact

`docs/architecture/system-overview.md`, `docs/architecture/api-contracts.md`,
monitoring/deployment owners and this wave.

## Validation And Evidence

Focused pytest for parser/service/models/worker, migration dry-run, tampered
snapshot negative smoke, diff/secret check and retained staging/rollback report.

## Status And Handoff

- Current WO status: `done`
- Dependency: WO-001
- Implemented: encrypted endpoint records, versioned staging, bounded exact-Core
  probes, rolling 24-hour 4–12 promotion, conditional >50% automatic churn stop,
  signed active catalog, three retained LKG candidates, exact rollback clone and
  env-gated worker.
- Proof: focused Emergency/worker/migration/crypto/tamper tests pass. Production
  signing material exists server-side, while worker remains disabled until
  runtime deploy and exact probe canary.
