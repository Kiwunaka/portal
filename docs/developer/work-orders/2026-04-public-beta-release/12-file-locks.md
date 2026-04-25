# File Locks

Status: active

## Current Locks

| Path | Owner | Reason | Status |
|---|---|---|---|
| `docs/developer/work-orders/2026-04-public-beta-release/**` | orchestrator | wave control artifacts | active |

## Lock Policy

- Research agents may write only their assigned `research/Rxx-*.md`.
- Work agents may write only files assigned in their WO.
- Agents are not alone in the codebase and must not revert edits made by others.
- Any lock conflict must be routed through the orchestrator.

