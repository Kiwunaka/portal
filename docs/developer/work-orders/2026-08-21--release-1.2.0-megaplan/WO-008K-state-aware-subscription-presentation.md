# WO-008K — State-aware subscription presentation

Status: `COMPLETE_LOCAL_I3`
Phase: `06`
Row advanced: `FE/P12-011`
Promotion: `NOT_REQUESTED`

## Outcome

Make the authenticated cabinet subscription entry point describe the account's
actual server-owned access state. The client remains a presenter: it does not
recalculate entitlement, price, offer eligibility or provider readiness.

## Implemented boundary

- `getAccessState` now accepts only the six canonical states from the shared
  access matrix. Empty, unknown and future values normalize to an unknown
  presentation state.
- One policy maps every canonical state to the subscription hero title and its
  primary checkout action:
  - paid unlimited: extend full access;
  - trial/bonus premium: choose a paid term for continuation;
  - free monthly/soft mode: remove the applicable limit;
  - expired or blocked: restore access.
- Unknown state uses neutral copy and makes no active, premium, trial or expiry
  claim.
- Every action keeps the existing `/subscription/checkout/` boundary, where
  catalog, provider capability, offer and payment state are revalidated.

## Index decision

`FE/P12-011` advances `I2 -> I3`. The exact source acceptance condition —
subscription title and CTA correspond to access state — is now proved for the
full local matrix and its unknown-state guard.

Distribution becomes `I3=298`, `I2=22`, `I1=40`, `I0=17`; `79` rows remain
below `I3`. Stage split becomes `8/33/17/21`.

## Local proof

- Focused ESLint for policy, subscription page and browser spec: PASS.
- WebApp optimized production build and TypeScript: PASS.
- Focused state-matrix Playwright test: `1/1` PASS; its single test contains
  seven browser cases (six canonical states plus unknown).
- Full cabinet and rewards Playwright regression: `68/68` PASS.
- Docs/candidate-preflight contracts: `37/37` PASS.
- Live explicit-root preflight: expected `BLOCKED`, seven blockers,
  `candidate_created=false`, pending stages `8/33/17/21`.

Machine evidence:
`evidence/008K-state-aware-subscription-presentation/008K-state-aware-subscription-presentation.json`.

## Evidence ceiling

This is dirty-worktree local source/test evidence. No exact candidate,
authenticated deployed-server readback, real provider/public-origin run,
payment, deployment, publication or promotion occurred.
