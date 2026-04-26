# Design System Sync

Last updated: 2026-04-26

`DESIGN.md` is the root design contract for this repository. `shared/design-tokens.json` is the machine-readable token source for marketing, cabinet, admin, and release-support UI.

## Required Sync Points

| Area | Source | Consumer |
| --- | --- | --- |
| Palette, radius, shadows, type, density | `shared/design-tokens.json` | `shared/design-tokens.ts`, marketing, webapp |
| Token shape | `shared/design-tokens.schema.json` | tests, review, token generation |
| Client design | `C:/Users/kiwun/Documents/ai/POKROV-app/DESIGN.md` | Android and Windows shell work |
| Generated assets | `docs/design/generated-assets-policy.md` | launch, store, social, app assets |

## Open Beta v4 Notes

- Marketing, checkout, cabinet, admin, and client docs must stay visually aligned around the `quiet-core-luminous-edge` theme.
- Android and Windows public visuals must not imply public readiness until signing, handoff, and audit gates pass.
- Admin views should use the `admin` density and favor compact evidence over large promotional layouts.
- Public surfaces may link to `/install/` as gated help, but public download claims require runtime handoff evidence.

## Review Checklist

- Token changes include schema-compatible JSON.
- Public copy uses `POKROV` as the product line and avoids direct public `VPN` wording.
- Any new generated image includes source prompt, dimensions, intended use, and review note.
- Screenshots used for launch or store work are fresh and match the current beta limitations.
