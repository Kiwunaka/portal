# POKROV polish maps

Date: 2026-06-09

These files are internal design references for the current POKROV polish pass:

- `client-app-map.png` - Android/Windows client direction.
- `web-cabinet-admin-map.png` - web cabinet and operator admin direction.
- `marketing-bot-map.png` - marketing site and Telegram bot direction.
- `design-map-text-atlas.md` - detailed text description for reviewers and models that cannot inspect images.

Generated image text is not product canon. Use the root `DESIGN.md`, `shared/design-tokens.json`, `copy/catalog.ru.json`, and the active client docs before copying any wording from these maps.

Implementation rules from this pass:

- First layer stays short: one main action, status, access days, support/recovery.
- Dead `Скоро` CTAs are hidden or shown as quiet unavailable states only where necessary.
- WARP/advanced privacy is visible only when backend/runtime can honestly offer it.
- Reviews use numeric `1/5` style ratings; Telegram Stars are payment wording only.
- Mobile admin uses cards; wide tables are desktop-only.
- Dynamic notices and promo slots stay backend-owned plain JSON, not arbitrary remote HTML.
