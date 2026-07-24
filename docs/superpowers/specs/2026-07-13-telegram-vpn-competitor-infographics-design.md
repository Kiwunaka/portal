# Telegram VPN competitor infographics — design specification

**Date:** 2026-07-13<br>
**Audience:** internal POKROV strategy team<br>
**Decision:** produce all three approved directions<br>
**Output:** three vertical PNG files, each exactly `1600 × 5000 px`

## 1. Objective

Turn the dated competitor research into three complementary internal visuals:

1. **Analytical report** — exact comparison and decision support.
2. **War room** — marketing pressure, risks, threats and attack window.
3. **Growth funnel** — map of observed and inferred acquisition/continuation mechanics from traffic source to Telegram, bot and product surfaces. Conversion and retention are not measured.

The three outputs must use one shared dataset and must not disagree on any number, evidence label or POKROV fact.

## 2. Source of truth

Primary machine-readable input:

- [infographic-data.json](../../competitive/telegram-vpn-2026-07-12/archive/infographic-data.json)

Human-readable synthesis and evidence:

- [master-dossier-ru.md](../../competitive/telegram-vpn-2026-07-12/archive/master-dossier-ru.md)
- [evidence-index.md](../../competitive/telegram-vpn-2026-07-12/archive/evidence-index.md)
- [market-metrics.csv](../../competitive/telegram-vpn-2026-07-12/archive/market-metrics.csv)
- [Excel workbook](../../../outputs/vpn-competitor-research-20260713/POKROV-telegram-vpn-competitors-2026-07-12.xlsx)

Canonical POKROV facts come from `docs/product/portal-vpn-product.md` and `shared/product-facts.json`. Competitor research is `EVIDENCE / ADVISORY`, not product authority.

## 3. Non-negotiable data rules

- Show snapshot date `2026-07-12` and post window `2026-05-12 — 2026-07-12`.
- Telegram subscribers, bot MAU, growth, reach and ERR must not be described as paid users, revenue, product MAU or churn.
- Display POKROV public growth as `нет подтверждённой сопоставимой метрики`, never zero.
- Exclude Luma from ordinary relative-growth/ERR ranking or mark it visibly as `proxy/repost anomaly`.
- Shuka reach is invalid; Sota reach is insufficient. Render missing values as `нет данных`, not zero.
- Marketing-aggression scores are analyst inference. Every score block must be labelled `аналитическая шкала 0–5`.
- Each source-of-growth block is labelled from `marketing_analysis[].inflow_evidence_class`: `подтверждено`, `смешанные данные` or `вывод по сигналам`. The label applies to the whole block, not to every individual bullet.
- No fake counters, fabricated reviews, invented conversion rates, CAC, LTV, revenue, market share or audience demographics.
- Do not imply that app install counts are Telegram acquisition attribution.
- No private keys, raw subscription links, QR codes, referral links, auth codes or payment tokens.

## 4. Shared visual system

### Canvas and grid

- Exact canvas: `1600 × 5000 px`.
- Safe margins: `96 px` left/right, `88 px` top/bottom.
- Base grid: 12 columns, `24 px` gutters.
- Section spacing: `72–112 px`.
- Minimum body text at final size: `28 px`; notes `22 px`; chart labels `24 px`.

### Typography

- Primary: `Golos Text` when locally available.
- Fallback: `Arial` / system sans.
- Strong hierarchy, tabular numerals where supported.
- No decorative script, fake terminal font or tiny footnotes.

### Shared semantic colors

- POKROV / positive: emerald `#147A4B`.
- Neutral/data ink: `#16211C` or light equivalent on dark surfaces.
- Growth warning/anomaly: amber `#D88914`.
- Decline/risk: red `#D24A3A`.
- Missing/insufficient: gray `#8B948F` with text label.

Color is never the only carrier of meaning; every status also has text or icon/shape distinction.

### Reusable evidence labels

- `ФАКТ` — direct/public verified observation.
- `ВЫВОД` — analyst inference.
- `НЕТ ДАННЫХ` — unavailable or invalid field.
- `АНОМАЛИЯ` — non-comparable metric class.

## 5. Infographic 01 — Analytical report

### Visual direction

Light editorial report: white/warm-gray canvas, dark green headline bands, emerald charts, restrained amber/red exceptions. Highest density of exact values.

### Narrative order

1. **Hero**
   - Title: `Telegram VPN 2026: рост, дистрибуция, продукт`.
   - The visual must not present product retention as a measured metric.
   - Subtitle: `Кто растёт, за счёт чего и где POKROV может выиграть без forced gate и призового спама`.
   - Snapshot/methodology strip.

2. **Executive KPI strip**
   - HitVPN `+386 200` — maximum absolute growth.
   - Sota `+15.3%` — fastest ordinary large app-backed grower.
   - `15` channels positive / `4` declining in the 19-channel set.
   - POKROV: `нет подтверждённой метрики`.

3. **Absolute growth leaderboard**
   - Horizontal bars for the top 11.
   - Luma included in absolute growth but visibly tagged anomaly.
   - Negative-growth tail shown separately.

4. **Scale versus growth**
   - Logarithmic x-axis: channel subscribers.
   - Main y-axis: `−4%…16%` for the ordinary comparison field.
   - Cats `+94%` and Luma `+199.7%` render in separate outlier cards/inset. Cats is labelled `gate/cross-promo`; Luma is labelled `proxy/repost anomaly`. Neither compresses the main chart.
   - Bubble class/outline uses only `android_footprint_scale.entries[].tier`. Unknown entries use one small hollow marker, never an inferred tier.
   - The ownership note from `android_footprint_scale.entries[].ownership_state` remains visible for Shuka and other qualified cases.

5. **Growth does not equal content frequency**
   - Compact comparison: GenVPN, NashVPN, MORI versus BlancVPN/Quattro.
   - Exact cadence where windows are comparable; two-month values labelled separately.

6. **Marketing pressure ladder**
   - Analyst scores with evidence snippets.
   - Top: HitVPN, Atlanta, Batya.
   - Unknown: Sota, Lagom shown without score.

7. **POKROV versus market matrix**
   - Entry, trial, Telegram dependency, platforms, store reach, recovery, routing depth, trust, social proof and growth engine.
   - Use `сильнее / слабее / не доказано`, not fabricated numeric scoring.

8. **Decision block**
   - What to copy: creators, simple referral, store/signing, status/roadmap, diagnostics.
   - What not to copy: mandatory gate, prizes, incentivized reviews, ad-SDK overload, fake claims.

9. **Sources and caveats**
   - Compact footer with file names and evidence labels.

## 6. Infographic 02 — War room

### Visual direction

Dark intelligence board: near-black/charcoal background, off-white data, orange-red threat signals, emerald POKROV opportunity. Dense but readable; no decorative military clichés.

### Narrative order

1. **Hero**
   - Title: `Карта захвата внимания`.
   - Subtitle: `Кто давит призами, кто покупает партнёров, кто вывозит продуктом`.

2. **Market threat map**
   - Four threat classes:
     - scale + app moat;
     - prize machine;
     - creator/affiliate machine;
     - utility/proxy funnel.
   - Competitors placed only where evidence supports the class.

3. **Aggression leaderboard**
   - HitVPN `5.0`, Atlanta `5.0`, Batya `5.0`, Luma/Platina `4.5`, GenVPN/GROZA `4.0`.
   - Label as analyst inference.

4. **Attack mechanics**
   - HitVPN: iPhone loop + channel/bot requirement.
   - Atlanta: creators + bounty + 30% + 50% partner offer.
   - Batya: continuous prizes + review reward + fear sales.
   - Luma: proxy-to-paid.
   - Nosok: placement reach + gate.

5. **Evidence versus effect**
   - Show that high cadence/pressure at GenVPN, NashVPN and MORI coexisted with negative 30-day channel dynamics. Do not claim that pressure caused the decline or that it failed at product conversion.
   - Show BlancVPN as low-pressure product communication.

6. **Product/release risk panel**
   - Kubik: debug signing + ad/attribution stack.
   - HiroVPN: tracking SDK overload.
   - Quattro: debug signing/local control token.
   - MantaRay: powerful UX with broad access/telemetry risk.

7. **POKROV defensive moat**
   - app-first;
   - real no-card trial;
   - Telegram optional;
   - no auto-renewal;
   - honest beta limitations.

8. **POKROV vulnerable flank**
   - no proven public growth series;
   - weak store reach/social proof;
   - unsigned Windows beta;
   - creator/referral/SEO engine unproven;
   - routing depth behind MantaRay.

9. **Attack window / action priorities**
   - creator engine with measurable attribution;
   - simple two-sided referral;
   - store/signing and release provenance;
   - public status/roadmap;
   - recovery without Telegram.

## 7. Infographic 03 — Growth funnel

### Visual direction

Warm narrative flow: cream background, violet/magenta acquisition accents, emerald POKROV alternative path. Rounded nodes and directional connectors; fewer numbers per block, stronger flow/mechanics reading without implying measured causality.

### Narrative order

1. **Hero**
   - Title: `От внимания к продукту`.
   - Subtitle: `Какие механики ведут внешний трафик в канал, бот и продуктовые поверхности`.

2. **Market mechanism map**
   - Source → Telegram gate/channel → bot trial/payment surface → app/client activation surface → lifecycle/referral surface.
   - Label the chain `наблюдаемые и предполагаемые механики`, not a measured conversion funnel.
   - Explicit warning: channel growth does not prove payment conversion, activation, retention or causality between stages.

3. **Six inflow engines**
   - prizes;
   - creators/affiliates;
   - app/store;
   - mandatory gate;
   - proxy/utility;
   - referral/reseller.
   - Each engine gets a concrete competitor example and evidence label.

4. **Three high-growth mechanism cases**
   - HitVPN: app scale ↔ giveaway ↔ bot/channel.
   - Atlanta: creator payout → gated bot → referral/partner economics.
   - Cats: differentiated anonymous login → gate → web continuity.
   - Label all three as analyst interpretation of co-occurring mechanics, not proven causal loops.

5. **Three cadence-with-decline cases**
   - GenVPN: high cadence coexisted with decline.
   - NashVPN: high cadence coexisted with decline.
   - MORI: content volume coexisted with decline.
   - Do not use arrows that imply the cadence caused the decline.

6. **Quality versus speed**
   - Fast acquisition: prizes/gates.
   - Product-continuation mechanisms: app, cabinet, recovery, status, support.
   - Mark the durability read as a strategic hypothesis. No invented conversion, retention or churn rates.

7. **POKROV alternative funnel**
   - Main path: Search/creator/content → app → 5-day trial without card → first connection → cabinet/support → paid key/renewal.
   - Side branch from account/cabinet: optional Telegram link + membership → `+10 days` and support/community continuation.
   - The Telegram branch must never sit on the required main line. Telegram is amplifier, not gate.

8. **Priority build sequence**
   - Foundation: recovery, diagnostics, status, signing.
   - Acquisition: creators, referral, SEO/platform landings.
   - Scale: stores, app proof, lifecycle governance.
   - No invented calendar dates or target metrics.

9. **North-star principle**
   - `Не покупать рост любой ценой. Строить приток, который доходит до первого подключения и остаётся из-за продукта.`

## 8. Production approach

- Build each infographic as deterministic HTML/SVG from `infographic-data.json`.
- Use CSS/SVG for all numeric charts; do not generate charts with an image model.
- Export at exact `1600 × 5000` using a browser renderer.
- Keep editable source HTML/CSS beside final PNG files.
- Generate a manifest containing output paths, dimensions, source dataset hash and creation date.

Planned output directory:

`docs/competitive/telegram-vpn-2026-07-12/infographics/`

Planned files:

- `01-analytical-report.html`
- `01-analytical-report.png`
- `02-war-room.html`
- `02-war-room.png`
- `03-growth-funnel.html`
- `03-growth-funnel.png`
- `manifest.json`

## 9. Verification

Each output must pass:

1. exact dimensions `1600 × 5000`;
2. PNG decode;
3. no clipped text, axes, labels or footer;
4. visible label for every missing/anomalous value;
5. reconciliation of all displayed metrics against `infographic-data.json`;
6. no formula-like fabricated figures;
7. readable at 50% preview and full resolution;
8. visual comparison across all three to ensure distinct roles but consistent facts;
9. source links and evidence notes retained in source HTML;
10. `git diff --check` and scoped link checks.

## 10. Scope boundary

This task creates internal research visuals only. It does not publish externally, change POKROV product behavior, edit competitor accounts, complete payments, download new third-party binaries or make release-readiness claims.
