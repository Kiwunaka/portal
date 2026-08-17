# WO-008 — Release And Production Proof

Status: `IN_PROGRESS`

## Required gates

- focused and affected backend tests, migration smoke and secret/diff checks;
- Flutter analyze/tests for client telemetry;
- admin lint/build/E2E/accessibility and marketing lint/build/SEO/responsive;
- exact scoped diff review in both repositories;
- commit and push platform/client promotion branches;
- deploy platform services and static apps, enable draft-only news worker;
- current-origin health/readbacks and Browser proof of the compact production
  Telegram menu;
- no new client binary unless the exact client diff is intentionally released.

Manual or blocked evidence remains labelled; it is never converted to PASS by
documentation alone.
