# Repo Feature Story Audit

Last updated: 2026-06-27

## Status

- Wave status: `active`
- Objective: create one canonical source-code-derived table of POKROV user stories, expected behavior, test status, defects, fixes, and retest state; then test each story, fix logic/copy/UX issues, and retest.
- Canonical tracker: [pokrov-canonical-feature-tracker.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-canonical-feature-tracker.md)
- Main table: [pokrov-canonical-feature-tracker.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-canonical-feature-tracker.csv)
- Entrypoint inventory: [pokrov-entrypoint-inventory.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-entrypoint-inventory.csv)
- Completion audit: [COMPLETION-AUDIT.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/work-orders/2026-06-27--repo-feature-story-audit/COMPLETION-AUDIT.md)
- Completion audit ledger: [COMPLETION-AUDIT.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/work-orders/2026-06-27--repo-feature-story-audit/COMPLETION-AUDIT.csv)

## Work Orders

| WO | Status | Scope | Notes |
| --- | --- | --- | --- |
| [WO-001-canonical-feature-tracker.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/work-orders/2026-06-27--repo-feature-story-audit/WO-001-canonical-feature-tracker.md) | `executing` | platform docs, source-derived inventory, imported existing story trackers | Canonical CSV/Markdown, entrypoint coverage, symbol coverage, script manifest status guard, tracker hygiene guards, and completion audit are current; no local story/entrypoint/script evidence gaps, generic public-symbol review rows, or client package public-API review rows remain. |

## Current Imported Coverage

| Source | Rows |
| --- | ---: |
| Telegram bots tracker | 57 |
| WebApp/admin tracker | 58 |
| Marketing tracker | 55 |
| POKROV-app client tracker | 67 |
| Backend API route rows | 165 |
| Active script/operator workflow rows | 123 |

## Next Queue

1. Run the full root pytest suite again when the next broad code/doc batch is ready.
2. Keep active script/operator workflow rows mapped to direct tests when new CLI tools are added.
3. Continue into remaining user-story behavior sweeps and owner/device/provider/RU-origin scenarios; do not convert local tests into live-readiness claims.
4. Add defects for any new mismatch, then fix and retest.
5. Keep [COMPLETION-AUDIT.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/work-orders/2026-06-27--repo-feature-story-audit/COMPLETION-AUDIT.md) and [COMPLETION-AUDIT.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/work-orders/2026-06-27--repo-feature-story-audit/COMPLETION-AUDIT.csv) synchronized before any completion claim.
