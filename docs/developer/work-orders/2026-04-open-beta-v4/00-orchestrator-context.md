# Orchestrator Context

Status: in progress
Date: 2026-04-26

## Source Of Truth

- Platform repo policy line: `portal/master`, implemented in this worktree on `codex/open-beta-v4`.
- Active client repo policy line: `POKROV-app/main`, implemented in the client worktree on `codex/open-beta-v4`.
- Canonical platform docs: `docs/product`, `docs/architecture`, `docs/operations`, `docs/developer`, `docs/user`.
- Canonical client docs: `C:/Users/kiwun/.config/superpowers/worktrees/POKROV-app/open-beta-v4/docs`.
- Shared product facts: `shared/product-facts.json`, `shared/public-urls.json`, `shared/design-tokens.json`, `shared/copy.ts`, and `copy/catalog.ru.json`.

## Release Stance

The default public target is `0.10.0-open-beta.N`.

`1.0.0` is blocked until every P0 gate has direct, redacted evidence:

- active payment provider proof;
- signed webhook and replay/auth rejection proof;
- runtime app-download smoke with live `TELEGRAM_INIT_DATA`;
- RU-origin POKROV host evidence and Telegram limitation handling;
- Android physical-device release-build localhost/control-surface audit;
- signed or clearly gated Android/Windows artifacts;
- security, privacy, performance, support, docs, and rollback evidence.

## Known External Blockers

| Gate | Current label | Missing dependency |
| --- | --- | --- |
| Lava.top live provider proof | blocked by missing access | merchant/API credentials and provider dashboard state |
| Telegram runtime download smoke | blocked by missing access | live `TELEGRAM_INIT_DATA` supplied only through environment |
| RU-origin check | blocked by missing access | healthy external RU probe host or current `mini` access |
| Android physical audit | blocked by missing access | physical device serial in `ANDROID_AUDIT_SERIAL` |
| Production signing | blocked by missing access | Android and Windows signing material |

## Orchestration Rules

- Research agents may only write their assigned `research/Rxx-*.md` file.
- Implementation work orders have file locks in `12-file-locks.md`.
- No secrets in markdown, logs, screenshots, prompts, commits, or evidence.
- All findings must use one evidence label: `confirmed`, `probable`, `unknown`, `needs local run`, `blocked by missing access`, or `deferred`.
- Do not claim public Android or `1.0.0` while any P0 gate is blocked.
