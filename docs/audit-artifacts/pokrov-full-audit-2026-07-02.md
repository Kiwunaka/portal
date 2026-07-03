# POKROV full audit, 2026-07-02

Scope: read-only audit of live production plus current local dirty tree. No fixes, deploys, admin mutations, paid transactions, or state-changing live API calls were performed.

## Verdict

Overall status: `WARN`, with two local release blockers.

- `FAIL`: local backend/API gate is red. `tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_user_data_prefers_mapped_nodes_for_paid_user` expects only the mapped `it` node, but `/api/user/1001` returns `["it", "pl"]`.
- `FAIL`: local marketing responsive gate is red due to a hydration mismatch in `ThemeToggle`: server `aria-label` is `Переключить на тёмную тему`, client `aria-label` is `Переключить тему`.
- `PASS`: live public pages and live app shell render in browser without observed console errors or horizontal overflow on audited routes.
- `PASS`: live `/api/health`, `/api/public/catalog`, `/api/payments/providers` return `200`; unauthenticated `/api/client/apps` returns expected `401`.
- `PASS`: live payment provider catalog is Lava.top-only.
- `BLOCKED_BY_ACCESS`: live unpaid Lava.top invoice probe was not run because `LAVATOP_API_KEY`, `LAVATOP_OFFER_ID`, and operator probe email env are absent.
- `BLOCKED_BY_ACCESS` / owner-gated: full completion is still blocked by Q-004 live Telegram WebApp/session and current-origin live app-session/deploy-approval evidence.

## Release blockers

| Area | Status | Evidence | Action |
| --- | --- | --- | --- |
| Backend/API node contract test | `FAIL` | Combined run: `131 passed, 1 failed`; isolated failing test also fails. Expected `["it"]`, actual `["it", "pl"]`. | Owner/dev decision: either update stale test to current canon `PAID = all enabled non-free nodes`, or restore mapped-node preference for `/api/user/{tg_id}`. |
| Marketing responsive hydration | `FAIL` | `npm.cmd run check:responsive` fails on mobile/tablet/desktop `/`; stack points to `marketing/src/components/home/homepage-topbar.tsx:62`. | Align server/client theme-toggle `aria-label`. |
| Live Lava invoice | `BLOCKED_BY_ACCESS` | `scripts/lavatop_invoice_probe.py --live` requires live Lava API key and offer id; env not present. Dry run only. | Provide probe env and explicit operator email, then run unpaid invoice probe without paying. |
| Owner gates Q-004 | `BLOCKED_BY_ACCESS` / owner labels | Source docs still mark Telegram WebApp gate blocked and live app-session as manual owner test. | Owner/operator evidence or explicit skip/attestation. |

Backend test triage note: current `portal_bot/api.py` deliberately routes `_nodes_for_user()` to `_fallback_nodes_for_user()` and ignores `UserNode` mapping evidence for runtime visibility. That matches the current written canon that paid users see all enabled non-free nodes, but it conflicts with the still-present test name and expectation.

## Truth and copy claims

`PASS`: browser sweep did not find positive claims of stable `1.0.0`, app-store availability, trusted Windows signing, raw Android physical-audit proof, RU-origin readiness, or production WARP on audited live public routes. `/offer/` matched the stable-launch regex only because it contains a defensive legal phrase, not a launch claim.

`WARN`: live `/vpn/` is a valid dedicated SEO/search-intent surface under the 2026-06-01 owner wording rule, but its `meta keywords` include `лучший vpn` and `лучший впн`. That is risky because hidden/metadata keyword stuffing and unsupported "best" claims remain forbidden.

`WARN`: `shared/support-ai-knowledge.json` still says not to use VPN as a direct public product description except legacy compatibility wording. That conflicts with the later approved SEO/search-intent exception. The support KB should be updated to mirror the 2026-06-01 rule instead of broadly forbidding visible VPN wording.

`PASS`: local copy/marketing guardrails mostly held:

- `npm.cmd run check:seo`: pass.
- `pytest tests/test_public_copy_guardrails.py tests/test_frontend_text_integrity.py tests/test_marketing_release_readiness.py`: included in the combined run and pass.

## SEO and search

Live browser metadata:

- `/`: title and H1 align around Android/Windows, 5-day trial, 99 RUB renewal; canonical `https://pokrov.space/`; `index, follow`.
- `/vpn/`: title/H1 target VPN search intent; canonical `https://pokrov.space/vpn/`; `index, follow`; risky `лучший vpn/впн` keywords.
- `/mobile/`, `/tiktok/`, `/youtube/`, `/devices/`, `/telegram/`: canonical self-links, `index, follow`, no observed overflow or console errors.
- `/install/`: canonical self-link, `noindex, follow`; installation/help intent is not search-indexed.
- `/checkout/`: canonical self-link, `index, follow`; first mobile viewport does not expose a visible plan/payment control.
- `/privacy/`, `/offer/`: canonical self-links, `index, follow`.
- `app.pokrov.space`: `noindex, nofollow`, as expected for cabinet surface.

HTTP SEO/static checks:

- `/robots.txt`: `200`, disallows `/api/` and `/_next/`, points to sitemap.
- `/sitemap.xml`: `200`, includes public marketing routes, lastmod `2026-06-29T00:36:49.915Z`.
- `/manifest.webmanifest`, `/favicon.ico`, `/opengraph-image.png`, `/twitter-image.png`: `200`.
- `WARN`: sampled manifest/favicon/OG/Twitter responses did not show `Cache-Control`; worth checking CDN/static cache policy before scale.

## Visual and browser

`PASS`: live homepage, SEO landings, install, checkout, legal, and app cabinet shell render without observed browser console errors or horizontal overflow at audited desktop/mobile sizes.

`WARN`: mobile `/checkout/` at `390x844` had no visible first-viewport interactive controls in the audit extraction. The first plan button is below the fold. For a purchase-intent route, this is a conversion risk.

`WARN`: mobile SEO landings use a dense always-visible nav stack before hero CTA. It is functional, but it delays the first primary action on mobile.

`PASS`: local `webapp` admin E2E specifically covers clickable pages inside mobile viewport and passed.

## Frontend speed

Live curl timings from current-origin workstation:

- `https://pokrov.space/`: `200`, `0.374s`, `118613` bytes.
- `https://pokrov.space/vpn/`: `200`, `0.395s`, `71759` bytes.
- `https://pokrov.space/checkout/`: `200`, `0.292s`, `33525` bytes.
- `https://app.pokrov.space/`: `200`, `0.640s`, `35871` bytes.
- `https://api.pokrov.space/api/health`: `200`, `0.222s`, `49` bytes.
- `https://api.pokrov.space/api/payments/providers`: `200`, `0.471s`, `381` bytes.

Local production build sizes:

- Marketing home: first load JS `105 kB`.
- Marketing checkout: first load JS `111 kB`.
- Marketing SEO landings: first load JS `96.3 kB`.
- Marketing install/legal/vpn: first load JS about `102 kB`.
- Webapp build passed under Next.js `16.1.6` / Turbopack.

Status: `PASS` for page weight and build budgets in this audit. Main speed/frontend concerns are mobile checkout first action visibility and static cache headers.

## Backend and API

Live production:

- `/api/health`: `200`, body `{"status":"ok", ...}`.
- `/api/public/catalog`: `200`, `Cache-Control: public, max-age=120`.
- `/api/payments/providers`: `200`, Lava.top-only provider catalog, `blocked=false`, `checkout_mode=account_session_first`, Telegram fallback available.
- `/api/client/apps`: `401` without auth, expected.

Local checks:

- `webapp npm.cmd run build`: `PASS`.
- `webapp npm.cmd run test:e2e:admin`: `PASS`, `19 passed`.
- Combined backend/payment/auth/copy/client-app tests: `FAIL`, `131 passed`, `1 failed`, `12 warnings`.
- Isolated failing test: `FAIL` again, same node-list mismatch.

## Payments

Current live truth:

- Lava.top is the only live provider exposed by `/api/payments/providers`.
- No paid transaction was made.
- Live invoice probe: `BLOCKED_BY_ACCESS` due missing env.
- Dry-run probe redaction check: `PASS`; it prints a redacted payload and reports missing offer id/API key without exposing secrets.

Reserve-provider comparison for RUB cards/SBP:

| Provider | Fit | Strengths | Risks / effort | Audit recommendation |
| --- | --- | --- | --- | --- |
| ЮKassa | Best primary reserve for РФ ИП/ООО | API covers payments, invoices, refunds, receipts, payouts, SBP participants, webhooks, auth/idempotency, SDK/OpenAPI. | Merchant onboarding, fiscal settings, webhook and ledger reconciliation work. | Pick first reserve unless legal/account constraints block it. |
| CloudPayments | Strong technical reserve | Cards/MIR, widget/API, refunds/cancel/confirm, SBP, SberPay/MIR Pay, notifications, fiscalization docs. | Heavier frontend/security integration; more webhook types; careful PCI/widget boundary. | Good second candidate, especially if widget/card UX matters. |
| Robokassa | Fast low-friction fallback | Simple MerchantLogin/password flow, ResultURL/SuccessURL/FailURL, cards/SBP, test mode, online-cashier docs. | Less fine-grained modern API model; exact refund/chargeback/reconciliation flow needs deeper proof. | Good emergency reserve path. |
| Prodamus | Possible payform reserve | Payment links, HMAC signature, notification URL, tax/fiscal fields, RUB. | Docs are more payform/course-oriented; REST API appears subscription-status focused; merchant terms need review. | Keep as reserve only after a small spike. |
| Telegram Stars | Telegram-only secondary | Native Telegram invoices, `XTR`, pre-checkout/successful-payment flow, no user card data in bot. | Not RUB/SBP, not web checkout replacement, proceeds and UX bound to Telegram Stars. | Useful for bot-only digital upsell, not main reserve. |

Production payment maturity still needs refund/chargeback evidence, reconciliation proof, fulfillment-ledger hardening, and live unpaid invoice proof with redacted IDs.

## Owner-gated leftovers

From `docs/developer/pokrov-open-questions.md` and `docs/developer/work-orders/2026-06-27--repo-feature-story-audit/COMPLETION-AUDIT.md`:

- Telegram WebApp real session: `BLOCKED_BY_ACCESS`.
- Live deployed app-session/current-origin approval: `MANUAL_OWNER_TEST`.
- Android physical install/connect: `SKIPPED_BY_OWNER`.
- Windows install/connect: `SKIPPED_BY_OWNER`.
- Payment dashboard maturity: `SKIPPED_BY_OWNER`.
- Signing/store/trust: `SKIPPED_BY_OWNER`.
- RU-origin probe: `SKIPPED_BY_OWNER`.
- WARP runtime release-build proof: `NOT_REQUESTED`.

## Owner questions

1. Confirm node contract: should paid `/api/user/{tg_id}` return all enabled non-free nodes, or only locally mapped/provisioned nodes when mappings exist?
2. Remove `лучший vpn` / `лучший впн` from `/vpn/` meta keywords, or keep and accept SEO-policy risk?
3. Update `shared/support-ai-knowledge.json` to allow visible VPN wording on dedicated SEO/search-intent surfaces?
4. Should `/checkout/` remain `index, follow`, or should payment-entry pages be `noindex, follow`?
5. Should mobile checkout expose a plan/continue control in the first viewport?
6. Which reserve payment provider should be implemented first: ЮKassa, CloudPayments, Robokassa, Prodamus, or Telegram Stars only for bot?
7. Provide Lava live probe env and email now, or leave live unpaid invoice as `BLOCKED_BY_ACCESS`?
8. Reopen Android/Windows physical install gates, or keep `SKIPPED_BY_OWNER` for this beta audit?
9. Reopen RU-origin probe from `mini` / `RFMINI`, or keep `SKIPPED_BY_OWNER` while no RU readiness claim is made?
10. Do we want Telegram Stars as a real secondary checkout lane, or only as future research?

## Evidence commands

Passed:

- `marketing`: `npm.cmd run check:seo`
- `marketing`: `npm.cmd run build`
- `webapp`: `npm.cmd run build`
- `webapp`: `npm.cmd run test:e2e:admin` -> `19 passed`
- `python scripts/run_client_release_gate.py preflight`
- `python scripts/client_security_smoke.py`
- live HTTP checks for public API/static routes
- browser route sweep for production marketing/app surfaces

Failed:

- `marketing`: `npm.cmd run check:responsive`
- `python -m pytest tests/test_public_copy_guardrails.py tests/test_frontend_text_integrity.py tests/test_marketing_release_readiness.py tests/test_api_payments_callbacks.py tests/test_lavatop_payment_providers.py tests/test_api_auth_and_tickets.py tests/test_admin_payments_api.py tests/test_smoke_client_apps.py -q --basetemp .tmp/pytest-audit-backend`
- `python -m pytest tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_user_data_prefers_mapped_nodes_for_paid_user -q --basetemp .tmp/pytest-audit-auth-single`

Blocked:

- `python scripts/lavatop_invoice_probe.py --live`: not run; required live Lava env absent.

Scratch artifacts created by checks:

- `.tmp-marketing-responsive-1783006707049`
- `.tmp/pytest-audit-backend`
- `.tmp/pytest-audit-auth-single`

## Source links

Local source-of-truth:

- `docs/developer/pokrov-open-questions.md`
- `docs/developer/work-orders/2026-06-27--repo-feature-story-audit/COMPLETION-AUDIT.md`
- `docs/product/portal-vpn-product.md`
- `shared/support-ai-knowledge.json`
- `marketing/src/app/vpn/page.tsx`
- `portal_bot/api.py`
- `tests/test_api_auth_and_tickets.py`

External provider docs:

- ЮKassa API: https://yookassa.ru/developers/api
- CloudPayments docs: https://developers.cloudpayments.ru/
- Robokassa quick start: https://docs.robokassa.ru/ru/quick-start
- Prodamus payform REST/integration docs: https://help.prodamus.ru/payform/integracii/rest-api
- Telegram Stars payments: https://core.telegram.org/bots/payments-stars
