# Final Git Promotion Record

Status: blocked-no-push-no-deploy

## Platform Lane

- Local branch: codex/public-beta-release-wave
- Local HEAD: see `evidence/logs/platform/platform-local-head-before.txt`
- Remote branch: origin/master
- Remote HEAD before promotion: see `evidence/logs/platform/platform-origin-master-head-before.txt`
- Dirty baseline evidence: `evidence/logs/platform/*`
- Internal commits included: IC-001, IC-002, IC-003, IC-004, IC-005, IC-006, IC-007, IC-008, IC-009, IC-010
- Real git commits created: none
- Merge/rebase/cherry-pick strategy: documented in `14-master-main-promotion-plan.md`; do not apply until external gates close and inherited dirty work is reviewed
- Push status: not pushed
- Deploy status: not deployed

## Client Lane

- Local branch: see `evidence/logs/client/client-current-branch-before.txt`
- Local HEAD: see `evidence/logs/client/client-local-head-before.txt`
- Remote branch: origin/main
- Remote HEAD before promotion: see `evidence/logs/client/client-origin-main-head-before.txt`
- Dirty baseline evidence: `evidence/logs/client/*`
- Internal commits included: IC-009, IC-010 for evidence/build classification
- Real git commits created: none
- Merge/rebase/cherry-pick strategy: documented in `14-master-main-promotion-plan.md`; promote reviewed client deltas only to `main`
- Push status: not pushed
- Artifact status: Windows beta zip/manifest, Android release APK, and Android release AAB built; public Android blocked by physical audit

## Validation After Promotion

- Commands run locally before promotion:
  - `python -m pytest tests/test_public_copy_guardrails.py -q`
  - `npm.cmd run check:seo` in `marketing/`
  - `npm.cmd run build` in `marketing/`
  - `npm.cmd run build` in `webapp/`
  - `npm.cmd run test:e2e` in `webapp/`
  - `python -m pytest tests/test_api_auth_and_tickets.py -q`
  - `python scripts/release_gate_check.py --output docs/audit-artifacts/public_beta_release_gate_report.md`
  - `python -m pytest tests/test_node_access.py -q`
  - `python -m pytest tests/test_predeploy_node_readiness.py -q`
  - `python scripts/release_gate_check.py --quick --brain-ip 82.21.114.104 --web-domain pokrov.space --passwords <root PASSWORDS.txt> --output docs/audit-artifacts/public_beta_release_gate_report_brain.md`
  - `python -m pytest tests/test_ru_probe_runner.py tests/test_render_ru_probe_report.py -q`
  - RU-origin probe from `mini`, rendered with `scripts/render_ru_probe_report.py`
  - `python -m pytest tests/test_api_payments_callbacks.py tests/test_admin_payments_api.py tests/test_freekassa_api_probe.py -q`
  - `python scripts/freekassa_api_probe.py --brain-ip 82.21.114.104 --passwords <root PASSWORDS.txt> --source site ...`
  - `python scripts/freekassa_api_probe.py --brain-ip 82.21.114.104 --passwords <root PASSWORDS.txt> --source bot ...`
  - `python scripts/run_client_release_gate.py build --target windows`
  - `python scripts/run_client_release_gate.py build --target android-apk`
  - `python scripts/run_client_release_gate.py build --target android-aab`
  - `python scripts/smoke_client_apps.py --base-url https://api.pokrov.space --check-providers --require-release-handoff`
  - `python scripts/release_gate_check.py --client-platform-gates android-apk --output docs/audit-artifacts/public_beta_release_gate_android_required.md`
  - `python -m pytest tests/test_node_access.py tests/test_predeploy_node_readiness.py tests/test_ru_probe_runner.py tests/test_render_ru_probe_report.py tests/test_freekassa_api_probe.py tests/test_api_payments_callbacks.py tests/test_admin_payments_api.py tests/test_public_copy_guardrails.py -q`
  - `git diff --check -- scripts/node_access.py tests/test_node_access.py scripts/ru_probe_runner.py tests/test_ru_probe_runner.py scripts/freekassa_api_probe.py tests/test_freekassa_api_probe.py docs/audit-artifacts docs/developer/work-orders/2026-04-public-beta-release`
- Results:
  - copy guardrails: `6 passed`
  - marketing SEO: passed
  - marketing build: passed
  - webapp build: passed
  - webapp E2E: `31 passed`
  - auth/tickets API tests: `58 passed`
  - default release gate report: local `PASS`
  - node access tests: `3 passed`
  - predeploy readiness tests: `5 passed`
  - brain-origin quick gate: `PASS`
  - RU probe/render tests: `7 passed`
  - payment/admin/probe tests: `25 passed`
  - client platform builds: Windows, Android APK, Android AAB completed
  - final focused regression set: `46 passed`
  - targeted whitespace check for changed release/tooling docs and scripts: passed with line-ending warnings only
  - full `git diff --check`: failed on inherited dirty `tests/test_bot_paywall.py` CRLF/trailing-whitespace noise; not auto-rewritten to avoid mixing unrelated dirty work
- Current blocked evidence:
  - payment provider live order creation: `BLOCKED_BY_PROVIDER_STATUS` (`Merchant not activated`)
  - RU-origin Telegram reachability: `FAIL` from `mini`
  - Android physical audit: `BLOCKED_NO_PHYSICAL_DEVICE`
  - runtime app-download smoke: `BLOCKED_NO_LIVE_TOKEN`
  - deploy/rollback/promotion: not run because release remains blocked
- Evidence:
  - `docs/audit-artifacts/public_beta_release_gate_report.md`
  - `docs/audit-artifacts/public_beta_release_gate_report_brain.md`
  - `docs/audit-artifacts/ru_probe_2026-04-26.md`
  - `docs/audit-artifacts/payment_provider_probe_2026-04-26.md`
  - `docs/audit-artifacts/client_platform_builds_2026-04-26.md`
  - `docs/audit-artifacts/runtime_app_download_smoke_2026-04-26.md`
  - `docs/audit-artifacts/android_physical_audit_2026-04-26.md`
  - baseline evidence under `evidence/logs/platform/*` and `evidence/logs/client/*`

## Promotion Decision

`blocked`: do not merge, push, or deploy as a public beta release until live payment provider activation/proof, Android physical release-build localhost/control-surface audit, runtime app-download smoke with live token, RU Telegram reachability/fallback decision, and deploy/rollback checks are complete.

## Rollback State

- Backend rollback: no deployed backend change in this wave
- Static rollback: no deployed static change in this wave
- Client artifact rollback: generated artifacts are local/build outputs; no public artifact promotion performed
- DB rollback: no migration or live DB mutation performed
- Payment rollback: no live payment completed; provider returned `Merchant not activated`
