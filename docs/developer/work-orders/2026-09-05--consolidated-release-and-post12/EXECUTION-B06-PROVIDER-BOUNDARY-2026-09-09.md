# B06 — доступность тестового режима LavaTop

Дата: 2026-09-09, current-origin. Проверен официальный
[FAQ о sandbox](https://developers.lava.top/en#is-there-a-sandbox-environment)
в браузере с раскрытым ответом. LavaTop сообщает об отсутствии sandbox и
предлагает проверку реальными платежами за недорогой контент. Swagger
«Try it out» сам по себе не является тестовой платёжной средой.

[Receipt](evidence/b06-provider-boundary-20260909/receipt.json) связывает
наблюдение с сохранённым screenshot. Это **PASS только проверки доступности
тестового режима**, не payment/refund/reconciliation E2E.

При действующем [бюджете $0](OWNER-DECISIONS-2026-09-09.md) новый платёж
для проверки B06 не выполняется. Refund ранее оплаченного реального заказа
также не является бесплатной тестовой операцией: провайдер описывает удержание
комиссии. Чужие и существующие клиентские платежи не используются как fixtures.
Новый invoice, charge, refund, dispute, обращение в поддержку и изменения
provider account/webhooks в этом срезе не создавались.

**B06 остаётся active / I3 / PARTIALLY_FIXED.** Локальные callback, ledger,
outbox и reconciliation проверки сохранены в [предыдущем отчёте](EXECUTION-B06.md)
и [проверке backend](EXECUTION-INTEGRATED-BACKEND-2026-09-08.md). Бесплатная
provider sandbox недоступна; полный E2E требует отдельного реального платёжного
сценария с допустимыми расходами и provider readback. Это фактическое внешнее
условие, а не повторный запрос разрешения на уже авторизованные действия.
Открытая зависимость B06 продолжает ограничивать полный parent
[B08](EXECUTION-B08-CURRENT-2026-09-09.md); его технические PASS сохранены.

Параллельный read-only readback O01 в 14:03:09 UTC подтвердил прежний живой
процесс, 29 успешных refreshes, ноль HTTP anomalies и неизменный absolute
deadline 23:37:16 UTC. Idle expiry уже PASS; absolute expiry ещё RUNNING,
новый процесс не запускался, TTL и время не менялись. Наблюдение сохранено
в receipt. Полный релиз остаётся открытым.

Проверки документации: 33 tests PASS; context audit PASS; package validator
83 R12 IDs / 528 links PASS; `git diff --check` PASS. Исходники продукта,
provider configuration, candidate и production deploy в этом срезе не менялись.
