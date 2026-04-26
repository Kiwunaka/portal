# R06 - Telegram, Downloads, RU-Origin, Support Channels

Status: research complete  
Date: 2026-04-26  
Agent: R06  
Scope: Telegram auth/download smoke, app-download endpoints, support/feedback bots, RU-origin probes, current reports

## Executive Summary

The current platform has the right primitives for beta download validation, but the evidence gates are still blocked by missing live access. `/api/client/apps` is authenticated by Telegram WebApp `initData`, and `scripts/smoke_client_apps.py` can verify the API payload plus referenced Android/Windows/docs URLs when `TELEGRAM_INIT_DATA` is supplied through the environment. The release gate already auto-adds that smoke when the env var exists.

The release documentation currently names a non-existent `runtime_app_download_smoke.py`; the repo-local script is `scripts/smoke_client_apps.py`. This mismatch can cause an operator to skip or fail the Telegram download gate unless fixed in the work-order plan.

RU-origin evidence remains blocked until a healthy external RU host, usually `mini` or a replacement, can run `scripts/ru_probe_runner.py`. Current docs correctly say current-origin and brain-origin checks do not prove RU reachability. The RU probe script checks Google, Telegram web/API surfaces, canonical POKROV hosts, foreign delivery nodes, and reserve paths, but it does not yet perform the documented large-body HTTPS stage.

Support and feedback data are durable in database tables, but Telegram notifications are best-effort. API ticket notifications, helpbot admin notifications, feedbackbot moderation notifications, and user reply notifications can be lost after a Telegram API/network failure because failures are only returned or logged; there is no durable notification outbox or retry worker.

## Evidence Table

| Label | Evidence | Source | Finding |
| --- | --- | --- | --- |
| confirmed | Telegram WebApp `initData` is verified server-side before auth. | `portal_bot/api.py:1422`, `portal_bot/api.py:2136` | `X-Telegram-Init-Data` is parsed, HMAC-checked against the bot token, and invalid signatures return `401`. |
| confirmed | `/api/client/apps` requires Telegram/web auth and returns runtime app URLs. | `portal_bot/api.py:6681`, `scripts/smoke_client_apps.py:123` | Download payload is not anonymous; live smoke needs a valid `TELEGRAM_INIT_DATA` value. |
| confirmed | Existing runtime download smoke script is `scripts/smoke_client_apps.py`. | `scripts/smoke_client_apps.py:2`, `scripts/release_gate_check.py:293` | The release gate auto-runs this script when `TELEGRAM_INIT_DATA` exists. |
| confirmed | Work-order release plan references `runtime_app_download_smoke.py`, which is absent. | `docs/developer/work-orders/2026-04-open-beta-v4/05-release-gate-plan.md:41`; repo script listing | Operator-facing command drift exists. |
| confirmed | Release report redacts generic secret/token/password patterns and bearer headers. | `scripts/release_gate_check.py:65`, `scripts/release_gate_check.py:282` | Useful baseline redaction exists, but `--init-data` is not explicitly covered. |
| confirmed | `smoke_client_apps.py` does not print `TELEGRAM_INIT_DATA` in normal output. | `scripts/smoke_client_apps.py:147-197` | It prints endpoint/artifact statuses and final URLs, not auth headers. |
| probable | Passing `--init-data` on the command line is unsafe for logged gate evidence. | `scripts/smoke_client_apps.py:125`, `scripts/release_gate_check.py:65` | The script accepts the flag, while release redaction does not explicitly redact `--init-data`. Use env-only. |
| confirmed | RU probe covers Google, Telegram API/web, POKROV canonical hosts, nodes, and reserve paths. | `scripts/ru_probe_runner.py:52-115`, `tests/test_ru_probe_runner.py` | The target set matches most release evidence needs. |
| confirmed | Current docs require current/brain/RU origin labels to remain separate. | `docs/operations/monitoring-and-visibility.md`, `scripts/release_gate_check.py:214-237` | A local green gate cannot be reported as RU evidence. |
| needs local run | Live current-origin, brain-origin, and RU-origin reachability were not executed by R06. | task access constraints | No live SSH, Telegram token, or RU host access was provided in this research task. |
| confirmed | API ticket notifications use single-attempt Telegram sends after DB commit. | `portal_bot/api.py:3402`, `portal_bot/api.py:7270`, `portal_bot/api.py:7319` | Ticket rows persist, but failed notification sends are not queued. |
| confirmed | Helpbot and feedbackbot admin notifications are best-effort only. | `portal_bot/helpbot.py:165`, `portal_bot/feedbackbot.py:222` | Failures are logged or ignored; no retry backlog exists. |

## P0 Issues

| ID | Label | Issue | Impact | Required action |
| --- | --- | --- | --- | --- |
| R06-P0-001 | blocked by missing access | Runtime app-download smoke lacks live `TELEGRAM_INIT_DATA` evidence. | Public beta/`1.0.0` cannot claim authenticated download readiness. | Operator must acquire a live token via SOP below and run `scripts/smoke_client_apps.py` with env-only token handling. |
| R06-P0-002 | blocked by missing access | RU-origin evidence is missing. | Geography-specific release confidence is unproven; Telegram limitations cannot be classified. | Run `ru_probe_runner.py` from `mini` or replacement RU host and render the report. |
| R06-P0-003 | confirmed | Release plan points to missing `runtime_app_download_smoke.py`. | Gate operator may run the wrong command or silently skip the actual download smoke. | Update gate docs/work-order plan to use `scripts/smoke_client_apps.py`, or add a compatibility wrapper with the documented name. |

## P1 Issues

| ID | Label | Issue | Impact | Required action |
| --- | --- | --- | --- | --- |
| R06-P1-001 | probable | `--init-data` command-line input is accepted but not explicitly redacted by `release_gate_check.py`. | If an operator uses the CLI flag and the command is copied into evidence, Telegram auth data may leak. | Prefer env-only SOP; add redaction for `--init-data`, `TELEGRAM_INIT_DATA=...`, `query_id=`, `auth_date=`, `user=`, and `hash=` patterns. |
| R06-P1-002 | confirmed | Support/feedback Telegram notifications have no durable retry queue. | Operators may miss support tickets, feedback submissions, or user/admin replies during Telegram/API outages. | Add notification outbox table, retry worker, admin backlog view, and tests. |
| R06-P1-003 | confirmed | RU probe does not implement the documented large-body HTTPS `>=64KB` stage. | Probe can miss path/body-size failures that affect real downloads or web payloads. | Extend `ru_probe_runner.py` to perform bounded GET/body-size checks for canonical web/API targets. |

## P2 Issues

| ID | Label | Issue | Impact | Required action |
| --- | --- | --- | --- | --- |
| R06-P2-001 | confirmed | `scripts/smoke_client_apps.py` has no `--redact` flag although work-order copy expects redacted smoke tooling. | The script is currently safe for init data, but the interface does not make evidence mode obvious. | Add `--redact` as a no-op/default evidence mode that suppresses any future sensitive fields and prints a redaction banner. |
| R06-P2-002 | unknown | Public fallback wording for RU Telegram blocking is not centralized as a reusable support macro. | Operators may improvise and accidentally imply Telegram is required. | Add a short canonical macro to launch/support docs after implementation owner approval. |

## Proposed Implementation Work

1. Align the app-download smoke name.
   - Replace `runtime_app_download_smoke.py --redact` references with `python scripts/smoke_client_apps.py --check-providers --require-release-handoff`.
   - Optional compatibility path: add `scripts/runtime_app_download_smoke.py` as a thin wrapper around `smoke_client_apps.py` with `--redact` support.

2. Harden runtime smoke redaction.
   - Remove operator use of `--init-data` from docs.
   - Extend `release_gate_check._redact_text()` to cover `--init-data`, `TELEGRAM_INIT_DATA=...`, and Telegram WebApp query fields.
   - Add a unit test that fails if a fake init-data string appears in the rendered report.

3. Extend RU probe parity.
   - Add large-body HTTPS checks to `ru_probe_runner.py` for `pokrov.space`, `app.pokrov.space`, `api.pokrov.space/api/health` or a safe API endpoint, and `t.me`.
   - Preserve stage-specific fields: `dns_ok`, `tcp_ok`, `tls_ok`, `http_ok`, `body_64kb_ok`.
   - Keep `telegram_reachability_problem` separate from `canonical_host_problem`.

4. Add support notification durability.
   - Add `NotificationOutbox` with `id`, `kind`, `target_channel`, `target_id`, `dedupe_key`, `payload_json`, `status`, `attempt_count`, `next_attempt_at`, `last_error`, `created_at`, `sent_at`.
   - Queue notifications after ticket/feedback DB commits instead of only sending inline.
   - Add worker retry with exponential backoff and dead-letter status.
   - Show unsent/retrying notification count in admin diagnostics.

## Exact Verification Commands

Run these from `C:/Users/kiwun/.config/superpowers/worktrees/VPN/open-beta-v4` unless a command says otherwise.

### Current-Origin Checks

```powershell
$env:PORTAL_API_BASE_URL = "https://api.pokrov.space"
# Set TELEGRAM_INIT_DATA with the SOP below. Do not paste the value into docs or command history.
python scripts/smoke_client_apps.py --base-url $env:PORTAL_API_BASE_URL --check-providers --require-release-handoff
```

```powershell
python scripts/ru_probe_runner.py --reserve-host rf1.pokrov.space --probe-host current --out ops-local/ru-probe-current-origin.json
python scripts/render_ru_probe_report.py --input ops-local/ru-probe-current-origin.json
```

### Brain-Origin Checks

```powershell
python scripts/verify_brain_ready.py --brain-ip 82.21.114.104 --repeat 5
```

```powershell
python scripts/remote_brain_network_probe.py --brain-ip 82.21.114.104 --ports 443,8443,9443
```

### RU-Origin Checks

Run on the external RU host, not on the local workstation and not on `brain`:

```powershell
python scripts/ru_probe_runner.py --reserve-host rf1.pokrov.space --probe-host mini --out ops-local/ru-probe.json
python scripts/render_ru_probe_report.py --input ops-local/ru-probe.json
```

If `mini` is unavailable:

```powershell
python scripts/ru_probe_runner.py --reserve-host rf1.pokrov.space --probe-host <replacement-ru-host-label> --probe-public-ip <replacement-public-ip-if-known> --out ops-local/ru-probe.json
python scripts/render_ru_probe_report.py --input ops-local/ru-probe.json
```

### Redaction Proof

```powershell
New-Item -ItemType Directory -Force .tmp | Out-Null
python scripts/smoke_client_apps.py --base-url https://api.pokrov.space --check-providers --require-release-handoff *> .tmp\client-apps-smoke.out
Select-String -Path .tmp\client-apps-smoke.out -Pattern "query_id=","auth_date=","hash=","user=","TELEGRAM_INIT_DATA"
```

Expected result: no matches. If matches appear, the output is not safe to attach.

After redaction hardening is implemented:

```powershell
python -m pytest tests/test_release_gate_check.py tests/test_api_auth_and_tickets.py -q
```

### Support Notification Durability After Implementation

```powershell
python -m pytest tests/test_api_auth_and_tickets.py tests/test_tickets_repo.py -q
python -m pytest tests/test_feedbackbot.py tests/test_helpbot.py -q
```

If new worker/outbox tests are added:

```powershell
python -m pytest tests/test_notification_outbox.py tests/test_worker_retention.py -q
```

## Token Acquisition SOP

Purpose: acquire live `TELEGRAM_INIT_DATA` without writing the value into markdown, chat, shell history, screenshots, or test logs.

1. Use only a designated tester/admin Telegram account.
2. Open the official POKROV Telegram WebApp or cabinet handoff from `@pokrov_vpnbot` inside Telegram, not a normal browser tab.
3. In the Telegram WebView console, read only:

```javascript
window.Telegram?.WebApp?.initData
```

4. Copy the value directly into the operator shell environment. Do not paste it into the prompt, docs, issue comments, screenshots, or a command-line argument.
5. Prefer PowerShell secret prompt:

```powershell
$secure = Read-Host "Paste TELEGRAM_INIT_DATA" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
  $env:TELEGRAM_INIT_DATA = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
} finally {
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
}
```

6. Run the smoke in the same shell:

```powershell
python scripts/smoke_client_apps.py --base-url https://api.pokrov.space --check-providers --require-release-handoff
```

7. Clear the variable immediately after the run:

```powershell
Remove-Item Env:\TELEGRAM_INIT_DATA
```

8. Evidence may include command name, exit status, endpoint statuses, artifact URL status summaries, and redaction proof. Evidence must not include the init data string, Telegram user JSON, `hash`, `query_id`, subscription URLs, or raw auth headers.

## RU-Origin Evidence Matrix

| Origin | Required command | Required pass criteria | If blocked |
| --- | --- | --- | --- |
| current-origin | `python scripts/ru_probe_runner.py --probe-host current ...` plus app-download smoke | Local operator can reach canonical POKROV hosts, `/api/health`, app download artifacts, and relevant public fallback URLs. | Mark `current-origin check: BLOCKED_BY_ACCESS` only if local network/tooling prevents the run. |
| brain-origin | `python scripts/verify_brain_ready.py --brain-ip 82.21.114.104 --repeat 5` | Required units active, listeners present, local resolved HTTPS checks pass, subscription/connect stability passes without printing tokens. | Mark `brain-origin check: BLOCKED_BY_ACCESS` if SSH/API access is missing. |
| RU-origin | `python scripts/ru_probe_runner.py --probe-host mini ...` from RU host | `google.com` reachable; `pokrov.space`, `app.pokrov.space`, `api.pokrov.space`, delivery nodes, and reserve status classified; Telegram surfaces classified separately. | Mark `RU-origin check: unavailable` or `BLOCKED_BY_ACCESS`; do not infer RU status from current/brain results. |
| Telegram from RU | Included in RU probe as `api.telegram.org` and `t.me` | If Telegram passes, bot/web continuation may be considered reachable from that RU vantage point. | If Telegram fails while POKROV hosts pass, classify `telegram_reachability_problem`, not a POKROV canonical-host failure. |
| Reserve from RU | Included with `--reserve-host rf1.pokrov.space` | `xhttp_alive` and `hysteria_alive` recorded, with Hysteria treated as best-effort UDP viability. | Reserve pass does not promote reserve paths to public default. |

## App-Download Smoke Plan

1. Confirm runtime host health:

```powershell
python scripts/smoke_client_apps.py --base-url https://api.pokrov.space --check-providers --require-release-handoff
```

2. Required checks inside the smoke:
   - `GET /api/health` returns 2xx/3xx.
   - `GET /api/client/apps` returns JSON under live Telegram auth.
   - Android has `play_url` or `apk_url` when release handoff is required.
   - Windows has `exe_url` when release handoff is required.
   - `docs_url` is present when release handoff is required.
   - Each non-empty URL passes `HEAD`, or fallback `GET` range for providers that reject `HEAD`.
   - `/api/payments/providers` has at least one enabled, valid RUB provider when `--check-providers` is used.

3. Required evidence:
   - Command without token value.
   - Exit code.
   - `[OK]` / `[FAIL]` lines.
   - Redaction proof showing no Telegram query fields in output.

4. Failure classification:
   - `401`: bad/expired `TELEGRAM_INIT_DATA`; reacquire via SOP.
   - Missing Android/Windows/docs URL: release handoff not synced or runtime env missing.
   - URL probe failure: artifact host or URL is stale/unreachable.
   - Provider failure: payment provider readiness issue, not a download issue.

## Telegram Limitation Language

Use this when RU-origin probe shows POKROV hosts are reachable but Telegram targets are blocked or degraded:

> Telegram may be unavailable from some networks. POKROV does not require Telegram for first launch or normal app use. Install or open the app from `https://pokrov.space/install/`, continue in the cabinet at `https://app.pokrov.space/`, and contact `support@pokrov.space` if Telegram bots do not open. Telegram bonus, bot support, and channel actions can be retried later when Telegram is reachable.

Operator rules:

- Do not say POKROV is down when only `api.telegram.org` or `t.me` failed and canonical POKROV hosts passed.
- Do not publish MTProto proxy secrets or links in docs/reports.
- Do not make Telegram the first recovery path; keep order as app, web cabinet, Telegram fallback.
- If Telegram is blocked from RU, support bot and feedback bot should be described as unavailable from that network, with `support@pokrov.space` and cabinet support as the public fallback.

## Support Notification Retry Backlog

Current durable state:

- `support_tickets` and `support_ticket_messages` persist ticket state.
- `feedback_entries` persists feedback moderation backlog.
- `reviews` persists approved public reviews.

Current non-durable notification paths:

- API ticket create sends admin Telegram notification once after DB commit.
- API ticket reply sends user/admin Telegram notification once.
- Helpbot `_notify_admin()` logs warning on failure and drops the notification.
- Feedbackbot `_notify_admin()` logs warning on failure and drops the notification.
- Feedbackbot publish acknowledgement to user swallows send failure.

Backlog proposal:

| Item | Priority | Work |
| --- | --- | --- |
| Notification outbox model | P1 | Add durable table with dedupe key, target, payload, attempts, status, and timestamps. |
| Queue API ticket notifications | P1 | Replace inline-only sends with queue plus best-effort immediate send. |
| Queue helpbot notifications | P1 | Store admin notification request when a helpbot ticket/message is created. |
| Queue feedback moderation notifications | P1 | Store moderation notification when feedback is captured. |
| Retry worker | P1 | Retry pending rows with exponential backoff and dead-letter after max attempts. |
| Admin visibility | P2 | Show pending/failed notification counts and last error in admin diagnostics. |
| Tests | P1 | Cover Telegram failure, retry success, dedupe, and no duplicate admin spam. |

## Final Status

R06 did not run live Telegram, brain SSH, or RU-origin commands because the required access values were not provided and must not be invented. The repo research supports these labels:

- Telegram runtime download smoke: `blocked by missing access`.
- RU-origin check: `blocked by missing access`.
- Brain-origin check: `blocked by missing access` until SSH/API access is provided.
- Support notification durability: `confirmed` gap.
- App-download smoke command drift: `confirmed` gap.
