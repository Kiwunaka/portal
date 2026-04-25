# Beta Release Wave - POKROV

Status: blocked - local default gates green; live/operator paid-beta proofs missing
Created: 2026-04-24
Canonical platform lane: portal/master
Canonical client lane: POKROV-app/main
Platform integration branch: codex/beta-release-platform
Client integration branch: codex/beta-release-client

## Global Beta Goal

Bring POKROV to a paid, invite-limited beta release candidate on production domains. This is not a public stable launch.

Beta is ready only when marketing, cabinet, app, admin, backend, payments, support, observability, release artifacts, docs, and emergency controls are truthful enough for up to 25 paid beta users.

## Paid Beta Safety Policy

Hard limits:

- Max active beta users: 25.
- Beta access is invite-controlled.
- Checkout must be disableable within 5 minutes.
- Downloads must be cabinet-gated and beta-labeled.
- Android APK is internal beta only unless signing and physical localhost audit pass.
- Windows unsigned build is allowed only as a gated beta artifact with explicit warning.
- No store or public cutover claim is allowed.
- No production SLA claim is allowed.
- Support target is best-effort 24h response, not guaranteed 24/7 SLA.
- Public and user copy must say beta where expectations matter.

Emergency controls required before deploy:

- disable checkout
- disable new trial issuance
- disable artifact downloads
- pause Telegram bonus claims
- pause payment webhook fulfillment
- manually extend or revoke beta access from admin
- show maintenance or unavailable state instead of fake success

## Current Blockers

| Blocker | Area | Status | Evidence | Owner WO |
|---|---|---|---|---|
| Paid beta provider acceptance and signed webhook behavior not confirmed | payments | open | `research/R07-payments-telegram-support.md` | WO-006 |
| Payment entitlement state handling has local regression coverage and admin ledger/reconciliation; live/provider proof remains open | payments/backend/admin | local regression green in W10; live/provider proof still open | `evidence/logs/WO-006-payments-keys-bonuses-support.md`, `evidence/logs/WO-004-admin-console.md`, `evidence/release-gates/W10-final-gate-summary.md` | WO-006, WO-004, WO-010 |
| Public marketing unsafe claims were removed in first pass; browser, copy, link, and visual gates pass locally | marketing/copy | local gates green; live deploy proof missing | `evidence/logs/WO-002-marketing-checkout-install.md`, `docs/audit-artifacts/release_gate_report.md` | WO-002, WO-010 |
| Cabinet continuation gaps were addressed in first pass; payment history is honest unavailable until backend endpoint exists | webapp | local build and E2E pass in W10 | `evidence/logs/WO-003-user-cabinet.md`, `docs/audit-artifacts/release_gate_report.md` | WO-003, WO-010 |
| Admin paid beta operator gaps mitigated with real payment ledger/manual reconciliation; broader live/admin metrics still need final gates | admin | local admin gates pass; live metrics blocked | `evidence/logs/WO-004-admin-console.md`, `docs/audit-artifacts/release_gate_report.md` | WO-004, WO-010 |
| Backend live Postgres, migration, profile delivery, and abuse controls unverified | backend/data | open | `research/R06-backend-api-data.md` | WO-005 |
| Android public release blocked by signing, handoff, runtime verification, and physical audit | client/security | internal beta only after W07 | `evidence/logs/WO-007-client-android-windows-beta.md` | WO-007, WO-009 |
| Windows trusted public release blocked; unsigned beta build now stages locally with warning metadata | client/release | local build green; public cutover blocked by signing/handoff proof | `evidence/logs/WO-007-client-android-windows-beta.md`, `evidence/release-gates/W10-final-gate-summary.md` | WO-007, WO-010 |
| Default local gate pack is green after post-W10 follow-up; paid-beta live/operator gates remain missing | release | blocked for paid beta | `docs/audit-artifacts/release_gate_report.md`, `evidence/release-gates/W10-final-gate-summary.md` | WO-010 |
| Live deploy, backup, rollback, brain-origin, RU-origin, and Android physical evidence missing or blocked by access | infra/ops | open; W08 classification added | `evidence/logs/WO-008-infra-nodes-observability-deploy.md` | WO-008, WO-010 |

## Research Agents

| ID | Scope | Status | Output | Key blockers |
|---|---|---|---|---|
| R01 | Product scope, beta definition, canonical docs | completed - Turing `019dc159-83f9-7da3-a791-f7ed5293a15a` | `research/R01-product-scope.md` | Android/signing, Windows signing/handoff, stale 7-day trial path, stale `POKROV VPN` canon note, live payment/deploy gates unverified |
| R02 | Design system, brand, visual audit | completed - Aquinas `019dc15f-248a-7170-8081-8465b92bb544`; replaced failed Confucius `019dc159-884d-7ec2-9598-f5f84da856f3` | `research/R02-design-system.md` | `Premium VPN` legacy subtitle, AES/WireGuard hero, checkout English/dev labels, client shell English-first, visual QA needs local runs |
| R03 | Marketing, checkout, install, legal | completed - Euler `019dc159-8cc5-75b1-97e7-d7c9b33a5fb5` | `research/R03-marketing-checkout.md` | Android labeled public release, unsupported AES/WireGuard/24-7 claims, hardcoded reviews JSON-LD, Germany/Frankfurt visual conflicts |
| R04 | WebApp user cabinet | completed - Boole `019dc159-912f-75f0-8d9e-efec1fecaf30` | `research/R04-webapp-cabinet.md` | `/settings/` missing, `/statistics/` redirects, checkout leaks internal/English copy and old styling, no payment history, Telegram bonus not actionable, E2E stale |
| R05 | Admin console | completed - Boyle `019dc159-fc3f-7672-9505-f5cdfeaec42c` | `research/R05-admin-console.md` | no payment/order ledger, plan/promo CRUD not exposed, no first-class devices, no incidents/SLA, rollout raw JSON-only, live admin blocked by access |
| R06 | Backend API, data model, migrations | completed - Heisenberg `019dc15a-00a3-7171-8fa1-e7415a59f452` | `research/R06-backend-api-data.md` | live Postgres/migrations blocked by access, control-panel/profile smoke needed, backend tests need run, install_id trial abuse probable, multi-device management incomplete |
| R07 | Payments, keys, Telegram, support bots, feedback | completed - Averroes `019dc15a-059d-7103-bbc1-8be0e5181da6` | `research/R07-payments-telegram-support.md` | no provider beta-ready, Lava/Tribute need acceptance/live webhook verification, Kassa.ai docs blocked, direct paid activation diverges from key-first, refunds do not revoke/adjust access |
| R08 | Client Android and Windows beta readiness | completed - Banach `019dc156-cf23-70a2-a8b2-555d9077ff19` | `research/R08-client-android-windows.md` | Android debug signing/physical audit, Windows unsigned seed lane, blank public handoff URLs, seed labels, selected apps missing, client still sends `trial_days` |
| R09 | Infra, observability, security/privacy | completed - Peirce `019dc156-d35c-7371-ac80-cda625303c4a` | `research/R09-infra-observability-security.md` | active-lane release gate rerun needed, Android physical audit missing, brain/RU/live metrics blocked by access, backup/restore proof unknown, security hardening risks |
| R10 | QA, release gates, docs, tech debt | completed - Cicero `019dc156-d792-73c2-b61e-99227af032f0` | `research/R10-qa-release-docs.md` | stale saved gate, payment callback tests not in default gate, Android audit missing, signing/handoff unproven, provider acceptance pending, live deploy/origin evidence missing |

## Work Orders

| WO | Scope | Lane | Agent | Status | Validation | Risk |
|---|---|---|---|---|---|---|
| WO-001 | Design system, brand assets, visual parity | mixed | Jason `019dc171-a972-7bd0-9821-5f378b5350c5` | first-pass evidence complete; downstream adoption open | copy guardrails pass; marketing/webapp build pass; visual smoke failing out of scope | design/copy drift |
| WO-002 | Marketing, checkout, install, legal | platform | Kuhn `019dc181-55b6-75e0-bf10-b7c9e742534d` | first-pass complete; checkout URL-key risk open | marketing build/SEO/link/copy checks pass; visual smoke blocked by webapp | unsafe claims |
| WO-003 | User cabinet | platform | Einstein `019dc181-5a69-7112-9c6e-25ae2021e25f` | first-pass complete; live checks open | webapp build pass; cabinet E2E 14 passed | continuation gaps/raw leakage |
| WO-004 | Admin console | platform | Anscombe `019dc18b-9022-7502-8754-0401b7cd706f` | first-pass complete; entitlement-action separation accepted pending W10 | admin API/smoke/build/E2E pass | fake/missing operator data |
| WO-005 | Backend contract hardening | platform | Goodall `019dc171-ae12-7c80-ba01-47116b19b1cd` | first-pass guardrails complete; live evidence open | backend suites pass; payment callback copy drift failing out of scope | identity/state/profile bugs |
| WO-006 | Payments, keys, Telegram bonus, support/feedback | platform | Meitner `019dc181-5ebd-7482-8a37-20b465250116` | first-pass payment hardening complete; provider/live proof open | payment/bot/ticket/worker tests pass; provider proof blocked | paid access mismatch |
| WO-007 | Android/Windows beta client | client | Poincare `019dc181-6328-7cc0-89b3-6c2d3e54f701` | first-pass complete; platform smoke follow-up resolved | client tests, seed validation, client security smoke, and Windows build pass | signing/audit/handoff gaps |
| WO-008 | Infra, nodes, observability, deploy readiness | platform | Kierkegaard `019dc181-6834-7b82-8201-1a237d3ce2aa` | first-pass complete; local quick/full gates green after follow-up | focused tests pass; quick/full local reports pass | stale metrics/rollback |
| WO-009 | Security, privacy, abuse, compliance audit | mixed | Avicenna `019dc171-b24d-7471-b8ea-c3023fa96998` | first-pass evidence complete; P0/P1 open | `client_security_smoke.py` pass; copy guardrails pass; payment/auth suite 1 failing | secrets/control surfaces |
| WO-010 | Paid beta release captain | mixed | W10 | final signoff complete: blocked; local stale gates resolved post-W10 | full/quick default gates green; payment/auth green; Android APK/AAB and Windows builds green; live/origin gates blocked | release confusion |

## Release Gates

| Gate | Command | Required for beta | Status | Evidence |
|---|---|---:|---|---|
| Backend app-first | `python -m pytest portal_bot/tests/test_app_first_api.py -q` | yes | passed in W05 | `evidence/logs/WO-005-backend-contract-hardening.md` |
| Backend core API | `python -m pytest tests/test_portal_api.py tests/test_api_auth_and_tickets.py tests/test_api_payments_callbacks.py -q` | yes | W10 release matrix passed core subset; supplemental auth/payment command passed `79 passed` | `docs/audit-artifacts/release_gate_report.md`, `evidence/release-gates/W10-final-gate-summary.md` |
| Worker/free cycle | `python -m pytest tests/test_worker_retention.py tests/test_free_cycle_service.py -q` | yes | passed in W06 | `evidence/logs/WO-006-payments-keys-bonuses-support.md` |
| Copy/UI smoke | `python -m pytest tests/test_public_copy_guardrails.py tests/test_ui_visual_smoke.py -q` / `python scripts/ui_visual_smoke.py` | yes | passed in full default release gate after post-W10 reconciliation | `docs/audit-artifacts/release_gate_report.md`, `evidence/release-gates/W10-final-gate-summary.md` |
| Link checks | `python scripts/check-links.py` | yes | passed in W02 | `evidence/logs/WO-002-marketing-checkout-install.md` |
| Admin smoke | `python scripts/admin_webapp_smoke.py` | yes | passed in W04 | `evidence/logs/WO-004-admin-console.md` |
| Client security smoke | `python scripts/client_security_smoke.py` | yes | passed after beta Windows metadata expectation update | `docs/audit-artifacts/release_gate_report.md`, `evidence/release-gates/W10-final-gate-summary.md` |
| API lifecycle | `python scripts/api_lifecycle_smoke.py` | yes | passed in quick and full local release gates | `docs/audit-artifacts/release_gate_report.md`, `docs/audit-artifacts/release_gate_quick_report.md` |
| Marketing build | `cd marketing; npm.cmd run build; npm.cmd run check:seo` | yes | build and SEO passed in W02 | `evidence/logs/WO-002-marketing-checkout-install.md` |
| WebApp E2E | `cd webapp; npm.cmd run build; npm.cmd run test:e2e; npm.cmd run test:e2e:admin` | yes | W10 full release report passed webapp build and combined Playwright E2E `31 passed`; W04 admin E2E previously passed | `docs/audit-artifacts/release_gate_report.md`, `evidence/logs/WO-004-admin-console.md` |
| Client tests | `cd C:/Users/kiwun/Documents/ai/POKROV-app; powershell -ExecutionPolicy Bypass -File ./scripts/run-tests.ps1` | yes | W10 full client suite passed through release gate | `docs/audit-artifacts/release_gate_report.md` |
| Client builds | `python scripts/run_client_release_gate.py build --target windows`, `--target android-apk`, and `--target android-aab` | yes | Android APK/AAB passed in W10; Windows build passed post-W10 with `pokrov_windows_beta.exe` | `evidence/release-gates/W10-final-gate-summary.md` |
| Full release report | `python scripts/release_gate_check.py --output docs/audit-artifacts/release_gate_report.md` | yes | default local gate set `PASS`; live/operator evidence still blocked/not requested | `docs/audit-artifacts/release_gate_report.md` |
| Android physical audit | `python scripts/android_localhost_audit.py --serial <serial>` | public Android only | blocked: `adb devices -l` showed no attached device | `evidence/release-gates/W10-final-gate-summary.md` |

## Final Signoff

- Design: local visual smoke, browser E2E, and builds pass.
- Backend: local release matrix and supplemental auth/payment gates pass; live Postgres/provider proof absent.
- Webapp: local build and combined Playwright E2E pass.
- Admin: local smoke/E2E evidence passes; live metrics/origin evidence absent.
- Client: Flutter tests, client security smoke, Android APK/AAB local builds, and Windows local build pass; public cutover still blocked by signing/audit/handoff.
- Infra: current-origin public host checks pass; brain-origin, RU-origin, backup/rollback, deploy proof blocked by access/not run.
- Security: Android public blocked by missing physical audit; payment provider live proof absent; evidence redaction policy preserved.
- Docs: W10 signoff and communications created; post-W10 local gate follow-up recorded; final decision remains `blocked`.
