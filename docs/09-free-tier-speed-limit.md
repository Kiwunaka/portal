# Free Tier policy and speed cap

> Historical note (2026-03-07): examples below reference the old `pl_free` contour. Current runtime truth for production is `free` as a dedicated free-node code plus a separate legacy `pl:8443` inbound. See `docs/36-node-source-of-truth-2026-03-07.md`.

## Target defaults

- `FREE_LIMIT_IP=1`
- `FREE_TOTAL_GB=30`
- `FREE_SPEED_LIMIT_KBPS=6250` (50 Mbps)
- `FREE_CYCLE_DAYS=30`

## Notes

- Free users should be provisioned on dedicated free nodes (for example `pl_free`).
- `limitIp` in panel is an IP-concurrency guard, not a strict device counter.
- Per-IP shaper (`6250 KB/s`) is closest to 50 Mbps per active IP on free port.
- Paid plans remain unlimited by traffic design, with `PAID_LIMIT_IP=5` by default.

## Monthly reset behavior

- FREE traffic cap resets every 30 days from activation anchor date.
- Existing FREE users get cycle anchor at migration/release time.
- New FREE users get cycle anchor when moved to FREE.
- Worker job applies due resets and shifts `next_reset_at` by +30 days.

## Optional node-level overrides

- `NODE_PL_FREE_LIMIT_IP=1`
- `NODE_PL_FREE_TOTAL_GB=30`

## Optional per-IP limiter

```bash
cd /root
PORT=8443 RATE_KBPS=6250 BURST_KB=512 ./install_free_per_ip_limiter.sh
```
