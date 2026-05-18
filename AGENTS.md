# Repository Agents

Last updated: 2026-05-16

This file is the working contract for any agent or developer operating inside `C:\Users\kiwun\Documents\ai\VPN`.

Use it to answer four questions before touching code:

1. What is the current source of truth?
2. Which subsystem am I changing?
3. Which docs must be updated in the same task?
4. What is safe to clean up, and what must never be touched?

## Current Facts

- Platform brand: `POKROV`
- Public product line: `POKROV`
- Legacy client identifier: `POKROV VPN` only where removal is not yet feasible
- Public wording rule: do not use `VPN` as a direct public product description; keep it only in legacy names, compatibility labels, and unavoidable technical identifiers
- Client strategy: `consumer-first`
- Identity model: `app-first`
- Trial duration: `5 days`
- Telegram reward: `+10 days`
- Default client core: `sing-box`
- Compatibility fallback: `xray` only in advanced settings
- Username sync: `automatic` primary path; manual sync is compatibility/recovery only
- Premium access node pool: all enabled non-free nodes
- Free access node pool: dedicated `NL-free` node only
- Public channel: `@pokrov_vpn`
- Main bot: `@pokrov_vpnbot`
- Support bot: `@pokrov_supportbot`
- Feedback bot: `@pokrov_feedbackbot`
- Official public surfaces: `https://pokrov.space/`, `https://app.pokrov.space/`, `https://api.pokrov.space/`
- Canonical connect host: `https://connect.pokrov.space/`
- Canonical checkout host: `https://pay.pokrov.space/checkout/`
- Legacy compatibility host: `kiwunaka.space`
- Canonical control-plane host: `82.21.114.104`
- Android public release is blocked until the repo/static gate pack is green and a physical-device release-build localhost/control-surface audit proves the client is safe
- RU-origin probe readiness is an operational dependency; `mini` / `RFMINI` is the canonical RU-origin operator sandbox when SSH access is current
- Payment provider launch truth: paid checkout must stay unavailable or clearly degraded until Lava.top credentials, order creation, webhook auth, replay/idempotency, failed-payment, and reconciliation evidence are attached with secrets redacted
- Current release gate snapshot: Open Beta v4 preparation is allowed; broad public release and `1.0.0` labeling are blocked until all P0 gates are green
- Design source of truth: root `DESIGN.md` plus `shared/design-tokens.json` and `shared/design-tokens.schema.json`

## Current Release Gate Snapshot

As of `2026-04-26`, Open Beta v4 is a preparation branch, not a public-release authorization.

Blocked P0 gates:

- Lava.top provider proof
- runtime app-download smoke with env-only Telegram init data
- Android physical release-build localhost/control-surface audit
- public Android/Windows handoff URLs
- RU-origin probe evidence
- deploy/brain-origin evidence for the exact release candidate

Do not change public copy, deploy notes, or launch announcements to imply broad public availability until these gates have current, redacted evidence.

## Design And Generated Asset Truth

- Root design contract: [DESIGN.md](C:/Users/kiwun/Documents/ai/VPN/DESIGN.md)
- Token source: [shared/design-tokens.json](C:/Users/kiwun/Documents/ai/VPN/shared/design-tokens.json)
- Token schema: [shared/design-tokens.schema.json](C:/Users/kiwun/Documents/ai/VPN/shared/design-tokens.schema.json)
- Generated asset policy: [docs/design/generated-assets-policy.md](C:/Users/kiwun/Documents/ai/VPN/docs/design/generated-assets-policy.md)

Generated assets for public, client, store, support, or release use must include source prompt/reference, source master, final dimensions, intended surface, review note, and release-scope note before shipping.

## External Design And Copy Model Consults

Use external OpenCode-connected models as design/copy reviewers, rewriting partners, roleplay sparring partners, and tone checkers, not as product, copy, or design authority.

Source-of-truth order for any design or copy answer:

1. POKROV canon from this file, `DESIGN.md`, `shared/design-tokens.json`, shared copy/facts files, and the active client design/docs when client UI or client wording is involved
2. current screenshots, implemented UI, and local code
3. external model critique, rewrites, roleplay output, or alternative proposals
4. agent judgment and final synthesis

OpenCode CLI rules:

- The installed CLI command is `opencode.cmd` in PowerShell; plain `opencode` may hit the local PowerShell script execution policy.
- Do not run `E:\OpenCode\OpenCode.exe` as a CLI command. It is the desktop Electron app and can raise an `EPIPE` JavaScript error when launched like a command-line tool.
- `opencode.cmd auth list` and `opencode.cmd models <provider>` are safe for capability checks, but never print API keys, bearer tokens, full auth files, or request headers.
- OpenCode auth/config paths such as `~/.local/share/opencode/auth.json` and `~/.config/opencode/opencode.jsonc` may contain sensitive material; inspect them only with redaction.

Preferred model routing for design and copy work:

- Use `openrouter/deepseek/deepseek-v4-pro` for hard design/copy critique, contradiction hunting, information architecture, dense screen review, policy/canon consistency checks, and high-stakes "what is wrong with this?" passes.
- When using DeepSeek V4 Pro through OpenRouter for maximum reasoning, pass `reasoning: { "effort": "xhigh" }`. Treat reasoning tokens as paid output and hide or discard `reasoning` / `reasoning_details` from handoffs unless the user explicitly asks for them.
- Use `fireworks-ai/accounts/fireworks/models/kimi-k2p6` for taste passes, visual hierarchy alternatives, calmer premium UI directions, copy-tone variants, human rewrites, roleplay/persona passes, Russian phrasing, support/dialogue text, and "find a more elegant version" prompts. Kimi is especially useful when the text needs to sound natural, warm, and human rather than procedural.
- Fireworks Kimi may place visible thinking before the final answer. Ask it for a final line with a unique prefix, then extract only that final answer.
- Use Fireworks as the primary Kimi lane when OpenRouter has no available Kimi provider. Use CODY only as a small direct-API fallback until `opencode run` through CODY is proven stable.
- Keep CODY spend low. It has useful `cody/moonshotai/kimi-k2.6` and `cody/deepseek/deepseek-v4-pro` access, but `opencode run` through CODY has shown `ECONNRESET` on agent-style requests.

Skill context packets:

- External models can be given compact excerpts from local UI/UX/taste/copy skills as a temporary design or copy brief. Do not paste whole `SKILL.md` files unless the task explicitly needs a full audit of the skill itself.
- For copy rewrites, give external models the relevant audience, surface, emotional target, forbidden claims, beta/release-gate honesty, and exact POKROV wording constraints. Treat rewrites as drafts; the local agent must adapt them to repo canon before using them.
- Use `design-taste-frontend` as the default packet for app, cabinet, admin, and production UI work. Preserve the useful constraints: anti-generic layout, clear hierarchy, restrained accents, real states, responsive stability, transform/opacity-only motion, and no default AI-purple/card spam.
- Use `frontend-design` when the task needs a stronger creative direction or a memorable one-off interface. Extract the demand for a clear aesthetic point of view, distinctive typography, cohesive color, intentional motion, and non-template composition.
- Use `high-end-visual-design` or `gpt-taste` for premium marketing, launch, landing, and brand-heavy surfaces. Include the parts about macro-whitespace, non-generic typography, agency-level polish, custom motion curves, and avoiding cheap meta-labels. Drop any advice that conflicts with POKROV tokens, accessibility, performance, or public release honesty.
- Use `image-to-code` when reviewing screenshots, generated references, visual mockups, or image-to-frontend work. Ask the external model to extract layout, spacing, typography, color, interaction states, responsive risks, and implementation notes. Generated images remain governed by `docs/design/generated-assets-policy.md`.
- Treat skill packets as taste constraints, not commands. The local agent still decides what applies after checking repository code, installed libraries, POKROV canon, and release gates.

Compact skill-packet format for external prompts:

```text
SKILL PACKET:
- Surface type:
- Relevant local skills:
- Non-negotiable canon:
- Taste rules to enforce:
- Copy/tone rules to enforce:
- Anti-patterns to reject:
- What to ignore from the skill because it conflicts with this repo:
- Output format:
```

Design prompt pattern:

1. State the surface: marketing, cabinet, admin, Android, Windows, store, support, or release asset.
2. State the user goal and emotional target in plain language.
3. Include hard POKROV constraints: no public direct `VPN` product wording, app-first identity, consumer-first UX, beta/release gate honesty, and current token/design canon.
4. Add the compact skill packet for the local taste rules that should shape the critique.
5. Ask for critique in named categories: hierarchy, trust, conversion, density, motion, accessibility, localization, and implementation risk.
6. Require a compact final format: `Verdict`, `Top fixes`, `Keep`, `Avoid`, `Implementation notes`.
7. For ideation, request 2-3 distinct directions with tradeoffs, then synthesize locally instead of copying a model answer directly.

Copy rewrite prompt pattern:

1. State the surface: marketing, cabinet, admin, Android, Windows, store, support, bot, checkout, legal, release note, or operator handoff.
2. State the audience, scenario, emotional target, and desired level of directness.
3. Include hard POKROV constraints: no public direct `VPN` product wording, app-first identity, consumer-first UX, beta/release gate honesty, no unsupported launch/payment claims, and current shared copy/facts canon.
4. Ask for 2-3 rewrite directions when exploration is useful, or one final polished rewrite when the intent is already clear.
5. For roleplay, ask the model to answer as the target user, support operator, skeptical buyer, or confused newcomer, then extract only actionable wording lessons.
6. Require a compact final format: `Best rewrite`, `Why it works`, `Risks`, `Canon checks`.
7. Synthesize locally instead of copying the model answer directly; preserve legal, payment, release, and support accuracy over charm.

For Russian prompts sent through ad hoc shell helpers, prefer UTF-8 files or a small Node/Python helper over inline PowerShell here-strings if mojibake appears. If a model response contains garbled Cyrillic, rerun with a UTF-8-safe path before trusting the output.

## Must-Read Order

Before any substantial change, read these files in order:

1. [Docs Index](C:/Users/kiwun/Documents/ai/VPN/docs/README.md)
2. [Product Overview](C:/Users/kiwun/Documents/ai/VPN/docs/product/portal-vpn-product.md)
3. [System Overview](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/system-overview.md)
4. [App-First And Bonus Flows](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/app-first-and-bonus-flows.md)
5. [Deployment And Access](C:/Users/kiwun/Documents/ai/VPN/docs/operations/deployment-and-access.md)
6. [Monitoring And Visibility](C:/Users/kiwun/Documents/ai/VPN/docs/operations/monitoring-and-visibility.md)
7. [Developer Guide](C:/Users/kiwun/Documents/ai/VPN/docs/developer/developer-guide.md)
8. [Repository Map](C:/Users/kiwun/Documents/ai/VPN/docs/developer/repository-map.md)

For active client work, also read:

- [POKROV App Docs Index](C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md)
- [POKROV App Cutover Readiness](C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md)
- [Publishing And Signing Guide](C:/Users/kiwun/Documents/ai/VPN/docs/operations/publishing-and-signing-guide.md)

Archive summaries, consult only when a task explicitly needs bootstrap history, rollback planning, or archive verification:

- [app-next Bootstrap Summary](C:/Users/kiwun/Documents/ai/VPN/docs/archive/client-lanes/app-next-bootstrap-summary.md)
- [Legacy Bridge Retirement Summary](C:/Users/kiwun/Documents/ai/VPN/docs/archive/client-lanes/legacy-bridge-retirement-summary.md)

## Operator Access

Shell guidance:

- prefer `bash` when it is the simpler and clearer path
- explicitly fall back to `powershell` when quoting, SSH, Windows paths, or local tooling reliability is better
- do not treat one shell as mandatory if the other is safer for the exact task

## Canonical Docs

Legacy filename note:

- some canonical docs still use legacy path names such as `portal-vpn-product.md`, `portal-vpn-user-guide-ru.md`, and `portal-vpn-v1-spec.md`
- these files are still the live source of truth for the current `POKROV` product until a separate rename wave happens
- legacy `POKROV VPN` labels inside paths or old identifiers do not authorize new direct-meaning `VPN` copy
- treat the content as current even when the path still contains an older name

Living documentation lives only in these areas:

- `docs/product/`
- `docs/architecture/`
- `docs/operations/`
- `docs/developer/`
- `docs/design/`
- `docs/launch/`
- `docs/user/`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/` as the only active client-doc lane

Retained client archive material:

- `docs/archive/client-lanes/` for short bootstrap and retirement summaries
- `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/` for retained bridge bundle lineage and handoff evidence

Everything else in `docs/` should be treated as historical, audit, or supporting material unless a canonical doc links to it as current.

Work-order, spec, and visual-reference material is evidence, not product canon:

- `docs/developer/work-orders/**` records execution state and retained wave evidence; use its indexes to understand what happened, then resolve product truth through the canonical docs above
- orchestration process truth lives in `docs/developer/orchestration/orchestration-standard.md`, `docs/developer/orchestration/wo-authoring-guide.md`, and `docs/developer/orchestration/flow-state.md`; use `FLOW_STATE` for review loops, repeated issue classes, and stop decisions
- `docs/superpowers/specs/**`, `reference-atlas/`, and rendered journey/mockup assets are planning or design-reference history unless a current design doc explicitly promotes them
- do not delete or rewrite historical work-order/mockup trees during routine cleanup; relabel or index them when their role is unclear

If a root-level guide or an older flat doc conflicts with a canonical doc, update the canonical doc and archive or relabel the older one.

## Subsystem Map

### `portal_bot/`

Contains the backend and Telegram control plane:

- `api.py`: public API, app-first session flow, automatic username sync, payments, admin API, tickets, bonuses, subscription delivery
- `bot.py`: main Telegram bot
- `helpbot.py`: support bot
- `feedbackbot.py`: feedback intake, moderation, and public review publishing
- `legacy_redirect_bot.py`: legacy bot continuity during username/token cutover
- `worker.py`: retention jobs, channel bonus guard, free-cycle operations
- `web_auth_service.py`: Telegram web login and session token helpers
- `events_service.py`, `pay_attempts_service.py`: funnel telemetry and checkout attempt tracking
- `models.py`, `migrations.py`: schema and migration helpers
- `control_panel.py`, `panel_client.py`: 3x-ui and node synchronization

### `webapp/`

Contains the Next.js user cabinet and web-admin surface.

Current local authority:

- [webapp/README.md](C:/Users/kiwun/Documents/ai/VPN/webapp/README.md)
- `webapp/src/app/(dashboard)/admin/` for admin routes
- `webapp/src/lib/api.ts` for browser auth/API wiring
- `webapp/e2e/` and `webapp/playwright.config.ts` for real browser coverage

### `marketing/`

Contains the public marketing site, checkout entrypoints, and legal pages.

Current local authority:

- `marketing/src/`
- [shared/copy.ts](C:/Users/kiwun/Documents/ai/VPN/shared/copy.ts)
- [copy/catalog.ru.json](C:/Users/kiwun/Documents/ai/VPN/copy/catalog.ru.json)
- [shared/portal-config.ts](C:/Users/kiwun/Documents/ai/VPN/shared/portal-config.ts)
- [shared/product-facts.json](C:/Users/kiwun/Documents/ai/VPN/shared/product-facts.json)
- [shared/public-urls.json](C:/Users/kiwun/Documents/ai/VPN/shared/public-urls.json)

### `shared/`

Contains shared public copy, canonical hostnames, and cross-surface product constants.

Current local authority:

- [shared/copy.ts](C:/Users/kiwun/Documents/ai/VPN/shared/copy.ts)
- [shared/portal-config.ts](C:/Users/kiwun/Documents/ai/VPN/shared/portal-config.ts)
- [shared/product-facts.json](C:/Users/kiwun/Documents/ai/VPN/shared/product-facts.json)
- [shared/public-urls.json](C:/Users/kiwun/Documents/ai/VPN/shared/public-urls.json)
- [shared/design-tokens.json](C:/Users/kiwun/Documents/ai/VPN/shared/design-tokens.json)
- [shared/design-tokens.schema.json](C:/Users/kiwun/Documents/ai/VPN/shared/design-tokens.schema.json)

### `infra/`

Contains runtime units and infrastructure assets used by deploy and observability tooling.

Current local authority:

- [infra/portal-node-metrics.service](C:/Users/kiwun/Documents/ai/VPN/infra/portal-node-metrics.service)
- [infra/portal-node-metrics.timer](C:/Users/kiwun/Documents/ai/VPN/infra/portal-node-metrics.timer)
- [docs/operations/deployment-and-access.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/deployment-and-access.md)
- [docs/operations/monitoring-and-visibility.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/monitoring-and-visibility.md)

### `scripts/`

Contains deploy, smoke, audit, migration, node, and release orchestration scripts.

Start from:

- [Repository Map](C:/Users/kiwun/Documents/ai/VPN/docs/developer/repository-map.md)
- [Deployment And Access](C:/Users/kiwun/Documents/ai/VPN/docs/operations/deployment-and-access.md)

### `C:/Users/kiwun/Documents/ai/POKROV-app`

Contains the canonical active client repository target for `Android` and `Windows`.

Workspace lane note:

- `POKROV-app/main` is the only active client development truth and client-doc canon
- expected local checkout path after bootstrap: `C:/Users/kiwun/Documents/ai/POKROV-app`
- the retired `app-next` bootstrap snapshot already landed here and was removed from the active workspace on `2026-04-23`
- new client product-direction, active client-contract work, release metadata, and retained bridge bundle archives now live here

Retained archive references:

- [app-next Bootstrap Summary](C:/Users/kiwun/Documents/ai/VPN/docs/archive/client-lanes/app-next-bootstrap-summary.md)
- [Legacy Bridge Retirement Summary](C:/Users/kiwun/Documents/ai/VPN/docs/archive/client-lanes/legacy-bridge-retirement-summary.md)

## Change-Impact Matrix

When behavior changes, update the matching canonical docs in the same task.

| Change area | Required docs |
| --- | --- |
| Product positioning, trial rules, pricing-facing behavior, branding | `docs/product/portal-vpn-product.md` |
| Backend architecture, API responsibilities, runtime components | `docs/architecture/system-overview.md` |
| App-first session flow, Telegram linking, username sync primary path, node-pool assignment, Telegram reward, support flow | `docs/architecture/app-first-and-bonus-flows.md` |
| Deploy flow, server access, release procedures, secret locations | `docs/operations/deployment-and-access.md` |
| Hostname policy, metrics freshness, node alerts, probe visibility, operator telemetry | `docs/operations/monitoring-and-visibility.md` |
| Repository workflow, tests, local commands, script usage, cleanup policy | `docs/developer/developer-guide.md`, `docs/developer/repository-map.md` |
| User-facing onboarding, support, trial, Telegram bonus, renewal | `docs/user/portal-vpn-user-guide-ru.md` |
| Client UX, client contracts, client roadmap | `C:/Users/kiwun/Documents/ai/POKROV-app/docs/*` for the active client lane; update `docs/archive/client-lanes/*` only when archive-summary labels or evidence notes themselves change |

## Fast Paths

### Backend task

1. Read the must-read set.
2. Inspect `portal_bot/api.py`, `portal_bot/worker.py`, and any touched services/repos.
3. Run focused backend tests.
4. Update canonical docs for any contract or flow changes.

### Web/Admin task

1. Read the must-read set plus `webapp/README.md`.
2. Inspect `webapp/src/app/(dashboard)/admin/`, `webapp/src/lib/api.ts`, and `portal_bot/api.py`.
3. Run `npm.cmd run build` inside `webapp/`.
4. Run `npm.cmd run test:e2e:admin` when browser-visible admin flows or auth gates change.
5. Keep web admin as the primary operator surface; Telegram admin is fallback-only.

### Marketing task

1. Read the must-read set plus product docs.
2. Inspect `marketing/src/`, `shared/copy.ts`, `copy/catalog.ru.json`, `shared/portal-config.ts`, `shared/product-facts.json`, and `shared/public-urls.json`.
3. Keep new public copy and CTA changes centralized in shared/catalog sources.

### Observability / Capacity task

1. Read `deployment-and-access.md` and `monitoring-and-visibility.md`.
2. Inspect `scripts/collect_node_metrics.py`, `infra/portal-node-metrics.service`, and `infra/portal-node-metrics.timer`.
3. Verify `/api/admin/metrics/status` freshness, per-node alerts, and probe-failure fields.
4. Treat hoster CPU warnings as capacity incidents requiring node and control-plane telemetry review.
5. Treat RU probe readiness itself as a tracked dependency. Use `mini` / `RFMINI` as the canonical RU-origin operator sandbox when SSH access is current; if auth or reachability is blocked, report `RU-origin check: BLOCKED_BY_ACCESS`.

### Client task

1. Read the must-read set plus the client docs.
2. Inspect `C:/Users/kiwun/Documents/ai/POKROV-app/` for active client work; inspect `docs/archive/client-lanes/*` or `artifacts/releases/bridge/*` only when the task explicitly needs retired bootstrap, rollback, or archive context.
3. Run targeted Flutter tests or build-smoke commands in the lane that actually changed; for active client work that should be `POKROV-app`.
4. Treat Android release-build localhost/control-surface verification as a release gate, not an optional audit.
5. Sync root canonical docs plus `POKROV-app/docs/*` for active client truth; touch retired client docs only when re-labeling archive or rollback material.

### Docs-only task

1. Update canonical docs first.
2. Archive or relabel stale duplicates.
3. Run link/doc consistency checks.

### Release task

Default definition of done:

- code or config change
- relevant tests or smoke checks
- push
- deploy

If deploy is blocked, document:

- what changed
- what was verified
- what remains blocked
- rollback-safe state

For node-access diagnostics and release handoffs, explicitly distinguish:

- `current-origin check`: from the operator workstation currently in use
- `brain-origin check`: from the control-plane host `82.21.114.104`
- `RU-origin check`: from `mini` or a replacement external RU probe host

## Branch, Worktree, And Promotion Rules

- Keep the root workspace `C:\Users\kiwun\Documents\ai\VPN` on local `master` as the prospective clean baseline for root-repo work
- Treat that root `master` baseline as the place you can resync from; do not turn it into a long-lived scratch branch
- `portal/master` is the policy label for the promoted platform line and normally maps to real `origin/master`
- `POKROV-app/main` is the policy label for the only active client development and promotion line and should map to the real `main` branch in the dedicated `POKROV-app` repository
- archived bridge material is retained for rollback evidence only and must not be treated as an active promotion line
- Do not assume a literal remote alias must exist locally for a policy label to apply
- Local branch or worktree names such as `main` and `portal-app` are optional machine-local aliases only
- If a local alias disagrees with the promotion target, the promotion target wins
- Root-repo changes under `backend`, `webapp`, `marketing`, `shared`, `infra`, `scripts`, and root `docs` promote through the root repo `master` line
- New client product-direction changes and active client-doc changes promote through `POKROV-app/main`
- retained bridge-bundle evidence under `POKROV-app/artifacts/releases/bridge/` is archive material, not a promotion target
- if a deliberate rollback requires touching retired bootstrap or bridge material, document that exception explicitly and do not reinterpret archived inputs as product canon
- When work needs isolation, create or use a dedicated feature branch or sibling worktree instead of reinterpreting baseline or alias branches as source of truth

## Source Of Truth Rules

Production source of truth:

- Postgres from `DATABASE_URL`
- shared hostnames, public copy, locked cross-surface facts, and design contracts from `shared/portal-config.ts`, `shared/copy.ts`, `shared/product-facts.json`, `shared/public-urls.json`, `shared/design-tokens.json`, and `shared/design-tokens.schema.json`

Repository source-of-truth rule:

- if you work on `backend`, `webapp`, `marketing`, root `docs`, `shared`, `infra`, or `scripts`, the canonical git truth is `portal/master`, which is the policy label for the promoted root-repo line and normally maps to real `origin/master`
- if you work on new `Android` or `Windows` client direction, the canonical git truth is `POKROV-app/main`, with expected checkout path `C:/Users/kiwun/Documents/ai/POKROV-app`
- if you work from archived client evidence, treat it as retired bootstrap/archive or rollback/archive reference material only; do not silently use it as active client canon
- root docs in this repository, including `AGENTS.md` and `docs/*`, must land on `portal/master`
- new client docs land on `POKROV-app/docs/*`; keep only short archive summaries in `docs/archive/client-lanes/*` for retired client lanes
- keep the root workspace on local `master` as the clean baseline prospectively; treat `main` and `portal-app` as optional local aliases rather than promotion truth
- do not treat local feature branches, old redirect remotes, deleted bootstrap aliases, or retained bridge archives as competing product truths once `portal/master` and `POKROV-app/main` are updated
- if a task spans the platform repo, the new client repo, and retained archive evidence, update and report each affected repo explicitly instead of assuming one repo transitively updates the others

Not source of truth:

- local SQLite files
- local temp DBs
- archived audit snapshots
- `.next/`, `.dart_tool/`, `node_modules/`, test caches
- `.tmp/`, `.tmp-*`, and other repo-local scratch directories
- old root guides moved into `docs/archive/`

Formal retained evidence:

- `ops-local/` local operator evidence, handoff state, and sensitive operational material that must be retained unless a deliberate evidence-management task says otherwise
- `docs/audit-artifacts/` archived audit evidence that must be retained unless a deliberate archival policy says otherwise

Out-of-repo scope:

- machine-local Android and adb noise such as `C:\Windows\adb.exe`, `%TEMP%`, Android SDK directories, and `~/.android`
- do not treat machine-global tooling state as repo cleanup unless the task explicitly targets machine maintenance

Routine cleanup rule:

- default cleanup should target repo-local generated caches, exported static builds, test artifacts, temporary DBs, and disposable scratch such as `.tmp/` and `.tmp-*`
- use `python scripts/cleanup_inventory.py --class all --dry-run` before cleanup, then apply only the selected classes; never hand-write a broad delete against the repo root
- `external/client-fork/` is retained rollback/reference material; routine cleanup may remove only its generated `.dart_tool`, `build`, and Windows Flutter `ephemeral` outputs
- do not delete `.venv/` or active dependency trees as part of normal cleanup unless you intentionally want a full workspace reset

3x-ui is an execution layer, not the product authority.

## Safe Cleanup Matrix

| Safe to remove | Notes |
| --- | --- |
| `__pycache__/` | Generated Python cache |
| `.pytest_cache/` | Generated pytest cache |
| `portal_api_test_*.db` | Temporary local test DBs |
| `.next/` | Next.js build cache |
| `test-results/` | Generated test artifacts |
| `*.tsbuildinfo` | TypeScript incremental cache |
| `.tmp/`, `.tmp-*` | Repo-local disposable scratch; safe to drop when not intentionally in use |
| local `node_modules/`, `.dart_tool/`, `build/`, `dist/` | Remove only during an intentional workspace reset, not as routine cleanup |
| `external/client-fork/app/.dart_tool`, `external/client-fork/app/build`, `external/client-fork/app/windows/flutter/ephemeral` | Generated legacy-fork caches; removable only through explicit cleanup intent |
| `webapp/out`, `marketing/out` | Generated static export outputs; safe to rebuild, must not be committed |

## Never-Touch Zones

Do not delete, print into markdown, or commit secret material from:

- `portal_bot/.env`
- `VPN NODE SSH KEYS/`
- `secrets for merchant/`
- `external/client-fork/app/windows/`

Do not remove release artifacts from client `out/` unless you know they are obsolete.
Do not delete `external/client-fork` source, bridge evidence, or signing-related subtrees as part of routine cleanup; only generated fork caches listed in the safe matrix are eligible.

Retained evidence and out-of-scope reminder:

- do not treat `ops-local/` as disposable scratch; it is retained local evidence and may also contain sensitive operational material
- do not treat archived evidence under `docs/audit-artifacts/` as disposable by default
- do not sweep machine-global Android or adb state such as `C:\Windows\adb.exe`, `%TEMP%`, SDK directories, or `~/.android` as part of repo cleanup

## Current Telegram Registry

- Main bot: `@pokrov_vpnbot`
- Support bot: `@pokrov_supportbot`
- Feedback bot: `@pokrov_feedbackbot`
- Public channel: `@pokrov_vpn`
- Verified channel URL: `https://t.me/pokrov_vpn/10`

The Telegram bonus flow is live. The bot is an administrator in the configured public channel.

## Reporting Format

For substantial tasks, leave a short handoff with:

- `What I checked`
- `What I found`
- `What I changed`
- `How I verified`
- `What remains / risk`

For node-access diagnostics, also include:

- `current-origin check`
- `brain-origin check`
- `RU-origin check`
