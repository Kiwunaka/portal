# POKROV Safe Support Agent Harness

- Date: 2026-07-15
- Status: owner-approved design; independent written-spec review approved
- Platform branch: `codex/support-agent-harness`
- Platform promotion line: `master`
- Active client repository: `C:/Users/kiwun/Documents/ai/POKROV-app`, promotion line `main`

## 1. Goal

Replace the current one-call support helper with the smallest useful read-only
agent harness. The agent must keep short-lived conversation context, retrieve
only approved public-support knowledge, reuse a stable prompt prefix for cache
hits, and escalate instead of guessing. It runs inside the existing Python API
process and must remain viable on the current low-resource server.

The useful outcome is not broad autonomy. It is a more consistent support
answer that remembers the current conversation, cites its internal support
topics, stays inside the public-support boundary, and fails safely when xCody
or MiniMax is unavailable.

## 2. Locked Owner Decisions

| Decision | Locked value |
|---|---|
| Autonomy | Read-only retrieval agent; no side effects |
| Model route | xCody OpenAI-compatible Chat Completions with `minimax-m3` |
| Reasoning wire field | `reasoning_effort: medium`; never raw camelCase `reasoningEffort` |
| Runtime | Existing Python/FastAPI process; no Docker, Node, Bun, Pi, Oh My Pi, MCP, or sidecar |
| Model-visible tools | Exactly one: `search_support_docs` |
| Agent budget | Normally one provider request; at most two provider requests and one tool call |
| Knowledge | Deployed, sanitized, allowlisted support bundle only |
| User input | Redacted current message plus bounded redacted current-session history |
| Memory | Volatile RAM memory, 60-minute TTL, no durable user profile |
| Forbidden access | Databases, accounts, attachments, raw diagnostics, keys, configs, shell, network tools, arbitrary files |
| Uncertainty | Immediate human escalation; no speculative answer |
| Root `AGENTS.md` | Repository-only authority; never runtime model context or support memory |

## 3. Scope

### In scope

- a provider-neutral micro-harness around the existing support model call;
- deterministic retrieval over `shared/support-ai-knowledge.json`;
- one locally executed, read-only knowledge-search tool;
- bounded, in-memory session context;
- stable-prefix prompt construction and cache telemetry;
- strict input redaction, output validation, and source-topic validation;
- xCody/MiniMax configuration through environment variables;
- retry, timeout, concurrency, and loop budgets;
- additive API session continuity for the in-app assistant;
- deterministic suggested actions and human escalation;
- focused unit, integration, adversarial, live-provider, cache, and load tests;
- canonical platform and active-client contract updates for changed behavior.

### Out of scope

- reading a customer account, entitlement, payment, key, node, or database row;
- reading ticket attachments or arbitrary repository/server files;
- changing settings, reconnecting, attaching diagnostics, creating tickets, or
  executing any other action on behalf of the user;
- long-term user memory or personalization across support sessions;
- embeddings, a vector database, external search, MCP, skills, subagents, Pi,
  Oh My Pi, Pydantic AI, LangGraph, or another agent framework;
- streaming responses;
- production deploy or owner environment mutation in the implementation task;
- treating model output as proof that an action succeeded.

## 4. Runtime Architecture

```text
authenticated support endpoint / helpbot / ticket flow
  -> input boundary and redactor
  -> authenticated owner-scope and opaque session resolver
  -> bounded RAM session store
  -> local deterministic pre-retriever
  -> stable-prefix context builder
  -> xCody model adapter
       -> final structured answer, or
       -> search_support_docs (one read-only call)
            -> bounded local tool result
            -> second and final model turn
  -> strict output validator and output redactor
  -> deterministic suggested actions / escalation
  -> redacted operational trace
```

The model proposes either a final structured answer or the single knowledge
tool call. Application code owns retrieval, limits, validation, memory,
redaction, telemetry, retries, and termination.

### 4.1 Units and interfaces

#### `SupportAgentPolicyStore`

Purpose: fail closed while loading the AGENTS-like runtime policy and render a
bounded canonical prompt from typed values rather than arbitrary instruction
text.

Interface:

```text
load(path) -> PolicySnapshot
```

The JSON object has no additional properties and uses this exact schema:

| Field | Type and bound | Required value |
|---|---|---|
| `schema_version` | string, 1--8 ASCII characters | `"1"` |
| `scope` | string enum | `"public_support"` |
| `role` | string enum | `"pokrov_safe_support_agent"` |
| `source_hierarchy` | unique array, exactly 4 items | Exact order: `operating_policy`, `retrieved_support_topics`, `redacted_session`, `redacted_user_message` |
| `forbidden_data` | unique array, exactly 10 items | Exact ordered code-owned list below |
| `output_contract` | closed object | Exact values `language="ru"`, `format="json_v1"`, `max_reply_chars=1200` |
| `escalation_rules` | unique array, exactly 8 items | Exact ordered code-owned list below |
| `forbidden_claim_patterns` | unique array, 12--32 strings | Required baseline plus normalized literal phrases, 2--120 characters each |

The required `forbidden_data` order is `account_data`, `database`,
`attachment`, `credential`, `connection_material`, `raw_diagnostics`,
`private_topology`, `shell`, `network_tool`, and `arbitrary_file`.
The required `escalation_rules` order is `uncertain`, `missing_source`,
`account_specific`, `payment_specific`, `sensitive_input`, `human_requested`,
`invalid_output`, and `provider_failure`. Runtime code maps these enums to
fixed prompt text and behavior; the file cannot add executable instructions.

Claim entries are not raw regular expressions. The loader applies Unicode
NFKC and case folding, maps punctuation to spaces, collapses whitespace, permits
only Unicode letters, digits, spaces, and `%`, then compiles an internally
generated expression using `re.escape` plus bounded flexible whitespace. This removes regex syntax
and ReDoS from policy data. The array must contain this normalized baseline;
additional entries may only narrow output further:

```text
100% анонимность
полная анонимность
гарантированная анонимность
100% доступность
гарантированный аптайм
никогда не отключается
pokrov стабильный релиз 1 0
pokrov доступен в google play
pokrov доступен в app store
pokrov подписан доверенным сертификатом
pokrov проверен из россии
pokrov готов для ru origin
```

Missing baseline entries, missing files, duplicate/unknown values, control
characters, wrong types, extra keys, over-limit text, compile failure, or a
stable rendered policy over 6,000 characters disable the harness before any
provider call and select the deterministic fallback with escalation.

The validated snapshot and its SHA-256 version are loaded atomically at process
startup. Reload is explicit and swaps snapshots only after full validation;
failure retains no partially parsed policy. The snapshot hash participates in
the stable-prefix hash and operational trace.

#### `SupportKnowledgeStore`

Purpose: load and validate the deployed support bundle once, expose a compact
stable index, and return bounded topic bodies.

Interface:

```text
load(path) -> KnowledgeSnapshot
search(query, limit, exclude_ids=()) -> list[KnowledgeHit]
read_topic_ids(ids) -> list[KnowledgeHit]
```

Invariants:

- accepted scope is exactly `public_support`;
- serialized KB size is at most 65,536 bytes;
- the bundle contains at most 20 rules and 100 topics;
- every topic ID matches the existing safe ID grammar;
- each topic has at most 20 keywords, each keyword is at most 80 characters,
  and each topic body is at most 1,200 characters;
- only `id`, `keywords`, and `body` are model-visible;
- search never accepts a path or URL;
- result IDs must exist in the loaded snapshot;
- one result bundle is capped at 5 topics and 6,000 characters;
- a changed KB version produces a new stable-prefix version.

#### `SupportSessionResolver`

Purpose: bind client-visible continuity to an already-authenticated owner and
surface without exposing an owner identifier to the harness.

Interface:

```text
resolve(surface, authenticated_owner_id, assistant_session_id) -> SessionScope
```

Invariants:

- authentication and ticket/sender ownership checks finish before resolution;
- `owner_scope_hash` is SHA-256 over a length-prefixed UTF-8 tuple of
  `(surface, authenticated_owner_id)`;
- `internal_session_key` is SHA-256 over a length-prefixed tuple of
  `(owner_scope_hash, assistant_session_id)`;
- the harness receives only the two hashes, never the raw owner identifier;
- the rate limiter uses `owner_scope_hash`, so rotating a client session ID
  cannot bypass the per-owner limit;
- the RAM store and one-in-flight guard use `internal_session_key`;
- a session ID presented by another owner or surface maps to a different
  internal key and cannot expose the first owner's context.

#### `SupportSessionStore`

Purpose: keep only short-lived, already-redacted conversational state.

Interface:

```text
get(session_id, now) -> SupportSession | empty
append(session_id, messages, state, now) -> None
evict(now) -> EvictionStats
```

Invariants:

- client-visible opaque session IDs match `[A-Za-z0-9_-]{16,64}`;
- store keys are internal SHA-256 hashes, not client-visible IDs;
- maximum 256 live sessions per process;
- TTL is 3,600 seconds after last access;
- each session retains at most 6 redacted messages total;
- each stored message is capped at the configured user/answer limit;
- structured state contains only issue topic, attempted safe steps, last safe
  outcome, and whether escalation was requested;
- no Telegram ID, account ID, email, IP, key, token, raw diagnostics, or
  attachment metadata is stored;
- expired and least-recently-used sessions are evicted synchronously on access;
- process restart intentionally clears all session memory.

#### `SupportContextBuilder`

Purpose: produce deterministic stable and volatile prompt zones.

Interface:

```text
build(snapshot, session, redacted_message, pre_retrieval) -> AgentContext
```

Stable prefix order:

1. support-agent operating policy;
2. trust-boundary and escalation rules;
3. final-output JSON contract;
4. `search_support_docs` schema;
5. compact KB topic index in deterministic topic-ID order;
6. prompt bundle and KB versions.

Stable-prefix resource limits:

- normalized policy text is at most 6,000 characters;
- compact topic index is at most 8,000 characters;
- policy, instructions, schemas, index, and framing together are at most
  18,000 serialized characters;
- the serialized full provider request is at most 36,000 characters.

Volatile suffix order:

1. bounded retrieved topic bodies;
2. structured current-session state;
3. up to six recent redacted messages;
4. current redacted user message.

The bounded retrieved bodies are at most 6,000 characters and the combined
session-history/state zone is at most 6,000 characters. The current message
remains capped at 1,200 characters.

Those zone caps are ceilings, not additive reservations. Immediately before
each provider request, the builder serializes the complete request and enforces
the 36,000-character cap, including message/tool wrappers. It preserves the
stable prefix and current user message, then admits retrieved topics in score
order and session messages newest-first. The normalized assistant tool-call
replay is separately capped at 1,200 characters. On a continuation, all
pre-retrieval topic bodies are removed before the bounded tool result is added;
older session messages are then removed if needed. A tool result is truncated
only at a topic boundary. If stable prefix, current message, replay, and at
least one complete tool topic cannot fit, or if the stable prefix alone exceeds
18,000 characters, the run makes no provider call and escalates.

The builder uses deterministic JSON key ordering and whitespace. Request IDs,
timestamps, user IDs, and diagnostics do not enter the stable prefix.

#### `XCodyChatAdapter`

Purpose: isolate OpenAI-compatible wire behavior and normalize responses,
usage, tool calls, and errors.

Interface:

```text
complete(messages, tools, tool_choice, request_timeout) -> ModelTurn
```

Wire contract:

- `POST {SUPPORT_AI_API_BASE_URL}/chat/completions`;
- bearer authentication from runtime secret storage;
- model `minimax-m3` by default;
- top-level snake-case `reasoning_effort: medium` when configured;
- `max_tokens: 1200` by default;
- `n: 1`; a missing choice or more than one choice is invalid;
- no OpenRouter-only `provider`, headers, or routing fields on xCody;
- no undocumented cache key or reasoning field;
- usage normalization includes prompt, completion, and cached tokens when the
  provider reports them;
- response bodies and hidden reasoning are never written to operational logs.

#### `SupportAgentHarness`

Purpose: own the bounded retrieval loop and return one safe application result.

Interface:

```text
run(SupportAgentRequest) -> SupportAgentResult
```

Budgets:

- maximum 2 provider HTTP requests per run;
- maximum 1 model-visible tool call;
- a retry consumes the second and final provider-request slot;
- a tool continuation consumes the second and final provider-request slot;
- default total wall budget 25 seconds;
- default per-provider-request timeout 12 seconds, capped by remaining wall
  budget;
- concurrency acquisition waits at most 250 milliseconds;
- maximum 1 in-flight run per session;
- process-wide model concurrency default 2;
- per-owner-scope interactive limit 6 runs per rolling minute;
- maximum 1,024 owner rate buckets per process, with 60-second expiry and LRU
  eviction;
- model input is at most 36,000 serialized characters, model output is at
  most 1,200 tokens, final reply is at most 1,200 characters, tool query is
  2--200 characters, and one result contains at most 5 topics/6,000
  characters.

The harness has no general tool registry. The only accepted tool name is
`search_support_docs`; an unknown tool, malformed arguments, multiple or
parallel calls, repeated call, or call after the budget is exhausted produces
a safe fallback and escalation. No denial text is sent through an extra model
request.

## 5. Retrieval and Agent Loop

### 5.1 One-turn fast path

1. Redact and truncate the new user message.
2. If the stored issue topic still exists, pin it first; then retrieve scored
   topics locally until the 3-topic limit. No embedding or model call is used.
3. Build the stable prefix and volatile suffix.
4. Ask MiniMax for the strict final JSON contract.
5. Validate topic IDs, content, and status.
6. Store only the redacted bounded session state and return the answer.

Retrieval is fully deterministic. Query, keywords, and bodies use Unicode NFKC,
case folding, `ё` to `е`, whitespace collapse, and alphanumeric tokens of at
least two characters. For each topic, an exact normalized keyword phrase in
the query scores 10, each query-token/keyword-token intersection scores 2, and
each query-token/body-token intersection scores 1. Repeated tokens score once.
Zero-score topics are omitted; results sort by descending score then ascending
topic ID. The pre-retriever returns the pinned session issue plus the first
scored topics up to 3; a missing old issue ID is cleared. The tool returns the
first 5, excluding topic IDs already supplied. The same fixtures prove ranking
on every supported issue family.

### 5.2 One-tool recovery path

If the supplied topics are insufficient, the first model turn may call:

```json
{
  "type": "function",
  "function": {
    "name": "search_support_docs",
    "description": "Search the deployed public-support knowledge bundle.",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "minLength": 2,
          "maxLength": 200
        }
      },
      "required": ["query"],
      "additionalProperties": false
    }
  }
}
```

The first request sends this schema with `tool_choice: "auto"`. A final answer
with no tool call is valid. A tool response is accepted only when it contains
exactly one function call, the name is exact, `tool_call_id` is 1--128 safe
ASCII characters matching `[A-Za-z0-9_-]+`, `finish_reason` is `tool_calls`,
and the decoded JSON-string arguments match the schema above. Unknown,
malformed, zero-ID, multiple, or parallel tool calls execute nothing and
produce a safe fallback. The query also passes the input boundary scanner;
typed redaction markers or any non-`continue` disposition invalidate the call.

For a valid call, the harness searches only the in-memory support snapshot and
returns at most five bounded topics. It preserves the exact normalized
assistant message containing `tool_calls`, then appends one OpenAI-compatible
`tool` message with the matching `tool_call_id`, the exact function name, and
bounded deterministic JSON content. The second request includes the same tool
schema but forces `tool_choice: "none"`. A tool call in that response is invalid
and produces a safe fallback; no third request is allowed. A final response
must contain exactly one choice, `finish_reason: "stop"`, no `tool_calls`, and
content matching the final JSON contract.

The request budget is deterministic:

| Path | Request 1 | Local tool | Request 2 | Further request |
|---|---|---|---|---|
| Fast answer | Final answer | No | No | Forbidden |
| Fast transient failure | Failure | No | One retry | Forbidden |
| Tool recovery | Valid tool call | Once | Final answer | Forbidden |
| Retried response asks for tool | Failure | No | Retry emits tool call | Forbidden; fallback |
| Tool path request 2 fails | Valid tool call | Once | Failure | Forbidden; fallback |

A retry and a tool continuation can therefore never occur in the same run.

### 5.3 Final model contract

```json
{
  "schema_version": "1",
  "status": "answer",
  "reply": "Краткий безопасный ответ пользователю",
  "source_topic_ids": ["connected_no_internet"],
  "session_state": {
    "issue_topic_id": "connected_no_internet",
    "attempted_steps": ["reconnect"],
    "last_outcome": "not_reported",
    "escalation_requested": false
  }
}
```

Validation rules:

- `status` is `answer` or `escalate`;
- `source_topic_ids` is a unique array of at most 5 known topic IDs;
- an answer requires at least one topic ID that was actually supplied by a
  retrieval result in this run;
- an escalation may have no source topic;
- `reply` is non-empty, Russian-facing, and capped at 1,200 characters;
- `issue_topic_id` is `null` or one known topic ID supplied in this run;
- `attempted_steps` is a unique array of at most 8 values from `reconnect`,
  `restart_app`, `switch_route_mode`, `refresh_access`, `reimport_profile`,
  `update_client`, `check_device_time`, `attach_diagnostics`, and
  `contact_support`;
- `last_outcome` is exactly one of `not_reported`, `resolved`, `unchanged`,
  `improved`, `worse`, or `blocked`;
- `status: "answer"` requires `escalation_requested: false`;
- `status: "escalate"` requires `escalation_requested: true`;
- the root and `session_state` objects are closed; unknown fields are rejected;
- invalid JSON is not repaired with an unbounded extra turn; it falls back to
  the deterministic safe response and human escalation;
- final plaintext is redacted again before storage or display.

## 6. Knowledge and Instruction Boundary

The runtime server does not mount the repository for the model and does not
give it a filesystem-read tool. The deploy bundle contains only:

- `shared/support-agent-policy.json`: compact public support operating policy;
- `shared/support-ai-knowledge.json`: sanitized topic bundle.

`support-agent-policy.json` is an AGENTS-like runtime policy, not another
repository `AGENTS.md`. It contains role, source hierarchy, forbidden data,
output contract, and escalation rules. Root `AGENTS.md`, system overview,
deployment/access documentation, audit evidence, work orders, and operator
runbooks are excluded from runtime and KB-refresh model context.

The existing KB refresh flow must use an explicit public-support source
allowlist. Changing that allowlist is in scope because it enforces the owner-
approved safety boundary. The positive allowlist is exactly:

```text
shared/support-agent-policy.json
docs/user/portal-vpn-user-guide-ru.md
docs/user/compatibility-clients-guide-ru.md
shared/product-facts.json
shared/public-urls.json
shared/tariff-catalog.json
```

The manifest contains exact repository-relative paths, not directory globs.
Inventory resolution rejects symlinks, missing paths, traversal, and resolved
paths outside the repository. Each source is at most 50,000 characters and the
combined projected source bundle is at most 200,000 characters. Root `AGENTS.md`, the
documentation registry, architecture/system/application/support documents,
deployment/access material, access matrices, audits, work orders, and runbooks
are excluded even if they contain useful support facts.

Structured sources use positive field/section projections before they enter
the provider payload:

| Source | Included projection |
|---|---|
| `support-agent-policy.json` | Exact schema keys `schema_version`, `scope`, `role`, `source_hierarchy`, `forbidden_data`, `output_contract`, `escalation_rules`, `forbidden_claim_patterns`; no extra keys |
| `portal-vpn-user-guide-ru.md` | Exact heading allowlist below; no default for new headings |
| `compatibility-clients-guide-ru.md` | Exact heading allowlist below; no default for new headings |
| `product-facts.json` | Top-level keys `brands`, `strategy`, `trial`, `telegram_reward`, `engines`, `platform_scope`, `network_defaults`, `versions`, `legal`; `operations` is never serialized |
| `public-urls.json` | Top-level keys `surfaces`, `legal`, `releases`, `telegram`; `contact` is never serialized |
| `tariff-catalog.json` | Top-level keys `catalog_version`, `default_currency`, `commerce_model`, `public_surface_policy`, `plan_aliases`, `pricing_preview`, `plans`; no extra keys |

The portal-guide heading allowlist is exactly:

```text
Быстрый старт
Что такое POKROV
Официальные адреса
Короткий путь для нового пользователя
Как устроены сайт, кабинет, Telegram и ссылка подключения
Бесплатный период и бонус
Как проходит первый запуск в приложении
Как выбирается режим оптимизации
Как работает авто-выбор маршрута
Как проходит путь через сайт и кабинет
Роль Telegram
Как получить бонус `+10 дней`
Основные разделы приложения
Основные разделы кабинета
Режимы маршрутизации
Поддержка
Если что-то пошло не так
Пробный период не активировался
Бонус за Telegram не начислился
Не открывается сайт или кабинет
Нужный сайт или сервис открывается плохо
Нужно восстановить доступ
Безопасность
Отзывы и предложения
Переход со старых ссылок и профилей
```

The compatibility-guide heading allowlist is exactly:

```text
Для кого этот документ
Самый короткий путь
Текущий статус совместимости
Что выбрать
Важная безопасность
Где взять личную ссылку
Karing
Hiddify
Happ
v2rayNG на Android
v2rayN на Windows
Streisand на iPhone и iPad
Shadowrocket, FoXray, V2Box и другие iOS-клиенты
NekoBox, NekoRay и sing-box for Android
Частые проблемы
Что написать в поддержку
Если вы помогаете родственнику или новичку
```

Missing required projected keys/headings, duplicate headings, parse failures,
or unexpected keys inside the runtime-policy schema abort refresh. Content
outside a positive projection is never concatenated, logged, or sent to the
provider. This specifically keeps the operational host fields currently under
`product-facts.json#/operations` outside model context.

Before any provider call, refresh performs a fail-closed content lint over
every projected source payload. It rejects secret-like data, private protocol links,
private IPs/hosts, internal filesystem paths, shell/deployment commands,
environment-variable or credential material, and non-public URLs. The exact
URL host set is derived only from the projected `shared/public-urls.json`
values after their own validation; URLs may not contain userinfo, query, or
fragment data. A `connect.pokrov.space` path must be `/`, an explicitly
documented static route, or the literal `...` placeholder, never a personal
token. A violation aborts the whole
refresh; unsafe input is never merely redacted and sent upstream. The
generated KB is independently schema-, size-, scope-, and safety-validated
before it can be applied.

Retrieved documents and user messages are data, never authoritative
instructions. Prompt-injection text inside either source cannot add tools,
expand the allowlist, change budgets, or override escalation rules.

## 7. Input and Output Safety

### Input disposition

The boundary scanner runs before retrieval, memory, tracing, or a provider
call and assigns exactly one disposition:

| Input class | Disposition | Provider/memory behavior |
|---|---|---|
| Raw VLESS/VMess/Trojan/SS/SSR/Hysteria/TUIC links; bearer/`sk-*`/JWT/init-data/key assignments; UUID/access keys; PEM/private keys; raw config/QR/WARP/WireGuard material; credential-like base64/high-entropy strings | `hard_reject` | No retrieval or provider call; store no message text; return fixed sensitive-data warning and human escalation |
| Card-like payment numbers | `hard_reject` | No retrieval/provider/memory; fixed payment-safety warning and human escalation |
| Explicit request to inspect an account, payment, key, attachment, database, server, or to execute a command | `local_escalate` | No provider call and no message text in memory; fixed boundary explanation and human escalation |
| Email, phone-like identifier, IPv4/IPv6/private host, or ordinary non-allowlisted URL | `redact_continue` | Replace the complete span with a typed marker before retrieval/provider/memory |
| Plain support text, including prompt-injection prose with no sensitive material | `continue` | Treat as untrusted data and run the bounded agent path |

When classes overlap, precedence is `hard_reject`, `local_escalate`,
`redact_continue`, then `continue`.

Scanning starts on the accepted API message (maximum 2,000 characters), then
redaction is applied, the model-facing text is capped at 1,200 characters, and
the scanner runs again across truncation boundaries. `redact_continue`
proceeds only when at least three alphanumeric tokens remain after typed
markers are removed; otherwise it becomes `local_escalate`. The only retained
security data is category/count and disposition, never the matched span or
marker-adjacent text. Hard-rejected and locally escalated messages do not enter
session history.

### Safe diagnostics

`safeDiagnostics` values do not enter the model or session memory in v1. The
assistant endpoint accepts at most four server-known keys:
`app_version`, `platform`, `route_mode`, and `connection_status`. It rejects
more than 20 submitted entries or more than 4,096 serialized characters,
discards every unknown key and its value without stringifying it, and records
only accepted constant key names. Unknown-name telemetry is a count, never the
attacker-controlled name. Accepted values must be scalar and at most 160
characters but are otherwise ignored by the harness and never logged. This
allowlist is endpoint-specific; broader ticket-diagnostics contracts do not
expand it.

### Output enforcement

- validate the final JSON shape locally;
- require grounding in topic IDs supplied during the run;
- run the same secret/PII scanner over `reply` and session state;
- reject raw URLs, configs, hosts, tokens, and deterministic forbidden product
  claim patterns;
- derive `suggestedActions` in application code, never from free model text;
- set `shouldEscalate=true` for model uncertainty, invalid output, missing
  sources, repeated recovery failure, payment/account ambiguity, secret-paste
  attempts, explicit human requests, or any harness failure.

`support-agent-policy.json` contains a versioned
`forbidden_claim_patterns` literal list compiled only through the loader's
`re.escape` path. V1 patterns cover exact prohibited classes such as guarantees of
100% anonymity or uptime, unverified stable/store availability, trusted-
signing claims, and RU-origin readiness claims. A match rejects the reply and
escalates. Source IDs prove retrieval provenance only; they do not prove
semantic entailment. Broader grounding quality is measured by deterministic
fixtures plus manual review, not claimed as a runtime guarantee.

## 8. Session and API Contract

### Application request

The existing `POST /api/client/support/assistant` request gains one optional
field:

```json
{
  "message": "Подключилось, но сайты не открываются",
  "scope": "support",
  "assistantSessionId": "opaque_random_16_to_64_chars",
  "ticketId": null,
  "safeDiagnostics": {}
}
```

If absent or invalid, the platform generates a new opaque session ID. The
active client keeps it only for the lifetime of the open assistant sheet and
sends it with subsequent messages. Closing the sheet ends client continuity;
server TTL eviction remains the final cleanup boundary.

Generated IDs use `secrets.token_urlsafe(24)` and therefore carry 192 bits of
randomness while fitting the declared grammar. Client-supplied IDs are never
treated as authorization.

`scope` must equal `support`; it is not used as a caller-selected security
surface. A supplied `ticketId` continues to require the existing owner check.

The endpoint resolves continuity only after its normal authentication check.
It combines the authenticated platform user ID with surface `app`, hashes that
owner scope, and derives the internal store key as specified in section 4.1.
The raw user ID never enters the prompt, harness request, memory value, or
trace. A caller cannot use another user's `assistantSessionId` to read context,
and rotating IDs cannot bypass the owner-scoped rate limit.

### Application response

```json
{
  "reply": "...",
  "assistantSessionId": "opaque_random_16_to_64_chars",
  "suggestedActions": [],
  "shouldEscalate": false,
  "source": "support_agent"
}
```

Unknown additive response fields remain ignorable by older clients. Ticket
creation, attachment, and operator APIs do not change.

### Ticket and Telegram continuity

Ticket/helpbot callers construct a surface-scoped opaque session key outside
the harness, after existing ticket-ownership or Telegram-sender validation.
They derive separate owner scopes (`ticket` and `helpbot`) and pass only hashes.
The ticket resolver uses the authenticated ticket owner plus ticket ID as a
length-prefixed tuple; the helpbot resolver uses the already-validated Telegram
sender ID. Each produces a stable base64url-encoded SHA-256 session token of
32 characters. The ticket token is stable only for that owner/ticket pair; the
helpbot token is stable only for that sender. Raw ticket, account, and Telegram
IDs remain inside the resolver and never enter the harness request, prompt,
memory value, or trace. Reuse lasts only while the matching process-local RAM
entry remains inside the 60-minute idle TTL; eviction/restart starts a fresh
conversation even though the resolver produces the same token.
The harness does not receive a database session and never loads ticket history.
It remembers only redacted messages that were passed through the harness during
the current 60-minute window.

V1 continuity is deliberately process-local. The portal API process and
helpbot process each own an independent RAM store, rate limiter, one-in-flight
map, and semaphore. There is no cross-process or cross-surface conversation
continuity, and a restart or request routed to a different process may lose
context. The response remains safe because every run can answer from the
deployed KB or escalate. Durable/shared memory is out of scope.

## 9. Cache and Resource Strategy

- stable prompt blocks appear before all retrieved/session/user data;
- tool and output schemas have deterministic key and property order;
- topic index order is stable by topic ID;
- `prompt_bundle_version`, `tool_bundle_version`, and KB version are recorded;
- KB or policy changes intentionally create a new prefix hash;
- history is append-only within the six-message bound;
- no summary model call is needed in v1;
- no full 38 KB knowledge dump is sent on every request;
- topic bodies are attached only after local retrieval;
- cache telemetry is observational: the harness records provider-reported
  cached tokens but never claims a hit when the field is missing.

Live pre-design evidence against the enterprise route:

- all 8 successful tool-enabled requests returned one valid
  `search_support_docs` tool call with valid JSON arguments;
- 2 of 10 requests timed out and none returned HTTP 400;
- one repeated 6,590-token prompt reported 6,589 cached tokens, proving the
  route can reuse an exact stable prefix; other requests reported zero or only
  a negligible cached-token count, so routing does not guarantee every hit.

Each process-wide concurrency semaphore defaults to 2 and waits at most 250
milliseconds. The theoretical deployment-wide maximum is `2 * live process
count` (four calls only when exactly one portal API and one helpbot process are
running); v1 makes no global concurrency guarantee across processes. A full 256-session RAM store
with six bounded messages per session plus 1,024 short-lived owner rate buckets
remains bounded. Busy, rate-limited, or expired runs return a safe fallback and operator
path instead of queuing unbounded work.

## 10. Error Handling and Termination

Every run terminates with `answer`, `escalate`, `fallback`, or `disabled`.

Retry only:

- connection resets and other transient transport failures;
- HTTP 429/502/503/504 when the shared deadline has enough time remaining;
- a model timeout only when the second request slot and enough wall budget
  remain.

Do not retry:

- HTTP 400/401/403;
- invalid tool names or arguments;
- invalid final JSON;
- output safety failures;
- a second-turn failure after the single tool budget is consumed.

Any retry uses a short jittered backoff and the same stable prefix. Each
provider request has a 12-second default timeout further capped by the
remaining 25-second run deadline. The global deadline and two-request limit
always win. A valid tool call consumes the continuation slot and disables
retry. Missing provider credentials, disabled flags, busy concurrency,
deadline exhaustion, malformed responses, and safety rejections return the
existing deterministic local fallback with `shouldEscalate=true`.

## 11. Configuration

Add or normalize these environment settings without committing credentials:

```text
SUPPORT_AI_ENABLED=false
SUPPORT_AI_AGENT_ENABLED=false
SUPPORT_AI_API_BASE_URL=https://api.xcody.dev/v1
SUPPORT_AI_MODEL=minimax-m3
SUPPORT_AI_REASONING_EFFORT=medium
SUPPORT_AI_TIMEOUT_SECONDS=12
SUPPORT_AI_RUN_DEADLINE_SECONDS=25
SUPPORT_AI_MAX_PROVIDER_REQUESTS=2
SUPPORT_AI_MAX_TOOL_CALLS=1
SUPPORT_AI_MAX_CONCURRENCY=2
SUPPORT_AI_CONCURRENCY_WAIT_MS=250
SUPPORT_AI_SESSION_TTL_SECONDS=3600
SUPPORT_AI_MAX_SESSIONS=256
SUPPORT_AI_OWNER_RATE_LIMIT_PER_MINUTE=6
SUPPORT_AI_MAX_RATE_BUCKETS=1024
SUPPORT_AI_PRE_RETRIEVAL_LIMIT=3
SUPPORT_AI_TOOL_RESULT_LIMIT=5
SUPPORT_AI_MAX_RETRIEVED_CHARS=6000
SUPPORT_AI_MAX_INPUT_CHARS=36000
SUPPORT_AI_MAX_OUTPUT_TOKENS=1200
```

Environment values may lower safety/resource ceilings but cannot raise the
hard caps in this document. Invalid, non-numeric, negative, or out-of-range
agent settings disable the harness and select fallback; they are not silently
expanded. In particular, provider requests/tools/output tokens remain capped
at `2/1/1200`, concurrency at 2, sessions at 256, rate buckets at 1,024, and
serialized input at 36,000 characters.

The production enterprise base URL and API key remain owner-side runtime
secrets. There is no shadow mode: it would double provider calls on the weak
server and obscure which implementation answered. Route selection is exact:

| `SUPPORT_AI_ENABLED` | `SUPPORT_AI_AGENT_ENABLED` | Runtime behavior |
|---|---|---|
| `false` | either | No provider call; deterministic local fallback |
| `true` | `false` | Existing legacy one-call support helper |
| `true` | `true` | New harness; at most two provider requests |

Only one row executes for a request, so legacy and harness calls never run in
parallel or serially for the same user message.

Application result mapping is also deterministic:

| Selected path/result | Public `source` | Public reply | `shouldEscalate` |
|---|---|---|---|
| Legacy helper success | Existing `support_ai` value | Legacy validated reply | Existing deterministic rule |
| Harness `answer` | `support_agent` | Validated agent reply | Deterministic issue rule |
| Harness `escalate` or any failure | `local_fallback` | Existing safe fallback | `true` |
| Provider disabled/unconfigured | `local_fallback` | Existing safe fallback | `true` |

The app, ticket flow, and helpbot use the same mapping. Model text cannot
select the public source label or suppress escalation.

## 12. Observability

Record one redacted trace per run:

```text
run_id
surface
session_id_hash
provider/model
prompt/tool/KB bundle versions and hashes
provider-request and tool-call count
retrieved topic IDs
redaction categories and counts
input/output/cached token counts when reported
per-request and total latency
retry/error class
final status and escalation reason code
```

Never log user message text, assistant reply text, hidden reasoning, tool raw
arguments, credentials, provider payloads, session IDs, diagnostics values, or
knowledge bodies.

## 13. Verification

### Deterministic tests

1. Policy-loader tests cover every field type/enum/count/length bound, unknown
   keys, unsafe literal-pattern characters, duplicate values, rendered-size
   overflow, atomic reload, and fail-closed startup with zero provider calls.
2. KB validation rejects wrong scope, unknown paths, unsafe bodies, duplicate
   IDs, secret patterns, and oversized results.
3. Retriever ranks known support issues and returns deterministic bounded
   results without external calls.
4. Input-boundary tests cover every disposition and precedence rule, including
   secrets split near truncation boundaries. Diagnostics tests prove only four
   constant key names can be logged and attacker-controlled names/values cannot.
5. Session store enforces ID format, TTL, LRU limit, six-message bound, and
   isolation between owners, surfaces, and sessions; rotating a session ID
   does not bypass the owner-scoped rate limit.
6. Stable-prefix serialization and hash remain identical when only user,
   session, request ID, or retrieval results change; overflow tests prove the
   exact first- and second-request truncation order.
7. Final-output tests cover every state enum, closed objects, source bounds,
   and answer/escalation coherence while preserving only safe state.
8. One valid tool call preserves the assistant `tool_calls` message, appends
   the matching `tool_call_id`, produces one bounded result, and permits only
   one final provider request with `tool_choice: "none"`.
9. Unknown, malformed, parallel, repeated, or over-budget tool calls escalate.
10. Invalid JSON, unknown source IDs, secret output, and configured forbidden
    literal-claim patterns fall back and escalate; no semantic-entailment test
    is claimed as a runtime control.
11. Fake-adapter tests prove the two-request truth table: retry and tool
    continuation are mutually exclusive, per-request timeout is capped by the
    run deadline, and concurrency acquisition/rate limiting are deterministic.
12. Existing ticket/helpbot/app callers retain a response when the provider is
    disabled or unavailable.
13. API tests cover generated and supplied assistant session IDs, authenticated
    owner binding, surface isolation, invalid IDs, stable ticket/helpbot
    derivation, TTL restart, and cross-owner collision attempts.
14. KB-refresh tests prove the exact positive source allowlist, projections,
    symlink/path rejection, per-file/aggregate limits, and fail-closed
    pre-provider lint; the fake provider records zero calls for every unsafe
    fixture.
15. Configuration-table tests prove exactly one of disabled, legacy, or
    harness paths runs and that no shadow/double call exists.

These deterministic fake-adapter tests are the implementation gate. They do
not require xCody credentials and must be `PASS` before code completion can be
claimed.

### Live xCody evaluation

Use synthetic public-support fixtures only:

- 48 normal questions across connection, speed, import, routing, activation,
  generic payment guidance, device limits, and official surfaces. Each fixture
  defines accepted topic IDs, required/forbidden concepts, and expected
  `answer` status;
- 12 adversarial questions containing prompt injection, secrets, raw links,
  account requests, requests for forbidden guarantees, and requests for
  commands;
- 10 three-turn sessions that refer to prior attempted steps;
- repeated identical-prefix probes to measure reported cache reuse;
- 5/15/30/60 RPM ramps with concurrency 1/2/4, stopping before any sustained
  provider failure or shared deadline breach.

Fixture concept checks use normalized literal phrase groups: every required
group needs at least one member and no forbidden member may appear. Load ramps
use distinct synthetic owner/session hashes so the intentional 6-RPM
per-owner limit does not turn the load test into a rate-limiter-only test. The
report records the fixture-bundle hash but no prompt or reply text.

Retain aggregate results only. A live run passes the harness gate when:

- no request produces an unhandled exception;
- no secret or private input appears in model context, output, memory, or logs;
- all out-of-scope/adversarial cases escalate;
- at least 41 of 48 normal fixtures return a validated `answer`; each answered
  fixture uses an accepted topic ID and satisfies its deterministic
  required/forbidden concept checks;
- at least 8 of 10 multi-turn fixtures preserve the expected issue topic,
  attempted-step code, and outcome without re-asking an already answered
  question;
- a human reviewer checks every normal/multi-turn answer that passed automated
  checks and records zero materially incorrect or unsafe troubleshooting steps;
- every factual answer cites only topic IDs supplied during that run;
- every malformed/tool/provider failure becomes a safe fallback;
- there are zero payload-format HTTP 400 responses;
- memory and concurrency stay within configured bounds;
- p50, p95, timeout, retry, fallback, and cache-hit metrics are reported
  honestly without converting missing provider evidence into a pass.

The retained report labels the exact route/model/candidate and uses repository
evidence labels. It is `PASS` only when the automated live suite runs against
that exact candidate and meets every criterion. If the owner performs the run
outside the retained harness, label it `MANUAL_OWNER_TEST`; if enterprise
credentials or route access are unavailable, label it `BLOCKED_BY_ACCESS`.
Missing live evidence does not invalidate deterministic code-test `PASS`, but
it blocks any claim of live-provider readiness.

### Baseline evidence before implementation

Using an isolated environment built from `portal_bot/requirements.txt` plus
test-only `pytest` and `httpx`:

```powershell
$py = Join-Path (Join-Path $env:TEMP 'pokrov-support-agent-venv-20260715') 'Scripts\python.exe'
$base = Join-Path $env:TEMP ('pokrov-support-agent-pytest-' + [guid]::NewGuid().ToString('N'))
& $py -B -m pytest -p no:cacheprovider --basetemp=$base tests/test_support_ai_service.py tests/test_client_ui_api_additions.py tests/test_pokrov_support_ai_kb_refresh.py -q
```

Result: `12 passed in 22.54s`.

## 14. Documentation and Repository Impact

Platform changes update:

- `docs/architecture/support-feedback-flow.md` as the canonical behavior owner;
- `docs/operations/deployment-and-access.md` for new runtime variables only;
- `portal_bot/.env.example` with secret-free xCody placeholders;
- focused service/API/KB tests.

Active-client behavior changes update
`C:/Users/kiwun/Documents/ai/POKROV-app/docs/architecture/in-app-ai-assistant-contract.md`
in the client repository when `assistantSessionId` plumbing is implemented.
The platform document may point to that contract but does not replace it.

## 15. Rollout and Done Condition

Implementation order:

1. policy/KB validation and deterministic retriever;
2. redaction hardening and bounded session store;
3. xCody adapter and normalized usage/tool events;
4. bounded harness loop and output enforcement;
5. API/helpbot/ticket integration behind `SUPPORT_AI_AGENT_ENABLED`;
6. active-client session-ID plumbing;
7. deterministic tests and canonical docs;
8. retained synthetic live evaluation, then owner-controlled enablement.

The implementation task is done when focused deterministic tests pass, the
synthetic live evaluation report is retained without secrets, existing support
fallbacks still work, the exact diff is reviewed for boundary violations, and
no deploy or production enablement is claimed or performed without a separate
owner instruction.
