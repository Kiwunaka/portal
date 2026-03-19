# Developer Guide

Last updated: 2026-03-19

## Purpose

This guide explains how to work safely in the `PORTAL` workspace and which files are current sources of truth.

## Repositories In Practice

### Main workspace

- [C:/Users/kiwun/Documents/ai/VPN](C:/Users/kiwun/Documents/ai/VPN)

Contains:

- backend
- Telegram bots
- worker jobs
- webapp
- marketing site
- deploy scripts
- platform docs

### Client workspace

- [C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app)

Contains:

- `PORTAL VPN` Flutter fork for Android and Windows

## Read Before Editing

Always start with:

- [docs/README.md](C:/Users/kiwun/Documents/ai/VPN/docs/README.md)
- [AGENTS.md](C:/Users/kiwun/Documents/ai/VPN/AGENTS.md)

## Backend Commands

### Run focused tests

```powershell
python -m pytest tests/test_worker_retention.py -q
python -m pytest portal_bot/tests/test_app_first_api.py -q
```

### Deploy backend

```powershell
python scripts/remote_deploy_brain_portal_code.py --brain-ip 82.21.114.104 --restart portal-api,portal-bot,portal-helpbot
```

## Client Commands

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

Whenever behavior changes, update docs in the same task.

Minimum docs to touch when relevant:

- product decisions
- runtime architecture
- deploy flow
- user-facing flow
- client contracts

## Safe Cleanup Targets

Safe to remove:

- `__pycache__/`
- `.pytest_cache/`
- `.next/`
- `test-results/`
- `portal_api_test_*.db`
- other purely generated caches

Not safe to remove without intent:

- `.env` files
- signing materials
- merchant secrets
- SSH key packs
- release artifacts still in use

## Source Of Truth Rules

- Postgres is production truth.
- 3x-ui is an execution layer, not the authoritative product model.
- local SQLite files and archived snapshots are historical only.

## Current Known Caveat

Do not assume Telegram bonus verification is fully operational until a real public channel username is configured.

