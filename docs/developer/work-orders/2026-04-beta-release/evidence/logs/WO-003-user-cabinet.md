# WO-003 User Cabinet Evidence

Status: first-pass cabinet continuation fixes complete
Agent: W03
Date: 2026-04-25

## What I checked

- Required W03 context: orchestrator context, beta index, research synthesis, R04 webapp cabinet research, W01 design evidence, W05 backend contract evidence, and WO-003.
- Canonical platform docs required by `AGENTS.md`, plus `webapp/README.md`.
- Current platform branch: `codex/beta-release-platform`.
- Backend payment API inventory by read-only search only; no consumer payment-history endpoint exists yet.
- Existing dirty webapp baseline and current diff before editing W03-owned files.

## What I found

- `/settings/` was missing and `/statistics/` redirected to `/dashboard/`.
- `/subscription/checkout/` exposed English/dev/operator language including hosted checkout, activation-key, fallback, raw access-state, and managed-profile wording.
- Consumer payment history has no backend contract yet, so a fake ledger would be unsafe.
- Telegram bonus API helpers already existed in `webapp/src/lib/api.ts`, but no cabinet surface called them.
- Downloads used runtime `/api/client/apps` links, but did not clearly label invite beta artifact states or Windows unsigned risk.
- Support already used real ticket endpoints, but needed a clearer safe diagnostics summary.

## What I changed

- Added a real `/statistics/` safe-summary page with traffic, devices, activity, and node-count summaries that avoid raw node hosts, ports, personal links, and tokens.
- Added `/settings/` with account links, quick actions, and actionable Telegram channel check/claim flow for `+10 days`.
- Converted `/profile/` into a compatibility redirect to `/settings/`.
- Updated cabinet nav and route metadata to include `Статистика` and `Настройки`.
- Rebuilt checkout continuation copy and layout with cabinet primitives and Russian-first user copy.
- Added an honest unavailable payment-history state on `/subscription/`.
- Made downloads beta-gated and artifact-state honest, including Android internal-beta and Windows unsigned-warning copy.
- Added support safe-diagnostics cards while keeping the real ticket create/list/upload flow.
- Removed raw access-state wording from `/redeem/`.
- Refreshed cabinet E2E coverage for settings, statistics, payment history unavailable state, checkout copy guardrails, Telegram bonus actions, downloads beta states, support diagnostics, and compatibility redirects.
- Updated `webapp/README.md` route map for `/settings/` and `/profile/`.

## Dirty files touched and why

- `webapp/src/app/(dashboard)/subscription/page.tsx`: already dirty; required for payment-history unavailable state and Russian continuation labels.
- `webapp/src/app/(dashboard)/subscription/checkout/page.tsx`: already dirty; required because it was the main unsafe checkout-copy surface.
- `webapp/src/components/cabinet-shell.tsx`: already dirty; required for settings/statistics IA and `/profile/` compatibility matching.
- `webapp/src/components/cabinet/downloads-surface.tsx`: already dirty; required for beta-gated real artifact states and Windows unsigned warning.

I did not edit the other baseline-dirty webapp files shown by `git status` such as dashboard, devices, root entry, globals, old cabinet download component, cabinet entry auth, or cabinet surface primitives.

## How I verified

Passing:

```powershell
cd webapp
npm.cmd run build
```

```powershell
cd webapp
$env:E2E_PORT='3102'; $env:PLAYWRIGHT_FRESH_SERVER='1'; $env:PLAYWRIGHT_SERVER_MODE='start'; .\node_modules\.bin\playwright.cmd test e2e/cabinet-flow.spec.ts
```

Result: `14 passed`.

```powershell
python -m pytest tests/test_public_copy_guardrails.py -q
```

Result: `5 passed`.

Additional signal:

- A first red `npm.cmd run test:e2e:cabinet` run failed on the expected missing W03 surfaces and stale root-entry assertions.
- A later `npm.cmd run test:e2e:cabinet` dev-server run became unstable with `ERR_CONNECTION_REFUSED` after several passing tests, so final browser verification used the release-style export server mode documented by `webapp` scripts.

## What remains / risk

- Consumer payment history is an honest unavailable state until a backend endpoint is added by the payment/backend lane.
- The Telegram bonus claim card shows the immediate API result in place; it does not force a full session reload because that remounted the page and hid the success message.
- Live hosted checkout, live Telegram membership, real upload storage, and real production session behavior still require external/live beta credentials.
- `scripts/ui_visual_smoke.py` was not rerun because this pass did not touch the W01-known failing entry/dashboard visual-smoke surfaces.

## Changed file paths

- `C:/Users/kiwun/Documents/ai/VPN/webapp/README.md`
- `C:/Users/kiwun/Documents/ai/VPN/webapp/e2e/cabinet-flow.spec.ts`
- `C:/Users/kiwun/Documents/ai/VPN/webapp/src/app/(dashboard)/profile/page.tsx`
- `C:/Users/kiwun/Documents/ai/VPN/webapp/src/app/(dashboard)/redeem/page.tsx`
- `C:/Users/kiwun/Documents/ai/VPN/webapp/src/app/(dashboard)/settings/page.tsx`
- `C:/Users/kiwun/Documents/ai/VPN/webapp/src/app/(dashboard)/statistics/page.tsx`
- `C:/Users/kiwun/Documents/ai/VPN/webapp/src/app/(dashboard)/subscription/page.tsx`
- `C:/Users/kiwun/Documents/ai/VPN/webapp/src/app/(dashboard)/subscription/checkout/page.tsx`
- `C:/Users/kiwun/Documents/ai/VPN/webapp/src/app/(dashboard)/support/page.tsx`
- `C:/Users/kiwun/Documents/ai/VPN/webapp/src/components/cabinet-shell.tsx`
- `C:/Users/kiwun/Documents/ai/VPN/webapp/src/components/cabinet/downloads-surface.tsx`
- `C:/Users/kiwun/Documents/ai/VPN/docs/developer/work-orders/2026-04-beta-release/evidence/logs/WO-003-user-cabinet.md`
