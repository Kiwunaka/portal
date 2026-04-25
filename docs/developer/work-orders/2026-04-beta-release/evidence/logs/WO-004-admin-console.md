# WO-004 Admin Console Evidence

Updated: 2026-04-25
Branch: `codex/beta-release-platform`
Worker: W04

## What I checked

- Read the W04 required orchestration, synthesis, research, upstream evidence, security baseline, and work-order files.
- Read the repository must-read docs and `webapp/README.md` before changing admin code.
- Inspected the current admin shell, admin nav, user side panel, web API client, admin Playwright coverage, and `portal_bot/api.py` admin/user/payment-adjacent sections.
- Checked the dirty workspace before edits. `portal_bot/api.py` was already dirty from concurrent payment/backend work; I touched it because the payment ledger needed a real admin API. I left unrelated dirty files untouched, including non-admin cabinet files owned by W03.

## What I found

- Admin routes existed for several operator areas, but there was no real payment/order ledger route in the admin nav or UI.
- The backend exposed payment callback and checkout behavior, but no admin-safe order listing endpoint and no note-required manual reconciliation endpoint.
- User detail already showed access and support/ticket context, but not enough payment order or device context for beta triage.
- Existing admin tests did not prove that manual reconciliation requires an audit note or that raw provider payload text stays out of the admin UI.

## What I changed

- Added an admin payment ledger API that lists real `ExternalOrder` rows with user context and last callback summary, without exposing raw provider payload JSON or metadata secrets.
- Added a note-required manual reconciliation API for payment orders. It updates ledger status only, records an `AdminAudit` entry with note/from/to status, and does not silently grant or revoke access.
- Added recent payment orders to the admin user card contract so support triage can see payment/access/device/ticket context together.
- Added `/admin/payments` to the admin nav and implemented the payment ledger UI with real loading/error/empty states, filters, last callback visibility, and reconciliation dialog validation.
- Extended the admin user side panel with device context and recent payment order visibility.
- Added backend and Playwright coverage for the payment ledger and note-required reconciliation flow.

## How I verified

- `python -m pytest tests/test_admin_payments_api.py -q --basetemp .tmp/pytest-w04-admin-payments-red` failed before implementation on missing admin payment endpoints.
- `npx.cmd playwright test e2e/admin-gate.spec.ts --grep 'payment ledger'` failed before implementation because `/admin/payments/` was unavailable.
- `python -m pytest tests/test_admin_payments_api.py -q --basetemp .tmp/pytest-w04-admin-payments-green` passed: 2 tests.
- `python -m pytest tests/test_admin_payments_api.py tests/test_admin_webapp_smoke.py -q --basetemp .tmp/pytest-w04-admin-combined` passed: 3 tests.
- `python scripts/admin_webapp_smoke.py` passed.
- `python -m pytest tests/test_api_auth_and_tickets.py tests/test_admin_webapp_smoke.py -q --basetemp .tmp/pytest-w04-admin-auth-tickets` passed: 58 tests.
- `npm.cmd run build` in `webapp/` passed.
- `npm.cmd run test:e2e:admin` in `webapp/` passed: 17 Playwright tests.
- `git diff --check` on W04-owned changed paths passed with only line-ending warnings for existing CRLF/LF normalization.

## What remains / risk

- The new reconciliation endpoint intentionally does not change subscriptions or device access. Operators still need the existing explicit access actions for entitlement changes.
- The ledger is limited to the latest 100 rows in the UI and backend defaults; deeper finance export/reporting remains outside this beta hardening pass.
- Canonical product/user docs were not changed because this is an internal admin beta contract and public product behavior did not change.
- The workspace still contains unrelated concurrent dirty and untracked files from other workers. I did not revert or clean them.

## Changed file paths

- `portal_bot/api.py`
- `tests/test_admin_payments_api.py`
- `webapp/src/lib/api.ts`
- `webapp/src/app/(dashboard)/admin/nav.ts`
- `webapp/src/app/(dashboard)/admin/payments/page.tsx`
- `webapp/src/components/admin/users/admin-user-side-panel.tsx`
- `webapp/e2e/admin-gate.spec.ts`
- `docs/developer/work-orders/2026-04-beta-release/evidence/logs/WO-004-admin-console.md`
