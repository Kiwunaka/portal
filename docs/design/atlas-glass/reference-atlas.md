# POKROV Atlas Glass Reference Atlas

Last updated: 2026-04-28

This note captures the visual direction for the Atlas Glass reset. It is a product-specific direction, not a copy target.

## Direction

POKROV should feel like an Apple-like premium utility: calm, readable, practical, and quietly expensive. The interface should show confidence through hierarchy, spacing, restrained motion, and honest state, not through cyber/security visual cliches.

## References To Use As Feeling Only

- Neuform / NovaEstate: premium dashboard feeling, rounded hierarchy, air, one dominant status panel with supporting cards, soft glass edges, calm financial/product confidence.
- Mobbin: mobile shell patterns, onboarding, subscription, checkout, support, empty/error/loading states.
- Linear dashboards: purposeful, audience-tuned dashboards with context-rich views and clear next action.
- shadcn-style dashboards: accessible composable primitives, responsive sidebars, tables, forms, skeletons, sheets/dialogs.

Do not copy layouts, palettes, cards, metrics, grids, icon choices, or compositions from any reference.

## Atlas Glass Rules

- Light theme: warm milk canvas, white/near-white surfaces, emerald primary, mint status accent, sparse gold warmth.
- Dark theme: charcoal green-black, never pure black; preserve emerald/mint contrast and reduce glow intensity.
- Medium glass: use blur only where it adds depth, capped by the root design contract; pair it with subtle borders and inner highlights.
- Consumer surfaces: softer, app-like, next-action oriented.
- Admin surfaces: denser, tighter, more operational, with static tables and risk/status badges.
- Marketing hero: POKROV must be immediately visible, with product-like glass panels rather than vague decorative blobs.

## Avoid

- Direct public `VPN` positioning except legacy or technical identifiers.
- Broad release, `1.0.0`, payment readiness, or Android/Windows handoff claims without evidence.
- Fake progress, full-screen route loaders after shell state exists, and animation that hides latency.
- Generic Tailwind/shadcn gray boxes, neon cyber effects, heavy blur behind text, random one-off hex colors.
- Generated final UI screenshots as product proof.

## Acceptance Checks

- No mojibake in active UI/copy sources.
- Light, dark, and system default verified across marketing and webapp.
- Loading states match page shape; no fake progress; shell persists.
- Public copy avoids direct `VPN` product wording and unsupported release claims.
- Generated assets, if used, have prompt/source, master, dimensions, intended surface, review note, and release-scope note.
