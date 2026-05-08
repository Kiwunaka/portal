# Public Beta Unblock Packet

Generated: 2026-05-08 06:20 MSK

## Purpose

This packet lists the exact external inputs still needed before POKROV can move from public-beta preparation to public-beta publication. It is an operator runbook, not a GO handoff.

Current truth files:

- `docs/audit-artifacts/public-beta-handoff-2026-05-07.md`
- `docs/audit-artifacts/public-beta-completion-audit-2026-05-07.md`
- `docs/audit-artifacts/public-beta-launch-decision-2026-05-08.json`
- `docs/audit-artifacts/release-gate-full-local-2026-05-08.md`
- `docs/audit-artifacts/release-gate-local-2026-05-08.md`
- `docs/audit-artifacts/release-gate-brain-2026-05-08.md`

Do not use older generic reports such as `release_gate_report.md` or `public_beta_release_gate_report*.md` as current truth when they conflict with the dated files above.

## Hard Guardrails

- Do not publish GitHub Releases for public distribution while the handoff says `NO-GO`.
- The GitHub prerelease is staged for smoke only while the handoff says `NO-GO`; do not treat it as public distribution.
- Non-mutating GitHub Release plan/dry-run checks remain allowed while `NO-GO`; any additional upload, asset replacement, runtime env sync, or launch announcement still requires the matching staging/GO evidence.
- A separate artifact-staging authorization has allowed the public prerelease asset upload for smoke only. It is not a public launch GO, must not sync runtime download URLs, and must not be announced.
- Do not sync runtime download URLs until the staged GitHub Release APK/EXE URLs pass the live runtime smoke. If live runtime smoke fails, withdraw or replace the staged release assets and keep the handoff `NO-GO`.
- Do not enable paid checkout until the aggregate paid-checkout evidence report has `safe_to_enable_paid_checkout=true`.
- Do not paste raw secrets, Telegram init data, payment identifiers, webhook payloads, mailbox contents, subscription links, or private keys into markdown.
- Redacted evidence is enough when it proves status, timestamp, provider/account, and outcome without exposing private values.

Artifact-staging evidence for `publish_github_release_assets.py --execute --go-evidence-file ...` must include all three exact marker lines in a separate staging authorization:

```text
ARTIFACT STAGING GO FOR RUNTIME SMOKE
NON-URL P0 GATES GREEN FOR ARTIFACT STAGING
ONLY REMAINING P0 GATE: RUNTIME APP-DOWNLOAD URL SMOKE
NO RUNTIME SYNC OR ANNOUNCEMENT
```

The staging authorization must not contain unresolved blocker markers such as `BLOCKED_BY_ACCESS`, `POST_DEPLOY_ONLY_BLOCKED_BY_ACCESS`, `EXTERNAL_DEPENDENCY`, `NOT_DONE_LOCAL_PLAN_READY_NO_GO`, `safe_to_publish_public_beta=false`, or `safe_to_enable_paid_checkout=false`; otherwise the publisher must refuse `--execute`.

## Required External Inputs

| Gate | Current status | Needed input | Owner/action |
| --- | --- | --- | --- |
| Android physical audit | `OPERATOR_ATTESTED` | Optional raw JSON from the already completed physical audit if the operator wants repo-validated `PASS` instead of operator-attested evidence | Current operator attestation is accepted for this beta pass; public/release copy must say operator-attested unless raw validation later proves `PASS` |
| Runtime app-download smoke | `BLOCKED_BY_ACCESS` | Runtime `APP_*` link sync and a passing live/signed `/api/client/apps` URL smoke; staged GitHub APK/EXE URLs already exist | Prefer brain-local signed initData smoke or env-only `TELEGRAM_INIT_DATA`; never paste raw init data; run live URL smoke before announcement |
| Email public auth | `DEPLOYED_PUBLIC_RUNTIME_PASS_EMAIL_ONLY_PROBE_PENDING` | Live verify/reset inbox proof from `EMAIL_PROBE_TO` | Email can be checked independently after deploy; keep public mode enabled only while delivery webhook URL plus relay secret remain configured and debug echo stays off |
| Lava.top checkout evidence | `POST_DEPLOY_ONLY_BLOCKED_BY_ACCESS` + `EXTERNAL_DEPENDENCY` | Provider/category acceptance plus live invoice/webhook/replay/failure/reconciliation/email-key proof | Check only after deploy with safe probe buyer data; attach redacted evidence JSON and run aggregate gate before enabling checkout |
| RU-origin probe | `SKIPPED_BY_OPERATOR` for this beta pass; latest probe `FAIL`, fresh rerun `BLOCKED_BY_ACCESS` | Optional working SSH/auth to `mini` or replacement RU probe host if operator wants to replace the skip with proof | Rerun RU probe from the actual RU-origin host, or keep the skip evidence and avoid RU-readiness claims |
| GitHub Releases | `PUBLISHED_PRERELEASE_STAGING` | Live runtime app-download smoke, runtime link sync authorization, and final GO handoff before distribution copy | Staged prerelease `v0.2.0-beta.1` exists for smoke with canonical APK/EXE assets; do not re-upload, sync runtime env, or announce unless replacing assets under a new staging authorization or publishing after the live smoke is green |
| Windows trusted signing | `UNSIGNED_BETA_RISK_ACCEPTED` | No signing input required for this outside-store beta pass | Keep public copy honest about the unknown-publisher warning |

## Command Sequence After Inputs Arrive

Run commands from `C:\Users\kiwun\Documents\ai\VPN`.

### 0. External Access Preflight

Before running mutating or live probes, classify which access-gated inputs are present in the current shell. This command is non-mutating and redacted: it does not publish, deploy, send email, create invoices, call payment APIs, or print token values.

```powershell
python scripts\public_beta_external_access_preflight.py `
  --handoff docs\audit-artifacts\public-beta-handoff-2026-05-07.md `
  --staged-apps-json docs\audit-artifacts\staged-client-apps-2026-05-07.json
```

Pass condition for starting the full live gate sequence: `ready_to_run_access_gated_smokes=true`. The preflight also exposes separate post-deploy flags: `ready_to_run_email_post_deploy_probe=true` means the email-only proof can run even while Lava.top is still blocked, `ready_to_run_lavatop_post_deploy_probe=true` means the invoice probe has a safe buyer address, and `ready_to_run_runtime_app_download_smoke=true` means the app-download smoke has its own inputs. If RU-origin remains skipped, preflight must expose `accepted_skips=["ru_origin_probe_evidence"]` and public claims must say RU-origin was not verified. Public publication still requires `safe_to_publish_public_beta=true`, which must not happen while the handoff is `NO-GO`.

### 1. Android Physical Audit

The current beta pass has operator-attested physical Android audit evidence in `docs/audit-artifacts/android-physical-audit-operator-note-2026-05-08.md`. Use the commands below only if replacing that attestation with raw repo-validated evidence.

Confirm SDK adb sees the physical device:

```powershell
& "$env:ANDROID_HOME\platform-tools\adb.exe" devices -l
```

Then run the release-build localhost/control-surface audit:

```powershell
python scripts\android_localhost_audit.py `
  --serial $env:ANDROID_AUDIT_SERIAL `
  --package space.pokrov.pokrov_android_shell `
  --release-evidence "app-release.apk sha256=1A369891641964A9A30A296E7D47111A07B6DDAAD5ABC293F7EF938A654DADB0" `
  --require-release-build `
  --connect-wait-sec 30 `
  --disconnect-wait-sec 15 `
  --output docs\audit-artifacts\android-localhost-audit-2026-05-07.json
```

Pass condition: report exists, `failures` is empty, installed package evidence is not debuggable, and the device is physical hardware, not an emulator.

If the physical audit was already completed outside this shell, keep the raw JSON file out of markdown and validate it:

```powershell
$env:ANDROID_AUDIT_EVIDENCE_JSON="<path-to-raw-android-localhost-audit-json>"
python scripts\validate_android_physical_audit_evidence.py `
  $env:ANDROID_AUDIT_EVIDENCE_JSON `
  --output docs\audit-artifacts\android-physical-audit-evidence-validation-2026-05-08.json
```

Pass condition: validation output has `classification=PASS`; emulator rehearsals, wrong package names, missing release package evidence, debuggable builds, missing connect/disconnect metadata, or non-empty `failures` keep Android blocked.

### 2. Runtime App-Download Smoke

Pre-public local policy coverage already rejects Play-only payloads, non-GitHub APK/EXE URLs, wrong extensions, and non-install docs URLs. The brain-local signed smoke below verifies `/api/client/apps` without returning `BOT_TOKEN` or raw init data; it currently blocks until runtime `APP_*` links are synced:

```powershell
python scripts\brain_runtime_app_download_smoke.py `
  --brain-ip 82.21.114.104 `
  --ssh-user root `
  --ssh-port 29374 `
  --source-unit portal-bot `
  --tg-id 900000001 `
  --output docs\audit-artifacts\runtime-app-download-smoke-brain-2026-05-08.json
```

If a real Telegram WebApp `initData` is available in the current shell, the wrapper smoke is also valid:

```powershell
$env:TELEGRAM_INIT_DATA="<redacted live init data>"
python scripts\runtime_app_download_smoke.py `
  --redact `
  --base-url https://api.pokrov.space `
  --require-release-handoff `
  --check-providers
```

The exact staged payload can be revalidated in policy-only mode before runtime env sync. This proves the payload shape and URL policy only; URL reachability is already recorded separately and can be rerun if assets are replaced:

```powershell
python scripts\runtime_app_download_smoke.py `
  --redact `
  --apps-json docs\audit-artifacts\staged-client-apps-2026-05-07.json `
  --require-release-handoff `
  --policy-only
```

The staged JSON must be shaped like `/api/client/apps` and contain the staged GitHub Releases APK/EXE URLs plus `https://pokrov.space/install/`.

The current staged GitHub APK/EXE URLs are reachable. Repeat the same staged payload check without `--policy-only` before syncing runtime env:

```powershell
python scripts\runtime_app_download_smoke.py `
  --redact `
  --apps-json docs\audit-artifacts\staged-client-apps-2026-05-07.json `
  --require-release-handoff
```

Pass condition: `/api/health`, `/api/client/apps`, all referenced Android/Windows/docs URLs, and provider policy checks pass without printing raw init data. A blocked provider catalog is acceptable only with explicit blocked reasons; a green provider catalog must expose exactly one enabled Lava.top row, with no disabled legacy provider rows. If this fails after artifact staging, do not sync `APP_*`, do not post the launch announcement, and withdraw or replace the staged release assets.

Before a real runtime sync, validate the exact staged values without mutating brain:

```powershell
python scripts\remote_brain_apply_release_handoff.py `
  --brain-ip 82.21.114.104 `
  --metadata-file docs\audit-artifacts\staged-client-apps-2026-05-07.json `
  --dry-run
```

The real sync is guarded. It requires a public GO handoff, or a narrow runtime-link authorization file created only after explicit operator approval. That file must contain exactly these markers:

```text
RUNTIME LINK SYNC GO FOR APP-DOWNLOAD SMOKE
STAGED GITHUB ASSET REACHABILITY GREEN
NO PUBLIC ANNOUNCEMENT
PAID CHECKOUT REMAINS CLOSED
```

With that evidence attached:

```powershell
python scripts\remote_brain_apply_release_handoff.py `
  --brain-ip 82.21.114.104 `
  --metadata-file docs\audit-artifacts\staged-client-apps-2026-05-07.json `
  --go-evidence-file docs\audit-artifacts\public-beta-runtime-link-sync-authorization-2026-05-08.md
```

### 2.5. Post-Deploy Payment And Email Probe

After backend/static deploy, run the bundled post-deploy probe first. Without `--live`, it only reads public API runtime status and classifies missing live inputs; it does not send email or create Lava.top invoices:

```powershell
python scripts\public_beta_post_deploy_probe.py `
  --output docs\audit-artifacts\public-beta-post-deploy-probe-2026-05-08.json
```

Expected current shape before probe addresses are supplied: `email_public_runtime_config_passed=true`, `safe_to_keep_email_public=true`, `post_deploy_probe_modes.email_public_runtime=PASS`, and live delivery/invoice modes still `BLOCKED_BY_ACCESS`. That is acceptable for "email is publicly configured after deploy" and for keeping public email mode enabled, but it is still not enough for inbox proof or paid checkout.

Email-only brain-local live probe, after deploy, when a safe recipient address is ready. This keeps relay secrets on `brain`; the local command passes only the probe recipient address and receives a redacted status report. This may produce `classification=BLOCKED_BY_ACCESS` if Lava.top is still missing, but `email_live_delivery_probe_passed=true` plus `safe_to_keep_email_public=true` is enough for the email-delivery proof:

```powershell
python scripts\brain_payment_email_readiness.py `
  --brain-ip 82.21.114.104 `
  --ssh-user root `
  --ssh-port 29374 `
  --passwords <redacted> `
  --plan-code start_99 `
  --post-deploy-live `
  --email-probe-to $env:EMAIL_PROBE_TO `
  --output docs\audit-artifacts\brain-post-deploy-live-probe-2026-05-08.json
```

Full brain-local live probe, after deploy, when both safe probe addresses are ready. This keeps Lava.top and email relay secrets on `brain`; the local command passes only the probe recipient/buyer addresses and receives a redacted status report:

```powershell
python scripts\brain_payment_email_readiness.py `
  --brain-ip 82.21.114.104 `
  --ssh-user root `
  --ssh-port 29374 `
  --passwords <redacted> `
  --plan-code start_99 `
  --post-deploy-live `
  --email-probe-to $env:EMAIL_PROBE_TO `
  --lavatop-probe-email $env:LAVATOP_PROBE_EMAIL `
  --output docs\audit-artifacts\brain-post-deploy-live-probe-2026-05-08.json
```

Pass condition for email live delivery proof: verify and reset probes return `PASS`, the merged post-deploy artifact has `email_live_delivery_probe_passed=true`, and the artifact contains only redacted HTTP status metadata. Pass condition for the full probe: verify/reset/payment-access-key email probes and the Lava.top invoice probe return `PASS` with only HTTP status metadata in the artifact. This proves live delivery/invoice creation only; webhook replay, failed-payment, manual-review mismatch, and reconciliation evidence still belong in the paid evidence JSON.

After either brain-local probe, merge the redacted brain artifact into the local post-deploy aggregator and refresh the launch decision:

```powershell
python scripts\public_beta_post_deploy_probe.py `
  --brain-live-probe-json docs\audit-artifacts\brain-post-deploy-live-probe-2026-05-08.json `
  --output docs\audit-artifacts\public-beta-post-deploy-probe-2026-05-08.json

python scripts\public_beta_launch_decision.py `
  --output docs\audit-artifacts\public-beta-launch-decision-2026-05-08.json
```

Pass condition for the email-only proof path: the refreshed post-deploy artifact has `safe_to_keep_email_public=true` and `email_live_delivery_probe_passed=true` while paid checkout may still be blocked. Pass condition for paid checkout remains stricter: the launch decision must stay `NO_GO` until Lava.top invoice, authenticated webhook, replay/idempotency, failed-payment, manual-review mismatch, reconciliation, and paid access-key email evidence are all green.

Fallback local live bundle, only when `EMAIL_PROBE_TO`, `LAVATOP_PROBE_EMAIL`, Lava.top credentials, relay URL/secret, and the redacted paid evidence JSON are intentionally present in the operator shell:

```powershell
python scripts\public_beta_post_deploy_probe.py `
  --live `
  --evidence-json docs\audit-artifacts\paid-checkout-live-evidence-2026-05-07.json `
  --output docs\audit-artifacts\public-beta-post-deploy-probe-2026-05-08.json
```

Local live mode sends verify/reset/payment-access-key email probes and creates one Lava.top probe invoice from local env. It still does not replace the authenticated webhook replay, failed-payment, manual-review mismatch, or reconciliation evidence; those must remain in the redacted paid evidence JSON before checkout can be enabled.

### 3. Email Auth And Delivery

First confirm live brain readiness still sees public mode, delivery webhook URL, relay secret, and debug echo off:

Replace `<redacted>` with the local password-file path only in the operator shell; do not paste that path or file contents into committed evidence.

```powershell
python scripts\brain_payment_email_readiness.py `
  --brain-ip 82.21.114.104 `
  --ssh-user root `
  --ssh-port 29374 `
  --passwords <redacted> `
  --plan-code start_99 `
  --output docs\audit-artifacts\payment-email-readiness-brain-2026-05-08.json
```

Public email mode is enabled on brain. The 2026-05-08 status reports `delivery_secret_configured=true`. Prefer the brain-local post-deploy probe above for live delivery evidence. If intentionally probing from a local shell that already has the relay env configured, prove live delivery from the same delivery path:

```powershell
python scripts\email_delivery_probe.py --kind verify --email $env:EMAIL_PROBE_TO --live
python scripts\email_delivery_probe.py --kind reset --email $env:EMAIL_PROBE_TO --live
python scripts\email_delivery_probe.py --kind payment_access_key --email $env:EMAIL_PROBE_TO --live
```

Pass condition: verify, reset, and payment-access-key delivery all return sent through the real delivery path, and the inbox/provider evidence is attached with message bodies and tokens redacted.

### 4. Lava.top Evidence Pack

Run the live invoice probe only from a shell with Lava.top env configured:

```powershell
python scripts\lavatop_invoice_probe.py --plan-code start_99 --email $env:LAVATOP_PROBE_EMAIL --live
```

After a real or approved sandbox order exists, replay only redacted callback evidence against the intended API URL:

```powershell
python scripts\lavatop_webhook_replay_smoke.py `
  --url https://api.pokrov.space/api/payments/result/lavatop `
  --order-id $env:LAVATOP_REPLAY_ORDER_ID `
  --contract-id $env:LAVATOP_REPLAY_CONTRACT_ID `
  --plan-code start_99 `
  --live
```

Create a redacted evidence JSON with this shape:

```json
{
  "checks": [
    {"name": "lavatop_live_invoice_creation", "status": "PASS", "source": "redacted invoice probe/provider evidence"},
    {"name": "lavatop_authenticated_success_webhook", "status": "PASS", "source": "redacted webhook evidence"},
    {"name": "lavatop_webhook_replay_idempotency", "status": "PASS", "source": "redacted duplicate webhook evidence"},
    {"name": "lavatop_failed_payment_no_fulfillment", "status": "PASS", "source": "redacted failed-payment evidence"},
    {"name": "lavatop_manual_review_mismatch", "status": "PASS", "source": "redacted amount/currency/plan mismatch evidence"},
    {"name": "lavatop_reconciliation_procedure", "status": "PASS", "source": "redacted reconciliation procedure evidence"},
    {"name": "paid_access_key_email_delivery", "status": "PASS", "source": "redacted paid access-key delivery evidence"}
  ]
}
```

Then aggregate it:

```powershell
python scripts\paid_checkout_launch_evidence_check.py `
  --readiness-json docs\audit-artifacts\payment-email-readiness-brain-2026-05-08.json `
  --evidence-json docs\audit-artifacts\paid-checkout-live-evidence-2026-05-07.json `
  --output docs\audit-artifacts\paid-checkout-launch-evidence-brain-2026-05-08.json
```

Pass condition: output has `classification=PASS` and `safe_to_enable_paid_checkout=true`.

### 5. RU-Origin Probe

After SSH/auth to `mini` or replacement RU probe host is restored:

```powershell
python scripts\ru_probe_runner.py --reserve-host rf1.pokrov.space --probe-host mini --out ops-local\ru-probe.json
python scripts\render_ru_probe_report.py --input ops-local\ru-probe.json
```

Promote only the redacted summary to `docs/audit-artifacts/`. Keep raw operator output and any sensitive host material out of git.

Pass condition: POKROV web/API hosts, Telegram hosts, and relevant node TCP checks are reachable from the actual RU-origin host. Operator-approved skip condition: `docs/audit-artifacts/ru-origin-skip-accepted-2026-05-08.md` is present, `public_beta_external_access_preflight.py` reports `ru_origin_probe_evidence=SKIPPED_BY_OPERATOR`, and public claims do not describe RU-origin readiness as verified.

### 6. Final Gate And Publication

After every P0 gate above is green, rerun the integrated gates:

```powershell
python scripts\release_gate_check.py --quick --brain-ip 82.21.114.104 --output docs\audit-artifacts\release-gate-brain-2026-05-08.md
python scripts\release_gate_check.py --client-platform-gates windows,android-apk --output docs\audit-artifacts\release-gate-full-local-2026-05-08.md
```

Confirm the staged GitHub Release plan and current published prerelease state:

```powershell
python scripts\prepare_github_release_plan.py --tag v0.2.0-beta.1 --title "POKROV 0.2.0-beta.1"
python scripts\publish_github_release_assets.py --tag v0.2.0-beta.1 --title "POKROV 0.2.0-beta.1"
```

Only after the handoff says `GO for public beta publication`, or after a new separate artifact-staging authorization says the current assets must be replaced for smoke, upload or replace assets with the guarded REST fallback or `gh` workflow:

```powershell
python scripts\publish_github_release_assets.py `
  --tag v0.2.0-beta.1 `
  --title "POKROV 0.2.0-beta.1" `
  --execute `
  --go-evidence-file docs\audit-artifacts\public-beta-artifact-staging-authorization-2026-05-08.md
```

Pass condition for artifact staging: public prerelease exists only for smoke, canonical APK/EXE assets are uploaded, expected GitHub Release URLs resolve, and no runtime env or launch copy is published yet.

Pass condition for public publication: runtime app-download smoke passes against those URLs, runtime link sync succeeds, static download surfaces are redeployed when needed, and the final handoff flips to GO without unsafe claims.

## Stop Conditions

Stop and keep the release `NO-GO` if any of these happens:

- physical Android audit cannot run on real hardware;
- runtime smoke lacks live runtime Android/Windows/docs URLs;
- email public mode turns off, the delivery relay secret disappears, debug echo turns on, or live verify/reset delivery cannot be proven;
- Lava.top provider acceptance or live payment evidence is incomplete;
- RU-origin Telegram reachability is failed or unavailable without an explicit `SKIPPED_BY_OPERATOR` artifact and public-claim guardrail;
- runtime links are synced, assets are replaced without fresh staging evidence, or announcement copy is posted while the handoff still says `NO-GO`;
- any command output includes unredacted secrets or user identifiers.
