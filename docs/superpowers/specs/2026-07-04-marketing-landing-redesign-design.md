# POKROV Redesign — Sub-Project 1: Marketing Landing Rebuild

- Date: 2026-07-04
- Status: Draft for review
- Parent effort: global redesign wave `0 → 1 → 2 → 3`; foundation (sub-project 0) landed in commit `fbe332e`
- Foundation spec: `docs/superpowers/specs/2026-07-04-design-foundation-redesign-design.md`

## 1. Context And Goal

The current marketing site mixes two visual eras (a CSS-module homepage plus ~1600 lines of legacy `lp-*` global CSS used by every other page), reads machine-written, and ships framer-motion and gsap as dead dependencies. The owner wants the whole public surface rebuilt from scratch: premium Apple-HIG look on the new white/emerald foundation, human selling copy, smooth 60fps motion, and clear install instructions.

Competitor research (foundation spec, Appendix A) showed the RU Telegram-ecosystem VPN market has no premium-looking landing, no real product UI on any page, and inflated dishonest claims everywhere. This rebuild takes the opposite wedge: calm premium design, real product UI, honest checkable facts.

## 2. Owner Decisions (locked)

| # | Question | Decision |
|---|---|---|
| 1 | Wave scope | **All public pages** — home, /install, /checkout, 6 intent pages, /offer, /privacy. Legacy `lp-*` CSS dies completely |
| 2 | Hero concept | **A. Split** — promise + CTAs left, live SVG app UI right |
| 3 | Copy tone | **Mix** — premium calm headlines, warm human microcopy («карту не просим», «всё уже настроено») |
| 4 | Tech approach | **A. Stack upgrade** — Next 16 + Tailwind v4 + framer-motion (align with webapp); gsap removed |
| 5 | Theme | Light-only (foundation decision); theme toggle removed from marketing |

## 3. Scope

In scope (all inside `marketing/`, plus shared copy files):

- Migration: Next 14 → 16, Tailwind v4 introduction, removal of `lp-*` global CSS and `homepage.module.css`, removal of gsap and dead animation code
- Full rebuild of: home page, `/install/`, `/checkout/` (UI layer), intent-page template + 6 intent pages, `/offer/` + `/privacy/` (typography reskin only), topbar, footer
- New copy for all rebuilt surfaces, centralized in `copy/catalog.ru.json` via `shared/copy.ts`
- Live SVG app-UI illustrations (hero phone, showcase screens, step mini-screens)
- Motion system per section 8
- SEO preservation: metadata, JSON-LD, sitemap, robots, manifest, funnel tracker
- Docs: `docs/product/portal-vpn-product.md` positioning refresh in the same wave

Out of scope:

- Webapp/cabinet changes (sub-project 2); client app (sub-project 3)
- Checkout payment logic, tariff data, provider availability rules — UI reskin only
- Legal text content changes in `/offer/`, `/privacy/`
- HyperFrames promo video — separate post-launch task
- New photography/3D; all product visuals are SVG/CSS
- Backend, bots, `portal_bot/`

## 4. Hard Constraints (from AGENTS.md / canon)

- Static export (`output: "export"`, `trailingSlash: true`) must survive.
- Copy centralization: new public strings land in `copy/catalog.ru.json` + `shared/copy.ts` keys; structured facts keep coming from `shared/product-facts.ts`, `shared/tariff-catalog.ts`, `shared/portal-config.ts`, `shared/public-urls.json`.
- Wording: visible SEO-intent `VPN`/`ВПН` allowed on dedicated surfaces; no hidden/stuffed usage; no store availability, stable `1.0.0`, trusted signing, RU-origin, or silent auto-update claims; beta honesty preserved.
- No fake counters, fake reviews, or self-scored competitor tables (anti-patterns from research).
- Design tokens are the only color/type/motion source; no hand-written hex in components (Tailwind maps to `--pokrov-*` variables).
- Accessibility: WCAG AA, 44px touch targets, `prefers-reduced-motion` fade-only fallback, keyboard-visible focus.
- Download CTAs keep the current model: they route to the cabinet downloads flow via `buildCabinetDownloadsHref` (as `install/page.tsx` does today). Marketing does not hardcode binary URLs. **New integration:** the HonestyStrip GitHub reference needs a centralized `github_releases` entry added to `shared/public-urls.json` (+ accessor in `shared/portal-config.ts`) in this wave — no shared source currently holds the GitHub URL.

## 5. Tech Migration

Order of operations (each step keeps the build green):

1. **Next 14 → 16**: bump `next`, `react`, `react-dom`, `eslint-config-next`; adopt async `params`/`searchParams` where signatures changed; verify static export of all routes. Marketing has no middleware/API routes, so risk is contained to metadata APIs and font loader (already `next/font`).
2. **Tailwind v4**: add `@tailwindcss/postcss` (same setup as webapp); `globals.css` shrinks to `@import "tailwindcss"`, token bridge (`@theme` mapping `--pokrov-*` vars to Tailwind color/spacing/radius/shadow names), base element styles, and the few keyframes Tailwind cannot express. Utility-first styling in components; `cn()` helper copied from webapp pattern.
3. **framer-motion**: keep as the only animation dependency; **remove gsap** from `package.json`.
4. Delete `homepage.module.css` and all `lp-*` / `checkout-*` classes as pages migrate; the migration is complete when `rg "lp-" marketing/src` returns only false positives outside styles.
5. Theme toggle and `data-theme` script are removed from `layout.tsx`; the dark half of the emitted token CSS stays (harmless, shared emitter) but no UI exposes it. `color-scheme` stays `light`.

## 6. Component Architecture

New `marketing/src/components/` layout; every section is an isolated unit with typed props, consuming copy via keys and facts via shared modules:

```
components/
  ui/            Button, Chip, Card, SectionHeading, Accordion, PriceCard, StepCard — primitives on Tailwind + tokens
  motion/        Reveal (IO-based), Stagger, springs/durations re-exported from tokens
  illustrations/ AppPhoneSvg (connect screen), AppWindowSvg (Windows), StepMiniSvg×3 — pure SVG components, no rasters
  layout/        Topbar, Footer, PageShell
  home/          Hero, HonestyStrip, ServicesGrid, Steps, Showcase, Pricing, TelegramBonus, Faq, FinalCta
  intent/        IntentHero, ScenarioCards + template assembling home sections with scenario copy
  install/       PlatformTabs, InstallSteps (Android/Windows), InstallFaq
  checkout/      reskinned client component reusing ui/* (logic untouched)
```

Rules: one section = one file; sections compose primitives; no section imports another section; `JsonLd`, `FunnelTracker`, `MarketingBrandLogo` are reused as-is.

## 7. Page Blueprints

### 7.1 Home

1. **Topbar** — solid white; hairline border + slight shadow appear after 8px scroll; brand mark, anchors (Возможности · Цены · FAQ), «Кабинет» ghost link, «Скачать» primary pill.
2. **Hero (split)** — left: kicker chip «5 дней бесплатно · карта не нужна», H1 (primary candidate: «YouTube снова летает. И всё остальное тоже.»; fallback: «Интернет, который просто работает»), one-sentence sub («Приложение для Android и Windows: одна кнопка — и любимые сервисы снова быстрые»), CTAs «Скачать бесплатно» (pill, token `emerald`) + «Как это работает» (ghost, scrolls to Steps); fact row `5 дней · от 99 ₽/30 дней · Android + Windows · до 5 устройств на основных тарифах` from shared facts (the start_99 plan is 1 device — per-plan limits are shown on pricing cards, see §7.1.7). Right: `AppPhoneSvg` — connect screen with `status_green` ring, floating chips (route, «Подключено») animated on transform/opacity.
3. **HonestyStrip** — 4 items, each literally true today: «Триал без карты» (5 дней, карта не запрашивается), «Без автосписаний — оплата разовым ключом, ничего не продлевается само» (all plans are one-time activation keys, `fulfillment: "activation_key"`), «Файлы приложения — на GitHub Releases, у всех на виду» (links via the new `github_releases` public-urls entry; wording must not read as "open source" — the repo is release-only), «Живая поддержка в Telegram» (support bot from the registry). No cancellation-flow claims: there is no auto-renewal, so nothing needs canceling — the copy says exactly that.
4. **ServicesGrid** — outcome tiles (YouTube, TikTok, Instagram, Discord, ChatGPT and the rest of the currently-true service set from shared facts/copy); wording sells daily-life results, not transport tech.
5. **Steps** — «Скачай приложение → Нажми Подключить → Готово»; each step has a mini SVG screen; step 3 mentions the 5-day trial starting automatically.
6. **Showcase** — three app screens (connect, locations, account) in device frames; scroll-driven crossfade/slide (framer-motion `useScroll`, transform-only); Android and Windows frames both present.
7. **Pricing** — trial card first («5 дней бесплатно — карта не нужна»), then the one-time `start_99` welcome plan (99 ₽ / 30 дней, 1 устройство) and the 239/669/1199/1699/1999 ladder from `shared/tariff-catalog.json` with honest per-month math («12 месяцев — это около 167 ₽/мес») and **per-plan device limits on each card**; no competitor tables, no fake discounts; checkout links unchanged.
8. **TelegramBonus** — +10 дней за подписку на `@pokrov_vpn`; explicit claim flow wording from facts.
9. **FAQ** — rewritten human answers (installation, trial, payment, devices, «нечего отменять — автосписаний нет» framed per §7.1.3, Windows SmartScreen honesty); spring accordions; feeds FAQ JSON-LD.
10. **FinalCta** — token `emerald_soft` band, dark text, one primary CTA (no dark gradient; landing is light-only).
11. **Footer** — product/support/legal columns, Telegram registry (bot, support bot, channel), GitHub releases link (same `github_releases` accessor as HonestyStrip, §4), offer/privacy.

### 7.2 /install/

Platform tabs (Android / Windows), each a numbered `InstallSteps` list with real UI drawn as SVG (download → OS permission dialog → first connect). Download buttons route to the cabinet downloads flow (`buildCabinetDownloadsHref`), as today; the split-APK explanation (arm64 default, armeabi legacy) is informational copy about what the user finds there, not direct binary links. Android covers unknown-sources permission; Windows honestly covers SmartScreen («Windows может предупредить — это нормально для приложений вне магазина», aligned with the existing support macro). Existing `marketing.install.*` copy keys are reused/extended; orphaned `marketing.install.apple.*` keys are pruned (Apple is `readiness_only` in product facts). The page becomes **indexable** and joins the sitemap (today it ships `noIndex` — the rebuild makes it a real content page targeting install-intent queries). Install FAQ + support links close the page.

### 7.3 Intent pages (/youtube, /tiktok, /mobile, /devices, /telegram, /vpn)

One new `IntentTemplate` replaces `MarketingLanding`: scenario hero (e.g. «Смотреть YouTube без замедлений»), 2–3 scenario cards, then shared Steps/Pricing/FAQ/FinalCta sections with per-page copy keys. `/vpn` keeps visible search-intent VPN wording per the owner-approved rule. `buildMarketingMetadata()`, per-page JSON-LD, and sitemap entries survive with updated descriptions.

### 7.4 /checkout/

Reskin only: existing client logic, provider truth rules, and plan selection stay; UI moves to `ui/*` primitives (cards, pills, price rows). Escape hatches (redeem, support) keep their routes.

### 7.5 /offer/, /privacy/

New PageShell + typography; body text untouched.

## 8. Motion Spec

- Tokens only: durations 160/220/320ms, `--pokrov-easing`, `--pokrov-easing-spring`; transform/opacity exclusively (60fps rule); no layout-property animation.
- Scroll reveal: IO-based `Reveal` (rise 12px + fade, once, threshold 0.2) for all sections; stagger 60ms for grids.
- framer-motion reserved for: hero floating chips (gentle y-loop), showcase scroll-binding, accordion open/close spring, CTA hover/tap scale (1.02/0.98).
- `prefers-reduced-motion`: all reveals/loops collapse to opacity-only or static; scroll-binding disabled.
- No parallax on text, no marquee, no animation on `/offer/`, `/privacy/`.

## 9. Copy Plan

- Every new user-visible string gets a `marketing.*` key in `copy/catalog.ru.json` with surface/tone flags; components read via `getCopyText` (fallbacks = final copy, per existing pattern). Existing keys are reused where semantics match; orphaned keys are pruned in the same change.
- Tone contract: headlines — calm, concrete, outcome-first, no exclamation marks; microcopy — warm and human; forbidden — pseudo-tech superlatives, fake numbers, «официальный сайт» phrasing, canceled-era cream/glass metaphors.
- Draft flow: I draft all copy → external consilium pass (Kimi lane for warmth/naturalness, DeepSeek lane for contradiction/claim hunting, per AGENTS.md routing) → local synthesis; models never author final canon directly.
- Claims checklist applied to every section: trial 5 days no-card, 99₽/30d entry, +10 days Telegram, Android+Windows beta, GitHub delivery, up-to-5-devices — all from shared facts; nothing about stores, 1.0.0, signing, RU-origin, auto-update.

## 10. SEO / Analytics Preservation

- Keep per-route `metadata` (titles/descriptions rewritten in new tone), OpenGraph/Twitter images, canonical URLs, `robots.ts`, `sitemap.ts`, `manifest.ts`.
- Keep SoftwareApplication + FAQ JSON-LD on home, per-intent JSON-LD, `FunnelTracker` events (same event names so funnel dashboards stay comparable).
- **Known check/code moves:** `scripts/check-marketing-seo.mjs` hardcodes a `sourceFiles` list that includes `src/components/marketing-landing.tsx` — this file is deleted, so the check's file list must be updated to the new template modules in the same change. `buildMarketingMetadata()` currently lives inside `marketing-landing.tsx` and is imported by every page route; it relocates to `src/lib/marketing-site.ts` (already in the check's file list) before the old component is removed.
- `npm run check:seo` and `npm run check:responsive` must pass; update check expectations only where they encode old file paths or old literal strings, not the checks' intent.
- Share images: regenerate OG/Twitter masters on the white/emerald brand per generated-asset policy (prompt/master/dimensions/review note recorded) — one task inside this wave.

## 11. Risks

| Risk | Handling |
|---|---|
| Next 14→16 breakage | Migration is step 1 in isolation: upgrade, build, export-compare route list before any redesign commits |
| Tailwind v4 + token bridge drift | Single `@theme` bridge file maps tokens once; no raw hex allowed in components (lint-guarded by review) |
| SEO regression from full copy rewrite | Route set, canonicals, JSON-LD shape, and funnel event names frozen; only human-visible text and metadata descriptions change (one deliberate exception: `/install/` flips noIndex→index and joins `MARKETING_SITEMAP_ROUTES`, §7.2); `check:seo` gates |
| SVG app UI drifts from real app | Screens are drawn from current POKROV-app connect/locations/account screenshots as reference; reviewed against client canon before ship |
| Checkout reskin breaks purchase flow | Logic files untouched; UI-only diff; manual walkthrough of plan → provider → redirect in static export |
| Copy catalog compliance flags | New keys carry `allowed_public` and VPN-wording flags consistent with the `2026-06-01` rule |

## 12. Verification And DoD

1. `npm run build` (static export; expected route set: `/`, `/install/`, `/checkout/`, `/mobile/`, `/youtube/`, `/tiktok/`, `/devices/`, `/telegram/`, `/vpn/`, `/offer/`, `/privacy/`, plus `/_not-found`, `robots.txt`, `sitemap.xml`, `manifest.webmanifest` — 15 export entries; compare before/after the Next 16 migration), `npm run check:seo`, `npm run check:responsive` — green.
2. `rg "lp-|gsap|Manrope"` in `marketing/` — no live references.
3. Browser smoke (my pass): home, install, one intent page, checkout, legal at 375px and 1280px; reduced-motion pass; console-error-free (funnel CORS on localhost excepted).
4. Contrast spot-check on new sections (foundation table applies; `status_green` never on text).
5. Owner visual review of the built site before deploy.
6. Same-wave docs: `docs/product/portal-vpn-product.md` positioning section updated.
7. Release DoD per AGENTS.md: code + checks + push; deploy of `marketing/` happens on owner go (this wave is the marketing deploy trigger agreed in sub-project 0).

## Appendix: Session Decision Log

- Companion screens: `.superpowers/brainstorm/redesign2-061222/hero-concept.html` (hero A chosen over Apple-center B and interactive C).
- Tone question answered in terminal: mix premium+warm.
- Stack question answered in terminal: option A (Next 16 + Tailwind v4 + framer-motion, gsap removed).
- Scope question answered in terminal: full public surface in one wave.
