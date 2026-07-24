# Индекс доказательств

**Срез:** 2026-07-12<br>
**Инвентарь на момент архивации:** 11 аналитических отчётов, 29 профилей конкурентов, 170 PNG/JPG-скриншотов в датированных папках исследования и raw evidence.

## Метки

| Метка | Значение |
|---|---|
| `PASS_DIRECT` | Экран, ветка или метрика непосредственно проверены в авторизованном интерфейсе |
| `PASS_PUBLIC` | Данные прочитаны из публичной страницы, widget, store listing или канала |
| `INFERENCE` | Вывод из нескольких наблюдаемых сигналов; не выдаётся за прямой факт |
| `OWNER_ONLY` | TGStat требует подтверждение владения чужим каналом |
| `NOT_INDEXED` | Канал существует, но не индексируется TGStat |
| `BLOCKED_DOWNLOAD` | Официальный APK найден, но получить валидный бинарник не удалось |
| `PLAY_ONLY` | Первый-party APK доступен через Play; зеркало не использовалось |
| `REPORT_ONLY` | Использован ранее сохранённый статический отчёт без повторного бинарного прохода |
| `PAYMENT_NOT_COMPLETED` | Checkout просмотрен, но деньги не переводились |

## 11 отчётов

### 2026-07-08 — первый массовый проход

1. [Полное исследование bot/site/Web App](../../telegram-vpn-2026-07-08/full-bot-site-webapp-research.md)
2. [Детальные bot flows](../../telegram-vpn-2026-07-08/report.md)
3. [Публичная проверка TGStat](../../telegram-vpn-2026-07-08/tgstat-public-check.md)
4. [Вторая выборка первого прохода: Cats, Nosok, Platina, Quattro](../../telegram-vpn-2026-07-08/wave2-report.md)

### 2026-07-09 — углубление и APK

5. [Статический разбор Quattro, HiroVPN и ByeByeDPI](../../telegram-vpn-2026-07-09/apk-competitor-static-analysis.md)
6. [Финальное сравнение и gap-анализ POKROV](../../telegram-vpn-2026-07-09/final-competitor-comparison-and-pokrov-gap.md)
7. [Полный разбор Quattro bot/channel](../../telegram-vpn-2026-07-09/quattro-bot-channel-deep-dive.md)

### 2026-07-12 — авторизованный TGStat и расширение рынка

8. [Блокировки протоколов и Amnezia-group findings](../amnezia-group-protocol-blocking-findings-ru.md)
9. [Финальный отчёт первой выборки](../final-market-report.md)
10. [Русская итоговая сводка второй волны](../telegram-vpn-wave2-summary-ru.md)
11. [Bot/channel/APK technical appendix второй волны](../telegram-vpn-wave2-and-apk-analysis.md)

## 29 профилей

### Экосистемные и исходные конкуренты

- [Quattro](../../../../competitor-profiles/quattro-vpn.md)
- [Cats VPN](../../../../competitor-profiles/cats-vpn.md)
- [Nosok VPN](../../../../competitor-profiles/nosok-vpn.md)
- [VPN Platina](../../../../competitor-profiles/platina-vpn.md)
- [Luma VPN](../../../../competitor-profiles/luma-vpn.md)
- [4ebur](../../../../competitor-profiles/net4ebur.md)
- [ArtVPN](../../../../competitor-profiles/artvpn.md)
- [MORI](../../../../competitor-profiles/mori-vpn.md)
- [NEO](../../../../competitor-profiles/neo-vpn.md)
- [NashVPN](../../../../competitor-profiles/nashvpn.md)
- [Kosmos VPN](../../../../competitor-profiles/kosmos-vpn.md)
- [OpenGate](../../../../competitor-profiles/opengate-vpn.md)
- [GROZA](../../../../competitor-profiles/groza-vpn.md)
- [Fen VPN](../../../../competitor-profiles/fen-vpn.md)

### Вторая рыночная волна

- [HitVPN](../../../../competitor-profiles/hitvpn.md)
- [Shuka VPN](../../../../competitor-profiles/shuka-vpn.md)
- [Atlanta VPN](../../../../competitor-profiles/atlanta-vpn.md)
- [Batya VPN](../../../../competitor-profiles/batya-vpn.md)
- [Durev VPN](../../../../competitor-profiles/durev-vpn.md)
- [FineVPN](../../../../competitor-profiles/finevpn.md)
- [Sota VPN](../../../../competitor-profiles/sota-vpn.md)
- [Lagom VPN](../../../../competitor-profiles/lagom-vpn.md)
- [BlancVPN](../../../../competitor-profiles/blancvpn.md)
- [GenVPN](../../../../competitor-profiles/genvpn.md)

### Приложения и инструменты

- [HiroVPN](../../../../competitor-profiles/hiro-vpn.md)
- [ByeByeDPI](../../../../competitor-profiles/byebye-dpi.md)
- [OverSecure](../../../../competitor-profiles/oversecure.md)
- [Kubik VPN](../../../../competitor-profiles/kubik-vpn.md)
- [MantaRay](../../../../competitor-profiles/mantaray.md)

Общая нормализованная таблица: [competitor-profiles/_summary.md](../../../../competitor-profiles/_summary.md).

## Авторизованный TGStat

### Структурированные данные

- [Короткий JSON-срез 10 каналов](../../../../competitor-profiles/raw/market/2026-07-12/seo/tgstat-summary.json)
- [Глубокий JSON-срез: growth, reach, citation, daily deltas, attraction rows](../../../../competitor-profiles/raw/market/2026-07-12/seo/tgstat-deep.json)
- [Redacted ledger второй волны](../../../../competitor-profiles/raw/market-wave2/2026-07-12/scrapes/session-notes.md)

### Ограничения доступа

- [Демография доступна только владельцу](../../../../competitor-profiles/raw/market/2026-07-12/screenshots/tgstat-audience-owner-only.jpg)
- [Дневной лимит бесплатных запросов](../../../../competitor-profiles/raw/market/2026-07-12/screenshots/tgstat-free-query-limit.jpg)

### Полные экраны первой выборки

- [Quattro](../../../../competitor-profiles/raw/market/2026-07-12/screenshots/tgstat-quattro-full.jpg)
- [Cats](../../../../competitor-profiles/raw/market/2026-07-12/screenshots/tgstat-cats-full.jpg)
- [Nosok](../../../../competitor-profiles/raw/market/2026-07-12/screenshots/tgstat-nosok-full.jpg)
- [Platina](../../../../competitor-profiles/raw/market/2026-07-12/screenshots/tgstat-platina-full.jpg)
- [Luma](../../../../competitor-profiles/raw/market/2026-07-12/screenshots/tgstat-luma-full.jpg)
- [MORI](../../../../competitor-profiles/raw/market/2026-07-12/screenshots/tgstat-mori-full.jpg)
- [Nash](../../../../competitor-profiles/raw/market/2026-07-12/screenshots/tgstat-nash-full.jpg)
- [GROZA](../../../../competitor-profiles/raw/market/2026-07-12/screenshots/tgstat-groza-full.jpg)
- [OpenGate](../../../../competitor-profiles/raw/market/2026-07-12/screenshots/tgstat-opengate-full.jpg)
- [4ebur](../../../../competitor-profiles/raw/market/2026-07-12/screenshots/tgstat-net4ebur-full.jpg)

### Widgets второй выборки

- [HitVPN](../../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/tgstat-hitvpn-widget.png)
- [Shuka](../../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/tgstat-shuka-widget.png)
- [Atlanta](../../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/tgstat-atlanta-widget.png)
- [Sota](../../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/tgstat-sota-widget.png)
- [Batya](../../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/tgstat-batya-widget.png)
- [Lagom](../../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/tgstat-lagom-widget.png)
- [BlancVPN](../../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/tgstat-blanc-widget.png)
- [GenVPN](../../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/tgstat-genvpn-widget.png)
- [Durev](../../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/tgstat-durev-widget.png)

## Bot, Web App и сайты

Полный набор первого прохода хранится в:

- [screenshots](../../telegram-vpn-2026-07-08/screenshots/)
- [screenshots-wave2](../../telegram-vpn-2026-07-08/screenshots-wave2/)
- [screenshots-big](../../telegram-vpn-2026-07-08/screenshots-big/)

Безопасные contact sheets:

- [Основная выборка](../../telegram-vpn-2026-07-08/telegram-vpn-competitors-contact-sheet.png)
- [Финальная redacted выборка](../../telegram-vpn-2026-07-08/telegram-vpn-final-safe-contact-sheet.png)
- [TGStat public](../../telegram-vpn-2026-07-08/telegram-vpn-tgstat-public-contact-sheet.png)
- [Wave 2](../../telegram-vpn-2026-07-08/telegram-vpn-wave2-contact-sheet.png)

Ключевые Web App/screens:

- [Cats anonymous login](../../../../competitor-profiles/raw/cats-vpn/2026-07-12/screenshots/anonymous-code-login.jpg)
- [Cats redacted account concept](../../../../competitor-profiles/raw/cats-vpn/2026-07-12/screenshots/anonymous-code-concept-redacted.jpg)
- [Quattro payment](../../../../competitor-profiles/raw/quattro/2026-07-12/screenshots/site-payment.jpg)
- [Quattro instructions](../../../../competitor-profiles/raw/quattro/2026-07-12/screenshots/site-instructions.jpg)
- [HitVPN maintenance](../../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/hitvpn-bot-maintenance.png)
- [Shuka pricing](../../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/shuka-pricing.png)
- [Atlanta pricing](../../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/atlanta-pricing.png)
- [Batya pricing](../../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/batya-pricing.png)
- [Durev pricing](../../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/durev-pricing.png)
- [FineVPN official beta APK message](../../../../competitor-profiles/raw/finevpn/2026-07-12/screenshots/bot-official-beta-apk.png)

## Разобранные Android-приложения

| Приложение | Статус | SHA-256 / основание | Сохранённые экраны |
|---|---|---|---|
| Quattro 0.18.1 | `REPORT_ONLY` для этого среза | см. [APK report](../../telegram-vpn-2026-07-09/apk-competitor-static-analysis.md) | исходный статический отчёт |
| HiroVPN 1.17.1 | `REPORT_ONLY` | см. [APK report](../../telegram-vpn-2026-07-09/apk-competitor-static-analysis.md) | исходный статический отчёт |
| ByeByeDPI 1.7.6 | `REPORT_ONLY` | см. [APK report](../../telegram-vpn-2026-07-09/apk-competitor-static-analysis.md) | исходный статический отчёт |
| OverSecure 1.1.7 | downloaded + static + emulator | `F3FC3DD14F92EF0837501345B050F91FBE56940A36688C842277A10D9B0EE167` | [folder](../../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/) |
| Kubik 1.2.4 | downloaded + static + emulator | `65C9E93EA4117BCC3319F6CAD5EF372F3A3057E474387A71D5026DCF609FAB52` | [folder](../../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/) |
| MantaRay 2.25.8 | downloaded + static + emulator | `2DAA9D98A1E9D7B974974FD3F6E6BD820FD31D857D2B43F9C15EDE34E1148BEC` | [folder](../../../../competitor-profiles/raw/market-wave2/2026-07-12/screenshots/) |

Временные локальные пути последнего прохода:

- `%TEMP%\codex-vpn-wave2\oversecure\oversecure.apk`
- `%TEMP%\codex-vpn-wave2\kubik\kubik.apk`
- `%TEMP%\codex-vpn-wave2\mantaray\mantaray.apk`

Они не являются надёжным архивом и могут быть очищены системой. Доказательной базой считаются SHA-256, отчёт, профили и сохранённые скриншоты. APK не добавлены в репозиторий из-за размера, лицензирования и риска тащить сторонний бинарник в продуктовый Git.

## Не сохранено намеренно

- raw subscription URLs и конфигурации;
- QR-коды подключения;
- Telegram ID и персональные account codes;
- referral, payment и auth tokens;
- приватные ключи, checkout capability URLs и временные trial keys;
- диагностические payloads без redaction.

Это не потеря исследования, а обязательная граница безопасности.
