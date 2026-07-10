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
    return @($lines | Where-Object { $_ -ne '' } | ForEach-Object { $_.Replace('\', '/') } | Sort-Object -Unique)
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
        untracked_paths = $untracked
        untracked_count = $untracked.Count
        ignored_paths = $ignored
        ignored_count = $ignored.Count
    }
}
```

Expected: staged plus unstaged tracked paths come from
`git diff HEAD --name-only`; untracked and ignored paths remain separate.

- [ ] **Step 2: Classify ignored paths using path metadata only**

Continue in the same PowerShell process. Known generated prefixes are checked
before risk words so package files such as `node_modules/**/token*` do not
become false secret hits. No content-search command belongs in this procedure.

```powershell
function Get-IgnoredClass {
    param([string]$Id, [string]$RelativePath)
    $path = $RelativePath.Replace('\', '/')

    if ($Id -eq 'release-hardening-platform' -and $path -match '^ops-local(?:/|$)') { return 'retained_snapshotted' }
    if ($Id -eq 'release-hardening-client' -and (
        $path -match '^artifacts(?:/|$)' -or
        $path -in @(
            'apps/android_shell/android/gradle/wrapper/gradle-wrapper.jar',
            'apps/android_shell/android/gradlew',
            'apps/android_shell/android/gradlew.bat',
            'apps/android_shell/android/local.properties'
        ) -or
        $path -match '^apps/ios_shell/ios/Flutter(?:/|$)'
    )) { return 'retained_snapshotted' }

    if ($path -match '(^|/)(node_modules|\.next|out|\.dart_tool|build|__pycache__)(/|$)' -or
        $path -match '(^|/)flutter/ephemeral(/|$)' -or
        $path -match '^(\.pytest_cache|\.tmp)(/|$)' -or
        $path -match '(^|/)portal_api_test_[^/]*\.db$' -or
        ($Id -ne 'release-hardening-client' -and $path -in @('marketing/next-env.d.ts', 'webapp/next-env.d.ts')) -or
        ($Id -eq 'release-hardening-client' -and (
            $path -match '^(apps|packages)/(?:.*/)?\.flutter-plugins[^/]*$' -or
            $path -match '^apps/android_shell/android/\.gradle(?:/|$)' -or
            $path -match '^apps/android_shell/android/(?:.*/)?GeneratedPluginRegistrant\.java$' -or
            $path -match '^apps/ios_shell/ios/Runner/GeneratedPluginRegistrant\.[^/]+$'
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
}
```

Expected: every ignored path is either `generated_disposable` or
`retained_snapshotted`. High-risk and unknown paths block cleanup and remain
in their local worktree.

- [ ] **Step 3: Persist inventory, classifications, expectations, and blockers**

```powershell
$manifest = [pscustomobject]@{
    schema_version = 2
    created_utc = [DateTime]::UtcNow.ToString('o')
    stage_a_state = 'INVENTORY_ONLY'
    audit_expectations = [pscustomobject]@{
        observed_on = '2026-07-10'
        platform_ops_local = [pscustomobject]@{ file_count=2; byte_count=2052 }
        client_artifacts = [pscustomobject]@{ file_count=114; byte_count=2016578139 }
    }
    audit_drift = @($drift)
    worktrees = @($entries)
    retained_snapshots = @()
    stashes = [pscustomobject]@{}
}
$json = $manifest | ConvertTo-Json -Depth 12
[IO.File]::WriteAllText($manifestPath, $json, [Text.UTF8Encoding]::new($false))

$blockers = @($entries | ForEach-Object { @($_.high_risk_paths) + @($_.unknown_paths) })
if ($drift.Count -gt 0) { throw "Preflight drift recorded in manifest; review before a new Stage A run" }
if ($blockers.Count -gt 0) { throw "Unknown/high-risk ignored paths recorded in manifest; cleanup remains blocked" }
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

function Assert-PlainTree {
    param([string]$Root)
    $rootItem = Get-Item -Force -LiteralPath $Root
    if (-not $rootItem.PSIsContainer -or ($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Not a plain directory: $Root"
    }
    $reparse = @(Get-ChildItem -Force -LiteralPath $Root -Recurse | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
    if ($reparse.Count -gt 0) { throw "Reparse point found below retained root: $Root" }
}

function Get-RetainedRecords {
    param([string]$Worktree, [string[]]$RelativeSpecs)
    $worktreeRoot = [IO.Path]::GetFullPath($Worktree)
    $filesByRelativePath = @{}
    foreach ($spec in $RelativeSpecs) {
        $source = [IO.Path]::GetFullPath((Join-Path $worktreeRoot $spec))
        if (-not $source.StartsWith($worktreeRoot + [IO.Path]::DirectorySeparatorChar, $comparison)) { throw "Retained source escaped worktree: $source" }
        if (-not (Test-Path -LiteralPath $source)) { throw "Mandatory retained source is missing: $source" }
        $item = Get-Item -Force -LiteralPath $source
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Retained source is a reparse point: $source" }
        $files = if ($item.PSIsContainer) {
            Assert-PlainTree $source
            @(Get-ChildItem -Force -File -Recurse -LiteralPath $source)
        } else { @($item) }
        foreach ($file in $files) {
            $relative = [IO.Path]::GetRelativePath($worktreeRoot, $file.FullName).Replace('\', '/')
            if ($relative -eq '..' -or $relative.StartsWith('../')) { throw "Retained file escaped worktree" }
            $filesByRelativePath[$relative] = $file.FullName
        }
    }
    return @($filesByRelativePath.Keys | Sort-Object | ForEach-Object {
        $file = Get-Item -Force -LiteralPath $filesByRelativePath[$_]
        [pscustomobject]@{
            relative_path = $_
            source_full_name = $file.FullName
            byte_length = $file.Length
            sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
        }
    })
}

function Assert-RecordMatch {
    param([object[]]$Expected, [object[]]$Actual, [string]$Label)
    $expectedByPath = @{}; foreach ($record in @($Expected)) { $expectedByPath[$record.relative_path] = $record }
    $actualByPath = @{}; foreach ($record in @($Actual)) { $actualByPath[$record.relative_path] = $record }
    $delta = @(Compare-Object @($expectedByPath.Keys | Sort-Object) @($actualByPath.Keys | Sort-Object) -CaseSensitive)
    if ($delta.Count -gt 0) { throw "$Label relative-path set mismatch" }
    foreach ($path in $expectedByPath.Keys) {
        if ($expectedByPath[$path].byte_length -ne $actualByPath[$path].byte_length -or $expectedByPath[$path].sha256 -ne $actualByPath[$path].sha256) {
            throw "$Label length/hash mismatch: $path"
        }
    }
}

function New-RetainedSnapshot {
    param(
        [string]$Id,
        [string]$Worktree,
        [string[]]$RelativeSpecs,
        [string]$AuditPrefix,
        [int]$ExpectedAuditFiles,
        [long]$ExpectedAuditBytes
    )
    $snapshotRoot = [IO.Path]::GetFullPath((Join-Path $backupRoot $Id))
    if (-not $snapshotRoot.StartsWith($backupRoot + [IO.Path]::DirectorySeparatorChar, $comparison)) { throw "Snapshot escaped backup root" }
    if (Test-Path -LiteralPath $snapshotRoot) { throw "Snapshot destination already exists: $snapshotRoot" }

    $sourceRecords = @(Get-RetainedRecords $Worktree $RelativeSpecs)
    $auditRecords = @($sourceRecords | Where-Object { $_.relative_path -eq $AuditPrefix -or $_.relative_path.StartsWith($AuditPrefix + '/', [StringComparison]::Ordinal) })
    $auditBytes = ($auditRecords | Measure-Object -Property byte_length -Sum).Sum
    if ($auditRecords.Count -ne $ExpectedAuditFiles -or $auditBytes -ne $ExpectedAuditBytes) {
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
        byte_count = ($sourceRecords | Measure-Object -Property byte_length -Sum).Sum
        files = @($sourceRecords | Select-Object relative_path, byte_length, sha256)
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
        } | Sort-Object relative_path)
    $sourceAfterCopy = @(Get-RetainedRecords $Worktree $RelativeSpecs | Select-Object relative_path, byte_length, sha256)
    Assert-RecordMatch @($saved.files) $sourceAfterCopy "$Id source-after-copy"
    Assert-RecordMatch @($saved.files) $destinationRecords "$Id destination"
    return [pscustomobject]@{ id=$Id; manifest=[IO.Path]::GetRelativePath($backupRoot, $snapshotManifestPath).Replace('\', '/'); file_count=$saved.file_count; byte_count=$saved.byte_count; verified=$true }
}

$platformSnapshot = New-RetainedSnapshot `
    -Id 'release-hardening-platform' `
    -Worktree 'C:\Users\kiwun\.config\superpowers\worktrees\VPN\release-hardening-platform' `
    -RelativeSpecs @('ops-local') `
    -AuditPrefix 'ops-local' -ExpectedAuditFiles 2 -ExpectedAuditBytes 2052

$clientSnapshot = New-RetainedSnapshot `
    -Id 'release-hardening-client' `
    -Worktree 'C:\Users\kiwun\.config\superpowers\worktrees\POKROV-app\release-hardening-client' `
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
byte length, and hash of every copied file. Both the source and destination are
re-enumerated after the copy; count-only or hash-only proof is insufficient.

- [ ] **Step 2: Record only verified snapshot manifests in the Stage A manifest**

```powershell
$manifest = [IO.File]::ReadAllText($manifestPath) | ConvertFrom-Json
$manifest.retained_snapshots = @($platformSnapshot, $clientSnapshot)
$manifest.stage_a_state = 'SNAPSHOTS_VERIFIED'
$temporaryManifest = "$manifestPath.tmp"
if (Test-Path -LiteralPath $temporaryManifest) { throw "Manifest temp collision" }
[IO.File]::WriteAllText($temporaryManifest, ($manifest | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))
[IO.File]::Move($temporaryManifest, $manifestPath, $true)
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
if ($manifest.stage_a_state -ne 'SNAPSHOTS_VERIFIED' -or @($manifest.retained_snapshots | Where-Object verified -eq $true).Count -ne 2) {
    throw "Retained snapshots are not fully verified"
}

function Invoke-GitPathSet {
    param([string]$Repo, [string[]]$GitArgs)
    $lines = @(& git -c core.quotepath=false -C $Repo @GitArgs)
    if ($LASTEXITCODE -ne 0) { throw "git failed in ${Repo}: $($GitArgs -join ' ')" }
    return @($lines | Where-Object { $_ -ne '' } | ForEach-Object { $_.Replace('\', '/') } | Sort-Object -Unique)
}
function Assert-SamePathSet {
    param([object[]]$Expected, [object[]]$Actual, [string]$Label)
    $delta = @(Compare-Object @($Expected | Sort-Object -Unique) @($Actual | Sort-Object -Unique) -CaseSensitive)
    if ($delta.Count -gt 0) { throw "$Label path-set mismatch" }
}
function Save-StageManifest {
    param([object]$Value)
    $temporary = "$manifestPath.tmp"
    if (Test-Path -LiteralPath $temporary) { throw "Manifest temp collision" }
    [IO.File]::WriteAllText($temporary, ($Value | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))
    [IO.File]::Move($temporary, $manifestPath, $true)
}

$messages = @{
    'premium-bank-app-portal' = 'pre-cleanup/2026-07-10/premium-bank-app-portal'
    'release-hardening-platform' = 'pre-cleanup/2026-07-10/release-hardening-platform'
    'release-hardening-client' = 'pre-cleanup/2026-07-10/release-hardening-client'
}

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
    $preStashPaths = @(($tracked + $untracked) | Sort-Object -Unique)
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
        oid = $newOid[0]
        pre_oid = if ($preOid.Count -eq 1) { $preOid[0] } else { $null }
        message = $message
        subject = $subject[0]
        path_count = $preStashPaths.Count
        verified_utc = [DateTime]::UtcNow.ToString('o')
    }
    $manifest.stashes | Add-Member -NotePropertyName $entry.id -NotePropertyValue $record
    Save-StageManifest $manifest
}

$manifest.stage_a_state = 'STAGE_A_VERIFIED'
Save-StageManifest $manifest
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
- Delete locally: only paths classified `generated_disposable`
- Delete locally after snapshot verification: retained ignored roots already
  copied in Task 3

**Interfaces:**
- Consumes: exhaustive classification, snapshot, and readable stash
- Produces: clean removable stale worktree

- [ ] **Step 1: Preview ignored cleanup**

Run:

```powershell
$ErrorActionPreference = 'Stop'
$manifestPath = 'C:\Users\kiwun\Documents\ai\worktree-snapshots\2026-07-10-docs-renewal\manifest.json'
$manifest = [IO.File]::ReadAllText($manifestPath) | ConvertFrom-Json
if ($manifest.stage_a_state -ne 'STAGE_A_VERIFIED' -or @($manifest.stashes.PSObject.Properties).Count -ne 3) {
    throw "Stage A proof gate is not complete"
}
$worktrees = @($manifest.worktrees.worktree)
foreach ($entry in @($manifest.worktrees)) {
    $currentIgnored = @(& git -c core.quotepath=false -C $entry.worktree ls-files --others --ignored --exclude-standard)
    if ($LASTEXITCODE -ne 0) { throw "Cannot re-inventory ignored paths for $($entry.id)" }
    $delta = @(Compare-Object @($entry.ignored_paths | Sort-Object -Unique) @($currentIgnored | Sort-Object -Unique) -CaseSensitive)
    if ($delta.Count -gt 0) { throw "$($entry.id) ignored path-set drift" }
    if (@($entry.ignored_classification | Where-Object classification -notin @('generated_disposable', 'retained_snapshotted')).Count -gt 0) {
        throw "$($entry.id) has an unsafe ignored classification"
    }
    git -C $entry.worktree clean -ndX
    if ($LASTEXITCODE -ne 0) { throw "Ignored cleanup preview failed for $($entry.id)" }
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

Only after Step 1 proves the current ignored relative-path set exactly matches
the manifest and the preview contains no path outside its classification:

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
