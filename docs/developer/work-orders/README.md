# POKROV Work Orders

Last updated: 2026-05-07

## Document Status

This directory is the living execution area for active orchestration waves and the retained evidence archive for completed or superseded waves.

## Purpose

Use this area to store active and resumable execution artifacts that should survive chat boundaries.

Templates do not live here.

Templates live under:

- [docs/developer/orchestration/templates/](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/templates)

## Naming

Wave folders should use this format:

- `YYYY-MM-DD--wave-name`

Inside each wave folder:

- `INDEX.md`
- `WO-001-short-title.md`
- `WO-002-short-title.md`

## Storage Rules

- keep only living execution artifacts or intentionally retained historical evidence here
- keep one `INDEX.md` per wave
- keep one bounded outcome per `WO`
- do not replace canonical product, architecture, operations, or active client docs with work-order notes
- active client workflow truth lives in `C:/Users/kiwun/Documents/ai/POKROV-app/docs/`
- use `docs/archive/client-lanes/*` only as historical bootstrap or rollback evidence when a wave needs that provenance
- link to evidence under `docs/audit-artifacts/` rather than copying raw logs into the WO
- rendered journeys, mockups, and visual audit outputs are retained evidence/reference; they are not current UI authority unless `DESIGN.md` or `docs/design/**` says so
- old wave folders should be indexed or marked historical instead of deleted during routine cleanup

## Continuity Rule

A new orchestrator should be able to resume from the wave folder alone:

- understand the queue from `INDEX.md`
- understand each WO from its contract and evidence
- see what was verified
- see what is still partial or blocked

If a wave touches the platform lane, the active `POKROV-app` lane, and/or the bridge release lane, keep that evidence separated inside the relevant `WO` files instead of collapsing them into one generic client result.

## Historical Material

Older flat orchestration and release logs under `docs/archive/flat-docs/` remain historical or supporting material unless canonical docs relink them as current.
