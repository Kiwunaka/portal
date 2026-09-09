# POST12-40 — `/t/<slug>` и достоверная placement attribution

**Scope:** один дополнительный вход в существующий acquisition pipeline.<br>
**Источник:** `pokrov_t_shortlink_attribution_plan(1).md`; исправления COR-02/03/04.<br>
**Не входит:** новые rewards/trial/referrals, изменение цен, рекламный SDK, новая tracking identity, закупка размещений.

## 1. Итоговый контракт

Один опубликованный slug соответствует одному immutable paid-placement identity. Redirect доставляет canonical metadata; существующая AcquisitionSession сохраняет touch/handoff; заказ фиксирует **неизменяемый snapshot атрибуции**; отчёт считает provider-confirmed paid и refunds. Attribution не выдаёт доступ, скидку, бонус или права на аккаунт.

Обычный `ref=plc_*` можно подделать, поэтому отдельно хранить уровень доказательства: `declared_query`, `verified_first_party_touch`, `unattributed`. Даже verified receipt не доказывает человека, просмотр рекламного поста или причинность покупки. Browser→app связывается только реальным handoff, не IP/fingerprint.

## 2. Архитектура, совместимая со static export

В прочитанном `marketing/next.config.mjs` установлен `output: "export"` [GH-MARKETING]. Динамический Next Route Handler из старого плана не работает как request-time backend экспортированного сайта [WEB-NEXT].

**Выбранное предложение:** сохранить static marketing; route `/t/*` на Caddy направить в существующий FastAPI **до** static fallback. Runtime service получает placement из БД и строит 302. Новая ссылка не требует frontend rebuild. Не переводить весь сайт на SSR и не добавлять Node process ради одного пути.

Логическая схема; фактические имена routers и Caddy файла определить по current owners:

```text
pokrov.space/t/<slug>
→ Caddy path matcher before file_server
→ FastAPI placement route
→ AcquisitionPlacement service + current DB/UoW
→ 302 /<approved-landing>?<canonical-utm/ref>
→ existing marketing acquisition flow
→ existing handoff/account/order
```

Маркетинговый JS не становится authority placement metadata. Public JSON resolve допускается для совместимости, но отдельный сетевой self-call из FastAPI в собственный JSON endpoint не нужен: оба используют один service layer.

## 3. Placement model

Переиспользовать существующую подходящую модель, если rebaseline её найдёт. Иначе additive table:

| Поле | Правило |
|---|---|
| id/public_id | Internal PK отдельно; public `plc_*` уникален и стабилен |
| slug | Нижний ASCII `[a-z0-9-]`, 3–64 символа, уникальность enforced DB |
| status | draft/live/disabled; не статус offer |
| source/campaign/content/publisher/exchange | Bounded normalized metadata; campaign/content identity freeze при publish |
| destination_path | Только разрешённый локальный path, никакого произвольного URL |
| cost_amount/currency | Decimal + исходная валюта; неизвестная стоимость = null |
| created/published/updated/disabled_at | UTC; publish фиксируется атомарно |
| revision | CAS для операторских изменений |
| cost/destination/status history | Через существующий audit/version mechanism |
| notes/external_order_ref | Только разрешённая операторская projection |

**Неизменяемость:** с первой публикации фиксируются public_id, slug, publisher и attribution identity. Повторная закупка/другая campaign — новая запись. Изменять destination/status/cost можно с audit+revision; отчет as-of не должен незаметно переписываться новым cost.

Не добавлять `offer_key` заранее без actual consumer. Отсутствие public resolve не должно подтверждать существование draft.

## 4. HTTP и destination safety

GET для navigation; HEAD для безопасной проверки без человеческого события/выдачи reward. Другие методы — 405. Неизвестный/draft — 404, disabled — 410 с «Ссылка неактивна», временный backend failure — 503 + bounded Retry-After. 302 с `Cache-Control: no-store`; не 301/308.

Incoming UTM/ref не могут overwrite canonical placement. Arbitrary input query не переносится. Destination allowlist — реальные landing routes, а не любой startsWith('/'):

- Reject schemes, `//`, backslash, controls/CRLF/NUL, traversal и encoded separator/double-encoding ambiguity.
- Парсить/нормализовать последовательно; после canonicalization повторно проверить origin/path/prefix.
- Никаких `Host`/`X-Forwarded-Host` от недоверенного клиента как authority redirect origin.
- Проверить существование target route в static export manifest либо canonical routes.
- Строгий лимит длины/charset slug и query. БД parameterized.

На backend failure не придумывать ref и не показывать false tracked success. Branded error содержит обычный безопасный переход на главную **без подтверждённой attribution**. Ошибка аналитики не лишает человека возможности скачать/оплатить через существующий продукт.

## 5. Attribution: минимальное расширение без второго трекера

### 5.1. Что сохраняется

AcquisitionSession, existing first/last touch semantics, acquisition handoff, event dedupe и order intent. `ref=plc_*` остаётся удобным public ключом. `/t/` не создаёт новый persistent user/session ID на каждый click.

### 5.2. Verified touch

Для отчёта с label `verified_first_party_touch` нужен server-issued bounded receipt, связывающий placement/revision/time/purpose с тем же acquisition session. Сначала проверить, можно ли расширить существующий one-time handoff/receipt без нового протокола.

Предлагаемый browser вариант: `/t/` выдаёт opaque short-lived first-party HttpOnly cookie для attribution only; landing вызывает узкий same-origin consume endpoint; backend связывает receipt с существующей AcquisitionSession и удаляет cookie. Использовать текущие CSRF/origin/request-bound controls. При API на другом subdomain добавить именно этот same-origin proxy route; не расширять cookies на все subdomains ради удобства.

Не передавать receipt в сторонние pixels, URL рефереры, logs или permanent browser storage. Содержимое cookie не содержит account credentials. Rate/burst limits и TTL используют существующий approved privacy/abuse contract, не новый долгоживущий fingerprint.

**Граница сложности:** если существующая receipt machinery не поддерживает нужный binding, оформить один небольшой additive contract. Не перепроектировать весь payment/acquisition. Пока receipt не доказан, разрешено сохранять `declared_query` как маркетинговую подсказку, но нельзя закрыть criterion verified lineage или использовать её для бонуса/денег. Checkout продолжает работать как unattributed/declared.

### 5.3. Повтор/несколько вкладок/preview bots

Однократный consume идемпотентен для того же session; replay в другом session rejected. Повторный genuine click может обновить last touch согласно current policy, не first touch. Две вкладки не создают account identity. Одна общая cookie без проверки соответствия navigation/placement не обеспечивает tab-level binding: она может быть перезаписана вторым переходом. Выбранный receipt contract должен проверить краткоживущий контекст конкретного перехода и текущую acquisition session либо отклонить неоднозначное связывание. Потеря/перезапись receipt даёт unattributed, не уверенное присвоение чужого placement; долгоживущий tracking ID для решения этой гонки запрещён. HEAD/preview hit не считается paid conversion или человеком. JS page_view тоже не гарантирует человека.

## 6. Immutable order snapshot

Не вычислять placement уже оплаченного заказа через текущий mutable `AcquisitionSession.last_ref`.

При local order creation сервер сохраняет существующим order-intent mechanism:

```text
attribution_schema + policy_revision
acquisition_session reference
selected touch reference + trust level + occurred_at
placement public_id + placement revision
source/campaign/content snapshot
attribution model + window
```

Цена, eligibility и entitlement остаются в собственных current contracts. Snapshot не берётся из callback и не восстанавливается из произвольного браузерного поля после оплаты. Повтор того же order intent возвращает ту же атрибуцию. Payment callback обновляет paid/refund outcome, а не первоисточник.

**Главный regression:** пользователь пришёл A, создал order A, затем пришёл B и оплатил старый A. Старый order остаётся A. Новый order после B получает attribution по зафиксированной current policy. Reload/late callback не переписывает историю. Срок модели атрибуции определён; 180-дневный browser cache из старого плана не является автоматически сроком paid attribution или legal retention.

## 7. Admin и CLI

P0-CLI либо небольшой existing Operator Center action — без ожидания нового рекламного кабинета. Общий service layer с validate/create/publish/disable/change-destination/cost-revision. Команда создания не обязана автоматически publish. Все writes имеют actor, explicit environment, expected revision, reason, existing auth/action-intent/audit; production по отдельному разрешению.

Admin read API размещать в текущем Admin v2 namespace после route inventory; не создавать рядом старый незащищённый `/api/admin/...` путь. Права просмотра стоимости отдельно от публичного resolver. Public endpoint возвращает только redirect/безопасные canonical attribution fields, не cost/notes/external_order_ref/internal IDs.

Создание новой ссылки, publish и закупка рекламы — три разных действия. Реальный marketing spend/public placement этим планом не разрешён.

## 8. Метрики с правильными знаменателями

| Метрика | Формула/смысл |
|---|---|
| redirect_hits | Технические GET/HEAD/preview обращения, не люди |
| landing_views | События страницы; не гарантированно human clicks |
| acquisition_sessions | Distinct existing browser session; не уникальные люди |
| download_clicks | Действия на CTA; не установленное приложение |
| installs/account links | Только подтверждённый handoff/событие, unknown отдельно |
| first_verified_connect | Product event, privacy-safe linked только при существующем binding |
| cost per landing view | placement cost / landing views |
| CPC | cost / явно определённые qualified clicks, только если такая метрика есть |
| cost per paid order | cost / provider-confirmed attributable paid orders |
| CAC first payer | cost / distinct attributable accounts с первой успешной покупкой |
| revenue/net revenue | В валюте заказа, refunds/reversals отдельно; не смешивать валюты без recorded FX |
| ROAS | Атрибутированная выручка / ad spend, не прибыль и не причинный incrementality |

Знаменатель 0, отсутствующие cost или недостаточный identity binding → null/N/A, не 0 и не придуманный результат. Renewals не считаются каждый раз новым customer. Дедупликация по order/event identity, attribution model/window/revision видимы. Cost correction и FX имеют дату/источник; никаких live FX незаметно задним числом.

Минимальный отчет: placement metadata+trust class; landing/session/download/handoff/first-connect/paid/refund counts; currency-aware amounts; выбранные ratios. Browser и app знаменатели отдельно. Нет raw per-user paths в public reports.

## 9. Migration / rollback / privacy

Additive table/index и compatible optional order snapshot fields. Обновлять по expand→code→observe, не разрушать existing acquisition. Уникальность slug/id и нужные query indexes; реальные Postgres transaction/concurrency tests.

Rollback после использования: выключить flag/resolver/новые writers, вернуть compatible code, сохранить placements/order snapshots/audit. `DROP TABLE` допустим лишь для неиспользованной disposable test DB по явному тестовому действию, не операционный rollback production.

No raw IP/UA/fingerprint/browsing history в attribution storage. Reverse proxy/access logs проверить отдельно: запрет в Python-модели не гарантирует отсутствие cookie/query в Caddy logs. Receipt redaction, ограниченный TTL/retention, deletion/aggregation semantics и согласованная privacy policy обязательны. 180 дней из старого localStorage поведения не принимать без current policy review.

## 10. Исполнимые задачи (дочерние POST12-40)

| ID | Результат | Зависимости | Oracle |
|---|---|---|---|
| T-01 | Current acquisition/payment/Caddy/static-export map | POST12-00 | Один owner каждого слоя; размещение не меняет trial |
| T-02 | Placement model/service/additive migration + CLI | T-01 | Unique publish identity/CAS/destination/role tests |
| T-03 | Verified touch receipt или reuse existing handoff contract | T-01/T-02 | Replay/expiry/cross-session rejected; no second identity |
| T-04 | FastAPI `/t/` + Caddy route + branded errors | T-02/T-03 | New slug без rebuild; 302/no-store; no open redirect |
| T-05 | Landing consume + existing handoff integration | T-03/T-04 | Trust class accurate; storage/network denial nonblocking |
| T-06 | Immutable order attribution snapshot | T-05 + current order UoW | Order A stays A after later B; idempotency/late callback |
| T-07 | Admin read/CLI audit + metrics | T-02/T-06 | CAC vs cost/order; 0/null; refunds/FX; role redaction |
| T-08 | E2E/security/migration/rollback | T-04/T-05/T-06/T-07 | Same pipeline, no grants/referral side effects |
| T-09 | Isolated/staging smoke and owner-authorized release | T-08 + deployment approval | Actual path, readback, rollback; no ad purchase |

## 11. Минимальная acceptance suite

Valid/draft/disabled/unknown slug; duplicate concurrent publish; query override; encoded traversal/CRLF/backslash/external redirect; crafted Host; new placement without marketing rebuild; backend unavailable; HEAD/preview; cookie blocked/JS unavailable; receipt expiry/replay/cross-session; two tabs; first/last touch; browser→app loss; A/B order snapshot; duplicate callback; payment pending/refund; no trial/bonus/referral mutation; no raw logs; unauthorized CLI/API; database downgrade без потери истории.

Локальная implementation goal завершается после соответствующих реально выполненных tests и plan-safe docs, не после выдуманного production smoke. T-09 и paid marketing launch имеют отдельную authority.

## Общие определения ссылок

[AUD-S01]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/docs/developer/work-orders/2026-08-21--release-1.2.0-megaplan/OWNER-FREEZE-2026-09-05.md
[AUD-S02]: https://github.com/Kiwunaka/POKROV-app/blob/da1ad7395615837432615e0f150d7c0bf05322a4/config/cutover-readiness.seed.json
[AUD-S03]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/docs/developer/work-orders/2026-08-21--release-1.2.0-megaplan/evidence/013GV-candidate33-bounded-windows-android-runtime/013GV-candidate33-gate-f-decision.json
[AUD-S04]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/docs/developer/work-orders/2026-08-21--release-1.2.0-megaplan/INDEX.md
[AUD-S05]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/docs/developer/work-orders/2026-08-21--release-1.2.0-megaplan/SOURCE-CROSSWALK.md
[AUD-S06]: https://github.com/Kiwunaka/POKROV-app/blob/da1ad7395615837432615e0f150d7c0bf05322a4/docs/operations/cutover-readiness.md
[AUD-S07]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/shared/tariff-catalog.json
[AUD-S08]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/marketing/src/app/checkout/checkout-client.tsx
[AUD-S09]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/portal_bot/api_payment_routes.py
[AUD-S10]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/portal_bot/admin_v2/security.py
[AUD-S11]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/adminapp/README.md
[AUD-S12]: https://github.com/Kiwunaka/pokrov-core/blob/c1185faa998c69fd5164af415249c96c68ab61bd/config/awg31-capability.json
[AUD-S13]: https://github.com/Kiwunaka/pokrov-core/blob/c1185faa998c69fd5164af415249c96c68ab61bd/engine/sing-box/protocol/awg/contract.go
[AUD-S14]: https://github.com/Kiwunaka/POKROV-app/blob/da1ad7395615837432615e0f150d7c0bf05322a4/apps/android_shell/android/app/src/main/kotlin/space/pokrov/pokrov_android_shell/AndroidCoreEgressProbe.kt
[AUD-S15]: https://github.com/Kiwunaka/POKROV-app/blob/da1ad7395615837432615e0f150d7c0bf05322a4/apps/android_shell/android/app/src/main/kotlin/space/pokrov/pokrov_android_shell/AndroidCoreOperationalEvents.kt
[AUD-S16]: https://github.com/Kiwunaka/POKROV-app/blob/da1ad7395615837432615e0f150d7c0bf05322a4/apps/linux_shell/README.md
[AUD-S17]: https://github.com/Kiwunaka/POKROV-app/blob/da1ad7395615837432615e0f150d7c0bf05322a4/config/release-handoff.seed.json
[AUD-S18]: https://api.github.com/repos/Kiwunaka/POKROV-app/contents/packages/app_shell/lib
[AUD-S19]: https://github.com/Kiwunaka/Pokrov-client/blob/main/README.md
[AUD-W01]: https://docs.amnezia.org/documentation/amnezia-wg/
[AUD-W02]: https://docs.amnezia.org/faq/
[AUD-W03]: https://github.com/amnezia-vpn/amneziawg-go
[AUD-W04]: https://learn.microsoft.com/en-us/windows/release-health/release-information
[AUD-W05]: https://base.garant.ru/12145525/5633a92d35b966c2ba2f1e859e7bdd69/
[AUD-W06]: https://epp.genproc.gov.ru/ru/proc_78/activity/legal-education/explain/otherwise/e8255163/
[GH-AWG]: https://github.com/Kiwunaka/pokrov-core/blob/c1185faa998c69fd5164af415249c96c68ab61bd/config/awg31-capability.json
[GH-AWG-FIX]: https://github.com/amnezia-vpn/amneziawg-go/commit/b5928efb6ca19f0153958460c3d141f04abc5c2e
[GH-MARKETING]: https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/marketing/next.config.mjs
[WEB-ANDROID]: https://developer.android.com/reference/android/net/VpnService.Builder
[WEB-CODEX-COMMANDS]: https://developers.openai.com/codex/cli/slash-commands
[WEB-CODEX-GOALS]: https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex
[WEB-NEXT]: https://nextjs.org/docs/14/app/building-your-application/deploying/static-exports
[WEB-WIREGUARD]: https://www.wireguard.com/protocol/
