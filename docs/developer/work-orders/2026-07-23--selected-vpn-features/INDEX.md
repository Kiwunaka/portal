# Selected VPN Features Execution Index

Last updated: 2026-07-23

Status: `LOCAL_QA_PASS`

Production `/guides/`: `BLOCKED_BY_DEPLOY`

## Goal

Довести выбранные владельцем конкурентные функции до единого, честного и проверяемого опыта в приложении, личном кабинете и на публичном сайте. Не плодить декоративные заглушки: пользовательская кнопка появляется только вместе с реальным контрактом, состояниями ошибки и тестом.

## Repository Lanes

| Lane | Base | Branch | Worktree | Owns |
| --- | --- | --- | --- | --- |
| Platform | `master@95febec` | `codex/selected-vpn-features-ios-ui` | `C:/Users/kiwun/Documents/ai/VPN/.worktrees/selected-vpn-features-ios-ui` | API, ЛК, сайт, shared facts, operator flows, platform docs/tests |
| Active client | `main@60a6ca4` | `codex/selected-vpn-features-ios-ui` | `C:/Users/kiwun/Documents/ai/POKROV-app/.worktrees/selected-vpn-features-ios-ui` | Android/Windows shell, runtime UI, client docs/tests |

Оба исходных worktree были чистыми при создании. Чужие dirty worktree и `artifacts/releases/**` не входят в write scope.

## Locked Product Decisions

- Визуальная система: текущий `pokrov-clear` — спокойный плоский iOS-like UI, grouped sections, тонкие разделители, emerald accent, без glow/neon/casino.
- Одинаковые понятия и тексты во всех трёх поверхностях; runtime-кнопки остаются только в приложении, а ЛК и сайт объясняют состояние/маршрут/восстановление.
- `NO-01` не реализуется как оплата за 5★ или положительный отзыв. Безопасный эквивалент: вознаграждение за приватное исследование, интервью или качественный подтверждённый баг-репорт; просьба оценить приложение остаётся без вознаграждения и без требования высокой оценки.
- Owner-approved `NO-05`: собственный Apple Account нужного региона остаётся основным путём. Публичный справочник разделяет живую выдачу временного US App Store-аккаунта у конкурента VanyaVPN, другие бесплатные общие источники, платную помощь с установкой, каталоги приложений и отдельные региональные аккаунты. Бесплатная раздача AppStops `/accounts/` на 2026-07-23 неактивна и показывается только как монитор, а не доступный источник. Реквизиты не копируются в репозиторий, кэш или статические страницы; внешние логины и покупки не проверялись. Общий аккаунт используется только через профиль приложения App Store, не через системные настройки Apple Account/iCloud, без платёжных данных и покупок, с выходом сразу после установки. Полная матрица и границы доказательств: [APPLE-ACCOUNT-SOURCES-2026-07-23.md](APPLE-ACCOUNT-SOURCES-2026-07-23.md).
- `NO-09` не превращается в ложное «ничего не собираем». Эквивалент: узкая формулировка «не храним историю посещённых сайтов», плюс таблица полей, целей, retention и удаления.
- MUST-09 выдаёт компенсацию только по подтверждённому incident authority, затронутому account/window и идемпотентному ledger grant. Жалоба пользователя сама по себе не создаёт деньги/дни.
- Колесо остаётся спокойной loyalty-механикой. Джекпот — `30 дней`; скидки ограниченные, одноразовые и не складываются. Экономика закрывается отдельными тестами до включения feature flag.

## Selected Scope And Routing

### MUST

| ID | Outcome | Surfaces | Baseline | Wave |
| --- | --- | --- | --- | --- |
| MUST-01 | Проверяемый connection status: tunnel, DNS, internet/HTTPS, route ownership | app, LK explanation | Runtime already exposes host/DNS/uplink/route counts; UI shows only a short status | W1 |
| MUST-02 | One-button staged repair | app, LK guide | Connect path can initialize, refresh profile, stage and reconnect; no single repair action | W1 |
| MUST-03 | Offline/cached shell | app | Last inbox/catalog survives only in memory; no explicit offline state contract | W1 |
| MUST-04 | Purpose routes: Video, AI, Social, Games, RU-direct, bypass | app, LK, site | RU-direct and selected apps exist; Android has a few static direct presets | W2 |
| MUST-05 | Route decision explanation | app, LK guide | Mode summaries exist; per-app/domain reason is absent | W2 |
| MUST-06 | Favorites and recent locations | app | Preferred node exists; favorites/recent lists do not | W1 |
| MUST-07 | Honest ping/load/health with freshness | app, LK status | API already returns health, latency and load; client hides most values and no freshness is returned | W1 |
| MUST-08 | Incident/release/action inbox | app, LK | Client notifications API/UI exists but currently mostly shows access state | W1/W3 |
| MUST-09 | Automatic incident compensation | API, LK, app inbox | Ledger and manual grants exist; no incident authority/eligibility pipeline | W3 |
| MUST-10 | Responsibility map | site, LK, app legal | Roles are spread across documents | W3 |
| MUST-11 | Field-level privacy table | site, LK, app legal | No complete user-facing inventory | W3 |
| MUST-12 | Pre-auth support and status | site, app first launch | Public help fragments exist; no unified pre-auth hub | W3 |
| MUST-13 | Official fallback-client matrix | site, LK, app recovery | Compatibility guide exists but is not a live versioned matrix | W3 |
| MUST-14 | Human route taxonomy | app, LK, site | Route modes exist; bypass/white-list/multihop taxonomy is incomplete | W2 |
| MUST-15 | ABI/host release smoke | CI/scripts, Android/Windows evidence | Existing release gates are partial; exact-candidate matrix stays required | W4 |

### SHOULD selected by owner

| IDs | Outcome | Surfaces | Wave |
| --- | --- | --- | --- |
| SHOULD-01, SHOULD-02 | Per-domain direct/VPN overrides and validated domain/IP/subnet rules | app, API, LK guide | W2 |
| SHOULD-03 | DNS presets/custom DNS plus Android LDPlayer tests | app, runtime, QA | W2 |
| SHOULD-04, SHOULD-05 | Kill Switch/Always-on guide and trusted Wi-Fi automation | app, guides | W2 |
| SHOULD-06, SHOULD-07 | QR/code device pairing and Android TV continuation | app, LK, site | W3 |
| SHOULD-09 | Referral center with status/history/conversion | app, LK | W3 |
| SHOULD-10 | Partner/affiliate cabinet foundation, intentionally disabled for later | API, LK | W5 foundation only |
| SHOULD-11, SHOULD-12 | Gifts/team packs and first-party campaign attribution | API, LK, site | W3 |
| SHOULD-13, SHOULD-14 | Competitor-switch offer and rewarded research | site, LK, admin | W3 |
| SHOULD-16, SHOULD-17 | Protection history and user-owned post-connect shortcuts | app | W1 |
| SHOULD-18, SHOULD-19 | LAN toggle and Android Quick Settings/Windows tray connect | app/hosts | W2 |
| SHOULD-20 | Idempotent config/profile refresh | app, API | W1 |

### CAN selected by owner

| ID | Decision | Wave |
| --- | --- | --- |
| CAN-01 | Add small renewal discounts to the wheel; keep 30-day jackpot and ledger-backed odds | W5 |
| CAN-02 | Activity calendar/streak, only from authoritative backend state | W5 |
| CAN-03 | Achievements for useful product actions | W5 |
| CAN-04 | Quests: first tunnel, second device, routing lesson, quality feedback | W5 |
| CAN-05 | Emergency reserve after an explicit entitlement/economy design | W5 discovery |
| CAN-06 | Multihop only after base route health/capacity proof | W5 discovery |
| CAN-15 | Security-tools bundle only for separately maintained, real functions | W6 discovery |

### Guide And Video Program

- Build a searchable guide registry instead of one giant FAQ page.
- Cover onboarding, installation, connection, every route mode, every setting, payment, devices, recovery, troubleshooting and fallback clients.
- Record short task-based videos from a clean emulator/device with no account data, tokens, IPs or raw configs visible.
- Each guide owns: platform/version, prerequisites, numbered steps, expected result, failure branch, last verified date and related short video.
- Initial target is coverage completeness, not an artificial count; the registry may exceed Blanc's observed 99 articles when distinct tasks require it.

## Execution Order

1. [WO-001 Protection core](WO-001-protection-core.md): MUST-01/02/03/06/07/08 plus SHOULD-16/17/20.
2. Routing controls: MUST-04/05/14 plus SHOULD-01/02/03/04/05/18/19 and gated CAN-06 discovery.
3. Owned operations/trust: MUST-09/10/11/12/13 plus SHOULD-06/07/09/11/12/13/14.
4. Exact-candidate release smoke: MUST-15; emulator remains preflight, not production proof.
5. Loyalty/economy: CAN-01/02/03/04/05 and later-only SHOULD-10.
6. Guide/video registry and production pipeline across app, LK and site.

Per-feature implementation and evidence ledger:
[IMPLEMENTATION-STATUS.md](IMPLEMENTATION-STATUS.md).

Current Apple Account and iOS installation source review:
[APPLE-ACCOUNT-SOURCES-2026-07-23.md](APPLE-ACCOUNT-SOURCES-2026-07-23.md).

## Current State

- Full interaction recheck: `LOCAL_QA_PASS`. The former manual trusted-Wi-Fi
  Flutter assertion, locked location rows and accessibility gaps are fixed and
  covered by widget, browser/E2E and fresh-APK ADB proof. The current production
  `/guides/` still serves the old homepage until this candidate is deployed.
  Exact proof, screenshots, limitations and cleanup are retained in
  [QA-RECHECK-2026-07-23.md](QA-RECHECK-2026-07-23.md).
- W1-W3 status: `IMPLEMENTED_LOCAL`; production/deploy claims remain closed.
- W4 status: local preflight/debug proof only; exact signed candidate and
  physical-device/store/origin checks are `MANUAL_OWNER_TEST`.
- W5 status: selected local loyalty work implemented; SHOULD-10 remains
  `FOUNDATION_DISABLED`; CAN-05 and CAN-06 remain `DISCOVERY_ONLY`.
- W6 status: CAN-15 remains `DISCOVERY_ONLY`.
- Guide registry: `46/46` detailed task guides and `46/46` visual targets
  integrated across public site and cabinet, with the app linking to the
  canonical route. A separate atlas documents `20` real Android screens and
  panels with non-obscuring numbered outlines. Video program is
  `PLANNED_NOT_RECORDED`.
- Deploy, signing, store publication and production mutation: `NOT_REQUESTED`.
- Android LDPlayer: authorized for local feature QA; it does not close physical-device or signing gates.

## Next Action

Deploy or otherwise align the QA-02 production guides destination, then verify
that exact origin. Signing, live-account connection, physical TalkBack,
publication, production flags/data and promotion remain separate owner actions.
The focused LDPlayer flow already passed for the local candidate. The
implementation ledger is retained in
[IMPLEMENTATION-STATUS.md](IMPLEMENTATION-STATUS.md); the current QA verdict is
retained in [QA-RECHECK-2026-07-23.md](QA-RECHECK-2026-07-23.md).
