# Internal support Vision checks — 2026-09-09

Implementation: `ace418fd3c4605b0321bf6e6e8c13335c298ca39`, based on
`d3eba8945e74eca025e2a8589be110d070fb562d`. Four support runtime modules,
three existing test modules and three canonical owner documents changed.
No schema, dependency, environment, worker, OIDC or client changes.
The owner explicitly approved external processing of support attachments.

## Current-origin checks

- `python -B -m pytest -p no:cacheprovider tests/test_support_case_context.py tests/test_support_agent_harness.py tests/test_support_agent_provider.py tests/test_support_agent_service.py -q`: PASS, 99 tests in 3.22 seconds on the final implementation. [Output](focused-final.txt).
- `python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`: PASS, 33 tests in 0.57 seconds after final documentation edits.
- `python -B scripts/agent_context_packet_audit.py --platform-context-root .`: PASS platform-context.
- `git diff --check` and staged diff check: PASS.
- Required backend router suite plus support/docs regression: running at this checkpoint. Command: `python -B -m pytest -p no:cacheprovider portal_bot/tests/test_app_first_api.py portal_bot/tests/test_app_first_service.py tests/test_api_auth_and_tickets.py tests/test_subscription_preview_api.py tests/test_helpbot_lifecycle.py tests/test_support_case_context.py tests/test_support_agent_harness.py tests/test_support_agent_safety.py tests/test_support_agent_service.py tests/test_support_agent_sessions.py tests/test_support_agent_provider.py tests/test_support_ai_service.py tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`. This run started before the scoped Python 3.10 timeout correction and receipt-claim guard. Those final changes have the focused 99-test pass above; the long-running process must not be presented as an exact-commit full pass. [Output destination](pytest.txt).

The long run subsequently completed: **PASS, 424 tests and 192 subtests in
904.41 seconds (15:04), exit code 0**. The source-timing limitation above remains;
the final scoped changes have their separate 99-test pass.

## Brain-origin preflight

Only four candidate support files were copied into
`/tmp/pokrov-support-internal-vision-20260909/portal_bot`; runtime and service
configuration were untouched. The probe imports these candidate files plus
unchanged live modules, uses the actual helpbot process environment, and replaces
DB/invoice access with in-process synthetic fixtures. No customer message,
database query or payment-provider operation is performed.

Command: `ssh -o BatchMode=yes -o ConnectTimeout=12 pokrov-brain /root/portal_bot/venv/bin/python /tmp/pokrov-support-internal-vision-20260909/internal-vision-smoke.py /tmp/pokrov-support-internal-vision-20260909/portal_bot`.

Final preflight: PASS, three model requests in 7.486 seconds. The first two read
a synthetic PNG and PDF; the third generated the support reply. Amount 99,
TIMEOUT and the image's red circle were recognized. Synthetic credentials and
email were absent from the admitted attachment projection and final reply.
This proves actual image input, not just text OCR. [Sanitized fixture result](brain-preflight.json).

Earlier probes exposed two setup/compatibility failures: the scratch path
initially lacked the shared policy directory, and Brain's Python 3.10 does not
support `asyncio.timeout`. The scratch layout was corrected and the code uses
`asyncio.wait_for`. A subsequent model reply claimed that a receipt confirms
payment; the final code now rejects that concrete unsupported source claim.

Model quality is not claimed perfect. The retained final preflight reply also
asserted that the pictured timeout is unrelated to payment; the fixture does
not establish that causal claim. The internal projection remains untrusted,
and the narrow receipt guard is not a general proof of semantic correctness.
The model cannot perform account/payment mutations.

An additional native rendering fixture had four PDF pages; exactly three were
rendered. On Brain this took 176 ms wall time, 169 ms renderer CPU and 49,640 KiB
peak renderer RSS. OCR and provider calls: zero. These are measurements of a
simple synthetic document, not capacity guarantees for arbitrary PDFs.
[Rendering result](pdf-render-smoke.json).

## Deployment and remaining evidence

Signed integration [PR #246](https://github.com/Kiwunaka/portal/pull/246) uses
`c57d51a915d6434fdb4955bafff231b644a941fa`. GitHub reports its signature verified.
Its tree `8b4f13f0d108e252a917091a282cb4be340e9b51` exactly matches the implementation
commit's tree, checked using `git rev-parse 'HEAD^{tree}'` and
`gh api repos/Kiwunaka/portal/git/commits/c57d51a915d6434fdb4955bafff231b644a941fa`.
At this checkpoint the cross-repository contract passed, release-base isolation
was SKIPPED, and repo-guardrails was still running.

PR #246 subsequently merged at 06:30:23 UTC as
`876e78da2ee5426a11d5aa74239fcff5efc9fa5d`. Both required checks completed
SUCCESS; release-base isolation remained SKIPPED. Server promotion is still
separate from this successful source merge.

Both ordinary master push workflows also completed SUCCESS:
[Guardrails 34319368085](https://github.com/Kiwunaka/portal/actions/runs/34319368085)
and [Release v2 Contract 34319368099](https://github.com/Kiwunaka/portal/actions/runs/34319368099).
The merge commit has the same tree and a verified GitHub signature.

- Production deployment: PASS, `876e78da2ee5426a11d5aa74239fcff5efc9fa5d`.
- Actual post-deploy support readback: PASS, retained below.
- End-user Telegram upload/delivery: MANUAL_OWNER_TEST.
- RU-origin, release 1.2.0 readiness and Cheburcheck integration: NOT_REQUESTED.
- Historical preflight/evidence from the previous OCR implementation is retained separately and is not proof of this candidate.

## Actual deployed runtime

The coordinated deployment receipt
`E:/r12-internal-vision-integration-20260909/build-identity-updated.json` reports
all 204 deployed payload hashes matching, public build identity `876e78d`,
and the retained backup
`/root/portal_bot.deploy-backups/20260909T064101Z-28716`. Common environment values
were preserved except the two public build identity fields. API/helpbot were
restarted; the worker and other bots retained their processes.

An independent readback at 06:44:32 UTC passed for all four support files,
actual process model/enabled flags, fresh API/helpbot starts, zero restart
counters and public `/api/health`. The deployed payload uses CRLF. The first
raw-file-versus-Git-blob assertion therefore failed; investigation confirmed
that raw deployed hashes exactly match the clean deployment checkout, while
LF-normalized hashes exactly match the signed Git source. Both hashes are
retained rather than representing a normalized match as a raw Git-blob match.
The observed API PID was 16595, helpbot PID 15891. [Readback](runtime-readback.json).
The deployment coordinator did not initiate the later API restart that produced
PID 16595. Its follow-up check again matched all 204 payload hashes with zero
differences and found the API active with zero restarts. Attribution of that
separate restart remains under investigation in the coordinating operations
task; the support source and model checks above still passed.

Command: `ssh -o BatchMode=yes -o ConnectTimeout=12 pokrov-brain /root/portal_bot/venv/bin/python /tmp/pokrov-support-internal-vision-20260909/internal-vision-smoke.py`.
The single post-deploy synthetic smoke imported actual `/root/portal_bot` code
and the current helpbot model configuration. **PASS, three provider calls in
10.049 seconds**. PNG visual details and error text, PDF amount, redaction and
final synthesis all passed. The reply distinguished a receipt from authoritative
payment confirmation and escalated the unresolved access discrepancy.
DB/invoice data were fixtures, not customer reads; no customer message was sent.
[Actual-root synthetic result](brain-postdeploy.json).
