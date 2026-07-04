# POKROV Redesign — Sub-Project 1: Implementation Plan

- Date: 2026-07-04
- Spec: `docs/superpowers/specs/2026-07-04-marketing-landing-redesign-design.md` (approved)
- Rule: every phase ends with a green `npm run build` in `marketing/`; commits land per phase.

## Phase 1 — Stack migration (old UI intact)

1.1 Upgrade `next` 14→16 (match webapp 16.1.x), `react`/`react-dom` 18→19, `eslint-config-next`; fix API breakages; verify static export emits the 15 expected entries (route list frozen in spec §12.1).
1.2 Add Tailwind v4 (`@tailwindcss/postcss` + postcss config, same as webapp), prepend `@import "tailwindcss"` + `@theme` token bridge (`--pokrov-*` → Tailwind names) to globals without deleting legacy CSS yet; add `cn()` util (clsx + tailwind-merge).
1.3 Remove `gsap` from dependencies.

## Phase 2 — Foundation components

2.1 `components/ui/`: Button (primary pill / ghost / link), Chip, Card, SectionHeading, Accordion (spring), PriceCard, StepCard.
2.2 `components/motion/`: `Reveal` (IO, rise 12px + fade, once, threshold 0.2), `Stagger` (60ms), reduced-motion collapse; motion constants re-exported from tokens.
2.3 `components/layout/`: Topbar (solid white, hairline after 8px scroll), Footer (columns + Telegram registry + GitHub link), PageShell.
2.4 `components/illustrations/`: AppPhoneSvg (connect screen, status_green ring), AppWindowSvg, StepMiniSvg ×3 — pure SVG, token-colored, drawn against current POKROV-app screens as reference.
2.5 Shared integration: `github_releases` entry in `shared/public-urls.json` + accessor in `shared/portal-config.ts`.

## Phase 3 — Pages (each replaces its legacy markup on completion)

3.1 Home: Hero, HonestyStrip, ServicesGrid, Steps, Showcase, Pricing (per-plan device limits), TelegramBonus, Faq, FinalCta; JSON-LD + FunnelTracker preserved.
3.2 `/install/`: PlatformTabs, InstallSteps (Android unknown-sources; Windows SmartScreen honesty), InstallFaq; noIndex→index; joins `MARKETING_SITEMAP_ROUTES`.
3.3 Intent template + 6 pages; `buildMarketingMetadata()` relocates to `src/lib/marketing-site.ts` first; `scripts/check-marketing-seo.mjs` sourceFiles updated in the same change.
3.4 `/checkout/` reskin (logic untouched); manual purchase-flow walkthrough.
3.5 `/offer/`, `/privacy/` typography reskin.
3.6 Legacy removal: `marketing-landing.tsx`, `homepage*`, `homepage.module.css`, all `lp-*`/`checkout-*` CSS, theme toggle + `data-theme` script; `rg "lp-|gsap|Manrope"` clean.

## Phase 4 — Copy pass

4.1 All new strings → `marketing.*` keys in `copy/catalog.ru.json` (surface/tone/`allowed_public` flags); prune orphans incl. `marketing.install.apple.*`.
4.2 Consilium review per AGENTS.md (Kimi warmth pass, DeepSeek claim/contradiction hunt) → local synthesis; claims checklist re-applied.

## Phase 5 — Verification, docs, ship

5.1 `npm run build` + `check:seo` + `check:responsive` green; export route diff vs Phase 1 baseline.
5.2 Browser smoke: home/install/intent/checkout/legal @ 375px + 1280px; reduced-motion; console clean (funnel CORS excepted).
5.3 OG/Twitter share images regenerated on white/emerald masters (asset policy note recorded).
5.4 `docs/product/portal-vpn-product.md` positioning refresh.
5.5 Owner visual review → push → deploy on owner go.
