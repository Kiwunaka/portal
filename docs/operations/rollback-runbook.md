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
2. For runtime downloads, switch the active pointer to the last verified release handoff, or disable the public route while preserving versioned metadata and artifacts.
3. Rebuild and redeploy marketing/webapp only after copy reflects the blocked state.
4. Keep existing paid access state intact unless a documented reconciliation task says otherwise.
5. Prepare a short support notice if users are already affected. Publish it only through an explicitly authorized owner/operator.
6. Follow the full [Paid Beta Deploy And Rollback Checklist](deployment-and-access.md#paid-beta-deploy-and-rollback-checklist) for retained evidence, rollback sources, and post-rollback verification.
