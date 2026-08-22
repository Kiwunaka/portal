# WO-003E — Shared release catalog consumer reconciliation

Status: `LOCALLY_PROVED_I3`
Phase: `01`
Ledger row: `FE/P12-010`
Promotion: `NOT_REQUESTED`

## Intent

Reconcile the Phase 01 backlog with behavior already delivered through
`WO-010D1` and the strict release-handoff v2 path. Prove that the portal does
not invent a second release catalog and that a user can inspect every required
release fact before downloading Android or Windows artifacts.

## Closed contract

- The release-handoff runtime projection remains the server authority behind
  `/api/client/apps` and its fail-closed `/api/public/client-apps` projection.
- The authenticated cabinet reads that catalog. Marketing install and homepage
  actions read the public projection of the same catalog.
- Android and Windows release cards show version, publication date, positive
  size, architecture/format, channel and the full SHA-256.
- A direct download is rendered only for a complete release tuple. Missing or
  partial metadata renders an explicit unavailable/support state and never
  substitutes an artifact from another platform or an unbound mirror.
- No new catalog, component library, dependency or release authority was
  introduced. Existing POKROV tokens, information architecture, focus states,
  reduced-motion behavior and mobile layout were preserved.

## Retained local proof

- WebApp production build: `PASS`, 40 static routes.
- Focused cabinet Playwright: `PASS`, `67/67`, including the exact Android and
  Windows version/date/size/architecture/channel/SHA-256 assertion.
- Authenticated/public client-app catalog projection: `PASS`, `6/6`.
- Focused marketing install and visible-copy contracts: `PASS`, `14/14`.
- Documentation/context/preflight tests: `PASS`, `34/34`; context audit,
  documentation links and scoped diff check: `PASS`.
- Candidate preflight remains honestly `BLOCKED` by five conditions, with 115
  ledger rows below `I3`; no candidate was created.
- The first wider adjacent API/marketing/copy run retained one unrelated
  homepage-contract failure after 47 passes plus 4 subtests. `WO-011H` aligned
  the stale `ServicesGrid` and hero-copy expectations with the governed page;
  the final wider rerun passed 48 tests plus 4 subtests.

Evidence:
`evidence/003E-shared-release-catalog/003E-shared-release-catalog.json`.

## Evidence ceiling

This is local source, API, production-build and browser-fixture proof. The
platform worktree is dirty and no exact 1.2.0 candidate, authenticated/public
deployed readback, hosted CI, published artifact verification, signing, deploy
or promotion was produced. `FE/P12-010` therefore advances to `I3`, not `I4`.
