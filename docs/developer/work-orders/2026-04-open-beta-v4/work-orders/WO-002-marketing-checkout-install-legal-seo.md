# WO-002 Marketing, Checkout, Install, Legal, SEO

Status: historical work order; current beta decision synced 2026-05-26
Owner: W02

## Scope

- `marketing/`.
- `shared/copy.ts`.
- `copy/catalog.ru.json`.
- `shared/product-facts.json`.
- `shared/public-urls.json`.
- Public checkout, install, legal, metadata, schema, and links.

## Acceptance

- Checkout state is truthful when Lava.top proof is green or blocked.
- Android and Windows availability states do not overclaim.
- Public copy avoids direct public `VPN` product wording except legacy or technical contexts.
- Metadata, schema, OG, Twitter, robots, sitemap, manifest, favicon, and app icons are release-ready.

## Verification

```powershell
Push-Location marketing
npm.cmd run build
Pop-Location
python scripts/check-links.py
python scripts/ui_visual_smoke.py
```
