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

Local checks: support suite initially 235 passed plus 184 subtests; focused updated support checks 158 passed plus 184 subtests, provider checks 24 passed. Documentation/evaluation checks 58 passed; platform-context audit PASS. Required backend regression is in progress. One early combined run was interrupted to separate slow backend tests from the fast support/documentation suites; it is not counted as a pass.

## Deployment

NOT_YET_DEPLOYED. `deploy.py` requires exact candidate and baseline hashes, validates staged Python/JSON, preserves `/root/portal_bot/.env`, backs up only the scoped files plus the support override, restarts only `portal-api` and `portal-helpbot`, and verifies delayed active/NRestarts=0 plus public API health. Failure restores the previous files and override.
