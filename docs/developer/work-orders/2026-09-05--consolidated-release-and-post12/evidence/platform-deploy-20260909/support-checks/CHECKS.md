# Support case checks, 2026-09-09

Implementation source: `327736186562fb61b447510c39bc651a06747ca4`, based on
`03920525bfc3993591a39d21e35bbe2e7e1d663d`. This is a support change, not release
1.2.0 acceptance. No schema/model/requirements changes. Native OCR packages
were installed on Brain; there is no new Python dependency.

## Current-origin checks

- `python -B -m pytest -p no:cacheprovider tests/test_support_case_context.py tests/test_support_agent_harness.py tests/test_support_agent_safety.py tests/test_support_agent_service.py tests/test_support_agent_sessions.py tests/test_support_agent_provider.py tests/test_support_ai_service.py tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`: PASS, 257 tests and 184 subtests. Retained output: [support-and-docs-pytest.txt](support-and-docs-pytest.txt).
- Backend router command: `python -B -m pytest -p no:cacheprovider portal_bot/tests/test_app_first_api.py portal_bot/tests/test_app_first_service.py tests/test_api_auth_and_tickets.py tests/test_subscription_preview_api.py -q`. Initial run: **FAIL**, 152 passed, 2 failed, 8 subtests passed, 758.36 seconds. Both failures were the two AI endpoint test doubles rejecting the newly added `case_context_enabled` keyword; the run had loaded the test module before its signatures were updated. This initial run is not labelled PASS.
- After updating those two doubles: `python -B -m pytest -p no:cacheprovider tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_ticket_create_appends_ai_hint_when_enabled tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_ticket_followup_appends_ai_hint_for_user_messages_only -q`: PASS, 2 tests, 11.85 seconds. [Output](api-two-recheck.txt).
- Final integration check on committed source: `python -B -m pytest -p no:cacheprovider tests/test_helpbot_lifecycle.py tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_ticket_create_appends_ai_hint_when_enabled tests/test_api_auth_and_tickets.py::ApiAuthAndTicketsTests::test_ticket_followup_appends_ai_hint_for_user_messages_only -q`: PASS, 10 tests, 42.75 seconds. [Output](helpbot-api-final.txt).
- `python -B scripts/agent_context_packet_audit.py --platform-context-root .`: PASS platform-context.
- `git diff --check`: PASS.

## Brain-origin preflight

The support diff was applied to copies of current live files in
`/root/portal_bot.deploy-staging/support-case-20260909-01/portal_bot`; no live code
promotion or restart was performed by the staging script. Staging preserved
the unrelated current API implementation, so this is a support-hunk preflight,
not proof of the complete source revision above. Local OCR smoke passed for a
generated PNG and a scanned PDF with a fixture email removed before model input.
Owner-bound schema queries ran in a read-only transaction. Two stored owned
Lava invoices were read with GET; only their closed statuses were emitted.
No provider or customer payload was saved in this evidence directory.

An additional local-only read of the incident's existing Telegram PDF passed:
the authenticated bot download returned a PDF, the sanitized extraction was
432 characters, and the expected payment amount was recognized. No provider
call or customer message was made; neither original nor extracted customer
content was retained here.

The experimental model produced a substantive Russian escalation on a synthetic
paid-but-no-access case in one request (4.443 seconds in the last preflight).
Earlier preflight exposed a rejected provider-domain string; the prompt and
local summary were corrected and the timeout fallback now has a regression test.
The preflight did not send a message to any customer and does not prove the
end-user Telegram delivery path after deployment.

Installed versions: Tesseract 4.1.1 with Russian/English language data;
Poppler/pdftotext 22.02.0; existing Pillow 12.3.0.

Secret-free model configuration was prepared, without restarting services:
`/root/portal_bot/support-case.env` plus
`/etc/systemd/system/{portal-api,portal-helpbot}.service.d/90-support-case.conf`.
The common `.env` was not rewritten. Runtime activation and exact deployed
source readback remain pending the coordinated backend deploy.

## Account repair and remaining checks

The user-authorized email/Telegram merge used the existing account-foundation
service and recorded an admin audit. Fresh readback confirmed one canonical
account, both active projections, the same preserved expiry, and an unchanged
paid order. Customer identifiers and account/payment payloads are intentionally
absent here. Access synchronization succeeded on six of seven nodes; the Saint
Petersburg node was unhealthy and its SSH banner timed out. This is an open
node issue, not a failed account merge.

- End-user Telegram/file delivery after deployment: MANUAL_OWNER_TEST.
- RU-origin and release readiness: NOT_REQUESTED by this support change.
- Complete backend deploy: owned by the coordinated release task; no deployment
  claim is made by these preflight checks.

## Brain-origin post-deploy readback

The coordinated deployment completed at 04:39:43 UTC. Its retained receipt at
`E:/r12-support-integration-20260909/deployed-runtime-verified.json` confirms all
204 files match source `7d37005e4260995ab44ec3adb14bbffa3d42738b`, tree
`948de00b12c0fdfcca541b6206dbe8de5212c7dc`. Public health passed; all five services
were active with zero restarts. This supersedes the pending deployment status
in the preflight record above; it does not establish release 1.2.0 readiness.

Command: `ssh -o BatchMode=yes -o ConnectTimeout=12 pokrov-brain /root/portal_bot/venv/bin/python /tmp/pokrov-support-case-20260909/live-smoke.py`.
Exit code 0. This imported actual `/root/portal_bot` code and inherited the live
helpbot process environment without forcing model or feature flags. Both API
and helpbot process environments selected the requested model and enabled the
agent. Synthetic PNG/scanned PDF extraction and email redaction passed. A
read-only database transaction confirmed the linked account's active state,
unchanged expiry and paid order; the existing operator-handled case suppressed
AI processing. No customer message or database mutation occurred.

The actual configured provider returned a schema-valid synthetic escalation in
one request, 7.570 seconds. It correctly identified a confirmed payment and
missing access, but also added an unnecessary login-method suggestion despite
the prompt forbidding that advice when ownership is already established. This
is a retained model-quality limitation, not proof of full semantic adherence.
The harness still grants no account/payment mutations. Full image vision is
not implemented: only sanitized OCR text is sent. End-user Telegram delivery
remains MANUAL_OWNER_TEST. [Sanitized readback](live-smoke.json).
