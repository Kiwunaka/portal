# POKROV Product Analytics, Telegram Entry And Operator UX

Document class: `EVIDENCE`

Status: `COMPLETED`

Last updated: 2026-08-17

## Goal

Сделать выпущенный POKROV `1.1.1` измеримым и управляемым продуктом: видеть
сквозной путь пользователя и безопасные причины отказов, превратить Telegram-
бота в короткое входное окно, заменить мокапы инструкций актуальными
скриншотами, сделать adminapp быстрым рабочим инструментом и только после этого
вернуть ежедневные интернет-новости в режиме черновик → подтверждение.

Эта волна не покупает трафик, не набирает пользовательскую базу и не публикует
приложение в сторах. Эти направления владелец оставил себе.

## Owner Decisions

- First-party analytics only. Сторонние рекламные SDK и trackers запрещены.
- Аналитики должно хватать для ответа «откуда пришёл, куда дошёл, что произошло,
  сколько заняло и почему не получилось», но она не собирает посещённые сайты,
  destination traffic, содержимое туннеля, raw VPN configs, секреты, provider
  payloads или тексты приватных чатов.
- `active user` = аккаунт с подтверждённым успешным подключением за rolling 7 days.
- Raw product/error events хранятся 90 дней; агрегаты можно хранить дольше при
  сохранении удаления/анонимизации аккаунта.
- Telegram-бот — вход, загрузка, привязка, краткая помощь и статус. Полный личный
  кабинет остаётся в webapp и не дублируется ботом.
- Telegram Stars отсутствуют в текущем пользовательском UI. Исторические поля и
  payment evidence не удаляются, пока нужны для бухгалтерской совместимости.
- Автоновости сначала создают только черновики. Автопубликация требует нового
  явного решения владельца.
- Acquisition/user-base и stores: `NOT_IN_SCOPE_OWNER`.

## Baseline

- Platform: `12f23e65b709678c5eb674b29b3a2755928f0307`, `master` synced.
- Client: `b09de51411d2a49a393d80b49c608bcf7ca18959`, `main` synced.
- Public stable release: `v1.1.1`.
- Current production updater requires Android `1.1.1` for clients on `1.1.0`.
- Existing attribution, funnel, WARP and Telegram-link events are retained as
  inputs; this wave reconciles them instead of creating a parallel analytics
  universe.

## Product Questions The System Must Answer

1. Сколько людей вошло через каждый source/campaign и entry point?
2. Сколько дошло до download, first open, login/link, trial, first connect,
   returning connect, checkout, paid, renewal and support resolution?
3. Где самый большой drop-off за выбранный период и на какой версии/platform?
4. Какая ошибка произошла, на каком stage, сколько заняла, повторяемая ли она и
   затронула ли Wi-Fi/LTE, приложение, API, bot, provider или background job?
5. Почему рассылка дала `28/61`, кого безопасно повторить и кто уже получил её?
6. Насколько свежи данные dashboard и нет ли ingestion/schema drift?
7. Какие версии клиентов устарели, требуют update и где update lifecycle ломается?

## Event Envelope V1

Каждое новое или нормализованное событие использует общий bounded envelope:

- `event_name`, `schema_version`, `event_id` and idempotency key;
- `occurred_at`, `received_at`, optional `started_at`, `duration_ms`, timezone
  normalization and `clock_skew_state`;
- safe `session_id`, `installation_id`, `device_id`, `account_id` only where the
  identity is legitimately linked; anonymous identities are not guessed;
- `platform`, `app_version`, `build_number`, `surface`, `subsystem`, `stage`;
- bounded `source`, `campaign`, `entry_path` and handoff coverage;
- `result`, normalized `error_category`, `error_code`, `retryable`,
  `attempt_number`, optional bounded `retry_after_seconds`;
- `correlation_id`/`trace_id`, safe network class and lifecycle state only when
  required for diagnosis;
- bounded allowlisted metadata. Unknown fields fail closed or go to quarantine.

Late and out-of-order events remain queryable by both occurrence and receive
time. Duplicate delivery cannot inflate funnels. Paid/access truth continues to
come from signed callbacks and entitlement records, never from telemetry.

## Required Event Families

| Family | Minimum stages |
| --- | --- |
| Entry and attribution | landing/bot entry, campaign handoff issued/consumed/expired/replayed |
| Distribution | asset selected, download started/completed/failed, installer opened, install/update result |
| Identity | login/code requested/issued/claimed/expired, Telegram/email link started/completed/failed, legacy migration |
| Access | trial started, entitlement changed, expiry/recovery, checkout started, provider-confirmed paid |
| Runtime | connect requested/started/succeeded/failed/cancelled, disconnect, background restore, reboot restore |
| Routing | location/variant selection, whitelist path, DNS, WARP, per-app plan, Wi-Fi/LTE transition |
| Support | help opened, AI request/result, diagnostics consent/send, ticket create/reply/resolution |
| Messaging | campaign plan, recipient attempt, delivery result/reason, retry, downstream open/action where provable |
| Operations | job start/result/duration, schema/ingestion lag, dashboard freshness, banner/news lifecycle |

## Telegram Delivery Contract

- Freeze recipient membership at guarded intent preparation.
- Persist one safe attempt row per recipient and attempt.
- Normalize Telegram failures to `blocked`, `bot_not_started_or_chat_not_found`,
  `account_deactivated`, `rate_limited`, `transient_provider`, `internal` and
  `unknown_safe`; raw provider text is not returned to ordinary admin clients.
- Store retryability, attempt number, timestamps, retry-after and successful
  Telegram message ID.
- Failed-only retry selects only retryable failed recipients and never resends to
  an already successful recipient for the same campaign.
- Admin shows denominator, sent, terminal failures, retryable failures, retries,
  conversion and data freshness. Every mutation remains intent/audit protected.

## Telegram Product Contract

First level must present one primary next step and no cabinet-style panel.

- New/unknown: Android, Windows, already-use-POKROV linking, short help.
- Returning: state-aware primary action, access status, open/download app, help.
- Full devices/payments/referral/history/settings stay in webapp unless a single
  bot action is required to enter or recover access.
- No Stars labels, price units, checkout buttons or current-user achievements.
- Every callback has loading acknowledgement, safe error recovery and back path.

## Instructions And Atlas Contract

Accepted screenshots must be captured in the current run, inspected after save
and labelled with platform/version/state. Coverage includes installation,
permissions, login/link/code, update, connect, modes, whitelist, per-app, DNS,
WARP, Wi-Fi/LTE, tile/notifications/background, bonuses/payment, support,
diagnostics and common failure recovery. Mockups may explain concepts but cannot
replace a real screenshot for a claimed current step. Unavailable proof is
`MANUAL_OWNER_TEST` or `BLOCKED_BY_ACCESS`.

## Admin Information Architecture

| Surface | Required answer |
| --- | --- |
| Overview | new/trial/paid/active, first-connect conversion, biggest drop-off, current failures, data freshness |
| Funnel | separate acquisition and product cohorts with explicit denominators and lineage coverage |
| Users | safe identity/device/access summary and role-audited event timeline |
| Errors | category/code/stage/version/platform/network/time, impact and retryability |
| Messaging | broadcasts, banners, lifecycle and news delivery/conversion without recipient leakage |
| Clients | version adoption, required update, download/install outcomes and unsupported builds |
| Support and AI | requests, response/error/escalation/resolution without exposing private chat text by default |
| Network | node/runtime/DNS/WARP/whitelist/per-app health with exact freshness/origin labels |
| Content jobs | source fetch, dedupe, draft, approval, publish and failure state |

All lists use bounded queries, pagination or virtualization, indexes, explicit
timezone/freshness, useful empty/loading/error/stale states, RBAC, redaction and
guarded mutations. Visual audit covers responsive layout, keyboard/focus,
labels, contrast and touch targets. Performance evidence includes API query and
visible page-load timings for key screens.

## Queue

| Work order | Outcome | Depends on | Status |
| --- | --- | --- | --- |
| WO-001 | Fresh visual/product audit and current-state inventory | — | `COMPLETED` |
| WO-002 | Event/error schema, storage, ingestion, retention and client/server wiring | WO-001 | `COMPLETED` |
| WO-003 | Per-recipient Telegram delivery analytics and failed-only retry | WO-002 | `COMPLETED` |
| WO-004 | Compact Telegram entry, no visible Stars/cabinet duplication | WO-001 | `COMPLETED` |
| WO-005 | Real screenshot atlas and broad problem/FAQ coverage | WO-001, WO-004 | `COMPLETED` |
| WO-006 | Fast, useful admin analytics and performance/accessibility proof | WO-002, WO-003 | `COMPLETED_WITH_PROD_AUTH_LIMIT` |
| WO-007 | Daily internet-news draft and approval pipeline | WO-002, WO-006 | `COMPLETED` |
| WO-008 | Gates, production proof, commit/push/deploy and closure | WO-002..WO-007 | `COMPLETED` |

## Acceptance Oracle

The wave closes only when:

1. A fresh screenshot-backed audit lists every checked step and its health.
2. The defined journey is measurable without inferred identity or vanity sums.
3. Error rows expose safe stage/time/duration/retry/version/correlation data.
4. A `28/61`-style broadcast has a safe reason breakdown and failed-only retry
   that cannot duplicate successful recipients.
5. Production bot is compact, buttons and error/back states are proven, and no
   current UI exposes Stars or duplicates the cabinet.
6. Instructions use inspected real screenshots for all available important paths.
7. Admin key pages meet bounded query and page-load budgets, show freshness and
   answer the product questions above.
8. News jobs generate deduplicated Russian drafts with source provenance and
   require manual approval.
9. Canonical docs/tests and exact source/runtime evidence agree; manual/blocked
   checks are never relabelled PASS.

## Non-Goals

- Buying ads, choosing campaigns or growing the user base.
- Store accounts, store listings, ASO or store publication.
- Capturing VPN destination data or introducing third-party analytics SDKs.
- Deleting historical Stars/accounting data merely to simplify naming.
- Autonomous news publication.
- A broad client redesign unrelated to an observed audited failure.

## Promotion Boundaries

- Platform changes promote through `master`; client changes through `main`.
- Read-only visual discovery precedes UI mutation.
- No broadcast, payment, account mutation or news publication occurs during audit.
- A new client binary is cut only if shipped client code changes.
- Every deploy names exact commit and origin; current-origin, brain-origin and
  RU-origin remain distinct.

## Current State And Next Action

The wave is complete. Platform code through `09b228e` is deployed; `master`
contains the final evidence record. Client telemetry is pushed to `main` at
`6575c22` and intentionally waits for the next client binary because no honest
physical-device release proof was available in this wave. Public stable remains
`1.1.1`.

Production readback proves the compact Telegram `/start` and Help/Back flow,
healthy platform services and current public surfaces. Draft-only news is enabled
once per day and the latest production run completed with two pending drafts;
automatic publication remains disabled. The authenticated admin visual readback
remains `BLOCKED_BY_ACCESS` because the browser session expired, while the public
admin shell, affected API contracts and authenticated synthetic E2E are green.
Acquisition/user-base and stores remain owner-owned and were not changed.
