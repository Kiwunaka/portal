# Repository Map

Last updated: 2026-07-06

## Document Status

This file is living source of truth for repository layout, local authorities, script categories, and test coverage entrypoints.

Legacy filename note:

- some canonical docs still use legacy `portal-vpn-*` path names
- those filenames do not change the current source of truth: the live product is `POKROV`, while `POKROV VPN` remains a legacy identifier only

## Repository Layout

| Path | Purpose | Local authority |
| --- | --- | --- |
| `portal_bot/` | FastAPI backend, Telegram bots, worker, data model, panel sync | root canonical docs plus `portal_bot/api.py`, `portal_bot/app_first_service.py`, `portal_bot/channel_bonus_service.py`, `portal_bot/warp_service.py`, and related tests |
| `webapp/` | Next.js continuation-first cabinet with visible IA `Главная / Доступ / Помощь / Аккаунт`, task/detail routes for entry, devices, statistics, downloads, redeem, support threads/legal docs, checkout continuation, and retained legacy admin routes until `adminapp/` parity deletion | `webapp/README.md`, `webapp/src/app/(dashboard)/` for the cabinet route group, `webapp/src/app/(admin)/admin/` for the temporary parity fallback operator route group, `webapp/src/lib/api.ts`, `webapp/e2e/`, `webapp/scripts/serve_export.py` |
| `adminapp/` | standalone Next.js operator app for `https://admin.pokrov.space/`, using shared POKROV design tokens, TanStack Table, Recharts, first-party ops APIs, provider quotas, durable alerts, and existing admin endpoints for parity modules | `adminapp/README.md`, `adminapp/src/app/`, `adminapp/src/components/`, `adminapp/src/lib/api.ts`, `portal_bot/api.py`, `tests/test_admin_ops_api.py` |
| `marketing/` | app-first public website, checkout continuation, legal pages, SEO routes, install help, and brand assets | root canonical docs plus `marketing/src/`, `marketing/src/app/install/`, `marketing/public/_redirects`, `shared/copy.ts`, `shared/product-facts.json`, `shared/public-urls.json`, `copy/catalog.ru.json` |
| `shared/` | shared host config, locked product facts, design tokens, token schema, and governed public copy for bot/site/app | `shared/portal-config.ts`, `shared/product-facts.json`, `shared/public-urls.json`, `shared/design-tokens.json`, `shared/design-tokens.schema.json`, `shared/copy.ts` |
| `infra/` | runtime units and infra assets | `infra/portal-node-metrics.service`, `infra/portal-node-metrics.timer`, `infra/portal-node-observer.service`, `infra/portal-node-observer.timer` |
| `scripts/` | deploy, smoke, node, release, audit, migration scripts | this file and `docs/operations/deployment-and-access.md` |
| `docs/developer/pokrov-canonical-feature-tracker.*` | canonical feature and user-story status table for bot, backend, webapp/admin, marketing, scripts, and client app behavior | `docs/developer/pokrov-canonical-feature-tracker.md`, `docs/developer/pokrov-canonical-feature-tracker.csv`, and the sidecar audit files listed in this map |
| `docs/operations/publishing-and-signing-guide.md` | canonical store, certificate, and release artifact guidance | this file and the operations guide itself |
| `docs/developer/orchestration/` | canonical orchestration standard, WO authoring rules, flow-state rules, context/cost harness rules, role contracts, and reusable templates | `docs/developer/orchestration/orchestration-standard.md`, `docs/developer/orchestration/wo-authoring-guide.md`, `docs/developer/orchestration/flow-state.md`, `docs/developer/orchestration/context-cost-harnesses.md` |
| `docs/developer/work-orders/` | living wave and work-order execution artifacts | `docs/developer/work-orders/README.md` |
| `docs/superpowers/specs/` | retained implementation specs | historical/reference only unless copied into a current WO or canonical doc |
| `docs/archive/plans/`, `docs/archive/design-plans/`, `docs/archive/superpowers-plans/` | completed planning packets and design plans | archive/reference only; not current work queues |
| `reference-atlas/` | retained local design reference atlas | design-reference history only; not a production surface |
| `docs/` | canonical platform docs plus archive | `docs/README.md` |
| `docs/archive/client-lanes/` | short historical summaries for retired client lanes | `docs/archive/client-lanes/README.md` |
| `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/` | retained bridge bundle lineage and handoff evidence archive | versioned bundle folders plus `release-manifests/` when present |

## Adjacent Repo Boundary

- live new client repo checkout: `C:/Users/kiwun/Documents/ai/POKROV-app`
- `POKROV-app/main` is the new client development truth for this program
- retired bootstrap provenance is summarized in `docs/archive/client-lanes/app-next-bootstrap-summary.md`
- retained bridge bundle lineage lives under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/`

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
| Agent context navigation | [docs/developer/agent-context-map.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/agent-context-map.md) |
| OpenAI operator assistants | [docs/developer/openai-operator-assistants.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/openai-operator-assistants.md) |
| Orchestrated work-order process | [docs/developer/orchestration/orchestration-standard.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/orchestration-standard.md), [docs/developer/orchestration/wo-authoring-guide.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/wo-authoring-guide.md), [docs/developer/orchestration/flow-state.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/flow-state.md), and [docs/developer/orchestration/context-cost-harnesses.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/orchestration/context-cost-harnesses.md) |
| User journey | [docs/user/portal-vpn-user-guide-ru.md](C:/Users/kiwun/Documents/ai/VPN/docs/user/portal-vpn-user-guide-ru.md) |
| Design system | [DESIGN.md](C:/Users/kiwun/Documents/ai/VPN/DESIGN.md), [shared/design-tokens.json](C:/Users/kiwun/Documents/ai/VPN/shared/design-tokens.json), [shared/design-tokens.schema.json](C:/Users/kiwun/Documents/ai/VPN/shared/design-tokens.schema.json), and [docs/design/design-system-sync.md](C:/Users/kiwun/Documents/ai/VPN/docs/design/design-system-sync.md) |
| Open Beta v4 release scope | [docs/product/public-beta-prd.md](C:/Users/kiwun/Documents/ai/VPN/docs/product/public-beta-prd.md) and [docs/operations/public-beta-release-runbook.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/public-beta-release-runbook.md) |
| Payment provider readiness | [docs/product/payment-and-access-key-contract.md](C:/Users/kiwun/Documents/ai/VPN/docs/product/payment-and-access-key-contract.md) and [docs/operations/lavatop-payment-operations.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/lavatop-payment-operations.md) |
| Client-specific contracts | [C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md](C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md) for the live new client lane, plus [app-next Bootstrap Summary](C:/Users/kiwun/Documents/ai/VPN/docs/archive/client-lanes/app-next-bootstrap-summary.md) and [Legacy Bridge Retirement Summary](C:/Users/kiwun/Documents/ai/VPN/docs/archive/client-lanes/legacy-bridge-retirement-summary.md) for archive evidence only |

## Branches, Worktrees, And Lanes

- `portal/master` is the policy label for the platform lane and maps to `origin/master`
- keep the root workspace `C:/Users/kiwun/Documents/ai/VPN` on `master` as the clean prospective platform baseline for `portal_bot/`, `webapp/`, `marketing/`, `shared/`, `infra/`, root `docs/`, and root `scripts/`
- `POKROV-app/main` is the policy label for the new client development lane and should map to the real `main` branch in the dedicated client repo once bootstrapped locally
- root docs in this repository, including `AGENTS.md` and `docs/*`, land on the platform lane; new client docs belong in `POKROV-app/docs/*` once bootstrapped
- `main` and `portal-app` are optional machine-local alias names or worktrees only; they are convenience handles, not authoritative roots
- retired bootstrap provenance and retained bridge evidence are archive inputs, not promotion targets

## Current Runtime Contract Pointers

- [docs/architecture/app-first-and-bonus-flows.md](C:/Users/kiwun/Documents/ai/VPN/docs/architecture/app-first-and-bonus-flows.md) is the canonical doc for app-first username sync and free-vs-premium node-pool behavior
- automatic username sync is the primary path; manual username sync remains compatibility/recovery only
- premium-grade access states `trial_premium`, `bonus_premium`, and `paid_unlimited` target all enabled non-free delivery nodes
- free-tier access states `free_monthly` and `free_soft_mode` target only the dedicated `NL-free` node
- smart-connect candidates/select logic, RTT telemetry, capacity-aware ranking, and stickiness are part of that same app-first contract and must not be documented separately from the pool rule
- `UserNode` is provisioning/history state for this contract; premium-grade candidate selection comes from the paid pool and capacity policy rather than old per-user pinning
- split-tunnel persistence is part of that same contract through `route_mode`, `selected_apps`, `requires_elevated_privileges`, and mirrored `route_policy.*` fields
- additive browser email auth lives under `/api/auth/email/*`, but current canon keeps it marked `soon` until transactional sender identity plus delivery-confirmation/webhook readiness and the public launch path are live
- support tickets live under `/api/tickets`, `/api/tickets/uploads`, and `/api/tickets/{ticket_id}/messages`; cabinet and admin continue real ticket threads instead of fake live-chat state. The optional support AI helper is server-side for `portal-api` and `@pokrov_supportbot`, uses `portal_bot/support_ai_service.py` plus `shared/support-ai-knowledge.json`, and stores model hints as `assistant` messages instead of pretending they are operator replies.
- app-first marketing ownership, checkout continuation, and cabinet top-level IA belong in the same canonical contract family as hostnames, support, and shared copy governance
- public user-facing version labels stay on `0.x.x-beta`; inherited strings like `2.5.7 dev` are release regressions
- versioned release metadata belongs under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/<version>/` during the bridge period and under `.../artifacts/releases/pokrov-app/<version>/` after cutover

## Script Categories

### Deploy and release

- `remote_deploy_brain_portal_code.py`
- `remote_deploy_brain_static_sites.py`
- `remote_brain_apply_release_handoff.py`
- `remote_apply_ru_bridge_relay.py`
- `remote_apply_transport_front.py`
- `remote_install_mini_canary_stack.py`
- `remote_install_mtproto_proxy.py`
- `remote_switch_bot_tokens.py`
- `release_orchestrator.py`

### Smoke and verification

- `admin_webapp_smoke.py`
- `android_localhost_audit.py`
- `app_bot_parity_smoke.py`
- `api_lifecycle_smoke.py`
- `client_security_smoke.py`
- `release_gate_check.py`
- `run_client_release_gate.py`
- `agent_context_packet_audit.py`
- `pokrov_ai_docs_assistant.py`
- `pokrov_operator_copilot.py`
- `pokrov_support_ai_kb_refresh.py`
- `render_ru_probe_report.py`
- `ru_probe_runner.py`
- `remote_transport_front_smoke.py`
- `smoke_client_apps.py`
- `runtime_app_download_smoke.py`
- `text_integrity.py`
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
  Desired-state reconciler for active key placement: premium/trial/paid keys on enabled paid nodes, free keys on the free pool.

### Audit and diagnostics

- `audit_node_dns.py`
- `audit_node_dns_matrix.py`
- `collect_node_metrics.py`
  Collects provisioned-client counts, online-connection hints, network throughput, dataplane/capacity fields, and writes node runtime metrics without treating `active_clients` as online users.
- `collect_xray_observer.py`
- `control_plane_drift_report.py`
- `portal_bot/daily_panel_node_healthcheck.py`
- `inspect_*`
- `remote_*inspect*`
- `remote_install_node_observer.py`

### Data and migration

- `migrate_sqlite_to_postgres.py`
- `migrate_to_nodes.py`
- `seed_nodes_from_facts.py`
- `sync_shared_surface_facts.py`

Shared-facts and handoff note:

- `sync_shared_surface_facts.py` now targets `POKROV-app/config/*.seed.json` by default and keeps the bridge Dart output as an explicit compatibility-only lane
- release handoff metadata now lives under `POKROV-app/artifacts/releases/...`; the preferred operator input is the client-owned JSON manifest, with `release-links.env` retained only as compatibility evidence when needed

## Canonical Feature Story Audit

These files are the current repo-wide feature/function audit and user-story
status ledger. Keep them together when adding, testing, or retesting a behavior.

- [pokrov-canonical-feature-tracker.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-canonical-feature-tracker.md)
- [pokrov-canonical-feature-tracker.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-canonical-feature-tracker.csv)
- [pokrov-entrypoint-inventory.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-entrypoint-inventory.csv)
- [pokrov-entrypoint-story-coverage.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-entrypoint-story-coverage.csv)
- [pokrov-entrypoint-story-coverage.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-entrypoint-story-coverage.md)
- [pokrov-code-function-inventory.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-code-function-inventory.csv)
- [pokrov-code-function-inventory.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-code-function-inventory.md)
- [pokrov-symbol-coverage-audit.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-symbol-coverage-audit.csv)
- [pokrov-symbol-coverage-audit.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-symbol-coverage-audit.md)
- [pokrov-private-helper-coverage.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-private-helper-coverage.csv)
- [pokrov-private-helper-coverage.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-private-helper-coverage.md)
- [pokrov-coverage-policy-decision-guide.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-coverage-policy-decision-guide.md)
- [pokrov-story-test-evidence-audit.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-story-test-evidence-audit.csv)
- [pokrov-story-test-evidence-audit.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-story-test-evidence-audit.md)
- [pokrov-defect-fix-retest-ledger.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-defect-fix-retest-ledger.csv)
- [pokrov-defect-fix-retest-ledger.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-defect-fix-retest-ledger.md)
- [pokrov-backend-route-coverage.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-backend-route-coverage.csv)
- [pokrov-script-workflow-coverage.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-script-workflow-coverage.csv)
- [pokrov-owner-gated-scenarios.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-owner-gated-scenarios.md)
- [pokrov-owner-gated-execution-guide.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-owner-gated-execution-guide.md)
- [pokrov-owner-gated-scenarios.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-owner-gated-scenarios.csv)
- [pokrov-owner-gated-results.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-owner-gated-results.csv)
- [pokrov-owner-answer-sheet.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-owner-answer-sheet.md)
- [pokrov-open-questions.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-open-questions.md)
- [pokrov-open-questions.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/pokrov-open-questions.csv)
- [COMPLETION-AUDIT.md](C:/Users/kiwun/Documents/ai/VPN/docs/developer/work-orders/2026-06-27--repo-feature-story-audit/COMPLETION-AUDIT.md)
- [COMPLETION-AUDIT.csv](C:/Users/kiwun/Documents/ai/VPN/docs/developer/work-orders/2026-06-27--repo-feature-story-audit/COMPLETION-AUDIT.csv)

## Test Matrix

### Backend and API

- `portal_bot/tests/test_app_first_api.py`
- `tests/test_shared_surface_facts.py`
- `tests/test_portal_api.py`
- `tests/test_api_auth_and_tickets.py`
- `tests/test_api_payments_callbacks.py`
- `tests/test_lavatop_payment_providers.py`
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

- `tests/test_app_bot_parity_smoke.py`
- `tests/test_bot_paywall.py`
- `tests/test_public_copy_guardrails.py`
- `tests/test_tickets_repo.py`
- `tests/test_reviews_username_masking.py`

### Frontend and smoke

- `tests/test_admin_webapp_smoke.py`
- `tests/test_client_security_smoke.py`
- `tests/test_frontend_text_integrity.py`
- `tests/test_public_copy_guardrails.py`
- `tests/test_ui_visual_smoke.py`
- `tests/test_release_gate_check.py`
- `tests/test_runtime_app_download_smoke.py`
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
- `run_client_release_gate.py` targets `C:/Users/kiwun/Documents/ai/POKROV-app` by default for the platform-owned gate lane and fails fast when that workspace is missing or incomplete
- `client_security_smoke.py` now validates the `POKROV-app` seed/runtime contract, Android host manifest, and Windows release-seed expectations instead of bridge-fork file paths
- retained bridge-period bundles and manifests should be stored with the mirrored archive under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/<version>/`
- `release_gate_check.py` requires `ANDROID_AUDIT_SERIAL=<physical-device-serial>` when Android build gates are requested and rejects emulator serials for that public-release path
- `release_gate_check.py` passes `ANDROID_AUDIT_PACKAGE` to `android_localhost_audit.py`; default package is `space.pokrov.pokrov_android_shell`
- `runtime_app_download_smoke.py --redact` is the retained-evidence-safe wrapper around `smoke_client_apps.py`
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

Use `python scripts/cleanup_inventory.py --class all --dry-run` as the source-of-truth inventory before removing these. Use `--apply` only for `safe` or explicitly approved `intentional-reset` classes.

Treat these as workspace dependencies or intentional reset targets, not routine cleanup:

- `node_modules/`
- `.dart_tool/`
- `build/`
- `dist/`
- `.venv/`

Treat these as retained evidence or release assets and preserve them unless you have explicit reason:

- retained bridge bundle archive under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/`
- signing material in `external/client-fork/app/windows/`
- operator evidence in `ops-local/`
- audit evidence in `docs/audit-artifacts/`
- old work orders, specs, visual audit renders, and local design atlas material unless a separate archival policy says to compress them

Out of scope for repo cleanup:

- Android Studio, adb, emulator, and other machine-local Android noise outside this repository

Client artifact note:

- wrapper-driven Android outputs now live under `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/build/app/outputs/...`
- wrapper-driven Windows raw outputs now live under `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/build/windows/x64/runner/Release/...`
- wrapper-driven Windows bundle outputs now live under `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/build/release_bundle/`
- retained bridge-period packaged release artifacts live under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/`

## Historical Material

Historical root guides now live under:

- [docs/archive/root-guides/](C:/Users/kiwun/Documents/ai/VPN/docs/archive/root-guides)

Do not use them as current operating instructions.
