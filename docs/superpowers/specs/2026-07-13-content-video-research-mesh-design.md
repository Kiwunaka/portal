# POKROV Content Research Mesh — Production Design

**Date:** 2026-07-13
**Status:** Owner-approved design; implementation has not started
**Scope:** Local `.content-video-ad` workspace, especially topic discovery, evidence collection, ranking, and the Research Inbox in Content Studio

## Purpose

Replace the current placeholder Trend Scout with a production research system that finds concrete topics, preserves evidence, explains its ranking, and returns three nearly production-ready topic packets:

- two safe production packets;
- one controlled AI-video experiment.

The system runs only when the owner clicks a button in Content Studio. It uses free discovery surfaces and the already approved OpenCode model gateway. It does not schedule background work, publish content, or start paid TTS, image, or video jobs.

This document defines intended behavior. Current code and retained scout runs remain the authority for what is implemented today.

## Audit Baseline

### What is already strong

The media-production half of the workspace is materially stronger than the research half:

- paid provider jobs are recorded and resumable;
- production episodes have machine gates for goals, success oracles, claims, legal review, duration, alignment, and visual density;
- evidence snapshots, final QC, publishing packs, and `run-state.json` already exist;
- Studio has a bounded command allowlist and a production queue;
- model and prompt audits reduce avoidable paid-generation mistakes;
- local verification passed on 2026-07-13:
  - `npm.cmd run typecheck` — PASS;
  - `npm.cmd test` — PASS, 32 tests;
  - `npm.cmd run scout:doctor` — PASS for installed extraction dependencies;
  - `npm.cmd run doctor` — PASS for Node, FFmpeg, FFprobe, and FAL credential presence.

### Critical research gaps

The current Scout does not fulfill the contract described by `AGENTS.md`, `config/content-series.yaml`, `docs/content-series-strategy.md`, and `prompts/agent-research.md`.

1. `configured_sources` returns configured source homepages, not concrete article or event candidates.
2. A normal `meme_news` run can return five configured homepages even though the contract requires 20 candidates.
3. `prompts/agent-research.md` is not invoked by the Scout implementation.
4. Every candidate in one lane receives the same configured default score. The retained DTF run scored the anti-bot page `29.8`.
5. There is no event clustering, cross-source corroboration, dynamic score rationale, selection confidence, or final `safe_production` / `experimental_ai_video` / `reserve` recommendation logic.
6. The generated claim is only “Scout found source candidate,” not a factual claim from the source.
7. Fetch risk is incorrectly used as a proxy for editorial and legal risk.
8. Anti-bot pages, empty bodies, missing dates, and broken encoding are not blocking content-quality failures.
9. The retained run at `runs/scout/20260629-000714/` contains:
   - `https://dtf.ru/` as the candidate rather than an article;
   - the anti-bot text “Вы, случайно, не робот?”;
   - corrupted Cyrillic in the report and draft YAML;
   - eight generic equal-duration scenes about the URL;
   - the same placeholder claim mapped to every scene.
10. Content Studio shows episodes, production runs, voice preview, materials, jobs, and logs, but no research inbox, Scout controls, source health, candidate pool, or packet review.
11. Scout tests prove mechanical artifact creation and the fixed `29.8` score. They do not prove topic quality, 20 unique candidates, recommendations, evidence coverage, or rejection of bad pages.
12. `trend-scout.eval.yaml` is non-blocking and is not sufficient evidence that the runtime satisfies its checks.

## Approved Product Decisions

The owner approved these decisions during brainstorming:

- architecture: **Research Mesh**;
- trigger: manual button in Content Studio only;
- output: 20 candidate pool, then two safe production packets and one AI-video experiment;
- topical perimeter: broad, including gaming, technology, AI, science, internet culture, politics, crime, and controversial current events;
- politics and crime require stronger evidence and mandatory manual approval;
- discovery cost: free sources only; no paid search API;
- POKROV remains a sponsor/banner layer and is not forced into ordinary topics;
- episode YAML generation is a separate explicit action after a topic packet is approved;
- paid TTS, image, and video generation remain outside Scout.

## Goals

1. Find concrete, current, source-backed topics rather than landing pages.
2. Preserve enough evidence to reproduce why a candidate was created and selected.
3. Produce a useful 20-candidate editorial pool without duplicate padding.
4. Return two safe topics and one factually safe experimental visual format.
5. Explain every score through evidence-backed field rationales.
6. Make source failures, partial coverage, contradictions, and uncertainty visible in Studio.
7. Turn owner approvals and rejections into retained steering data.
8. Keep the existing episode, evidence, paid-job, render, QC, and publishing boundaries intact.

## Non-Goals

- scheduled or recurring research;
- paid search providers;
- background notifications;
- autonomous publishing;
- automatic paid media generation;
- bypassing anti-bot, paywall, account, or platform controls;
- treating LLM output as factual evidence;
- guaranteeing virality or platform recommendations;
- rewriting the existing Remotion/media pipeline.

## System Architecture

```text
Content Studio: “Найти темы”
  -> Scout Orchestrator + run-state.json
    -> Discovery adapters
       -> RSS / Atom
       -> first-party/open APIs
       -> Google Trends RSS
       -> local SearXNG
       -> HTML / sitemap fallback
    -> SourceItem normalization
    -> Source content-quality gate
    -> URL/content deduplication
    -> Event clustering
    -> Evidence graph and claim mapping
    -> Editorial and legal risk gates
    -> OpenCode editorial enrichment and critique
    -> Dynamic trend score + confidence + selection score
    -> Diversity selector
       -> 20 candidates
       -> 2 safe production packets
       -> 1 AI-video experiment
    -> Studio Research Inbox
       -> approve / reject / retain brief
       -> separate “Создать episode YAML” action
```

Each component has one public responsibility and communicates through typed JSON-compatible contracts. A source adapter does not score topics. An LLM does not fetch or invent evidence. The selector does not weaken legal gates to fill three slots.

## Discovery Layer

### Free source surfaces

The initial registry should use source adapters, not a single generic webpage fetcher.

Verified or documented surfaces from the 2026-07-13 audit include:

- [Habr RSS documentation](https://habr.com/ru/docs/help/lenta/) — Habr documents RSS for site feeds, hubs, tags, comments, and search results. The local audit request timed out, so Habr health must remain a live runtime observation rather than a permanent PASS.
- [DTF all feed](https://dtf.ru/rss/all) — local audit returned HTTP 200 and `application/rss+xml`.
- [VC all feed](https://vc.ru/rss/all) — local audit returned HTTP 200 and `application/rss+xml`.
- [StopGame news feed](https://rss.stopgame.ru/rss_news.xml) — discovered from the site’s RSS `<link>` and returned HTTP 200.
- [Playground news feed](https://www.playground.ru/rss/news.xml) and [articles feed](https://www.playground.ru/rss/articles.xml) — discovered from the site’s RSS `<link>` elements and returned HTTP 200.
- [Google Trends RU feed](https://trends.google.com/trending/rss?geo=RU) — local audit returned HTTP 200 and XML.
- Steam store review and other first-party Steam surfaces already used by `src/research/steam.ts`.
- owner-provided local references and source URL lists.

The registry must also support configured official and established publisher feeds for politics, crime, law, science, business, entertainment, and global news. Those sources are discovery and evidence inputs, not an allowlist of truth.

### Local SearXNG

SearXNG remains a free local breadth adapter. It is not the sole source of evidence.

- If available, it runs configured query families and returns concrete result URLs.
- If unavailable, feed/API adapters continue and the run records degraded breadth.
- A missing SearXNG instance must never silently fall back to configured homepages.
- Search result snippets are discovery hints only. Claims require extracted source evidence.

### HTML and sitemap fallback

HTML or sitemap extraction is used when a source lacks a healthy structured feed. It remains read-only and respects the existing green/yellow/red risk contract.

The fallback must not use stealth, proxy, browser accounts, or paywall bypass by default. Any separately approved red-risk read-only extraction remains logged and cannot become the standard path.

## Source Adapter Contract

Every adapter returns normalized `SourceItem` records with at least:

```text
id
source_id
source_family
source_role_hint
canonical_url
title
published_at
discovered_at
language
author                 optional
raw_metrics            source-specific engagement values
text_excerpt
content_hash
snapshot_path
fetch_method
http_status            when available
content_type           when available
health_status
risk_profile
```

Adapters also return a source-health result even when they return no items. This separates “no relevant items” from “the source failed.”

## Content-Quality Gate

A `SourceItem` is rejected before clustering when it is any of the following:

- a configured homepage or section landing page instead of a concrete item;
- an anti-bot, login, consent-only, or access-denied page;
- empty or below the configured minimum useful body size;
- missing a canonical URL or title;
- missing `published_at` when the candidate is presented as current news;
- outside the lane’s freshness window without an explicit evergreen classification;
- affected by mojibake or an excessive replacement-character ratio;
- a duplicate URL or duplicate content hash;
- fetched with a blocking error;
- a raw search-result snippet with no extracted source page.

Rejected records remain in source-health and rejection artifacts for audit. They do not become candidates.

## Event Clustering And Deduplication

The system clusters multiple articles about the same event before scoring.

Clustering uses normalized canonical URLs, title similarity, named entities, time proximity, content hashes, and LLM-assisted comparison only when deterministic signals are inconclusive.

The cluster is the topic candidate boundary. One event should not occupy several positions in the pool because it appeared on several sites.

Default diversity constraints:

- no more than two candidates from one event cluster;
- the second candidate from a cluster must use a materially different format or editorial angle;
- one domain cannot dominate the 20-candidate pool;
- the final three packets must not all come from the same source family or series lane;
- when fewer than 20 valid clusters exist, mark the run `PARTIAL` instead of adding duplicates or weak filler.

## Evidence Graph

Every source-driven candidate contains explicit source roles:

- `discovery`: where the signal was found;
- `primary`: first-party statement, official document, original dataset, direct record, original review, or original source material;
- `independent`: a separate source that confirms or challenges the claim;
- `context`: background that is not used as direct proof.

Each factual claim contains:

```text
claim_id
normalized_claim
source_refs[]
evidence_excerpts[]
snapshot_hashes[]
source_roles[]
confidence
contradictions[]
unknowns[]
intended_narration_use
intended_visual_use
```

The evidence excerpt is short and bounded. Long source text is not copied into production artifacts.

### Minimum evidence rules

Normal source-driven topic:

- one strong primary/first-party source, or
- two genuinely independent sources.

Politics, crime, accusations, court matters, and controversial public events:

- one primary record, first-party statement, or authoritative original document;
- two independent confirmations or analyses;
- explicit wording that distinguishes allegation, charge, claim, ruling, conviction, correction, and confirmed fact;
- a current-status and date check;
- mandatory manual approval before episode creation.

An official statement proves that the statement exists. It does not automatically prove every assertion inside it. Contradictions remain visible.

Private-person accusations, minors, doxxing, unnecessary identifying information, and graphic material are rejected by default. The system does not turn real harm into a punchline merely because the topic is trending.

## OpenCode Editorial Layer

The LLM layer receives retained evidence packets. It does not browse independently inside the runtime design and may not add unreferenced facts.

Approved routing:

- `opencode-go/kimi-k2.6`: editorial angle, hook variants, causal story spine, punchline options, visual nouns, and format routing;
- `opencode-go/deepseek-v4-pro`: claim-to-evidence critique, contradiction check, safety review, and selection critique;
- `opencode-go/glm-5.1`: factual script writing only after owner approval and only from a fact packet;
- OpenRouter and new paid model IDs remain out of scope without explicit owner approval.

Requests use stable prompt prefixes, dynamic evidence suffixes, low reasoning effort, and JSON-only output. Only `message.content` is parsed. Reasoning details, raw provider payloads, headers, and secrets are not retained.

Invalid JSON or schema failures receive a small bounded retry. Exhausted retries produce `BLOCKED_EDITORIAL`; the runtime must not invent a packet from malformed output.

## Candidate And Packet Contracts

### Candidate

Every candidate includes:

- identity: title, cluster ID, slug, topic family;
- routing: `series.lane_id`, `format_id`, and why they fit;
- signal: timestamps, age, source families, engagement signals;
- fact packet: claims, evidence, contradictions, unknowns;
- editorial angle: hook, why now, why funny/interesting, story spine, twist;
- visual feasibility: proof frames, concrete visual nouns, continuity groups, expected visual-state count, banner fit;
- risk review: copyright, reused content, politics, crime, allegation, public/private person, minor, graphic content, synthetic-label requirement;
- production plan: model stack, cost band, first smoke, success oracle, stop conditions;
- score: numeric fields, rationales, evidence references, confidence, and selection result.

### Production packet

The final packet is the candidate plus a concise owner-review presentation. It is not an episode YAML and it does not contain paid media.

Two packet classes exist:

- `safe_production`: evidence, legal, visual, and cost-predictability gates passed;
- `ai_video_experiment`: the same evidence and legal gates passed, but one visual mechanic remains uncertain and has a cheap first smoke.

An experiment may carry production uncertainty. It may not carry unresolved factual or legal uncertainty.

## Scoring And Selection

The existing canonical formula remains unchanged:

```text
trend_score.total =
  freshness * 1.2
+ audience_heat * 1.4
+ absurdity * 1.2
+ evidence_strength * 1.5
+ visual_punch * 1.1
+ repeatability * 1.3
+ brand_nonintrusion * 1.0
+ legal_safety * 1.0
- production_cost * 0.8
```

Each value is calculated per candidate rather than copied from lane defaults. Every field stores a reason, evidence references, and confidence.

`trend_score.total` must still exactly match the formula. A separate candidate-only selection value controls ordering:

```text
selection_score =
  trend_score.total
  * evidence_confidence
  * coverage_confidence
  - configured_risk_penalties
```

Hard gates run before selection score. A blocked candidate cannot be rescued by high trendiness.

Hard gates:

1. source content quality;
2. evidence coverage;
3. legal/editorial safety;
4. visual feasibility;
5. valid series/format routing;
6. known production cost band and first smoke.

`brand_nonintrusion` rewards topics where the POKROV banner can coexist without hijacking the story. It never turns ordinary content into VPN education.

## Research Run State

Scout runs receive the same durable operating-loop discipline as production runs.

Phases:

```text
idle
discovering
extracting
normalizing
clustering
verifying
enriching
ranking
ready | partial | failed | cancelled
```

`runs/scout/<run-id>/run-state.json` includes:

- goal and research success oracle;
- current phase and counts;
- per-source health;
- inspection surfaces;
- validation ownership;
- LLM job summaries without secrets;
- steering log;
- blockers;
- next action;
- cancellation state;
- timestamps and safe telemetry.

## Artifact Layout

```text
runs/scout/<run-id>/
  run-state.json
  source-health.json
  source-items/
  snapshots/
  rejections/
  clusters/
  evidence/
  candidates/
  packets/
    safe-01.json
    safe-02.json
    experiment-01.json
  shortlist.json
  scout-report.json
  scout-report.md
  decisions.jsonl
```

Snapshots are sanitized, bounded, and hashed. They must not contain secrets, raw provider headers, private customer data, subscription URLs, or private source material.

## Content Studio Research Inbox

Studio gains a `Research Inbox` navigation item and a `Найти темы` button.

### Run view

Show:

- current phase and progress;
- source health and degraded adapters;
- discovered item, cluster, valid candidate, and packet counts;
- cancellation control;
- explicit `no paid media` status.

### Packet view

Show three featured cards:

- `SAFE #1`;
- `SAFE #2`;
- `AI EXPERIMENT`.

Each card opens:

- hook and story spine;
- claim map and evidence graph;
- source links and local snapshot paths;
- score breakdown and rationales;
- contradictions and unknowns;
- visual-state plan;
- risk flags and required approvals;
- expected cost band and first smoke;
- selection explanation.

### Candidate pool

The full 20-candidate table supports filtering by source family, topic family, series lane, risk, evidence state, and format.

### Owner actions

- `Approve packet`: records the approval and writes a stable topic brief;
- `Reject`: requires a short reason and appends it to `decisions.jsonl` and run steering;
- `Reserve`: retains a packet without advancing;
- `Создать episode YAML`: separate explicit action available only after approval;
- no packet action submits paid TTS, image, or video jobs.

## Error Handling

Required statuses:

- `SOURCE_DEGRADED`: one source failed; other adapters continue;
- `REJECTED_CONTENT`: homepage, anti-bot, mojibake, empty body, missing current date, or other content-quality failure;
- `BLOCKED_EVIDENCE`: minimum evidence rule not met;
- `BLOCKED_CONFLICT`: material unresolved contradiction;
- `BLOCKED_LEGAL`: allegation, private-person, minor, graphic, copyright, or platform risk requires rejection or authority;
- `BLOCKED_EDITORIAL`: OpenCode output remains invalid after bounded retry;
- `PARTIAL`: fewer than 20 valid candidates or insufficient source-family coverage;
- `FAILED`: no useful pool can be produced;
- `CANCELLED`: owner cancelled the run.

A source failure does not fail the whole run unless the remaining coverage cannot satisfy the oracle. A partial run does not claim success.

## Testing Strategy

### Unit and fixture tests

- parse representative RSS, Atom, API, HTML, and sitemap fixtures;
- canonicalize URLs and timestamps;
- detect mojibake, anti-bot pages, homepages, empty content, and duplicate hashes;
- cluster duplicate event coverage;
- build claim-to-evidence mappings;
- enforce normal and politics/crime evidence gates;
- calculate the exact canonical trend score;
- calculate selection confidence and penalties;
- enforce diversity constraints;
- parse mocked OpenCode JSON and bounded retry behavior.

### Integration tests

- deterministic mock run from at least 60 source items to 20 valid candidates and three packets;
- partial run when fewer than 20 valid clusters exist;
- one degraded adapter while the rest complete;
- contradictory sources block selection;
- AI experiment passes evidence/legal gates but retains a visual smoke requirement;
- approval writes a topic brief but creates no provider job;
- episode YAML creation remains a separate action.

### Studio tests

- list research runs and source health;
- open packet details and evidence paths;
- approve, reject with reason, reserve, cancel;
- prevent path traversal and arbitrary command execution;
- verify research actions do not submit paid media.

### Live health checks

Live network health is not part of deterministic unit tests. Add a separate read-only command such as:

```text
npm run scout:health
```

It reports current feed/search/extraction status, HTTP/content type when available, and a redacted error preview. It does not convert a historical PASS into current proof.

### Required verification commands

```text
npm.cmd run typecheck
npm.cmd test
npm.cmd run scout:doctor
npm.cmd run scout:health
npm.cmd run scout -- --lane topics
npm.cmd run secrets:scan
git diff --check
```

`evals/trend-scout.eval.yaml` should become a blocking code-backed contract rather than a non-blocking prose checklist.

## Success Oracle

The implementation is successful when an owner-triggered research run can prove all of the following:

1. It returns 20 unique concrete-topic candidates when enough valid clusters exist.
2. The pool covers at least four configured source families, or the run is honestly marked `PARTIAL`.
3. No homepage, anti-bot page, empty extraction, or corrupted-Cyrillic item appears in the valid pool.
4. Each candidate has a canonical URL, timestamps appropriate to its classification, series/format routing, evidence state, score rationale, risk state, and visual feasibility.
5. The top three contain two safe production packets and one AI-video experiment.
6. All top-three claims map to retained evidence excerpts and snapshot hashes.
7. Politics/crime/accusation packets satisfy the enhanced evidence rule and remain manual-approval only.
8. The AI-video experiment has no unresolved factual/legal weakness and names the cheapest useful smoke.
9. Studio explains why each packet was selected and exposes degraded sources and blockers.
10. Approving a packet writes a brief but starts no paid media generation.
11. The run can be reproduced and audited from its retained artifacts without relying on chat memory.

Not enough:

- a Scout command exits with code zero;
- 20 rows exist but include duplicates or landing pages;
- an LLM returns a plausible list without retained evidence;
- the same default score is copied to every candidate;
- three packets exist but source, legal, or visual gates were skipped;
- a Studio page renders while its actions bypass the contracts above.

## Documentation Impact

Implementation will require scoped updates inside the local `.content-video-ad` workspace:

- `AGENTS.md` research rules only if behavior or owner contract changes;
- `config/scout.yaml` source adapters, health, query families, and selector rules;
- `config/content-series.yaml` only for score/selection schema changes;
- `docs/content-series-strategy.md` for current research and selection behavior;
- `docs/pipeline.md` for the Scout-to-episode approval boundary;
- `docs/video-agent-operating-loop.md` for Scout `run-state.json`;
- `README.md` for Studio and commands;
- `evals/trend-scout.eval.yaml` for blocking acceptance.

Do not duplicate current behavior into root `AGENTS.md`. The local `.content-video-ad` directory is intentionally ignored by the platform repository and must not be force-added wholesale. This root design spec is the tracked review artifact.

## Implementation Boundary

This design does not authorize implementation, paid provider calls, deployment, or publishing. The next step after spec review and owner review is a separate implementation plan.
