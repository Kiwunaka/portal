# POKROV Atlas Glass Component Inventory

Last updated: 2026-04-28

## Current Families

- `shell-primitives.tsx`: base surface, status badge, section header, metric card, dialog shell, form field, empty state, timeline, button/link class helpers.
- `cabinet/surface.tsx`: active cabinet route, KPI row, hero, section, list, card grid.
- `cabinet-page.tsx`: older cabinet page/section/fact/action primitives still used by some routes.
- `cabinet-primitives.tsx`: older operational primitives; retire after confirming usage.
- `admin-shell.tsx`: admin-only compact/dark panel, button, badge, table, field, KPI and empty-state helpers.

## Duplication To Reduce

- Page headers across shell, cabinet, older cabinet, and admin.
- Metric tiles across shell, cabinet KPI rows, fact grids, admin strips.
- Status badges across global, admin, and repeated tone maps.
- Surface/panel classes across `.glass-card`, `.stat-card`, `.node-card`, cabinet sections, admin panels, marketing cards.

## Target Primitive Contracts

- `Surface`
- `GlassPanel`
- `BentoCard`
- `MetricTile`
- `ActionCard`
- `StatusBadge`
- `ProgressMeter`
- `SkeletonBlock`
- `PageHeader`
- `EmptyState`
- `ErrorState`

## Token Gaps

- Dark semantic text, muted text, status bg/text/line, focus ring, nav active, table header/divider, skeleton, progress, shadows, and buttons.
- Marketing has independent `--lp-*` variables; reset should bridge to shared POKROV variables.
- `design-tokens.ts` maps `product` density to `public`; keep this in mind before relying on product density.

## Migration Notes

- Keep admin density and table helpers, but replace hardcoded tone maps gradually.
- Keep active cabinet/surface patterns as the migration base.
- Fold global visual classes into primitives where touched.
- Remove duplicated flattening overrides only when the replacement visual system is verified.
