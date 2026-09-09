# R12-C03 — checkout state ownership and local sequence acceptance

2026-09-06. Platform source `a50d446`, client `70907c0`, Core `8dc57a8`.
**I3: extraction sequence implemented and locally verified.** Current packaged
acceptance and N01/N03 runtime dependencies remain OPEN; this is not release
readiness. [Receipt and committed source hashes](evidence/c03-checkout.json).

`useCheckoutController` owns catalog/provider readiness, quote input identity,
expiry, immutable order intent, recovery after uncertain create and payment
return polling. The component renders its state and invokes its actions. Effect
dependencies, abort/deadline behavior, acquisition independence, order payload,
server quote/return authority and all JSX are retained.

The view shrinks 1259 → 435 lines; the controller contains 939 lines, including
the existing typed API helpers and presentation projections. This is an explicit
state owner, not a claim of reduced total code, bundle size or faster rendering.
Canonical implementation boundary: `marketing/README.md`.

## Evidence

- AST node-text comparison against exact baseline `04923e1`: **69 state/effect
  statements and 23 helper bodies identical**, checkout JSX and loading fallback
  identical. The retained script uses the pinned baseline. This source proof is
  supplemental to the browser checks.
- `npm.cmd run build`, `npm.cmd run check:seo`, `npm.cmd run check:responsive`
  from `marketing`: **PASS**. Responsive suite runs the separate nine-scenario
  `checkCheckoutAuthority` fixture: invalid quote, missing token, expiry, input
  race, optional acquisition, read timeout, key race, mutation retry and quote
  change. API responses are synthetic; no provider/payment was called.
- `npx.cmd eslint src/app/checkout/checkout-client.tsx
  src/app/checkout/use-checkout-controller.ts`: **PASS**, no warnings. Build
  includes the final TypeScript check.
- Root pytest for commercial, marketing story, frontend text, public copy,
  governance, winback and visual-smoke contracts: **55 PASS**. Checks now follow
  both files without dropping their existing assertions. One obsolete snippet
  was already absent from `04923e1`; it now checks the actual ticket binding plus
  typed payload spread instead of the old explicit-property spelling.
- `python -B scripts/ui_visual_smoke.py` and
  `python -B scripts/check-links.py --report E:/r12-c03-checkout-link-report.md`:
  **PASS**. New owner copy remains in the public-copy and mojibake scan surface.
- Current client `70907c0`: `flutter test
  test/managed_profile_lifecycle_test.dart test/account_session_coordinator_test.dart
  test/connection_experience_test.dart test/support_conversation_controller_test.dart
  test/support_polling_test.dart` — **33 PASS**, cwd `packages/app_shell`.
  The earlier [support report](EXECUTION-C03-SUPPORT.md) retains 208 widget and
  coordinator checks for the same client source.

Initial attempts with missing/unused moved imports and the obsolete contract
snippet are retained as failures/warnings, not counted as passes. The final
build, lint, contract and browser runs above cover the committed source.

## C03 requirement-by-requirement state

| Requirement | Evidence | Current result |
| --- | --- | --- |
| Profile lifecycle first | [C03A](EXECUTION-CONTINUED.md#c03a--standalone-managed-profile-lifecycle-owner), current standalone tests | I3 PASS |
| Connection/presentation ownership | Existing coordinator/reducer/presenter, 14 current standalone tests | I3 PASS; no additional split needed |
| Account/support state | [Account](EXECUTION-C03-ACCOUNT.md), [support](EXECUTION-C03-SUPPORT.md), current isolated tests | I3 PASS |
| Checkout ownership | `useCheckoutController`, exact extraction comparison, nine feature browser cases | I3 PASS |
| Separate extraction and behavior changes | Client extraction `e91b85d` before fix `70907c0`; checkout extraction has identical state/effects/JSX | PASS |
| Root/part growth guard | Prior profile/account extracts shrink bootstrap; current bootstrap unchanged at 6482; 29 parts; checkout view reduced | PASS for composition roots; import/export wiring adds lines in library entrypoints |
| No size-based speed claim | Counts describe placement only; no new performance target is claimed | PASS |

No additional source extraction is required by the inspected C03 sequence.
Registry remains active / I3 / NEEDS_RUNTIME_PROOF pending dependency-bound
installed candidate checks. Checkout browser tests are functional feature tests,
not isolated hook unit tests or real provider evidence. The overall plan is OPEN.

Evidence and screenshot paths/hashes are retained in the receipt. Existing
untracked marketing instruction files are excluded; client/Core sources and
native binaries are unchanged by this platform commit. No push, merge, deploy,
publication, signing, purchase, provider mutation or new release candidate.
The responsive runner stopped its local server. Rollback is the scoped platform
commit; previous client, candidate and audit evidence is preserved.

Platform handoff PASS: docs/context pytest 33;
`agent_context_packet_audit.py --platform-context-root .`;
`validate_package.py` — 13 import hashes, 83 R12 IDs, 378 legacy IDs,
255 local links; `git diff --check`. Receipt binds ten committed platform blobs,
14 archive files and 57 retained responsive screenshots.
