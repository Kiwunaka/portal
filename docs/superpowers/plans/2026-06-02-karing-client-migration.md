# Karing Client Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove and, if green, migrate the POKROV Android + Windows client lane from the current clean-room shell to a POKROV-branded Karing-based fork without losing app-first provisioning, managed subscriptions, release honesty, or GPL compliance.

**Architecture:** Use a separate Karing-based sibling repo first, not a destructive overwrite of `C:/Users/kiwun/Documents/ai/POKROV-app`. The fork must keep upstream Karing mergeable while adding a POKROV managed mode that hides generic proxy-utility surfaces from normal users and consumes POKROV backend contracts as the source of truth.

**Tech Stack:** Flutter/Dart, Karing GPL-3.0-or-later base, sing-box/vpn-service runtime, POKROV backend API, Android APK/AAB, Windows EXE/MSIX/ZIP.

---

## Current Findings

- User decision on `2026-06-02`: reopen the previous clean-room decision and prefer Karing as the client base if it is buildable and legally shippable.
- Existing client lane: `C:/Users/kiwun/Documents/ai/POKROV-app`.
- Previous decision file: `C:/Users/kiwun/Documents/ai/POKROV-app/docs/decisions/2026-04-18-karing-vs-clean-room-gate.md` currently says `clean-room selected`.
- Karing license: `GPL-3.0-or-later` plus a name/association restriction. A POKROV fork must not use the Karing name or imply association without consent.
- Public Karing clone inspected at commit `e5a39a2` did not contain enough local source files for direct build in the shallow checkout. Missing imports include `lib/app/local_services/vpn_service.dart`, `lib/app/utils/*.dart`, `lib/app/private/sentry_utils_private.dart`, `lib/screens/accessibility_screen.dart`, `lib/screens/list_remove_screen.dart`, and `lib/screens/statistics_records_screen.dart`. `pubspec.yaml` also points `vpn_service` to `../vpn-service/`.
- Therefore the first implementation task is a source-completeness and buildability gate. Do not start branding or UX work until that gate is green.

## Target Repo Layout

- `C:/Users/kiwun/Documents/ai/POKROV-karing/`
  - New sibling repo for the Karing-based fork spike and later candidate lane.
  - Remotes: `upstream` = `https://github.com/KaringX/karing.git`; `origin` = future POKROV fork remote.
  - Branches: `upstream-main`, `codex/pokrov-managed-mode`, later promoted branch decided explicitly.
- `C:/Users/kiwun/Documents/ai/POKROV-app/`
  - Keep intact as the current canonical client lane until the Karing candidate passes release gates.
  - Update docs/decisions only after user approval for the decision record.
- `C:/Users/kiwun/Documents/ai/VPN/`
  - Platform/backend source of truth remains unchanged.
  - Backend APIs remain product authority; Karing/3x-ui/sing-box are execution layers.

## Success Criteria

- Android release APK builds from source and installs.
- Windows release EXE builds from source and runs.
- First-run POKROV managed flow works: app creates/uses an app-first session, fetches managed profile, silently imports it, asks route-mode question, and connects.
- Normal user UI exposes `Protection / Locations / Rules / Profile`, not raw subscription/config/editor-first Karing UI.
- Manual import, raw profile editing, WebDAV/iCloud backup, generic QR import, Cloudflare WARP, zashboard, and low-level proxy settings are hidden behind an explicit advanced/recovery path or removed.
- POKROV backend remains source of truth for entitlement, trial, device identity, subscription, node pools, support, checkout, and smart-connect hints.
- GPL compliance is ready before distributing any modified binary.

## Stop Conditions

- Full Karing source cannot be obtained or built from source.
- `vpn-service` source/dependency cannot be resolved in a GPL-compatible, reproducible way.
- Android or Windows cannot connect using POKROV managed profile without patching private binary-only code.
- Required pruning means rewriting most Karing UI and runtime glue; in that case keep clean-room POKROV-app and reuse Karing only as a reference.

---

### Task 1: Record The Reopened Base Decision

**Files:**
- Create: `C:/Users/kiwun/Documents/ai/POKROV-app/docs/decisions/2026-06-02-karing-base-reopen.md`
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md`
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-app/docs/implementation/client-release-backlog.md`

- [ ] **Step 1: Create decision note**

Write a short decision record with:

```markdown
# Karing Base Reopen

Date: 2026-06-02
Status: reopened for gated spike
Decision owner: owner/operator

## Decision

Reopen the earlier clean-room-only decision and evaluate a Karing-based POKROV client fork.

## Reason

The current clean-room client lane is slow to reach production confidence. Karing already provides a Flutter, cross-platform, sing-box-first client foundation that may reduce Android and Windows runtime risk.

## Gate

Karing is accepted only if the full source tree is buildable, GPL obligations are satisfied, POKROV managed onboarding works, and generic proxy-utility surfaces can be hidden without a near-total rewrite.

## Non-Goals

This does not overwrite the current POKROV-app lane. It creates a gated candidate lane first.
```

- [ ] **Step 2: Update cutover status**

In `cutover-readiness.md`, change only the base-decision lines to say:

```markdown
- base decision: `Karing-based candidate reopened for gated spike; clean-room lane remains current until candidate gates pass`
```

- [ ] **Step 3: Add backlog item**

In `client-release-backlog.md`, add one top-level item:

```markdown
## Karing-Based Candidate Lane

- [ ] Prove full-source Karing buildability for Android and Windows
- [ ] Implement POKROV managed mode
- [ ] Pass Android + Windows release gates before any public cutover
```

- [ ] **Step 4: Commit decision docs**

Run:

```powershell
git -C C:\Users\kiwun\Documents\ai\POKROV-app diff -- docs/decisions docs/operations/cutover-readiness.md docs/implementation/client-release-backlog.md
git -C C:\Users\kiwun\Documents\ai\POKROV-app status --short
```

Expected: only the decision/backlog/cutover docs from this task are newly changed beyond any existing unrelated local changes.

---

### Task 2: Prove Karing Source Completeness

**Files:**
- Create: `C:/Users/kiwun/Documents/ai/POKROV-karing/`
- Create: `C:/Users/kiwun/Documents/ai/POKROV-karing/tools/check_source_completeness.ps1`
- Read: `C:/Users/kiwun/Documents/ai/POKROV-karing/pubspec.yaml`
- Read: `C:/Users/kiwun/Documents/ai/POKROV-karing/LICENSE.md`

- [ ] **Step 1: Clone candidate source**

Run:

```powershell
cd C:\Users\kiwun\Documents\ai
git clone https://github.com/KaringX/karing.git POKROV-karing
cd C:\Users\kiwun\Documents\ai\POKROV-karing
git remote rename origin upstream
git checkout -b codex/pokrov-managed-mode
git log -1 --oneline
```

Expected: repo exists and branch is `codex/pokrov-managed-mode`.

- [ ] **Step 2: Resolve `vpn_service`**

Check `pubspec.yaml`.

If it still contains:

```yaml
vpn_service:
  path: ../vpn-service/
```

then try:

```powershell
cd C:\Users\kiwun\Documents\ai
git clone https://github.com/KaringX/vpn-service.git vpn-service
```

Expected: `C:/Users/kiwun/Documents/ai/vpn-service` exists, or the task stops with `BLOCKED: vpn_service source unavailable`.

- [ ] **Step 3: Add source-completeness checker**

Create `tools/check_source_completeness.ps1`:

```powershell
$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$lib = Join-Path $root "lib"
$missing = @()

Get-ChildItem $lib -Filter *.dart -Recurse | ForEach-Object {
  Select-String -Path $_.FullName -Pattern "import 'package:karing/([^']+)'" | ForEach-Object {
    $rel = $_.Matches[0].Groups[1].Value
    $target = Join-Path $lib $rel
    if (-not (Test-Path $target)) {
      $missing += $rel
    }
  }
}

$missing = $missing | Sort-Object -Unique
if ($missing.Count -gt 0) {
  Write-Host "Missing package:karing imports:"
  $missing | ForEach-Object { Write-Host " - $_" }
  exit 1
}

Write-Host "Karing local imports are complete."
```

- [ ] **Step 4: Run source-completeness checker**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\kiwun\Documents\ai\POKROV-karing\tools\check_source_completeness.ps1
```

Expected: `Karing local imports are complete.` If missing imports remain, stop the migration and decide whether to request/locate full source or keep clean-room.

- [ ] **Step 5: Commit source-check tooling**

Run:

```powershell
git -C C:\Users\kiwun\Documents\ai\POKROV-karing add tools/check_source_completeness.ps1
git -C C:\Users\kiwun\Documents\ai\POKROV-karing commit -m "chore: add Karing source completeness check"
```

---

### Task 3: Build Upstream Karing Before Branding

**Files:**
- Read: `C:/Users/kiwun/Documents/ai/POKROV-karing/pubspec.yaml`
- Read: `C:/Users/kiwun/Documents/ai/POKROV-karing/android/`
- Read: `C:/Users/kiwun/Documents/ai/POKROV-karing/windows/`

- [ ] **Step 1: Fetch dependencies**

Run:

```powershell
cd C:\Users\kiwun\Documents\ai\POKROV-karing
flutter --version
flutter pub get
```

Expected: dependency resolution succeeds without path errors.

- [ ] **Step 2: Analyze**

Run:

```powershell
flutter analyze
```

Expected: no fatal missing-source errors. Existing upstream lint warnings may be recorded, but build-blocking errors stop the migration.

- [ ] **Step 3: Build Android debug**

Run:

```powershell
flutter build apk --debug
```

Expected: `build/app/outputs/flutter-apk/app-debug.apk` exists.

- [ ] **Step 4: Build Windows debug**

Run:

```powershell
flutter build windows --debug
```

Expected: `build/windows/x64/runner/Debug/karing.exe` or equivalent runner artifact exists.

- [ ] **Step 5: Record build proof**

Create:

```text
C:/Users/kiwun/Documents/ai/POKROV-karing/docs/pokrov/buildability-proof.md
```

with the exact commit, Flutter version, dependency result, Android artifact path, Windows artifact path, and blockers if any.

- [ ] **Step 6: Commit build proof**

Run:

```powershell
git -C C:\Users\kiwun\Documents\ai\POKROV-karing add docs/pokrov/buildability-proof.md
git -C C:\Users\kiwun\Documents\ai\POKROV-karing commit -m "docs: record upstream Karing buildability proof"
```

---

### Task 4: Add POKROV Branding And Compliance Shell

**Files:**
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-karing/pubspec.yaml`
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/main.dart`
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/app/utils/app_utils.dart`
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/app/utils/system_scheme_utils.dart`
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-karing/android/app/src/main/AndroidManifest.xml`
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-karing/windows/runner/Runner.rc`
- Create: `C:/Users/kiwun/Documents/ai/POKROV-karing/NOTICE-POKROV.md`
- Create: `C:/Users/kiwun/Documents/ai/POKROV-karing/docs/pokrov/gpl-compliance.md`

- [ ] **Step 1: Rename visible app identity**

Set visible name to `POKROV`, package/bundle IDs to POKROV-owned IDs, and URI scheme to `pokrov`.

Expected visible strings:

```text
POKROV
pokrov://
```

Forbidden visible strings in normal UI:

```text
Karing
Clash Mi
Doggygo
airport
```

- [ ] **Step 2: Add compliance files**

`NOTICE-POKROV.md` must include:

```markdown
# POKROV Client Notices

This client is a modified distribution based on Karing.

Karing copyright:
Copyright (C) 2024 by nebula

License:
GNU General Public License, version 3 or later.

POKROV modifications:
- POKROV branding
- POKROV managed onboarding and backend provisioning
- Consumer-first UI pruning
- POKROV release packaging

No association with the original Karing project is implied.
```

`docs/pokrov/gpl-compliance.md` must include:

```markdown
# GPL Compliance Checklist

- [ ] Source code for the distributed binary is published or offered under GPL terms
- [ ] GPL license text is included
- [ ] Karing copyright notices are preserved
- [ ] Modified files are marked through git history and release notes
- [ ] POKROV does not use Karing name or imply upstream association
- [ ] Third-party dependency licenses are inventoried before public distribution
```

- [ ] **Step 3: Build after branding**

Run:

```powershell
flutter analyze
flutter build apk --debug
flutter build windows --debug
```

Expected: both debug builds still succeed.

- [ ] **Step 4: Commit branding shell**

Run:

```powershell
git add pubspec.yaml lib android windows NOTICE-POKROV.md docs/pokrov/gpl-compliance.md
git commit -m "feat: add POKROV branding and compliance notices"
```

---

### Task 5: Implement POKROV Managed Mode

**Files:**
- Create: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/pokrov/pokrov_config.dart`
- Create: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/pokrov/pokrov_api_client.dart`
- Create: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/pokrov/pokrov_session_store.dart`
- Create: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/pokrov/pokrov_managed_profile.dart`
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/main.dart`
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/app/modules/server_manager.dart`

- [ ] **Step 1: Define immutable product config**

`pokrov_config.dart`:

```dart
class PokrovConfig {
  static const appName = 'POKROV';
  static const apiBaseUrl = String.fromEnvironment(
    'POKROV_API_BASE_URL',
    defaultValue: 'https://api.pokrov.space',
  );
  static const checkoutBaseUrl = String.fromEnvironment(
    'POKROV_CHECKOUT_BASE_URL',
    defaultValue: 'https://pay.pokrov.space/checkout/',
  );
  static const supportEmail = 'support@pokrov.space';
  static const publicChannel = '@pokrov_vpn';
}
```

- [ ] **Step 2: Add app-first API client**

`pokrov_api_client.dart` must expose:

```dart
class PokrovApiClient {
  Future<Map<String, dynamic>> startTrial(Map<String, dynamic> deviceContext);
  Future<Map<String, dynamic>> getManagedProfile(String sessionToken);
  Future<Map<String, dynamic>> getDashboard(String sessionToken);
  Future<void> postLatencySamples(String sessionToken, List<Map<String, dynamic>> samples);
}
```

Endpoints:

```text
POST /api/client/session/start-trial
GET /api/client/profile/managed
GET /api/client/dashboard
POST /api/client/nodes/latency-samples
```

- [ ] **Step 3: Persist POKROV session securely**

`pokrov_session_store.dart` must persist:

```text
install_id
session_token
app_account_id
device_id
profile_revision
route_mode
selected_apps
```

Use `flutter_secure_storage` for tokens and normal local storage only for non-secret UI state.

- [ ] **Step 4: Convert managed profile into Karing profile**

`pokrov_managed_profile.dart` must accept POKROV managed profile fields:

```text
version
profile_revision
transport_profile
transport_kind
engine_hint
config_format
config_payload
fallback_order
support_context
smart_connect
```

If `config_format == sing-box-json`, import `config_payload` through Karing's existing sing-box profile path.

- [ ] **Step 5: Build and test managed import**

Run against a non-secret local or staging session token:

```powershell
flutter test
flutter build apk --debug
flutter build windows --debug
```

Expected: managed profile appears as one locked POKROV profile, not as a user-editable random subscription.

- [ ] **Step 6: Commit managed mode**

Run:

```powershell
git add lib/pokrov lib/main.dart lib/app/modules/server_manager.dart
git commit -m "feat: add POKROV managed profile mode"
```

---

### Task 6: Replace First-Layer UI With POKROV Consumer Shell

**Files:**
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/screens/home_screen.dart`
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/screens/home_screen_widgets.dart`
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/screens/group_screen.dart`
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/screens/settings_screen.dart`
- Create: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/pokrov/ui/protection_screen.dart`
- Create: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/pokrov/ui/locations_screen.dart`
- Create: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/pokrov/ui/rules_screen.dart`
- Create: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/pokrov/ui/profile_screen.dart`

- [ ] **Step 1: Lock first-layer tabs**

Normal mode tabs must be exactly:

```text
Protection
Locations
Rules
Profile
```

- [ ] **Step 2: Hide generic import surfaces**

Remove from first layer:

```text
Add profile by URL/content
Add profile by QR
Import from file
Backup and sync
WebDAV
iCloud
Cloudflare WARP account
Raw DNS editor
Raw routing editor
Zashboard
```

These can remain behind `Profile -> Settings -> Advanced recovery` only if needed for operator recovery.

- [ ] **Step 3: Add activation gate**

Before trial/session exists:

```text
Protection: Try free
Locations: gated, no fake countries
Rules: gated
Profile: support/recovery only
```

- [ ] **Step 4: Add route-mode question**

Before first live connect, ask:

```text
How should this device work?
Optimize everything on this device
Only selected apps
```

Persist to backend route-mode fields.

- [ ] **Step 5: Build UI**

Run:

```powershell
flutter analyze
flutter test
flutter build apk --debug
flutter build windows --debug
```

Expected: no first-layer generic proxy utility screens remain in normal mode.

- [ ] **Step 6: Commit consumer shell**

Run:

```powershell
git add lib/screens lib/pokrov/ui
git commit -m "feat: add POKROV consumer shell"
```

---

### Task 7: Wire Smart Connect, Support, Checkout, And Telegram Reward

**Files:**
- Create: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/pokrov/pokrov_smart_connect.dart`
- Create: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/pokrov/pokrov_support.dart`
- Create: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/pokrov/pokrov_checkout.dart`
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/pokrov/ui/locations_screen.dart`
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-karing/lib/pokrov/ui/profile_screen.dart`

- [ ] **Step 1: Smart-connect shortlist**

Use backend `smart_connect.shortlist` as the shortlist source.

Rules:

```text
premium: probe up to 5 eligible non-free nodes
free: NL-free only
stickiness threshold: 15%
```

- [ ] **Step 2: Safe diagnostics**

Support payload may include:

```text
app version
platform
route mode
DNS policy
transport profile
ruleset version
linked Telegram state
last connection status
```

Support payload must not include:

```text
raw VLESS links
UUIDs
private keys
short IDs
subscription URLs
panel credentials
```

- [ ] **Step 3: Checkout handoff**

Open:

```text
https://pay.pokrov.space/checkout/
```

in external browser/application.

- [ ] **Step 4: Telegram reward handoff**

Use:

```text
@pokrov_vpn
@pokrov_vpnbot
```

as secondary/reward surfaces, not primary login walls.

- [ ] **Step 5: Build**

Run:

```powershell
flutter analyze
flutter test
flutter build apk --debug
flutter build windows --debug
```

- [ ] **Step 6: Commit integrations**

Run:

```powershell
git add lib/pokrov
git commit -m "feat: wire POKROV smart connect and continuations"
```

---

### Task 8: Release Gate The Karing Candidate

**Files:**
- Create: `C:/Users/kiwun/Documents/ai/POKROV-karing/docs/pokrov/release-gate.md`
- Create: `C:/Users/kiwun/Documents/ai/POKROV-karing/scripts/build-pokrov-android.ps1`
- Create: `C:/Users/kiwun/Documents/ai/POKROV-karing/scripts/build-pokrov-windows.ps1`

- [ ] **Step 1: Android release build**

Run:

```powershell
flutter build apk --release --dart-define=POKROV_API_BASE_URL=https://api.pokrov.space
flutter build appbundle --release --dart-define=POKROV_API_BASE_URL=https://api.pokrov.space
```

Expected:

```text
build/app/outputs/flutter-apk/app-release.apk
build/app/outputs/bundle/release/app-release.aab
```

- [ ] **Step 2: Windows release build**

Run:

```powershell
flutter build windows --release --dart-define=POKROV_API_BASE_URL=https://api.pokrov.space
```

Expected: release runner exists under `build/windows/x64/runner/Release/`.

- [ ] **Step 3: Smoke on real devices**

Required checks:

```text
Android physical install starts
Windows app starts
Try free works or existing staging session imports
Connect works
Disconnect works
Locations show real POKROV nodes
Support opens safe continuation
Checkout opens canonical hosted checkout
No first-layer raw config leakage
```

- [ ] **Step 4: GPL release package**

Before distributing binaries, prepare:

```text
source archive URL or written source offer
LICENSE.md
NOTICE-POKROV.md
third-party license inventory
release commit SHA
artifact SHA256 sums
```

- [ ] **Step 5: Commit release gate docs**

Run:

```powershell
git add docs/pokrov scripts
git commit -m "docs: add POKROV Karing release gate"
```

---

### Task 9: Cutover Decision And Rollback

**Files:**
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/cutover-readiness.md`
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-app/docs/product/client-product-contract.md`
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/android-release-audit.md`
- Modify: `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/windows-release-readiness.md`
- Modify: `C:/Users/kiwun/Documents/ai/VPN/docs/operations/deployment-and-access.md` only if public download URLs or release handoff behavior change.

- [ ] **Step 1: Compare lanes**

Produce a one-page comparison:

```text
Clean-room POKROV-app:
- current build state
- known blockers
- release confidence

Karing-based POKROV:
- Android build state
- Windows build state
- managed provisioning state
- UI pruning state
- GPL readiness
- remaining blockers
```

- [ ] **Step 2: Ask for explicit owner cutover approval**

Do not replace the canonical client lane without explicit owner approval.

Required approval wording:

```text
Approve Karing-based POKROV as the new Android + Windows client candidate lane.
```

- [ ] **Step 3: Keep rollback path**

Rollback rule:

```text
Current POKROV-app clean-room lane remains available until Karing-based app has a tester-proven Android + Windows beta and no worse production blockers.
```

- [ ] **Step 4: Publish beta only after gates**

Allowed wording:

```text
POKROV Android + Windows beta candidate
```

Forbidden wording until evidence exists:

```text
stable
1.0.0
store-ready
trusted Windows signing
Play-ready
```

---

## Execution Order

1. Task 1: decision docs.
2. Task 2: source completeness.
3. Task 3: upstream builds.
4. Task 4: branding/compliance.
5. Task 5: managed mode.
6. Task 6: consumer shell.
7. Task 7: smart-connect/continuations.
8. Task 8: release gates.
9. Task 9: cutover decision.

## Key Risk Register

- **Incomplete public source:** Current inspected Karing tree misses many local imports. This is P0.
- **Path dependency:** `vpn_service` path dependency must be resolved from source.
- **Inherited UX debt:** Karing's generic proxy utility screens are valuable for power users but wrong for first-layer POKROV UX.
- **GPL obligations:** Shipping a modified fork means shipping/offering corresponding source.
- **Upstream merge drift:** Keep POKROV patches isolated under `lib/pokrov/` where possible.
- **Release trust:** Windows remains unsigned unless a signing identity is added; Android outside-store claims remain beta-only.

## Handoff Choice

Plan complete. Recommended implementation mode:

1. **Subagent-driven for Task 2 and Task 3** because source/buildability can fail fast and should be isolated.
2. **Inline execution for Tasks 4-7** after gates pass, because product judgment and UI pruning need tight owner feedback.
3. **Manual owner checks for Task 8 Android physical device and final cutover approval.**
