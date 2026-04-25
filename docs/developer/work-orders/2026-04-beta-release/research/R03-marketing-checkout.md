# R03 Marketing Checkout

Status: complete

## Scope

Marketing acquisition, checkout, install, legal, SEO landings, redirects, CTA consistency.

## Files/docs inspected

- `marketing/src/app/page.tsx`
- `marketing/src/components/home/homepage.tsx`
- `marketing/src/components/home/homepage.module.css`
- `marketing/src/components/marketing-landing.tsx`
- `marketing/src/components/json-ld.tsx`
- `marketing/src/app/checkout/page.tsx`
- `marketing/src/app/checkout/checkout-client.tsx`
- `marketing/src/app/install/page.tsx`
- `marketing/src/app/mobile/page.tsx`
- `marketing/src/app/tiktok/page.tsx`
- `marketing/src/app/youtube/page.tsx`
- `marketing/src/app/devices/page.tsx`
- `marketing/src/app/telegram/page.tsx`
- `marketing/src/app/offer/page.tsx`
- `marketing/src/app/privacy/page.tsx`
- `marketing/src/app/layout.tsx`
- `marketing/src/app/robots.ts`
- `marketing/src/app/sitemap.ts`
- `marketing/src/app/manifest.ts`
- `marketing/src/lib/marketing-site.ts`
- `marketing/src/lib/pokrov.ts`
- `marketing/package.json`
- `marketing/public/_redirects`
- `shared/copy.ts`
- `copy/catalog.ru.json`
- `shared/product-facts.json`
- `shared/public-urls.json`
- `shared/portal-config.ts`
- `shared/tariff-catalog.ts`
- `shared/tariff-catalog.json`
- `shared/access-matrix.json`
- `shared/promo-slots.json`
- `docs/product/portal-vpn-product.md`

## Current state

- confirmed: Root marketing uses the newer homepage component, with checkout-first CTAs generated from active tariff plans and `/checkout/?plan=...` links.
- confirmed: SEO intent pages `/mobile/`, `/tiktok/`, `/youtube/`, `/devices/`, and `/telegram/` share `MarketingLanding`, canonical metadata, breadcrumb JSON-LD, app-first copy, Android + Windows scope, 5-day trial copy, Free Monthly fallback, and key-first paid upgrade messaging.
- confirmed: `/checkout/` is implemented as a client checkout bridge. It fetches `/api/public/catalog`, falls back to shared tariff data, builds purchase URLs from `CANONICAL_CHECKOUT_URL` (`https://pay.pokrov.space/checkout/`), supports promo preview math, checks activation-key status, and sends redeem continuation to `app.pokrov.space/redeem/?key=...`.
- confirmed: `/checkout/` does not expose raw subscription/config delivery in source. Its public story is activation key -> redeem key -> managed premium.
- confirmed: `/install/` conditionally links real Android/Windows artifacts only when public env URLs exist. Without artifact URLs, it routes to help/cabinet/support instead of pretending a file exists.
- confirmed: legacy SEO redirects exist only in `marketing/public/_redirects`, from old `/vpn-*` slugs to canonical `/mobile/`, `/tiktok/`, `/youtube/`, `/devices/`, and `/telegram/` routes.
- confirmed: `npm.cmd run check:seo` passes in `marketing/`.
- needs local run: no browser render, mobile viewport screenshot, payment-provider continuation, or live API/catalog check was run because this work order is read-only and should edit only this report.

## Gaps against beta

- confirmed: The shared facts match the product doc for 5-day trial, +10 Telegram reward, Android + Windows public scope, Apple readiness-only scope, and canonical public/API/connect/pay hosts.
- confirmed: Checkout uses the right paid-beta commerce model (`buy_key`, `redeem_key`, `managed_premium`) via shared tariff catalog and `buildCheckoutHostHref`.
- confirmed: CTA direction is mostly consistent: homepage and landing pages converge to install or checkout, checkout converges to hosted pay, redeem, cabinet, Telegram fallback, or install.
- confirmed: `/checkout/` is marked `noIndex: true` even though the product doc says it is the primary public acquisition, pricing, paywall, and activation-key purchase surface.
- unknown: the checkout noindex setting may be intentional during beta, but it is a mismatch if paid beta requires search-indexable pricing.
- confirmed: Marketing source no longer contains direct public `VPN` wording except shared validation allowlists, the legacy `@pokrov_vpn` channel handle, the legacy compatibility host fact, and legacy redirect slugs.
- confirmed: SEO checker verifies canonical landing route files, redirect entries, sitemap source membership, and public `VPN`/old-brand strings, but it does not catch unsupported capability claims, fake review provenance, legal completeness, or mobile visual regressions.

## P0 blockers

- confirmed: unsupported public release claim. `marketing/src/components/marketing-landing.tsx:162` marks Android as `Public release`, while `docs/product/portal-vpn-product.md:81` says Android public promotion remains blocked until repo/static gates and physical-device release-build localhost/control-surface audit are green. Do not ship paid-beta public marketing with Android labeled public release until that release gate is actually satisfied, or relabel as beta/waitlist/install help.
- confirmed: unsupported homepage technical claims. `marketing/src/components/home/homepage.tsx:209` shows `AES-256 / WireGuard`, but canonical product facts and docs say default client core is `sing-box` and `xray` is advanced fallback; WireGuard/AES-256 is not established as a public promise in the inspected facts. Remove or replace with policy-safe generic connection wording before launch.
- confirmed: unsupported homepage availability/support claims. `marketing/src/components/home/homepage.tsx:47` says `Support 24/7`, and line 94 says a human answer is available any time. I found support channels, but no inspected SLA or staffing proof. This should be removed or backed by an operational SLA before paid beta.
- probable: hardcoded public reviews have no approval provenance. `marketing/src/components/marketing-landing.tsx:72-86` seeds named masked reviews with dated Android/Windows/Telegram stories, and the same component emits them into Review JSON-LD. Product rules allow approved reviews, but this implementation is hardcoded rather than fed from approved feedback evidence. Treat as a blocker unless these exact reviews are verified and approved.

## P1 beta polish

- confirmed: `/checkout/` noindex should be an explicit beta decision. If paid beta acquisition depends on organic discovery or indexed pricing, flip the metadata strategy; if not, document why checkout remains noindex while linked from indexed pages.
- confirmed: homepage visual implies a specific location (`Germany, Frankfurt` at `marketing/src/components/home/homepage.tsx:214`) while product direction says normal consumer UX should show one logical location and hide transport/node detail. Use a logical POKROV label unless that specific location is an intentional public promise.
- confirmed: checkout renders raw activation keys back to the page (`marketing/src/app/checkout/checkout-client.tsx:380`) and sends redeem continuation with `?key=` (`checkout-client.tsx:168-171`, `275`, `416`). This is not raw config delivery, but activation keys are still bearer-like. Consider POST/status lookup with a short continuation token or at least masking after validation.
- confirmed: `/checkout/` has public fallback pricing from `shared/tariff-catalog.json`.
- needs local run: launch should verify live `/api/public/catalog` exactly matches shared catalog before paid beta so stale prices do not appear when API fetch fails.
- confirmed: install page correctly avoids fake downloads if artifact env vars are empty, but it should be locally rendered with both empty and populated artifact envs before launch.
- confirmed: legal pages exist and link support/email/Telegram, but paid beta terms are thin: no visible seller/legal entity, refund window/process, payment processor terms, activation-key redemption rules, cancellation/non-recurring wording, or data retention details. Legal/compliance owner should expand before paid traffic.

## P2 defer

- confirmed: SEO landing pages are heavily shared via one component, which keeps facts consistent but may create similar content across `/mobile/`, `/tiktok/`, `/youtube/`, `/devices/`, and `/telegram/`. Acceptable for beta, but long-term SEO quality would improve with more page-specific content.
- confirmed: metadata and JSON-LD are present, but schema validation was not run in a rendered browser or Rich Results Test.
- confirmed: marketing CSS includes responsive breakpoints at `1180`, `980/920`, `780`, and `560` px, plus `minmax(0, 1fr)` grid patterns. Needs visual QA rather than source-only confidence.

## Technical debt

- confirmed: There are two marketing landing systems: root homepage uses `components/home/homepage.tsx`, while SEO pages use `components/marketing-landing.tsx`. They are aligned in broad story but drift in claims; the root homepage is where the unsupported WireGuard/AES/24-7/Frankfurt claims appeared.
- confirmed: `check-marketing-seo.mjs` does useful string/route checks but should be extended with launch-claim guardrails: no `Public release` when release docs say blocked, no transport claims (`WireGuard`, `AES-256`) unless sourced, no hardcoded reviews without an allowlist, and no unsupported SLA terms.
- confirmed: `copy/catalog.ru.json` still contains older marketing copy variants that are not all used by current root homepage/checkout. It should be pruned or mapped to active routes to reduce future copy drift.

## Security/privacy risks

- confirmed: no raw subscription/config links were found in normal marketing/checkout/install source.
- confirmed: `/checkout/` queries activation-key status via a URL path (`/api/access-keys/status/{key}`), which can put keys in access logs. If activation keys are bearer credentials, prefer a POST body or opaque lookup token.
- confirmed: redeem continuation places activation keys in a query string to the webapp.
- unknown: the key query handoff may be an intentional contract, but it should be reviewed for browser history, analytics, referrer, and support screenshot exposure.
- probable: legal privacy copy does not describe payment processor sharing or retention in enough detail for a paid checkout surface.

## Required implementation WOs

- R03-1: relabel Android/Windows download cards for beta truth, and remove any `Public release` wording until release gates are green.
- R03-2: replace unsupported homepage technical/location/SLA claims (`AES-256 / WireGuard`, `Germany, Frankfurt`, `Support 24/7`, human answer any time) with sourced, product-safe copy.
- R03-3: remove hardcoded testimonial/review JSON-LD or replace it with verified approved feedback from the moderation source.
- R03-4: decide and document `/checkout/` indexability for paid beta; update metadata if checkout should be indexable.
- R03-5: expand legal pages for paid beta seller/payment/refund/redemption/privacy specifics.
- R03-6: review activation-key status/redeem transport for URL/log leakage and mask key display where practical.
- R03-7: add static claim checks to `marketing/scripts/check-marketing-seo.mjs`.

## Validation commands

- confirmed: `npm.cmd run check:seo` in `marketing/` passed.
- needs local run: `npm.cmd run build` in `marketing/` was not run to avoid generating build output during this read-only research task.
- needs local run: render `/`, `/checkout/`, `/install/`, `/mobile/`, `/tiktok/`, `/youtube/`, `/devices/`, `/telegram/`, `/offer/`, and `/privacy/` at desktop and mobile widths; check for text overflow, broken navigation, and hydration errors.
- needs local run: live `/api/public/catalog` response against `https://api.pokrov.space/api/public/catalog`.
- needs local run: hosted checkout continuation against `https://pay.pokrov.space/checkout/?plan=...` with a safe test path.
- blocked by missing access: cannot verify payment provider merchant/legal requirements or real approved-review provenance from repository source alone.

## Evidence links

- `marketing/src/components/marketing-landing.tsx:72-86` - hardcoded default reviews.
- `marketing/src/components/marketing-landing.tsx:119` - public pages avoid raw subscription link and use activation key.
- `marketing/src/components/marketing-landing.tsx:162-177` - Android/Windows `Public release` cards and Apple readiness card.
- `marketing/src/components/home/homepage.tsx:47` - `Support 24/7` proof point.
- `marketing/src/components/home/homepage.tsx:94` - human answer any time support bullet.
- `marketing/src/components/home/homepage.tsx:209` - `AES-256 / WireGuard` visual claim.
- `marketing/src/components/home/homepage.tsx:214` - specific Germany/Frankfurt visual location.
- `marketing/src/app/checkout/page.tsx:17` - checkout `noIndex: true`.
- `marketing/src/app/checkout/checkout-client.tsx:105-118` - public catalog fetch candidate bases.
- `marketing/src/app/checkout/checkout-client.tsx:129-132` - activation-key status lookup path.
- `marketing/src/app/checkout/checkout-client.tsx:168-171` - redeem URL construction with key query param.
- `marketing/src/app/checkout/checkout-client.tsx:274-275` - hosted checkout and redeem href construction.
- `marketing/src/app/checkout/checkout-client.tsx:412-416` - hosted checkout and redeem CTAs.
- `marketing/src/app/install/page.tsx:13-20` - artifact/help fallback helpers.
- `marketing/src/app/install/page.tsx:153-192` - Android/Windows artifact conditional rendering.
- `marketing/public/_redirects:1-10` - legacy SEO redirects.
- `shared/product-facts.json:12-24` - 5-day trial, +10 Telegram reward, Android/Windows public scope, Apple readiness-only.
- `shared/public-urls.json:3-7` - canonical public, webapp, API, connect, and checkout hosts.
- `shared/tariff-catalog.json:5-14` - key-first commerce model and public surface policy.
- `docs/product/portal-vpn-product.md:81` - Android release still blocked until release-build localhost/control-surface audit.
- `docs/product/portal-vpn-product.md:157-160` - marketing route roles and canonical SEO landing family.
- `docs/product/portal-vpn-product.md:198-202` - checkout-first acquisition and no raw subscription links in default UX.
