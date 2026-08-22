# WO-003H — Cross-repository version truth reconciliation

Status: `LOCALLY_PROVED_I3`
Phase: `01`
Ledger row: `REL/VER-001`
Promotion: `NOT_REQUESTED`

## Intent

Close the active version drift that left client packages, API/UI projection and
platform owner documentation on different release lines. Preserve one release
authority: the client release-handoff seed for retained/development truth and a
generated strict-v2 handoff for a new exact candidate.

## Closed contract

- Client parity validates Android and Windows `1.2.0+30`, app-shell product
  `1.2.0`, retained public `1.1.6`, Core `1.0.3` and intended Core `1.1.0`.
- The active platform publishing, deployment, developer and repository-map
  owners now project retained public `v1.1.6` / `1.1.6+29` and working
  `1.2.0+30` `PRE_CANDIDATE_LOCAL` with `candidate_created=false`.
- The standard client release gate derives those required platform-document
  facts from `config/release-handoff.seed.json` and fails when a required owner
  is missing or stale. CI already runs that gate with explicit platform/Core
  roots; a source contract prevents removal of the cross-repository check.
- Strict-v2 runtime projection and `/api/client/apps` remain the version source
  for the update prompt and release cards. No platform mirror manifest or
  handwritten runtime override was added.
- Six completed or superseded `1.0.4-beta.1` through `1.1.1` work-order waves
  are registry-classified `EVIDENCE`; their bodies and exact old claims remain
  retained but no longer masquerade as active release truth.

## Retained local proof

- Full client seed/parity/release-v2/cross-repository contract gate: `PASS`.
- Platform docs/context plus strict schema/runtime projection: `PASS`, `89/89`.
- Exact authenticated/public client-app API release slice: `PASS`, `6/6`, with
  12 existing `datetime.utcnow()` warnings.
- Exact client update prompt/version widget: `PASS`, `1/1`.
- The first adjacent broad observation was `NOT_PASS`, `97/98`: an old
  program-application review test omitted the now-required action intent and
  received the correct `428 intent_required`. The fixture now proves the direct
  fail-closed response, prepares the L3 intent, confirms the exact application
  ID, replays the same idempotency key and checks the opaque grant reference.
  The exact test passes `1/1`, its full file passes `9/9`, and the final combined
  platform slice is `98/98`.
- Candidate preflight remains honestly `BLOCKED` by five conditions,
  `candidate_created=false`, with 111 ledger rows below `I3`.

Evidence:
`evidence/003H-version-truth/003H-version-truth.json`.

## Evidence ceiling

This proves local package parity, handoff-derived documentation, API/UI
projection and executable cross-repository contracts. All worktrees remain
dirty, the public release index and exact 1.2.0 candidate are absent, and hosted
CI/deployed readback/signing/promotion remain unproved or unauthorized.
`REL/VER-001` therefore advances to `I3`, not `I4`.
