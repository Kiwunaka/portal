# R04 User Cabinet Public Beta Readiness

Status: [confirmed] complete

## Scope

- [confirmed] Research scope: user cabinet readiness for public beta across dashboard/status, downloads, redeem, subscription, devices, statistics, support, public-beta labels, raw secret leakage, and build/E2E needs.
- [confirmed] This was a research-only pass. Only this assigned file was created.
- [confirmed] I did not edit implementation files and did not read or print never-touch secret material.

## Files/docs inspected

- [confirmed] `AGENTS.md`.
- [confirmed] `docs/README.md`.
- [confirmed] `docs/product/portal-vpn-product.md`.
- [confirmed] `docs/architecture/system-overview.md`.
- [confirmed] `docs/architecture/app-first-and-bonus-flows.md`.
- [confirmed] `docs/operations/deployment-and-access.md`.
- [confirmed] `docs/operations/monitoring-and-visibility.md`.
- [confirmed] `docs/developer/developer-guide.md`.
- [confirmed] `docs/developer/repository-map.md`.
- [confirmed] `webapp/README.md`.
- [confirmed] `webapp/src/app/(dashboard)/**` user and admin route inventory.
- [confirmed] `webapp/src/components/cabinet*.tsx` and `webapp/src/components/cabinet/**`.
- [confirmed] `webapp/src/lib/api.ts`.
- [confirmed] `webapp/e2e/**`.
- [confirmed] Prior paid-beta inherited evidence only: `docs/developer/work-orders/2026-04-beta-release/research/R04-webapp-cabinet.md`.
- [confirmed] Prior paid-beta inherited W03 evidence only: `docs/developer/work-orders/2026-04-beta-release/evidence/logs/WO-003-user-cabinet.md`.
- [confirmed] Public-beta R01 context: `docs/developer/work-orders/2026-04-public-beta-release/research/R01-product-public-beta-scope.md`.

## Current cabinet status

- [confirmed] The cabinet route contract is materially improved versus paid-beta R04: `/settings/` and `/statistics/` now exist, `/profile/` redirects to `/settings/`, `/dashboard/downloads/` redirects to `/downloads/`, and `/pricing/` redirects to `/subscription/`.
- [confirmed] Current top-level cabinet nav includes Dashboard, Subscription, Devices, Statistics, Downloads, Support, and Settings. Downloads remains visible even though canon treats it as a task route, but this is probably acceptable for beta artifact handoff.
- [confirmed] Dashboard, devices, and statistics render safe summaries from session/dashboard state: access status, traffic, device counts, live connection counts, active-user estimate, and node-count summaries.
- [confirmed] Consumer dashboard/statistics/devices avoid first-layer raw token, QR, `?format=plain`, node host, and port display in source and E2E assertions.
- [probable] The labels "people online" and live connection counts are safe enough as aggregate estimates, but they should be visually reviewed so public users do not read them as surveillance or exact people tracking.

## Downloads and public-beta labels

- [confirmed] Downloads use runtime `/api/client/apps` via `fetchClientApps()` and fallback public config URLs.
- [confirmed] Download copy is beta-gated: Android Play/APK cards are beta-only, Android public release is called closed until final checks, and Windows warns that the installer may be unsigned.
- [confirmed] This matches the canonical blocker state for Android and Windows trust, but it means cabinet downloads are not ready to be presented as stable public distribution.
- [probable] If the public-beta cut means open public downloads, the current "internal beta/invited testers" Android wording needs an orchestrator decision: either keep Android hidden/internal, or update copy only after signing and physical-device audit pass.

## Redeem, subscription, and checkout

- [confirmed] Redeem is wired to real API helpers: `fetchAccessKeyStatus()` and `redeemAccessKey()`.
- [confirmed] Checkout continuation builds a hosted checkout URL from the canonical checkout host with plan and optional promo context. It does not create a second in-cabinet payment wall.
- [confirmed] Subscription page shows current plan/access, plan options, checkout, redeem, and support escalation without raw connection sharing.
- [confirmed] Consumer payment history is still an honest unavailable state. The page says the history will appear when backend provides a safe user statement and routes users to support if payment did not update access.
- [confirmed] This is truthful, but it is a public-beta risk because paid users have no self-serve receipt/payment ledger in the cabinet.

## Settings and Telegram reward

- [confirmed] Settings now exposes Telegram bonus actions using `checkChannelSubscriberStatus()` and `claimChannelBonus()`.
- [confirmed] The UI separates read-only membership check from explicit claim, matching the app-first bonus contract.
- [blocked by missing access] Real Telegram membership, real claim idempotency, and production session refresh after claim were not verified in this R04 pass.
- [probable] The success state does not force a full session reload by design, inherited from W03 evidence; that is acceptable if the local success message remains visible and later refresh reconciles server state.

## Support truth

- [confirmed] Support is a real ticket surface, not decorative state. `support/page.tsx` fetches tickets, creates tickets, uploads attachments, and reloads the list after create.
- [confirmed] Thread view loads a ticket, sends replies, and uploads reply attachments through `/api/tickets/{id}/messages`.
- [confirmed] Attachment rendering only resolves `/uploads/support/` through the API host or absolute `http/https` URLs, rejecting other protocols.
- [confirmed] Support page includes a safe diagnostics section and explicitly says personal links, keys, access-point addresses, and public device address are not shown or requested.
- [probable] Support thread remains on older `glass-card`/violet UI instead of the newer cabinet primitives. This is not a contract blocker, but it is visible polish debt for a public audience.
- [needs local run] Cabinet E2E creates a ticket but does not cover opening `/support/thread/?id=...`, replying, or rendering/uploading attachments in the thread. Add this before public-beta signoff.

## Raw secret leakage

- [confirmed] Consumer route source and cabinet E2E keep raw `subscription_url`, token strings, `?format=plain`, QR copy/import actions, raw node hostnames, and ports out of first-layer cabinet pages.
- [confirmed] Admin E2E mocks and admin API types still contain subscription URLs/tokens for operator recovery paths; that is outside consumer cabinet scope and must remain permission-gated.
- [confirmed] `webapp/e2e/cabinet-flow.spec.ts` asserts that dashboard, subscription, devices/statistics, settings, and support do not render `mock_token` or raw compatibility strings.
- [unknown] Production API payloads may still include personal connection fields in `GET /api/dashboard` and `GET /api/user/{tg_id}`; current consumer components appear not to render them, but live production rendering was not checked.

## Build and E2E status

- [confirmed] Inherited W03 evidence reports `npm.cmd run build` passing and export-server Playwright cabinet spec passing with `14 passed`.
- [confirmed] Current cabinet E2E has been refreshed for settings, statistics, payment-history unavailable state, checkout copy guardrails, Telegram bonus actions, downloads beta states, support diagnostics, compatibility redirects, and narrow mobile viewport.
- [needs local run] I did not run build or Playwright in this R04 pass because the assignment is research-only and the worktree contains many concurrent edits from other agents.
- [needs local run] Before public-beta signoff, rerun from `webapp/`: `npm.cmd run build`, `npm.cmd run test:e2e:cabinet`, and preferably `npm.cmd run test:e2e`.
- [needs local run] Add/verify browser coverage for `/support/thread/?id=<ticket>`, ticket reply, attachment upload/rendering, `/redeem/` success/failure states, and checkout handoff URL.
- [blocked by missing access] Live hosted checkout, live Telegram auth/bonus, real attachment storage, production session cookies, runtime `/api/client/apps`, and deployed static export were not verified.

## Highest-risk findings

1. [confirmed] Consumer payment history remains unavailable because there is no safe user-facing backend ledger yet. The UI is honest, but public-beta paid users must go through support for receipt/reconciliation visibility.
2. [confirmed] Downloads are still beta-constrained: Android is explicitly not public-ready, and Windows may be unsigned. Broad public beta must not present these as stable/trusted artifacts.
3. [needs local run] Current public-beta worktree needs a fresh webapp build and cabinet E2E run after all concurrent edits, not only inherited W03 evidence.
4. [blocked by missing access] The riskiest live flows were not proven here: hosted checkout, Telegram bonus membership/claim, real support upload storage, production session cookies, and runtime app-download URLs.
5. [needs local run] Support ticket reality is wired, but thread/reply/upload rendering lacks current cabinet E2E coverage and the thread page still uses older UI primitives.

## What I checked

- [confirmed] Canonical docs and `webapp/README.md` for current source of truth.
- [confirmed] User cabinet routes, cabinet components, API wrappers, and Playwright coverage.
- [confirmed] Prior paid-beta R04 and W03 evidence as inherited context only.

## What I found

- [confirmed] W03 closed the largest paid-beta cabinet route/copy gaps.
- [confirmed] The current cabinet is broadly public-beta-candidate for continuation, redeem, settings, downloads, and support, provided the remaining live checks are not treated as green.
- [confirmed] The biggest public-beta risks are not raw secret leakage in first-layer cabinet UI; they are payment-history absence, artifact/trust status, missing live proof, and support-thread coverage.

## What I changed

- [confirmed] Created this research file only: `docs/developer/work-orders/2026-04-public-beta-release/research/R04-user-cabinet.md`.

## How I verified

- [confirmed] Static read-only inspection of the assigned cabinet files, API wrappers, E2E specs, and inherited evidence.
- [confirmed] `git status` showed many existing concurrent modifications; I did not revert or edit them.
- [needs local run] No local build, Playwright run, browser screenshot pass, deploy, live payment, live Telegram, or live support-upload verification was performed by this R04 pass.

## What remains / risk

- [needs local run] Fresh `webapp` build and E2E after the public-beta wave settles.
- [needs local run] Add support-thread reply/upload E2E and checkout handoff URL assertion.
- [blocked by missing access] Live session, hosted checkout, Telegram bonus, runtime downloads, and upload storage checks.
- [probable] Public-beta captain should decide whether Android remains internal-only while Windows is gated beta, or whether public labels wait for signing/audit closure.
