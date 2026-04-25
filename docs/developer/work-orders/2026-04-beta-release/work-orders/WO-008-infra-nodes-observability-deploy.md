# WO-008 Infra, Nodes, Observability, Deploy Readiness

Status: draft
Lane: platform

## Scope

Prepare paid beta infra, node health, metrics, origin checks, deploy readiness, and rollback evidence.

## Assigned Paths

- `infra/**`
- `scripts/collect_node_metrics.py`
- `scripts/remote_*`
- `scripts/node_access.py`
- `scripts/release_orchestrator.py`
- `scripts/release_gate_check.py`
- operations docs if behavior changes

## Required Behavior

- Admin shows real node/route health or explicit unavailable state.
- Metrics are not fake.
- Alerts classify high latency, high CPU, stale metrics, packet loss, overload, offline.
- Origin checks are documented as current-origin, brain-origin, and RU-origin.
- Deploy handoff says what was deployed and what was not.
- No secrets printed in logs/evidence.

## Deploy And Rollback Gate

Deploy is allowed only after:

- core gates are green or explicitly classified
- DB backup is completed if migrations are included
- rollback command/path is documented
- current deployed version is captured
- new version/artifact identifiers are captured
- payment/webhook test is run in low-volume mode
- admin can disable checkout/downloads after deploy

Promotion safety:

- capture current local HEAD and remote HEAD
- do not force-push or overwrite remote changes if behind `origin/master`
- do not force-push or overwrite remote changes if client branch is behind `origin/main`
- orchestrator chooses merge/rebase/cherry-pick after gates
- local dirty beta candidate deploy is allowed only if exact commit/patch state and rollback path are captured

## Validation

- `python -m pytest tests/test_observer_service.py tests/test_observer_api.py -q`
- `python -m pytest tests/test_collect_xray_observer.py tests/test_predeploy_node_readiness.py -q`
- `python -m pytest tests/test_nodes_repo_load_aware.py tests/test_node_access.py -q`
- `python scripts/verify_brain_ready.py`
- `python scripts/release_gate_check.py --brain-ip 82.21.114.104 --quick`

## Handoff Format

- What I checked
- What I found
- What I changed
- How I verified
- What remains / risk
- current-origin check
- brain-origin check
- RU-origin check
