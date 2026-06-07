# POKROV Marketing

Last updated: 2026-06-07

## Document Status

This file is the local authority for `marketing/`, the public site at
`https://pokrov.space/`, and public acquisition/SEO/checkout entry pages.

The browser cabinet and admin surface live in `webapp/` at
`https://app.pokrov.space/`.

## Current Surface Map

- `/` is owned by `marketing/src/components/home/homepage.tsx`.
- Shared public metadata, FAQ, sitemap paths, and JSON-LD helpers live in
  `marketing/src/lib/marketing-site.ts`.
- Reusable SEO landing pages currently use
  `marketing/src/components/marketing-landing.tsx`.
- `/checkout/` is the public hosted-checkout continuation entry.
- `/install/` is the public install/help entry.
- `/offer/` and `/privacy/` are legal pages.

## Surface Boundary

Public marketing should:

- explain the app-first POKROV path;
- lead to install, checkout, cabinet, support, and legal pages;
- keep beta limitations honest;
- use visible `VPN` / `ВПН` wording only on search-intent surfaces where it
  helps users and follows the root wording rule;
- avoid hidden text, cloaking, keyword stuffing, unsupported "best" claims,
  and unsupported release/payment/store claims.

Public marketing should not:

- become a second cabinet;
- expose raw subscription links or QR as a normal first-layer path;
- imply store availability, trusted Windows signing, stable `1.0.0`, raw
  Android audit proof, production WARP proof, or RU-origin readiness;
- duplicate the same product story across many card-grid sections.

## Active Density Plan

The active public-site density plan is
`docs/design/2026-06-06-web-admin-site-density-plan.md`.

Current priority:

1. Keep `/` as a homepage-specific, short acquisition path.
2. Keep `/mobile/`, `/devices/`, `/telegram/`, `/youtube/`, and `/tiktok/`
   on the reusable `MarketingLanding` template.
3. Keep `/vpn/` as a separate search-intent longform page because it has
   explicit `VPN` / `ВПН` SEO wording and a different evidence/copy boundary.
4. Reduce repeated proof cards and section descriptions before adding new
   marketing blocks.
5. Keep checkout/install/legal SEO facts accurate.

## Verification

Run from `marketing/`:

```powershell
npm.cmd run build
npm.cmd run check:seo
npm.cmd run check:responsive
```

Run from the repository root when visible Russian copy changes:

```powershell
python -m pytest tests/test_frontend_text_integrity.py tests/test_public_copy_guardrails.py -q
```
