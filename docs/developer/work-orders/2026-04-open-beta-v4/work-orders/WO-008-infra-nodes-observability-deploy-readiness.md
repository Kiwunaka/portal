# WO-008 Infra, Nodes, Observability, Deploy Readiness

Status: pending research
Owner: W08

## Scope

- Node metrics and probe scripts.
- Deploy and rollback runbooks.
- Brain/current/RU origin evidence.
- Admin network status requirements.

## Acceptance

- Origin evidence is separated and labeled.
- Node metrics freshness and alert reasons are actionable.
- Deploy and rollback runbooks name required commands and blockers.
- RU-origin missing access is documented without implying green status.

## Verification

```powershell
python scripts/predeploy_node_readiness.py --brain-ip 82.21.114.104 --web-domain pokrov.space
python scripts/release_gate_check.py --quick
```
