# POKROV Content Research Mesh — Production Design

**Date:** 2026-07-13
**Status:** Owner-approved design; implementation has not started
**Scope:** Local `.content-video-ad` workspace, especially topic discovery, evidence collection, ranking, and the Research Inbox in Content Studio

## Purpose

Replace the current placeholder Trend Scout with a production research system that finds concrete topics, preserves evidence, explains its ranking, and returns three nearly production-ready topic packets:

- two safe production packets;
- one controlled AI-video experiment.

The only user-facing trigger is a button in Content Studio. The same orchestrator remains callable through a manual CLI for tests and operator diagnostics; neither entry point schedules background work. The system uses free discovery surfaces and the already approved OpenCode model gateway. It does not publish content or start paid TTS, image, or video jobs.

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
- user-facing trigger: manual button in Content Studio only;
- internal trigger: the existing Scout CLI may invoke the same orchestrator for tests and operator diagnostics, but never from a scheduler;
- output: 20 candidate pool, then two safe production packets and one AI-video experiment;
- topical perimeter: broad, including gaming, technology, AI, science, internet culture, politics, crime, and controversial current events;
- politics and crime require stronger evidence and mandatory manual approval;
- discovery cost: free sources only; no paid search API;
- POKROV remains a sponsor/banner layer and is not forced into ordinary topics;
- episode YAML generation is a separate explicit action after a topic packet is approved;
- paid TTS, image, and video generation remain outside Scout.

This owner decision intentionally supersedes the current `1 safe + 1 experiment + 1 reserve` Scout contract. Implementation must update all current local owners in the same change:

```yaml
trend_scout:
  choose:
    safe_production: 2
    experimental_ai_video: 1
    reserve_candidate: 0
```

The required owner updates are `.content-video-ad/AGENTS.md`, `config/content-series.yaml`, `docs/content-series-strategy.md`, `docs/pipeline.md`, `prompts/agent-research.md`, and `evals/trend-scout.eval.yaml`. Until those changes land and pass together, current runtime behavior remains authoritative and the new selector must not be called implemented.

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
- [BBC Russian](https://feeds.bbci.co.uk/russian/rss.xml), [TASS](https://tass.ru/rss/v2.xml), [RIA](https://ria.ru/export/rss2/archive/index.xml), [RBC](https://rssexport.rbc.ru/rbcnews/news/30/full.rss), [Guardian World](https://www.theguardian.com/world/rss), and [DW Russian](https://rss.dw.com/rdf/rss-ru-all) feeds — local audit returned HTTP 200 XML/RSS for each.
- Steam store review and other first-party Steam surfaces already used by `src/research/steam.ts`.
- owner-provided local references and source URL lists.

The registry must also support configured official and established publisher feeds for politics, crime, law, science, business, entertainment, and global news. Those sources are discovery and evidence inputs, not an allowlist of truth.

### V1 discovery groups

`config/scout.yaml` defines these exact groups and minimum health requirements:

| Group | Requirement | Initial adapters |
| --- | --- | --- |
| `ru_core` | required, at least 3 healthy | `dtf_all`, `vc_all`, `habr_current`, `stopgame_news`, `playground_news` |
| `broad_news` | required, at least 3 healthy | `bbc_ru`, `tass`, `ria`, `rbc`, `guardian_world`, `dw_ru` |
| `trend_signal` | required, at least 1 healthy | `google_trends_ru`, configured Steam signal adapters |
| `owner_local` | optional | configured local reference folders and owner URL lists |
| `official_records` | conditional per candidate | registry lookups chosen by entity/jurisdiction; no global health claim |

The 2026-07-13 audit observed HTTP 200 XML/RSS responses from the configured URLs for BBC Russian, TASS, RIA, RBC, Guardian World, and DW Russian. That observation is not permanent health proof; each run records fresh status.

A required group is `healthy` when it meets its minimum healthy-adapter count, `degraded` when at least one adapter works but the minimum is missed, and `blocked` when zero adapters work. Lifecycle `ready` requires every required group to be healthy. Any degraded/blocked required group makes an otherwise useful run `partial`. A run fails for discovery-group outage only when all three required groups are blocked.

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
schema_version
id
source_id
source_family
publisher_group_id
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
adapter_id
adapter_config_hash
checked_at
http_status            when available
content_type           when available
health_status
risk_profile
```

Adapters also return a versioned source-health result even when they return no items. The health record includes `checked_at`, adapter identity, adapter/config hash, observed status, item count, latency, and a redacted error preview. This separates “no relevant items” from “the source failed” and prevents historical health from looking current.

`source_family` and `publisher_group_id` are configured registry values, not LLM guesses. V1 source families are:

```text
community_ru
gaming_press_ru
tech_press_ru
trend_signal
first_party_platform
official_record
international_press
owner_local
```

New families require a config/schema update and fixture coverage. `publisher_group_id` groups domains under common editorial ownership and is used to prevent syndicated or commonly controlled sources from counting as independent confirmations.

Concrete results from SearXNG or direct extraction may introduce an unregistered domain. Such an item is normalized as:

```text
source_family = unregistered
publisher_group_id = quarantine:<registrable-domain>
registration_status = quarantined
```

Quarantined items may remain as discovery hints and produce `source-onboarding/<domain>.json`, but they do not count as evidence, independent confirmation, source-family coverage, or one of the 20 valid candidates. Registration requires an explicit config change that assigns source family, publisher group, risk profile, extraction policy, and fixtures. The running Scout never auto-promotes a domain.

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

V1 thresholds live in `config/scout.yaml`, are versioned with the run, and have these defaults:

```yaml
quality:
  min_body_chars:
    article_or_news: 400
    official_notice: 160
    steam_review: 40
  max_replacement_char_ratio: 0.002
  max_redirects: 5
  max_response_bytes: 1500000
freshness:
  breaking_hours: 72
  current_days: 7
  evergreen_trigger_days: 30
diversity:
  max_candidates_per_registered_domain: 5
  max_candidates_per_source_family: 8
  ready_min_source_families: 4
```

A feed title or snippet that does not meet the appropriate body threshold must be followed to the concrete item and extracted; the snippet alone is not evidence. `breaking` covers items at most 72 hours old, `current` covers items at most seven days old, and `evergreen` requires a separate current trigger no older than 30 days. Missing or unclassifiable dates block current-news classification.

The replacement-character ratio is the count of Unicode replacement characters divided by normalized text length. Known mojibake signatures may add a rejection reason, but must be fixture-tested before becoming blocking.

## Event Clustering And Deduplication

The system clusters multiple articles about the same event before scoring.

Clustering uses normalized canonical URLs, title similarity, named entities, time proximity, content hashes, and LLM-assisted comparison only when deterministic signals are inconclusive.

The cluster is the topic candidate and uniqueness boundary. One event cluster produces exactly one candidate in the 20-candidate pool. Alternative hooks or formats live inside that candidate and do not consume another pool slot.

Default diversity constraints:

- exactly one candidate per event cluster;
- one domain cannot dominate the 20-candidate pool;
- the final three packets must not all come from the same source family or series lane;
- when fewer than 20 valid clusters exist, mark lifecycle status `partial` instead of adding duplicates or weak filler.

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

Definitions used by the gate:

- **strong primary:** the original review, dataset, filing, recording, first-party release, direct record, or document held by the event actor or record custodian, with a retained snapshot and date;
- **authoritative original:** a source that is the custodian of a specific record, such as a court docket, regulator notice, company filing, original dataset, or platform record; this describes provenance, not neutrality or truthfulness;
- **genuinely independent:** a source with different editorial control and `publisher_group_id`, non-syndicated body text, and reporting that is not merely a rewrite of the same press release;
- **material contradiction:** a disagreement that changes the actor, action, date, magnitude, outcome, legal status, or the truth of the hook. It blocks selection unless the packet is explicitly about the dispute and represents both sides with separate claims.

A first-party or official statement proves that the statement or document exists. Assertions inside it about other actors, causes, outcomes, or contested events require independent confirmation. Shared ownership, syndicated copy, substantially identical text, and multiple domains repeating one press release do not count as independence.

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

Private-person accusations, minors, doxxing, unnecessary identifying information, and graphic material are rejected by default. The system does not turn real harm into a punchline merely because the topic is trending.

## Verification Feedback Loop

Evidence gaps are closed by an explicit bounded loop rather than by allowing the LLM to browse freely.

1. `ClaimPlanner` extracts proposed claims and missing evidence roles from the normalized cluster. Kimi may suggest wording and query terms, but its output is advisory.
2. `VerificationQueryBuilder` deterministically combines entities, dates, claim terms, and required source roles into queries.
3. `DiscoveryCoordinator` re-invokes only eligible adapters: local SearXNG, configured feed/search adapters, official-source registry lookups, and direct HTTP extraction for returned concrete URLs.
4. `ProvenanceResolver` classifies source role and independence from registry ownership, canonical domain, byline, content similarity, and syndication markers.
5. `EvidenceGate` recomputes claim coverage, contradictions, and unknowns.
6. The loop stops after two verification rounds or the configured per-cluster query budget of 12, whichever comes first. Remaining gaps become blockers; the system does not keep searching indefinitely.

Final ownership is explicit:

- `EvidenceGate` owns evidence eligibility;
- `RiskEngine` owns rule-based legal/editorial flags and hard blocks; LLM risk critique is advisory;
- `FormatRouter` maps candidate features to the configured series/format registry; LLM suggestions must validate against that registry;
- `ScoreEngine` owns numeric values, confidence, penalties, and exact formula arithmetic;
- `Selector` owns diversity and final packet roles only after all upstream gates pass.

## Versioned Risk Policy

`config/scout.yaml -> risk_policy.version: 1` defines rule IDs, flags, severity, and action. `RiskEngine` stores every matched rule ID/version with the candidate. LLM critique may add a flag for rule evaluation but can never clear or downgrade a rule match.

V1 flags and actions are:

| Flag | Derived action |
| --- | --- |
| `politics`, `crime`, `court` | require enhanced evidence, enhanced approval, and a current-status check |
| `accusation_public_figure` | enhanced evidence/approval; wording must preserve allegation/charge/ruling status |
| `public_figure` | no automatic block; combine with politics/crime/accusation and identity/likeness rules to derive the action |
| `accusation_private_person` | hard block by default |
| `private_person` | enhanced review; identifying detail must be necessary and public-interest justified |
| `minor_identifiable` | hard block by default |
| `minor_nonidentifying` | enhanced review plus public-interest justification |
| `graphic_explicit` | hard block |
| `graphic_implied` | enhanced review and a no-explicit-visual constraint |
| `copyright_low`, `reused_content_low` | eligible with retained source/attribution plan |
| `copyright_medium`, `reused_content_medium` | `legal_safety <= 3`; not eligible for top three until the rights plan changes |
| `copyright_high`, `reused_content_high` | hard block |

`enhanced_review_required` is a derived field set when any non-blocking enhanced rule matches. A hard-block rule sets `BLOCKED_LEGAL` regardless of score. Synthetic-media disclosure is also rule-derived: photoreal reconstruction of a real public event/person or any platform-required synthetic disclosure sets `synthetic_media_label_needed: true`. Each packet retains `risk_policy_version`, matched rules, derived actions, and rationale.

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

V1 uses these 0–5 rubrics. A value outside the rubric is a schema error.

| Field | Deterministic rubric |
| --- | --- |
| `freshness` | `5` ≤24h; `4` >24–72h; `3` >72h–7d; `2` evergreen/current topic with a trigger ≤7d; `1` evergreen with a trigger >7–30d; `0` missing/outside policy. |
| `audience_heat` | `5` ≥90th native-metric percentile plus a second source family, or ≥3 independent trend signals; `4` ≥75th percentile or 2 signals; `3` ≥50th percentile or 1 strong signal; `2` measured below median; `1` coverage without comparable metrics; `0` no heat evidence. Percentiles are computed per adapter/run and retained. |
| `absurdity` | `5` the verified mechanism is inherently surprising and explainable in one sentence; `4` strong incongruity with little setup; `3` useful twist after setup; `2` angle depends heavily on writing; `1` weak novelty; `0` no honest absurdity. Kimi proposes, DeepSeek critiques, `ScoreEngine` stores both rationales. |
| `evidence_strength` | `5` primary + 2 independent; `4` primary + 1 independent or 3 independent; `3` 2 independent; `2` single primary; `1` single secondary/discovery; `0` none. Enhanced-risk topics require the `5` pattern regardless of numeric total. |
| `visual_punch` | Default news/facts profile: `5` ≥16 concrete states including proof and continuity; `4` ≥12; `3` ≥8; `2` ≥5; `1` <5; `0` no viable plan. Other formats define equivalent thresholds in their registered profile and must be fixture-tested. |
| `repeatability` | `5` approved lane with ≥3 distinct current clusters; `4` approved lane with ≥2; `3` under-study/owner-test lane with ≥2; `2` one credible follow-up; `1` one-off; `0` no valid lane. |
| `brand_nonintrusion` | `5` banner fits without crop or story change; `4` minor layout adjustment; `3` proof/layout repair required; `2` banner competes with the key evidence; `1` topic must be bent toward POKROV; `0` incompatible. |
| `legal_safety` | `5` no material flags; `4` enhanced manual approval after evidence lock; `3` controllable medium risk but not top-three eligible; `2` high risk; `1` likely harmful/noncompliant; `0` prohibited. |
| `production_cost` | `0` source-only/existing assets; `1` ≤4 generated assets; `2` 5–12; `3` 13–22; `4` >22 or required motion bakeoff; `5` multi-model fragile work without a bounded first smoke. |

### V1 visual scoring profiles

Every topic-selectable V1 format has a versioned visual profile. Score `2` means one required mechanic is missing, `1` means the plan is generic or misses two or more mechanics, and `0` means infeasible. Scores `3–5` are format-specific:

| Format | `5` | `4` | `3` minimum viable |
| --- | --- | --- | --- |
| `generated_news_fact_story` | ≥16 concrete states with proof and continuity | 12–15 states with proof | 8–11 states with proof |
| `steam_review_readout` | exact real crop, moving support, ≥3 semantic support beats, banner-safe | exact crop, moving support, 2 beats | exact crop and one valid moving support loop |
| `patch_notes_therapy` | primary patch-note proof, 5 story beats, ≥8 states | proof, 4 beats, ≥6 states | proof and ≥4 concrete states |
| `steam_stats_anomaly` | first-party chart/API proof, 3 comparisons, ≥8 states | proof, 2 comparisons, ≥6 states | proof, 1 comparison, ≥4 states |
| `ai_remaster_visual` | same-subject pair, controlled reveal, ≥3 comparison details | same-subject pair, reveal, ≥1 detail | same-subject pair and basic reveal |
| `tier_list_absurdity` | ≥5 evidence-backed items and explicit ranking criteria | 4 items and criteria | 3 items and criteria |
| `kira_dance` | approved donor, complete dance audit/contact-sheet feasibility, camera/floor/body parity | approved donor and audit with only a noncritical gap | donor provenance plus feasible 4s smoke; full audit still pending |
| `kira_story` | one continuity master, 5–6 explicit motion beats, bounded clip plan | master and 4 motion beats | master, 3 motion beats, one bounded smoke |

`full_video_parts` is excluded from the topic selector because it is owner-provided source-serial work. Under-study formats are also excluded until their scoring profile and fixtures are explicitly added. Profile identity/version is retained with every candidate.

All metric inputs, state counts, and rubric reasons are retained in `score_rationale`. Editorial rubric fields are never accepted from one model pass without the configured critique pass.

Only `absurdity` uses a subjective editorial score in V1. Kimi proposes a 0–5 value and rationale from the locked evidence packet; DeepSeek independently returns `accept` or a counter-score. If the scores differ by at most one, `ScoreEngine` uses the lower value. If they differ by more than one, one reconciliation pass receives both rationales and the same evidence. A remaining difference greater than one emits `UNRESOLVED_EDITORIAL_SCORE`, and the candidate does not count toward the valid 20. Freshness, heat, evidence, visual profile, repeatability, brand fit, legal safety, and cost are computed by rule engines from retained inputs; LLM output cannot directly set those numeric values.

`trend_score.total` must still exactly match the formula. A separate candidate-only selection value controls ordering:

```text
selection_score =
  trend_score.total
  * evidence_confidence
  * coverage_confidence
  - configured_risk_penalties
```

Confidence is deterministic:

| Evidence shape | `evidence_confidence` |
| --- | ---: |
| primary + 2 independent, no material contradiction | `1.00` |
| primary + 1 independent | `0.90` |
| 2 independent | `0.80` |
| single primary, normal-risk pool only | `0.65` |
| below minimum or material contradiction | `0.00` |

`coverage_confidence = min(1, qualified_evidence_source_count / target_source_count)`, where the target is `2` for normal topics and `3` for enhanced-risk topics. Sources sharing a `publisher_group_id` count once.

Configured non-blocking penalties are:

```text
ENHANCED_MANUAL_APPROVAL       2
MINOR_NON_MATERIAL_CONFLICT    2
SOURCE_RIGHTS_REVIEW           1
VISUAL_SMOKE_REQUIRED          1   # experiment role only
```

Material conflicts, high rights risk, missing evidence, and harmful subject treatment are hard blocks and are not converted into numeric penalties.

Hard gates run before selection score. A blocked candidate cannot be rescued by high trendiness.

Hard gates:

1. source content quality is `PASS`;
2. a valid pool candidate has `evidence_confidence >= 0.65`; enhanced-risk candidates require `1.00`;
3. a top-three packet requires `evidence_confidence >= 0.80`, `legal_safety >= 4`, and no material contradiction;
4. a top-three packet requires `brand_nonintrusion >= 4`;
5. safe packets require `visual_punch >= 3`; experiments require `visual_punch >= 4` plus a bounded first smoke;
6. copyright/reuse risk is not `high`;
7. series and format IDs exist in the current registry;
8. production cost band and first smoke are known.

`brand_nonintrusion` rewards topics where the POKROV banner can coexist without hijacking the story. It never turns ordinary content into VPN education.

## Research Run State

Scout runs receive the same durable operating-loop discipline as production runs.

State uses three orthogonal fields:

- `phase`: current lowercase work phase;
- `status`: lowercase lifecycle state;
- `issues[]`: uppercase machine-readable issue codes.

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
complete
```

Statuses:

```text
queued | running | ready | partial | failed | cancelled
```

Terminal semantics are exact:

- `ready`: all three required discovery groups are healthy, exactly 20 valid event-cluster candidates cover at least four source families, and the selector produced two eligible safe packets plus one eligible AI-video experiment;
- `partial`: at least one valid candidate exists, but any `ready` cardinality or coverage condition is missing, including 20 candidates with fewer than two safe packets or no eligible experiment;
- `failed`: zero valid candidates, a fatal integrity/schema error prevents trustworthy artifacts, or all required discovery groups are unavailable;
- `cancelled`: the operator won the terminal-state transition before the final report was atomically committed.

Partial runs expose every individually eligible packet with a `run_status: partial` warning. An individually eligible packet may still be reviewed and approved; the run itself must not be described as successful. Missing packet roles are left empty and receive explicit reasons. The selector never fabricates a role to satisfy cardinality.

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

All JSON contracts contain `schema_version`. Run state also records `config_hash`, `adapter_set_hash`, and `parent_run_id` when a retry derives from an older run.

### Cancellation, timeout, and restart semantics

- queued cancellation removes the job from the queue and writes terminal `cancelled` state;
- running cancellation signals one shared `AbortController`, stops scheduling new adapter or LLM work, aborts fetches, and terminates an OpenCode subprocess after a five-second grace period;
- adapter timeout defaults to 30 seconds per request; OpenCode timeout defaults to 120 seconds per call; both are configurable and retained in the run config snapshot;
- terminal transitions use compare-and-set semantics and are immutable. `ready` or `partial` wins only after the final report is atomically renamed into place; otherwise a concurrent cancellation wins;
- partial artifacts already written remain inspectable but are never relabeled as completed output;
- on Studio restart, orphaned `running` runs become `failed` with issue code `INTERRUPTED`;
- `Retry` creates a new run with `parent_run_id`, may reuse immutable snapshot/content-hash artifacts, and never overwrites the old run.

## Artifact Layout

```text
runs/scout/<run-id>/
  run-state.json
  source-health.json
  source-items/
  source-onboarding/
  snapshots/
  rejections/
  clusters/
  evidence/
  candidates/
  packets/
    safe-01.json
    safe-02.json
    experiment-01.json
  topic-briefs/
    index.json
    <packet-id>.<brief-id>.v1.json
  shortlist.json
  scout-report.json
  scout-report.md
  decisions.jsonl
```

Packet filenames are role slots, not promises. A `partial` run writes only roles that have eligible packets and records missing roles in `shortlist.json`; it does not create placeholder packet files.

Snapshots are sanitized, bounded, and hashed. They must not contain secrets, raw provider headers, private customer data, subscription URLs, or private source material.

Owner-local sources use a separate visibility contract:

```text
source_visibility = private_owner_local
local_ref_id
allowlisted_realpath_root_id
content_hash
owner_paraphrase          optional
excerpt_redacted = true
```

Raw private material is never copied into `snapshots/`, reports, packet JSON, prompts, or publishing output. Persisted evidence uses hash/pointer-only plus an optional owner-authored paraphrase; it does not store a source excerpt. Studio may open the original on demand only through the allowlisted realpath boundary, labels it private, and never exposes it through a shareable report route. OpenCode receives no raw private material by default. Private local evidence cannot support a public factual claim without qualifying public confirmation; it may support private production mechanics such as an owner-provided motion reference.

An approved topic brief contains:

```text
schema_version
brief_id
packet_id
packet_revision_hash
evidence_revision_hash
approval_ids[]
generated_at
locked_claims[]
series_and_format
editorial_angle
visual_plan
source_refs[]
trend_score
```

`brief_id` is the first 32 hexadecimal characters of SHA-256 over `packet_id + packet_revision_hash + evidence_revision_hash + sorted approval_ids`. That same tuple is the idempotency key. Repeating approval for the same revisions returns the same filename and content. `index.json` maps packet/revision tuples to brief IDs and identifies the latest eligible revision. Any packet, evidence, wording, or approval revision produces a new brief ID; old files and index entries remain retained.

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

- `Approve editorial`: records the normal owner approval against packet and evidence revision hashes;
- `Approve enhanced-risk wording`: separate required action for politics, crime, accusation, court, and other `enhanced_review_required` packets;
- `Reject`: requires a short reason and appends it to `decisions.jsonl` and run steering;
- `Reserve`: retains a packet without advancing;
- `Создать episode YAML`: separate explicit action available only after approval;
- no packet action submits paid TTS, image, or video jobs.

Approvals are independent tracks, not one mutually exclusive enum:

```yaml
approval:
  editorial: pending | approved | rejected | stale
  enhanced: not_required | pending | approved | rejected | stale
  derived: pending | eligible | rejected | stale
```

Transition rules:

1. a new normal packet starts `editorial=pending`, `enhanced=not_required`;
2. a new enhanced-risk packet starts `editorial=pending`, `enhanced=pending`;
3. editorial rejection makes `derived=rejected` for that packet revision;
4. enhanced approval is accepted only after editorial approval and after the reviewer confirms locked wording, evidence revision, and current status;
5. any packet/evidence/wording revision makes every previous approval `stale`;
6. `derived=eligible` only when editorial is `approved` and enhanced is either `not_required` or `approved`;
7. rejected and stale revisions remain retained and cannot create a brief.

The enhanced approval record includes owner identity, timestamp, packet revision hash, evidence revision hash, wording checksum, and `current_status_checked_at`. `enhanced_approval_ttl_hours` defaults to `12`. Episode creation after that window changes enhanced state to `stale` and requires a new current-status check and approval. Topic-brief creation and episode YAML creation are blocked until derived state is `eligible`.

`Создать episode YAML` accepts only a current approved topic brief. It:

1. invokes the approved fact-packet script route only after approval;
2. writes `content/episode.<slug>.yaml` with `brief_ref`, locked `claim_map`, source refs, evidence/approval revision hashes, trend score, legal review, and visual plan;
3. validates the resulting episode contract;
4. submits no paid provider job;
5. refuses to overwrite an existing output unless the owner supplies a new slug/version explicitly.

## Studio And Extraction Security Boundary

V1 Content Studio is a local operator surface, not a network service.

- bind to `127.0.0.1` by default;
- refuse non-loopback `--host` in V1; remote Studio access is out of scope;
- accept mutating API requests only from the exact configured Origin and with an in-memory CSRF token injected into the page and sent through `X-POKROV-Studio-CSRF`;
- cap JSON request bodies at 64 KiB and reject unsupported content types;
- keep the command allowlist; no request field becomes a shell command or arbitrary argument vector;
- serve files only from allowlisted real paths under `runs/scout/`, `content/`, and explicitly approved generated preview roots;
- resolve `realpath` for both root and target and reject symlink, junction, or reparse-point escape;
- allowlist served extensions and never derive a local file path from an untrusted source URL;
- render source titles, excerpts, URLs, and errors through `textContent` or context-aware escaping, never raw `innerHTML`;
- ship a restrictive CSP. Inline scripts/styles require per-response nonces rather than broad `unsafe-inline`.

Extraction has a separate SSRF boundary:

- accept only `http:` and `https:` for remote sources;
- reject URL credentials, non-canonical hosts, loopback, private, link-local, multicast, and cloud-metadata address ranges after DNS resolution;
- revalidate every redirect target and stop after five redirects;
- enforce configured timeouts and the 1.5 MB response cap;
- the only loopback HTTP exception is the exact configured SearXNG base URL, used solely by its adapter and never accepted from a request payload;
- `file:` is allowed only for configured owner-local adapters whose real paths stay inside allowlisted reference roots.

## Error Handling

Required issue codes (not lifecycle statuses):

- `SOURCE_DEGRADED`: one source failed; other adapters continue;
- `SOURCE_GROUP_DEGRADED`: a required discovery group missed its minimum healthy-adapter count;
- `REJECTED_CONTENT`: homepage, anti-bot, mojibake, empty body, missing current date, or other content-quality failure;
- `BLOCKED_EVIDENCE`: minimum evidence rule not met;
- `BLOCKED_CONFLICT`: material unresolved contradiction;
- `BLOCKED_LEGAL`: allegation, private-person, minor, graphic, copyright, or platform risk requires rejection or authority;
- `BLOCKED_EDITORIAL`: OpenCode output remains invalid after bounded retry;
- `UNRESOLVED_EDITORIAL_SCORE`: Kimi and DeepSeek still differ by more than one point after reconciliation;
- `INSUFFICIENT_POOL`: fewer than 20 valid event clusters;
- `INSUFFICIENT_COVERAGE`: fewer than four source families;
- `MISSING_SAFE_ROLE`: fewer than two eligible safe packets;
- `MISSING_EXPERIMENT_ROLE`: no eligible AI-video experiment;
- `INTERRUPTED`: process/server exited while the run was `running`;
- `INTEGRITY_FAILURE`: artifacts or schema cannot be trusted.

A source failure does not fail the whole run unless the remaining coverage cannot produce any valid candidate or a trustworthy report. Lifecycle `partial` and `failed` follow the exact terminal semantics in Research Run State. A partial run does not claim success.

## Testing Strategy

### Unit and fixture tests

- parse representative RSS, Atom, API, HTML, and sitemap fixtures;
- canonicalize URLs and timestamps;
- detect mojibake, anti-bot pages, homepages, empty content, and duplicate hashes;
- quarantine unregistered SearXNG/direct-extraction domains and prevent them from counting as evidence;
- calculate required discovery-group `healthy` / `degraded` / `blocked` state;
- cluster duplicate event coverage;
- build claim-to-evidence mappings;
- enforce normal and politics/crime evidence gates;
- apply every V1 visual scoring profile and Kimi/DeepSeek reconciliation rule;
- apply every V1 risk-policy rule and derived enhanced/hard-block action;
- calculate the exact canonical trend score;
- calculate selection confidence and penalties;
- enforce diversity constraints;
- parse mocked OpenCode JSON and bounded retry behavior;
- enforce hash/pointer-only persistence for `private_owner_local` evidence.

### Integration tests

- deterministic mock run from at least 60 source items to 20 valid candidates and three packets;
- partial run when fewer than 20 valid clusters exist;
- one degraded adapter while the rest complete;
- contradictory sources block selection;
- AI experiment passes evidence/legal gates but retains a visual smoke requirement;
- approval writes a topic brief but creates no provider job;
- episode YAML creation remains a separate action;
- required-group degradation produces `partial`, while all required groups blocked produces `failed`;
- packet/evidence/wording changes stale approvals and create a new brief revision;
- identical approval revisions return the same brief ID/file;
- episode creation rejects stale enhanced approval and refuses output overwrite.

### Studio tests

- list research runs and source health;
- open packet details and evidence paths;
- approve, reject with reason, reserve, cancel;
- prevent path traversal and arbitrary command execution;
- verify research actions do not submit paid media.

### Security and lifecycle tests

- reject missing/foreign Origin, missing/incorrect CSRF header, unsupported content type, and JSON bodies over 64 KiB;
- verify CSP contains no broad `unsafe-inline` and untrusted titles/excerpts render as text, including script-tag fixtures;
- reject `..`, symlink, junction, and Windows reparse-point escape from every file endpoint;
- reject SSRF to loopback, RFC1918/private, link-local, multicast, IPv6 local, cloud-metadata, URL credentials, and redirect targets that resolve into blocked ranges;
- verify only the exact configured SearXNG adapter can use its loopback exception;
- enforce redirect count, response-size, adapter timeout, and OpenCode timeout;
- cancel queued and running jobs, abort fetch/subprocess work, and prove no new work starts after cancellation;
- cover cancellation-versus-atomic-completion race and immutable terminal states;
- mark orphaned running jobs `failed/INTERRUPTED` on restart and create a new `parent_run_id` retry without overwriting artifacts;
- enforce editorial/enhanced approval transitions, 12-hour staleness, wording/evidence revision binding, and derived eligibility;
- prove topic-brief revision retention/idempotency and the no-overwrite episode YAML rule;
- prove raw private owner-local material never appears in snapshots, JSON reports, prompts, or publishing output.

### Live health checks

Live network health is not part of deterministic unit tests. Add a separate read-only command such as:

```text
npm run scout:health -- --report-only
npm run scout:health -- --require-minimum
```

Both modes report current feed/search/extraction status, `checked_at`, adapter/config identity, HTTP/content type when available, and a redacted error preview.

- `--report-only` exits `0` when a schema-valid observation report is written, regardless of whether observed source state is `HEALTHY`, `DEGRADED`, or `BLOCKED`; internal command/schema failure exits `1`.
- `--require-minimum` exits `0` for `HEALTHY`, `2` for `DEGRADED`, `3` for `BLOCKED`, and `1` for internal command failure.

Deterministic implementation acceptance requires `--report-only` to produce a valid report. It must not turn a temporary source outage into a code PASS or FAIL. An actual live Scout run uses the observed source state to determine `ready`, `partial`, or `failed`.

### Required verification commands

```text
npm.cmd run typecheck
npm.cmd test
npm.cmd run scout:doctor
npm.cmd run scout:health -- --report-only
npm.cmd run scout -- --lane topics
npm.cmd run secrets:scan
git diff --check
```

`evals/trend-scout.eval.yaml` should become a blocking code-backed contract rather than a non-blocking prose checklist.

The CLI command is an internal/manual verification path into the same orchestrator. It is not a scheduler and does not weaken the owner-facing “button in Studio” workflow.

## Success Oracle

The implementation is successful when an owner-triggered research run can prove all of the following:

1. It returns 20 unique concrete-topic candidates when enough valid clusters exist.
2. The pool covers at least four configured source families, or the run is honestly marked lifecycle `partial`.
3. No homepage, anti-bot page, empty extraction, or corrupted-Cyrillic item appears in the valid pool.
4. Each candidate has a canonical URL, timestamps appropriate to its classification, series/format routing, evidence state, score rationale, risk state, and visual feasibility.
5. The top three contain two safe production packets and one AI-video experiment.
6. All top-three public claims map to retained evidence excerpts and snapshot hashes; private owner-local production references use the hash/pointer-only contract and cannot be sole support for a public claim.
7. Politics/crime/accusation packets satisfy the enhanced evidence rule and remain manual-approval only.
8. The AI-video experiment has no unresolved factual/legal weakness and names the cheapest useful smoke.
9. Studio explains why each packet was selected and exposes degraded sources and blockers.
10. Reaching derived approval state `eligible` writes an idempotent revision-bound brief but starts no paid media generation.
11. The run can be reproduced and audited from its retained artifacts without relying on chat memory.

Not enough:

- a Scout command exits with code zero;
- 20 rows exist but include duplicates or landing pages;
- an LLM returns a plausible list without retained evidence;
- the same default score is copied to every candidate;
- three packets exist but source, legal, or visual gates were skipped;
- a Studio page renders while its actions bypass the contracts above.

## Documentation Impact

Implementation will require scoped updates inside the local `.content-video-ad` workspace. The selector contract change is atomic: code cannot claim the new behavior until all starred owner documents agree and tests enforce it.

- **`AGENTS.md`** for `2 safe + 1 experiment`, manual-trigger boundary, and enhanced-risk gate;
- **`config/scout.yaml`** for versioned source adapters, thresholds, health, query budgets, selector rules, and security policy;
- **`config/content-series.yaml`** for `safe_production: 2`, `experimental_ai_video: 1`, `reserve_candidate: 0`, score/selection schema, and rubric profile references;
- **`docs/content-series-strategy.md`** for current research and selection behavior;
- **`docs/pipeline.md`** for the Scout-to-topic-brief-to-episode approval boundary;
- **`prompts/agent-research.md`** for the current packet schema and exact shortlist contract;
- `docs/video-agent-operating-loop.md` for Scout `run-state.json`;
- `README.md` for Studio and commands;
- **`evals/trend-scout.eval.yaml`** for blocking acceptance and the removal of the old reserve requirement.

Do not duplicate current behavior into root `AGENTS.md`. The local `.content-video-ad` directory is intentionally ignored by the platform repository and must not be force-added wholesale. This root design spec is the tracked review artifact.

## Implementation Boundary

This design does not authorize implementation, paid provider calls, deployment, or publishing. The next step after spec review and owner review is a separate implementation plan.
