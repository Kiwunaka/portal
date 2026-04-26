# Public Beta Release Runbook

Last updated: 2026-04-26

## Current Decision

Do not release publicly until P0 evidence gates are green.

## Gate Order

1. Run local platform tests.
2. Run marketing and webapp builds.
3. Run client preflight against `POKROV-app`.
4. Attach runtime download smoke evidence.
5. Attach Lava.top provider evidence or keep checkout unavailable.
6. Attach Android physical release-build audit evidence.
7. Attach current-origin, brain-origin, and RU-origin reports separately.
8. Update launch decision before deploy or announcement.

## Blocked Means Blocked

If a gate depends on missing credentials, external host access, signing, or physical device access, record `blocked by missing access` instead of substituting a local check.

Keeping checkout unavailable is acceptable only for preparation work or a tightly gated beta scope. It does not make a broad public release green; public paid launch still requires Lava.top evidence.
