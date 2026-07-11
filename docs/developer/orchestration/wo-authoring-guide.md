# POKROV WO Authoring Guide

Last updated: 2026-07-11

This guide owns the compact work-order contract and the conditions that expand it. The [orchestration standard](orchestration-standard.md) owns ceremony, routing, lifecycle, review, and closure.

## When To Create A WO

Use a WO for `bounded_wo` or `release_wo`. A direct task needs focused validation and handoff, not a placeholder WO.

Create one WO for one bounded outcome. If two outcomes have different write owners, acceptance oracles, or promotion paths, split them. A WO is durable task memory, not a transcript and not product canon.

## Compact Contract

Start from [WO.template.md](templates/WO.template.md). The compact WO contains only:

1. metadata;
2. goal;
3. non-goals;
4. write scope;
5. no-touch scope;
6. authority anchors;
7. acceptance oracle;
8. docs impact;
9. validation and evidence;
10. status and handoff.

Use exact paths in scope fields. Authority anchors should be the selected router row, canonical owners, current code/tests, and exact runtime evidence needed for this outcome. Do not paste a universal read pack.

The acceptance oracle states what observation decides success. A plan, prose review, or file edit is not an oracle by itself. If no trustworthy oracle exists, route discovery or strategy as an activity and keep a new WO `draft`; do not advance it to `ready` or `active`. After execution has begun, missing proof is represented only by a normalized `partial` or `blocked` status, as appropriate.

## Conditional Proof Blocks

Add a block only when its trigger applies. `release_wo` usually activates several blocks, but still omits irrelevant boilerplate.

| Optional block | Required when |
| --- | --- |
| MREP | a trustworthy end-to-end path exists and local correctness can diverge |
| Risk proof | runtime, persistence, security, payment, release, generated-artifact, or origin risk exists |
| Mechanism adequacy | weak textual proof could falsely close semantic/runtime acceptance |
| Reviewability | an independent reviewer is selected |
| Validation attribution | checks span WO, wave, integration, or pre-existing failures |
| Manual gates | provider, device, signing, store, deploy, account, or origin access is required |
| Promotion evidence | more than a throwaway local edit is intended to land |
| Context/cost harness | reusable prompt, provider route, batch/eval, or prompt-heavy system changes |

### MREP

Record the entry point, expected result, smallest trustworthy end-to-end path, validation, evidence reference, and limitations. If no meaningful path exists, omit the block and explain that limitation in the oracle or handoff.

### Risk Proof

Name the risk, authoritative boundary, positive and negative cases, required evidence scope, and closure owner. Do not substitute implementation steps for proof.

### Mechanism Adequacy

Classify acceptance as semantic, textual, mechanical, artifact-shape, runtime-behavior, or hybrid. State why the proof reaches the authoritative boundary and list blind spots. Text-only proof may close only a text-bounded claim.

### Reviewability

Name expected diff shape, risk lenses, proof boundaries, tricky invariants, required inspection surfaces, and relevant pre-existing debt. This lets the reviewer inspect the result instead of rediscovering the task.

### Validation Attribution

Separate checks owned by this WO from wave integration and pre-existing or unrelated failures. Use the standard evidence `attribution` values for every recorded result.

### Manual Gates

Name the exact gate, owner, candidate, environment or origin, required access, evidence destination, and effect if unavailable. Use the standard manual labels. A skip or attestation is not a pass.

### Promotion Evidence

Record repository lane, working branch/worktree, commit state, intended promotion state, and any integration owner. Do not infer promotion from a local branch name.

### Context/Cost Harness

Define stable-prefix and dynamic-suffix boundaries, redaction, static packet audit, provider-neutral usage telemetry, evaluation contour, and residual cost or latency risk. Follow [context-cost-harnesses.md](context-cost-harnesses.md).

## Evidence Records

Use the structured evidence dimensions from the orchestration standard. One record describes one check at one target scope and freshness. Keep command summaries compact; put durable logs, screenshots, reports, or manifests in their canonical evidence location and link them.

Do not:

- widen a local result to an exact candidate or deployed environment;
- mix current and historical evidence;
- hide WO-owned failures in a wave-level summary;
- copy raw secrets, personal data, provider payloads, or connection material;
- claim a manual gate was executed when it was not.

## Scope And Steering Changes

Update the WO before continuing when steering changes write scope, no-touch scope, lane, authority, acceptance, risk, documentation impact, validation, manual gates, or promotion intent. The orchestrator reruns the collision gate for changed write scope and selects any newly required proof block or role.

## Review And Flow State

Independent reviewers use the normalized verdict, finding, and evidence interface from the standard. Add [FLOW_STATE](flow-state.md) only when review, a fix cycle, blocked or partial state, or durable handoff triggers it. Do not place an empty flow block in every WO.

## Continuity And Handoff

A resumable WO preserves:

- goal and current status;
- exact write and no-touch scope;
- authority anchors and acceptance oracle;
- documentation impact;
- validation and evidence with attribution;
- blockers, accepted risks, and next action;
- lane and promotion state;
- any triggered proof blocks and conditional flow state.

Keep exploration prose, hidden reasoning, duplicate command logs, and unrelated repository history out of the WO.

## Immutability

While active, update the WO as the durable execution contract. After status becomes `complete`, or the WO is superseded and retained as evidence, do not rewrite it to match later product truth.

Use a dated addendum for a factual correction that must preserve the original record. Use a superseding WO for new scope, changed acceptance, or a new decision. Current behavior still belongs in its canonical product, architecture, operations, design, or client owner.
