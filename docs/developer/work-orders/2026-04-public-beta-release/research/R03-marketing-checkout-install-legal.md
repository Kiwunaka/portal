# R03 Marketing Checkout Install Legal

Status: DONE
Research date: 2026-04-25
Agent: R03
Scope: marketing, checkout, install, and legal truth for the open public beta release wave.

## Read Scope

- `AGENTS.md`
- `docs/README.md`
- `docs/product/portal-vpn-product.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/app-first-and-bonus-flows.md`
- `docs/operations/deployment-and-access.md`
- `docs/operations/monitoring-and-visibility.md`
- `docs/developer/developer-guide.md`
- `docs/developer/repository-map.md`
- `marketing/src/`
- `shared/copy.ts`
- `copy/catalog.ru.json`
- `shared/public-urls.json`
- `shared/product-facts.json`
- `shared/portal-config.ts`
- inherited paid-beta evidence: `docs/developer/work-orders/2026-04-beta-release/research/R03-marketing-checkout.md`
- inherited paid-beta W02 evidence: `docs/developer/work-orders/2026-04-beta-release/evidence/logs/WO-002-marketing-checkout-install.md`

## Source-Of-Truth Baseline

- confirmed: public brand is `POKROV`; direct public product wording should not use direct-meaning `VPN`.
- confirmed: public scope is Android + Windows; Apple is readiness-only for this wave.
- confirmed: trial is `5 days`; Telegram reward is `+10 days`; default commerce model is buy activation key, redeem key, managed premium.
- confirmed: canonical hosts are centralized in `shared/public-urls.json`: `https://pokrov.space/`, `https://app.pokrov.space/`, `https://api.pokrov.space/`, `https://connect.pokrov.space/`, and `https://pay.pokrov.space/checkout/`.
- confirmed: `connect.pokrov.space` is config/connect delivery only, not an acquisition or pricing surface.

## Current Marketing/Checkout/Install Truth

- confirmed: homepage CTAs in `marketing/src/components/home/homepage.tsx` route into `/checkout/?plan=...`, `/install/`, cabinet, support, or channel; I did not find a normal acquisition CTA to `connect.pokrov.space`.
- confirmed: shared SEO landing helper routes checkout CTAs to `/checkout/?plan=...` and install CTAs to `/install/`; direct artifact delivery was removed by inherited W02 work.
- confirmed: `/checkout/` builds hosted pay URLs through `buildCheckoutHostHref()`, which starts from `CANONICAL_CHECKOUT_URL` and therefore points to `https://pay.pokrov.space/checkout/` (`marketing/src/lib/marketing-site.ts:246-247`, `marketing/src/app/checkout/checkout-client.tsx:280`).
- confirmed: checkout keeps the key-first story: buy activation key, redeem in app/cabinet, continue managed premium. It does not expose raw config/connect links in the inspected source.
- confirmed: install page does not expose public direct files by default. It gates Android/Windows buttons on public artifact env values and otherwise routes to help/cabinet/support (`marketing/src/app/install/page.tsx:43-44`, `marketing/src/app/install/page.tsx:178-206`).
- confirmed: install page tells Android truth as internal beta until signing and physical audit, and Windows truth as beta possibly unsigned (`marketing/src/app/install/page.tsx:175`, `marketing/src/app/install/page.tsx:198`).
- confirmed: direct public `VPN` wording was not found in marketing/copy/shared surfaces except the allowed validation code and legacy Telegram handles in `shared/copy.ts` / `shared/public-urls.json`.

## Highest-Risk Findings

1. confirmed: stale paid/invite-beta copy remains on public landing surfaces. `marketing/src/components/marketing-landing.tsx:430` says the wave is a paid beta with limited access, `marketing/src/components/marketing-landing.tsx:506-507` says access is invitation-limited and "Paid beta - up to 25 active users", and `copy/catalog.ru.json:70` says "Paid beta POKROV for Android and Windows". For an open public beta release, this is the highest copy-truth risk.

2. confirmed: primary checkout is still noindexed. `/checkout/` is the documented primary public acquisition/pricing/paywall route, but `marketing/src/app/checkout/page.tsx:17` sets `noIndex: true`; `/install/` also sets `noIndex: true` at `marketing/src/app/install/page.tsx:33`. If open public beta expects public discoverability or shared link previews through search/social crawlers, this needs an explicit release-captain decision.

3. probable: checkout copy implies email signup exists on the public site. `marketing/src/app/checkout/checkout-client.tsx:439` says "Email signup on the site gives only Free Monthly", while canonical docs say public email browser continuation must stay marked `soon` until sender identity, delivery confirmation, and public launch path are live. This should be reworded unless another agent has just shipped and verified email as a public path.

4. probable: Apple install catalog copy can read like a future product promise. Source UI fallback says Apple readiness/no false download, which is safe (`marketing/src/app/install/page.tsx:221`), but shared copy says the Apple version will be connected soon (`copy/catalog.ru.json:1170`). That is softer than a store claim, but for open public beta it may overpromise if Apple remains readiness-only.

5. needs local run: runtime artifact/download truth is not proven from source alone. Install behavior depends on `NEXT_PUBLIC_APP_ANDROID_APK_URL`, `NEXT_PUBLIC_APP_WINDOWS_EXE_URL`, `NEXT_PUBLIC_APP_DOCS_URL`, and cabinet `/downloads/` runtime behavior. A local build/render plus live `/api/client/apps` or release-handoff smoke is needed before declaring public install safe.

## Additional Findings

- confirmed: legal pages now contain beta limits, activation-key redemption, refund/dispute support handling, Android audit/signing caveat, unsigned Windows warning, and best-effort support without production SLA (`marketing/src/app/offer/page.tsx:45-55`).
- confirmed: privacy page says payment events include order/status/amount/provider status and manual reconciliation, and says card data is not stored by POKROV (`marketing/src/app/privacy/page.tsx:44`).
- confirmed: privacy page says external payment provider sharing is limited to payment/refund/dispute/support needs (`marketing/src/app/privacy/page.tsx:52`).
- probable: legal is still thin for a fully open public beta. I did not find a seller/legal entity, jurisdiction, formal refund window, provider terms link, data retention periods, or deletion request process in the inspected legal source.
- confirmed: marketing structured data sets `downloadUrl` to `/install/`, not to raw app artifacts or `connect.pokrov.space` (`marketing/src/lib/marketing-site.ts:210`).
- confirmed: checkout uses activation-key status in a URL path and redeem continuation in a query string. This is inherited from paid-beta R03 and remains a privacy/security review item, but it is not raw connect delivery.
- unknown: live hosted checkout provider state was not checked. Source points to the canonical pay host, but I did not verify merchant availability or payment-provider copy/access.
- blocked by missing access: I cannot verify payment-provider legal requirements, refund execution policy, actual merchant identity, or provider-dashboard state from repository source alone.
- needs local run: no `marketing` build, link check, browser screenshot, or hosted checkout flow was run in this R03 pass because the instruction was to edit only this research file in a shared dirty worktree.

## Public Beta Readiness Notes

- confirmed: no raw `connect.pokrov.space` acquisition CTA was found in inspected marketing source; `CANONICAL_CONNECT_URL` is exported through shared config but not used as a public acquisition href in the marketing files scanned.
- confirmed: no direct public `VPN` copy regression was found beyond allowed handles/validators.
- confirmed: no App Store or Google Play availability claim was found in the inspected source.
- confirmed: no production SLA promise was found; offer explicitly says best-effort up to 24 hours and no production SLA.
- probable: the word "paid beta" and invite-limited language is now the main public-beta positioning blocker, not the inherited W02 technical claims.

## Recommended Release-Captain Decisions

- Decide whether open public beta should replace all "paid beta", "invitation-limited", and "up to 25 users" copy before launch.
- Decide whether `/checkout/` must remain `noindex` for beta safety or become indexable as the primary public acquisition route.
- Confirm whether public email signup is actually live. If not, reword checkout to "email soon" or remove the Free Monthly email sentence.
- Confirm Apple wording should remain readiness-only without "soon" language.
- Run marketing build, link check, mobile/desktop render, checkout hosted-pay smoke, and install/download smoke after W02/W03/W06 changes settle.

