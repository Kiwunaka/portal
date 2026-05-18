# GOAL.md — POKROV Public Release GO

## Run command for Codex

Use this from the platform workspace after Codex has access to both repositories:

```text
/goal Read GOAL.md, AGENTS.md, the latest git history, and the current release evidence. Execute the POKROV public Android + Windows release objective end to end. Continue in evidence-backed checkpoints until COMPLETE_PUBLIC_RELEASE_GO or RELEASE_BLOCKED_BY_ACCESS_NO_VALID_PATH. The owner authorizes production deploys, service restarts, runtime APP_* sync, live Lava.top/email probes, commits, pushes, and final launch/status doc updates. Do not fabricate evidence. Redact secrets, personal identifiers, payment IDs, callback payloads, Telegram initData, subscription URLs, and private emails from committed evidence.
```

## Owner authorization and intended outcome

The target is **public release to real users** for POKROV Android + Windows.

Owner decisions for this goal:

- Release target: public Android + Windows release, outside app stores, as-is.
- App Store, Google Play, Microsoft Store, iOS, and macOS are out of scope for this release.
- Do not block release on trusted Windows signing, app-store signing, AAB/store submission, notarization, MSIX/store packaging, or new app-store manifests.
- Keep public versioning truthful. Do not invent `1.0.0` unless current repo docs and product versioning are deliberately updated. The default public line may remain `0.x.x-beta` while still being public.
- Production access is authorized: SSH to `brain`, backend/static deploy, service restart, runtime env inspection/mutation, release handoff sync, smoke checks, commits, and push.
- Lava.top payment is considered working by the owner, but Codex must still attach fresh redacted evidence for the exact public route being enabled.
- Email is considered working by the owner, but Codex must still verify runtime readiness and retain redacted evidence.
- Buyer/probe email is owner-provided. Use it only as a local runtime input such as `POKROV_RELEASE_BUYER_EMAIL`; do **not** commit the raw email address into docs or evidence.
- RU-origin check is reduced to **brain/API reachability from RU**. Telegram from Russia is expected unavailable and must not block this release. Do not treat RU Telegram unreachability as a failed gate.
- If RU host access is missing, search local files and prior evidence for current `mini` / RU access. If unavailable, mark only the RU brain-reachability gate as `BLOCKED_BY_ACCESS` with exact next command/input.
- Do not resume RF ingress, `rf1` promotion, or `mini` ingress experiments.

This owner authorization supersedes old `NO_GO` state files as a work order. It does **not** supersede the evidence rule: public GO is allowed only after the current candidate has real evidence or explicit owner-accepted `NOT_APPLICABLE` status for out-of-scope gates.

## Latest context to account for first

Before changing anything, inspect the current branch heads and latest commits. At minimum, account for these recent platform changes:

- `26f808b` — `Document live Lava and email beta evidence`.
- `2670c1e` — `Refresh cabinet after external checkout return`.
- `f9b499d` — `Fix Lava webhook behind local proxy`.
- `43b18f4` — `Stabilize cabinet navigation and beta checkout`.
- `b1c507b` — `Fix cabinet auth routing and CTA contrast`.

Current known state from the latest repo docs:

- Email continuation is no longer simply `soon`; it is live when `/api/auth/email/status` proves public delivery readiness.
- Lava.top `start_99` authenticated cabinet beta path has live evidence for invoice creation, authenticated success callback, invalid-auth rejection, account extension, and idempotency.
- `webapp/public/release-status.json` may still be stale and say `NO_GO` from 2026-05-09. It must be regenerated or updated after the new evidence run.
- `docs/developer/work-orders/2026-04-open-beta-v4/13-launch-decision.md` may still be old `NO_GO`. It is a state file to update only after gates are green.
- `docs/product/public-beta-prd.md` may still say broad public launch is not authorized. It must be updated only if this goal reaches public GO.

## Canonical workspaces

Platform workspace:

```text
C:/Users/kiwun/Documents/ai/VPN
```

Platform promotion truth:

```text
portal/master -> origin/master
```

Client workspace:

```text
C:/Users/kiwun/Documents/ai/POKROV-app
```

Client promotion truth:

```text
POKROV-app/main -> origin/main
```

Use dedicated branches/worktrees if either workspace is dirty. Do not reinterpret local aliases as source of truth.

## Must-read before changing anything

Read in this order:

1. `AGENTS.md`
2. `README.md`
3. `docs/README.md`
4. `docs/product/portal-vpn-product.md`
5. `docs/product/public-beta-prd.md`
6. `docs/product/payment-and-access-key-contract.md`
7. `docs/architecture/system-overview.md`
8. `docs/architecture/app-first-and-bonus-flows.md`
9. `docs/operations/deployment-and-access.md`
10. `docs/operations/public-beta-release-runbook.md`
11. `docs/operations/runtime-app-download-smoke.md`
12. `docs/operations/android-release-audit.md`
13. `docs/operations/lavatop-payment-operations.md`
14. `docs/operations/monitoring-and-visibility.md`
15. `docs/developer/developer-guide.md`
16. `docs/developer/repository-map.md`
17. `docs/developer/work-orders/2026-04-open-beta-v4/INDEX.md`
18. `docs/developer/work-orders/2026-04-open-beta-v4/13-launch-decision.md`
19. `docs/audit-artifacts/live-payment-email-confirmation-2026-05-15.md`
20. `webapp/README.md`
21. `webapp/public/release-status.json`
22. `C:/Users/kiwun/Documents/ai/POKROV-app/README.md`
23. `C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md`
24. `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md`
25. `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/release-handoff.json` if present

If a file is missing, record it and continue with the nearest canonical replacement.

## Non-negotiable product rules

Preserve these unless a newer canonical doc is deliberately changed in the same task:

- Brand and public product line are `POKROV`.
- Avoid direct public `VPN` product wording. Keep it only in legacy names, compatibility labels, filenames, or unavoidable technical identifiers.
- Strategy is `consumer-first` and `app-first`.
- Trial is `5 days`.
- Telegram reward is `+10 days`.
- Telegram is optional continuation, linking, bonus, recovery, support, feedback, and fallback commerce. It is not the primary onboarding wall.
- Android + Windows are the public release targets.
- iOS/macOS/store work is out of scope for this release.
- Marketing owns public acquisition and checkout continuation.
- WebApp owns continuation-first cabinet, renewal, downloads, redeem, support, and primary admin.
- `connect.pokrov.space` is config delivery, not public acquisition.
- Raw subscription links, QR, `?format=plain`, node internals, hostnames, public IPs, and transport acronyms must not reappear in first-layer consumer UX.
- Email browser continuation is live only when runtime readiness is green. If readiness fails, UI must degrade honestly.
- Public checkout may expose only evidence-backed routes/plans. If only `start_99` is proven, public checkout must be restricted to `start_99` until more evidence exists.
- Windows unsigned outside-store release is acceptable for this owner-approved release only with visible unknown-publisher/SmartScreen warning copy.
- Android outside-store APK release is acceptable as-is if runtime links, live download smoke, and current Android audit/attestation posture are documented honestly.

## Never do

- Never print or commit secrets, private keys, bearer tokens, callback signatures, raw payment payloads, raw payment IDs, raw Telegram initData, raw subscription URLs, personal connection links, private SSH keys, or full user identifiers.
- Never commit the raw buyer/probe email; use it only in local commands and redact it in retained evidence.
- Never delete retained evidence under `ops-local/`, `docs/audit-artifacts/`, `docs/developer/work-orders/`, retained bridge archives, signing material, merchant secrets, or SSH key packs.
- Never mark a gate as passed because a local/static check passed when that gate requires live runtime, brain-origin, RU-origin, provider, email-inbox, or deploy evidence.
- Never claim store readiness, trusted signing, notarization, TestFlight, Google Play, Microsoft Store, iOS, or macOS release.
- Never treat RU Telegram unreachability as a blocker. For this goal, RU-origin checks only brain/API reachability.
- Never run RF ingress, `rf1` promotion, or `mini` ingress experiments.

## Checkpoint 0 — baseline

Before fixing, write a local checkpoint note:

```text
CHECKPOINT 0 — Baseline
- platform branch + head SHA:
- client branch + head SHA:
- dirty files:
- latest platform commits reviewed:
- latest client commits reviewed:
- current release-status verdict:
- current launch decision:
- current runtime APP_* state:
- current Android/Windows artifact URLs:
- current Lava/email runtime status:
- current RU access source:
- known release blockers:
```

Inspect at minimum:

```powershell
git status
git log --oneline -30 --decorate
```

Run the same in `C:/Users/kiwun/Documents/ai/POKROV-app`.

## Gate matrix

Build or refresh a gate table with these gates. Every gate must have `status`, `evidence path`, `command/source`, `date/time`, `notes`, and `next action`.

Allowed statuses:

```text
PASS | FAIL | BLOCKED_BY_ACCESS | BLOCKED_BY_POLICY | NOT_APPLICABLE
```

Required gates:

1. `platform_git_baseline_clean_or_accounted`
2. `client_git_baseline_clean_or_accounted`
3. `current_origin_quick_gate`
4. `current_origin_full_gate`
5. `backend_payment_callback_tests`
6. `backend_app_first_and_api_tests`
7. `webapp_build_and_e2e`
8. `marketing_build_seo_links_visual`
9. `client_security_smoke`
10. `client_preflight`
11. `client_android_release_artifact_present`
12. `client_windows_release_artifact_present`
13. `runtime_APP_links_approved_and_synced`
14. `live_api_client_apps_contains_final_android_windows_urls`
15. `runtime_app_download_smoke_redacted`
16. `Android_release_audit_or_owner_accepted_attestation`
17. `Windows_unsigned_warning_copy`
18. `Lava_top_provider_catalog_live_and_lava_only`
19. `Lava_top_start_99_invoice_live`
20. `Lava_top_authenticated_success_webhook_live`
21. `Lava_top_invalid_auth_rejected`
22. `Lava_top_replay_idempotency`
23. `Lava_top_failed_payment_no_fulfillment`
24. `Lava_top_manual_review_or_mismatch`
25. `Lava_top_refund_chargeback_reconciliation_procedure`
26. `anonymous_public_checkout_emails_exactly_one_access_key`
27. `email_auth_status_green`
28. `email_register_verify_login_live`
29. `email_reset_or_recovery_live_or_degraded_honestly`
30. `post_deploy_payment_email_probe`
31. `current_origin_brain_api_reachability`
32. `brain_origin_self_check`
33. `RU_origin_brain_api_reachability_only`
34. `public_downloads_visible_and_truthful`
35. `public_checkout_visible_and_truthful_for_enabled_plan`
36. `public_copy_safe_claims`
37. `canonical_docs_consistency`
38. `release_status_json_consistency`
39. `final_launch_decision_GO`
40. `deploy_backend_static_and_verify`
41. `commits_and_push_complete`

Gate-specific rules:

- Mark signing/store/manifests as `NOT_APPLICABLE` for this release, with note: `Owner-approved outside-store Android+Windows release as-is; no trusted signing/store manifests in scope`.
- Mark RU Telegram checks as `NOT_APPLICABLE`, with note: `Owner states Telegram from Russia is unavailable; release RU check is brain/API reachability only`.
- If `start_99` is the only proven payment plan, restrict public checkout to `start_99` and mark other plans `NOT_APPLICABLE` or disabled.
- If raw Android physical audit cannot be produced but current docs accept operator attestation for this beta wave and owner accepts release as-is, mark `Android_release_audit_or_owner_accepted_attestation=PASS` only with exact evidence path and wording `OPERATOR_ATTESTED`, not raw evidence.
- If any runtime/deploy/probe input is missing, do not ask broad questions. Search local files, docs, env examples, `ops-local/`, audit artifacts, and release handoff metadata. If still missing, mark the precise gate `BLOCKED_BY_ACCESS`.

## Work policy

Work in checkpoints. At each checkpoint:

1. Pick the highest-impact non-green release gate.
2. Read the local source and docs for that gate.
3. Make the smallest safe change.
4. Run a meaningful verification.
5. Deploy or sync runtime values when that is the required next step and access exists.
6. Update evidence/status/docs only for facts actually proven.
7. Commit/push checkpoint changes when they are coherent and green.
8. Continue until public GO or a true access dead end.

Do not stop merely because old docs say `NO_GO`. Treat old `NO_GO` as the current state to overcome with evidence and updated launch decision.

## Verification commands

Use the exact command set that fits the touched area. Do not skip silently.

Backend focused checks:

```powershell
python -m pytest tests/test_api_payments_callbacks.py tests/test_lavatop_payment_providers.py -q
python -m pytest portal_bot/tests/test_app_first_api.py -q
python -m pytest tests/test_portal_api.py -q
python -m pytest tests/test_api_auth_and_tickets.py -q
python -m pytest tests/test_smart_connect_api.py tests/test_network_rollout_api.py -q
python scripts/api_lifecycle_smoke.py
```

Shared copy/frontend guardrails:

```powershell
python -m pytest tests/test_frontend_text_integrity.py tests/test_public_copy_guardrails.py -q
```

WebApp:

```powershell
cd webapp
npm.cmd run build
npm.cmd run test:e2e:cabinet
npm.cmd run test:e2e
npm.cmd run test:e2e:admin
```

Marketing:

```powershell
cd marketing
npm.cmd run check:seo
npm.cmd run build
cd ..
python scripts/check-links.py
python scripts/ui_visual_smoke.py
```

Client from platform root:

```powershell
python scripts/client_security_smoke.py
python scripts/run_client_release_gate.py preflight
python scripts/run_client_release_gate.py test --suite portal
python scripts/run_client_release_gate.py test --suite full
python scripts/run_client_release_gate.py build --target windows
python scripts/run_client_release_gate.py build --target android-apk
```

Release gate entrypoints:

```powershell
python scripts/release_gate_check.py --quick
python scripts/release_gate_check.py
python scripts/release_orchestrator.py --gates-only
```

Deploy and runtime checks:

```powershell
python scripts/release_orchestrator.py --brain-ip 82.21.114.104 --stage backend
python scripts/release_orchestrator.py --brain-ip 82.21.114.104 --stage static
python scripts/release_orchestrator.py --brain-ip 82.21.114.104 --stage verify
```

Payment/email post-deploy probe:

```powershell
$env:POKROV_RELEASE_BUYER_EMAIL="<owner-provided-buyer-email>"
python scripts\brain_payment_email_readiness.py --brain-ip 82.21.114.104 --ssh-user root --ssh-port 29374 --post-deploy-live --email-probe-to $env:POKROV_RELEASE_BUYER_EMAIL --lavatop-probe-email $env:POKROV_RELEASE_BUYER_EMAIL --output docs\audit-artifacts\brain-post-deploy-live-probe-<YYYY-MM-DD>.json
```

Runtime download smoke:

```powershell
python scripts\runtime_app_download_smoke.py --redact
```

Android audit if a physical device is available:

```powershell
python scripts\android_localhost_audit.py --serial <physical-device-serial> --connect-wait-sec 30 --disconnect-wait-sec 15
```

RU-origin brain/API reachability only:

```powershell
# First search local docs/ops-local for current RU host access.
# If mini/RU host access works, run only a brain/API reachability check from that origin.
# Do not check Telegram from RU for this release gate.
```

## Runtime APP_* sync policy

Runtime download links are not public merely because staged GitHub Release URLs exist.

For this owner-approved release, Codex may sync runtime `APP_*` values if final Android/Windows URLs are known or can be derived from release handoff metadata.

Required sequence:

1. Verify staged APK/EXE/docs URLs are reachable.
2. Confirm the values are the final public Android + Windows outside-store URLs.
3. Sync runtime `APP_ANDROID_APK_URL`, `APP_WINDOWS_EXE_URL`, and related docs/install URL values through the repo-approved script or documented deploy path.
4. Deploy/restart required services.
5. Verify `GET /api/client/apps` from live `api.pokrov.space` returns the final URLs.
6. Run `runtime_app_download_smoke.py --redact`.
7. Update retained evidence, `release-status.json`, and launch docs.

If final URLs cannot be found, search:

- `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/`
- `release-handoff.json`
- versioned `release-links.env`
- GitHub Releases
- `docs/audit-artifacts/`
- `ops-local/`

If still unavailable, mark `runtime_APP_links_approved_and_synced=BLOCKED_BY_ACCESS` with exact missing file/value.

## Lava.top and email release policy

The owner says payment and email are working. Treat that as permission to test and release, not as a substitute for evidence.

For public release, prove and retain redacted evidence for:

1. Lava.top-only provider catalog.
2. Live `start_99` invoice creation.
3. Hosted checkout return behavior.
4. Authenticated success callback activates the account or issues the key as expected.
5. Missing/invalid auth is rejected.
6. Replay/idempotency does not extend access or issue a key twice.
7. Failed payment does not fulfill access.
8. Manual-review/mismatch path does not fulfill access.
9. Refund/chargeback reconciliation has an operator procedure and, if feasible, a live/provider-backed proof.
10. Anonymous public checkout sends exactly one access key email to the probe buyer email.
11. Email auth status is green.
12. Email register/verify/login is live.
13. Reset/recovery is live or the UI degrades honestly if not in scope.

Do not commit raw email addresses or payment identifiers. In evidence, write `redacted buyer email`, `redacted order id`, `redacted payment id`.

## Android and Windows release policy

Android:

- Release target is outside-store APK for real public users.
- Do not block on Google Play or AAB/store submission.
- Use current operator-attested physical-device audit if canonical docs and current owner decision allow it.
- Do not describe operator attestation as raw audit evidence.
- If a physical device is available, run the raw audit and replace/upgrade evidence.

Windows:

- Release target is outside-store unsigned Windows beta artifact.
- Do not block on trusted signing, MSIX, Microsoft Store, or SmartScreen removal.
- Public copy must warn about SmartScreen/unknown-publisher prompts.
- Verify download, install/handoff copy, and cabinet/download surfaces.

## RU-origin policy

For this release only:

- Required RU check: brain/API reachability from a Russian origin, if access exists.
- Telegram from Russia is expected unavailable and not a release blocker.
- Do not run Telegram reachability as a failing RU gate.
- Do not run RF ingress or `mini` ingress experiments.
- If RU access is unavailable after searching local files and retained evidence, mark `RU_origin_brain_api_reachability_only=BLOCKED_BY_ACCESS` and state exact missing access.

## Docs and status updates

When facts change, update canonical docs in the same change set.

Likely affected files:

- `webapp/public/release-status.json`
- `docs/product/public-beta-prd.md`
- `docs/product/payment-and-access-key-contract.md`
- `docs/product/portal-vpn-product.md` if public release scope or email/payment claims change
- `docs/architecture/system-overview.md` if runtime flow changes
- `docs/architecture/app-first-and-bonus-flows.md` if auth/payment/session flow changes
- `docs/operations/public-beta-release-runbook.md`
- `docs/operations/runtime-app-download-smoke.md`
- `docs/operations/lavatop-payment-operations.md`
- `docs/operations/deployment-and-access.md`
- `docs/developer/work-orders/2026-04-open-beta-v4/13-launch-decision.md`
- new dated files under `docs/audit-artifacts/`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/...` when client handoff metadata changes

Do not document speculative future behavior. Only document confirmed code, deployed runtime status, live probes, owner-approved scope, and retained evidence.

## Public copy requirements

Before GO, scan public copy and live surfaces for these constraints:

- No direct public `VPN` product positioning except legacy/technical contexts.
- No claim that iOS/macOS/store releases are live.
- No claim that Windows is signed or SmartScreen-free.
- No claim that Telegram works from Russia.
- No raw subscription link as first-layer user CTA.
- No stale `soon` label for email when runtime status proves it live.
- No live email promise if runtime status fails.
- No public checkout plans beyond evidence-backed plan(s).
- No public download CTA unless runtime `/api/client/apps` and smoke evidence are green.

## Completion criteria

### COMPLETE_PUBLIC_RELEASE_GO

Report `COMPLETE_PUBLIC_RELEASE_GO` only when all are true:

- Required gate matrix is `PASS` or owner-approved `NOT_APPLICABLE` with rationale.
- Runtime Android/Windows links are live, approved, and smoke-tested.
- Public downloads are visible and truthful.
- Lava.top public checkout is live only for evidence-backed plan(s), with redacted live evidence.
- Email auth and paid-key email delivery are verified or any non-green email path degrades honestly.
- Android outside-store release state is truthful and accepted for this release.
- Windows unsigned warning posture is truthful and visible.
- RU-origin brain/API check is PASS, or the only remaining RU issue is exact `BLOCKED_BY_ACCESS` accepted by owner policy. Do not block on RU Telegram.
- `webapp/public/release-status.json` is updated to a current GO artifact for the approved release scope.
- `docs/developer/work-orders/2026-04-open-beta-v4/13-launch-decision.md` is updated from old NO_GO to exact GO scope.
- Product/runbook/client docs are consistent with the final public Android+Windows outside-store release scope.
- Backend/static deploy and live verify pass.
- Required tests/builds/smokes for touched areas pass or any skipped check has exact non-release-blocking rationale.
- Changes are committed and pushed to the appropriate canonical branches.

### RELEASE_BLOCKED_BY_ACCESS_NO_VALID_PATH

Report this only when no safe repo-owned work remains and progress requires missing access/input. Include:

- exact blocked gate;
- exact missing input;
- exact next command that would use it;
- what was already fixed, deployed, tested, and pushed.

Do not use this status while there is still a repo-owned contradiction, stale status file, failed build/test, or unverified live route that can be fixed with available access.

## Final report format

Use this format exactly:

```text
Result:
- COMPLETE_PUBLIC_RELEASE_GO | RELEASE_BLOCKED_BY_ACCESS_NO_VALID_PATH

What I checked:
-

What I found:
-

What I changed:
-

How I verified:
-

Gate matrix:
- gate: status — evidence/source — notes

Live public surfaces:
- marketing:
- webapp/cabinet:
- downloads:
- checkout:
- email:
- support:

Origin checks:
- current-origin check:
- brain-origin check:
- RU-origin brain/API check:
- RU Telegram check: NOT_APPLICABLE — owner states Telegram from Russia is unavailable and not a release blocker

Remaining blockers / risks:
-

Changed files:
-

Commits / branches / push status:
-

Final user-safe launch statement:
-
```
