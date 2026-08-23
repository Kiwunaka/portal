# WO-004A2 — Direct Cutover And Visual Baseline

Status: `COMPLETE_I3`
Classification: `ACTIVE_EXECUTION`
Phase: `02`
Lane: active client connection presentation

## Bounded outcome

Close the two remaining frontend PR-train rows from `WO-004A` without
reintroducing a second connection-state authority:

- accept the implemented direct cutover to the typed reducer/coordinator as
  the owner decision for `FE_PR/PR-01`;
- retain deterministic widget goldens for the critical idle, first-route,
  verified and degraded presentation states required by `FE_PR/PR-02`.

This follow-up changes no runtime behavior and creates no candidate, artifact,
signing, publication, deployment or physical-device evidence.

## Authority decision: direct cutover

The source plan proposed a bounded debug old/new shadow period while the old UI
remained active. That migration mechanism is no longer safe or useful in the
current tree:

1. `ConnectionCoordinator` owns the only mutable runtime snapshot, explicit
   transition intent, action-in-flight flag and attempt state.
2. `ConnectionExperienceReducer.reduce` and
   `ConnectionPresentation.fromExperience` are derived only inside the focused
   connection boundary.
3. Home consumes one immutable `ProtectionViewState` and one
   `ProtectionIntents` boundary. The boundary contract rejects parallel raw
   connection fields, copy and callbacks in the composition root/Home props.
4. Profile, support, Home, the connect disc and the shell controller consume
   the shared presentation instead of owning a legacy status reducer.

Recreating a legacy reducer merely to compare it with the accepted reducer
would restore two connection truths and weaken the architecture already proved
by `WO-004A`. The owner decision is therefore **direct cutover accepted**. Any
future comparison must use retained input/output fixtures against the one
canonical reducer, not a second live state machine.

## Visual baseline

The active client now retains four deterministic `390 x 844` widget goldens:

- `home-idle-light.png`;
- `route-scope-dark.png`;
- `home-verified-dark.png`;
- `home-degraded-light.png`.

The golden test disables animations, isolates the image cache, renders the
real Home flow, compares without update mode and passes for all four images.
The separate semantics test proves that the CTA and live protection status use
the single presentation source without duplicate announcements.

## Verification — 2026-08-22

- `powershell -NoProfile -ExecutionPolicy Bypass -File .\test\client-presentation-boundary.ps1`: `PASS`.
- `flutter test test/connection_experience_test.dart`: `14/14 PASS`.
- `flutter test test/pokrov_seed_app_test.dart --plain-name "matches deterministic critical-state goldens"`: `1/1 PASS` covering four retained images.
- Source search finds reducer/presenter construction only in
  `connection_experience.dart`; no second live reducer/presenter owner is
  present under `packages/app_shell/lib`.
- Ledger/JSON assertions: `377` rows with
  `I3=276, I2=36, I1=45, I0=20`; both current evidence documents parse.
- Platform documentation, context and candidate-preflight regression:
  `41/41 PASS`; context audit and link check: `PASS`.
- Live candidate preflight remains honestly `BLOCKED` with seven blockers,
  `candidate_created=false`, `101` rows below `I3` and stage split
  `31/32/17/21`.
- SHA-256 identities and exact command results are retained in
  `evidence/004A2-direct-cutover-visual/004A2-direct-cutover-visual.json`.

## Ledger decision

- `FE_PR/PR-01`: `I1 -> I3`, `LOCALLY_PROVED`. Direct cutover is the accepted
  migration decision and the one-owner boundary is guarded.
- `FE_PR/PR-02`: `I1 -> I3`, `LOCALLY_PROVED`. Presenter/disc/haptic behavior
  and the four deterministic critical-state goldens pass.

The evidence ceiling is `I3`. Physical Android/Windows rendering, TalkBack,
Narrator, OS scaling and exact-candidate screenshots remain Phase 11
`MANUAL_OWNER_TEST`/candidate evidence before `I4`.
