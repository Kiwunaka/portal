# WO-008M — Subscription and checkout aggregate

Status: `COMPLETE_LOCAL_I3`
Phase: `06`
Row advanced: `FE_PR/PR-05`
Promotion: `NOT_REQUESTED`

## Outcome

Close the frontend source plan's complete local subscription/checkout
aggregate across active Android/Windows, cabinet, marketing and backend. Reuse
the existing server catalog, offer, order, entitlement and payment owners; do
not turn telemetry, browser storage or the active client into payment truth.

## Implemented boundary

- Access state: cabinet maps all six canonical server access states to the
  correct subscription title and primary action. Unknown states produce a
  neutral management action. Payment-return states are displayed separately
  and never imply entitlement from payment telemetry.
- Capabilities: cabinet and marketing render the ordered server provider
  capability response. Unavailable methods stay disabled with the returned
  reason, and backend order creation rejects a disabled method even if a
  client submits it directly.
- Revalidation and idempotency: only a current catalog plan and valid signed
  offer can create an order. Locked revalidation covers subject, provider,
  price, revision, terms, capacity, reservation and deadline before provider
  I/O; retry and callback paths preserve deterministic lock order and an
  existing pending order cannot be paid again as a fresh order.
- Return path: an identity-free signed capability is stored in versioned
  session storage. Redirect URLs contain only a bounded surface/provider hint.
  The token-only no-store status endpoint exposes the closed
  processing/paid/failed/cancelled/manual-review/expired contract. Cabinet
  refreshes access after paid and keeps paid/access-stale on explicit refresh
  and support actions.
- Active client: Profile consumes the live subscription and server plan price,
  displays subscription details and opens the bounded checkout handoff. It
  does not calculate price, select providers or infer payment success.
- Payment analytics: bounded checkout-start, click and pay-attempt facts feed
  abandoned-funnel diagnostics. Signed provider callbacks and external orders
  remain the only accounting truth; telemetry cannot fulfill access.
- Accessibility/performance: the current cabinet critical checkout route is
  covered by the existing axe, narrow-viewport, deterministic visual and
  no-waterfall gates; the active-client and cross-surface local quality owners
  remain unchanged.

## Index decision

`FE_PR/PR-05` advances `I2 -> I3`: each of the source aggregate's five named
concerns—access state, capabilities, revalidation, return page and payment
analytics—has a current local implementation and test path. This does not
raise the evidence ceiling of provider-specific `FE/P12-012..014` or broad
atomic-deploy `MKT/MKT-600`; those rows remain `I2` until their external and
exact-candidate acceptance facts exist.

Distribution becomes `I3=303`, `I2=19`, `I1=40`, `I0=15`; `74` rows remain
below `I3`. Stage split becomes `3/33/17/21`.

## Local proof

- Payment return, commercial consumer/order and payment-funnel backend matrix:
  `30/30` PASS.
- Active-client subscription details and server-price/API paths: `2/2` PASS.
- WebApp production build: PASS, 40 static routes.
- Cabinet/rewards Playwright: `69/69` PASS, including all access states,
  every return state, paid/access mismatch, provider fail-closed behavior,
  checkout concurrency, axe, narrow viewport and deterministic visuals.
- Marketing lint and SEO: PASS. Responsive gate, including its own production
  build, no-JS, reduced-motion and browser matrix: PASS.
- Documentation and candidate-preflight contracts: `37/37` PASS; platform
  context audit: PASS. Read-only preflight remains expected `BLOCKED` with
  seven blockers, no candidate and exact pending split `3/33/17/21`.
- Scoped diff and secret checks: PASS, zero secret-pattern matches.

Machine evidence:
`evidence/008M-subscription-checkout-aggregate/008M-subscription-checkout-aggregate.json`.

## Evidence ceiling

This is local source/test/build evidence from dirty development worktrees. No
live provider redirect, real payment, PostgreSQL two-connection concurrency,
Android/Windows physical-device payment return, deployed analytics readback,
exact candidate, hosted clean check, deployment, publication or promotion ran.
Those facts remain required before `I4` and broad commercial-consistency
closure.
