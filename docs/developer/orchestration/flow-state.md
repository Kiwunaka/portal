# POKROV FLOW_STATE

Last updated: 2026-07-11

`FLOW_STATE` is a conditional, compact routing ledger for review loops and durable handoffs. It is not a transcript, completion report, or default WO section.

## Contract

| Contract | Value |
| --- | --- |
| Schema | `2` |
| Applicability | `conditional` |
| Same-class stop threshold | `3` |

Conditional triggers: review | fix_cycle | blocked | partial | durable_handoff

Do not create `FLOW_STATE` for direct work or a WO that has none of these triggers. Create it when the first trigger fires, update it after each relevant routing event, and remove nothing needed by the next owner.

## Vocabulary

Allowed states: review | fix_cycle | redesign_required | blocked | partial | complete

Allowed next actions: execute | owned_finding_recheck | fresh_final_review | release_validation | problem_class_analysis | wait_for_access | close

Finding status: open | fixed | accepted_risk | blocked

## Schema

Use one object in the active WO or durable handoff:

```json
{
  "version": 2,
  "wo_id": "WO-XXX",
  "state": "review",
  "cycle": 1,
  "open_findings": [
    {
      "id": "Q1",
      "owner": "spec",
      "issue_class": "docs_impact_missing",
      "status": "open",
      "mechanism_changed": false,
      "evidence_ref": "review-verdict.md#Q1"
    }
  ],
  "same_class_without_mechanism_change": {
    "docs_impact_missing": 1
  },
  "next_action": "owned_finding_recheck",
  "stop_reason": null
}
```

`cycle` increments when findings return for another executor pass. `open_findings` keeps findings needed for routing; remove a resolved item from that list only after its status and evidence remain preserved in the review record. `evidence_ref` points to the owned review or retained proof.

## Update Rules

After each review or fix pass:

1. record every finding with a stable `issue_class` and explicit owner;
2. set the finding status and evidence reference;
3. record whether the fix changed the mechanism that caused the class;
4. update the same-class counter;
5. select one allowed state and one allowed next action;
6. record a stop reason when ordinary routing cannot continue.

The filing reviewer performs `owned_finding_recheck` only for their findings. Use `fresh_final_review` for an independent final pass when selected by the WO. Use `release_validation` only for the exact candidate and triggered release gates.

## Same-Class Stop Mechanism

The counter measures repeated findings in one issue class without a mechanism change.

- First occurrence: set the class counter to `1`.
- Second occurrence without a mechanism change: set it to `2` and require the next pass to address the class mechanism.
- Third occurrence without a mechanism change: stop ordinary fix routing, set state to `redesign_required`, set next action to `problem_class_analysis`, and record `stop_reason`.
- A proven mechanism change starts a new count for later occurrences of that class; retain the prior review evidence.

Do not bypass the threshold by renaming an equivalent issue class, switching executors, or closing and reopening the finding.

## Problem-Class Analysis

Before another executor pass, record:

- the repeated issue class and affected surfaces;
- why local fixes did not close it;
- the mechanism change needed;
- revised acceptance and validation;
- whether scope, lane, docs impact, or manual gates changed;
- whether to split, rescope, accept a bounded risk, wait for access, or ask the user.

Execution resumes only after the contract and collision gate reflect any scope change. If no safe mechanism or required authority exists, use `blocked` with `wait_for_access`, or preserve a truthful `partial` outcome.

## Completion

Use `complete` with `close` only when no finding remains open or blocked, accepted risks are explicit, required evidence exists, and no stop reason still requires action. Keep the final state as durable evidence; completed WOs are not rewritten into product canon.
