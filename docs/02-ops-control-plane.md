# Ops: Control Plane

The control-plane node runs:
- `portal-bot` systemd service
- `portal-api` systemd service
- `portal-helpbot`
- `portal-node-metrics.timer` (every 60s runtime metrics / health score)
- Caddy for WebApp + static/marketing
- production `Postgres` database
- `x-ui` installed for panel/API access and legacy compatibility, but not as the source of subscription delivery

## Environment variables

Use `/root/portal_bot/.env` on the server (not committed):

- `BOT_TOKEN`
- `ADMIN_ID`
- `DATABASE_URL`
- `PUBLIC_API_BASE_URL` (e.g. `https://<your-domain>:2096`)
- `WEBAPP_URL`

Current production note:
- on 7 March 2026 production services read `DATABASE_URL` from `.env` and use `Postgres`;
- local `portal.db` may still exist on disk, but it is not the production source of truth.

Legacy single-node fallback (only used if `nodes` table is empty):
- `PANEL_URL`, `PANEL_PATH`, `PANEL_USER`, `PANEL_PASS`, `INBOUND_ID`
- `HOST_DOMAIN`, `VLESS_*`

## Backups

- On production, back up `Postgres` daily (`pg_dump` or storage-level snapshot).
- Keep at least 7 days.
- SQLite backup instructions are relevant only for local/dev or historical snapshots.

## Logs

- `journalctl -u portal-bot -f`
- `journalctl -u portal-api -f`
- `journalctl -u portal-node-metrics.service -f`
- `journalctl -u portal-helpbot -f`

## Node Metrics Timer

Install/update timer on brain:

```bash
python scripts/remote_install_node_metrics_timer.py --brain-ip 82.21.114.104 --ssh-port 29374
```

Enable and verify on control-plane:

```bash
systemctl daemon-reload
systemctl enable --now portal-node-metrics.timer
systemctl status portal-node-metrics.timer --no-pager
systemctl list-timers --all | grep portal-node-metrics
```

Freshness sanity checks:

```bash
journalctl -u portal-node-metrics.service -n 50 --no-pager
set -a
. /root/portal_bot/.env
set +a
psql "$DATABASE_URL" -At -c "select max(sampled_at) from node_health_samples;"
```

Admin API freshness:
- endpoint: `GET /api/admin/metrics/status`
- requires real Telegram admin auth (`X-Telegram-Init-Data` or an authenticated admin WebApp session)
- expected: `{"status":"fresh", ...}`
- old checks with plain `X-Admin-Id` are no longer sufficient

Recovery procedure if stale:

```bash
systemctl restart portal-node-metrics.service
systemctl restart portal-node-metrics.timer
sleep 5
journalctl -u portal-node-metrics.service -n 50 --no-pager
```

## Brain Node: x-ui Subscription Port Conflict

On the brain node we keep the portal subscription endpoint on `:2096` (for URLs like `https://<domain>:2096/s8Kx2mP7qR4wT/<token>`).

Some 3x-ui builds start an internal "subscription service" on `:2096` by default, which conflicts with Caddy/portal.

Fix (brain only):
- Disable 3x-ui built-in sub server and move it away from `:2096` (we do not use it).
- Keys live in `/etc/x-ui/x-ui.db` table `settings`.

Example:

```bash
cp /etc/x-ui/x-ui.db /etc/x-ui/x-ui.db.bak-$(date +%Y%m%d-%H%M%S)
sqlite3 /etc/x-ui/x-ui.db "BEGIN; delete from settings where key in ('subEnable','subPort'); insert into settings(key,value) values('subEnable','false'); insert into settings(key,value) values('subPort','2097'); COMMIT;"
systemctl restart x-ui
```

Current runtime note (verified on 7 March 2026):
- `x-ui` on brain is `active`;
- `subEnable=false`;
- `subPort=2097`;
- portal-owned subscription endpoint remains on `:2096`.

## Current delivery topology

- `brain` is the control-plane host and currently disabled in the delivery pool.
- Enabled delivery nodes are `free`, `it`, `nl`, `pl`, `us`.
- Current standard delivery profile is `VLESS + TCP + Reality` on `443/tcp`.

## Local Ops Scripts

Many repo root scripts use SSH (paramiko). Install dependencies locally:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\pip.exe install -r requirements-ops.txt
pip install -r requirements-ops.txt
```
