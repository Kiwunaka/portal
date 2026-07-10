# POKROV App Agent Context And Docs Renewal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give `POKROV-app` its own thin Codex contract and reconcile current client docs/config seeds without touching retained release artifacts or overwriting dirty historical work.

**Architecture:** Commit the non-overlapping root contract, client registry/router, and PowerShell guard first. Snapshot and classify the old dirty release-hardening worktree before updating overlapping canon/config/release docs. Keep each correction group independently revertible.

**Tech Stack:** Markdown, PowerShell Core, existing seed validator, Flutter/Dart tests already in the repo, Git worktrees.

## Global Constraints

- Work only in a dedicated client worktree on `codex/agent-context-refactor-client`.
- Client root `AGENTS.md`: at most 8,192 UTF-8 bytes and 120 physical lines.
- Client `docs/README.md`: at most 12,288 UTF-8 bytes and 240 physical lines.
- Android and Windows are current outside-store beta surfaces; iOS/macOS remain readiness tracks.
- Do not put a release-version snapshot in client `AGENTS.md`.
- Current beta line is `1.0.0-beta`; stable `1.0.0` is not proven.
- Platform shared facts and contracts remain cross-repo owners where the client consumes them.
- Never modify `artifacts/releases/**` in this plan.
- Never run Android/Windows release builds merely to validate docs.
- Signing, store, device, real-user, WARP, and origin gates remain manual/current-evidence requirements.
- No new dependency, service, MCP server, vector store, model catalog, or generator.
- Historical/evidence docs are classified centrally and not rewritten.

---

## Collision Gate And Worktree

Current audited state:

- client `main` clean at `4722cd8`, 20 commits ahead of `origin/main`;
- clean `codex/market-ready-cis-client-integration` at the same commit;
- dirty `codex/release-hardening-client`, 91 commits behind, overlaps product,
  architecture, operations, config, and release files.

Before creating the worktree:

```powershell
git status --short --branch
git worktree list --porcelain
git -C .worktrees/market-ready-cis-client-integration status --short
git -C C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\release-hardening-client status --short
```

Create:

```powershell
git worktree add C:\Users\kiwun\Documents\ai\POKROV-app\.worktrees\agent-context-refactor-client -b codex/agent-context-refactor-client codex/market-ready-cis-client-integration
```

Commit 1 may proceed on its strict write set. Commits 2–4 wait until the cleanup
plan's Stage A snapshots and classifies `release-hardening-client`.

---

### Task 1: Add Thin Client Contract, Router, And Guard

**Files:**
- Create: `AGENTS.md`
- Create: `test/docs-contract.ps1`
- Modify: `docs/README.md`
- Modify: `scripts/validate-seed.ps1`
- Modify: `test/README.md`

**Interfaces:**
- Consumes: platform/client authority boundary from the approved spec
- Produces: `test/docs-contract.ps1` and a client task router/registry

- [ ] **Step 1: Create the failing PowerShell contract test**

Use:

```powershell
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$errors = [System.Collections.Generic.List[string]]::new()

function Require-True {
  param([bool]$Condition, [string]$Message)
  if (-not $Condition) { $errors.Add($Message) }
}

$agentsPath = Join-Path $root "AGENTS.md"
Require-True (Test-Path -LiteralPath $agentsPath -PathType Leaf) "AGENTS.md is required"

if (Test-Path -LiteralPath $agentsPath) {
  $agents = [IO.File]::ReadAllText($agentsPath)
  $bytes = [Text.Encoding]::UTF8.GetByteCount($agents)
  $lines = ($agents -split "\r?\n").Count
  Require-True ($bytes -le 8192) "AGENTS.md exceeds 8192 UTF-8 bytes"
  Require-True ($lines -le 120) "AGENTS.md exceeds 120 physical lines"

  foreach ($required in @(
    "POKROV-app/main",
    "docs/README.md",
    "Android",
    "Windows",
    "iOS",
    "macOS",
    "MANUAL_OWNER_TEST",
    "artifacts/releases",
    "git diff --check"
  )) {
    Require-True ($agents.Contains($required)) "AGENTS.md is missing semantic guard: $required"
  }

  foreach ($forbidden in @(
    "OpenCode",
    "Fireworks",
    "CODY",
    "Last updated:",
    "model catalog",
    "active plans"
  )) {
    Require-True (-not $agents.Contains($forbidden)) "AGENTS.md contains volatile content: $forbidden"
  }

  Require-True ($agents -notmatch '\b\d+\.\d+\.\d+(?:-[A-Za-z0-9.]+)?\b') "AGENTS.md must not contain a release-version snapshot"
}

$registry = [IO.File]::ReadAllText((Join-Path $root "docs\README.md"))
$registryBytes = [Text.Encoding]::UTF8.GetByteCount($registry)
$registryLines = ($registry -split "\r?\n").Count
Require-True ($registryBytes -le 12288) "docs/README.md exceeds 12288 UTF-8 bytes"
Require-True ($registryLines -le 240) "docs/README.md exceeds 240 physical lines"
foreach ($class in @(
  "CANONICAL",
  "ACTIVE_EXECUTION",
  "EVIDENCE",
  "HISTORICAL_REFERENCE",
  "OPERATOR_PLAYBOOK",
  "EXPERIMENTAL"
)) {
  Require-True ($registry.Contains($class)) "docs/README.md is missing class $class"
}
Require-True ($registry.Contains("| Task | Read first | Inspect | Verify | Docs impact |")) "docs/README.md lacks task routes"
Require-True ($registry.Contains("| Class | Review | Owner | Path |")) "docs/README.md lacks document registry"

if ($errors.Count -gt 0) {
  $errors | ForEach-Object { Write-Error $_ }
  exit 1
}

Write-Host "Client docs contract OK." -ForegroundColor Green
```

- [ ] **Step 2: Run RED**

```powershell
powershell -ExecutionPolicy Bypass -File .\test\docs-contract.ps1
```

Expected: failure because `AGENTS.md` and the renewed tables do not exist.

- [ ] **Step 3: Create the thin client root**

Use only:

1. `POKROV-app/main` and separate platform-repo boundary;
2. authority ladder and `docs/README.md` router;
3. Android/Windows public scope and Apple readiness-only boundary;
4. platform shared-fact dependency;
5. runtime/core/secure-storage/secret guards;
6. destructive-operation and evidence-retention guards;
7. release honesty and manual labels;
8. focused Flutter/host/docs verification and handoff.

Explicitly forbid changes under `artifacts/releases/**` unless the task itself
is an approved release-artifact task. Do not include versions, dates, models,
active plans, or a global must-read list.

- [ ] **Step 4: Replace the client index with routes and registry**

Use:

```markdown
| Task | Read first | Inspect | Verify | Docs impact |
```

Routes:

- shell/UI/copy;
- app-first/account/API;
- runtime/core/WARP;
- Android;
- Windows;
- Apple readiness;
- release metadata;
- design;
- docs/history.

Use:

```markdown
| Class | Review | Owner | Path |
```

Review values:
`RECONCILED | REVIEWED_NO_CHANGE | PENDING_COLLISION_REVIEW |
UNRESOLVED_OWNER_DECISION`.

If the client has no local operator playbook or experimental helper, include
one explicit `REVIEWED_NO_CHANGE` registry row for each class stating
`no client-local owner; platform tools do not enter the client default route`.

Initial ownership:

- `CANONICAL`: root `README.md`, root `DESIGN.md`, client product contract,
  app-first onboarding, folder/package/bootstrap architecture, in-app assistant
  contract, 2026-06-13 product/UI direction, and the five machine-readable
  config owners;
- `ACTIVE_EXECUTION`: client release backlog, cutover readiness, Android and
  Windows readiness, WARP proof, responsive captures, motion/performance, and
  Apple readiness;
- `EVIDENCE`: public-beta PRD, dated June handoffs/closure audits,
  client-UI/API additions, retained beta WO, and completed implementation maps;
- `HISTORICAL_REFERENCE`: older decisions, pre-2026-06-13 design/consilium
  briefs, specs, generated design references, archive, Karing, and clean-room
  inputs.

- [ ] **Step 5: Integrate the guard into seed validation**

Add these required files to `scripts/validate-seed.ps1`:

```powershell
"AGENTS.md",
"test\docs-contract.ps1",
"config\cutover-readiness.seed.json",
"config\release-handoff.seed.json"
```

Add both JSON seeds to the existing `$jsonFiles` collection. Before successful
exit, call:

```powershell
& (Join-Path $root "test\docs-contract.ps1")
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}
```

Document the new guard in `test/README.md`.

- [ ] **Step 6: Run GREEN and commit**

```powershell
powershell -ExecutionPolicy Bypass -File .\test\docs-contract.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\validate-seed.ps1
git diff --check
git diff --name-only -- artifacts/releases
git add AGENTS.md docs/README.md test/docs-contract.ps1 test/README.md scripts/validate-seed.ps1
git commit -m "docs: add thin client agent contract"
```

Expected: tests pass and artifact diff is empty.

### Task 2: Reconcile Current Client Canon

**Files:**
- Modify: `README.md`
- Modify: `docs/product/client-product-contract.md`
- Modify: `docs/architecture/app-first-onboarding-flow.md`
- Modify: `docs/architecture/bootstrap-workflow.md`
- Modify: `docs/architecture/in-app-ai-assistant-contract.md`
- Modify: `test/docs-contract.ps1`

**Interfaces:**
- Consumes: snapshotted/classified `release-hardening-client` overlap
- Produces: current client product/onboarding/runtime/assistant contracts

- [ ] **Step 1: Stop unless dirty historical overlap is preserved**

Run the cleanup plan's Stage A first. Review the saved diff for every file in
this task. If it contains current work that should be replayed, apply it to the
new client worktree before continuing.

- [ ] **Step 2: Add stale-text assertions**

Add before the final `if ($errors.Count -gt 0)` block:

```powershell
$forbiddenByFile = @{
  "README.md" = @(
    "no release wiring",
    "Selected-apps parity is still outside this cycle"
  )
  "docs\architecture\app-first-onboarding-flow.md" = @("0.x.x-beta")
  "docs\architecture\bootstrap-workflow.md" = @(
    "per-app Android parity remains deferred"
  )
  "docs\architecture\in-app-ai-assistant-contract.md" = @(
    "If ticket APIs are not enough for live AI help"
  )
}

foreach ($relativePath in $forbiddenByFile.Keys) {
  $text = [IO.File]::ReadAllText((Join-Path $root $relativePath))
  foreach ($forbidden in $forbiddenByFile[$relativePath]) {
    Require-True (-not $text.Contains($forbidden)) "$relativePath contains stale text: $forbidden"
  }
}
```

Run and expect RED.

- [ ] **Step 3: Apply the current contracts**

Required corrections:

- recognize the public beta handoff while keeping generated `build/**`
  non-authoritative;
- replace `0.x.x-beta` with current `1.0.0-beta` beta truth;
- replace Atlas-driven language with current `pokrov-clear`/2026-06-13
  direction;
- mark selected-app picker/policy beta-active and production-proof-gated;
- document implemented `POST /api/client/support/assistant`;
- link exact platform product, app-first, download, and publishing owners;
- keep stable/store/signing/device/WARP claims blocked by current evidence.

- [ ] **Step 4: Run focused behavior checks**

```powershell
Push-Location .\packages\app_shell
flutter test test/app_first_runtime_bootstrap_test.dart --plain-name "client support assistant uses app-session auth"
flutter test test/pokrov_seed_app_test.dart --plain-name "rules app picker can use native Android catalog"
flutter test test/ui_copy_contract_test.dart
flutter test test/assistant_contract_test.dart
Pop-Location
powershell -ExecutionPolicy Bypass -File .\test\docs-contract.ps1
git diff --check
```

Expected: all focused tests pass.

- [ ] **Step 5: Commit**

```powershell
git add README.md docs/product/client-product-contract.md docs/architecture/app-first-onboarding-flow.md docs/architecture/bootstrap-workflow.md docs/architecture/in-app-ai-assistant-contract.md test/docs-contract.ps1
git commit -m "docs: reconcile current client contracts"
```

### Task 3: Align Client Config Seeds

**Files:**
- Modify: `config/product-contract.seed.json`
- Modify: `config/platform-matrix.seed.json`
- Modify: `config/cutover-readiness.seed.json`
- Modify: `test/docs-contract.ps1`
- Do not modify: `config/release-handoff.seed.json`
- Do not modify: `artifacts/releases/**`

**Interfaces:**
- Consumes: current release-handoff seed as machine-readable release owner
- Produces: product/platform/cutover seeds aligned with current beta truth

- [ ] **Step 1: Add cross-seed assertions**

Add before the final `if ($errors.Count -gt 0)` block:

```powershell
$product = Get-Content -Raw config/product-contract.seed.json | ConvertFrom-Json
$platform = Get-Content -Raw config/platform-matrix.seed.json | ConvertFrom-Json
$release = Get-Content -Raw config/release-handoff.seed.json | ConvertFrom-Json
$cutover = Get-Content -Raw config/cutover-readiness.seed.json | ConvertFrom-Json
$runtime = Get-Content -Raw config/runtime-profile.seed.json | ConvertFrom-Json

Require-True ($product.client_version_line -eq $release.latest_repo_backed_release.version) "Product and release version lines disagree"
Require-True ($cutover.latest_repo_backed_release.github_release -eq $release.latest_repo_backed_release.github_release) "Cutover and release-handoff URLs disagree"
Require-True ($cutover.latest_repo_backed_release.github_repo_visibility -eq "public") "Cutover seed still describes the release repo as private"
Require-True ($cutover.latest_repo_backed_release.anonymous_download_smoke -match "^PASS_") "Cutover seed lacks public anonymous-download proof"
Require-True ($product.trial_days -eq $runtime.trial_days -and $product.telegram_bonus_days -eq $runtime.telegram_bonus_days) "Product and runtime trial/reward facts disagree"
```

Run `test/docs-contract.ps1` and expect RED on current drift.

- [ ] **Step 2: Update selected-app status exactly**

```json
"selected_apps_status": {
  "android": "beta_picker_and_policy_active",
  "windows": "beta_picker_and_policy_active",
  "public_claim": "picker_and_policy_active_production_proof_gated"
}
```

- [ ] **Step 3: Update platform readiness exactly**

```json
"release_readiness": {
  "android": "outside_store_beta_public_manual_live_smoke_pending",
  "ios": "readiness_only_store_blocked",
  "macos": "readiness_only_notarization_blocked",
  "windows": "outside_store_unsigned_beta_public_manual_live_smoke_pending"
}
```

Align `cutover-readiness.seed.json` URL/visibility/download proof to the
unchanged current `release-handoff.seed.json`.

- [ ] **Step 4: Verify and commit**

```powershell
powershell -ExecutionPolicy Bypass -File .\test\docs-contract.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\validate-seed.ps1
git diff --check
git diff --name-only -- artifacts/releases
git add config/product-contract.seed.json config/platform-matrix.seed.json config/cutover-readiness.seed.json test/docs-contract.ps1
git commit -m "config: align client seeds with current beta truth"
```

Expected: seed checks pass and no release artifact changes.

### Task 4: Clarify Client Release And Design Boundaries

**Files:**
- Modify: `docs/operations/warp-runtime-proof-checklist.md`
- Modify: `docs/operations/windows-release-readiness.md`
- Modify: `docs/implementation/client-release-backlog.md`
- Modify: `docs/design/DESIGN.md`
- Modify: `docs/README.md`
- Modify: `test/docs-contract.ps1`

**Interfaces:**
- Consumes: current client registry and aligned config seeds
- Produces: final current/execution/evidence/history boundary

- [ ] **Step 1: Update boundary statements**

Apply:

- current UI may say `WARP`, while raw WireGuard material, keys, and topology
  remain forbidden;
- remove the contradiction between current outside-store beta truth and “not
  release truth” in Windows readiness;
- replace backlog `0.x.x-beta` references with `1.0.0-beta` or explicit
  beta-patch labels;
- turn `docs/design/DESIGN.md` into a short superseded pointer to the root
  `DESIGN.md` and 2026-06-13 direction, without rewriting old design history;
- mark unchanged current docs `REVIEWED_NO_CHANGE` in the registry;
- leave dated June handoffs and release artifacts untouched.

- [ ] **Step 2: Add release/history guard assertions**

Add these checks before the final `if ($errors.Count -gt 0)` block:

```powershell
$legacyDesign = [IO.File]::ReadAllText((Join-Path $root "docs\design\DESIGN.md"))
$backlog = [IO.File]::ReadAllText((Join-Path $root "docs\implementation\client-release-backlog.md"))
$windows = [IO.File]::ReadAllText((Join-Path $root "docs\operations\windows-release-readiness.md"))
$warp = [IO.File]::ReadAllText((Join-Path $root "docs\operations\warp-runtime-proof-checklist.md"))
$registry = [IO.File]::ReadAllText((Join-Path $root "docs\README.md"))
Require-True ($legacyDesign.Contains("HISTORICAL_REFERENCE") -and $legacyDesign.Contains("../../DESIGN.md")) "Legacy client design doc lacks superseded pointer"
Require-True (-not $backlog.Contains("0.x.x-beta")) "Client backlog contains stale beta version line"
Require-True (($windows + $warp).Contains("MANUAL_OWNER_TEST")) "Windows/WARP docs lack manual proof boundary"
Require-True ($registry.Contains("EVIDENCE")) "Client registry lacks evidence classification"
```

- [ ] **Step 3: Run focused checks**

```powershell
Push-Location .\packages\app_shell
flutter test test/design_system_contract_test.dart
flutter test test/ui_copy_contract_test.dart
flutter test test/warp_lifecycle_contract_test.dart
Pop-Location
powershell -ExecutionPolicy Bypass -File .\test\docs-contract.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\validate-seed.ps1
git diff --check
git diff --name-only -- artifacts/releases
```

Expected: all checks pass and artifact diff remains empty.

- [ ] **Step 4: Commit**

```powershell
git add docs/README.md docs/design/DESIGN.md docs/operations/warp-runtime-proof-checklist.md docs/operations/windows-release-readiness.md docs/implementation/client-release-backlog.md test/docs-contract.ps1
git commit -m "docs: clarify client release and design boundaries"
```

### Task 5: Run The Client Validation Epoch

**Files:**
- Verify only

- [ ] **Step 1: Run current non-release validation**

```powershell
powershell -ExecutionPolicy Bypass -File .\test\docs-contract.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\validate-seed.ps1
powershell -ExecutionPolicy Bypass -File .\test\seed-layout.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1
git diff --check
git status --short
git diff --name-only -- artifacts/releases
```

Expected:

- all commands exit 0;
- no release artifact diff;
- no new dependency/service;
- four commits are independently revertible;
- dirty neighboring work remains recoverable.

## Manual And Release Gates Not Cleared

- Android physical release-build audit.
- Exact APK install/connect/reconnect/revoke smoke.
- Windows exact-artifact install/restart/secure-storage smoke.
- Windows trusted signing and SmartScreen reputation.
- Play, Microsoft Store, WinGet, TestFlight, App Store, or notarization.
- Real-user app-session download smoke.
- WARP release-build proof.
- Current-origin, brain-origin, and RU-origin evidence.
- Stable `1.0.0` claims.
- Public announcement or production deploy.
