# R12-B06 — payment, reversal и outbox

Дата: 2026-09-06. Результат: **I3 / PARTIALLY_FIXED**.
Source commit: `58e3684b9071921d289d009f6993385f2fa7b902`.
Команды, origins, SHA исходников и логов:
[evidence/b06-payments.json](evidence/b06-payments.json).

## Исправления по воспроизведённым ошибкам

1. Lava.top paid callback принимал `99.001` и строку `NaN` при цене заказа
   99 RUB. Проверка через float допускала дробную копейку, а сравнения с NaN
   обходили проверки диапазона. Оба API subtests дали FAIL со статусом paid.
   Теперь используется существующий Decimal parser: конечная положительная
   сумма, не более двух дробных знаков и точное равенство заказу. Неправильная
   сумма, валюта, отсутствие валюты и чужой plan остаются manual_review без
   grant/access key. Контрольные валидные Lava.top callbacks проходят.
2. Outbox recovery забирал просроченный claim у ещё активной dispatch
   transaction. Два реальных соединения PostgreSQL 16.15 воспроизвели
   `recovered=1` вместо 0. Dispatch и failure finalization теперь держат
   блокировку строки до commit/rollback; recovery использует `SKIP LOCKED`.
   После исправления — PASS: два backend PID, одна доставка, один provisioning
   job, один payment grant. Существующая stale recovery после брошенного claim,
   retry/dead-letter и rollback частичной записи сохранены.
3. Новый Lava.top envelope дедуплицировался по raw JSON hash: тот же event при
   другом порядке ключей создавал повторную запись. Оба refund/chargeback
   subtests дали FAIL. Теперь `event_id` входит в provider callback identity.
   При отсутствии order binding result endpoint отвечает `manual_review`,
   сохраняет redacted receipt и не создаёт order/grant/key. Это не выполненная
   финансовая сверка и не автоматически созданное order-specific обращение.

## Что покрыто локально

| Критерий B06 | Текущее доказательство |
| --- | --- |
| Auth, replay, duplicate, mismatch | Обязательный payment/auth suite: 125 PASS, 14 subtests; финальный Lava.top subset после изменения amount validation: 22 PASS, 8 subtests |
| Amount/currency/plan | Шесть API cases: wrong amount, fractional kopeck, NaN, wrong currency, missing currency, wrong plan; все остановлены без fulfillment |
| Частичное fulfillment и повтор | Existing callback/claim tests: сбой durable fulfillment и email delivery, replay, сохранение snapshot, отсутствие второго grant/key |
| Outbox | 46 claims/outbox/runtime checks PASS; отдельный PostgreSQL race PASS; 2 downstream provisioning checks PASS, включая reversed grant deny |
| Refund/chargeback | Existing flat signed callback fixtures подтверждают reversal и replay; 2 новых envelope subtests подтверждают только receipt/dedupe/manual-review boundary |
| Reconciliation | 3 admin payment API tests PASS: intent-bound, duplicate-safe, atomic repair и audit; provider dashboard не использован |

Все provider/email/panel ответы в API tests — fixtures. Реальный PostgreSQL
использует только loopback `r12_checkout_rehearsal` и отдельные случайные
schemas, сохранённые после проверки. Его наличие не превращает provider
fixtures в provider sandbox. Повтор whole-suite не подменяется подсчётом
subtests: точные команды и момент финальных source changes записаны в evidence.

## Проверка актуального provider contract

[Документация Lava.top](https://developers.lava.top/en), прочитанная 2026-09-06,
описывает новый reversal envelope отдельно от старого payment payload. В
показанных примерах нет local order ID/original contract ID; из них нельзя
вывести однозначную связь с заказом. Полный и частичный refund также нельзя
считать одним и тем же entitlement/revenue переходом. Нужны provider evidence
и проверяемая reconciliation path; поиск заказа по email/product/amount не
добавлялся. Наличие отдельного provider sandbox этим этапом не подтверждено.

## Незакрытые gates

- Controlled provider sandbox или отдельно разрешённый live payment/refund,
  provider dashboard readback и сверка с конкретным ledger: **MANUAL_OWNER_TEST**.
- Доставка новых reversal events в production, точная order binding и
  partial-refund policy/path: **NEEDS_RUNTIME_PROOF / NEEDS_CONTEXT**.
- B08 restore/migrations/deploy/rollback: **OPEN**. Один outbox concurrency case
  не доказывает всю B08 matrix.
- Новые candidate, публикация, signing, production DB mutation, расходы,
  refunds, push, merge и deploy: **NOT_REQUESTED / не выполнялись**.

Client/Core, retained candidate.33 и публичный release index не изменены.
Локальная проверка не закрывает B06 целиком и не меняет readiness текущей beta.
