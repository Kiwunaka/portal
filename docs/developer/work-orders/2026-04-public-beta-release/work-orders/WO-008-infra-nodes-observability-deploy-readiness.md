# WO-008 Infra, Nodes, Observability, Deploy Readiness

Status: draft
Agent: W08
Lane: platform
Priority: P0/P1

## Goal

Verify and document deploy, rollback, node, metrics, probe, and observability readiness for public beta.

## Write Scope

- `scripts/collect_node_metrics.py`
- `scripts/node_dataplane_probe.py`
- `scripts/release_gate_check.py`
- `scripts/verify_brain_ready.py`
- `infra/**`
- `docs/operations/deployment-and-access.md`
- `docs/operations/monitoring-and-visibility.md`
- `docs/developer/work-orders/2026-04-public-beta-release/**`

## Acceptance

- Deploy path known.
- Rollback path known.
- Metrics real or explicitly unavailable.
- Node health visible.
- current-origin, brain-origin, and RU-origin evidence classified separately.
- Emergency controls are visible or listed as blockers.

## Validation

```powershell
python -m pytest tests/test_observer_service.py tests/test_observer_api.py -q
python -m pytest tests/test_collect_xray_observer.py tests/test_predeploy_node_readiness.py -q
python -m pytest tests/test_nodes_repo_load_aware.py tests/test_node_access.py -q
python scripts/verify_brain_ready.py
```

