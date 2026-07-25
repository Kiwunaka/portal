# Архив исследования Telegram VPN

**Срез:** 2026-07-12<br>
**Окно постов:** 2026-05-12 — 2026-07-12<br>
**Назначение:** внутренняя конкурентная разведка POKROV<br>
**Статус:** `EVIDENCE / ADVISORY`; не заменяет канонические продуктовые документы POKROV

Эта папка — единая точка входа в исследование. Она не переписывает исходные отчёты, а связывает их, фиксирует числовой набор для инфографики и отделяет прямые наблюдения от аналитических выводов.

## Что сохранено

| Файл | Назначение |
|---|---|
| [master-dossier-ru.md](master-dossier-ru.md) | Единая русская сводка: рынок, рост, маркетинг, приток, сильные/слабые стороны и выводы для POKROV |
| [market-metrics.csv](market-metrics.csv) | Плоская таблица 19 каналов для Excel, графиков и повторного анализа |
| [infographic-data.json](infographic-data.json) | Машиночитаемый источник готовых инфографик: метрики, оценки, оговорки и POKROV benchmark |
| [evidence-index.md](evidence-index.md) | Карта 11 отчётов, 29 профилей, 170 скриншотов и APK-артефактов |
| [POKROV-telegram-vpn-competitors-2026-07-12.xlsx](../../../../outputs/vpn-competitor-research-20260713/POKROV-telegram-vpn-competitors-2026-07-12.xlsx) | Проверенная Excel-книга: dashboard, source metrics, marketing analysis, app audit и methodology |

## Готовые инфографики

| Материал | PNG | Редактируемый HTML |
|---|---|---|
| Аналитический отчёт | [01-analytical-report.png](../infographics/01-analytical-report.png) | [01-analytical-report.html](../infographics/01-analytical-report.html) |
| War room | [02-war-room.png](../infographics/02-war-room.png) | [02-war-room.html](../infographics/02-war-room.html) |
| Growth funnel | [03-growth-funnel.png](../infographics/03-growth-funnel.png) | [03-growth-funnel.html](../infographics/03-growth-funnel.html) |

Размеры, SHA-256 PNG и hash исходного dataset сохранены в [manifest.json](../infographics/manifest.json).

## Главные исходные отчёты

- [Финальный проход первой выборки](../final-market-report.md) — боты, сайты, Web App, TGStat, контент, APK и рекомендации.
- [Русская сводка второй волны](../telegram-vpn-wave2-summary-ru.md) — HitVPN, Shuka, Atlanta, Batya, Durev, FineVPN, дополнительные каналы и приложения.
- [Техническое приложение второй волны](../telegram-vpn-wave2-and-apk-analysis.md) — полные bot-flow, двухмесячный контент-аудит и статический/UI-анализ OverSecure, Kubik и MantaRay.
- [Сводка всех профилей](../../../../competitor-profiles/_summary.md) — 29 нормализованных карточек конкурентов.

## Правила интерпретации

1. Telegram subscribers, рост канала, ERR и охват не равны платящим клиентам, выручке или VPN MAU.
2. Bot MAU — Telegram-показатель месячных пользователей бота, а не число активных подписок.
3. Демография, география и полный источник роста чужих каналов в TGStat недоступны даже после авторизации: `OWNER_ONLY`.
4. Оценка маркетинговой агрессивности — аналитическая шкала, а не метрика TGStat. В JSON рядом с ней хранится основание и уверенность.
5. Luma — отдельный proxy/repost-класс. ERR 638.5% и охват выше базы нельзя сравнивать с обычным каналом.
6. Публичные widgets второй волны не дали полного source-of-growth. Источники притока там помечены как выводы, если нет прямого подтверждения.
7. Ни одна оплата конкурентам не выполнялась. Персональные ключи, referral URLs, payment tokens, Telegram ID и raw subscription links не сохранены.

## Быстрый вывод

- Максимальный абсолютный рост: HitVPN, `+386 200` за 30 дней.
- Максимальный относительный обычный app-backed рост во второй волне: Sota `+15.3%`, Lagom `+15.1%`.
- Максимальный относительный рост первой выборки: Cats `+94%`; Luma `+199.7%` исключён из обычного сравнения как proxy/repost anomaly.
- Самые агрессивные доказанные модели: HitVPN, Atlanta и Batya.
- Самая чистая продуктовая коммуникация: BlancVPN.
- Лучший power-user Android UX из разобранных: MantaRay.
- Самый опасный release/privacy-контур из разобранных: Kubik.
- Окно POKROV: app-first вход, честный trial без карты, необязательный Telegram и нормальное восстановление; главный дефицит — собственная машина дистрибуции и store reach.

## Обновление среза

Новый проход должен создаваться отдельной датированной папкой. Значения 2026-07-12 не перезаписывать: они нужны для сравнения динамики.
