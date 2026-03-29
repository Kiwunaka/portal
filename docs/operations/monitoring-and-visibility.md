# Monitoring And Visibility

Last updated: 2026-03-29

## Document Status

This file is living source of truth for hostname migration policy, external RU probe operations, and operator visibility into app, bot, device, and IP context.

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
- `kiwunaka.space` is compatibility-only for migration and legacy subscription continuity

Compatibility rule for `kiwunaka.space`:

- keep it alive only while older subscriptions and imported profiles still depend on it
- do not use it in new QR codes, fresh config links, bot onboarding, app onboarding, public CTA copy, or support macros for new users
- when support sees an old `kiwunaka.space` profile, the preferred answer is migration to the canonical `pokrov.space` line rather than re-issuing another legacy entrypoint

## Monitoring Layers

Monitoring should cover four layers together:

1. public entrypoints and hostname correctness
2. app, webapp, and bot session health
3. node reachability and public egress
4. support visibility for linked Telegram, device, and IP context
5. per-node freshness, sustained resource alerts, and probe failure reasons

The platform should be operated as one system. A broken Telegram handoff, dead node, or wrong hostname can all appear to the user as "VPN does not work".

## External RU Probe Policy

Required cadence:

- every `6 hours`

Required probe origin:

- an external RU node or other external RU vantage point that is outside the control-plane host

Required checks on each run:

1. confirm the probe host can reach `google.com`
2. confirm the probe host can reach Telegram surfaces such as `api.telegram.org` and `t.me`
3. confirm the probe host can resolve and reach the current public `POKROV` surfaces when needed
4. confirm the probe host can reach the intended node endpoints used by current subscriptions
5. confirm the current reserve ingress state from RU:
   - `xhttp_alive`
   - `hysteria_alive`
4. record failures in a compact operator-readable report

Minimum report fields:

- UTC timestamp
- probe host label and public IP if known
- whether `google.com` was reachable
- whether the Telegram surfaces were reachable
- node-by-node status
- per-target split health for `DNS`, `TCP`, `TLS`, `HTTP`, and `UDP` when applicable
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

## Node Metrics Freshness And Alerts

The admin and operator view must treat node freshness per node, not only as one global timestamp.

Required node-level visibility:

- freshness state for each node
- sustained CPU / RAM / disk pressure alerts
- sustained latency / error-rate alerts
- high client-density alerts
- `last_probe_stage`
- `last_probe_error_kind`
- `last_probe_error_message`

Operational rule:

- `portal-node-metrics.timer` must stay healthy on every relevant host
- hoster CPU warnings should trigger a review of per-node metrics plus control-plane load on the canonical host

Primary repository touchpoints:

- `scripts/collect_node_metrics.py`
- `infra/portal-node-metrics.service`
- `infra/portal-node-metrics.timer`
- `/api/admin/metrics/status`
- `/api/admin/nodes/health`

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

- `mini` is the canonical RU probe origin
- `rf1` is the reserve ingress for operator and VIP/manual access
- do not use `mini` for general user traffic
- do not treat `rf1` as a general delivery node until repeated RU probes prove stability

Current backlog note:

- RU ingress / RF reserve experiments are paused
- keep using `mini` only as the RU probe origin
- do not resume `mini` canary work or `rf1` promotion until the product owner explicitly requests it

Reserve interpretation:

- `xhttp_alive=true` means the TCP reserve path remains available for operator and VIP access
- `hysteria_alive=true` is still best-effort and should be treated as a UDP viability signal until repeated RU checks confirm it
- if `xhttp_alive=true` while canonical hosts fail, preserve the reserve contour and keep the default consumer path unchanged
- while the RF reserve idea is in backlog, keep collecting probe evidence but do not treat reserve-path improvements as active roadmap work

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
- effective admin status: `active`, `expired`, `blocked`, `manual_test`

Visibility rule:

- this data exists for support diagnosis, abuse control, and account recovery
- it must not be echoed back to public marketing copy as surveillance language
- user-facing support copy should describe this as technical context used to help diagnose connection issues

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
