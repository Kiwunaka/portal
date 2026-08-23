# WO-003G — Current readiness and retained history separation

Status: `LOCALLY_PROVED_I3`
Phase: `01`
Ledger rows: `REL/DOC-001`, `REL_DOD/DOD-19`
Promotion: `NOT_REQUESTED`

## Intent

Make every active release-readiness document answer only the current 1.2.0
question. Candidate-specific results and obsolete release targets remain
available as dated evidence, but cannot masquerade as current state or approve
new bytes.

## Closed contract

- The active client backlog, cutover, Android, Windows and WARP documents now
  describe the retained public `1.1.6` line and the uncreated `1.2.0+30`
  `PRE_CANDIDATE_LOCAL` target only. Their previous bodies are preserved under
  explicit `EVIDENCE` history paths.
- The active responsive gate names `1.2.0+30`; its old `1.0.0-beta` wording is
  retained separately. Motion/performance and Apple checklists explicitly name
  their current `ACTIVE_EXECUTION` role and exact-candidate/manual boundary.
- The client registry classifies eight current readiness owners separately from
  the history directories. Its executable contract rejects a stale candidate
  status in an active readiness owner and rejects snapshots without an
  evidence-only promotion boundary.
- The canonical client platform matrix now agrees with the retained public
  `1.1.6` Android/Windows truth. Windows still fails closed for new promotion
  pending trusted signing; Android's exact Huawei follow-up remains manual.
- The platform public-beta runbook and 2026-08-13 direct-release tracker are
  registry-classified `EVIDENCE`. The latter points current execution to the
  1.2.0 megaplan, and neither retained document is part of the active release
  owner test set.
- No history was deleted, no old status was converted into a pass and no
  candidate, signing, deploy, sync or promotion action was performed.

## Retained local proof

- Client documentation registry/current-history contract: `PASS`.
- Full client seed, release-v2, parity and cross-repository contract gate:
  `PASS`; Core remains `DIRTY_DEVELOPMENT_REPLACEMENT_PENDING`.
- Platform documentation/context tests: `PASS`, `31/31`.
- Platform context audit and documentation-link contract: `PASS`.
- JSON parsing and scoped whitespace/diff checks: `PASS`.
- Candidate preflight remains honestly `BLOCKED` by five conditions,
  `candidate_created=false`, with 112 ledger rows below `I3`.

Evidence:
`evidence/003G-readiness-current-history/003G-readiness-current-history.json`.

## Evidence ceiling

This proves local classification, canonical seed alignment and executable
documentation contracts. All three worktrees remain dirty; the public release
index and exact 1.2.0 candidate are absent. Hosted CI, signed artifact identity,
physical-device/clean-machine proof, deployed readback and promotion remain
unproved or unauthorized. `REL/DOC-001` and `REL_DOD/DOD-19` therefore advance
to `I3`, not `I4`.
