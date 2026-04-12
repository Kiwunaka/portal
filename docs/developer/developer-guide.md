# Developer Guide

Last updated: 2026-04-12

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
- those files remain authoritative for current `POKROV VPN` behavior until a dedicated rename pass happens

## Read Before Editing

Always start with:

- [docs/README.md](C:/Users/kiwun/Documents/ai/VPN/docs/README.md)
- [AGENTS.md](C:/Users/kiwun/Documents/ai/VPN/AGENTS.md)
- [Repository Map](C:/Users/kiwun/Documents/ai/VPN/docs/developer/repository-map.md)

For client work, also read:

- [external/client-fork/app/docs/README.md](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/docs/README.md)
- [Monitoring And Visibility](C:/Users/kiwun/Documents/ai/VPN/docs/operations/monitoring-and-visibility.md)
- [Publishing And Signing Guide](C:/Users/kiwun/Documents/ai/VPN/docs/operations/publishing-and-signing-guide.md)

For web-admin or marketing work, also read:

- [docs/architecture/system-overview.md](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/system-overview.md)
- [docs/architecture/app-first-and-bonus-flows.md](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/app-first-and-bonus-flows.md)
- [Monitoring And Visibility](C:/Users/kiwun/Documents/ai/VPN/docs/operations/monitoring-and-visibility.md)

## Main Workspaces

### Platform workspace

- [C:/Users/kiwun/Documents/ai/VPN](C:/Users/kiwun/Documents/ai/VPN)

Contains backend, bots, worker jobs, webapp, marketing site, ops scripts, and platform docs.

### Client workspace

- [C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app)

Contains the `POKROV VPN` Flutter fork for Android and Windows.

Current scope note:

- full public `v1` target is Android and Windows
- `iOS` and `macOS` work in this wave is documentation, readiness, and packaging prep only

Shell note:

- prefer `bash` when it is simpler
- use `powershell` when Windows quoting, SSH, or local tool behavior is more reliable there

## Backend Commands

Run focused tests:

```powershell
python -m pytest portal_bot/tests/test_app_first_api.py -q
python -m pytest tests/test_portal_api.py -q
python -m pytest tests/test_worker_retention.py -q
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

- `release_gate_check.py` now runs the canonical public-v1 `pytest` matrix plus client security smoke, lifecycle smoke, link checks, marketing/webapp production builds, and Playwright browser E2E.
- `scripts/release_orchestrator.py --gates-only` is the working one-command entrypoint when you want the documented gate flow without remote deploy steps.
- `python scripts/release_orchestrator.py --gates-only --dry-run` should print the planned local gate step instead of returning an empty pass.
- Add `--brain-ip 82.21.114.104` when you also want the predeploy node-readiness gate included in the same report.
- After client artifacts are published, use `--release-env-file external/client-fork/release-links.env` with `release_orchestrator.py` to sync runtime download URLs before deploy or verify.
- `scripts/client_security_smoke.py` is the repo-level static guardrail for default local-surface settings, RU preset groundwork, and known localhost control paths; it does not replace the required Android release-build reachability audit.
- set `ANDROID_AUDIT_SERIAL=<device-serial>` before `release_gate_check.py` when you want the opt-in adb runtime localhost audit folded into the same report

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
- `npm.cmd run test:e2e` must stay mapped to `playwright test` so the default release gate runs every spec, including `webapp/e2e/oidc-fallback.spec.ts`.
- `tests/test_admin_webapp_smoke.py` is a structure/build smoke, not a replacement for Playwright browser coverage.
- `webapp/e2e/cabinet-flow.spec.ts` covers the non-app user cabinet flow with mocked API contracts.
- `webapp/e2e/oidc-fallback.spec.ts` protects the browser fallback where `app.pokrov.space` returns HTML and the client must retry OIDC start against `api.pokrov.space`.
- admin browser checks should include a narrow mobile or Telegram WebView-like viewport so tap targets, overflow, and modal actions stay usable inside the embedded webapp.
- observer-lite admin checks should cover dashboard summary counts, users-table filter parity, detail diagnostics, and node collector health rendering.
- user-facing config delivery should expose one public `ссылка подключения` via `connect.pokrov.space`; hidden `?format=plain` compatibility must stay out of normal copy and browser flows.

Run inside `marketing/`:

```powershell
npm.cmd run build
python ..\scripts\check-links.py
python ..\scripts\ui_visual_smoke.py
```

Marketing release rules:

- public acquisition CTA must never route users into raw `connect.pokrov.space`
- Android and Windows download CTA should use runtime `APP_*` release URLs when they exist, otherwise the install/docs fallback
- public `Открыть кабинет` CTA should point to `https://app.pokrov.space/`
- pricing CTA should enter through public `/checkout/` with plan context, not directly through `pay.pokrov.space`
- `robots.ts`, `sitemap.ts`, `manifest.ts`, favicon, apple icon, and share-preview assets are part of the release contract, not optional polish

Run inside the client repo:

```powershell
flutter test test/features/portal
flutter build apk --release
flutter build windows --release
```

Client release-gate note:

- Android stays release-blocked until a release-build audit proves there is no unauthenticated localhost proxy, DNS, command, or admin/control surface exposed to other apps, even if APK/AAB build smoke is green
- run `python scripts/client_security_smoke.py` before broader client release verification so default local-surface settings and RU preset groundwork fail fast in CI or local gates
- run `python scripts/android_localhost_audit.py --serial <device-serial> --connect-wait-sec 30 --disconnect-wait-sec 15` on a release-installed Android build for the manual-assisted localhost listener audit
- client verification for this wave must also cover routing presets `Global` and `Все, кроме РФ`, plus DNS split and leak checks on Android and Windows
- when node-reachability evidence is included in a client release handoff, label `current-origin`, `brain-origin`, and `RU-origin` checks separately

For Windows packaging:

```powershell
flutter_distributor package --platform windows --targets msix
```

## Documentation Rules

Whenever behavior, contracts, support flow, or release flow changes, update the canonical docs in the same task.

When public copy, review moderation, or nickname masking changes, also update:

- [tests/test_public_copy_guardrails.py](C:/Users/kiwun/Documents/ai/VPN/tests/test_public_copy_guardrails.py)
- [tests/test_reviews_username_masking.py](C:/Users/kiwun/Documents/ai/VPN/tests/test_reviews_username_masking.py)

Minimum docs to touch when relevant:

- product behavior
- runtime architecture
- app-first / Telegram reward logic
- deploy flow
- developer workflow
- user-facing flow
- client-specific contracts
- publishing and signing guide when distribution, certificates, store status, or artifact names change
- monitoring and visibility guide when hostname policy, probe expectations, support telemetry, or operator visibility changes
- shared copy/catalog sources when public CTA text, checkout hosts, or cross-surface copy changes

## RF Probe And Reserve Commands

Run from the repository root:

```powershell
python scripts/ru_probe_runner.py --reserve-host rf1.pokrov.space --probe-host mini --out ops-local/ru-probe.json
python scripts/render_ru_probe_report.py --input ops-local/ru-probe.json
```

Operational rules:

- `mini` is probe-only for current work
- `mini` may be unavailable; RU probe readiness is its own tracked operational dependency
- if `mini` is unavailable, use Check-Host as coarse RU corroboration and RIPE Atlas as stronger corroboration, but do not relabel that evidence as a true `RU-origin check`
- RU ingress / RF reserve experiments are backlog-only
- do not resume `mini` canary work, evolve the transport matrix, or provision `rf1` unless the product owner explicitly asks to return to that track
- `rf1` is reserve-only for operator and VIP/manual use in phase 1
- keep `rf1` outside the default runtime delivery pool until repeated RU probes confirm stable behavior
- observer-lite phase 1 stays observe-only; do not add throttle or block actions without an explicit product decision

## Generated Artifact Policy

Safe to remove when they are local-generated:

- `__pycache__/`
- `.pytest_cache/`
- `.next/`
- `test-results/`
- `portal_api_test_*.db`
- `*.tsbuildinfo`
- `webapp/out`, `marketing/out` after rebuild or deploy

Only remove these with explicit intent to reset a workspace:

- local `node_modules/`
- `.dart_tool/`
- `build/`
- `dist/`
- `.venv/`

Not safe to remove without intent:

- `.env` files
- signing materials
- merchant secrets
- SSH key packs
- release artifacts still being distributed
- archived evidence that operations still rely on

## Source Of Truth Rules

- Postgres is production truth.
- 3x-ui is an execution layer, not the product authority.
- local SQLite files and archived snapshots are historical only.
- root-level historical guides moved into `docs/archive/` are not current docs.

## Additional Developer Map

For repository layout, script categories, subsystem authorities, and test matrix, use:

- [Repository Map](C:/Users/kiwun/Documents/ai/VPN/docs/developer/repository-map.md)
