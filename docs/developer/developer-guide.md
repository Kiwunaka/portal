# Developer Guide

Last updated: 2026-03-20

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

## Main Workspaces

### Platform workspace

- [C:/Users/kiwun/Documents/ai/VPN](C:/Users/kiwun/Documents/ai/VPN)

Contains backend, bots, worker jobs, webapp, marketing site, ops scripts, and platform docs.

### Client workspace

- [C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app)

Contains the `POKROV VPN` Flutter fork for Android and Windows.

## Backend Commands

Run focused tests:

```powershell
python -m pytest portal_bot/tests/test_app_first_api.py -q
python -m pytest tests/test_portal_api.py -q
python -m pytest tests/test_worker_retention.py -q
```

Deploy backend:

```powershell
python scripts/remote_deploy_brain_portal_code.py --brain-ip 82.21.114.104 --restart portal-api,portal-bot,portal-helpbot
```

## Frontend Commands

Run inside `webapp/`:

```powershell
npm install
npm run dev
npm run build
```

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

## Generated Artifact Policy

Safe to remove when they are local-generated:

- `__pycache__/`
- `.pytest_cache/`
- `.next/`
- `test-results/`
- `portal_api_test_*.db`
- `*.tsbuildinfo`
- local `node_modules/`, `.dart_tool/`, `build/`, `dist/` if not needed as retained outputs

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
