# Agent Context Map

Last updated: 2026-07-03

This map is an operator navigation layer for agents working in this workspace.
It is not a product, release, design, or API source of truth. When this file and
a canonical document disagree, update or follow the canonical document.

## Source-Of-Truth Ladder

Use this order when building context:

1. `AGENTS.md`, `DESIGN.md`, shared facts/copy/tokens, and the canonical docs
   listed in `docs/README.md`.
2. Current local code, tests, generated type contracts, and the active client
   repo at `C:/Users/kiwun/Documents/ai/POKROV-app`.
3. Current evidence files: release handoff JSON, audit artifacts, work-order
   completion notes, smoke logs, and owner/operator attestations.
4. Historical work orders, old specs, visual references, retained bridge
   bundles, and archive summaries.
5. External model critique or rewrites. Treat this as review input, never
   authority.

Do not promote historical notes, old screenshots, retained bridge material, or
model output above canonical docs and current code.

## Lane Boundary

| Lane | Path | Branch policy | Owns |
| --- | --- | --- | --- |
| Root platform | `C:/Users/kiwun/Documents/ai/VPN` | `master -> origin/master` | backend, bots, webapp, marketing, shared facts/copy/tokens, infra, scripts, root docs |
| Active client | `C:/Users/kiwun/Documents/ai/POKROV-app` | `main -> origin/main` | Android, Windows, client shell, client docs, client release handoff metadata |

Root docs may reference client truth, but new client behavior and active client
docs land in `POKROV-app`. Retired `app-next`, bridge, Karing reopen, clean-room,
old mockup, and old work-order material is archive/reference unless the owner
explicitly reopens that lane.

## Current Status Labels

Keep these labels separate:

- `outside-store public beta GO as of 2026-05-15`: Android and Windows beta was
  authorized with accepted skips.
- `1.0.0-beta implementation/artifacts exist`: repo-side beta artifacts exist,
  but this is not stable `1.0.0`.
- `MANUAL_OWNER_TEST`: physical device, real Telegram user, payment dashboard,
  signing identity, store access, or live account proof is required.
- `OPERATOR_ATTESTED`: owner/operator reported evidence without raw retained
  artifact.
- `SKIPPED_BY_OWNER` or `SKIPPED_BY_OPERATOR`: known accepted skip, not a pass.
- `BLOCKED_BY_ACCESS`: check could not run because required access was missing.

Do not claim stable `1.0.0`, store availability, trusted Windows signing, raw
Android physical-audit proof, production WARP maturity, or RU-origin readiness
without current redacted evidence.

## Evidence Origin Model

Use explicit origin names in audits, release notes, and handoffs:

- `current-origin check`: the workstation/session currently running the check.
- `brain-origin check`: the control-plane host `82.21.114.104`.
- `RU-origin check`: `mini` / `RFMINI` or a replacement external RU probe host.

Never collapse these into a generic "reachable" claim. RU-origin readiness is a
tracked dependency for public hosts, API, and delivery nodes.

## Subsystem Map

| Subsystem | Start with | Then inspect |
| --- | --- | --- |
| Backend/API/bots | `docs/architecture/system-overview.md`, `docs/architecture/app-first-and-bonus-flows.md`, `docs/product/portal-vpn-product.md` | `portal_bot/api.py`, `portal_bot/bot.py`, `portal_bot/helpbot.py`, service modules, migrations, focused tests |
| Web/admin cabinet | `webapp/README.md`, app-first docs, shared facts/copy | `webapp/src/app/(dashboard)/`, `webapp/src/app/(admin)/admin/`, `webapp/src/lib/api.ts`, `webapp/e2e/`, backend API routes |
| Marketing/public | product docs, design docs, shared facts/copy/URLs | `marketing/src/`, `shared/copy.ts`, `copy/catalog.ru.json`, `shared/product-facts.json`, `shared/public-urls.json` |
| Client | `POKROV-app/docs/README.md`, cutover/release docs, app shell tests | `POKROV-app/packages/app_shell/`, `apps/android_shell/`, `apps/windows_shell/`, release artifacts and manifests |
| Ops/release | deployment, monitoring, publishing/signing, release runbooks | `scripts/`, `infra/`, audit artifacts, release handoff JSON, probe reports |
| Design/docs | `DESIGN.md`, design tokens/schema, generated asset policy | affected UI code, screenshots/captures, `docs/design/`, `docs/README.md`, repository map |

## Read Routes By Task

Backend:

1. Read the root must-read docs from `AGENTS.md`.
2. Inspect the concrete API/bot/service files before editing.
3. Use targeted tests first. Broaden when changing shared contracts.
4. Update product, architecture, operations, or user docs when behavior changes.

Web/admin:

1. Read root must-read docs plus `webapp/README.md`.
2. Inspect admin/cabinet routes, `webapp/src/lib/api.ts`, and matching backend
   endpoints.
3. Run build and the focused Playwright suite when browser-visible flows change.

Marketing:

1. Read product, public wording, design, and shared copy/facts docs.
2. Keep user-facing claims centralized in shared/catalog sources.
3. Run SEO/responsive/build checks after public surface changes.

Client:

1. Work in `C:/Users/kiwun/Documents/ai/POKROV-app`.
2. Read client docs before changing app shell, release handoff, or client copy.
3. Run the lane's Flutter/test script; physical Android, signing, store, and real
   account checks remain owner/manual gates unless access is present.

Ops/release:

1. Distinguish current-origin, brain-origin, and RU-origin evidence.
2. Treat payment dashboard, deploy approval, signing, store, live Telegram user,
   and RU probe access as gated resources.
3. If blocked, record the exact gate label instead of inventing proof.

Docs/design:

1. Update canonical docs first.
2. Link or relabel retained history; do not rewrite old evidence as current
   product truth.
3. Generated assets need prompt/reference, source master, dimensions, intended
   surface, review note, and release-scope note before shipping.

## Archive And Do-Not-Use Boundaries

Use as archive/reference only unless explicitly reopened:

- `docs/archive/client-lanes/**`
- retired `app-next` bootstrap summaries
- retained bridge bundles under `POKROV-app/artifacts/releases/bridge/`
- Karing reopen / clean-room gate notes
- old visual explorations, rendered route maps, reference-atlas material
- `docs/superpowers/specs/**` unless promoted into a current work order or
  canonical doc
- old work-order execution files as product authority

Safe pattern: read historical material to understand why, then resolve current
truth through canonical docs, active code, and current tests.

## Context-Budget Workflow

Use the 250k context window as a budget, not a pantry:

1. Start with `rg`, `rg --files`, `git status`, `git diff --stat`, and targeted
   indexes.
2. Read only the relevant canonical docs and local files for the task.
3. Prefer small excerpts with line references over whole-file dumps.
4. Spawn agents for independent domains only: canon/docs, backend, web/marketing,
   client/release, ops/audit. Merge their findings locally.
5. Use embeddings/vector DB later for repeated semantic retrieval across the
   archive. Do not use it as the first authority or as a replacement for `rg`
   plus canonical-doc reads.
6. For expensive external model consults, create a compact packet and run
   `python scripts/agent_context_packet_audit.py <packet.md>` first.

Default answer to "how do we search this repo": `rg` first, targeted reading
second, parallel read-only agents for independent domains third, embeddings once
the stable canon/archive boundary is already documented.
