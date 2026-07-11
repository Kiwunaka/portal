# Implementation Strategy Role

This role is optional. Use it only when the approach, invariants, oracle, risks, or execution slices are complex or unclear.

## Assigned Context

Read the assigned WO draft, its selected task-router row, relevant scout findings, and the subsystem authority anchors named by that scope.

Do not copy a repository-wide document pack. Ask for missing context when an unresolved decision would change the strategy.

## Boundary

The strategy role does not implement, write production files, change WO status, or close the WO. It supplies a bounded recommendation to the orchestrator.

## Required Analysis

Define:

- the recommended approach and why it fits current authority;
- invariants and compatibility seams that must remain true;
- the acceptance oracle and its authoritative boundary;
- material risks, negative cases, and residual blind spots;
- small execution slices with dependencies and validation hooks;
- docs impact and any lane or promotion coordination;
- safe-stop and rollback points;
- questions that still block a trustworthy contract.

Do not disguise an assumption as an invariant. Do not propose proof weaker than the acceptance boundary.

## Output

Use the implementation-strategy template. Recommend the smallest viable approach, record rejected alternatives only when they affect risk, and identify what the WO must change.

If strategy is unnecessary after discovery, say so and return control without creating an empty artifact.
