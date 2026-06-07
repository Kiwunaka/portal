# Support Macros

Last updated: 2026-06-07

## Source Of Truth

The code source for admin canned replies is
`shared/support-macros.ts`.

The admin ticket UI imports the same catalog through
`webapp/src/lib/support-macros.ts`. Do not add a second hardcoded
`ADMIN_REPLY_TEMPLATES` array inside admin pages.

Macros are beta-safe operator drafts. Operators may edit them before sending,
but they must keep these rules:

- do not ask users to send card data, private connection links, QR codes, raw
  configs, or secrets;
- do not point users to unofficial mirrors;
- do not imply store availability, trusted Windows signing, stable `1.0.0`,
  raw Android audit proof, production WARP proof, or RU-origin readiness;
- keep Telegram optional for first start and daily use;
- keep manual profile and QR wording as recovery/compatibility-only.

## Admin Macro Catalog

### `diagnostic_context` / `Данные`

Use when the issue lacks basic context.

Draft:

```text
Уточните, пожалуйста:

1. Устройство и версию системы.
2. Версию приложения POKROV.
3. На каком шаге возникла ошибка.
4. Текст ошибки или скриншот без личной ссылки и QR.
```

### `cannot_connect` / `Подключение`

Use for ordinary connection failures before escalating to node or API
diagnostics.

Draft:

```text
**Что попробовать:**
1. Обновите профиль в приложении.
2. Выберите другую локацию или авто-выбор.
3. Отключите другие сетевые клиенты.
4. Переподключитесь и напишите, что изменилось.
```

### `payment_or_key` / `Оплата`

Use for paid order, activation key, or redeem issues.

Draft:

```text
Проверим оплату или код вручную. Пришлите, пожалуйста, примерное время оплаты, выбранный срок, получили ли вы код доступа и где пробовали его активировать: в приложении или кабинете. Данные карты присылать не нужно.
```

### `download_not_visible` / `Файл`

Use when a beta file is not visible to the account.

Draft:

```text
Файл может быть доступен не всем аккаунтам beta сразу. Откройте кабинет: https://app.pokrov.space/ и проверьте раздел загрузок. Если файл не появился, ответьте здесь, и мы проверим доступ. Не используйте неофициальные зеркала.
```

### `windows_smartscreen` / `Windows`

Use when a Windows beta tester sees SmartScreen or unknown-publisher warnings.

Draft:

```text
Текущая Windows beta может показать предупреждение Microsoft Defender SmartScreen или неизвестного издателя. Если вы не ожидали beta-сборку, остановитесь и уточните источник у поддержки. Если вы одобренный тестер, используйте только файл из кабинета или поддержки.
```

### `telegram_bonus_missing` / `Бонус`

Use when Telegram `+10 days` did not apply.

Draft:

```text
Проверьте, пожалуйста: Telegram привязан к тому же аккаунту POKROV, вы подписаны на @pokrov_vpn, и проверка бонуса была запущена повторно в приложении или кабинете. Если бонус не появился, пришлите примерное время попытки.
```

### `manual_profile_safety` / `Профиль`

Use when a user asks for a QR, raw subscription link, or compatible-client
manual import.

Draft:

```text
Личная ссылка или QR нужны только для восстановления или совместимого клиента. В обычном пути POKROV подтягивает доступ сам после входа. Не отправляйте личную ссылку или QR в публичные чаты.
```

### `operator_escalation` / `Оператор`

Use when the case needs a manual operator or engineering check.

Draft:

```text
Передал обращение на ручную проверку. Оператор посмотрит историю и вернется с ответом в этом же треде.
```

## Engineering Escalation Template

Use this when handing a case to engineering:

```text
User issue:
Platform:
App version:
Account/session state:
Telegram linked:
Route mode:
Download/source used:
Payment/key state:
Last successful connect:
Observed error:
Current-origin evidence:
Brain-origin evidence:
RU-origin evidence:
Sensitive data redacted: yes
```
