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
- Create locally: `C:/Users/kiwun/Documents/ai/worktree-snapshots/2026-07-10-docs-renewal/cleanup-proof-gate.ps1`
- Delete locally: only paths classified `generated_disposable`
- Delete locally after snapshot verification: retained ignored roots already
  copied in Task 3

**Interfaces:**
- Consumes: exhaustive classification, snapshot, and readable stash
- Produces: clean removable stale worktree

- [ ] **Step 1: Create the single read-only destruction proof gate**

Save the following exact source as the local ignored file
`cleanup-proof-gate.ps1` named above. This is the only proof implementation
used before clean and worktree removal. It reads and hashes evidence but never
changes a repository, worktree, stash, snapshot, or manifest.

The gate never compares all retained live files after stash. It compares live
path/length/SHA-256 only for `ignored_retained`, because those bytes are not in
the stash and must still exist unchanged before cleanup. `tracked_dirty` and
`untracked` require the snapshot hash plus exact direct-stash OID, subject, and
path membership. `tracked_clean` requires the frozen branch/HEAD and snapshot.
`tracked_deleted` requires an absent pre-stash source record plus exact deletion
path membership in the direct stash. The post-clean removal proof consumes the
receipt from that immediately preceding live ignored-retained proof.

```powershell
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$ManifestPath,
    [Parameter(Mandatory)][string]$EntryId,
    [Parameter(Mandatory)][ValidateSet('BeforeClean','AfterClean','BeforeStaleRemoval','BeforeTemporaryRemoval')][string]$Mode
)
$ErrorActionPreference = 'Stop'
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
function Invoke-GitLines {
    param([string]$Repo, [string[]]$GitArgs)
    $lines = @(& git -c core.quotepath=false -C $Repo @GitArgs)
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) { throw "git failed in ${Repo} ($exitCode): $($GitArgs -join ' ')" }
    return @($lines)
}
function Invoke-GitPathSet {
    param([string]$Repo, [string[]]$GitArgs, [string]$Label)
    $lines = @(Invoke-GitLines $Repo $GitArgs)
    $set = New-OrdinalSet @($lines | Where-Object { $_ -ne '' } | ForEach-Object { $_.Replace('\', '/') }) $Label
    return @($set)
}
function Assert-PlainTree {
    param([string]$Root, [string]$Label)
    $item = Get-Item -Force -LiteralPath $Root
    if (-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "$Label root is not a plain directory" }
    $reparse = @(Get-ChildItem -Force -Recurse -LiteralPath $Root | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
    if ($reparse.Count -ne 0) { throw "$Label contains a reparse point" }
}
function Get-RecordSet {
    param([string]$Root, [string]$ExcludedFullName)
    $records = [Collections.Generic.List[object]]::new()
    foreach ($file in @(Get-ChildItem -Force -File -Recurse -LiteralPath $Root)) {
        if ($ExcludedFullName -and [string]::Equals($file.FullName, $ExcludedFullName, $comparison)) { continue }
        $records.Add([pscustomobject]@{
            relative_path = [IO.Path]::GetRelativePath($Root, $file.FullName).Replace('\', '/')
            byte_length = $file.Length
            sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
        })
    }
    return @($records)
}
function Get-LiveIgnoredRetainedRecords {
    param([string]$Worktree, [object[]]$SavedRecords)
    $root = [IO.Path]::GetFullPath($Worktree)
    $records = foreach ($saved in @($SavedRecords|Where-Object original_git_state -CEQ 'ignored_retained')) {
        $source=[IO.Path]::GetFullPath((Join-Path $root $saved.relative_path))
        if(-not $source.StartsWith($root+[IO.Path]::DirectorySeparatorChar,$comparison)-or-not(Test-Path -LiteralPath $source -PathType Leaf)){throw "Ignored retained source escaped or is missing: $($saved.relative_path)"}
        $file=Get-Item -Force -LiteralPath $source
        if($file.Attributes -band [IO.FileAttributes]::ReparsePoint){throw "Ignored retained source is a reparse point: $($saved.relative_path)"}
        [pscustomobject]@{relative_path=$saved.relative_path;byte_length=$file.Length;sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash;original_git_state='ignored_retained';snapshot_present=$true}
    }
    return @($records)
}
function Assert-RecordMatch {
    param([object[]]$Expected, [object[]]$Actual, [string]$Label)
    $expectedMap = New-OrdinalRecordMap $Expected relative_path "$Label expected"
    $actualMap = New-OrdinalRecordMap $Actual relative_path "$Label actual"
    Assert-OrdinalBijection @($expectedMap.Keys) @($actualMap.Keys) "$Label paths"
    foreach ($path in $expectedMap.Keys) {
        if ($expectedMap[$path].byte_length -ne $actualMap[$path].byte_length -or [string]$expectedMap[$path].sha256 -cne [string]$actualMap[$path].sha256) { throw "$Label length/hash mismatch: $path" }
        if($expectedMap[$path].PSObject.Properties.Name -contains 'original_git_state' -and $actualMap[$path].PSObject.Properties.Name -contains 'original_git_state' -and $expectedMap[$path].original_git_state -cne $actualMap[$path].original_git_state){throw "$Label Git-state mismatch: $path"}
    }
}
function Get-LivePreviewRecords {
    param([object]$Entry)
    $classMap = New-OrdinalRecordMap @($Entry.ignored_classification) path "$($Entry.id) classifications"
    $covered = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $previewPaths = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $records = [Collections.Generic.List[object]]::new()
    foreach ($line in @(Invoke-GitLines $Entry.worktree @('clean','-ndX'))) {
        if (-not $line.StartsWith('Would remove ', [StringComparison]::Ordinal)) { throw "$($Entry.id) unparseable clean preview: $line" }
        $candidate = $line.Substring(13).Replace('\', '/').TrimEnd('/')
        if ($candidate.Length -eq 0 -or $candidate.Contains('"') -or $candidate.Contains("`r") -or $candidate.Contains("`n") -or -not $previewPaths.Add($candidate)) { throw "$($Entry.id) unsafe/duplicate preview path: $candidate" }
        $matches = @($Entry.ignored_paths | Where-Object { $_ -ceq $candidate -or $_.StartsWith($candidate + '/', [StringComparison]::Ordinal) })
        if ($matches.Count -eq 0) { throw "$($Entry.id) preview path has no authorized leaf: $candidate" }
        $classes = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        foreach ($path in $matches) {
            if (-not $covered.Add($path)) { throw "$($Entry.id) overlapping preview coverage: $path" }
            [void]$classes.Add([string]$classMap[$path].classification)
        }
        if ($classes.Count -ne 1) { throw "$($Entry.id) preview mixes generated and retained data: $candidate" }
        $target = [IO.Path]::GetFullPath((Join-Path $Entry.worktree $candidate))
        if (-not $target.StartsWith([IO.Path]::GetFullPath($Entry.worktree) + [IO.Path]::DirectorySeparatorChar, $comparison)) { throw "$($Entry.id) preview escaped worktree" }
        if (Test-Path -LiteralPath $target) {
            $targetItem = Get-Item -Force -LiteralPath $target
            if ($targetItem.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "$($Entry.id) preview target is a reparse point: $candidate" }
            if ($targetItem.PSIsContainer) { Assert-PlainTree $target "$($Entry.id) preview $candidate" }
        }
        $records.Add([pscustomobject]@{ path=$candidate; classification=@($classes)[0] })
    }
    Assert-OrdinalBijection @($Entry.ignored_paths) @($covered) "$($Entry.id) preview coverage"
    return @($records)
}
function Assert-PreviewRecordMatch {
    param([object[]]$Expected, [object[]]$Actual, [string]$Label)
    $expectedMap = New-OrdinalRecordMap $Expected path "$Label expected"
    $actualMap = New-OrdinalRecordMap $Actual path "$Label actual"
    Assert-OrdinalBijection @($expectedMap.Keys) @($actualMap.Keys) "$Label paths"
    foreach ($path in $expectedMap.Keys) {
        if ([string]$expectedMap[$path].classification -cne [string]$actualMap[$path].classification) { throw "$Label classification mismatch: $path" }
    }
}
function Assert-RegisteredWorktree {
    param([object]$Spec)
    $records = [Collections.Generic.List[object]]::new(); $current = $null
    foreach ($line in @(Invoke-GitLines $Spec.repo_root @('worktree','list','--porcelain'))) {
        if ($line.StartsWith('worktree ', [StringComparison]::Ordinal)) {
            if ($null -ne $current) { $records.Add($current) }
            $current = [pscustomobject]@{ path=$line.Substring(9); head=$null; branch=$null }
        } elseif ($null -ne $current -and $line.StartsWith('HEAD ', [StringComparison]::Ordinal)) { $current.head=$line.Substring(5) }
        elseif ($null -ne $current -and $line.StartsWith('branch ', [StringComparison]::Ordinal)) { $current.branch=$line.Substring(7) }
    }
    if ($null -ne $current) { $records.Add($current) }
    $matches = @($records | Where-Object { [string]::Equals([IO.Path]::GetFullPath($_.path), [IO.Path]::GetFullPath($Spec.worktree), $comparison) })
    if ($matches.Count -ne 1 -or $matches[0].head -cne $Spec.head -or $matches[0].branch -cne "refs/heads/$($Spec.branch)") { throw "$($Spec.id) worktree registration mismatch" }
}

$manifestFullPath = [IO.Path]::GetFullPath($ManifestPath)
$backupRoot = Split-Path -Parent $manifestFullPath
$manifest = [IO.File]::ReadAllText($manifestFullPath) | ConvertFrom-Json
$expectedState = if ($Mode -cin @('BeforeClean','AfterClean')) { 'STAGE_A_VERIFIED' } else { 'CLEANED_VERIFIED' }
if ($manifest.schema_version -ne 2 -or $manifest.stage_a_state -cne $expectedState -or @($manifest.audit_drift).Count -ne 0) { throw "Manifest is not in exact $expectedState state" }
if ($manifest.audit_expectations.platform_ops_local.file_count -ne 2 -or $manifest.audit_expectations.platform_ops_local.byte_count -ne 2052 -or
    $manifest.audit_expectations.client_artifacts.file_count -ne 114 -or $manifest.audit_expectations.client_artifacts.byte_count -ne 2016578139) { throw 'Manifest retained audit expectations mismatch' }
if ($manifest.proof_gate.path -cne 'cleanup-proof-gate.ps1') { throw 'Manifest proof-gate path mismatch' }
$selfPath = [IO.Path]::GetFullPath($PSCommandPath)
if (-not [string]::Equals($selfPath, [IO.Path]::GetFullPath((Join-Path $backupRoot $manifest.proof_gate.path)), $comparison)) { throw 'Running an unregistered proof gate' }
if ((Get-Item -Force -LiteralPath $selfPath).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Proof gate is a reparse point' }
if ((Get-FileHash -LiteralPath $selfPath -Algorithm SHA256).Hash -cne $manifest.proof_gate.sha256) { throw 'Proof-gate hash mismatch' }

$staleSpecs = @(
    [pscustomobject]@{ id='premium-bank-app-portal'; worktree='C:\Users\kiwun\.config\superpowers\worktrees\VPN\premium-bank-app-portal'; repo_root='C:\Users\kiwun\Documents\ai\VPN'; branch='codex/premium-bank-app-portal'; tracked=30; untracked=2; ignored=45423; retained_branch='master' },
    [pscustomobject]@{ id='release-hardening-platform'; worktree='C:\Users\kiwun\.config\superpowers\worktrees\VPN\release-hardening-platform'; repo_root='C:\Users\kiwun\Documents\ai\VPN'; branch='codex/release-hardening-platform'; tracked=91; untracked=117; ignored=42122; retained_branch='master' },
    [pscustomobject]@{ id='release-hardening-client'; worktree='C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\release-hardening-client'; repo_root='C:\Users\kiwun\Documents\ai\POKROV-app'; branch='codex/release-hardening-client'; tracked=26; untracked=27; ignored=143; retained_branch='main' }
)
$temporarySpecs = @(
    [pscustomobject]@{ id='agent-context-refactor-platform'; worktree='C:\Users\kiwun\Documents\ai\VPN\.worktrees\agent-context-refactor'; repo_root='C:\Users\kiwun\Documents\ai\VPN'; branch='codex/agent-context-refactor'; retained_branch='master'; head=$null },
    [pscustomobject]@{ id='agent-context-refactor-client'; worktree='C:\Users\kiwun\Documents\ai\POKROV-app\.worktrees\agent-context-refactor-client'; repo_root='C:\Users\kiwun\Documents\ai\POKROV-app'; branch='codex/agent-context-refactor-client'; retained_branch='main'; head=$null }
)
$staleMap = New-OrdinalRecordMap $staleSpecs id 'expected stale worktrees'
$entryMap = New-OrdinalRecordMap @($manifest.worktrees) id 'manifest worktrees'
Assert-OrdinalBijection @($staleMap.Keys) @($entryMap.Keys) 'manifest worktree IDs'
if ($expectedState -ceq 'CLEANED_VERIFIED') {
    Assert-OrdinalBijection @($staleMap.Keys) @($manifest.cleanup_receipts | ForEach-Object id) 'cleanup receipt IDs'
    foreach($receipt in @($manifest.cleanup_receipts)){if($receipt.ignored_count -ne 0 -or $receipt.preview_count -ne 0 -or $receipt.preclean_ignored_retained_verified -ne $true){throw "$($receipt.id) cleanup receipt is not complete recovery proof"}}
}
foreach ($id in $staleMap.Keys) {
    $spec = $staleMap[$id]; $entry = $entryMap[$id]
    if (-not [string]::Equals([IO.Path]::GetFullPath($entry.worktree), [IO.Path]::GetFullPath($spec.worktree), $comparison) -or
        -not [string]::Equals([IO.Path]::GetFullPath($entry.repo_root), [IO.Path]::GetFullPath($spec.repo_root), $comparison) -or
        $entry.branch -cne $spec.branch -or $entry.tracked_count -ne $spec.tracked -or $entry.untracked_count -ne $spec.untracked -or $entry.ignored_count -ne $spec.ignored -or
        $entry.tracked_count -ne @($entry.tracked_paths).Count -or $entry.head_tree_count -ne @($entry.head_tree_paths).Count -or $entry.index_file_count -ne @($entry.index_file_paths).Count -or $entry.untracked_count -ne @($entry.untracked_paths).Count -or $entry.ignored_count -ne @($entry.ignored_paths).Count -or
        @($entry.ignored_classification).Count -ne $entry.ignored_count -or @($entry.high_risk_paths).Count -ne 0 -or @($entry.unknown_paths).Count -ne 0) { throw "$id manifest shape mismatch" }
    Assert-OrdinalBijection @($entry.ignored_paths) @($entry.ignored_classification | ForEach-Object path) "$id classification"
    foreach ($classification in @($entry.ignored_classification | ForEach-Object classification)) {
        if ($classification -cnotin @('generated_disposable','retained_snapshotted')) { throw "$id unsafe classification" }
    }
    [void](New-OrdinalRecordMap @($entry.clean_preview_records) path "$id frozen preview")
}
Assert-OrdinalBijection @('release-hardening-platform','release-hardening-client') @($manifest.retained_snapshots | ForEach-Object id) 'snapshot IDs'
Assert-OrdinalBijection @($staleMap.Keys) @($manifest.stashes | ForEach-Object id) 'stash IDs'
$stashMap = New-OrdinalRecordMap @($manifest.stashes) id 'stash records'
$stashOidSets = [Collections.Generic.Dictionary[string,Collections.Generic.HashSet[string]]]::new([StringComparer]::Ordinal)
foreach ($repoRoot in @('C:\Users\kiwun\Documents\ai\VPN','C:\Users\kiwun\Documents\ai\POKROV-app')) {
    $oidSet = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($oid in @(Invoke-GitLines $repoRoot @('stash','list','--format=%H'))) { [void]$oidSet.Add($oid) }
    $stashOidSets.Add($repoRoot, $oidSet)
}
$verifiedStashPathsById=[Collections.Generic.Dictionary[string,Collections.Generic.HashSet[string]]]::new([StringComparer]::Ordinal)
foreach ($id in $staleMap.Keys) {
    $spec=$staleMap[$id]; $entry=$entryMap[$id]; $stash=$stashMap[$id]
    [void](Invoke-GitLines $spec.repo_root @('cat-file','-e',"$($stash.oid)^{commit}"))
    if (-not $stashOidSets[$spec.repo_root].Contains([string]$stash.oid)) { throw "$id direct stash OID is no longer in refs/stash history" }
    $subject=@(Invoke-GitLines $spec.repo_root @('show','-s','--format=%s',[string]$stash.oid))
    if ($subject.Count -ne 1 -or $subject[0] -cne $stash.subject -or $stash.subject -cne "On $($entry.branch): $($stash.message)") { throw "$id stash subject mismatch" }
    $stashPaths=@(Invoke-GitPathSet $spec.repo_root @('stash','show','--include-untracked','--name-only','--no-renames',[string]$stash.oid) "$id stash paths")
    $expectedStashPaths = New-OrdinalSet @(@($entry.tracked_paths) + @($entry.untracked_paths)) "$id expected stash paths"
    Assert-OrdinalBijection @($expectedStashPaths) $stashPaths "$id stash contents"
    if ($stash.path_count -ne $expectedStashPaths.Count) { throw "$id stash count mismatch" }
    $verifiedStashPathsById.Add($id,$expectedStashPaths)
}
foreach ($summary in @($manifest.retained_snapshots)) {
    $snapshotManifestPath=[IO.Path]::GetFullPath((Join-Path $backupRoot $summary.manifest))
    if (-not $snapshotManifestPath.StartsWith($backupRoot + [IO.Path]::DirectorySeparatorChar,$comparison)) { throw "$($summary.id) snapshot manifest escaped backup root" }
    $snapshotRoot=Split-Path -Parent $snapshotManifestPath
    Assert-PlainTree $snapshotRoot "$($summary.id) snapshot"
    $saved=[IO.File]::ReadAllText($snapshotManifestPath) | ConvertFrom-Json
    $savedBytes=(@($saved.files)|Measure-Object -Property byte_length -Sum).Sum
    if ($saved.id -cne $summary.id -or $saved.file_count -ne @($saved.files).Count -or $saved.tracked_deletion_count -ne @($saved.tracked_deletions).Count -or $saved.record_count -ne ($saved.file_count+$saved.tracked_deletion_count) -or $saved.file_count -ne $summary.file_count -or $saved.tracked_deletion_count -ne $summary.tracked_deletion_count -or $saved.record_count -ne $summary.record_count -or $saved.byte_count -ne $summary.byte_count -or $saved.byte_count -ne $savedBytes) { throw "$($summary.id) snapshot manifest shape mismatch" }
    $fileMap=New-OrdinalRecordMap @($saved.files) relative_path "$($summary.id) saved records";$deletionMap=New-OrdinalRecordMap @($saved.tracked_deletions) relative_path "$($summary.id) tracked deletions"
    $statePaths=@($fileMap.Keys)+@($deletionMap.Keys);[void](New-OrdinalSet $statePaths "$($summary.id) retained state mapping")
    $sourceMatches=@($staleMap.Values|Where-Object{[string]::Equals([IO.Path]::GetFullPath($_.worktree),[IO.Path]::GetFullPath($saved.source_worktree),$comparison)})
    if($sourceMatches.Count -ne 1){throw "$($summary.id) source worktree mapping mismatch"}
    $sourceSpec=$sourceMatches[0];$sourceEntry=$entryMap[$sourceSpec.id];$stashPathsForSource=$verifiedStashPathsById[$sourceSpec.id]
    $dirtySet=New-OrdinalSet @($sourceEntry.tracked_paths) "$($summary.id) frozen dirty paths";$headSet=New-OrdinalSet @($sourceEntry.head_tree_paths) "$($summary.id) frozen HEAD tree";$indexSet=New-OrdinalSet @($sourceEntry.index_file_paths) "$($summary.id) frozen index";$untrackedSet=New-OrdinalSet @($sourceEntry.untracked_paths) "$($summary.id) frozen untracked paths";$ignoredSet=New-OrdinalSet @($sourceEntry.ignored_paths) "$($summary.id) frozen ignored paths";$classMap=New-OrdinalRecordMap @($sourceEntry.ignored_classification) path "$($summary.id) ignored classes"
    foreach($record in @($saved.files)){
        if($record.snapshot_present -ne $true -or -not $record.sha256){throw "$($summary.id) saved record lacks snapshot hash: $($record.relative_path)"}
        switch -CaseSensitive ($record.original_git_state) {
            'ignored_retained' { if(-not $ignoredSet.Contains($record.relative_path)-or$headSet.Contains($record.relative_path)-or$indexSet.Contains($record.relative_path)-or$dirtySet.Contains($record.relative_path)-or$untrackedSet.Contains($record.relative_path)-or$classMap[$record.relative_path].classification -cne 'retained_snapshotted'-or$stashPathsForSource.Contains($record.relative_path)-or$record.head_present-ne$false-or$record.index_present-ne$false){throw "$($summary.id) conflicting ignored-retained recovery: $($record.relative_path)"} }
            'tracked_dirty' { if(-not($headSet.Contains($record.relative_path)-or$indexSet.Contains($record.relative_path))-or-not$dirtySet.Contains($record.relative_path)-or$ignoredSet.Contains($record.relative_path)-or$untrackedSet.Contains($record.relative_path)-or-not$stashPathsForSource.Contains($record.relative_path)-or$record.head_present-ne$headSet.Contains($record.relative_path)-or$record.index_present-ne$indexSet.Contains($record.relative_path)){throw "$($summary.id) tracked-dirty recovery lacks exact HEAD/index/stash evidence: $($record.relative_path)"} }
            'untracked' { if(-not $untrackedSet.Contains($record.relative_path)-or$headSet.Contains($record.relative_path)-or$indexSet.Contains($record.relative_path)-or$dirtySet.Contains($record.relative_path)-or$ignoredSet.Contains($record.relative_path)-or-not$stashPathsForSource.Contains($record.relative_path)-or$record.head_present-ne$false-or$record.index_present-ne$false){throw "$($summary.id) untracked recovery lacks exact stash evidence: $($record.relative_path)"} }
            'tracked_clean' { if(-not $headSet.Contains($record.relative_path)-or-not$indexSet.Contains($record.relative_path)-or$dirtySet.Contains($record.relative_path)-or$untrackedSet.Contains($record.relative_path)-or$ignoredSet.Contains($record.relative_path)-or$stashPathsForSource.Contains($record.relative_path)-or$record.head_present-ne$true-or$record.index_present-ne$true){throw "$($summary.id) tracked-clean recovery conflicts with frozen HEAD/index: $($record.relative_path)"} }
            default { throw "$($summary.id) unknown retained Git state: $($record.original_git_state)" }
        }
    }
    foreach($record in @($saved.tracked_deletions)){
        if($record.original_git_state -cne 'tracked_deleted'-or$record.snapshot_present -ne $false-or-not$headSet.Contains($record.relative_path)-or-not$dirtySet.Contains($record.relative_path)-or$untrackedSet.Contains($record.relative_path)-or$ignoredSet.Contains($record.relative_path)-or-not$stashPathsForSource.Contains($record.relative_path)-or$record.head_present-ne$true-or$record.index_present-ne$indexSet.Contains($record.relative_path)){throw "$($summary.id) tracked-deleted recovery lacks exact HEAD-tree/index/stash deletion evidence: $($record.relative_path)"}
    }
    Assert-RecordMatch @($saved.files) @(Get-RecordSet $snapshotRoot $snapshotManifestPath) "$($summary.id) snapshot contents"
    if ($Mode -ceq 'BeforeClean' -and $sourceSpec.id -ceq $EntryId) {
        $ignoredExpected=@($saved.files|Where-Object original_git_state -CEQ 'ignored_retained')
        Assert-RecordMatch $ignoredExpected @(Get-LiveIgnoredRetainedRecords $saved.source_worktree @($saved.files)) "$($summary.id) live ignored_retained only"
    }
    if($Mode -ceq 'BeforeStaleRemoval' -and $sourceSpec.id -ceq $EntryId){
        $ignoredExpected=@($saved.files|Where-Object original_git_state -CEQ 'ignored_retained')
        $liveIgnoredCount=@($ignoredExpected|Where-Object{Test-Path -LiteralPath (Join-Path $saved.source_worktree $_.relative_path) -PathType Leaf}).Count
        if($liveIgnoredCount -eq $ignoredExpected.Count){
            Assert-RecordMatch $ignoredExpected @(Get-LiveIgnoredRetainedRecords $saved.source_worktree @($saved.files)) "$($summary.id) removal live ignored_retained only"
        }elseif($liveIgnoredCount -eq 0){
            $receipt=@($manifest.cleanup_receipts|Where-Object id -CEQ $EntryId)
            if($receipt.Count -ne 1 -or $receipt[0].preclean_ignored_retained_verified -ne $true){throw "$($summary.id) missing pre-clean ignored-retained proof receipt"}
        }else{throw "$($summary.id) partial ignored-retained live tree before removal"}
    }
}

if ($Mode -ceq 'BeforeTemporaryRemoval') {
    $temporaryMap=New-OrdinalRecordMap $temporarySpecs id 'expected temporary worktrees'
    if (-not $temporaryMap.ContainsKey($EntryId)) { throw "Unexpected temporary worktree ID: $EntryId" }
    $spec=$temporaryMap[$EntryId]
    $head=@(Invoke-GitLines $spec.repo_root @('rev-parse','--verify',"$($spec.branch)^{commit}"))
    if ($head.Count -ne 1) { throw "$EntryId branch HEAD is ambiguous" }
    $spec.head=$head[0]
    Assert-RegisteredWorktree $spec
    $currentBranch=@(Invoke-GitLines $spec.worktree @('branch','--show-current'))
    $currentHead=@(Invoke-GitLines $spec.worktree @('rev-parse','HEAD'))
    if($currentBranch.Count -ne 1 -or $currentBranch[0] -cne $spec.branch -or $currentHead.Count -ne 1 -or $currentHead[0] -cne $spec.head){throw "$EntryId current branch/HEAD mismatch"}
    [void](Invoke-GitLines $spec.repo_root @('merge-base','--is-ancestor',$spec.branch,$spec.retained_branch))
    $tracked=@(Invoke-GitPathSet $spec.worktree @('diff','HEAD','--name-only','--no-renames') "$EntryId tracked")
    $untracked=@(Invoke-GitPathSet $spec.worktree @('ls-files','--others','--exclude-standard') "$EntryId untracked")
    $ignored=@(Invoke-GitPathSet $spec.worktree @('ls-files','--others','--ignored','--exclude-standard') "$EntryId ignored")
    $preview=@(Invoke-GitLines $spec.worktree @('clean','-ndX'))
    if ($tracked.Count -ne 0 -or $untracked.Count -ne 0 -or $ignored.Count -ne 0 -or $preview.Count -ne 0) { throw "$EntryId temporary worktree is not fully clean" }
    $rootItem=Get-Item -Force -LiteralPath $spec.worktree
    if (-not $rootItem.PSIsContainer -or ($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "$EntryId temporary worktree root is unsafe" }
    Write-Output "PROOF_OK $Mode $EntryId"
    return
}

if (-not $staleMap.ContainsKey($EntryId)) { throw "Unexpected stale worktree ID: $EntryId" }
$spec=$staleMap[$EntryId]; $entry=$entryMap[$EntryId]; $spec | Add-Member -NotePropertyName head -NotePropertyValue $entry.head
Assert-RegisteredWorktree $spec
$branch=@(Invoke-GitLines $entry.worktree @('branch','--show-current')); $head=@(Invoke-GitLines $entry.worktree @('rev-parse','HEAD'))
if ($branch.Count -ne 1 -or $branch[0] -cne $entry.branch -or $head.Count -ne 1 -or $head[0] -cne $entry.head) { throw "$EntryId branch/HEAD drift" }
$tracked=@(Invoke-GitPathSet $entry.worktree @('diff','HEAD','--name-only','--no-renames') "$EntryId current tracked")
$untracked=@(Invoke-GitPathSet $entry.worktree @('ls-files','--others','--exclude-standard') "$EntryId current untracked")
if ($tracked.Count -ne 0 -or $untracked.Count -ne 0) { throw "$EntryId has tracked/untracked changes" }
$ignored=@(Invoke-GitPathSet $entry.worktree @('ls-files','--others','--ignored','--exclude-standard') "$EntryId current ignored")
if ($Mode -ceq 'BeforeClean') {
    Assert-OrdinalBijection @($entry.ignored_paths) $ignored "$EntryId live ignored"
    Assert-PreviewRecordMatch @($entry.clean_preview_records) @(Get-LivePreviewRecords $entry) "$EntryId live preview"
} else {
    if ($ignored.Count -ne 0 -or @(Invoke-GitLines $entry.worktree @('clean','-ndX')).Count -ne 0) { throw "$EntryId ignored/preview state is not empty after clean" }
}
if ($Mode -ceq 'BeforeStaleRemoval') {
    Assert-OrdinalBijection @($staleMap.Keys) @($manifest.cleanup_receipts | ForEach-Object id) 'cleanup receipt IDs'
    [void](Invoke-GitLines $spec.repo_root @('merge-base','--is-ancestor',$spec.branch,$spec.retained_branch))
}
$rootItem=Get-Item -Force -LiteralPath $entry.worktree
if (-not $rootItem.PSIsContainer -or ($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "$EntryId worktree root is unsafe" }
Write-Output "PROOF_OK $Mode $EntryId"
```

- [ ] **Step 2: Pin the proof gate before any destructive call**

Run after saving the exact script. A changed gate cannot authorize cleanup:

```powershell
$ErrorActionPreference='Stop'
$manifestPath='C:\Users\kiwun\Documents\ai\worktree-snapshots\2026-07-10-docs-renewal\manifest.json'
$proofGatePath='C:\Users\kiwun\Documents\ai\worktree-snapshots\2026-07-10-docs-renewal\cleanup-proof-gate.ps1'
$manifest=[IO.File]::ReadAllText($manifestPath) | ConvertFrom-Json
if ($manifest.stage_a_state -cne 'STAGE_A_VERIFIED' -or @($manifest.audit_drift).Count -ne 0 -or $manifest.PSObject.Properties.Name -contains 'proof_gate') { throw 'Proof gate can only be pinned once from exact STAGE_A_VERIFIED state' }
$proofItem=Get-Item -Force -LiteralPath $proofGatePath
if ($proofItem.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Proof gate is a reparse point' }
$manifest | Add-Member -NotePropertyName proof_gate -NotePropertyValue ([pscustomobject]@{ path='cleanup-proof-gate.ps1'; sha256=(Get-FileHash -LiteralPath $proofGatePath -Algorithm SHA256).Hash })
$temporary="$manifestPath.tmp"
if (Test-Path -LiteralPath $temporary) { throw 'Manifest temp collision' }
[IO.File]::WriteAllText($temporary,($manifest|ConvertTo-Json -Depth 14),[Text.UTF8Encoding]::new($false))
[IO.File]::Move($temporary,$manifestPath,$true)
```

- [ ] **Step 3: Prove, clean, and prove again without separating the calls**

Run this whole block. Do not copy a `git clean -fdX` line without its adjacent
proof calls and immediate exit check:

```powershell
$ErrorActionPreference='Stop'
$manifestPath='C:\Users\kiwun\Documents\ai\worktree-snapshots\2026-07-10-docs-renewal\manifest.json'
$proofGatePath='C:\Users\kiwun\Documents\ai\worktree-snapshots\2026-07-10-docs-renewal\cleanup-proof-gate.ps1'
$ids=@('premium-bank-app-portal','release-hardening-platform','release-hardening-client')
foreach($id in $ids){
    $manifest=[IO.File]::ReadAllText($manifestPath)|ConvertFrom-Json
    $entry=@($manifest.worktrees|Where-Object id -CEQ $id)
    if($entry.Count -ne 1){throw "$id manifest entry mismatch"}
    & $proofGatePath -ManifestPath $manifestPath -EntryId $id -Mode BeforeClean
    if(-not $?){throw "$id pre-clean proof failed"}
    & git -C $entry[0].worktree clean -fdX
    $cleanExit=$LASTEXITCODE
    if($cleanExit -ne 0){throw "$id git clean failed ($cleanExit)"}
    & $proofGatePath -ManifestPath $manifestPath -EntryId $id -Mode AfterClean
    if(-not $?){throw "$id post-clean proof failed"}

    $manifest=[IO.File]::ReadAllText($manifestPath)|ConvertFrom-Json
    $receiptIds=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($receipt in @($manifest.cleanup_receipts)){if(-not $receiptIds.Add([string]$receipt.id)){throw 'Duplicate cleanup receipt ID'}}
    if(-not $receiptIds.Add($id)){throw "$id already has a cleanup receipt"}
    $manifest.cleanup_receipts=@($manifest.cleanup_receipts)+@([pscustomobject]@{id=$id;verified_utc=[DateTime]::UtcNow.ToString('o');ignored_count=0;preview_count=0;preclean_ignored_retained_verified=$true})
    $temporary="$manifestPath.tmp"; if(Test-Path -LiteralPath $temporary){throw 'Manifest temp collision'}
    [IO.File]::WriteAllText($temporary,($manifest|ConvertTo-Json -Depth 14),[Text.UTF8Encoding]::new($false));[IO.File]::Move($temporary,$manifestPath,$true)
}
$manifest=[IO.File]::ReadAllText($manifestPath)|ConvertFrom-Json
$receiptSet=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach($receipt in @($manifest.cleanup_receipts)){if(-not $receiptSet.Add([string]$receipt.id)){throw 'Duplicate cleanup receipt ID'}}
$expected=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal);foreach($id in $ids){[void]$expected.Add($id)}
if($manifest.stage_a_state -cne 'STAGE_A_VERIFIED' -or -not $expected.SetEquals($receiptSet)){throw 'All three post-clean proofs are required'}
$manifest.stage_a_state='CLEANED_VERIFIED'
$temporary="$manifestPath.tmp";if(Test-Path -LiteralPath $temporary){throw 'Manifest temp collision'}
[IO.File]::WriteAllText($temporary,($manifest|ConvertTo-Json -Depth 14),[Text.UTF8Encoding]::new($false));[IO.File]::Move($temporary,$manifestPath,$true)
```

Expected: each clean is authorized by a fresh live proof, exits 0, and is
followed immediately by an ignored-empty proof. The manifest reaches
`CLEANED_VERIFIED` only after three distinct post-clean receipts.

### Task 6: Remove Stale Worktrees And Merged Branches

**Files:**
- Git worktree metadata only

**Interfaces:**
- Consumes: clean worktree, readable stash, verified ignored snapshot
- Produces: removed stale worktree and retained branch history

- [ ] **Step 1: Prove and remove each stale worktree without force**

The reusable gate checks `CLEANED_VERIFIED`, exact cleanup receipts, current
branch/HEAD, reachability, empty tracked/untracked/ignored/preview state, and
all recovery evidence immediately before each removal:

```powershell
$ErrorActionPreference='Stop'
$manifestPath='C:\Users\kiwun\Documents\ai\worktree-snapshots\2026-07-10-docs-renewal\manifest.json'
$proofGatePath='C:\Users\kiwun\Documents\ai\worktree-snapshots\2026-07-10-docs-renewal\cleanup-proof-gate.ps1'
$removals=@(
    [pscustomobject]@{id='premium-bank-app-portal';repo='C:\Users\kiwun\Documents\ai\VPN';worktree='C:\Users\kiwun\.config\superpowers\worktrees\VPN\premium-bank-app-portal'},
    [pscustomobject]@{id='release-hardening-platform';repo='C:\Users\kiwun\Documents\ai\VPN';worktree='C:\Users\kiwun\.config\superpowers\worktrees\VPN\release-hardening-platform'},
    [pscustomobject]@{id='release-hardening-client';repo='C:\Users\kiwun\Documents\ai\POKROV-app';worktree='C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\release-hardening-client'}
)
foreach($removal in $removals){
    & $proofGatePath -ManifestPath $manifestPath -EntryId $removal.id -Mode BeforeStaleRemoval
    if(-not $?){throw "$($removal.id) pre-removal proof failed"}
    & git -C $removal.repo worktree remove $removal.worktree
    $removeExit=$LASTEXITCODE
    if($removeExit -ne 0){throw "$($removal.id) worktree removal failed ($removeExit)"}
}
```

Expected: all commands succeed without `--force`.

- [ ] **Step 2: Delete only the merged local branches**

Run:

```powershell
& git -C 'C:\Users\kiwun\Documents\ai\VPN' branch -d codex/premium-bank-app-portal
if($LASTEXITCODE -ne 0){throw 'premium branch deletion failed'}
& git -C 'C:\Users\kiwun\Documents\ai\VPN' branch -d codex/release-hardening-platform
if($LASTEXITCODE -ne 0){throw 'platform release branch deletion failed'}
& git -C 'C:\Users\kiwun\Documents\ai\POKROV-app' branch -d codex/release-hardening-client
if($LASTEXITCODE -ne 0){throw 'client release branch deletion failed'}
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

- [ ] **Step 1: Remove temporary clean worktrees and branches**

Run without `--force`:

```powershell
$ErrorActionPreference='Stop'
$manifestPath='C:\Users\kiwun\Documents\ai\worktree-snapshots\2026-07-10-docs-renewal\manifest.json'
$proofGatePath='C:\Users\kiwun\Documents\ai\worktree-snapshots\2026-07-10-docs-renewal\cleanup-proof-gate.ps1'

& $proofGatePath -ManifestPath $manifestPath -EntryId 'agent-context-refactor-platform' -Mode BeforeTemporaryRemoval
if(-not $?){throw 'platform docs worktree proof failed'}
& git -C 'C:\Users\kiwun\Documents\ai\VPN' worktree remove 'C:\Users\kiwun\Documents\ai\VPN\.worktrees\agent-context-refactor'
if($LASTEXITCODE -ne 0){throw 'platform docs worktree removal failed'}
& git -C 'C:\Users\kiwun\Documents\ai\VPN' branch -d codex/agent-context-refactor
if($LASTEXITCODE -ne 0){throw 'platform docs branch deletion failed'}
& git -C 'C:\Users\kiwun\Documents\ai\VPN' merge-base --is-ancestor codex/product-audit-closure master
if($LASTEXITCODE -ne 0){throw 'product-audit branch is not reachable from master'}
& git -C 'C:\Users\kiwun\Documents\ai\VPN' branch -d codex/product-audit-closure
if($LASTEXITCODE -ne 0){throw 'product-audit branch deletion failed'}

& $proofGatePath -ManifestPath $manifestPath -EntryId 'agent-context-refactor-client' -Mode BeforeTemporaryRemoval
if(-not $?){throw 'client docs worktree proof failed'}
& git -C 'C:\Users\kiwun\Documents\ai\POKROV-app' worktree remove 'C:\Users\kiwun\Documents\ai\POKROV-app\.worktrees\agent-context-refactor-client'
if($LASTEXITCODE -ne 0){throw 'client docs worktree removal failed'}
& git -C 'C:\Users\kiwun\Documents\ai\POKROV-app' branch -d codex/agent-context-refactor-client
if($LASTEXITCODE -ne 0){throw 'client docs branch deletion failed'}
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
