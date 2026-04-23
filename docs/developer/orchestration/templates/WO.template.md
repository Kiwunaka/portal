# WO-<NNN> - <work-order-title>

> Primary execution contract for one unit of work.
> The orchestrator owns status, routing, and closure.
> Executors, reviewers, and validators append evidence inside this file instead of rewriting the work order from scratch.

## WO Snapshot

| Field | Value |
| --- | --- |
| WO id | `WO-<NNN>` |
| Title | `<short outcome title>` |
| Status | `draft | ready | executing | spec-review | quality-review | fix-cycle | blocked | partial | complete` |
| Draft confidence | `grounded | candidate | unknown` |
| Priority | `P0 | P1 | P2 | P3` |
| WO class | `platform-only | client-only | mixed` |
| Primary repo lane | `portal/master | POKROV-app/main | archive evidence only` |
| Secondary repo lane | `<blank if not mixed>` |
| Primary write roots | `<paths>` |
| Secondary write roots | `<blank if not mixed>` |
| Dependencies | `<WO ids or external blockers>` |
| Orchestrator | `<role / chat / owner>` |
| Active executor | `<name or blank>` |
| Spec reviewer | `<name or blank>` |
| Quality reviewer | `<name or blank>` |
| Release validator | `<name or blank>` |
| Created | `<timestamp>` |
| Last updated | `<timestamp>` |

## Drafting Rule

This file may be created directly from a user request.

When that happens:

- fields grounded by the request and current repo truth may be filled immediately
- fields that still depend on discovery, review, runtime evidence, or manual checks should be marked `candidate`, `unknown`, `needs discovery`, or `blocked by evidence`
- draft assumptions must not be presented as final closure facts

## Goal

`<one sentence describing the exact result this WO should achieve>`

## Why This WO Exists

`<why the work matters now, which problem or risk it removes, and what larger wave goal it unlocks>`

## Partial-Success Submission Strand

Use this section when the WO can produce a valid smaller outcome without claiming full completion.

- Minimum acceptable partial outcome: `<what can legitimately ship or hand off>`
- What must still be true before that partial outcome is accepted: `<guardrails>`
- What still remains after a partial outcome: `<explicit remaining scope>`
- What must never be claimed in a partial outcome: `<false-completion statements to avoid>`

## Non-Goals

- `<explicitly out-of-scope item>`
- `<another out-of-scope item>`

## Current Code Anchors (Must Read)

Read these before touching code or docs. Delete rows that do not apply and add the exact files that do.

| Path | Why it matters | Read status | Notes |
| --- | --- | --- | --- |
| `AGENTS.md` | `global repo contract, must-read order, docs impact, cleanup and never-touch rules` | `not started` | `` |
| `docs/developer/developer-guide.md` | `developer workflow, validation commands, canonical branch rules` | `not started` | `` |
| `docs/developer/repository-map.md` | `repo layout, test matrix, script inventory` | `not started` | `` |
| `<exact file path>` | `<why this file is central to the WO>` | `not started` | `` |
| `<exact file path>` | `<why this file is central to the WO>` | `not started` | `` |

## Docs Impact

Update the canonical docs in the same task when behavior or contracts change.

| Doc path | Why impacted | Update required | Status |
| --- | --- | --- | --- |
| `docs/product/portal-vpn-product.md` | `<only if product-facing rules change>` | `yes | no` | `pending` |
| `docs/architecture/system-overview.md` | `<only if runtime responsibilities change>` | `yes | no` | `pending` |
| `docs/architecture/app-first-and-bonus-flows.md` | `<only if app-first / username / node-pool / bonus flow changes>` | `yes | no` | `pending` |
| `docs/operations/deployment-and-access.md` | `<only if deploy or release flow changes>` | `yes | no` | `pending` |
| `docs/operations/monitoring-and-visibility.md` | `<only if hostnames, metrics, alerts, or probes change>` | `yes | no` | `pending` |
| `docs/developer/developer-guide.md` | `<only if workflow or validation commands change>` | `yes | no` | `pending` |
| `docs/developer/repository-map.md` | `<only if repo map or script inventory changes>` | `yes | no` | `pending` |
| `docs/user/portal-vpn-user-guide-ru.md` | `<only if user-facing onboarding/support/trial behavior changes>` | `yes | no` | `pending` |
| `C:/Users/kiwun/Documents/ai/POKROV-app/docs/...` | `<only if new client contract or UX changes>` | `yes | no` | `pending` |
| `docs/archive/client-lanes/...` | `<only if archive summaries or retained evidence notes themselves change>` | `yes | no` | `pending` |

## Write Scope

### Allowed write paths

- `<exact directory or file>`
- `<exact directory or file>`

### Allowed supporting additions

- `<small helper code, test, or doc additions allowed inside write scope>`
- `<regen or sync output allowed if the WO explicitly requires it>`

### Explicitly out of scope

- `<paths or subsystems that must not be edited>`
- `<secrets, never-touch zones, or unrelated repos>`

## WO Class And Routing Decision

- WO class: `platform-only | client-only | mixed`
- Classification reason: `<why this is the correct lane decision>`
- Canonical landing rule:
- `platform-only` lands on `portal/master`
- `client-only` lands on `POKROV-app/main` by default
- historical bootstrap or bridge archive notes may inform the WO, but they do not define the landing lane
- `mixed` requires separate platform and new-client git evidence before closure when each lane is touched

## Execution Freedom

This section tells the executor how much freedom exists inside the WO.

### Freedom allowed

- `<small refactors, helper methods, or tests inside scope are allowed if they directly support acceptance criteria>`
- `<updating exact canonical docs listed above is allowed when the contract truly changed>`
- `<adding missing glue code is allowed when it stays inside the write scope and preserves current product truth>`

### Freedom not allowed

- `<do not invent new product behavior, routes, CTA flows, or release promises>`
- `<do not widen the write scope without the orchestrator updating this WO first>`
- `<do not treat local temp state, archives, or execution layers as source of truth>`
- `<do not collapse platform and client git evidence into one lane>`

## Required Design

Describe the intended implementation shape before work starts. Keep this section concrete enough that reviewers can tell whether the executor stayed on-contract.

### Design summary

`<how the solution should be shaped at a high level>`

### Must preserve

- `<existing behavior or contract that cannot regress>`
- `<compatibility seam or fallback that must remain intact>`

### Required changes

- `<specific behavior, file area, or data flow that must change>`
- `<specific docs or evidence change that must happen>`

### Mixed-lane coordination

- `<leave blank if not mixed>`
- `<if mixed, say what must land in platform first and what must then be aligned in client>`

### Rollback / compatibility seam

- `<how to stop safely if the WO only lands partially>`

## Acceptance Criteria

- [ ] `<user-visible or operator-visible outcome>`
- [ ] `<code or contract outcome>`
- [ ] `<docs outcome>`
- [ ] `<validation outcome>`
- [ ] `<git-evidence outcome>`

## Validation

Delete unused subsections instead of leaving a wall of `N/A`.

### Validation Status

- Overall status: `not_run | partial | pass | fail | blocked`
- Summary: `<one-line state of validation>`

### Common Validation Record

| Check type | Command or evidence | Exit code | Result | Scope | Notes |
| --- | --- | --- | --- | --- | --- |
| `focused automated check` | `<exact command>` | `<0 / non-zero / n/a>` | `pass | fail | partial | blocked` | `<touched area>` | `<notes>` |
| `artifact` | `<path to markdown/json/png artifact>` | `n/a` | `pass | fail | partial | blocked` | `<touched area>` | `<notes>` |
| `manual check` | `<manual step name>` | `n/a` | `pass | fail | partial | blocked` | `<environment>` | `<notes>` |

### Backend Validation

Use when the WO touches `portal_bot/`, API flow, worker logic, panel sync, auth, tickets, payments, or retention.

| Field | Record |
| --- | --- |
| Focused backend tests | `<pytest files or commands such as portal_bot/tests/test_app_first_api.py, tests/test_portal_api.py, tests/test_api_auth_and_tickets.py, tests/test_api_payments_callbacks.py, tests/test_worker_retention.py>` |
| API lifecycle smoke | `<python scripts/api_lifecycle_smoke.py or reason not needed>` |
| Contract surfaces checked | `<endpoints, flows, callbacks, or ticket paths actually verified>` |
| Post-deploy backend verify | `<python scripts/verify_brain_ready.py or reason not needed>` |
| Data or migration notes | `<migration, rollback, compatibility seam>` |

### Webapp Validation

Use when the WO touches `webapp/`, operator auth, admin routes, or browser-visible cabinet flows.

| Field | Record |
| --- | --- |
| Webapp build | `<npm.cmd run build in webapp/>` |
| Admin smoke | `<python scripts/admin_webapp_smoke.py or reason not needed>` |
| Playwright scope | `<npm.cmd run test:e2e or npm.cmd run test:e2e:admin>` |
| Mobile or WebView check | `<narrow viewport or Telegram WebView-like check>` |
| API contract dependency | `<backend assumptions and how they were validated>` |

### Marketing Validation

Use when the WO touches `marketing/`, public copy, checkout entry, legal pages, or SEO surfaces.

| Field | Record |
| --- | --- |
| Marketing build | `<npm.cmd run build in marketing/>` |
| Link check report | `<python ..\\scripts\\check-links.py plus artifact path>` |
| UI visual smoke report | `<python ..\\scripts\\ui_visual_smoke.py plus artifact path>` |
| Shared copy truth checked | `<shared/* and copy/catalog.ru.json alignment>` |
| CTA / legal / SEO truth | `<cabinet CTA, checkout CTA, legal links, metadata, sitemap, manifest>` |

### Infra Validation

Use when the WO touches infra, metrics, node readiness, probes, timers, observers, or host-level visibility.

| Field | Record |
| --- | --- |
| Node readiness gate | `<python scripts/predeploy_node_readiness.py or equivalent>` |
| Metrics freshness and alerts | ``/api/admin/metrics/status`` summary, per-node alerts, freshness |
| Collector runtime parity | `<collect_node_metrics.py and node_dataplane_probe.py status>` |
| Origin matrix | `<current-origin check / brain-origin check / RU-origin check>` |
| DNS / TLS / dataplane artifacts | `<artifact paths>` |
| Systemd or timer status | `<services or timers touched>` |

### Client Validation

Use when the WO touches the new client repo, the legacy bridge repo, packaging, runtime client behavior, or client docs that depend on code truth.

| Field | Record |
| --- | --- |
| Client security smoke | `<python scripts/client_security_smoke.py>` |
| Flutter test suite | `<python scripts/run_client_release_gate.py test --suite portal|full>` |
| Client build targets | `<windows / android-apk / android-aab and artifact paths>` |
| Android localhost audit | `<device class, phases, summary from scripts/android_localhost_audit.py>` |
| Routing and DNS leak validation | `<Global / All except RU / DNS split or leak checks>` |
| Release handoff alignment | `<APP_* URLs, artifact names, public/operator split>` |

### Release Validation

Use when this WO affects release readiness, release evidence, deploy flow, or post-deploy verification.

| Field | Record |
| --- | --- |
| Gate pack command | `<python scripts/release_gate_check.py ... or python scripts/release_orchestrator.py --gates-only ...>` |
| Gate pack report | `<docs/audit-artifacts/release_gate_report.md summary>` |
| Release handoff sync | `<remote_brain_apply_release_handoff.py status or reason not needed>` |
| Deploy steps | `<backend deploy / static deploy / observer or timer ensure>` |
| Post-deploy verify | `<verify_brain_ready.py, checkout continuation, API health, canonical host verify>` |
| Release blockers | `<physical Android audit, RU-origin proof, unsigned artifact, unsynced URLs, other blockers>` |
| Rollback-safe state | `<what is live, what is not, how to stop safely>` |

## Manual Checks

Use this table for checks that depend on operator judgment, runtime state, device state, or origin-specific evidence.

| Check | Environment / device / origin | Result | Owner | Timestamp | Notes |
| --- | --- | --- | --- | --- | --- |
| `<manual check name>` | `<desktop / physical Android / current-origin / brain-origin / RU-origin>` | `pass | fail | partial | blocked` | `<name>` | `<timestamp>` | `<notes>` |
| `<manual check name>` | `<environment>` | `pass | fail | partial | blocked` | `<name>` | `<timestamp>` | `<notes>` |

## Completion

### Closure Decision

- Completion state: `not ready | partial | complete | blocked`
- Closure summary: `<one short paragraph explaining what is now true>`

### Done Definition For This WO

- `<what must be true to call the WO complete>`
- `<what documentation or evidence must exist>`
- `<what must still remain false if the WO is only partial>`

### What Changed

- `<code, docs, config, or artifacts changed>`
- `<important supporting work added inside scope>`

### What Remains

- `<anything intentionally deferred>`
- `<anything blocked externally>`

## Git Evidence

Record the exact repo lanes touched by this WO. For mixed WOs, fill both lanes and do not close the WO on one lane alone.

| Repo lane | Canonical branch | Working branch | Commit(s) | Pushed | PR / compare | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `platform` | `portal/master` | `<branch>` | `<sha(s)>` | `yes | no` | `<url or blank>` | `<notes>` |
| `client-dev` | `POKROV-app/main` | `<branch>` | `<sha(s)>` | `yes | no` | `<url or blank>` | `<notes>` |
| `client-bridge` | `<bridge main if used>` | `<branch>` | `<sha(s)>` | `yes | no` | `<url or blank>` | `<notes>` |

## Reviewer Findings

### Spec Reviewer

| Cycle | Reviewer | Verdict | Findings summary | Re-review needed | Timestamp |
| --- | --- | --- | --- | --- | --- |
| `1` | `<name>` | `pass | fail | partial` | `<summary>` | `yes | no` | `<timestamp>` |

### Quality Reviewer

| Cycle | Reviewer | Verdict | Findings summary | Re-review needed | Timestamp |
| --- | --- | --- | --- | --- | --- |
| `1` | `<name>` | `pass | fail | partial` | `<summary>` | `yes | no` | `<timestamp>` |

### Release Validator

| Cycle | Reviewer | Verdict | Findings summary | Re-review needed | Timestamp |
| --- | --- | --- | --- | --- | --- |
| `1` | `<name>` | `pass | fail | partial | not needed` | `<summary>` | `yes | no` | `<timestamp>` |

## Fix-Cycle Log

Use this section for 1:1 reviewer-to-executor loops. Do not paraphrase away the actual issue.

| Cycle | Triggered by | Findings to address | Executor response | Re-review result | Timestamp |
| --- | --- | --- | --- | --- | --- |
| `1` | `spec-review | quality-review | release-validator` | `<paste the actual findings or a tight quote>` | `<what changed>` | `<pass | fail | pending>` | `<timestamp>` |

## Open Risks

- `<residual risk>`
- `<monitoring item>`
- `<follow-up WO candidate>`
