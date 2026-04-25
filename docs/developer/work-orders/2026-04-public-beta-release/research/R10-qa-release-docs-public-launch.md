# R10 QA Release Docs Public Launch

Status: complete
Date: 2026-04-25
Role: R10
Scope: QA, release gates, docs, public launch operations

Constraint honored: read-only research except this assigned file.

Claim labels used below: `confirmed`, `probable`, `unknown`, `needs local run`, `blocked by missing access`.

## Sources Checked

Confirmed:

- `AGENTS.md`
- `docs/README.md`
- `docs/product/portal-vpn-product.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/app-first-and-bonus-flows.md`
- `docs/operations/deployment-and-access.md`
- `docs/operations/monitoring-and-visibility.md`
- `docs/operations/publishing-and-signing-guide.md`
- `docs/developer/developer-guide.md`
- `docs/developer/repository-map.md`
- `docs/developer/orchestration/orchestration-standard.md`
- `scripts/release_gate_check.py`
- `docs/audit-artifacts/release_gate_report.md`
- `docs/audit-artifacts/release_gate_quick_report.md`
- `docs/developer/work-orders/2026-04-beta-release/INDEX.md`
- `docs/developer/work-orders/2026-04-beta-release/05-release-gate-plan.md`
- `docs/developer/work-orders/2026-04-beta-release/06-paid-beta-signoff.md`
- `docs/developer/work-orders/2026-04-beta-release/07-paid-beta-user-communications.md`
- `docs/developer/work-orders/2026-04-beta-release/evidence/logs/WO-008-infra-nodes-observability-deploy.md`
- `docs/developer/work-orders/2026-04-beta-release/evidence/release-gates/W10-final-gate-summary.md`
- `docs/developer/work-orders/2026-04-beta-release/research/R10-qa-release-docs.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md`

Unknown:

- I found no narrative 05/06/07/08 docs under `docs/developer/work-orders/2026-04-public-beta-release/` yet. The public-beta wave currently has evidence scaffolding and git-state captures, so this memo treats the paid-beta 05/06/07 docs plus W08/W10 evidence as inherited source material.

## Executive Finding

Confirmed: public beta is not launch-ready from the inspected evidence.

The local default and quick gate reports are green as of `2026-04-25`, and W10 recorded local Android APK/AAB plus Windows beta build success. That is useful RC evidence, but it does not clear public beta. Public beta still needs live deploy proof, runtime handoff proof, signed or explicitly limited artifact posture, Android physical release-build audit, live payment/provider proof, separate origin checks, rollback proof, emergency-switch proof, and approved launch communications.

Public beta should stay `blocked` until the release captain can point to a fresh signoff packet with those P0 gates either green or explicitly accepted as public-beta limitations.

## P0 Public Beta Gate Plan

| Gate | Label | Required evidence | Current state |
| --- | --- | --- | --- |
| Fresh full gate | confirmed | `python scripts/release_gate_check.py --output docs/audit-artifacts/release_gate_report.md` after all public-beta edits | last inspected report is `PASS`, but current worktree is actively dirty; needs rerun before signoff |
| Quick triage gate | confirmed | `python scripts/release_gate_check.py --quick --output docs/audit-artifacts/release_gate_quick_report.md` | last inspected report is `PASS`; needs rerun after concurrent agents finish |
| Payment regression | confirmed | `python -m pytest tests/test_api_auth_and_tickets.py tests/test_api_payments_callbacks.py -q` and admin reconciliation evidence | W10 says `79 passed`; rerun required after payment/admin edits |
| Payment live proof | blocked by missing access | provider acceptance, signed webhook verification, low-volume sandbox/live payment, duplicate webhook, failed/refund/manual-review path | not completed in W10 |
| Client full tests | confirmed | `python scripts/run_client_release_gate.py preflight` and `python scripts/run_client_release_gate.py test --suite full` against `POKROV-app` | full suite passed in saved report; rerun required |
| Client artifact builds | confirmed | `python scripts/run_client_release_gate.py build --target windows`, `android-apk`, `android-aab` | W10 says all local builds passed after follow-up |
| Android physical audit | confirmed | release-installed physical device run of `python scripts/android_localhost_audit.py --serial <serial>` before/after connect/disconnect | blocked; no attached physical device |
| Android signing | confirmed | production signing proof, not debug-keystore fallback | not proven |
| Windows signing/posture | confirmed | trusted signing proof, or explicit public-beta decision that Windows remains gated/unsigned with warnings | trusted signing not proven |
| Runtime download smoke | confirmed | `TELEGRAM_INIT_DATA` backed `scripts/smoke_client_apps.py --check-providers --require-release-handoff` or equivalent redacted live session proof | skipped in saved reports |
| Release handoff sync | confirmed | versioned `POKROV-app/artifacts/releases/pokrov-app/<version>/release-handoff.json`, runtime env sync, public URL validation | not proven |
| Deploy | confirmed | backend/static deploy evidence, service status, post-deploy smoke, current deployed version | not completed |
| Origin checks | confirmed | separate `current-origin check`, `brain-origin check`, and `RU-origin check` lines | current-origin public host check passed; brain/RU blocked |
| Backup/rollback | confirmed | DB backup if migration/data deploy, static rollback source, backend rollback command, release-handoff rollback source | not completed |
| Emergency controls | confirmed | checkout disable, trial disable, downloads disable, Telegram bonus pause, webhook fulfillment pause, manual extend/revoke | not proven live |
| Support readiness | confirmed | cabinet ticket flow, support bot fallback, admin payment/device/ticket visibility, 24h best-effort copy | local evidence partial; live proof missing |
| Comms approval | confirmed | public-beta announcement, payment-opened, pause/maintenance, known-limitations, support instructions | paid-beta drafts exist but are not approved to send and may need public-beta wording review |

## P1 Public Beta Gates

- confirmed: Run `marketing` build plus `npm.cmd run check:seo` when public SEO, checkout, install, legal, metadata, or release URLs change.
- confirmed: Run `webapp` build plus `npm.cmd run test:e2e` and `npm.cmd run test:e2e:admin` after cabinet/admin/payment/support edits.
- confirmed: Capture required screenshots from inherited `05-release-gate-plan.md`: marketing homepage, checkout, install, cabinet, tariff/payment, devices/downloads, support, admin users/payments/nodes/tickets, Android shell, Windows shell.
- confirmed: Verify public copy keeps `POKROV` naming, avoids direct public product wording with `VPN`, keeps email continuation marked `soon`, and keeps `Blocked only` hidden/internal.
- probable: Add a public-beta `INDEX.md` or signoff doc before launch so the new wave has its own 05/06/07/08 equivalents instead of relying only on inherited paid-beta docs.
- probable: Include active client root, client platform gates, Android audit status, runtime smoke status, and origin status in the final release-captain headline so stale local PASS reports cannot be misread.

## Live And Manual Blockers

Confirmed:

- Android public release is blocked by missing physical release-build localhost/control-surface audit and production signing proof.
- Local repo/static gates do not prove live deploy, live node enablement, runtime download authorization, or production payment behavior.
- W10 did not deploy, push, onboard users, or publish artifacts.
- `release_gate_check.py` can pass without client platform build gates unless `--client-platform-gates` is supplied.
- Android build gates in `release_gate_check.py` require `ANDROID_AUDIT_SERIAL` and reject emulator serials.
- Runtime app-download smoke is skipped unless a live token/session input is available.
- Brain-origin and RU-origin checks remain blocked by access/probe availability in inspected evidence.
- Production backup/restore and rollback proof are missing.

Probable:

- A public-beta launch attempt will need a stricter signoff threshold than paid beta because public surfaces, download URLs, public artifact trust, support mailbox readiness, and marketing copy become user-visible outside an invite-only audience.
- The current dirty multi-agent worktree invalidates any final gate result until all assigned changes are merged or intentionally excluded.

Unknown:

- Whether live provider dashboard category/product acceptance is complete.
- Whether production `APP_*` artifact URLs match the current `POKROV-app` beta artifacts.
- Whether `support@pokrov.space` and any required sender identity are live enough for public support and store/contact use.
- Whether current production node metrics freshness and per-node alerts are healthy from admin endpoints.

## Final Signoff Shape

Use one release-captain signoff document for public beta. It should not be closed by an executor. It should include:

1. Decision: `go`, `go with accepted limitations`, or `blocked`.
2. Candidate identity: platform branch/HEAD, `origin/master` HEAD, client branch/HEAD, `origin/main` HEAD, artifact version, artifact checksums, signing status.
3. Gate table: quick/full gate timestamps, payment suite, frontend builds/E2E, client tests/builds, Android audit, runtime smoke, live payment proof, deploy smoke, origin checks.
4. Public limitations: Android status, Windows status, email continuation status, support SLA wording, routing-mode limitations.
5. Live operations: deployed commit, service status, metrics freshness, node health, support/admin availability.
6. Rollback: backend rollback command, static rollback source, release-handoff rollback source, DB backup/restore note, node/transport rollback path.
7. Emergency controls: checkout/trial/download/bonus/webhook pause plus manual extend/revoke proof.
8. Communications: approved public-beta announcement, payment-opened copy, maintenance/pause copy, known limitations, support instructions.
9. Evidence hygiene: redacted logs/screenshots only; no raw tokens, payment IDs, Telegram IDs, emails, webhook payloads, private links, or secret values.

Public beta can only be `go with accepted limitations` if every limitation is user-visible and operationally controllable. Android without physical audit should remain internal-only, not public.

## Launch Readiness

Confirmed ready-ish:

- Local quick and default reports from W10 follow-up are green.
- Local client tests and local Android/Windows builds have useful inherited evidence.
- Paid-beta communication drafts exist for opening, payment pause, Android internal APK warning, Windows unsigned warning, support instructions, known limitations, waitlist, post-beta thanks, onboarding, and manual reconciliation.
- Canonical docs define public scope as Android + Windows, Apple as readiness-only, email continuation as `soon`, and support as best-effort.

Needs local run:

- Rerun all listed gates after the public-beta wave finishes current edits.
- Rerun screenshots/manual browser checks because current UI/public copy has many in-flight changes.
- Rerun client platform builds from `POKROV-app` and copy artifact metadata into the final signoff.

Blocked by missing access:

- Live deploy and post-deploy smoke.
- Live payment/provider proof.
- Runtime app-download smoke with a real beta session.
- Brain-origin and RU-origin evidence.
- Android physical-device audit.

## Rollback Readiness

Confirmed missing for public beta:

- No production deploy happened in W10, so there is no deployment rollback record from that pass.
- Future deploy must capture backend previous version, static backup source, release-handoff rollback source, DB backup status, node/transport rollback commands, and post-rollback checks.
- Emergency controls must be verified before public beta users are sent to checkout or downloads.

Probable:

- Public-beta rollback should be rehearsed as a read-only checklist first, then as a low-risk operational drill before any public announcement.

## Communications Readiness

Confirmed:

- Inherited paid-beta comms are prepared but explicitly not approved to send while signoff is blocked.
- Messages correctly warn that Android is internal beta only and Windows may show SmartScreen or unknown-publisher warnings.
- Support copy tells users not to share keys, connection links, receipts, payment numbers, tokens, or personal data publicly.

Needs local run/review:

- Public-beta wording should be reviewed against the public wording rule and current release posture.
- Do not send payment-opened or public launch copy until live payment and download gates pass or the orchestrator accepts a narrower limitation.
- If public beta differs from paid beta, create public-beta-specific comms rather than reusing invite-only paid-beta wording unchanged.

## Tests To Rerun Before Signoff

Run from the platform worktree unless noted:

```powershell
python scripts/release_gate_check.py --quick --output docs/audit-artifacts/release_gate_quick_report.md
python scripts/release_gate_check.py --output docs/audit-artifacts/release_gate_report.md
python -m pytest tests/test_api_auth_and_tickets.py tests/test_api_payments_callbacks.py -q
python -m pytest tests/test_bot_paywall.py tests/test_tickets_repo.py tests/test_reviews_username_masking.py -q
python -m pytest tests/test_worker_retention.py tests/test_free_cycle_service.py -q
python scripts/api_lifecycle_smoke.py
python scripts/client_security_smoke.py
python scripts/run_client_release_gate.py preflight
python scripts/run_client_release_gate.py test --suite full
python scripts/run_client_release_gate.py build --target windows
python scripts/run_client_release_gate.py build --target android-apk
python scripts/run_client_release_gate.py build --target android-aab
```

When physical Android hardware is attached:

```powershell
set ANDROID_AUDIT_SERIAL=<physical-device-serial>
python scripts/release_gate_check.py --client-platform-gates windows,android-apk,android-aab --output docs/audit-artifacts/release_gate_report.md
python scripts/android_localhost_audit.py --serial %ANDROID_AUDIT_SERIAL% --connect-wait-sec 30 --disconnect-wait-sec 15
```

Frontend focused gates:

```powershell
cd marketing
npm.cmd run build
npm.cmd run check:seo
cd ..\webapp
npm.cmd run build
npm.cmd run test:e2e
npm.cmd run test:e2e:admin
```

Live/operator gates, only with approval and redaction:

```powershell
python scripts/release_gate_check.py --brain-ip 82.21.114.104 --quick --output docs/audit-artifacts/release_gate_quick_report.md
python scripts/release_orchestrator.py --brain-ip 82.21.114.104 --release-metadata-file <POKROV-app release-handoff.json>
python scripts/smoke_client_apps.py --check-providers --require-release-handoff
```

## Highest-Risk Findings

1. confirmed: Android cannot be public-beta distributed until a release-installed physical device passes the localhost/control-surface audit and production signing is proven.
2. blocked by missing access: Live provider acceptance and signed webhook/payment behavior are still unproven; local callback tests do not prove paid public launch safety.
3. confirmed: The current green local reports omit live deploy, runtime download smoke, brain-origin, RU-origin, backup, rollback, and emergency-switch evidence.
4. probable: Concurrent public-beta edits make the W10 green reports stale for final signoff until quick/full gates, frontend E2E, payment tests, and client gates are rerun.
5. confirmed: Public launch communications exist only as inherited paid-beta drafts and are explicitly not approved to send while signoff remains blocked.

## Recommendation

Keep public beta `blocked`.

Next release-captain action should be a public-beta signoff packet, not another broad research pass: freeze the candidate, rerun the P0/P1 gates, collect live/manual evidence, classify every blocked item, and only then approve launch, launch-with-limitations, or rollback-safe no-go.
