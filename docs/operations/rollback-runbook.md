# Rollback Runbook

Last updated: 2026-08-22

## Rollback Triggers

- provider callbacks mutate access incorrectly;
- runtime downloads point to wrong or unavailable artifacts;
- Android audit fails after publication;
- support or cabinet exposes sensitive evidence;
- deployment breaks app-first session flow.

## Rollback Actions

1. Disable public checkout or provider availability.
2. For runtime downloads, switch the active pointer to the last verified release handoff, or disable the public route while preserving versioned metadata and artifacts.
3. Rebuild and redeploy marketing/webapp only after copy reflects the blocked state.
4. Keep existing paid access state intact unless a documented reconciliation task says otherwise.
5. Prepare a short support notice if users are already affected. Publish it only through an explicitly authorized owner/operator.
6. Follow the full [Paid Beta Deploy And Rollback Checklist](deployment-and-access.md#paid-beta-deploy-and-rollback-checklist) for retained evidence, rollback sources, and post-rollback verification.

## Client Stable Pointer Rollback

The client repository owns the executable pointer contract:

- catalog: `C:/Users/kiwun/Documents/ai/POKROV-app/config/release-rollback-catalog.seed.json`
- stable pointer: `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/release-handoff.json`
- switcher: `C:/Users/kiwun/Documents/ai/POKROV-app/scripts/set-release-stable-pointer.ps1`

Versioned handoffs are immutable rollback targets. Before promotion, the
catalog must contain both the exact candidate and the retained prior stable
handoff with matching identity and SHA-256. Validate and dry-run first:

```powershell
pwsh C:/Users/kiwun/Documents/ai/POKROV-app/scripts/set-release-stable-pointer.ps1 `
  -CatalogPath C:/Users/kiwun/Documents/ai/POKROV-app/config/release-rollback-catalog.seed.json `
  -ValidateOnly

pwsh C:/Users/kiwun/Documents/ai/POKROV-app/scripts/set-release-stable-pointer.ps1 `
  -CatalogPath C:/Users/kiwun/Documents/ai/POKROV-app/config/release-rollback-catalog.seed.json `
  -ExpectedCurrentReleaseId <current-release-id> `
  -TargetReleaseId <rollback-release-id>
```

An authorized apply additionally requires `-Apply`, a new `-BackupPath`, and a
new `-ReceiptPath`. The external backup and receipt must be outside
`artifacts/releases`;
the backup must share the pointer filesystem. The expected current release is
the optimistic lock. The switch fails closed on a stale current ID,
missing/unlisted target, digest mismatch, overwrite attempt, or failed
readback. After the pointer switch, apply the same versioned handoff
to runtime config, rebuild static download surfaces if URLs changed, and retain
separate `current-origin`, `brain-origin`, and `RU-origin` results where each is
claimed.

The current source contract and isolated A→B→A fixture are `PASS_LOCAL`. The
exact `1.2.0` candidate does not exist yet, pointer/runtime mutation is
`NOT_AUTHORIZED`, and its rollback drill remains `NOT_RUN`.

## Canonical Support Ownership Rollback

- A code rollback may ignore `support_tickets.account_id`, `support_attachments.owner_account_id`, their indexes, `migration.support_account_ownership.v1`, and support ownership review rows. Retain all of them as additive evidence.
- Do not drop the additive support columns or indexes, delete the marker/reviews, clear assigned owners, or rewrite legacy Telegram fields during routine rollback. SQLite column removal requires a destructive table rebuild and is not a routine rollback action.
- Retain ticket/message/upload rows and files exactly as recorded. Account merge is not reversed by moving support rows back to a superseded account.
- Before any deployment, `MANUAL_OWNER_TEST` must cover real backup/restore rehearsal, production PostgreSQL DDL/index lock impact, concurrent account merge versus support writes, and redacted before/after ownership counts and review evidence. These checks are not satisfied by local SQLite or unit tests.

## Private Attachment Binding Rollback

- Code rollback may stop issuing/accepting `attachment_id`, but must retain the
  additive nullable `support_attachments.ticket_id`, unique `message_id`,
  `attached_at`, `expires_at`, and their indexes. Do not drop them or rebuild
  SQLite tables during routine rollback.
- Keep rolling acceptance of exact old private triplets until every deployed
  WebApp/client candidate is known to use `attachment_id`. Preserve non-private
  Telegram/client media compatibility.
- Never restore public `/uploads/support/*` serving. Roll back the WebApp to a
  version that still performs authenticated private downloads, or disable the
  attachment UI while ticket text remains available.
- Retain staged and bound files/rows. An emergency cleanup may target only rows
  that are unbound and have an explicit expired `expires_at`; legacy null-expiry
  and bound rows are rollback evidence, not disposable cache.
- After atomic upload rename, persistence and commit-acknowledgement failures
  intentionally retain the final file. Do not remove it from an error handler or
  rollback script: the row may have committed. Let the reconciler verify a
  rowless final and enforce the safety grace before unlink.
- The supervised cleanup defaults are interval `900`, safety grace `3600`, batch
  `100`, and selected-file/DB-row processing limit `500`. A rollback that removes or pauses this
  worker must retain the upload directory and all rows; review integer-only
  orphan/missing counters before re-enabling. Never compensate with a broad
  filesystem delete.
- Cleanup cursors and their frozen filesystem-mtime/DB-max-ID cycle boundaries
  are process-local and reset on restart. After rollback or worker restart,
  allow uninterrupted runs through a complete observed wrap before treating
  later-window zero counts as useful. File processing and selection memory are
  limited, but every run enumerates the whole upload directory once; measure
  production large-directory latency before relying on the configured cadence.
- Before promotion, retain `MANUAL_OWNER_TEST` for production PostgreSQL DDL and
  index-lock impact; backup/restore with redacted bound/unbound/dangling counts;
  real PostgreSQL create/reply/retry concurrency; cookie, bearer, and Telegram
  initData downloads through the reverse proxy; and sampled old-history plus
  missing-file behavior. Local passes do not satisfy these gates.
- Production worker operation and cadence are a `MANUAL_OWNER_TEST`; local job
  wiring and reconciler tests do not prove live scheduling.
- PostgreSQL commit-ack loss and POSIX power-loss durability are a
  `MANUAL_OWNER_TEST`: verify file and parent-directory fsync behavior, durable
  row-plus-file preservation after lost acknowledgement, and grace-delayed
  cleanup of a confirmed rowless final.
