# POKROV Design Cards - 2026-05-18

## Purpose

Three design cards for the current POKROV direction:

- Landing: first start and trial entry.
- Cabinet: authenticated continuation surface.
- App: Android and Windows client direction.

These cards are design references, not release authorization and not store/public-launch evidence.

## Final Assets

| Surface | Final PNG | Dimensions | Render source |
| --- | --- | --- | --- |
| Landing | `docs/design/assets/pokrov-design-card-landing-2026-05-18.png` | 1440x920 | `docs/archive/design-plans/pokrov-design-cards-2026-05-18.html` |
| Cabinet | `docs/design/assets/pokrov-design-card-cabinet-2026-05-18.png` | 1440x920 | `docs/archive/design-plans/pokrov-design-cards-2026-05-18.html` |
| App | `docs/design/assets/pokrov-design-card-app-2026-05-18.png` | 1440x920 | `docs/archive/design-plans/pokrov-design-cards-2026-05-18.html` |

## Source Master And Logo Handling

- Source logo master: `external/logogo.png`.
- Derived render asset: `docs/design/assets/pokrov-mark-raster.png`.
- `logo/logowithtext-email.png` was intentionally not used because it contains the legacy public subtitle `PREMIUM VPN`.
- The deterministic HTML/PNG render supersedes the initial imagegen mood previews because exact logo and text fidelity matter here.

## Prompt / Reference

Design brief used for generation and review:

- Brand: `POKROV`.
- Public wording: do not use `VPN` as a direct public product description.
- Product facts: app-first, consumer-first, 5 day trial, Telegram `+10 days`, Android + Windows beta scope.
- Release honesty: outside-store public beta is allowed by the 2026-05-15 evidence pack, but no app-store, stable `1.0.0`, trusted Windows signing, raw Android-audit, RU-origin, or production payment-maturity claims.
- Visual canon: warm light canvas, emerald primary action, mint status, Manrope-like typography, restrained premium interface.

## Review Note

Reviewed against `DESIGN.md`, `shared/design-tokens.json`, active product/cabinet/app docs, and OpenCode model critique:

- DeepSeek V4 Pro: approved direction, requested CTA and copy cleanup.
- Kimi K2.6: approved direction, requested warmer Russian copy and less internal meta voice.
- MiniMax 2.7: warned that these are fixed presentation boards and production needs proper responsive reflow.
- GLM 5.1: requested localization consistency, stronger app state model, and action-first CTAs.
- Mimo V2.5 Pro: OpenCode/OpenRouter listed the model, but `opencode run` returned `No allowed providers are available for the selected model`.

Applied follow-up changes:

- Landing primary CTA changed to `Попробовать 5 дней`.
- Early `Тарифы` CTA removed from the landing hero.
- Trial copy reframed as trial-first instead of card-first.
- Cabinet primary CTA changed to `Открыть приложение`.
- Internal design-note copy replaced with user-facing beta/status copy.
- App card now shows connected, connecting/off, and protected state language.

## Release Scope Note

The cards are safe as design exploration for implementation planning. They may support outside-store public beta communication, but they do not claim Android store availability, Windows trusted signing, raw Android physical-audit proof, RU-origin readiness, production Lava.top maturity, or stable `1.0.0` release gates.
