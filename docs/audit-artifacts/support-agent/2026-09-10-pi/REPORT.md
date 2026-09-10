# Support pi investigation — 2026-09-10

Candidate: `ee400086db05b8d41a9278296ff6e69f4595300b`, based on platform
`d9d0ac05dfe9e79dcdb2a9dcc3c718b9a773b88c`. Runtime hashes are in `manifest.json`.

## Change

DeepSeek 4.1 high now uses actual pi-agent-core 0.85.1 for ticket/helpbot case
investigations. Ten closed tools cover owner-bound account/payment/history,
diagnostics, attachment Vision, stored node measurements, approved knowledge,
internal notes, operator queueing and proposed operator reviews. Python owns
identity/revision checks and the atomic commit of staged notes/handoff with the
validated public reply. There are no account/payment/refund/access mutation or
arbitrary filesystem/shell tools. Legacy profiles, standalone app assistant and
recovery text-only handling keep their prior route.

A discovered pre-existing 2,000-character ticket storage/detail truncation is
fixed for public assistant replies: up to 12,000 model characters plus the code
handoff footer are retained and returned. Internal/user limits remain unchanged.
The standard deploy payload now includes pi's runner and package/lock files,
and refuses to promote a dependency lock without a matching prepared install.

## Local verification

PASS:

- `python -B -m pytest -p no:cacheprovider tests/test_support_pi_agent.py tests/test_support_case_context.py tests/test_support_agent_harness.py tests/test_support_agent_service.py tests/test_remote_deploy_brain_portal_code.py tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q` — 125 passed. The subsequent pi usage aggregation change passed its two focused harness cases; the added owned/foreign node assertion passed all three tool tests.
- `python -B -m pytest -p no:cacheprovider tests/test_support_agent_provider.py tests/test_support_agent_policy.py tests/test_support_agent_safety.py tests/test_helpbot_lifecycle.py tests/test_remote_deploy_brain_portal_code.py -q` — 136 passed.
- `python -B -m pytest -p no:cacheprovider portal_bot/tests/test_app_first_api.py portal_bot/tests/test_app_first_service.py tests/test_subscription_preview_api.py -q` — 58 passed.
- The API regression run (`tests/test_api_auth_and_tickets.py` plus focused support selections) completed 111 passed and 8 subtests with one failure in the newly added fixture: the API reused the first still-open ticket. The fixture now closes that ticket before testing the stale case. `python -B -m pytest -p no:cacheprovider tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_pi_notes_and_handoff_commit_with_reply_and_reject_stale_turn tests/test_support_pi_agent.py tests/test_support_agent_harness.py -q` — 54 passed, including atomic handoff, private-note exclusion, long public replies and stale-result rejection.
- `python -B -m pytest -p no:cacheprovider tests/test_tickets_repo.py tests/test_support_work_service.py -q` — 17 passed.
- `python -B -m pytest -p no:cacheprovider tests/test_release_gate_check.py tests/test_release_orchestrator.py tests/test_check_script_manifest.py -q` — 44 passed and 21 subtests.
- `python -B scripts/agent_context_packet_audit.py --platform-context-root .` — PASS.
- `node --check portal_bot/support_pi/runner.mjs`, Python compilation and `git diff --check` — PASS.

## Brain-origin synthetic evaluation

`smoke.py` uses the real service, case tools, pi loop, DeepSeek and attachment
Vision, with a separate temporary SQLite database and generated PNG/PDF files.
No customer rows or messages are used or changed. The fixtures cover a paid
inactive account, active access plus two attachments, and an account with no
orders. Actual tool names/result keys and sanitized replies are retained.

The initial two-step pi/DeepSeek compatibility check passed (three model turns).
`predeploy.jsonl` retains the first successful payment case; that run then stopped
on a missing `original_name` in the attachment fixture, which was corrected.
`predeploy-fixed-fixture.jsonl` retains an early file-case fallback whose original
fixed error detail was unavailable. `predeploy-diagnostics.jsonl` retained a
later successful file answer that quoted and rejected a hostile file instruction;
its substring mutation screen failed, although it did not claim to execute a
refund. The prompt now requires silently ignoring such instructions. The final
model turn is reserved for a reply after tool results. Failed model runs discard
drafts and retain a bounded factual fallback when payment/access reads exist.

`predeploy-final-code.jsonl` and `candidate-predeploy.jsonl` passed all three
scenarios; the latter took about 11–22 seconds. These precede only final runner
indentation and the immutable source hash check in the smoke driver.
`committed-predeploy.jsonl` is the authoritative predeploy run for the exact
candidate hashes and pinned dependency lock.

## Deployment state

NOT_DEPLOYED at this checkpoint. Guarded `deploy.py --candidate <candidate>`
preflight returned PLAN_PASS, including baseline/stage digests, Node/package
versions, unchanged support environment, both running services and HTTPS health.
`prerequisites.json` records the official Node archive SHA-256 and isolated npm
lock install. Node/dependencies were prepared additively without changing the
running services. The apply path backs up scoped files/environment, retains new
file provenance, switches only the two dependency/runtime links, restarts only
API/helpbot, and restores the previous state on failure.

Independent review: NOT_REQUESTED. Real customer conversations and RU-origin
delivery: NOT_REQUESTED. Stored node snapshots are not live connectivity proof.
These checks do not establish payment reconciliation, automatic access repair,
refund execution, or any release 1.2.0 readiness claim.
