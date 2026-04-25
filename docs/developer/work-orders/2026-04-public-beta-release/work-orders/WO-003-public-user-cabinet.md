# WO-003 Public User Cabinet

Status: draft
Agent: W03
Lane: platform
Priority: P0

## Goal

Make the user cabinet a real continuation surface for public beta: status, downloads, redeem, subscription, devices, statistics, and support must show actual or explicitly unavailable states.

## Write Scope

- `webapp/src/app/(dashboard)/**`
- `webapp/src/components/cabinet/**`
- `webapp/src/components/cabinet-*.tsx`
- `webapp/src/lib/api.ts`
- `webapp/e2e/**`
- `webapp/README.md`
- `docs/developer/work-orders/2026-04-public-beta-release/**`

## Acceptance

- Cabinet is not a second landing page.
- Downloads are truthful and beta-labeled.
- Raw subscription secrets are hidden from normal UI.
- Support ticket flow is real, not decorative.
- Payment/redeem continuation has honest next steps.

## Validation

```powershell
cd webapp
npm.cmd run build
npm.cmd run test:e2e
```

