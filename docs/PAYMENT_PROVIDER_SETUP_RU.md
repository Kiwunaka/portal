# Подключение касс PORTAL

Обновлено: 7 марта 2026

## Что это за документ

Это текущий source of truth по рублёвым кассам:
- какие провайдеры поддерживаются кодом;
- какие URL указывать в кабинете кассы;
- какие env нужны на `brain`;
- как включать и выключать провайдеров без переписывания кода.

## Текущая схема

- `PORTAL` создаёт `ExternalOrder` и решает, через какого провайдера вести платёж.
- Checkout и бот получают список доступных касс из `/api/payments/providers`.
- Callback, refund и chargeback идут в единый контур `portal_bot/api.py`.
- FreeKassa оставлена только как legacy fallback.
- Основной путь на будущее: несколько провайдеров с переключением через env.

## Общие URL

Базовый сайт:
- `https://portal-privacy.online`

Логотип:
- `https://portal-privacy.online/portal-logo.svg`

Успешная оплата:
- `https://kiwunaka.space/pay/success`

Неуспешная оплата:
- `https://kiwunaka.space/pay/fail`

## Paypalich / Pally

Документация:
- [pally.info/reference/api](https://pally.info/reference/api)

Поля магазина:
- `URL магазина`: `https://portal-privacy.online`
- `Success URL`: `https://kiwunaka.space/pay/success?provider=pally`
- `Fail URL`: `https://kiwunaka.space/pay/fail?provider=pally`
- `Result URL`: `https://kiwunaka.space/api/payments/result/pally`
- `Refund URL`: `https://kiwunaka.space/api/payments/refund/pally`
- `Chargeback URL`: `https://kiwunaka.space/api/payments/chargeback/pally`

Env:
- `PALLY_API_BASE_URL=https://pally.info/api/v1`
- `PALLY_API_TOKEN=...`
- `PALLY_SHOP_ID=...`

## Platima

Документация:
- [platima.com/docs](https://platima.com/docs/)

Поля проекта:
- `URL адрес логотипа`: `https://portal-privacy.online/portal-logo.svg`
- `URL адрес для уведомлений`: `https://kiwunaka.space/api/payments/result/platima`

Redirect URL:
- `success_url`: `https://kiwunaka.space/pay/success?provider=platima`
- `fail_url`: `https://kiwunaka.space/pay/fail?provider=platima`

Env:
- `PLATIMA_API_BASE_URL=https://platima.com/api/v1`
- `PLATIMA_PROJECT_ID=...`
- `PLATIMA_API_KEY_PROJECT=...`
- `PAYMENT_LOGO_URL=https://portal-privacy.online/portal-logo.svg`

## Cardlink

Документация:
- [cardlink.link/reference/api](https://cardlink.link/reference/api)

Поля проекта:
- `URL магазина`: `https://portal-privacy.online`
- `Success URL`: `https://kiwunaka.space/pay/success?provider=cardlink`
- `Fail URL`: `https://kiwunaka.space/pay/fail?provider=cardlink`
- `Result URL`: `https://kiwunaka.space/api/payments/result/cardlink`
- `Refund URL`: `https://kiwunaka.space/api/payments/refund/cardlink`
- `Chargeback URL`: `https://kiwunaka.space/api/payments/chargeback/cardlink`

Env:
- `CARDLINK_API_BASE_URL=https://cardlink.link/api/v1`
- `CARDLINK_API_TOKEN=...`
- `CARDLINK_SHOP_ID=...`

## FreeKassa

Статус:
- legacy fallback;
- использовать только как резервную совместимость, пока новые кассы не включены полностью.

Документация:
- [docs.freekassa.com](https://docs.freekassa.com/)

Notify:
- `https://kiwunaka.space/api/payments/freekassa/notify`

Env:
- `FK_SITE_SHOP_ID=...`
- `FK_SITE_API_KEY=...`
- `FK_SITE_SECRET_WORD_1=...`
- `FK_SITE_SECRET_WORD_2=...`
- `FK_BOT_SHOP_ID=...`
- `FK_BOT_API_KEY=...`
- `FK_BOT_SECRET_WORD_1=...`
- `FK_BOT_SECRET_WORD_2=...`
- `FREEKASSA_PAY_HOST=pay.fk.money`

## Включение и выключение провайдеров

Порядок показа:
- `RUB_PAYMENT_PROVIDER_ORDER=cardlink,pally,platima,freekassa`

Разрешённые провайдеры:
- `RUB_PAYMENT_PROVIDER_ENABLED=cardlink,pally,platima,freekassa`

Как это работает:
- если провайдер есть в `ORDER`, но для него нет секретов, он не показывается;
- если провайдер настроен, но убран из `ENABLED`, он тоже не показывается;
- bot, marketing checkout и backend используют один и тот же catalog.

## Как добавить новую кассу дальше

1. Добавить provider meta и create/callback adapter в `portal_bot/payment_providers.py`.
2. Прописать env в `portal_bot/.env.example`.
3. Добавить provider в `RUB_PAYMENT_PROVIDER_ORDER`.
4. Настроить callback URLs в кабинете провайдера.
5. Прогнать smoke:
   - `/api/payments/providers`
   - create-public
   - callback result
   - success/fail redirect
   - bot tariff -> provider -> payment link

## Что проверил

- сверил актуальные API entrypoints провайдеров;
- зафиксировал единые callback/redirect URL для `brain`;
- добавил логотип в публичную статику сайта.

## Что нашёл

- FreeKassa не годится как основной путь для карт/СБП, если нужен checkout без FKWallet;
- текущий проекту нужен provider-agnostic workflow, а не привязка к одной кассе;
- для следующих провайдеров достаточно менять env и включение в catalog.

## Что изменил

- добавил multi-provider runbook;
- зафиксировал URL и env matrix;
- вынес логотип в публичный static path.

## Что осталось / риск

- без реальных токенов новых касс нельзя сделать финальный боевой smoke по живой оплате;
- перед включением каждого нового провайдера нужен отдельный ручной callback smoke.
