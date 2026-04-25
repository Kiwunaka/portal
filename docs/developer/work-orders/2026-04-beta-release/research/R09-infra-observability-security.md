# R09 Infra Observability Security

Status: research complete
Last updated: 2026-04-25
Scope: POKROV paid beta release wave, infra/observability/security readiness.

This is a read-only audit. No deploy, live SSH, adb, pytest, release gate, or browser commands were run in this pass. Claims are labeled as requested:

- confirmed: repository evidence, docs, tests, or existing artifacts directly support the claim.
- probable: repository evidence strongly suggests the claim, but this pass did not exhaustively prove it.
- unknown: not enough evidence was found in the inspected scope.
- needs local run: a local command or device run is needed to prove current state.
- blocked by missing access: live brain, RU probe, production, provider, or device access is needed.

## Sources Reviewed

- confirmed: Operations anchors reviewed: `docs/operations/deployment-and-access.md`, `docs/operations/monitoring-and-visibility.md`, `docs/operations/publishing-and-signing-guide.md`.
- confirmed: Product/system anchors reviewed: `docs/README.md`, `docs/product/portal-vpn-product.md`, `docs/architecture/system-overview.md`, `docs/architecture/app-first-and-bonus-flows.md`, `docs/developer/developer-guide.md`, `docs/developer/repository-map.md`.
- confirmed: Client lane anchors reviewed: `C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md`, `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md`.
- confirmed: Infra files reviewed under `infra/`, including metrics and observer systemd units, HAProxy/Caddy transport configs, qdisc shaping profiles, free egress/per-IP limiter setup, and logrotate.
- confirmed: Scripts reviewed include `scripts/collect_node_metrics.py`, `scripts/node_dataplane_probe.py`, `scripts/node_access.py`, `scripts/release_gate_check.py`, `scripts/release_orchestrator.py`, `scripts/verify_brain_ready.py`, `scripts/client_security_smoke.py`, `scripts/android_localhost_audit.py`, `scripts/ru_probe_runner.py`, `scripts/render_ru_probe_report.py`, and `scripts/remote_*` deploy/sync/probe helpers.
- confirmed: Security and observability tests reviewed include API auth/ticket tests, payment callback tests, observer tests, node metrics/probe tests, Android localhost audit tests, release gate tests, and node access tests.

## Key Blockers

1. needs local run: A fresh release gate is required after the active client cutover to `C:/Users/kiwun/Documents/ai/POKROV-app`. The existing artifact `docs/audit-artifacts/release_gate_report.md` shows a previous PASS on 2026-04-23, but parts of its tail still reference the retired `external/client-fork/app` lane. It is useful history, not current paid beta proof.
2. needs local run: Android public release remains blocked until a physical-device release-build localhost/control-surface audit passes. `scripts/release_gate_check.py` can require the Android audit when Android platform gates are requested, and rejects emulator serials for required public Android gates, but no fresh physical-device evidence was produced in this pass.
3. blocked by missing access: Brain-origin deploy/readiness proof was not collected. `scripts/verify_brain_ready.py` covers required services, ports, health, static surfaces, checkout callback reachability, subscription delivery, and connect-host checks, but it needs access to the control-plane host.
4. blocked by missing access: RU-origin readiness was not proven. `scripts/ru_probe_runner.py` and `scripts/render_ru_probe_report.py` provide the right probe/report path, but the docs correctly treat `mini` or any RU replacement as an operational dependency, not a guaranteed property.
5. blocked by missing access: Live metrics freshness, observer freshness, and alert behavior were not checked against `/api/admin/metrics/status` or `/api/admin/nodes/health` from production.
6. unknown: Production Postgres backup/restore proof before deploy is not confirmed from the inspected release orchestration. SQLite backup helpers and static deployment backups exist, but a current Postgres backup gate or restore drill was not found.

## Infra And Deploy

- confirmed: `scripts/release_orchestrator.py` sequences gates, optional handoff sync, backend deploy, static deploy, optional qdisc/observer helpers, and post-deploy verification. It requires `--brain-ip` for deploy/verify phases.
- confirmed: `scripts/remote_deploy_brain_portal_code.py` deploys portal code to brain and restarts `portal-api`, `portal-bot`, `portal-helpbot`, and `portal-feedbackbot` by default. Tests assert shared runtime assets and feedbackbot inclusion, and fail inactive requested units after restart.
- confirmed: Static deploy keeps previous static surface copies under `legacy_backups`, giving a local static rollback path.
- confirmed: `scripts/verify_brain_ready.py` expects `caddy`, `portal-api`, `portal-bot`, `portal-helpbot`, and `portal-feedbackbot`, plus listener ports 443 and 8444, API health, marketing/webapp surfaces, checkout callback reachability, and subscription/connect-host checks.
- probable: The deploy path is service-complete for paid beta backend/static release mechanics, assuming brain SSH and production environment are correct.
- needs local run: Run the orchestrated gate/deploy/verify path from the operator workstation before declaring release readiness.
- unknown: No current evidence was found for an automated production Postgres predeploy backup gate or restore validation in the release orchestrator.

## Node Sync And 3x-ui Boundaries

- confirmed: `portal_bot/control_panel.py` treats the database as product authority and 3x-ui as execution layer. It separates paid and free pool placement, supports draining/disable/resync flows, and avoids treating panel state as product truth.
- confirmed: `portal_bot/panel_client.py` executes panel mutations and supports transport profile catalogs, inbound mappings, paid/free limits, and node-specific panel credentials.
- confirmed: `scripts/remote_brain_sync_users_to_nodes.py` implements policy-aware brain-side sync: free nodes receive only free users, while regular country nodes are paid-only.
- confirmed: `scripts/remote_sync_users_to_nodes.py` is an older/minimal sync path that copies local DB state to brain and has less explicit policy structure. It should not be treated as the preferred paid beta sync path without an operator reason.
- probable: Paid beta node sync boundaries are sound when the API/control-panel path and `remote_brain_sync_users_to_nodes.py` are used.
- needs local run: A predeploy node readiness test and a live brain-origin sync dry-run/verification should be captured before release.

## Metrics, Alerts, Incidents, And Logs

- confirmed: `infra/portal-node-metrics.timer` and `infra/portal-node-observer.timer` run at a 60 second cadence with persistent timers.
- confirmed: `infra/portal-node-metrics.service` reads `/root/portal_bot/.env` and runs `collect_node_metrics.py` from the portal runtime.
- confirmed: `scripts/collect_node_metrics.py` records CPU, memory, disk, network totals/rates, health score, error rate, active connections, dataplane probe stage/error/classification, hoster family/ASN/subnet, IPv4/IPv6 health, and transport-health root cause fields.
- confirmed: `scripts/node_dataplane_probe.py` performs layered DNS/TCP/TLS/SNI/certificate target probing and derives stage, family, and root-cause classifications.
- confirmed: Admin metrics endpoints expose alert and freshness data through `/api/admin/metrics/status` and `/api/admin/nodes/health`; tests cover alert fields and observer shape.
- confirmed: `infra/portal-node-observer.logrotate` rotates `/var/log/xray/access.log` daily, keeps 7 copies, uses `copytruncate`, and creates logs with `0640 root adm`.
- confirmed: `scripts/remote_xui_logs.py` can read recent x-ui journal logs remotely. This is useful for incidents but may expose sensitive runtime details if copied into handoffs without redaction.
- needs local run: Query production `/api/admin/metrics/status` and `/api/admin/nodes/health` to confirm freshness, alert thresholds, observer push recency, and per-node probe fields.
- probable: Incident visibility is adequate for beta if freshness and probe reports are actively checked during release. The repo evidence is stronger for detection than for documented incident-response playbooks.

## Secrets, SSH, And Sensitive Material

- confirmed: `.gitignore` covers `.env`, `**/.env`, `VPN NODE SSH KEYS/`, `ops-local/`, and `secrets for merchant/`.
- confirmed: `git ls-files` checks found no tracked entries for the obvious local secret/key/signing paths checked in this pass.
- confirmed: Secret-bearing local files exist in the workspace and were not needed for this report. They must not be committed or copied into markdown.
- confirmed: `scripts/node_access.py` supports key/password lookup through local key material and environment variables, but uses Paramiko `AutoAddPolicy()`.
- confirmed: Other remote helper scripts also use `AutoAddPolicy()` patterns.
- probable: SSH helper ergonomics are good, but host key verification should be hardened before this becomes a routine paid beta operator path.
- needs local run: Validate local operator SSH material and known-hosts setup without printing secrets.

## Local Control Surfaces And Android Localhost Audit

- confirmed: `scripts/android_localhost_audit.py` detects localhost listeners on Android over adb, probes listeners, fails on new localhost listeners, and fails on successful unauthenticated probes. Tests cover listener parsing, new listener detection, successful-probe failure, and adb recovery.
- confirmed: `scripts/release_gate_check.py` can require the Android localhost audit when Android platform gates are requested and rejects emulator serials for required public Android gates.
- confirmed: The current active Android manifest declares the VPN service as non-exported with `android.permission.BIND_VPN_SERVICE` and special-use foreground service permission.
- confirmed: The current active Android build seed still uses debug signing for release configuration, which blocks production/public release signing readiness.
- needs local run: Run the Android audit on a physical device with the release build installed and record the result as release evidence.

## Admin/API Auth And Web Session Security

- confirmed: API auth supports Telegram initData validation and signed web session bearer tokens.
- confirmed: Admin endpoints use admin guard tests, including coverage for admin-only metrics and node operations.
- confirmed: Development auth is gated by `WEBAPP_DEV_AUTH` and local-loopback/dev-origin checks; the default is disabled.
- confirmed: `portal_bot/web_auth_service.py` signs web session tokens with HMAC and validates expiry with constant-time comparison. Telegram OIDC validation includes issuer, audience, expiry/issued-at, JWKS, PKCE/state handling.
- confirmed: The webapp stores `portal_web_session_token` in `window.localStorage` and sends it as an Authorization bearer token.
- probable: The bearer/localStorage model is acceptable for an internal beta only with strong XSS discipline, short expiry, and TLS, but it is weaker than an HttpOnly Secure SameSite cookie model for public paid traffic.
- needs local run: Re-run the admin/auth regression tests and inspect production environment flags to confirm no dev-auth path is enabled.

## Payment Callback Security

- confirmed: Payment callback tests cover FreeKassa invalid signature rejection, idempotent result handling, invalid-signature non-poisoning, notify alias behavior, and provider wrapper callbacks for Cardlink, Pally, Platima, and FreeKassa.
- confirmed: `PAYMENT_CALLBACK_TOLERANT_MODE` defaults to false in code and example configuration.
- probable: Signature/idempotency basics are covered well enough for beta code readiness.
- blocked by missing access: Live provider callback configuration, merchant dashboards, and production webhook reachability were not verified in this pass.

## Rate Limiting, Abuse, And Fraud Basics

- confirmed: Diagnostics runs have an in-memory rate limiter that returns 429 for repeated calls.
- confirmed: Referral anti-fraud delay settings exist, and referral bonuses can be queued/delayed for review.
- confirmed: Admin cleanup logic is constrained around manual/test users in tests.
- probable: Broad rate limiting for auth, email, payment initiation, support upload, and ticket flows is not consistently visible in the inspected code. This should be treated as a paid beta risk unless separately proven.
- probable: Abuse/fraud controls are basic rather than comprehensive. They reduce obvious referral and diagnostics abuse, but do not replace provider-side fraud/risk controls or global API throttling.

## Privacy-Safe Diagnostics

- confirmed: Node probe/metrics errors are truncated before storage.
- confirmed: Observer pushes are HMAC/timestamp authenticated before acceptance.
- confirmed: Support upload storage uses generated names, but the static support upload route is bearerless once a file name is known.
- probable: Support upload URLs are hard to guess but not access-controlled per request; this is a privacy hardening item for paid beta.
- probable: Remote log helper output should be treated as sensitive operational material and redacted before any public or semi-public handoff.

## Backups And Rollback

- confirmed: `scripts/backup_portal_db.py` exists for SQLite backups.
- confirmed: Static deployment scripts preserve previous static outputs under a legacy backup location.
- confirmed: Some one-off remote scripts back up SQLite before mutation.
- unknown: A current production Postgres `pg_dump` or restore-check gate was not found in the release orchestrator path.
- needs local run: Capture a current production backup/restore or at least backup-existence proof before paid beta deploy.

## Origin Readiness

- current-origin check: needs local run. The repo has a previous release gate PASS artifact from 2026-04-23, but a fresh run is needed because the active client lane now lives at `C:/Users/kiwun/Documents/ai/POKROV-app`.
- brain-origin check: blocked by missing access. `scripts/verify_brain_ready.py` and remote probe helpers exist, but this pass did not access `82.21.114.104`.
- RU-origin check: blocked by missing access. `scripts/ru_probe_runner.py` can produce a structured RU-origin report, but no `mini` or replacement RU probe host was available in this pass.

## Recommended Validation Commands

- needs local run: `python scripts/release_gate_check.py --brain-ip 82.21.114.104 --quick`
- needs local run: Set `ANDROID_AUDIT_SERIAL` to a physical-device serial, then run `python scripts/release_gate_check.py --client-platform-gates windows,android-apk,android-aab`
- needs local run: `python scripts/android_localhost_audit.py --serial <physical-device-serial> --connect-wait-sec 30 --disconnect-wait-sec 15`
- blocked by missing access: `python scripts/verify_brain_ready.py --brain-ip 82.21.114.104`
- blocked by missing access: `python scripts/ru_probe_runner.py --reserve-host rf1.pokrov.space --probe-host mini --out ops-local/ru-probe.json`
- needs local run: `python scripts/render_ru_probe_report.py --input ops-local/ru-probe.json`
- needs local run: `python -m pytest tests/test_api_auth_and_tickets.py tests/test_api_payments_callbacks.py -q`
- needs local run: `python -m pytest tests/test_observer_service.py tests/test_observer_api.py tests/test_collect_xray_observer.py tests/test_predeploy_node_readiness.py -q`
- needs local run: `python -m pytest tests/test_node_access.py tests/test_node_dataplane_probe.py tests/test_ru_probe_runner.py tests/test_render_ru_probe_report.py -q`
- needs local run: `python scripts/client_security_smoke.py`

## Release Recommendation

- probable: The repository contains the right mechanisms for a paid beta infra release: gated deploy orchestration, production readiness checks, node observability, per-node probes, observer data, payment callback signature tests, admin guards, and Android localhost audit tooling.
- needs local run: Do not mark R09 green until the current release gate, Android physical-device localhost audit, brain-origin readiness verification, metrics freshness check, and backup proof are captured.
- blocked by missing access: Do not claim RU-origin readiness until an actual RU probe host run is recorded.
- probable: For paid beta hardening, prioritize SSH host key verification, broader API rate limiting, web session storage hardening, authenticated support upload retrieval, log redaction policy, and explicit Postgres backup/restore evidence.
