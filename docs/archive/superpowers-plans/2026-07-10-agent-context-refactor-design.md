# POKROV Codex Context And Active Documentation Renewal

Date: 2026-07-10
Status: IMPLEMENTED_HISTORICAL
Scope: platform docs, POKROV-app docs, Codex-only instructions, orchestration,
historical retrieval policy, and safe local worktree cleanup

## Current Owners

Current instructions and documentation authority now live in root `AGENTS.md`,
`docs/README.md`, `docs/developer/agent-context-map.md`, and the active client
owner at `C:/Users/kiwun/Documents/ai/POKROV-app/docs/`.

## Historical Snapshot Boundary — 2026-07-10

The client-without-AGENTS, expected-canon, worktree, baseline, and promotion sections are 2026-07-10 historical snapshots. They preserve the approved rationale and evidence; they are not current instructions.

## Problem

The root `AGENTS.md` is 39,120 bytes and 556 lines. Codex stops adding
project instruction files after `project_doc_max_bytes`, which defaults to
32 KiB. The current file is cut around line 448, before the source-of-truth,
cleanup, never-touch, and reporting rules. This is a correctness and safety
failure, not just a token-cost problem.

The mandatory read order then adds 4,073 lines and 284,944 bytes before an
agent reaches task-specific code. Navigation and policy are repeated across
`AGENTS.md`, `docs/README.md`, `agent-context-map.md`,
`developer-guide.md`, `repository-map.md`, orchestration docs, and role
prompts.

The active documentation layer has also drifted. Known conflicts include:

- standalone `adminapp` ownership versus legacy web-admin wording and paths;
- `1.0.0-beta` versus `0.x.x-beta` wording;
- the operational role of `mini` / `RFMINI`;
- actual ad-filter behavior versus future-toggle language;
- general public-copy rules versus approved SEO `VPN` / `ВПН` wording;
- smart-connect defaults in code versus older product prose;
- a historical beta authorization versus candidate-specific current gates;
- new account, payment, and client-security work in the active integration
  branches.

`POKROV-app` is a separate Git repository. It does not inherit the platform
root contract and currently has no root `AGENTS.md`. Its docs index also mixes
current contracts, active execution, completed decisions, and historical
release handoffs.

The repository already has useful work-order, evidence, `FLOW_STATE`, role,
and context-cost standards. The problem is not absence of process. The problem
is that the process is too broadly routed, repeats global rules, and can turn a
small task into unnecessary ceremony.

Official references support a thin entry contract and progressive disclosure:

- <https://learn.chatgpt.com/docs/agent-configuration/agents-md>
- <https://openai.com/index/harness-engineering/>

## Outcome

Create one coherent Codex-native documentation system for the platform and
client repositories:

1. thin automatically loaded root contracts;
2. one task router per repository;
3. an explicit documentation registry and source-of-truth model;
4. current canonical docs reconciled with code, tests, shared facts, and
   candidate-specific evidence;
5. compact orchestration that is opt-in by task risk;
6. external-model preferences isolated in an operator playbook;
7. history searchable for rationale without becoming current authority;
8. mechanical checks that prevent the system from growing back into a wiki
   inside `AGENTS.md`.

This is one renewal program, not one giant commit. It will be delivered in
small waves so the active `market-ready-cis-integration` work is preserved.

## Non-Goals

- No GraphRAG, MCP server, SaaS documentation platform, vector service,
  documentation generator, or new package.
- No Claude, Gemini, Copilot, or generic cross-agent instruction adapters.
- No platform nested `AGENTS.md` files without a measured need.
- No rewriting historical evidence to make it look current.
- No mass frontmatter migration across hundreds of files.
- No production deploy, payment operation, node mutation, or public release
  claim as part of the documentation renewal itself.
- No deletion, relocation, or repository conversion of `.content-video-ad`.
- No silent product decision when current code and intended canon disagree.

## Repository And Instruction Architecture

### Platform repository

```text
AGENTS.md
docs/README.md
docs/developer/agent-context-map.md
docs/developer/developer-guide.md
docs/developer/repository-map.md
docs/developer/agent-playbooks/external-model-consults.md
docs/developer/orchestration/**
docs/archive/README.md
```

The platform root contract is the only tracked `AGENTS.md` inside the
platform repository in this program.

### Client repository

```text
C:/Users/kiwun/Documents/ai/POKROV-app/AGENTS.md
C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md
C:/Users/kiwun/Documents/ai/POKROV-app/docs/{product,architecture,design,operations}/**
```

The client gets its own thin root contract. Its existing `docs/README.md`
will be the client task router and registry; no second client navigation file
is added unless the index cannot stay inside its budget.

### Local video workspace

`.content-video-ad/AGENTS.md` remains a machine-local, ignored scoped
contract. It is not platform clutter and is not a tracked client instruction
source.

## Authority Model

A single flat ladder is insufficient because task authority, intended product
behavior, implemented behavior, and live runtime state answer different
questions. The router will expose four resolution ladders.

### Task and workflow authority

1. System and developer instructions supplied by Codex.
2. Direct user instruction for the current task within those boundaries.
3. Repository root `AGENTS.md`.
4. Intentionally scoped local `AGENTS.md`, which may specialize but may not
   weaken universal safety, evidence, destructive-operation, or release-honesty
   rules.
5. Task router and developer process docs.

### Intended product authority

1. Owner-approved product decisions and machine-readable shared contracts.
2. Canonical product, architecture, operations, design, and user docs.
3. Current code and tests as implementation evidence.
4. Active work orders as execution state, never product authority.
5. Historical decisions and archive for rationale only.
6. External model output as advisory critique only.

When code and canonical intent disagree, record a conflict. Do not silently
declare either side correct.

### Observed runtime authority

1. Current production database and current provider/control-plane state.
2. Candidate-specific runtime, API, UI, device, origin, and operator evidence.
3. Current generated reports or artifacts with recorded provenance.
4. Older evidence, attestations, and release handoffs.

Observed runtime state does not by itself authorize a new product contract or a
broader public claim.

### Release-claim authority

1. Exact candidate identity.
2. Current candidate-specific gate evidence.
3. Required manual/provider/device/origin checks.
4. Current release decision.
5. Historical authorization only as background.

An old `GO` cannot close a new candidate. An archive may explain why a
decision was made; it may never decide what should be done now.

## Documentation Classes

`docs/README.md` in each repository will classify important documents
centrally:

- `CANONICAL`: current product, architecture, operations, design, developer,
  or user contract;
- `ACTIVE_EXECUTION`: current plans, work orders, checklists, or unresolved
  decisions;
- `EVIDENCE`: audit artifacts, ledgers, candidate reports, release handoffs,
  and attestations;
- `HISTORICAL_REFERENCE`: completed plans, superseded decisions, old
  screenshots, retired lanes, and rollback provenance;
- `OPERATOR_PLAYBOOK`: optional tooling and consult preferences that are
  current for operators but are not product or coding-agent authority;
- `EXPERIMENTAL`: opt-in tools or research that does not define normal agent
  behavior.

Classification lives in the registry. Existing evidence and archive files are
not bulk-edited just to add labels.

Every active canonical document must have one clear owner in the registry and
must either be reconciled in this program or explicitly recorded as
`REVIEWED_NO_CHANGE`. A file is not canonical merely because it lives under a
directory whose name sounds current.

## Thin Root Contracts

### Platform `AGENTS.md`

Hard budget:

- at most 8,192 UTF-8 bytes;
- at most 120 physical lines;
- target 6-8 KiB.

It contains only:

1. repository mission and platform/client boundary;
2. instruction and authority precedence;
3. start-of-task classification and task-router pointer;
4. universal secret, destructive-operation, evidence-retention, archive, and
   concurrent-work safety;
5. release-claim and manual-gate honesty;
6. external-model advisory boundary;
7. docs-impact trigger;
8. branch/promotion truth and focused verification;
9. short handoff expectations.

It does not contain dated status snapshots, host inventories, model catalogs,
prices, prompt templates, active-plan lists, third-party research links, full
subsystem inventories, a global must-read list, or copied product facts.

### Client `AGENTS.md`

The client root uses the same 8,192-byte and 120-line limits. It adds only
client-specific rules:

- `POKROV-app/main` ownership and promotion boundary;
- platform shared-fact dependency;
- Android/Windows current public scope and Apple readiness boundary;
- runtime/core, secure-storage, signing, device, and release-evidence guards;
- client task routes through `docs/README.md`;
- focused Flutter/host verification and manual gates.

It must not copy the platform wiki or dated release handoffs.

## Task Routing

`docs/developer/agent-context-map.md` is the detailed platform router. Its
primary table uses:

| Task | Read first | Inspect | Verify | Docs impact |
| --- | --- | --- | --- | --- |

Routes cover:

- backend/API/bots;
- account, authentication, email, and payments;
- web cabinet;
- standalone `adminapp`;
- marketing/SEO/copy;
- shared facts/design contracts;
- infrastructure/observability;
- scripts/release operations;
- documentation and cleanup;
- active client repository;
- historical investigation.

The map points directly to relevant docs and code. It never says “read the
global must-read set.”

Hard budget:

- at most 12,288 UTF-8 bytes;
- at most 240 physical lines.

`POKROV-app/docs/README.md` provides equivalent client routes for shell/UI,
runtime/core, WARP, platform API contracts, Android, Windows, Apple readiness,
release packaging, design, and docs/history.

## Active Documentation Renewal

“All important docs” means the active entrypoints and canonical contracts, not
all 644 files under `docs/`.

### Platform entrypoints

- `AGENTS.md`
- `docs/README.md`
- `docs/developer/agent-context-map.md`
- `docs/developer/developer-guide.md`
- `docs/developer/repository-map.md`
- `docs/archive/README.md`
- `DESIGN.md`

### Platform domain canon

The program reviews and reconciles the current product, architecture,
operations, design, launch, and user contracts listed as `CANONICAL` in the
renewed `docs/README.md`. Priority goes to documents governing:

- product identity, availability, trial/reward, account, payment, and beta
  limitations;
- system/API/app-first/payment/support/client-delivery architecture;
- deployment, observability, payments, publishing, rollback, and origin
  evidence;
- public copy, SEO, design tokens, generated assets, user guidance, and launch
  claims.

Audit ledgers, generated inventories, completion reports, dated handoffs, and
old launch copy are moved out of the canonical list when they are evidence or
history. They remain intact.

### Conflict-resolution ledger

The implementation plan will keep a compact ledger with:

- claim or contract;
- current canonical owner;
- code/test/shared-fact evidence;
- runtime/candidate evidence when relevant;
- active neighboring-branch impact;
- decision: `UPDATE_CANON`, `UPDATE_IMPLEMENTATION`, `RECLASSIFY`,
  `REVIEWED_NO_CHANGE`, or `UNRESOLVED_OWNER_DECISION`;
- affected platform and client docs.

The active `market-ready-cis-integration` branches are reconciled before
product/account/payment/client canon is finalized. This program does not
overwrite their newer truth from an older base.

The expected structural and claim-boundary resolutions are listed below, but
each remains a conflict-ledger candidate until the wave-start collision gate
confirms the newest branch and owner-approved baseline:

- `adminapp` is the primary operator write surface; legacy web admin is a
  fallback/parity surface;
- current distributed beta is `1.0.0-beta`, the approved target candidate is
  `1.0.0-rc.1`, and stable `1.0.0` remains unproven;
- existing outside-store beta authorization and new market-ready release
  readiness are separate ledgers;
- `mini` / `RFMINI` is the RU probe/sandbox and an opt-in emergency bridge,
  not a normal delivery node or control plane;
- visible `VPN` / `ВПН` is allowed only on approved SEO/search-intent
  surfaces; normal shared copy remains stricter;
- Lava.top beta checkout evidence does not prove stable refund, chargeback, or
  reconciliation maturity;
- current smart-connect defaults are the code/test-backed shortlist of eight
  candidates and 20% stickiness; older five/15% prose is updated unless the
  neighboring implementation changes the contract;
- the July market-ready design is approved target state, not evidence that the
  target runtime already exists.

The following canon waits for the neighboring implementation and its tests:
account identities/devices/sessions, OTP/recovery/refresh rotation,
first-connect trial activation, Telegram reward migration, referral economy,
free-soft-mode enforcement, payment ownership/claim flow, persisted notices,
FCM delivery, stable WARP proof, retention windows, exact RC metadata, and
stable release status.

Ad filtering stays `UNRESOLVED_OWNER_DECISION`: current backend behavior
always loads the block ruleset, older product prose describes a future explicit
toggle, and the market-ready target calls the feature a non-goal. Neither code
nor canon is normalized until the active implementation chooses and proves
`UPDATE_IMPLEMENTATION` or an owner-approved current product contract.

## Orchestration Renewal

The existing orchestration directory remains. It is simplified and made
task-risk-aware rather than replaced.

### Ceremony levels

- `direct`: small, low-risk, single-pass tasks; no WO or `FLOW_STATE`.
- `bounded_wo`: work that must survive context boundaries, separates
  executor/reviewer roles, spans multiple steps, or has meaningful risk.
- `release_wo`: release-, deploy-, payment-, security-, persistence-,
  provider-, device-, or origin-sensitive work requiring candidate-specific
  proof.

A WO is not required merely because a task has more than one shell command.

### Work-order contract

Compact WOs retain only goal, non-goals, write scope, authority anchors,
acceptance oracle, docs impact, validation, no-touch scope, and status.

Full WOs add MREP, risk proof, mechanism adequacy, reviewability, validation
attribution, manual gates, promotion evidence, and context/cost harness only
when the task actually needs them.

Completed WOs are evidence. They are not silently rewritten into new product
truth.

The default `WO.template.md` becomes compact. It does not preload a fixed
eight-document checklist or every backend/web/marketing/infra/client/release
validation matrix. Optional proof and validation blocks are copied from the
authoring guide only when their trigger applies. This keeps one template owner
without creating a family of near-duplicate WO templates.

### Evidence model

The existing evidence list is split into independent dimensions:

- source: `static_review`, `synthetic_test`, `tracked_fixture`,
  `generated_artifact`, `api_e2e`, `ui_behavior`, `runtime_smoke`,
  `full_validation_epoch`, `manual`, or `n/a`;
- target scope: local, exact candidate, deployed environment, provider,
  physical device, current-origin, brain-origin, or RU-origin;
- freshness: current-candidate, current-environment, retained-current, or
  historical/stale;
- attribution: WO-owned, wave/integration, pre-existing, unrelated, or blocked
  by access.

No single “tier” number is allowed to imply all four dimensions.

### `FLOW_STATE`

`FLOW_STATE` is created only when a WO enters review/fix-cycle, becomes
blocked/partial, or needs durable handoff. It is compact decision state, not a
transcript or universal task log.

The third same-class finding without a mechanism change still stops ordinary
fix routing. Status vocabulary and stop rules are normalized across
`orchestration-standard.md`, `flow-state.md`, role prompts, and templates.

### Role boundaries

- orchestrator: classification, routing, status, integration, and completion;
  not routine implementation;
- scout: read-only minimum context and conflict discovery;
- implementation strategy: optional for complex or unclear work, not a
  mandatory hop;
- executor: bounded writes, docs impact, and evidence; never self-closes;
- spec reviewer: contract compliance only;
- quality reviewer: correctness, maintainability, security, performance,
  usability, and evidence quality after spec compliance;
- release validator: exact-candidate gates, origins, manual blockers, rollback
  safety, and public-claim boundaries only when release-sensitive.

Role files reference the shared standard instead of copying the complete lane,
claim, and source-of-truth rules.

Target budgets:

- orchestration standard: at most 16 KiB;
- orchestrator role: at most 5 KiB;
- every other role: at most 4 KiB;
- context-cost harness: at most 12 KiB;
- default WO template: at most 12 KiB;
- wave index and other orchestration templates: at most 8 KiB each;
- no mandatory role chain for a direct task.

## External Model Consult Playbook

Create:

`docs/developer/agent-playbooks/external-model-consults.md`

This is an operator preference playbook, not product canon and not a mandatory
read for backend/frontend/client agents.

It owns:

- current OpenRouter/OpenCode consult models;
- dated price and availability snapshots;
- routing between Kimi, DeepSeek, GPT, and alternative reviewers;
- prompt patterns and compact skill packets;
- OpenCode CLI and PowerShell quirks;
- cache-aware packet shape for expensive repeated consults;
- output extraction and redaction rules.

The playbook must state:

- Codex remains the implementation/orchestration authority;
- external models are narrow reviewers or rewriting partners only;
- model IDs, prices, availability, and latency must be reverified before a
  cost-sensitive run;
- no secret, auth, payment, user, subscription, or raw operational material is
  sent;
- external output never outranks canon, code, tests, or current evidence.

`context-cost-harnesses.md` keeps provider-neutral packet and telemetry rules.
It links to the playbook but does not duplicate model catalogs, prices, routing,
prompt patterns, or OpenCode shell notes.

The existing OpenAI operator-assistant/vector-store helper is classified
`EXPERIMENTAL` and removed from the default agent route. This renewal neither
adds a retrieval service nor expands that helper.

## Historical Retrieval

Historical retrieval is allowed only for rationale, provenance, regression
forensics, and release-evidence questions.

Default route:

1. current registry and canonical docs;
2. `rg` / `rg --files` over exact historical zones;
3. `git log`, `git log -S`, `git log -G`, blame, and relevant PR/commit
   discussion when available;
4. targeted reads from `docs/archive/**`,
   `docs/developer/work-orders/**`, `docs/audit-artifacts/**`,
   `docs/superpowers/specs/**`, old decisions, and retained release material.

No historical file may define current action without promotion through an
active canonical document.

No index is built in this program. If repeated real queries later show that
`rg` plus Git is insufficient, the next step may be a local, generated,
ignored SQLite FTS/BM25 index with metadata:

- repository;
- subsystem;
- document class: current, history, or evidence;
- date;
- `superseded_by`;
- work-order;
- release/candidate.

Embeddings may be evaluated only after a fixed historical-query benchmark
shows material FTS misses. They remain optional, local/rebuildable where
possible, outside the default context chain, and non-authoritative.

## POKROV-app Renewal

The client repository is part of this program and receives:

1. a thin root `AGENTS.md`;
2. a renewed `docs/README.md` with task routes and document classes;
3. reconciliation of current client product, architecture, design, operations,
   release-readiness, and implementation-backlog docs against current code,
   tests, config seeds, and platform contracts;
4. explicit separation of current `1.0.0-beta` truth from completed June
   handoffs and old Karing/clean-room decisions;
5. cross-repo links back to the exact platform contract owners;
6. client-specific verification and manual-gate language.

Client edits occur in a dedicated `codex/*` branch/worktree from the current
client baseline. The clean `main` checkout is not used as a scratchpad.
Platform and client commits, tests, promotion evidence, and rollback remain
separate.

## .content-video-ad

`.content-video-ad` is an intentional autonomous local workspace, mostly for
POKROV/VPN content production. It remains ignored and is not cleaned up.

After the tracked platform root is shortened, its local `AGENTS.md` is reduced
to a 20-22 KiB target so the combined Codex instruction chain remains below
32 KiB with margin. The local contract must preserve its unique offer,
production workflow, model/TTS routing, public wording, and safety rules while
pointing to its own detailed playbooks. This is a local-only change with its
own before/after backup and verification.

## Mechanical Verification

No new dependency or service is added. Existing tests and scripts are extended
where appropriate.

Required platform checks:

- root UTF-8 byte and physical-line budgets;
- router, orchestration, role, and context-harness budgets;
- only the intended tracked platform `AGENTS.md`;
- required root semantic guards;
- forbidden volatile catalogs/status snapshots in root;
- resolvable local Markdown links;
- valid task-route paths and commands;
- registry classification for every listed important doc;
- no GraphRAG/vector/embedding recommendation as a current architecture;
- docs-assistant/support-KB allowlists remain semantically correct;
- cleanup inventory includes current generated roots such as
  `adminapp/out`;
- `git diff --check` and focused tests.

Required client checks:

- client root contract budgets and semantic guards;
- client registry/task routes point to real files;
- focused Flutter/analyze/test/build checks selected by changed docs/contracts;
- no historical release handoff promoted as a fresh candidate pass;
- `git diff --check`.

Manual `codex debug prompt-input` before/after inspection may confirm the
effective instruction chain, but it is not a CI dependency.

## Delivery Waves

### Wave 0: specification and baseline

- finish this design and the implementation plan;
- record branch/worktree/client baseline;
- inventory active docs and conflict owners;
- do not modify the neighboring task.

### Wave 1: platform containment

- shrink root `AGENTS.md`;
- remove the global must-read loop;
- update the platform router/registry enough to preserve every moved rule;
- record a migration table from each removed root rule to its single
  authoritative destination;
- add size and semantic gates;
- keep the diff deliberately small.

### Wave 2: platform developer and orchestration layer

- normalize developer guide, repository map, archive policy, WO rules,
  evidence model, `FLOW_STATE`, roles, templates, and context-cost harness;
- create the external-model consult playbook;
- update experimental assistant classification.

Wave 2 does not start while the active platform worktree has unlanded changes
to `developer-guide.md`, `repository-map.md`, or another Wave 2 target. A
non-overlapping orchestration-only slice may proceed only with an explicit file
allowlist and its own commit.

### Wave 3: platform canonical refresh

- first reconcile the completed `market-ready-cis-integration` baseline;
- resolve the conflict ledger against current code/tests/shared facts;
- update or reclassify important product, architecture, operations, design,
  launch, and user docs;
- do not rewrite evidence/history.

### Wave 4: client repository

- create the client root contract;
- renew the client registry/routes;
- reconcile important client canon and release/evidence boundaries;
- verify in the separate client lane.

### Wave 5: local workspace and cleanup

- reduce `.content-video-ad/AGENTS.md` locally and verify the combined chain;
- snapshot and remove stale worktrees only through the reversible procedure;
- promote platform and client commits only after newer canon is preserved.

Each wave has its own diff review, focused checks, and commit. A failed wave
does not require rolling back already verified containment.

Before every wave, record a collision gate:

- current branch/HEAD for both repositories;
- active worktrees and their dirty paths;
- overlap with the proposed wave write set;
- action: proceed, narrow the write set, wait for landing, or replay on the
  newer baseline.

## Stop Conditions

Stop the current wave instead of stretching it when:

- a new dependency, service, MCP server, vector store, or manifest loader is
  required;
- platform containment exceeds seven files before a separate reviewed commit;
- root or router exceeds its byte/line budget;
- a removed universal safety rule has no authoritative destination;
- a product conflict is being “resolved” only by rewriting prose without
  implementation, test, or owner-decision evidence;
- evidence/history content would be rewritten rather than reclassified or
  linked;
- an active neighboring worktree owns the same files and its changes are not
  yet committed/reconciled;
- cleanup cannot prove retained tracked, untracked, and ignored state is safe.

## Concurrent Work And Promotion

Platform design work currently lives in:

`C:/Users/kiwun/Documents/ai/VPN/.worktrees/agent-context-refactor`

on:

`codex/agent-context-refactor`

The active platform integration remains in:

`C:/Users/kiwun/Documents/ai/VPN/.worktrees/market-ready-cis-integration`

The active client integration remains in:

`C:/Users/kiwun/Documents/ai/POKROV-app/.worktrees/market-ready-cis-client-integration`

Neither active worktree is edited by this branch. Before Wave 3 or Wave 4:

1. re-read both active task states;
2. identify commits and files changed since this specification;
3. replay/rebase the documentation wave onto the newest intended baseline;
4. preserve newer product and client canon;
5. rerun all affected checks.

The current platform `master` predates July/adminapp work. This branch must
not be merged directly into that old baseline. The safe order is:

1. promote the current platform baseline into `master`;
2. replay/rebase the small documentation commits onto updated `master`;
3. verify and merge;
4. keep client promotion separate on `POKROV-app/main`;
5. remove temporary branches/worktrees only after commit reachability is
   proven.

## Safe Worktree Cleanup

Old dirty worktrees are not disposable merely because their branch tips are
merged. For each stale worktree:

1. verify no active Codex task owns it;
2. inventory ignored paths as well as tracked and untracked state without
   printing file contents or secret values;
3. stop if ignored state is retained, unknown, secret-bearing, or otherwise
   not safely reproducible; removal is allowed only when ignored entries are
   absent or explicitly classified as disposable generated output;
4. inspect changed paths and scan for obvious secret/bearer material without
   printing sensitive values;
5. create a clearly named local stash with tracked and untracked files;
6. record stash object, worktree path, branch, HEAD, tracked/untracked/ignored
   counts, and time in retained local operator evidence;
7. verify the stash is readable, the worktree clean, and no retained ignored
   state would be lost;
8. remove the worktree without `--force`;
9. delete only a branch whose commit is reachable from the intended retained
   line;
10. never push the stash automatically.

If ignored-state classification, secret scanning, or stash verification is
uncertain, cleanup stops and the worktree remains.

## Completion Criteria

The program is complete only when:

1. platform and client root contracts fit their budgets and preserve universal
   guards;
2. task routes no longer require irrelevant global reading;
3. every important active doc is classified and either reconciled or marked
   `REVIEWED_NO_CHANGE`;
4. known canon conflicts are resolved or explicitly left as
   `UNRESOLVED_OWNER_DECISION`;
5. orchestration is consistent, compact, and optional for direct tasks;
6. external model/tool preferences live only in the dedicated playbook or
   experimental helper docs;
7. archive/evidence remains intact and cannot drive current action;
8. platform and client focused checks pass independently;
9. active neighboring work is preserved;
10. promotion and cleanup leave recoverable Git state.

## Rollback

Each tracked wave is an isolated commit and can be reverted independently.
Platform and client repos have separate rollback points.

Local `.content-video-ad` edits require a before-change backup.

Worktree cleanup is rollback-safe only after the named stash object and
reconstruction path are verified. No destructive cleanup is considered
complete merely because a directory disappeared.
