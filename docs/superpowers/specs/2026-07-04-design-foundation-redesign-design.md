# POKROV Redesign — Sub-Project 0: Design Foundation

- Date: 2026-07-04
- Status: Draft for review
- Owner decisions captured: 2026-07-04 brainstorm session (visual companion + terminal)
- Parent effort: global redesign wave `0 → 1 → 2 → 3` (foundation → marketing landing → web cabinet → client app polish)

## 1. Context And Goal

The owner requested a full redesign of the POKROV public landing, web cabinet, and client app. Current pain: cream background (`#f7f3eb`) reads dated, copy feels machine-written, visual taste is inconsistent, animations are missing or unused (framer-motion/gsap installed but dead in `marketing/`), and the webapp has broken font loading plus two divergent component systems.

Sub-project 0 delivers the shared visual foundation that every later surface consumes, so the landing (1), cabinet (2), and client app (3) land on one system without repainting twice.

Deliverable summary: rewritten values in `shared/design-tokens.json` (keys/schema stable except one additive block), a matching `DESIGN.md` update, and working Golos Text font loading on both web surfaces.

## 2. Owner Decisions (locked)

| # | Question | Decision |
|---|---|---|
| 1 | Brand character on white | **A. Evolution** — keep POKROV emerald identity, refreshed and brighter, on pure white |
| 2 | Typography | **Golos Text** for display + body (Cyrillic-first), JetBrains Mono stays for technical strings |
| 3 | Dark theme policy | Landing: **light-only**. Cabinet + client app: light + dark with manual toggle (iOS-style) |
| 4 | Token rollout | **A. In-place overhaul** of `shared/design-tokens.json`; intermediate cabinet state accepted, cabinet is not deployed until its own wave |

## 3. Scope

In scope:

- `shared/design-tokens.json`: value rewrite, theme rename + version bump
- `shared/design-tokens.schema.json`: additive change for the new `component.switch` block only
- `DESIGN.md`: brand direction, theme model, and surface rules updated to match
- Font loading: Golos Text via `next/font/google` (subsets `latin`, `cyrillic`) wired in `marketing/src/app/layout.tsx` and `webapp/src/app/layout.tsx`
- Verification: builds, cabinet e2e smoke, documented contrast table

Out of scope (later sub-projects):

- Landing page redesign, copy rewrite, section structure (sub-project 1)
- Cabinet/admin component redesign, iOS switch component implementation, instructions surfaces (sub-project 2)
- Client app changes in `POKROV-app` (sub-project 3; client repo keeps its own design docs and adopts these values in its own wave)
- Removing the marketing dark-mode toggle (happens inside sub-project 1's rebuild; foundation only sets the policy)
- Copy catalog changes (`copy/catalog.ru.json`, `shared/copy.ts`)

## 4. Token Changes — `shared/design-tokens.json`

Theme identity: `name: "pokrov-clear"`, `version: "2026-07-redesign-w01"`.

### 4.1 Palette — light

| Key | Old | New | Note |
|---|---|---|---|
| `canvas` | `#f7f3eb` | `#ffffff` | pure white brand canvas |
| `canvas_alt` | `#f0eadf` | `#f5f7f6` | alternating sections, grouped-list background |
| `surface` | `rgba(255,255,255,0.86)` | `#ffffff` | content planes become solid (HIG policy) |
| `surface_strong` | `rgba(253,252,248,0.98)` | `#ffffff` | |
| `surface_subtle` | `#f9f6ef` | `#f7f9f8` | |
| `surface_muted` | `#edf4ee` | `#eef4f1` | mint-tinted panels |
| `surface_glass*` (light) | `rgba(255,255,255,0.72)` / `0.88` | unchanged | already neutral; overlays only, per glass policy |
| `surface_raised` | `rgba(255,255,255,0.94)` | `#ffffff` | |
| `text` | `#1f2636` | `#16181d` | neutral near-black (drops blue cast) |
| `text_soft` | `#667081` | `#5e6772` | |
| `text_muted` | `#8a9287` | `#9aa1a9` | |
| `text_inverse` | `#f8f5ef` | `#ffffff` | |
| `emerald` | `#20674f` | `#12805a` | primary action; white text contrast 4.93:1 (passes AA 4.5:1) |
| `emerald_strong` | `#174f3d` | `#0f6b47` | hover/pressed |
| `emerald_soft` | `#e7f2ec` | `#e6f4ed` | tint backgrounds |
| `mint` | `#dcefe5` | `#dff2e9` | |
| `mint_strong` | `#a9d5bf` | `#9fdcc0` | |
| `sage` | `#9cab90` | keep value, mark deprecated in DESIGN.md | no new usage |
| `gold_soft` | `#d8c8a8` | keep value, mark deprecated in DESIGN.md | no new usage |
| `line` | `rgba(31,38,54,0.1)` | `rgba(17,24,20,0.08)` | hairline borders |
| `line_strong` | `rgba(31,106,82,0.2)` | `rgba(18,128,90,0.18)` | |
| `focus_ring` | `#20674f` | `#12805a` | |

New palette keys (additive): `status_green: "#34c759"` (light) / `status_green_dark: "#30d158"` — iOS system green reserved for the "connected" state and switch fill, never for text. The palette schema accepts additional string properties (`additionalProperties` + `required` list), so these keys need no schema change; the only schema addition in this spec is the `component.switch` block (§4.6).

### 4.2 Palette — dark (cabinet + client app only)

Keep the elevation-aware off-black green model from the 2026-07 HIG wave; changes are alignment only:

| Key | Old | New |
|---|---|---|
| `canvas_dark` / `canvas_dark_alt` | `#111715` / `#151c19` | unchanged |
| `surface_dark` | `rgba(18,29,24,0.92)` | `#161d1a` (solid) |
| `surface_dark_strong` | `rgba(14,23,19,0.98)` | `#121917` (solid) |
| `surface_raised_dark` | `rgba(20,27,24,0.94)` | `#182019` (solid) |
| `surface_glass_dark*` | keep translucent (overlays only) | unchanged values |
| dark accent (`focus_ring_dark`, button dark bg) | `#8ac4ab` | unchanged |
| `emerald_dark` | `#123d31` | unchanged |
| all other dark keys (`surface_subtle_dark`, `surface_muted_dark`, `text_dark*`, `line_dark*`) | — | unchanged |

Semantic groups (`success/warning/danger/info/neutral`): light `success.bg` aligns to `#e6f4ed`; all other semantic values unchanged (they already sit correctly on white).

### 4.3 Typography

| Key | Old | New |
|---|---|---|
| `body_family` / `display_family` | `Manrope` | `Golos Text` |
| `mono_family` | `JetBrains Mono` | unchanged (loading deferred until a surface ships mono text) |
| `display_letter_spacing` | `-0.02em` | `-0.01em` (Golos needs less negative tracking) |
| `size_display` | `clamp(2.25rem, 5vw, 3.25rem)` | `clamp(2.5rem, 6vw, 4rem)` |
| other sizes/weights/line-heights | — | unchanged; landing may use local weight 800 (Golos supports 400–900) without a new token |

### 4.4 Shadows

Lighter and tighter for a white canvas:

| Key | New value |
|---|---|
| `soft` | `0 2px 8px rgba(17,24,20,0.05)` |
| `medium` | `0 8px 24px rgba(17,24,20,0.07)` |
| `strong` | `0 16px 48px rgba(17,24,20,0.10)` |
| `soft_dark` / `medium_dark` / `strong_dark` | unchanged |
| `focus` | `0 0 0 3px rgba(18,128,90,0.25)` |

### 4.5 Radius

Unchanged except documentation intent: marketing CTAs use `pill`; cabinet/app controls use `control` (`0.875rem`). No key changes.

### 4.6 Components

| Key | New value |
|---|---|
| `button.background` | `#12805a` |
| `button.background_hover` | `#0f6b47` |
| `button.secondary_background` | `#ffffff` |
| `button.border` | `rgba(18,128,90,0.2)` |
| `button.*_dark` | unchanged |
| `nav.active_bg` | `#e6f4ed` |
| `nav.hover_bg` | `rgba(17,24,20,0.04)` |
| `nav.text` | `#5e6772` |
| `card.border` | `1px solid rgba(17,24,20,0.08)` |
| `card.background` | `#ffffff` |
| `card.background_dark` | `#182019` (solid, matches `surface_raised_dark`) |
| `card.inner_edge` | `none` (solid planes need no inner highlight) |
| `card.inner_edge_dark` | `none` (same rationale) |
| `table.header_bg` | `#f5f7f6` |
| `table.divider` | `rgba(17,24,20,0.06)` |
| `table.row_hover_bg` | `rgba(18,128,90,0.05)` |
| `skeleton.base` | `rgba(17,24,20,0.06)` |
| `skeleton.highlight` | `rgba(255,255,255,0.85)` |
| `progress.fill` | `linear-gradient(90deg, #12805a, #0f6b47)` |
| `app_connect.ring` | `rgba(18,128,90,0.18)` |

New additive block `component.switch` (iOS-style toggle canon; requires matching schema addition):

```json
"switch": {
  "width": "51px",
  "height": "31px",
  "thumb": "27px",
  "on_background": "#34c759",
  "on_background_dark": "#30d158",
  "off_background": "rgba(120, 120, 128, 0.16)",
  "off_background_dark": "rgba(120, 120, 128, 0.32)",
  "thumb_color": "#ffffff",
  "transition": "220ms cubic-bezier(0.34, 1.3, 0.64, 1)"
}
```

### 4.7 Motion, glass, density, iconography, accessibility

- `motion`: values unchanged (160/220/320ms, apple ease + spring, transform/opacity only, reduced-motion fade). DESIGN.md gains an explicit page-transition rule for later waves.
- `glass`: unchanged (solid content planes, translucent overlays, max blur 16px).
- `density`: unchanged.
- `iconography`: JSON values unchanged (`web_default: "lucide-react"`, `web_shell_legacy: "material-symbols"` stay machine-readable). The migration intent — retire material-symbols naming during sub-project 2 — is recorded in DESIGN.md only.
- `accessibility`: unchanged (AA floor, 44px touch targets).

## 5. DESIGN.md Updates

Same commit as tokens:

- Brand direction: white canvas replaces "light canvas"; cream/warm wording removed; `#12805a` named as light primary; `status_green` usage rule (connected state + switches only, never body text).
- Theme model: landing is light-only by policy; the dual-theme token emission stays (webapp consumes it), marketing stops exposing a toggle when sub-project 1 rebuilds it.
- Typography: Golos Text named as brand family with `next/font` loading requirement (no more CSS-only references). New rule: surfaces consume the `--font-*` variables emitted by `next/font`, never the raw `--pokrov-font-*` family strings (next/font uses hashed family names; the raw string will not resolve to the self-hosted face).
- Text roles: `text_muted` (`#9aa1a9`, ~2.6:1 on white) is scoped to decorative/non-essential text only — placeholders, disabled states, ornament; anything a user must read uses `text_soft` or stronger.
- Deprecated: `sage`, `gold_soft`, legacy `-dark`-suffixed variables (already legacy), card `inner_edge` / `inner_edge_dark`.
- iOS control canon: switch dimensions/colors, grouped-list pattern with inset separators and chevrons, tooltip/popover/banner slots named as the control vocabulary for sub-projects 1–3.

## 6. Font Loading Changes

- `marketing/src/app/layout.tsx`: replace Manrope import with Golos Text (`next/font/google`, subsets `latin` + `cyrillic`, weights 400/500/600/700/800, variable `--font-golos`; keep `--font-manrope` alias emitted equal to Golos during transition so existing CSS keeps rendering until sub-project 1 replaces it).
- `webapp/src/app/layout.tsx`: add the same `next/font/google` Golos Text setup (webapp currently loads no font files at all); map the existing `--font-manrope` var in `globals.css` to the new font variable so current styles pick it up without a mass rename. In the same pass, fix the hardcoded cream `viewport.themeColor` `#f7f3eb` → `#ffffff` (keep/add the dark-scheme entry `#111715` via the media-query form).
- Both surfaces are static-export Next.js; `next/font/google` downloads at build time and self-hosts — no runtime Google Fonts dependency.

## 7. Consumers And Data Flow

- `shared/design-tokens.ts` (`getDesignTokenThemeCss`, `getDesignTokenDensityCssVariables`) reads the JSON and emits CSS variables; no signature changes.
- `marketing/src/app/layout.tsx` and `webapp/src/app/layout.tsx` inject the emitted stylesheet; no wiring changes beyond fonts and the webapp `themeColor` fix (§6).
- Old marketing `lp-*` CSS and webapp `globals.css` consume `var(--pokrov-*, fallback)`; variables stay defined, so hardcoded cream fallbacks never activate. They are cleaned up in sub-projects 1–2.
- Client app (`POKROV-app`) does not read this JSON at runtime; it adopts the values in sub-project 3 via its own design docs.

## 8. Risks And Intermediate States

| Risk | Handling |
|---|---|
| Cabinet looks plain (white on white) until sub-project 2 | Accepted by owner. Cards keep hairline borders + shadows, so hierarchy survives. Do not deploy webapp until its wave; deploys are manual per AGENTS.md. |
| Old marketing pages (`lp-*`, intent pages) shift palette before their rebuild | Accepted; marketing deploy also waits for sub-project 1. |
| Contrast regressions | Contrast table in this spec: `#12805a` on white 4.93:1 (AA normal text), white on `#12805a` same, `#0f6b47` on white 6.5:1, `#16181d` on white 17.8:1, `#5e6772` on white 5.74:1, dark accent `#8ac4ab` on `#111715` unchanged from shipped wave. `text_muted` `#9aa1a9` (~2.6:1) is decorative-only per §5. `status_green` is never used for text. |
| Schema addition breaks build | Only `component.switch` requires a schema change (palette accepts additional string keys); `design-tokens.schema.json` updated in the same commit; schema validation run locally. |
| Golos Text render differences (metrics vs Manrope) | Display tracking loosened to −0.01em; visual smoke on both surfaces before commit. |

## 9. Verification

1. Token JSON validates against updated schema.
2. `npm run build` passes in `marketing/` and `webapp/`.
3. `npm run test:e2e:cabinet` smoke passes in `webapp/` (no visual assertions expected to break; catches runtime/layout errors).
4. Manual visual smoke: landing home + `/install/` + cabinet dashboard in light and dark, checking font actually loads (network tab shows self-hosted woff2) and no cream remnants from variables.
5. Contrast table from section 8 spot-checked with a contrast tool.

## 10. Definition Of Done

- Tokens, schema, DESIGN.md, and both layout font changes land in one commit on the root repo `master` line.
- Verification steps 1–5 recorded.
- No production deploy in this sub-project; deploy happens with sub-project 1 (marketing) and sub-project 2 (webapp) respectively.

---

## Appendix A. Competitor Research Synthesis (input for sub-project 1)

Researched 2026-07-04 via web search: Durev VPN (`durevpn.com`), Ded VPN (`dedvpn.one`), Bebra VPN (`bebra.ai`), Batya VPN (`batyavpn.com`), Mori VPN (`morivpn.com`), Neo VPN (`neo-vpn.com`); Fen VPN and Magnum VPN are Telegram-only funnels with no web landing.

Common structure: hero promise → icon feature grid → server/country proof → pricing (per-month framing + discount badges) → reviews → FAQ → Telegram CTA. Pricing anchors: 250–500₽/мес baseline, 150–350₽/мес effective annual, micro-trial 1–49₽ or 3–7 free days (often an auto-renew card-capture trap).

Strongest plays observed: Durev — total meme-brand commitment and a competitor price table; Mori — argued trust (named log-handover incidents, architecture explanations, engineer-grade FAQ); Bebra — operational credibility (real binaries, moneyback, temporary Apple ID workaround for RU App Store).

Opportunities none of them take (POKROV wedge):

1. Nobody looks premium — a calm HIG-grade white landing is instantly distinct.
2. Nobody shows the real product UI — polished real app frames are an uncopyable trust claim.
3. Nobody uses honest, checkable numbers — modest verifiable facts («5 дней бесплатно, карта не нужна») read as radical honesty here.
4. Nobody solves the clone/«официальный сайт» identity problem — POKROV's canonical domain + GitHub releases + bot registry is a stateable trust story.
5. Auto-renew traps are the norm — «без автосписаний / отмена в один тап» is an ownable wedge.
6. Onboarding clarity is absent — a 3-step install section with real screenshots beats everyone.

Copy lessons (RU market): sell daily-life outcomes («YouTube снова летает»), effort elimination («всё уже настроено», «одна кнопка»), per-month price with visible discount math; avoid pseudo-tech superlatives, inflated counters, self-scored comparison tables, «официальный сайт» phrasing, and third-party checkout domains.

## Appendix B. Session Decisions Log

- Visual companion session: `.superpowers/brainstorm/redesign-20260704-045115` (screens: accent-direction, typography).
- Q1 accent: option A (emerald on white) chosen from 4 rendered directions (apple-blue, graphite-mono, fresh-rebrand rejected).
- Q2 font: Golos Text chosen over Manrope (current), Inter, Onest from live Cyrillic specimens.
- Q3 dark theme: landing light-only; cabinet/app dual-theme.
- Q4 rollout: in-place token overhaul.
- HyperFrames (`github.com/heygen-com/hyperframes`, `npx skills add heygen-com/hyperframes`) noted for sub-project 1 implementation: candidate for hero promo video / animated connect demo assets.
