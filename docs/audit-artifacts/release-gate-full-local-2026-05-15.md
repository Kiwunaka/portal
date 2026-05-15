# Release Gate Report

- Generated at: `2026-05-15 04:14:00`
- Status: `PASS`
- Gate set: `default`
- Brain IP supplied: `no`
- Client platform gates: `none`
- Android audit required by selected gates: `operator-attested separately`

## Summary

The monolithic `python scripts\release_gate_check.py --output docs\audit-artifacts\release-gate-full-local-2026-05-15.md` orchestration was stopped after a timeout before it wrote a report. The same default-gate command set was then run as separate foreground commands so each result could be observed and recorded.

| Gate | Command | Result |
|---|---|---|
| Release pytest matrix | `python -m pytest portal_bot/tests/test_app_first_api.py tests/test_portal_api.py tests/test_worker_retention.py tests/test_observer_service.py tests/test_observer_api.py tests/test_collect_xray_observer.py tests/test_predeploy_node_readiness.py tests/test_admin_webapp_smoke.py tests/test_public_copy_guardrails.py tests/test_reviews_username_masking.py -q` | `53 passed` |
| Admin/auth regressions | `python -m pytest tests\test_api_auth_and_tickets.py -q` | `63 passed` |
| Payment and marketing release honesty | `python -m pytest tests\test_bot_paywall.py tests\test_marketing_release_readiness.py -q` | `49 passed` |
| Paid checkout/tooling guardrails | `python -m pytest tests\test_paid_checkout_launch_evidence_check.py tests\test_live_probe_scripts.py tests\test_public_beta_post_deploy_probe.py tests\test_freekassa_api_probe.py tests\test_freekassa_staging_smoke.py -q` | `21 passed` |
| GitHub and launch decision tooling | `python -m pytest tests\test_prepare_github_release_plan.py tests\test_publish_github_release_assets.py tests\test_public_beta_external_access_preflight.py tests\test_public_beta_launch_decision.py -q` | `53 passed` |
| Client preflight | `python scripts\run_client_release_gate.py preflight` | `PASS` |
| Client full tests | `python scripts\run_client_release_gate.py test --suite full` | `PASS` |
| Backend payment callbacks | `python -m pytest tests\test_api_payments_callbacks.py tests\test_lavatop_payment_providers.py -q` | `36 passed` |
| Probe redaction/unit checks | `python -m pytest tests\test_live_probe_scripts.py tests\test_brain_payment_email_readiness.py -q` | `13 passed` |
| Quick release gate bundle | `python scripts\release_gate_check.py --quick --output docs\audit-artifacts\release-gate-local-quick-2026-05-15.md` | `PASS` |

## Evidence Classification

| Evidence | Scope | Status | Notes |
|---|---|---|---|
| current-origin check | local default gate set | PASS | Manual equivalent of the default gate set passed after the monolithic wrapper timed out before writing a report. |
| brain-origin check | separate brain runtime/payment probes | PASS | See `docs/audit-artifacts/brain-runtime-app-download-smoke-2026-05-15.json` and `docs/audit-artifacts/brain-post-deploy-live-probe-2026-05-15.json`; node readiness is tracked separately. |
| RU-origin check | external RU probe (`mini` or replacement) | OPERATOR_ATTESTED_LIMITED | Scope reduced by owner: Telegram-from-Russia is not a blocker; current remaining RU check is brain/API reachability if access exists. |
| Android physical audit | release-build localhost/control-surface audit | OPERATOR_ATTESTED | Owner reported the physical Android audit was completed and OK on 2026-05-15. |
| Runtime app-download smoke | `/api/client/apps` and provider checks | PASS | Brain-signed runtime smoke passed with GitHub APK/EXE and install docs URLs. |
| Client platform builds | GitHub Release artifacts | PASS | APK/EXE already published in GitHub Releases and fresh HEAD checks returned HTTP 200. |

## Notes

- Pytest emitted a Windows temp cleanup `PermissionError` after some runs; the affected commands still exited `0` after reporting all tests passed.
- No raw tokens, payment ids, Telegram initData, subscription URLs, private emails, or callback payloads are stored in this artifact.
