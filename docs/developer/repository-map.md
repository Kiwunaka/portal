# Repository Map

Last updated: 2026-04-22

## Document Status

This file is living source of truth for repository layout, local authorities, script categories, and test coverage entrypoints.

Legacy filename note:

- some canonical docs still use legacy `portal-vpn-*` path names
- those filenames do not change the current source of truth: the live product is `POKROV`, while `POKROV VPN` remains a legacy identifier only

## Repository Layout

| Path | Purpose | Local authority |
| --- | --- | --- |
| `portal_bot/` | FastAPI backend, Telegram bots, worker, data model, panel sync | root canonical docs plus `portal_bot/api.py`, `portal_bot/app_first_service.py`, `portal_bot/channel_bonus_service.py`, and related tests |
| `webapp/` | Next.js user cabinet and primary admin surface | `webapp/README.md`, `webapp/src/app/(dashboard)/admin/`, `webapp/src/components/admin/users/`, `webapp/src/lib/api.ts`, `webapp/e2e/` |
| `marketing/` | public website, checkout, legal pages, SEO routes and brand assets | root canonical docs plus `marketing/src/`, `marketing/src/app/install/`, `marketing/public/_redirects`, `shared/copy.ts`, `shared/product-facts.json`, `shared/public-urls.json`, `copy/catalog.ru.json` |
| `shared/` | shared host config, locked product facts, design tokens, and public copy for bot/site/app | `shared/portal-config.ts`, `shared/product-facts.json`, `shared/public-urls.json`, `shared/design-tokens.json`, `shared/copy.ts` |
| `infra/` | runtime units and infra assets | `infra/portal-node-metrics.service`, `infra/portal-node-metrics.timer`, `infra/portal-node-observer.service`, `infra/portal-node-observer.timer` |
| `scripts/` | deploy, smoke, node, release, audit, migration scripts | this file and `docs/operations/deployment-and-access.md` |
| `docs/operations/publishing-and-signing-guide.md` | canonical store, certificate, and release artifact guidance | this file and the operations guide itself |
| `docs/developer/orchestration/` | canonical orchestration standard, role contracts, and reusable templates | `docs/developer/orchestration/orchestration-standard.md` |
| `docs/developer/work-orders/` | living wave and work-order execution artifacts | `docs/developer/work-orders/README.md` |
| `docs/` | canonical platform docs plus archive | `docs/README.md` |
| `app-next/` | in-repo bootstrap source workspace for the new client lane | `app-next/docs/README.md`, `app-next/docs/operations/cutover-readiness.md` |
| `external/client-fork/app/` | retained legacy Flutter fork and bridge/hotfix release lane | `external/client-fork/app/docs/README.md`, `external/client-fork/app/scripts/package_windows.ps1`, release asset masters in `external/logogo.png`, `logo/logoclear.svg`, and `logo/logowithtext.svg` |

## Adjacent Repo Boundary

- live new client repo checkout: `C:/Users/kiwun/Documents/ai/POKROV-app`
- `POKROV-app/main` is the new client development truth for this program
- `app-next/` in this repository is the retained bootstrap-source and transition/reference workspace for that repo
- `external/client-fork/app/` remains the bridge/hotfix and current public release-truth lane until formal cutover

## Which Doc Is Authoritative

| Topic | Authoritative doc |
| --- | --- |
| Product rules | [docs/product/portal-vpn-product.md](C:/Users/kiwun/Documents/ai/VPN/docs/product/portal-vpn-product.md) |
| Platform architecture | [docs/architecture/system-overview.md](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/system-overview.md) |
| App-first and Telegram reward flow | [docs/architecture/app-first-and-bonus-flows.md](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/app-first-and-bonus-flows.md) |
| Deploy and access | [docs/operations/deployment-and-access.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/deployment-and-access.md) |
| Monitoring and visibility | [docs/operations/monitoring-and-visibility.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/monitoring-and-visibility.md) |
| Publishing and signing | [docs/operations/publishing-and-signing-guide.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/publishing-and-signing-guide.md) |
| Developer workflow | [docs/developer/developer-guide.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/developer-guide.md) |
| Orchestrated work-order process | [docs/developer/orchestration/orchestration-standard.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/orchestration-standard.md) |
| User journey | [docs/user/portal-vpn-user-guide-ru.md](C:/Users/kiwun/Documents/ai/VPN/docs/user/portal-vpn-user-guide-ru.md) |
| Client-specific contracts | [C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md](C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md) for the live new client lane, [app-next/docs/README.md](C:/Users/kiwun/Documents/ai/VPN/app-next/docs/README.md) as retained bootstrap-source material, and [external/client-fork/app/docs/README.md](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/docs/README.md) for bridge release truth |

## Branches, Worktrees, And Lanes

- `portal/master` is the policy label for the platform lane and maps to `origin/master`
- keep the root workspace `C:/Users/kiwun/Documents/ai/VPN` on `master` as the clean prospective platform baseline for `portal_bot/`, `webapp/`, `marketing/`, `shared/`, `infra/`, root `docs/`, and root `scripts/`
- `POKROV-app/main` is the policy label for the new client development lane and should map to the real `main` branch in the dedicated client repo once bootstrapped locally
- treat `external/client-fork/app/` as the explicit bridge/hotfix and current release-truth lane until formal cutover
- root docs in this repository, including `AGENTS.md` and `docs/*`, land on the platform lane; new client docs belong in `POKROV-app/docs/*` once bootstrapped, while `external/client-fork/app/docs/*` are bridge docs only
- `main`, `portal-app`, and `app-next` are optional machine-local alias names or worktrees only; they are convenience handles, not authoritative roots
- if `app-next` exists, treat it as the temporary bootstrap-source workspace for `POKROV-app`, not as the permanent promotion target
- treat the legacy client checkout nested under the platform workspace as a separate bridge repository with its own promotion path, not as a subtree of `portal/master`

## Current Runtime Contract Pointers

- [docs/architecture/app-first-and-bonus-flows.md](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/app-first-and-bonus-flows.md) is the canonical doc for app-first username sync and free-vs-premium node-pool behavior
- automatic username sync is the primary path; manual username sync remains compatibility/recovery only
- premium-grade access states `trial_premium`, `bonus_premium`, and `paid_unlimited` target all enabled non-free delivery nodes
- free-tier access states `free_monthly` and `free_soft_mode` target only the dedicated `NL-free` node
- smart-connect shortlist logic, RTT upload, and stickiness are part of that same app-first contract and must not be documented separately from the pool rule
- split-tunnel persistence is part of that same contract through `route_mode`, `selected_apps`, `requires_elevated_privileges`, and mirrored `route_policy.*` fields
- additive browser email auth lives under `/api/auth/email/*` and should be documented together with transactional sender identity plus delivery-confirmation/webhook readiness
- support tickets live under `/api/tickets`, `/api/tickets/uploads`, and `/api/tickets/{ticket_id}/messages`; cabinet and admin continue real ticket threads instead of fake live-chat state
- public user-facing version labels stay on `0.x.x-beta`; inherited strings like `2.5.7 dev` are release regressions

## Script Categories

### Deploy and release

- `remote_deploy_brain_portal_code.py`
- `remote_deploy_brain_static_sites.py`
- `remote_brain_apply_release_handoff.py`
- `remote_apply_transport_front.py`
- `remote_install_mini_canary_stack.py`
- `remote_switch_bot_tokens.py`
- `release_orchestrator.py`

### Smoke and verification

- `admin_webapp_smoke.py`
- `android_localhost_audit.py`
- `api_lifecycle_smoke.py`
- `client_security_smoke.py`
- `release_gate_check.py`
- `run_client_release_gate.py`
- `render_ru_probe_report.py`
- `ru_probe_runner.py`
- `remote_transport_front_smoke.py`
- `smoke_client_apps.py`
- `ui_visual_smoke.py`
- `verify_brain_ready.py`
- `check-links.py`

Marketing-specific release checks now live in:

- `scripts/check-links.py`
- `scripts/ui_visual_smoke.py`
- `tests/test_marketing_release_readiness.py`

### Node and panel operations

- `list_nodes.py`
- `node_access.py`
- `remote_brain_nodes_sanity.py`
- `remote_manage_xui.py`
- `remote_sync_users_to_nodes.py`

### Audit and diagnostics

- `audit_node_dns.py`
- `audit_node_dns_matrix.py`
- `collect_node_metrics.py`
- `collect_xray_observer.py`
- `control_plane_drift_report.py`
- `inspect_*`
- `remote_*inspect*`
- `remote_install_node_observer.py`

### Data and migration

- `migrate_sqlite_to_postgres.py`
- `migrate_to_nodes.py`
- `seed_nodes_from_facts.py`
- `sync_shared_surface_facts.py`

## Test Matrix

### Backend and API

- `portal_bot/tests/test_app_first_api.py`
- `tests/test_shared_surface_facts.py`
- `tests/test_portal_api.py`
- `tests/test_api_auth_and_tickets.py`
- `tests/test_api_payments_callbacks.py`
- `tests/test_api_p0_extensions.py`
- `tests/test_smart_connect_api.py`
- `tests/test_network_rollout_api.py`

### Worker and retention

- `tests/test_worker_retention.py`
- `tests/test_free_cycle_service.py`

### Control plane and nodes

- `tests/test_control_panel_free_fallback.py`
- `tests/test_control_plane_drift_report.py`
- `tests/test_nodes_repo_load_aware.py`
- `tests/test_node_access.py`
- `tests/test_panel_client_conflicts.py`
- `tests/test_observer_service.py`
- `tests/test_observer_api.py`
- `tests/test_collect_xray_observer.py`
- `tests/test_predeploy_node_readiness.py`
- `tests/test_remote_apply_transport_front.py`

### Bot, support, and user surfaces

- `tests/test_bot_paywall.py`
- `tests/test_public_copy_guardrails.py`
- `tests/test_tickets_repo.py`
- `tests/test_reviews_username_masking.py`

### Frontend and smoke

- `tests/test_admin_webapp_smoke.py`
- `tests/test_client_security_smoke.py`
- `tests/test_public_copy_guardrails.py`
- `tests/test_ui_visual_smoke.py`
- `webapp/e2e/admin-gate.spec.ts`
- `webapp/e2e/cabinet-flow.spec.ts`

### Client release verification

- `python scripts/client_security_smoke.py`
- `python scripts/run_client_release_gate.py test --suite portal`
- `python scripts/run_client_release_gate.py test --suite full`
- `python scripts/run_client_release_gate.py build --target windows`
- `python scripts/run_client_release_gate.py build --target android-apk`
- `python scripts/run_client_release_gate.py build --target android-aab`
- `python scripts/release_gate_check.py --client-platform-gates windows,android-apk,android-aab`
- `python scripts/android_localhost_audit.py --serial <device-serial> --connect-wait-sec 30 --disconnect-wait-sec 15`
- `Push-Location external/client-fork/app; powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\package_windows.ps1"; Pop-Location`
- focused inner-loop inside `external/client-fork/app/`: `flutter test test/features/portal`
- `release_gate_check.py` requires `ANDROID_AUDIT_SERIAL=<physical-device-serial>` when Android build gates are requested and rejects emulator serials for that public-release path
- Android release-build localhost-listener audit before connect, after connect, and after disconnect
- unauthorized local-client attempt against any proxy, DNS, Clash API, or command surface
- public routing preset smoke for `Global` and `All except RU`
- hidden/internal `Blocked only` verification only after geo assets and DNS behavior are ready
- DNS split and leak validation on Android and Windows
- node-reachability evidence split into `current-origin`, `brain-origin`, and `RU-origin` checks

## Generated Artifact Policy

Treat these as disposable repo-local scratch unless intentionally retained:

- `__pycache__/`
- `.pytest_cache/`
- `.next/`
- `portal_api_test_*.db`
- `*.tsbuildinfo`
- `webapp/out`
- `marketing/out`
- `.tmp/`, `.tmp-*`, screenshots, logcat dumps, XML dumps, and temp runtime snapshots created during local diagnostics

Treat these as workspace dependencies or intentional reset targets, not routine cleanup:

- `node_modules/`
- `.dart_tool/`
- `build/`
- `dist/`
- `.venv/`

Treat these as retained evidence or release assets and preserve them unless you have explicit reason:

- `external/client-fork/app/out/` packaged release bundle
- signing material in `external/client-fork/app/windows/`
- operator evidence in `ops-local/`
- audit evidence in `docs/audit-artifacts/`

Out of scope for repo cleanup:

- Android Studio, adb, emulator, and other machine-local Android noise outside this repository

Client artifact note:

- raw Android outputs live under `external/client-fork/app/build/app/outputs/...`
- raw Windows outputs live under `external/client-fork/app/build/windows/x64/runner/Release/...`
- Android build targets in `scripts/run_client_release_gate.py` refresh `external/client-fork/app/out/` with canonical `apk` and `aab` copies
- Windows packaging still canonicalizes the Windows bundle into `external/client-fork/app/out/`

## Historical Material

Historical root guides now live under:

- [docs/archive/root-guides/](C:/Users/kiwun/Documents/ai/VPN/docs/archive/root-guides)

Do not use them as current operating instructions.
