# Free Tier: отдельный inbound `:8443` + лимит 50 Mbps

Цель: у Free-пользователей отдельный входной порт `8443` на PL-ноде и ограничение скорости **50 Mbps суммарно на порт**.

Важно:
- Лимит через `tc` в этой схеме **общий на всех Free одновременно** (не "50 Mbps на каждого").
- "1 ключ = 1 устройство" реализуется только приближённо: через `limitIp` (лимит на одновременное число IP).

## 1) Сделать отдельный inbound на PL-ноде (порт 8443)

На PL-ноде в 3x-ui:
1. `Inbounds` -> добавить новый inbound `VLESS Reality`.
2. Порт: `8443`.
3. Все параметры Reality и transport (private key, shortIds, serverNames/SNI, flow, fingerprint) сделать **такими же**, как у основного inbound `443`, чтобы поведение совпадало.
4. Сохранить inbound и записать его `inbound_id` (он нужен в `portal.db` как `pl_free.inbound_id`).

## 2) Добавить запись `pl_free` в `portal.db`

Идея: Free использует `code=pl_free`, а платные используют `pl` + остальные страны.

Нода `pl_free` должна быть как `pl`, но:
- `code`: `pl_free`
- `vless_port`: `8443`
- `inbound_id`: ID inbound на `8443`
- Reality-параметры: такие же, как у `pl`
- `enabled`: `true`

## 3) Креды панели: только через env (без секретов в репо)

На control-plane (brain) в `/root/portal_bot/.env`:
- `NODE_PL_PANEL_USER` / `NODE_PL_PANEL_PASS`
- `NODE_PL_FREE_PANEL_USER` / `NODE_PL_FREE_PANEL_PASS` (обычно те же, что `PL`)

Если нужно переопределить URL/путь панели:
- `NODE_PL_PANEL_BASE_URL`, `NODE_PL_PANEL_PATH`
- `NODE_PL_FREE_PANEL_BASE_URL`, `NODE_PL_FREE_PANEL_PATH`

## 4) Ограничить скорость Free (Linux `tc`)

На PL-ноде (root):
```bash
cd /root
# PORT=8443 RATE=50mbit - по умолчанию такие
PORT=8443 RATE=50mbit ./install_free_egress_shaper.sh
```

Проверка:
```bash
tc -s qdisc show
tc -s class show
systemctl status portal-free-egress-shaper.service
```

## 5) "1 ключ = 1 устройство" (приближённо)

В 3x-ui у клиента есть поле `limitIp`. Мы выставляем его для `pl_free`.

Это не "количество устройств", а **количество одновременных IP**.

Рекомендация по умолчанию:
- `NODE_PL_FREE_LIMIT_IP=2` (мягче для юзеров: телефон + ноут)


## 6) Current default plan policy (bot/API)

- Free defaults:
  - `FREE_LIMIT_IP=2`
  - `FREE_TOTAL_GB=40`
- Paid defaults:
  - `PAID_LIMIT_IP=5`
  - traffic is unlimited by design

Node-specific overrides are supported via `NODE_<CODE>_...`, for example:
- `NODE_PL_FREE_LIMIT_IP=2`
- `NODE_PL_FREE_TOTAL_GB=40`

## 7) Optional: per-IP 50 Mbps limiter (closest to "per user")

If you need closer behavior to "50 Mbps each", use per-IP limiter on Free port:

```bash
cd /root
PORT=8443 RATE_KBPS=6250 BURST_KB=512 ./install_free_per_ip_limiter.sh
```

Files:
- `infra/setup_free_per_ip_limiter.sh`
- `infra/install_free_per_ip_limiter.sh`
- `scripts/remote_install_free_per_ip_limiter.py`

Notes:
- This is per-IP, not strict per account UUID.
- With `limitIp=2`, one account can use up to 2 IPs in parallel.
- Limiter is drop-based and can be less smooth than tc shaping.

## 8) Rollout status (2026-02-08)

- `pl` free inbound `:8443` now has per-IP limiter enabled in production.
- Installed via:

```bash
python scripts/remote_install_free_per_ip_limiter.py --code pl --ssh-port 29374 --port 8443 --rate-kbps 6250 --burst-kb 512
```

- Service/state expected on `pl`:

```bash
systemctl is-enabled portal-free-per-ip-limiter.service
systemctl is-active portal-free-per-ip-limiter.service
nft list table inet portal_free_rate
```

- Expected: `enabled`, `active`, and nft rules for both `input`/`output` on port `8443`.
