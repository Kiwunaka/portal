# Repository Map

Last updated: 2026-08-27

## Purpose

This map owns top-level path and subsystem boundaries, concise script
categories, and verification entrypoints. Start task-specific navigation at the
[Agent Context Map](agent-context-map.md) and workflow at the
[Developer Guide](developer-guide.md).

## Platform, Client, And Archive Boundaries

- C:/Users/kiwun/Documents/ai/VPN is the platform repository. Its promotion
  lane is portal/master, mapped to origin/master.
- C:/Users/kiwun/Documents/ai/POKROV-app is the active Android/Windows
  repository. Code, client docs, and current artifacts promote through
  POKROV-app/main.
- Root platform docs never become client-repo code authority. Client docs do
  not replace platform product, API, or operations owners.
- docs/archive/, retired client-lane summaries, and retained bridge bundles
  are history, rollback, or evidence inputs only.

## Top-Level Ownership

| Path | Responsibility | Start here |
| --- | --- | --- |
| portal_bot/ | FastAPI backend, Telegram bots, workers, canonical accounts, device sessions and recovery, anti-abuse, economy, payments, entitlements, private support, node/control integration, and modular Admin API v2 BFF | [Backend module map](backend-module-map.md), portal_bot/api.py, portal_bot/admin_v2/, portal_bot/bot.py, domain service/repository modules, focused tests |
| adminapp/ | Canonical Operator Center; frozen legacy shell and seven-workspace migration oracle, exact static build identity, guarded operator flows | adminapp/README.md, adminapp/operator-center.manifest.json, adminapp/scripts/generate-build-contract.mjs, adminapp/src/, adminapp/e2e/, tests/test_operator_center_manifest.py |
| webapp/ | User cabinet plus temporary admin parity fallback | webapp/README.md, webapp/src/app/(dashboard)/ for cabinet, webapp/src/app/(admin)/admin/ for fallback, webapp/src/lib/api.ts, webapp/e2e/ |
| marketing/ | Public acquisition, checkout entry, install help, legal and SEO surfaces | marketing/src/, shared public facts and copy, marketing checks |
| shared/ and copy/ | Cross-surface product facts, hosts, design tokens, and governed copy | shared/product-facts.json, shared/public-urls.json, shared/design-tokens.json, shared/copy.ts, copy/catalog.ru.json |
| infra/ | Runtime service/timer units and infrastructure assets | infra/, deployment and monitoring docs |
| scripts/ | Deploy, release, migration, smoke, probe, audit, and cleanup entrypoints | script categories below and operations docs |
| tests/ | Platform contract, API, service, operations, and documentation regression tests | focused entrypoints below |
| docs/ | Canonical platform docs, active work orders, evidence, and archive | docs/README.md |

The additive account foundation lives under portal_bot/ and is exercised by
tests/test_account_foundation.py. It is repository implementation evidence,
not proof of production deployment. Public numeric identity, stateless bearer,
payment fulfillment, and entitlement authority remain legacy-compatible until
their dedicated migration and promotion gates close.

## Canonical Owners

| Topic | Owner |
| --- | --- |
| Product rules | [Product overview](../product/portal-vpn-product.md) |
| Platform runtime and API boundaries | [System overview](../architecture/system-overview.md) |
| App-first identity, bonuses, and node pools | [App-first and bonus flows](../architecture/app-first-and-bonus-flows.md) |
| Deployment and promotion | [Deployment and access](../operations/deployment-and-access.md) |
| Monitoring, probes, and origin evidence | [Monitoring and visibility](../operations/monitoring-and-visibility.md) |
| Client delivery and update behavior | [Client delivery plan](../operations/client-delivery-update-content-plan.md) |
| Developer workflow and cleanup | [Developer Guide](developer-guide.md) |
| Task-specific context | [Agent Context Map](agent-context-map.md) |
| Active client contracts | C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md |

## Canonical Audit Artifacts

Use these tracked ledgers and summaries for the repository feature/story audit:

- Canonical story tracker: [pokrov-canonical-feature-tracker.md](pokrov-canonical-feature-tracker.md) and [pokrov-canonical-feature-tracker.csv](pokrov-canonical-feature-tracker.csv).
- Entrypoints: [pokrov-entrypoint-inventory.csv](pokrov-entrypoint-inventory.csv), [pokrov-entrypoint-story-coverage.csv](pokrov-entrypoint-story-coverage.csv), and [pokrov-entrypoint-story-coverage.md](pokrov-entrypoint-story-coverage.md).
- Source inventory: [pokrov-code-function-inventory.csv](pokrov-code-function-inventory.csv) and [pokrov-code-function-inventory.md](pokrov-code-function-inventory.md).
- Symbol coverage: [pokrov-symbol-coverage-audit.csv](pokrov-symbol-coverage-audit.csv) and [pokrov-symbol-coverage-audit.md](pokrov-symbol-coverage-audit.md).
- Private-helper coverage and policy: [pokrov-private-helper-coverage.csv](pokrov-private-helper-coverage.csv), [pokrov-private-helper-coverage.md](pokrov-private-helper-coverage.md), and [pokrov-coverage-policy-decision-guide.md](pokrov-coverage-policy-decision-guide.md).
- Story/test evidence: [pokrov-story-test-evidence-audit.csv](pokrov-story-test-evidence-audit.csv) and [pokrov-story-test-evidence-audit.md](pokrov-story-test-evidence-audit.md).
- Defect/fix/retest evidence: [pokrov-defect-fix-retest-ledger.csv](pokrov-defect-fix-retest-ledger.csv) and [pokrov-defect-fix-retest-ledger.md](pokrov-defect-fix-retest-ledger.md).
- Route and workflow coverage: [pokrov-backend-route-coverage.csv](pokrov-backend-route-coverage.csv) and [pokrov-script-workflow-coverage.csv](pokrov-script-workflow-coverage.csv).
- Owner gates: [pokrov-owner-gated-scenarios.md](pokrov-owner-gated-scenarios.md), [pokrov-owner-gated-execution-guide.md](pokrov-owner-gated-execution-guide.md), [pokrov-owner-gated-scenarios.csv](pokrov-owner-gated-scenarios.csv), [pokrov-owner-gated-results.csv](pokrov-owner-gated-results.csv), and [pokrov-owner-answer-sheet.md](pokrov-owner-answer-sheet.md).
- Open questions: [pokrov-open-questions.md](pokrov-open-questions.md) and [pokrov-open-questions.csv](pokrov-open-questions.csv).
- Completion evidence: [docs/developer/work-orders/2026-06-27--repo-feature-story-audit/COMPLETION-AUDIT.md](work-orders/2026-06-27--repo-feature-story-audit/COMPLETION-AUDIT.md) and [docs/developer/work-orders/2026-06-27--repo-feature-story-audit/COMPLETION-AUDIT.csv](work-orders/2026-06-27--repo-feature-story-audit/COMPLETION-AUDIT.csv).

## Script Categories

Use script names as entrypoints, then read the target script and its canonical
operations owner before changing behavior.

| Category | Main entrypoints |
| --- | --- |
| Deploy and release | release_orchestrator.py, remote_deploy_brain_portal_code.py, remote_brain_runtime_source_probe.py, remote_deploy_brain_static_sites.py |
| Client verification | run_client_release_gate.py, client_security_smoke.py, android_localhost_audit.py, runtime_app_download_smoke.py |
| Observability and probes | collect_node_metrics.py, verify_brain_ready.py, ru_probe_runner.py, render_ru_probe_report.py |
| Node/control operations | node_inventory.py, remote_sync_users_to_nodes.py, remote_manage_xui.py |
| Owned AWG lab operations | remote_activate_owned_awg_labs.py, remote_rebind_owned_awg_lab_ports.py, remote_ensure_owned_awg_firewall.py, remote_bind_owned_awg_lab_device.py, remote_select_owned_awg_lab.py, remote_set_owned_awg31_variant.py, remote_audit_owned_awg_alignment.py, remote_probe_owned_awg_udp_path.py, remote_probe_owned_awg_udp_roundtrip.py, remote_count_owned_awg_packets.py, remote_run_owned_awg_core_interop.py |
| Data and migration | migrate_sqlite_to_postgres.py, migrate_to_nodes.py, seed_nodes_from_facts.py, sync_shared_surface_facts.py |
| Commercial contract and rollback | generate_commercial_contract.py, commercial_revision_bundle.py |
| Repository audit | check-links.py, text_integrity.py, agent_context_packet_audit.py, cleanup_inventory.py |

mini is an operator probe/sandbox and opt-in emergency bridge. Scripts that
target it do not make it a normal delivery node or control-plane host.

## Focused Test Entrypoints

| Area | Entry |
| --- | --- |
| Account foundation | tests/test_account_foundation.py |
| App-first/API/bots | portal_bot/tests/test_app_first_api.py, tests/test_portal_api.py, tests/test_api_auth_and_tickets.py |
| Backend composition slices | tests/test_module_slices.py |
| Payments and entitlements | tests/test_api_payments_callbacks.py, tests/test_lavatop_payment_providers.py |
| Commercial authority and capacity | tests/test_commercial_contracts.py, tests/test_commercial_capacity_service.py, tests/test_commercial_revision_bundle.py |
| Primary operator surface | tests/test_operator_center_manifest.py, tests/test_admin_ops_api.py, adminapp/e2e/ |
| Cabinet and admin fallback | webapp/e2e/cabinet-flow.spec.ts, webapp/e2e/admin-gate.spec.ts |
| Marketing and shared copy | tests/test_public_copy_guardrails.py, tests/test_marketing_release_readiness.py |
| Nodes and observability | tests/test_observer_service.py, tests/test_observer_api.py, tests/test_predeploy_node_readiness.py |
| Developer documentation | tests/test_agent_docs_contract.py |
| Active client boundary | scripts/run_client_release_gate.py targeting POKROV-app |

Run interactive Python checks through the configured system interpreter after
installing `portal_bot/requirements.txt`; exact release scripts may retain an
isolated environment they create themselves. Use the focused commands in the
[Developer Guide](developer-guide.md).

## Current Release And Promotion Truth

- Retained distributed stable-direct client: `v1.1.6`; public package line
  `1.1.6+29`.
- Working source target: `1.2.0+4046`, `PRE_CANDIDATE_LOCAL`,
  `candidate_created=false`.
- The client `config/release-handoff.seed.json` owns both facts. The next
  candidate is defined only by a generated and validated strict-v2 handoff.
- Store availability, trusted Windows signing and exact-final Huawei/RU-LTE
  claims remain unproven.
- Account foundation: implemented in the repository, not
  production-deployed/proven.
- Platform code and docs promote through portal/master; active client code,
  docs, and artifacts promote separately through POKROV-app/main.
- Physical-device, signing, store, payment-provider, production-database, and
  origin checks stay explicit; local tests do not replace them.

For generated artifacts, workspace dependencies, retained evidence, and
never-touch zones, use the cleanup section of the
[Developer Guide](developer-guide.md).
