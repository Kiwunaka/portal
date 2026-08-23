# WO-003F — Release notes and visible version authority

Status: `LOCALLY_PROVED_I3`
Phase: `01`
Ledger row: `REL_DOD/DOD-16`
Promotion: `NOT_REQUESTED`

## Intent

Close the remaining consumer gap in the strict release-handoff v2 path. A new
candidate must carry one version-matched release-note record, prove that its
package/UI version agrees with the same handoff, and project both facts into
the app and cabinet without a parallel manifest or operator-authored runtime
override.

## Closed contract

- Strict schema v2 requires `release.release_notes.summary` and a canonical
  GitHub release URL whose tag matches `release.version`. The summary is a
  bounded single line so runtime env projection cannot split the value.
- The client generator requires and preserves that record. Before generating
  the handoff, it rejects any candidate version that differs from Android,
  Windows or app-shell package identity.
- Android and Windows release builds pass their package-derived public version
  through `POKROV_APP_VERSION`. The shared `pokrovClientVersion` value owns
  update requests, diagnostics and visible profile/navigation version text.
  This avoids the circular and invalid design of rebuilding an artifact after
  its final hash was placed in the handoff.
- Runtime sync validates the exact v2 handoff and projects its version, release
  notes URL/summary and creation time to both Android and Windows `APP_*`
  values. It does not preserve a second notes source for v2.
- `/api/client/apps` supplies those facts to the existing client update prompt
  and authenticated cabinet. The cabinet renders the summary and canonical
  notes link next to version/date/size/channel/checksum; missing notes make the
  release tuple partial and hide direct download.
- Legacy schema v1 remains migration-only metadata for retained releases. No
  public candidate, deploy, runtime sync or promotion was created.

## Retained local proof

- Strict platform schema, validator and runtime projection: `PASS`, `57/57`.
- Client generator/parity/UI-identity contract: `PASS`, `15/15`.
- Client seed/docs/cross-repo contract scaffold: `PASS`.
- Exact client update-prompt widget test: `PASS`, `1/1`; the visible target
  version and release-note summary came from the same update payload.
- Authenticated/public client-app API projection: `PASS`, `6/6`.
- WebApp production build: `PASS`, 40 static routes.
- Cabinet Playwright: final `PASS`, `67/67`, including version, notes URL,
  notes summary and all other release-card facts for Android and Windows.
- The first cabinet run retained `66/67`: an older secondary-APK fixture lacked
  the newly mandatory notes fields, so the fail-closed UI correctly removed
  its download action. The fixture was completed and the full suite reran.
- Candidate preflight remains honestly `BLOCKED` by five conditions,
  `candidate_created=false`, with 114 ledger rows below `I3`.
- Documentation/context/preflight tests: `PASS`, `34/34`; platform context,
  documentation links, JSON parsing and scoped diff checks: `PASS`.

Evidence:
`evidence/003F-release-identity-consumers/003F-release-identity-consumers.json`.

## Evidence ceiling

This is local source, generator, API, package-parity, widget, production-build
and browser-fixture proof. All three worktrees remain dirty; the public release
index and exact 1.2.0 candidate are absent. Hosted CI, signed artifact identity,
deployed runtime/cabinet readback and promotion remain unproved or unauthorized.
`REL_DOD/DOD-16` therefore advances to `I3`, not `I4`.
