# WO-002 Marketing, Public Checkout, Install, Legal

Status: draft
Agent: W02
Lane: platform
Priority: P0

## Goal

Make the public site truthful for open public beta: checkout only when safe, install/download states honest, legal/support copy limitation-aware, and no public platform promise unsupported by evidence.

## Write Scope

- `marketing/src/**`
- `shared/copy.ts`
- `copy/catalog.ru.json`
- `shared/public-urls.json`
- `shared/product-facts.json`
- `docs/product/portal-vpn-product.md`
- `docs/user/portal-vpn-user-guide-ru.md`
- `docs/developer/work-orders/2026-04-public-beta-release/**`

## Acceptance

- Public checkout CTA uses canonical checkout host and can show unavailable/maintenance when gates are red.
- Android/Windows download copy reflects release gate state.
- Legal/refund/support pages do not promise stable/SLA/store availability.
- Public acquisition does not route to raw `connect.pokrov.space`.

## Validation

```powershell
cd marketing
npm.cmd run build
npm.cmd run check:seo
cd ..
python scripts/check-links.py
python -m pytest tests/test_public_copy_guardrails.py -q
```

