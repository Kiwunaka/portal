# Developer Guide

Last updated: 2026-03-31

## Document Status

This file is living source of truth for developer workflow in the `POKROV` workspace.

## Purpose

Use this guide for:

- how to start reading the repo
- which commands to run for focused verification
- when to update docs
- what cleanup is safe

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

## Backend Commands

Run focused tests:

```powershell
python -m pytest portal_bot/tests/test_app_first_api.py -q
python -m pytest tests/test_portal_api.py -q
python -m pytest tests/test_worker_retention.py -q
python -m pytest tests/test_observer_service.py tests/test_observer_api.py tests/test_collect_xray_observer.py tests/test_predeploy_node_readiness.py -q
python -m unittest tests.test_node_dataplane_probe tests.test_ru_probe_runner tests.test_render_ru_probe_report
```

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
npm.cmd run test:e2e:admin
```

Notes:

- `webapp` owns the primary admin surface.
- Real browser checks live under `webapp/e2e/`.
- `tests/test_admin_webapp_smoke.py` is a structure/build smoke, not a replacement for Playwright browser coverage.
- admin browser checks should include a narrow mobile or Telegram WebView-like viewport so tap targets, overflow, and modal actions stay usable inside the embedded webapp.
- observer-lite admin checks should cover dashboard summary counts, users-table filter parity, detail diagnostics, and node collector health rendering.

Run inside the client repo:

```powershell
flutter test test/features/portal
flutter build apk --release
flutter build windows --release
```

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
- local `node_modules/`, `.dart_tool/`, `build/`, `dist/` if not needed as retained outputs
- `webapp/out`, `marketing/out` after rebuild or deploy

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
