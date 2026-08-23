# WO-006I — Safe transport failure classification

Status: `COMPLETE_LOCAL_I3`
Phase: `04`
Ledger rows: `OBS/OBS-050`, `REL_GATE/GATE-B`
Promotion: `NOT_REQUESTED`

## Outcome

Replace the generic transport bucket at the Core start boundary with four
closed, support-actionable classes while preserving the existing event ABI and
the rule that raw provider, destination, credential and protocol text never
crosses into client diagnostics.

## Implemented contract

- The canonical platform catalog now has 121 entries and four additive codes:
  `TRANSPORT-001` timeout, `TRANSPORT-002` connection refusal,
  `TRANSPORT-003` authentication rejection and `TRANSPORT-004` protocol
  negotiation failure.
- Core classifies typed deadlines, typed network timeouts and refusal errors
  before applying a bounded reviewed marker set. Configuration failures remain
  `CORE-005`, generic connection failures remain `CORE-006`, and unknown start
  failures remain `CORE-003`.
- Core event schema/ABI versions remain `1`; desktop ABI remains `2`. Only the
  closed error-code set changes, so no callback or binary ABI v3 is introduced.
- Dart runtime translation, Android parsing and Windows service fencing accept
  exactly the four new codes. Unknown event names and raw URL/secret-like error
  material remain rejected.
- Platform, client and Core snapshots bind the new catalog SHA-256
  `7d3bf242777d5bf76bbebcf162e5969d3f83d7f68b2787051e1c4fddeadc3dc7`;
  the event-schema SHA-256 remains
  `3044d28db7e1e047654427bc0c38e5e33e95f2e48ec2c72cbbdf07e01d42ff13`.
- The generated support reference exposes only stable Russian messages,
  reviewed operator actions, retry policy and release-blocking status.

## Local proof

- Platform catalog/reference/handoff regression: `75/75` PASS; validator reports
  121 entries and exact cross-repository hashes.
- Core canonical release gate: PASS on Go `1.25.13`, including ABI,
  observability, AWG2, supported package, daemon/libbox and TLS/uTLS checks.
  Both start classifiers pass eight reviewed cases plus planted raw-material
  rejection.
- Observability contracts: `3/3` PASS; observability runtime: `27/27` PASS.
- Android direct/store focused JVM gates: `BUILD SUCCESSFUL`; the parser accepts
  all four transport codes and rejects a planted URL with token material.
- Windows service runtime target rebuilt; the serial native executable passes
  with all four codes and raw-material rejection.
- Gate B focused state/diagnostics/migration tests: `24/24` PASS;
  runtime-engine: `59` PASS plus one declared exact-old-DLL skip.
- Full client seed/version/observability/source/hygiene/docs contract: PASS.

Evidence:
`evidence/006I-transport-failure-classification/006I-transport-failure-classification.json`.

## Evidence ceiling

This is local source/test evidence from dirty development worktrees. No exact
candidate, physical-device runtime observation, provider response, operator
production readback, signing, publication or promotion was created. The two
rows reach `I3`, not `I4` or `I5`.
