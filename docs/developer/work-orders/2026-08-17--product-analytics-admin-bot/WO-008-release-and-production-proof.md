# WO-008 — Release And Production Proof

Status: `COMPLETED`

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

## Exact result

- Platform promotion: `master`, runtime code commit `09b228e`; production source
  hashes for `news_draft_service.py`, `bot.py` and `events_service.py` match the
  local commit byte-for-byte.
- Client promotion: `main` at `6575c22`; no new binary was cut. Public stable
  remains `1.1.1`, and the telemetry diff waits for the next physically verified
  client release.
- Predeploy PostgreSQL backup:
  `/root/portal_bot/db-backups/portal-predeploy-20260817T173013Z.dump`,
  107053466 bytes, SHA-256
  `6088f9b6f15cfcea3f62fab170363bf99ac4f8f22ee60bcb250a7c4e47e9d0fe`.
- Latest backend rollback copy:
  `/root/portal_bot.deploy-backups/20260817T174324Z-88504`.
- Static release `20260817173205` was atomically switched for marketing,
  webapp and adminapp.
- `verify_brain_ready.py --brain-ip 82.21.114.104 --repeat 2` passed after the
  final runtime deploy: Caddy and all five portal units active, health 200, both
  SRS rules valid, current public apps served, and both subscription reads had
  7 lines, 7 hosts and 33 outbounds.
- `brain_telegram_bot_menu_check.py --brain-ip 82.21.114.104` passed against the
  live bot token without exposing it. Commands and the web-app menu button match
  the deployed contract.
- Live Browser `/start`, Help and Back proof passed; see evidence 35 and 36.
- Flutter analyze, full 304-test suite, seed/docs contracts; admin lint/build and
  60/60 E2E; marketing lint/build/SEO/responsive; webapp lint/build; affected
  backend, contract and news tests; secret/PII scan and `git diff --check` passed.

## Honest limits

- Authenticated production admin visual audit is `BLOCKED_BY_ACCESS`: the open
  browser tab had an expired session and its existing session renewal failed.
  Public shell HTTP 200, production worker readback and authenticated synthetic
  E2E are PASS, but they do not replace a live authenticated screenshot.
- Android/Windows telemetry is pushed but not present in public `1.1.1`; no
  release claim is made for it until a later exact client binary is built and
  verified.
- Buying traffic/user acquisition and store publication remain
  `NOT_IN_SCOPE_OWNER`.
