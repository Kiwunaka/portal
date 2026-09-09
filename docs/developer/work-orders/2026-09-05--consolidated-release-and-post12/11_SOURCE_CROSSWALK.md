# Источники, трассировка и пределы проверки

**Дата консолидации:** 2026-09-05.<br>
**Прочитаны:** семь новых вложений, предыдущий master-plan и backlog. Для отдельных исправлений использованы точные GitHub-файлы и первичные внешние документы.<br>
**Не заявляется:** новый полный аудит всех строк кода, исполнение Flutter/Go/backend tests, вход в production, живые оплаты, carrier/OEM испытания или запуск Goals.

## 1. Входные файлы и SHA-256

Хеши ниже рассчитаны по реально приложенным байтам, а не скопированы из старого INDEX. Они идентифицируют источник плана, не удостоверяют правильность его утверждений. Исходники не включены второй конкурирующей execution-очередью: этот пакет содержит итоговые MD; старые файлы остаются историей.

| ID | Исходный файл | Байты | SHA-256 | Итоговый владелец |
|---|---|---:|---|---|
| NEW-01 | `POKROV_SMART_ROUTING_AND_SMART_ACCESS_DETAILED_PLAN_2026-08-26.md` | 75164 | `19b24007e6c74f99d1c53a7aa20f0618982aa6f55589fdce46cfb9a0e49dee97` | [06_POST12_SMART_ROUTING_ACCESS.md](06_POST12_SMART_ROUTING_ACCESS.md) — Smart Routing, WP-00–16 |
| NEW-02 | `pokrov_t_shortlink_attribution_plan(1).md` | 34723 | `70513452dea0592743550e7f71c4bf8f34e981898bfdbd2de27e78ec2a7b5f19` | [07_POST12_SHORTLINK_ATTRIBUTION.md](07_POST12_SHORTLINK_ATTRIBUTION.md) — Shortlink /t/, 42 раздела |
| NEW-03 | `pokrovplan` | 13194 | `c991d77e59ee33a78c3044a4a8aac7294b5644889f23034b6858b46875a9e93a` | [05_POST12_TRANSPORT_AWG.md](05_POST12_TRANSPORT_AWG.md) — AWG 3.1 DisableCookies, 8 фаз и DoD |
| NEW-04 | `README.md` | 444 | `100aa3cae096411346fae544ecd3cc83c64ee59b1c80245f1ab399dc942f4077` | [00_START_HERE.md](00_START_HERE.md) — Retained dated inputs; не execution authority |
| NEW-05 | `INDEX.md` | 8438 | `77777ccfed1d1861f38feb0528a70b6fe266a20d061dcd2eac616f9e212046ff` | [04_POST12_SHARED_ARCHITECTURE.md](04_POST12_SHARED_ARCHITECTURE.md) — Родительский POST12 portfolio и activation gate |
| NEW-06 | `POKROV_ADAPTIVE_TRANSPORT_PRE_ARCHITECTURE_PLAN_2026-08-29.md` | 61679 | `346161bf23f57cf28d07920a558805e7d3ac008df358f45d909a202b7673adce` | [04_POST12_SHARED_ARCHITECTURE.md](04_POST12_SHARED_ARCHITECTURE.md) — ATS-000–016, 32 раздела |
| NEW-07 | `INDEX(1).md` | 47199 | `78c576873538e71c2cecf502cca0f379892bd7dd5811cc887438d5dd8696f1fd` | [05_POST12_TRANSPORT_AWG.md](05_POST12_TRANSPORT_AWG.md) — Censorship resilience, CR-000–023 |
| AUDIT-01 | `pokrov_audit_2026-09-05/MASTER_PLAN.md` | 111814 | `9d00edefba4c2486b27b4771838c32048ff42afd149d308e06e0080a7cbe637c` | [02_RELEASE_1_2_0.md](02_RELEASE_1_2_0.md) — Предыдущий аудит 5 сентября; исторические source/evidence выводы |
| AUDIT-02 | `pokrov_audit_2026-09-05/EXECUTION_BACKLOG.md` | 73761 | `68a5bf3c44d2e24d86c2e4c47b77e5e3f96ccaf145d8cd56fae7f0790ea21704` | [03_RELEASE_BACKLOG_83.md](03_RELEASE_BACKLOG_83.md) — Человекочитаемый предыдущий backlog |
| AUDIT-03 | `pokrov_audit_2026-09-05/execution_backlog.json` | 91057 | `ec8676c4b5053f2c048bf498594e9a7658386cb9b4e7cca6679bce5d398975cc` | [03_RELEASE_BACKLOG_83.md](03_RELEASE_BACKLOG_83.md) — Машинный источник 83 R12-ID |

### Сверка с импортными хешами старого INDEX

- `POKROV_SMART_ROUTING_AND_SMART_ACCESS_DETAILED_PLAN_2026-08-26.md`: совпадает с историческим import hash.
- `pokrovplan`: совпадает с историческим import hash.
- `pokrov_t_shortlink_attribution_plan(1).md`: совпадает с историческим import hash.

## 2. Что откуда перенесено

| Старый источник/ID | Итоговый документ | Решение |
|---|---|---|
| 83 R12 slices прежнего аудита | 03 | Все IDs, зависимости и направления сохранены; уточнённые DoD помечены |
| 378 требований canonical release ledger | 02/03/09 | Сохраняются в repo; полная новая построчная сертификация не заявляется |
| POST12-00 | 04 | Один activation/baseline, переиспользуется ATS-000 и CR-000 |
| POST12-05 | 04 | Общее обязательное ядро ADR/fixtures, feature-specific эксперименты отдельно |
| POST12-10 | 05 | AWG/TCP/XHTTP/resilience, без второго Core |
| POST12-20 | 06 | Smart Routing/Access, один каталог и согласованный resolver/data path |
| POST12-30 | 08 | Источник отсутствует; только source gate и известный scope |
| POST12-40 | 07 | Небольшой acquisition adapter с исправленной доверенной lineage |
| pokrovplan, фазы 1–5/8 | 05 | AWG flag/upstream/compatibility/runtime; full lab отдельно от cheap connect proof |
| pokrovplan, фаза 6 | 06 | DNS/service scope; не смешивать DNS и VPN |
| pokrovplan, фаза 7 | 09 и последующий security review | Supply chain/retention/privacy, без заявления ETSI/CRA соответствия |
| Retained README | 00/01 | План — данные для работы, не самостоятельное разрешение |

### Полная карта ATS-ID

| ID | Итоговый владелец | Применимость |
|---|---|---|
| ATS-000 | [04](04_POST12_SHARED_ARCHITECTURE.md) | Общее ядро либо сводный gate по выбранному scope |
| ATS-001 | [04](04_POST12_SHARED_ARCHITECTURE.md) | Общее ядро либо сводный gate по выбранному scope |
| ATS-002 | [04](04_POST12_SHARED_ARCHITECTURE.md) | Общее ядро либо сводный gate по выбранному scope |
| ATS-003 | [04](04_POST12_SHARED_ARCHITECTURE.md) | Общее ядро либо сводный gate по выбранному scope |
| ATS-004 | [04](04_POST12_SHARED_ARCHITECTURE.md) | Общее ядро либо сводный gate по выбранному scope |
| ATS-005 | [04](04_POST12_SHARED_ARCHITECTURE.md) | Общее ядро либо сводный gate по выбранному scope |
| ATS-006 | [04](04_POST12_SHARED_ARCHITECTURE.md) | Общее ядро либо сводный gate по выбранному scope |
| ATS-007 | [04](04_POST12_SHARED_ARCHITECTURE.md) | Общее ядро либо сводный gate по выбранному scope |
| ATS-008 | [04](04_POST12_SHARED_ARCHITECTURE.md) | Feature-specific device/AWG gate |
| ATS-009 | [04](04_POST12_SHARED_ARCHITECTURE.md) и [05](05_POST12_TRANSPORT_AWG.md) | Feature-specific device/AWG gate |
| ATS-010 | [04](04_POST12_SHARED_ARCHITECTURE.md) | Общее ядро либо сводный gate по выбранному scope |
| ATS-011 | [04](04_POST12_SHARED_ARCHITECTURE.md) | Отдельный эксперимент; DEFER/NO-GO допустимы, не prerequisite общего ядра |
| ATS-012 | [04](04_POST12_SHARED_ARCHITECTURE.md) | Отдельный эксперимент; DEFER/NO-GO допустимы, не prerequisite общего ядра |
| ATS-013 | [04](04_POST12_SHARED_ARCHITECTURE.md) | Общее ядро либо сводный gate по выбранному scope |
| ATS-014 | [04](04_POST12_SHARED_ARCHITECTURE.md) | Общее ядро либо сводный gate по выбранному scope |
| ATS-015 | [04](04_POST12_SHARED_ARCHITECTURE.md) | Общее ядро либо сводный gate по выбранному scope |
| ATS-016 | [04](04_POST12_SHARED_ARCHITECTURE.md) | Общее ядро либо сводный gate по выбранному scope |

### Полная карта CR-ID

| ID | Итоговый владелец | Сохраняемая граница |
|---|---|---|
| CR-000 | [05](05_POST12_TRANSPORT_AWG.md) | Baseline из POST12-00 не выполняется повторно |
| CR-001 | [05](05_POST12_TRANSPORT_AWG.md) | Общие контракты из 04, implementation/применимость из 05 |
| CR-002 | [05](05_POST12_TRANSPORT_AWG.md) | Общие контракты из 04, implementation/применимость из 05 |
| CR-003 | [05](05_POST12_TRANSPORT_AWG.md) | Общие контракты из 04, implementation/применимость из 05 |
| CR-004 | [05](05_POST12_TRANSPORT_AWG.md) | Общие контракты из 04, implementation/применимость из 05 |
| CR-005 | [05](05_POST12_TRANSPORT_AWG.md) | Общие контракты из 04, implementation/применимость из 05 |
| CR-006 | [05](05_POST12_TRANSPORT_AWG.md) | Общие контракты из 04, implementation/применимость из 05 |
| CR-007 | [05](05_POST12_TRANSPORT_AWG.md) | Общие контракты из 04, implementation/применимость из 05 |
| CR-008 | [05](05_POST12_TRANSPORT_AWG.md) | POST12-10; exact capability/runtime evidence по выбранному scope |
| CR-009 | [05](05_POST12_TRANSPORT_AWG.md) | POST12-10; exact capability/runtime evidence по выбранному scope |
| CR-010 | [05](05_POST12_TRANSPORT_AWG.md) | Один AWG контур; существующий foundation повторно не писать |
| CR-011 | [05](05_POST12_TRANSPORT_AWG.md) | Один AWG контур; существующий foundation повторно не писать |
| CR-012 | [05](05_POST12_TRANSPORT_AWG.md) | Один AWG контур; существующий foundation повторно не писать |
| CR-013 | [05](05_POST12_TRANSPORT_AWG.md) | Измеренный gap → bounded lab; не обязательная интеграция всего портфеля |
| CR-014 | [05](05_POST12_TRANSPORT_AWG.md) | Измеренный gap → bounded lab; не обязательная интеграция всего портфеля |
| CR-015 | [05](05_POST12_TRANSPORT_AWG.md) | Измеренный gap → bounded lab; не обязательная интеграция всего портфеля |
| CR-016 | [05](05_POST12_TRANSPORT_AWG.md) | Измеренный gap → bounded lab; не обязательная интеграция всего портфеля |
| CR-017 | [05](05_POST12_TRANSPORT_AWG.md) | Измеренный gap → bounded lab; не обязательная интеграция всего портфеля |
| CR-018 | [05](05_POST12_TRANSPORT_AWG.md) | POST12-10; exact capability/runtime evidence по выбранному scope |
| CR-019 | [05](05_POST12_TRANSPORT_AWG.md) | Общие контракты из 04, implementation/применимость из 05 |
| CR-020 | [05](05_POST12_TRANSPORT_AWG.md) | Общие контракты из 04, implementation/применимость из 05 |
| CR-021 | [05](05_POST12_TRANSPORT_AWG.md) | POST12-10; exact capability/runtime evidence по выбранному scope |
| CR-022 | [05](05_POST12_TRANSPORT_AWG.md) | Общие контракты из 04, implementation/применимость из 05 |
| CR-023 | [05](05_POST12_TRANSPORT_AWG.md) | POST12-10; exact capability/runtime evidence по выбранному scope |

### Полная карта WP-ID

| ID | Итоговый владелец | Сохраняемая граница |
|---|---|---|
| WP-00 | [06](06_POST12_SMART_ROUTING_ACCESS.md) | POST12-20, текущая реализация сверяется перед изменением |
| WP-01 | [06](06_POST12_SMART_ROUTING_ACCESS.md) | POST12-20, текущая реализация сверяется перед изменением |
| WP-02 | [06](06_POST12_SMART_ROUTING_ACCESS.md) | POST12-20, текущая реализация сверяется перед изменением |
| WP-03 | [06](06_POST12_SMART_ROUTING_ACCESS.md) | POST12-20, текущая реализация сверяется перед изменением |
| WP-04 | [06](06_POST12_SMART_ROUTING_ACCESS.md) | POST12-20, текущая реализация сверяется перед изменением |
| WP-05 | [06](06_POST12_SMART_ROUTING_ACCESS.md) | POST12-20, текущая реализация сверяется перед изменением |
| WP-06 | [06](06_POST12_SMART_ROUTING_ACCESS.md) | Сохранён портфель трёх внешних adapters; коммерческое разрешение не предполагается |
| WP-07 | [06](06_POST12_SMART_ROUTING_ACCESS.md) | POST12-20, текущая реализация сверяется перед изменением |
| WP-08 | [06](06_POST12_SMART_ROUTING_ACCESS.md) | POST12-20, текущая реализация сверяется перед изменением |
| WP-09 | [06](06_POST12_SMART_ROUTING_ACCESS.md) | POST12-20, текущая реализация сверяется перед изменением |
| WP-10 | [06](06_POST12_SMART_ROUTING_ACCESS.md) | POST12-20, текущая реализация сверяется перед изменением |
| WP-11 | [06](06_POST12_SMART_ROUTING_ACCESS.md) | POST12-20, текущая реализация сверяется перед изменением |
| WP-12 | [06](06_POST12_SMART_ROUTING_ACCESS.md) | POST12-20, текущая реализация сверяется перед изменением |
| WP-13 | [06](06_POST12_SMART_ROUTING_ACCESS.md) | POST12-20, текущая реализация сверяется перед изменением |
| WP-14 | [06](06_POST12_SMART_ROUTING_ACCESS.md) | Own provider по фактическому состоянию; не обязан быть создан после всех внешних |
| WP-15 | [06](06_POST12_SMART_ROUTING_ACCESS.md) | QA применима к выбранным платформам/сервисам/providers, не всей возможной вселенной |
| WP-16 | [06](06_POST12_SMART_ROUTING_ACCESS.md) | Canary только после отдельного разрешения и относящихся к нему gates |

### `/t/` и новые локальные ID

T-01–T-09 в файле 07 — подробные work packages внутри прежнего POST12-40. Они не создают новое business-domain authority. HAPP-01–HAPP-05 в файле 08 — source/revalidation очередь внутри POST12-30, не выдуманная реализация отсутствующего плана.

## 3. Предел HAPP/iOS

В parent INDEX есть ссылка на `docs/superpowers/plans/2026-08-26-happ-ios-subscription-bs.md`, import hash `a2643a9bfe156cddb5f36bd7622d444201196e960ffddbe2ad0b79a578a68397` и историческая ветка `codex/happ-ios-canary` / `221f43f22fb27abdeef0d85f74cb0cc04299863a`.

Самого полного плана среди новых вложений нет. Чтение точного пути в GitHub на исследованном platform SHA и указанном branch commit вернуло 404. Library search и уточнение не вернули сам документ: найдены ссылки из INDEX, но не содержание. Это ограничение выполненного поиска, не утверждение, что файл никогда не существовал. Реализация HAPP до retrieval и current-contract reconciliation не специфицирована; остальные ветки этим не блокируются.

## 4. Пинованные репозиторные источники и первичная проверка

Данные ниже проверялись для консолидации отдельных замечаний. Они не означают новый полный current-head audit всех репозиториев. Чтение конкретного pinned файла не устанавливает сегодняшнее production состояние.

### GH-MARKETING

Реальный marketing output: export на закреплённом срезе. [GH-MARKETING](https://github.com/Kiwunaka/portal/blob/6b41f758ca228a0d5ff13ede0f865096cdac2134/marketing/next.config.mjs)

Подтверждён `output: "export"`; предложенный старым /t/-планом runtime Route Handler нельзя просто положить в статический bundle. Выбран серверный адаптер существующего backend.

### GH-AWG

Текущий исследованный AWG3.1 capability pin/MTU/HP. [GH-AWG](https://github.com/Kiwunaka/pokrov-core/blob/c1185faa998c69fd5164af415249c96c68ab61bd/config/awg31-capability.json)

Закреплён v3.1.20260814, обязательная header protection, MTU 1280/1400/1408; DisableCookies не указан среди полей прочитанного capability. Это source contract, не runtime PASS.

### GH-AWG-FIX

Upstream fix DisableCookies underload от 28.08.2026. [GH-AWG-FIX](https://github.com/amnezia-vpn/amneziawg-go/commit/b5928efb6ca19f0153958460c3d141f04abc5c2e)

Прочитан commit/diff: меняется ветвь проверки underload при DisableCookies. Это основание пересмотреть pin перед экспериментом, но не доказанный текущий production баг POKROV. Обновление upstream не выполнено.

### WEB-NEXT

Next.js static export: build-time handlers и unsupported dynamic features. [WEB-NEXT](https://nextjs.org/docs/14/app/building-your-application/deploying/static-exports)

Доступная официальная страница версии 14 использована для устойчивого ограничения static export. Она не утверждает точную установленную версию Next в POKROV; actual package lock проверяется агентом.

### WEB-ANDROID

Android VpnService.Builder: per-app exclusion и builder contract. [WEB-ANDROID](https://developer.android.com/reference/android/net/VpnService.Builder)

### WEB-WIREGUARD

WireGuard protocol: cookies/DoS. [WEB-WIREGUARD](https://www.wireguard.com/protocol/)

### WEB-CODEX-GOALS

OpenAI: Using Goals in Codex. [WEB-CODEX-GOALS](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex)

### WEB-CODEX-COMMANDS

OpenAI: Codex developer/slash commands. [WEB-CODEX-COMMANDS](https://developers.openai.com/codex/cli/slash-commands)


## 5. Явные предложения новой редакции

К авторским решениям этого пакета, а не установленным возможностям исходного кода, относятся: FastAPI/Caddy placement adapter; trust classes и ограниченный reuse receipt для /t/; immutable order snapshot; отказ делать все внешние providers обязательным первым milestone; separation light/lab/soak proof; scoped DoR; последовательность bounded Codex goals. Их rationale и acceptance содержатся в соответствующих файлах.

При работе подтверждать совместимость с текущим каноном. Уже имеющаяся корректная реализация имеет приоритет над предложенным названием файла/класса. Изменение замысла должно сохранять требуемый outcome, tests и traceability, а не просто помечаться «не нужно».

## 6. Неподтверждённые внешние возможности

Новые коммерческие разрешения Comss/Xbox DNS/dns.malw.link, текущая совместимость всех сервисов, доступность HAPP возможностей, независимость всех ASN, эффективность AWG против конкретных ТСПУ и production privacy/no-logs не установлены этой консолидацией. В планах они оставлены конкретными verification/decision gates, не заполнены предположениями.

Формулировки ETSI/CRA, безопасного стирания на SSD/flash и RAM-only/no-logs не означают соответствие стандарту или гарантию отсутствия данных. Нужны применимость, threat model, фактическое поведение и отдельный review. Этот пакет не является сертификатом, юридическим заключением или разрешением на рекламу.

## 7. Что проверено у самого пакета

Состав, внутренние ссылки, полный набор 83 IDs, граф зависимостей, исходные хеши и длина ready-to-paste goal проверяются структурно. Отчёт — [12_PACKAGE_VALIDATION.md](12_PACKAGE_VALIDATION.md). Его PASS относится к документам, не к POKROV binaries и не к release readiness.

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
