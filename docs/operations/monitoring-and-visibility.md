# Monitoring And Visibility

Last updated: 2026-06-07

## Document Status

This file is living source of truth for hostname migration policy, external RU probe operations, and operator visibility into app, bot, device, and IP context.

Quick handoff runbooks:

- [Email Delivery Webhook Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/email-delivery-webhook-handoff.md)
- [RU Origin Probe Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/ru-origin-probe-handoff.md)
- [Release Links And Final Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/release-links-and-final-handoff.md)
- [Support Macros](C:/Users/kiwun/Documents/ai/VPN/docs/launch/support-macros.md)

## Canonical Hostname Policy

Current official public surfaces are:

- marketing and public site: `https://pokrov.space/`
- user cabinet and web login: `https://app.pokrov.space/`
- public API host: `https://api.pokrov.space/`
- config / subscription host: `https://connect.pokrov.space/`
- hosted checkout entry: `https://pay.pokrov.space/checkout/`

Hostname role split:

- `pokrov.space` is the canonical public brand and must be used in new product copy, onboarding, release notes, support scripts, and distribution links
- `app.pokrov.space` is the canonical browser entry for account continuation, web login, and checkout continuation
- `api.pokrov.space` is the canonical API base for browser and app-first web flows
- `connect.pokrov.space` is the canonical public config host for `subscription_url`, QR import, and browser-visible connection delivery
- `connect.pokrov.space` serves the rollout-selected app-managed profile and should keep `legacy_reality_fallback` as the baseline until canary cohorts are explicitly enabled for `grpc_443_primary`
- legacy `api.pokrov.space/s8Kx2mP7qR4wT/...` should be monitored as compatibility, not as the primary public connection surface
- `kiwunaka.space` is compatibility-only for migration and legacy subscription continuity

Compatibility rule for `kiwunaka.space`:

- keep it alive only while older subscriptions and imported profiles still depend on it
- do not use it in new QR codes, fresh config links, bot onboarding, app onboarding, public CTA copy, or support macros for new users
- when support sees an old `kiwunaka.space` profile, the preferred answer is migration to the canonical `pokrov.space` line rather than re-issuing another legacy entrypoint

## Monitoring Layers

Monitoring should cover four layers together:

1. public entrypoints and hostname correctness
2. app, webapp, and bot session health, including Telegram and email browser-continuation parity
3. node reachability and public egress
4. support visibility for linked Telegram, device, and IP context
5. per-node freshness, sustained resource alerts, and probe failure reasons

The platform should be operated as one system. A broken Telegram handoff, dead node, or wrong hostname can all appear to the user as "VPN does not work".

## Identity And Email Visibility

The browser identity rollout should stay operator-visible instead of hiding inside generic session errors.

Required support and admin identity fields:

- `auth_origin` such as `app`, `telegram`, `email`, or `checkout_ticket`
- linked email presence and verification state when email auth is enabled
- linked Telegram presence
- install or device context tied to the same session

Operational rule:

- transactional sender health for `noreply@pokrov.space` should be monitored separately from node health and Telegram availability
- Telegram and email are equal browser-continuation entry families into the same cabinet session model; investigate failures in either path as first-class auth incidents instead of assuming only one route is canonical
- email verification or recovery incidents must not be misclassified as node or routing incidents
- the latest local green release-gate report does not replace `current-origin`, `brain-origin`, or `RU-origin` evidence in a release handoff

If the issue is email-specific, hand off through:

- [email-delivery-webhook-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/email-delivery-webhook-handoff.md)

## Transport Rollout Visibility

Transport rollout must stay visible to operators instead of being buried in opaque config.

Visibility rule:

- admin and operator views should show `transport_health`, `probe_classification`, `ipv4_health`, and `ipv6_health` alongside node freshness
- the active transport profile should be readable from node health so operators can tell whether a node is still on `legacy_reality_fallback`, has moved to `grpc_443_primary`, or is reserved for `operator_lab`
- `network_rollout_config` is the operator-owned source of rollout policy and should be checked whenever transport or DNS diverge by cohort
- qdisc rollout evidence should stay operator-visible through `infra/node-qdisc-profiles.json`, `scripts/remote_apply_node_qdisc.py show`, `tc -s qdisc`, and `scripts/remote_node_qdisc_smoke.py`
- admin node health must show `panel_state` and `dataplane_state` separately; panel failure must not suppress dataplane probe evidence
- operator-readable node context must include `hoster_family`, `hoster_asn`, `subnet`, `root_cause_summary`, `root_cause_detail`, `telegram_app_path`, and `telegram_web_path`
- `operator_lab` allowlists are control-plane data, not user-facing diagnostics, and must not leak into public UI or support copy
- if a failure is provider- or family-specific, fail over by `subnet` first, then by `hoster_family`, and only then by country label
- release and incident reports must keep `current-origin check`, `brain-origin check`, and `RU-origin check` as separate evidence lines
- do not collapse those origins into a single verdict because each origin answers a different question

## Subscription Truth And Smart-Connect Visibility

Admin truth must be install-aware and explicit about missing data instead of implying certainty.

Required admin summary fields:

- `active_nonfree_accounts`
- `trial_accounts`
- `bonus_accounts`
- `unique_install_ids_24h`
- `unique_install_ids_7d`
- `observer_seen_accounts_24h`
- `data_quality.metrics`
- `data_quality.app_installs`
- `data_quality.observer`

Required operator meaning:

- entitlement counts describe backend truth for active premium-grade access, trial access, and bonus access
- install counts describe recent app-seen activity, not a perfect human count
- observer counts describe observer-seen accounts, not a full billing truth replacement
- each data-quality badge must render as `ok`, `stale`, or `missing`

Smart-connect visibility rule:

- the managed manifest exposes shortlist-level `health_score`, `cpu_percent`, `panel_latency_ms`, `backend_penalty`, `cpu_penalty`, `shortlist_revision`, and stickiness metadata
- accepted client RTT uploads are stored through the `smart_connect_latency_sample` event with `install_id`, `carrier`, `platform`, selected node, previous node, and accepted RTT samples
- operators should be able to reason about recent RTT quality by node, carrier, and platform without exposing raw samples in public consumer UI
- shortlist evidence must respect the paid-pool vs `NL-free` pool boundary; a “better ping” does not authorize crossing the access-tier rule

## WARP Material Visibility

WARP is a client-local Hiddify-core lifecycle feature with backend
consent/event telemetry. Backend-managed WARP material is an optional operator
lane, not a prerequisite for the normal client-local toggle. Production WARP
readiness still requires Android and Windows release-build proof. Operator
monitoring must keep that distinction explicit.

Current WARP operator summary:

- `GET /api/admin/client/warp/summary`
- admin-only
- redacted by construction; it returns counts and timestamps, not WireGuard
  keys, account tokens, subscription URLs, or raw config material

Required fields:

- total, active, stale-active, revoked, and rotation-requested optional WARP
  materials
- active client-local WARP consents
- recent material provisions, provisioning failures, rotation requests,
  runtime errors/fallbacks, and rate-limit hits
- redacted runtime summary: last runtime state, last reason code, per-state
  counts, and the latest runtime event headers without user messages,
  WireGuard/account material, or raw metadata
- configured `material_max_age_hours`

Operational rules:

- material older than `WARP_MATERIAL_MAX_AGE_HOURS` is stale and must not be
  returned through managed profile material delivery
- provisioning is limited by `WARP_MATERIAL_PROVISION_LIMIT_PER_HOUR`
- app-requested rotation is limited by `WARP_ROTATION_LIMIT_PER_HOUR`
- rate-limit and provisioning-failure events should be investigated as abuse,
  misconfigured automation, or operator workflow issues before blaming the
  client runtime
- a green summary does not prove production WARP; production proof still needs
  Android and Windows release-build connect/disconnect/fallback evidence

## External RU Probe Policy

Required cadence:

- every `6 hours`

Required probe origin:

- an external RU node or other external RU vantage point that is outside the control-plane host

Availability rule:

- `mini` / `RFMINI` is the canonical RU-origin operator sandbox and preferred RU probe host
- if `mini` TCP reachability is present but SSH auth fails, treat the run as `RU-origin check: BLOCKED_BY_ACCESS`, not as proof that RU visibility is absent
- if `mini` is actually down, treat RU-origin observability as degraded until a replacement external RU host is ready

RU-origin scope:

- RU-origin release evidence is scoped to `POKROV` public hosts, API health, and delivery-node reachability from a Russian vantage point
- the RU-origin release verdict must be computed only from the POKROV-owned target set and the explicitly tracked reserve ingress checks
- if a probe payload contains extra non-release targets, keep them as incidental diagnostics only and do not fold them into the RU-origin verdict

Required checks on each run:

1. confirm the probe host can reach `google.com`
2. confirm the probe host can resolve and reach the current public `POKROV` surfaces when needed
3. confirm the probe host can reach the intended node endpoints used by current subscriptions
4. measure the path as separate probe stages instead of one flat `ping`:
   - `DNS`
   - `TCP/443`
   - `TLS`
   - `large-body HTTPS >=64KB`
5. confirm the current reserve ingress state from RU:
   - `xhttp_alive`
   - `hysteria_alive`
6. record failures in a compact operator-readable report

Minimum report fields:

- UTC timestamp
- probe host label and public IP if known
- whether `google.com` was reachable
- node-by-node status
- per-target split health for `DNS`, `TCP`, `TLS`, `HTTP`, and `UDP` when applicable
- `probe_classification`
- `ipv4_health`
- `ipv6_health`
- `transport_health`
- recent smart-connect shortlist stickiness and RTT-quality evidence when install-scoped samples exist
- reserve status for `xhttp_alive` and `hysteria_alive`
- derived classifications such as `probe_host_problem`, `canonical_host_problem`, `foreign_edge_problem`, `eu_node_problem`
- notes for DNS, TCP, TLS, or route anomalies

Escalation rule:

- if `google.com` is unavailable from the RU probe host, treat the run as a probe-environment failure first
- if `google.com` is reachable but one or more `POKROV` nodes are not, treat the result as a node or public-edge incident
- if canonical `pokrov.space` surfaces fail while `kiwunaka.space` still works, treat that as a hostname migration incident and prioritize the canonical path

Operator response:

1. confirm whether the issue is probe-host-specific or reproducible elsewhere
2. compare the failing nodes against control-plane health and recent deploy activity
3. check DNS, TLS/SNI, and port reachability on the affected path
4. drain and resync unhealthy nodes before disabling them if recovery fails
5. keep support informed with the canonical hostnames only

Vantage-point reporting rule:

- `current-origin check` means the probe ran from the operator workstation currently in use
- `brain-origin check` means the probe ran from the control-plane host `82.21.114.104`
- `RU-origin check` means the probe ran from `mini` or a replacement external RU host
- do not collapse these into one status line because each origin answers a different question
- do not call a node RU-broken until an `RU-origin check` actually fails from a working RU probe host
- if SSH, admin auth, provider dashboard, physical device, or RU probe access is missing, report the affected origin as `BLOCKED_BY_ACCESS` and name the missing dependency instead of treating the check as passed or failed
- `current-origin check` is allowed to use local repo/static gates, browser/API probes, and non-secret public endpoints; it does not prove what `brain` or a Russian network can reach

## Node Metrics Freshness And Alerts

The admin and operator view must treat node freshness per node, not only as one global timestamp.

Required node-level visibility:

- freshness state for each node
- `hoster_family`
- `hoster_asn`
- `subnet`
- sustained CPU / RAM / disk pressure alerts
- live `online_keys_now` count per node from panel runtime
- live `online_connections_now` count per node from panel runtime `ip_count` with a per-key fallback when the panel omits it
- current Ethernet RX/TX throughput in `Mbps`
- 24h peak Ethernet throughput in `Mbps`
- port-capacity utilization against the default `1 Gbit/s` node uplink
- sustained latency / error-rate alerts
- high client-density alerts
- observer collector freshness per node
- observer parse-error and unmatched counters per node
- `last_probe_stage`
- `last_probe_error_kind`
- `last_probe_error_message`
- `probe_classification`
- `ipv4_health`
- `ipv6_health`
- `transport_health`

Metrics freshness state rules:

- `ok`: the node has a recent metrics sample, expected numeric totals are present, dataplane probe fields are present, and observer freshness is inside the configured window when observer-lite is enabled
- `stale`: the last metrics or observer sample exists but is older than the freshness window; show the last timestamp and age rather than zeroing values
- `missing`: no usable sample exists for the node or a required counter family is absent; render the field as missing/unavailable, not as `0`
- `unavailable`: the metrics collector, admin metrics endpoint, panel runtime, or probe path could not be reached from the checking origin; show the failed origin and blocker, such as `brain-origin BLOCKED_BY_ACCESS` or `panel unavailable`
- `failed`: the collector or probe ran and returned an explicit failure classification, such as DNS, TCP, TLS, HTTP body, transport, packet loss, high latency, overload, high CPU, or offline
- per-node cards must keep `panel_state`, `dataplane_state`, metrics freshness, observer freshness, and RU-origin evidence separate so one unavailable layer does not hide useful evidence from another layer
- high CPU, high RAM, high disk, high latency, high packet loss, high client density, overload, stale metrics, missing observer data, and offline states must be operator-visible as alert reasons, not folded into a generic red status

Operator-facing rendering rule:

- distinguish real `0` from missing telemetry; `RAM`, disk totals, and free space must show that metrics did not arrive when totals are absent
- current node-card latency and dataplane probe in admin are collected from the control-plane host `brain`
- do not confuse the `brain -> node` control-plane probe with the separate external RU probe result
- node cards should show both `online_keys_now` and `online_connections_now`; these are live runtime numbers, not observer-lite history
- current Ethernet throughput in admin comes from the live panel/server metrics collected by `brain`
- if network counters are missing, the admin surface must show missing telemetry rather than `0 Mbps`
- use the current and 24h peak Ethernet view for capacity planning, server purchase decisions, and early warning before saturating the `1 Gbit/s` uplink
- keep raw probe fields visible, but add a readable operator explanation for known probe failures
- do not use `ping` as the consumer-path health authority; prefer probe stage, TLS/body stage, and transport-health output
- for `reality_target_mismatch`, explain that the expected REALITY target name did not match the certificate name or SNI returned by the node
- if a node shows field failures with an otherwise green basic TLS probe, treat the current REALITY camouflage target as suspect and be ready to rotate it instead of assuming the dataplane is healthy
- when rotating a REALITY target, update both the node runtime inbound (`dest` plus `serverNames`) and the `brain` `nodes.reality_sni` value in the same task so drift, subscriptions, and operator diagnostics stay aligned
- prefer country-appropriate, normal public TLS targets for each node; avoid keeping a generic target after it has shown region-specific failures in the field
- when a failure is provider- or family-specific, fail over by `subnet` first, then by `hoster_family`, and only then by country label

Operational rule:

- `portal-node-metrics.timer` must stay healthy on every relevant host
- `portal-daily-healthcheck.timer` runs on `brain` once per day at `06:30 UTC` / `09:30 MSK` and writes a JSON summary under `/root/portal_bot/health_reports/`
- the daily summary checks API health, `portal-api-healthcheck.timer`, `portal-node-metrics.timer`, per-node metrics freshness, DB `user_nodes` expected counts, and real 3x-ui managed-client counts
- daily panel counts must compare only managed identities (`tgId` or `User_<tg_id>`); legacy/manual 3x-ui rows without a POKROV managed identity are tracked as `unknown_rows` and require a separate cleanup decision before deletion
- `portal-node-observer.timer` must stay healthy on every rollout node where `observer_push_secret` is configured
- hoster CPU warnings should trigger a review of per-node metrics plus control-plane load on the canonical host
- code deploys for the metrics collector must ship both `collect_node_metrics.py` and `node_dataplane_probe.py`, otherwise the systemd job will fail with an import error on the control-plane host
- newly enabled delivery nodes must be verified with both subscription output and panel `active_clients`; database `user_nodes` mappings alone do not prove the clients exist on the 3x-ui inbound

Runtime telemetry wave `2026-06-02`:

- `/api/admin/nodes/runtime` is a read-only live panel snapshot for operator diagnosis: panel auth result, panel latency, auth mode indicator, current online counts, server status, and managed inbound details
- runtime panel fields must be labeled as execution confirmation only; they must not override Postgres truth for tariff, trial, premium/free access, subscription status, or user entitlement
- a failed runtime snapshot for one node must not hide database health or metrics freshness for other nodes; admin UI should show partial results and the failing node error
- `/api/funnel/events` stores anonymous marketing-site funnel events in `funnel_events` without IP address or user-agent retention
- `/api/admin/funnel/summary` combines anonymous site events with known `events`, `pay_attempts`, and `external_orders` to show the operator path: site entry, cabinet/bot open, checkout start, paid confirmation, and connection confirmation
- funnel counts are operational direction signals, not billing reconciliation; paid truth still comes from signed provider callbacks and fulfillment records

Primary repository touchpoints:

- `scripts/collect_node_metrics.py`
- `scripts/node_dataplane_probe.py`
- `scripts/collect_xray_observer.py`
- `scripts/remote_install_node_observer.py`
- `portal_bot/daily_panel_node_healthcheck.py`
- `infra/portal-daily-healthcheck.service`
- `infra/portal-daily-healthcheck.timer`
- `infra/portal-node-metrics.service`
- `infra/portal-node-metrics.timer`
- `infra/portal-node-observer.service`
- `infra/portal-node-observer.timer`
- `/api/admin/metrics/status`
- `/api/admin/nodes/health`
- `/api/admin/nodes/runtime`
- `/api/admin/funnel/summary`
- `/api/funnel/events`
- `/api/internal/observer/batches`

Observer-lite rollout rule:

- delivery nodes that participate in observer-lite must keep a stable xray access log at `/var/log/xray/access.log`
- install collector/logrotate/timer with `scripts/remote_install_node_observer.py`
- rollout starts with one canary node for `24-48h`
- only after low parse-error and unmatched rates on the canary can the timer be enabled on the rest of the delivery pool

## Suggested RU Probe Workflow

Existing repository helpers:

- [scripts/remote_brain_network_probe.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_brain_network_probe.py)
- [scripts/release_gate_check.py](C:/Users/kiwun/Documents/ai/VPN/scripts/release_gate_check.py)

Repository helper added for reporting:

- [scripts/ru_probe_runner.py](C:/Users/kiwun/Documents/ai/VPN/scripts/ru_probe_runner.py)
- [scripts/render_ru_probe_report.py](C:/Users/kiwun/Documents/ai/VPN/scripts/render_ru_probe_report.py)
- [scripts/ru_probe_sample.json](C:/Users/kiwun/Documents/ai/VPN/scripts/ru_probe_sample.json)

Recommended external RU probe flow:

1. run the actual reachability checks from the external RU host
2. save the raw JSON result locally or copy it back into the repo workspace
3. render a compact operator summary with `render_ru_probe_report.py`
4. attach the rendered summary to the operator handoff or incident thread

Example:

```powershell
python scripts/ru_probe_runner.py --reserve-host rf1.pokrov.space --probe-host mini --out ops-local/ru-probe.json
python scripts/render_ru_probe_report.py --input scripts/ru_probe_sample.json
```

RF role split:

- `mini` / `RFMINI` is the canonical RU probe origin and universal operator sandbox
- `rf1` is the reserve ingress for operator and VIP/manual access
- owner-approved exception on `2026-06-01`: `mini` may carry emergency `ru_bridge_relay` traffic on `tcp/443` for allowlisted or incident-promoted cohorts, bridging only to POKROV delivery nodes except US
- do not treat `rf1` as a general delivery node until repeated RU probes prove stability
- owner-approved exception on `2026-04-24`: the dedicated free node (`151.245.217.23`) also runs the Telegram-only `portal-mtproto.service` on `tcp/9443`; monitor it separately from POKROV delivery-node health and do not count it as normal subscription traffic

Current backlog note:

- RU ingress / RF reserve experiments are paused
- `rf1` promotion remains paused
- `mini` bridge work has resumed only for `ru_bridge_relay`; keep separate evidence for probe health, bridge listener health, and downstream non-US target reachability
- the MTProto exception does not reopen the paused RF reserve canary; the earlier `mini:443` attempt remains disabled and separate from POKROV delivery-node health

Interpretation note:

- a successful `current-origin check` only proves reachability from that current workstation
- a successful `brain-origin check` only proves control-plane reachability
- missing `RU-origin check` data means RU-specific conclusions remain unproven, even if another origin succeeds or fails
- a green `ru_bridge_relay` listener does not prove normal RU-origin readiness; it only proves the bridge contour is available for the selected cohort/profile

When handing this off, use:

- [ru-origin-probe-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/ru-origin-probe-handoff.md)

Reserve interpretation:

- `xhttp_alive=true` means the TCP reserve path remains available for operator and VIP access
- `hysteria_alive=true` is still best-effort and should be treated as a UDP viability signal until repeated RU checks confirm it
- if `xhttp_alive=true` while canonical hosts fail, preserve the reserve contour and keep the default consumer path unchanged
- while the RF reserve idea is in backlog, keep collecting probe evidence but do not treat reserve-path improvements as active roadmap work

Telegram MTProto proxy interpretation:

- `portal-mtproto.service active` proves the Telegram proxy daemon is running on the free node
- `current-origin check` and `brain-origin check` should verify `151.245.217.23:9443/tcp` separately from HTTPS checks because MTProto is not an HTTP service
- free-node reachability to `core.telegram.org` controls whether the daily config refresh timer can stay enabled
- if `mini` is considered again for the standard release probe, a fresh RU-origin check must prove POKROV host/API/node reachability first; any separate proxy work stays outside the standard RU-origin release verdict
- the MTProto link and secret are operational secret material and should stay in `/etc/portal-mtproto.env`, not in docs or incident reports

## App, Bot, Device, And IP Visibility

The support and operator stack should be able to correlate these domains of information for one user/account journey:

- app account
- linked Telegram account if present
- device records
- last known IP context
- subscription and node context

Useful operator-visible fields include:

- internal account identifier
- linked Telegram user ID and current username if linked
- `install_id`
- `device_name`
- `platform`
- `model`
- `app_version`
- `last_ip` or equivalent last seen public IP field
- current subscription status
- assigned node or recent node history when available
- current `online now` node list for the key from panel runtime
- recent observer node/IP history as a separate "seen recently" layer

Operator interpretation rule for shared-family keys:

- "online now" should be treated as live key/runtime presence on one or more nodes
- observer-lite should be treated as recent evidence of where the key was seen, not as proof of a current active session
- without a separate per-device identity model, one shared key can show multiple simultaneous runtime connections but still represents one subscription identity
- effective admin status: `active`, `expired`, `blocked`, `manual_test`
- observer state: `ok`, `watch`, `suspicious`
- observer reasons, recent IPs, recent nodes, and last observed time

Visibility rule for non-app configs:

- runtime IP and observer-lite visibility must keep working for imported/manual configs even when the official app was never installed
- app device records remain a separate app-first telemetry layer and must not be treated as the only source of "devices in use"

Visibility rule:

- this data exists for support diagnosis, abuse control, and account recovery
- it must not be echoed back to public marketing copy as surveillance language
- user-facing support copy should describe this as technical context used to help diagnose connection issues
- observer-lite phase 1 is `observe-only`: no auto-block, no auto-throttle, no Telegram operator spam
- when observer-lite has no observations yet, admin surfaces should show an explicit empty state instead of presenting zero-only counters as meaningful observations

## Support And Incident Triage

When the user says "the app, bot, or site is not working", triage in this order:

1. confirm they are using `pokrov.space` or `app.pokrov.space`
2. check whether the account has a linked Telegram identity
3. inspect the most recent device record and `last_ip`
4. inspect current node and subscription status
5. compare with the latest RU probe result and backend health

Typical patterns:

- Telegram opens but web login fails: check canonical hostname routing and web session handoff
- one device fails while another works: compare `device_name`, `platform`, `app_version`, and `last_ip`
- multiple users fail in the same geography: compare RU probe output and node reachability
- old profile works only through `kiwunaka.space`: migration is incomplete; keep compatibility but move the user toward `pokrov.space`

## What Is User-Visible Versus Operator-Visible

User-visible:

- official domains
- whether Telegram is linked
- visible device names inside the app
- support prompts asking for a short issue description

Operator-visible:

- device and session context
- linked Telegram identifiers
- recent IP context
- node assignment and reachability clues
- incident history and probe results

Manual/test cleanup policy:

- only explicit manual/test users are eligible for destructive cleanup in admin
- operators should keep real-user cleanup out of routine admin tooling

Only collect and expose the minimum operational context needed to diagnose service problems and keep the app-first account model working reliably.
