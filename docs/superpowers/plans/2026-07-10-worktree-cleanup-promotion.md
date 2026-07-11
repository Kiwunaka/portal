# Worktree Cleanup And Promotion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve every unique tracked, untracked, and retained ignored file; remove stale worktrees and merged local branches; then promote the verified platform and client documentation lines without force operations.

**Architecture:** Stage A inventories, snapshots retained ignored state, and creates reversible named stashes before docs that overlap stale worktrees. Stage B uses one pinned, resumable Python proof/operator to remove only exhaustively classified ignored output. Stage C remains blocked until separately reviewed removal operators can remove clean worktrees without `--force`. Stage D promotes platform `master` and client `main` only after all checks pass.

**Tech Stack:** Git worktrees/stash, Python standard library for destructive proof/operator code, PowerShell Core for earlier non-gate steps, Windows path validation, SHA-256, existing platform/client test commands.

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

The counts above are expected audit inputs, not constants to copy into a new
manifest. The same audit measured `release-hardening-platform/ops-local/**` as
2 files / 2,052 bytes and the complete client `artifacts/**` tree, across all
tracked states, as 114 files / 2,016,578,139 bytes. Stage A must re-inventory
the live path sets and retained files. Any count, HEAD, branch, or path-set
drift is a stop condition until it is reviewed and recorded.

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
- Create in Task 2: `C:/Users/kiwun/Documents/ai/worktree-snapshots/2026-07-10-docs-renewal/manifest.json`
- Do not modify: any repository file in this task

**Interfaces:**
- Consumes: current worktree list
- Produces: validated local snapshot root

- [ ] **Step 1: Validate the backup path before creating it**

Run in PowerShell Core:

```powershell
$ErrorActionPreference = 'Stop'
$allowedRoot = [IO.Path]::GetFullPath('C:\Users\kiwun\Documents\ai\worktree-snapshots')
$backupRoot = [IO.Path]::GetFullPath('C:\Users\kiwun\Documents\ai\worktree-snapshots\2026-07-10-docs-renewal')
$comparison = [StringComparison]::OrdinalIgnoreCase
if (-not ($backupRoot.StartsWith($allowedRoot + [IO.Path]::DirectorySeparatorChar, $comparison))) {
    throw "Backup root escaped allowed snapshot directory: $backupRoot"
}
if (-not (Test-Path -LiteralPath $allowedRoot)) {
    New-Item -ItemType Directory -Path $allowedRoot | Out-Null
}
$allowedItem = Get-Item -Force -LiteralPath $allowedRoot
if (-not $allowedItem.PSIsContainer -or ($allowedItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw "Allowed snapshot root is not a plain directory: $allowedRoot"
}
if (Test-Path -LiteralPath $backupRoot) {
    throw "One-shot snapshot destination already exists; do not reuse or merge it: $backupRoot"
}
New-Item -ItemType Directory -Path $backupRoot | Out-Null
$backupItem = Get-Item -Force -LiteralPath $backupRoot
if (-not $backupItem.PSIsContainer -or ($backupItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw "Snapshot destination is not a plain directory: $backupRoot"
}
```

Expected: a new plain directory exists only beneath
`C:/Users/kiwun/Documents/ai/worktree-snapshots/`. Stage A is one-shot. If a
later step fails, preserve this partial destination for diagnosis and choose a
new absent destination after review; never retry into or merge with it.

- [ ] **Step 2: Re-list all platform and client worktrees**

Run:

```powershell
git -C 'C:\Users\kiwun\Documents\ai\VPN' worktree list --porcelain
git -C 'C:\Users\kiwun\Documents\ai\POKROV-app' worktree list --porcelain
```

Expected: all three stale and both active integration worktrees are visible.
If a path or branch differs from the baseline table, stop before Task 2. Do
not continue by editing the expectation in place; review the drift and start a
new one-shot Stage A run with an absent destination.

### Task 2: Inventory And Classify Every Stale Worktree

**Files:**
- Modify locally: `C:/Users/kiwun/Documents/ai/worktree-snapshots/2026-07-10-docs-renewal/manifest.json`
- Create in Git object stores: one named tracked/untracked stash per stale
  worktree in Task 4
- Do not modify: stale worktree contents in this task

**Interfaces:**
- Consumes: validated snapshot root
- Produces: exhaustive path classification and overlap list

- [ ] **Step 1: Inventory complete path sets and current identity**

Run once. This records Git-relative paths only; it never reads file contents:

```powershell
$ErrorActionPreference = 'Stop'
$backupRoot = [IO.Path]::GetFullPath('C:\Users\kiwun\Documents\ai\worktree-snapshots\2026-07-10-docs-renewal')
$manifestPath = Join-Path $backupRoot 'manifest.json'
if (-not (Test-Path -LiteralPath $backupRoot -PathType Container)) { throw "Missing one-shot snapshot root" }
if (Test-Path -LiteralPath $manifestPath) { throw "Inventory manifest already exists; do not merge Stage A runs" }

function Invoke-GitPathSet {
    param([string]$Repo, [string[]]$GitArgs)
    $lines = @(& git -c core.quotepath=false -C $Repo @GitArgs)
    if ($LASTEXITCODE -ne 0) { throw "git failed in ${Repo}: $($GitArgs -join ' ')" }
    $normalized = @($lines | Where-Object { $_ -ne '' } | ForEach-Object { $_.Replace('\', '/') })
    $set = New-OrdinalSet $normalized "git paths in $Repo"
    return @(Get-OrdinalSortedValues $set)
}

function New-OrdinalSet {
    param([object[]]$Values, [string]$Label)
    $set = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($value in @($Values)) {
        if ($value -isnot [string] -or $value.Length -eq 0) { throw "$Label has an empty or non-string value" }
        if (-not $set.Add($value)) { throw "$Label has a duplicate value: $value" }
    }
    return ,$set
}

function Get-OrdinalSortedValues {
    param([Collections.Generic.HashSet[string]]$Set)
    [string[]]$values = @($Set)
    [Array]::Sort($values, [StringComparer]::Ordinal)
    return $values
}

function Assert-OrdinalBijection {
    param([object[]]$Expected, [object[]]$Actual, [string]$Label)
    $expectedSet = New-OrdinalSet $Expected "$Label expected"
    $actualSet = New-OrdinalSet $Actual "$Label actual"
    if ($expectedSet.Count -ne $actualSet.Count -or -not $expectedSet.SetEquals($actualSet)) {
        throw "$Label is not an ordinal one-to-one match"
    }
}

$specs = @(
    [pscustomobject]@{ id='premium-bank-app-portal'; worktree='C:\Users\kiwun\.config\superpowers\worktrees\VPN\premium-bank-app-portal'; repo_root='C:\Users\kiwun\Documents\ai\VPN'; expected_branch='codex/premium-bank-app-portal'; expected_tracked=30; expected_untracked=2; expected_ignored=45423 },
    [pscustomobject]@{ id='release-hardening-platform'; worktree='C:\Users\kiwun\.config\superpowers\worktrees\VPN\release-hardening-platform'; repo_root='C:\Users\kiwun\Documents\ai\VPN'; expected_branch='codex/release-hardening-platform'; expected_tracked=91; expected_untracked=117; expected_ignored=42122 },
    [pscustomobject]@{ id='release-hardening-client'; worktree='C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\release-hardening-client'; repo_root='C:\Users\kiwun\Documents\ai\POKROV-app'; expected_branch='codex/release-hardening-client'; expected_tracked=26; expected_untracked=27; expected_ignored=143 }
)

$drift = [Collections.Generic.List[string]]::new()
$entries = foreach ($spec in $specs) {
    $worktree = [IO.Path]::GetFullPath($spec.worktree)
    $branch = @(& git -C $worktree branch --show-current)
    if ($LASTEXITCODE -ne 0 -or $branch.Count -ne 1) { throw "Cannot read branch for $worktree" }
    $head = @(& git -C $worktree rev-parse HEAD)
    if ($LASTEXITCODE -ne 0 -or $head.Count -ne 1) { throw "Cannot read HEAD for $worktree" }
    $tracked = @(Invoke-GitPathSet $worktree @('diff', 'HEAD', '--name-only', '--no-renames'))
    $headTree = @(Invoke-GitPathSet $worktree @('ls-tree', '-r', '--name-only', 'HEAD'))
    $indexFiles = @(Invoke-GitPathSet $worktree @('ls-files'))
    $untracked = @(Invoke-GitPathSet $worktree @('ls-files', '--others', '--exclude-standard'))
    $ignored = @(Invoke-GitPathSet $worktree @('ls-files', '--others', '--ignored', '--exclude-standard'))
    if ($branch[0] -ne $spec.expected_branch) { $drift.Add("$($spec.id): branch") }
    if ($tracked.Count -ne $spec.expected_tracked) { $drift.Add("$($spec.id): tracked count") }
    if ($untracked.Count -ne $spec.expected_untracked) { $drift.Add("$($spec.id): untracked count") }
    if ($ignored.Count -ne $spec.expected_ignored) { $drift.Add("$($spec.id): ignored count") }
    [pscustomobject]@{
        id = $spec.id
        worktree = $worktree
        repo_root = [IO.Path]::GetFullPath($spec.repo_root)
        branch = $branch[0]
        head = $head[0]
        tracked_paths = $tracked
        tracked_count = $tracked.Count
        head_tree_paths = $headTree
        head_tree_count = $headTree.Count
        index_file_paths = $indexFiles
        index_file_count = $indexFiles.Count
        untracked_paths = $untracked
        untracked_count = $untracked.Count
        ignored_paths = $ignored
        ignored_count = $ignored.Count
    }
}
```

Expected: staged plus unstaged tracked paths come from
`git diff HEAD --name-only`. The exact `HEAD` tree and current index are frozen
separately with exit-checked `git ls-tree -r --name-only HEAD` and
`git ls-files`; untracked and ignored paths remain separate.

- [ ] **Step 2: Classify ignored paths using path metadata only**

Continue in the same PowerShell process. Known generated prefixes are checked
before risk words so package files such as `node_modules/**/token*` do not
become false secret hits. No content-search command belongs in this procedure.

```powershell
function Get-IgnoredClass {
    param([string]$Id, [string]$RelativePath)
    $path = $RelativePath.Replace('\', '/')

    if ($Id -ceq 'release-hardening-platform' -and $path -cmatch '^ops-local(?:/|$)') { return 'retained_snapshotted' }
    if ($Id -ceq 'release-hardening-client' -and (
        $path -cmatch '^artifacts(?:/|$)' -or
        $path -cin @(
            'apps/android_shell/android/gradle/wrapper/gradle-wrapper.jar',
            'apps/android_shell/android/gradlew',
            'apps/android_shell/android/gradlew.bat',
            'apps/android_shell/android/local.properties'
        ) -or
        $path -cmatch '^apps/ios_shell/ios/Flutter(?:/|$)'
    )) { return 'retained_snapshotted' }

    if ($path -cmatch '(^|/)(node_modules|\.next|out|\.dart_tool|build|__pycache__)(/|$)' -or
        $path -cmatch '(^|/)flutter/ephemeral(/|$)' -or
        $path -cmatch '^apps/macos_shell/macos/Flutter/ephemeral(?:/|$)' -or
        $path -cmatch '^(\.pytest_cache|\.tmp)(/|$)' -or
        $path -cmatch '(^|/)portal_api_test_[^/]*\.db$' -or
        ($Id -cne 'release-hardening-client' -and $path -cin @('marketing/next-env.d.ts', 'webapp/next-env.d.ts')) -or
        ($Id -ceq 'release-hardening-client' -and (
            $path -cmatch '^(apps|packages)/(?:.*/)?\.flutter-plugins[^/]*$' -or
            $path -cmatch '^apps/android_shell/android/\.gradle(?:/|$)' -or
            $path -cmatch '^apps/android_shell/android/(?:.*/)?GeneratedPluginRegistrant\.java$' -or
            $path -cmatch '^apps/ios_shell/ios/Runner/GeneratedPluginRegistrant\.[^/]+$'
        ))
    ) { return 'generated_disposable' }

    if ($path -match '(^|/)\.env(?:[./]|$)|secret|credential|(^|/)auth(?:[./]|$)|token|password|subscription|\.(pfx|pem|key|jks|keystore)$') {
        return 'high_risk'
    }
    return 'unknown'
}

foreach ($entry in $entries) {
    $classified = foreach ($path in @($entry.ignored_paths)) {
        [pscustomobject]@{ path=$path; classification=(Get-IgnoredClass $entry.id $path) }
    }
    $entry | Add-Member -NotePropertyName ignored_classification -NotePropertyValue @($classified)
    $entry | Add-Member -NotePropertyName high_risk_paths -NotePropertyValue @($classified | Where-Object classification -eq 'high_risk' | ForEach-Object path)
    $entry | Add-Member -NotePropertyName unknown_paths -NotePropertyValue @($classified | Where-Object classification -eq 'unknown' | ForEach-Object path)
    Assert-OrdinalBijection @($entry.ignored_paths) @($classified | ForEach-Object path) "$($entry.id) ignored classification"
}
```

Expected: every ignored path is either `generated_disposable` or
`retained_snapshotted`. High-risk and unknown paths block cleanup and remain
in their local worktree.

- [ ] **Step 3: Persist inventory, classifications, expectations, and blockers**

```powershell
$expectedIds = @('premium-bank-app-portal', 'release-hardening-platform', 'release-hardening-client')
Assert-OrdinalBijection $expectedIds @($entries | ForEach-Object id) 'worktree IDs'
foreach ($entry in $entries) {
    if ($entry.tracked_count -ne @($entry.tracked_paths).Count -or
        $entry.head_tree_count -ne @($entry.head_tree_paths).Count -or
        $entry.index_file_count -ne @($entry.index_file_paths).Count -or
        $entry.untracked_count -ne @($entry.untracked_paths).Count -or
        $entry.ignored_count -ne @($entry.ignored_paths).Count -or
        @($entry.ignored_classification).Count -ne $entry.ignored_count) {
        throw "$($entry.id) persisted counts do not match path arrays"
    }
    Assert-OrdinalBijection @($entry.ignored_paths) @($entry.ignored_classification | ForEach-Object path) "$($entry.id) persisted classification"
}
$blockers = @($entries | ForEach-Object { @($_.high_risk_paths) + @($_.unknown_paths) })
$inventoryState = if ($drift.Count -eq 0 -and $blockers.Count -eq 0) { 'INVENTORY_VERIFIED' } else { 'INVENTORY_BLOCKED' }
$manifest = [pscustomobject]@{
    schema_version = 2
    created_utc = [DateTime]::UtcNow.ToString('o')
    stage_a_state = $inventoryState
    audit_expectations = [pscustomobject]@{
        observed_on = '2026-07-10'
        platform_ops_local = [pscustomobject]@{ file_count=2; byte_count=2052 }
        client_artifacts = [pscustomobject]@{ file_count=114; byte_count=2016578139 }
    }
    audit_drift = @($drift)
    worktrees = @($entries)
    retained_snapshots = @()
    stashes = @()
    cleanup_receipts = @()
}
$json = $manifest | ConvertTo-Json -Depth 12
[IO.File]::WriteAllText($manifestPath, $json, [Text.UTF8Encoding]::new($false))

if ($drift.Count -gt 0) { throw "Preflight drift recorded in manifest; review before a new Stage A run" }
if ($blockers.Count -gt 0) { throw "Unknown/high-risk ignored paths recorded in manifest; cleanup remains blocked" }
$reloaded = [IO.File]::ReadAllText($manifestPath) | ConvertFrom-Json
if ($reloaded.stage_a_state -cne 'INVENTORY_VERIFIED' -or @($reloaded.audit_drift).Count -ne 0) { throw "Reloaded inventory is not verified" }
Assert-OrdinalBijection $expectedIds @($reloaded.worktrees | ForEach-Object id) 'reloaded worktree IDs'
foreach ($entry in @($reloaded.worktrees)) {
    if (@($entry.high_risk_paths).Count -ne 0 -or @($entry.unknown_paths).Count -ne 0) { throw "$($entry.id) reloaded blockers are non-empty" }
    if ($entry.tracked_count -ne @($entry.tracked_paths).Count -or $entry.head_tree_count -ne @($entry.head_tree_paths).Count -or $entry.index_file_count -ne @($entry.index_file_paths).Count -or $entry.untracked_count -ne @($entry.untracked_paths).Count -or $entry.ignored_count -ne @($entry.ignored_paths).Count) { throw "$($entry.id) reloaded counts mismatch" }
    Assert-OrdinalBijection @($entry.ignored_paths) @($entry.ignored_classification | ForEach-Object path) "$($entry.id) reloaded classification"
    foreach ($classification in @($entry.ignored_classification | ForEach-Object classification)) {
        if ($classification -cnotin @('generated_disposable', 'retained_snapshotted')) { throw "$($entry.id) has unsafe classification $classification" }
    }
}
```

Expected: `manifest.json` persists complete relative path sets and counts,
without file contents. Compare `tracked_paths` and `untracked_paths` against
every later plan write set. A path overlap requires explicit reconciliation;
an ancestor branch does not make dirty work obsolete.

### Task 3: Snapshot Mandatory Retained Local State

**Files:**
- Copy locally: `release-hardening-platform/ops-local/**`
- Copy locally: `release-hardening-client/artifacts/**`
- Copy locally: the client Gradle wrapper JAR/scripts, `local.properties`, and
  `apps/ios_shell/ios/Flutter/**` paths named in Step 1
- Create locally: SHA-256 manifests beneath the matching snapshot directories

**Interfaces:**
- Consumes: exhaustive classification from Task 2
- Produces: recoverable retained ignored state

- [ ] **Step 1: Copy every mandatory retained path into absent destinations**

Run this block once. It enumerates both sides with
`Get-ChildItem -Force -File -Recurse`, rejects reparse points, and preserves
paths relative to the owning worktree. It copies the complete client
`artifacts/**` tree regardless of tracked state.

```powershell
$ErrorActionPreference = 'Stop'
$backupRoot = [IO.Path]::GetFullPath('C:\Users\kiwun\Documents\ai\worktree-snapshots\2026-07-10-docs-renewal')
$manifestPath = Join-Path $backupRoot 'manifest.json'
$comparison = [StringComparison]::OrdinalIgnoreCase

function New-OrdinalSet {
    param([object[]]$Values, [string]$Label)
    $set = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($value in @($Values)) {
        if ($value -isnot [string] -or $value.Length -eq 0 -or -not $set.Add($value)) { throw "$Label has an invalid or duplicate value: $value" }
    }
    return ,$set
}
function Assert-OrdinalBijection {
    param([object[]]$Expected, [object[]]$Actual, [string]$Label)
    $expectedSet = New-OrdinalSet $Expected "$Label expected"
    $actualSet = New-OrdinalSet $Actual "$Label actual"
    if ($expectedSet.Count -ne $actualSet.Count -or -not $expectedSet.SetEquals($actualSet)) { throw "$Label mismatch" }
}
function New-OrdinalRecordMap {
    param([object[]]$Records, [string]$KeyProperty, [string]$Label)
    $map = [Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
    foreach ($record in @($Records)) {
        $key = $record.$KeyProperty
        if ($key -isnot [string] -or $key.Length -eq 0 -or $map.ContainsKey($key)) { throw "$Label has an invalid or duplicate key: $key" }
        $map.Add($key, $record)
    }
    return ,$map
}
function Assert-InventoryPredecessor {
    param([object]$Manifest)
    if ($Manifest.schema_version -ne 2 -or $Manifest.stage_a_state -cne 'INVENTORY_VERIFIED') { throw 'Snapshot task requires exact INVENTORY_VERIFIED predecessor state' }
    if (@($Manifest.audit_drift).Count -ne 0 -or @($Manifest.retained_snapshots).Count -ne 0 -or @($Manifest.stashes).Count -ne 0 -or @($Manifest.cleanup_receipts).Count -ne 0) { throw 'Inventory predecessor contains drift or premature proof records' }
    $expected = @(
        [pscustomobject]@{ id='premium-bank-app-portal'; tracked=30; untracked=2; ignored=45423 },
        [pscustomobject]@{ id='release-hardening-platform'; tracked=91; untracked=117; ignored=42122 },
        [pscustomobject]@{ id='release-hardening-client'; tracked=26; untracked=27; ignored=143 }
    )
    Assert-OrdinalBijection @($expected | ForEach-Object id) @($Manifest.worktrees | ForEach-Object id) 'inventory worktree IDs'
    $expectedMap = New-OrdinalRecordMap $expected id 'expected worktrees'
    foreach ($entry in @($Manifest.worktrees)) {
        $spec = $expectedMap[$entry.id]
        if ($entry.tracked_count -ne $spec.tracked -or $entry.untracked_count -ne $spec.untracked -or $entry.ignored_count -ne $spec.ignored -or
            $entry.tracked_count -ne @($entry.tracked_paths).Count -or $entry.head_tree_count -ne @($entry.head_tree_paths).Count -or $entry.index_file_count -ne @($entry.index_file_paths).Count -or $entry.untracked_count -ne @($entry.untracked_paths).Count -or
            $entry.ignored_count -ne @($entry.ignored_paths).Count -or @($entry.ignored_classification).Count -ne $entry.ignored_count) {
            throw "$($entry.id) inventory count mismatch"
        }
        if (@($entry.high_risk_paths).Count -ne 0 -or @($entry.unknown_paths).Count -ne 0) { throw "$($entry.id) inventory blockers are non-empty" }
        Assert-OrdinalBijection @($entry.ignored_paths) @($entry.ignored_classification | ForEach-Object path) "$($entry.id) classification"
        foreach ($classification in @($entry.ignored_classification | ForEach-Object classification)) {
            if ($classification -cnotin @('generated_disposable', 'retained_snapshotted')) { throw "$($entry.id) unsafe classification: $classification" }
        }
    }
}

$inventoryManifest = [IO.File]::ReadAllText($manifestPath) | ConvertFrom-Json
Assert-InventoryPredecessor $inventoryManifest

function Assert-PlainTree {
    param([string]$Root)
    $rootItem = Get-Item -Force -LiteralPath $Root
    if (-not $rootItem.PSIsContainer -or ($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Not a plain directory: $Root"
    }
    $reparse = @(Get-ChildItem -Force -LiteralPath $Root -Recurse | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
    if ($reparse.Count -gt 0) { throw "Reparse point found below retained root: $Root" }
}

function Test-RetainedSpecPath {
    param([string]$RelativePath,[string[]]$RelativeSpecs)
    foreach($specValue in $RelativeSpecs){$spec=$specValue.Replace('\','/').TrimEnd('/');if($RelativePath -ceq $spec -or $RelativePath.StartsWith($spec+'/',[StringComparison]::Ordinal)){return $true}}
    return $false
}

function Get-RetainedRecords {
    param([string]$Worktree, [string[]]$RelativeSpecs, [object]$InventoryEntry)
    $worktreeRoot = [IO.Path]::GetFullPath($Worktree)
    $filesByRelativePath = [Collections.Generic.Dictionary[string,string]]::new([StringComparer]::Ordinal)
    foreach ($spec in $RelativeSpecs) {
        $source = [IO.Path]::GetFullPath((Join-Path $worktreeRoot $spec))
        if (-not $source.StartsWith($worktreeRoot + [IO.Path]::DirectorySeparatorChar, $comparison)) { throw "Retained source escaped worktree: $source" }
        if (-not (Test-Path -LiteralPath $source)) { continue }
        $item = Get-Item -Force -LiteralPath $source
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Retained source is a reparse point: $source" }
        $files = if ($item.PSIsContainer) {
            Assert-PlainTree $source
            @(Get-ChildItem -Force -File -Recurse -LiteralPath $source)
        } else { @($item) }
        foreach ($file in $files) {
            $relative = [IO.Path]::GetRelativePath($worktreeRoot, $file.FullName).Replace('\', '/')
            if ($relative -eq '..' -or $relative.StartsWith('../')) { throw "Retained file escaped worktree" }
            if ($filesByRelativePath.ContainsKey($relative)) { throw "Duplicate retained relative path: $relative" }
            $filesByRelativePath.Add($relative, $file.FullName)
        }
    }
    $trackedDirty=New-OrdinalSet @($InventoryEntry.tracked_paths) "$($InventoryEntry.id) tracked-dirty inventory"
    $headTree=New-OrdinalSet @($InventoryEntry.head_tree_paths) "$($InventoryEntry.id) HEAD-tree inventory"
    $indexFiles=New-OrdinalSet @($InventoryEntry.index_file_paths) "$($InventoryEntry.id) index-file inventory"
    $untracked=New-OrdinalSet @($InventoryEntry.untracked_paths) "$($InventoryEntry.id) untracked inventory"
    $ignored=New-OrdinalSet @($InventoryEntry.ignored_paths) "$($InventoryEntry.id) ignored inventory"
    $classificationMap=New-OrdinalRecordMap @($InventoryEntry.ignored_classification) path "$($InventoryEntry.id) ignored classifications"
    $deletions=[Collections.Generic.List[object]]::new()
    foreach($path in $trackedDirty){
        if(-not (Test-RetainedSpecPath $path $RelativeSpecs) -or $filesByRelativePath.ContainsKey($path)){continue}
        if(-not $headTree.Contains($path) -or $untracked.Contains($path) -or $ignored.Contains($path)){throw "Absent dirty retained path is not an exact HEAD-tree deletion: $path"}
        $deletions.Add([pscustomobject]@{relative_path=$path;original_git_state='tracked_deleted';snapshot_present=$false;head_present=$true;index_present=$indexFiles.Contains($path)})
    }
    $deletionMap=New-OrdinalRecordMap @($deletions) relative_path "$($InventoryEntry.id) tracked deletions"
    foreach($specValue in $RelativeSpecs){
        $spec=$specValue.Replace('\','/').TrimEnd('/')
        $covered=@($filesByRelativePath.Keys|Where-Object{$_ -ceq $spec -or $_.StartsWith($spec+'/',[StringComparison]::Ordinal)})+@($deletionMap.Keys|Where-Object{$_ -ceq $spec -or $_.StartsWith($spec+'/',[StringComparison]::Ordinal)})
        if($covered.Count -eq 0){throw "Mandatory retained spec has no saved or tracked-deleted record: $spec"}
    }
    [string[]]$relativePaths = @($filesByRelativePath.Keys)
    [Array]::Sort($relativePaths, [StringComparer]::Ordinal)
    $files=@($relativePaths | ForEach-Object {
        $file = Get-Item -Force -LiteralPath $filesByRelativePath[$_]
        $isIgnored=$ignored.Contains($_);$isUntracked=$untracked.Contains($_);$isHead=$headTree.Contains($_);$isIndex=$indexFiles.Contains($_);$isDirty=$trackedDirty.Contains($_)
        if($isIgnored){
            if($isUntracked -or $isHead -or $isIndex -or $isDirty -or -not $classificationMap.ContainsKey($_) -or $classificationMap[$_].classification -cne 'retained_snapshotted'){throw "Conflicting ignored retained state: $_"}
            $state='ignored_retained'
        }elseif($isUntracked){
            if($isHead -or $isIndex -or $isDirty){throw "Conflicting untracked retained state: $_"};$state='untracked'
        }elseif($isDirty -and ($isHead -or $isIndex)){
            $state='tracked_dirty'
        }elseif(-not $isDirty -and $isHead -and $isIndex){
            $state='tracked_clean'
        }else{throw "Retained path has no frozen Git state: $_"}
        [pscustomobject]@{
            relative_path = $_
            source_full_name = $file.FullName
            byte_length = $file.Length
            sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
            original_git_state = $state
            snapshot_present = $true
            head_present = $isHead
            index_present = $isIndex
        }
    })
    Assert-OrdinalBijection @($files|ForEach-Object relative_path) @($filesByRelativePath.Keys) "$($InventoryEntry.id) saved retained states"
    $allStatePaths=@($files|ForEach-Object relative_path)+@($deletions|ForEach-Object relative_path)
    [void](New-OrdinalSet $allStatePaths "$($InventoryEntry.id) retained state mapping")
    return [pscustomobject]@{files=$files;tracked_deletions=@($deletions)}
}

function Assert-RecordMatch {
    param([object[]]$Expected, [object[]]$Actual, [string]$Label)
    $expectedByPath = New-OrdinalRecordMap $Expected relative_path "$Label expected records"
    $actualByPath = New-OrdinalRecordMap $Actual relative_path "$Label actual records"
    Assert-OrdinalBijection @($expectedByPath.Keys) @($actualByPath.Keys) "$Label relative-path set"
    foreach ($path in $expectedByPath.Keys) {
        if ($expectedByPath[$path].byte_length -ne $actualByPath[$path].byte_length -or $expectedByPath[$path].sha256 -ne $actualByPath[$path].sha256) {
            throw "$Label length/hash mismatch: $path"
        }
        if($expectedByPath[$path].PSObject.Properties.Name -contains 'original_git_state' -and $actualByPath[$path].PSObject.Properties.Name -contains 'original_git_state' -and $expectedByPath[$path].original_git_state -cne $actualByPath[$path].original_git_state){throw "$Label Git-state mismatch: $path"}
        if($expectedByPath[$path].PSObject.Properties.Name -contains 'head_present' -and $actualByPath[$path].PSObject.Properties.Name -contains 'head_present' -and ($expectedByPath[$path].head_present -ne $actualByPath[$path].head_present -or $expectedByPath[$path].index_present -ne $actualByPath[$path].index_present)){throw "$Label HEAD/index membership mismatch: $path"}
    }
}
function Assert-DeletionMatch {
    param([object[]]$Expected,[object[]]$Actual,[string]$Label)
    $expectedMap=New-OrdinalRecordMap $Expected relative_path "$Label expected";$actualMap=New-OrdinalRecordMap $Actual relative_path "$Label actual"
    Assert-OrdinalBijection @($expectedMap.Keys) @($actualMap.Keys) "$Label paths"
    foreach($path in $expectedMap.Keys){if($expectedMap[$path].original_git_state -cne 'tracked_deleted' -or $actualMap[$path].original_git_state -cne 'tracked_deleted' -or $expectedMap[$path].snapshot_present -ne $false -or $actualMap[$path].snapshot_present -ne $false -or $expectedMap[$path].head_present -ne $true -or $actualMap[$path].head_present -ne $true -or $expectedMap[$path].index_present -ne $actualMap[$path].index_present){throw "$Label invalid deletion state: $path"}}
}

function New-RetainedSnapshot {
    param(
        [string]$Id,
        [string]$Worktree,
        [object]$InventoryEntry,
        [string[]]$RelativeSpecs,
        [string]$AuditPrefix,
        [int]$ExpectedAuditFiles,
        [long]$ExpectedAuditBytes
    )
    $snapshotRoot = [IO.Path]::GetFullPath((Join-Path $backupRoot $Id))
    if (-not $snapshotRoot.StartsWith($backupRoot + [IO.Path]::DirectorySeparatorChar, $comparison)) { throw "Snapshot escaped backup root" }
    if (Test-Path -LiteralPath $snapshotRoot) { throw "Snapshot destination already exists: $snapshotRoot" }

    $retainedState = Get-RetainedRecords $Worktree $RelativeSpecs $InventoryEntry
    $sourceRecords = @($retainedState.files)
    $trackedDeletions=@($retainedState.tracked_deletions)
    $auditRecords = @($sourceRecords | Where-Object { $_.relative_path -eq $AuditPrefix -or $_.relative_path.StartsWith($AuditPrefix + '/', [StringComparison]::Ordinal) })
    $auditDeletions=@($trackedDeletions|Where-Object{$_.relative_path -eq $AuditPrefix -or $_.relative_path.StartsWith($AuditPrefix+'/',[StringComparison]::Ordinal)})
    $auditBytes = ($auditRecords | Measure-Object -Property byte_length -Sum).Sum
    if (($auditRecords.Count+$auditDeletions.Count) -ne $ExpectedAuditFiles -or ($auditDeletions.Count -eq 0 -and $auditBytes -ne $ExpectedAuditBytes)) {
        throw "$Id retained audit input drifted; do not copy or clean"
    }

    New-Item -ItemType Directory -Path $snapshotRoot | Out-Null
    foreach ($record in $sourceRecords) {
        $destination = [IO.Path]::GetFullPath((Join-Path $snapshotRoot $record.relative_path))
        if (-not $destination.StartsWith($snapshotRoot + [IO.Path]::DirectorySeparatorChar, $comparison)) { throw "Retained destination escaped snapshot root" }
        if (Test-Path -LiteralPath $destination) { throw "Retained destination collision: $destination" }
        [IO.Directory]::CreateDirectory((Split-Path -Parent $destination)) | Out-Null
        [IO.File]::Copy($record.source_full_name, $destination, $false)
    }

    $snapshotManifestPath = Join-Path $snapshotRoot '.snapshot-sha256.json'
    $persisted = [pscustomobject]@{
        id = $Id
        source_worktree = [IO.Path]::GetFullPath($Worktree)
        relative_specs = @($RelativeSpecs)
        file_count = $sourceRecords.Count
        tracked_deletion_count = $trackedDeletions.Count
        record_count = $sourceRecords.Count+$trackedDeletions.Count
        byte_count = ($sourceRecords | Measure-Object -Property byte_length -Sum).Sum
        files = @($sourceRecords | Select-Object relative_path, byte_length, sha256, original_git_state, snapshot_present, head_present, index_present)
        tracked_deletions=@($trackedDeletions)
        audit=[pscustomobject]@{prefix=$AuditPrefix;expected_file_count=$ExpectedAuditFiles;expected_byte_count=$ExpectedAuditBytes;observed_saved_files=$auditRecords.Count;observed_tracked_deletions=$auditDeletions.Count;observed_saved_bytes=$auditBytes}
    }
    [IO.File]::WriteAllText($snapshotManifestPath, ($persisted | ConvertTo-Json -Depth 8), [Text.UTF8Encoding]::new($false))

    Assert-PlainTree $snapshotRoot
    $saved = [IO.File]::ReadAllText($snapshotManifestPath) | ConvertFrom-Json
    $destinationRecords = @(Get-ChildItem -Force -File -Recurse -LiteralPath $snapshotRoot |
        Where-Object FullName -ne $snapshotManifestPath |
        ForEach-Object {
            [pscustomobject]@{
                relative_path = [IO.Path]::GetRelativePath($snapshotRoot, $_.FullName).Replace('\', '/')
                byte_length = $_.Length
                sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
            }
        })
    $sourceAfterCopy=Get-RetainedRecords $Worktree $RelativeSpecs $InventoryEntry
    Assert-RecordMatch @($saved.files) @($sourceAfterCopy.files|Select-Object relative_path,byte_length,sha256,original_git_state,snapshot_present,head_present,index_present) "$Id source-after-copy"
    Assert-DeletionMatch @($saved.tracked_deletions) @($sourceAfterCopy.tracked_deletions) "$Id tracked deletions after copy"
    Assert-RecordMatch @($saved.files) $destinationRecords "$Id destination"
    return [pscustomobject]@{ id=$Id; manifest=[IO.Path]::GetRelativePath($backupRoot, $snapshotManifestPath).Replace('\', '/'); file_count=$saved.file_count;tracked_deletion_count=$saved.tracked_deletion_count;record_count=$saved.record_count; byte_count=$saved.byte_count; verified=$true }
}

$platformInventory=@($inventoryManifest.worktrees|Where-Object id -CEQ 'release-hardening-platform');if($platformInventory.Count -ne 1){throw 'Platform inventory entry mismatch'}
$clientInventory=@($inventoryManifest.worktrees|Where-Object id -CEQ 'release-hardening-client');if($clientInventory.Count -ne 1){throw 'Client inventory entry mismatch'}
$platformSnapshot = New-RetainedSnapshot `
    -Id 'release-hardening-platform' `
    -Worktree 'C:\Users\kiwun\.config\superpowers\worktrees\VPN\release-hardening-platform' `
    -InventoryEntry $platformInventory[0] `
    -RelativeSpecs @('ops-local') `
    -AuditPrefix 'ops-local' -ExpectedAuditFiles 2 -ExpectedAuditBytes 2052

$clientSnapshot = New-RetainedSnapshot `
    -Id 'release-hardening-client' `
    -Worktree 'C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\release-hardening-client' `
    -InventoryEntry $clientInventory[0] `
    -RelativeSpecs @(
        'artifacts',
        'apps/android_shell/android/gradle/wrapper/gradle-wrapper.jar',
        'apps/android_shell/android/gradlew',
        'apps/android_shell/android/gradlew.bat',
        'apps/android_shell/android/local.properties',
        'apps/ios_shell/ios/Flutter'
    ) `
    -AuditPrefix 'artifacts' -ExpectedAuditFiles 114 -ExpectedAuditBytes 2016578139
```

Expected: each persisted SHA-256 manifest contains the exact relative path,
byte length, hash, and original Git state of every copied file. The allowed
saved-file states are `ignored_retained`, `tracked_dirty`, `untracked`, and
`tracked_clean`. A tracked deletion is a separate `tracked_deleted` record
with `snapshot_present=false`; it has no fabricated snapshot bytes. State paths
are ordinal and one-to-one. Every state record also freezes `head_present` and
`index_present`. An absent dirty retained path is `tracked_deleted` only when
the exact frozen HEAD-tree set contains it; current-index membership may be
true for an unstaged deletion or false for a staged deletion. An absent dirty
path outside HEAD is rejected. Both source and destination are re-enumerated
after copying, and every saved destination still requires a SHA-256 match.

- [ ] **Step 2: Record only verified snapshot manifests in the Stage A manifest**

```powershell
$manifest = [IO.File]::ReadAllText($manifestPath) | ConvertFrom-Json
Assert-InventoryPredecessor $manifest
Assert-OrdinalBijection @('release-hardening-platform', 'release-hardening-client') @($platformSnapshot.id, $clientSnapshot.id) 'new retained snapshot IDs'
$manifest.retained_snapshots = @($platformSnapshot, $clientSnapshot)
$manifest.stage_a_state = 'SNAPSHOTS_VERIFIED'
$temporaryManifest = "$manifestPath.tmp"
if (Test-Path -LiteralPath $temporaryManifest) { throw "Manifest temp collision" }
[IO.File]::WriteAllText($temporaryManifest, ($manifest | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))
[IO.File]::Move($temporaryManifest, $manifestPath, $true)
$reloaded = [IO.File]::ReadAllText($manifestPath) | ConvertFrom-Json
if ($reloaded.stage_a_state -cne 'SNAPSHOTS_VERIFIED' -or @($reloaded.audit_drift).Count -ne 0 -or @($reloaded.stashes).Count -ne 0 -or @($reloaded.cleanup_receipts).Count -ne 0) { throw 'Snapshot transition did not persist exact state' }
Assert-OrdinalBijection @('release-hardening-platform', 'release-hardening-client') @($reloaded.retained_snapshots | ForEach-Object id) 'persisted retained snapshot IDs'
foreach ($snapshot in @($reloaded.retained_snapshots)) {
    if ($snapshot.verified -ne $true -or $snapshot.record_count -le 0 -or $snapshot.file_count+$snapshot.tracked_deletion_count -ne $snapshot.record_count -or $snapshot.byte_count -lt 0) { throw "$($snapshot.id) snapshot summary is incomplete" }
}
```

Expected: the main manifest points to the two persisted, verified snapshot
manifests. Do not print file contents or copy any retained path into Git.

### Task 4: Stash Tracked And Untracked State

**Files:**
- Git object store only; no tracked source files

**Interfaces:**
- Consumes: completed ignored-state snapshot
- Produces: named, readable local stash per stale worktree

- [ ] **Step 1: Create and prove each stash from its immediate object ID**

Run once. Before every stash, this rechecks the exact frozen inventory and
requires a non-empty tracked-plus-untracked set. It never rediscovers a stash
by searching its message.

```powershell
$ErrorActionPreference = 'Stop'
$manifestPath = 'C:\Users\kiwun\Documents\ai\worktree-snapshots\2026-07-10-docs-renewal\manifest.json'
$manifest = [IO.File]::ReadAllText($manifestPath) | ConvertFrom-Json

function New-OrdinalSet {
    param([object[]]$Values, [string]$Label)
    $set = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($value in @($Values)) {
        if ($value -isnot [string] -or $value.Length -eq 0 -or -not $set.Add($value)) { throw "$Label has an invalid or duplicate value: $value" }
    }
    return ,$set
}
function Get-OrdinalSortedValues {
    param([Collections.Generic.HashSet[string]]$Set)
    [string[]]$values = @($Set)
    [Array]::Sort($values, [StringComparer]::Ordinal)
    return $values
}
function Assert-OrdinalBijection {
    param([object[]]$Expected, [object[]]$Actual, [string]$Label)
    $expectedSet = New-OrdinalSet $Expected "$Label expected"
    $actualSet = New-OrdinalSet $Actual "$Label actual"
    if ($expectedSet.Count -ne $actualSet.Count -or -not $expectedSet.SetEquals($actualSet)) { throw "$Label mismatch" }
}
function New-OrdinalRecordMap {
    param([object[]]$Records, [string]$KeyProperty, [string]$Label)
    $map = [Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
    foreach ($record in @($Records)) {
        $key = $record.$KeyProperty
        if ($key -isnot [string] -or $key.Length -eq 0 -or $map.ContainsKey($key)) { throw "$Label has an invalid or duplicate key: $key" }
        $map.Add($key, $record)
    }
    return ,$map
}
function Invoke-GitPathSet {
    param([string]$Repo, [string[]]$GitArgs)
    $lines = @(& git -c core.quotepath=false -C $Repo @GitArgs)
    if ($LASTEXITCODE -ne 0) { throw "git failed in ${Repo}: $($GitArgs -join ' ')" }
    $set = New-OrdinalSet @($lines | Where-Object { $_ -ne '' } | ForEach-Object { $_.Replace('\', '/') }) "git paths in $Repo"
    return @(Get-OrdinalSortedValues $set)
}
function Assert-SamePathSet {
    param([object[]]$Expected, [object[]]$Actual, [string]$Label)
    Assert-OrdinalBijection $Expected $Actual $Label
}
function Assert-SnapshotPredecessor {
    param([object]$Value)
    if ($Value.schema_version -ne 2 -or $Value.stage_a_state -cne 'SNAPSHOTS_VERIFIED') { throw 'Stash task requires exact SNAPSHOTS_VERIFIED predecessor state' }
    if (@($Value.audit_drift).Count -ne 0 -or @($Value.stashes).Count -ne 0 -or @($Value.cleanup_receipts).Count -ne 0) { throw 'Snapshot predecessor has drift or premature records' }
    $expectedCounts = @(
        [pscustomobject]@{ id='premium-bank-app-portal'; tracked=30; untracked=2; ignored=45423 },
        [pscustomobject]@{ id='release-hardening-platform'; tracked=91; untracked=117; ignored=42122 },
        [pscustomobject]@{ id='release-hardening-client'; tracked=26; untracked=27; ignored=143 }
    )
    Assert-OrdinalBijection @($expectedCounts | ForEach-Object id) @($Value.worktrees | ForEach-Object id) 'snapshot predecessor worktree IDs'
    $countMap = New-OrdinalRecordMap $expectedCounts id 'snapshot predecessor expected counts'
    foreach ($entry in @($Value.worktrees)) {
        $spec = $countMap[$entry.id]
        if ($entry.tracked_count -ne $spec.tracked -or $entry.untracked_count -ne $spec.untracked -or $entry.ignored_count -ne $spec.ignored -or
            $entry.tracked_count -ne @($entry.tracked_paths).Count -or $entry.head_tree_count -ne @($entry.head_tree_paths).Count -or $entry.index_file_count -ne @($entry.index_file_paths).Count -or $entry.untracked_count -ne @($entry.untracked_paths).Count -or
            $entry.ignored_count -ne @($entry.ignored_paths).Count -or @($entry.ignored_classification).Count -ne $entry.ignored_count) { throw "$($entry.id) predecessor count mismatch" }
        if (@($entry.high_risk_paths).Count -ne 0 -or @($entry.unknown_paths).Count -ne 0) { throw "$($entry.id) predecessor blockers are non-empty" }
        Assert-OrdinalBijection @($entry.ignored_paths) @($entry.ignored_classification | ForEach-Object path) "$($entry.id) predecessor classification"
        foreach ($classification in @($entry.ignored_classification | ForEach-Object classification)) {
            if ($classification -cnotin @('generated_disposable', 'retained_snapshotted')) { throw "$($entry.id) unsafe predecessor classification" }
        }
    }
    Assert-OrdinalBijection @('release-hardening-platform', 'release-hardening-client') @($Value.retained_snapshots | ForEach-Object id) 'snapshot predecessor snapshot IDs'
    foreach ($summary in @($Value.retained_snapshots)) {
        if ($summary.verified -ne $true -or $summary.file_count -le 0 -or $summary.byte_count -le 0) { throw "$($summary.id) snapshot summary invalid" }
        $snapshotManifestPath = Join-Path (Split-Path -Parent $manifestPath) $summary.manifest
        $saved = [IO.File]::ReadAllText($snapshotManifestPath) | ConvertFrom-Json
        $savedBytes=(@($saved.files)|Measure-Object -Property byte_length -Sum).Sum
        if ($saved.id -cne $summary.id -or $saved.file_count -ne @($saved.files).Count -or $saved.tracked_deletion_count -ne @($saved.tracked_deletions).Count -or $saved.record_count -ne ($saved.file_count+$saved.tracked_deletion_count) -or $saved.file_count -ne $summary.file_count -or $saved.tracked_deletion_count -ne $summary.tracked_deletion_count -or $saved.record_count -ne $summary.record_count -or $saved.byte_count -ne $summary.byte_count -or $saved.byte_count -ne $savedBytes) { throw "$($summary.id) snapshot manifest count mismatch" }
        $fileMap=New-OrdinalRecordMap @($saved.files) relative_path "$($summary.id) snapshot files";$deletionMap=New-OrdinalRecordMap @($saved.tracked_deletions) relative_path "$($summary.id) tracked deletions"
        $retainedStatePaths=@($fileMap.Keys)+@($deletionMap.Keys);[void](New-OrdinalSet $retainedStatePaths "$($summary.id) retained state paths")
        foreach($record in @($saved.files)){
            if($record.original_git_state -cnotin @('ignored_retained','tracked_dirty','untracked','tracked_clean') -or $record.snapshot_present -ne $true -or -not $record.sha256){throw "$($summary.id) invalid saved state: $($record.relative_path)"}
            if($record.original_git_state -cin @('ignored_retained','untracked') -and ($record.head_present -ne $false -or $record.index_present -ne $false)){throw "$($summary.id) non-tracked state has HEAD/index membership"}
            if($record.original_git_state -ceq 'tracked_dirty' -and -not($record.head_present -or $record.index_present)){throw "$($summary.id) tracked-dirty state lacks HEAD/index membership"}
            if($record.original_git_state -ceq 'tracked_clean' -and ($record.head_present -ne $true -or $record.index_present -ne $true)){throw "$($summary.id) tracked-clean state lacks exact HEAD/index membership"}
        }
        foreach($record in @($saved.tracked_deletions)){if($record.original_git_state -cne 'tracked_deleted' -or $record.snapshot_present -ne $false -or $record.head_present -ne $true -or $record.PSObject.Properties.Name -cnotcontains 'index_present'){throw "$($summary.id) invalid tracked deletion: $($record.relative_path)"}}
    }
}
function Save-StageManifest {
    param([object]$Value)
    $temporary = "$manifestPath.tmp"
    if (Test-Path -LiteralPath $temporary) { throw "Manifest temp collision" }
    [IO.File]::WriteAllText($temporary, ($Value | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))
    [IO.File]::Move($temporary, $manifestPath, $true)
}
function Get-CleanPreviewRecords {
    param([object]$Entry)
    $classificationMap = New-OrdinalRecordMap @($Entry.ignored_classification) path "$($Entry.id) preview classifications"
    $covered = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $previewPathSet = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $records = [Collections.Generic.List[object]]::new()
    $lines = @(& git -c core.quotepath=false -C $Entry.worktree clean -ndX)
    if ($LASTEXITCODE -ne 0) { throw "$($Entry.id) clean preview failed" }
    foreach ($line in $lines) {
        if (-not $line.StartsWith('Would remove ', [StringComparison]::Ordinal)) { throw "$($Entry.id) unparseable clean preview line: $line" }
        $candidate = $line.Substring(13).Replace('\', '/').TrimEnd('/')
        if ($candidate.Length -eq 0 -or $candidate.Contains('"') -or $candidate.Contains("`r") -or $candidate.Contains("`n") -or -not $previewPathSet.Add($candidate)) {
            throw "$($Entry.id) unsafe or duplicate clean preview path: $candidate"
        }
        $matches = @($Entry.ignored_paths | Where-Object { $_ -ceq $candidate -or $_.StartsWith($candidate + '/', [StringComparison]::Ordinal) })
        if ($matches.Count -eq 0) { throw "$($Entry.id) preview path covers no classified ignored path: $candidate" }
        $classes = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        foreach ($path in $matches) {
            if (-not $covered.Add($path)) { throw "$($Entry.id) overlapping clean preview coverage: $path" }
            [void]$classes.Add([string]$classificationMap[$path].classification)
        }
        if ($classes.Count -ne 1) { throw "$($Entry.id) preview path mixes generated and retained data: $candidate" }
        $records.Add([pscustomobject]@{ path=$candidate; classification=@($classes)[0] })
    }
    Assert-OrdinalBijection @($Entry.ignored_paths) @($covered) "$($Entry.id) preview coverage"
    $recordMap = New-OrdinalRecordMap @($records) path "$($Entry.id) preview records"
    [string[]]$keys = @($recordMap.Keys)
    [Array]::Sort($keys, [StringComparer]::Ordinal)
    return @($keys | ForEach-Object { $recordMap[$_] })
}

Assert-SnapshotPredecessor $manifest
$messages = [Collections.Generic.Dictionary[string,string]]::new([StringComparer]::Ordinal)
$messages.Add('premium-bank-app-portal', 'pre-cleanup/2026-07-10/premium-bank-app-portal')
$messages.Add('release-hardening-platform', 'pre-cleanup/2026-07-10/release-hardening-platform')
$messages.Add('release-hardening-client', 'pre-cleanup/2026-07-10/release-hardening-client')

foreach ($entry in @($manifest.worktrees)) {
    $branch = @(& git -C $entry.worktree branch --show-current)
    if ($LASTEXITCODE -ne 0 -or $branch.Count -ne 1 -or $branch[0] -ne $entry.branch) { throw "$($entry.id) branch drift" }
    $head = @(& git -C $entry.worktree rev-parse HEAD)
    if ($LASTEXITCODE -ne 0 -or $head.Count -ne 1 -or $head[0] -ne $entry.head) { throw "$($entry.id) HEAD drift" }

    $tracked = @(Invoke-GitPathSet $entry.worktree @('diff', 'HEAD', '--name-only', '--no-renames'))
    $untracked = @(Invoke-GitPathSet $entry.worktree @('ls-files', '--others', '--exclude-standard'))
    $ignoredBefore = @(Invoke-GitPathSet $entry.worktree @('ls-files', '--others', '--ignored', '--exclude-standard'))
    Assert-SamePathSet @($entry.tracked_paths) $tracked "$($entry.id) tracked"
    Assert-SamePathSet @($entry.untracked_paths) $untracked "$($entry.id) untracked"
    Assert-SamePathSet @($entry.ignored_paths) $ignoredBefore "$($entry.id) ignored"
    $preStashSet = New-OrdinalSet @($tracked + $untracked) "$($entry.id) pre-stash paths"
    $preStashPaths = @(Get-OrdinalSortedValues $preStashSet)
    if ($preStashPaths.Count -eq 0) { throw "$($entry.id) stash would be a no-op" }

    $preOid = @(& git -C $entry.repo_root rev-parse --verify -q refs/stash)
    $preOidExit = $LASTEXITCODE
    if ($preOidExit -eq 1) { $preOid = @() }
    elseif ($preOidExit -ne 0 -or $preOid.Count -ne 1) { throw "Cannot read pre-stash OID for $($entry.id)" }

    $message = $messages[$entry.id]
    & git -C $entry.worktree stash push --include-untracked -m $message
    if ($LASTEXITCODE -ne 0) { throw "stash push failed for $($entry.id)" }
    $newOid = @(& git -C $entry.repo_root rev-parse --verify refs/stash)
    if ($LASTEXITCODE -ne 0 -or $newOid.Count -ne 1) { throw "Cannot read immediate stash OID for $($entry.id)" }
    if ($preOid.Count -eq 1 -and $newOid[0] -eq $preOid[0]) { throw "$($entry.id) stash OID did not change" }

    $subject = @(& git -C $entry.repo_root show -s --format=%s $newOid[0])
    if ($LASTEXITCODE -ne 0 -or $subject.Count -ne 1 -or $subject[0] -ne "On $($entry.branch): $message") {
        throw "$($entry.id) stash message mismatch"
    }
    $stashPaths = @(Invoke-GitPathSet $entry.repo_root @('stash', 'show', '--include-untracked', '--name-only', '--no-renames', $newOid[0]))
    Assert-SamePathSet $preStashPaths $stashPaths "$($entry.id) stash"

    $trackedAfter = @(Invoke-GitPathSet $entry.worktree @('diff', 'HEAD', '--name-only', '--no-renames'))
    $untrackedAfter = @(Invoke-GitPathSet $entry.worktree @('ls-files', '--others', '--exclude-standard'))
    $statusAfter = @(& git -C $entry.worktree status --short)
    if ($LASTEXITCODE -ne 0 -or $trackedAfter.Count -ne 0 -or $untrackedAfter.Count -ne 0 -or $statusAfter.Count -ne 0) {
        throw "$($entry.id) is not tracked/untracked clean after stash"
    }
    $ignoredAfter = @(Invoke-GitPathSet $entry.worktree @('ls-files', '--others', '--ignored', '--exclude-standard'))
    Assert-SamePathSet @($entry.ignored_paths) $ignoredAfter "$($entry.id) post-stash ignored"

    $record = [pscustomobject]@{
        id = $entry.id
        oid = $newOid[0]
        pre_oid = if ($preOid.Count -eq 1) { $preOid[0] } else { $null }
        message = $message
        subject = $subject[0]
        path_count = $preStashPaths.Count
        verified_utc = [DateTime]::UtcNow.ToString('o')
    }
    $entry | Add-Member -NotePropertyName clean_preview_records -NotePropertyValue @(Get-CleanPreviewRecords $entry)
    $existingStashMap = New-OrdinalRecordMap @($manifest.stashes) id 'persisted stashes'
    if ($existingStashMap.ContainsKey($entry.id)) { throw "Duplicate persisted stash ID: $($entry.id)" }
    $manifest.stashes = @($manifest.stashes) + @($record)
    Save-StageManifest $manifest
}

if ($manifest.stage_a_state -cne 'SNAPSHOTS_VERIFIED' -or @($manifest.audit_drift).Count -ne 0 -or @($manifest.cleanup_receipts).Count -ne 0) { throw 'Stash loop predecessor state drifted' }
Assert-OrdinalBijection @('premium-bank-app-portal', 'release-hardening-platform', 'release-hardening-client') @($manifest.stashes | ForEach-Object id) 'verified stash IDs'
foreach ($entry in @($manifest.worktrees)) {
    Assert-OrdinalBijection @($entry.ignored_paths) @($entry.ignored_classification | ForEach-Object path) "$($entry.id) final classification"
    [void](New-OrdinalRecordMap @($entry.clean_preview_records) path "$($entry.id) persisted clean preview")
}
$manifest.stage_a_state = 'STAGE_A_VERIFIED'
Save-StageManifest $manifest
$reloaded = [IO.File]::ReadAllText($manifestPath) | ConvertFrom-Json
if ($reloaded.stage_a_state -cne 'STAGE_A_VERIFIED' -or @($reloaded.audit_drift).Count -ne 0 -or @($reloaded.cleanup_receipts).Count -ne 0) { throw 'Final Stage A state did not persist exactly' }
Assert-OrdinalBijection @('premium-bank-app-portal', 'release-hardening-platform', 'release-hardening-client') @($reloaded.worktrees | ForEach-Object id) 'reloaded final worktree IDs'
Assert-OrdinalBijection @('premium-bank-app-portal', 'release-hardening-platform', 'release-hardening-client') @($reloaded.stashes | ForEach-Object id) 'reloaded final stash IDs'
Assert-OrdinalBijection @('release-hardening-platform', 'release-hardening-client') @($reloaded.retained_snapshots | ForEach-Object id) 'reloaded final snapshot IDs'
foreach ($entry in @($reloaded.worktrees)) {
    if (@($entry.high_risk_paths).Count -ne 0 -or @($entry.unknown_paths).Count -ne 0 -or $entry.head_tree_count -ne @($entry.head_tree_paths).Count -or $entry.index_file_count -ne @($entry.index_file_paths).Count -or $entry.ignored_count -ne @($entry.ignored_paths).Count -or @($entry.ignored_classification).Count -ne $entry.ignored_count) { throw "$($entry.id) reloaded final entry is incomplete" }
    Assert-OrdinalBijection @($entry.ignored_paths) @($entry.ignored_classification | ForEach-Object path) "$($entry.id) reloaded final classification"
    foreach($classification in @($entry.ignored_classification|ForEach-Object classification)){if($classification -cnotin @('generated_disposable','retained_snapshotted')){throw "$($entry.id) reloaded unsafe classification"}}
    [void](New-OrdinalRecordMap @($entry.clean_preview_records) path "$($entry.id) reloaded clean preview")
}
```

Expected: each `stash push --include-untracked` exits 0, creates a different
immediate `refs/stash` OID, has the exact expected subject, and contains the
exact pre-stash tracked/untracked path set. The immediate verified OID is
persisted after each stash. Afterwards tracked/untracked state is empty and
the exact ignored path set is unchanged.

- [ ] **Step 2: Enforce the Stage A stop gate**

Do not run any Stage B or Stage C command unless `manifest.json` says
`STAGE_A_VERIFIED` and contains all three direct stash OIDs plus both verified
snapshot manifests. Stop on an existing snapshot destination, any reparse
point, branch/HEAD/path-set drift, unknown or high-risk ignored path,
copy/count/length/hash mismatch, stash no-op, stash command failure, unchanged
or unexpected OID, message mismatch, stash path-set mismatch, dirty post-stash
state, or changed ignored set. Preserve the worktrees, snapshot, and any
already-created stash for recovery; never weaken the gate to continue.

### Task 5: Remove Only Classified Ignored Generated Output

**Files:**

- Build locally only after this tracked amendment:
  `C:/Users/kiwun/Documents/ai/worktree-snapshots/2026-07-10-docs-renewal/cleanup-proof-gate.py`
- Create while pinning: `cleanup-proof-gate.lock`
- Use transiently: `manifest.json.task5.tmp`
- Delete locally: only the three frozen stale worktrees' exhaustively classified
  ignored paths, after the applicable retained records have passed live and
  saved cryptographic proof

**Interfaces:**

- Consumes: the exact approved Stage A manifest, two pinned snapshot manifests,
  three direct stashes, exhaustive classification, and exact worktree registries
- Produces: three resumable cleanup receipts and `CLEANED_VERIFIED`
- Does not authorize: stale-worktree removal, branch deletion, temporary
  worktree removal, promotion, or any Task 6/8 mutation

The former PowerShell gate and external clean loop are rejected. Build one
standalone Python-standard-library program at the fixed path above. Do not add a
wrapper, second runner, package, service, database, vector index, or cache.

- [ ] **Step 1: Implement one pinned program and four CLI commands**

Run the program only as `python.exe -B`. Its command surface is exact:

- `pin`: one-shot evidence pin; never deletes data;
- `prove`: read-only, with `BeforeClean`, `AfterClean`,
  `BeforeStaleRemoval`, and `BeforeTemporaryRemoval` modes;
- `execute-task5`: the sole fresh-run path allowed to invoke ignored cleanup;
- `recover-task5`: the sole recovery command for an interrupted pin epoch or an
  already-started Task 5 run. Pin recovery is non-cleaning; cleanup recovery may
  resume only the exact existing run.

The argument contract is fixed: `pin` receives the manifest path and approved
self hash; `prove` also receives one mode and entry ID; `execute-task5` also
receives one new run nonce. `recover-task5` receives the approved hash and uses
no nonce for a detected pin epoch, or requires the exact existing nonce for a
cleanup epoch. No command accepts a worktree path, Git argument, cleanup order,
or executable override from the caller.

The program must use only the Python standard library. It must reject an
unexpected path, non-plain source, reparse source/root, wrong byte count,
unapproved self SHA-256, failed parser/import smoke, or non-stdlib import. Every
command rehashes its own bytes and checks the manifest pin. Proof-only Git calls
use `GIT_OPTIONAL_LOCKS=0`, NUL-delimited byte parsing where paths are returned,
and never write a repository, index, worktree, stash, snapshot, or manifest.
Every proof-only Git path—including the general inventory adapter—must drain
stdout and stderr concurrently with bounded buffers, emit aggregate heartbeats
at least every 30 seconds, stop on no-progress or output-limit breach, and avoid
a blind total timeout while verified byte/process progress continues. It never
prints path inventory or unbounded child output.

The only auxiliary files are:

- `cleanup-proof-gate.lock`: a fixed one-byte, plain, non-reparse file created
  by `pin` and held with `msvcrt` for the full execute/recover session;
- `manifest.json.task5.tmp`: an absent-at-entry/exit atomic candidate that is
  never overwritten. Its presence requires `recover-task5`.

- [ ] **Step 2: Pin the exact approved evidence, not a Stage A-shaped substitute**

`pin` must accept only this raw predecessor:

- manifest bytes: `21,147,426`;
- manifest SHA-256:
  `99eef04c5e3cd82afa4251c689c83f47b3cd08e0177f4769fb71a9b9d5001cb0`;
- schema/state: `2 / STAGE_A_VERIFIED`;
- worktrees/snapshots/stashes/cleanup receipts/audit drift: `3 / 2 / 3 / 0 / 0`;
- ignored paths: `87,688` = `87,624 generated_disposable` +
  `64 retained_snapshotted`, with `0 unknown` and `0 high-risk`;
- clean-preview partitions: `11 / 316 / 25`;
- direct-stash path sets, in cleanup order: `32 / 208 / 53`;
- retained payload: `126` files / `2,016,644,392` bytes.

It must also pin the two persisted snapshot manifests by raw bytes and SHA-256:

| Snapshot ID | Bytes | SHA-256 |
| --- | ---: | --- |
| `release-hardening-platform` | 1,291 | `3c4bcf28d15e2f859fc58c10e35c16e3bc23d66aa3e5c81014a4099ce5c08079` |
| `release-hardening-client` | 46,246 | `6e132375b675ec5b31610a76857555017cecc72ae2957e61ed1725a69ebf0776` |

The client pin includes the exact `62` `ignored_retained` records /
`312,937,647` bytes threatened by Task 5. The remaining client snapshot records
stay outside the deletion targets.

All manifest and snapshot loads are strict JSON loads. Reject duplicate keys,
NaN/Infinity, booleans used as integers, floats used as integers, missing or
extra properties, wrong exact types, malformed hashes/timestamps, duplicate
IDs/paths, path escapes, and invalid state membership. Validate every declared
snapshot record and audit field, not only aggregate counts.

The raw snapshot manifests remain immutable and must match their exact byte and
file-hash pins. A per-file record SHA is valid only as exactly 64 hexadecimal
characters, in uppercase, lowercase, or mixed case. Canonicalize it in memory
to lowercase before record-digest or payload-hash comparison; never rewrite the
persisted bytes. Reject any non-hex character or wrong/mixed length. Live-format
tests must traverse the comparison path for all `126` actual uppercase records,
not only lowercase synthetic fixtures.

Compute canonical SHA-256 over the immutable projection:

```text
schema_version
created_utc
audit_expectations
audit_drift
worktrees
retained_snapshots
stashes
```

The reviewed script hard-codes the expected digest and recomputes it on every
invocation. The mutable manifest may repeat the value but is never its
authority. Mutable governance is limited to `cleanup_run`, `cleanup_receipts`,
the final `stage_a_state` transition, and later authority-bound removal receipt
collections. Optional `future_authorities` records may exist only inside a
`COMPLETE` `cleanup_run`; none of these mutable fields widens or changes the
immutable projection.

Stash authority is the exact ordered direct chain for
`premium-bank-app-portal`, `release-hardening-platform`, and
`release-hardening-client`. Prove each approved OID, predecessor, order,
message/subject, path-set digest and membership, commit readability, raw blob
recovery, and local LFS-object availability. Never apply, pop, drop, rewrite,
fetch, or materialize a stash through filters.

Registry authority is an exact bijection of five platform and four client
path/branch identities. The three stale path/branch/HEAD records stay frozen to
Stage A. Every non-stale root, docs/control, and active integration record must
have `registry HEAD == current branch ref` at each proof epoch. Reject a
missing, extra, replaced, detached, duplicate, unknown-key, or ref-mismatched
entry. Do not freeze a docs commit SHA in the script.

After complete validation, `pin` adds one exact `proof_gate` record containing
the fixed path, script bytes/hash, predecessor bytes/hash, immutable-evidence
hash, both snapshot-manifest pins, cleanup order, and pin time. It validates and
fsyncs the candidate before atomic `os.replace`, reloads the published bytes,
and checks exact postconditions. An existing `proof_gate`, lock mismatch,
candidate collision, or predecessor drift blocks pinning without mutation.

The normal pre-pin shape is the raw predecessor alone. A recoverable pin epoch
begins only when the permanent lock exists; its allowed durable shapes are raw
predecessor plus lock, raw predecessor plus lock and one exact temp candidate,
or the published `proof_gate` manifest plus lock and no temp. `recover-task5`
detects this epoch before any runtime validation and never invokes cleanup.

Validate the current raw predecessor with the predecessor schema, not the
runtime schema. Define the sole `PIN` one-step relation as exact raw predecessor
to exact `proof_gate` candidate. With a temp candidate, validate both raw files,
the relation, approved source, lock, and live read-only seals before promoting
or rejecting it; never overwrite the temp. With lock only, repeat read-only
predecessor validation and deterministic candidate construction. After replace,
reload the pinned manifest under the runtime schema and require the exact lock
and no temp. Cover crashes after lock creation, after candidate fsync but before
replace, and after replace, plus a wrong candidate; every recovery path is
non-cleaning and fail-closed.

- [ ] **Step 3: Keep proof cost mode-specific and recovery filter-aware**

| Mode | Required payload proof |
| --- | --- |
| `BeforeClean` | Validate all immutable evidence, stashes, classification, and registries; hash only the target's saved `ignored_retained` files and live peers. |
| `AfterClean` | Require zero tracked, untracked, ignored, and preview paths; rehash only the target's affected saved snapshot records. |
| `BeforeStaleRemoval` | Require `CLEANED_VERIFIED`, exact receipts and reachability, a fully empty target, the exact target stash, the deterministic pre-removal profile where earlier targets are absent and the current/later targets remain exactly once, and a full hash of that target's retained snapshot. |
| `BeforeTemporaryRemoval` | Require `CLEANED_VERIFIED`, exact earlier removal receipts/profile, a clean target, dynamic branch-ref/registry agreement, retained-line reachability, and retained recovery proof. |

Recovery checks must distinguish Git's raw object bytes from checked-out bytes.
Verify raw stash blobs directly, validate LFS pointer syntax plus the exact local
object hash/length, and prove CRLF-to-LF recovery without invoking checkout
filters or fetching data. Missing local recovery material blocks the mode.

Hash in bounded chunks. Emit aggregate-only counters at least every 30 seconds;
never print paths or contents. Stop after ten minutes with no CPU, I/O, or
progress change. Do not impose the old blind wall-time cutoff while verified
hash progress continues.

- [ ] **Step 4: Make cleanup one locked, durable state machine**

The top-level state remains `STAGE_A_VERIFIED` until the last receipt. Progress
lives in a strict nested object:

```text
PINNED (no cleanup_run)
  -> READY(ordinal=0, nonce, script_sha256)
  -> PREPROOF_VERIFIED(entry=1, evidence_digest)
  -> CLEAN_ATTEMPT_ARMED(entry=1, armed_utc)
  -> CLEAN_ATTEMPT_RECORDED(entry=1, outcome_digest)
  -> CLEAN_EXIT_VERIFIED(entry=1, exit=0, evidence_digest)
  -> READY(ordinal=1, receipt=1)
  -> PREPROOF_VERIFIED(entry=2, evidence_digest)
  -> CLEAN_ATTEMPT_ARMED(entry=2, armed_utc)
  -> CLEAN_ATTEMPT_RECORDED(entry=2, outcome_digest)
  -> CLEAN_EXIT_VERIFIED(entry=2, exit=0, evidence_digest)
  -> READY(ordinal=2, receipts=2)
  -> PREPROOF_VERIFIED(entry=3, evidence_digest)
  -> CLEAN_ATTEMPT_ARMED(entry=3, armed_utc)
  -> CLEAN_ATTEMPT_RECORDED(entry=3, outcome_digest)
  -> CLEAN_EXIT_VERIFIED(entry=3, exit=0, evidence_digest)
  -> COMPLETE(receipts=3) + CLEANED_VERIFIED
```

Every possible child launch is preceded by durable `CLEAN_ATTEMPT_ARMED`.
Within the uninterrupted lock-owning invocation, that marker permits exactly
one native cleanup call; it never permits a cleanup call after recovery.
Every returned native outcome then becomes durable `CLEAN_ATTEMPT_RECORDED`.
Read-only post-attempt observation transitions the outcome to
`CLEAN_EXIT_VERIFIED` or exact `BLOCKED`; neither state has an outgoing cleanup
transition. `BLOCKED` has no outgoing automatic transition.

The cleanup order and receipt-ID order are exact:

1. `premium-bank-app-portal`
2. `release-hardening-platform`
3. `release-hardening-client`

A new run requires an independently supplied nonce and the approved script
SHA-256. Once started, only that nonce and hash may resume. For each entry the
program must, without yielding a shell step:

1. perform the full target `BeforeClean` proof and compute one aggregate
   evidence digest;
2. atomically publish `PREPROOF_VERIFIED` with entry/ordinal, nonce, self hash,
   immutable digest, exact SHA-256 of the manifest bytes immediately preceding
   PREPROOF, stash digest, ignored/preview counts, affected
   snapshot/live counts and bytes, and the pre-proof digest;
3. reload and strictly validate the published manifest;
4. repeat the affected snapshot/live cryptographic proof and require the same
   digest;
5. atomically publish and reload `CLEAN_ATTEMPT_ARMED` before launching a child.
   It preserves every PREPROOF identity, digest, count, and byte aggregate and
   adds only the arm time; it contains no native outcome or post-live claim;
6. only in that same uninterrupted lock-owning invocation, invoke the sole
   deletion subprocess once as the fixed argument array
   `['git', '-C', <frozen-worktree>, 'clean', '-fdX']`, with `shell=False`;
7. make the mutating adapter return one bounded native outcome for exit,
   launch, timeout, stall, or output-limit termination; do not raise past the
   point where the child may have run;
8. with no fallible observation, injected yield, or shell step in between,
   atomically publish `CLEAN_ATTEMPT_RECORDED`. It preserves every PREPROOF
   and ARMED identity/digest/aggregate field, and adds the exact outcome kind,
   integer native exit or explicit no-exit, bounded stdout/stderr lengths and
   SHA-256 values, and observed UTC. It deliberately contains no fabricated
   post-live fields;
9. reload that marker and perform the read-only post-attempt live observation;
10. only for native exit `0`, stderr length `0`, and the exact required live
   result, atomically publish `CLEAN_EXIT_VERIFIED` with the observed live
   counts/digest. Otherwise atomically publish exact `BLOCKED` with the native
   outcome plus exact post-live tracked/untracked/ignored/preview counts and
   digest; and
11. from `CLEAN_EXIT_VERIFIED`, run `AfterClean`, append the bound receipt, and
    advance the ordinal atomically.

If post-attempt observation fails or stalls, keep
`CLEAN_ATTEMPT_RECORDED` byte-for-byte durable. Emit only bounded aggregate
error evidence when appropriate. Explicit recovery may retry that read-only
observation, but must not clean, create a receipt, infer success, or mutate any
other evidence until one exact observation permits the next state.

If recovery finds `CLEAN_ATTEMPT_ARMED` without an exact recoverable
`CLEAN_ATTEMPT_RECORDED` candidate, the native outcome is unknowable. It may run
only bounded read-only observation and then publish exact `BLOCKED` with reason
`UNKNOWN_NATIVE_OUTCOME_AFTER_ARM`, explicit no-exit, and observed post-live
counts/digest. Observation failure leaves ARMED durable and emits only aggregate
error evidence. It never relaunches cleanup, reaches `CLEAN_EXIT_VERIFIED`, or
creates a receipt from ARMED.

There is no raw shell cleanup command to copy. On receipt three, the same atomic
write sets `cleanup_run.state=COMPLETE` and
`stage_a_state=CLEANED_VERIFIED`. Either field without the three-record ordinal
bijection is invalid.

Each receipt records at least its ID/ordinal, nonce, script SHA-256,
immutable-evidence and pre-proof digests, direct-stash OID/evidence digest,
affected snapshot-manifest SHA-256, affected saved/live counts and bytes,
pre-clean ignored/preview counts, `preclean_ignored_retained_verified=true`,
clean exit code `0`, zero post-clean tracked/untracked/ignored/preview counts,
and pre/post UTC timestamps. It is valid only when derived from the exact
durable `CLEAN_EXIT_VERIFIED` record and all shared pre-proof, output, and
identity fields remain bound to that record.

- [ ] **Step 5: Fail closed across crashes and require explicit recovery**

- `READY` plus the full original ignored set may begin a fresh pre-proof.
- After exact temp-candidate recovery, `PREPROOF_VERIFIED` plus the full
  original ignored set and no attempt candidate means no cleanup outcome became
  durable; only `recover-task5` may repeat proof and deletion.
- `PREPROOF_VERIFIED` plus zero ignored/preview without a durable matching
  attempt marker is ambiguous and becomes exact `BLOCKED`; absence never proves
  that this operator completed cleanup.
- `CLEAN_ATTEMPT_ARMED` permits a native call only to the uninterrupted
  invocation that published and reloaded it. Any recovery invocation has no
  cleanup edge: it promotes an exact outcome candidate if present, or performs
  read-only observation and fails closed as `UNKNOWN_NATIVE_OUTCOME_AFTER_ARM`.
- `CLEAN_ATTEMPT_RECORDED` has no cleanup edge. Recovery may repeat only bounded
  read-only post observation. A successful observation publishes
  `CLEAN_EXIT_VERIFIED` only for the exact successful native/live result;
  otherwise it publishes exact `BLOCKED`. Repeated observation failure leaves
  the attempt marker unchanged.
- `CLEAN_EXIT_VERIFIED` may run only `AfterClean` and publish the bound receipt.
  Recovery from this state must never issue a second cleanup call.
- A partial ignored set, mixed preview, nonzero tracked/untracked state, changed
  immutable core, snapshot, stash, registry, or failed/noisy/timed-out cleanup
  attempt is durably `BLOCKED`. Preserve all evidence and require independent
  review; never append a receipt or retry automatically.
- Existing valid receipts are re-proved and skipped, never duplicated. A
  completed run is read-only and refuses a second execution.
- A temp candidate is never overwritten. Recovery validates current and
  candidate bytes, their one-step state relation, and live state before either
  promotion or rejection. It never infers success merely from an empty tree and
  never retries automatically.

Runtime candidate recovery accepts only exact one-step relations
`PREPROOF_VERIFIED -> CLEAN_ATTEMPT_ARMED`,
`CLEAN_ATTEMPT_ARMED -> CLEAN_ATTEMPT_RECORDED | BLOCKED`, and
`CLEAN_ATTEMPT_RECORDED -> CLEAN_EXIT_VERIFIED | BLOCKED`, followed by the
existing clean-exit-to-receipt relation. Crash fixtures cover arm publication,
after spawn, during child execution, after child return, outcome-candidate
fsync/replace/reload, observation, post-proof, and receipt boundaries. Fixtures
after spawn must finish recovery with `CLEAN_CALLS=1`; a crash before spawn may
remain at zero calls but never permits recovery to launch one.

- [ ] **Step 6: Enforce the exact mutation and future-authority surface**

Before pinning, a reviewed builder may create only the fixed gate source. `pin`
may create the fixed lock and atomically add `proof_gate` to the manifest.
`execute-task5`/`recover-task5` may atomically update only `cleanup_run`, the
three receipts, the final state, and exactly the three authorized ignored trees.

Only after `cleanup_run.state=COMPLETE` and `CLEANED_VERIFIED`, the manifest may
gain up to two ordered `cleanup_run.future_authorities`: `stale-removal`, then
`temporary-removal`. Each exact scoped record pins the fixed operator path,
byte count and SHA-256; gate SHA-256; reconstructed predecessor-manifest
SHA-256; receipt-schema SHA-256; fixed target order; authorization time;
`prior_registry_digest`; and `registry_baseline_digest`. The gate must rehash,
parse, and standard-library-audit the pinned operator on every applicable prove.

| Authority | Fixed operator path | Receipt-schema SHA-256 |
| --- | --- | --- |
| `stale-removal` | snapshot root `stale-removal-operator.py` | `ac0cf646977e9f664aec9eeea2f6f06257b2b4af7e82c7028856c3de16c7b155` |
| `temporary-removal` | snapshot root `temporary-removal-operator.py` | `5af25cadbc6131c6c9b48c0e20cb07d756ed503b2cf2ae358080efded1a877af` |

Reconstruct the stale-authority predecessor by removing the complete authority
list and both future receipt collections. Reconstruct the temporary-authority
predecessor by retaining the exact stale authority and stale receipts while
removing only the temporary authority and receipts. Canonically serialize each
result and require its pinned predecessor SHA-256. A missing authority,
shape-only record, source-only operator, extra property, mismatched
source/schema/gate hash, or unreconstructable predecessor blocks the proof mode.

The stale authority starts from the pinned `CLEANED_VERIFIED` exact `5 / 4`
registry baseline and uses the exact 64-zero `prior_registry_digest` sentinel.
The temporary authority may appear only after all stale receipts; its
`prior_registry_digest` must equal the final stale `registry_after_digest`,
while its `registry_baseline_digest` pins the independently reviewed post-Task-7
live registry.

The exact stale and temporary receipt schemas bind nonce, operator/gate and
immutable hashes, target identity and ordinal order, pre-removal proof, native
result, and observed time. The authority baseline is the chain's `before`; each
receipt binds the current live registry as `registry_before_digest` and the
verified result as `registry_after_digest`. The first current digest must equal
the authority baseline, and every later current digest must equal the prior
receipt's after digest. The temporary chain also proves the stale-to-temporary
bridge.

Before accepting any future receipt, the gate must recompute the exact
pre-removal proof for that target, pinned authority, and registry-before epoch;
`pre_removal_proof_digest` must equal that recomputed digest. Stale
`target_head`/branch/stash/snapshot fields must equal the frozen target identity
derived from the exact registry and Stage A evidence. Temporary `target_head`
must equal the dynamic target branch/ref identity in that exact registry epoch;
`retained_head` must equal the applicable retained `master` or `main` ref used
for the reachability proof. Hex shape alone never authenticates either HEAD.

These optional authorities enable only the pinned gate's read-only
`BeforeStaleRemoval` and `BeforeTemporaryRemoval` proofs. They do not authorize
worktree or branch mutation: Tasks 6 and 8 still require their own reviewed
operator, nonce, lock/crash journal, and execution handoff.

Forbidden mutations include tracked/untracked deletion; stash creation,
apply/pop/drop, or ref rewrite; snapshot or snapshot-manifest changes; repo
config, index, HEAD, branch, worktree registration, active worktree, or
`.content-video-ad` changes; force operations; recursive OS deletion;
`shell=True`; dynamic command strings; cleanup outside the three frozen roots;
and path inventory output.

- [ ] **Step 7: Pass the 13-part test matrix before pinning**

1. **Strict JSON:** reject duplicate keys/constants, bool/float integers,
   missing/extra fields, duplicate IDs/paths, and malformed hashes.
2. **Exact pin:** reject wrong predecessor bytes/hash, already-pinned state,
   immutable drift, wrong source path/hash, reparse roots/files, and temp
   collision without mutation. Cover lock-only recovery, candidate
   fsync/pre-replace crash, post-replace recovery, wrong candidate, the exact
   predecessor-to-`proof_gate` `PIN` relation, and zero cleanup calls.
3. **Snapshot authority:** reject either raw manifest pin mismatch, bad state or
   audit subset, missing/extra payload, size/hash drift, reparse/special files,
   and path escape. Exercise all `126` actual uppercase record hashes through
   in-memory canonicalization and payload comparison; reject non-hex and every
   wrong or mixed-length case without changing persisted bytes.
4. **Stash authority:** reject OID/predecessor/order/subject/message/path-set
   drift, missing commit/LFS object, bad LFS pointer, raw blob mismatch, and
   CRLF/LF recovery mismatch.
5. **Classification:** pass an exact `87,688`-record fixture; reject a
   missing/extra leaf, unknown/high-risk class, overlapping or mixed preview,
   unparseable preview, and new ignored leaf.
6. **Git state:** reject branch/HEAD/index/tracked/untracked drift, unsafe root,
   registration mismatch, and nonzero Git exit.
7. **Registry:** pass exact `5 / 4`; reject missing/replaced/extra/detached
   entries, a fifth client entry, stale HEAD drift, and dynamic ref mismatch;
   pass a legitimate docs advance whose registry HEAD equals its branch ref.
8. **Mode scoping:** prove targeted Task 5 hashes, empty `AfterClean`, full
   per-target stale-removal hashes, dynamic docs HEADs, and reachability.
9. **Adjacency/static:** prove one implementation, fixed argument arrays,
   durable arm before child launch, immediate outcome capture, durable outcome
   before post observation, no shell wrapper, and no mutation reachable from
   `prove`.
10. **Crash injection:** cover both sides of PREPROOF, cleanup,
    `CLEAN_ATTEMPT_ARMED`, spawn, child execution/return,
    `CLEAN_ATTEMPT_RECORDED`, observation, `CLEAN_EXIT_VERIFIED`, durable
    `BLOCKED`, candidate replace, receipts one/two, and final transition. Prove
    every exact one-step relation, repeated observation failure, zero recovery
    cleanup calls from ARMED, and total `CLEAN_CALLS=1` after every spawn.
11. **Isolated destructive fixture:** under a verified OS temp directory only,
    remove classified ignored generated/snapshotted-retained fixtures while
    preserving tracked, untracked, and out-of-root files.
12. **Performance/heartbeat:** validate a synthetic `87,688`-record manifest,
    bounded-memory hashes and inventories, aggregate progress, and no-progress
    stop. Actual-child tests must cover continuing progress beyond the old
    total cutoff, true stall, concurrent stderr pressure, and stdout/stderr
    output limits for the general proof-only Git adapter.
13. **Atomicity and future authority:** validate-before-replace, fsync/close,
    `os.replace`, exact reload, collision recovery, predecessor reconstruction,
    operator AST/stdlib pins, receipt-schema hashes, registry baselines, receipt
    chains, and stale-to-temporary bridging. Mutate every semantic field in both
    future receipt chains—including proof digest, target/retained HEADs,
    authority hashes, target/order, and registry links—and require rejection.

- [ ] **Step 8: Separate build, review, pin, and execution authority**

This amendment supersedes the earlier frozen build verdict. The `141,919`-byte
gate at SHA-256
`d398baa455a2fced7276912266c6785f74795138832755c7a75090af23ba960e`
and its `61,591`-byte test packet at SHA-256
`43f3287c72f960b79648ba9af1a733087d2531fdc364e3567e4d668faaa2f4a6`
remain historical `SOURCE_PASS` evidence for the previous contract, but are now
`NOT_CONFORMING / DO_NOT_PIN`.

The later frozen rebuild is also forbidden: source `161,158` bytes /
`6d933d585ecd38c11428a81a7c81f99db074691afb0f26644d1c90adb423f855`
and tests `97,107` bytes /
`a7f8ce4e79d5092230816392a3cb20ebf5ff55c7840367a25a818b9979031f70`
are `SOURCE_FAIL / DO_NOT_PIN`. The authoritative frozen review is SHA-256
`116424abd5401a923466c9629a4ed231b6cf8239159659d3ceff1865d6691a3b`.
Passing isolated tests do not override that verdict. Rebuild source and tests
against this stricter pre-launch arm, outcome, pin-recovery, live-format,
proof-binding, and streaming contract, then repeat fresh tests and independent
frozen review.

The handoff is fail-closed:

1. a builder creates only the fixed source and runs all isolated tests;
2. a fresh static reviewer approves the exact source bytes/SHA-256, stdlib-only
   imports, mutation reachability, and all 13 test results, and proves the live
   manifest, snapshots, stashes, registries, and worktrees did not change;
3. a separate pin operator receives that exact hash and invokes `pin` once;
4. an independent post-pin review proves the exact `proof_gate`, lock, immutable
   digest, unchanged evidence, and no `cleanup_run` or receipts;
5. only then may a separate Task 5 operator receive a new nonce plus the same
   approved hash and invoke `execute-task5` once;
6. any interrupted run goes to a separate `recover-task5` review/handoff; and
7. a final independent review must prove three exact receipts,
   `cleanup_run.state=COMPLETE`, `CLEANED_VERIFIED`, preserved snapshots/stashes,
   exact registries, and no unauthorized mutation.

Pinning is not cleanup authorization. Task 5 completion is not Task 6 or Task 8
authorization.

### Task 6: Remove Stale Worktrees And Merged Branches

**Status: `BLOCKED_AS_WRITTEN`.** The removed inline PowerShell proof/removal
and branch-deletion blocks are not executable authority.

**Files:**

- Git worktree/branch metadata only, after a separate reviewed operator exists
- Append-only stale-removal receipts in the local evidence manifest

**Interfaces:**

- Consumes: `CLEANED_VERIFIED`, three exact Task 5 receipts, the exact pinned
  stale `future_authorities` record, the Python `BeforeStaleRemoval` mode,
  readable stashes, full target snapshots, and exact ordinal registry profiles
- Produces: three non-forced worktree-removal receipts, then three normal
  merged-branch deletion receipts

- [ ] **Step 1: Build and review a separate stale-removal operator**

Task 5 deliberately provides proof but no removal authority. Before Task 6,
write a separate tracked plan amendment and build one single-purpose operator.
A fresh reviewer must approve its exact bytes/hash, fixtures, lock/nonce and
crash journal, mutation surface, and deterministic registry transitions.

The fixed worktree order and IDs remain:

1. `premium-bank-app-portal`
2. `release-hardening-platform`
3. `release-hardening-client`

For each ID, the operator must durably record pre-removal proof, call the pinned
Python gate's `prove` command in `BeforeStaleRemoval` mode, and—without yielding
control—perform exactly one fixed-argument, non-forced Git worktree removal. It
then proves the expected registry absence and atomically appends an ordinal
removal receipt. The proof must cover exact cleanup receipts, target
branch/HEAD, reachability, empty tracked/untracked/ignored/preview state, the
exact direct stash, the full target snapshot hash, and a registry profile where
earlier fixed-order targets are absent while the current and later targets
remain exactly once. Post-removal absence belongs only to the operator's
verified receipt.

No inline removal command, `--force`, shell wrapper, automatic retry, or
inference from an absent directory is allowed. A partial registry transition,
candidate collision, changed proof evidence, or interrupted removal blocks for
explicit independently reviewed recovery.

- [ ] **Step 2: Delete only proved merged branches through that operator**

Only after all three worktree-removal receipts exist may the reviewed operator
consider the corresponding local branches. It must re-prove each exact branch
tip is reachable from the retained branch, use normal non-forced branch deletion
only, verify absence, and append a branch-removal receipt. Named stashes and
both snapshots remain readable and unchanged.

Task 6 stays blocked until its operator and exact execution handoff receive an
independent review. Nothing pinned or executed in Task 5 authorizes this task.

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

**Status: `BLOCKED_AS_WRITTEN`.** The removed inline PowerShell proof,
worktree-removal, reachability, and branch-deletion block is not executable
authority.

**Files:**

- Git worktree/branch metadata only, after promotion and a separately reviewed
  removal operator exist
- Append-only temporary-removal receipts in the local evidence manifest

**Interfaces:**

- Consumes: completed Task 7 promotion, `CLEANED_VERIFIED`, exact Task 6
  removal receipts/profile, the exact pinned temporary `future_authorities`
  record, the Python `BeforeTemporaryRemoval` mode, clean docs worktrees,
  dynamic branch refs, and retained-line reachability
- Produces: the requested steady state with recoverable evidence

- [ ] **Step 1: Build and review a separate temporary-removal operator**

Task 5 supplies the shared read-only proof mode but does not authorize Task 8.
After Task 7 is independently green, write a separate tracked plan amendment
and build one single-purpose operator. A fresh reviewer must approve its exact
bytes/hash, fixed IDs/order, tests, lock/nonce and crash journal, expected
registry profiles, branch-reachability policy, receipt schema, and mutation
surface before any execution handoff.

The operator must handle these proof identities in order:

1. `agent-context-refactor-platform`
2. `agent-context-refactor-client`

For each identity, it must durably record pre-removal proof, call the pinned
Python gate's `prove` command in `BeforeTemporaryRemoval` mode and—without
yielding control—perform exactly one fixed-argument, non-forced Git worktree
removal. It then proves the exact registry absence and atomically appends an
ordinal temporary-worktree receipt.

The adjacent proof must require a clean target, dynamic
`registry HEAD == current branch ref`, exact earlier stale-removal receipts and
registry profile, reachability from the retained platform `master` or client
`main`, and retained recovery evidence. It must resolve docs HEADs at proof time;
no current docs commit SHA may be frozen in the operator.

- [ ] **Step 2: Remove only independently proved reachable branches**

After the matching worktree receipt, the operator may use only normal
non-forced branch deletion for `codex/agent-context-refactor` and
`codex/agent-context-refactor-client`. The platform
`codex/product-audit-closure` branch requires its own immediate ancestor proof
against `master`. Every successful absence check gets a branch-removal receipt.

No raw removal/deletion command, `--force`, shell wrapper, automatic retry, or
inference from absence is permitted. A partial transition, candidate collision,
changed promotion/ref, failed proof, or interrupted removal blocks for explicit
independently reviewed recovery.

- [ ] **Step 3: Verify the steady state and preserve recovery evidence**

The final independent review must prove:

- platform root is on `master` and client root is on `main`;
- both active market-ready worktrees remain registered until their own tasks
  finish;
- stale and docs worktrees/branches are absent only where exact receipts exist;
- snapshots, named stashes, proof-gate bytes, and all recovery receipts remain
  readable and unchanged; and
- no additional local branch was deleted.

Task 8 remains blocked until its separate operator, static review, and execution
handoff are complete.

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
if ((Get-Item -Force -LiteralPath $source).Attributes -band [IO.FileAttributes]::ReparsePoint) {
    throw "Content-video source is a reparse point"
}
if (Test-Path -LiteralPath $destination) {
    throw "Content-video backup destination already exists"
}
$destinationParent = Split-Path -Parent $destination
if (-not (Test-Path -LiteralPath $destinationParent)) {
    New-Item -ItemType Directory -Path $destinationParent | Out-Null
}
if ((Get-Item -Force -LiteralPath $destinationParent).Attributes -band [IO.FileAttributes]::ReparsePoint) {
    throw "Content-video backup parent is a reparse point"
}
[IO.File]::Copy($source, $destination, $false)
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
