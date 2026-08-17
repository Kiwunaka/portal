# WO-006 — Admin Observability And Usability

Status: `COMPLETED_WITH_PROD_AUTH_LIMIT`

`/funnel` now includes product quality totals, safe errors by category/code,
stage/subsystem/network/version and source freshness. `/broadcast` shows exact
delivery reasons and retry limits. `/news` adds daily source/run status and a
manual editor queue. All reads are bounded; all writes remain action-intent
protected.

Admin lint/build, production build and the full authenticated E2E suite passed
(`60/60`). The public production `/news/` shell returns HTTP 200 and the worker
readback proves current data, but the production browser session was expired and
could not be renewed from its existing cookie. Authenticated production visual
inspection therefore remains exactly `BLOCKED_BY_ACCESS`, not a claimed PASS.
