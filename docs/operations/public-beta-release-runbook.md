# Public Beta Release Runbook

Last updated: 2026-05-15

## Current Decision

Do not release publicly until P0 evidence gates are green.

## Gate Order

1. Run local platform tests.
2. Run marketing and webapp builds.
3. Run client preflight against `POKROV-app`.
4. Attach runtime download smoke evidence.
5. Attach Lava.top provider evidence for the exact checkout route being enabled; the authenticated cabinet beta path has `2026-05-15` evidence, while failed-payment, reconciliation, and anonymous paid-key delivery still need separate evidence.
6. Attach Android physical release-build audit evidence.
7. Attach current-origin, brain-origin, and RU-origin reports separately.
8. Update launch decision before deploy or announcement.

## Blocked Means Blocked

If a gate depends on missing credentials, external host access, signing, or physical device access, record `blocked by missing access` instead of substituting a local check.

Keeping checkout unavailable is acceptable only for preparation work or a tightly gated beta scope. The `2026-05-15` Lava.top evidence allows the authenticated cabinet beta path to stay enabled, but it does not by itself make a broad public release green.
