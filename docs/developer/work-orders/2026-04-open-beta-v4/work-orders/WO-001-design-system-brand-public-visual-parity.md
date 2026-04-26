# WO-001 Design System, Brand, Visual Parity

Status: pending research
Owner: W01

## Scope

- Platform root `DESIGN.md`.
- Client `POKROV-app/DESIGN.md` and `docs/design/DESIGN.md`.
- `shared/design-tokens.json` and `shared/design-tokens.schema.json`.
- Web theme/CSS variable sync.
- Flutter theme sync.

## Acceptance

- Design tokens map to code tokens.
- Design lint passes or alpha-tool exception is documented.
- Mobile widths `320`, `360`, and `390` have no horizontal overflow.
- Motion respects reduced motion.
- Contrast meets WCAG AA for body text and primary CTAs.

## Verification

```powershell
npx @google/design.md lint DESIGN.md
npm.cmd run build
python scripts/ui_visual_smoke.py
```
