# Scout Discovery

This is a read only discovery artifact. It records targeted anchors, conflicts, scope, docs impact, and validation seeds.

Request or WO: `<identifier>`
Scout: `<owner>`
Date: `<timestamp>`

## Request Summary

- Requested outcome: `<outcome>`
- Known constraints: `<constraints>`
- Candidate ceremony: `direct | bounded_wo | release_wo`
- Candidate repository lane: `platform | active_client | mixed | unknown`

## Assigned Context

| Anchor | What it establishes | Freshness or authority |
| --- | --- | --- |
| `<selected task-router row>` | `<routing and docs impact>` | `<current>` |
| `<subsystem owner>` | `<intended behavior>` | `<classification>` |
| `<code, test, or runtime evidence>` | `<implemented or observed state>` | `<freshness>` |

Do not list a repository-wide document pack. Add only anchors used by this discovery.

## Conflicts And Unknowns

| Item | Evidence | Consequence | Needs owner decision |
| --- | --- | --- | --- |
| `<conflict or unknown>` | `<reference>` | `<scope, oracle, or risk effect>` | `<yes or no>` |

Distinguish current-owner conflicts from archived or historical explanation.

## Scope Candidate

- Write scope: `<exact paths>`
- No-touch scope: `<exact paths, lanes, data, or concurrent owners>`
- Collision seams: `<worktrees or paths to check>`
- Lane rationale: `<why this lane owns the writes>`

## Docs Impact

| Canonical owner | Expected impact | Reason |
| --- | --- | --- |
| `<exact path>` | `<change, no change, or unknown>` | `<reason>` |

## Validation Seeds

| Candidate check | Target scope | Oracle reached | Limitation or manual gate |
| --- | --- | --- | --- |
| `<focused check>` | `<scope>` | `<yes, no, or partial>` | `<limitation>` |

## Risks

- `<risk and authoritative boundary>`
- `<access, release, data, security, or integration risk>`

## Recommendation

- Next step: `<execute, request optional strategy, split, ask owner, or stop>`
- Proposed acceptance oracle: `<observation>`
- Required proof blocks or reviewers: `<only those triggered>`
- Blocking context: `<none or exact missing decision/evidence>`

The orchestrator owns ceremony, role routing, status, and closure.
