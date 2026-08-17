# WO-006 — Admin Observability And Usability

Status: `COMPLETED_LOCAL_PENDING_PROD_READBACK`

`/funnel` now includes product quality totals, safe errors by category/code,
stage/subsystem/network/version and source freshness. `/broadcast` shows exact
delivery reasons and retry limits. `/news` adds daily source/run status and a
manual editor queue. All reads are bounded; all writes remain action-intent
protected.

Admin lint/build and focused authenticated E2E are release gates. Production
visual readback remains `BLOCKED_BY_ACCESS` until the owner supplies a current
admin browser session after deploy.
