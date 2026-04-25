# WO-008 Infra, Nodes, Observability, Deploy Evidence

Status: first-pass local evidence; post-W10 quick/full local gates pass
Agent: W08
Last updated: 2026-04-25

## What I checked

- Required wave context: `00-orchestrator-context.md`, `INDEX.md`, `01-research-synthesis.md`, `research/R09-infra-observability-security.md`, `research/R10-qa-release-docs.md`, `evidence/security-audit/WO-009-security-baseline.md`, and `work-orders/WO-008-infra-nodes-observability-deploy.md`.
- Canonical ops/developer docs required by `AGENTS.md`: docs index, product overview, system overview, app-first flow, deployment/access, monitoring/visibility, developer guide, and repository map.
- W08 write-scope files only: release gate report generator plus deployment and monitoring docs plus this evidence log.
- Baseline dirtiness: `platform-git-diff-name-only-before.txt` already listed `docs/operations/deployment-and-access.md` and `docs/operations/monitoring-and-visibility.md`; I touched them to add W08 paid-beta deploy/rollback, redaction, metrics freshness, and origin-blocked rules.
- I did not edit `portal_bot/api.py`, webapp UI, marketing UI, or client code.

## What I found

- `scripts/release_gate_check.py` previously reported a single global pass/fail plus command tails, but did not clearly classify `current-origin`, `brain-origin`, `RU-origin`, Android physical audit, runtime smoke, or client platform build evidence.
- The saved release-gate evidence remains insufficient for paid-beta signoff without fresh active-lane proof and separate origin labels.
- Live production/brain/RU checks were not possible in this pass because the task did not provide live SSH/admin/RU probe credentials or physical Android hardware.
- A local quick gate can run without live secrets, but the current dirty candidate is not green.

## What I changed

- `scripts/release_gate_check.py`
  - Adds report context for quick/default gate scope, brain IP presence, selected client platform gates, runtime smoke, and Android audit scope.
  - Adds an `Evidence Classification` table with explicit statuses for current-origin, brain-origin, RU-origin, Android physical audit, runtime app-download smoke, and client platform builds.
  - Redacts obvious token/secret/password/bearer values from generated markdown command lines and output tails.
- `docs/operations/deployment-and-access.md`
  - Adds paid-beta deploy/rollback checklist, promotion-safety capture requirements, emergency switch capture requirements, and evidence redaction rules.
  - Adds release-gate classification expectations.
- `docs/operations/monitoring-and-visibility.md`
  - Adds blocked-by-access origin labeling guidance.
  - Adds per-node metrics freshness states: `ok`, `stale`, `missing`, `unavailable`, and `failed`.

## How I verified

Passed:

- `python -m unittest tests.test_release_gate_check -v` -> `10 passed`
- redaction helper smoke via `python -c ... release_gate_check._redact_text(...)` -> token/password/bearer/secret assignment values printed as `<redacted>`
- `python -m pytest tests/test_observer_service.py tests/test_observer_api.py -q` -> `6 passed`
- `python -m pytest tests/test_collect_xray_observer.py tests/test_predeploy_node_readiness.py -q` -> `8 passed`
- `python -m pytest tests/test_nodes_repo_load_aware.py tests/test_node_access.py -q` -> `5 passed`
- `python -m pytest tests/test_collect_node_metrics_observability.py tests/test_node_observability_gate.py tests/test_node_observability_schema.py -q` -> `11 passed`, with existing `datetime.utcnow()` deprecation warnings in tests
- `python -m pytest tests/test_release_gate_check.py tests/test_release_orchestrator.py -q` -> `19 passed`

Quick release gate:

- `python scripts/release_gate_check.py --quick --output .tmp/WO-008-release-gate-quick-report.md` -> `FAIL`
- Passed gates: critical worker regression, API lifecycle smoke, public link checks, marketing production build, admin webapp smoke, webapp production build.
- Failed gates:
  - `Client security smoke`: Windows release seed no longer has expected `pokrov_windows_seed.exe` binary name/required file.
  - `Client portal Flutter tests`: `selected apps status is explicit beta MVP copy` failed in active `POKROV-app`.
  - `WebApp Playwright E2E`: 5 cabinet-flow specs failed around email-soon, settings/Telegram bonus, payment history/checkout copy, and downloads/support copy.
  - `UI visual smoke`: stale/missing webapp-entry and dashboard copy expectations.
- The generated quick report classified `current-origin check` as `FAIL`, `brain-origin check` as `BLOCKED_BY_ACCESS`, `RU-origin check` as `BLOCKED_BY_ACCESS`, Android physical audit as `BLOCKED_BY_ACCESS`, runtime app-download smoke as `SKIPPED_NO_LIVE_TOKEN`, and client platform builds as `NOT_REQUESTED`.

## Post-W10 Orchestrator Follow-Up

After W03/W07/W10 follow-up work, the current local candidate was rerun through the release gates:

- `python scripts/release_gate_check.py --quick --output docs/audit-artifacts/release_gate_quick_report.md`: `PASS`.
- `python scripts/release_gate_check.py --output docs/audit-artifacts/release_gate_report.md`: `PASS`.
- `python scripts/run_client_release_gate.py build --target windows`: `PASS`.

The first-pass W08 `.tmp` quick-gate failures are historical and no longer represent the current local gate state.

## What remains / risk

- Paid beta is no longer blocked on the default local gate set, but it remains blocked on live/operator evidence below.
- Brain-origin deploy/readiness, metrics freshness from production admin endpoints, and post-deploy service verification remain `BLOCKED_BY_ACCESS`.
- RU-origin readiness remains `BLOCKED_BY_ACCESS`; `mini` or a replacement external RU probe host is still required.
- Android public release remains blocked until a release-installed physical device passes the localhost/control-surface audit.
- Production Postgres backup/restore proof was not collected in this pass and must be captured before any migration/data deploy.
- No deploy or push was performed.

## current-origin check

- Local non-secret observer/node/release unit checks: `PASS`.
- Local quick and default release gates from the current workstation: `PASS`, with reports at `docs/audit-artifacts/release_gate_quick_report.md` and `docs/audit-artifacts/release_gate_report.md`.

## brain-origin check

- `BLOCKED_BY_ACCESS`.
- Required follow-up: run `python scripts/verify_brain_ready.py --brain-ip 82.21.114.104` or `python scripts/release_gate_check.py --brain-ip 82.21.114.104 --quick` with approved access, then record redacted service, metrics, and probe evidence.

## RU-origin check

- `BLOCKED_BY_ACCESS`.
- Required follow-up: run `python scripts/ru_probe_runner.py --reserve-host rf1.pokrov.space --probe-host mini --out ops-local/ru-probe.json` from a healthy external RU origin or replacement, then render a redacted summary with `python scripts/render_ru_probe_report.py --input ops-local/ru-probe.json`.

## Changed file paths

- `docs/operations/deployment-and-access.md`
- `docs/operations/monitoring-and-visibility.md`
- `docs/developer/work-orders/2026-04-beta-release/evidence/logs/WO-008-infra-nodes-observability-deploy.md`
- `scripts/release_gate_check.py`
