# External Model Consults

Document class: `OPERATOR_PLAYBOOK`
Usage: opt-in only
Last verified: 2026-07-11

This playbook owns optional external-model routing, price snapshots, prompt
shapes, skill packets, and OpenCode shell notes. It is not part of the default
Codex task route. Do not install a dependency, plugin, MCP server, gateway, or
service to use it. If the existing optional path is unavailable, continue with
Codex and record the consult as not run.

## Authority Boundary

Codex remains the repository operator and decision owner. It selects the
minimum current sources, protects no-touch scope, edits files, runs checks,
reviews the diff, and produces the handoff. An external model may critique a
redacted packet or draft alternatives; it may not discover the repository,
choose product truth, call tools, change files, close a gate, or authorize a
claim.

Resolve every suggestion against the current task route, canonical owners,
current code and tests, and exact runtime evidence. Reject conflicting advice.
Do not cite a consult as proof. Use it only when an independent angle is worth
the extra data exposure, latency, and cost.

## Data And Secret Boundary

Send only task-bounded excerpts that have been reviewed as data leaving the
repository boundary. Never send:

- API keys, tokens, credentials, private keys, auth/config files, headers, or
  bearer material;
- customer or operator identifiers, private support text, Telegram init data,
  payment payloads, subscription URLs, or connection material;
- `.env` contents, raw provider responses, hidden reasoning fields, broad
  repository dumps, or unrelated evidence.

Use placeholders only when structure matters. Prefer a short paraphrase over a
raw excerpt when the exact text is unnecessary. If the consult cannot work
without restricted data, do not run it.

## Current OpenRouter Consult Set

The following snapshot came from the public official
[`GET /api/v1/models`](https://openrouter.ai/api/v1/models) catalog on
2026-07-11. `AVAILABLE` means the ID appeared in that catalog; it does not
guarantee account access, throughput, latency, or future availability. Prices
are catalog USD rates per one million tokens. Context is the advertised
maximum, not a recommendation to send a large packet. The leading
`openrouter/` segment below is the OpenCode provider selector; the official
catalog ID is the remaining `author/model` segment.

| Model ID | Availability | Context tokens | Input / 1M USD | Output / 1M USD | Role | Cost check |
| --- | --- | --- | --- | --- | --- | --- |
| `openrouter/deepseek/deepseek-v4-pro` | `AVAILABLE` | `1048576` | `$0.435` | `$0.870` | Contradiction hunting, dense design or canon critique; use xhigh reasoning only when explicitly justified | `reverify before cost-sensitive use` |
| `openrouter/z-ai/glm-5.1` | `AVAILABLE` | `202752` | `$0.966` | `$3.036` | Parallel alternative-angle review | `reverify before cost-sensitive use` |
| `openrouter/openai/gpt-5.5-pro` | `AVAILABLE` | `1050000` | `$30.00` | `$180.00` | Narrow, high-stakes, expensive senior review | `reverify before cost-sensitive use` |
| `openrouter/moonshotai/kimi-k2.6` | `AVAILABLE` | `262144` | `$0.660` | `$3.410` | Taste, natural Russian copy, roleplay, and elegant alternatives | `reverify before cost-sensitive use` |
| `openrouter/moonshotai/kimi-k2.7-code` | `AVAILABLE` | `262144` | `$0.720` | `$3.500` | Code and engineering trade-off critique | `reverify before cost-sensitive use` |
| `openrouter/xiaomi/mimo-v2.5-pro` | `AVAILABLE` | `1048576` | `$0.435` | `$0.870` | Parallel alternative-angle review | `reverify before cost-sensitive use` |
| `openrouter/minimax/minimax-m2.7` | `AVAILABLE` | `204800` | `$0.240` | `$0.960` | Parallel alternative-angle review | `reverify before cost-sensitive use` |
| `openrouter/nvidia/nemotron-3-ultra-550b-a55b` | `AVAILABLE` | `1000000` | `$0.500` | `$2.200` | Parallel alternative-angle review | `reverify before cost-sensitive use` |

The catalog query does not supply a task-specific latency measurement. Treat
latency as `NOT_MEASURED` until the exact route and prompt are measured. Before
cost-sensitive use, rerun the public catalog query and verify the exact ID,
availability, context, and input/output prices. If an ID is missing, mark it
`UNAVAILABLE`; do not substitute a similarly named model.

DeepSeek's `xhigh` option is a deliberate exception for a narrow hard review,
not a default. Treat reasoning tokens as paid output. GPT-5.5 Pro receives a
compact, curated question rather than open-ended repository exploration. GLM,
MiniMax, MiMo, and Nemotron provide breadth only when parallel review has a
defined synthesis oracle.

## Price, Availability, And Latency Snapshot

The table is a dated observation, not product canon or a purchasing promise.
For any paid run, record the verification date, selected exact ID, visible
catalog prices, and whether latency was measured. Do not log raw prompts,
responses, secrets, or hidden reasoning to calculate cost. Use the
[provider-neutral harness](../orchestration/context-cost-harnesses.md) for
comparable telemetry and attribution.

## OpenCode And PowerShell Rules

OpenCode is an existing optional operator path, not a repository dependency.

- In PowerShell, invoke the CLI as `opencode.cmd`. Plain `opencode` may resolve
  to a blocked PowerShell script.
- Never invoke `E:/OpenCode/OpenCode.exe` as a CLI. It is the desktop Electron
  application.
- Use only read-only catalog/capability checks before a consult. Never print or
  inspect auth/config contents, request headers, bearer values, or secrets.
- If an exact model is missing, stop that lane. Do not silently reroute it.
- If inline Cyrillic is garbled, pass a UTF-8 file through a small existing
  helper instead of embedding a large PowerShell here-string.
- Ask for a concise final answer with a unique prefix. Extract only that final
  answer. Discard reasoning or `reasoning_details`; never retain hidden chain
  of thought in a handoff or artifact.

## Cache-Aware Packet Shape

Keep reusable material first and volatile material last:

```text
# STABLE PREFIX
reviewer role and Codex authority boundary
redacted POKROV canon needed for this task
stable rubric, skill constraints, and output contract

# CACHE BREAKPOINT

# DYNAMIC SUFFIX
current task and user steering
date and selected route
cwd, branch, status, and candidate identity
fresh targeted excerpts and relevant tool output
```

Do not move a date, run ID, Git state, or fresh excerpt into the stable prefix.
For a repeated or expensive packet, run the repository's static packet audit
described in the provider-neutral harness. A static pass does not prove remote
cache use, answer quality, latency, or final cost.

## SKILL PACKET

Give a compact task-specific taste or copy brief. Do not paste an entire skill
file unless the task is explicitly auditing that skill.

```text
SKILL PACKET:
- Surface type:
- Relevant local skills:
- Non-negotiable canon:
- Taste rules to enforce:
- Copy/tone rules to enforce:
- Anti-patterns to reject:
- What to ignore because it conflicts with this repository:
- Output format:
```

Skill packets constrain critique; they do not override POKROV canon,
accessibility, performance, release honesty, installed libraries, or Codex
judgment.

## Design Consult Pattern

1. Name the surface, user goal, and intended emotional effect.
2. Include only the relevant current screenshot or redacted code excerpt.
3. State hard canon, design tokens, accessibility limits, release truth, and
   the compact skill packet.
4. Request critique under named categories: hierarchy, trust, density, motion,
   localization, accessibility, and implementation risk.
5. Ask for two or three distinct directions only when trade-offs matter.
6. Require `Verdict`, `Top fixes`, `Keep`, `Avoid`, and `Implementation notes`.

The external answer is a review input. Codex checks current code and local
design authority before choosing or implementing any direction.

## Copy Consult Pattern

1. Name the surface, audience, scenario, emotional target, and directness.
2. Include the exact allowed facts and forbidden product, payment, store,
   signing, origin, or release claims.
3. Request one polished rewrite when intent is settled, or two or three
   genuinely distinct options when exploration is useful.
4. For roleplay, ask for user reaction and wording lessons, not invented facts.
5. Require `Best rewrite`, `Why it works`, `Risks`, and `Canon checks`.

Codex reconciles wording with shared copy/facts and the current owner before
editing a public surface. Accuracy wins over charm.

## Output Extraction And Local Synthesis

Retain only the requested final critique or rewrite. Remove hidden reasoning,
provider metadata, duplicated prompt text, and unsupported claims. Compare the
answer with the original oracle, current repository authority, tests, and
evidence. Synthesize locally; never copy an external answer directly into code
or canon.

Record the consult as advisory and state which suggestions were accepted,
rejected, or left unverified. If the output conflicts with authority, leaks
restricted data, or cannot be attributed to the exact prompt/model snapshot,
discard it and continue without it.
