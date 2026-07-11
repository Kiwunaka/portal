# POKROV Orchestration

Last updated: 2026-07-11

This directory owns the Codex-native process for work that needs durable context, bounded execution, independent review, or release proof. It defines process, not product truth.

## Quick Start

Choose the smallest ceremony that controls the actual risk.

| Ceremony | Trigger | Required artifacts |
| --- | --- | --- |
| `direct` | small, low-risk, single-pass work | focused validation and handoff |
| `bounded_wo` | durable context, independent review, multiple bounded steps, or meaningful risk | compact WO; selected roles; conditional `FLOW_STATE` |
| `release_wo` | release, deploy, payment, security, persistence, provider, device, or origin-sensitive work | full triggered proof blocks, release validator, candidate-specific evidence |

`direct` work does not require a work order or `FLOW_STATE`. For either WO ceremony:

1. Resolve the repository lane and exact write scope through the [task router](../agent-context-map.md).
2. Run the collision gate against current worktrees before execution.
3. Create one compact WO from the [authoring guide](wo-authoring-guide.md).
4. Select only the roles needed for the risk.
5. Add [FLOW_STATE](flow-state.md) only when its conditional trigger fires.
6. Close against the acceptance oracle and structured evidence, not chat memory.

## Process Owners

- [orchestration-standard.md](orchestration-standard.md): ceremony, routing, lifecycle, role selection, review, and closure.
- [wo-authoring-guide.md](wo-authoring-guide.md): compact WO contract and trigger-based proof blocks.
- [flow-state.md](flow-state.md): conditional review-loop state and same-class stop mechanism.
- [context-cost-harnesses.md](context-cost-harnesses.md): provider-neutral packet, redaction, telemetry, and audit rules.
- [roles/](roles/): bounded role contracts selected by the orchestrator.
- [templates/](templates/): WO, review, strategy, discovery, wave, and completion artifacts.
- [work-orders/README.md](../work-orders/README.md): wave storage, continuity, and evidence boundary.

## Context Rule

There is no universal document pack or mandatory role chain. Each participant reads the assigned WO, the selected router row, and only the subsystem owners needed for that scope. Expand context when evidence exposes a real dependency.

## Authority Boundary

Canonical product, architecture, operations, design, and active client documents remain authoritative for intended behavior. Code, tests, and exact runtime evidence establish implementation and observed state. Work orders preserve execution context and evidence; they do not override those owners.

Completed or superseded work orders are immutable evidence. Correct them with an addendum or a superseding WO.
