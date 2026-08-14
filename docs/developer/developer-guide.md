# Developer Guide

Last updated: 2026-07-14

## Purpose

This guide owns the current developer workflow for the platform repository:
task routing, branch and collision hygiene, focused verification, documentation
impact, and safe cleanup boundaries. Repository layout belongs in the
[Repository Map](repository-map.md); product and runtime truth belongs to the
canonical owners linked below.

## Start At The Task Router

Start every task at
[docs/developer/agent-context-map.md](agent-context-map.md). It selects only the reads, code
anchors, verification, and documentation owners required for that task. Do not
turn this guide into a universal reading list.

Keep small, low-risk coding tasks direct. Use the
[orchestration standard](orchestration/orchestration-standard.md) when durable
handoff, independent review, multiple bounded steps, release sensitivity, or
meaningful risk requires a work order.

## Current Workspace Boundaries

- The platform repository at C:/Users/kiwun/Documents/ai/VPN owns portal_bot/,
  adminapp/, webapp/, marketing/, shared/, infra/, scripts/, platform tests,
  and root docs.
- adminapp/ is the primary operator surface.
  webapp/src/app/(admin)/admin/ is the temporary parity fallback.
- Active Android and Windows code, client documentation, and release artifacts
  live in the sibling C:/Users/kiwun/Documents/ai/POKROV-app repository.
  POKROV-app/main is the client promotion line.
- Retired bootstrap material and bridge bundles are archive or rollback
  evidence, never active development lanes.
- The distributed client is 1.0.0-beta. 1.0.0-rc.1 is a target; stable 1.0.0
  is not proven.
- mini is an operator probe/sandbox and an opt-in emergency bridge. It is not
  part of normal delivery or the control plane.

### Account foundation status

The additive account foundation is implemented in the repository and covered
by tests/test_account_foundation.py; it is not production-deployed or
production-proven. Public numeric account identity, stateless bearer auth,
payment fulfillment, and entitlement authority remain legacy-compatible.

Before production promotion, retain explicit manual gates for PostgreSQL
rehearsal, concurrency, rollback, and preservation of existing identity,
payment, and entitlement behavior. Do not convert repository evidence into a
deployment claim.

## Branch, Worktree, And Collision Workflow

- Keep the root platform checkout on master as the clean prospective baseline.
- Do implementation on a focused codex/* branch or isolated worktree.
- Platform work promotes through the portal/master policy lane, which maps to
  origin/master; client work promotes separately through POKROV-app/main.
- Preserve unrelated user changes, stashes, ignored evidence, and neighboring
  worktrees. Never replay a stash wholesale to recover one overlapping fact.
- Before editing shared files, record the current branch/HEAD, inspect every
  relevant worktree, and classify name overlaps as current, already landed,
  retained history, or unresolved.

Minimum collision gate:

~~~powershell
git status --short --branch
git rev-parse HEAD
git worktree list --porcelain
git -C <neighbor-worktree> status --short
git -C <neighbor-worktree> diff --name-only -- <planned-files>
~~~

Stop when another worktree has unresolved edits to the same files or when the
expected prerequisite commit is absent. After implementation, verify
git diff --name-only against the declared write scope before staging.

## Focused Verification Commands

Interactive focused checks use the configured system Python. Install the
tracked backend requirements into that interpreter after dependency changes;
release and migration rehearsals may still create an isolated environment when
their script owns one.

~~~powershell
$py = (Get-Command python.exe).Source
& $py -m pip install -r portal_bot/requirements.txt
~~~

### Backend, account, API, and bots

~~~powershell
& $py -B -m pytest -p no:cacheprovider tests/test_account_foundation.py -q
& $py -B -m pytest -p no:cacheprovider tests/test_module_slices.py -q
& $py -B -m pytest -p no:cacheprovider portal_bot/tests/test_app_first_api.py tests/test_portal_api.py -q
& $py -B -m pytest -p no:cacheprovider tests/test_api_auth_and_tickets.py tests/test_worker_retention.py -q
~~~

### Primary admin and web fallback

~~~powershell
& $py -B -m pytest -p no:cacheprovider tests/test_admin_ops_api.py -q
Push-Location adminapp
npm.cmd run build
npm.cmd run test:e2e
Pop-Location

Push-Location webapp
npm.cmd run build
npm.cmd run test:e2e:cabinet
npm.cmd run test:e2e:admin
Pop-Location
~~~

Use [adminapp/README.md](../../adminapp/README.md) and
[webapp/README.md](../../webapp/README.md) for surface-specific setup and
browser commands. Admin parity work must verify the standalone surface first.

### Marketing and shared public facts

~~~powershell
Push-Location marketing
npm.cmd run check:seo
npm.cmd run build
Pop-Location
& $py -B scripts/check-links.py
& $py -B -m pytest -p no:cacheprovider tests/test_public_copy_guardrails.py tests/test_marketing_release_readiness.py -q
~~~

### Infrastructure and observability

~~~powershell
& $py -B -m pytest -p no:cacheprovider tests/test_observer_service.py tests/test_observer_api.py tests/test_collect_node_metrics_observability.py -q
& $py -B -m pytest -p no:cacheprovider tests/test_predeploy_node_readiness.py tests/test_remote_apply_transport_front.py -q
~~~

Keep current-origin, brain-origin, and RU-origin evidence separate. A local
green test does not prove a deployed host or external origin.

### Release orchestration

- The GitHub Actions release orchestrator is manual-only and defaults to
  `dry-run`; use `full` only with explicit operator deploy intent and current
  gates.
- Dispatch inputs are passed through step environment variables and Bash
  argument arrays, not interpolated into shell source. `NODE_PASS_BRAIN` is
  scoped to the orchestrator step.
- A secret-bearing remote run is allowed only for the canonical brain host
  `82.21.114.104` with `pokrov.space` and `api.pokrov.space`. The local
  `scripts/release_orchestrator.py` enforces the same brain-host boundary when
  `NODE_PASS_BRAIN` is present.

### Active client boundary

~~~powershell
& $py -B scripts/run_client_release_gate.py preflight
& $py -B scripts/run_client_release_gate.py test --suite portal
~~~

Run builds and full client gates only when the task changes release behavior.
Physical-device, signing, store, and stable-release claims remain separate
owner gates.

### Developer and documentation contracts

~~~powershell
& $py -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py -q
git diff --check
~~~

## Feature Story Audit Artifacts

The [Repository Map](repository-map.md#canonical-audit-artifacts) links every
canonical feature/story ledger and human summary. Start with the
[canonical tracker](pokrov-canonical-feature-tracker.md), then use the
[owner-gated scenarios](pokrov-owner-gated-scenarios.md),
[open questions](pokrov-open-questions.md), and the retained completion audit
([COMPLETION-AUDIT.md](work-orders/2026-06-27--repo-feature-story-audit/COMPLETION-AUDIT.md),
[COMPLETION-AUDIT.csv](work-orders/2026-06-27--repo-feature-story-audit/COMPLETION-AUDIT.csv))
for the current evidence class and remaining owner gates.

## Documentation Impact

Update behavior owners in the same change; link to them here rather than
copying their current release snapshot.

| Change | Canonical owner |
| --- | --- |
| Positioning, trial, pricing-facing behavior, branding | [Product overview](../product/portal-vpn-product.md) |
| Backend/API/runtime responsibilities | [System overview](../architecture/system-overview.md) |
| Identity, app-first linking, bonuses, node-pool behavior | [App-first and bonus flows](../architecture/app-first-and-bonus-flows.md) |
| Deploy, access, promotion, secrets | [Deployment and access](../operations/deployment-and-access.md) |
| Hosts, probes, metrics, operator visibility | [Monitoring and visibility](../operations/monitoring-and-visibility.md) |
| Binary delivery, update checks, dynamic content | [Client delivery plan](../operations/client-delivery-update-content-plan.md) plus active client docs |
| User onboarding, support, renewal | [User guide](../user/portal-vpn-user-guide-ru.md) |
| Developer workflow or repository ownership | This guide and [Repository Map](repository-map.md) |

Client behavior changes also update
C:/Users/kiwun/Documents/ai/POKROV-app/docs/. Do not rewrite archived client
summaries unless their archive label or retained evidence changes.

## Cleanup Workflow And Never-Touch Boundary

Cleanup is snapshot-backed and deferred. Inventory first, apply only an
explicit supported class, then inventory again:

~~~powershell
& $py -B scripts/cleanup_inventory.py --class all --dry-run
& $py -B scripts/cleanup_inventory.py --class safe --apply
& $py -B scripts/cleanup_inventory.py --class all --dry-run
~~~

The safe class is for generated repo-local caches, test databases, static
exports, and disposable scratch identified by the inventory. Treat
node_modules/, .dart_tool/, build/, dist/, and .venv/ as workspace dependencies
or intentional-reset targets, not routine cleanup.

Never remove or rewrite during routine cleanup:

- .git/, worktrees, branches, stashes, or unrelated local changes;
- .env files, credentials, SSH keys, merchant secrets, or signing material;
- ops-local/ evidence, docs/audit-artifacts/, work orders, specs, or archive
  history;
- client release bundles, manifests, checksums, or retained bridge evidence;
- source forks or owner-provided design/reference assets.

Cleanup authorization does not authorize deployment, release publication,
history rewriting, or destructive recovery.
