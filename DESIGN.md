# POKROV Design System

Last updated: 2026-04-26

This file is the root design contract for public, cabinet, admin, and release-support surfaces in this repository.

## Source Of Truth

- Canonical tokens: `shared/design-tokens.json`
- Token schema: `shared/design-tokens.schema.json`
- Token TypeScript adapter: `shared/design-tokens.ts`
- Product facts and public URLs remain in `shared/product-facts.json`, `shared/public-urls.json`, and `shared/portal-config.ts`.
- Active client design docs live in `C:/Users/kiwun/Documents/ai/POKROV-app/DESIGN.md` and `C:/Users/kiwun/Documents/ai/POKROV-app/docs/design/DESIGN.md`.

## Brand Direction

POKROV should feel calm, premium, reliable, and practical. The interface should help a user start in the app, understand account state, and recover through the cabinet or support without needing transport-layer knowledge.

Use:

- light canvas, white surfaces, mint status accents, and deep green primary actions;
- restrained motion and clear focus states;
- dense but readable admin surfaces;
- app-first language for onboarding, trial, renewal, support, and downloads.

Avoid:

- direct public product copy that describes POKROV with `VPN`;
- legacy subtitle lockups as visible public branding;
- decorative visual noise that competes with account, payment, or safety state;
- unsupported public safety claims for Android, Windows, paid checkout, or downloads.

## Surface Rules

| Surface | Density | Primary job |
| --- | --- | --- |
| Marketing | `public` | Explain POKROV and route users to app-first start, cabinet, checkout, or support. |
| Checkout | `public` | Show plans and payment availability truthfully; hide or disable unavailable providers. |
| Cabinet | `cabinet` | Keep subscription, devices, downloads, support, and profile state scannable. |
| Admin | `admin` | Prioritize operational truth, filters, warnings, and auditability over promotion. |
| Client docs | `product` | Keep Android/Windows beta limitations precise and aligned with release gates. |

## Generated Assets

Generated images, icons, screenshots, app-store graphics, and social preview derivatives must have:

- prompt or source-reference note;
- source asset or approved master reference;
- final dimensions and file path;
- reviewer/date note;
- explicit statement that the asset does not contain legacy public `VPN` wording unless it is an unavoidable compatibility label.

Do not ship generated release assets from scratch without checking them against the current brand master and token palette.
