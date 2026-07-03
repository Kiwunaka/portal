# МЕГА МОНСТР ПЛАН.md — POKROV VPN: capacity-aware smart-connect, subscription steering, fair-use telemetry

> Единый большой prompt/план доработок для репозиториев `Kiwunaka/portal` и `Kiwunaka/POKROV-app`.
> Не делить на «этапы» в продуктовой логике. Делать как один большой scope: backend/control-plane, node agents, subscription renderer, app-client smart-connect, observability, tests, rollout switches, rollback.
> Главная идея: **не пытаться посчитать “активных людей/устройства” там, где это технически недостоверно**. POKROV сейчас отдаёт подписки, которые пользователь может импортировать в любые клиенты: Hiddify, Happ, Karing, v2rayN, sing-box clients, Nekobox, Shadowrocket-like клиенты и т.д. Поэтому один ключ может быть использован семьёй, несколькими устройствами или вообще шариться. Система должна управлять нагрузкой и качеством по **ключу, трафику, IP/ASN-отпечаткам, насыщению нод, RTT и health**, а не по фейковому `active_users`.

---

## 0. Абсолютная формулировка задачи

Нужно превратить текущий POKROV smart-connect из “список нод + немного health + sticky hint” в **capacity-aware control-plane**, который:

- работает и для собственного POKROV-app;
- работает для внешних клиентов через subscription URL;
- не требует точного подсчёта активных устройств;
- не ломает пользователей, которые сидят в Hiddify/Happ/прочих клиентах;
- умеет не перегружать 1 Gbit ноды;
- умеет мягко ограничивать/перенаправлять “тяжёлые” ключи без тупого бана;
- умеет отличать “семья использует ключ” от “ключ улетел в публичный слив” только вероятностно;
- даёт оператору понятную картину: какая нода горит, какой ключ давит сеть, какой пул надо разгрузить, где проблема с маршрутом;
- не полагается на `active_clients` из панели как на `online users`;
- не считает `UserNode` mapping финальной правдой выбора ноды;
- не делает агрессивные reconnect/switch, потому что VPN-клиенты, особенно сторонние, живут по своим правилам.

---

## 1. Техническая правда, от которой нельзя уходить

### 1.1. “Активный пользователь” в универсальной подписке — недостоверная сущность

Для подписки, которую человек импортировал в любой клиент, backend не контролирует клиентский runtime. Он не знает:

- сколько устройств реально используют один UUID;
- один это человек с телефоном + ноутбуком или десять человек;
- сколько “активных клиентов” в данный момент держат именно пользовательские туннели;
- какие клиенты поддерживают автоматический выбор ноды;
- как часто клиент обновляет подписку;
- как клиент сортирует ноды;
- как клиент кеширует subscription;
- применяет ли клиент selector/urltest;
- умеет ли клиент отдавать тебе RTT;
- переподключится ли клиент после изменения подписки.

Поэтому точный `online_users_now` на уровне аккаунта невозможен как строгая бизнес-метрика. Нужно заменить его на несколько честных, измеримых сигналов:

```text
key_traffic_bps
key_traffic_bytes_window
key_distinct_source_ips_window
key_distinct_asns_window
key_distinct_countries_window
key_nodes_seen_window
key_parallel_node_pressure
key_connection_churn
node_tx_mbps
node_packet_loss
node_tcp_retransmits
node_cpu_softirq
node_health_score
node_capacity_score
client_rtt_samples
subscription_fetch_behavior
```

### 1.2. `active_clients` из панели нельзя использовать как online

Текущий collector берёт `active_clients = len(clients)` из inbound settings. Это количество заведённых клиентов/ключей на inbound, а не online users. Это можно хранить как `provisioned_clients_count`, но нельзя использовать для балансировки как текущую нагрузку.

Нужно переименовать/развести:

```text
active_clients             -> оставить только как legacy/compat, не использовать в capacity
provisioned_clients_count  -> сколько ключей заведено на ноде
online_connections_hint    -> если есть достоверный источник
source_ip_count_5m         -> сколько разных IP видели по логам/observer
key_pressure_score         -> нагрузка ключа, не количество людей
node_capacity_pressure     -> давление ноды
```

### 1.3. Основной bottleneck для Xray/VLESS Reality при 100+ активных — сеть

У тебя 1 Gbit ноды. Реальный лимит наступает не когда CPU 90%, а когда:

- `tx_mbps_1m` стабильно > 700–800 Mbps;
- `tx_mbps_5m` стабильно > 650–750 Mbps;
- появляются retransmits/drop/loss;
- растёт latency/jitter;
- shared hoster начинает душить;
- нода входит в вечерний oversubscription.

CPU и RAM нужны, но для твоей модели главный ресурс — **egress capacity**.

---

## 2. Внешние технические опоры

Использовать только как источник фактов/возможностей, не как магию.

### Xray

Xray `stats` включает внутреннюю статистику, а при включённых policy-счётчиках можно получать user traffic вида `user>>>[email]>>>traffic>>>uplink/downlink`; если у пользователя нет email, user-stat не включится. Это важно: **email/label ключа должен быть обязательным техническим идентификатором**, даже если публично он не показывается.

Xray `metrics` может слушать локальный адрес и отдавать `/debug/vars`; там есть `stats` по inbound/outbound/user и `observatory`, то есть можно строить collector без скрейпинга панели как единственного источника.

Xray API `HandlerService` умеет добавлять/удалять пользователей для VMess/VLESS/Trojan/Shadowsocks, а `StatsService` отдаёт встроенную статистику. Значит provisioner должен уметь работать не только через 3x-ui panel, но и через Xray API там, где это возможно.

Xray `observatory`/`burstObservatory` делает HTTPing outbound-состояния; его можно использовать как дополнительный сигнал health, но не как единственный сигнал доступности для реального пользователя.

### sing-box

sing-box `urltest` умеет тестировать список outbounds, имеет `url`, `interval`, `tolerance`, `idle_timeout` и `interrupt_exist_connections`. По умолчанию при пустом URL используется `https://www.gstatic.com/generate_204`, interval — `3m`, tolerance — `50ms`.

sing-box `selector` задаёт список outbounds и default outbound, но важный нюанс: selector currently controllable through Clash API. Нельзя рассчитывать, что все сторонние клиенты будут управлять selector так, как твой POKROV-app.

Следствие для POKROV: для собственного app можно делать полноценный smart-connect, а для внешних подписок нужно делать **subscription steering**: порядок нод, состав нод, формат, кеширование, naming, TTL, отдельные пулы.

---

## 3. Главный архитектурный принцип

Не строить “device limit enforcement” на недостоверном online. Строить **account/key fairness**.

Правильные сущности:

```text
Account         = платёжная/пользовательская сущность
AccessKey       = технический UUID/email/key, которым реально ходят в Xray
Subscription    = URL/token, по которому внешний клиент получает конфиг
Node            = VPS/edge node
Pool            = логическая группа нод: premium, free, fair-use, drain, canary
KeyPressure     = насколько ключ давит сеть
NodeCapacity    = насколько нода близка к пределу
AssignmentHint  = рекомендация control-plane, куда вести ключ
SubscriptionView = конкретный отрендеренный список нод для token/client format
```

Не пытаться “доказать, что там мама/папа/бабушка”. Вместо этого:

- дать нормальный family-friendly допуск;
- ловить только явные перегрузы/аномалии;
- тяжелые ключи переводить в fair-use поведение;
- не ломать платящего пользователя из-за мобильного CGNAT/смены IP;
- показывать оператору причины.

---

## 4. Новый словарь данных

Добавить в backend понятные доменные сущности.

### 4.1. `node_capacity_policy`

Описывает физические возможности ноды и operator knobs.

```sql
CREATE TABLE node_capacity_policy (
    id SERIAL PRIMARY KEY,
    node_code VARCHAR(32) UNIQUE NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    capacity_mbps INTEGER NOT NULL DEFAULT 1000,
    soft_tx_ratio FLOAT NOT NULL DEFAULT 0.70,
    drain_tx_ratio FLOAT NOT NULL DEFAULT 0.80,
    hard_tx_ratio FLOAT NOT NULL DEFAULT 0.90,

    soft_cpu_percent FLOAT NOT NULL DEFAULT 70.0,
    drain_cpu_percent FLOAT NOT NULL DEFAULT 82.0,
    hard_cpu_percent FLOAT NOT NULL DEFAULT 90.0,

    max_retrans_percent FLOAT NOT NULL DEFAULT 4.0,
    max_packet_loss_percent FLOAT NOT NULL DEFAULT 2.0,

    min_health_score FLOAT NOT NULL DEFAULT 60.0,
    stale_after_seconds INTEGER NOT NULL DEFAULT 180,

    premium_weight INTEGER NOT NULL DEFAULT 100,
    free_weight INTEGER NOT NULL DEFAULT 10,
    fair_use_weight INTEGER NOT NULL DEFAULT 40,

    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);
```

### 4.2. `node_runtime_metrics`

Это не замена `NodeHealthSample`, а более чистая таблица для временных метрик.

```sql
CREATE TABLE node_runtime_metrics (
    id BIGSERIAL PRIMARY KEY,
    node_code VARCHAR(32) NOT NULL,
    sampled_at TIMESTAMP NOT NULL DEFAULT now(),

    source VARCHAR(64) NOT NULL DEFAULT 'node-agent',

    cpu_percent FLOAT,
    load1 FLOAT,
    load5 FLOAT,
    load15 FLOAT,
    cpu_steal_percent FLOAT,
    cpu_iowait_percent FLOAT,
    softirq_percent FLOAT,

    memory_used_mb INTEGER,
    memory_total_mb INTEGER,

    network_rx_mbps FLOAT,
    network_tx_mbps FLOAT,
    network_total_mbps FLOAT,
    network_tx_mbps_1m FLOAT,
    network_tx_mbps_5m FLOAT,
    network_rx_mbps_1m FLOAT,
    network_rx_mbps_5m FLOAT,

    tcp_retrans_percent FLOAT,
    tcp_established_count INTEGER,
    tcp_timewait_count INTEGER,
    conntrack_used INTEGER,
    conntrack_max INTEGER,

    xray_process_rss_mb INTEGER,
    xray_open_fds INTEGER,
    xray_restart_count_24h INTEGER,

    dataplane_ok BOOLEAN,
    dataplane_rtt_ms INTEGER,
    dataplane_error_kind VARCHAR(64),
    dataplane_error_message VARCHAR(500),

    panel_ok BOOLEAN,
    panel_latency_ms INTEGER,
    panel_error_kind VARCHAR(64),

    capacity_score FLOAT,
    capacity_state VARCHAR(32), -- healthy / warm / soft_drain / hard_reject / stale / down
    reject_reason VARCHAR(128),

    meta_json TEXT
);

CREATE INDEX idx_node_runtime_metrics_code_time
ON node_runtime_metrics (node_code, sampled_at DESC);
```

### 4.3. `key_usage_rollups`

Счётчики по ключу. Не “девайсы”, а usage.

```sql
CREATE TABLE key_usage_rollups (
    id BIGSERIAL PRIMARY KEY,
    account_tg_id BIGINT NOT NULL,
    key_id VARCHAR(64) NOT NULL,
    key_email VARCHAR(160) NOT NULL,
    node_code VARCHAR(32) NOT NULL,

    window_kind VARCHAR(16) NOT NULL, -- 1m / 5m / 1h / 24h / 30d
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,

    uplink_bytes BIGINT NOT NULL DEFAULT 0,
    downlink_bytes BIGINT NOT NULL DEFAULT 0,
    total_bytes BIGINT NOT NULL DEFAULT 0,

    avg_bps FLOAT,
    p95_bps FLOAT,
    max_bps FLOAT,

    source_ip_count INTEGER NOT NULL DEFAULT 0,
    source_asn_count INTEGER NOT NULL DEFAULT 0,
    source_country_count INTEGER NOT NULL DEFAULT 0,
    node_count INTEGER NOT NULL DEFAULT 1,

    connection_count_hint INTEGER,
    connection_churn_score FLOAT,

    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX uq_key_usage_rollup
ON key_usage_rollups (key_id, node_code, window_kind, window_start);
```

### 4.4. `key_source_observations`

Это уже ближе к твоему observer, но надо сделать нормальным contract.

```sql
CREATE TABLE key_source_observations (
    id BIGSERIAL PRIMARY KEY,
    account_tg_id BIGINT NOT NULL,
    key_id VARCHAR(64) NOT NULL,
    node_code VARCHAR(32) NOT NULL,

    observed_at TIMESTAMP NOT NULL DEFAULT now(),
    source_ip_hash VARCHAR(96) NOT NULL,
    source_ip_prefix_hash VARCHAR(96),
    source_asn VARCHAR(32),
    source_country VARCHAR(8),
    source_family VARCHAR(16), -- ipv4 / ipv6 / unknown

    identity_source VARCHAR(32) NOT NULL DEFAULT 'xray-access-log',
    confidence FLOAT NOT NULL DEFAULT 0.5,

    raw_safe_json TEXT
);

CREATE INDEX idx_key_source_observations_key_time
ON key_source_observations (key_id, observed_at DESC);
```

Нельзя хранить сырые IP без нужды. Лучше hash + /24 или /48 hash для грубой группировки. Сырые IP можно держать коротко, если юридически/операционно нужно, но по умолчанию редактировать/хешировать.

### 4.5. `key_pressure_state`

Текущий state ключа.

```sql
CREATE TABLE key_pressure_state (
    key_id VARCHAR(64) PRIMARY KEY,
    account_tg_id BIGINT NOT NULL,

    pressure_score FLOAT NOT NULL DEFAULT 0.0,
    pressure_state VARCHAR(32) NOT NULL DEFAULT 'normal',
    -- normal / warm / heavy / suspected_shared / fair_use / blocked_manual_review

    reason_codes_json TEXT NOT NULL DEFAULT '[]',

    bps_5m FLOAT,
    bps_1h FLOAT,
    bytes_24h BIGINT,
    bytes_30d BIGINT,

    source_ip_count_1h INTEGER,
    source_ip_count_24h INTEGER,
    source_asn_count_24h INTEGER,
    source_country_count_24h INTEGER,
    node_count_1h INTEGER,

    last_seen_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);
```

### 4.6. `subscription_fetch_events`

Для сторонних клиентов это очень важный слой. Subscription fetch — почти единственная обратная связь от клиента.

```sql
CREATE TABLE subscription_fetch_events (
    id BIGSERIAL PRIMARY KEY,
    account_tg_id BIGINT NOT NULL,
    subscription_token_hash VARCHAR(96) NOT NULL,

    fetched_at TIMESTAMP NOT NULL DEFAULT now(),
    source_ip_hash VARCHAR(96),
    source_asn VARCHAR(32),
    source_country VARCHAR(8),

    user_agent VARCHAR(500),
    accept_header VARCHAR(300),
    requested_format VARCHAR(32),
    resolved_format VARCHAR(32),

    rendered_node_count INTEGER,
    rendered_pool VARCHAR(32),
    profile_revision VARCHAR(128),

    cache_hint_seconds INTEGER,
    meta_json TEXT
);

CREATE INDEX idx_subscription_fetch_events_token_time
ON subscription_fetch_events (subscription_token_hash, fetched_at DESC);
```

### 4.7. `rendered_subscription_snapshots`

Снимок того, что реально отдали клиенту.

```sql
CREATE TABLE rendered_subscription_snapshots (
    id BIGSERIAL PRIMARY KEY,
    subscription_token_hash VARCHAR(96) NOT NULL,
    account_tg_id BIGINT NOT NULL,

    rendered_at TIMESTAMP NOT NULL DEFAULT now(),
    resolved_format VARCHAR(32) NOT NULL,
    profile_revision VARCHAR(128) NOT NULL,

    node_codes_json TEXT NOT NULL,
    primary_node_code VARCHAR(32),
    pool_code VARCHAR(32),

    reason_json TEXT NOT NULL DEFAULT '{}',
    content_hash VARCHAR(96) NOT NULL
);
```

### 4.8. `node_provisioning_jobs`

Нужен надёжный reconciler.

```sql
CREATE TABLE node_provisioning_jobs (
    id BIGSERIAL PRIMARY KEY,
    account_tg_id BIGINT NOT NULL,
    key_id VARCHAR(64) NOT NULL,
    node_code VARCHAR(32) NOT NULL,

    desired_state VARCHAR(32) NOT NULL, -- present / absent / disabled / rotated
    current_state VARCHAR(32) NOT NULL DEFAULT 'pending',

    attempts INTEGER NOT NULL DEFAULT 0,
    last_error_kind VARCHAR(64),
    last_error_message VARCHAR(500),

    next_run_at TIMESTAMP NOT NULL DEFAULT now(),
    locked_at TIMESTAMP,
    locked_by VARCHAR(64),

    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX uq_node_provisioning_jobs_open
ON node_provisioning_jobs (key_id, node_code, desired_state)
WHERE current_state IN ('pending', 'running', 'retry');
```

---

## 5. Новая модель метрик: что считать вместо online users

### 5.1. Нода

Для каждой ноды считать:

```text
node_tx_mbps_1m
node_tx_mbps_5m
node_rx_mbps_1m
node_rx_mbps_5m
node_tx_ratio_1m = tx_mbps_1m / capacity_mbps
node_tx_ratio_5m = tx_mbps_5m / capacity_mbps
cpu_percent
cpu_steal_percent
softirq_percent
tcp_retrans_percent
tcp_established_count
dataplane_rtt_ms
dataplane_ok
metrics_staleness_seconds
panel_ok
xray_ok
```

Нода должна иметь state:

```text
healthy       = можно давать новым пользователям
warm          = можно, но снижать приоритет
soft_drain    = не давать новым auto-подключениям, но не рвать старых
hard_reject   = исключить из новых профилей/подписок
stale         = метрики старые, не доверять
down          = dataplane/panel/xray не работает
maintenance   = руками выключено
```

### 5.2. Ключ

Для каждого `AccessKey` считать:

```text
key_bps_1m
key_bps_5m
key_bps_1h
key_bytes_24h
key_bytes_30d
key_source_ip_count_1h
key_source_ip_count_24h
key_source_asn_count_24h
key_source_country_count_24h
key_node_count_1h
key_fetch_ip_count_24h
key_fetch_ua_count_24h
key_connection_churn_score
```

Ключ должен иметь state:

```text
normal
warm
heavy
suspected_shared
fair_use
manual_review
disabled
```

`fair_use` не означает бан. Это означает:

- ниже приоритет в перегруженных пулах;
- subscription renderer может ставить меньше нод;
- heavy ключи можно отправлять в отдельный pool;
- пользователю можно показать/отправить “ключ сильно нагружен, обновите подписку или создайте отдельные ключи для устройств”;
- hard action только при явной аномалии.

---

## 6. Scoring ноды

В `portal_bot/node_policy.py` заменить текущий подход на capacity-aware. Не удалять старые поля, но перестать строить финальный выбор на `active_clients`.

### 6.1. Hard reject

Нода не должна попадать в новые auto/select/subscription primary, если:

```python
if not node.enabled:
    reject("disabled")

if not node.accepting_new_clients:
    reject("not_accepting_new_clients")

if node.is_draining:
    reject("draining")

if metrics_stale_seconds > stale_after_seconds:
    reject("metrics_stale")

if dataplane_ok is False:
    reject("dataplane_down")

if node_tx_ratio_1m >= hard_tx_ratio:
    reject("tx_hard_saturated_1m")

if node_tx_ratio_5m >= drain_tx_ratio and node_tx_ratio_1m >= drain_tx_ratio:
    reject("tx_saturated_sustained")

if cpu_percent >= hard_cpu_percent:
    reject("cpu_hard")

if tcp_retrans_percent >= max_retrans_percent:
    reject("tcp_retrans_high")

if packet_loss_percent >= max_packet_loss_percent:
    reject("packet_loss_high")
```

### 6.2. Soft score

Меньше score — лучше.

```python
def node_selection_score(node, client_rtt_ms=None, user_region_hint=None):
    tx_ratio_1m = clamp(node.tx_mbps_1m / node.capacity_mbps, 0, 2)
    tx_ratio_5m = clamp(node.tx_mbps_5m / node.capacity_mbps, 0, 2)
    cpu_ratio = clamp(node.cpu_percent / 100, 0, 1.5)
    retrans = clamp(node.tcp_retrans_percent or 0, 0, 20)
    panel_latency = clamp(node.panel_latency_ms or 0, 0, 3000)
    dataplane_rtt = clamp(node.dataplane_rtt_ms or 0, 0, 3000)
    client_rtt = clamp(client_rtt_ms or dataplane_rtt or panel_latency or 250, 1, 5000)

    score = 0
    score += client_rtt * 0.35
    score += tx_ratio_1m * 260
    score += tx_ratio_5m * 380
    score += cpu_ratio * 140
    score += retrans * 35
    score += clamp(node.cpu_steal_percent or 0, 0, 40) * 6
    score += clamp(node.softirq_percent or 0, 0, 60) * 3
    score += clamp(node.panel_error_rate or 0, 0, 1) * 120
    score -= clamp(node.operator_weight or 100, 0, 200) * 0.15

    if node.capacity_state == "warm":
        score += 80
    if node.capacity_state == "soft_drain":
        score += 300
    if user_region_hint and node.region == user_region_hint:
        score -= 25

    return round(score, 3)
```

### 6.3. Capacity state updater

В metrics collector или отдельном service:

```python
def capacity_state_for(node, metrics, policy):
    if metrics.is_stale(policy.stale_after_seconds):
        return "stale", "metrics_stale"

    if not metrics.dataplane_ok:
        return "down", "dataplane_down"

    tx_ratio_1m = metrics.tx_mbps_1m / policy.capacity_mbps
    tx_ratio_5m = metrics.tx_mbps_5m / policy.capacity_mbps

    if tx_ratio_1m >= policy.hard_tx_ratio:
        return "hard_reject", "tx_hard_1m"

    if tx_ratio_5m >= policy.drain_tx_ratio:
        return "soft_drain", "tx_drain_5m"

    if tx_ratio_1m >= policy.soft_tx_ratio or tx_ratio_5m >= policy.soft_tx_ratio:
        return "warm", "tx_warm"

    if metrics.cpu_percent >= policy.hard_cpu_percent:
        return "hard_reject", "cpu_hard"

    if metrics.cpu_percent >= policy.drain_cpu_percent:
        return "soft_drain", "cpu_drain"

    if metrics.tcp_retrans_percent and metrics.tcp_retrans_percent >= policy.max_retrans_percent:
        return "soft_drain", "tcp_retrans"

    return "healthy", "ok"
```

---

## 7. Scoring ключа

Цель: не банить семьи, а выявлять ключи, которые реально давят сеть или похожи на публичный слив.

### 7.1. Key pressure score

```python
def key_pressure_score(k):
    score = 0

    # bandwidth pressure
    score += clamp(k.bps_5m / 50_000_000, 0, 5) * 25      # 50 Mbps chunks
    score += clamp(k.bps_1h / 25_000_000, 0, 5) * 15      # sustained pressure

    # daily/monthly traffic pressure
    score += clamp(k.bytes_24h / gib(80), 0, 5) * 12
    score += clamp(k.bytes_30d / gib(1500), 0, 5) * 10

    # sharing hints; weak, not final truth
    if k.source_ip_count_1h > 5:
        score += (k.source_ip_count_1h - 5) * 5
    if k.source_ip_count_24h > 12:
        score += (k.source_ip_count_24h - 12) * 3
    if k.source_asn_count_24h > 4:
        score += (k.source_asn_count_24h - 4) * 12
    if k.source_country_count_24h > 3:
        score += (k.source_country_count_24h - 3) * 18
    if k.node_count_1h > 3:
        score += (k.node_count_1h - 3) * 8

    # subscription leakage hints
    if k.fetch_ip_count_24h > 8:
        score += (k.fetch_ip_count_24h - 8) * 4
    if k.fetch_ua_count_24h > 5:
        score += (k.fetch_ua_count_24h - 5) * 5

    return clamp(score, 0, 500)
```

### 7.2. Pressure states

```python
if score < 60:
    state = "normal"
elif score < 120:
    state = "warm"
elif score < 200:
    state = "heavy"
elif score < 320:
    state = "suspected_shared"
else:
    state = "fair_use"
```

Hard block только если есть явные причины:

```text
- ключ появился в публичном списке;
- сотни IP/ASN за сутки;
- аномальный трафик разрушает ноды;
- chargeback/fraud/manual admin action;
- key used after cancellation.
```

### 7.3. Family-safe политика

Не считать нарушением само по себе:

```text
2-5 IP за день
1-3 ASN за день
мобильный CGNAT
дом + телефон + ноутбук
смена IPv6 prefix
несколько стран за отпуск/роуминг
несколько клиентов с одним User-Agent
```

Считать подозрительным только комбинации:

```text
очень высокий трафик + много ASN + много стран
очень высокий sustained Mbps + много IP
один ключ одновременно виден на 4+ нодах
один ключ качает > 80 GB/day несколько дней подряд
subscription token fetch идёт с десятков IP/UA
```

---

## 8. Новый control-plane для собственного POKROV-app

Собственное приложение можно контролировать лучше, чем сторонние клиенты. Поэтому для POKROV-app сделать реальный flow:

```text
client -> GET /api/client/nodes/candidates
backend -> shortlist capacity-aware candidates
client -> RTT probe candidates
client -> POST /api/client/nodes/select
backend -> final decision + provisioning guarantee
client -> GET /api/client/profile/managed?selected_node=...
client -> connect
client -> periodically report runtime live stats if available
```

### 8.1. Endpoint: candidates

```http
GET /api/client/nodes/candidates?region=auto&transport_profile=legacy_reality_fallback
Authorization: Bearer <session>
```

Response:

```json
{
  "profile_revision": "2026-06-28:capacity-v1",
  "strategy": "capacity_aware",
  "ttl_seconds": 120,
  "client_probe_timeout_ms": 900,
  "shortlist": [
    {
      "code": "nl-1",
      "country": "Нидерланды",
      "city": "Amsterdam",
      "probe": { "host": "nl1.example.com", "port": 443 },
      "capacity_state": "healthy",
      "rank_hint": {
        "node_score": 42.3,
        "tx_ratio_5m": 0.31,
        "cpu_percent": 21.0,
        "dataplane_rtt_ms": 18
      }
    }
  ]
}
```

### 8.2. Endpoint: select

```http
POST /api/client/nodes/select
Authorization: Bearer <session>
```

Payload:

```json
{
  "profile_revision": "2026-06-28:capacity-v1",
  "mode": "auto",
  "manual_node_code": null,
  "previous_node_code": "de-1",
  "transport_profile": "legacy_reality_fallback",
  "samples": [
    { "node_code": "de-1", "rtt_ms": 55 },
    { "node_code": "nl-1", "rtt_ms": 35 },
    { "node_code": "pl-1", "rtt_ms": 70 }
  ],
  "runtime": {
    "platform": "android",
    "app_version": "1.0.0-beta.3"
  }
}
```

Response:

```json
{
  "selected_node_code": "nl-1",
  "previous_node_code": "de-1",
  "stickiness_applied": false,
  "reason": "best_rtt_with_capacity",
  "ttl_seconds": 900,
  "requires_profile_refresh": true,
  "managed_profile_url": "/api/client/profile/managed?selected_node_code=nl-1"
}
```

### 8.3. Sticky logic

Не таскать пользователя между странами без причины.

```python
if previous_node_still_healthy:
    improvement = (previous_score - best_score) / max(previous_score, 1)
    if improvement < stickiness_threshold:
        keep previous
```

Но если previous:

```text
hard_reject
down
stale
soft_drain + new connection
tx_ratio_5m > 0.85
manual operator drain
```

то stickiness игнорируется.

### 8.4. App code changes

В `packages/app_shell/lib/app_first_runtime_bootstrap.dart`:

- оставить `_maybeUploadSmartConnectLatency` для compat;
- добавить явный `_fetchSmartConnectCandidates`;
- добавить `_selectSmartConnectNodeRemote`;
- перестать использовать `POST /latency-samples` как способ manual preference с `rtt_ms: 1`;
- manual location отправлять как `mode=manual`;
- auto отправлять как `mode=auto`;
- managed profile получать после `select`, если backend ответил `requires_profile_refresh`;
- `interrupt_exist_connections` не включать без нужды: у пользователя должен быть controlled reconnect, а не рандомный обрыв.

---

## 9. Subscription steering для внешних клиентов

Это самая важная часть, потому что сейчас пользователи используют любые клиенты.

### 9.1. Принцип

Для внешнего клиента backend не может сделать real-time select. Он может управлять только:

```text
какие ноды попали в подписку
в каком порядке они идут
как они называются
какой формат отдан
какой TTL/cache hint
какой pool выбран для ключа
какие старые ноды остаются валидными
когда ключ ротируется
```

### 9.2. Subscription renderer

Сделать единый renderer:

```http
GET /sub/{token}
GET /sub/{token}?format=auto
GET /sub/{token}?format=vless
GET /sub/{token}?format=singbox
GET /sub/{token}?format=clash
GET /sub/{token}?format=hiddify
```

Если format не указан:

```python
format = detect_by_user_agent(request.headers["User-Agent"], request.headers["Accept"])
```

Если не уверен — отдавать raw VLESS list.

### 9.3. Форматы

#### Raw VLESS

Для максимально совместимых клиентов:

```text
vless://uuid@host:443?...#POKROV%20Auto%201%20-%20NL
vless://uuid@host:443?...#POKROV%20Auto%202%20-%20DE
vless://uuid@host:443?...#🇳🇱%20Нидерланды
vless://uuid@host:443?...#🇩🇪%20Германия
```

Порядок — главный steering mechanism.

#### sing-box JSON

Для клиентов, которые умеют sing-box config:

- создать `urltest` outbound `POKROV Auto`;
- включить top candidates;
- не ставить слишком агрессивный interval;
- `interrupt_exist_connections` по умолчанию `false`.

#### Clash Meta YAML

Для клиентов с Clash-like subscription:

- proxy-groups:
  - `POKROV Auto` url-test
  - `POKROV Manual` select
  - country groups
- health check URL `https://www.gstatic.com/generate_204` или `https://cp.cloudflare.com/generate_204` по профилю.

### 9.4. Dynamic ordering

Subscription request должен ранжировать ноды так:

```python
nodes = eligible_paid_nodes(account)
nodes = exclude_hard_reject(nodes)
nodes = include_soft_drain_only_if_manual_or_existing(nodes)

primary = best node by:
    node_capacity_score
    historical key affinity
    key pressure state
    country preference
    pool policy
    last rendered snapshot
```

Для normal key:

```text
top 3 auto candidates
then all healthy paid countries
then warm nodes lower
do not include hard_reject/down/stale
```

Для heavy/fair-use key:

```text
prefer fair_use_pool nodes
avoid already warm premium nodes
reduce top auto list to 2-3
still keep paid access unless hard abuse
```

Для free key:

```text
only NL-free / free pool
```

### 9.5. Cache headers

Сторонние клиенты могут кешировать как хотят, но backend должен делать правильно:

```http
Cache-Control: no-store, no-cache, must-revalidate, max-age=0
Pragma: no-cache
Expires: 0
Profile-Update-Interval: 300
Subscription-Userinfo: upload=...; download=...; total=...; expire=...
```

Не все клиенты уважают это, но это лучше, чем ничего.

### 9.6. Subscription snapshots

Каждый render писать в `rendered_subscription_snapshots`, чтобы потом понимать:

- какой список нод был выдан;
- почему пользователь мог остаться на старой ноде;
- какой format был отдан;
- какой primary был на тот момент;
- какое решение принял backend.

---

## 10. Provisioning: убрать UserNode-залипание

Сейчас главный риск: если пользователь provisioned только на `it`/`pl`, backend не может честно выбрать `de`/`nl`.

### 10.1. Для текущего масштаба

Premium/trial/paid keys должны быть provisioned на всех enabled paid nodes.

Это не идеально по количеству клиентов в панели, но для твоих текущих 5–10 нод и сотен аккаунтов это нормально.

Правило:

```python
if user in premium_access:
    desired_nodes = all enabled paid nodes except maintenance/hard disabled
elif user in free_access:
    desired_nodes = canonical free pool
else:
    desired_nodes = []
```

### 10.2. Reconciler

Не делать sync только при выдаче ключа. Нужен постоянный reconciler:

```text
каждые N минут:
  load all active users
  load all enabled nodes
  compute desired user-key-node matrix
  create provisioning jobs
  process jobs with retries
  mark drift
  report drift to admin
```

### 10.3. Lazy provisioning потом

На большем масштабе можно сделать lazy provisioning, но для внешних подписок всё равно нужна гарантия: если нода есть в subscription, ключ должен реально существовать на этой ноде.

Правило:

```text
renderer must not emit node unless key provisioned or provisioning synchronously succeeded
```

### 10.4. Rotation

UUID rotation делать только как controlled action:

```text
normal -> no rotation
heavy -> no rotation
suspected_shared -> warning + optional rotate
public leak -> rotate + old key grace 15-60 min
cancelled/fraud -> disable
```

---

## 11. Node agent

Сейчас collector завязан на panel и dataplane probe. Нужен lightweight agent на каждой VPS.

### 11.1. Agent output

Каждые 10–15 секунд agent собирает:

```json
{
  "node_code": "de-1",
  "sampled_at": "2026-06-28T12:00:00Z",
  "cpu": {
    "percent": 22.5,
    "steal_percent": 0.2,
    "iowait_percent": 1.1,
    "softirq_percent": 3.4,
    "load1": 0.55,
    "load5": 0.42
  },
  "memory": {
    "used_mb": 890,
    "total_mb": 4096
  },
  "network": {
    "interface": "eth0",
    "rx_bytes_total": 123,
    "tx_bytes_total": 456,
    "rx_mbps": 80.2,
    "tx_mbps": 340.5
  },
  "tcp": {
    "established": 512,
    "time_wait": 120,
    "retrans_percent": 0.4
  },
  "process": {
    "xray_running": true,
    "xray_rss_mb": 180,
    "xray_open_fds": 900
  }
}
```

### 11.2. Agent security

- push endpoint только по HMAC;
- secret на ноде unique;
- timestamp + nonce;
- reject если clock skew > 90 секунд;
- не логировать secret;
- не принимать public metrics без auth.

```http
POST /api/internal/nodes/{node_code}/metrics
X-POKROV-Timestamp: ...
X-POKROV-Signature: hmac_sha256(secret, body + timestamp)
```

### 11.3. Implementation options

Agent может быть:

- Python script + systemd timer;
- Go static binary;
- bash + curl для MVP, но лучше Python/Go.

Для точности network rate лучше agent должен считать delta локально или backend должен считать delta по total bytes. Не полагаться только на instantaneous `bytes_per_sec`, если источник нестабилен.

---

## 12. Xray stats collector

### 12.1. Включить stats/metrics

Для каждой ноды в Xray config:

```json
{
  "stats": {},
  "metrics": {
    "listen": "127.0.0.1:11111"
  }
}
```

И policy для user traffic. Принцип: каждый client должен иметь `email`, который является stable technical key label:

```text
pokrov:<account_id>:<key_id>
```

Не использовать сырой email пользователя как technical email.

### 12.2. Сбор

Collector читает:

```text
http://127.0.0.1:11111/debug/vars
```

Извлекает:

```text
stats.user.<email>.uplink/downlink
stats.inbound.<tag>.uplink/downlink
stats.outbound.<tag>.uplink/downlink
observatory.*
```

Считает delta между samples.

### 12.3. User stats caveat

Если несколько людей используют один UUID/email, Xray stats покажет суммарный трафик ключа. Это нормально. Это именно то, что нужно для `key_pressure`, а не для `device_count`.

---

## 13. Observer/access-log parser

Нужен парсер, который из Xray access log или panel stats получает source-IP hints по key.

### 13.1. Что парсить

Минимально:

```text
timestamp
node_code
key_email / uuid / user label
source_ip
destination/domain optional
protocol optional
accepted/rejected
```

### 13.2. Что хранить

Не сырые IP навсегда, а:

```text
source_ip_hash
source_prefix_hash
asn
country
first_seen
last_seen
hit_count
confidence
```

### 13.3. Confidence

Не каждый лог одинаково надёжен.

```text
xray_access_log_email_match -> 0.9
panel_online_summary        -> 0.6
netstat_by_port_only        -> 0.2
subscription_fetch_ip       -> 0.4
app_runtime_report          -> 0.8
```

### 13.4. Не делать

- не считать каждый IP отдельным устройством;
- не банить за IPv6 rotation;
- не банить за мобильный NAT;
- не показывать оператору сырые IP без причины;
- не использовать destination domains для профилирования пользователя.

---

## 14. Fair-use поведение

### 14.1. Основной policy

POKROV должен быть “семейно терпимым”, но не “ключ на весь район”.

Пример:

```text
normal:
  full premium pool
  no warnings

warm:
  full premium pool
  lower auto priority on saturated nodes
  silent observe

heavy:
  avoid warm nodes
  prefer high-capacity nodes
  show optional warning in cabinet/app
  no hard block

suspected_shared:
  prefer fair-use/high-capacity pool
  reduce subscription auto shortlist
  notify: "ключ сильно нагружен"

fair_use:
  route to fair-use pool first
  optional speed/fairness pool
  admin visible
  allow support appeal

manual_review:
  operator decides
```

### 14.2. Сообщения пользователю

Не писать “вы нарушитель”. Писать:

```text
Мы видим высокую нагрузку на ключ. Чтобы соединение работало стабильнее, обновите подписку или создайте отдельный ключ для второго устройства.
```

### 14.3. Device slots как future-friendly, но не mandatory

Добавить в UI/portal:

```text
"Создать ключ для устройства"
"Переименовать ключ"
"Сбросить ключ"
"Показать QR"
```

Но не требовать от всех сразу. Для external clients это добровольный путь улучшить качество и справедливость.

---

## 15. Pool design

### 15.1. Pools

```text
premium_pool:
  обычные платные/trial/bonus пользователи

free_pool:
  NL-free или dedicated free nodes

fair_use_pool:
  heavy/suspected_shared keys, но без унижения UX

canary_pool:
  новые ноды/новые transport profiles

maintenance_pool:
  исключить из render/select

legacy_pool:
  старые ноды, которые ещё нельзя удалить
```

### 15.2. Node membership

```sql
CREATE TABLE node_pool_membership (
    node_code VARCHAR(32) NOT NULL,
    pool_code VARCHAR(32) NOT NULL,
    weight INTEGER NOT NULL DEFAULT 100,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (node_code, pool_code)
);
```

### 15.3. Selection

```python
def pools_for_key(key):
    if key.access_lane == "free":
        return ["free_pool"]

    if key.pressure_state in {"fair_use", "suspected_shared"}:
        return ["fair_use_pool", "premium_pool"]

    return ["premium_pool"]
```

---

## 16. Subscription renderer naming

Очень важно для external clients.

### 16.1. Имена

Raw VLESS list:

```text
POKROV Auto 1 · NL
POKROV Auto 2 · DE
POKROV Auto 3 · PL
🇳🇱 Нидерланды · Amsterdam
🇩🇪 Германия · Frankfurt
🇵🇱 Польша · Warsaw
🇮🇹 Италия · Milan
🇺🇸 США · New York
```

Не добавлять в названия “overloaded”, “abuse”, “fair-use”. Пользователь не должен видеть внутренние ярлыки.

### 16.2. Порядок

Для клиентов, которые тупо берут первый node:

```text
1. best primary
2. second best same macro-region
3. third best backup
4. manual country nodes
```

### 16.3. Скрытие нод

- `hard_reject/down/stale` — не отдавать новым subscription render;
- `soft_drain` — отдавать ниже или только если это manual/legacy;
- `maintenance` — не отдавать;
- `fair_use_only` — отдавать только fair-use keys.

---

## 17. Backend API contract

### 17.1. Keep existing compatibility

Не ломать:

```text
/api/client/profile/managed
/api/client/nodes/latency-samples
/sub/<token>
existing Telegram/bot/web flows
```

### 17.2. Add new endpoints

```http
GET /api/client/nodes/candidates
POST /api/client/nodes/select
POST /api/client/runtime/stats
GET /api/client/subscription/preview
GET /api/admin/nodes/capacity
GET /api/admin/keys/pressure
POST /api/admin/nodes/{code}/drain
POST /api/admin/nodes/{code}/undrain
POST /api/admin/keys/{key_id}/rotate
POST /api/internal/nodes/{code}/metrics
POST /api/internal/nodes/{code}/xray-stats
```

### 17.3. Runtime stats from own app

For POKROV-app only:

```json
{
  "selected_node_code": "nl-1",
  "connected": true,
  "latency_ms": 42,
  "uplink_bps": 120000,
  "downlink_bps": 5000000,
  "runtime_core": "sing-box",
  "transport_profile": "legacy_reality_fallback",
  "route_mode": "all_except_ru",
  "error_kind": ""
}
```

Do not require this for external clients.

---

## 18. Changes in specific files

### 18.1. `portal_bot/models.py`

Add:

```text
NodeCapacityPolicy
NodeRuntimeMetric
AccessKey / or extend existing key model
KeyUsageRollup
KeySourceObservation
KeyPressureState
SubscriptionFetchEvent
RenderedSubscriptionSnapshot
NodePoolMembership
NodeProvisioningJob
```

If existing `User` has one UUID/email, introduce `AccessKey` without breaking legacy:

```sql
access_keys:
  id
  key_id
  tg_id
  uuid
  email
  label
  state
  created_at
  rotated_at
  revoked_at
  pressure_state
  current_pool_policy
```

Legacy users get one default key:

```text
key_id = default
uuid = users.uuid
email = users.email
```

### 18.2. `portal_bot/migrations.py`

Add idempotent migrations:

- create new tables;
- add missing columns to `nodes`;
- backfill `node_capacity_policy` for all nodes;
- backfill `access_keys` from users;
- backfill pool membership:
  - paid nodes -> premium_pool
  - free node -> free_pool
- create indexes;
- no destructive migration.

### 18.3. `scripts/collect_node_metrics.py`

Change:

- stop using `active_clients` as load penalty;
- rename/count provisioned clients;
- ingest node agent metrics;
- ingest Xray `/debug/vars`;
- compute network rate with 1m/5m EWMA;
- compute capacity state;
- write `NodeRuntimeMetric`;
- update `Node` current fields for admin compatibility.

### 18.4. `portal_bot/node_policy.py`

Implement:

```text
node_capacity_state()
node_hard_reject_reason()
rank_nodes_for_app()
rank_nodes_for_subscription()
rank_nodes_for_manual_country()
rank_nodes_for_key_pressure()
```

Make constants configurable:

```python
SMART_CONNECT_SHORTLIST_LIMIT = env_int("SMART_CONNECT_SHORTLIST_LIMIT", 8)
SMART_CONNECT_STALE_AFTER_SECONDS = env_int("SMART_CONNECT_STALE_AFTER_SECONDS", 180)
SMART_CONNECT_CPU_REJECT_PERCENT = env_float("SMART_CONNECT_CPU_REJECT_PERCENT", 85.0)
SMART_CONNECT_STICKINESS_THRESHOLD_PERCENT = env_int("SMART_CONNECT_STICKINESS_THRESHOLD_PERCENT", 20)
```

### 18.5. `portal_bot/nodes_repo.py`

Current sorting is health_score then weight. Replace with capacity-aware ranking:

```python
def eligible_nodes(session, user, key=None, purpose="subscription"):
    ...
```

Do not let `UserNode` mapping reduce candidate pool. Use `UserNode` only as provisioning status/historical mapping.

### 18.6. `portal_bot/app_first_service.py`

- include selected node hints in managed profile;
- respect `/nodes/select`;
- keep old `smart_connect` contract for app UI;
- add `profile_revision = rollout_version + capacity_policy_version`.

### 18.7. `portal_bot/api.py`

Add endpoints and integrate renderer.

`/api/client/nodes/latency-samples` becomes telemetry-only compatible endpoint. It may update sticky preference, but not be the only selection API.

### 18.8. `scripts/remote_sync_users_to_nodes.py`

Change to desired-state reconciler:

```text
sync all premium active keys to all eligible premium nodes
sync free keys only to free pool
sync fair-use keys to fair-use pool + optional premium fallback
remove/revoke only through explicit desired_state absent/disabled
```

### 18.9. `POKROV-app`

In `packages/app_shell/lib/app_first_runtime_bootstrap.dart`:

- add candidates/select flow;
- use remote selected node before materializing config;
- manual location uses `mode=manual`;
- auto uses `mode=auto`;
- runtime stats endpoint best-effort;
- do not block connect if telemetry upload fails;
- do not interrupt existing connections unless user explicitly reconnects.

In `locations_surface.dart`:

- UI says:
  - “Авто: выберем быстрый доступный маршрут”
  - “Ручная страна: применится при переподключении”
- show current node if runtime live stats available.
- do not expose fair-use/internal states to user.

---

## 19. Subscription compatibility detection

Implement:

```python
def detect_subscription_format(user_agent, accept, query_format):
    if query_format in allowed:
        return query_format

    ua = user_agent.lower()

    if "sing-box" in ua or "singbox" in ua:
        return "singbox"

    if "clash" in ua or "mihomo" in ua or "stash" in ua:
        return "clash"

    if "hiddify" in ua:
        return "vless"  # or hiddify if custom renderer is verified

    if "happ" in ua:
        return "vless"

    return "vless"
```

Do not overfit. Unknown clients get raw VLESS.

---

## 20. Admin UI

Add admin pages/cards:

### 20.1. Node capacity dashboard

Show:

```text
Node
State
TX 1m / 5m
Capacity %
CPU
Retrans
Dataplane RTT
Stale age
Provisioned keys
Top pressure keys
Actions: drain / undrain / maintenance / hide from subscriptions
```

### 20.2. Key pressure dashboard

Show:

```text
Account
Key label
Pressure state
5m Mbps
24h GB
30d GB
IP count 24h
ASN count 24h
Countries 24h
Nodes 1h
Last seen
Actions: notify / fair-use / rotate / reset state
```

### 20.3. Subscription render debug

For account/key:

```text
simulate /sub token
show resolved format
show node order
show reasons
show excluded nodes with reject reason
```

This is critical for support: “почему у юзера нет Германии?”

---

## 21. Tests to add

### 21.1. Backend unit tests

```text
test_node_hard_reject_when_tx_1m_above_90_percent
test_node_soft_drain_when_tx_5m_above_80_percent
test_node_stale_rejected_after_180_seconds
test_active_clients_not_used_as_online_load
test_provisioned_clients_does_not_penalize_idle_node
test_key_pressure_family_usage_stays_normal
test_key_pressure_many_asn_high_traffic_becomes_suspected_shared
test_key_pressure_heavy_bps_routes_to_fair_use_pool
test_usernode_mapping_does_not_limit_premium_candidates
test_free_user_gets_only_free_pool
test_subscription_renderer_excludes_down_nodes
test_subscription_renderer_orders_by_capacity_score
test_subscription_renderer_records_snapshot
test_latency_samples_telemetry_does_not_force_manual_rtt_1_hack
test_nodes_select_manual_rejects_unavailable_node
test_nodes_select_auto_respects_stickiness
test_nodes_select_ignores_stickiness_when_previous_hard_reject
```

### 21.2. Integration tests

```text
start user trial
provision all paid nodes
render vless subscription
simulate node saturation
render subscription again
assert saturated node moved down/excluded
simulate key heavy state
assert fair_use pool preferred
simulate app RTT selection
assert selected node included in managed profile
```

### 21.3. App tests

```text
resolveManagedProfile_calls_candidates_then_select
manual_location_uses_nodes_select_mode_manual
telemetry_failure_does_not_block_connection
selected_node_profile_refresh_happens_before_runtime_config
locations_ui_shows_reconnect_hint
```

---

## 22. Observability and alerts

### 22.1. Metrics names

Expose internal Prometheus-like metrics from backend:

```text
pokrov_node_tx_mbps{node="de-1"}
pokrov_node_capacity_ratio{node="de-1"}
pokrov_node_capacity_state{node="de-1",state="soft_drain"}
pokrov_node_dataplane_rtt_ms{node="de-1"}
pokrov_node_metrics_stale_seconds{node="de-1"}
pokrov_key_pressure_score_bucket{state="heavy"}
pokrov_subscription_renders_total{format="vless"}
pokrov_subscription_render_node_count{format="vless"}
pokrov_provisioning_jobs_pending
pokrov_provisioning_jobs_failed
```

### 22.2. Alerts

```text
node_tx_ratio_5m > 0.85 for 5m
node_metrics_stale > 300s
node_dataplane_down > 60s
all_nodes_in_region_down
provisioning_jobs_failed > 0
subscription_renders_error_rate > 1%
key_pressure_fair_use_count sudden spike
```

### 22.3. Operator daily report

Every day:

```text
Top nodes by TX
Top keys by traffic
Nodes saturated
Nodes stale
Provisioning drift
Keys moved to fair-use
Subscription formats used
```

---

## 23. Rollout switches

Even though this is one big plan, add feature flags to reduce risk:

```text
CAPACITY_AWARE_NODE_SELECTION=true
SUBSCRIPTION_DYNAMIC_ORDERING=true
SUBSCRIPTION_EXCLUDE_HARD_REJECT=true
KEY_PRESSURE_SCORING=true
KEY_PRESSURE_FAIR_USE_ROUTING=false initially
APP_NODES_SELECT_ENDPOINT=true
XRAY_METRICS_COLLECTOR=true
NODE_AGENT_METRICS=true
USERNODE_MAPPING_AS_CANDIDATE_LIMIT=false
```

Default safe behavior:

- dynamic ordering can be on;
- hard exclusion of down/stale nodes can be on;
- fair-use routing should compute first, enforce later;
- key rotation never automatic at first.

---

## 24. Rollback

Must be able to turn off:

```text
CAPACITY_AWARE_NODE_SELECTION=false
SUBSCRIPTION_DYNAMIC_ORDERING=false
KEY_PRESSURE_FAIR_USE_ROUTING=false
```

Rollback behavior:

- use old `health_score + weight`;
- still keep metrics collection;
- subscription renders all enabled paid nodes as before;
- no user key deletion;
- no UUID rotation;
- no hard fair-use action.

Never make migration that prevents old subscription rendering.

---

## 25. Acceptance criteria

The work is done only when all statements are true:

```text
1. A paid/trial user can be provisioned on every paid enabled node.
2. UserNode mapping no longer traps premium users on 1-2 old nodes.
3. A saturated 1 Gbit node stops receiving new auto-primary placements.
4. A node with stale metrics is excluded from auto-primary.
5. active_clients/provisioned client count is not treated as online users.
6. Xray user traffic is collected per key when email exists.
7. Subscription renderer records fetch events and rendered snapshots.
8. Raw VLESS subscription works for unknown clients.
9. Own POKROV-app can select node via /nodes/select before fetching final managed profile.
10. Manual location no longer fakes RTT=1.
11. Heavy key scoring exists but does not ban families by default.
12. Admin can see node saturation and key pressure.
13. Operator can drain a node and subscriptions stop putting it first.
14. Tests cover saturation, stale, UserNode unstick, subscription rendering, app selection, key pressure.
15. Feature flags can disable enforcement without deleting data.
```

---

## 26. Concrete prompt for coding agent

Use this exact instruction block for implementation work:

```text
You are working in two private repositories:

- Kiwunaka/portal
- Kiwunaka/POKROV-app

Implement capacity-aware smart-connect and subscription steering for POKROV VPN.

Do not rely on active_clients as online users. In this product users import subscription links into arbitrary clients, and one Xray/VLESS key can be shared across multiple devices/people. Exact active user/device count is not available. Replace online-user assumptions with key pressure, node capacity, traffic rate, source IP/ASN hints, subscription fetch behavior, RTT samples, and dataplane health.

Preserve all existing public flows. Do not break current subscription URLs. Do not rotate or disable user keys automatically unless an explicit admin action exists. Add feature flags so enforcement can be disabled while metrics remain collected.

In portal:

1. Add data models and migrations for node capacity policy, node runtime metrics, key usage rollups, key source observations, key pressure state, subscription fetch events, rendered subscription snapshots, node pool membership, and provisioning jobs.

2. Introduce AccessKey abstraction if missing. Backfill existing users so each user has a default AccessKey using existing uuid/email. Ensure Xray technical email is stable and stats-compatible.

3. Update metrics collection:
   - collect node network tx/rx Mbps from OS/agent;
   - collect Xray stats/metrics from local metrics endpoint when available;
   - keep panel metrics as secondary;
   - compute node capacity state: healthy/warm/soft_drain/hard_reject/stale/down;
   - do not use provisioned client count as online load.

4. Update node_policy.py:
   - implement capacity-aware ranking;
   - hard reject down/stale/saturated nodes;
   - score based on tx ratio, CPU, retransmits, dataplane RTT, client RTT, weight;
   - implement key pressure scoring;
   - keep free/premium pool separation.

5. Update nodes_repo.py:
   - do not let UserNode mapping limit premium candidate nodes;
   - treat UserNode as provisioning state/history only;
   - expose eligible paid/free/fair-use pools.

6. Update provisioning:
   - active premium/trial/paid keys must exist on all enabled paid nodes for current scale;
   - free keys only on free pool;
   - build desired-state reconciler with retries;
   - renderer must not emit a node for a key unless key is provisioned on that node or provisioning succeeded.

7. Add backend endpoints:
   - GET /api/client/nodes/candidates
   - POST /api/client/nodes/select
   - POST /api/client/runtime/stats
   - POST /api/internal/nodes/{code}/metrics
   - admin capacity/key pressure endpoints
   - keep /api/client/nodes/latency-samples as compatibility telemetry.

8. Update subscription renderer:
   - support format=auto/vless/singbox/clash;
   - detect common clients by User-Agent but default unknown clients to raw VLESS;
   - dynamically order nodes by capacity score and key policy;
   - exclude hard_reject/down/stale nodes from new renders;
   - record fetch events and rendered snapshots;
   - return no-cache headers and subscription userinfo where compatible.

9. Add fair-use logic:
   - compute pressure state normal/warm/heavy/suspected_shared/fair_use;
   - do not ban based only on multiple IPs;
   - only combine traffic pressure + ASN/country/IP churn;
   - fair-use routing must be feature-flagged before enforcement.

10. Add admin UI:
   - node capacity dashboard;
   - key pressure dashboard;
   - subscription render debug;
   - drain/undrain controls;
   - key rotate/manual review controls.

In POKROV-app:

11. Update app_first_runtime_bootstrap.dart:
   - fetch candidates;
   - measure RTT;
   - POST /nodes/select;
   - fetch managed profile for selected node when needed;
   - keep telemetry best-effort;
   - manual location uses mode=manual, not fake RTT=1;
   - do not block connection if telemetry fails.

12. Update locations UI:
   - "Auto" means backend chooses fastest healthy route;
   - manual country applies on reconnect;
   - show current node when runtime stats are available;
   - do not expose internal fair-use/drain labels.

Testing:

13. Add backend tests for:
   - saturated node reject;
   - stale node reject;
   - active_clients not used as online;
   - UserNode mapping not limiting candidates;
   - subscription dynamic ordering;
   - key pressure family-safe behavior;
   - fair-use scoring;
   - provisioning all paid nodes;
   - app select contract.

14. Add app tests for:
   - candidates -> select -> managed profile flow;
   - manual selection uses mode=manual;
   - telemetry failure does not block connect;
   - UI reconnect hint.

Acceptance:

- Existing subscription links continue to work.
- External clients get compatible configs.
- Own app gets better immediate node choice.
- One overloaded node stops being first for new renders.
- Families are not banned just for multiple IPs.
- Operator can see why a node/key was scored a certain way.
- All new enforcement can be disabled by feature flags.
```

---

## 27. Source notes for implementation

Use these docs as technical anchors:

- Xray stats: `stats` object enables internal stats; user traffic stats are keyed by email, and user stats require email.
- Xray metrics: local metrics endpoint can expose `/debug/vars` with stats for inbound/outbound/user and observatory data.
- Xray API: `HandlerService` can add/delete users for VLESS/VMess/Trojan/Shadowsocks, and `StatsService` provides built-in stats access.
- Xray observatory/burstObservatory: HTTPing-style outbound health probes are available, but should be only one signal.
- sing-box urltest: supports testing outbounds by URL/interval/tolerance and can interrupt existing connections if configured.
- sing-box selector: supports default outbound and selectable outbounds, but arbitrary clients may not expose/control selector consistently.

Reference URLs:

```text
https://xtls.github.io/config/stats.html
https://xtls.github.io/config/metrics.html
https://xtls.github.io/config/api.html
https://xtls.github.io/config/observatory.html
https://sing-box.sagernet.org/configuration/outbound/urltest/
https://sing-box.sagernet.org/configuration/outbound/selector/
```

---

## 28. Final mental model

Stop thinking:

```text
сколько людей онлайн?
```

Start thinking:

```text
какая нода может принять ещё трафик?
какой ключ создаёт давление?
какой список нод надо отдать этому subscription token прямо сейчас?
какую ноду собственное приложение должно выбрать до подключения?
какие старые соединения не трогать?
что показать оператору, чтобы он понял проблему за 10 секунд?
```

POKROV должен стать не системой “пользователь = один девайс”, а системой:

```text
Account + AccessKey + NodeCapacity + KeyPressure + SubscriptionSteering
```

Это честная архитектура для VPN-сервиса, который одновременно поддерживает своё приложение и любые внешние клиенты.
