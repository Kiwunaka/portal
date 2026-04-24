# Developer Guide

Last updated: 2026-04-24

## Document Status

This file is living source of truth for developer workflow in the `POKROV` workspace.

## Purpose

Use this guide for:

- how to start reading the repo
- which commands to run for focused verification
- when to update docs
- what cleanup is safe

Legacy filename note:

- some canonical docs still use legacy `portal-vpn-*` filenames
- those files remain authoritative for current `POKROV` behavior until a dedicated rename pass happens
- legacy `POKROV VPN` labels in filenames or identifiers do not authorize new direct-meaning `VPN` copy

## Read Before Editing

Always start with:

- [docs/README.md](C:/Users/kiwun/Documents/ai/VPN/docs/README.md)
- [AGENTS.md](C:/Users/kiwun/Documents/ai/VPN/AGENTS.md)
- [Repository Map](C:/Users/kiwun/Documents/ai/VPN/docs/developer/repository-map.md)

For client work, also read:

- [C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md](C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md)
- [C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md](C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md)
- [Monitoring And Visibility](C:/Users/kiwun/Documents/ai/VPN/docs/operations/monitoring-and-visibility.md)
- [Publishing And Signing Guide](C:/Users/kiwun/Documents/ai/VPN/docs/operations/publishing-and-signing-guide.md)

Add these only when needed:

- [app-next Bootstrap Summary](C:/Users/kiwun/Documents/ai/VPN/docs/archive/client-lanes/app-next-bootstrap-summary.md) for historical bootstrap evidence
- [Legacy Bridge Retirement Summary](C:/Users/kiwun/Documents/ai/VPN/docs/archive/client-lanes/legacy-bridge-retirement-summary.md) for rollback or artifact-forensics context

For web-admin or marketing work, also read:

- [docs/architecture/system-overview.md](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/system-overview.md)
- [docs/architecture/app-first-and-bonus-flows.md](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/app-first-and-bonus-flows.md)
- [Monitoring And Visibility](C:/Users/kiwun/Documents/ai/VPN/docs/operations/monitoring-and-visibility.md)
- [webapp/README.md](C:/Users/kiwun/Documents/ai/VPN/webapp/README.md)

For orchestrated multi-step work, also read:

- [docs/developer/orchestration/orchestration-standard.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/orchestration-standard.md)
- [docs/developer/orchestration/README.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/README.md)
- [docs/developer/work-orders/README.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/work-orders/README.md)

## Main Workspaces

### Platform workspace

- [C:/Users/kiwun/Documents/ai/VPN](C:/Users/kiwun/Documents/ai/VPN)

Contains backend, bots, worker jobs, webapp, marketing site, ops scripts, and platform docs.

Platform baseline note:

- prospectively keep the root workspace on `master` as the clean platform baseline
- use feature branches or extra worktrees for platform experiments instead of redefining the root workspace as a different authoritative lane

### New client development repo

- `C:/Users/kiwun/Documents/ai/POKROV-app`

Contains the new canonical client-repo target for `Android` and `Windows`.

Client lane note:

- `POKROV-app/main` is the new client development truth for this rework
- the retired `app-next` bootstrap snapshot already landed here, so new client product-direction work should land here by default

### Historical bootstrap reference

- [app-next Bootstrap Summary](C:/Users/kiwun/Documents/ai/VPN/docs/archive/client-lanes/app-next-bootstrap-summary.md)

Records the retired bootstrap lane that fed the initial `POKROV-app` snapshot.

Reference note:

- treat `app-next` as historical provenance only
- do not route new client product-direction work through the deleted alias or its old docs

### Bridge archive summary

- [Legacy Bridge Retirement Summary](C:/Users/kiwun/Documents/ai/VPN/docs/archive/client-lanes/legacy-bridge-retirement-summary.md)

Tracks the retired bridge lane and the retained mirrored bundle lineage.

Archive note:

- active workflow truth now lives in `POKROV-app`
- use retained bridge artifacts only for rollback-safe evidence, checksum comparison, or release forensics
- do not treat the old bridge repo as a normal completion lane

Current scope note:

- full public `v1` target is Android and Windows
- `iOS` and `macOS` work in this wave is documentation, readiness, and packaging prep only

## Branch, Worktree, And Promotion Policy

- `portal/master` is the policy label used in docs, work orders, and handoffs for the platform lane; it maps to `origin/master`
- `POKROV-app/main` is the policy label for the new client development lane and should map to the `main` branch of the dedicated `POKROV-app` repository
- `portal/master` remains the only canonical git truth for `backend`, `webapp`, `marketing`, root `docs`, `shared`, `infra`, and root `scripts`
- `POKROV-app/main` is the canonical git truth for new `Android` and `Windows` client development work
- root docs in this workspace, including `AGENTS.md` and `docs/*`, always land on the platform lane; new client docs belong in `POKROV-app/docs/*`
- prospectively treat the root workspace on `master` as the clean platform baseline, and promote platform changes back to `origin/master`
- promote new client development changes through `POKROV-app/main`
- archived bridge material does not define a promotion lane
- `main` and `portal-app` are optional machine-local aliases or worktree names only; they are convenience labels, not authoritative roots or promotion targets
- if a task changes the platform repo and the new client repo, push and report each affected canonical branch separately

Shell note:

- prefer `bash` when it is simpler
- use `powershell` when Windows quoting, SSH, or local tool behavior is more reliable there

## Orchestrated Work Orders

Use the orchestration standard when work should survive chat boundaries, needs executor and reviewer separation, or crosses the platform and client lanes.

Canonical paths:

- [docs/developer/orchestration/orchestration-standard.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/orchestration-standard.md)
- [docs/developer/orchestration/roles/](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/roles)
- [docs/developer/orchestration/templates/](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/templates)
- [docs/developer/work-orders/README.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/work-orders/README.md)

Current rules:

- the orchestrator owns WO routing, status, docs impact, and completion judgment
- WOs route by `write-scope`, not by topic
- `portal/master` remains the canonical truth label for the platform lane and maps to `origin/master`
- `POKROV-app/main` remains the canonical truth label for the new client development lane
- any retained bridge evidence must be called out explicitly as archive evidence rather than as a live repo lane
- mixed WOs must preserve separate git evidence for the platform lane and the new client lane when each is touched
- the executor does not self-close the WO
- reviewers should run with fresh context
- a green automated check does not close a WO when manual checks, deploy steps, Android localhost audit, or origin evidence still remain open
- live execution artifacts belong under `docs/developer/work-orders/`; reusable templates belong under `docs/developer/orchestration/templates/`

## Current Runtime Contract Reminders

- automatic username sync is the primary identity-sync path across app-first, web-login, and Telegram-link flows; manual username sync is compatibility/recovery tooling only
- premium-grade access states `trial_premium`, `bonus_premium`, and `paid_unlimited` use the paid pool, which means all enabled non-free delivery nodes
- free-tier access states `free_monthly` and `free_soft_mode` use the free pool, which means the dedicated `NL-free` node only
- smart-connect shortlist selection stays inside those pool boundaries; premium profiles can expose up to `5` eligible non-free nodes, while free stays `NL-free` only
- the client-side RTT upload contract is `POST /api/client/nodes/latency-samples`; it stores install-scoped diagnostic evidence and does not bypass `UserNode` pinning
- the persisted split-tunnel contract is backend-owned through `route_mode`, `selected_apps`, `requires_elevated_privileges`, and mirrored `route_policy.*` fields; do not document it as client-only local state
- additive browser email auth lives under `/api/auth/email/*`, but public docs and entry copy must keep it marked `soon` until transactional sender identity, delivery confirmation, and the public launch path are live
- before that launch, web and cabinet should expose a truthful unavailable or `soon` state instead of acting like verify or reset mail works
- support is a real `/api/tickets*` contract, including `/api/tickets/uploads` for authenticated browser attachments; do not describe it as an imaginary live chat
- transport rollout is additive: `legacy_reality_fallback` stays the baseline until the canary completes, while `grpc_443_primary` is the allowlisted app-first primary for rollout cohorts
- `reserve_xhttp_cdn` is the dormant reserve transport profile; it stays disabled by default and is only for explicit allowlisted fallback
- `network_rollout_config` is the operator-owned rollout policy for transport, DNS, routing, and operator-lab allowlists; treat it as the source of truth for app-managed policy resolution
- node shaping is repo-truth driven through `infra/node-qdisc-profiles.json` and the `remote_apply_node_qdisc.py` / `remote_node_qdisc_smoke.py` helpers, so treat qdisc changes as part of release verification instead of an informal operator tweak
- public user-facing version labels across app, web, cabinet, and release notes must stay on `0.x.x-beta`; treat inherited strings like `2.5.7 dev` as regressions
- when reporting node reachability during rollout work, keep `current-origin check`, `brain-origin check`, and `RU-origin check` separate instead of collapsing them into one status
- versioned release metadata belongs under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/<version>/` for retained bridge lineage and under `.../artifacts/releases/pokrov-app/<version>/` for canonical client-lane bundles
- the stable root-orchestrator pointer is `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/release-handoff.json` when that file is maintained

## Backend Commands

Run focused tests:

```powershell
python -m pytest portal_bot/tests/test_app_first_api.py -q
python -m pytest tests/test_portal_api.py -q
python -m pytest tests/test_worker_retention.py -q
python -m pytest tests/test_smart_connect_api.py tests/test_network_rollout_api.py -q
python -m pytest tests/test_api_auth_and_tickets.py -q
python -m pytest tests/test_remote_apply_transport_front.py -q
python -m pytest tests/test_observer_service.py tests/test_observer_api.py tests/test_collect_xray_observer.py tests/test_predeploy_node_readiness.py -q
python scripts/api_lifecycle_smoke.py
python -m unittest tests.test_node_dataplane_probe tests.test_ru_probe_runner tests.test_render_ru_probe_report
```

Full public-v1 release gate from a fresh shell:

```powershell
python scripts/release_gate_check.py
python scripts/release_orchestrator.py --gates-only
```

Notes:

- `release_gate_check.py` now runs the canonical public-v1 `pytest` matrix plus admin/auth regression, client security smoke, `python scripts/run_client_release_gate.py test --suite full`, lifecycle smoke, link checks, marketing/webapp production builds, admin webapp smoke, Playwright browser E2E, and UI visual smoke.
- `release_gate_check.py --quick` swaps the default full client Flutter suite for `python scripts/run_client_release_gate.py test --suite portal`.
- on Windows, `release_gate_check.py` injects a repo-local disposable `--basetemp` for every `python -m pytest ...` subprocess so release gates do not inherit a broken global `%TEMP%\\pytest-of-<user>\\pytest-current` cleanup tail from the workstation.
- add `--client-platform-gates windows,android-apk,android-aab` or set `CLIENT_PLATFORM_GATES` when you want the same report to include artifact-producing client builds.
- once `CLIENT_PLATFORM_GATES` includes `android-apk` or `android-aab`, `release_gate_check.py` requires `ANDROID_AUDIT_SERIAL` and treats emulator serials as preflight-only, not as a valid public-release audit.
- `scripts/release_orchestrator.py --gates-only` is the one-command entrypoint when you want the documented gate flow without remote deploy, release handoff sync, or post-deploy verify steps.
- the full `scripts/release_orchestrator.py` path can chain local gates, optional `APP_*` sync, backend deploy, static deploy, optional rollout helpers, and brain-local verify, but it still does not publish binaries or replace separate external-origin evidence
- latest verified local run: `python scripts/release_orchestrator.py --gates-only` exited `0` on `2026-04-13`; see `docs/audit-artifacts/release_gate_report.md` for the current local gate snapshot.
- Add `--brain-ip 82.21.114.104` when you also want the predeploy node-readiness gate included in the same report.
- `--release-metadata-file` and `--release-env-file` cannot be combined with `--gates-only`; after client artifacts are published, use the full `release_orchestrator.py` flow to sync runtime download URLs before deploy or verify.
- `scripts/client_security_smoke.py` is the repo-level static guardrail for the `POKROV-app` seed contract, Android host manifest, runtime-artifact pin, and Windows release-seed expectations; it does not replace the required Android release-build reachability audit.
- set `ANDROID_AUDIT_SERIAL=<device-serial>` before `release_gate_check.py` when you want the opt-in adb runtime localhost audit folded into the same report
- set `ANDROID_AUDIT_CONNECT_WAIT_SEC` and `ANDROID_AUDIT_DISCONNECT_WAIT_SEC` when that adb localhost audit needs non-default timing
- without `ANDROID_AUDIT_SERIAL`, a green repo/static gate run still does not authorize Android public publication
- an emulator-backed `ANDROID_AUDIT_SERIAL` run is useful for adb preflight, but the final Android public-release gate still requires `python scripts/android_localhost_audit.py` on physical hardware

Deploy backend:

```powershell
python scripts/remote_deploy_brain_portal_code.py --brain-ip 82.21.114.104 --restart portal-api,portal-bot,portal-helpbot
python scripts/remote_install_node_observer.py --brain-ip 82.21.114.104 --node-code pl --run-now
```

## Frontend Commands

Run inside `webapp/`:

```powershell
npm install
npm.cmd run dev
npm.cmd run build
npm.cmd run test:e2e
npm.cmd run test:e2e:admin
```

Notes:

- `webapp` owns the primary admin surface.
- Real browser checks live under `webapp/e2e/`.
- `tests/test_admin_webapp_smoke.py` is a structure/build smoke, not a replacement for Playwright browser coverage.
- `webapp/e2e/cabinet-flow.spec.ts` covers the non-app user cabinet flow with mocked API contracts.
- `npm.cmd run test:e2e` now builds the static export, then serves `webapp/out` through `webapp/scripts/serve_export.py` on port `3102`, so the main browser gate matches the export-style deploy surface instead of `next dev`.
- `npm.cmd run test:e2e:admin` uses the same build-plus-export-server flow on port `3101`, which removes the standalone admin timeout that came from cold `next dev` bootstrap and HMR reload churn.
- `npm.cmd run test:e2e:cabinet` remains the quicker inner-loop command when you only want that spec and do not need the full release-style export gate.
- the release-style Playwright scripts still clear a stale port owner first and disable server reuse so local browser checks do not inherit a leftover export server or stale HMR session.
- admin browser checks should include a narrow mobile or Telegram WebView-like viewport so tap targets, overflow, and modal actions stay usable inside the embedded webapp.
- observer-lite admin checks should cover dashboard summary counts, users-table filter parity, detail diagnostics, and node collector health rendering.
- user-facing config delivery should expose one public `ссылка подключения` via `connect.pokrov.space`; hidden `?format=plain` compatibility must stay out of normal copy and browser flows.

Run inside `marketing/`:

```powershell
npm.cmd run check:seo
npm.cmd run build
python ..\scripts\check-links.py
python ..\scripts\ui_visual_smoke.py
```

Marketing release rules:

- public acquisition CTA must never route users into raw `connect.pokrov.space`
- public acquisition CTA priority is checkout-first on marketing surfaces; install help and cabinet-open links are secondary intent-driven exits
- authenticated WebApp download CTA should use `/api/client/apps` runtime URLs first, then the `APP_*` / docs fallback
- marketing download CTA is build-time and must be rebuilt/redeployed when `NEXT_PUBLIC_APP_*` public URLs change
- public `Открыть кабинет` CTA should point to `https://app.pokrov.space/`
- pricing CTA should enter through public `/checkout/` with plan context, not directly through `pay.pokrov.space`
- public-facing marketing and cabinet copy should stay in calm user language rather than transport jargon, raw profile labels, or operator shorthand
- `robots.ts`, `sitemap.ts`, `manifest.ts`, favicon, apple icon, and share-preview assets are part of the release contract, not optional polish

## Frontend Surface Map

After the current premium/SEO/copy pass, keep this split explicit:

- `marketing/` owns the public homepage, checkout-first `/checkout/`, install help, offer/privacy pages, indexable SEO landings, and site metadata surfaces
- `webapp/` owns `app.pokrov.space` entry, dashboard, subscription, devices, statistics, support, downloads, redeem, checkout continuation, and admin
- `connect.pokrov.space` is config delivery only and must not be treated as a public acquisition page
- when a task spans both surfaces, verify the handoff `pokrov.space -> app.pokrov.space` instead of reviewing each side in isolation

Current platform-owned client gate verification from the repository root:

```powershell
python scripts/run_client_release_gate.py preflight
python scripts/run_client_release_gate.py test --suite portal
python scripts/run_client_release_gate.py test --suite full
python scripts/run_client_release_gate.py build --target windows
python scripts/run_client_release_gate.py build --target android-apk
python scripts/run_client_release_gate.py build --target android-aab
```

Client release-gate note:

- Android stays release-blocked until a release-build audit proves there is no unauthenticated localhost proxy, DNS, command, or admin/control surface exposed to other apps
- run `python scripts/client_security_smoke.py` before broader client release verification so the `POKROV-app` seed contract, Android host manifest, runtime-artifact pin, and Windows release seed fail fast in CI or local gates
- `run_client_release_gate.py` now targets `C:/Users/kiwun/Documents/ai/POKROV-app` by default and fails fast when that workspace is missing or incomplete
- `python scripts/run_client_release_gate.py preflight` verifies the `POKROV-app` seed workspace layout, wrapper scripts, host shells, and seed configs before client gates run
- `python scripts/run_client_release_gate.py test --suite full` delegates to `C:/Users/kiwun/Documents/ai/POKROV-app/scripts/run-tests.ps1`
- `python scripts/run_client_release_gate.py test --suite portal` bootstraps the workspace and runs the narrower Flutter lane in `packages/app_shell`, `apps/android_shell`, and `apps/windows_shell`
- raw Android outputs for the wrapper now live under `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/build/app/outputs/...`
- the Windows wrapper now delegates to `C:/Users/kiwun/Documents/ai/POKROV-app/scripts/build-windows-release.ps1 -SyncRuntime -SkipTests -SkipAnalyze` and expects the unsigned zip plus manifest under `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/build/release_bundle/`
- retained bridge bundles live under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/`; they are archive evidence, not the active release lane
- run `python scripts/android_localhost_audit.py --serial <device-serial> --connect-wait-sec 30 --disconnect-wait-sec 15` on a release-installed Android build for the manual-assisted localhost listener audit
- if you fold Android build targets into `release_gate_check.py`, export `ANDROID_AUDIT_SERIAL=<physical-device-serial>` first or let the gate fail loudly instead of treating a repo/static-only run as release-ready
- public client verification for this wave must cover routing presets `Global` and `All except RU`, plus DNS split and leak checks on Android and Windows
- `Blocked only` remains hidden or internal until geo assets, rules, and DNS behavior are ready for honest public verification
- when node-reachability evidence is included in a client release handoff, label `current-origin`, `brain-origin`, and `RU-origin` checks separately

For Windows packaging:

```powershell
flutter_distributor package --platform windows --targets msix
```

Windows packaging guardrails:

- keep `windows/packaging/exe/make_config.yaml` on a canonical public publisher URL such as `https://pokrov.space/`, not a GitHub repository URL
- public and packaged `MSIX` identity fields such as display name, identity name, publisher display name, description, executable naming, and protocol activation must resolve to `POKROV` / `pokrov`
- do not ship legacy `POKROV VPN`, `Pokrov.Vpn`, or `hiddify` residue in packaged Windows public or hidden identity fields
- release-facing raster branding should regenerate from [external/logogo.png](C:/Users/kiwun/Documents/ai/VPN/external/logogo.png), while vector branding should regenerate from [logo/logoclear.svg](C:/Users/kiwun/Documents/ai/VPN/logo/logoclear.svg) and [logo/logowithtext.svg](C:/Users/kiwun/Documents/ai/VPN/logo/logowithtext.svg)

## Documentation Rules

Whenever behavior, contracts, support flow, release flow, cabinet IA, or public CTA priority changes, update the canonical docs in the same task.

When a task touches transport catalog behavior, `network_rollout_config`, or node shaping, keep the rollout docs aligned in the same change set:

- [docs/architecture/system-overview.md](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/system-overview.md)
- [docs/architecture/app-first-and-bonus-flows.md](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/app-first-and-bonus-flows.md)
- [docs/operations/deployment-and-access.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/deployment-and-access.md)
- [docs/operations/monitoring-and-visibility.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/monitoring-and-visibility.md)
- [docs/developer/developer-guide.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/developer-guide.md)

If code is still in flight, document only the confirmed surfaces and routes that already exist in:

- `marketing/src/app/`
- `webapp/src/app/`
- `shared/copy.ts`
- `shared/portal-config.ts`
- `shared/product-facts.json`
- `shared/public-urls.json`
- `shared/design-tokens.json`

Do not document speculative routes, unfinished CTA behavior, or future release promises just because the copy pass has started.

When public copy, review moderation, or nickname masking changes, also update:

- [tests/test_public_copy_guardrails.py](C:/Users/kiwun/Documents/ai/VPN/tests/test_public_copy_guardrails.py)
- [tests/test_reviews_username_masking.py](C:/Users/kiwun/Documents/ai/VPN/tests/test_reviews_username_masking.py)

Current redesign guardrails:

- public feed defaults in `portal_bot/api.py` should use human Russian copy and avoid raw node, transport, checkout, and direct-meaning `VPN` wording
- public aggregate counters should expose additive truth metadata instead of forcing UI to invent whether the number is live, estimated, or account-derived
- user-facing Russian docs should avoid public jargon such as direct-meaning `VPN`, `checkout`, `fallback`, `managed premium`, `trial`, `scope`, raw `SNI`/`DNS`, and consumer-facing `узлы`
- governed catalog copy must not reintroduce old network or premium subtitle lines
- trial copy must stay on `5 days`; older longer-duration trial copy is stale
- first-layer app copy must stay consumer-language only and hide transport, runtime, local-control, hostname, port, and raw subscription terms
- local dev admin checks may seed `portal_web_session_token` in Playwright, but production UI must still require a real cabinet session before `/admin/*` opens

Focused redesign guardrail checks:

```powershell
python -m pytest tests/test_public_copy_guardrails.py tests/test_redesign_spine.py -q
cd webapp; npm.cmd run test:e2e:admin -- --grep "requires a real cabinet session"
cd C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell; flutter test test/pokrov_seed_app_test.dart --plain-name "first-layer app shell copy hides transport and control terms"
```

Minimum docs to touch when relevant:

- product behavior
- runtime architecture
- app-first / Telegram reward / username sync / node-pool logic
- deploy flow
- developer workflow
- user-facing flow
- client-specific contracts
- publishing and signing guide when distribution, certificates, store status, or artifact names change
- monitoring and visibility guide when hostname policy, probe expectations, support telemetry, or operator visibility changes
- shared copy/catalog sources when public CTA text, checkout hosts, cross-surface copy, or cabinet/nav labels change

Shared-surface rule:

- treat `shared/copy.ts`, `copy/catalog.ru.json`, `shared/product-facts.json`, `shared/public-urls.json`, and `shared/design-tokens.json` as the only governed source set for cross-surface copy, host, product, and design facts
- TypeScript reads those files directly through `shared/*.ts` adapters
- Python reads those files through `portal_bot/shared_surface_facts.py`
- `scripts/sync_shared_surface_facts.py` now syncs those facts into `C:/Users/kiwun/Documents/ai/POKROV-app/config/product-contract.seed.json`, `config/runtime-profile.seed.json`, and `config/platform-matrix.seed.json` by default
- the legacy bridge Dart file remains compatibility-only through `scripts/sync_shared_surface_facts.py --target-lane bridge` or `--target-lane both`
- release handoff metadata now belongs under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/`; the standard operator input is the versioned `release-links.env`, while stamped JSON manifests in `release-manifests/` remain supporting evidence unless a separate canonical metadata file is intentionally prepared

## RF Probe And Reserve Commands

Run from the repository root:

```powershell
python scripts/ru_probe_runner.py --reserve-host rf1.pokrov.space --probe-host mini --out ops-local/ru-probe.json
python scripts/render_ru_probe_report.py --input ops-local/ru-probe.json
```

Operational rules:

- `mini` is probe-only for current work
- `mini` may be unavailable; RU probe readiness is its own tracked operational dependency
- RU ingress / RF reserve experiments are backlog-only
- do not resume `mini` canary work, evolve the transport matrix, or provision `rf1` unless the product owner explicitly asks to return to that track
- `rf1` is reserve-only for operator and VIP/manual use in phase 1
- keep `rf1` outside the default runtime delivery pool until repeated RU probes confirm stable behavior
- observer-lite phase 1 stays observe-only; do not add throttle or block actions without an explicit product decision

## Generated Artifact Policy

Disposable repo-local scratch:

- `__pycache__/`
- `.pytest_cache/`
- `.next/`
- `test-results/`
- `portal_api_test_*.db`
- `*.tsbuildinfo`
- `webapp/out`, `marketing/out` after rebuild or deploy
- `.tmp/`, `.tmp-*`, screenshots, logcat dumps, XML dumps, and temp runtime snapshots created for local debugging or release checks

Only remove these with explicit intent to reset a workspace:

- local `node_modules/`
- `.dart_tool/`
- `build/`
- `dist/`
- `.venv/`

Retained evidence and release bundles:

- `ops-local/` when it contains operator evidence or probe snapshots
- `docs/audit-artifacts/`
- `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/` retained bridge bundle archive
- `.env` files
- signing materials
- merchant secrets
- SSH key packs
- release artifacts still being distributed

Out of scope for routine repo cleanup:

- Android Studio, adb, emulator, and other machine-local Android noise outside this repository

## Source Of Truth Rules

- Postgres is production truth.
- 3x-ui is an execution layer, not the product authority.
- local SQLite files and archived snapshots are historical only.
- root-level historical guides moved into `docs/archive/` are not current docs.

## Additional Developer Map

For repository layout, script categories, subsystem authorities, and test matrix, use:

- [Repository Map](C:/Users/kiwun/Documents/ai/VPN/docs/developer/repository-map.md)
