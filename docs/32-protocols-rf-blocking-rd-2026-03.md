# Протоколы и обход блокировок в РФ: R&D (2026-03)

Обновлено: 4 марта 2026

## 1. Краткий вывод
- Основной production-протокол можно оставлять `VLESS + REALITY`, но нужен резервный контур.
- На практике у провайдеров уже встречаются кейсы, где поведение `XTLS/VLESS` и высокие концентрации соединений на один IP ухудшают доступность.
- Самый реалистичный резерв на ближайший релиз: `Hysteria2` (UDP-oriented) + аккуратный canary rollout.
- Для CDN/HTTP-маскировки имеет смысл отдельный трек с `XHTTP`, но только после совместимости с клиентской экосистемой.

## 2. Что известно по VLESS Reality и блокировкам

### 2.1 Сигналы из сообщества и трекеров
- В community-трекерах net4people есть обсуждения о нестабильности доступности и блокировках в РФ (`Issue #546`, открыта 6 мая 2024; `Issue #490`, 11 июля 2024).
- В Xray issue-трекере есть кейсы, связанные с транспортом `XHTTP` и деградациями/регрессиями:
  - `#4846` (opened 26 Oct 2024): packet-down проблемы.
  - `#5460` (opened 30 Sep 2025, closed): packet-up проблема совместимости со старым behavior.

Вывод (инференс): filtering уже не сводится к «просто порт/IP», важны транспортные паттерны и клиентская версия.

## 3. Сравнение протоколов

## 3.1 VLESS + REALITY
Плюсы:
- Сильная интеграция в Xray/3x-ui стек.
- Хорошая производительность на TCP.
- Наработанная операционная база в текущем проекте.

Риски:
- При массовом однотипном профиле трафика и высоком fan-in на один IP заметнее для активного анализа.
- Нужен регулярный update policy (Xray core + transport defaults).

## 3.2 Hysteria2
Плюсы:
- UDP-транспорт и иной сетевой профиль относительно VLESS/TCP.
- Официальные docs и быстрые релизы (например, v2.6.4 от 31 Jan 2026).

Риски:
- UDP может блокироваться/деградировать у части операторов.
- Требуется отдельная клиентская поддержка и обучение пользователей.

## 3.3 Shadowsocks-2022
Плюсы:
- Формально стандартизованный профиль (SIP022).
- Широкая клиентская поддержка по экосистеме Shadowsocks.

Риски:
- Как standalone-решение часто уступает гибкости Xray-транспортов для сложных DPI-сценариев.
- Потребуются отдельные policy/limits и troubleshooting-playbook.

## 3.4 XHTTP / CDN-proxying
Плюсы:
- Дополнительный слой маскировки через HTTP-подобные паттерны.
- В Xray/XTLS ветке идет активное развитие transport-поведения (packet-up/packet-down).

Риски:
- Совместимость клиентов неравномерная (в публичных гайдах отдельно отмечают, что xhttp не везде поддержан).
- Нужен аккуратный rollout и version-gating на клиентах.

## 4. Рекомендуемая staged-стратегия

### Stage 0 (сейчас)
- Оставляем `VLESS+REALITY` как primary.
- Включаем авто-детект блокировок ноды (раздел 6).

### Stage 1 (canary 5-10%)
- Добавляем `Hysteria2` на 1-2 paid ноды.
- Выдаем только canary-группе пользователей через отдельный campaign/start-link.
- Сравниваем success-rate подключения и retention с control-группой.

### Stage 2 (25-40%)
- Расширяем HY2 на все paid-регионы.
- Подключаем fallback policy в WebApp/боте: если primary-connect fail N раз, предлагаем резервный профиль.

### Stage 3 (production backup)
- Для каждого paid-региона: минимум 1 primary profile (REALITY) + 1 backup profile (HY2).
- Отдельный трек для `XHTTP` только после стабилизации клиентского парка.

## 5. Risk matrix

- `R1`: массовая деградация VLESS/REALITY на части провайдеров.
  - Вероятность: средняя.
  - Влияние: высокое.
  - Митигатор: HY2 backup + быстрый traffic-shift.

- `R2`: блокировка/ограничение UDP (влияет на HY2).
  - Вероятность: средняя.
  - Влияние: среднее.
  - Митигатор: держать REALITY как рабочий fallback.

- `R3`: несовместимость клиентов по XHTTP.
  - Вероятность: высокая.
  - Влияние: среднее.
  - Митигатор: version-gated rollout + явная совместимость в UI.

## 6. Авто-детект «нода заблокирована»

Рекомендуемый алгоритм (складывается из локальных метрик + внешних проб):

1. Каждые 5 минут synthetic-probe из 2-3 внешних vantage points:
- TCP connect,
- TLS handshake latency,
- success/fail ratio.

2. Внутренние сигналы (из `node_health_samples` и panel):
- резкий рост `panel_error_rate`,
- падение `active_clients` при стабильном общем трафике кластера,
- stop-growth у `total_up/down_bytes` при ожидаемом прайм-тайме.

3. Правило инцидента `node_block_suspected`:
- `probe_fail_rate >= 0.6` 15 минут подряд
  ИЛИ
- `probe_fail_rate >= 0.4` + `active_clients` падение > 50% за 30 минут.

4. Автодействия:
- понизить weight/disable ноды,
- перевести новых пользователей на другие ноды,
- отправить alert в админ-канал + тикет runbook.

## 7. Что делать сейчас в проекте

1. Добавить HY2 как резервный профиль на 1 регионе (canary).
2. В admin dashboard вывести метрику `connect_success_rate` по ноде/протоколу.
3. Добавить status-page для internal ops: `blocked_suspected` / `degraded` / `healthy`.
4. Обновлять Xray до актуальных релизов по rolling policy (не реже 1 раза в 2-4 недели с canary).

## 8. Источники (с датами и ссылками)

### Официальная документация / primary
- Xray-core releases (актуальные ветки релизов, в выдаче есть v25.10.15 от 15 Oct 2025):
  - https://github.com/XTLS/Xray-core/releases
- XTLS XHTTP transport docs:
  - https://xtls.github.io/ru/config/transports/xhttp.html
- Xray issue #4846 (opened 26 Oct 2024):
  - https://github.com/XTLS/Xray-core/issues/4846
- Xray issue #5460 (opened 30 Sep 2025, closed):
  - https://github.com/XTLS/Xray-core/issues/5460
- Xray issue #4176 (XHTTP latency/perf context):
  - https://github.com/XTLS/Xray-core/issues/4176
- Hysteria2 overview docs:
  - https://v2.hysteria.network/docs/getting-started/Overview/
- Hysteria release `app/v2.6.4` (31 Jan 2026):
  - https://github.com/apernet/hysteria/releases/tag/app%2Fv2.6.4
- Shadowsocks 2022 spec (SIP022):
  - https://shadowsocks.org/doc/sip022.html
- Cloudflare post-quantum to origins (added/updated June 2025):
  - https://blog.cloudflare.com/post-quantum-to-origins/

### Community signals (использовать как дополнительный сигнал, не как единственный источник)
- net4people issue #546 (6 May 2024):
  - https://github.com/net4people/bbs/issues/546
- net4people issue #490 (11 Jul 2024):
  - https://github.com/net4people/bbs/issues/490
- ntc.party thread "protocols and methods bypassing censorship" (started by r2do92, 6 May 2024):
  - https://ntc.party/t/protocols-and-methods-for-bypassing-censorship
- ntc.party thread "still no answer for what happened in Russia" (6 Jul 2024):
  - https://ntc.party/t/still-no-answer-for-what-happened-in-russia
- Reddit (эксплуатационные кейсы):
  - HY2 thread (published 4 Jun 2024, UTC): https://www.reddit.com/r/selfhosted/comments/1dbjzxy/yet_another_vpn_protocol_hysteria2/
  - GFW + HY2 case (published 6 Aug 2024, UTC): https://www.reddit.com/r/Piracy/comments/1el7696/getting_around_great_firewall_china_gfw_using/
  - China firewall bypass thread (published 3 Sep 2024, UTC): https://www.reddit.com/r/chineselanguage/comments/1f8ef8k/bypass_chinas_great_firewall_for_chinese_resident/
- Habr article about XHTTP (published 30 Nov 2024):
  - https://habr.com/ru/articles/863270/

---

Примечание: выводы по приоритету `REALITY primary + HY2 backup` являются инженерной рекомендацией на 4 марта 2026 на основе текущих источников и практической операционной модели проекта.
