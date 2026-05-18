# POKROV Orchestration Docs

Last updated: 2026-05-16

## Document Status

This directory is the living source of truth for repo-native orchestration, work-order, and review-loop standards in the `POKROV` workspace.

## Purpose

Use this directory when a task needs more than one execution pass, more than one role, or more than one repository lane.

This standard exists to keep multi-step work reliable in a workspace that now has:

- one canonical platform lane `portal/master`
- one canonical active client-development lane `POKROV-app/main`
- one explicit bridge release-truth lane at `external/client-fork/app/` when release or hotfix evidence requires it
- historical `app-next/` bootstrap material that may still be read as archive evidence but must not be treated as an active landing lane
- mandatory docs-update rules
- release-sensitive manual checks
- evidence requirements that outlive a single chat

Historical boundary:

- orchestration files define process, not product behavior
- completed wave folders, old specs, rendered visual audits, and mockup/reference assets are retained evidence until a deliberate archival task compresses them
- current product decisions must be copied back into canonical docs before they are treated as source of truth

## Directory Map

- [orchestration-standard.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/orchestration-standard.md)
  canonical process and lifecycle rules
- [wo-authoring-guide.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/wo-authoring-guide.md)
  work-order ceremony levels, proof blocks, evidence tiers, reviewability, and validation attribution
- [flow-state.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/flow-state.md)
  compact fix-cycle state, reviewer recheck semantics, and stop rules
- [roles/](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/roles)
  paste-ready role contracts for orchestrator, executor, and reviewers
- [templates/](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/templates)
  templates for wave indexes, work orders, discovery, strategy, review, and completion evidence
- [work-orders README](C:/Users/kiwun/Documents/ai/VPN/docs/developer/work-orders/README.md)
  naming and storage rules for live wave and WO artifacts

## How To Use

1. Start from [orchestration-standard.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/orchestration-standard.md).
2. Use [wo-authoring-guide.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/wo-authoring-guide.md) when drafting or reviewing a `WO` contract.
3. Use [flow-state.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/flow-state.md) once a `WO` enters review or fix-cycle.
4. Use [roles/orchestrator.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/roles/orchestrator.md) to launch or resume an orchestration session.
5. Create or update a wave folder under [docs/developer/work-orders/](C:/Users/kiwun/Documents/ai/VPN/docs/developer/work-orders/README.md).
6. Route active client work to `POKROV-app/main` by default, and call out any bridge-lane work as explicit release-truth or hotfix evidence.
7. Drive each `WO` through the required review loop before closure.

## Scope Rule

These files define the orchestration process.

They do not replace the canonical product, architecture, operations, or client docs. Every work order must still route back to the correct source-of-truth documents for the behavior being changed, and historical `app-next/` notes remain reference material only.
