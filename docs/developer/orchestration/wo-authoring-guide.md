# POKROV WO Authoring Guide

Last updated: 2026-05-16

## Document Status

This file is the authoring guide for `POKROV` work orders.

Use it together with:

- [orchestration-standard.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/orchestration-standard.md)
- [flow-state.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/flow-state.md)
- [WO.template.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/templates/WO.template.md)

The standard defines lifecycle and routing. This guide defines how to write a WO that an executor, reviewer, and validator can actually close without relying on chat memory.

## Wave Layout

Live wave folders stay under:

```text
docs/developer/work-orders/<YYYY-MM-DD--slug>/INDEX.md
docs/developer/work-orders/<YYYY-MM-DD--slug>/WO-001-<slug>.md
```

Use exactly one active `INDEX.md` per wave. If an external review packet needs a unique filename, create that as an export artifact, not as a competing active index.

Wave folder names use:

- `YYYY-MM-DD--kebab-case-slug`
- exactly two hyphens between date and slug
- date first, slug second

## Ceremony Levels

Use a compact WO for low-risk, singleton, docs-only, mechanical, or narrow localized work where local correctness cannot differ from final system correctness.

Use a full WO for medium or high-risk work, batch execution, shared contracts, generated artifacts, validation harnesses, runtime behavior, persistence, security, data integrity, API/UI hierarchy, release evidence, or origin-specific proof.

A compact WO may omit detailed proof blocks only when it explicitly records:

- low risk mode and reason
- validation scope
- MREP status or N/A reason
- hard no-touch scope
- acceptance criteria

## Durable Thread Memory

A WO is the durable memory of the workstream, not a transcript.

Anything that must survive thread compaction, remote steering, role handoff, or delayed review belongs in a file:

- the WO for scope, proof, status, and findings
- the wave `INDEX.md` for routing and ordering
- completion evidence for closure state
- retained artifacts for screenshots, reports, generated files, or runtime proof

If a later steering message changes scope, risk, validation, manual checks, repo lane, or acceptance, update the WO before continuing. Do not leave the new contract only in chat.

## Goal And Oracle

A strong WO goal needs a verification oracle.

Bad shape:

- implement the plan in this Markdown file

Better shape:

- implement the behavior, and prove it with the named tests, artifact inspection, runtime smoke, manual gate, or release report that decides correctness

For medium/high-risk work, the oracle normally lives in:

- `Minimal E2E Path (MREP)`
- `Risk Proof Plan`
- `Mechanism Adequacy`
- `Validation Attribution`

If no trustworthy oracle exists yet, the WO should be discovery, strategy, partial, or blocked instead of pretending implementation can close it.

## Inspection Surface

When the result is visual, generated, interactive, or operational, name where the reviewer should inspect it.

Examples:

- local browser target
- static `index.html`
- rendered screenshot or PDF
- generated manifest or bundle
- release-gate markdown report
- admin/cabinet/browser page
- device/runtime smoke output

The inspection surface should be diffable, reviewable, or reproducible whenever possible. A screenshot without source, command, or environment context is weak evidence.

## Long-Running Feedback Loops

If a WO depends on later feedback, PR comments, deploy completion, provider access, device availability, or external-origin evidence, record:

- cadence or next check
- owner
- stop condition
- artifact or thread to update
- what should happen when feedback arrives

Use a heartbeat or automation when the current thread should wake up later and continue the loop. Do not model a recurring monitor as a one-time manual reminder unless the user explicitly wants that.

## Evidence Source Tiers

Use these tier labels when recording checks:

| Tier | Meaning |
| --- | --- |
| `static_review` | Source, config, docs, or diff inspection only. |
| `synthetic_test` | Unit or generated test built for this WO. |
| `tracked_fixture` | A fixture, snapshot, sample, or corpus retained in the repo or evidence folder. |
| `generated_artifact` | A built/exported artifact, report, screenshot, bundle, manifest, or derived file. |
| `api_e2e` | End-to-end API flow through real route boundaries or smoke harness. |
| `ui_behavior` | Browser, client, or interactive UI behavior check. |
| `runtime_smoke` | Runtime service, local server, device, deployed host, or process-level smoke. |
| `full_validation_epoch` | Whole gate pack or full release-style validation contour. |
| `manual` | Human/operator/device/provider confirmation. |
| `n/a` | Not applicable, with a short reason. |

Do not let a broad acceptance criterion close on a weaker tier unless the WO narrows the criterion and records the residual risk.

## Minimal E2E Path

Every medium/high-risk WO should state the minimal end-to-end path that proves the intended result at the smallest trustworthy boundary.

Required fields:

- `Entry point`
- `Expected`
- `Validation`
- `Evidence source tier`
- `Notes`

If there is no meaningful MREP, write `n/a` and explain why. Do not leave the section blank.

## Risk Proof Plan

Set `Required: yes` when local correctness can differ from final system correctness.

Common triggers:

- validation harnesses or release gates
- generated artifacts or static exports
- shared contracts across platform and client lanes
- runtime, persistence, payments, security, or data integrity
- UI hierarchy where screenshot/build output can differ from source intent
- origin-specific evidence such as `current-origin`, `brain-origin`, or `RU-origin`
- manual/provider/device evidence required for closure

For low-risk docs, mechanical renames, formatting, or isolated read-only discovery, set `Required: no` with a short reason.

When required, define:

- risk reason
- authoritative boundary
- closure cases
- negative controls
- evidence source tiers required
- full validation owner

The plan should define proof boundaries, not implementation steps.

## Mechanism Adequacy

Set `Required: yes` when the WO is proof-heavy: guard, validator, analyzer, static policy, generated artifact, validation harness, release gate, or any semantic acceptance that can be falsely closed by one example.

When required, state:

- acceptance kind: `semantic`, `textual`, `mechanical`, `artifact-shape`, `runtime-behavior`, or `hybrid`
- proposed proof mechanism
- why the mechanism reaches the authoritative boundary
- known blind spots
- whether regex/text-only proof is allowed

Semantic acceptance such as "X must not affect behavior, routing, ranking, validation, persistence, permissions, or output" cannot be closed by regex/text-only proof unless the WO narrows acceptance to literal text, artifact name, or path scope and records the remaining risk.

## Reviewability

Write the WO so a reviewer knows where to look before they start.

Required fields for full WOs:

- `Expected diff shape`
- `Risk lenses`
- `Proof boundaries`
- `Known tricky invariants`
- `Reviewer must inspect`
- `Pre-existing issues that should be follow-up debt unless they block acceptance`

This prevents generic review passes and keeps reviewer attention on the real risk zones.

## Validation Attribution

Validation must say what belongs to this WO and what belongs to the wider wave.

Required fields for full WOs:

- `Checks owned by this WO`
- `Evidence source tiers required`
- `Failures likely attributable to this WO`
- `Failures that are wave-level/integration`

This keeps two mistakes out of the process:

- treating an unrelated or pre-existing failure as proof the WO is bad
- ignoring an owned failure by calling it "not my test"

## Quality Bar

Each WO must be self-contained enough for executor, reviewer, and validator to work without chat history.

Medium/high-risk WOs need:

- concrete evidence anchors
- target files and symbols
- MREP or explicit N/A
- risk proof plan or explicit N/A
- mechanism adequacy or explicit N/A
- reviewability guidance
- validation attribution
- focused validation

The WO plan is guidance, not a script. Put route, ordering constraints, and known traps in the WO, but leave local implementation mechanics to the executor when current code evidence supports a better route.
