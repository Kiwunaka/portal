# POKROV Work Orders

Last updated: 2026-07-14

This directory stores durable execution state and retained execution evidence. It is not a product, architecture, operations, design, release, or active-client source of truth.

## Classification

- Active WOs and their active wave index are `ACTIVE_EXECUTION`.
- Completed or superseded WOs, closed indexes, reviews, and completion records are `EVIDENCE`.

The classification controls retrieval: active artifacts may route current execution; evidence may explain what happened. Neither silently overrides canonical owners, current code/tests, or exact runtime evidence.

## Naming And Layout

For wave directories created after `2026-07-11`, use:

```text
docs/developer/work-orders/YYYY-MM-DD--wave-name/
```

This naming rule is forward-only. Every wave path already present at the cutoff is grandfathered, including `2026-07-09-growth-megapass` and other legacy single-dash names. Do not rename active or evidence directories to enforce the new format; their existing paths and links remain authoritative identifiers for those records.

Inside it, use:

```text
INDEX.md
WO-001-short-title.md
WO-002-short-title.md
```

Exactly one active `INDEX.md` exists per wave. It routes the queue, dependencies, current state, blockers, and next action. Export packets and audit reports use distinct filenames and cannot become a competing active index.

## Storage Rules

- Keep one bounded outcome per WO.
- Link canonical owners and durable evidence; do not copy their full contents.
- Keep raw logs, screenshots, manifests, and release proof in the canonical artifact/evidence location and reference them.
- Keep platform and active-client lane evidence distinguishable when a wave spans repositories.
- Preserve completed and superseded material; relabel unclear history instead of deleting it during routine cleanup.
- Keep templates under [orchestration/templates](../orchestration/templates/), not in a live wave.

## Evidence Boundary

Completed evidence is not rewritten into product canon. If a completed WO contains a decision that should remain current, reconcile that decision through the canonical owner and link back to the WO as provenance.

Completed or superseded WOs are immutable. Use a dated addendum for a factual correction that preserves the original record. Use a superseding WO for new scope, changed acceptance, or a new decision.

## Retained Audit Work Order

The completed repository feature/story audit remains available through
[2026-06-27--repo-feature-story-audit/INDEX.md](2026-06-27--repo-feature-story-audit/INDEX.md),
with its current output summary and completion evidence retained in that wave.

## Continuity Contract

A new orchestrator must be able to resume active work from the wave folder without chat history. Preserve:

- goal and status;
- exact write and no-touch scope;
- authority anchors and acceptance oracle;
- validation and structured evidence;
- blockers, accepted risks, and next action;
- documentation impact;
- lane and promotion state;
- triggered proof blocks and conditional `FLOW_STATE` when applicable.

Do not preserve hidden reasoning, duplicate command logs, irrelevant exploration, secrets, private data, or raw provider payloads.

## Closure

When a WO closes, update the wave index classification and next action. Keep remaining manual or access-dependent gates explicit. A useful bounded result may be `partial`; missing authority or proof may be `blocked`. Do not relabel either as complete to make the wave look finished.
