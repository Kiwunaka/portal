# Scout Discovery - <topic-or-wo-seed>

> Read-only discovery artifact.
> Scout gathers current truth, routing signals, and validation seeds.
> Scout does not implement, widen scope, or declare completion.

## Discovery Snapshot

| Field | Value |
| --- | --- |
| Topic | `<short request title>` |
| Requested by | `<user / orchestrator / wave>` |
| Discovery owner | `<scout role or name>` |
| Status | `draft | in-progress | ready-for-wo | blocked` |
| Candidate WO class | `platform-only | client-only | mixed | unknown` |
| Candidate primary repo lane | `portal/master | PORTALapp/main | unknown` |
| Candidate secondary repo lane | `<blank if not mixed>` |
| Timestamp | `<timestamp>` |

## Request Summary

- Requested outcome: `<what the user or wave seems to want>`
- Why now: `<why this request exists now>`
- Known constraints: `<constraints already stated>`

## Must-Read Pack Reviewed

- [ ] `AGENTS.md`
- [ ] `docs/README.md`
- [ ] `docs/product/portal-vpn-product.md`
- [ ] `docs/architecture/system-overview.md`
- [ ] `docs/architecture/app-first-and-bonus-flows.md`
- [ ] `docs/operations/deployment-and-access.md`
- [ ] `docs/operations/monitoring-and-visibility.md`
- [ ] `docs/developer/developer-guide.md`
- [ ] `docs/developer/repository-map.md`
- [ ] Client docs pack, if candidate scope touches `external/client-fork/app/**`

## Current Truth Summary

### Confirmed current behavior

- `<grounded behavior from code or canonical docs>`
- `<grounded behavior from code or canonical docs>`

### Source-of-truth anchors

- `<shared file, canonical doc, or runtime authority>`
- `<shared file, canonical doc, or runtime authority>`

### Conflicts or stale material noticed

- `<old flat doc, archive, or implementation mismatch>`
- `<unknown or leave blank>`

## Repo Boundary And Write-Scope Candidate

| Question | Answer |
| --- | --- |
| Which files or directories look in scope | `<paths>` |
| Which repo lane owns those paths | `<platform / client / mixed>` |
| Why this is not another lane | `<reason>` |
| Does `shared/*` make this mixed | `yes | no | maybe` |
| Confidence in classification | `high | medium | low` |

## Current Code Anchors (Must Read)

Copy only the anchors that should later appear in the WO.

| Path | Why it matters | Read status | Notes |
| --- | --- | --- | --- |
| `<exact path>` | `<why it is central to the work>` | `done` | `<notes>` |
| `<exact path>` | `<why it is central to the work>` | `done` | `<notes>` |

## Docs Impact Candidate

| Doc path | Why it may need an update | Likely required |
| --- | --- | --- |
| `docs/product/portal-vpn-product.md` | `<reason>` | `yes | no | maybe` |
| `docs/architecture/system-overview.md` | `<reason>` | `yes | no | maybe` |
| `docs/architecture/app-first-and-bonus-flows.md` | `<reason>` | `yes | no | maybe` |
| `docs/operations/deployment-and-access.md` | `<reason>` | `yes | no | maybe` |
| `docs/operations/monitoring-and-visibility.md` | `<reason>` | `yes | no | maybe` |
| `docs/developer/developer-guide.md` | `<reason>` | `yes | no | maybe` |
| `docs/developer/repository-map.md` | `<reason>` | `yes | no | maybe` |
| `docs/user/portal-vpn-user-guide-ru.md` | `<reason>` | `yes | no | maybe` |
| `external/client-fork/app/docs/...` | `<reason>` | `yes | no | maybe` |

## Observed Gaps, Risks, Or Reasons For Work

- `<bug, missing contract, unclear behavior, or release risk>`
- `<user pain, operator pain, or truth mismatch>`
- `<what could regress if this is handled loosely>`

## Constraints And Invariants

- `<non-negotiable from AGENTS.md or canonical docs>`
- `<never-touch, source-of-truth, hostname, node-pool, or release rule>`
- `<repo boundary or documentation landing rule>`

## Validation Seeds

List only the checks that are likely needed if this becomes a WO.

| Surface | Candidate check | Why it matters |
| --- | --- | --- |
| `backend` | `<pytest or lifecycle smoke>` | `<reason>` |
| `webapp` | `<build, admin smoke, Playwright>` | `<reason>` |
| `marketing` | `<build, links, visual smoke>` | `<reason>` |
| `infra` | `<node readiness, metrics freshness, origin matrix>` | `<reason>` |
| `client` | `<client security smoke, release gate suite, localhost audit>` | `<reason>` |
| `release` | `<release_gate_check.py or release_orchestrator.py --gates-only>` | `<reason>` |

## Recommended WO Seed

### Goal seed

`<one-sentence candidate goal>`

### Why-this-exists seed

`<one paragraph that can feed directly into the WO>`

### Non-goals seed

- `<explicitly not part of this WO>`
- `<explicitly not part of this WO>`

### Write-scope seed

- Allowed write paths: `<paths>`
- Explicitly out of scope: `<paths>`

### Acceptance seeds

- `<candidate acceptance criterion>`
- `<candidate acceptance criterion>`

## Questions That Still Need Strategy

- `<question that blocks a clean WO>`
- `<question that affects design or repo classification>`

## Recommended Next Step

- `create WO directly`
- `write implementation strategy first`
- `split into multiple WOs`
- `stop because the request is outside current truth or scope`

## Handoff To Orchestrator

- Suggested WO title: `<WO-xxx title seed>`
- Suggested WO class: `<platform-only | client-only | mixed>`
- Suggested first executor lane: `<platform / client>`
- Suggested reviewer focus: `<spec, quality, release>`
