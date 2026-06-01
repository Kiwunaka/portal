# Agent Context And Cost Harnesses

Last updated: 2026-05-23

## Document Status

This file is the workspace standard for cache-aware agent prompts, external-model context packets, and LLM cost/latency harnesses.

Use it when a `WO`, review packet, design/copy consult, release-goal packet, or video-agent prompt sends substantial repeated context to an LLM.

## Sources And Scope

This guidance is based on:

- OpenAI Codex use cases: durable goals, teammate setup, production systems, review, and automation workflows.
- OpenAI Prompt Caching guide: prompt caching starts at 1024+ prompt tokens, exposes `usage.prompt_tokens_details.cached_tokens`, and supports `prompt_cache_retention` on supported models.
- The local prompt-caching playbook reviewed from `C:/Users/kiwun/Downloads/Telegram Desktop/prompt-caching-playbook`.

The source-specific pricing numbers in external playbooks are useful for prioritization, not product canon. The local rule is: measure cache hit rate and token split in our own traces before treating a savings claim as proven.

## What We Should Add To Agent Work

### 1. Cache-Aware Context Packet Shape

Every repeatable prompt packet should be assembled in this order:

```text
# STABLE PREFIX
tool definitions or tool names
role and output contract
POKROV canon and safety rules
stable repo/workflow rules
stable examples or rubrics

# CACHE BREAKPOINT

# DYNAMIC SUFFIX
current task
current date
cwd, branch, git status
latest user steering
fresh file excerpts
run id / trace id
tool outputs
```

Do not put current date, request id, trace id, live `git status`, dirty-file lists, or current run state at the start of a reusable prompt. These values belong after the cache breakpoint.

### 2. Context Packet Harness

Before reusing or sharing a large prompt packet, run:

```powershell
python scripts/agent_context_packet_audit.py <packet.md>
```

The harness flags dynamic markers in the stable prefix and estimates whether the stable prefix is large enough to qualify for OpenAI prompt caching. It is deliberately conservative and does not call any provider.

Use this harness for:

- generated external-model review packets
- copy/design critique packets sent through OpenCode
- WO packets that include large canon excerpts
- release-goal packets reused across multiple sessions
- `.content-video-ad` research/script prompt packets when they become repeatable

### 3. Telemetry Harness For Real LLM Calls

Any repo-owned production LLM integration should log a provider-neutral record:

```json
{
  "provider": "openai | anthropic | gemini | self_hosted | other",
  "model": "model-id",
  "prompt_tokens": 0,
  "cache_read_tokens": 0,
  "cache_write_tokens": 0,
  "new_input_tokens": 0,
  "output_tokens": 0,
  "cache_hit_rate": 0.0,
  "ttft_ms": 0,
  "total_latency_ms": 0,
  "system_prompt_hash": "12-char-prefix",
  "tools_hash": "12-char-prefix",
  "prompt_cache_key": "redacted-or-coarse-segment"
}
```

For OpenAI Responses or Chat Completions, parse `usage.prompt_tokens_details.cached_tokens` when it is present. Requests below 1024 prompt tokens should be expected to report `cached_tokens=0`.

Telemetry must never log raw prompts, secrets, auth headers, Telegram initData, private emails, payment payloads, or subscription URLs.

### 4. WO-Level Cost/Context Risk

Set the `LLM Context And Cost Harness` section in the WO to `Required: yes` when the work creates or changes:

- an agent prompt or reusable context packet
- an external-model consult path
- a prompt-heavy batch process
- an eval or review harness that repeats the same large context
- provider routing for OpenAI, Anthropic, Gemini, OpenRouter, Fireworks, CODY, or self-hosted models
- `.content-video-ad` scripts/prompts/model orchestration

Set `Required: no` for ordinary product code, docs-only edits, and one-off manual model consults where no repeatable LLM call path changes.

### 5. Provider Routing Rules

For cache-heavy workloads:

- prefer stable direct-provider routes when cache telemetry matters
- avoid switching model/provider mid-session unless a cold-cache reset is acceptable
- keep tool definitions stable and versioned; reordering tools can invalidate the cached prefix
- keep `prompt_cache_key` coarse enough to aggregate traffic, not per one-off request
- use longer retention only when request gaps make it useful and the provider supports it

OpenRouter and similar proxy routes can be fine for one-off critique, but cache-sensitive agent loops need explicit proof that cache stats and sticky routing work.

## Codex Use-Case Mapping For POKROV

The OpenAI Codex use-case page reinforces patterns we already want locally:

| Codex pattern | POKROV implementation |
| --- | --- |
| Durable goal | `GOAL.md`, `FLOW_STATE`, and work-order completion evidence. |
| Set up a teammate | `AGENTS.md`, canonical docs, and stable context packets. |
| Production systems | WO proof boundaries, release gates, and exact repo-lane evidence. |
| Review and repair loops | owned-finding rechecks, fresh-final reviews, and problem-class analysis. |
| Automation | heartbeats/automations only when a real later check or feedback loop exists. |

The missing piece was cost observability. That is why this file adds the packet linter and telemetry schema.

## Anti-Patterns To Reject

- Dynamic date/session/request ids before the cache breakpoint.
- Rebuilding the whole prompt from unordered maps or unsorted tool arrays.
- Adding live `git status` or file tree output to the stable system block.
- Reformatting old conversation history on every turn.
- Putting dynamic tool results into a cached prefix.
- Sending large provider calls without cache usage telemetry.
- Claiming cost improvement without before/after token and cache-hit evidence.

## Completion Standard

A prompt-heavy WO is not complete until it records:

- stable prefix and dynamic suffix boundaries
- the harness or telemetry used
- cache hit evidence or a reason it is not measurable
- expected residual cost risk
- whether failures are attributable to this WO or to provider/proxy behavior
