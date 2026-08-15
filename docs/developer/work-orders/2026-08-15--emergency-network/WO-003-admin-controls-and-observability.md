# WO-003 — Admin Controls And Observability

## Metadata

| Field | Value |
| --- | --- |
| WO id | `WO-003-admin-controls-and-observability` |
| Title | Operator can inspect, promote, disable and roll back emergency catalogs |
| Ceremony | `bounded_wo` |
| WO status | `done` |
| Orchestrator | `/root` |
| Repository lane | `platform` |
| Working branch or worktree | scoped platform branch after WO-002 |
| Intended promotion state | platform `master`; deploy in WO-007 |
| Created / updated | `2026-08-15` |

## Goal

Add an admin surface for active/staging versions, live/stale counts, safe endpoint
identity, country, probe freshness, rejection reasons, preview, explicit
promotion, temporary disable and rollback without exposing credentials.

## Non-Goals

- Editing UUID, keys, SNI or arbitrary profile JSON in the browser.
- Automatic promotion based only on TCP latency.
- New general-purpose node control plane.

## Write Scope

- focused admin API/service routes
- `adminapp/src/` emergency catalog surface
- admin E2E and platform admin tests
- `adminapp/README.md` and monitoring owner

## No-Touch Scope

- legacy admin parity surface unless a compatibility link is required
- raw provider/source payloads in UI or logs

## Authority Anchors

Standalone adminapp router row, current admin auth/audit patterns, WO-002 service
contract and monitoring owner.

## Acceptance Oracle

- Authoritative boundary: authenticated admin action plus resulting active snapshot.
- Success observation: preview shows safe delta; promote/disable/rollback requires
  explicit action, produces audit record and changes only the intended snapshot.
- Negative cases: stale revision, CSRF/auth failure, last healthy reserve removal,
  unsafe >50% automatic delta and concurrent update fail closed.
- Proof mechanism: API tests, admin E2E, revision-conflict and rollback smoke.
- Limitations: admin UI does not prove tunnel behavior.
- Triggered proof blocks: MREP, risk proof, reviewability.

## Docs Impact

`adminapp/README.md`, monitoring/system overview and this wave.

## Validation And Evidence

Admin lint/build/E2E, focused admin API tests, audit-event inspection and
credential-canary absence from rendered/logged output.

## Status And Handoff

- Current WO status: `done`
- Dependency: WO-002
- Implemented locally: redacted status/counts/active-revision/probe/worker read
  model, dedicated `adminapp` route, and guarded stage/promote/disable/rollback actions
  through the existing action-intent boundary.
- Safe promotion preview exposes counts only; action-intent binds the target and
  current distribution revision, >50% automatic churn fails closed, temporary
  disable cannot be reversed by worker, and raw host/material/signature canaries
  are absent from the read model and UI.
- Disable stops new catalog delivery. A previously issued signed offline cache
  remains intentionally non-recallable until its existing expiry.
- No production deploy or runtime proof is claimed by this local state.
