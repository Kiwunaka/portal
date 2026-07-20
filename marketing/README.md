# POKROV Marketing

Last updated: 2026-07-20

## Document Status

Document class: CANONICAL. This file is the local authority for `marketing/`,
the public site at `https://pokrov.space/`, and the acquisition, SEO, public
copy, and checkout-entry surfaces.

The browser cabinet lives in `webapp/` at `https://app.pokrov.space/`. The
primary operator surface lives in `adminapp/` at `https://admin.pokrov.space/`;
the old webapp admin routes are a retained parity fallback only.

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

## Copy And Paid-Rewards Gate

The Telegram start promise is always decomposed as:

> До 10 дней на старте: 5 дней бесплатно в приложении и ещё 5 дней после привязки Telegram и подтверждения подписки на канал.

`TELEGRAM_START_PROMISE` in `src/lib/seo-pages.ts` is the shared source for
that wording. Do not turn it into a direct Telegram `+10` claim; already issued
historical `+10` grants belong to authenticated account state, not acquisition
copy.

Paid-reward availability copy is build-time gated by
`NEXT_PUBLIC_PAID_REWARDS_MARKETING_ENABLED`. The default is off; only the exact
value `"1"` may render the shared message about the weekly wheel, activity
calendar, and rare `+30 days`. Do not publish reward weights or infer them from
visible sectors.

This marketing gate is the last rollout step. It may be enabled only after the
same deployed backend candidate has enabled and verified both independent
`BONUS_WHEEL_ENABLED` and `BONUS_CALENDAR_ENABLED` paths. Turning backend flags
off does not rewrite an already exported static site, so rollback also requires
a fresh marketing build/deploy with the public gate removed.

## Retained Density Guidance

The completed public-site density plan is retained guidance, not current
authority:
`docs/archive/design-plans/2026-06-06-web-admin-site-density-plan.md`.

Current priority:

1. Keep `/` as a homepage-specific, short acquisition path.
2. Keep `/mobile/`, `/devices/`, `/telegram/`, `/youtube/`, and `/tiktok/`
   on the reusable `MarketingLanding` template.
3. Keep `/vpn/` as a separate search-intent longform page because it has
   explicit `VPN` / `ВПН` SEO wording and a different evidence/copy boundary.
4. Reduce repeated proof cards and section descriptions before adding new
   marketing blocks.
5. Keep checkout/install/legal SEO facts accurate.

## Density Ownership

| Route family | Owner | Density rule |
| --- | --- | --- |
| `/` | `marketing/src/components/home/homepage.tsx` | Homepage-specific acquisition path; keep one primary story and one primary CTA above the fold. |
| `/mobile/`, `/devices/`, `/telegram/`, `/youtube/`, `/tiktok/` | `marketing/src/components/marketing-landing.tsx` | Reusable SEO landing template; keep the compact sequence `hero -> scenario -> pricing -> FAQ -> related links -> CTA`. |
| `/vpn/` | `marketing/src/app/vpn/page.tsx` | Dedicated search-intent longform surface; explicit `VPN` / `ВПН` wording is allowed only here and in matching metadata when it stays visible and useful. |
| `/checkout/`, `/install/`, legal pages | route-local pages under `marketing/src/app/` | Task pages, not acquisition proof walls; keep facts and release limits accurate. |

Marketing CSS variables should bridge through `shared/design-tokens.json` via
`getDesignTokenCssVariables("public")`; route-specific exceptions need a clear
reason in the route or this README.

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
