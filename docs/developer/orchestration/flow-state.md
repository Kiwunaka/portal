# POKROV Flow State

Last updated: 2026-05-23

## Document Status

This file is living source of truth for compact orchestration state, fix-cycle stop rules, and reviewer handoff semantics.

## Purpose

`FLOW_STATE` keeps a work order from drifting into endless same-executor fix loops.

It is not a chat summary and not completion evidence. It is a compact process ledger that records only the facts needed to decide the next safe orchestration action.

Use it when a `WO` enters review, fix-cycle, release validation, or any long-running handoff that may survive context compaction.

## Core Rule

Repeated adjacent findings of the same class are a signal that the mechanism is not closed.

If the same issue class appears for the third time without a mechanism change, the orchestrator must stop ordinary fix routing and require a problem-class analysis before the executor continues.

This avoids cycles where each pass fixes one local case while the same underlying problem keeps reappearing elsewhere.

## Required State

Each active `WO` should keep a compact `FLOW_STATE` block in the work-order file once review starts.

Minimum fields:

```json
{
  "version": 1,
  "wo_id": "WO-XXX",
  "state": "draft | executing | review | fix-cycle | redesign-required | blocked | complete",
  "ordinary_fix_cycles": 0,
  "same_class_without_mechanism_change": {},
  "findings": [],
  "next_action": "continue | owned-finding-recheck | fresh-final-review | problem-class-analysis | pause-for-human | close",
  "stop_reason": null
}
```

Finding shape:

```json
{
  "id": "Q1",
  "source": "spec-reviewer | quality-reviewer | release-validator",
  "cycle": 1,
  "issue_class": "docs-impact-missing",
  "surface": "docs/developer",
  "summary": "The WO template does not capture docs-impact closure.",
  "status": "open | fixed | accepted-risk | blocked",
  "mechanism_changed": false,
  "evidence": "path or command summary"
}
```

## Issue Classes

Use a stable issue class when a reviewer files a finding. Add a new class only when none of these fit.

Recommended classes:

- `acceptance-gap`
- `docs-impact-missing`
- `release-claim-drift`
- `copy-policy-drift`
- `source-of-truth-conflict`
- `validation-gap`
- `validation-attribution-gap`
- `proof-boundary-gap`
- `mechanism-adequacy-gap`
- `reviewability-gap`
- `context-cost-harness-gap`
- `prompt-cache-regression`
- `scope-creep`
- `stale-evidence`
- `wrong-lane-routing`
- `permission-or-secret-risk`
- `test-brittleness`
- `implementation-quality`
- `review-process-gap`

## Review Loop Semantics

Use two review modes:

- `owned-finding recheck`
  The same reviewer checks only the findings they previously filed. They should not broaden the review unless the fix clearly created new risk in the same touched area.
- `fresh-final review`
  A new fresh-context reviewer checks the final state after owned findings are closed.

Default sequence:

1. executor completes the WO pass
2. spec reviewer checks contract compliance
3. executor fixes exact spec findings if needed
4. the same spec reviewer rechecks only owned findings
5. quality reviewer checks implementation quality after spec findings are closed
6. executor fixes exact quality findings if needed
7. the same quality reviewer rechecks only owned findings
8. a fresh-final reviewer checks the final state when the WO is non-trivial or risk-sensitive
9. release validator runs when release-sensitive evidence is part of the WO

## Stop Rules

Stop ordinary same-executor fix routing when any condition is true:

- `ordinary_fix_cycles >= 3` and unresolved findings remain
- the same `issue_class` appears for the third time with `mechanism_changed=false`
- a fix changes the WO write scope, repo lane, docs impact, release risk, or manual-check requirements
- a reviewer finds a source-of-truth conflict that cannot be resolved inside the current WO
- validation keeps failing for the same reason after two focused fix attempts
- required external access, device access, deploy access, or origin evidence is unavailable

When a stop rule fires, set:

```json
{
  "state": "redesign-required",
  "next_action": "problem-class-analysis",
  "stop_reason": "same_issue_class_without_mechanism_change"
}
```

## Problem-Class Analysis

Before another executor pass, the orchestrator must record a short analysis in the WO:

- repeated issue class
- affected surfaces
- why local fixes are not closing the class
- mechanism that should close the class
- acceptance criteria that must change
- validator, test, lint, docs rule, or workflow guardrail to add
- whether the WO should be split, rescoped, or escalated to the user

After the analysis, the orchestrator may route a new executor pass only if the pass changes the mechanism or explicitly narrows the WO to a valid partial outcome.

## Compaction And Handoff

`FLOW_STATE` must survive context compaction and role handoff.

Preserve:

- current `state`
- `ordinary_fix_cycles`
- open findings
- issue-class counts
- whether the last pass changed the mechanism
- next action
- stop reason

Do not preserve:

- long reviewer prose
- duplicate command logs
- stale exploration notes
- hidden reasoning

## Completion Rule

A WO may not be marked `complete` while `FLOW_STATE.next_action` is `problem-class-analysis`, `pause-for-human`, or any open finding remains without an explicit `accepted-risk` note from the orchestrator.
