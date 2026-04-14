# Передача для настройки email-доставки через webhook

Last updated: 2026-04-15

## Зачем нужен этот файл

Используйте эту инструкцию перед тем, как считать регистрацию, подтверждение email и восстановление пароля реально рабочими в проде.

Сейчас backend отправляет письма не напрямую через SMTP, а через webhook. Если webhook или отправитель не настроены, публичный email auth считается заблокированным.

## Что backend ожидает увидеть

Текущие настройки:

- `EMAIL_AUTH_WEBHOOK_URL`
- `EMAIL_AUTH_WEBHOOK_TIMEOUT_SECONDS`
- `EMAIL_AUTH_TOKEN_SECRET`
- `EMAIL_AUTH_DEBUG_ECHO`

Правило для продакшена:

- если ожидается настоящая отправка писем, `EMAIL_AUTH_DEBUG_ECHO` не должен оставаться включённым

Что backend шлёт в webhook:

- `kind`
- `email`
- `token`
- `linked_tg_id`

Типы писем сейчас:

- `verify`
- `reset`

## Когда сразу останавливаемся

Сразу считаем email auth заблокированным, если нет хотя бы одного пункта:

- реального отправителя для `noreply@pokrov.space`
- рабочего `EMAIL_AUTH_WEBHOOK_URL`
- webhook-обработчика, который принимает JSON и реально отправляет письмо
- живого почтового ящика для теста
- подтверждения, что и verify, и reset письма доходят

## Что нужно получить от вас

Передайте:

- production webhook URL
- какой сервис реально будет отправлять письма от `noreply@pokrov.space`
- кто владелец или администратор этого отправителя
- хотя бы один тестовый ящик, куда можно проверить доставку
- подтверждение, что email auth уже пора включать публично

Не присылайте секреты провайдера в git или markdown.

## Что делать по шагам

1. Проверьте, что отправитель `noreply@pokrov.space` реально подтверждён у почтового провайдера.
2. Проверьте, что `EMAIL_AUTH_WEBHOOK_URL` прописан в runtime env на `brain`.
3. Проверьте, что `EMAIL_AUTH_DEBUG_ECHO` выключен.
4. Проверьте, что `EMAIL_AUTH_TOKEN_SECRET` существует.
5. Запустите живой сценарий отправки verify-письма.
6. Запустите живой сценарий отправки reset-письма.
7. Убедитесь, что webhook отвечает успешно и оба письма реально приходят во входящий ящик.
8. Если письма не доходят, сразу отмечайте email auth как blocked. Не называйте релиз готовым.

## Что обязательно нужно доказать

Нужно подтвердить все пункты:

- регистрация может отправить verify email
- verify email доходит
- восстановление пароля может отправить reset email
- reset email доходит
- проблемы доставки не путаются с node-проблемами или routing-проблемами

## Что нужно прислать мне обратно

Пришлите:

- домен или host webhook URL
- подтверждение, что `EMAIL_AUTH_DEBUG_ECHO` был выключен
- подтверждение, что отправитель был именно `noreply@pokrov.space`
- один зацензуренный пример verify-письма
- один зацензуренный пример reset-письма
- время живой проверки
- итог для доставки: `sent`, `delivery_error` или `not_configured`

Подойдут такие доказательства:

- события в панели провайдера
- application logs без личных данных
- скриншоты пришедших verify и reset сообщений

## Частые причины блокировки

- `EMAIL_AUTH_WEBHOOK_URL` не задан
- включён `EMAIL_AUTH_DEBUG_ECHO=true`
- отправитель не подтверждён у провайдера
- webhook отвечает `400+`
- письмо так и не доходит до inbox
- оператор принимает email-проблему за сетевую или node-проблему

## Связанные инструкции

- [Monitoring And Visibility](C:/Users/kiwun/Documents/ai/VPN/docs/operations/monitoring-and-visibility.md)
- [Передача по финальным ссылкам и релизному handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/release-links-and-final-handoff.md)
- [Deployment And Access](C:/Users/kiwun/Documents/ai/VPN/docs/operations/deployment-and-access.md)
