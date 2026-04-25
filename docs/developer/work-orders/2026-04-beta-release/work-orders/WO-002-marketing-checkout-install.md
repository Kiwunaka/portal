# WO-002 Marketing, Checkout, Install, Legal

Status: draft
Lane: platform

## Scope

Make marketing a real paid beta acquisition path, not a decorative storefront.

## Assigned Paths

- `marketing/src/**`
- `marketing/public/**`
- `shared/copy.ts`
- `copy/catalog.ru.json`
- `shared/product-facts.json`
- `shared/public-urls.json`
- `docs/product/portal-vpn-product.md` if behavior/copy contract changes

Use explicit lock before editing shared copy/fact files.

## Required Changes

- Homepage positions POKROV as paid beta when expectations matter.
- Checkout uses the canonical tariff catalog and real next steps.
- Install page routes to cabinet-gated beta downloads or truthful blocked/internal states.
- Legal/refund/support copy reflects paid beta limits.
- SEO landings converge to the same checkout/install/cabinet story.
- No direct public `VPN` wording, fake claims, stale trial/bonus/pricing, raw config delivery, or unavailable artifacts shown as live.

## Validation

- `cd marketing; npm.cmd run build`
- `cd marketing; npm.cmd run check:seo`
- `python scripts/check-links.py`
- `python scripts/ui_visual_smoke.py`
- `python -m pytest tests/test_public_copy_guardrails.py -q`

## Handoff Format

- What I checked
- What I found
- What I changed
- How I verified
- What remains / risk

