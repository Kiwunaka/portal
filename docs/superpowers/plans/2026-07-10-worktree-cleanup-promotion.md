# Worktree Cleanup And Promotion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve every unique tracked, untracked, and retained ignored file; remove stale worktrees and merged local branches; then promote the verified platform and client documentation lines without force operations.

**Architecture:** Stage A inventories, snapshots retained ignored state, and creates reversible named stashes before docs that overlap stale worktrees. Stage B removes only exhaustively classified ignored generated output. Stage C removes clean worktrees without `--force`. Stage D promotes platform `master` and client `main` only after all checks pass.

**Tech Stack:** Git worktrees/stash, PowerShell Core, Windows filesystem path validation, SHA-256 file hashes, existing platform/client test commands.

## Global Constraints

- Never use `git reset --hard`, `git checkout --`, forced worktree removal, or force push.
- Never compose recursive filesystem deletion across shells.
- Before recursive copy/delete, resolve the absolute source and target and prove both stay inside their intended roots.
- Never print file contents from `ops-local/**`, release artifacts, secrets, signing material, local databases, or ignored auth/config files.
- `git stash --include-untracked` does not preserve ignored files; ignored state is a separate mandatory inventory.
- Unknown, secret-bearing, or unclassified ignored state blocks removal.
- A local stash is never pushed automatically.
- A local branch is deleted only after `git merge-base --is-ancestor` proves its HEAD is reachable from the retained branch.
- Platform and client repositories retain separate commits and promotion evidence.
- Active integration worktrees are never removed by this plan.

---

## Current Read-Only Baseline

Observed on 2026-07-10; remeasure before acting:

| Worktree | Branch | Tracked dirty | Untracked | Ignored | Known retained ignored risk |
| --- | --- | ---: | ---: | ---: | --- |
| `C:/Users/kiwun/.config/superpowers/worktrees/VPN/premium-bank-app-portal` | `codex/premium-bank-app-portal` | 30 | 2 | 45,423 | unknown until path-level classification |
| `C:/Users/kiwun/.config/superpowers/worktrees/VPN/release-hardening-platform` | `codex/release-hardening-platform` | 91 | 117 | 42,122 | `ops-local/**`; test DBs require generated-state classification |
| `C:/Users/kiwun/.config/superpowers/worktrees/POKROV-app/release-hardening-client` | `codex/release-hardening-client` | 26 | 27 | 143 | `artifacts/**` must be retained |

All three branch tips were ancestors of their retained branch at audit time.
Recheck immediately before branch deletion.

Active worktrees to preserve:

- `C:/Users/kiwun/Documents/ai/VPN/.worktrees/market-ready-cis-integration`
- `C:/Users/kiwun/Documents/ai/POKROV-app/.worktrees/market-ready-cis-client-integration`
- the documentation worktree until its commits reach `master`

### Interfaces

- Stage A produces: stash-ready patch state, ignored-state snapshot, collision
  classification, and manifest.
- Stage B consumes: a complete classification where every ignored path is
  `generated_disposable` or `retained_snapshotted`.
- Stage C consumes: clean Git status and no retained ignored data.
- Stage D consumes: green platform/client commits and clean main checkouts.

---

### Task 1: Create The Local Snapshot Root

**Files:**
- Create locally: `C:/Users/kiwun/Documents/ai/worktree-snapshots/2026-07-10-docs-renewal/`
- Create locally: `C:/Users/kiwun/Documents/ai/worktree-snapshots/2026-07-10-docs-renewal/manifest.json`
- Do not modify: any repository file in this task

**Interfaces:**
- Consumes: current worktree list
- Produces: validated local snapshot root

- [ ] **Step 1: Validate the backup path before creating it**

Run in PowerShell Core:

```powershell
$allowedRoot = [IO.Path]::GetFullPath('C:\Users\kiwun\Documents\ai\worktree-snapshots')
$backupRoot = [IO.Path]::GetFullPath('C:\Users\kiwun\Documents\ai\worktree-snapshots\2026-07-10-docs-renewal')
$comparison = [StringComparison]::OrdinalIgnoreCase
if (-not ($backupRoot.StartsWith($allowedRoot + [IO.Path]::DirectorySeparatorChar, $comparison))) {
    throw "Backup root escaped allowed snapshot directory: $backupRoot"
}
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
```

Expected: directory exists only beneath
`C:/Users/kiwun/Documents/ai/worktree-snapshots/`.

- [ ] **Step 2: Re-list all platform and client worktrees**

Run:

```powershell
git -C 'C:\Users\kiwun\Documents\ai\VPN' worktree list --porcelain
git -C 'C:\Users\kiwun\Documents\ai\POKROV-app' worktree list --porcelain
```

Expected: all three stale and both active integration worktrees are visible.
If a path or branch differs from the baseline table, update the collision
record before continuing.

### Task 2: Inventory And Classify Every Stale Worktree

**Files:**
- Modify locally: `C:/Users/kiwun/Documents/ai/worktree-snapshots/2026-07-10-docs-renewal/manifest.json`
- Create in Git object stores: one named tracked/untracked stash per stale
  worktree in Task 4
- Do not modify: stale worktree contents in this task

**Interfaces:**
- Consumes: validated snapshot root
- Produces: exhaustive path classification and overlap list

- [ ] **Step 1: Collect counts without printing contents**

Run the following once per stale worktree, setting `$worktree` to each exact
path in the baseline table:

```powershell
$worktree = [IO.Path]::GetFullPath('C:\Users\kiwun\.config\superpowers\worktrees\VPN\premium-bank-app-portal')
$tracked = @(& git -C $worktree diff --name-only)
$untracked = @(& git -C $worktree ls-files --others --exclude-standard)
$ignored = @(& git -C $worktree ls-files --others --ignored --exclude-standard)
[pscustomobject]@{
    worktree = $worktree
    branch = (& git -C $worktree branch --show-current)
    head = (& git -C $worktree rev-parse HEAD)
    tracked_count = $tracked.Count
    untracked_count = $untracked.Count
    ignored_count = $ignored.Count
} | Format-List
```

Expected: no file contents are printed. Counts are reconciled with the latest
state rather than copied blindly from the audit table.

- [ ] **Step 2: Scan changed paths for secret-bearing risk without printing values**

Run once per stale worktree:

```powershell
git -C $worktree status --short | Select-String -Pattern '(?i)(\.env|secret|credential|auth|token|key|\.pfx|\.pem|\.key|ops-local)'
Push-Location $worktree
rg.exe -l -i --hidden "BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY|authorization\s*:\s*bearer|api[_-]?key\s*[:=]|client[_-]?secret\s*[:=]" .
Pop-Location
```

Expected: path names only. Every hit is classified before stashing. A real
secret-bearing path is retained locally and never copied into tracked docs,
chat, or a pushed branch.

- [ ] **Step 3: Classify ignored paths by exact safe prefixes**

Allowed generated/disposable examples after inspection:

```text
**/node_modules/**
**/.next/**
**/out/**
**/.dart_tool/**
**/build/**
**/flutter/ephemeral/**
**/__pycache__/**
.pytest_cache/**
.tmp/**
portal_api_test_*.db
```

Mandatory retained/snapshotted roots:

```text
release-hardening-platform/ops-local/**
release-hardening-client/artifacts/**
```

Any `.env*`, auth file, signing file, key, password bundle, subscription
material, database outside the explicit test-DB pattern, or path not matching
the classification blocks removal until separately preserved.

- [ ] **Step 4: Produce the overlap list**

Run for each stale worktree:

```powershell
git -C $worktree diff --name-only
git -C $worktree ls-files --others --exclude-standard
```

Expected: path names only. Compare them against every planned platform/client
write path. Copy relevant diffs into the conflict review before docs renewal;
do not assume an ancestor branch means the dirty work is obsolete.

- [ ] **Step 5: Write the inventory manifest without file contents**

```powershell
$backupRoot = [IO.Path]::GetFullPath('C:\Users\kiwun\Documents\ai\worktree-snapshots\2026-07-10-docs-renewal')
$worktrees = @(
  'C:\Users\kiwun\.config\superpowers\worktrees\VPN\premium-bank-app-portal',
  'C:\Users\kiwun\.config\superpowers\worktrees\VPN\release-hardening-platform',
  'C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\release-hardening-client'
)
$entries = foreach ($path in $worktrees) {
    [pscustomobject]@{
        worktree = [IO.Path]::GetFullPath($path)
        branch = (& git -C $path branch --show-current)
        head = (& git -C $path rev-parse HEAD)
        tracked_count = @(& git -C $path diff --name-only).Count
        untracked_count = @(& git -C $path ls-files --others --exclude-standard).Count
        ignored_count = @(& git -C $path ls-files --others --ignored --exclude-standard).Count
    }
}
[pscustomobject]@{
    created_utc = [DateTime]::UtcNow.ToString('o')
    worktrees = $entries
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $backupRoot 'manifest.json') -Encoding utf8
```

Expected: manifest contains paths, branches, HEADs, and counts only.

### Task 3: Snapshot Retained Ignored State

**Files:**
- Copy locally: `release-hardening-platform/ops-local/**`
- Copy locally: `release-hardening-client/artifacts/**`
- Create locally: SHA-256 manifests beneath the matching snapshot directories

**Interfaces:**
- Consumes: exhaustive classification from Task 2
- Produces: recoverable retained ignored state

- [ ] **Step 1: Validate source and destination roots**

Run separately for each retained root:

```powershell
$sourceWorktree = [IO.Path]::GetFullPath('C:\Users\kiwun\.config\superpowers\worktrees\VPN\release-hardening-platform')
$source = [IO.Path]::GetFullPath((Join-Path $sourceWorktree 'ops-local'))
$backupRoot = [IO.Path]::GetFullPath('C:\Users\kiwun\Documents\ai\worktree-snapshots\2026-07-10-docs-renewal')
$destination = [IO.Path]::GetFullPath((Join-Path $backupRoot 'release-hardening-platform\ops-local'))
$comparison = [StringComparison]::OrdinalIgnoreCase
if (-not $source.StartsWith($sourceWorktree + [IO.Path]::DirectorySeparatorChar, $comparison)) {
    throw "Source escaped worktree: $source"
}
if (-not $destination.StartsWith($backupRoot + [IO.Path]::DirectorySeparatorChar, $comparison)) {
    throw "Destination escaped snapshot root: $destination"
}
```

For the client repeat with:

```text
sourceWorktree = C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\release-hardening-client
relative source = artifacts
destination = C:\Users\kiwun\Documents\ai\worktree-snapshots\2026-07-10-docs-renewal\release-hardening-client\artifacts
```

Expected: both prefix assertions pass.

- [ ] **Step 2: Copy without displaying content**

Run:

```powershell
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
Copy-Item -LiteralPath $source -Destination $destination -Recurse -Force
```

Expected: retained ignored roots exist in the snapshot directory.

- [ ] **Step 3: Verify file counts and hashes**

Run:

```powershell
$sourceFiles = @(Get-ChildItem -LiteralPath $source -File -Recurse)
$destinationFiles = @(Get-ChildItem -LiteralPath $destination -File -Recurse)
if ($sourceFiles.Count -ne $destinationFiles.Count) {
    throw "Snapshot file-count mismatch"
}
$sourceHashes = @{}
foreach ($file in $sourceFiles) {
    $relative = [IO.Path]::GetRelativePath($source, $file.FullName)
    $sourceHashes[$relative] = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
}
foreach ($file in $destinationFiles) {
    $relative = [IO.Path]::GetRelativePath($destination, $file.FullName)
    $destinationHash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    if (-not $sourceHashes.ContainsKey($relative) -or $sourceHashes[$relative] -ne $destinationHash) {
        throw "Snapshot hash mismatch for retained relative path"
    }
}
```

Expected: counts match. Do not print file contents or include them in chat.

### Task 4: Stash Tracked And Untracked State

**Files:**
- Git object store only; no tracked source files

**Interfaces:**
- Consumes: completed ignored-state snapshot
- Produces: named, readable local stash per stale worktree

- [ ] **Step 1: Create a named stash**

Run the exact command in each stale worktree:

```powershell
git -C 'C:\Users\kiwun\.config\superpowers\worktrees\VPN\premium-bank-app-portal' stash push --include-untracked -m "pre-cleanup/2026-07-10/premium-bank-app-portal"
$premiumStash = git -C 'C:\Users\kiwun\Documents\ai\VPN' rev-parse refs/stash
git -C 'C:\Users\kiwun\Documents\ai\VPN' stash show --include-untracked --stat $premiumStash

git -C 'C:\Users\kiwun\.config\superpowers\worktrees\VPN\release-hardening-platform' stash push --include-untracked -m "pre-cleanup/2026-07-10/release-hardening-platform"
$platformReleaseStash = git -C 'C:\Users\kiwun\Documents\ai\VPN' rev-parse refs/stash
git -C 'C:\Users\kiwun\Documents\ai\VPN' stash show --include-untracked --stat $platformReleaseStash

git -C 'C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\release-hardening-client' stash push --include-untracked -m "pre-cleanup/2026-07-10/release-hardening-client"
$clientReleaseStash = git -C 'C:\Users\kiwun\Documents\ai\POKROV-app' rev-parse refs/stash
git -C 'C:\Users\kiwun\Documents\ai\POKROV-app' stash show --include-untracked --stat $clientReleaseStash
$manifestPath = 'C:\Users\kiwun\Documents\ai\worktree-snapshots\2026-07-10-docs-renewal\manifest.json'
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
$manifest | Add-Member -NotePropertyName stashes -NotePropertyValue ([pscustomobject]@{
    premium_bank_app_portal = $premiumStash
    release_hardening_platform = $platformReleaseStash
    release_hardening_client = $clientReleaseStash
}) -Force
$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifestPath -Encoding utf8
```

Expected: a stash object ID is returned and the tracked/untracked worktree
status becomes clean. Record the exact object ID in the local manifest.

- [ ] **Step 2: Verify reconstruction before deleting anything**

Run:

```powershell
$premiumLine = git -C 'C:\Users\kiwun\Documents\ai\VPN' stash list --format="%H %gs" | Where-Object { $_ -like '*pre-cleanup/2026-07-10/premium-bank-app-portal*' } | Select-Object -First 1
$platformReleaseLine = git -C 'C:\Users\kiwun\Documents\ai\VPN' stash list --format="%H %gs" | Where-Object { $_ -like '*pre-cleanup/2026-07-10/release-hardening-platform*' } | Select-Object -First 1
$clientReleaseLine = git -C 'C:\Users\kiwun\Documents\ai\POKROV-app' stash list --format="%H %gs" | Where-Object { $_ -like '*pre-cleanup/2026-07-10/release-hardening-client*' } | Select-Object -First 1
$premiumStash = ($premiumLine -split ' ', 2)[0]
$platformReleaseStash = ($platformReleaseLine -split ' ', 2)[0]
$clientReleaseStash = ($clientReleaseLine -split ' ', 2)[0]
if (-not $premiumStash -or -not $platformReleaseStash -or -not $clientReleaseStash) {
    throw "One or more named cleanup stashes are missing"
}
git -C 'C:\Users\kiwun\Documents\ai\VPN' stash show --include-untracked --name-status $premiumStash
git -C 'C:\Users\kiwun\Documents\ai\VPN' stash show --include-untracked --name-status $platformReleaseStash
git -C 'C:\Users\kiwun\Documents\ai\POKROV-app' stash show --include-untracked --name-status $clientReleaseStash
git -C 'C:\Users\kiwun\.config\superpowers\worktrees\VPN\premium-bank-app-portal' status --short
git -C 'C:\Users\kiwun\.config\superpowers\worktrees\VPN\release-hardening-platform' status --short
git -C 'C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\release-hardening-client' status --short
```

Expected: stash paths match the pre-stash tracked/untracked inventory and Git
status has no tracked/untracked changes.

### Task 5: Remove Only Classified Ignored Generated Output

**Files:**
- Delete locally: only paths classified `generated_disposable`
- Delete locally after snapshot verification: retained ignored roots already
  copied in Task 3

**Interfaces:**
- Consumes: exhaustive classification, snapshot, and readable stash
- Produces: clean removable stale worktree

- [ ] **Step 1: Preview ignored cleanup**

Run:

```powershell
$worktrees = @(
  'C:\Users\kiwun\.config\superpowers\worktrees\VPN\premium-bank-app-portal',
  'C:\Users\kiwun\.config\superpowers\worktrees\VPN\release-hardening-platform',
  'C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\release-hardening-client'
)
foreach ($worktree in $worktrees) {
    git -C $worktree clean -ndX
}
```

Expected: every listed path exists in Task 2 classification. If one path is
unknown, stop; do not run the destructive command.

- [ ] **Step 2: Revalidate the worktree absolute path**

Before any recursive deletion:

```powershell
$allowed = [IO.Path]::GetFullPath('C:\Users\kiwun\.config\superpowers\worktrees')
$comparison = [StringComparison]::OrdinalIgnoreCase
$worktrees = @(
  'C:\Users\kiwun\.config\superpowers\worktrees\VPN\premium-bank-app-portal',
  'C:\Users\kiwun\.config\superpowers\worktrees\VPN\release-hardening-platform',
  'C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\release-hardening-client'
)
foreach ($worktree in $worktrees) {
    $target = [IO.Path]::GetFullPath($worktree)
    if (-not $target.StartsWith($allowed + [IO.Path]::DirectorySeparatorChar, $comparison)) {
        throw "Worktree escaped allowed cleanup root: $target"
    }
}
```

Expected: assertion passes for each of the three stale worktrees.

- [ ] **Step 3: Remove classified ignored paths**

Only after the preview count equals the classified ignored count:

```powershell
foreach ($worktree in $worktrees) {
    git -C $worktree clean -fdX
    git -C $worktree status --short --ignored
}
```

Expected: no ignored path remains; retained copies and hashes still exist under
the external snapshot root.

### Task 6: Remove Stale Worktrees And Merged Branches

**Files:**
- Git worktree metadata only

**Interfaces:**
- Consumes: clean worktree, readable stash, verified ignored snapshot
- Produces: removed stale worktree and retained branch history

- [ ] **Step 1: Prove branch reachability**

For platform branches:

```powershell
git -C 'C:\Users\kiwun\Documents\ai\VPN' merge-base --is-ancestor codex/premium-bank-app-portal master
git -C 'C:\Users\kiwun\Documents\ai\VPN' merge-base --is-ancestor codex/release-hardening-platform master
```

For the client:

```powershell
git -C 'C:\Users\kiwun\Documents\ai\POKROV-app' merge-base --is-ancestor codex/release-hardening-client main
```

Expected: every command exits 0. A non-zero result blocks branch deletion.

- [ ] **Step 2: Remove each clean worktree without force**

Run from the owning main checkout:

```powershell
git -C 'C:\Users\kiwun\Documents\ai\VPN' worktree remove 'C:\Users\kiwun\.config\superpowers\worktrees\VPN\premium-bank-app-portal'
git -C 'C:\Users\kiwun\Documents\ai\VPN' worktree remove 'C:\Users\kiwun\.config\superpowers\worktrees\VPN\release-hardening-platform'
git -C 'C:\Users\kiwun\Documents\ai\POKROV-app' worktree remove 'C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\release-hardening-client'
```

Expected: all commands succeed without `--force`.

- [ ] **Step 3: Delete only the merged local branches**

Run:

```powershell
git -C 'C:\Users\kiwun\Documents\ai\VPN' branch -d codex/premium-bank-app-portal
git -C 'C:\Users\kiwun\Documents\ai\VPN' branch -d codex/release-hardening-platform
git -C 'C:\Users\kiwun\Documents\ai\POKROV-app' branch -d codex/release-hardening-client
```

Expected: normal `-d` deletion succeeds; named stashes remain readable.

### Task 7: Promote Platform And Client Documentation

**Files:**
- Git branches and worktree metadata only

**Interfaces:**
- Consumes: green platform/client commits and completed collision reconciliation
- Produces: platform `master`, client `main`, clean root checkouts

- [ ] **Step 1: Promote the active platform baseline first**

From the clean platform root checkout:

```powershell
git switch master
git merge --ff-only codex/market-ready-cis-integration
```

Expected: `master` contains the committed account-foundation baseline. If the
merge is not fast-forward, stop and inspect the graph; do not force or create
an unreviewed merge.

- [ ] **Step 2: Replay the docs branch onto updated master**

From the docs worktree:

```powershell
git rebase master
```

Expected: conflicts are resolved by preserving newer account/product/client
canon and reapplying the thin-context/docs architecture. Rerun every platform
plan check after the rebase.

- [ ] **Step 3: Fast-forward platform master to the verified docs branch**

From the platform root:

```powershell
git merge --ff-only codex/agent-context-refactor
```

Expected: platform `master` reaches all verified documentation commits.

- [ ] **Step 4: Fast-forward client main to the verified client docs branch**

From the client root:

```powershell
git switch main
git merge --ff-only codex/agent-context-refactor-client
```

Expected: client `main` reaches the verified client docs commit without a
force operation.

- [ ] **Step 5: Push only after final verification**

Run:

```powershell
git push origin master
git -C 'C:\Users\kiwun\Documents\ai\POKROV-app' push origin main
```

Expected: normal pushes succeed. If remote history moved, stop and fetch/review;
do not force push.

### Task 8: Remove Temporary Docs Worktrees

**Files:**
- Git worktree metadata only

**Interfaces:**
- Consumes: commits reachable from retained platform/client branches
- Produces: requested steady state

- [ ] **Step 1: Prove temporary branch reachability**

Run:

```powershell
git merge-base --is-ancestor codex/product-audit-closure master
git merge-base --is-ancestor codex/agent-context-refactor master
git -C 'C:\Users\kiwun\Documents\ai\POKROV-app' merge-base --is-ancestor codex/agent-context-refactor-client main
```

Expected: all commands exit 0.

- [ ] **Step 2: Remove temporary clean worktrees and branches**

Run without `--force`:

```powershell
git -C 'C:\Users\kiwun\Documents\ai\VPN' worktree remove 'C:\Users\kiwun\Documents\ai\VPN\.worktrees\agent-context-refactor'
git -C 'C:\Users\kiwun\Documents\ai\VPN' branch -d codex/agent-context-refactor
git -C 'C:\Users\kiwun\Documents\ai\VPN' branch -d codex/product-audit-closure
git -C 'C:\Users\kiwun\Documents\ai\POKROV-app' worktree remove 'C:\Users\kiwun\Documents\ai\POKROV-app\.worktrees\agent-context-refactor-client'
git -C 'C:\Users\kiwun\Documents\ai\POKROV-app' branch -d codex/agent-context-refactor-client
```

Expected steady state:

- platform root on `master`;
- client root on `main`;
- active market-ready worktrees retained until their own tasks finish;
- stale and documentation worktrees removed;
- all local snapshots and named stashes still recoverable.

List remaining local branches in both repos. Do not delete any additional branch
without the same reachability and active-task ownership checks.

### Task 9: Contract The Local Content-Video Instruction Chain

**Files:**
- Backup locally: `C:/Users/kiwun/Documents/ai/worktree-snapshots/2026-07-10-docs-renewal/content-video-ad/AGENTS.before.md`
- Modify locally: `C:/Users/kiwun/Documents/ai/VPN/.content-video-ad/AGENTS.md`
- Do not commit: the workspace remains intentionally ignored

**Interfaces:**
- Consumes: final thin platform root contract
- Produces: combined root + local Codex instruction chain below 32 KiB

- [ ] **Step 1: Copy the current local contract to the snapshot root**

```powershell
$source = [IO.Path]::GetFullPath('C:\Users\kiwun\Documents\ai\VPN\.content-video-ad\AGENTS.md')
$backupRoot = [IO.Path]::GetFullPath('C:\Users\kiwun\Documents\ai\worktree-snapshots\2026-07-10-docs-renewal')
$destination = [IO.Path]::GetFullPath((Join-Path $backupRoot 'content-video-ad\AGENTS.before.md'))
$comparison = [StringComparison]::OrdinalIgnoreCase
if (-not $source.StartsWith([IO.Path]::GetFullPath('C:\Users\kiwun\Documents\ai\VPN\.content-video-ad') + [IO.Path]::DirectorySeparatorChar, $comparison)) {
    throw "Content-video source escaped local workspace"
}
if (-not $destination.StartsWith($backupRoot + [IO.Path]::DirectorySeparatorChar, $comparison)) {
    throw "Content-video backup escaped snapshot root"
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
Copy-Item -LiteralPath $source -Destination $destination -Force
```

Expected: backup hash equals the original before edits.

- [ ] **Step 2: Reduce the local contract to 20–22 KiB**

Preserve:

- POKROV/VPN content mission, offer, brand and public wording;
- end-to-end production loop and output contract;
- reference/trend/dance safety;
- legal/safety prohibitions;
- model/TTS/avatar/recovery/trace guards;
- exact commands and failure handoff.

Replace detailed duplicated instructions with links to existing local owners:

```text
docs/pokrov-brand.md
docs/pipeline.md
docs/video-agent-operating-loop.md
docs/model-routing.md
docs/opencode-production-script-rules.md
docs/prompting-principles.md
docs/avatar-generation-rules.md
docs/tts-narration-rules.md
docs/legal-safety.md
docs/social-publishing-rules.md
config/models.yaml
```

Do not change the offer, workflow, model routes, TTS rules, or public-copy
policy while shortening.

- [ ] **Step 3: Verify byte budgets and local gates**

```powershell
python -c "from pathlib import Path; root=Path(r'C:\Users\kiwun\Documents\ai\VPN\AGENTS.md').read_bytes(); local=Path(r'C:\Users\kiwun\Documents\ai\VPN\.content-video-ad\AGENTS.md').read_bytes(); print({'root':len(root),'local':len(local),'combined':len(root)+len(local)}); assert len(local) <= 22528; assert len(root)+len(local) < 32768"
npm.cmd run prompts:audit
npm.cmd run typecheck
```

Expected: local file is 20–22 KiB, combined chain is below 32 KiB, prompt audit
and typecheck pass.

- [ ] **Step 4: Record the local-only result**

Report the original/final hashes and byte counts. Do not stage or commit the
ignored workspace.
