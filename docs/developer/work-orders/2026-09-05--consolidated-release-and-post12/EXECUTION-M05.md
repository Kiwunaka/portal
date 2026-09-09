# R12-M05 — атрибуция и серверная воронка

Дата: 2026-09-06. Результат: **I3 / PARTIALLY_FIXED**.
Команды, source tuple и SHA логов:
[evidence/m05-attribution.json](evidence/m05-attribution.json).
Source commit: `8293c484eb5e1953099d7cdbfcdf6f5dbe4d17b6`.

## Исправления

Admin funnel засчитывал клиентские `paid`/`renewed` как оплату, а
`connected_ok` и first-connection self-report — как подключение. Теперь
оплата требует server-owned `ExternalOrder`/Stars `PayAttempt` со статусом
paid и временем оплаты. Подключение требует `ConnectionEvidence` вида
`observer_connection` после первой подходящей оплаты и до конца периода.
Раннее trial-подключение не становится post-payment outcome.

Browser first-touch cohort и distinct known-user product cohort остаются
раздельными. Тест подтверждает: без handoff серверная оплата и observer fact
дают product outcome, но не создают acquisition session. Диагностические
события сохраняют своё назначение и не определяют платёжный numerator.

В acquisition pipeline IPv4 referrer сохранялся в БД и становился fallback
source. Браузер также копировал его в source и local storage, поэтому одного
исправления referrer на сервере было недостаточно. Теперь оба слоя отбрасывают
IP literals в referrer/source. При чтении старого browser cache эти поля
очищаются и перезаписываются; session ID и допустимая campaign history
сохраняются. Допустимые domain referrers и named sources работают как прежде.
Серверная очистка относится к новым принятым touches: ретроактивная миграция
исторической БД не выполнялась.

## Доказательства

- Before: 1 IPv4 fallback regression FAIL; затем 2 explicit-source FAIL.
  IPv6 referrer до изменений уже отбрасывался host allowlist.
- Два API regressions воспроизвели ошибочные payment/connection outcomes.
  Проверяются self-report, observer до оплаты, неподходящий evidence kind,
  observer после оплаты и product outcome без browser handoff.
- Browser utility исполняется через существующий TypeScript compiler и Node VM
  с localStorage/fetch fixtures: before 2 FAIL / 1 PASS; after 3 PASS.
  Проверены новый referrer/source, ранее сохранённый cache и сохранение
  допустимой first-touch attribution. Реальные внешние запросы не отправляются.
- Финальный acquisition/API suite: 17 PASS. Existing commercial order/pilot
  suite: 15 PASS; admin commercial projection: 1 PASS.
- Commercial tests сохраняют immutable campaign→offer→order→grant lineage,
  observer-based first connect, D7/D30 windows, renewal и reversal; read model
  не выдаёт anonymous/account/order identifiers. Код этих проекций не менялся.
- Marketing build, lint, SEO, responsive и 39 copy/governance/pilot checks — PASS.
- Обязательный backend router suite: 154 PASS и 8 subtests PASS.
  Documentation contracts: 33 PASS; context audit и package check: PASS,
  включая 165 local links, все 83 R12 IDs и сохранённые 378 legacy IDs.
- Scoped source/manifests scan не нашёл перечисленные ad/fingerprint SDK.
  Это проверка исходников и manifests, не сетевой аудит финального APK/EXE.

## Открытые границы

M05 целиком не закрыт: M02/F02 runtime proof и B06 provider
payment/refund/reconciliation E2E остаются открытыми. Локальные fixtures
не заменяют проверку действующей коммерции и опубликованного клиента.
`/t/` POST12-40 не добавлялся; внешний pilot, расходы и отправки не запускались.

Изменены только platform source/tests и их владельцы документации.
Client/Core и retained candidate.33 не изменены. Новые candidate builds,
signing, push, merge, deploy и production DB mutation не выполнялись.
