# DeepSeek 4.1 high support rollout — 2026-09-10

Owner instruction: select DeepSeek 4.1 high and remove the completion-token limit.
This is a support-only change, not a platform/client release-readiness claim.

## Changes

- Exact OpenRouter `deepseek/deepseek-v4.1-flash`, high reasoning for text and images.
- `json_object` because this endpoint rejects `json_schema`; local closed schema and safety validation remain. `data_collection=allow` was disclosed in the preceding model matrix before the owner selected the route.
- Remove the support completion-token setting and request cap. Preserve 45-second synthesis, 18-second attachment, 50-second total deadline and bounded streamed responses.
- Accept safe replies up to 12,000 characters, keep short session memory, deliver Telegram replies in chunks.
- Redact and bound attachment fields instead of discarding the whole file when a field slightly exceeds its target length. Real repeats exposed uncertainty lengths of 205–271 against a 200-character projection.
- Clarify that active access does not decide refunds, matched same-account payments do not require another login, and the model cannot claim it transferred a ticket.

## Validation

All live calls originate on owned Brain and use synthetic accounts, payment states, PNG and PDF. No customer DB read, payment-provider action, ticket creation or customer messaging occurs in the smoke runner. The actual candidate adapter constructs requests without payload overrides. Tests do not prove model answers are always factually correct or measure complete client/Telegram latency.

Initial full run: 12/12 synthesis responses accepted, but PNG projection rejected; `predeploy.jsonl` retains it. `file-repeat.jsonl` retains two reproductions with field lengths. After projection repair, `corrected-file-repeat.jsonl` shows 4/4 files read across two repeats, with 1,330/1,661-character final replies accepted. A subsequent full run in `final-predeploy.jsonl` retains two safety-triggered local answers, 10/12 accepted model syntheses, 2/2 readable files, no API errors and no test-secret leakage. The exact committed candidate `0d66797d57bbdd0a90b143425fbddb75f9c4def1` then passed 12/12 model syntheses, 2/2 attachments, all concept/status checks, zero API failures and no test-secret leakage (`committed-predeploy.jsonl`). Three additional scenarios intentionally use code-owned transfer, operator suppression or local KB. This small sample is not an accuracy guarantee. `manifest.json` binds eight deployment files to the baseline and candidate. Read-only deployment PLAN passed.

Local checks: support suite initially 235 passed plus 184 subtests; focused updated support checks 158 passed plus 184 subtests, provider checks 24 passed. Documentation/evaluation checks 58 passed; platform-context audit PASS. Required backend regression PASS: 154 tests plus 8 subtests in 758.24 seconds. One early combined run was interrupted to separate slow backend tests from the fast support/documentation suites; it is not counted as a pass.

## Deployment

PASS: candidate `0d66797d57bbdd0a90b143425fbddb75f9c4def1` is deployed on Brain. The support surface is exactly hash-matched, both services are active with NRestarts=0 and effective DeepSeek 4.1 high settings. Delayed Brain health and current-origin HTTPS health pass. Postdeploy synthetic paid/access and PNG/PDF scenarios pass (`postdeploy.jsonl`); real customer conversations and RU-origin delivery were NOT_REQUESTED.

Process deviation: GitHub rejected the ordinary merge because the local commits were unsigned. The PowerShell command sequence continued into the authorized support deployment despite the earlier command failure. Production therefore briefly precedes source promotion. No branch protection was bypassed. Source promotion is being completed using the documented GitHub-signed, tree-equal snapshot procedure. Original feature commits and runtime receipts remain retained. Independent review was not performed.

`deploy-receipt.json` and `runtime-readback.json` retain exact service identities. Backup: `/root/portal_bot.deploy-backups/manual-support-ds41-0d66797d57bb`. Common environment and database were not changed. Both required checks on PR #270 head `22bde37` passed; release-base-isolation was SKIPPED by its workflow condition, not treated as a pass. `deploy.py` requires exact candidate and baseline hashes, validates staged Python/JSON, preserves `/root/portal_bot/.env`, backs up only the scoped files plus the support override, restarts only `portal-api` and `portal-helpbot`, and verifies delayed active/NRestarts=0 plus public API health. Failure restores the previous files and override.

## Exact commands

From the scoped worktree:

```powershell
python -B -m pytest -p no:cacheprovider tests/test_support_agent_policy.py tests/test_support_agent_service.py tests/test_support_agent_safety.py tests/test_support_ai_service.py tests/test_support_case_context.py -q
# PASS: 158 tests and 184 subtests
python -B -m pytest -p no:cacheprovider tests/test_support_agent_provider.py -q
# PASS: 24 tests, after fixing a test fixture reused after its response stream was consumed
python -u -B -m pytest -p no:cacheprovider tests/test_pokrov_support_agent_eval.py tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -v -o faulthandler_timeout=60
# PASS: 58 tests
python -B scripts/agent_context_packet_audit.py --platform-context-root .
# PASS platform-context
git diff --check
# PASS
python -u -B -m pytest -p no:cacheprovider portal_bot/tests/test_app_first_api.py portal_bot/tests/test_app_first_service.py tests/test_api_auth_and_tickets.py tests/test_subscription_preview_api.py -v -o faulthandler_timeout=60
# PASS: 154 tests and 8 subtests
```

The updated harness, long-answer and helpbot lifecycle tests passed within the
110 passing tests of the focused run whose only failure was the consumed-stream
provider test fixture; that fixture was then fixed and all 24 provider tests passed.

On Brain, staged committed candidate without service changes:

```sh
/root/portal_bot/venv/bin/python /tmp/pokrov-support-ds41-high/smoke.py --mode full --output committed-predeploy
/root/portal_bot/venv/bin/python /tmp/pokrov-support-ds41-high/deploy.py --candidate 0d66797d57bbdd0a90b143425fbddb75f9c4def1
```
