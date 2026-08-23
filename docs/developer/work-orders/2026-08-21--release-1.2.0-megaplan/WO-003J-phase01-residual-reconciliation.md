# WO-003J — Phase 01 residual authority reconciliation

Status: `PARTIAL_LOCAL_I2_EXTERNAL_BLOCKERS`
Phase: `01`
Ledger rows: `FE/P12-023`, `FE_PR/PR-00`
Promotion: `NOT_REQUESTED`

## Decision

Reconcile two Phase 01 rows against their exact source acceptance without
converting local implementation, an isolated local commit or unavailable
hosted/public evidence into a stronger release claim.

## Stable public trust surface

The source plan explicitly defines `Kiwunaka/pokrov` as a trust surface, not a
UI source. Stable 1.2.0 must publish canonical APK/EXE assets, checksums,
signature metadata, manifest, release notes, minimum OS/architecture, app
build, Core version/ABI, build date, source commits, channel, known issues and
upgrade notes.

The strict v2 handoff defines these identities and the client staging gate
keeps them out of source/history paths. The actual public baseline is now
audited, and isolated release-index revision
`f07654af496d042fa8dba3d8b2695e987c8e9eb7` implements the fail-closed v2
source contract. It remains unpublished and has no owner-controlled active
signing key. `FE/P12-023` is therefore `I2`, not public/candidate proof.

## Freeze/contracts train

The PR-00 inputs are implemented across their canonical owners:

- WO-001 records exact repository baselines, lanes and promotion branches;
- WO-002/003 define and consume strict release-handoff v2 plus explicit
  pre-candidate/release flags;
- WO-008A owns the deterministic product/commercial fact snapshot;
- WO-006A/006I own the stable reason-code catalog and generated support view;
- WO-010E owns cross-platform motion/reduced-motion semantics.

Current commercial-contract generation and the focused manifest/catalog tests
pass `73/73`; focused client motion/app-shell regression passes `164/164`.
Dedicated branch `codex/1.2.0-pr00-true` now adds exactly one commit,
`1632234bb78d18b09fa83cd02249d27859b1c409`, over the source plan's actual
platform promotion base `280ed9157f5804d4bc719cb8d6cab471caafb937`. Its
validator returns `PASS_RELEASE_BASE_ISOLATED_NO_VISIBLE_UI`, binds four exact
contract snapshots and permits nine contract/evidence paths with zero visible
UI paths. Prior `dcfbbce...` was isolated only against a local aggregate parent
and is withdrawn. The corrected branch is not pushed and hosted required
checks are `NOT_RUN`, so `FE_PR/PR-00` remains `I2`, not `I3`.

Evidence:

- `evidence/003J-phase01-residual-reconciliation/003J-phase01-residual-reconciliation.json`;
- `evidence/013K-pr00-isolated-result/013K-pr00-isolated-result.json`.

## Evidence ceiling

A local public-index checkout/implementation and a local isolated
no-visible-UI commit now exist. A published owner-key-ready index, hosted PR,
review, required checks, signed artifact, candidate, publication and promotion
do not. Those are external/owner evidence gaps, not documentation gaps.
