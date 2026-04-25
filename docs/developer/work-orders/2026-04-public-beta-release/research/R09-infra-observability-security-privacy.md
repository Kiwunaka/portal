# R09 Infra Observability Security Privacy

Status: research complete
Last updated: 2026-04-25
Scope: public beta infra, observability, security, privacy, deploy, rollback, and origin-readiness.

This was a read-only research pass except for this assigned output file. I did not run live SSH, adb, browser, deploy, release-gate, provider, or RU-probe commands. I did not read or print secret-bearing files.

Labels used below:

- confirmed: repository code, tests, docs, or inherited evidence directly supports the claim.
- probable: repository evidence strongly suggests the claim, but current live state was not proven here.
- unknown: inspected scope does not contain enough evidence.
- needs local run: a local command, device run, or generated report is required.
- blocked by missing access: live brain, production admin, provider, physical device, or RU-origin access is required.

## Sources Reviewed

- confirmed: `AGENTS.md`.
- confirmed: Canonical docs: `docs/README.md`, `docs/product/portal-vpn-product.md`, `docs/architecture/system-overview.md`, `docs/architecture/app-first-and-bonus-flows.md`, `docs/operations/deployment-and-access.md`, `docs/operations/monitoring-and-visibility.md`, `docs/developer/developer-guide.md`, and `docs/developer/repository-map.md`.
- confirmed: Infra and release scripts: `scripts/release_gate_check.py`, `scripts/release_orchestrator.py`, `scripts/verify_brain_ready.py`, `scripts/collect_node_metrics.py`, `scripts/node_dataplane_probe.py`, `scripts/node_observability_gate.py`, `scripts/ru_probe_runner.py`, `scripts/render_ru_probe_report.py`, `scripts/android_localhost_audit.py`, `scripts/client_security_smoke.py`, `scripts/remote_deploy_brain_portal_code.py`, `scripts/remote_deploy_brain_static_sites.py`, `scripts/remote_install_node_metrics_timer.py`, and `scripts/remote_install_node_observer.py`.
- confirmed: Runtime units: `infra/portal-node-metrics.service`, `infra/portal-node-metrics.timer`, and related metrics/observer references in docs.
- confirmed: API and admin surfaces: `portal_bot/api.py`, including `/api/admin/metrics/status`, `/api/admin/nodes/health`, observer ingest, support uploads, CORS, and admin auth paths.
- confirmed: Relevant tests: `tests/test_release_gate_check.py`, `tests/test_verify_brain_ready.py`, `tests/test_collect_node_metrics_observability.py`, `tests/test_node_dataplane_probe.py`, `tests/test_predeploy_node_readiness.py`, `tests/test_node_observability_gate.py`, `tests/test_node_observability_schema.py`, `tests/test_observer_api.py`, `tests/test_observer_service.py`, `tests/test_client_security_smoke.py`, `tests/test_android_localhost_audit.py`, `tests/test_ru_probe_runner.py`, `tests/test_render_ru_probe_report.py`, `tests/test_remote_deploy_brain_portal_code.py`, and `tests/test_panel_client_metrics.py`.
- confirmed: Inherited paid-beta R09/W08/W09 evidence only: `docs/developer/work-orders/2026-04-beta-release/research/R09-infra-observability-security.md`, `docs/developer/work-orders/2026-04-beta-release/evidence/logs/WO-008-infra-nodes-observability-deploy.md`, `docs/developer/work-orders/2026-04-beta-release/evidence/security-audit/WO-009-security-baseline.md`, and the corresponding W08/W09 work orders.
- confirmed: Existing gate artifact header: `docs/audit-artifacts/release_gate_report.md` generated `2026-04-25 02:12:51`.

## Highest-Risk Findings

1. blocked by missing access: Public beta still lacks live brain-origin and RU-origin proof. The current saved `release_gate_report.md` is a local current-origin PASS only; it explicitly marks brain-origin and RU-origin as `BLOCKED_BY_ACCESS`. `verify_brain_ready.py` can check services, listeners, public surfaces, checkout, and connect-host subscription delivery from brain, while `ru_probe_runner.py` can produce the RU-origin report, but neither result is present in this pass.
2. needs local run: Android public release remains blocked until a release-installed physical device passes the localhost/control-surface audit. `release_gate_check.py` requires `ANDROID_AUDIT_SERIAL` and rejects emulator serials when Android build gates are requested, and `android_localhost_audit.py` fails on new reachable localhost listeners. The saved gate did not request Android platform builds and marks Android physical audit as `BLOCKED_BY_ACCESS`.
3. unknown: Production Postgres backup/restore proof is not established in the inspected release path. `release_orchestrator.py` can run gates, handoff sync, deploy, metrics timer ensure, observer install, qdisc rollout, and post-deploy verify, but I did not find a public-beta deploy gate that creates a fresh `pg_dump`, verifies restore/readback, or records rollback position for production Postgres. Static rollback and qdisc rollback paths are better covered than database rollback.
4. confirmed: Metrics visibility is stronger than paid-beta baseline, but `/api/admin/metrics/status` still does not fully match the documented `ok/stale/missing/unavailable/failed` semantics. The endpoint reports `fresh`/`stale` and can render missing memory, disk, and network telemetry as `0`-like percentages or rates, while `/api/admin/nodes/health` preserves more nulls. This can make missing telemetry look like low utilization during public beta unless production checks explicitly inspect raw fields.
5. probable: Public-beta security/privacy hardening has unresolved P1 risk around browser and operator surfaces. Evidence confirms wildcard CORS with credentials, web session bearer tokens in `localStorage`, bearerless static support-upload URLs once filenames are known, and widespread Paramiko `AutoAddPolicy()` in SSH helpers. These may be acceptable only with explicit beta risk acceptance, tight evidence redaction, and non-public distribution scope.

## Deploy And Rollback Readiness

- confirmed: `release_orchestrator.py` can sequence local gates, optional release-handoff sync, metrics timer ensure, observer timer install, backend deploy, static deploy, qdisc rollout, qdisc failure cleanup, and post-deploy brain verification.
- confirmed: `remote_deploy_brain_portal_code.py` deploys backend code and shared runtime assets, and its default restart set includes `portal-api`, `portal-bot`, `portal-helpbot`, and `portal-feedbackbot`; tests assert feedbackbot inclusion and failure on inactive requested units.
- confirmed: `verify_brain_ready.py` requires `caddy`, `portal-api`, `portal-bot`, `portal-helpbot`, and `portal-feedbackbot`, plus listeners on `443` and `8444`, API health, app/marketing/checkout surfaces, and subscription checks through both API compatibility and canonical `connect.pokrov.space`.
- confirmed: Static deploy preserves previous webapp/marketing directories under `legacy_backups`, giving a static rollback source.
- confirmed: qdisc rollout has explicit `disable` and `rollback` cleanup steps in `release_orchestrator.py` when qdisc apply/smoke fails.
- unknown: No current production Postgres backup/restore drill evidence was found for this public-beta release path.
- needs local run: Before deploy, capture current local/remote HEADs, exact dirty patch state, release artifact IDs, static backup path, database backup or no-DB-change statement, and rollback commands.

## Observability And Node Metrics

- confirmed: `collect_node_metrics.py` stores panel health, dataplane probe stage/error/classification, CPU, memory, disk, network totals/rates, active client count, hoster family/ASN/subnet, IPv4/IPv6 health, and transport-health root-cause details.
- confirmed: The collector separates panel state from dataplane state, so panel login/inbound failures do not suppress dataplane evidence.
- confirmed: `portal-node-metrics.timer` runs every 60 seconds and uses `/root/portal_bot/.env`; docs say deploys must ship both `collect_node_metrics.py` and `node_dataplane_probe.py` to avoid import failures.
- confirmed: `/api/admin/nodes/health` exposes per-node online keys/connections, network current/24h peak, observer counters, transport health, hoster metadata, probe classification, and freshness fields.
- confirmed: Observer-lite ingest is HMAC/timestamp authenticated, idempotent by batch, and tracks unmatched plus parse-error counts.
- probable: The code is ready to surface node incidents if the timer is installed and live credentials are valid.
- blocked by missing access: Production `/api/admin/metrics/status`, `/api/admin/nodes/health`, timer status, and sample freshness were not checked here.
- needs local run: Run focused node/observer tests and a production admin metrics check before public beta handoff.

## Origin Separation

- current-origin check: confirmed local artifact exists. `docs/audit-artifacts/release_gate_report.md` shows local default gate PASS at `2026-04-25 02:12:51`, with no brain IP and no Android/client platform build gates.
- brain-origin check: blocked by missing access. Run `python scripts/verify_brain_ready.py --brain-ip 82.21.114.104` or the orchestrator verify path with approved access.
- RU-origin check: blocked by missing access. Run `ru_probe_runner.py` from `mini` or a replacement external RU host, then render a redacted report. Do not infer RU readiness from current-origin or brain-origin checks.

## Security And Privacy

- confirmed: `release_gate_check.py` redacts obvious token/password/secret/bearer values from command lines and output tails.
- confirmed: Secret-material locations are documented as never-touch zones, and this pass did not inspect them.
- confirmed: `client_security_smoke.py` is included in default and quick gates and passed in the saved local report.
- confirmed: `android_localhost_audit.py` detects localhost TCP/UDP listeners, compares phases, and fails on new reachable unauthenticated localhost surfaces.
- confirmed: CORS currently allows `["*"]` with credentials in `portal_bot/api.py`.
- confirmed: webapp stores `portal_web_session_token` in `window.localStorage` and sends it as an Authorization bearer token.
- confirmed: support uploads are mounted as static files after authenticated upload.
- confirmed: many SSH helpers use Paramiko `AutoAddPolicy()`.
- probable: The public beta can proceed only with explicit acceptance of these P1 hardening items or with fixes before broader distribution.

## Recommended Validation Commands

- needs local run: `python scripts/release_gate_check.py --output docs/audit-artifacts/release_gate_report.md`
- needs local run: `python scripts/release_gate_check.py --client-platform-gates windows,android-apk,android-aab --output docs/audit-artifacts/release_gate_report.md` with `ANDROID_AUDIT_SERIAL` set to a physical device.
- needs local run: `python scripts/android_localhost_audit.py --serial <physical-device-serial> --connect-wait-sec 30 --disconnect-wait-sec 15`
- blocked by missing access: `python scripts/verify_brain_ready.py --brain-ip 82.21.114.104`
- blocked by missing access: `python scripts/ru_probe_runner.py --reserve-host rf1.pokrov.space --probe-host mini --out ops-local/ru-probe.json`
- needs local run: `python scripts/render_ru_probe_report.py --input ops-local/ru-probe.json`
- needs local run: `python -m pytest tests/test_release_gate_check.py tests/test_verify_brain_ready.py tests/test_collect_node_metrics_observability.py tests/test_node_dataplane_probe.py tests/test_predeploy_node_readiness.py tests/test_node_observability_gate.py tests/test_node_observability_schema.py tests/test_observer_api.py tests/test_observer_service.py -q`
- needs local run: production backup proof or explicit no-migration/no-DB-change statement before deploy.

## What I Checked

- Canonical platform docs, release/metrics scripts, infra metrics units, relevant API surfaces, observer/node/security tests, current saved gate evidence, and inherited paid-beta R09/W08/W09 evidence.

## What I Found

- The repository has materially better public-beta gate classification and node observability than the inherited paid-beta starting point.
- The saved current-origin gate is green, but live brain/RU checks, Android physical audit, production metrics freshness, and database rollback proof remain unresolved.
- Several security/privacy hardening gaps remain beta-acceptable only with explicit risk acceptance.

## What I Changed

- Added this assigned research file only.

## How I Verified

- Read-only inspection of docs, scripts, API code, tests, and inherited evidence.
- No tests or live checks were run in this pass.

## What Remains / Risk

- Public beta signoff should not claim full operational readiness until brain-origin, RU-origin, Android physical audit, production metrics freshness, and backup/rollback evidence are captured.
- Treat raw logs, support uploads, Android audit JSON, payment/provider payloads, Telegram IDs, subscription links, and SSH/provider output as sensitive evidence requiring redaction before promotion into docs.
