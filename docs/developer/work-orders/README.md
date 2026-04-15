# POKROV Work Orders

Last updated: 2026-04-15

## Document Status

This directory is the living execution area for orchestration waves and work orders.

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

- keep only living execution artifacts here
- keep one `INDEX.md` per wave
- keep one bounded outcome per `WO`
- do not replace canonical product or architecture docs with work-order notes
- link to evidence under `docs/audit-artifacts/` rather than copying raw logs into the WO

## Continuity Rule

A new orchestrator should be able to resume from the wave folder alone:

- understand the queue from `INDEX.md`
- understand each WO from its contract and evidence
- see what was verified
- see what is still partial or blocked

## Historical Material

Older flat orchestration and release logs under `docs/archive/flat-docs/` remain historical or supporting material unless canonical docs relink them as current.
