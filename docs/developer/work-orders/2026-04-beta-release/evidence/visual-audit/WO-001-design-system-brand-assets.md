# WO-001 Design System Brand Assets Evidence

Status: first-pass token and asset lock
Agent: W01
Date: 2026-04-25

## What I checked

- Read the orchestrator context, synthesis, R02 design research, and WO-001 work order.
- Read the required canonical platform docs plus active client cutover/readiness docs relevant to brand and release assets.
- Checked platform and client branch/status before edits.
- Compared current scope against baseline evidence logs:
  - `shared/design-tokens.json` was not dirty in current status before W01 edits.
  - `shared/design-tokens.ts` was not dirty in current status before W01 edits.
  - `logo/` was not dirty in current status before W01 edits.
  - this evidence file did not exist before W01.
  - the broader work-order tree is untracked wave material; I did not modify baseline dirty webapp/marketing/client component files.
- Inspected token consumers in `marketing/src/app/layout.tsx` and `webapp/src/app/layout.tsx`.
- Inspected current logo masters:
  - `logo/logoclear.svg`
  - `logo/logowithtext.svg`
  - `external/logogo.png` via R02 and canonical docs.

## What I found

- `shared/design-tokens.json` was still a small theme object and did not cover the beta acceptance surface for status colors, controlled radii by surface, component dimensions, icon policy, glass policy, or approved brand assets.
- `tests/test_shared_surface_facts.py` expects `theme.name` to be `quiet-core-luminous-edge` and a `glass.content_planes` token, while the token file still had the older `pokrov-calm-premium` shape.
- The current public token bridge already feeds marketing with `public` density and webapp with `cabinet` density.
- The legacy wordmark file contains a subtitle lockup that must remain reference-only and must not be used as visible beta branding.
- Existing broad webapp/marketing files were already dirty before W01 and are owned by other workers in this wave, so I did not sweep component UI.

## What I changed

- Expanded `shared/design-tokens.json` into the beta token contract:
  - renamed theme to `quiet-core-luminous-edge`
  - preserved the light warm canvas and emerald/mint direction
  - added semantic status tokens
  - added surface-specific density and radius tokens for public, cabinet, admin, and product contexts
  - added component sizing tokens for buttons, navigation, tables, cards, and app connect affordance
  - added typography, glass, iconography, motion, and accessibility policy tokens
  - added approved brand asset pointers and blocked public-use policy for legacy subtitle lockups
- Updated `shared/design-tokens.ts` as a narrow token bridge so new tokens are available as CSS variables while keeping existing variable names stable.
- Added `logo/pokrov-wordmark.svg` as a subtitle-free POKROV wordmark source for later surface owners.
- Did not modify `external/logogo.png`, existing logo masters, marketing components, webapp components, or active client files.

## How I verified

- `python -m json.tool shared/design-tokens.json > $null` exited 0.
- `python -m pytest tests/test_public_copy_guardrails.py -q` passed: 5 passed.
- `npm.cmd run build` in `marketing/` passed.
- `npm.cmd run build` in `webapp/` passed.
- `python -m pytest tests/test_shared_surface_facts.py -q` did not pass, but it failed before reaching the design-token assertions on an existing out-of-scope product fact mismatch: `product["brands"]["client"]` is currently `POKROV`, while the test expects `POKROV Network`.
- `python scripts/ui_visual_smoke.py` did not pass because existing dirty webapp pages are missing expected entry/dashboard copy. The failed files were `webapp/src/app/page.tsx` and `webapp/src/app/(dashboard)/dashboard/page.tsx`, both outside W01 scope and already dirty in the platform baseline.

## What remains / risk

- W02/W03/W07 still need to consume the new tokens across marketing, cabinet/admin, and client surfaces; this pass only locks the shared contract and bridge.
- Legacy subtitle wordmark usage still needs a surface-level search/removal pass before paid beta screenshots or publication.
- Derived favicon, launcher, splash, tray, installer, share-preview, and store assets still need regeneration from approved masters before release.
- The active client palette remains hard-coded in Flutter and needs a W07 token-sync pass.
- Existing `tests/test_shared_surface_facts.py` and `scripts/ui_visual_smoke.py` failures should be triaged by the relevant owners because their failing surfaces are outside this pass.

## Changed file paths

- `C:/Users/kiwun/Documents/ai/VPN/shared/design-tokens.json`
- `C:/Users/kiwun/Documents/ai/VPN/shared/design-tokens.ts`
- `C:/Users/kiwun/Documents/ai/VPN/logo/pokrov-wordmark.svg`
- `C:/Users/kiwun/Documents/ai/VPN/docs/developer/work-orders/2026-04-beta-release/evidence/visual-audit/WO-001-design-system-brand-assets.md`
