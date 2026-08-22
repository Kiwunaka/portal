# POKROV Marketing

Last updated: 2026-08-13

## Document Status

Document class: CANONICAL. This file is the local authority for `marketing/`,
the public site at `https://pokrov.space/`, and the acquisition, SEO, public
copy, and checkout-entry surfaces.

The browser cabinet lives in `webapp/` at `https://app.pokrov.space/`. The
primary operator surface lives in `adminapp/` at `https://admin.pokrov.space/`;
the old webapp admin routes are a retained parity fallback only.

## Current Surface Map

- `/` is owned by `marketing/src/app/page.tsx`. Its trust-led sequence is
  `Hero`, `HonestyStrip`, `Steps`, `Showcase`, `Pricing`, `Faq` and `FinalCta`;
  the retired service-claim grid must not be remounted as a parallel homepage
  promise surface.
- Shared public metadata, FAQ, sitemap paths, and JSON-LD helpers live in
  `marketing/src/lib/marketing-site.ts`.
- Reusable search-intent pages use `marketing/src/components/seo/seo-content-page.tsx`
  and the registry in `marketing/src/lib/seo-pages.ts`; the compact scenario
  pages continue to use `marketing/src/components/intent/intent-landing.tsx`.
- `/checkout/` is the public hosted-checkout continuation entry.
- `/install/` is the public install/help entry.
- `/support/` is the short support entry and reuses the canonical
  `/support/install/` task page instead of falling through to the homepage.
- `/offer/` and `/privacy/` are legal pages.

## Surface Boundary

Public marketing should:

- explain the app-first POKROV path;
- lead to install, checkout, cabinet, support, and legal pages;
- lead with the strongest current product proof and place relevant availability
  limits after that proof;
- use visible `VPN` / `ВПН` wording only on search-intent surfaces where it
  helps users and follows the root wording rule;
- use `лучший VPN` / `best VPN` on dedicated search-intent surfaces

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
   on the reusable `IntentLanding` template.
3. Keep `/vpn/` as the broad download-intent longform page.
4. Keep `/best-vpn/` and `/compare/free-vpn/` as proof-first comparison-intent
   pages with qualified `лучший VPN` wording and current product facts.
5. Reduce repeated proof cards and section descriptions before adding new
   marketing blocks.
6. Keep checkout/install/legal SEO facts accurate.
7. On 390 px mobile, keep the first screen to one short meaning and a primary CTA; move troubleshooting and secondary detail into existing accordions or disclosures.
8. The trial `5 days` fact may link to the compact checkout continuation, while the adjacent price fact remains exactly `от 99 ₽` / `за полный месяц`.

## Density Ownership

| Route family | Owner | Density rule |
| --- | --- | --- |
| `/` | `marketing/src/components/home/homepage.tsx` | Homepage-specific acquisition path; keep one primary story and one primary CTA above the fold. |
| `/mobile/`, `/devices/`, `/telegram/`, `/youtube/`, `/tiktok/` | `marketing/src/components/intent/intent-landing.tsx` | Reusable SEO landing template; keep the compact sequence `hero -> scenario -> pricing -> FAQ -> related links -> CTA`. |
| `/vpn/` | `marketing/src/app/vpn/page.tsx` | Dedicated broad download-intent longform surface with proof-first `VPN` / `ВПН` copy. |
| `/best-vpn/`, `/compare/free-vpn/`, platform/install/trust/support intent routes | `marketing/src/lib/seo-pages.ts` plus `marketing/src/components/seo/seo-content-page.tsx` | Answer-first pages may use qualified `лучший VPN` claims when the named scenario and supporting facts are visible together. |
| `/checkout/`, `/install/`, legal pages | route-local pages under `marketing/src/app/` | Task pages, not acquisition proof walls; keep facts and release limits accurate. |

Marketing CSS variables should bridge through `shared/design-tokens.json` via
`getDesignTokenCssVariables("public")`; route-specific exceptions need a clear
reason in the route or this README.

Motion is progressive and bounded. Reveal content is visible in server HTML
and becomes observer-driven only after its own client island hydrates; compact
stagger groups use at most 60 ms per item and 240 ms total, while long lists do
not stagger. Hero chips finish after two cycles. With OS Reduce Motion enabled,
the desktop showcase renders every screen in normal document flow instead of
creating the sticky track, spatial hero motion is absent, and carousel scroll
actions are immediate. The mobile showcase always exposes previous/next
controls and an announced `Экран N из M` position.

The 2026-08-22 production build measured the shared Framer Motion chunk at
141.5 KiB minified / 47.2 KiB gzip. Marketing therefore uses strict
`LazyMotion` with an asynchronous `domAnimation` feature bundle and minimal
`m` components; layout-only motion must not reintroduce `domMax` without a new
measurement and user-visible need. The resulting feature split is 43.5 KiB
minified / 17.1 KiB gzip, a 98.0 KiB / 30.1 KiB reduction for that measured
animation payload.

Install platform tabs use automatic activation with one tab in the keyboard
order. Left/Right arrows wrap, Home/End select the boundary tabs, and focus,
`aria-selected` and the visible panel move together. `check:responsive` proves
that keyboard contract and runs `axe-core` on the homepage and install route;
any serious or critical finding fails the check alongside the existing
responsive, no-JavaScript and reduced-motion matrix.

`check:responsive` builds the production static export, applies the same
dot-joined Next segment-payload aliases expected by a plain static host, and
serves `out/` through the pinned Python toolchain. It deliberately does not use
the Next development server or Fast Refresh as release evidence.

## Verification

Run from `marketing/`:

```powershell
npm.cmd run build
npm.cmd run check:seo
npm.cmd run check:responsive
```

Browser performance samples are collected only against an explicitly named
owned environment. `npm.cmd run collect:performance -- ...` emits a numeric
array for one allowlisted LCP/CLS/TBT or cabinet route-content metric; it does
not assert PASS. Sampling rules, budgets, evidence normalization and current
manual gates are owned by
`docs/operations/performance-and-local-quality-gate.md`.

Run from the repository root when visible Russian copy changes:

```powershell
python -m pytest tests/test_frontend_text_integrity.py tests/test_public_copy_guardrails.py -q
```

## Claim governance and commercial pilot

Public copy is constrained by the generated marketing-governance registry and
its canonical evidence references. Trust-led owned copy is the repository
default; service-led or advertising profiles remain blocked until a real,
non-expired owner legal record names the permitted channels. Checkout price,
deadline, terms, availability and commercial lineage remain server-owned.

The 1.2.0 winback package is local and fail-closed. Marketing must not turn its
draft contract into a public campaign, infer eligibility, reset its 72-hour
deadline or select a winner from CTR. The operational owner and external gates
are documented in `docs/operations/marketing-governance-and-winback-pilot.md`.

## Trust And Guide Routes

The public selected-feature catalog owns these static/export-safe routes:

- `/status/` for current and recent operator-owned incidents;
- `/support/` and `/support/install/` for the same compact installation and
  connection-help task;
- `/transparency/` for responsibility and field-level privacy facts;
- `/fallback/` for official fallback-client guidance and the owner-approved
  temporary Apple account best-effort boundary;
- `/programs/` for switch, research, and team-pack intake explanations;
- `/guides/` for 46 searchable instructions, category filters, failure
  branches, proactive fallback setup, 18 real screens across seven fallback
  clients, and a per-task visual target; results stay collapsed until the user
  opens the one instruction they need;
- `/guides/pokrov-app/` for the separate 22-screen Android atlas whose primary
  screens are real Huawei and LDPlayer captures from the public stable 1.1.1 APK,
  with non-obscuring numbered target outlines and
  button-by-button legends; capture metadata lives in a disclosure instead of
  competing with the search task.

All routes consume `shared/trust-and-guides.json` through the typed shared
module. `shared/guide-visuals.ts` must cover every guide ID. Fallback-client
tasks use reviewed real screenshots where available and an explicitly labelled
reconstruction only when no safe source exists. Each real screen records the
exact action and its source. `shared/pokrov-screen-atlas.ts` owns the
separate application-screen registry and every referenced screenshot must be a
redacted current-candidate capture. Guide videos remain unpublished until a
clean, redacted recording is attached to the matching guide ID.
