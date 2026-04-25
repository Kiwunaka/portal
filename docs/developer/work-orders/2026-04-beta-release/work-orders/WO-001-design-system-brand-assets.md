# WO-001 Design System, Brand Assets, Visual Parity

Status: draft
Lane: mixed
Primary owners: shared design/copy surfaces, marketing, webapp, client assets

## Scope

Normalize POKROV visual language for paid beta. Attached refs override current tokens for this wave.

Target direction:

- light canvas
- emerald/mint accent
- dark charcoal text
- rounded cards
- thin borders
- soft shadows
- calm premium utility style
- Russian-first interface
- sidebar and top status badge where appropriate
- real tables, cards, and statuses
- no aggressive gradients
- no fake cyber styling
- no dev/demo indicators
- beta labels only where intentionally needed

## Assigned Paths

Platform:

- `shared/design-tokens.json`
- `logo/`
- `external/logogo.png`
- `marketing/src/**`
- `webapp/src/**`

Client:

- `C:/Users/kiwun/Documents/ai/POKROV-app/assets/**`
- `C:/Users/kiwun/Documents/ai/POKROV-app/packages/**`
- `C:/Users/kiwun/Documents/ai/POKROV-app/apps/**`

Use explicit lock before editing shared files.

## Required Changes

- Derive/update shared tokens from refs or document why a token deviates.
- Ensure logo/wordmark consistency across marketing, cabinet, admin, Android, and Windows.
- Remove or isolate old visual styles, visible Hiddify residue, dev labels, fake demo states, and public `Premium VPN` subtitle usage.
- Create screenshot evidence under `evidence/visual-audit/`.

## Validation

- `python -m pytest tests/test_public_copy_guardrails.py -q`
- `python scripts/ui_visual_smoke.py`
- `cd marketing; npm.cmd run build`
- `cd webapp; npm.cmd run build`
- Client visual smoke as available.

## Handoff Format

- What I checked
- What I found
- What I changed
- How I verified
- What remains / risk

