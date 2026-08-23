# Agent Context Map

This file routes a task to the smallest useful context. It does not define product or release truth. Start with the [root contract](../../AGENTS.md), choose one row below, and use the [documentation registry](../README.md) only when a route needs another owner or evidence class.

## Authority By Question

For task and workflow instructions, use this order:

1. system and developer instructions;
2. the user's request;
3. root `AGENTS.md`;
4. an explicit scoped contract named by the task or selected row;
5. this router and the relevant process documentation.

For intended product behavior, use this order:

1. owner-approved shared contracts such as `shared/product-facts.json`, `shared/public-urls.json`, `shared/copy.ts`, and `shared/design-tokens.json`;
2. canonical domain documents classified in `docs/README.md`;
3. current code and tests;
4. active work orders;
5. targeted history;
6. external critique, which remains advisory.

For observed runtime state, use this order:

1. the exact production database, provider, or control-plane state when authorized;
2. current runtime, API, UI, device, and named-origin evidence for the exact environment;
3. artifacts generated from that observation;
4. older evidence.

For a release claim, use this order:

1. identify the exact commit, artifact, manifest, and environment candidate;
2. inspect current gates for that candidate;
3. run or label required manual, provider, device, signing, store, and origin checks;
4. read the current release decision for that candidate;
5. use history only to explain lineage.

## Lane Boundary

| Lane | Working path | Promotion line | Owns |
| --- | --- | --- | --- |
| Platform | `C:/Users/kiwun/Documents/ai/VPN` | `master` | `portal_bot/`, `webapp/`, `adminapp/`, `marketing/`, `shared/`, `infra/`, `scripts/`, platform tests and root docs |
| Active client | `C:/Users/kiwun/Documents/ai/POKROV-app` | `main` | Android, Windows, shared client packages, client tests, client docs and client release metadata |

Client implementation and client docs land in `POKROV-app`. Platform APIs and root canonical owners land here. Retained bridge bundles, retired client summaries, older mockups, and closed work orders are reference material unless the owner explicitly reopens them.

## Evidence Labels And Origins

- `PASS`: the named check passed for the exact candidate and environment.
- `MANUAL_OWNER_TEST`: owner-controlled account, device, provider, signing, store, or live session is still required.
- `OPERATOR_ATTESTED`: an operator statement exists without replacing it with raw retained evidence.
- `SKIPPED_BY_OWNER` and `SKIPPED_BY_OPERATOR`: an explicit accepted skip, never a pass.
- `BLOCKED_BY_ACCESS`: required access was unavailable.
- `NOT_REQUESTED`: the check was outside the authorized scope.

Name evidence origins explicitly: `current-origin`, `brain-origin`, and `RU-origin`. One origin never proves another. Keep release labels candidate-specific and do not infer stable, store, signing, device, payment, or regional readiness from a different candidate or origin.

## Task Router

Commands are focused starting points. Run them from the path named in the cell, add narrower tests for the exact change, and do not run live mutation or deploy commands without authorization.

| Task | Read first | Inspect | Verify | Docs impact |
| --- | --- | --- | --- | --- |
| Backend/API/bots | `docs/architecture/system-overview.md`<br>`docs/architecture/app-first-and-bonus-flows.md` | `portal_bot/api.py`<br>`portal_bot/bot.py`<br>`portal_bot/worker.py`<br>`portal_bot/models.py` | From platform root: `python -B -m pytest -p no:cacheprovider portal_bot/tests/test_app_first_api.py portal_bot/tests/test_app_first_service.py tests/test_api_auth_and_tickets.py tests/test_subscription_preview_api.py -q` | `docs/architecture/system-overview.md`<br>`docs/architecture/app-first-and-bonus-flows.md`<br>`docs/architecture/api-contracts.md` |
| Account/auth/email/payments | `docs/product/payment-and-access-key-contract.md`<br>`docs/architecture/payment-state-machine.md`<br>`docs/architecture/app-first-and-bonus-flows.md` | `portal_bot/web_auth_service.py`<br>`portal_bot/email_auth_service.py`<br>`portal_bot/email_delivery_service.py`<br>`portal_bot/payment_providers.py`<br>`portal_bot/api.py` | From platform root: `python -B -m pytest -p no:cacheprovider portal_bot/tests/test_email_auth.py tests/test_api_payments_callbacks.py tests/test_lavatop_payment_providers.py tests/test_payment_email_readiness_smoke.py -q` | `docs/product/payment-and-access-key-contract.md`<br>`docs/architecture/payment-state-machine.md`<br>`docs/architecture/app-first-and-bonus-flows.md`<br>`docs/operations/payment-reconciliation.md` |
| Web cabinet | `webapp/README.md`<br>`docs/architecture/app-first-and-bonus-flows.md` | `webapp/src/app/(dashboard)/`<br>`webapp/src/lib/api.ts`<br>`webapp/e2e/`<br>`portal_bot/api.py` | From `webapp/`: `npm.cmd run build`<br>`npm.cmd run lint`<br>`npm.cmd run test:e2e:cabinet` | `webapp/README.md`<br>`docs/architecture/app-first-and-bonus-flows.md`<br>`docs/user/portal-vpn-user-guide-ru.md` |
| Standalone adminapp | `adminapp/README.md`<br>`docs/architecture/system-overview.md`<br>`docs/operations/monitoring-and-visibility.md` | `adminapp/src/`<br>`adminapp/e2e/`<br>`portal_bot/api.py`<br>`portal_bot/models.py` | From `adminapp/`: `npm.cmd run build`<br>`npm.cmd run lint`<br>`npm.cmd run test:e2e`<br>From platform root: `python -B -m pytest -p no:cacheprovider tests/test_admin_ops_api.py tests/test_admin_payments_api.py -q` | `adminapp/README.md`<br>`docs/architecture/system-overview.md`<br>`docs/operations/monitoring-and-visibility.md` |
| Marketing/SEO/copy | `marketing/README.md`<br>`docs/product/portal-vpn-product.md`<br>`docs/operations/marketing-governance-and-winback-pilot.md`<br>`DESIGN.md` | `marketing/src/`<br>`shared/copy.ts`<br>`copy/catalog.ru.json`<br>`shared/product-facts.json`<br>`shared/contracts/marketing/`<br>`shared/public-urls.json` | From `marketing/`: `npm.cmd run build`<br>`npm.cmd run check:seo`<br>`npm.cmd run check:responsive`<br>From platform root: `python -B -m pytest -p no:cacheprovider tests/test_frontend_text_integrity.py tests/test_public_copy_guardrails.py tests/test_marketing_governance.py tests/test_winback_pilot.py -q` | `docs/product/portal-vpn-product.md`<br>`docs/operations/marketing-governance-and-winback-pilot.md`<br>`marketing/README.md`<br>`docs/user/portal-vpn-user-guide-ru.md`<br>shared copy/facts owners |
| Shared facts/design contracts | `DESIGN.md`<br>`docs/design/design-system-sync.md`<br>`docs/design/generated-assets-policy.md` | `shared/product-facts.json`<br>`shared/public-urls.json`<br>`shared/portal-config.ts`<br>`shared/design-tokens.json`<br>`shared/design-tokens.schema.json` | From platform root: `python -B -m pytest -p no:cacheprovider tests/test_shared_surface_facts.py tests/test_admin_design_guardrails.py -q`<br>Run affected frontend builds | `DESIGN.md`<br>`docs/design/design-system-sync.md`<br>`docs/design/generated-assets-policy.md`<br>affected canonical domain document |
| Infrastructure/observability | `docs/operations/deployment-and-access.md`<br>`docs/operations/monitoring-and-visibility.md` | `scripts/collect_node_metrics.py`<br>`infra/portal-node-metrics.service`<br>`infra/portal-node-metrics.timer`<br>`portal_bot/panel_client.py` | From platform root: `python -B -m pytest -p no:cacheprovider tests/test_collect_node_metrics.py tests/test_collect_node_metrics_observability.py tests/test_panel_client_metrics.py tests/test_live_probe_scripts.py -q` | `docs/operations/deployment-and-access.md`<br>`docs/operations/monitoring-and-visibility.md`<br>candidate-specific evidence under `docs/audit-artifacts/` |
| Performance/local quality gate | `docs/operations/performance-and-local-quality-gate.md`<br>`shared/contracts/performance/performance-budgets.v1.json` | `scripts/performance_budget_gate.py`<br>`scripts/collect_web_performance.py`<br>`scripts/api_latency_probe.py`<br>`scripts/release_1_2_local_quality_gate.py`<br>affected client/web surfaces | From platform root: `python -m pytest -q tests/test_performance_budget_gate.py tests/test_collect_web_performance.py tests/test_api_latency_probe.py tests/test_new_performance_evidence.py tests/test_release_1_2_local_quality_gate.py`<br>Run `scripts/release_1_2_local_quality_gate.py` with explicit platform/client/Core worktrees for the final local slice | `docs/operations/performance-and-local-quality-gate.md`<br>matching client capture owner<br>exact-environment evidence outside retained release artifacts until Phase 11 |
| Scripts/release operations | `docs/developer/developer-guide.md`<br>`docs/developer/repository-map.md`<br>`docs/operations/publishing-and-signing-guide.md` | exact script under `scripts/`<br>`scripts/release_gate_check.py`<br>`scripts/release_orchestrator.py`<br>related files under `infra/` | From platform root: `python -B -m pytest -p no:cacheprovider tests/test_release_gate_check.py tests/test_release_orchestrator.py tests/test_check_script_manifest.py -q`<br>Run the changed script's dry-run or audit mode | `docs/developer/developer-guide.md`<br>`docs/developer/repository-map.md`<br>matching file under `docs/operations/`<br>exact candidate evidence |
| Documentation/cleanup | `docs/README.md`<br>`docs/developer/agent-context-map.md`<br>`docs/developer/developer-guide.md` | `git status --short --branch`<br>`git diff --name-only`<br>`rg.exe -n "<term>" docs`<br>the canonical owner and conflicting copies | From platform root: `python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`<br>`python -B scripts/agent_context_packet_audit.py --platform-context-root .`<br>`git diff --check` | `docs/README.md` for classification changes<br>`docs/developer/agent-context-map.md` for routes<br>the canonical owner before archive relabeling |
| Active client repository | `C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md`<br>`C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md` | `C:/Users/kiwun/Documents/ai/POKROV-app/packages/app_shell/`<br>`C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/`<br>`C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/` | From the changed client package/app: `flutter analyze`<br>`flutter test`<br>Run the candidate-specific build or release preflight named by client docs | `C:/Users/kiwun/Documents/ai/POKROV-app/docs/` first<br>root architecture/operations docs only when the platform contract changes |
| Historical investigation | `docs/README.md`<br>`docs/archive/README.md` | `rg.exe -n "<term>" docs/archive docs/developer/work-orders`<br>`git log -- <path>`<br>`git show <sha>:<path>` | Re-run the focused check for any current conclusion<br>`git diff --check`<br>Run platform-context audit if registry/router changes | Update the current canonical owner when warranted<br>relabel `docs/archive/` or registry classification only when its historical role was wrong |

## Targeted History Route

Use this sequence only when current owners and evidence do not answer the question:

1. locate the class and owner in `docs/README.md`;
2. search a narrow term with `rg.exe` in the relevant archive or work-order path;
3. use `git log -- <path>` and `git show <sha>:<path>` for provenance;
4. read only the targeted historical files surfaced by those commands.

History explains why and never decides current action. Reconcile any useful finding through the current canonical owner, code, tests, and exact runtime evidence.
