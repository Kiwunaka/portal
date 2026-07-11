# Agent Context And Cost Harnesses

Last updated: 2026-07-11

This file owns provider-neutral rules for reusable context packets, redaction, usage telemetry, and cost/latency evaluation. It does not select models, vendors, operator tools, or prices.

## Applicability

Use this harness when work creates or changes a reusable prompt, provider route, prompt-heavy batch or evaluation, external consult path, or production prompt system. Ordinary code, ordinary docs, and one-off manual drafting do not need an empty harness block.

## Packet Shape

Keep stable, reusable content before run-specific content:

```text
# STABLE PREFIX
role and authority boundary
output contract
stable safety and canon excerpts
stable tools, rubric, and examples

# CACHE BREAKPOINT

# DYNAMIC SUFFIX
current task and steering
date, run id, and trace id
cwd, branch, status, and candidate identity
fresh file excerpts and tool output
```

Preserve stable-prefix order. Sort generated tool or rubric lists deterministically. Do not place dates, identifiers, current status, dirty paths, fresh excerpts, or tool results before the cache breakpoint.

## Static Packet Audit

Run the repository auditor before high-volume reuse or an expensive evaluation:

```powershell
python scripts/agent_context_packet_audit.py <packet.md>
```

For the platform context itself:

```powershell
python scripts/agent_context_packet_audit.py --platform-context-root .
```

The auditor checks packet shape and dynamic markers. It makes no network call and does not prove remote cache behavior, answer quality, latency, or price.

## Redaction Boundary

Packets, traces, and artifacts must not contain:

- secrets, credentials, tokens, private keys, auth headers, or raw configuration stores;
- raw customer data, personal email, session data, payment payloads, or private support conversations;
- subscription URLs, connection material, unredacted provider payloads, or hidden reasoning;
- broad repository dumps when targeted excerpts are enough.

Use placeholders or irreversible hashes only when they are necessary for correlation. Hashes must be coarse enough to avoid reconstructing sensitive values. Review exported packets as data leaving the repository boundary even when the receiver is automated.

## Provider-Neutral Telemetry

Record comparable measurements without coupling the contract to one API:

```json
{
  "route_label": "redacted-stable-label",
  "model_label": "opaque-versioned-label",
  "request_count": 0,
  "input_tokens": 0,
  "cache_read_tokens": 0,
  "cache_write_tokens": 0,
  "new_input_tokens": 0,
  "output_tokens": 0,
  "cache_hit_rate": null,
  "time_to_first_output_ms": null,
  "total_latency_ms": 0,
  "stable_prefix_hash": "short-non-sensitive-hash",
  "tools_hash": "short-non-sensitive-hash",
  "result": "pass | fail | blocked"
}
```

Map available usage fields into this shape. Keep unsupported measurements `null`; never fabricate zeros for unavailable telemetry. Store aggregate or per-run measurements only when the retention policy permits them. Do not log raw prompts or responses merely to compute cost.

`new_input_tokens` should be derived only when the source accounting is compatible. Document the formula and prevent negative values. A cache hit rate is meaningful only when the measured route exposes a compatible cache-read count.

## Evaluation Contour

Before claiming an improvement, define:

- baseline and candidate packet versions;
- stable-prefix hash and change reason;
- representative tasks and output oracle;
- warm-up treatment and sample size;
- token, cache, latency, quality, and failure measurements available;
- attribution for route or access failures;
- acceptable regression bounds and stop condition.

Compare equivalent tasks and candidate settings. Report missing telemetry and variance. A lower token count does not prove better quality; a faster response does not prove correct output; a static audit does not prove cache use.

## WO Contract

When the authoring-guide trigger fires, the optional WO block records:

- stable-prefix and dynamic-suffix contents;
- redaction review and export boundary;
- static audit command and result;
- available telemetry mapping;
- evaluation oracle and residual risk;
- ownership of route-dependent failures;
- retained aggregate evidence reference.

Keep task-specific routing preferences outside this provider-neutral owner. Do not add a dependency, gateway, vector store, loader, or service merely to satisfy this documentation contract.

## Completion

The harness is complete when the reusable packet passes the applicable static audit, prohibited data is absent, measurements are honestly mapped, the quality oracle runs or is explicitly blocked, and the handoff states residual cost, latency, cache, and attribution limits.
