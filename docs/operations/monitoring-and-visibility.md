# Monitoring And Visibility

Last updated: 2026-08-21

## Document Status

This file is living source of truth for hostname migration policy, external RU probe operations, and operator visibility into app, bot, device, and IP context.

Current procedure owners:

- [Publishing And Signing Guide](C:/Users/kiwun/Documents/ai/VPN/docs/operations/publishing-and-signing-guide.md) for artifact creation, signing, publication, and exact-candidate handoff verification
- [Deployment And Access](C:/Users/kiwun/Documents/ai/VPN/docs/operations/deployment-and-access.md) for runtime metadata application and deploy access
- [RU Origin Probe Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/ru-origin-probe-handoff.md) for the active external RU probe checklist
- [Support Macros](C:/Users/kiwun/Documents/ai/VPN/docs/launch/support-macros.md) for user-facing incident wording

Retained evidence, not current procedure authority:

- [Email Delivery Webhook Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/email-delivery-webhook-handoff.md)
- [Release Links And Final Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/release-links-and-final-handoff.md)

Monitoring owns hostname, origin, probe, metrics, and operator-telemetry truth.
It does not recreate release metadata or signing steps. Keep `current-origin`,
`brain-origin`, and `RU-origin` as separate evidence lines; use the publishing
and deployment owners above for candidate and runtime handoff procedures.

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

## First-party Acquisition And Product Funnels

POKROV uses only its own bounded funnel telemetry. No advertising SDK or
third-party marketing tracker is part of this contract. The allowed questions
are: where the person came from, which POKROV step they reached, what action
they completed, and where the journey stopped.

Acquisition data keeps normalized first/last touch values for `source`,
`campaign`, `content`, `ref`, entry route, channel, and referrer host. It may
record an approved asset click, bot intent, checkout start, provider-confirmed
payment, account/app continuation, and confirmed connection. It must not retain
raw browser session ids, raw URL/query strings, IP addresses, user agents, VPN
destination history, support message bodies, credentials, connection material,
or provider payloads. Browser sessions are retained for `180 days`; one-time
cross-surface handoffs expire after `72 hours` and cannot grant access.

The `/funnel` admin screen deliberately exposes two separate cohorts:

- `Реклама`: browser acquisition sessions whose first touch is inside the
  selected period. Its lineage is entry intent → resolved handoff → linked
  checkout → provider-confirmed paid → confirmed connect. Missing handoff is
  `unknown`; no IP/UA/timestamp fingerprinting is allowed.
- `Продукт`: distinct known users with an app/account open inside the period.
  Checkout, paid, and connect sets are intersected with the preceding known-user
  set. Overlapping `events`, Telegram Stars attempts, and external orders must
  not inflate one person into several conversions.

Every downstream numerator is a subset of its preceding denominator. Payment
truth comes from signed provider callbacks and entitlement records, never from
marketing events. The aggregate response and UI must not enumerate anonymous
session hashes, handoff tokens, Telegram/account/order ids, or raw event rows.

The funnel's paid numerator reads only paid `external_orders` and Stars
`pay_attempts` with a recorded payment time. Client `paid`/`renewed` events
remain diagnostics. Its connected numerator requires a durable
`ConnectionEvidence` row of kind `observer_connection`, observed at or after
that cohort's first qualifying payment and within the selected period's end.
Client `connected_ok`, self-report and cached first-connection timestamps do
not establish this outcome; an earlier trial connection does not count as a
post-payment connection. The existing commercial conversion projection
separately binds campaign/offer/order/grant and renewal/reversal lineage.
Literal IP referrers are discarded before persistence and cannot become an
automatic acquisition source; an absent source remains `unknown`.

Commercial capacity is a separate entitlement-owned projection. The
`capacity_automation` object on `GET /api/admin/campaigns` shows exact commercial
revision/SHA, active units, the 300-unit limit, current band, 70% pause and
strict-below-65% resume thresholds, pending reservation forecast, gate reasons,
per-campaign caps/paid/reservation counts and evaluation freshness. Alert on a
stale worker/readback or a live auto-managed campaign at a forbidden capacity
band. Do not treat projected pending units, node telemetry, clicks or funnel
counts as entitlement truth. Transition evidence is the bounded `AdminAudit`
chain `capacity.auto_pause|auto_hold|auto_resume`; a dashboard read performs no
mutation.

## Transport Rollout Visibility

User360 and support attempts include bounded connectivity self-reports when the
client supplies them. Compare server assignment at report time with fetched,
staged and effective revision references and protocol families. The card exposes
mismatch, client proof stage, observation age (or unknown) and a safe next step.
No connectivity IP, topology, key or config is returned. Existing sensitive-field
permissions and audit apply. Reports are correlated per client run/attempt and
the highest sequence wins within that attempt; an informational report does not
replace its success/failure outcome. Client evidence is not server-observed
traffic, and a historical assignment is not a live policy lookup.

Transport rollout must stay visible to operators instead of being buried in opaque config.

Visibility rule:

- admin and operator views should show `transport_health`, `probe_classification`, `ipv4_health`, and `ipv6_health` alongside node freshness
- the active transport profile should be readable from node health so operators can tell whether a node is still on `legacy_reality_fallback`, has moved to `grpc_443_primary`, or is reserved for `operator_lab`
- `network_rollout_config` is the operator-owned source of rollout policy and should be checked whenever transport or DNS diverge by cohort
- qdisc rollout evidence should stay operator-visible through `infra/node-qdisc-profiles.json`, `scripts/remote_apply_node_qdisc.py show`, `tc -s qdisc`, and `scripts/remote_node_qdisc_smoke.py`
- admin node health must show `panel_state` and `dataplane_state` separately; panel failure must not suppress dataplane probe evidence
- operator-readable node context must include bounded `hoster_family`, `hoster_asn`, `root_cause_summary`, `root_cause_detail`, `telegram_app_path`, and `telegram_web_path`; it must not retain or render target names, SNI, IP addresses, certificate names, or raw exception text
- `operator_lab` allowlists are control-plane data, not user-facing diagnostics, and must not leak into public UI or support copy
- if a failure is provider- or family-specific, fail over by `hoster_family` and then by country label; endpoint-derived subnet data is not retained
- release and incident reports must keep `current-origin check`, `brain-origin check`, and `RU-origin check` as separate evidence lines
- do not collapse those origins into a single verdict because each origin answers a different question
- a fronted Smart DNS lab must expose frontend route readiness, loopback backend health and service state as separate bounded fields; never retain client addresses, queried names, application SNI or payloads, and never turn source/bundle readiness into live access proof

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

- the managed manifest and `/api/client/nodes/candidates` expose shortlist-level `health_score`, `cpu_percent`, `panel_latency_ms`, `backend_penalty`, `cpu_penalty`, `capacity_state`, `capacity_score`, `tx_ratio`, `tx_mbps`, `shortlist_revision`, and stickiness metadata
- `health_score` is an ordering signal, not a standalone functional kill switch; scores below `60` apply a large backend penalty while explicit failures such as stale metrics, disabled/draining state, dataplane down, CPU hot, packet loss, TCP retransmit, or network saturation remain the hard-reject reasons
- accepted client RTT and node-selection uploads are stored through the `smart_connect_latency_sample` event with `install_id`, `carrier`, `platform`, selected node, previous node, accepted RTT samples, selection mode, and whether stickiness was applied
- operators should be able to reason about recent RTT quality by node, carrier, and platform without exposing raw samples in public consumer UI
- subscription renders should record `subscription_fetch_events` and `rendered_subscription_snapshots` with token fingerprints, resolved format, node order, excluded-node reasons, status, and content hashes, never raw tokens or rendered subscription bodies
- shortlist evidence must respect effective `TRIAL`/`PAID` entitlement; legacy free-pool rows are retirement evidence and never authorize live delivery

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

## Automatic client access-network context

Android reports on app open/connect/running/failure, at most once per minute
per account in a process. Support → User → Events shows the latest source
IP, carrier and approximate region with observation time. Access requires
`support.sensitive.read` and records `support.network_context.read` in audit.
L1 sees no network values. Unavailable direct API transport shows unknown IP;
an old observation never proves the present connection's source address.

The existing supervised anti-abuse worker clears raw IP and
`client_network_metadata` within 72 hours; backlog includes the new field.
No separate worker/database is introduced. An operator-local City MMDB at
`CLIENT_NETWORK_GEOIP_CITY_DB_PATH` enables subdivision lookup. The existing
country MMDB alone may provide country while region stays unknown. Neither
lookup transmits IP to a third party. Local fixtures do not establish deployed
Android-to-API evidence or physical carrier/geography accuracy.

## Security Abuse Visibility

`/api/admin/metrics/status` includes a `security` block with 24-hour counters
from `security_events`.

Track these as operator-facing abuse signals:

- `rate_limit_hit`: brute force, token scanning, callback spam, or broken automation
- `payment_callback_invalid_signature`: bad provider auth/signature attempts
- `support_upload_reject`: one event per rejected upload with a stable bounded reason; `store_failed` is reserved for non-HTTP storage/persistence failure
- `support_attachment_denied`: private attachment access mismatch
- `admin_access_denied`: non-admin account attempted admin access
- `subscription_lookup_failed`: unknown subscription token lookup, usually token scanning when repeated

Operational rules:

- these events must not contain bearer tokens, payment secrets, raw callback bodies, subscription URLs, or attachment bytes
- repeated `subscription_lookup_failed` from one origin is an abuse signal even when delivery nodes are healthy
- callback failure spikes should be checked against provider dashboard status before treating them as user payment failures
- volumetric DDoS is still outside the guarantee of app-level counters; correlate with HAProxy, hoster, and firewall evidence

Support attachment and encrypted-bundle visibility for this candidate is
metadata-only:

- `shared/contracts/support/` defines the signed recipient-key and short-lived
  extended-policy shapes. The authenticated route records bounded case/upload,
  offset, status, byte-count and failure-code metadata only. It never logs,
  decrypts or parses ciphertext. The isolated worker validates content in
  memory and keeps only the original encrypted envelope in accepted/quarantine
  storage. Local route/worker/client tests are not production key custody,
  storage, deploy, rotation, schedule or successful-upload evidence;

- `ticket_attachment_uploaded` logs owner ID, canonical media type, stored private reference, and byte count, never file bytes or payload content;
- `support_upload_reject` is emitted once for each HTTP format, body-size, attachment-size, or pending quota rejection, including oversized streaming reads; it includes only a stable reason and status. Non-HTTP storage/persistence failure uses `store_failed`. Filename, body, bytes, and private payload are excluded;
- `store_failed` can include an ambiguous database commit acknowledgement after final rename. The upload path preserves that final file, so operators must correlate redacted row/file and cleanup counts instead of treating the event as proof that no row committed. A rowless final is expected to remain until the configured safety grace and reconciler pass;
- `support_attachment_denied` covers bound-ticket or legacy-owner download mismatch;
- supervised `support_attachment_cleanup` logs integer-only local counters for expired rows/files, missing or row-reappeared expired files, old temp files, rowless canonical files, selected file candidates (`file_candidates_selected`), total directory entries enumerated (`filesystem_entries_enumerated`), bounded DB rows scanned, DB rows whose canonical file is missing, malformed names skipped, file errors, and file/row cycle-wrap flags. The DB missing-file counter is non-destructive and includes bound, unexpired, and legacy rows within the deterministic query limit;
- a worker-held process-local cursor freezes one filesystem mtime cutoff and one DB max-ID high-water per cycle, then advances by filename and row ID. Newer entries do not extend the active cycle; integer wrap flags expose exhaustion, while names, IDs, cutoffs, and cursor values are never logged. Worker restart discards active snapshots and begins new cycles;
- file candidate processing and selection memory are bounded by `SUPPORT_ATTACHMENT_CLEANUP_SCAN_LIMIT`, but candidate selection enumerates the whole upload directory once per run and `filesystem_entries_enumerated` can therefore exceed that limit. Treat large-directory latency as a production manual gate rather than a locally proven bound;
- operators should track redacted counts of pending unexpired, expired unbound, bound, and dangling ticket/message rows during migration rehearsal and backup/restore. No raw stored name, owner payload, or attachment body belongs in a shared metric label;
- local SQLite counters, worker wiring tests, and E2E requests are not proof that the production worker schedule, PostgreSQL, reverse proxy, or filesystem behavior is live.

## Telemetry Retention

`portal_bot/worker.py` runs a supervised telemetry retention job. It prunes high-volume backend telemetry while keeping payment order rows as the reconciliation ledger.

Default retention windows:

- `EVENT_RETENTION_DAYS=90` for raw product/error `events`
- `FUNNEL_EVENT_RETENTION_DAYS=90` for raw `funnel_events`
- `PAY_ATTEMPT_RETENTION_DAYS=365` for Telegram Stars `pay_attempts`
- `EXTERNAL_PAYMENT_EVENT_RETENTION_DAYS=180` for raw provider callback event logs
- `SUBSCRIPTION_EVENT_RETENTION_DAYS=90` for subscription fetch/render logs
- `RU_PROBE_RETENTION_DAYS=180` for unheld RU probe runs, their normalized
  target results, and routine uploader heartbeat history
- `TELEMETRY_RETENTION_INTERVAL_SECONDS=21600` for cleanup cadence

Do not use this job to delete `external_orders`: those rows remain the payment ledger and are needed for reconciliation, refund/chargeback review, and launch evidence.

The separate supervised `antiabuse_retention_job` owns sensitive IP/HMAC field
deadlines. Defaults and hard bounds:

- raw-IP code cap: 72 hours;
- full-IP HMAC code cap: 7 days;
- IPv4 `/24` or IPv6 `/64` prefix HMAC code cap: 90 days;
- `ANTIABUSE_RETENTION_INTERVAL_SECONDS=300`, clamped to 60-900 seconds;
- `ANTIABUSE_RETENTION_MAX_BATCHES_PER_RUN=20`, clamped to 1-100 batches per
  thread chunk;
- `ANTIABUSE_RETENTION_BATCH_LIMIT=1000`, capped at 10000 rows per field and
  transaction.

Each chunk fixes its observation time, commits bounded `SKIP LOCKED` batches
outside the asyncio event loop and yields after its configured batch cap.
Remaining backlog retries after one second. Alert on a stopped `portal-worker`,
job exceptions, or persistent backlog. The windows are an operational SLO, not
a PostgreSQL TTL. During an incident or guarded rollback, use
`python scripts/cleanup_antiabuse_retention.py` for read-only counts and add
`--apply` only for an explicit one-shot drain. The JSON contains counts, not
database URLs or row contents.

Do not prune an RU run while `retention_hold=true`. Exact-candidate release
evidence sets that hold together with a redacted reason; routine retention may
remove only unheld data older than the configured window.

## External RU Probe Policy

Required cadence:

- every `6 hours`

Required probe origin:

- an external RU node or other external RU vantage point that is outside the control-plane host

Availability rule:

- `mini` / `RFMINI` is the canonical RU-origin operator sandbox and preferred RU probe host
- if `mini` TCP reachability is present but SSH auth fails, treat the run as `RU-origin check: BLOCKED_BY_ACCESS`, not as proof that RU visibility is absent
- if `mini` is actually down, treat RU-origin observability as degraded until a replacement external RU host is ready
- `mini` remains a bridge/sandbox, not a normal RU delivery node
- the planned new RU server may become both a full RU node and a second bridge; until it has probe evidence, treat it as planned capacity only
- bridge health, RU-node health, and RU-origin release readiness must be separate fields in operator notes

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

### RU Probe Read Model And Freshness

Canonical timing:

- runner cadence: every `6 hours`
- last eligible run becomes stale after `7 hours`
- uploader heartbeat becomes stale after `45 minutes`
- uploader retry cadence: every `15 minutes`
- database retention: `180 days` for unheld RU runs and associated routine
  telemetry

The extra hour between the 6-hour schedule and the 7-hour stale boundary is a
delivery grace window, not permission to skip a run. `adminapp` may poll the
read model every minute, but that polling neither runs the probe nor refreshes
the evidence timestamp.

Server verdict semantics:

- `ok`: a current eligible run exists and the scoped POKROV checks passed
- `degraded`: current evidence is usable but partial/non-release diagnostics
  require attention
- `failed`: the runner completed and returned an explicit scoped failure
- `stale`: a previously eligible result exists but is older than 7 hours
- `missing`: no eligible result has been stored
- `unavailable`: the read source could not be queried; this is not a zero or a
  failed RU run
- `BLOCKED_BY_ACCESS`: signed or operator-retained evidence says the required
  probe access was unavailable; it must not be converted to `PASS`

Keep four independently useful layers on each node card:

1. `brain` metrics freshness and control-plane dataplane probe
2. panel/runtime state
3. observer-lite state
4. RU-origin result and uploader health

A successful `brain -> node` check cannot replace RU-origin evidence. A stale
heartbeat does not rewrite the last stored run as failed; it means new results
may no longer be arriving. A missing run and an unavailable admin endpoint are
different operational incidents.

The read boundary is:

- `/api/admin/probes/ru-origin/latest` for the global and per-node current view
- `/api/admin/probes/ru-origin/runs` for bounded history
- `/api/admin/probes/ru-origin/uploader-status` for spool delivery health

These endpoints return normalized, redacted state from `ru_probe_runs`,
`ru_probe_target_results`, and `ru_probe_uploader_heartbeats`. They do not
return the HMAC secret, private spool artifact, arbitrary response body, raw
subscription material, or host credential.

## Node Metrics Freshness And Alerts

The admin and operator view must treat node freshness per node, not only as one global timestamp.

Required node-level visibility:

- freshness state for each node
- `hoster_family`
- `hoster_asn`
- sustained CPU / RAM / disk pressure alerts
- provisioned key/client count per node as `provisioned_clients_count`; this replaces treating panel `active_clients` as live online load
- live `online_connections_hint` per node when a runtime source can provide it; render it as a hint, not a billing or people counter
- current Ethernet RX/TX throughput in `Mbps`
- 1m and 5m TX/RX throughput in `Mbps`
- 24h peak Ethernet throughput in `Mbps`
- port-capacity utilization against the default `1 Gbit/s` node uplink
- capacity state, capacity score, hard-reject reason, dataplane probe status/RTT, packet loss, and TCP retransmit percentage
- top pressure-key count by node from `key_pressure_state`
- sustained latency / error-rate alerts
- high client-density alerts
- observer collector freshness per node
- observer parse-error and unmatched counters per node
- `last_probe_stage`
- `last_probe_error_kind`
- `last_probe_error_message` only as the same bounded error code as `last_probe_error_kind`, never as raw text
- `probe_classification`
- `ipv4_health`
- `ipv6_health`
- `transport_health`

Metrics freshness state rules:

- `ok`: the node has a recent metrics sample, expected numeric totals are present, dataplane probe fields are present, and observer freshness is inside the configured window when observer-lite is enabled
- `stale`: the last metrics or observer sample exists but is older than the freshness window; show the last timestamp and age rather than zeroing values
- `missing`: no usable sample exists for the node or a required counter family is absent; render the field as missing/unavailable, not as `0`
- a collector sample is complete only when CPU, RAM used/total, disk used/total/free, and both RX/TX counter or rate families are present; an incomplete sample keeps panel/dataplane facts visible with `metrics_state=missing`, but sets current node health false so smart-connect hard-rejects it until a complete sample arrives
- `unavailable`: the metrics collector, admin metrics endpoint, panel runtime, or probe path could not be reached from the checking origin; show the failed origin and blocker, such as `brain-origin BLOCKED_BY_ACCESS` or `panel unavailable`
- `failed`: the collector or probe ran and returned an explicit failure classification, such as DNS, TCP, TLS, HTTP body, transport, packet loss, high latency, overload, high CPU, or offline
- per-node cards must keep `panel_state`, `dataplane_state`, metrics freshness, observer freshness, and RU-origin evidence separate so one unavailable layer does not hide useful evidence from another layer
- high CPU, high RAM, high disk, high latency, high packet loss, high client density, overload, stale metrics, missing observer data, and offline states must be operator-visible as alert reasons, not folded into a generic red status

Operator-facing rendering rule:

- distinguish real `0` from missing telemetry; `RAM`, disk totals, and free space must show that metrics did not arrive when totals are absent
- current node-card latency and dataplane probe in admin are collected from the control-plane host `brain`
- `panel_latency_ms` measures the full `brain -> panel admin API` transaction; it is control-plane latency and must not be labeled or interpreted as user VPN/dataplane latency
- do not confuse the `brain -> node` control-plane probe with the separate external RU probe result
- node cards should show `provisioned_clients_count` separately from any `online_connections_hint`; provisioned count is configured key inventory, not online load
- current 3x-ui online reads use `POST /panel/api/clients/onlines` with the session CSRF header. Each node summary or client snapshot attempts this read once, including when it is unavailable; the next snapshot may retry. An unavailable response remains distinct from a successful empty list and preserves existing last-seen inference.
- the legacy ops overview and Operator Center shift overview execute the synchronous metrics/capacity/alerts projection in Starlette's bounded threadpool. A DB session is created, used, and closed in that worker thread; collecting the overview must not block the API event loop.
- latest per-node health samples use `ix_node_health_samples_node_sampled_id` on `(node_code, sampled_at, id)`. Capacity alert evidence uses `ix_node_runtime_metrics_lower_node_sampled_id` on `(lower(node_code), sampled_at, id)` to match its existing case-insensitive filter. Both B-trees support the descending timestamp/ID order through a backward scan. For a populated PostgreSQL database, create and validate these indexes with `CREATE INDEX CONCURRENTLY` before source rollout; startup migrations then reuse them. Fresh databases and SQLite/maintenance migrations create the same declared indexes.
- current Ethernet throughput in admin comes from the live panel/server metrics collected by `brain`
- if network counters are missing, the admin surface must show missing telemetry rather than `0 Mbps`
- use the current and 24h peak Ethernet view for capacity planning, server purchase decisions, and early warning before saturating the `1 Gbit/s` uplink
- keep stable probe stage, classification, and health categories visible, with a bounded operator explanation for known failures; raw target, SNI, IP, certificate, and exception fields are transient only and must never be printed or retained
- REALITY target validation must parse DNS SAN/CN from the peer DER certificate even when the TLS handshake uses `CERT_NONE`; an absent or unparsable DER certificate is `reality_target_unavailable`, not a healthy target check
- do not use `ping` as the consumer-path health authority; prefer probe stage, TLS/body stage, and transport-health output
- for `reality_target_mismatch`, explain that the expected REALITY target name did not match the certificate name or SNI returned by the node
- if a node shows field failures with an otherwise green basic TLS probe, treat the current REALITY camouflage target as suspect and be ready to rotate it instead of assuming the dataplane is healthy
- when rotating a REALITY target, update both the node runtime inbound (`dest` plus `serverNames`) and the `brain` `nodes.reality_sni` value in the same task so drift, subscriptions, and operator diagnostics stay aligned
- prefer country-appropriate, normal public TLS targets for each node; avoid keeping a generic target after it has shown region-specific failures in the field
- when a failure is provider- or family-specific, fail over by `hoster_family` and then by country label; subnet data is neither retained nor rendered

Operational rule:

- `portal-node-metrics.timer` must stay healthy on every relevant host
- Brain-origin release evidence must derive the active delivery set from the live enabled `nodes` rows, not from the retained operator inventory. Run `python scripts/remote_brain_network_probe.py --brain-ip <brain> --live-enabled-nodes --json-out <artifact>`; its v2 report retains only node code, configured port and bounded TCP status/error category. Host, IP, SNI and raw exceptions are never returned. The legacy inventory mode remains diagnostic-only; use `--node-code`, `--redact` and `--json-out` for a bounded named-target check.
- `python scripts/verify_brain_ready.py --brain-ip <brain> --json-out <artifact>` writes a separate secret-free readiness envelope for required services, listener presence, public/static endpoint checks and redacted subscription-sample counts. It is still a Brain-origin/control-plane check, not authenticated client egress, current-origin, RU-origin or exact-candidate proof.
- `python scripts/remote_brain_runtime_source_probe.py --brain-ip <brain> --source-revision <full-commit> --json-out <artifact>` binds the live tracked backend payload to exact committed Git blobs without deploy or restart. It retains counts and bounded mismatch paths only, accepts exactly `CRLF_TO_LF_ONLY` as a semantic byte normalization and fails on every other difference. Keep this source-identity slice separate from readiness, enabled-node reachability, authenticated egress and regional-origin evidence.
- collector work is bounded to four concurrent nodes and a 45-second overall deadline per node by default; its systemd unit allows 180 seconds for a multi-node cycle. Blocking dataplane probes run outside the asyncio event loop; a timed-out or collector-exception node atomically records a bounded `collector_timeout` or `collector_exception` failure, preserves its last numeric telemetry as historical data, and is immediately hard-rejected without blocking other node samples
- `node_dataplane_probe.py` is an unauthenticated edge-reachability diagnostic only: it reports bounded stage/classification/health categories after DNS, TCP, ordinary TLS, and REALITY target-certificate checks. Its stdout, `--out` artifact, and persisted collector records contain no target, SNI, address, certificate-name, or raw-exception material. Its legacy `dataplane_ok` projection must not be treated as proof that a VLESS/REALITY client authenticated or transferred data through the node.
- when `AUTHENTICATED_EGRESS_ENFORCEMENT_ENABLED=true`, smart-connect eligibility is authorized only by a fresh `authenticated_egress_ok=true`; `false`, missing, expired, or unavailable material is then a hard rejection even when `edge_reachability_ok=true`. With the default rollout value `false`, the collector still records the authenticated result in its dedicated fields but it must not degrade primary node health, score, probe error, or routing eligibility.
- the authenticated probe uses an external bounded adapter configured by `NODE_AUTHENTICATED_EGRESS_ADAPTER` and `NODE_AUTHENTICATED_EGRESS_PROFILES`. The collector sends only the node code, endpoint, and a non-secret profile id over stdin; UUIDs, private keys, REALITY material, subscription URLs, and tokens stay in the adapter's separate owner-managed credential store and must never appear in repository files, command arguments, stdout, metrics JSON, or logs.
- the adapter subprocess does not inherit the collector service environment. It receives only a fixed neutral environment (`PATH`, `LANG`, and `LC_ALL` on Linux; `PATH` and `SystemRoot` on Windows). The adapter must resolve `profile_id` itself through an owner-managed protected fixed path or operating-system credential provider; DB, bot, panel, and canary secrets must not be passed through environment variables.
- on Linux the configured adapter and registry must be absolute regular-file paths, resolve without symlinks, be owned by root or the collector service user, and not be group/world-writable. A path that fails these checks is unavailable and cannot produce PASS.
- the profiles registry has schema `{"schema_version":1,"profiles":{"<node>":{"profile_id":"<id>","expires_at":"<UTC Z timestamp>"}}}` and contains no connection material. Missing/invalid registry entries and expired profiles produce `probe_material_unavailable`, `probe_material_invalid`, or `probe_material_expired`; none can be converted into PASS.
- an adapter may return PASS only after a real core such as sing-box or Xray authenticates with the dedicated canary profile, disables direct fallback, and completes a bounded HTTPS request through that proxy path. A successful TCP/TLS socket, core startup, or handshake viability hint is insufficient. Adapter output is a strict small JSON object with `schema_version`, matching `profile_id`, `status`, `classification`, and `detail_code`; free-text or raw core output is rejected.
- the production-shaped sing-box implementation is `scripts/singbox_authenticated_egress_adapter.py`. It reads its fixed runtime contract only from `/etc/pokrov/authenticated-egress-adapter.json`, resolves the separate protected canary store, exact-matches the requested node/endpoint/profile binding, and starts sing-box with one loopback SOCKS inbound, one VLESS/REALITY outbound, `route.final` fixed to that outbound, and logging disabled. Direct, block, selector, and URL-test fallback outbounds are forbidden by generated-config validation. On Linux, the adapter exposes the marker request only through a fresh `0600` Unix-domain socket inside a fresh `0700` per-invocation runtime directory. Because sing-box SOCKS does not document inherited-FD or Unix-socket listeners, the adapter accepts the internal loopback listener only while `/proc` proves it belongs to the live child before and after the marker request; a pre-existing endpoint, missing ownership proof, or lost child is fail-closed and can never produce PASS.
- the adapter proves egress with Python's SOCKS5 and verified TLS implementations, not curl: it CONNECTs by the configured POKROV-owned hostname, sends a bounded HTTPS GET, and accepts only the configured status plus marker header. The canonical marker route is `GET /api/public/authenticated-egress-probe`, which returns empty HTTP `204` with `X-Pokrov-Egress-Probe: pokrov-authenticated-egress-v1` and no user, token, or customer data.
- sing-box receives a fixed minimal environment and no credential arguments. Its ephemeral config and the one-shot Unix socket are created under the private `/run/pokrov-authenticated-egress` runtime directory with directory/file/socket modes `0700`/`0600`/`0600`, contain no alternative egress path, and are removed after every result. Core stdout/stderr are discarded; adapter stdout remains the single strict response object. The production implementation is Linux-only; on Windows it fails closed rather than treating an unverifiable loopback listener as authenticated egress.
- canary credentials must be dedicated, least-privilege, individually revocable, and time-bounded. Creating the panel client, installing the core/adapter, populating its protected credential store, and setting the two runtime variables are owner-authorized deployment actions; local code and tests do not constitute runtime readiness.
- `portal-daily-healthcheck.timer` runs on `brain` once per day at `06:30 UTC` / `09:30 MSK` and writes a JSON summary under `/root/portal_bot/health_reports/`
- the daily summary checks API health, `portal-api-healthcheck.timer`, `portal-node-metrics.timer`, per-node metrics freshness, DB `user_nodes` expected counts, and real 3x-ui managed-client counts
- daily panel reads run with at most four independent node clients at once; each login/inbound read has a 45-second deadline. Results retain canonical node order, and a timed-out or unavailable panel is recorded as `panel_unavailable` without cancelling other node reads.
- daily panel counts must compare only managed identities (`tgId`, `User_<tg_id>`, or a panel UUID that maps to an expected POKROV user); legacy/manual 3x-ui rows without a POKROV managed identity are tracked as `unknown_rows` and require a separate cleanup decision before deletion
- expected access is satisfied only by an enabled panel client; disabled retained entries stay in inventory counters but do not count as provisioned access
- enabled managed identities outside their expected pool are retained as one count-only access-drift observation with unique-identity and placement totals; this does not page by itself because a legacy or extra placement is not proof of user impact. Missing expected enabled profiles remain actionable issues; disabled unexpected entries remain non-paging inventory.
- daily expected access evaluates each active non-manual user with the current pool policy at the report timestamp: bounded premium trials and premium users use paid nodes; while `FREE_TIER_ENABLED=false`, free/expired users expect no delivery access. The canonical `free_standard` or `free_soft` node rule applies only during an explicitly enabled rollback. Strict node-role failures, ambiguous entitlement projections, and manual/test users are count-only `policy_unresolved` or `manual` evidence, never actionable access drift; retained reports must not contain their Telegram IDs, UUIDs, emails, or raw panel identities
- retained `user_nodes` rows for inactive or retired access are reported in the JSON summary but must not page operators by themselves when panel managed identities match the current expected users
- disabled nodes and control-plane rows must stay visible in capacity payloads when useful, but must not create `node_capacity:*` active alerts merely because their disabled state is intentional
- CPU, RAM, disk, network, panel-API latency, error-rate, and client-density alerts require three consecutive samples by default (`NODE_METRICS_SUSTAINED_SAMPLES`); a single current snapshot must never bypass this window
- a routing `hard_reject` still excludes the node immediately from smart-connect, but Telegram/durable `node_capacity:*` paging requires three consecutive runtime samples by default (`NODE_CAPACITY_ALERT_SUSTAINED_SAMPLES`); disk usage at or above `SMART_CONNECT_DISK_REJECT_PERCENT` (default `95`) is an immediate `disk_full` hard reject, while `SMART_CONNECT_DISK_SOFT_PERCENT` (default `90`) marks the node warm
- authenticated-egress measurements are collected independently of routing enforcement; `AUTHENTICATED_EGRESS_ENFORCEMENT_ENABLED` defaults to `false` and must be enabled only after the rollout inventory has fresh authenticated PASS evidence
- Telegram ops notifications are Russian, action-oriented, omit internal fingerprints, batch simultaneous active/resolved events, and aggregate confirmed capacity hard-rejects into one pool event. Panel API latency stays visible in the admin dashboard but does not page while user-path dataplane/error checks remain healthy. A pool event is `critical` only when every enabled delivery node is affected and the dataplane is also unconfirmed; otherwise it is a warning.
- the daily panel/node check sends Telegram only when the actionable issue set changes, sends one recovery message when it clears, and does not repeat an identical issue set each day. Count-only access-drift observations remain in the retained JSON report without changing daily status or triggering Telegram.
- `error_rate_high` is suppressed while the same node has a confirmed capacity hard-reject incident and clears after the recent health window is healthy, preventing a delayed duplicate incident after recovery
- node metrics collection must parse both 3x-ui `settings` response shapes, JSON string and object/dict, before deriving `provisioned_clients_count`
- `portal-node-observer.timer` must stay healthy on every rollout node where `observer_push_secret` is configured
- `PORTAL_OBSERVER_SOURCE_TIMEZONE` is required on observer nodes whose Xray log timestamps are naive; use `UTC`, `Z`, or a strict fixed offset such as `+03:00` or `-04:00`. IANA names and missing, ambiguous, invalid, or out-of-bounds values are fail-closed: affected lines increment `parse_error_count` and create no connection evidence.
- observer batches must carry only canonical UTC `Z` `occurred_at` values. After collector configuration or timezone changes, manually compare one retained source line with the resulting UTC evidence and exact `activated_at + 5 days` expiry on the same deployed candidate; timer health alone is not this proof.
- hoster CPU warnings should trigger a review of per-node metrics plus control-plane load on the canonical host
- code deploys for the metrics collector must ship both `collect_node_metrics.py` and `node_dataplane_probe.py`, otherwise the systemd job will fail with an import error on the control-plane host
- newly enabled delivery nodes must be verified with subscription output plus provisioned-key evidence from panel/runtime; database `user_nodes` mappings alone do not prove the clients exist on the 3x-ui inbound, and panel `active_clients` must be labeled as configured/provisioned clients rather than online users
- `/api/admin/nodes/capacity` is the operator capacity dashboard source for node state, TX ratio, dataplane, key pressure counts, drain/undrain state, and reject reasons
- `/api/admin/keys/pressure` is the operator key-pressure dashboard source; use it for review/rotation decisions, not automatic family-hostile enforcement
- `/api/admin/subscription/preview` is the operator subscription-debug source for resolved client format, node order, excluded-node reasons, and token fingerprint without returning raw subscription URLs or config payloads
- `/api/internal/nodes/{node_code}/metrics` and `/api/internal/nodes/{node_code}/xray-stats` are HMAC-authenticated ingest paths for node-agent metrics and key traffic rollups; signed node-agent `meta` is an allowlisted bounded schema, not trusted diagnostic text
- admin and subscription reads must re-sanitize legacy `transport_health_json` and probe error fields before rendering, so persisted target, SNI, address, certificate, exception, token, list, nested object, and subnet material cannot be replayed

Runtime telemetry wave `2026-06-02`:

- `/api/admin/nodes/runtime` is a read-only live panel snapshot for operator diagnosis: panel auth result, panel latency, auth mode indicator, current online counts, server status, and managed inbound details
- runtime panel fields must be labeled as execution confirmation only; they must not override Postgres truth for tariff, trial, premium/free access, subscription status, or user entitlement
- a failed runtime snapshot for one node must not hide database health or metrics freshness for other nodes; admin UI should show partial results and the failing node error
- `/api/funnel/events` stores anonymous marketing-site funnel events in `funnel_events` without IP address or user-agent retention
- `/api/admin/funnel/summary` combines anonymous site events with known `events`, `pay_attempts`, and `external_orders` to show the operator path: site entry, cabinet/bot open, checkout start, paid confirmation, and connection confirmation
- funnel counts are operational direction signals, not billing reconciliation; paid truth still comes from signed provider callbacks and fulfillment records

Admin ops app wave `2026-07-06`, command-center redesign updated locally on
`2026-07-23`:

- `adminapp/` is the canonical operator UI for
  `https://admin.pokrov.space/`. Overview plus 17 peer capability routes are a
  frozen direct-entry set mapped by `operator-center.manifest.json` into seven
  target workspaces; five network routes, incident and two support routes now
  use v2 work contracts, while 10 routes remain on compatibility contracts.
  Frontend build, route manifest, expected Admin API schema
  and backend meta identity are separate evidence inputs
- a missing optional deployment identity remains `null` plus an explicit
  warning. A contradictory app, route-manifest hash or frontend/API schema is a
  P0 candidate/deploy mismatch: stop the cutover and use the retained rollback
  target. Local build or plan-only success is not public readback
- the canonical v2 browser path starts with `/api/admin/v2/auth/me` and uses an
  opaque HttpOnly `__Host-` cookie. The browser keeps only the derived CSRF in
  process memory; bearer and raw Telegram initData are absent from Web Storage.
  Missing/revoked/expired sessions, revoked roles, unknown permissions and
  untrusted unsafe origins are access failures, never a healthy source state
- operator bootstrap/revoke/step-up and every successful v2 command retain
  environment plus the exact role/permission snapshot. Governance now exposes
  a bounded explorer/CSV, Action Intent-to-audit command lineage, JIT/break-glass
  review state and a redacted support-bundle access log. Export and sensitive-log
  reads create their own audit rows; local test evidence is not production
  identity, hosted retention-worker or public-deploy proof
- expired temporal roles are authorization failures on the next request. Monitor
  pending JIT/break-glass reviews, active break-glass grants, suspended operators
  with live sessions, and the last-active-superadmin guard. Never resolve those
  conditions through direct table edits during normal operation
- `/api/admin/v2/governance/privacy` reports configured raw telemetry windows,
  support-bundle TTL/hold/backlog counts and field inventory. Treat non-zero
  overdue backlog, file errors or a stopped retention worker as unresolved even
  when the governance read itself is healthy
- the active shell has no fixed desktop sidebar; the overview is a light triage ledger with an incident feed, selected evidence, factual next-step links, separate Brain/RU freshness, and a compact fleet strip
- the first screen uses only its compact overview and RU-latest reads; selecting an incident does not fetch another payload, while charts, full alert actions, and heavy entity cards remain route-local
- the network workspace reads `/api/admin/v2/network/*`. Fleet and Node 360 must
  show inventory, brain/runtime, observer and RU-origin status independently;
  an invalid RU manifest is a failed RU source, not permission to label current
  or brain evidence as RU evidence and not a reason to hide the rest of fleet
- network reads are observation-only: opening traffic, alerts, providers or the
  emergency catalog must not refresh alerts, poll providers, promote catalogs,
  emit notifications or mutate command state. Provider-note text, host/panel
  material, subnets and raw emergency endpoint material are forbidden in the
  browser projection
- migrated node/provider/emergency commands and alert silence must appear in
  the same Action Intent audit lineage. A direct legacy network mutation from
  the canonical frontend is a migration regression; a destructive command
  without high-risk permission plus current step-up is an authorization failure
- global admin search routes operators into user investigation by Telegram ID, username, display name, install ID, order ID, node code, key/email, or related operator identifiers
- v1 does not require Grafana, Beszel, Netdata, VictoriaMetrics, or provider APIs; first-party Postgres tables, collected node samples, usage rollups, and admin API snapshots are the source of truth
- `/api/admin/ops/overview` is the top-level ops snapshot combining a purpose-built compact user/ticket/node summary, one metrics-freshness snapshot, node capacity, free-tier burn, provider cap status, and already durable active alerts; it must not invoke the full `/api/admin/summary` or refresh the alert engine on a browser read
- `/api/admin/online/users` is the bounded live online aggregate for the "Сейчас онлайн" screen; it includes user identity, subscription type, online node/count fields, pressure score, and risk flags, and must not expose raw IP addresses in shared lists
- raw/recent IP details are allowed only inside the individual user card, using observer-backed investigation data already available to admins
- `/api/admin/payments/summary?period=today|7d|30d` is the payments aggregate for revenue, paid count, pending/manual-review/failed counts, and abandoned buy-click/checkout counts
- `/api/admin/payments/orders` remains the order table source; problem orders should be surfaced above the table
- `/api/admin/nodes/health`, `/api/admin/nodes/runtime`, `/api/admin/nodes/drift`, and `/api/admin/keys/pressure` power the health-first node, online, and key-risk screens
- `/api/admin/nodes/drift` derives the REALITY public key in memory from each active inbound's private key and returns only the public key; when an expected PBK exists, an absent or invalid runtime key is drift rather than an unverifiable pass
- A Reality public-profile/listener-port difference can be inspected with `python scripts/reconcile_node_runtime_ports.py --only <codes>`. The default is dry-run and prints only node code, public DB port, live Xray listener port, status, and mismatch names. A port-only difference is `topology_unattested`, not an automatically repairable drift: HAProxy or another L4 frontend may intentionally own public `443` and route to an internal listener such as `10443`. Never rewrite the public profile to an internal port for a fronted node. Applying requires explicit current production authorization, `--apply`, the same exact `--only` allowlist, one current CAS confirmation per node (`--confirm <code:expected_db_port:expected_runtime_port>`), and a separate operator attestation (`--attest-direct-listener <code:expected_runtime_port>`) made only after current node-side evidence proves that no L4 frontend owns or maps the public endpoint. Apply rebuilds the plan from fresh panel snapshots immediately before its DB transaction; both confirmations must match that fresh plan. The DB CAS covers enabled state and every persisted Node field used to resolve the selected profile, so any concurrent metadata change rolls back the batch. Apply aborts the whole batch unless the live inbound has the exact expected inbound id and matches enabled/VLESS/TCP/Reality/SNI/SID/PBK with port as its only difference; it changes only canonical DB inventory, never panels, clients, Xray, or services. A post-commit readback mismatch exits nonzero and triggers only a guarded compare-and-swap compensating rollback from the retained in-memory preimage; output reports the redacted rollback status, and a rollback conflict requires manual owner recovery. After approval, retain the redacted dry-run, topology evidence, exact confirmations, apply output, and post-apply dry-run for the exact candidate.
- `predeploy_node_readiness.py` classifies a public `443` to internal listener difference as `verified_front` only when the node-local transport-front unit is active, its exact loopback backend mapping exists, HAProxy validates the installed config and owns `443`, and Xray owns the mapped listener. Any missing check remains drift; verified fronting never authorizes changing the public profile to the internal port.
- node lifecycle actions in `adminapp` require explicit typed confirmation; node resync supports dry-run before execution
- `/api/admin/v2/growth/broadcasts/{intent_id}/delivery` reads the bounded
  attempts persisted for one frozen broadcast intent. The operator sees
  delivered, terminal/retryable failures, reason categories, attempt timing and
  freshness. Failed-only retry may select only explicit 429 rows and never a
  successful or uncertain recipient. Raw Telegram response text and recipient
  IDs are not returned by the aggregate endpoint. Canonical send/status use the
  v2 growth action-intent boundary; `/api/admin/broadcast` remains compatibility
  execution behind that stored intent, not a second browser write path.
- product/error events use Event Envelope V1: idempotent `event_id`, occurrence
  and receive time, duration, platform/version/surface/subsystem/stage, bounded
  attribution, normalized result/error/retry fields and allowlisted metadata.
  Active user means a distinct account with a confirmed successful connection
  in the rolling seven-day window. The envelope must never contain browsing
  history, destination traffic, raw config, credentials or private chat text.
- operational release health is separate from product events. Authenticated
  `POST /api/client/observability/release-health/batches` accepts at most 100
  strict Operational Event Envelope V1 projections per bounded JSON/gzip body.
  It retains event/build/platform/outcome/catalog-code dimensions in
  `release_health_events` plus one nullable `selected_app_count` integer for the
  exact Android `app.routing.selection.finished` projection. The value is
  bounded to `0..128`; package names, executable names and selected-app lists
  are rejected. Duplicate UUIDs do not increment the cohort and the table has
  no account, install, device, session, correlation, IP, domain, destination,
  package or arbitrary metadata column.
- Android and Windows write the allowlisted operational record to their bounded
  local store before attempting this projection. Upload is best-effort and
  existing-session-only; an unavailable session leaves local evidence intact
  and must not trigger trial or session creation.
- release-health schema/compression/privacy rejects retain only aggregate
  `quarantine.<reason>` counters. Payloads, `Authorization`, `Cookie`, request
  bodies and arbitrary headers are not logged or quarantined. These counters
  are ingest health, not incident, payment, entitlement or support authority.
- `GET /api/admin/observability/release-health` groups current-window events by
  exact release/build/platform identity and reports crash/connect/update counts
  plus deltas against the preceding equal window. Android routing adds only
  `routing_count_events` and `selected_app_count_total`; neither field reveals
  which packages were selected. The known-issue read model is candidate scoped.
  Neither projection carries identity/destination/package fields or mutates
  incidents/releases. Retention emits only integer counters:
  deleted health rows, bundle rows, accepted objects, quarantine chunks, access
  audits, held skips, missing files, and file errors. Non-zero `file_errors`, a
  persistent backlog, or a stopped worker blocks production retention evidence.
- Authenticated
  `GET /api/client/observability/release-health/baseline` is a separate
  fail-closed client projection. Accepted events contribute through a dedicated
  deployment secret to one 12-bit bucket scoped to the exact build and aligned
  UTC week. One authenticated account contributes to one bucket; collisions
  only undercount. Each bucket is capped at 64 total and 32 per-family events,
  and bucket rows expire after 14 days. Fewer than ten distinct buckets returns
  `insufficient_cohort` without an observed count. An available response still
  exposes only closed sample and failure-rate bands for overall, crash,
  connection and update health; it contains no exact totals, bucket indexes,
  account/install/device/session value or stable contributor hash. Missing or
  invalid `RELEASE_HEALTH_COHORT_SECRET` returns unavailable and never weakens
  the threshold.
- L1 support can use the safe bundle summary/timeline but cannot download an
  object. L2/SRE access requires the explicit allowlist, a fixed reason, an
  expiring one-time grant, and retained audit rows. A local RBAC test is not
  evidence that production identities or directory permissions are correct.
- Temporary support-mode issuance is an audited L2 Action Intent tied to one
  case and exact build. Monitor issued/redeemed/expired status and command
  outcomes without logging the activation code, code hash, nonce, signed
  payload or user diagnostic contents. Repeated redeem failures are abuse or
  client-version signals, not permission to weaken owner/audience checks.
- The `PSD1-*` diagnostic decoder is a no-upload read. Its output is bounded
  non-identifying facts and must never be correlated into account/device truth
  without separate authorized evidence. Android/Windows manual export writes
  only the encrypted envelope; export cancellation is not delivery success.
- Production support-mode evidence requires the exact candidate and retained
  proof of visible indicator, <=30-minute expiry, cumulative caps, nonce replay
  rejection, Android SAF export, Windows save dialog and encrypted-only file
  contents. Local source/widget/unit proof remains `I3`, not runtime `I4`.
- the user card exposes a bounded safe event timeline for support diagnosis:
  event name, occurrence/receive time, platform/version/build, subsystem/stage,
  result, normalized error, retryability, duration and network class. It never
  returns arbitrary event metadata, session/device/account ids, trace ids,
  browsing destinations, raw configs or credentials.
- `/api/admin/v2/growth/news-drafts` exposes only bounded RSS-source/run health
  and safe draft metadata; `/api/admin/v2/growth/live-updates` preserves
  `source_draft_id` lineage. `portal-worker` may collect once per day when
  `NEWS_DRAFT_WORKER_ENABLED=true`; it stores no article body, deduplicates by
  source item hash and cannot publish. An editor must write the Russian summary
  and complete the v2 growth L2 `live_update.create` intent.
- release rollout monitoring is candidate- and platform-scoped. The cockpit
  must keep current/brain/RU evidence separate and show diagnostic gates,
  adoption, release-health delta, support-bundle delta, known issues, observation
  deadline and thresholds together. A missing cohort is `MISSING`, not zero.
  Rollout start requires all gates; observation close requires its elapsed
  window and PASS health delta. Pause/rollback request/mismatched artifact
  configuration must make the public client-app response advertise zero rollout.
  `external_artifact_switch=NOT_PERFORMED` is an operator action result, never
  rollback completion evidence.
- `python -B scripts/release_1_2_pb14_candidate_gate.py --release-index-root
  <exact-release-index-checkout> --output <evidence.json>` is the repeatable
  local PB-14 control. It revalidates the retained manifest and detached
  signature against the manifest-bound public keyring, injects one
  identity-free exact-build health regression into an isolated temporary
  database, and requires observation close to fail plus the guarded rollback
  request to advertise zero candidate rollout. Its fixture cohort and
  `external_artifact_switch=NOT_PERFORMED` result are local `I3` evidence only;
  they are not deployed cohort, public promotion or rollback-completion proof.
- consumer access has exactly three effective statuses: `TRIAL`, `PAID` and `PENDING`; every current gift, promo-day grant and operator grant is `PAID`, while raw `FREE` values are legacy storage only
- `/api/admin/free-tier/summary` and `/api/admin/free-tier/users` are retained as `Архив FREE` retirement and historical-observability surfaces; with `FREE_TIER_ENABLED=false` they must show no active delivery keys, mappings, enabled pool membership, or queued/running free-provisioning jobs
- a node reconciliation is complete only when every `TRIAL`/`PAID` account is enabled on each canonical paid-node group and every `PENDING` account is disabled everywhere; aggregate dry-run/apply/readback evidence must contain no raw Telegram ID, UUID, email or connection material
- production readback on `2026-08-19` confirmed the retired-free invariant at zero and reconciled all 67 known accounts: 22 effective `PAID` plus 8 `TRIAL` accounts are enabled on all seven paid nodes, while 37 `PENDING` accounts are disabled on every node. The paid-coverage audit reported zero missing or disallowed mappings. Seven bounded trials may still retain raw `FREE` storage labels; entitlement projection, not that legacy label, decides delivery.
- a scheduled release announcement must execute the existing guarded `live_update.create` and `broadcast.send` actions, use deterministic per-action idempotency keys and retain per-recipient Telegram outcome reasons. `scripts/remote_schedule_release_announcement.py` installs a one-shot persistent Brain timer from a root-only config; a partial broadcast is a failed guarded action and must not be reported as complete.
- `/api/public/live-updates` returns an empty list when there is no active operator-authored update. It must not invent placeholder releases, dates or Telegram post links; expired release cards are removed through guarded `live_update.delete` or disabled through guarded `live_update.update`.
- operators must monitor queued/running/retry/manual-review node-provisioning jobs and must not infer `soft_active` from traffic bytes; the target role/inbound must be confirmed first
- payment-entitlement outbox visibility is integer-only: `pending`,
  `processing`, `delivered`, `dead_letter`, and oldest open age in seconds. The
  worker log reports only integer transition counters. It must not include the
  event payload, provider body, local owner, checkout URL, SQL or parameters;
  stale claims recover after the configured lease and exhausted work remains a
  closed-code dead letter for reconciliation
- payment-provider HTTP telemetry is aggregate and fixed-shape: provider,
  closed operation, HTTP status, integer latency and closed result code, with
  count/total/max latency rollups. `connector_queue_entries` and
  `connector_wait_ms` separately count and time aiohttp connection-queue events;
  snapshots sum entries and retain total/max wait. Time spent still queued when
  a request times out or is cancelled is included (`timeout` / `cancelled`),
  while DNS, connection creation and response reads are excluded. URL/query,
  headers, credentials, request
  fields, response body and exception text are forbidden. A local sample proves
  instrumentation shape only; provider availability, deployed pool saturation,
  timeout rate and latency SLO require exact-runtime evidence
- `/api/health.payment_db` is the bounded-threadpool payment DB projection:
  integer-only active/max-active, started/completed/failed, queue-wait total/max
  and use-case duration total/max. It must never expose SQL, bind parameters,
  account/order identity or exception text. Sustained active=max-active,
  increasing queue wait or failure count is an operator signal, but local tests
  do not establish production pool sizing or latency SLOs
- `/api/health.database_pool` separately reports PostgreSQL connection queue
  `attempts`, `waiting`, `max_waiting`, `timeouts`, `wait_total_ms`, and
  `wait_max_ms`. These fixed integer counters time blocking queue gets,
  including timeout and immediate returns; connection creation, pre-ping and
  SQL run outside that timer. The observer preserves QueuePool limits and
  errors. It uses the `_queue_class` hook in pinned SQLAlchemy 2.0.46, covered
  by an actual saturation/timeout regression; recheck that hook when upgrading
  SQLAlchemy. Counters belong to the active pool and reset on recreation.
  SQLite retains its default pool and returns null for this projection.
- `/api/health.event_loop_lag` observes the API event loop with one lifespan-owned
  monotonic timer at a one-second interval. It retains only `status`,
  `interval_ms`, `samples`, `last_lag_ms`, `max_lag_ms`, and `lag_total_ms`.
  Last/max are null before the first observation; status is `warming_up` until
  then, `collecting` while running, or `failed` if collection stops unexpectedly.
  The task is cancelled and awaited on shutdown (`stopped`); an API used without
  lifespan returns null for this projection. Each new lifespan has fresh counters.
  Timer delay is not request latency or DB/HTTP pool wait; cumulative total/max
  cannot establish p95 or a production SLO. No request or account data is sampled.
- an access-key UUID rotation is not successful on canonical DB or panel-row readback alone: after every affected panel confirms the replacement row, the worker must receive an authenticated Xray restart acknowledgement, then bounded `/server/status` proof from two consecutive samples that `xray.state=running` with no `xray.errorMsg`, and then re-read the panel row. The same apply/readback sequence is required when compensation restores the old UUID. An apply error or post-apply row mismatch is `rotation_runtime_apply_failed` (or `rotation_compensation_failed` during rollback) and requires `manual_review`; it must never finalize the canonical UUID. These panel signals confirm process/config application, not an independent authenticated dataplane canary; the dedicated egress canary remains an operator-run check and is not invoked with a customer identity during rotation.
- `free_standard` and `free_soft` are legacy rollback/cleanup roles only; while free delivery is disabled they must not be selected, provisioned, or fall back to paid or `operator_lab` nodes
- nftables shaper readiness requires Linux canary evidence for syntax, IPv4/IPv6 TCP/UDP throughput, NAT sharing, counters, premium isolation, idempotent setup, and rollback; local dry-run evidence is not production proof
- `/api/admin/provider-quotas`, `/api/admin/provider-quotas/{node_code}`, and `/api/admin/provider-quotas/status` own manual provider/hoster traffic-cap configuration, reset windows, thresholds, status, and audit trail
- `/api/admin/nodes/timeseries` exposes CPU, RAM, disk, network, traffic-counter, and capacity history from `node_health_samples` and `node_runtime_metrics`
- `/api/admin/traffic/summary` groups `key_usage_rollups` by day, node, and pool; any free-pool series is historical retirement evidence, not a current tariff
- `/api/admin/alerts`, `/api/admin/alerts/{id}/ack`, and `/api/admin/alerts/{id}/silence` own durable alert center behavior; alert rows store severity, source, status, first/last seen, resolved state, ack, silence window, and Telegram delivery status
- durable alert sources in v1 include the retired-free-pool invariant, provider cap, node metrics freshness, node capacity, and selected security/admin error counters
- `portal_bot/worker.py` runs `admin_ops_alert_refresh` on a short interval so durable alerts and Telegram admin notifications do not depend on an operator opening `adminapp/`
- the overview reads its active-alert queue from the same durable snapshot and does not issue a second `/api/admin/alerts` request; the dedicated alerts route keeps its own read/ack/silence workflow
- Telegram admin notifications for new and resolved warning/critical alerts must include only short titles and fingerprints; do not include raw config payloads, API tokens, provider secrets, panel passwords, or full metadata JSON

Emergency catalog visibility wave `2026-08-15`:

- `GET /api/admin/emergency-network/status` is the bounded operator read model
  for worker enablement/configuration state, snapshot status counts, active
  revision, aggregate exact-probe levels and retained rollback candidates
- the read model reports `ready`, `disabled` or `invalid` worker configuration
  without returning adapter paths, source URLs, controlled probe URL/digest,
  endpoint material, host hashes, ciphertext, signatures or crypto keys
- staging, promotion, disable and rollback are explicit action-intent operations with
  confirmation and idempotency. Staging remains unavailable unless the worker
  configuration is fully ready; promotion remains unavailable below four
  healthy exact adapter probes
- every promotion preview exposes only a bounded safe delta (retained, added and
  removed counts plus the replacement ratio). Automatic worker promotion stops
  while distribution is disabled; an explicit operator promotion or rollback
  reopens it
- disable is a server-side kill switch for new catalog/profile delivery. It does
  not recall a still-valid signed offline catalog already cached on a device, so
  snapshot expiry and entitlement checks remain part of incident handling
- these local admin aggregates show catalog control-plane state only. They do
  not prove access through a Russian white-list origin, tunnel behavior or the
  exact release candidate; retain those as separate RU-origin and release
  evidence

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
- `/api/admin/nodes/drift`
- `/api/admin/ops/overview`
- `/api/admin/online/users`
- `/api/admin/keys/pressure`
- `/api/admin/payments/summary`
- `/api/admin/free-tier/summary`
- `/api/admin/provider-quotas/status`
- `/api/admin/emergency-network/status`
- `/api/admin/alerts`
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

For Brain-origin delivery evidence, use `remote_brain_network_probe.py
--live-enabled-nodes`; retained-inventory output is not the current delivery
authority. A former-free MTProto `9443/tcp` check remains a separate named
diagnostic and does not change the VPN delivery verdict.

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
- planned topology after the new RU host is live: eligible foreign non-US nodes may have two bridge paths, `mini` and the new RU bridge; each path needs independent listener, downstream, and rollback evidence
- do not treat `rf1` as a general delivery node until repeated RU probes prove stability
- the former dedicated free node (`151.245.217.23`) has no enabled POKROV delivery role in the canonical database; its separate Telegram-only MTProto service, if retained, stays outside subscription traffic and needs its own current runtime attestation

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
- in Hiddify/sing-box profiles `POKROV мост §hide§` is a hidden technical detour for `Белые списки`, not a standalone user country; standalone bridge delay failures should not be counted as delivery-node outages

When handing this off, use:

- [ru-origin-probe-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/ru-origin-probe-handoff.md)

Reserve interpretation:

- `xhttp_alive=true` means the TCP reserve path remains available for operator and VIP access
- `hysteria_alive=true` is still best-effort and should be treated as a UDP viability signal until repeated RU checks confirm it
- if `xhttp_alive=true` while canonical hosts fail, preserve the reserve contour and keep the default consumer path unchanged
- while the RF reserve idea is in backlog, keep collecting probe evidence but do not treat reserve-path improvements as active roadmap work

Telegram MTProto proxy interpretation:

- `portal-mtproto.service active` would prove only that the Telegram proxy daemon is running on the former free node; no current service-state claim is allowed without reachable node-side evidence
- `current-origin check` and `brain-origin check` should verify `151.245.217.23:9443/tcp` separately from HTTPS checks because MTProto is not an HTTP service
- former-free-node reachability to `core.telegram.org` controls whether the separate MTProto config refresh timer may be enabled
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

## Cockpit checks and the final release decision

The operational `gate_matrix` policy is `pokrov.operator-cockpit-gates/v2`:
11 named checks plus separate current/brain/RU origin readiness. `ready` and
`status` describe only this matrix. The API always reports
`gate_f_decision=NOT_EVALUATED`; the cockpit does not load a Gate F report.
The UI shows the policy, actual check count and this limitation even when all
operational checks pass. Each cockpit check aggregates the latest evidence
from every represented origin using the evidence status precedence; current
PASS cannot hide brain/RU FAIL or an attestation/skip. The separate origin
readiness still applies. Guarded rollout registry actions retain their existing
permissions, preview, confirmation and audit requirements. They do not replace
owner release authorization or switch an external artifact pointer.

The separate final policy is `pokrov.release-1.2.0.gate-f-decision/v1`, whose
19 required IDs are owned by `scripts/release_1_2_gate_f.py`. The following is a
review crosswalk of related areas, never an automatic transfer of PASS:

The API includes `gate_f_policy_version` and `gate_f_mapping`, with one entry
per final `check_id` and its `cockpit_inputs` (including `origin:current`,
`origin:brain`, `origin:ru`). The UI renders the complete 19-row table on demand.
An empty input list explicitly means independent evidence is required.
Contract parity with the final policy's version and 19 IDs is tested.

| Cockpit input | Related final Gate F area; requires its own bound receipt |
| --- | --- |
| `app_tests`, `core_tests`, `backend_tests`, `admin_tests` | `gates_a_e_exact_candidate`, `mandatory_stop_ship_and_dod`, `no_open_p0_false_green_or_secret_leak`, `hosted_required_checks` |
| `android_proof` | `android_ldplayer_rehearsal`, `android_physical_device`; these remain distinct |
| `windows_proof` | `windows_live_network` |
| `payment_proof` | `payment_provider_e2e` |
| `update_proof` | `gates_a_e_exact_candidate`, `rollback_and_kill_controls` |
| `signing` | `supply_chain_signature_sbom_provenance`, `target_channel_signing_and_manual_gates` |
| `public_url` | `release_docs_manifest_binding`; a URL alone does not establish byte/signature identity |
| `docs_support_readiness` | `release_docs_manifest_binding`, `mandatory_stop_ship_and_dod` |
| Separate current/brain/RU readiness | `current_origin`, `brain_origin`, `ru_origin`, only with matching candidate and origin |

No cockpit check alone supplies `authenticated_client_egress`,
`operator_auth_rbac_action_intent`, `legal_commercial_approval`, or
`performance_and_release_health`. These four final areas and all other required
Gate F evidence remain independent. An operational green must not be displayed
or consumed as final GO. A rollback request still reports
`external_artifact_switch=NOT_PERFORMED` until the separate switch is executed
and verified; a paused registry is not proof of a completed rollback.
The cockpit read model separately reports
`rollout.external_artifact_switch=NOT_EVALUATED`: it does not query the external
artifact store. The UI distinguishes this observation gap from the stored
`paused` flag and `rollback_requested` state. The action result describes what
that command performed; the cockpit does not invent a subsequent external result.
