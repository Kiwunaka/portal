# POKROV Open Questions Ledger

Last updated: 2026-06-28

## Purpose

This ledger records questions that remain unclear during the repo feature-story
audit. It turns the owner-question list into a diffable artifact so unresolved
policy or access decisions do not disappear inside prose.

Canonical CSV:
[pokrov-open-questions.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-open-questions.csv)

Owner answer sheet:
[pokrov-owner-answer-sheet.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-owner-answer-sheet.md)

Coverage policy decision guide:
[pokrov-coverage-policy-decision-guide.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-coverage-policy-decision-guide.md)

## Current Counts

| Metric | Count |
| --- | ---: |
| Open questions | 3 |
| Blocking full goal completion | 1 |
| Non-blocking procedural questions | 2 |
| Answered questions | 1 |

## Blocking Questions

| ID | Blocks | Why |
| --- | --- | --- |
| `Q-004` | `yes` | The owner/operator must execute, explicitly defer, block, or attest the remaining Telegram WebApp/session and live deployed app-session checks using `pokrov-owner-gated-execution-guide.md`; Telegram WebApp execution is `BLOCKED_BY_ACCESS` because this session has no callable desktop-control tool, and current-origin public hosts/API health, brain deploy-state, and brain-origin signed `/api/client/apps` still do not become real-user/current-origin authenticated PASS evidence. |

## Answered Questions

| ID | Answer | Effect |
| --- | --- | --- |
| `Q-001` | `ACCEPT_STORY_AND_SYMBOL_TIERS` accepted by owner on 2026-06-28. | Source-level helper inventory and coverage tiers plus user-story tests are sufficient for this audit; Q-001 no longer blocks goal completion. |

## Non-Blocking Questions

| ID | Blocks | Default |
| --- | --- | --- |
| `Q-002` | `no` | CSV/Markdown remain canonical status artifacts; XLSX files are retained source audit artifacts. |
| `Q-003` | `no` | Do not use sub-agents unless the owner explicitly approves that execution model. |

## Completion Rule

The full active goal is not complete while any row with
`blocks_goal_completion=yes` remains `open`, unless the owner answers the
question or explicitly accepts the default assumption as final.

Use `pokrov-owner-answer-sheet.md` for the compact answer codes and gate IDs.
