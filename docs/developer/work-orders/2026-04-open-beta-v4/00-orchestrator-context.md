# Orchestrator Context

Status: superseded by 2026-05-15 beta decision
Date: 2026-05-26

## Supersession Note

This file preserves the original 2026-04-26 orchestration context. Current release truth is:

- outside-store public Android + Windows beta is `GO` from the 2026-05-15 evidence pack;
- `1.0.0`, app-store release, trusted Windows signing, raw Android physical-audit proof, RU-origin readiness, and production payment maturity remain separate follow-up gates;
- owner hardware, real-user Telegram/WebApp, payment dashboard, live deploy approval, signing, store access, and RU-origin checks are labeled `MANUAL_OWNER_TEST`, `SKIPPED_BY_OWNER`, `OPERATOR_ATTESTED`, `NOT_REQUESTED`, or `BLOCKED_BY_ACCESS` for agent work.

## Source Of Truth

- Platform repo policy line: `portal/master`, implemented in this worktree on `codex/open-beta-v4`.
- Active client repo policy line: `POKROV-app/main`, implemented in the client worktree on `codex/open-beta-v4`.
- Canonical platform docs: `docs/product`, `docs/architecture`, `docs/operations`, `docs/developer`, `docs/user`.
- Canonical client docs: `C:/Users/kiwun/.config/superpowers/worktrees/POKROV-app/open-beta-v4/docs`.
- Shared product facts: `shared/product-facts.json`, `shared/public-urls.json`, `shared/design-tokens.json`, `shared/copy.ts`, and `copy/catalog.ru.json`.

## Release Stance

The default public target is the `0.x.x-beta` outside-store beta line.

`1.0.0` is blocked until every P0 gate has direct, redacted evidence:

- active payment provider proof;
- signed webhook and replay/auth rejection proof;
- runtime app-download smoke with live `TELEGRAM_INIT_DATA`;
- RU-origin POKROV host evidence and Telegram limitation handling;
- Android physical-device release-build localhost/control-surface audit;
- signed or clearly gated Android/Windows artifacts;
- security, privacy, performance, support, docs, and rollback evidence.

## Current Manual / External Follow-Ups

| Gate | Current label | Missing dependency |
| --- | --- | --- |
| Lava.top live provider proof | `PASS_FOR_BETA` / production follow-up | refund, chargeback, and reconciliation evidence before stronger payment claims |
| Telegram runtime download smoke | `PASS` with brain-signed synthetic init data / `MANUAL_OWNER_TEST` for real user | real user opening Telegram WebApp |
| RU-origin check | `SKIPPED_BY_OPERATOR` | healthy external RU probe host or current `mini` access before RU-origin claim |
| Android physical audit | `OPERATOR_ATTESTED` / `MANUAL_OWNER_TEST` for raw proof | retained raw device audit evidence before stronger Android claim |
| Production signing | `NOT_REQUESTED` for beta | Android and Windows signing material before store/trusted claims |

## Orchestration Rules

- Research agents may only write their assigned `research/Rxx-*.md` file.
- Implementation work orders have file locks in `12-file-locks.md`.
- No secrets in markdown, logs, screenshots, prompts, commits, or evidence.
- All findings must use one evidence label: `confirmed`, `probable`, `unknown`, `needs local run`, `blocked by missing access`, or `deferred`.
- Do not claim `1.0.0`, store availability, trusted Windows signing, raw Android physical-audit proof, or RU-origin readiness while those separate gates are not proven.
