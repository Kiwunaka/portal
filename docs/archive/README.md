# Historical Notes And Archive

Last updated: 2026-07-21

## Purpose

This directory and the surrounding historical materials exist to preserve context without competing with current source-of-truth docs.

## What Is Historical

The following materials are useful for investigation, migration context, and forensic history, but are not living operating instructions:

- dated architecture snapshots
- audits
- postmortems
- old rollout notes
- older flat docs in `docs/archive/flat-docs/`
- root guides moved into `docs/archive/root-guides/`
- completed planning packets in `docs/archive/plans/`
- completed design plans and boards in `docs/archive/design-plans/`
- old Superpowers execution plans in `docs/archive/superpowers-plans/`
- dated competitor and censorship research in `docs/archive/competitive/`

## Root Guide Archive

Archived root-level guides currently stored here:

- [ADMIN_GUIDE_2026-02-20.md](C:/Users/kiwun/Documents/ai/VPN/docs/archive/root-guides/ADMIN_GUIDE_2026-02-20.md)
- [USER_GUIDE_RU_2026-02-15.md](C:/Users/kiwun/Documents/ai/VPN/docs/archive/root-guides/USER_GUIDE_RU_2026-02-15.md)
- [cleanup-report-2026-03-04.md](C:/Users/kiwun/Documents/ai/VPN/docs/archive/root-guides/cleanup-report-2026-03-04.md)

## Planning Archives

- [Archived Planning Packets](C:/Users/kiwun/Documents/ai/VPN/docs/archive/plans/README.md)
- [Archived Design Plans](C:/Users/kiwun/Documents/ai/VPN/docs/archive/design-plans/README.md)
- [Archived Superpowers Plans](C:/Users/kiwun/Documents/ai/VPN/docs/archive/superpowers-plans/README.md)
- [Archived Competitor Research](C:/Users/kiwun/Documents/ai/VPN/docs/archive/competitive/telegram-vpn-2026-07-12/README.md)

## How To Use Older Docs

Use this retrieval order:

1. Start with the current [documentation registry](../README.md) and its
   canonical domain owners.
2. Use `rg` and `rg --files` to locate exact terms and paths.
3. Use targeted Git log, search, and blame queries when current files do not
   explain the provenance.
4. Read only the relevant archive, work-order, audit, or spec history.
5. Let archive material explain why a decision was made, but never let it
   decide the current action when a canonical owner exists.

No index, dependency, database, service, MCP, GraphRAG, or embeddings layer is
part of the current historical-retrieval architecture.

A separate future benchmark may evaluate a local generated and ignored SQLite
FTS/BM25 index with repository, subsystem, class, date, `superseded_by`,
work-order, and release metadata. Embeddings may be evaluated only after a
fixed historical-query benchmark proves material misses in lexical search.
This task neither creates nor authorizes that benchmark or any index; either
requires a separate owner-approved plan.
