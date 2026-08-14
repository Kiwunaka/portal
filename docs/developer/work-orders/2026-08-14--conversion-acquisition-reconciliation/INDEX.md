# POKROV Conversion-first Acquisition And Retention

Status: `ACTIVE_EXECUTION`

## Goal

Довести POKROV до цельной conversion-first воронки без намеренного технического
долга и без регресса публичной `v1.0.4-beta.1`: человек понимает продукт,
скачивает официальный Android/Windows-клиент без стены авторизации, переносит
источник привлечения в оплату и первый запуск, видит только доступные тарифы,
получает полезные уведомления без спама, а оператор честно видит, откуда пришли,
куда дошли, что делали и где остановились.

Отдельный обязательный результат — вернуть видимые и работающие варианты
`Белые списки` в приложении, доказав всю цепочку production rollout → API →
кэш → UI → materialization/runtime. Наличие кода или теста без live payload не
считается завершением.

## Product Rules

- Аналитика только first-party. Никаких рекламных SDK и сторонних
  маркетинговых трекеров.
- Разрешены acquisition/product события и технические ошибки, необходимые для
  ответа на четыре вопроса: источник, следующий шаг, выполненное действие,
  место остановки. История посещённых сайтов через VPN не собирается.
- `start_99` — один первый полный месяц за 99 ₽ на одном устройстве, доступный
  один раз. Следующая обычная покупка месяца — 239 ₽; автопродления нет.
- Главная показывает три предложения: `start_99`, 6 и 12 месяцев. Checkout
  сохраняет все шесть планов и остаётся компактным.
- Реферал: приглашённому +5 дней, пригласившему +10 дней только после первой
  успешной оплаченной покупки приглашённого и действующей 72-часовой
  антифрод-задержки. Установка, триал и подключение бонус не выпускают.
- Trial — 5 дней. Постоянной бесплатной ноды нет.
- Lifecycle/incident сообщения важнее рекламы. Промо не может вытеснять
  проблему доступа, оплату или критический инцидент.
- Apple, stores, юрлица, Kira/content ads, новый платёжный провайдер, recurring
  billing, free node и широкая переделка клиента вне этой волны.

## Queue

| Work order | Outcome | Depends on | Status |
| --- | --- | --- | --- |
| [WO-001](WO-001-audit-reconciliation-and-owner-decisions.md) | Старые аудиты сверены с точным baseline, решения владельца записаны | — | `COMPLETE` |
| [WO-002](WO-002-product-truth-and-branch-baseline.md) | Одна текущая правда о версии, ценах, trial, free и referral; безопасные рабочие ветки | WO-001 | `COMPLETE` |
| [WO-003](WO-003-public-release-and-direct-downloads.md) | Публичный безопасный каталог релизов и прямые Android/Windows загрузки без auth fallback | WO-002 | `COMPLETE` |
| [WO-004](WO-004-first-party-attribution-and-handoff.md) | First/last touch, реальные download/checkout/paid/connect события и TTL handoff до app/account | WO-002, WO-003 | `IN_PROGRESS` |
| [WO-005](WO-005-marketing-and-seo-conversion-layer.md) | Новый первый слой сайта, три тарифа и честные intent/SEO формулировки | WO-002, WO-003 | `IN_PROGRESS` |
| [WO-006](WO-006-checkout-eligibility.md) | `start_99` виден только доступному аккаунту; compact checkout не регрессирует | WO-002 | `IN_PROGRESS` |
| [WO-007](WO-007-lifecycle-notifications-and-promo-arbiter.md) | Единая приоритетная доставка lifecycle/incident/promo по app, OS и Telegram | WO-002, WO-004 | `IN_PROGRESS` |
| [WO-008](WO-008-telegram-guided-entry.md) | Бот ведёт к одному следующему шагу вместо панели, рабочие download/help ветки сохранены | WO-003, WO-004 | `IN_PROGRESS` |
| [WO-009](WO-009-live-whitelist-variants.md) | `Белые списки` видны и выбираются в production app, fail-closed безопасность сохранена | WO-002 | `IN_PROGRESS` |
| [WO-010](WO-010-honest-admin-funnels.md) | Acquisition и product funnels разделены и не выдают сумму разных identity за cohort | WO-004 | `IN_PROGRESS` |
| [WO-011](WO-011-release-promotion-and-production-proof.md) | Exact gates, commits, push, deploy и current-origin production evidence | WO-003..WO-010 | `PENDING` |

## Acceptance Oracle

Волна завершена только если:

1. новые/изменённые canonical owners, код и тесты не противоречат друг другу;
2. анонимный пользователь получает точный официальный APK/EXE без входа;
3. источник и кампания доходят до download, checkout, paid и первого
   подтверждённого connect там, где выполнен безопасный handoff; неизвестная
   связь остаётся `unknown`, а не угадывается;
4. Telegram и сайт ведут пользователя коротким путём, не скрывая платформу,
   цену, ограничения 99 ₽ и отсутствие автосписаний;
5. lifecycle/promo не дублируются, соблюдают opt-out, quiet hours и лимит;
6. prod `GET /api/client/locations` отдаёт безопасные variants для реально
   включённой когорты, приложение их показывает и выбранный вариант попадает в
   точную materialized-конфигурацию;
7. admin показывает отдельные acquisition/product конверсии с явным знаменателем;
8. platform продвигается в `master`, client — в `main`; exact commit hashes,
   runtime origin и проверки записаны без превращения manual/blocked в PASS.

## Commit And Promotion Boundaries

Планируемые reviewable commits:

1. platform truth/public release contract;
2. platform attribution schema, events and safe handoff;
3. marketing/checkout/bot conversion surfaces;
4. lifecycle/promo delivery and admin funnel semantics;
5. client handoff/notification/whitelist surface and runtime fixes, если нужны;
6. exact documentation/evidence closure.

Коммиты могут быть объединены только если фактический diff мал и владелец
контракта один. Platform и client никогда не смешиваются в одном Git history.
Сначала focused tests, затем relevant regression gates, secret/diff review,
push feature branches, fast-forward promotion lines, deploy platform, exact
current-origin smoke; новый бинарный релиз создаётся только если client diff
реально меняет доставляемый бинарник.

## Current Baseline

- Platform exact baseline: `bf79d3d`, совпадает с `origin/master`.
- Client exact baseline: `e172d4b`, совпадает с `origin/main`.
- Public release: `v1.0.4-beta.1`; Android `1.0.4+2013`; Windows
  `1.0.4-beta.1+13`.
- Current RUB catalog: 99 / 239 / 669 / 1199 / 1699 / 1999.
- Local promotion refs были stale на старте; это не непромерженная работа.
  Перед разработкой их разрешается только fast-forward, без фиктивных merge.

## Browser Baseline — Telegram

Проверено 2026-08-14 в авторизованном Telegram Web через встроенный Browser:

- returning `/start` показывает восемь равноправных кнопок; это подтверждает
  ощущение «панели управления»;
- `Помощь` открывает ещё шесть действий;
- Android-ветка уже короткая и полезная: ARM64 основной, ARMv7 и universal —
  запасные, ручное подключение вторично;
- значит, задача WO-008 — упростить первый уровень, а не переписать рабочие
  платформенные/download ветки.

Browser не использует системную мышь. Платёж, отправка свободного текста и
изменения аккаунта во время discovery не выполнялись.

## Resume Rule

Продолжать с первого `IN_PROGRESS` WO. Не начинать широкую полировку app UI до
новых замечаний владельца после фактического использования приложения. Эти
замечания добавляются отдельным bounded WO или superseding addendum, не
подмешиваются молча в текущие acceptance criteria.
