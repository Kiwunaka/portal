# OpenAI Operator Assistants

Last updated: 2026-05-28

## Document Status

This file is the local playbook for experimental, operator-facing OpenAI helpers.
These helpers are not production runtime services and must stay read-only unless
a separate work order explicitly promotes a bounded action path.

## Why This Exists

The useful OpenAI Cookbook patterns for this repository are:

- File Search over canonical POKROV docs for grounded answers.
- Function calling with a narrow read-only operator tool surface.
- Evals and guardrails before any public-copy or release-claim answer is trusted.
- Prompt/cache discipline from the local context-cost harness.

This gives operators a faster way to ask "what does canon say?" without turning
the model into product authority.

## Safety Boundaries

Hard rules:

- do not index `portal_bot/.env`, `VPN NODE SSH KEYS/`, `secrets for merchant/`,
  `ops-local/`, `external/client-fork/app/windows/`, subscription URLs, payment
  payloads, Telegram init data, private emails, or raw user identifiers
- do not let the model deploy, SSH, grant access, revoke access, refund, edit
  payments, mutate users, or publish release claims
- keep `current-origin check`, `brain-origin check`, and `RU-origin check`
  separate in handoffs
- label owner-only checks as `MANUAL_OWNER_TEST`, `OPERATOR_ATTESTED`,
  `SKIPPED_BY_OWNER`, `SKIPPED_BY_OPERATOR`, `NOT_REQUESTED`, or
  `BLOCKED_BY_ACCESS`
- treat model output as a draft; canonical docs and local tests remain authority

## Docs Assistant With File Search

Inventory the allowlisted sources without calling OpenAI:

```powershell
python scripts/pokrov_ai_docs_assistant.py inventory
```

Create a vector store or upload to an existing one:

```powershell
$env:OPENAI_API_KEY="<redacted>"
python scripts/pokrov_ai_docs_assistant.py sync --output .tmp/pokrov-openai-vector-store.json
```

Ask against an existing vector store:

```powershell
$env:POKROV_OPENAI_VECTOR_STORE_ID="vs_..."
python scripts/pokrov_ai_docs_assistant.py ask "What can we honestly claim about RU-origin readiness?"
```

The script sends only the explicit allowlist in `DEFAULT_SOURCE_PATHS`. Extra
files must be repo-relative and pass the same never-touch guard.

## Operator Copilot With Function Calling

List the available tool schemas:

```powershell
python scripts/pokrov_operator_copilot.py list-tools
```

Run one local tool directly:

```powershell
python scripts/pokrov_operator_copilot.py tool pokrov_list_canon
New-Item -ItemType Directory -Force .tmp | Out-Null
"{""timeout_sec"": 120}" | Set-Content -Encoding utf8 .tmp/copilot-tool-args.json
python scripts/pokrov_operator_copilot.py tool pokrov_run_public_copy_guardrails --args-file .tmp/copilot-tool-args.json
```

Ask through OpenAI function calling:

```powershell
$env:OPENAI_API_KEY="<redacted>"
python scripts/pokrov_operator_copilot.py ask "Check the public-copy guardrails and summarize release-claim risk."
```

Current tools are intentionally read-only:

- `pokrov_list_canon`
- `pokrov_read_canonical_doc_excerpt`
- `pokrov_run_public_copy_guardrails`
- `pokrov_check_payment_email_readiness`
- `pokrov_build_origin_status_handoff`

The model only chooses tool calls. The Python process validates and executes the
registered handlers.

## Verification

Focused checks:

```powershell
python -m pytest tests/test_pokrov_ai_docs_assistant.py tests/test_pokrov_operator_copilot.py tests/test_agent_context_packet_audit.py tests/test_public_copy_guardrails.py
```

Before scaling repeated prompt packets, run:

```powershell
python scripts/agent_context_packet_audit.py <packet.md>
```

## Promotion Rule

Before any helper becomes a production service, create a work order that defines:

- exact tool list and schemas
- read/write classification for each tool
- auth boundary and operator role
- audit logging without raw prompts or secrets
- eval dataset and graders for canon correctness
- rollback and kill-switch behavior
