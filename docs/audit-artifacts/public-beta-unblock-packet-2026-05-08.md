# Public Beta Unblock Packet 2026-05-08

Generated: 2026-05-08 after the post-handoff runtime smoke refresh.

## Purpose

This packet lists the exact external inputs still needed before POKROV can move from public-beta preparation to public-beta publication. It is an operator runbook, not a GO handoff.

Current truth files:

- `docs/audit-artifacts/public-beta-handoff-2026-05-08.md`
- `docs/audit-artifacts/public-beta-completion-audit-2026-05-08.md`
- `docs/audit-artifacts/public-beta-launch-decision-2026-05-08.json`
- `docs/audit-artifacts/public-beta-external-access-preflight-2026-05-08.json`
- `docs/audit-artifacts/ru-origin-skip-accepted-2026-05-08.md`
- `docs/audit-artifacts/release-gate-full-local-2026-05-08.md`
- `docs/audit-artifacts/release-gate-local-2026-05-08.md`
- `docs/audit-artifacts/release-gate-brain-2026-05-08.md`

Do not use older generic reports such as `release_gate_report.md` or `public_beta_release_gate_report*.md` as current truth when they conflict with the dated files above.

## Current Status

| Gate | Status | Exact missing input |
| --- | --- | --- |
| Runtime app-download smoke | `BLOCKED_BY_ACCESS` | Runtime-link sync GO plus live `/api/client/apps` smoke |
| Email public delivery | `BLOCKED_BY_ACCESS` | `EMAIL_PROBE_TO` |
| Lava.top checkout evidence | `BLOCKED_BY_ACCESS` / `EXTERNAL_DEPENDENCY` | `LAVATOP_PROBE_EMAIL`, provider acceptance, invoice/webhook/replay/failure/manual-review/reconciliation/paid-key email evidence |
| RU-origin probe | `SKIPPED_BY_OPERATOR` | Optional working RU probe access if the operator wants to replace the skip |
| Android physical audit | `OPERATOR_ATTESTED` | Optional raw audit JSON only if replacing the accepted attestation |
| Windows signing | `UNSIGNED_BETA_RISK_ACCEPTED` | No signing input required for this outside-store beta pass |

Public email mode is enabled on brain. Keep it public only while delivery webhook URL plus relay secret remain configured and debug echo stays off.

## Hard Guardrails

- Do not publish GitHub Releases for public distribution while the handoff says `NO-GO`.
- The existing GitHub prerelease is staged for smoke only; do not treat it as live runtime distribution until runtime links are synced and smoked.
- Do not sync runtime download URLs until the staged GitHub APK/EXE URLs and install docs remain reachable.
- Do not enable paid checkout until aggregate paid-checkout evidence has `safe_to_enable_paid_checkout=true`.
- Do not paste raw secrets, Telegram init data, payment identifiers, webhook payloads, mailbox contents, subscription links, or private keys into markdown.

Artifact-staging authorization markers:

```text
ARTIFACT STAGING GO FOR RUNTIME SMOKE
NON-URL P0 GATES GREEN FOR ARTIFACT STAGING
ONLY REMAINING P0 GATE: RUNTIME APP-DOWNLOAD URL SMOKE
NO RUNTIME SYNC OR ANNOUNCEMENT
```

## 0. External Access Preflight

This command is non-mutating and redacted:

```powershell
python scripts\public_beta_external_access_preflight.py
```

Pass condition for the full live sequence: `ready_to_run_access_gated_smokes=true`.

Separate useful flags:

- `ready_to_run_email_post_deploy_probe=true` means email-only proof can run.
- `ready_to_run_lavatop_post_deploy_probe=true` means Lava.top invoice probe has a safe buyer address.
- `ready_to_run_runtime_app_download_smoke=true` means the app-download smoke has its own inputs.
- `accepted_skips=["ru_origin_probe_evidence"]` means public claims must say RU-origin was not verified.

## 1. Runtime App-Download Smoke

The current post-handoff brain-local signed smoke artifact is:

- `docs/audit-artifacts/runtime-app-download-smoke-brain-2026-05-08-post-handoff.json`

It proves brain-local signed auth reaches `/api/client/apps`, but it remains blocked because live Android/Windows/docs URLs are empty.

Before runtime sync, revalidate the client-owned handoff:

```powershell
python scripts\runtime_app_download_smoke.py `
  --redact `
  --apps-json ..\POKROV-app\artifacts\releases\release-handoff.json `
  --require-release-handoff `
  --policy-only
```

Then verify reachability:

```powershell
python scripts\runtime_app_download_smoke.py `
  --redact `
  --apps-json ..\POKROV-app\artifacts\releases\release-handoff.json `
  --require-release-handoff
```

Dry-run the exact brain values without mutation:

```powershell
python scripts\remote_brain_apply_release_handoff.py `
  --brain-ip 82.21.114.104 `
  --metadata-file ..\POKROV-app\artifacts\releases\release-handoff.json `
  --dry-run
```

The real sync requires a narrow runtime authorization file with all markers:

```text
RUNTIME LINK SYNC GO FOR APP-DOWNLOAD SMOKE
OPERATOR_APPROVED_RUNTIME_LINK_SYNC=true
STAGED GITHUB ASSET REACHABILITY GREEN
NO PUBLIC ANNOUNCEMENT
PAID CHECKOUT REMAINS CLOSED
```

After that file exists:

```powershell
python scripts\remote_brain_apply_release_handoff.py `
  --brain-ip 82.21.114.104 `
  --metadata-file ..\POKROV-app\artifacts\releases\release-handoff.json `
  --go-evidence-file docs\audit-artifacts\public-beta-runtime-link-sync-authorization-2026-05-08.md
```

Then rerun the live smoke:

```powershell
python scripts\brain_runtime_app_download_smoke.py `
  --brain-ip 82.21.114.104 `
  --ssh-user root `
  --ssh-port 29374 `
  --source-unit portal-bot `
  --tg-id 900000001 `
  --output docs\audit-artifacts\runtime-app-download-smoke-brain-2026-05-08-post-handoff.json
```

Stop and keep the release `NO-GO` if any of these happens:

- live `/api/client/apps` still lacks Android, Windows, or docs URLs;
- any APK/EXE/docs URL fails;
- provider policy returns a green non-Lava catalog;
- raw Telegram init data or bot token appears in output.

## 2. Email Public Proof

Run after a safe recipient is provided:

```powershell
python scripts\brain_payment_email_readiness.py `
  --brain-ip 82.21.114.104 `
  --ssh-user root `
  --ssh-port 29374 `
  --post-deploy-live `
  --email-probe-to <probe-email> `
  --output docs\audit-artifacts\brain-post-deploy-live-probe-2026-05-08.json
```

Then aggregate:

```powershell
python scripts\public_beta_post_deploy_probe.py `
  --brain-live-probe-json docs\audit-artifacts\brain-post-deploy-live-probe-2026-05-08.json `
  --output docs\audit-artifacts\public-beta-post-deploy-probe-2026-05-08.json
```

Pass condition includes:

- `email_public_runtime_config_passed=true`
- `safe_to_keep_email_public=true`
- `email_live_delivery_probe_passed=true`
- `post_deploy_probe_modes.email_public_runtime=PASS`

## 3. Lava.top Proof

Run only with safe buyer data:

```powershell
python scripts\brain_payment_email_readiness.py `
  --brain-ip 82.21.114.104 `
  --ssh-user root `
  --ssh-port 29374 `
  --post-deploy-live `
  --email-probe-to <probe-email> `
  --lavatop-probe-email <buyer-email> `
  --output docs\audit-artifacts\brain-post-deploy-live-probe-2026-05-08.json
```

Paid checkout remains closed until these artifacts are green:

- `docs/audit-artifacts/payment-email-readiness-brain-2026-05-08.json`
- `docs/audit-artifacts/paid-checkout-launch-evidence-brain-2026-05-08.json`

The Lava evidence must cover provider acceptance, invoice creation, authenticated webhook, replay/idempotency, failed-payment no-fulfillment, manual-review mismatch, reconciliation, and paid access-key email delivery.

## 4. Optional Evidence Replacement

Android attestation is accepted for this beta pass. If raw evidence is later available:

```powershell
$env:ANDROID_AUDIT_EVIDENCE_JSON="<path-to-raw-android-localhost-audit-json>"
python scripts\validate_android_physical_audit_evidence.py `
  $env:ANDROID_AUDIT_EVIDENCE_JSON `
  --output docs\audit-artifacts\android-physical-audit-evidence-validation-2026-05-08.json
```

RU-origin remains `SKIPPED_BY_OPERATOR`; public copy must not claim RU-origin readiness.

## Final Recheck

After any unblock step:

```powershell
python scripts\public_beta_launch_decision.py `
  --output docs\audit-artifacts\public-beta-launch-decision-2026-05-08.json
```

Public publication requires `verdict=GO` and `safe_to_publish_public_beta=true`. Until then, keep the Telegram channel copy as draft-only.
