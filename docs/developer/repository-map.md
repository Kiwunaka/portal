# Repository Map

Last updated: 2026-04-12

## Document Status

This file is living source of truth for repository layout, local authorities, script categories, and test coverage entrypoints.

Legacy filename note:

- some canonical docs still use legacy `portal-vpn-*` path names
- those filenames do not change the current product brand: the live product is `POKROV VPN`

## Repository Layout

| Path | Purpose | Local authority |
| --- | --- | --- |
| `portal_bot/` | FastAPI backend, Telegram bots, worker, data model, panel sync | root canonical docs plus code |
| `webapp/` | Next.js user cabinet and primary admin surface | `webapp/README.md`, `webapp/src/app/(dashboard)/admin/`, `webapp/src/lib/api.ts`, `webapp/e2e/` |
| `marketing/` | public website, checkout, legal pages, SEO routes and brand assets | root canonical docs plus `marketing/src/`, `marketing/public/`, `shared/copy.ts`, `copy/catalog.ru.json` |
| `shared/` | shared host config and public copy for bot/site/app | `shared/portal-config.ts`, `shared/copy.ts` |
| `infra/` | runtime units and infra assets | `infra/portal-node-metrics.service`, `infra/portal-node-metrics.timer`, `infra/portal-node-observer.service`, `infra/portal-node-observer.timer` |
| `scripts/` | deploy, smoke, node, release, audit, migration scripts | this file and `docs/operations/deployment-and-access.md` |
| `docs/operations/publishing-and-signing-guide.md` | canonical store, certificate, and release artifact guidance | this file and the operations guide itself |
| `docs/` | canonical platform docs plus archive | `docs/README.md` |
| `external/client-fork/app/` | Flutter client fork | `external/client-fork/app/docs/README.md` |

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
| User journey | [docs/user/portal-vpn-user-guide-ru.md](C:/Users/kiwun/Documents/ai/VPN/docs/user/portal-vpn-user-guide-ru.md) |
| Client-specific contracts | [external/client-fork/app/docs/README.md](C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app/docs/README.md) |

## Script Categories

### Deploy and release

- `remote_deploy_brain_portal_code.py`
- `remote_deploy_brain_static_sites.py`
- `remote_brain_apply_release_handoff.py`
- `remote_install_mini_canary_stack.py`
- `remote_switch_bot_tokens.py`
- `release_orchestrator.py`

### Smoke and verification

- `admin_webapp_smoke.py`
- `android_localhost_audit.py`
- `api_lifecycle_smoke.py`
- `client_security_smoke.py`
- `release_gate_check.py`
- `render_ru_probe_report.py`
- `ru_probe_runner.py`
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

## Test Matrix

### Backend and API

- `portal_bot/tests/test_app_first_api.py`
- `tests/test_portal_api.py`
- `tests/test_api_auth_and_tickets.py`
- `tests/test_api_payments_callbacks.py`
- `tests/test_api_p0_extensions.py`

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

### Bot, support, and user surfaces

- `tests/test_bot_paywall.py`
- `tests/test_public_copy_guardrails.py`
- `tests/test_tickets_repo.py`
- `tests/test_reviews_username_masking.py`

### Frontend and smoke

- `tests/test_admin_webapp_smoke.py`
- `tests/test_public_copy_guardrails.py`
- `tests/test_release_orchestrator.py`
- `tests/test_remote_brain_network_probe.py`
- `tests/test_webapp_release_scripts.py`
- `tests/test_ui_visual_smoke.py`
- `webapp/e2e/admin-gate.spec.ts`
- `webapp/e2e/cabinet-flow.spec.ts`
- `webapp/e2e/oidc-fallback.spec.ts`

### Client release verification

- `python scripts/client_security_smoke.py`
- `python scripts/android_localhost_audit.py --serial <device-serial> --connect-wait-sec 30 --disconnect-wait-sec 15`
- `flutter test test/features/portal`
- Android release-build localhost-listener audit before connect, after connect, and after disconnect
- unauthorized local-client attempt against any proxy, DNS, Clash API, or command surface
- routing preset smoke for `Global` and `Все, кроме РФ`
- DNS split and leak validation on Android and Windows
- node-reachability evidence split into `current-origin`, `brain-origin`, and `RU-origin` checks

## Generated Artifact Policy

Treat these as disposable local output unless intentionally retained:

- `__pycache__/`
- `.pytest_cache/`
- `.next/`
- `portal_api_test_*.db`
- `*.tsbuildinfo`
- `webapp/out`
- `marketing/out`

Treat these as workspace dependencies or intentional reset targets, not routine cleanup:

- `node_modules/`
- `.dart_tool/`
- `build/`
- `dist/`
- `.venv/`

Treat these as retained assets and preserve them unless you have explicit reason:

- client `out/`
- signing material in `external/client-fork/app/windows/`
- ops snapshots in `ops-local/`
- audit evidence in `docs/audit-artifacts/`

## Historical Material

Historical root guides now live under:

- [docs/archive/root-guides/](C:/Users/kiwun/Documents/ai/VPN/docs/archive/root-guides)

Do not use them as current operating instructions.
