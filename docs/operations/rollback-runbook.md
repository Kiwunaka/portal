# Rollback Runbook

Last updated: 2026-07-14

## Rollback Triggers

- provider callbacks mutate access incorrectly;
- runtime downloads point to wrong or unavailable artifacts;
- Android audit fails after publication;
- support or cabinet exposes sensitive evidence;
- deployment breaks app-first session flow.

## Rollback Actions

1. Disable public checkout or provider availability.
2. Remove or blank public download URLs in runtime handoff.
3. Rebuild and redeploy marketing/webapp only after copy reflects the blocked state.
4. Keep existing paid access state intact unless a documented reconciliation task says otherwise.
5. Publish a short support update if users are already affected.

## Canonical Support Ownership Rollback

- A code rollback may ignore `support_tickets.account_id`, `support_attachments.owner_account_id`, their indexes, `migration.support_account_ownership.v1`, and support ownership review rows. Retain all of them as additive evidence.
- Do not drop the additive support columns or indexes, delete the marker/reviews, clear assigned owners, or rewrite legacy Telegram fields during routine rollback. SQLite column removal requires a destructive table rebuild and is not a routine rollback action.
- Retain ticket/message/upload rows and files exactly as recorded. Account merge is not reversed by moving support rows back to a superseded account.
- Before any deployment, `MANUAL_OWNER_TEST` must cover real backup/restore rehearsal, production PostgreSQL DDL/index lock impact, concurrent account merge versus support writes, and redacted before/after ownership counts and review evidence. These checks are not satisfied by local SQLite or unit tests.
