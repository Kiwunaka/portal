---
name: admin-webapp-smoke
description: Run focused smoke checks for Portal Admin WebApp routes and admin API bindings after frontend or API contract changes.
---

# Admin WebApp Smoke

## When to use
- After changes in `webapp/src/app/(dashboard)/admin/*` or `webapp/src/lib/api.ts`.
- Before release for admin operations (users, tickets, promos, broadcast, referrals, bonuses).

## Steps
1. Build check:
- `cd webapp && npm.cmd run build`

2. Access gate:
- non-admin session must not stay on `/admin/*`.
- admin session must see all sections and load data.

3. Section smoke:
- Dashboard: summary + metrics/timeseries load.
- Users: open card, send message, extend, block/unblock, regenerate token.
- Nodes: health table, sync action, traffic rows.
- Tickets: list, status update, reply.
- Promos: create/update/delete promo, create gift code, toggle/create/delete plan.
- Broadcast: send by segment, optional `tg_ids`, live-updates create/update/delete.
- Referrals: start-link create/update/deactivate, campaign links builder.
- Bonuses: wheel config load/update (`preset`, `weights`, `cooldown_hours`).

4. Link sanity:
- verify admin/user CTA links point to `https://t.me/net4ebur_bot` where expected.

5. Log/report:
- capture failures with route + action + API error body.
- append release note in `docs/`.
