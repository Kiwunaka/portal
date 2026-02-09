# Ops: Control Plane

The control-plane node runs:
- `portal-bot` systemd service
- `portal-api` systemd service
- `portal-node-metrics.timer` (every 60s runtime metrics / health score)
- Caddy for WebApp + panel reverse proxy (optional)

## Environment variables

Use `/root/portal_bot/.env` on the server (not committed):

- `BOT_TOKEN`
- `ADMIN_ID`
- `DATABASE_URL` (usually `sqlite:////root/portal_bot/portal.db`)
- `PUBLIC_API_BASE_URL` (e.g. `https://<your-domain>:2096`)
- `WEBAPP_URL` (e.g. `https://<your-domain>:8444/webapp/`)

Legacy single-node fallback (only used if `nodes` table is empty):
- `PANEL_URL`, `PANEL_PATH`, `PANEL_USER`, `PANEL_PASS`, `INBOUND_ID`
- `HOST_DOMAIN`, `VLESS_*`

## Backups

- Backup `portal.db` daily (cron).
- Keep at least 7 days.

## Logs

- `journalctl -u portal-bot -f`
- `journalctl -u portal-api -f`
- `journalctl -u portal-node-metrics.service -f`

## Node Metrics Timer

Install/update timer on brain:

```bash
python scripts/remote_install_node_metrics_timer.py --brain-ip 82.21.114.104 --ssh-port 29374
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

## Local Ops Scripts

Many repo root scripts use SSH (paramiko). Install dependencies locally:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\pip.exe install -r requirements-ops.txt
pip install -r requirements-ops.txt
```
