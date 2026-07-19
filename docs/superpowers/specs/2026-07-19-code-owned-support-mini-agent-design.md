# POKROV Code-Owned Support Mini-Agent

- Date: 2026-07-19
- Status: owner-approved architecture; independent written-spec review pending
- Platform branch: `codex/support-agent-harness`
- Platform promotion line: `master`
- Active client repository: `C:/Users/kiwun/Documents/ai/POKROV-app`, promotion line `main`

## 1. Decision and Outcome

The first support-agent version uses a code-owned retrieval harness and exactly
one xCody/MiniMax request. Application code selects allowlisted support topics,
owns session memory, sources, suggested actions, escalation, budgets, and all
safety decisions. MiniMax receives only the redacted question, bounded
redacted session context, and already selected public-support topics. It
returns only an answer status and user-facing reply.

This design removes the model-visible tool loop from the previously approved
safe-harness design. It is still an agent harness rather than a raw API call:
retrieval, context assembly, memory, policy enforcement, fallback, and result
state form a bounded deterministic runtime around the model. The model has no
authority and no way to request additional access.

The intended result is a useful Russian support assistant that:

- remembers the current short support conversation;
- answers from the deployed public-support bundle;
- consumes one bounded model call per eligible message;
- benefits from a stable prompt prefix when the provider cache supports it;
- never reads accounts, databases, attachments, keys, diagnostics, commands,
  arbitrary files, or the network;
- returns a grounded deterministic answer or transfers to a human when the
  model or evidence is insufficient.

## 2. Relationship to the 2026-07-15 Design

This document supersedes the following parts of
`2026-07-15-safe-support-agent-harness-design.md`:

- the `search_support_docs` model-visible tool schema;
- the two-request tool/retry loop;
- model-generated source topic IDs;
- model-generated session state;
- model control over suggested actions or escalation;
- request budgets that permit more than one provider request.

The following previously approved boundaries remain authoritative unless this
document narrows them:

- the public-support allowlist and knowledge validation;
- the typed AGENTS-like runtime policy;
- input redaction and output safety scanning;
- authenticated owner/surface session isolation;
- process-local bounded RAM memory;
- app, ticket, and helpbot API boundaries;
- xCody OpenAI-compatible Chat Completions with `minimax-m3` and
  `reasoning_effort: medium`;
- deterministic fallback and human escalation;
- no deploy or production enablement without a separate owner instruction.

During implementation, this document becomes the authority for the runtime
architecture. The older design remains historical evidence for the safety
boundary and abandoned tool-loop experiment, not an alternative runtime mode.

## 3. Locked Owner Decisions

| Decision | Locked value |
|---|---|
| Architecture | Code-owned retrieval and memory with one model synthesis call |
| Provider | xCody OpenAI-compatible Chat Completions |
| Model | `minimax-m3` |
| Reasoning | `reasoning_effort: medium` |
| Provider calls | At most one per eligible user message; no retry |
| Model-visible tools | None |
| Runtime | Existing Python process; no Docker, sidecar, Pi, Oh My Pi, MCP, or agent framework |
| Knowledge | Loaded, validated, sanitized, allowlisted public-support bundle only |
| Memory | Owner- and surface-scoped volatile RAM, 60-minute idle TTL |
| Model output | Closed object containing only schema version, status, and reply |
| Application-owned output | Sources, session state, actions, escalation, public source label |
| Forbidden access | DB, account, payment state, attachments, raw diagnostics, keys, configs, shell, arbitrary files, external tools |
| Failure behavior | Grounded local KB answer when safe; otherwise immediate human transfer |
| Production mutation | Out of scope |

`AGENTS.md` in the repository is never sent to the model. The model receives a
small typed runtime policy derived from `support-agent-policy.json`. Session
memory is the bounded data structure described below, not a writable agent
memory file.

## 4. Scope

### In scope

- deterministic local retrieval over `shared/support-ai-knowledge.json`;
- code-owned topic selection and provenance;
- stable-prefix context construction;
- one structured MiniMax synthesis request;
- bounded session continuity for app, ticket, and helpbot surfaces;
- safe deterministic answer rendering when the provider fails;
- strict input, provider-output, and final-output validation;
- owner-scoped rate limiting, concurrency control, deadlines, and telemetry;
- focused deterministic, semantic, adversarial, session, cache, and load tests;
- canonical platform and active-client documentation updates when behavior is
  implemented.

### Out of scope

- model tool calling of any kind;
- reading user accounts, entitlements, payment records, keys, nodes, or DB rows;
- reading attachments, raw ticket history, raw diagnostics, configs, or
  arbitrary server/repository files;
- shell commands, network tools, external search, or side effects;
- durable cross-process memory or a user profile;
- embeddings or a vector database;
- model-generated sources, state transitions, actions, or security decisions;
- automatic ticket creation or action execution;
- streaming;
- a second provider call, including retries, repair prompts, summaries, or
  shadow traffic;
- production deployment or flag changes.

## 5. Runtime Architecture

```text
authenticated app / ticket / helpbot request
  -> owner and surface session resolver
  -> input classifier, redactor, and length boundary
  -> bounded RAM session lookup
  -> deterministic allowlisted KB retrieval
  -> code-owned topic selection and confidence decision
       -> no safe evidence: fixed human transfer, zero provider calls
       -> safe evidence:
            stable policy/cache prefix
            + selected topic bodies
            + code-owned session state
            + recent redacted messages
            + current redacted question
            -> one xCody MiniMax request, no tools
            -> minimal JSON parser and reply safety validator
                 -> valid answer: code-owned result assembly
                 -> model escalation/failure: grounded local renderer
                      -> safe grounded reply, or fixed human transfer
  -> code-owned source IDs, state, actions, escalation, and redacted trace
```

The provider is a bounded language renderer over evidence already chosen by
the application. It cannot broaden retrieval scope, invoke tools, name its own
sources, mutate memory, suppress escalation, or claim that an action ran.

## 6. Components and Contracts

### 6.1 Policy and knowledge snapshots

`SupportAgentPolicyStore` and `SupportKnowledgeStore` retain the validation and
fail-closed behavior from the 2026-07-15 design. They load once into immutable
snapshots and expose only typed values. The positive knowledge path is the
deployed public-support bundle; request data can never provide a path, URL,
topic body, or policy fragment.

The knowledge snapshot remains bounded to 100 topics, 20 keywords per topic,
1,200 characters per body, 65,536 serialized bytes, and the exact
`public_support` scope. Model-visible and locally rendered text is rejected at
load time if it contains a private connection scheme, credential-like value,
IP address, disallowed host, unsafe URL, control character, or invalid shape.

An immutable snapshot hash identifies the exact policy/KB candidate in traces
and evaluation reports. Failed reload retains no partial snapshot and results
in deterministic escalation without a provider call.

### 6.2 Deterministic retrieval and topic selection

The retriever receives only:

- the current redacted question;
- the existing session issue topic ID, when present and still allowlisted;
- bounded prior redacted user messages when the current message is a short
  follow-up such as “не помогло”.

It returns at most three complete allowlisted topics in deterministic score
order. Normalization, scoring, tie-breaking, session-topic pinning, and bounds
are code-owned and versioned by tests. A query cannot select a topic by
supplying a file path, URL, raw topic object, or unknown ID.

Retrieval produces one of three code-owned dispositions:

| Disposition | Meaning | Runtime behavior |
|---|---|---|
| `confident` | One primary topic is selected by a closed high-precision intent rule, or a previously established confident issue has a clear follow-up | Send up to three selected topics to MiniMax; grounded local rendering is permitted on provider failure |
| `candidate` | Relevant topics exist but the primary topic is ambiguous | Send up to three topics to MiniMax; local rendering on failure is forbidden, so failure transfers to a human |
| `none` | No safe relevant topic exists | Make no provider call and transfer to a human |

The generic retrieval score and score margin never grant `confident` status by
themselves in v1. A pre-spec diagnostic over the 48 normal fixtures showed that
even high-scoring or exact-keyword primary hits can be semantically ambiguous.
`confident` therefore comes only from a separate closed mapping of normalized,
high-precision phrase groups to exactly one topic, or from a previously
confident issue plus a locally recognized follow-up. Every rule must have zero
known false-positive primary topics in the fixture before it can be enabled.
All other non-zero retrieval is `candidate`.

The rules are constants in code, not model output or environment text. The
implementation may prefer `candidate` over a wrong confident match. Changes to
tokenization, weights, phrase rules, or pinning increment `retriever_version`
and rerun the semantic fixture; they are not runtime-tunable in v1.

The ordered selected topic IDs are the only possible provenance for the run.
The model never sees or returns a field that can alter them. Public source IDs
come from the subset actually used to assemble the final answer:

- a valid model answer uses the selected IDs recorded for its context;
- a local grounded answer uses only its primary topic ID;
- a human-transfer fallback uses no topic ID.

### 6.3 Session memory

The existing owner/surface resolver remains the authorization boundary. It
derives an internal session key only after normal authentication or sender/
ticket ownership validation. Raw owner, ticket, Telegram, or account IDs never
enter the harness context or trace.

Each process keeps at most 256 sessions with a 60-minute idle TTL and LRU
eviction. A session retains at most six redacted messages plus this closed
code-owned state:

```json
{
  "issue_topic_id": "connected_no_internet",
  "attempted_steps": ["reconnect"],
  "last_outcome": "unchanged",
  "escalation_requested": false
}
```

State changes are deterministic:

- `issue_topic_id` becomes the confident primary topic; a candidate result
  cannot replace an established issue, and an unknown/removed ID is cleared;
- `attempted_steps` can only append a closed safe step code recognized from an
  explicit user statement or an action previously suggested by application
  code; model prose cannot append a step;
- `last_outcome` changes only when a bounded local classifier recognizes an
  explicit user report (`resolved`, `unchanged`, `improved`, `worse`, or
  `blocked`); otherwise it remains `not_reported` or its prior value;
- `escalation_requested` becomes true only from an explicit human request or a
  code-owned escalation branch;
- hard-rejected or local-escalation input is never appended to message history.

Closing the app assistant sheet ends client continuity. Process restart,
eviction, or routing to another process intentionally loses memory. There is no
cross-process synchronization in v1.

### 6.4 Context builder and cache prefix

The provider request has deterministic ordering.

Stable prefix:

1. typed public-support role and forbidden-access boundary;
2. instruction hierarchy and prompt-injection rule;
3. answer style in Russian;
4. minimal output JSON contract;
5. compact topic index in topic-ID order;
6. policy, prompt, KB, and retriever versions.

Volatile suffix:

1. selected topic bodies in retrieval order;
2. code-owned session state;
3. recent redacted messages in chronological order;
4. current redacted user question.

All user/history content is placed in explicit untrusted-data delimiters. Text
inside those delimiters cannot change policy, request tools, add sources, or
alter the output schema.

Hard bounds:

- stable prefix: 18,000 serialized characters maximum;
- selected bodies: three topics and 3,600 characters maximum;
- session state and history: 6,000 characters maximum;
- current redacted question: 1,200 characters maximum;
- complete serialized provider request: 30,000 characters maximum.

The builder preserves the stable prefix and current question, admits selected
topics in score order, and admits recent history newest-first until the full
request fits. It never truncates a topic body mid-object. If the primary topic
or current question cannot fit, it makes no provider call and transfers to a
human.

No request ID, timestamp, owner/session identifier, diagnostic value, or
dynamic tool schema appears in the stable prefix. Provider-reported cached
tokens are recorded when present. Missing cache telemetry is `not_reported`,
not a claimed hit.

### 6.5 xCody adapter

The adapter makes exactly one OpenAI-compatible request:

```text
POST {SUPPORT_AI_API_BASE_URL}/chat/completions
Authorization: Bearer <runtime secret>
Content-Type: application/json
```

Required payload behavior:

- `model: "minimax-m3"` by default;
- `messages`: deterministic context described above;
- `reasoning_effort: "medium"` using the snake-case wire field;
- `temperature: 0.2`;
- `max_tokens: 1200`;
- `n: 1`;
- `response_format: {"type":"json_object"}`;
- no `tools`, `tool_choice`, `parallel_tool_calls`, OpenRouter routing object,
  Anthropic Messages fields, undocumented cache key, or provider-specific
  data-collection object.

The request uses the xCody `/v1/chat/completions` dialect, not Anthropic
`/v1/messages`. Earlier live evidence showed the 400-class incompatibility
when structured response mode and model-visible tools were combined across
mixed upstream shards. This design removes the tool fields completely and
retains JSON mode only on the no-tools request. The exact payload must pass the
short live gate with zero HTTP 400 responses before broader testing.

Default provider timeout is 20 seconds with a hard total run deadline of 25
seconds. There is no retry for timeout, transport failure, 429, 5xx, 400,
invalid JSON, empty `message.content`, or unsafe output. A second request would
double worst-case latency and resource use and is forbidden.

The adapter normalizes only status, one choice, content, finish reason, usage,
and error class. It never logs or persists the API key, request body, response
body, hidden reasoning, user text, or assistant reply.

### 6.6 Minimal model output

The only accepted decoded object is:

```json
{
  "schema_version": "1",
  "status": "answer",
  "reply": "Короткий безопасный ответ по выбранным материалам."
}
```

Validation rules:

- the root is a JSON object with exactly these three keys;
- `schema_version` is exactly `"1"`;
- `status` is exactly `answer` or `escalate`;
- `reply` is a non-empty string of at most 1,200 characters;
- an accepted answer is Russian-facing and follows the compact support format;
- no trailing text, tool call, source ID, action, state object, command,
  markdown link, raw URL, secret-like span, private host, config, unsupported
  guarantee, or forbidden product claim is permitted;
- `finish_reason` must be `stop`, and exactly one choice must be present.

If `status` is `escalate`, application code discards the model reply and
transfers to a human. It does not override an explicit uncertainty signal with
a local answer. The model cannot supply the final transfer text or suppress
`shouldEscalate`.

### 6.7 Code-owned result assembly

Application code produces the public result from validated local facts:

```json
{
  "reply": "...",
  "assistantSessionId": "opaque_session_id",
  "suggestedActions": ["reconnect", "write_to_support"],
  "shouldEscalate": false,
  "source": "support_agent"
}
```

Rules:

- `source_topic_ids` used internally are copied from selected retrieval hits,
  never parsed from model prose;
- suggested actions come from a closed application mapping keyed by primary
  topic and safe state;
- every action remains a suggestion and requires explicit user confirmation in
  the existing UI; the harness executes nothing;
- `shouldEscalate` is true for explicit human requests, account/payment-
  specific questions, sensitive input, no evidence, candidate-only provider
  failure, model escalation, invalid/unsafe output, deadline/provider failure
  without a confident topic, or repeated unsuccessful troubleshooting;
- the public `source` label is selected by the executed code path, not model
  content.

## 7. Deterministic Fallback

Fallback is part of the agent, not a generic “something went wrong” response.
It has two outcomes.

### Grounded local answer

Allowed only when retrieval disposition is `confident`. The renderer takes the
primary allowlisted topic body, strips or replaces raw public URLs and other
nonessential link text, adds only fixed code-owned framing, caps the result at
1,200 characters, and runs the same final output safety scanner. It does not
combine arbitrary topics or invent steps. The result uses the primary topic ID
and may suggest only actions mapped to that topic.

If the sanitized body is empty, malformed, unsafe, or cannot satisfy the
fixture for that topic, local rendering is forbidden.

### Human transfer

Every other failure returns a fixed Russian message explaining that there is
not enough safe information and a human will help. It contains no model text,
user text, provider error detail, or guessed troubleshooting. It sets
`shouldEscalate=true`, includes `write_to_support`, and records a code-owned
reason enum.

This truth table is exhaustive:

| Condition | Provider calls | Public outcome |
|---|---:|---|
| Input hard reject or local-only escalation | 0 | Human transfer |
| No retrieved topic | 0 | Human transfer |
| Valid model answer | 1 | Validated model reply with code-owned provenance |
| Model/provider failure + confident topic | 1 | Grounded local answer if final scanner passes; otherwise human transfer |
| Model/provider failure + candidate topic | 1 | Human transfer |
| Model requests escalation | 1 | Human transfer |
| Harness disabled or unconfigured | 0 | Existing deterministic local fallback with escalation |

## 8. Safety Boundary

The v1 boundary is unchanged and explicit: the agent reads only allowlisted
public-support topics and the cleaned current-session conversation. It has no
database handle, account client, attachment loader, raw diagnostics, secret
store access beyond the adapter's opaque provider credential, command runner,
general file API, network tool, or tool registry.

Input handling preserves the four dispositions from the prior design:

- `hard_reject` for raw connection material and high-risk credentials;
- `local_escalate` for account/payment-specific data or an explicit human
  request;
- `redact_continue` for safely removable PII/URL/token-like spans when enough
  ordinary support text remains;
- `continue` for plain support text, including prompt-injection prose.

Only category/count and disposition enter telemetry. `safeDiagnostics` remain
outside model context and session memory. The endpoint may validate and count
the existing four safe key names, but values are ignored by this harness.

The final reply passes the output safety scanner regardless of whether it came
from MiniMax or the local renderer. Any scanner rejection becomes a fixed
human transfer; rejected text is not logged or added to memory.

## 9. Resource, Rate, and Configuration Limits

Hard v1 ceilings:

| Resource | Ceiling |
|---|---:|
| Provider requests per eligible message | 1 |
| Model-visible tools | 0 |
| Model concurrency per process | 2 |
| Concurrency wait | 250 ms |
| In-flight runs per internal session | 1 |
| Owner-scope interactive requests | 6 per rolling minute |
| Owner rate buckets per process | 1,024 |
| Sessions per process | 256 |
| Session idle TTL | 3,600 s |
| Retained messages per session | 6 |
| Provider request | 30,000 serialized characters |
| Model output | 1,200 tokens / 1,200 reply characters |
| Provider timeout / total deadline | 20 s / 25 s |

Configuration remains secret-free in the repository:

```text
SUPPORT_AI_ENABLED=false
SUPPORT_AI_AGENT_ENABLED=false
SUPPORT_AI_API_BASE_URL=https://api.xcody.dev/v1
SUPPORT_AI_MODEL=minimax-m3
SUPPORT_AI_REASONING_EFFORT=medium
SUPPORT_AI_TIMEOUT_SECONDS=20
SUPPORT_AI_RUN_DEADLINE_SECONDS=25
SUPPORT_AI_MAX_CONCURRENCY=2
SUPPORT_AI_CONCURRENCY_WAIT_MS=250
SUPPORT_AI_SESSION_TTL_SECONDS=3600
SUPPORT_AI_MAX_SESSIONS=256
SUPPORT_AI_OWNER_RATE_LIMIT_PER_MINUTE=6
SUPPORT_AI_MAX_RATE_BUCKETS=1024
SUPPORT_AI_PRE_RETRIEVAL_LIMIT=3
SUPPORT_AI_MAX_INPUT_CHARS=30000
SUPPORT_AI_MAX_OUTPUT_TOKENS=1200
```

Old tool-loop settings for two provider requests and one tool call are removed
from canonical configuration and have no runtime effect. The safe rollback is
`SUPPORT_AI_AGENT_ENABLED=false`, which selects the existing legacy helper; a
second hidden agent implementation is not retained.

Route selection remains exclusive:

| `SUPPORT_AI_ENABLED` | `SUPPORT_AI_AGENT_ENABLED` | Behavior |
|---|---|---|
| `false` | either | Zero provider calls; deterministic fallback |
| `true` | `false` | Existing legacy one-call support helper |
| `true` | `true` | Code-owned mini-agent; zero or one provider call |

There is no shadow mode and no simultaneous legacy/agent call.

## 10. Observability

One redacted trace records:

```text
run_id
surface
session_id_hash
provider/model/reasoning effort
policy/prompt/KB/retriever versions and hashes
retrieval disposition and selected topic IDs
provider request count and normalized status/error class
prompt/completion/cached token counts when reported
queue/provider/total latency
input/output redaction category counts
final path and escalation reason code
```

It never records user text, reply text, topic bodies, session IDs, owner IDs,
diagnostic values, provider payloads, hidden reasoning, credentials, or raw
errors containing upstream data.

## 11. Verification Strategy

Tests run in risk order. Expensive live and RPM tests are forbidden until the
small semantic gate passes. This avoids spending requests on a payload or
architecture that is already known to be wrong.

### 11.1 Deterministic implementation gate

Focused tests must prove:

1. input redaction and all four dispositions, including split/truncated secret
   patterns, make zero provider calls where required;
2. KB/policy loaders reject scope, path, link, secret, duplicate, size, and
   shape violations before any provider call;
3. retrieval is deterministic, bounded, owner-independent, and covers accepted
   topics in the 48-case fixture, with at least 46/48 accepted topics in the
   top three;
4. high-precision intent rules and established-issue follow-ups are measured
   separately and contain zero known wrong confident primary topics in the
   fixture; raw score/margin never upgrades an ambiguous case from `candidate`;
5. the exact provider payload contains one user synthesis request, JSON mode,
   snake-case medium reasoning, and no tool/Anthropic/OpenRouter-only fields;
6. the model parser accepts only the three-field closed object and rejects
   empty content, extra keys, sources, state, actions, unsafe text, wrong finish
   reason, multiple choices, and malformed JSON;
7. timeout, 400, 429, 5xx, transport error, invalid JSON, empty content, and
   safety rejection produce no retry and follow the exhaustive fallback table;
8. local rendering uses only the confident primary topic and passes the same
   output scanner;
9. source IDs, state, actions, escalation, and public source labels cannot be
   influenced by model fields or prose;
10. sessions enforce owner/surface isolation, TTL, LRU, six-message bound,
    deterministic state transitions, and one in-flight request;
11. prompt hashes stay stable when only user/session/topic bodies change, and
    complete requests stay under the declared caps;
12. disabled, legacy, and agent routes are mutually exclusive;
13. app, ticket, and helpbot retain a safe response when xCody is unavailable.

The focused deterministic suite must be `PASS` before any live claim.

### 11.2 Short live semantic gate

Run exactly 12 synthetic public-support cases covering connection, speed,
import, routing, activation, generic payment guidance, official surfaces, one
follow-up, and provider-output edge cases. Use the exact candidate payload and
aggregate-only logging.

The gate passes only when:

- zero secret/private values enter context, output, memory, or logs;
- zero payload-format HTTP 400 responses occur;
- at least 10/12 provider replies are non-empty, parseable, and safe;
- at least 11/12 final end-user outcomes satisfy their required/forbidden
  semantic concepts, counting a grounded local answer when the provider fails;
- every non-answer safely transfers to a human;
- request count is never above one;
- p50, p95, status classes, finish reasons, usage, and cached-token telemetry
  are reported without raw prompts or replies.

Failure stops the live campaign. Fix the root cause and rerun this 12-case gate
before proceeding.

### 11.3 Full semantic and adversarial gate

Only after the short gate passes, run:

- 48 normal synthetic questions with accepted topic IDs and required/forbidden
  concept groups;
- 12 adversarial cases covering prompt injection, raw connection links,
  credentials, PII, account/payment state, commands, arbitrary files,
  guarantees, and requests to ignore policy;
- 10 three-turn sessions covering prior steps, outcomes, topic continuity,
  escalation, and cross-owner/session isolation;
- repeated stable-prefix probes for provider-reported cache reuse.

Pass criteria:

- all 12 adversarial cases follow the expected local disposition with zero
  leaks and zero unauthorized access;
- at least 43/48 normal cases return a safe answer satisfying topic and concept
  checks; every other case transfers cleanly;
- at least 9/10 session fixtures preserve the expected code-owned issue,
  attempted step, and outcome without cross-session contamination;
- zero model outputs can forge sources, state, actions, or escalation;
- zero HTTP 400 payload-format responses and zero unhandled exceptions;
- a human reviewer finds zero materially unsafe or incorrect troubleshooting
  steps among automated passes;
- cache results are reported as observed values; absence of provider cache
  telemetry is `NOT_OBSERVED`, not failure or a fabricated hit.

### 11.4 RPM and resource characterization

Only after the full semantic gate passes, run isolated synthetic 5, 15, 30,
and 60 RPM ramps with concurrency 1, 2, and 4. Distinct synthetic owner/session
hashes prevent the intentional 6-RPM owner limiter from turning this into a
limiter-only test. Concurrency above the runtime ceiling measures safe busy
fallback, not hidden extra model concurrency.

For each ramp retain only aggregate:

- attempted/completed/provider/fallback counts;
- status/error classes and zero-400 check;
- queue, provider, and end-to-end p50/p95/p99 latency;
- achieved RPM and maximum in-flight provider calls;
- timeout, busy, rate-limit, parse, safety, and local-fallback rates;
- prompt/completion/cached tokens when reported;
- process CPU, RSS, session count, rate-bucket count, and post-run recovery.

Stop a ramp after three consecutive provider failures, any safety leak, any
unhandled exception, process-bound breach, or observed p95 above the 25-second
run deadline. Do not increase concurrency to bypass the hard per-process limit.
The report characterizes sustainable throughput; it does not claim a provider
RPM entitlement that xCody has not documented.

## 12. Evidence Labels and Done Condition

Every report names the exact branch commit, policy/KB/retriever versions,
route, model, reasoning effort, payload hash, test bundle hash, and timestamp.
Local deterministic success is not production proof. Use `PASS`,
`MANUAL_OWNER_TEST`, `BLOCKED_BY_ACCESS`, `NOT_OBSERVED`, or `NOT_REQUESTED`
without upgrading missing evidence.

Implementation is complete only when:

- this design and the implementation plan are owner-approved;
- obsolete model-visible tool-loop behavior is removed from the active agent
  path;
- deterministic tests pass;
- the short live gate passes before the full and RPM suites run;
- retained aggregate evidence meets the declared gates;
- canonical platform and client contracts describe the implemented behavior;
- the final diff is reviewed for secrets, boundaries, unrelated changes, and
  release-claim honesty;
- no deploy, production flag change, or production-readiness claim is made
  without a separate owner instruction and exact runtime evidence.
