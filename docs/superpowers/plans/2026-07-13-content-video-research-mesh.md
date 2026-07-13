# POKROV Content Research Mesh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the placeholder Trend Scout with a production Research Mesh that produces a 20-topic evidence-backed pool, two safe packets, one bounded AI-video experiment, and revision-bound owner approvals from Content Studio without starting paid media.

**Architecture:** A typed orchestrator coordinates registered free-source adapters, secure extraction, deterministic normalization and clustering, bounded evidence verification, rule-owned risk/scoring, OpenCode editorial enrichment, and a diversity selector. Durable run artifacts and approvals are written atomically; Content Studio is a loopback-only operator UI over the same services used by the manual CLI.

**Tech Stack:** TypeScript 6, Node.js ESM, Zod 4, Commander, fs-extra, execa/OpenCode, Node `fetch`, fast-xml-parser 5.10.0, tldts 7.4.8, ipaddr.js 2.4.0, proper-lockfile 4.1.2, Node test runner, local HTML/CSS/JavaScript Studio.

## Global Constraints

- The implementation workspace is `C:\Users\kiwun\Documents\ai\VPN\.content-video-ad`; all paths below are relative to that directory unless a root path is written explicitly.
- The approved design is `C:\Users\kiwun\Documents\ai\VPN\docs\superpowers\specs\2026-07-13-content-video-research-mesh-design.md` and wins over the old Scout implementation.
- The only user-facing trigger is the Content Studio button `Найти темы`; the manual CLI is allowed only for tests and operator diagnostics. No scheduler is added.
- Discovery uses free surfaces only. No paid search API, OpenRouter model, new paid LLM model, account automation, proxy, stealth fetch, paywall bypass, publishing action, or paid TTS/image/video call is introduced.
- Research-ranking OpenCode calls use only `opencode-go/kimi-k2.6` and `opencode-go/deepseek-v4-pro`, `--pure`, `--variant low`, bounded JSON schemas, and retained safe telemetry. `opencode-go/glm-5.1` is allowed only in the separate post-approval fact-packet episode-writing action.
- A ready run requires exactly 20 unique event-cluster candidates, at least four registered source families, healthy `ru_core`, `broad_news`, and `trend_signal` groups, two distinct safe packets, and one distinct AI-video experiment packet.
- A partial run never pads duplicates, landing pages, quarantined domains, weak snippets, blocked evidence, unresolved risk, or malformed LLM output into the valid pool.
- Politics, crime, court, accusations, and controversial public events require primary/authoritative evidence, two independent confirmations, a current-status check, editorial approval, and separate enhanced approval. Private-person accusations, identifiable minors, explicit graphic material, and high copyright/reuse risk are hard-blocked by default.
- POKROV VPN stays a sponsor/banner layer. `brand_nonintrusion` never rewards bending the story toward VPN education.
- Topic-brief creation and episode YAML creation are separate explicit owner actions. Neither action submits provider jobs. Existing output files are never overwritten.
- Every persisted JSON contract contains `schema_version`; every run snapshots config hashes, adapter-set hashes, limits, timeouts, source health, issues, and safe telemetry.
- Run caps are exact: 60 items/adapter, 300 total items, 40 sitemap URLs/source, 120 direct pages, 60 clusters after dedupe, 40 verified clusters, 25 OpenCode clusters, 12 verification queries/cluster, 240 verification queries total, 12 OpenCode calls, batch size 10, one schema retry/call, eight concurrent fetches, two concurrent OpenCode calls, and 900 seconds wall clock.
- Remote extraction accepts only `http:`/`https:`, rejects credentials and blocked IP ranges after DNS resolution and on every redirect, caps redirects at five and response size at 1,500,000 bytes, and permits loopback only for the exact configured SearXNG adapter URL.
- Studio binds only to `127.0.0.1`, rejects non-loopback hosts, requires exact Origin plus `X-POKROV-Studio-CSRF` for mutations, caps JSON bodies at 64 KiB, serves allowlisted extensions from allowlisted real paths, and emits a nonce-based CSP without `unsafe-inline`.
- Never persist raw private owner-local material, secrets, headers, provider payloads, reasoning details, subscription URLs, or customer data. Owner-local evidence is hash/pointer-only and cannot independently support a public factual claim.
- Preserve current `cuts` and `kira` Scout compatibility paths. `meme_news` becomes a deprecated alias of `topics`; it must no longer generate draft episode YAML before approval.
- Do not force-add the ignored `.content-video-ad/` directory to the platform repository. Task 0 establishes a separate version-control boundary only if the owner explicitly approves it.

---

## File Structure

### Contracts and configuration

- `src/scout/contracts.ts` — Zod schemas and inferred JSON-compatible domain types.
- `src/scout/configSchema.ts` — strict V2 `config/scout.yaml` schema.
- `src/scout/config.ts` — config loading, hashing, registry validation, legacy lane mapping.
- `src/scout/runState.ts` — phase/status transitions, cancellation, restart recovery, terminal compare-and-set.
- `src/scout/artifactStore.ts` — atomic JSON/text/JSONL writes, revision hashes, run layout.
- `config/scout.yaml` — source registry, groups, thresholds, budgets, risk policy, visual profiles, security.

### Discovery, extraction, and evidence

- `src/scout/adapters/types.ts` — adapter dependency and result interfaces.
- `src/scout/adapters/rss.ts` — RSS/Atom/Google Trends and sitemap parsing.
- `src/scout/adapters/searxng.ts` — exact local SearXNG breadth adapter.
- `src/scout/adapters/ownerLocal.ts` — configured owner URL and private-local reference adapter.
- `src/scout/sourceRegistry.ts` — registered-domain lookup and quarantine records.
- `src/scout/networkPolicy.ts` — DNS/IP/redirect/size/timeout SSRF boundary.
- `src/scout/extract.ts` — public HTML extraction through the safe fetch layer and local parser helper.
- `src/scout/quality.ts` — normalization, canonicalization, date/freshness checks, content-quality rejection.
- `src/scout/snapshots.ts` — bounded sanitized public snapshots and private pointer-only evidence.
- `src/scout/clustering.ts` — deterministic event clustering and uncertain-pair interface.
- `src/scout/evidence.ts` — claim graph, provenance/independence checks, contradictions, evidence gate.
- `src/scout/verification.ts` — two-round, 12-query/cluster evidence feedback loop.

### Editorial, scoring, and selection

- `src/scout/risk.ts` — versioned signal extraction, fail-closed policy rules, derived actions.
- `src/scout/opencode.ts` — bounded Kimi/DeepSeek JSON calls with cancellation and safe telemetry.
- `src/scout/formatProfiles.ts` — eight V1 format visual profiles and format routing.
- `src/scout/scoring.ts` — deterministic rubrics, rationale records, confidence, penalties, formula audit.
- `src/scout/selector.ts` — pool eligibility, diversity ordering, two-safe/one-experiment assignment.
- `src/scout/orchestrator.ts` — bounded phase orchestration and trustworthy partial/failure behavior.
- `src/scout/index.ts` — public exports and compatibility dispatch.
- `src/scout/reports.ts` — V2 report rendering; legacy draft generation is removed from topic scouting.

### Approvals, Studio, and episode handoff

- `src/scout/approvals.ts` — revision-bound editorial/enhanced decisions and brief idempotency.
- `src/scout/episodeWriter.ts` — post-approval GLM fact-packet writer constrained to locked claims.
- `src/scout/episodeFromBrief.ts` — schema-valid episode YAML from an eligible current brief, no provider jobs.
- `src/lib/schema.ts` — optional research brief/revision fields on `EpisodeSchema`.
- `src/studio/security.ts` — Origin, CSRF, CSP, body, host, and realpath guards.
- `src/studio/researchQueue.ts` — one-run research queue with cancellation and restart semantics.
- `src/studio/researchApi.ts` — typed list/detail/start/cancel/retry/approve/reject/reserve/brief/episode actions.
- `src/studio/page.ts` — nonce-injected Research Inbox UI using DOM `textContent` for untrusted values.
- `src/studio/server.ts` — thin loopback HTTP composition root and compatibility re-export of `indexHtml`.
- `src/studio/commands.ts` — existing paid/production allowlist remains isolated from research actions.

### Verification and owners

- `tests/scoutContracts.test.ts`, `tests/scoutRunState.test.ts`, `tests/scoutAdapters.test.ts`, `tests/scoutSecurity.test.ts`, `tests/scoutQuality.test.ts`, `tests/scoutEvidence.test.ts`, `tests/scoutRisk.test.ts`, `tests/scoutScoring.test.ts`, `tests/scoutSelector.test.ts`, `tests/scoutOrchestrator.test.ts`, `tests/scoutApprovals.test.ts`, `tests/studioResearch.test.ts`, `tests/scoutAcceptance.test.ts` — focused deterministic coverage.
- `tests/fixtures/scout/` — bounded UTF-8 RSS, Atom, sitemap, HTML, anti-bot, mojibake, contradiction, risk, and 60-item integration fixtures.
- `src/cli.ts`, `package.json`, `package-lock.json` — new topic, health, approval, and episode commands with defined exit codes.
- `AGENTS.md`, `config/content-series.yaml`, `docs/content-series-strategy.md`, `docs/pipeline.md`, `docs/video-agent-operating-loop.md`, `prompts/agent-research.md`, `evals/trend-scout.eval.yaml`, `README.md` — atomic owner and operator updates.

## Canonical Execution Navigation

The numbered list below is the execution order even when reading the detailed delivery-slice chapters through direct links.

1. [Task 0 — repository boundary](#task-0-establish-a-reviewable-local-repository-boundary)
2. [Task 1 — contracts and config](#task-1-add-strict-v2-contracts-and-config-loading)
3. [Task 2 — durable run state](#task-2-add-atomic-artifact-storage-and-exact-run-state-transitions)
4. [Task 3 — discovery adapters](#task-3-implement-registered-discovery-adapters-and-source-health)
5. [Task 4 — secure extraction and quality](#task-4-enforce-ssrf-safe-extraction-bounded-snapshots-and-the-content-quality-gate)
6. [Task 5 — clustering and evidence](#task-5-cluster-events-and-close-evidence-gaps-with-a-bounded-verification-loop)
7. [Task 6 — risk engine](#task-6-add-the-versioned-fail-closed-risk-engine)
8. [Task 7 — OpenCode enrichment](#task-7-add-bounded-opencode-editorial-and-critique-calls)
9. [Task 8 — scoring and selector](#task-8-implement-format-routing-deterministic-scoring-and-the-diversity-selector)
10. [Task 9 — orchestrator and CLI](#task-9-compose-the-bounded-orchestrator-reports-health-command-and-cli-exit-semantics)
11. [Task 10 — approvals and episode handoff](#task-10-implement-approvals-idempotent-topic-briefs-and-no-overwrite-episode-creation)
12. [Task 11 — secured Research API](#task-11-harden-content-studio-and-expose-a-typed-research-api)
13. [Task 12 — Research Inbox UI](#task-12-build-the-research-inbox-operator-ui)
14. [Task 13 — blocking E2E acceptance](#task-13-make-the-contract-blocking-prove-the-full-story-and-update-every-owner-document-atomically)

---

## Delivery Slice 0 — Version-Control Precondition

### Task 0: Establish a reviewable local repository boundary

**Files:**
- Inspect: `.gitignore`
- Create only with owner approval: `.git/` inside `.content-video-ad`

**Interfaces:**
- Consumes: the existing local `.gitignore`, which already excludes secrets, media, private references, provider outputs, and `runs/*`.
- Produces: a standalone `main` baseline plus `codex/research-mesh` feature branch so every later task can end in a real commit without force-adding the workspace to the platform repository.

- [ ] **Step 1: Confirm the current platform ignore boundary**

Run from `C:\Users\kiwun\Documents\ai\VPN`:

```powershell
git check-ignore -v .content-video-ad/src/scout/index.ts
```

Expected: exit `0` and `.gitignore:87:.content-video-ad/`. Do not run `git add -f`.

- [ ] **Step 2: Confirm the local ignore rules cover sensitive and heavy files**

Run from `.content-video-ad`:

```powershell
rg.exe -n "^(\.env|\*key|\*secret|runs/|video refs/|dance video ref/|\*\.mp4|\*\.png)" .gitignore
```

Expected: every named class is present. If any class is missing, stop before repository initialization and add only the missing ignore pattern after owner approval.

- [ ] **Step 3: Initialize and baseline only after explicit owner approval**

```powershell
git init -b main
npm.cmd run secrets:scan
git add .gitignore AGENTS.md README.md package.json package-lock.json tsconfig.json config content docs evals prompts remotion scripts src tests
git diff --cached --check
git status --short
git commit -m "chore: baseline content video workspace"
git switch -c codex/research-mesh
```

Expected: secret scan `pass`, no ignored media/keys/runs staged, baseline commit succeeds, active branch is `codex/research-mesh`.

---

## Delivery Slice 1 — Contracts, Config, And Durable State

### Task 1: Add strict V2 contracts and config loading

**Files:**
- Create: `src/scout/contracts.ts`
- Create: `src/scout/configSchema.ts`
- Modify: `src/scout/types.ts`
- Modify: `src/scout/config.ts`
- Modify: `config/scout.yaml`
- Modify: `package.json`
- Modify: `package-lock.json`
- Test: `tests/scoutContracts.test.ts`

**Interfaces:**
- Consumes: `readYaml<T>(path)` from `src/lib/files.ts` and the approved schema names below.
- Produces: `readScoutConfig(path?: string): Promise<ScoutConfig>`, `hashScoutConfig(config): string`, `SourceItemSchema`, `SourceHealthSchema`, `EventClusterSchema`, `ClaimEvidenceSchema`, `CandidateSchema`, `ProductionPacketSchema`, `ShortlistSchema`, `ResearchRunStateSchema`, `ApprovalRecordSchema`, and inferred exported types with exactly those names.

- [ ] **Step 1: Install only the four audited runtime dependencies and one type package**

```powershell
npm.cmd install fast-xml-parser@5.10.0 tldts@7.4.8 ipaddr.js@2.4.0 proper-lockfile@4.1.2
npm.cmd install --save-dev @types/proper-lockfile@4.1.4
```

Expected: `package.json` pins the exact versions and `npm.cmd install` exits `0`.

- [ ] **Step 2: Write the failing contract test**

Create `tests/scoutContracts.test.ts` with these assertions:

```ts
import assert from "node:assert/strict";
import test from "node:test";
import { readScoutConfig } from "../src/scout/config";
import {
  CandidateSchema,
  ResearchRunStateSchema,
  SourceItemSchema,
} from "../src/scout/contracts";

test("V2 scout config encodes the approved cardinality, groups, and caps", async () => {
  const config = await readScoutConfig();
  assert.equal(config.version, 2);
  assert.deepEqual(config.selector.roles, { safe_production: 2, experimental_ai_video: 1 });
  assert.equal(config.diversity.ready_min_source_families, 4);
  assert.equal(config.limits.max_total_source_items, 300);
  assert.equal(config.limits.max_wall_clock_seconds, 900);
  assert.deepEqual(Object.keys(config.discovery_groups).sort(), [
    "broad_news", "official_records", "owner_local", "ru_core", "trend_signal",
  ]);
});

test("quarantined domains are valid only with reserved values", () => {
  const base = {
    schema_version: 2,
    id: "src-1",
    source_id: "unknown",
    source_family: "unregistered",
    publisher_group_id: "quarantine:example.co.uk",
    source_role_hint: "discovery",
    canonical_url: "https://news.example.co.uk/story",
    title: "Concrete story",
    published_at: "2026-07-13T08:00:00.000Z",
    discovered_at: "2026-07-13T09:00:00.000Z",
    language: "ru",
    raw_metrics: {},
    text_excerpt: "x".repeat(400),
    content_hash: "a".repeat(64),
    snapshot_path: null,
    fetch_method: "searxng",
    adapter_id: "searxng_local",
    adapter_config_hash: "b".repeat(64),
    checked_at: "2026-07-13T09:00:00.000Z",
    http_status: 200,
    content_type: "text/html",
    health_status: "healthy",
    risk_profile: "green",
    registration_status: "quarantined",
    source_visibility: "public",
  } as const;
  assert.equal(SourceItemSchema.parse(base).registration_status, "quarantined");
  assert.throws(() => SourceItemSchema.parse({ ...base, source_family: "tech_press_ru" }));
  assert.throws(() => SourceItemSchema.parse({ ...base, publisher_group_id: "publisher:example" }));
});

test("pool eligibility and shortlist role are independent", () => {
  const candidate = CandidateSchema.parse(candidateFixture());
  assert.equal(candidate.pool_disposition, "pool_only");
  assert.equal(candidate.shortlist_role, null);
});

test("run state keeps phase, status, and issues orthogonal", () => {
  const state = ResearchRunStateSchema.parse(runStateFixture());
  assert.equal(state.phase, "discovering");
  assert.equal(state.status, "running");
  assert.deepEqual(state.issues, []);
});

function candidateFixture() {
  return {
    schema_version: 2,
    id: "candidate-01",
    cluster_id: "cluster-01",
    slug: "concrete-story",
    title: "Concrete story",
    topic_family: "technology",
    series: { lane_id: "generated_news_fact_story", rationale: "Approved source-backed lane" },
    format_id: "generated_news_fact_story",
    source_item_ids: ["src-1"],
    source_families: ["tech_press_ru"],
    claims: [],
    contradictions: [],
    unknowns: [],
    editorial: { hook: "Hook", why_now: "Current", why_interesting: "Clear mechanism", story_spine: ["A", "B"], twist: "B" },
    visual_plan: { profile_id: "generated_news_fact_story", profile_version: 1, concrete_state_count: 8, proof_frames: ["headline"], continuity_groups: [], banner_fit: "minor_adjustment", success_oracle: ["Proof visible"], states: [{ id: "v01", narration_goal: "Show the verified hook", visual_nouns: ["device"], proof_refs: ["src-1"], continuity_group: null }] },
    risk: { policy_version: 1, flags: [], matched_rule_ids: [], derived_actions: [], enhanced_review_required: false, hard_blocked: false, synthetic_media_label_needed: false, rationale: [] },
    production: { uncertainty: "low", experiment_axis: "none", cost_band: "medium", first_smoke: "one proof-frame layout", success_oracle: ["Story is legible"], stop_conditions: ["proof frame unreadable"] },
    trend_score: scoreFixture(),
    evidence_confidence: 0.65,
    coverage_confidence: 0.5,
    risk_penalties: [],
    selection_score: 8.6775,
    pool_disposition: "pool_only",
    shortlist_role: null,
    gate_results: [],
  };
}

function scoreFixture() {
  const names = ["freshness", "audience_heat", "absurdity", "evidence_strength", "visual_punch", "repeatability", "brand_nonintrusion", "legal_safety", "production_cost"];
  return {
    ...Object.fromEntries(names.map((name) => [name, { value: 3, rationale: "fixture", evidence_refs: [], confidence: 1 }])),
    total: 26.7,
  };
}

function runStateFixture() {
  return {
    schema_version: 2,
    run_id: "20260713-090000",
    goal: "Find evidence-backed topics",
    success_oracle: ["20 unique candidates", "two safe and one experiment"],
    phase: "discovering",
    status: "running",
    issues: [],
    counts: { discovered: 0, extracted: 0, accepted_sources: 0, rejected_sources: 0, clusters: 0, valid_candidates: 0, packets: 0 },
    source_health: [],
    inspection_surfaces: [],
    validation_ownership: [],
    llm_jobs: [],
    steering_log: [],
    blockers: [],
    next_action: "Continue discovery",
    cancellation: { requested: false },
    config_hash: "a".repeat(64),
    adapter_set_hash: "b".repeat(64),
    limits: { max_wall_clock_seconds: 900 },
    started_at: "2026-07-13T09:00:00.000Z",
    updated_at: "2026-07-13T09:00:00.000Z",
  };
}
```

- [ ] **Step 3: Run the contract test and verify the expected failure**

```powershell
node --import tsx --test tests/scoutContracts.test.ts
```

Expected: FAIL because `src/scout/contracts.ts` and the V2 config fields do not exist.

- [ ] **Step 4: Implement the strict contract surface**

Create `src/scout/contracts.ts`. Use `z.strictObject` for persisted objects, `z.discriminatedUnion` for public/private sources, `.superRefine` for quarantine invariants, and these exact exported enums and object keys:

```ts
import { z } from "zod";

export const SourceFamilySchema = z.enum([
  "community_ru", "gaming_press_ru", "tech_press_ru", "trend_signal",
  "first_party_platform", "official_record", "international_press",
  "owner_local", "unregistered",
]);
export const SourceRoleSchema = z.enum(["discovery", "primary", "independent", "context"]);
export const RunPhaseSchema = z.enum(["idle", "discovering", "extracting", "normalizing", "clustering", "verifying", "enriching", "ranking", "complete"]);
export const RunStatusSchema = z.enum(["queued", "running", "ready", "partial", "failed", "cancelled"]);
export const IssueCodeSchema = z.enum([
  "SOURCE_DEGRADED", "SOURCE_GROUP_DEGRADED", "REJECTED_CONTENT", "BLOCKED_EVIDENCE",
  "BLOCKED_CONFLICT", "BLOCKED_LEGAL", "BLOCKED_EDITORIAL", "UNRESOLVED_EDITORIAL_SCORE",
  "INSUFFICIENT_POOL", "INSUFFICIENT_COVERAGE", "MISSING_SAFE_ROLE", "MISSING_EXPERIMENT_ROLE",
  "INTERRUPTED", "INTEGRITY_FAILURE", "RUN_LIMIT_REACHED",
]);
const HashSchema = z.string().regex(/^[a-f0-9]{64}$/);
const IsoDateSchema = z.string().datetime();

const PublicSourceItemSchema = z.strictObject({
  schema_version: z.literal(2), id: z.string().min(1), source_id: z.string().min(1),
  source_family: SourceFamilySchema, publisher_group_id: z.string().min(1), source_role_hint: SourceRoleSchema,
  canonical_url: z.string().url(), title: z.string().min(1), published_at: IsoDateSchema.nullable(),
  discovered_at: IsoDateSchema, language: z.string().min(2), author: z.string().min(1).optional(),
  raw_metrics: z.record(z.string(), z.union([z.string(), z.number(), z.boolean(), z.null()])),
  text_excerpt: z.string(), content_hash: HashSchema, snapshot_path: z.string().nullable(),
  fetch_method: z.string().min(1), adapter_id: z.string().min(1), adapter_config_hash: HashSchema,
  checked_at: IsoDateSchema, http_status: z.number().int().min(100).max(599).optional(),
  content_type: z.string().optional(), health_status: z.enum(["healthy", "degraded", "blocked"]),
  risk_profile: z.enum(["green", "yellow", "red"]), registration_status: z.enum(["registered", "quarantined"]),
  source_visibility: z.literal("public"),
}).superRefine((value, ctx) => {
  const quarantineFamily = value.source_family === "unregistered";
  const quarantineGroup = /^quarantine:[a-z0-9.-]+$/.test(value.publisher_group_id);
  const quarantined = value.registration_status === "quarantined";
  if (quarantineFamily !== quarantined || quarantineGroup !== quarantined) {
    ctx.addIssue({ code: "custom", message: "quarantined sources require source_family=unregistered and a quarantine: publisher group" });
  }
});

const PrivateSourceItemSchema = z.strictObject({
  schema_version: z.literal(2), id: z.string().min(1), source_id: z.string().min(1),
  source_family: z.literal("owner_local"), publisher_group_id: z.string().min(1), source_role_hint: SourceRoleSchema,
  registration_status: z.literal("registered"), source_visibility: z.literal("private_owner_local"),
  local_ref_id: z.string().min(1), allowlisted_realpath_root_id: z.string().min(1), content_hash: HashSchema,
  owner_paraphrase: z.string().max(700).optional(), excerpt_redacted: z.literal(true), discovered_at: IsoDateSchema,
  checked_at: IsoDateSchema, adapter_id: z.string().min(1), adapter_config_hash: HashSchema,
  health_status: z.enum(["healthy", "degraded", "blocked"]), risk_profile: z.enum(["green", "yellow", "red"]),
});
export const SourceItemSchema = z.union([PublicSourceItemSchema, PrivateSourceItemSchema]);

export const SourceHealthSchema = z.strictObject({
  schema_version: z.literal(2), adapter_id: z.string().min(1), group_id: z.string().min(1),
  adapter_config_hash: HashSchema, checked_at: IsoDateSchema,
  status: z.enum(["healthy", "degraded", "blocked"]), item_count: z.number().int().nonnegative(),
  latency_ms: z.number().int().nonnegative(), http_status: z.number().int().optional(),
  content_type: z.string().optional(), error_preview: z.string().max(300).optional(),
});

export const ClaimEvidenceSchema = z.strictObject({
  claim_id: z.string().min(1), normalized_claim: z.string().min(1), source_refs: z.array(z.string()).min(1),
  evidence_excerpts: z.array(z.string().max(700)), snapshot_hashes: z.array(HashSchema),
  source_roles: z.array(SourceRoleSchema), confidence: z.number().min(0).max(1),
  contradictions: z.array(z.string()), unknowns: z.array(z.string()),
  intended_narration_use: z.string(), intended_visual_use: z.string(),
});

export const EventClusterSchema = z.strictObject({
  schema_version: z.literal(2), id: z.string().min(1), canonical_title: z.string().min(1),
  source_item_ids: z.array(z.string()).min(1), canonical_urls: z.array(z.string().url()).min(1),
  entity_keys: z.array(z.string()), first_published_at: IsoDateSchema.nullable(), last_published_at: IsoDateSchema.nullable(),
  deterministic_similarity: z.number().min(0).max(1), llm_comparison_used: z.boolean(),
});

const ScoreFieldSchema = z.strictObject({
  value: z.number().int().min(0).max(5), rationale: z.string().min(1), evidence_refs: z.array(z.string()), confidence: z.number().min(0).max(1),
});
export const TrendScoreSchema = z.strictObject({
  freshness: ScoreFieldSchema, audience_heat: ScoreFieldSchema, absurdity: ScoreFieldSchema,
  evidence_strength: ScoreFieldSchema, visual_punch: ScoreFieldSchema, repeatability: ScoreFieldSchema,
  brand_nonintrusion: ScoreFieldSchema, legal_safety: ScoreFieldSchema, production_cost: ScoreFieldSchema,
  total: z.number(),
});

export const CandidateSchema = z.strictObject({
  schema_version: z.literal(2), id: z.string().min(1), cluster_id: z.string().min(1), slug: z.string().min(1),
  title: z.string().min(1), topic_family: z.string().min(1),
  series: z.strictObject({ lane_id: z.string().min(1), rationale: z.string().min(1) }), format_id: z.string().min(1),
  source_item_ids: z.array(z.string()).min(1), source_families: z.array(SourceFamilySchema).min(1),
  claims: z.array(ClaimEvidenceSchema), contradictions: z.array(z.string()), unknowns: z.array(z.string()),
  editorial: z.strictObject({ hook: z.string(), why_now: z.string(), why_interesting: z.string(), story_spine: z.array(z.string()), twist: z.string() }),
  visual_plan: z.strictObject({ profile_id: z.string(), profile_version: z.number().int().positive(), concrete_state_count: z.number().int().nonnegative(), proof_frames: z.array(z.string()), continuity_groups: z.array(z.string()), banner_fit: z.string(), success_oracle: z.array(z.string()), states: z.array(z.strictObject({ id: z.string().min(1), narration_goal: z.string().min(1), visual_nouns: z.array(z.string().min(1)).min(1), proof_refs: z.array(z.string()), continuity_group: z.string().nullable() })).min(1) }),
  risk: z.strictObject({ policy_version: z.number().int().positive(), flags: z.array(z.string()), matched_rule_ids: z.array(z.string()), derived_actions: z.array(z.string()), enhanced_review_required: z.boolean(), hard_blocked: z.boolean(), synthetic_media_label_needed: z.boolean(), rationale: z.array(z.string()) }),
  production: z.strictObject({ uncertainty: z.enum(["low", "medium", "high"]), experiment_axis: z.enum(["none", "motion_transfer", "reference_to_video", "continuity_edit", "ai_remaster_reveal", "new_visual_treatment"]), cost_band: z.string(), first_smoke: z.string(), success_oracle: z.array(z.string()), stop_conditions: z.array(z.string()) }),
  trend_score: TrendScoreSchema, evidence_confidence: z.number().min(0).max(1), coverage_confidence: z.number().min(0).max(1),
  risk_penalties: z.array(z.strictObject({ code: z.string(), value: z.number().nonnegative() })), selection_score: z.number(),
  pool_disposition: z.enum(["pool_only", "safe_eligible", "experiment_eligible"]),
  shortlist_role: z.enum(["safe_01", "safe_02", "experiment_01"]).nullable(),
  gate_results: z.array(z.strictObject({ gate: z.string(), pass: z.boolean(), reason: z.string() })),
});

export const ProductionPacketSchema = z.strictObject({
  schema_version: z.literal(2), packet_id: z.string().min(1), candidate: CandidateSchema,
  packet_revision_hash: HashSchema, evidence_revision_hash: HashSchema,
  run_status: RunStatusSchema, review_summary: z.string(), required_approvals: z.array(z.enum(["editorial", "enhanced"])),
});
export const ShortlistSchema = z.strictObject({
  schema_version: z.literal(2), run_id: z.string(), roles: z.strictObject({
    safe_01: z.string().nullable(), safe_02: z.string().nullable(), experiment_01: z.string().nullable(),
  }), missing_roles: z.array(z.enum(["safe_01", "safe_02", "experiment_01"])), selection_rationale: z.array(z.string()),
});

export const ApprovalRecordSchema = z.strictObject({
  schema_version: z.literal(2), approval_id: z.string(), action: z.enum(["approve_editorial", "approve_enhanced", "reject", "reserve", "resolve_risk"]),
  owner: z.string(), at: IsoDateSchema, packet_id: z.string(), packet_revision_hash: HashSchema,
  evidence_revision_hash: HashSchema, wording_checksum: HashSchema.optional(), current_status_checked_at: IsoDateSchema.optional(),
  reason: z.string().max(500).optional(), risk_policy_version: z.number().int().positive().optional(), evidence_refs: z.array(z.string()).optional(),
});

export const ResearchRunStateSchema = z.strictObject({
  schema_version: z.literal(2), run_id: z.string(), parent_run_id: z.string().optional(), goal: z.string(), success_oracle: z.array(z.string()),
  phase: RunPhaseSchema, status: RunStatusSchema, issues: z.array(IssueCodeSchema),
  counts: z.strictObject({ discovered: z.number().int().nonnegative(), extracted: z.number().int().nonnegative(), accepted_sources: z.number().int().nonnegative(), rejected_sources: z.number().int().nonnegative(), clusters: z.number().int().nonnegative(), valid_candidates: z.number().int().nonnegative(), packets: z.number().int().nonnegative() }),
  source_health: z.array(SourceHealthSchema), inspection_surfaces: z.array(z.strictObject({ kind: z.string(), path: z.string(), status: z.string() })),
  validation_ownership: z.array(z.strictObject({ check: z.string(), owner: z.string(), status: z.string() })),
  llm_jobs: z.array(z.strictObject({ provider: z.string(), model: z.string(), latency_ms: z.number().int().nonnegative(), stable_prompt_hash: HashSchema, status: z.string(), prompt_tokens: z.number().int().nonnegative().optional(), cached_tokens: z.number().int().nonnegative().optional(), output_tokens: z.number().int().nonnegative().optional() })),
  steering_log: z.array(z.strictObject({ at: IsoDateSchema, source: z.string(), note: z.string(), impact: z.string() })),
  blockers: z.array(z.string()), next_action: z.string(), cancellation: z.strictObject({ requested: z.boolean(), requested_at: IsoDateSchema.optional(), completed_at: IsoDateSchema.optional() }),
  config_hash: HashSchema, adapter_set_hash: HashSchema, limits: z.record(z.string(), z.number()),
  started_at: IsoDateSchema, updated_at: IsoDateSchema, completed_at: IsoDateSchema.optional(),
});

export type SourceItem = z.infer<typeof SourceItemSchema>;
export type SourceHealth = z.infer<typeof SourceHealthSchema>;
export type EventCluster = z.infer<typeof EventClusterSchema>;
export type ClaimEvidence = z.infer<typeof ClaimEvidenceSchema>;
export type Candidate = z.infer<typeof CandidateSchema>;
export type ProductionPacket = z.infer<typeof ProductionPacketSchema>;
export type Shortlist = z.infer<typeof ShortlistSchema>;
export type ResearchRunState = z.infer<typeof ResearchRunStateSchema>;
export type ApprovalRecord = z.infer<typeof ApprovalRecordSchema>;
```

Create `src/scout/configSchema.ts` with a strict schema for every approved config section and exact numeric bounds. The public shape must be:

```ts
export type ScoutConfig = {
  version: 2;
  discovery_groups: Record<"ru_core" | "broad_news" | "trend_signal" | "owner_local" | "official_records", { required: boolean; min_healthy: number; adapter_ids: string[] }>;
  adapters: Record<string, { kind: "rss" | "atom" | "sitemap" | "searxng" | "owner_urls" | "owner_local"; enabled: boolean; url?: string; source_family: string; publisher_group_id: string; group_id: string; risk_profile: "green" | "yellow" | "red" }>;
  official_registry: Record<string, { domains: string[]; source_family: "official_record"; publisher_group_id: string; group_id: "official_records"; risk_profile: "green" | "yellow" }>;
  query_families: Record<string, string[]>;
  quality: { min_body_chars: { article_or_news: 400; official_notice: 160; steam_review: 40 }; max_replacement_char_ratio: 0.002; max_redirects: 5; max_response_bytes: 1500000 };
  freshness: { breaking_hours: 72; current_days: 7; evergreen_trigger_days: 30 };
  diversity: { max_candidates_per_registered_domain: 5; max_candidates_per_source_family: 8; ready_min_source_families: 4 };
  selector: { roles: { safe_production: 2; experimental_ai_video: 1 }; penalties: { ENHANCED_MANUAL_APPROVAL: 2; MINOR_NON_MATERIAL_CONFLICT: 2; SOURCE_RIGHTS_REVIEW: 1; VISUAL_SMOKE_REQUIRED: 1 } };
  limits: Record<string, number>;
  timeouts: { adapter_seconds: 30; opencode_seconds: 120; subprocess_grace_seconds: 5 };
  risk_policy: { version: 1; enhanced_approval_ttl_hours: 12; rules: Array<{ id: string; flag: string; action: string }> };
  visual_profiles: Record<string, { version: 1; selectable: boolean; score_5: Record<string, unknown>; score_4: Record<string, unknown>; score_3: Record<string, unknown> }>;
  security: { searxng_base_url: string; owner_local_roots: Record<string, string>; allowed_file_extensions: string[] };
  outputs: { root: "runs/scout" };
  legacy_lanes: { cuts: { owner_links_path: string; output_kind: "source_audit" }; kira: { owner_links_path: string; output_kind: "donor_brief"; paid_motion_requires_approval: true } };
};
```

Use `ScoutConfigSchema.parse(await readYaml(configPath))` in `readScoutConfig`, and hash the canonical recursively key-sorted JSON representation with SHA-256. Re-export V2 types from `src/scout/types.ts`; keep only the legacy `ScoutRiskProfile`, `ScoutOutputKind`, and legacy option/report types needed by `cuts` and `kira` compatibility.

- [ ] **Step 5: Replace `config/scout.yaml` with V2 registry data**

The config must register these exact initial adapters and ownership groups:

```yaml
version: 2
discovery_groups:
  ru_core: { required: true, min_healthy: 3, adapter_ids: [dtf_all, vc_all, habr_current, stopgame_news, playground_news] }
  broad_news: { required: true, min_healthy: 3, adapter_ids: [bbc_ru, tass, ria, rbc, guardian_world, dw_ru] }
  trend_signal: { required: true, min_healthy: 1, adapter_ids: [google_trends_ru, steam_signals] }
  owner_local: { required: false, min_healthy: 0, adapter_ids: [owner_urls, owner_local_refs] }
  official_records: { required: false, min_healthy: 0, adapter_ids: [] }
adapters:
  dtf_all: { kind: rss, enabled: true, url: "https://dtf.ru/rss/all", source_family: community_ru, publisher_group_id: dtf, group_id: ru_core, risk_profile: green }
  vc_all: { kind: rss, enabled: true, url: "https://vc.ru/rss/all", source_family: community_ru, publisher_group_id: vc, group_id: ru_core, risk_profile: green }
  habr_current: { kind: rss, enabled: true, url: "https://habr.com/ru/rss/articles/", source_family: tech_press_ru, publisher_group_id: habr, group_id: ru_core, risk_profile: green }
  stopgame_news: { kind: rss, enabled: true, url: "https://rss.stopgame.ru/rss_news.xml", source_family: gaming_press_ru, publisher_group_id: stopgame, group_id: ru_core, risk_profile: green }
  playground_news: { kind: rss, enabled: true, url: "https://www.playground.ru/rss/news.xml", source_family: gaming_press_ru, publisher_group_id: playground, group_id: ru_core, risk_profile: green }
  bbc_ru: { kind: rss, enabled: true, url: "https://feeds.bbci.co.uk/russian/rss.xml", source_family: international_press, publisher_group_id: bbc, group_id: broad_news, risk_profile: green }
  tass: { kind: rss, enabled: true, url: "https://tass.ru/rss/v2.xml", source_family: international_press, publisher_group_id: tass, group_id: broad_news, risk_profile: green }
  ria: { kind: rss, enabled: true, url: "https://ria.ru/export/rss2/archive/index.xml", source_family: international_press, publisher_group_id: ria, group_id: broad_news, risk_profile: green }
  rbc: { kind: rss, enabled: true, url: "https://rssexport.rbc.ru/rbcnews/news/30/full.rss", source_family: international_press, publisher_group_id: rbc, group_id: broad_news, risk_profile: green }
  guardian_world: { kind: rss, enabled: true, url: "https://www.theguardian.com/world/rss", source_family: international_press, publisher_group_id: guardian, group_id: broad_news, risk_profile: green }
  dw_ru: { kind: rss, enabled: true, url: "https://rss.dw.com/rdf/rss-ru-all", source_family: international_press, publisher_group_id: dw, group_id: broad_news, risk_profile: green }
  google_trends_ru: { kind: rss, enabled: true, url: "https://trends.google.com/trending/rss?geo=RU", source_family: trend_signal, publisher_group_id: google_trends, group_id: trend_signal, risk_profile: green }
  steam_signals: { kind: owner_urls, enabled: true, source_family: first_party_platform, publisher_group_id: steam, group_id: trend_signal, risk_profile: green }
  searxng_local: { kind: searxng, enabled: false, url: "http://127.0.0.1:8080", source_family: unregistered, publisher_group_id: "quarantine:searxng", group_id: trend_signal, risk_profile: yellow }
  owner_urls: { kind: owner_urls, enabled: true, source_family: owner_local, publisher_group_id: owner, group_id: owner_local, risk_profile: yellow }
  owner_local_refs: { kind: owner_local, enabled: true, source_family: owner_local, publisher_group_id: owner, group_id: owner_local, risk_profile: yellow }
official_registry:
  ru_official_law: { domains: [publication.pravo.gov.ru], source_family: official_record, publisher_group_id: ru_official_law, group_id: official_records, risk_profile: green }
  ru_government: { domains: [government.ru, kremlin.ru], source_family: official_record, publisher_group_id: ru_government, group_id: official_records, risk_profile: green }
  ru_courts: { domains: [sudrf.ru, arbitr.ru], source_family: official_record, publisher_group_id: ru_courts, group_id: official_records, risk_profile: green }
  eu_official: { domains: [europa.eu], source_family: official_record, publisher_group_id: eu_official, group_id: official_records, risk_profile: green }
  us_official: { domains: [sec.gov, justice.gov], source_family: official_record, publisher_group_id: us_official, group_id: official_records, risk_profile: green }
query_families:
  current_ru: ["технологии игры ИИ наука новости сегодня", "странная новость интернет культура сегодня"]
  broad_current: ["world technology science unusual current event", "gaming AI business current event"]
  verification: ["официальное заявление документ дата", "independent confirmation date status"]
quality:
  min_body_chars: { article_or_news: 400, official_notice: 160, steam_review: 40 }
  max_replacement_char_ratio: 0.002
  max_redirects: 5
  max_response_bytes: 1500000
freshness: { breaking_hours: 72, current_days: 7, evergreen_trigger_days: 30 }
diversity: { max_candidates_per_registered_domain: 5, max_candidates_per_source_family: 8, ready_min_source_families: 4 }
selector:
  roles: { safe_production: 2, experimental_ai_video: 1 }
  penalties: { ENHANCED_MANUAL_APPROVAL: 2, MINOR_NON_MATERIAL_CONFLICT: 2, SOURCE_RIGHTS_REVIEW: 1, VISUAL_SMOKE_REQUIRED: 1 }
limits:
  max_items_per_adapter: 60
  max_total_source_items: 300
  max_sitemap_urls_per_source: 40
  max_direct_pages: 120
  max_clusters_after_dedupe: 60
  max_clusters_entering_verification: 40
  max_clusters_entering_opencode: 25
  max_verification_queries_per_cluster: 12
  max_verification_queries_total: 240
  max_opencode_calls: 12
  opencode_batch_size: 10
  max_schema_retries_per_call: 1
  max_concurrent_fetches: 8
  max_concurrent_opencode: 2
  max_wall_clock_seconds: 900
timeouts: { adapter_seconds: 30, opencode_seconds: 120, subprocess_grace_seconds: 5 }
risk_policy:
  version: 1
  enhanced_approval_ttl_hours: 12
  rules:
    - { id: politics_v1, flag: politics, action: enhanced }
    - { id: crime_v1, flag: crime, action: enhanced }
    - { id: court_v1, flag: court, action: enhanced }
    - { id: accusation_public_v1, flag: accusation_public_figure, action: enhanced }
    - { id: public_figure_v1, flag: public_figure, action: observe }
    - { id: accusation_private_v1, flag: accusation_private_person, action: hard_block }
    - { id: private_person_v1, flag: private_person, action: enhanced }
    - { id: minor_identifiable_v1, flag: minor_identifiable, action: hard_block }
    - { id: minor_nonidentifying_v1, flag: minor_nonidentifying, action: enhanced }
    - { id: graphic_explicit_v1, flag: graphic_explicit, action: hard_block }
    - { id: graphic_implied_v1, flag: graphic_implied, action: enhanced }
    - { id: copyright_low_v1, flag: copyright_low, action: eligible_with_attribution }
    - { id: reused_low_v1, flag: reused_content_low, action: eligible_with_attribution }
    - { id: copyright_medium_v1, flag: copyright_medium, action: pool_only }
    - { id: reused_medium_v1, flag: reused_content_medium, action: pool_only }
    - { id: copyright_high_v1, flag: copyright_high, action: hard_block }
    - { id: reused_high_v1, flag: reused_content_high, action: hard_block }
security:
  searxng_base_url: "http://127.0.0.1:8080"
  owner_local_roots: { dance_refs: "dance video ref", video_refs: "video refs", parkour: "parkour background" }
  allowed_file_extensions: [.json, .md, .txt, .yaml, .yml, .html, .png, .jpg, .jpeg, .webp]
outputs: { root: "runs/scout" }
legacy_lanes:
  cuts: { owner_links_path: "full-video-parts/links.txt", output_kind: source_audit }
  kira: { owner_links_path: "dance video ref", output_kind: donor_brief, paid_motion_requires_approval: true }
```

Add all eight visual profiles from the approved spec under `visual_profiles`; each profile is `version: 1`, `selectable: true`, and has exact score-5/4/3 thresholds. Keep `full_video_parts` and under-study formats absent or `selectable: false`.

- [ ] **Step 6: Run the contract and type checks**

```powershell
node --import tsx --test tests/scoutContracts.test.ts
npm.cmd run typecheck
```

Expected: PASS.

- [ ] **Step 7: Commit the contract slice**

```powershell
git add package.json package-lock.json config/scout.yaml src/scout/contracts.ts src/scout/configSchema.ts src/scout/config.ts src/scout/types.ts tests/scoutContracts.test.ts
git diff --cached --check
git commit -m "feat: add research mesh contracts and config"
```

Expected: one scoped commit and no generated/private files staged.

### Task 2: Add atomic artifact storage and exact run-state transitions

**Files:**
- Create: `src/scout/artifactStore.ts`
- Create: `src/scout/runState.ts`
- Test: `tests/scoutRunState.test.ts`

**Interfaces:**
- Consumes: `ResearchRunStateSchema`, `ResearchRunState`, `IssueCodeSchema`, `proper-lockfile`.
- Produces: `atomicWriteJson(path, value): Promise<void>`, `appendJsonLine(path, value): Promise<void>`, `revisionHash(value): string`, `createResearchRun(args): Promise<ResearchRunState>`, `transitionRun(args): Promise<ResearchRunState>`, `commitTerminalReport(args): Promise<ResearchRunState>`, `requestCancellation(runDir, now?): Promise<ResearchRunState>`, `finalizeCancellation(runDir, now?): Promise<ResearchRunState>`, and `recoverInterruptedRuns(root, now?): Promise<string[]>`.

- [ ] **Step 1: Write failing lifecycle tests**

Create `tests/scoutRunState.test.ts`:

```ts
import assert from "node:assert/strict";
import test from "node:test";
import fs from "fs-extra";
import os from "node:os";
import path from "node:path";
import { readJson } from "../src/lib/files";
import type { ResearchRunState } from "../src/scout/contracts";
import { atomicWriteJson, revisionHash } from "../src/scout/artifactStore";
import { commitTerminalReport, createResearchRun, finalizeCancellation, recoverInterruptedRuns, requestCancellation, transitionRun } from "../src/scout/runState";

test("terminal state is immutable and report rename precedes ready", async () => {
  const runDir = await fs.mkdtemp(path.join(os.tmpdir(), "mesh-state-"));
  await createResearchRun({ runDir, runId: "run-1", configHash: "a".repeat(64), adapterSetHash: "b".repeat(64), limits: { max_wall_clock_seconds: 900 }, now: "2026-07-13T09:00:00.000Z" });
  await transitionRun({ runDir, phase: "ranking", now: "2026-07-13T09:01:00.000Z" });
  const state = await commitTerminalReport({ runDir, report: { schema_version: 2, run_id: "run-1" }, status: "ready", now: "2026-07-13T09:02:00.000Z" });
  assert.equal(state.status, "ready");
  assert.equal(await fs.pathExists(path.join(runDir, "scout-report.json")), true);
  await assert.rejects(() => requestCancellation(runDir, "2026-07-13T09:03:00.000Z"), /terminal/i);
});

test("cancellation wins before final report commit", async () => {
  const runDir = await fs.mkdtemp(path.join(os.tmpdir(), "mesh-cancel-"));
  await createResearchRun({ runDir, runId: "run-2", configHash: "a".repeat(64), adapterSetHash: "b".repeat(64), limits: { max_wall_clock_seconds: 900 }, now: "2026-07-13T09:00:00.000Z" });
  await transitionRun({ runDir, phase: "discovering", status: "running", now: "2026-07-13T09:00:00.500Z" });
  const requested = await requestCancellation(runDir, "2026-07-13T09:00:01.000Z");
  assert.equal(requested.status, "running");
  assert.equal(requested.cancellation.requested, true);
  await assert.rejects(() => commitTerminalReport({ runDir, report: {}, status: "partial", now: "2026-07-13T09:00:01.250Z" }), /cancellation won/i);
  const cancelled = await finalizeCancellation(runDir, "2026-07-13T09:00:01.500Z");
  assert.equal(cancelled.status, "cancelled");
  await assert.rejects(() => commitTerminalReport({ runDir, report: {}, status: "partial", now: "2026-07-13T09:00:02.000Z" }), /terminal/i);
});

test("restart marks orphaned running runs failed and retains old artifacts", async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "mesh-recover-"));
  const runDir = path.join(root, "run-3");
  await createResearchRun({ runDir, runId: "run-3", configHash: "a".repeat(64), adapterSetHash: "b".repeat(64), limits: { max_wall_clock_seconds: 900 }, now: "2026-07-13T09:00:00.000Z" });
  await atomicWriteJson(path.join(runDir, "source-health.json"), { retained: true });
  const recovered = await recoverInterruptedRuns(root, "2026-07-13T10:00:00.000Z");
  const state = await readJson<ResearchRunState>(path.join(runDir, "run-state.json"));
  assert.deepEqual(recovered, ["run-3"]);
  assert.equal(state.status, "failed");
  assert.equal(state.issues.includes("INTERRUPTED"), true);
  assert.equal(await fs.pathExists(path.join(runDir, "source-health.json")), true);
});

test("revision hashes ignore object key order", () => {
  assert.equal(revisionHash({ a: 1, b: 2 }), revisionHash({ b: 2, a: 1 }));
});
```

- [ ] **Step 2: Run the lifecycle test and verify failure**

```powershell
node --import tsx --test tests/scoutRunState.test.ts
```

Expected: FAIL because the artifact and state modules do not exist.

- [ ] **Step 3: Implement atomic storage**

Create `src/scout/artifactStore.ts` with canonical JSON hashing and same-directory temp-file rename:

```ts
import crypto from "node:crypto";
import path from "node:path";
import fs from "fs-extra";
import lockfile from "proper-lockfile";

function canonical(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value as Record<string, unknown>).sort(([a], [b]) => a.localeCompare(b)).map(([key, entry]) => [key, canonical(entry)]));
  }
  return value;
}

export function revisionHash(value: unknown): string {
  return crypto.createHash("sha256").update(JSON.stringify(canonical(value))).digest("hex");
}

export async function atomicWriteJson(filePath: string, value: unknown): Promise<void> {
  await fs.ensureDir(path.dirname(filePath));
  const temp = `${filePath}.${process.pid}.${crypto.randomUUID()}.tmp`;
  await fs.writeFile(temp, `${JSON.stringify(value, null, 2)}\n`, "utf8");
  await fs.rename(temp, filePath);
}

export async function withArtifactLock<T>(runDir: string, action: () => Promise<T>): Promise<T> {
  await fs.ensureDir(runDir);
  const release = await lockfile.lock(runDir, { realpath: false, retries: { retries: 20, minTimeout: 25, maxTimeout: 100 }, stale: 30_000 });
  try { return await action(); } finally { await release(); }
}

export async function appendJsonLine(filePath: string, value: unknown): Promise<void> {
  await fs.ensureDir(path.dirname(filePath));
  await fs.appendFile(filePath, `${JSON.stringify(value)}\n`, "utf8");
}
```

- [ ] **Step 4: Implement state creation, transition, cancellation, recovery, and terminal commit**

Create `src/scout/runState.ts` with these rules in code:

```ts
import path from "node:path";
import fs from "fs-extra";
import { readJson } from "../lib/files";
import { ResearchRunStateSchema, type ResearchRunState } from "./contracts";
import { atomicWriteJson, withArtifactLock } from "./artifactStore";

const terminal = new Set(["ready", "partial", "failed", "cancelled"]);
const phaseOrder = ["idle", "discovering", "extracting", "normalizing", "clustering", "verifying", "enriching", "ranking", "complete"] as const;
const nowIso = () => new Date().toISOString();

async function load(runDir: string): Promise<ResearchRunState> {
  return ResearchRunStateSchema.parse(await readJson(path.join(runDir, "run-state.json")));
}

export async function createResearchRun(args: { runDir: string; runId: string; configHash: string; adapterSetHash: string; limits: Record<string, number>; parentRunId?: string; now?: string }): Promise<ResearchRunState> {
  const now = args.now ?? nowIso();
  const state = ResearchRunStateSchema.parse({ schema_version: 2, run_id: args.runId, parent_run_id: args.parentRunId, goal: "Find evidence-backed production topics", success_oracle: ["20 unique valid candidates", "two safe packets", "one AI-video experiment"], phase: "idle", status: "queued", issues: [], counts: { discovered: 0, extracted: 0, accepted_sources: 0, rejected_sources: 0, clusters: 0, valid_candidates: 0, packets: 0 }, source_health: [], inspection_surfaces: [], validation_ownership: [], llm_jobs: [], steering_log: [], blockers: [], next_action: "Start discovery", cancellation: { requested: false }, config_hash: args.configHash, adapter_set_hash: args.adapterSetHash, limits: args.limits, started_at: now, updated_at: now });
  await atomicWriteJson(path.join(args.runDir, "run-state.json"), state);
  return state;
}

export async function transitionRun(args: { runDir: string; phase?: ResearchRunState["phase"]; status?: "running"; issues?: ResearchRunState["issues"]; blockers?: string[]; nextAction?: string; counts?: Partial<ResearchRunState["counts"]>; now?: string }): Promise<ResearchRunState> {
  return withArtifactLock(args.runDir, async () => {
    const state = await load(args.runDir);
    if (terminal.has(state.status)) throw new Error(`Run is terminal: ${state.status}`);
    if (args.phase && phaseOrder.indexOf(args.phase) < phaseOrder.indexOf(state.phase)) throw new Error(`Phase regression: ${state.phase} -> ${args.phase}`);
    const next = ResearchRunStateSchema.parse({ ...state, phase: args.phase ?? state.phase, status: args.status ?? state.status, issues: args.issues ?? state.issues, blockers: args.blockers ?? state.blockers, next_action: args.nextAction ?? state.next_action, counts: { ...state.counts, ...args.counts }, updated_at: args.now ?? nowIso() });
    await atomicWriteJson(path.join(args.runDir, "run-state.json"), next);
    return next;
  });
}

export async function requestCancellation(runDir: string, now = nowIso()): Promise<ResearchRunState> {
  return withArtifactLock(runDir, async () => {
    const state = await load(runDir);
    if (terminal.has(state.status)) throw new Error(`Run is terminal: ${state.status}`);
    const queued = state.status === "queued";
    const next = ResearchRunStateSchema.parse({ ...state, phase: queued ? "complete" : state.phase, status: queued ? "cancelled" : state.status, cancellation: { requested: true, requested_at: now, ...(queued ? { completed_at: now } : {}) }, next_action: queued ? "Inspect retained artifacts or retry" : "Stop in-flight work and finalize cancellation", updated_at: now, ...(queued ? { completed_at: now } : {}) });
    await atomicWriteJson(path.join(runDir, "run-state.json"), next);
    return next;
  });
}

export async function finalizeCancellation(runDir: string, now = nowIso()): Promise<ResearchRunState> {
  return withArtifactLock(runDir, async () => {
    const state = await load(runDir);
    if (terminal.has(state.status)) {
      if (state.status === "cancelled") return state;
      throw new Error(`Run is terminal: ${state.status}`);
    }
    if (!state.cancellation.requested) throw new Error("Cancellation was not requested");
    const next = ResearchRunStateSchema.parse({ ...state, phase: "complete", status: "cancelled", cancellation: { ...state.cancellation, completed_at: now }, next_action: "Inspect retained partial artifacts or retry", updated_at: now, completed_at: now });
    await atomicWriteJson(path.join(runDir, "run-state.json"), next);
    return next;
  });
}

export async function commitTerminalReport(args: { runDir: string; report: unknown; status: "ready" | "partial" | "failed"; issues?: ResearchRunState["issues"]; now?: string }): Promise<ResearchRunState> {
  return withArtifactLock(args.runDir, async () => {
    const state = await load(args.runDir);
    if (terminal.has(state.status)) throw new Error(`Run is terminal: ${state.status}`);
    if (state.cancellation.requested) throw new Error("Cancellation won before final report commit");
    await atomicWriteJson(path.join(args.runDir, "scout-report.json"), args.report);
    const now = args.now ?? nowIso();
    const next = ResearchRunStateSchema.parse({ ...state, phase: "complete", status: args.status, issues: args.issues ?? state.issues, next_action: args.status === "ready" ? "Review shortlisted packets" : "Review blockers and eligible partial packets", updated_at: now, completed_at: now });
    await atomicWriteJson(path.join(args.runDir, "run-state.json"), next);
    return next;
  });
}

export async function recoverInterruptedRuns(root: string, now = nowIso()): Promise<string[]> {
  if (!(await fs.pathExists(root))) return [];
  const recovered: string[] = [];
  for (const entry of (await fs.readdir(root)).sort()) {
    const runDir = path.join(root, entry);
    const statePath = path.join(runDir, "run-state.json");
    if (!(await fs.pathExists(statePath))) continue;
    await withArtifactLock(runDir, async () => {
      const state = await load(runDir);
      if (state.status !== "running") return;
      const next = ResearchRunStateSchema.parse({ ...state, phase: "complete", status: "failed", issues: [...new Set([...state.issues, "INTERRUPTED"])], blockers: [...state.blockers, "Studio or Scout process exited while the run was active"], next_action: "Retry as a new run with parent_run_id", updated_at: now, completed_at: now });
      await atomicWriteJson(statePath, next);
      recovered.push(state.run_id);
    });
  }
  return recovered;
}
```

- [ ] **Step 5: Run lifecycle and regression checks**

```powershell
node --import tsx --test tests/scoutRunState.test.ts
npm.cmd run typecheck
npm.cmd test
```

Expected: focused test PASS; full suite PASS.

- [ ] **Step 6: Commit durable state**

```powershell
git add src/scout/artifactStore.ts src/scout/runState.ts tests/scoutRunState.test.ts
git diff --cached --check
git commit -m "feat: add durable research run state"
```

Expected: one scoped commit.

---

## Delivery Slice 5 — End-To-End Acceptance And Owner Truth

### Task 13: Make the contract blocking, prove the full story, and update every owner document atomically

**Files:**
- Create: `src/scout/evaluation.ts`
- Create: `scripts/write-scout-acceptance-fixture.ts`
- Create: `tests/support/researchAcceptanceFixture.ts`
- Create: `tests/scoutAcceptance.test.ts`
- Modify: `evals/trend-scout.eval.yaml`
- Modify: `package.json`
- Modify: `AGENTS.md`
- Modify: `config/content-series.yaml`
- Modify: `docs/content-series-strategy.md`
- Modify: `docs/pipeline.md`
- Modify: `docs/video-agent-operating-loop.md`
- Modify: `README.md`
- Verify: `prompts/agent-research.md`

**Interfaces:**
- Consumes: one retained Scout run directory and the full deterministic service fixture.
- Produces: `evaluateResearchRun(runDir): Promise<ResearchEvaluation[]>`, blocking `scout:eval`, a 60-item-to-20-candidate acceptance test, current owner documentation, and retained live-health evidence.

- [ ] **Step 1: Build the deterministic 60-item acceptance fixture**

Create `tests/support/researchAcceptanceFixture.ts` exporting `buildAcceptanceFixture()`. It must generate exactly:

```text
60 normalized source items
24 event clusters before gates
4 rejected clusters: homepage, anti-bot, mojibake, missing current date
20 valid unique clusters after gates
4 registered source families in the final pool
5 registered domains minimum
2 safe-eligible candidates minimum
1 experiment-eligible candidate minimum
1 enhanced-risk politics/crime candidate with primary + 2 independent confirmations
1 material contradiction that remains pool-blocked
1 quarantined SearXNG domain that remains a discovery hint only
0 private raw bytes in persisted values
```

Use fixed timestamps anchored at `2026-07-13T09:00:00.000Z`, stable SHA-256 hashes, and only `fixture.invalid` URLs. Generate duplicate coverage by assigning two or three registered publishers to the same event key; never duplicate an event key in the expected 20.

- [ ] **Step 2: Write the failing end-to-end acceptance test**

Create `tests/scoutAcceptance.test.ts`:

```ts
import assert from "node:assert/strict";
import test from "node:test";
import fs from "fs-extra";
import os from "node:os";
import path from "node:path";
import { runResearchMesh } from "../src/scout/orchestrator";
import { evaluateResearchRun } from "../src/scout/evaluation";
import { buildAcceptanceFixture } from "./support/researchAcceptanceFixture";

test("production fixture proves 60 sources to 20 candidates and three packets", async () => {
  const runDir = await fs.mkdtemp(path.join(os.tmpdir(), "mesh-acceptance-"));
  const fixture = buildAcceptanceFixture();
  const result = await runResearchMesh({ runDir, lane: "topics", services: fixture.services, now: fixture.now });
  assert.equal(result.status, "ready");
  assert.equal(result.pool.length, 20);
  assert.equal(new Set(result.pool.map((candidate) => candidate.cluster_id)).size, 20);
  assert.equal(new Set(result.pool.flatMap((candidate) => candidate.source_families)).size >= 4, true);
  assert.deepEqual(result.packets.map((packet) => packet.candidate.shortlist_role).sort(), ["experiment_01", "safe_01", "safe_02"]);
  assert.equal(result.pool.some((candidate) => candidate.title.includes("Вы, случайно, не робот")), false);
  assert.equal(result.pool.some((candidate) => candidate.source_families.includes("unregistered")), false);
  const serialized = JSON.stringify(await fs.readJson(path.join(runDir, "scout-report.json")));
  assert.doesNotMatch(serialized, /private owner fixture bytes/i);
  assert.doesNotMatch(serialized, /FAL_KEY|AIza|sk-[A-Za-z0-9_-]{20,}/);
  const evaluations = await evaluateResearchRun(runDir);
  assert.equal(evaluations.every((item) => item.status === "pass"), true, JSON.stringify(evaluations, null, 2));
});

test("evaluation fails duplicate clusters, bad arithmetic, and missing evidence", async () => {
  const runDir = await fs.mkdtemp(path.join(os.tmpdir(), "mesh-eval-fail-"));
  const fixture = buildAcceptanceFixture();
  await runResearchMesh({ runDir, lane: "topics", services: fixture.services, now: fixture.now });
  const reportPath = path.join(runDir, "scout-report.json");
  const report = await fs.readJson(reportPath);
  report.candidates[1].cluster_id = report.candidates[0].cluster_id;
  report.candidates[2].trend_score.total += 1;
  report.candidates[3].claims = [];
  await fs.writeJson(reportPath, report);
  const evaluations = await evaluateResearchRun(runDir);
  assert.equal(evaluations.some((item) => item.id === "unique_event_clusters" && item.status === "fail"), true);
  assert.equal(evaluations.some((item) => item.id === "trend_formula" && item.status === "fail"), true);
  assert.equal(evaluations.some((item) => item.id === "claim_evidence" && item.status === "fail"), true);
});
```

- [ ] **Step 3: Run the acceptance test and verify failure**

```powershell
node --import tsx --test tests/scoutAcceptance.test.ts
```

Expected: FAIL because the fixture builder/evaluator are absent.

- [ ] **Step 4: Implement the code-backed blocking evaluator**

`evaluateResearchRun` parses `run-state.json`, `scout-report.json`, `shortlist.json`, candidate files, packet files, source health, evidence, and decisions through the strict schemas. It returns one blocking result per exact ID:

```text
valid_artifact_schemas
concrete_source_quality
unique_event_clusters
candidate_count
source_family_coverage
claim_evidence
enhanced_risk_evidence
risk_hard_blocks
trend_formula
score_rationales
selector_roles
selector_distinctness
experiment_smoke_bounds
no_private_raw_material
no_paid_media_jobs
terminal_state_truth
```

Each result is `{ id, status: "pass" | "fail", blocking: true, details }`. The evaluator never changes run state and exits nonzero when any blocking result fails.

Replace `evals/trend-scout.eval.yaml` with `blocking: true` and the same IDs, expected artifact paths, and command `npm.cmd run scout:eval -- --run runs/scout/acceptance-fixture`. Remove the reserve requirement and prose-only checks.

Add:

```json
{
  "scout:eval": "tsx src/cli.ts scout-eval",
  "scout:fixture": "tsx scripts/write-scout-acceptance-fixture.ts"
}
```

`scripts/write-scout-acceptance-fixture.ts` imports `buildAcceptanceFixture`, resolves the exact path `runs/scout/acceptance-fixture`, and refuses to proceed when it falls outside the Scout root. If a schema-valid fixture at that path already passes `evaluateResearchRun`, return it unchanged; if a non-passing path already exists, fail without deleting or overwriting it. Otherwise run the deterministic orchestrator into the new path. It makes no network, OpenCode, or provider call.

- [ ] **Step 5: Update every canonical owner in the same change**

Make these exact semantic changes:

- `AGENTS.md`: replace `1 safe + 1 experiment + 1 reserve` with `2 safe + 1 AI-video experiment`; add Studio-button trigger, enhanced evidence/approval, 20 unique event-cluster pool, no draft YAML before approval, and no paid media from Scout.
- `config/content-series.yaml`: set `safe_production: 2`, `experimental_ai_video: 1`, `reserve_candidate: 0`; document `pool_disposition`, nullable `shortlist_role`, exact canonical formula, risk/visual profile references, and source-family diversity.
- `docs/content-series-strategy.md`: describe Research Mesh, source roles, clustering, three packet roles, enhanced topics, and owner steering retention.
- `docs/pipeline.md`: define `Studio button -> Research Mesh -> approval(s) -> topic brief -> separate episode YAML -> normal production pipeline`; state that Scout cannot submit provider jobs.
- `docs/video-agent-operating-loop.md`: add Scout phases/status/issues, ready/partial/failed/cancelled semantics, parent retry, cancellation, and retained inspection surfaces.
- `README.md`: document `npm run studio`, `scout:doctor`, both `scout:health` modes, manual diagnostic `scout -- --lane topics`, `scout:eval`, exit codes, and no scheduler/media behavior.
- `prompts/agent-research.md`: verify it contains two safe, one experiment, no reserve, evidence-only facts, and no episode YAML.

Do not duplicate this local product behavior into the platform root `AGENTS.md`.

- [ ] **Step 6: Run deterministic acceptance and all owner-contract checks**

```powershell
node --import tsx --test tests/scoutAcceptance.test.ts
npm.cmd run typecheck
npm.cmd test
npm.cmd run scout:doctor
npm.cmd run secrets:scan
python ..\scripts\agent_context_packet_audit.py prompts\agent-research.md
```

Expected: all commands PASS. `npm.cmd test` includes every focused test from Tasks 1–13.

- [ ] **Step 7: Run read-only live health and preserve the observed classification honestly**

```powershell
npm.cmd run scout:health -- --report-only
```

Expected: exit `0` and a schema-valid health report. Its observed source state may be `HEALTHY`, `DEGRADED`, or `BLOCKED`; record the actual state and `checked_at` without converting it into a code pass/fail claim.

- [ ] **Step 8: Run one live manual Scout diagnostic through the production orchestrator**

```powershell
npm.cmd run scout -- --lane topics
```

Expected exit meaning: `0=ready`, `2=partial`, `3=failed`, `130=cancelled`, `1=internal/schema error`. Exit `1` blocks implementation acceptance. Exit `2` or `3` is retained as a current external-source/evidence result and must match run artifacts; it is not relabeled PASS. Confirm no provider job ledger or episode YAML was created.

- [ ] **Step 9: Validate an eligible fixture brief-to-episode handoff without paid media**

```powershell
npm.cmd run scout:fixture
npm.cmd run scout:eval -- --run runs/scout/acceptance-fixture
npm.cmd run validate:episodes
```

Expected: blocking Scout eval PASS and generated approved fixture episode contract PASS. Do not run `make`, TTS, image, video, render, or publishing commands.

- [ ] **Step 10: Perform the final scoped diff and secret review**

```powershell
git status --short --branch
git diff --stat
git diff --check
git diff -- AGENTS.md README.md package.json config/content-series.yaml config/scout.yaml docs/content-series-strategy.md docs/pipeline.md docs/video-agent-operating-loop.md evals/trend-scout.eval.yaml prompts/agent-research.md src/scout src/studio src/cli.ts src/lib/schema.ts tests
npm.cmd run secrets:scan
```

Expected: only Research Mesh files are changed, diff check has no errors, secret scan PASS, and no generated/live run artifacts are staged.

- [ ] **Step 11: Commit the blocking acceptance and owner truth**

```powershell
git add AGENTS.md README.md package.json package-lock.json config/content-series.yaml config/scout.yaml docs/content-series-strategy.md docs/pipeline.md docs/video-agent-operating-loop.md evals/trend-scout.eval.yaml prompts/agent-research.md scripts/write-scout-acceptance-fixture.ts src/scout/evaluation.ts src/cli.ts tests/scoutAcceptance.test.ts tests/support/researchAcceptanceFixture.ts
git diff --cached --check
git commit -m "feat: prove production research mesh acceptance"
```

Expected: one scoped commit.

---

## Execution Order And Review Gates

Execute Tasks 0–13 in order. After every task:

1. run its focused failing test before implementation;
2. implement only that task’s contract;
3. run its focused test, `npm.cmd run typecheck`, and the full regression suite named in the task;
4. inspect the scoped diff for secrets, unrelated files, and accidental provider/media actions;
5. commit only the listed files;
6. review the commit before starting the next task.

Reviewer gates correspond to the approved decomposition:

| Gate | Tasks | Independently testable result |
| --- | --- | --- |
| Contracts/config | 0–2 | Strict schemas, exact V2 config, immutable durable run state |
| Research backend | 3–5 | Registered free-source discovery, secure extraction, quality rejection, clustering, evidence loop |
| Selector | 6–9 | Fail-closed risk, bounded OpenCode, deterministic scores, 20-pool/2-safe/1-experiment orchestration |
| Studio/actions | 10–12 | Revision-bound approvals, idempotent brief, no-overwrite episode handoff, secured Research Inbox |
| E2E acceptance | 13 | Blocking evaluator, 60→20→3 proof, current owner docs, live observation retained honestly |

## Plan Self-Review Checklist

- Spec coverage: every design section maps to at least one task in the table below.
- Placeholder scan: no prohibited placeholder phrase remains; every code-changing step names exact files, contracts, commands, and expected results.
- Type consistency: candidate, packet, shortlist, approval, brief, run-state, source-health, and episode revision names are identical across task interfaces.
- Safety consistency: only the exact SearXNG adapter gets loopback network access; Studio remains loopback-only; research actions never enter the production command queue.
- State consistency: phase/status/issues remain orthogonal; terminal states are immutable; report rename precedes ready/partial; cancellation can win only before terminal commit.
- Editorial consistency: evidence/risk/scoring engines own truth and numbers; LLMs provide bounded editorial suggestions/critique and cannot clear deterministic flags.
- Product consistency: 20 unique clusters, two safe packets, one experiment, zero reserve, and separate episode generation are repeated identically in config, tests, docs, prompt, eval, CLI, and UI.
- Git consistency: the ignored workspace is never force-added to the platform repository; real per-task commits require the explicitly approved standalone repository boundary from Task 0.

### Spec-to-task coverage

| Spec area | Task(s) |
| --- | --- |
| Source registry, groups, free surfaces, health | 1, 3, 9 |
| Local SearXNG and quarantine | 3, 4 |
| HTML/sitemap fallback and SSRF boundary | 3, 4 |
| Content-quality rejection and snapshots | 4 |
| Event clustering and uniqueness | 5, 8, 13 |
| Evidence graph, provenance, contradictions | 5 |
| Two-round verification loop and budgets | 5, 9 |
| Risk policy and fail-closed uncertainty | 6 |
| Kimi/DeepSeek enrichment and reconciliation | 7 |
| Visual profiles, trend score, confidence, penalties | 8 |
| Pool disposition, diversity, packet roles | 8, 9 |
| Run state, cancellation, timeout, retry, artifacts | 2, 9, 11 |
| Editorial/enhanced approval and 12-hour TTL | 10 |
| Brief revision/idempotency and episode no-overwrite | 10 |
| Studio loopback/Origin/CSRF/CSP/path controls | 11 |
| Research Inbox and operator actions | 12 |
| Blocking eval, tests, live health, owner docs | 13 |

## Completion Handoff Requirements

The implementation handoff must report:

- exact commits created in the standalone workspace repository;
- changed modules and owner docs;
- focused and full command results with exit codes;
- live health classification and `checked_at`;
- live Scout lifecycle/exit code and retained run path;
- proof that no paid provider/media/publishing action ran;
- any `MANUAL_OWNER_TEST`, `BLOCKED_BY_ACCESS`, external source outage, or remaining concern without converting it into PASS;
- branch state, uncommitted files, push state, and deployment state.

---

## Delivery Slice 4 — Revision-Bound Decisions, Episode Handoff, And Content Studio

### Task 10: Implement approvals, idempotent topic briefs, and no-overwrite episode creation

**Files:**
- Create: `src/scout/approvals.ts`
- Create: `src/scout/episodeWriter.ts`
- Create: `src/scout/episodeFromBrief.ts`
- Modify: `src/scout/contracts.ts`
- Modify: `src/lib/schema.ts`
- Modify: `src/cli.ts`
- Test: `tests/scoutApprovals.test.ts`

**Interfaces:**
- Consumes: current packet/evidence revisions, `ApprovalRecordSchema`, `artifactStore` locking/hashing, approved brief, `opencode-go/glm-5.1` fact-packet writer after eligibility, and `EpisodeSchema`.
- Produces: `deriveApprovalState(args): ApprovalState`, `recordPacketDecision(args): Promise<ApprovalRecord>`, `createTopicBrief(args): Promise<TopicBrief>`, `runApprovedFactPacketWriter(args): Promise<EpisodeDraft>`, and `createEpisodeFromBrief(args: { brief; slug; contentDir; writeScript; resolveSourceRef; onProviderJob }): Promise<{ path: string; episode: Episode }>`.

- [ ] **Step 1: Verify explicit visual states and extend contracts with approval state and topic briefs**

Keep this Task 1 field required in `CandidateSchema.visual_plan` and add it to every later candidate fixture:

```ts
states: z.array(z.strictObject({
  id: z.string().min(1),
  narration_goal: z.string().min(1),
  visual_nouns: z.array(z.string().min(1)).min(1),
  proof_refs: z.array(z.string()),
  continuity_group: z.string().nullable(),
})).min(1)
```

Add and export:

```ts
export const ApprovalStateSchema = z.strictObject({
  editorial: z.enum(["pending", "approved", "rejected", "stale"]),
  enhanced: z.enum(["not_required", "pending", "approved", "rejected", "stale"]),
  derived: z.enum(["pending", "eligible", "rejected", "stale"]),
});

export const TopicBriefSchema = z.strictObject({
  schema_version: z.literal(2), brief_id: z.string().regex(/^[a-f0-9]{32}$/), packet_id: z.string(),
  packet_revision_hash: HashSchema, evidence_revision_hash: HashSchema, approval_ids: z.array(z.string()).min(1),
  generated_at: IsoDateSchema, locked_claims: z.array(ClaimEvidenceSchema).min(1),
  series_and_format: z.strictObject({ lane_id: z.string(), format_id: z.string() }),
  editorial_angle: z.strictObject({ hook: z.string(), why_now: z.string(), why_interesting: z.string(), story_spine: z.array(z.string()), twist: z.string() }),
  visual_plan: CandidateSchema.shape.visual_plan, source_refs: z.array(z.string()).min(1), trend_score: TrendScoreSchema,
});
export type TopicBrief = z.infer<typeof TopicBriefSchema>;
export type ApprovalState = z.infer<typeof ApprovalStateSchema>;
```

- [ ] **Step 2: Write failing approval and episode tests**

Create `tests/scoutApprovals.test.ts`:

```ts
import assert from "node:assert/strict";
import test from "node:test";
import fs from "fs-extra";
import os from "node:os";
import path from "node:path";
import { createTopicBrief, deriveApprovalState, recordPacketDecision } from "../src/scout/approvals";
import { createEpisodeFromBrief } from "../src/scout/episodeFromBrief";

test("editorial and enhanced approvals are independent and revision-bound", () => {
  const now = "2026-07-13T10:00:00.000Z";
  const current = revisions();
  const editorial = approval("approve_editorial", current, "2026-07-13T09:00:00.000Z");
  assert.deepEqual(deriveApprovalState({ enhancedRequired: true, current, approvals: [editorial], now, ttlHours: 12 }), { editorial: "approved", enhanced: "pending", derived: "pending" });
  const enhanced = { ...approval("approve_enhanced", current, "2026-07-13T09:05:00.000Z"), wording_checksum: "c".repeat(64), current_status_checked_at: "2026-07-13T09:04:00.000Z" };
  assert.equal(deriveApprovalState({ enhancedRequired: true, current, approvals: [editorial, enhanced], now, ttlHours: 12 }).derived, "eligible");
  assert.equal(deriveApprovalState({ enhancedRequired: true, current: { ...current, evidence_revision_hash: "d".repeat(64) }, approvals: [editorial, enhanced], now, ttlHours: 12 }).derived, "stale");
});

test("enhanced approval expires after twelve hours", () => {
  const current = revisions();
  const approvals = [approval("approve_editorial", current, "2026-07-12T20:00:00.000Z"), { ...approval("approve_enhanced", current, "2026-07-12T20:05:00.000Z"), wording_checksum: "c".repeat(64), current_status_checked_at: "2026-07-12T20:04:00.000Z" }];
  assert.equal(deriveApprovalState({ enhancedRequired: true, current, approvals, now: "2026-07-13T09:00:00.000Z", ttlHours: 12 }).enhanced, "stale");
});

test("identical eligible revisions return one retained brief", async () => {
  const runDir = await fs.mkdtemp(path.join(os.tmpdir(), "mesh-brief-"));
  const packet = packetFixture();
  await fs.ensureDir(path.join(runDir, "packets"));
  await fs.writeJson(path.join(runDir, "packets", "safe-01.json"), packet);
  await recordPacketDecision({ runDir, packet, action: "approve_editorial", owner: "owner", now: "2026-07-13T09:00:00.000Z" });
  const first = await createTopicBrief({ runDir, packet, now: "2026-07-13T09:01:00.000Z", ttlHours: 12 });
  const second = await createTopicBrief({ runDir, packet, now: "2026-07-13T09:02:00.000Z", ttlHours: 12 });
  assert.equal(first.brief_id, second.brief_id);
  const files = (await fs.readdir(path.join(runDir, "topic-briefs"))).filter((name) => name.endsWith(".json") && name !== "index.json");
  assert.equal(files.length, 1);
});

test("episode action validates the brief, submits no jobs, and refuses overwrite", async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "mesh-episode-"));
  const contentDir = path.join(root, "content");
  let providerCalls = 0;
  const resolveSourceRef = async (id: string) => ({ title: `Источник ${id}`, url: `https://fixture.invalid/${id}` });
  const result = await createEpisodeFromBrief({ brief: briefFixture(), slug: "approved-topic-v1", contentDir, writeScript: async () => scriptFixture(), resolveSourceRef, onProviderJob: () => { providerCalls += 1; } });
  assert.equal(await fs.pathExists(result.path), true);
  assert.equal(providerCalls, 0);
  assert.equal(result.episode.brief_ref.brief_id, briefFixture().brief_id);
  await assert.rejects(() => createEpisodeFromBrief({ brief: briefFixture(), slug: "approved-topic-v1", contentDir, writeScript: async () => scriptFixture(), resolveSourceRef, onProviderJob: () => { providerCalls += 1; } }), /already exists/i);
});

function revisions() { return { packet_id: "packet-1", packet_revision_hash: "a".repeat(64), evidence_revision_hash: "b".repeat(64) }; }
function approval(action: string, current: ReturnType<typeof revisions>, at: string) { return { schema_version: 2, approval_id: `${action}-${at}`, action, owner: "owner", at, ...current }; }

function scoreField(value: number) { return { value, rationale: "fixture evidence", evidence_refs: ["source-1"], confidence: 1 }; }
function trendScore() { return { freshness: scoreField(5), audience_heat: scoreField(4), absurdity: scoreField(4), evidence_strength: scoreField(5), visual_punch: scoreField(4), repeatability: scoreField(5), brand_nonintrusion: scoreField(5), legal_safety: scoreField(5), production_cost: scoreField(3), total: 42.4 }; }
function claimFixture() { return { claim_id: "c01", normalized_claim: "Компания выпустила тестовое устройство", source_refs: ["source-1", "source-2", "source-3"], evidence_excerpts: ["Официальная запись подтверждает выпуск"], snapshot_hashes: ["1".repeat(64)], source_roles: ["primary", "independent", "independent"], confidence: 1, contradictions: [], unknowns: [], intended_narration_use: "Факт выпуска", intended_visual_use: "Официальный proof frame" }; }
function visualPlan() { return { profile_id: "generated_news_fact_story", profile_version: 1, concrete_state_count: 8, proof_frames: ["source-1"], continuity_groups: ["device"], banner_fit: "no_change", success_oracle: ["Устройство и proof frame читаются"], states: [{ id: "v01", narration_goal: "Показать хук", visual_nouns: ["устройство", "коробка"], proof_refs: ["source-1"], continuity_group: "device" }, { id: "v02", narration_goal: "Показать подтверждение", visual_nouns: ["официальная запись"], proof_refs: ["source-2"], continuity_group: null }] }; }
function packetFixture() {
  return {
    schema_version: 2, packet_id: "packet-1", packet_revision_hash: "a".repeat(64), evidence_revision_hash: "b".repeat(64), run_status: "partial", review_summary: "Проверенный безопасный пакет", required_approvals: ["editorial"],
    candidate: {
      schema_version: 2, id: "candidate-1", cluster_id: "cluster-1", slug: "approved-topic", title: "Компания выпустила тестовое устройство", topic_family: "technology",
      series: { lane_id: "generated_news_fact_story", rationale: "Проверенная новостная микроистория" }, format_id: "generated_news_fact_story", source_item_ids: ["source-1", "source-2", "source-3"], source_families: ["official_record", "tech_press_ru", "international_press"], claims: [claimFixture()], contradictions: [], unknowns: [],
      editorial: { hook: "Это устройство появилось внезапно", why_now: "Выпуск подтверждён сегодня", why_interesting: "Неожиданный механизм", story_spine: ["выпуск", "подтверждение", "последствие"], twist: "Самая странная функция оказалась официальной" }, visual_plan: visualPlan(),
      risk: { policy_version: 1, flags: [], matched_rule_ids: [], derived_actions: [], enhanced_review_required: false, hard_blocked: false, synthetic_media_label_needed: false, rationale: ["Нет материальных флагов"] },
      production: { uncertainty: "low", experiment_axis: "none", cost_band: "medium", first_smoke: "Проверить читаемость proof frame", success_oracle: ["Хук и доказательство понятны"], stop_conditions: ["Proof frame не читается"] },
      trend_score: trendScore(), evidence_confidence: 1, coverage_confidence: 1, risk_penalties: [], selection_score: 42.4, pool_disposition: "safe_eligible", shortlist_role: "safe_01", gate_results: [{ gate: "minimum_evidence", pass: true, reason: "primary plus two independent" }],
    },
  };
}
function briefFixture() {
  return { schema_version: 2, brief_id: "1".repeat(32), packet_id: "packet-1", packet_revision_hash: "a".repeat(64), evidence_revision_hash: "b".repeat(64), approval_ids: ["approval-1"], generated_at: "2026-07-13T09:01:00.000Z", locked_claims: [claimFixture()], series_and_format: { lane_id: "generated_news_fact_story", format_id: "generated_news_fact_story" }, editorial_angle: packetFixture().candidate.editorial, visual_plan: visualPlan(), source_refs: ["source-1", "source-2", "source-3"], trend_score: trendScore() };
}
function scriptFixture() {
  return { title: "Странное устройство появилось официально", narration: "Секунду: компания действительно выпустила это странное устройство, и официальный документ уже лежит в открытом доступе. Сначала все решили, что это шутка или ранний концепт. Но две независимые редакции сверили дату, модель и описание функции. Устройство оказалось настоящим, просто его главная возможность звучит так, будто инженер спорил с маркетологом до утра. [short pause] Самое смешное — спор выиграл инженер, а покупателям теперь придётся объяснять друзьям, зачем эта кнопка вообще существует. Источники показываем в кадре, без выдуманных цифр и громких обещаний. Все формулировки остаются точными, а спорные детали в сценарий не попадают.", tts_style: "Сухая серьёзная подача с короткой паузой перед панчлайном", sentence_claim_ids: [{ sentence: "Компания выпустила устройство", claim_ids: ["c01"] }, { sentence: "Источники подтвердили выпуск", claim_ids: ["c01"] }] };
}
```

- [ ] **Step 3: Run the approval tests and verify failure**

```powershell
node --import tsx --test tests/scoutApprovals.test.ts
```

Expected: FAIL because approval/brief/episode modules and schema fields are absent.

- [ ] **Step 4: Implement decision records and derived state**

`recordPacketDecision` acquires the run lock, validates the current packet, requires a non-empty reason for reject, refuses enhanced approval before editorial approval, binds every record to packet/evidence hashes, and appends one JSON object to `decisions.jsonl`. It also appends a safe steering entry to `run-state.json`. Reserve never advances derived state. Reject sets derived rejected for that exact revision.

`deriveApprovalState` applies this order: revision mismatch => stale; latest editorial rejection => rejected; no editorial approval => pending; enhanced not required => eligible; enhanced rejection => rejected; no enhanced approval => pending; missing wording/current-status binding => pending; current-status age over 12 hours => stale; otherwise eligible.

- [ ] **Step 5: Implement idempotent topic briefs**

Use this exact ID function:

```ts
function briefId(packetId: string, packetRevisionHash: string, evidenceRevisionHash: string, approvalIds: string[]) {
  return createHash("sha256").update(packetId + packetRevisionHash + evidenceRevisionHash + [...approvalIds].sort().join("")).digest("hex").slice(0, 32);
}
```

`createTopicBrief` recalculates derived state under the run lock, refuses rejected/stale/pending state, writes ``topic-briefs/${packetId}.${briefId}.v1.json`` only when absent, and atomically updates `topic-briefs/index.json`. The index keeps every tuple and a `latest_eligible_by_packet` map; it never deletes old revisions.

- [ ] **Step 6: Implement the approved fact-packet writer and episode handoff**

`runApprovedFactPacketWriter` is outside the Scout ranking budget and is callable only with a current eligible `TopicBrief`. It invokes `opencode-go/glm-5.1` through `opencode.cmd run --pure --variant low`, supplies locked claims/visual states and `prompts/script-writer.md`, requires JSON-only 85–115-word Russian narration, one hook in the first two seconds, one micro-pause, claim IDs per sentence, and no new facts. One schema retry is allowed; no reasoning/raw prompt/provider payload is retained. Validate every returned claim ID against `brief.locked_claims`, then run a local DeepSeek critique only if the existing approved script route already requires it; do not browse.

Add to `EpisodeSchema`:

```ts
brief_ref: z.strictObject({ brief_id: z.string(), packet_id: z.string(), packet_revision_hash: z.string(), evidence_revision_hash: z.string(), approval_ids: z.array(z.string()) }).optional(),
research_revision: z.strictObject({ generated_at: z.string().datetime(), source_run_id: z.string().optional() }).optional(),
```

`createEpisodeFromBrief` slugifies only the explicit owner slug, writes ``content/episode.${slug}.yaml``, resolves each retained source ID through `resolveSourceRef` backed by the current run’s strict source-item index, maps locked claims/sources/legal review/trend score/series/format/visual states into the episode contract, validates with `EpisodeSchema`, writes atomically, and checks `fs.pathExists` before any writer call. It accepts no overwrite flag. The callback `onProviderJob` exists only as a test oracle and is never invoked.

- [ ] **Step 7: Add internal CLI diagnostics for decisions and episode creation**

Add commands `scout-approve`, `scout-reject`, `scout-reserve`, `scout-brief`, and `scout-create-episode`. They take run/packet identifiers and explicit owner/reason/slug inputs, call the same services as Studio, and expose no scheduler or media flags. Enhanced approval is a separate `--enhanced` action and requires `--current-status-checked-at` plus wording checksum derived inside the service, not supplied as arbitrary trusted state.

- [ ] **Step 8: Run approval, episode validation, type, and full tests**

```powershell
node --import tsx --test tests/scoutApprovals.test.ts
npm.cmd run validate:episodes
npm.cmd run typecheck
npm.cmd test
```

Expected: PASS; no provider-job fixture was called.

- [ ] **Step 9: Commit approvals and handoff**

```powershell
git add src/scout/approvals.ts src/scout/episodeWriter.ts src/scout/episodeFromBrief.ts src/scout/contracts.ts src/lib/schema.ts src/cli.ts tests/scoutApprovals.test.ts
git diff --cached --check
git commit -m "feat: approve research packets and create episodes"
```

Expected: one scoped commit.

### Task 11: Harden Content Studio and expose a typed Research API

**Files:**
- Create: `src/studio/security.ts`
- Create: `src/studio/researchQueue.ts`
- Create: `src/studio/researchApi.ts`
- Modify: `src/studio/server.ts`
- Test: `tests/studioResearch.test.ts`

**Interfaces:**
- Consumes: `runResearchMesh`, run-state cancellation/recovery, approval/brief/episode services, configured allowed roots/extensions, and direct typed request bodies.
- Produces: `assertLoopbackHost`, `assertMutationRequest`, `readBoundedJson`, `resolveAllowedFile`, `ResearchQueue`, `createResearchApi`, and secured HTTP routes under `/api/research`.

- [ ] **Step 1: Write failing HTTP security and lifecycle tests**

Create `tests/studioResearch.test.ts` using `createStudioServer` on `127.0.0.1` and port `0`. Parse the CSRF token from the returned bootstrap JSON and assert:

```ts
test("Studio rejects non-loopback host at construction", () => {
  assert.throws(() => createStudioServer({ cwd: process.cwd(), host: "0.0.0.0", port: 4317, maxConcurrent: 1, maxQueued: 20 }), /loopback/i);
});

test("mutations require exact Origin, CSRF, JSON, and a body at most 64 KiB", async () => {
  const studio = await startFixtureStudio();
  await assertStatus(studio.url + "/api/research/runs", { method: "POST", headers: { "content-type": "application/json" }, body: "{}" }, 403);
  await assertStatus(studio.url + "/api/research/runs", { method: "POST", headers: { origin: "http://evil.example", "content-type": "application/json", "x-pokrov-studio-csrf": studio.csrf }, body: "{}" }, 403);
  await assertStatus(studio.url + "/api/research/runs", { method: "POST", headers: { origin: studio.url, "content-type": "text/plain", "x-pokrov-studio-csrf": studio.csrf }, body: "{}" }, 415);
  await assertStatus(studio.url + "/api/research/runs", { method: "POST", headers: { origin: studio.url, "content-type": "application/json", "x-pokrov-studio-csrf": studio.csrf }, body: JSON.stringify({ value: "x".repeat(65536) }) }, 413);
  await studio.close();
});

test("CSP uses nonces and no broad unsafe-inline", async () => {
  const studio = await startFixtureStudio();
  const response = await fetch(studio.url);
  const csp = response.headers.get("content-security-policy") ?? "";
  assert.match(csp, /script-src 'nonce-[^']+'/);
  assert.match(csp, /style-src 'nonce-[^']+'/);
  assert.doesNotMatch(csp, /unsafe-inline/);
  await studio.close();
});

test("research actions never enter the production command queue", async () => {
  const studio = await startFixtureStudio();
  const before = await (await fetch(studio.url + "/api/jobs")).json();
  await studio.mutate("/api/research/runs", { action: "start" });
  const after = await (await fetch(studio.url + "/api/jobs")).json();
  assert.deepEqual(after.queue.jobs, before.queue.jobs);
  await studio.close();
});
```

Add tests for queued cancellation, running cancellation, no new work after abort, restart recovery to `failed/INTERRUPTED`, retry with `parent_run_id`, cancellation-versus-final-rename race, file traversal, disallowed extension, symlink/junction escape, and private-local open returning `204` with no bytes or URL. Inject a fake OS opener and assert it receives only an allowlisted realpath.

- [ ] **Step 2: Run Studio tests and verify failure**

```powershell
node --import tsx --test tests/studioResearch.test.ts
```

Expected: FAIL because Studio currently lacks all listed controls/routes.

- [ ] **Step 3: Implement the Studio security helpers**

`assertLoopbackHost` accepts only `127.0.0.1` and `::1`; V1 startup rejects `localhost`, LAN IPs, and wildcard hosts to avoid DNS/bind ambiguity. The exact allowed Origin is derived from the bound address and actual port.

`readBoundedJson` requires `application/json`, reads at most 65,536 bytes, destroys the request on overflow, rejects invalid JSON, and returns a Zod-parsed route body. `assertMutationRequest` uses `crypto.timingSafeEqual` for the in-memory CSRF token and exact Origin.

`resolveAllowedFile` calls `fs.realpath` on root and target, requires target to be strictly under one of `runs/scout`, `content`, or configured preview roots, validates the lowercase extension, and walks each path segment with `lstat` to reject symbolic links, junctions, and reparse-point escapes. Source URLs never become local paths.

Every HTML response gets a fresh 32-byte base64url nonce and this policy:

```text
default-src 'self'; base-uri 'none'; frame-ancestors 'none'; object-src 'none'; form-action 'self'; img-src 'self' data:; media-src 'self'; connect-src 'self'; script-src 'nonce-${nonce}'; style-src 'nonce-${nonce}'
```

- [ ] **Step 4: Implement the cancellable ResearchQueue**

Use a separate queue from `ProductionQueue`. It has statuses `queued | running | succeeded | failed | cancelled`, max concurrency one, max queued five, and each job owns one `AbortController`. Cancelling queued removes it and writes terminal cancelled state. Cancelling running aborts the controller and waits for the orchestrator’s five-second subprocess grace. `drain()` never starts a job whose signal is aborted. On server startup call `recoverInterruptedRuns(runs/scout)` before accepting mutations.

- [ ] **Step 5: Implement typed research routes**

Use direct service calls, not shell commands or arbitrary argument arrays:

```text
GET  /api/research/runs
GET  /api/research/runs/:runId
GET  /api/research/runs/:runId/candidates
GET  /api/research/runs/:runId/packets/:slot
POST /api/research/runs                    { action: "start" }
POST /api/research/runs/:runId/cancel      {}
POST /api/research/runs/:runId/retry       {}
POST /api/research/runs/:runId/decisions   { packetId, action, reason? }
POST /api/research/runs/:runId/briefs      { packetId }
POST /api/research/runs/:runId/episodes    { briefId, slug }
POST /api/research/private-local/open      { runId, localRefId }
```

Validate run/packet/brief/slug IDs with anchored allowlist regexes and resolve them through retained indexes, never direct paths. `start` accepts no source URL/model/command fields. `retry` creates a new run ID and parent link. Decision actions are `approve_editorial`, `approve_enhanced`, `reject`, and `reserve`; reject requires reason. Episode route calls no provider queue. Private-local open checks Origin/CSRF/allowlisted realpath, calls the injected host OS opener, and returns `204` with no body.

- [ ] **Step 6: Run Studio security, type, and full tests**

```powershell
node --import tsx --test tests/studioResearch.test.ts
npm.cmd run typecheck
npm.cmd test
```

Expected: PASS.

- [ ] **Step 7: Commit the secured Research API**

```powershell
git add src/studio/security.ts src/studio/researchQueue.ts src/studio/researchApi.ts src/studio/server.ts tests/studioResearch.test.ts
git diff --cached --check
git commit -m "feat: secure Studio research operations"
```

Expected: one scoped commit.

### Task 12: Build the Research Inbox operator UI

**Files:**
- Create: `src/studio/page.ts`
- Modify: `src/studio/server.ts`
- Modify: `tests/productionTools.test.ts`
- Modify: `tests/studioResearch.test.ts`

**Interfaces:**
- Consumes: secured JSON routes, CSRF bootstrap token, current run/packet/candidate schemas.
- Produces: `indexHtml({ csrfToken, nonce }): string` and a Research Inbox with run status, featured packets, full candidate pool, source health, evidence, actions, and explicit no-paid-media state.

- [ ] **Step 1: Add failing page-contract and XSS tests**

Add assertions:

```ts
const html = indexHtml({ csrfToken: "csrf-fixture", nonce: "nonce-fixture" });
assert.match(html, /Research Inbox/);
assert.match(html, /Найти темы/);
assert.match(html, /SAFE #1/);
assert.match(html, /SAFE #2/);
assert.match(html, /AI EXPERIMENT/);
assert.match(html, /Платные медиа: не запускаются/);
assert.match(html, /x-pokrov-studio-csrf/i);
assert.doesNotMatch(html, /\.innerHTML\s*=/);
assert.match(html, /textContent/);
assert.match(html, /nonce="nonce-fixture"/);
```

In the HTTP fixture, return a source title `</script><img src=x onerror=alert(1)>`, refresh the page data through a browser DOM fixture or the exported renderer helper, and assert it remains text, not an element.

- [ ] **Step 2: Run page tests and verify failure**

```powershell
node --import tsx --test tests/productionTools.test.ts tests/studioResearch.test.ts
```

Expected: FAIL because the current page has no inbox and assigns dynamic HTML through `innerHTML`.

- [ ] **Step 3: Move page generation to a nonce-aware module**

Create `page.ts`; keep `server.ts` as a re-export for existing imports. Inject both nonce and CSRF token as JSON escaped with `<` replaced by `\u003c`. Put the same nonce on the single `<style>` and `<script>` blocks.

Replace every dynamic `innerHTML` write, including episodes/runs/jobs, with `document.createElement`, `replaceChildren`, and `textContent`. Event handlers use `addEventListener`; no untrusted string is interpolated into executable code or CSS.

- [ ] **Step 4: Implement the approved Inbox views and actions**

Add navigation for `Research Inbox`, `Эпизоды`, `Прогоны`, and `Очередь`. The research view contains:

- `Найти темы` and refresh controls;
- phase/progress, discovered/extracted/cluster/candidate/packet counts, cancellation, parent retry link, no-paid-media pill;
- source-group health and degraded adapter detail;
- three featured slots with missing-role explanations;
- packet detail with hook, story spine, claims/evidence links, score fields/rationales, contradictions, unknowns, visual states, risk rules, required approvals, cost band, first smoke, and selection rationale;
- 20-row candidate table filtered by source family, topic family, lane, risk, evidence state, and format;
- editorial approve, enhanced approve, reject-with-reason, reserve, create brief, and create episode actions gated by current state.

Poll only while a research job is queued/running and stop polling at terminal state. Render `partial` and `failed` with explicit issue codes; never label them successful.

- [ ] **Step 5: Run page, Studio, type, and full tests**

```powershell
node --import tsx --test tests/productionTools.test.ts tests/studioResearch.test.ts
npm.cmd run typecheck
npm.cmd test
```

Expected: PASS.

- [ ] **Step 6: Commit the Research Inbox**

```powershell
git add src/studio/page.ts src/studio/server.ts tests/productionTools.test.ts tests/studioResearch.test.ts
git diff --cached --check
git commit -m "feat: add Studio Research Inbox"
```

Expected: one scoped commit.

---

## Delivery Slice 3 — Risk, Editorial Enrichment, Scoring, Selection, And Orchestration

### Task 6: Add the versioned fail-closed risk engine

**Files:**
- Create: `src/scout/risk.ts`
- Create: `tests/fixtures/scout/risk-cases.json`
- Test: `tests/scoutRisk.test.ts`

**Interfaces:**
- Consumes: registered source taxonomy, retained claim text/evidence, person/entity records, Kimi flags, DeepSeek flags, and `config.risk_policy`.
- Produces: `extractRiskSignals(input): RiskSignal[]`, `evaluateRiskPolicy(input): Candidate["risk"]`, and `resolveRiskDecision(input): RevisionBoundRiskDecision`.

- [ ] **Step 1: Write positive, negative, ambiguous, Russian, and English fixtures**

Create `tests/fixtures/scout/risk-cases.json` with one object per exact ID below. Each object contains `title`, `claims`, `source_tags`, `entity_records`, `kira_flags`, `deepseek_flags`, and `expected` (`flags`, `enhanced`, `hard_blocked`, `uncertain`):

```text
ru_politics_positive
en_politics_positive
ru_crime_charge_not_conviction
en_court_ruling
ru_private_accusation
en_private_accusation
ru_minor_identifiable
en_minor_nonidentifying
ru_graphic_explicit
en_graphic_implied
copyright_medium
reused_content_high
public_figure_neutral
negative_game_patch
negative_fictional_crime_word
ambiguous_person_status
ambiguous_accusation
ambiguous_minor_age
```

The negative game-patch fixture must contain the word `убийство` only inside a fictional game mechanic and expect no real-world crime flag. The charge fixture must preserve `обвинён`, not rewrite it as `осуждён`.

- [ ] **Step 2: Write the failing policy test**

```ts
import assert from "node:assert/strict";
import test from "node:test";
import fs from "fs-extra";
import path from "node:path";
import { evaluateRiskPolicy, extractRiskSignals } from "../src/scout/risk";
import { readScoutConfig } from "../src/scout/config";

test("risk fixtures match versioned fail-closed outcomes", async () => {
  const config = await readScoutConfig();
  const cases = await fs.readJson(path.resolve("tests/fixtures/scout/risk-cases.json"));
  for (const fixture of cases) {
    const signals = extractRiskSignals(fixture);
    const result = evaluateRiskPolicy({ signals, policy: config.risk_policy });
    assert.deepEqual([...result.flags].sort(), [...fixture.expected.flags].sort(), fixture.id);
    assert.equal(result.enhanced_review_required, fixture.expected.enhanced, fixture.id);
    assert.equal(result.hard_blocked, fixture.expected.hard_blocked, fixture.id);
    assert.equal(result.derived_actions.includes("resolve_classification"), fixture.expected.uncertain, fixture.id);
  }
});

test("LLM flags can add uncertainty but cannot clear deterministic matches", async () => {
  const config = await readScoutConfig();
  const signals = extractRiskSignals({ title: "Суд предъявил обвинение", claims: ["Публичной фигуре предъявлено обвинение"], source_tags: ["court"], entity_records: [{ kind: "person", visibility: "public" }], kimi_flags: [], deepseek_flags: [] });
  const result = evaluateRiskPolicy({ signals: [...signals, { flag: "crime", state: "not_matched", producer: "deepseek", evidence_refs: [] }], policy: config.risk_policy });
  assert.equal(result.flags.includes("court"), true);
  assert.equal(result.flags.includes("accusation_public_figure"), true);
});
```

- [ ] **Step 3: Run the test and verify failure**

```powershell
node --import tsx --test tests/scoutRisk.test.ts
```

Expected: FAIL because `risk.ts` is absent.

- [ ] **Step 4: Implement deterministic signal producers and policy evaluation**

Define versioned Russian/English matchers as arrays of `{ id, include, exclude }`. Required categories are politics, crime, court, accusation/charge/ruling/conviction/correction, private/public person, minor, graphic explicit/implied, copyright low/medium/high, and reused-content low/medium/high. Every match returns `{ flag, state: "matched" | "not_matched" | "uncertain", producer, evidence_refs }`.

Union producers with this exact rule:

```ts
function mergeSignalStates(states: Array<"matched" | "not_matched" | "uncertain">) {
  if (states.includes("matched")) return "matched" as const;
  if (states.includes("uncertain")) return "uncertain" as const;
  return "not_matched" as const;
}
```

Deterministic `matched` cannot be cleared by either model. Producer disagreement marks classification uncertain. Uncertain accusation/minor/private-person/graphic blocks the candidate from the valid 20. Uncertain politics/crime/court applies enhanced requirements immediately and still blocks episode creation until revision-bound resolution.

Derived outcomes are exact: hard block emits `BLOCKED_LEGAL`; enhanced flags set `enhanced_review_required`; medium copyright/reuse forces `legal_safety <= 3` and `pool_only`; photoreal reconstruction of a real public event/person sets `synthetic_media_label_needed`. Store policy version, matcher IDs, evidence refs, flags, actions, and rationale.

- [ ] **Step 5: Run risk, type, and full tests**

```powershell
node --import tsx --test tests/scoutRisk.test.ts
npm.cmd run typecheck
npm.cmd test
```

Expected: PASS.

- [ ] **Step 6: Commit risk policy**

```powershell
git add src/scout/risk.ts tests/scoutRisk.test.ts tests/fixtures/scout/risk-cases.json
git diff --cached --check
git commit -m "feat: enforce versioned scout risk policy"
```

Expected: one scoped commit.

### Task 7: Add bounded OpenCode editorial and critique calls

**Files:**
- Create: `src/scout/opencode.ts`
- Modify: `prompts/agent-research.md`
- Test: `tests/scoutOpenCode.test.ts`

**Interfaces:**
- Consumes: batches of at most ten evidence-locked candidate inputs, caller `AbortSignal`, run-wide `BudgetCounter`, and an injectable command runner.
- Produces: `runKimiEditorialBatch(args): Promise<KimiEditorial[]>`, `runDeepSeekCritiqueBatch(args): Promise<DeepSeekCritique[]>`, `reconcileAbsurdity(args): Promise<ReconciledAbsurdity>`, and safe `LlmJobSummary` records.

- [ ] **Step 1: Write failing parser, retry, and cancellation tests**

Create `tests/scoutOpenCode.test.ts`:

```ts
import assert from "node:assert/strict";
import test from "node:test";
import { runKimiEditorialBatch } from "../src/scout/opencode";

test("OpenCode parses message content and retries malformed JSON once", async () => {
  const outputs = ["not json", JSON.stringify({ items: [{ candidate_id: "c1", hook: "Hook", why_now: "Now", why_interesting: "Mechanism", story_spine: ["A", "B"], twist: "B", absurdity_score: 4, absurdity_rationale: "Verified incongruity", visual_nouns: ["device"], suggested_lane_id: "generated_news_fact_story", suggested_format_id: "generated_news_fact_story", risk_flags: [] }] })];
  let calls = 0;
  const result = await runKimiEditorialBatch({ evidencePackets: [{ candidate_id: "c1", claims: [], allowed_lane_ids: ["generated_news_fact_story"] }], signal: new AbortController().signal, maxRetries: 1, runCommand: async () => ({ stdout: outputs[calls++], stderr: "", exitCode: 0, latencyMs: 10 }) });
  assert.equal(calls, 2);
  assert.equal(result.items[0].candidate_id, "c1");
  assert.equal(result.jobs.length, 2);
});

test("exhausted schema retry returns BLOCKED_EDITORIAL", async () => {
  const result = await runKimiEditorialBatch({ evidencePackets: [{ candidate_id: "c1", claims: [], allowed_lane_ids: ["generated_news_fact_story"] }], signal: new AbortController().signal, maxRetries: 1, runCommand: async () => ({ stdout: "{}", stderr: "", exitCode: 0, latencyMs: 10 }) });
  assert.deepEqual(result.blocked_candidate_ids, ["c1"]);
  assert.equal(result.issue, "BLOCKED_EDITORIAL");
});

test("cancelled calls do not schedule a retry", async () => {
  const controller = new AbortController();
  controller.abort();
  let calls = 0;
  await assert.rejects(() => runKimiEditorialBatch({ evidencePackets: [{ candidate_id: "c1", claims: [], allowed_lane_ids: ["generated_news_fact_story"] }], signal: controller.signal, maxRetries: 1, runCommand: async () => { calls += 1; return { stdout: "", stderr: "", exitCode: 130, latencyMs: 1 }; } }), /aborted/i);
  assert.equal(calls, 0);
});
```

- [ ] **Step 2: Run the OpenCode tests and verify failure**

```powershell
node --import tsx --test tests/scoutOpenCode.test.ts
```

Expected: FAIL because `opencode.ts` is absent.

- [ ] **Step 3: Implement strict model schemas and command runner**

Use Zod strict schemas. Kimi may output only candidate ID, hook, why-now, why-interesting, story spine, twist, visual nouns, suggested registered lane/format, absurdity score/rationale, and advisory risk flags. DeepSeek may output only candidate ID, claim critique, contradiction flags, accept/counter absurdity score, safety flags, and selector critique. Neither schema accepts new facts or URLs.

The default runner uses:

```ts
const subprocess = execa("opencode.cmd", ["run", "--pure", "--model", model, "--variant", "low", "Read the attached evidence packet and return one JSON object only.", "--file", promptPath], {
  cwd: process.cwd(),
  reject: false,
  windowsHide: true,
  cancelSignal: signal,
  forceKillAfterDelay: 5000,
  timeout: 120000,
});
```

Write the stable prefix and dynamic evidence suffix to a temporary OS directory, remove that directory in `finally`, and persist only provider/model, latency, stable-prefix SHA-256, optional token counts present in structured output, and success/schema-error/cancelled state. Do not persist prompt text, stdout, stderr, raw provider events, or reasoning.

Batch at most ten candidates, permit one small schema retry, count every initial/retry/reconciliation call against `max_opencode_calls`, and stop scheduling when the signal aborts or the budget is exhausted. Validate suggested lane/format against config and discard invalid suggestions.

For absurdity: Kimi proposes 0–5, DeepSeek accepts or counters. Difference at most one uses the lower value. Difference greater than one gets one reconciliation call containing both rationales and the same locked evidence. A remaining difference greater than one emits `UNRESOLVED_EDITORIAL_SCORE` and excludes the candidate from the valid 20.

- [ ] **Step 4: Replace the research prompt contract**

Update `prompts/agent-research.md` to require 20 pool candidates, two `safe_production`, one `ai_video_experiment`, zero reserve, evidence-ref-only facts, mutually exclusive `pool_disposition`, nullable `shortlist_role`, bounded experiment smoke, enhanced-risk wording, and no episode YAML. Remove the old recommendation schema and the instruction that snapshots are collected later.

- [ ] **Step 5: Run OpenCode, prompt audit, type, and full tests**

```powershell
node --import tsx --test tests/scoutOpenCode.test.ts
python ..\scripts\agent_context_packet_audit.py prompts\agent-research.md
npm.cmd run typecheck
npm.cmd test
```

Expected: focused tests PASS; context packet audit PASS; full suite PASS.

- [ ] **Step 6: Commit the editorial layer**

```powershell
git add src/scout/opencode.ts prompts/agent-research.md tests/scoutOpenCode.test.ts
git diff --cached --check
git commit -m "feat: add bounded scout editorial enrichment"
```

Expected: one scoped commit.

### Task 8: Implement format routing, deterministic scoring, and the diversity selector

**Files:**
- Create: `src/scout/formatProfiles.ts`
- Create: `src/scout/scoring.ts`
- Create: `src/scout/selector.ts`
- Modify: `src/lib/trendScoring.ts`
- Test: `tests/scoutScoring.test.ts`
- Test: `tests/scoutSelector.test.ts`

**Interfaces:**
- Consumes: evidence-eligible clusters, risk output, Kimi/DeepSeek editorial output, config visual profiles/penalties, and the current canonical weighted formula.
- Produces: `routeFormat(input, config): FormatRoute`, `computeHeatPercentiles(items): HeatObservation[]`, `scoreCandidate(input): ScoredCandidateResult`, `auditTrendTotal(score): boolean`, and `selectResearchPool<T extends SelectorCandidate>(candidates: T[], config): { pool: T[]; shortlist: Shortlist; assigned: Array<T & { shortlist_role: "safe_01" | "safe_02" | "experiment_01" }>; issues: IssueCode[] }`. `ScoredCandidateResult` contains exactly `trend_score`, `evidence_confidence`, `coverage_confidence`, `risk_penalties`, `selection_score`, `pool_disposition`, and `gate_results`; the orchestrator merges it into the typed candidate identity/editorial/evidence record and builds `ProductionPacket` files from assigned full candidates.

`SelectorCandidate` is the exact minimal view `{ id, cluster_id, registered_domain, source_families, series: { lane_id }, pool_disposition, shortlist_role, selection_score, risk: { hard_blocked }, production: { uncertainty, experiment_axis } }`; selection code cannot inspect titles or LLM prose.

- [ ] **Step 1: Write failing scoring tests**

Create `tests/scoutScoring.test.ts`:

```ts
import assert from "node:assert/strict";
import test from "node:test";
import { scoreCandidate } from "../src/scout/scoring";

test("all numeric fields follow deterministic rubrics and exact arithmetic", () => {
  const scored = scoreCandidate({
    now: "2026-07-13T12:00:00.000Z", publishedAt: "2026-07-13T00:00:00.000Z",
    heatPercentile: 0.92, independentTrendSignals: 2, absurdity: { value: 4, rationale: "verified", evidenceRefs: ["claim-1"] },
    evidenceShape: "primary_plus_two_independent", visual: { formatId: "generated_news_fact_story", concreteStates: 16, proof: true, continuity: true },
    laneClusterCount: 3, laneStatus: "approved", bannerFit: "no_change", risk: { enhanced: false, mediumRights: false, hardBlocked: false },
    generatedAssetCount: 18, fragileMultiModel: false, evidenceRefs: ["source-1", "source-2", "source-3"], targetSourceCount: 2,
  });
  assert.equal(scored.trend_score.freshness.value, 5);
  assert.equal(scored.trend_score.audience_heat.value, 5);
  assert.equal(scored.trend_score.evidence_strength.value, 5);
  assert.equal(scored.trend_score.visual_punch.value, 5);
  assert.equal(scored.trend_score.production_cost.value, 3);
  assert.equal(scored.trend_score.total, 44.9);
  assert.equal(scored.evidence_confidence, 1);
  assert.equal(scored.coverage_confidence, 1);
  assert.equal(scored.selection_score, 44.9);
});

test("enhanced and experiment penalties cannot replace hard gates", () => {
  const scored = scoreCandidate({ now: "2026-07-13T12:00:00.000Z", publishedAt: "2026-07-10T00:00:00.000Z", heatPercentile: 0.5, independentTrendSignals: 1, absurdity: { value: 3, rationale: "verified", evidenceRefs: [] }, evidenceShape: "below_minimum", visual: { formatId: "kira_story", concreteStates: 4, proof: true, continuity: true }, laneClusterCount: 2, laneStatus: "approved", bannerFit: "minor_adjustment", risk: { enhanced: true, mediumRights: false, hardBlocked: false }, generatedAssetCount: 4, fragileMultiModel: false, evidenceRefs: [], targetSourceCount: 3 });
  assert.equal(scored.evidence_confidence, 0);
  assert.equal(scored.pool_disposition, "pool_only");
  assert.equal(scored.gate_results.some((gate) => gate.gate === "minimum_evidence" && !gate.pass), true);
});
```

- [ ] **Step 2: Write failing selector tests**

Create `tests/scoutSelector.test.ts`:

```ts
import assert from "node:assert/strict";
import test from "node:test";
import { selectResearchPool } from "../src/scout/selector";
import { readScoutConfig } from "../src/scout/config";

test("selector returns twenty clusters, two safe packets, and one experiment", async () => {
  const config = await readScoutConfig();
  const candidates = Array.from({ length: 24 }, (_, index) => candidate(index, index < 18 ? "safe_eligible" : index < 21 ? "experiment_eligible" : "pool_only"));
  const selected = selectResearchPool(candidates, config);
  assert.equal(selected.pool.length, 20);
  assert.deepEqual(selected.shortlist.missing_roles, []);
  assert.deepEqual(selected.assigned.map((candidate) => candidate.shortlist_role).sort(), ["experiment_01", "safe_01", "safe_02"]);
  assert.equal(new Set(selected.assigned.map((candidate) => candidate.id)).size, 3);
  assert.equal(new Set(selected.assigned.map((candidate) => candidate.cluster_id)).size, 3);
});

test("selector returns honest missing roles without filler", async () => {
  const config = await readScoutConfig();
  const selected = selectResearchPool(Array.from({ length: 19 }, (_, index) => candidate(index, "safe_eligible")), config);
  assert.equal(selected.pool.length, 19);
  assert.equal(selected.shortlist.roles.experiment_01, null);
  assert.equal(selected.issues.includes("INSUFFICIENT_POOL"), true);
  assert.equal(selected.issues.includes("MISSING_EXPERIMENT_ROLE"), true);
});

function candidate(index: number, disposition: "safe_eligible" | "experiment_eligible" | "pool_only") {
  const families = ["community_ru", "gaming_press_ru", "tech_press_ru", "international_press"] as const;
  const lanes = ["generated_news_fact_story", "patch_notes_therapy", "steam_stats_anomaly", "kira_story"] as const;
  const family = families[index % families.length];
  const lane = lanes[index % lanes.length];
  return { id: `candidate-${index}`, cluster_id: `cluster-${index}`, registered_domain: `source-${index % 6}.fixture.invalid`, source_families: [family], series: { lane_id: lane }, pool_disposition: disposition, shortlist_role: null, selection_score: 100 - index, risk: { hard_blocked: false }, production: { uncertainty: disposition === "experiment_eligible" ? "medium" : "low", experiment_axis: disposition === "experiment_eligible" ? "continuity_edit" : "none" } };
}
```

- [ ] **Step 3: Run scoring/selector tests and verify failure**

```powershell
node --import tsx --test tests/scoutScoring.test.ts tests/scoutSelector.test.ts
```

Expected: FAIL because the new modules are absent.

- [ ] **Step 4: Implement all eight visual profiles and format routing**

`formatProfiles.ts` exposes profiles only for `generated_news_fact_story`, `steam_review_readout`, `patch_notes_therapy`, `steam_stats_anomaly`, `ai_remaster_visual`, `tier_list_absurdity`, `kira_dance`, and `kira_story`. Encode the score-5/4/3 mechanics exactly from the spec. Scores 2/1/0 mean one missing required mechanic, generic/two missing mechanics, and infeasible. Exclude `full_video_parts` and under-study lanes.

`routeFormat` uses registered topic features and evidence types; LLM suggestions are accepted only when the ID exists, is selectable, and its required mechanics are present. No fallback ID is invented.

- [ ] **Step 5: Implement deterministic rubrics and exact selection arithmetic**

Reuse `calculateTopicScore` after mapping the nine named score fields to its `_0_5` input. Store rationale/evidence/confidence beside every field and verify `Math.abs(recalculated - stored) < 0.000001`.

`computeHeatPercentiles` groups comparable numeric metrics by adapter and metric key, ranks values with stable average rank for ties, and persists adapter ID, metric key, raw value, sample size, and percentile in `score_rationale`. Cross-adapter raw counts are never directly compared. Missing comparable metrics uses the rubric’s coverage-only score rather than an invented percentile.

Use exact evidence confidence and `coverage_confidence = Math.min(1, qualifiedEvidenceSourceCount / targetSourceCount)`. Apply only configured non-blocking penalties. Compute `selection_score = trend_score.total * evidence_confidence * coverage_confidence - penaltyTotal`.

Run hard gates before disposition. `safe_eligible` requires evidence at least `0.8`, legal at least `4`, brand at least `4`, visual at least `3`, low uncertainty, no experiment axis, known cost/smoke, registered lane/format, and no material conflict. `experiment_eligible` requires the same factual/legal/brand gates, visual at least `4`, medium uncertainty, one allowed non-none axis, non-empty hypothesis, max three paid calls, max four video seconds, and a non-empty stop condition. Every other valid pool candidate is `pool_only`.

- [ ] **Step 6: Implement stable diversity selection**

Sort by selection score descending, then candidate ID. Fill the pool while enforcing one event cluster, max five candidates per registered domain, and max eight per source family. Do not backfill quarantined/blocked items. Assign `safe_01`, `safe_02`, and `experiment_01` to three distinct IDs/clusters; final three cannot all share a source family or lane. Missing cardinality/coverage/roles emit the exact issue codes and leave nullable roles empty.

- [ ] **Step 7: Run scoring, selector, type, and full tests**

```powershell
node --import tsx --test tests/scoutScoring.test.ts tests/scoutSelector.test.ts
npm.cmd run typecheck
npm.cmd test
```

Expected: PASS.

- [ ] **Step 8: Commit scoring and selector**

```powershell
git add src/scout/formatProfiles.ts src/scout/scoring.ts src/scout/selector.ts src/lib/trendScoring.ts tests/scoutScoring.test.ts tests/scoutSelector.test.ts
git diff --cached --check
git commit -m "feat: score and select research packets"
```

Expected: one scoped commit.

### Task 9: Compose the bounded orchestrator, reports, health command, and CLI exit semantics

**Files:**
- Create: `src/scout/orchestrator.ts`
- Modify: `src/scout/index.ts`
- Modify: `src/scout/reports.ts`
- Modify: `src/scout/search.ts`
- Modify: `src/cli.ts`
- Modify: `package.json`
- Test: `tests/scoutOrchestrator.test.ts`

**Interfaces:**
- Consumes: every service from Tasks 1–8 through an injectable `ResearchServices` object and one shared `AbortController`.
- Produces: `runResearchMesh(options): Promise<ResearchRunResult>`, `runScoutHealth(options): Promise<HealthReport>`, `exitCodeForRun(status): 0 | 2 | 3 | 130`, and compatibility dispatch for `topics`, deprecated `meme_news`, `cuts`, and `kira`.

- [ ] **Step 1: Write failing phase, partial, failure, cap, and CLI-code tests**

Create `tests/scoutOrchestrator.test.ts` with a deterministic service fixture. Assert these exact cases:

```ts
import assert from "node:assert/strict";
import test from "node:test";
import fs from "fs-extra";
import os from "node:os";
import path from "node:path";
import { exitCodeForRun, runResearchMesh } from "../src/scout/orchestrator";
import { fakeResearchServices } from "./support/fakeResearchServices";

test("ready run writes the complete artifact graph atomically", async () => {
  const runDir = await fs.mkdtemp(path.join(os.tmpdir(), "mesh-ready-"));
  const result = await runResearchMesh({ runDir, lane: "topics", services: fakeResearchServices({ clusters: 24, sourceFamilies: 4, safe: 4, experiments: 2 }), now: "2026-07-13T09:00:00.000Z" });
  assert.equal(result.status, "ready");
  assert.equal(result.pool.length, 20);
  assert.equal(result.packets.length, 3);
  for (const file of ["run-state.json", "source-health.json", "shortlist.json", "scout-report.json", "scout-report.md"]) assert.equal(await fs.pathExists(path.join(runDir, file)), true, file);
  assert.equal(await fs.pathExists(path.join(runDir, "packets/safe-01.json")), true);
  assert.equal(await fs.pathExists(path.join(runDir, "packets/safe-02.json")), true);
  assert.equal(await fs.pathExists(path.join(runDir, "packets/experiment-01.json")), true);
});

test("nineteen valid clusters produce partial without placeholder packet", async () => {
  const runDir = await fs.mkdtemp(path.join(os.tmpdir(), "mesh-partial-"));
  const result = await runResearchMesh({ runDir, lane: "topics", services: fakeResearchServices({ clusters: 19, sourceFamilies: 4, safe: 2, experiments: 0 }), now: "2026-07-13T09:00:00.000Z" });
  assert.equal(result.status, "partial");
  assert.equal(result.issues.includes("INSUFFICIENT_POOL"), true);
  assert.equal(result.issues.includes("MISSING_EXPERIMENT_ROLE"), true);
  assert.equal(await fs.pathExists(path.join(runDir, "packets/experiment-01.json")), false);
});

test("all required groups blocked produces failed", async () => {
  const runDir = await fs.mkdtemp(path.join(os.tmpdir(), "mesh-failed-"));
  const result = await runResearchMesh({ runDir, lane: "topics", services: fakeResearchServices({ clusters: 0, sourceFamilies: 0, requiredGroupsBlocked: true }), now: "2026-07-13T09:00:00.000Z" });
  assert.equal(result.status, "failed");
});

test("one degraded required group makes an otherwise complete run partial", async () => {
  const runDir = await fs.mkdtemp(path.join(os.tmpdir(), "mesh-degraded-"));
  const result = await runResearchMesh({ runDir, lane: "topics", services: fakeResearchServices({ clusters: 24, sourceFamilies: 4, safe: 4, experiments: 2, degradedRequiredGroup: "ru_core" }), now: "2026-07-13T09:00:00.000Z" });
  assert.equal(result.status, "partial");
  assert.equal(result.issues.includes("SOURCE_GROUP_DEGRADED"), true);
});

test("run-wide caps stop scheduling and emit RUN_LIMIT_REACHED", async () => {
  const runDir = await fs.mkdtemp(path.join(os.tmpdir(), "mesh-cap-"));
  const services = fakeResearchServices({ clusters: 80, sourceFamilies: 4, safe: 4, experiments: 2, maxItemsObserved: 301 });
  const result = await runResearchMesh({ runDir, lane: "topics", services, now: "2026-07-13T09:00:00.000Z" });
  assert.equal(result.issues.includes("RUN_LIMIT_REACHED"), true);
  assert.equal(services.counters.totalSourceItems <= 300, true);
});

test("CLI status mapping is exact", () => {
  assert.equal(exitCodeForRun("ready"), 0);
  assert.equal(exitCodeForRun("partial"), 2);
  assert.equal(exitCodeForRun("failed"), 3);
  assert.equal(exitCodeForRun("cancelled"), 130);
});
```

`tests/support/fakeResearchServices.ts` must return deterministic registered source items, health, clusters, evidence, risk, editorial output, scores, and selectors without network or OpenCode. It exposes counters for every configured cap.

Add one table-driven test case for each configured cap: items per adapter, total items, sitemap URLs, direct pages, clusters after dedupe, clusters entering verification, clusters entering OpenCode, queries per cluster, total queries, OpenCode calls, OpenCode batch size, and schema retry. Each case asserts that the observed counter never exceeds config, `RUN_LIMIT_REACHED` names the exhausted counter, and no later work is scheduled. Add a fake-clock wall-time case that aborts in-flight fetch/OpenCode work at 900 seconds and asserts the subprocess grace never exceeds five seconds.

- [ ] **Step 2: Run the orchestrator tests and verify failure**

```powershell
node --import tsx --test tests/scoutOrchestrator.test.ts
```

Expected: FAIL because the new orchestrator and fake service support do not exist.

- [ ] **Step 3: Implement phase orchestration and bounded scheduling**

`runResearchMesh` must:

1. create the run and transition to `running/discovering`;
2. execute registered adapters with max eight fetches and persist fresh health;
3. transition through extracting, normalizing, clustering, verifying, enriching, and ranking in order;
4. check the shared wall-clock signal and every counter before scheduling each item/page/cluster/query/call;
5. write source items, rejections, snapshots, clusters, evidence, candidates, packets, shortlist, JSON report, and Markdown report through `artifactStore`;
6. derive ready/partial/failed only from group health, valid pool, coverage, and role output;
7. commit the final report before terminal run state;
8. on abort, stop new scheduling immediately, permit five seconds for OpenCode termination, and commit `cancelled` only when cancellation won; wall-clock exhaustion with trustworthy candidates becomes partial plus `RUN_LIMIT_REACHED`;
9. never call episode, provider-job, render, QC, publishing, or media functions.

Use a simple semaphore class with FIFO waiters for fetch/OpenCode concurrency. Stable pre-ranking before capped stages sorts by source eligibility, freshness, heat availability, evidence-role availability, then canonical ID.

- [ ] **Step 4: Render V2 artifacts and keep legacy lanes separate**

`reports.ts` writes the approved layout. Packet filenames are role slots and are omitted when the role is missing. Markdown lists status, source group health, counts, each candidate score/rationale, missing roles, contradictions, blockers, and `No paid media started`.

Move the old `buildDraftEpisode` path out of topic scouting. `index.ts` maps `topics` and `meme_news` to `runResearchMesh`; it emits one deprecation note for `meme_news`. Preserve `cuts`/`kira` through a `runLegacyScout` compatibility function with their existing owner-approval/no-download boundaries.

- [ ] **Step 5: Add CLI and health commands**

Update scripts:

```json
{
  "scout": "tsx src/cli.ts scout",
  "scout:doctor": "tsx src/cli.ts scout-doctor",
  "scout:health": "tsx src/cli.ts scout-health"
}
```

`scout --lane topics` invokes the same orchestrator as Studio. Set `process.exitCode` to `0`, `2`, `3`, or `130` for ready/partial/failed/cancelled; unexpected config/schema/internal errors use `1`. `--run` and `--parent-run-id` are operator diagnostics only. Do not add time/schedule flags.

`scout-health --report-only` writes a schema-valid current observation report and exits `0` regardless of observed healthy/degraded/blocked; internal failure exits `1`. `--require-minimum` exits `0` healthy, `2` degraded, `3` blocked, `1` internal failure. Report checked-at, adapter/config hash, HTTP/content type where available, item count, latency, and redacted error preview.

- [ ] **Step 6: Run orchestrator, CLI help, type, and full tests**

```powershell
node --import tsx --test tests/scoutOrchestrator.test.ts
npm.cmd run scout -- --help
npm.cmd run scout:health -- --help
npm.cmd run typecheck
npm.cmd test
```

Expected: focused tests PASS; help shows no scheduler flags; full suite PASS.

- [ ] **Step 7: Commit the orchestrator**

```powershell
git add package.json package-lock.json src/cli.ts src/scout/orchestrator.ts src/scout/index.ts src/scout/reports.ts src/scout/search.ts tests/scoutOrchestrator.test.ts tests/support/fakeResearchServices.ts
git diff --cached --check
git commit -m "feat: orchestrate production topic research"
```

Expected: one scoped commit.

---

## Delivery Slice 2 — Discovery, Extraction, Clustering, And Evidence

### Task 3: Implement registered discovery adapters and source health

**Files:**
- Create: `src/scout/adapters/types.ts`
- Create: `src/scout/adapters/rss.ts`
- Create: `src/scout/adapters/searxng.ts`
- Create: `src/scout/adapters/ownerLocal.ts`
- Create: `src/scout/sourceRegistry.ts`
- Create: `src/scout/sourceHealth.ts`
- Create: `tests/fixtures/scout/rss.xml`
- Create: `tests/fixtures/scout/atom.xml`
- Create: `tests/fixtures/scout/google-trends.xml`
- Create: `tests/fixtures/scout/sitemap.xml`
- Test: `tests/scoutAdapters.test.ts`

**Interfaces:**
- Consumes: `ScoutConfig`, `SourceHealth`, `tldts.getDomain`, `fast-xml-parser.XMLParser`, and the `SafeFetch` function type declared below so adapters never call global `fetch` directly.
- Produces: `RawSourceRecord`, `AdapterResult`, `ScoutAdapter`, `parseFeedXml`, `createConfiguredAdapters`, `registrationForUrl`, `writeOnboardingRecord`, and `calculateDiscoveryGroupHealth`.

- [ ] **Step 1: Write bounded UTF-8 feed fixtures**

Create four fixtures with fixed dates and concrete URLs. `rss.xml` must contain two `<item>` records, one Cyrillic title, `link`, `guid`, `pubDate`, `description`, and a numeric engagement extension. `atom.xml` must contain two `<entry>` records with `link href`, `id`, `updated`, `summary`, and `author/name`. `google-trends.xml` must contain one trend item plus two linked news items. `sitemap.xml` must contain two concrete `<url><loc>` records and one `<lastmod>` per record. Keep each fixture under 6 KiB and do not use live URLs that are expected to remain reachable.

Use these exact concrete fixture URLs:

```xml
https://fixture.example/news/concrete-event-one
https://fixture.example/news/concrete-event-two
https://fixture.example/atom/concrete-event-three
https://fixture.example/atom/concrete-event-four
https://fixture.example/sitemap/concrete-event-five
https://fixture.example/sitemap/concrete-event-six
```

- [ ] **Step 2: Write the failing adapter and group-health tests**

Create `tests/scoutAdapters.test.ts`:

```ts
import assert from "node:assert/strict";
import test from "node:test";
import fs from "fs-extra";
import path from "node:path";
import { parseFeedXml } from "../src/scout/adapters/rss";
import { registrationForUrl } from "../src/scout/sourceRegistry";
import { calculateDiscoveryGroupHealth } from "../src/scout/sourceHealth";
import { readScoutConfig } from "../src/scout/config";
import { SourceHealthSchema } from "../src/scout/contracts";

test("RSS, Atom, Trends, and sitemap fixtures become concrete records", async () => {
  const fixtures = ["rss.xml", "atom.xml", "google-trends.xml", "sitemap.xml"];
  const counts = [];
  for (const fixture of fixtures) {
    const xml = await fs.readFile(path.resolve("tests/fixtures/scout", fixture), "utf8");
    const records = parseFeedXml(xml, { adapterId: fixture, discoveredAt: "2026-07-13T09:00:00.000Z" });
    counts.push(records.length);
    assert.equal(records.every((item) => new URL(item.url).pathname !== "/"), true);
    assert.equal(records.every((item) => Boolean(item.title && item.publishedAt)), true);
  }
  assert.deepEqual(counts, [2, 2, 1, 2]);
});

test("unknown domains are quarantined by registrable domain", async () => {
  const config = await readScoutConfig();
  const registered = registrationForUrl("https://dtf.ru/games/123-story", config);
  const unknown = registrationForUrl("https://news.example.co.uk/story", config);
  assert.equal(registered.registrationStatus, "registered");
  assert.equal(unknown.registrationStatus, "quarantined");
  assert.equal(unknown.sourceFamily, "unregistered");
  assert.equal(unknown.publisherGroupId, "quarantine:example.co.uk");
});

test("required discovery groups use fresh adapter observations", async () => {
  const config = await readScoutConfig();
  const observed = [
    health("dtf_all", "ru_core", "healthy"), health("vc_all", "ru_core", "healthy"), health("habr_current", "ru_core", "blocked"),
    health("stopgame_news", "ru_core", "healthy"), health("playground_news", "ru_core", "blocked"),
    health("bbc_ru", "broad_news", "healthy"), health("tass", "broad_news", "healthy"), health("ria", "broad_news", "blocked"),
    health("rbc", "broad_news", "healthy"), health("guardian_world", "broad_news", "blocked"), health("dw_ru", "broad_news", "blocked"),
    health("google_trends_ru", "trend_signal", "healthy"), health("steam_signals", "trend_signal", "blocked"),
  ];
  const groups = calculateDiscoveryGroupHealth(config, observed.map((entry) => SourceHealthSchema.parse(entry)));
  assert.equal(groups.ru_core.status, "healthy");
  assert.equal(groups.broad_news.status, "healthy");
  assert.equal(groups.trend_signal.status, "healthy");
});

function health(adapter_id: string, group_id: string, status: string) {
  return { schema_version: 2, adapter_id, group_id, adapter_config_hash: "a".repeat(64), checked_at: "2026-07-13T09:00:00.000Z", status, item_count: status === "healthy" ? 1 : 0, latency_ms: 1 };
}
```

- [ ] **Step 3: Run the adapter tests and verify failure**

```powershell
node --import tsx --test tests/scoutAdapters.test.ts
```

Expected: FAIL because adapter modules and fixtures are absent.

- [ ] **Step 4: Define the adapter boundary**

Create `src/scout/adapters/types.ts`:

```ts
import type { ScoutConfig } from "../configSchema";
import type { SourceHealth } from "../contracts";

export type RawSourceRecord = {
  adapterId: string;
  sourceId: string;
  url: string;
  title: string;
  publishedAt: string | null;
  discoveredAt: string;
  language: string;
  author?: string;
  snippet: string;
  rawMetrics: Record<string, string | number | boolean | null>;
  sourceRoleHint: "discovery" | "primary" | "independent" | "context";
};

export type SafeFetchResult = {
  finalUrl: string;
  status: number;
  contentType: string;
  body: Uint8Array;
  checkedAt: string;
  latencyMs: number;
};

export type SafeFetch = (url: string, options: { adapterId: string; signal: AbortSignal; allowExactLoopbackUrl?: string }) => Promise<SafeFetchResult>;
export type AdapterContext = { config: ScoutConfig; fetch: SafeFetch; signal: AbortSignal; now: string; maxItems: number };
export type AdapterResult = { items: RawSourceRecord[]; health: SourceHealth; onboarding: Array<{ domain: string; path: string }> };
export type ScoutAdapter = { id: string; groupId: string; run(context: AdapterContext): Promise<AdapterResult> };
```

- [ ] **Step 5: Implement XML parsing and configured adapters**

In `src/scout/adapters/rss.ts`, configure `XMLParser` with `ignoreAttributes: false`, `attributeNamePrefix: "@_"`, `removeNSPrefix: true`, and `parseTagValue: false`. Normalize singleton/array values through one `arrayOf` helper. Recognize these exact roots and mappings:

```ts
const mappings = {
  rss: { items: ["rss", "channel", "item"], url: ["link", "guid"], title: ["title"], date: ["pubDate", "published", "updated"], snippet: ["description", "encoded"] },
  atom: { items: ["feed", "entry"], url: ["link.@_href", "id"], title: ["title.#text", "title"], date: ["updated", "published"], snippet: ["summary.#text", "content.#text", "summary", "content"] },
  sitemap: { items: ["urlset", "url"], url: ["loc"], title: ["loc"], date: ["lastmod"], snippet: ["loc"] },
} as const;
```

`parseFeedXml(xml, context)` returns stable records sorted by `publishedAt desc`, then URL. Reject an XML item with no absolute HTTP(S) URL, no title, or an invalid date string. Google Trends uses its item title/date as the signal record and stores linked news titles/URLs in `rawMetrics` as bounded JSON strings; linked news URLs are later expanded by verification, not counted as evidence from the Trends feed itself.

`createConfiguredAdapters(config)` must instantiate enabled RSS/Atom/sitemap adapters from config. Each adapter calls the injected `SafeFetch`, caps output at `context.maxItems`, and returns a `SourceHealthSchema` record even when parsing fails. Error previews are `String(error).replace(/[\r\n]+/g, " ").slice(0, 300)`.

In `src/scout/adapters/searxng.ts`, build only ``${configuredBase}/search?q=${encodeURIComponent(query)}&format=json``; pass `adapterId: "searxng_local"` and `allowExactLoopbackUrl: configuredBase` to `SafeFetch`. Search snippets remain `sourceRoleHint: "discovery"` and never become evidence until the concrete page is safely extracted.

In `src/scout/adapters/ownerLocal.ts`, public owner URLs become discovery records; private files become only `{ local_ref_id, allowlisted_realpath_root_id, content_hash, excerpt_redacted: true }` downstream. Do not read private bytes into a prompt or report.

- [ ] **Step 6: Implement registry and health grouping**

Create `src/scout/sourceRegistry.ts` with deterministic hostname matching and no LLM classification:

```ts
import { getDomain } from "tldts";
import type { ScoutConfig } from "./configSchema";

export function registrationForUrl(rawUrl: string, config: ScoutConfig) {
  const host = new URL(rawUrl).hostname.toLowerCase().replace(/^www\./, "");
  const domain = getDomain(host) ?? host;
  const registered = Object.entries(config.adapters).find(([, adapter]) => adapter.url && (getDomain(new URL(adapter.url).hostname) ?? new URL(adapter.url).hostname) === domain);
  if (registered) {
    const [adapterId, adapter] = registered;
    return { adapterId, registrationStatus: "registered" as const, sourceFamily: adapter.source_family, publisherGroupId: adapter.publisher_group_id };
  }
  const official = Object.entries(config.official_registry).find(([, entry]) => entry.domains.some((registeredDomain) => host === registeredDomain || host.endsWith(`.${registeredDomain}`)));
  if (official) {
    const [adapterId, entry] = official;
    return { adapterId, registrationStatus: "registered" as const, sourceFamily: entry.source_family, publisherGroupId: entry.publisher_group_id };
  }
  return { adapterId: "unregistered", registrationStatus: "quarantined" as const, sourceFamily: "unregistered" as const, publisherGroupId: `quarantine:${domain}` };
}
```

`writeOnboardingRecord(runDir, url, registration)` writes ``source-onboarding/${domain}.json`` with schema version, domain, first URL, observed adapter, and required registration fields; it never promotes the domain.

Create `src/scout/sourceHealth.ts`. For every configured group, count fresh records whose adapter IDs belong to that group. Status is `healthy` when `healthyCount >= min_healthy`, `degraded` when at least one adapter is healthy but the minimum is missed, and `blocked` when zero are healthy. Optional groups use the same observation status but never independently force run failure.

- [ ] **Step 7: Run adapter, type, and full tests**

```powershell
node --import tsx --test tests/scoutAdapters.test.ts
npm.cmd run typecheck
npm.cmd test
```

Expected: PASS.

- [ ] **Step 8: Commit registered discovery**

```powershell
git add src/scout/adapters src/scout/sourceRegistry.ts src/scout/sourceHealth.ts tests/scoutAdapters.test.ts tests/fixtures/scout
git diff --cached --check
git commit -m "feat: add registered research adapters"
```

Expected: one scoped commit.

### Task 4: Enforce SSRF-safe extraction, bounded snapshots, and the content-quality gate

**Files:**
- Create: `src/scout/networkPolicy.ts`
- Modify: `src/scout/extract.ts`
- Modify: `scripts/scout_extract.py`
- Create: `src/scout/quality.ts`
- Create: `src/scout/snapshots.ts`
- Create: `tests/fixtures/scout/article.html`
- Create: `tests/fixtures/scout/antibot.html`
- Create: `tests/fixtures/scout/mojibake.html`
- Test: `tests/scoutSecurity.test.ts`
- Test: `tests/scoutQuality.test.ts`

**Interfaces:**
- Consumes: injected DNS resolver/fetcher for tests, `ipaddr.js`, config quality/security thresholds, public `RawSourceRecord` values.
- Produces: `createSafeFetch(deps): SafeFetch`, `assertPublicAddress(address): void`, `canonicalizeSourceUrl(url): string`, `evaluateSourceQuality(input): QualityDecision`, `extractPublicHtml(args): Promise<ExtractedDocument>`, `writePublicSnapshot(args)`, and `privateEvidencePointer(args)`.

- [ ] **Step 1: Write failing network-policy tests**

Create `tests/scoutSecurity.test.ts` with a fake resolver and fake fetch sequence so no test reaches the network:

```ts
import assert from "node:assert/strict";
import test from "node:test";
import { assertPublicAddress, createSafeFetch } from "../src/scout/networkPolicy";

test("blocked IPv4 and IPv6 ranges fail closed", () => {
  for (const address of ["127.0.0.1", "10.0.0.1", "172.16.0.1", "192.168.1.1", "169.254.169.254", "100.64.0.1", "0.0.0.0", "224.0.0.1", "::1", "fe80::1", "fc00::1", "ff02::1", "::ffff:127.0.0.1"]) {
    assert.throws(() => assertPublicAddress(address), /blocked address/i);
  }
  assert.doesNotThrow(() => assertPublicAddress("93.184.216.34"));
  assert.doesNotThrow(() => assertPublicAddress("2606:2800:220:1:248:1893:25c8:1946"));
});

test("URL credentials and redirect-to-private are rejected", async () => {
  const calls: string[] = [];
  const safeFetch = createSafeFetch({
    resolve: async (host) => [{ address: host === "public.example" ? "93.184.216.34" : "127.0.0.1", family: host === "public.example" ? 4 : 4 }],
    fetchImpl: async (url) => {
      calls.push(String(url));
      return new Response(null, { status: 302, headers: { location: "http://private.example/secret" } });
    },
    now: () => "2026-07-13T09:00:00.000Z",
    limits: { timeoutMs: 30000, maxRedirects: 5, maxBytes: 1500000 },
  });
  await assert.rejects(() => safeFetch("https://user:pass@public.example/story", { adapterId: "rss", signal: new AbortController().signal }), /credentials/i);
  await assert.rejects(() => safeFetch("https://public.example/story", { adapterId: "rss", signal: new AbortController().signal }), /blocked address/i);
  assert.deepEqual(calls, ["https://public.example/story"]);
});

test("only exact SearXNG adapter and base get the loopback exception", async () => {
  const safeFetch = createSafeFetch({
    resolve: async () => [{ address: "127.0.0.1", family: 4 }],
    fetchImpl: async () => new Response("{\"results\":[]}", { status: 200, headers: { "content-type": "application/json" } }),
    now: () => "2026-07-13T09:00:00.000Z",
    limits: { timeoutMs: 30000, maxRedirects: 5, maxBytes: 1500000 },
  });
  const signal = new AbortController().signal;
  await safeFetch("http://127.0.0.1:8080/search?q=x&format=json", { adapterId: "searxng_local", signal, allowExactLoopbackUrl: "http://127.0.0.1:8080" });
  await assert.rejects(() => safeFetch("http://127.0.0.1:8080/admin", { adapterId: "rss", signal, allowExactLoopbackUrl: "http://127.0.0.1:8080" }), /blocked address/i);
});
```

- [ ] **Step 2: Write failing quality and snapshot tests**

Create `tests/scoutQuality.test.ts`:

```ts
import assert from "node:assert/strict";
import test from "node:test";
import fs from "fs-extra";
import os from "node:os";
import path from "node:path";
import { canonicalizeSourceUrl, evaluateSourceQuality } from "../src/scout/quality";
import { privateEvidencePointer, writePublicSnapshot } from "../src/scout/snapshots";

test("quality gate rejects landing, anti-bot, short, missing-date, and mojibake content", () => {
  const good = input();
  assert.equal(evaluateSourceQuality(good).accepted, true);
  assert.equal(evaluateSourceQuality({ ...good, canonicalUrl: "https://example.com/" }).accepted, false);
  assert.equal(evaluateSourceQuality({ ...good, text: "Вы, случайно, не робот?".repeat(30) }).reason, "anti_bot");
  assert.equal(evaluateSourceQuality({ ...good, text: "short" }).reason, "body_too_short");
  assert.equal(evaluateSourceQuality({ ...good, publishedAt: null }).reason, "missing_current_date");
  assert.equal(evaluateSourceQuality({ ...good, text: `${"а".repeat(399)}���` }).reason, "mojibake");
});

test("canonical URL removes trackers but preserves story identity", () => {
  assert.equal(canonicalizeSourceUrl("HTTPS://Example.COM/story/?utm_source=x&b=2&a=1#fragment"), "https://example.com/story?a=1&b=2");
});

test("public snapshots are bounded and private pointers contain no bytes", async () => {
  const runDir = await fs.mkdtemp(path.join(os.tmpdir(), "mesh-snapshot-"));
  const publicPath = await writePublicSnapshot({ runDir, sourceId: "s1", title: "Title", url: "https://example.com/story", publishedAt: "2026-07-13T08:00:00.000Z", excerpt: "x".repeat(5000), checkedAt: "2026-07-13T09:00:00.000Z" });
  const saved = await fs.readJson(publicPath);
  assert.equal(saved.excerpt.length <= 700, true);
  const pointer = privateEvidencePointer({ localRefId: "dance-01", rootId: "dance_refs", contentHash: "a".repeat(64) });
  assert.deepEqual(Object.keys(pointer).sort(), ["allowlisted_realpath_root_id", "content_hash", "excerpt_redacted", "local_ref_id", "source_visibility"]);
});

function input() {
  return { canonicalUrl: "https://example.com/story", configuredLandingUrls: ["https://example.com/"], title: "Concrete title", text: "Нормальный текст статьи ".repeat(40), publishedAt: "2026-07-13T08:00:00.000Z", classification: "current" as const, minBodyChars: 400, maxReplacementRatio: 0.002, now: "2026-07-13T09:00:00.000Z" };
}
```

- [ ] **Step 3: Run both focused tests and verify failure**

```powershell
node --import tsx --test tests/scoutSecurity.test.ts tests/scoutQuality.test.ts
```

Expected: FAIL because network, quality, and snapshot modules do not exist.

- [ ] **Step 4: Implement the network boundary**

Create `src/scout/networkPolicy.ts`. Parse every resolved address with `ipaddr.parse`; convert IPv4-mapped IPv6 through `toIPv4Address`; accept only `range() === "unicast"`. Parse URLs with `new URL`, require `http:` or `https:`, reject username/password, lowercase the hostname, and resolve with `{ all: true, verbatim: true }`. A loopback request is allowed only when all of these are true: `adapterId === "searxng_local"`, `allowExactLoopbackUrl` parses successfully, scheme/hostname/port exactly match, and requested pathname is `/search`.

Use this exact fetch loop:

```ts
for (let redirect = 0; redirect <= limits.maxRedirects; redirect += 1) {
  await assertUrlAllowed(current, options);
  const response = await fetchImpl(current, { redirect: "manual", signal: combinedSignal, headers: { "User-Agent": "POKROV-Scout/2.0 (+read-only)", Accept: "application/rss+xml, application/atom+xml, application/xml, text/xml, application/json, text/html;q=0.9" } });
  if ([301, 302, 303, 307, 308].includes(response.status)) {
    const location = response.headers.get("location");
    if (!location) throw new Error("redirect without location");
    if (redirect === limits.maxRedirects) throw new Error("redirect limit exceeded");
    current = new URL(location, current).toString();
    continue;
  }
  const chunks: Uint8Array[] = [];
  let size = 0;
  if (response.body) for await (const chunk of response.body as unknown as AsyncIterable<Uint8Array>) {
    const bytes = chunk instanceof Uint8Array ? chunk : new Uint8Array(chunk);
    size += bytes.byteLength;
    if (size > limits.maxBytes) throw new Error("response size limit exceeded");
    chunks.push(bytes);
  }
  return { finalUrl: current, status: response.status, contentType: response.headers.get("content-type") ?? "", body: Buffer.concat(chunks), checkedAt: now(), latencyMs: Date.now() - started };
}
throw new Error("unreachable redirect state");
```

Build one timeout `AbortController`, relay the caller signal, clear the timer in `finally`, and never retry a policy rejection.

- [ ] **Step 5: Route HTML extraction through safe bytes only**

Change `extractScoutSource` to `extractPublicHtml({ config, url, adapterId, safeFetch, signal, outPath })`. The TypeScript layer fetches bounded bytes first, writes a temporary UTF-8 HTML file under the run’s `.tmp/` directory, invokes `execa("python", ["scripts/scout_extract.py", "extract", "--html-file", tempPath, "--url", fetched.finalUrl, "--out", outPath, "--adapter", "basic"])`, then removes only that verified run-local temp file in `finally`.

Modify `scripts/scout_extract.py` so runtime extraction requires `--html-file`; remove `urllib.request`, direct Crawl4AI URL fetch, direct Scrapling URL fetch, `--stealth`, `--proxy`, and `--account-profile` paths. `doctor` may still report library availability, but runtime network ownership stays in TypeScript. The helper returns parsed title/markdown only and cannot make network requests.

- [ ] **Step 6: Implement quality decisions and snapshots**

`canonicalizeSourceUrl` lowercases scheme/host, removes default ports/fragments, removes `utm_*`, `fbclid`, `gclid`, and `yclid`, sorts remaining query entries, collapses duplicate slashes, and removes a trailing slash except at root.

`evaluateSourceQuality` returns exactly:

```ts
export type QualityDecision = { accepted: true; reason: "accepted" } | { accepted: false; reason: "landing_page" | "anti_bot" | "access_denied" | "empty" | "body_too_short" | "missing_title" | "missing_current_date" | "stale" | "mojibake" | "duplicate_url" | "duplicate_content" | "fetch_error" | "search_snippet_only" };
```

Check rejection in this order: fetch error, canonical/title, configured landing URL or root path, anti-bot/access phrases, empty/length, current date/freshness, replacement-character ratio, duplicate canonical URL, duplicate SHA-256 normalized-content hash, raw search snippet. Normalize Unicode to NFC and whitespace before hashing. Retain every rejected record under ``rejections/${sourceId}.json`` with the reason and source-health reference.

`writePublicSnapshot` persists only schema version, source ID, title, URL, published/checked dates, an excerpt capped at 700 characters, and SHA-256 of that canonical payload. `privateEvidencePointer` returns only the five keys asserted by the test; no local path or bytes are included.

- [ ] **Step 7: Run security, quality, doctor, and regression checks**

```powershell
node --import tsx --test tests/scoutSecurity.test.ts tests/scoutQuality.test.ts
npm.cmd run scout:doctor
npm.cmd run typecheck
npm.cmd test
```

Expected: focused tests PASS; doctor reports dependency availability without fetching; full suite PASS.

- [ ] **Step 8: Commit the extraction boundary**

```powershell
git add src/scout/networkPolicy.ts src/scout/extract.ts src/scout/quality.ts src/scout/snapshots.ts scripts/scout_extract.py tests/scoutSecurity.test.ts tests/scoutQuality.test.ts tests/fixtures/scout/article.html tests/fixtures/scout/antibot.html tests/fixtures/scout/mojibake.html
git diff --cached --check
git commit -m "feat: secure scout extraction and quality gates"
```

Expected: one scoped commit; no raw fetched page or private local source is staged.

### Task 5: Cluster events and close evidence gaps with a bounded verification loop

**Files:**
- Create: `src/scout/clustering.ts`
- Create: `src/scout/evidence.ts`
- Create: `src/scout/verification.ts`
- Create: `tests/fixtures/scout/evidence-normal.json`
- Create: `tests/fixtures/scout/evidence-enhanced.json`
- Create: `tests/fixtures/scout/evidence-contradiction.json`
- Test: `tests/scoutEvidence.test.ts`

**Interfaces:**
- Consumes: accepted public `SourceItem[]`, registered publisher groups, an optional `comparePairs(pairs, signal)` callback, and a `discoverVerification(query, requiredRole, signal)` callback.
- Produces: `clusterSourceItems(items, comparePairs?): Promise<EventCluster[]>`, `resolveProvenance(items): ProvenanceRecord[]`, `buildClaimGraph(cluster, items, proposedClaims): ClaimEvidence[]`, `evaluateEvidenceGate(args): EvidenceGateResult`, and `runVerificationLoop(args): Promise<VerificationResult>`.

- [ ] **Step 1: Write failing clustering and evidence tests**

Create `tests/scoutEvidence.test.ts`:

```ts
import assert from "node:assert/strict";
import test from "node:test";
import { clusterSourceItems } from "../src/scout/clustering";
import { evaluateEvidenceGate } from "../src/scout/evidence";
import { runVerificationLoop } from "../src/scout/verification";
import { SourceItemSchema } from "../src/scout/contracts";

test("coverage of one event forms one candidate boundary", async () => {
  const clusters = await clusterSourceItems([
    item("a", "https://a.example/story", "Компания выпустила устройство X", "publisher-a", "2026-07-13T08:00:00.000Z"),
    item("b", "https://b.example/report", "Устройство X официально выпущено компанией", "publisher-b", "2026-07-13T08:30:00.000Z"),
    item("c", "https://c.example/other", "Совсем другое игровое событие", "publisher-c", "2026-07-13T08:40:00.000Z"),
  ].map((entry) => SourceItemSchema.parse(entry)));
  assert.equal(clusters.length, 2);
  assert.equal(clusters[0].source_item_ids.length, 2);
});

test("normal evidence accepts primary or two independent sources", () => {
  assert.equal(evaluateEvidenceGate({ enhancedRisk: false, sources: [provenance("primary", "p1")], claims: [], materialContradiction: false }).eligible, true);
  assert.equal(evaluateEvidenceGate({ enhancedRisk: false, sources: [provenance("independent", "p1"), provenance("independent", "p2")], claims: [], materialContradiction: false }).eligible, true);
  assert.equal(evaluateEvidenceGate({ enhancedRisk: false, sources: [provenance("independent", "p1"), provenance("independent", "p1")], claims: [], materialContradiction: false }).eligible, false);
});

test("enhanced evidence needs primary plus two independent publisher groups and no material conflict", () => {
  const sources = [provenance("primary", "official"), provenance("independent", "p1"), provenance("independent", "p2")];
  assert.equal(evaluateEvidenceGate({ enhancedRisk: true, sources, claims: [], materialContradiction: false }).evidenceConfidence, 1);
  assert.equal(evaluateEvidenceGate({ enhancedRisk: true, sources, claims: [], materialContradiction: true }).eligible, false);
});

test("verification stops after two rounds and twelve queries per cluster", async () => {
  let calls = 0;
  const result = await runVerificationLoop({
    clusterId: "cluster-1", initialSources: [], requiredRoles: ["primary", "independent", "independent"],
    maxRounds: 2, maxQueries: 12, signal: new AbortController().signal,
    buildQueries: ({ round }) => Array.from({ length: 10 }, (_, index) => ({ query: `round-${round}-query-${index}`, requiredRole: "independent" as const })),
    discover: async () => { calls += 1; return []; },
    recompute: (sources) => ({ eligible: false, sources, blockers: ["missing evidence"] }),
  });
  assert.equal(calls, 12);
  assert.equal(result.rounds, 2);
  assert.deepEqual(result.blockers, ["missing evidence"]);
});

function item(id: string, canonical_url: string, title: string, publisher_group_id: string, published_at: string) {
  return { schema_version: 2, id, source_id: id, source_family: "tech_press_ru", publisher_group_id, source_role_hint: "independent", canonical_url, title, published_at, discovered_at: published_at, language: "ru", raw_metrics: {}, text_excerpt: title.repeat(30), content_hash: id.padEnd(64, "a"), snapshot_path: `snapshots/${id}.json`, fetch_method: "fixture", adapter_id: id, adapter_config_hash: "b".repeat(64), checked_at: published_at, http_status: 200, content_type: "text/html", health_status: "healthy", risk_profile: "green", registration_status: "registered", source_visibility: "public" };
}
function provenance(role: string, publisherGroupId: string) { return { sourceItemId: `${role}-${publisherGroupId}`, role, publisherGroupId, syndicated: false, contentSimilarity: 0.2 }; }
```

- [ ] **Step 2: Run the evidence tests and verify failure**

```powershell
node --import tsx --test tests/scoutEvidence.test.ts
```

Expected: FAIL because clustering/evidence/verification modules are absent.

- [ ] **Step 3: Implement deterministic event clustering**

Normalize titles to lowercase NFC tokens, remove punctuation and a versioned Russian/English stopword set, derive entity keys from capitalized multi-character tokens and numbers, and calculate:

```text
similarity = title_jaccard*0.50 + entity_jaccard*0.25 + time_proximity*0.15 + content_prefix_similarity*0.10
```

Join records deterministically when canonical URL/content hash matches or similarity is at least `0.78`. Mark pairs from `0.62` through `0.779999` as uncertain; pass only those pairs to `comparePairs`, and join only when the schema-valid comparison says `same_event=true` with confidence at least `0.8`. Sort items by canonical URL before union-find, derive cluster ID as the first 24 hex characters of SHA-256 over sorted source item IDs, and cap after clustering using stable pre-ranking.

- [ ] **Step 4: Implement provenance and evidence gates**

`resolveProvenance` assigns roles from registered source metadata, direct-record patterns, byline, publisher group, content similarity, and syndication markers. Multiple domains with the same `publisher_group_id`, content similarity at least `0.9`, or the same press-release fingerprint count once.

`evaluateEvidenceGate` returns:

```ts
type EvidenceGateResult = {
  eligible: boolean;
  evidenceConfidence: 0 | 0.65 | 0.8 | 0.9 | 1;
  qualifiedSourceCount: number;
  blockers: Array<"missing_primary" | "missing_independent" | "shared_ownership" | "syndicated_only" | "material_contradiction" | "missing_current_status">;
};
```

Normal confidence is `1` for primary+2 independent, `0.9` for primary+1 independent, `0.8` for two independent, `0.65` for one primary, and `0` below minimum or with a material contradiction. Enhanced risk is eligible only at `1` and with current-status timestamp. A first-party statement proves that the statement exists; contested assertions inside it still need independent support.

Build claim records only from retained excerpts/snapshot hashes. Classify a contradiction as material when actor, action, date, magnitude, outcome, legal status, or hook truth changes. A dispute-format packet may preserve both sides as separate claims; otherwise material conflict emits `BLOCKED_CONFLICT`.

- [ ] **Step 5: Implement the bounded feedback loop**

For each cluster, `runVerificationLoop` performs at most two rounds. `VerificationQueryBuilder` deterministically combines retained entity keys, ISO date, normalized claim terms, and required role labels. It invokes only configured SearXNG/feed/official lookup/direct extraction callbacks, deduplicates by canonical URL/content hash, stops immediately when the evidence gate passes, and never exceeds 12 cluster queries or the run-wide counter supplied by the orchestrator. Remaining gaps become `BLOCKED_EVIDENCE`; the function does not downgrade requirements.

- [ ] **Step 6: Run evidence, type, and full tests**

```powershell
node --import tsx --test tests/scoutEvidence.test.ts
npm.cmd run typecheck
npm.cmd test
```

Expected: PASS.

- [ ] **Step 7: Commit clustering and evidence**

```powershell
git add src/scout/clustering.ts src/scout/evidence.ts src/scout/verification.ts tests/scoutEvidence.test.ts tests/fixtures/scout/evidence-normal.json tests/fixtures/scout/evidence-enhanced.json tests/fixtures/scout/evidence-contradiction.json
git diff --cached --check
git commit -m "feat: cluster events and verify evidence"
```

Expected: one scoped commit.
