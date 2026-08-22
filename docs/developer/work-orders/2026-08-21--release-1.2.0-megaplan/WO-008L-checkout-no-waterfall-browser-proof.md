# WO-008L — Checkout no-waterfall browser proof

Status: `COMPLETE_LOCAL_I3`
Phase: `06`
Row advanced: `FE/P12-120`
Promotion: `NOT_REQUESTED`

## Outcome

Prove that independent portal checkout data starts concurrently in real
browsers. Preserve the required dependency boundary: an offer preview may only
run after a verified catalog and selected plan exist.

## Authority reconciliation

The source plan assigns `P12-120` to `portal` and defines its acceptance as “No
unnecessary waterfall.” The former ledger next action incorrectly expanded it
to an active-client path. This closure follows the source criterion and covers
both portal checkout surfaces: authenticated cabinet and public marketing.

## Implemented proof

- Cabinet probe intercepts catalog and payment-provider requests, withholds
  both responses and requires both requests to arrive first (`2/2`).
- Public-checkout probe intercepts catalog, payment-provider and acquisition
  handoff requests, withholds all responses and requires all three to arrive
  first (`3/3`).
- Each probe enforces a start-time spread below 500 ms. A sequential await of
  any intercepted request times out/fails the gate.
- Existing offer-preview effects stay sequenced after catalog and active-plan
  state. No speculative request or client-owned offer calculation was added.

## Index decision

`FE/P12-120` advances `I2 -> I3`. Distribution becomes `I3=299`, `I2=21`,
`I1=40`, `I0=17`; `78` rows remain below `I3`. Stage split becomes
`7/33/17/21`.

## Local proof

- WebApp focused ESLint: PASS.
- Marketing ESLint: PASS.
- WebApp optimized production build and focused concurrency browser test:
  `1/1` PASS.
- Full WebApp cabinet/rewards browser suite: `69/69` PASS.
- Marketing production build plus responsive, no-JS, reduced-motion, a11y,
  interaction and checkout-concurrency gate: PASS.
- Docs/candidate-preflight contracts: `37/37` PASS.
- Live explicit-root preflight: expected `BLOCKED`, seven blockers,
  `candidate_created=false`, pending stages `7/33/17/21`.

Machine evidence:
`evidence/008L-checkout-no-waterfall-browser-proof/008L-checkout-no-waterfall-browser-proof.json`.

## Evidence ceiling

This is dirty-worktree local source/test evidence. Timings are ordering guards,
not a deployed-origin performance benchmark. No exact candidate, real provider
or public-origin readback, payment, deployment, publication or promotion
occurred.
