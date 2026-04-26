# Fix Cycle Ledger

Status: active

| ID | Trigger | Root cause | Fix | Verification |
| --- | --- | --- | --- | --- |
| FIX-001 | Review: Telegram init-data redaction incomplete. | Redaction covered only space-form `--init-data` and a small field set. | Added equals-form handling and extra Telegram fields including `signature` and `chat_instance`; added wrapper stdout/stderr redaction tests. | `python -m pytest tests/test_release_gate_check.py tests/test_runtime_app_download_smoke.py -q` |
| FIX-002 | Review: Android audit could pass against stale/debug installed app. | Release gate only required a physical serial for Android build gates. | Added `ANDROID_AUDIT_RELEASE_EVIDENCE`, `--require-release-build`, package evidence parsing, debuggable/version checks, and docs updates. | `python -m pytest tests/test_android_localhost_audit.py tests/test_release_gate_check.py -q` |
| FIX-003 | Review: payment gate wording sounded optional for broad launch. | Runbook did not distinguish gated-beta prep from broad release approval. | Clarified that unavailable checkout is acceptable only for prep/gated beta and does not make broad release green. | docs review and `python scripts/check-links.py` |
| FIX-004 | Review: active Open Beta work order was not indexed. | Docs index linked generic work-orders README only. | Added links to active work-order index and launch decision. | `python scripts/check-links.py` |
| FIX-005 | Review: stale tech-debt/design entries after implementation. | Work-order synthesis still described missing wrapper/design files. | Updated synthesis and tech-debt register to reflect implemented wrapper/design/schema and remaining live-evidence blockers. | targeted grep for stale phrases |
| FIX-006 | Review: client docs had retired-lane and incomplete route/DNS evidence wording. | Windows and Android readiness docs inherited older bridge/four-platform language and missed public route/DNS checks. | Removed retired-lane claims and added route-mode, DNS/leak, and origin-evidence blockers. | targeted grep and client-doc review |
| FIX-007 | Quick release gate initially failed WebApp E2E. | `webapp/node_modules` was absent in the isolated worktree, so `next` was missing for Playwright command. | Ran `npm.cmd ci --no-audit --no-fund` in `webapp/`; reran E2E and quick release gate. | Playwright 31 passed; `release_gate_check.py --quick` PASS |
