# <YYYY-MM-DD--wave-name> Wave Index

> Orchestrator-owned file.
> Use this index for routing, WO order, phase control, and wave closure.
> Keep implementation detail, validation detail, reviewer detail, and git evidence inside the individual WO files.

## Wave Snapshot

| Field | Value |
| --- | --- |
| Wave id | `<YYYY-MM-DD--wave-name>` |
| Wave objective | `<one-sentence outcome for the whole wave>` |
| Status | `draft | ready | active | blocked | partial | closed` |
| Orchestrator | `<role name / chat / owner>` |
| Execution model | `phase-first | dependency-first | mixed` |
| Canonical repo lanes in scope | `portal/master` / `POKROV-app/main` / `<archive evidence only if needed>` |
| Primary scope roots | `<paths>` |
| Start gate | `<what must be true before launch>` |
| Closure gate | `<what must be true before the wave can close>` |
| Last updated | `<timestamp>` |

## Read Gate

- [ ] Reviewed the mandatory root read order from `AGENTS.md`.
- [ ] Added the `POKROV-app` docs pack for active client scope.
- [ ] Added the archive client-lane summaries only when historical bootstrap or rollback evidence matters.
- [ ] Confirmed canonical write lanes before launching any executor.
- [ ] Confirmed doc-impact expectations for every WO in this wave.
- [ ] Confirmed no WO requires printing or committing material from never-touch zones.

## Orchestrator Responsibilities

- Keep this file as the single routing and ordering truth for the wave.
- Decide WO class from write scope and canonical repo lane, not from the topic name.
- Launch at most one executor per active write scope.
- Require fresh spec review and fresh quality review before marking a WO complete.
- Require separate platform and client git evidence before closing any mixed WO.
- Write the final closure summary instead of letting executors declare the wave done.

## Status Keys

### Wave status

| Value | Meaning |
| --- | --- |
| `draft` | Wave exists but WO order or scope is still changing. |
| `ready` | WO list and launch order are stable enough to execute. |
| `active` | At least one WO is executing or under review. |
| `blocked` | Wave cannot continue until an external blocker is resolved. |
| `partial` | Some WOs are complete, but the wave cannot close cleanly yet. |
| `closed` | Closure summary is written and all remaining work is intentionally handed off. |

### WO status

| Value | Meaning |
| --- | --- |
| `draft` | WO shell exists but is not ready for execution. |
| `ready` | WO has enough context for an executor to start. |
| `executing` | One executor is actively working this WO. |
| `spec-review` | Fresh spec reviewer is checking contract compliance. |
| `quality-review` | Fresh quality reviewer is checking implementation quality. |
| `fix-cycle` | Executor is addressing reviewer findings. |
| `blocked` | WO cannot move without external input, infra, or evidence. |
| `partial` | WO delivered a valid partial outcome with explicit remaining scope. |
| `complete` | WO met acceptance and closure criteria. |

## Phase Plan

| Phase | Goal | Ordered WOs | Entry gate | Exit gate | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `Phase 1` | `<truth, grounding, or prerequisite outcome>` | `<WO-001, WO-002>` | `<what must be true to start>` | `<what must be true to exit>` | `draft` | `<notes>` |
| `Phase 2` | `<next outcome>` | `<WO-003>` | `<gate>` | `<gate>` | `draft` | `<notes>` |
| `Phase 3` | `<next outcome>` | `<WO-004>` | `<gate>` | `<gate>` | `draft` | `<notes>` |

## Ordered WO Queue

| Order | WO id | Title | WO class | Primary write scope | Depends on | Parallel group | Active role | Status | Closure note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `1` | `WO-001` | `<title>` | `platform-only` | `<paths>` | `-` | `A` | `orchestrator` | `ready` | `<leave blank until closed>` |
| `2` | `WO-002` | `<title>` | `client-only` | `<paths>` | `WO-001` | `A` | `orchestrator` | `draft` | `<leave blank until closed>` |
| `3` | `WO-003` | `<title>` | `mixed` | `<paths>` | `WO-001, WO-002` | `B` | `orchestrator` | `draft` | `<leave blank until closed>` |

Parallel-group note:
- WOs in different groups may be explored or reviewed in parallel.
- Do not run more than one executor inside the same write scope at the same time.
- Mixed WOs require separate git evidence for platform and client lanes before closure.

## Dependency And Routing Notes

- `platform-only`: changes live only under root platform paths and land on `portal/master`.
- `client-only`: changes live only under one client lane; default to `POKROV-app/main`, and call out archive evidence separately when retired bridge lineage matters.
- `mixed`: one logical WO with multiple write lanes, separate git-evidence lanes, and one closure decision by the orchestrator.
- If a WO changes `shared/*`, confirm whether the work stays platform-only or becomes mixed because client sync or adoption is required.

## Launch Notes

### Current launch decision

- `<which WO launches next and why>`
- `<what evidence or dependency was checked before launch>`
- `<what is intentionally deferred to a later phase>`

### Active blockers

- `<blocker>`
- `<owner>`
- `<next check>`

## Wave Closure Summary

### Completed WOs

- `<WO id>: <one-line outcome>`

### Partial Or Blocked WOs

- `<WO id>: <what shipped, what remains, why it stopped>`

### Docs And Contract Updates

- `<canonical doc updated or intentionally unchanged>`

### Validation Summary

- `<top-line gate, smoke, or manual evidence for the wave>`

### Git Evidence Summary

| Repo lane | Canonical branch | Final commit(s) | Pushed | Notes |
| --- | --- | --- | --- | --- |
| `platform` | `portal/master` | `<sha(s)>` | `yes | no` | `<notes>` |
| `client-dev` | `POKROV-app/main` | `<sha(s)>` | `yes | no` | `<notes>` |
| `archive-evidence` | `<n/a if unused>` | `<artifact version or summary>` | `n/a` | `<notes>` |

### Remaining Risk / Next Wave Seed

- `<risk or unfinished work>`
- `<recommended next WO or next wave>`
