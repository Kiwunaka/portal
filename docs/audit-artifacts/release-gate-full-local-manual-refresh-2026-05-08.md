# Manual Full Local Gate Component Refresh

- Generated at: `2026-05-08 10:52:15 +03:00`
- Status: `PASS`
- Scope: current-origin full/default gate components, run manually after the latest bot access-key keyboard repair/redeploy and brain quick gate refresh.
- Standard runner note: `python scripts\release_gate_check.py --output docs\audit-artifacts\release-gate-full-local-2026-05-08.md` timed out in the runner on 2026-05-08 and is retained separately as `docs/audit-artifacts/release-gate-full-local-refresh-attempt-2026-05-08.md`. This artifact is a manual component refresh, not an overwrite of the standard report.

## Summary

| Gate component | Status | Evidence |
| --- | --- | --- |
| Release pytest matrix | PASS | `221 passed, 3 subtests passed in 277.11s` |
| Admin/auth regressions | PASS | `64 passed in 75.13s` |
| Client preflight | PASS | POKROV-app gate root, Android shell, Windows shell, scripts, and build lanes present |
| Client security smoke | PASS | Product contract, runtime profile/artifacts, Android manifest/build config, and Windows release seed passed |
| Client Flutter tests | PASS | Workspace Flutter tests, Android shell tests, Windows shell tests, and Android Gradle unit tests passed |
| API lifecycle smoke | PASS | `Ran 1 test ... OK` |
| Public link checks | PASS | SEO, CTA, legal, checkout fallback, and compatibility link checks passed |
| Marketing production build | PASS | `next build` completed; 16 static routes generated |
| Admin WebApp smoke | PASS | `Admin WebApp smoke passed.` |
| WebApp production build | PASS | `next build` completed; 31 static routes generated |
| WebApp Playwright E2E | PASS | `47 passed (1.6m)` |
| UI visual smoke | PASS | `UI visual smoke passed.` |

## Commands

```powershell
python -m pytest portal_bot/tests/test_app_first_api.py tests/test_portal_api.py tests/test_worker_retention.py tests/test_observer_service.py tests/test_observer_api.py tests/test_collect_xray_observer.py tests/test_predeploy_node_readiness.py tests/test_smart_connect_api.py tests/test_network_rollout_api.py tests/test_client_security_smoke.py tests/test_smoke_client_apps.py tests/test_admin_webapp_smoke.py tests/test_bot_paywall.py tests/test_marketing_release_readiness.py tests/test_live_probe_scripts.py tests/test_public_beta_post_deploy_probe.py tests/test_public_beta_external_access_preflight.py tests/test_validate_android_physical_audit_evidence.py tests/test_paid_checkout_launch_evidence_check.py tests/test_freekassa_api_probe.py tests/test_freekassa_staging_smoke.py tests/test_prepare_github_release_plan.py tests/test_publish_github_release_assets.py tests/test_public_beta_launch_decision.py tests/test_public_copy_guardrails.py tests/test_reviews_username_masking.py -q --basetemp .tmp\pytest-basetemp\manual-full-matrix-20260508-latest
python -m pytest tests/test_api_auth_and_tickets.py -q --basetemp .tmp\pytest-basetemp\manual-auth-20260508-latest
python scripts\run_client_release_gate.py test --suite full
python scripts\run_client_release_gate.py preflight
python scripts\client_security_smoke.py
python scripts\api_lifecycle_smoke.py
python scripts\check-links.py
python scripts\admin_webapp_smoke.py
python scripts\ui_visual_smoke.py
npm.cmd run build # in marketing/
npm.cmd run build # in webapp/
npm.cmd run test:e2e # in webapp/
```

## Evidence Limits

- This is a current-origin component refresh only.
- It does not prove brain-origin reachability; the current brain-origin evidence is `docs/audit-artifacts/release-gate-brain-2026-05-08.md`, generated at `2026-05-08 08:36:26`.
- It does not prove RU-origin readiness, Android physical release-build audit, runtime `/api/client/apps` with env-only Telegram init data, GitHub Release publication, live email inbox delivery, or Lava.top paid-checkout evidence.
- Standard full runner reliability still needs investigation because the 2026-05-08 wrapper attempt timed out even though the individual components above passed.
