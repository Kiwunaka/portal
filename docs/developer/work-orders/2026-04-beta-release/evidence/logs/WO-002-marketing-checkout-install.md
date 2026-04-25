# WO-002 Marketing Checkout Install Evidence

Status: first-pass W02 implementation
Agent: W02
Date: 2026-04-25

## What I checked

- Read the beta orchestrator context, synthesis, beta scope, R02/R03 research, W01 visual evidence, and WO-002 order.
- Read the required canonical platform docs in the agent order before editing.
- Checked branch and dirty state before W02 edits: current branch was `codex/beta-release-platform`.
- Compared touched files against the captured platform baseline:
  - none of the W02-touched marketing/copy files were listed as dirty in `evidence/logs/platform-git-status-before.txt`.
  - the broader `docs/developer/work-orders/2026-04-beta-release/` tree is untracked wave material; this file is the W02 handoff log.
- Inspected marketing home, SEO landing, checkout, install, offer/privacy, shared catalog copy, and marketing structured data helpers.
- Ran a public-claim scan for `24/7`, `WireGuard`, `AES-256`, `Public release`, hardcoded technical/location claims, and forbidden direct public `VPN` copy.

## What I found

- Homepage still had unsupported public claims: `Поддержка 24/7`, human answer at any time, `AES-256 / WireGuard`, and `Германия, Франкфурт`.
- Shared SEO landing copy labeled Android and Windows cards as `Public release` and linked cards directly to artifact env URLs when present.
- The SEO landing had hardcoded masked reviews and emitted them into SoftwareApplication Review JSON-LD without repository provenance.
- Install copy and catalog strings still implied public direct downloads rather than cabinet-gated beta artifacts.
- Legal pages were too thin for paid beta: they did not state beta limits, internal Android status, unsigned Windows warning, best-effort support, activation-key redemption, or payment-provider/manual reconciliation notes.

## What I changed

- Replaced homepage support, protocol, and location claims with beta-safe copy:
  - support target is best-effort up to 24 hours.
  - first-layer mock no longer says `AES-256 / WireGuard`.
  - mock route no longer names Germany/Frankfurt.
- Changed SEO landing platform cards from public release/download claims to beta/internal statuses and routed them to `/install/` instead of direct artifact URLs.
- Removed hardcoded default testimonials from the SEO landing and stopped emitting hardcoded Review JSON-LD. The page now only renders review JSON-LD if verified reviews are explicitly passed in.
- Changed install page behavior so public install cards route to cabinet downloads or help, not direct public artifact URLs.
- Masked activation-key display in checkout status output.
- Added paid-beta checkout/legal copy for activation keys, manual payment reconciliation, refund/dispute support, Android internal APK limits, unsigned Windows warning, and best-effort support.
- Updated centralized Russian catalog entries so shared marketing/install/checkout copy matches the beta truth.

## How I verified

- `npm.cmd run build` in `marketing/`: passed.
- `npm.cmd run check:seo` in `marketing/`: passed after build.
- `python -m pytest tests/test_public_copy_guardrails.py -q`: passed, 5 passed.
- `python scripts/check-links.py`: passed.
- Static claim scan over `marketing/src`, `copy`, `shared`, and `marketing/public`: no matches for `24/7`, `WireGuard`, `AES-256`, `Public release`, `Германия`, `Франкфурт`, `Premium VPN`, `Hiddify`, or `Kill Switch`.
- `python scripts/ui_visual_smoke.py`: failed on existing out-of-scope webapp expectations in `webapp/src/app/page.tsx` and `webapp/src/app/(dashboard)/dashboard/page.tsx`; I reverted the generated report change and did not edit webapp.

## What remains / risk

- Checkout still uses the existing URL-based activation-key status/redeem contract; W06 owns backend/payment contract drift.
- `/checkout/` remains `noIndex: true`; that looks intentional for invite-limited beta but should be confirmed by release captain if SEO acquisition is needed.
- Windows signing and Android public release gates remain blocked outside W02.
- Final browser visual QA should be rerun after W03 webapp work settles, because the broad UI visual smoke currently fails on webapp-owned dirty files.

## Changed file paths

- `C:/Users/kiwun/Documents/ai/VPN/copy/catalog.ru.json`
- `C:/Users/kiwun/Documents/ai/VPN/marketing/src/app/checkout/checkout-client.tsx`
- `C:/Users/kiwun/Documents/ai/VPN/marketing/src/app/checkout/page.tsx`
- `C:/Users/kiwun/Documents/ai/VPN/marketing/src/app/install/page.tsx`
- `C:/Users/kiwun/Documents/ai/VPN/marketing/src/app/offer/page.tsx`
- `C:/Users/kiwun/Documents/ai/VPN/marketing/src/app/privacy/page.tsx`
- `C:/Users/kiwun/Documents/ai/VPN/marketing/src/components/home/homepage.tsx`
- `C:/Users/kiwun/Documents/ai/VPN/marketing/src/components/marketing-landing.tsx`
- `C:/Users/kiwun/Documents/ai/VPN/marketing/src/lib/marketing-site.ts`
- `C:/Users/kiwun/Documents/ai/VPN/docs/developer/work-orders/2026-04-beta-release/evidence/logs/WO-002-marketing-checkout-install.md`
