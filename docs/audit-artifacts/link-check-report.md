# Link Check Report

- FAIL: 0
- PASS: 30

| Status | File | Message |
| --- | --- | --- |
| PASS | `marketing\src\app\robots.ts` | Marketing SEO route is present |
| PASS | `marketing\src\app\sitemap.ts` | Marketing SEO route is present |
| PASS | `marketing\src\app\manifest.ts` | Marketing SEO route is present |
| PASS | `marketing\public\opengraph-image.png` | Marketing SEO route is present |
| PASS | `marketing\public\twitter-image.png` | Marketing SEO route is present |
| PASS | `marketing\public\favicon.ico` | Marketing SEO route is present |
| PASS | `marketing\public\apple-icon.png` | Marketing SEO route is present |
| PASS | `marketing\src\app\page.tsx` | Public marketing CTA no longer routes to connect host |
| PASS | `marketing\src\components\layout\page-shell.tsx` | Public cabinet CTA points to webapp host |
| PASS | `marketing\src\components\home\pricing.tsx` | Pricing CTA routes through public checkout gateway |
| PASS | `marketing\src\components\layout\footer.tsx` | Marketing footer exposes canonical news channel |
| PASS | `marketing\src\app\layout.tsx` | Layout includes `metadataBase` metadata wiring |
| PASS | `marketing\src\app\layout.tsx` | Layout includes `manifest` metadata wiring |
| PASS | `marketing\src\app\layout.tsx` | Layout includes `icons` metadata wiring |
| PASS | `marketing\src\app\layout.tsx` | Layout includes `apple` metadata wiring |
| PASS | `marketing\src\app\layout.tsx` | Layout includes `/favicon.ico` metadata wiring |
| PASS | `marketing\src\app\layout.tsx` | Layout includes `/apple-icon.png` metadata wiring |
| PASS | `marketing\src\lib\marketing-site.ts` | Marketing metadata declares `alternates` |
| PASS | `marketing\src\lib\marketing-site.ts` | Marketing metadata declares `canonical` |
| PASS | `marketing\src\lib\marketing-site.ts` | Marketing metadata declares `twitter` |
| PASS | `marketing\src\lib\marketing-site.ts` | Marketing metadata declares `images` |
| PASS | `marketing\src\app\page.tsx` | Home page wires `buildMarketingMetadata` |
| PASS | `marketing\src\app\page.tsx` | Home page wires `buildSoftwareApplicationJsonLd` |
| PASS | `marketing\src\app\page.tsx` | Home page wires `buildFaqJsonLd` |
| PASS | `marketing\src\app\checkout\checkout-client.tsx` | Checkout gateway uses cabinet-safe fallback instead of connect host |
| PASS | `marketing\src\app\offer\page.tsx` | Legal page avoids direct checkout CTA |
| PASS | `marketing\src\app\privacy\page.tsx` | Legal page avoids direct checkout CTA |
| PASS | `webapp\src\app\(dashboard)\support\legal\page.tsx` | Webapp legal links use absolute marketing URLs |
| PASS | `portal_bot\api.py` | Admin campaign link builder marks public checkout as safe fallback |
| PASS | `portal_bot\api.py` | Compat env-flag for numeric subscription fallback is present |
