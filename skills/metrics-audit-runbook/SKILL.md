---
name: metrics-audit-runbook
description: Validate Portal metrics pipeline end-to-end (collector, timer, DB freshness, admin API/timeseries). Use after backend/ops changes touching monitoring or node telemetry.
---

# Metrics Audit Runbook

## When to use
- After edits in `scripts/collect_node_metrics.py`, `portal_bot/api.py`, `portal_bot/models.py`, `portal_bot/migrations.py`.
- Before release when admin dashboard depends on health/timeseries data.

## Steps
1. Data model sanity:
- verify `node_health_samples` includes traffic counters (`total_up_bytes`, `total_down_bytes`, `total_traffic_bytes`).

2. Local regression:
- `python -m unittest tests/test_api_auth_and_tickets.py`
- `python -m unittest tests/test_api_p0_extensions.py`

3. Collector smoke:
- `python scripts/collect_node_metrics.py --error-window 5 --source smoke`
- expect per-node lines with `healthy=`, `latency_ms=`, `active_clients=`, `up_bytes=`, `down_bytes=`.

4. Timer health (brain):
- `systemctl is-enabled portal-node-metrics.timer`
- `systemctl is-active portal-node-metrics.timer`
- `systemctl list-timers portal-node-metrics.timer --all`
- `journalctl -u portal-node-metrics.service -n 50 --no-pager`

5. API freshness:
- `GET /api/admin/metrics/status` -> `status=fresh`.
- `GET /api/admin/metrics/timeseries?from=YYYY-MM-DD&to=YYYY-MM-DD` returns daily points.
- `GET /api/admin/nodes/traffic?from=YYYY-MM-DD&to=YYYY-MM-DD` returns per-node traffic rows.

6. Document artifacts:
- write outcome to `docs/` with date, commands, and observed values.
