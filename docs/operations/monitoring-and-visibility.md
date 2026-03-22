# Monitoring And Visibility

Last updated: 2026-03-22

## Document Status

This file is living source of truth for hostname migration policy, external RU probe operations, and operator visibility into app, bot, device, and IP context.

## Canonical Hostname Policy

Current official public surfaces are:

- marketing and public site: `https://pokrov.space/`
- user cabinet and web login: `https://app.pokrov.space/`
- public API host: `https://api.pokrov.space/`

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

The platform should be operated as one system. A broken Telegram handoff, dead node, or wrong hostname can all appear to the user as "VPN does not work".

## External RU Probe Policy

Required cadence:

- every `6 hours`

Required probe origin:

- an external RU node or other external RU vantage point that is outside the control-plane host

Required checks on each run:

1. confirm the probe host can reach `google.com`
2. confirm the probe host can resolve and reach the current public `POKROV` surfaces when needed
3. confirm the probe host can reach the intended node endpoints used by current subscriptions
4. record failures in a compact operator-readable report

Minimum report fields:

- UTC timestamp
- probe host label and public IP if known
- whether `google.com` was reachable
- node-by-node status
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

## Suggested RU Probe Workflow

Existing repository helpers:

- [scripts/remote_brain_network_probe.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_brain_network_probe.py)
- [scripts/release_gate_check.py](C:/Users/kiwun/Documents/ai/VPN/scripts/release_gate_check.py)

Repository helper added for reporting:

- [scripts/render_ru_probe_report.py](C:/Users/kiwun/Documents/ai/VPN/scripts/render_ru_probe_report.py)
- [scripts/ru_probe_sample.json](C:/Users/kiwun/Documents/ai/VPN/scripts/ru_probe_sample.json)

Recommended external RU probe flow:

1. run the actual reachability checks from the external RU host
2. save the raw JSON result locally or copy it back into the repo workspace
3. render a compact operator summary with `render_ru_probe_report.py`
4. attach the rendered summary to the operator handoff or incident thread

Example:

```powershell
python scripts/render_ru_probe_report.py --input scripts/ru_probe_sample.json
```

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

Only collect and expose the minimum operational context needed to diagnose service problems and keep the app-first account model working reliably.
