# POKROV Documentation Finalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the platform and client documentation system reproducible from a clean checkout, reconcile current documentation status without overriding concurrent product work, and remove only proven disposable local output.

**Architecture:** Keep root `AGENTS.md` thin and route task context through the existing registry/router. Treat generated ledgers as evidence derived from tracked inputs, retain workbook provenance under `docs/audit-artifacts/`, and separate current canon from completed plans and historical evidence. Cleanup is exact-path and manual; automated cleanup `--apply`, protected zones, active worktrees, secrets, and retained evidence are out of scope.

**Tech Stack:** Markdown, CSV, XLSX evidence, Python 3.12 generators and pytest, PowerShell, Git worktrees.

## Global Constraints

- Work only in `C:/Users/kiwun/Documents/ai/VPN-docs-finalization` on `codex/docs-finalization` until integration.
- Do not modify `C:/Users/kiwun/Documents/ai/VPN` or any existing neighboring worktree; they contain concurrent work.
- Do not modify product code, runtime state, release artifacts, secrets, docs-assistant allowlists, or support knowledge-base allowlists.
- Preserve `.content-video-ad`, `docs/audit-artifacts/**`, archive history, rollback evidence, and generated provenance.
- Never use `scripts/cleanup_inventory.py --apply`; cleanup must use verified exact paths and remain outside protected/concurrent zones.
- A current local test pass is not release, device, signing, store, provider, deploy, brain-origin, or RU-origin proof.
- Stage and commit only task-owned files after checking the scoped diff.

---

### Task 1: Reproducible Evidence Ledgers And Navigation

**Files:**
- Create: `docs/audit-artifacts/source-trackers/2026-06-27/marketing-landing-user-story-tracker.xlsx`
- Create: `docs/audit-artifacts/source-trackers/2026-06-27/pokrov-client-user-story-tracker.xlsx`
- Modify: `docs/developer/pokrov-canonical-feature-tracker.csv`
- Modify: `docs/developer/pokrov-canonical-feature-tracker.md`
- Modify generated ledgers under `docs/developer/pokrov-*.csv` and `docs/developer/pokrov-*.md` only through their repository generators where a generator exists
- Modify: `docs/developer/repository-map.md`
- Modify: `docs/developer/work-orders/2026-06-27--repo-feature-story-audit/WO-001-canonical-feature-tracker.md`
- Modify: `docs/developer/work-orders/2026-06-27--repo-feature-story-audit/COMPLETION-AUDIT.md`
- Test: `tests/test_story_test_evidence_audit.py`
- Test: `tests/test_code_function_inventory.py`
- Test: `tests/test_pokrov_migration_defaults.py`

**Interfaces:**
- Consumes: the two retained source workbooks currently under the ignored platform/client `outputs/` trees and canonical CSV inputs already tracked in Git.
- Produces: tracked, portable source-tracker paths; generated ledgers matching current CSV/code counts; developer navigation that reaches every canonical audit artifact.

- [ ] **Step 1: Confirm the red baseline**

Run:

```powershell
python -B -m pytest -p no:cacheprovider tests\test_story_test_evidence_audit.py tests\test_pokrov_migration_defaults.py -q
```

Expected: failures for stale Markdown/generated counts, missing repository-map navigation, and ignored `outputs/*.xlsx` provenance when run from the clean worktree.

- [ ] **Step 2: Retain source workbooks as tracked evidence**

Copy the exact source workbooks without modifying their contents:

```text
C:/Users/kiwun/Documents/ai/VPN/outputs/019f05ac-5b2e-7053-abc2-f4ac146e2ff4/marketing_landing_user_story_tracker.xlsx
C:/Users/kiwun/Documents/ai/POKROV-app/outputs/019f05ac-cfd2-7423-96b6-a7fb48dc87a9/pokrov_flutter_feature_user_story_tracker.xlsx
```

Store them at the two `docs/audit-artifacts/source-trackers/2026-06-27/` paths listed above. Verify byte size and SHA-256 equality between each source and retained copy. Do not delete either ignored source workbook in this task.

- [ ] **Step 3: Replace non-portable source-tracker references**

Update the 55 marketing and 67 client rows in `pokrov-canonical-feature-tracker.csv` so `source_tracker` points at the matching tracked evidence workbook with repository-relative forward-slash paths. Update the source list in `pokrov-canonical-feature-tracker.md`. Do not change story text, status, test proof, or manual-gate meaning.

- [ ] **Step 4: Regenerate derived evidence**

Run in this order:

```powershell
python -B scripts/audit_story_test_evidence.py
python -B scripts/generate_defect_fix_retest_ledger.py
python -B scripts/generate_code_function_inventory.py --client-root C:/Users/kiwun/Documents/ai/POKROV-app
python -B scripts/generate_private_helper_coverage.py
```

Review every generated diff. Generated counts must come from current CSV/code, not hand-selected expected numbers.

- [ ] **Step 5: Synchronize human summaries and navigation**

Update the canonical tracker summary, completed WO current-output block, and completion audit to the generated values. Restore explicit repository-map links for every artifact named by `NAVIGATION_ARTIFACTS` and `WORK_ORDER_NAVIGATION_ARTIFACTS` in `tests/test_story_test_evidence_audit.py`. Preserve historical dated result rows as historical evidence rather than rewriting old run results.

- [ ] **Step 6: Run the green task gate**

```powershell
python -B -m pytest -p no:cacheprovider tests\test_story_test_evidence_audit.py tests\test_code_function_inventory.py tests\test_pokrov_migration_defaults.py tests\test_check_script_manifest.py -q
git diff --check
```

Expected: all tests pass and `git diff --check` exits `0`.

- [ ] **Step 7: Commit the scoped task**

Stage only the source-workbook evidence, tracker/ledger outputs, navigation, and completed-WO summary files. Commit with message `docs: make audit ledgers reproducible`.

---

### Task 2: Registry Reconciliation And Historical Closure

**Files:**
- Modify: `docs/README.md`
- Modify: current canonical/operation documents named by a `PENDING_*` registry row only when evidence proves an actual stale statement
- Move or modify: `docs/superpowers/plans/2026-07-10-pokrov-codex-docs-renewal-roadmap.md`
- Move or modify: `docs/superpowers/specs/2026-07-10-agent-context-refactor-design.md`
- Modify link owners that point to either moved file
- Test: `tests/test_agent_docs_contract.py`
- Test: `tests/test_agent_context_packet_audit.py`
- Test: `tests/test_pokrov_migration_defaults.py`

**Interfaces:**
- Consumes: current `master` canon, the clean `POKROV-app/main` documentation contract, and read-only branch/worktree state for concurrent unmerged work.
- Produces: registry review states that distinguish completed reconciliation from future concurrent work; completed context-refactor plans no longer present themselves as active/unexecuted.

- [ ] **Step 1: Audit each pending row against current authority**

For every `PENDING_WAVE_2`, `PENDING_WAVE_3`, `PENDING_CLIENT_REVIEW`, and `PENDING_COLLISION_REVIEW` row, inspect its named document, current code/tests, and active client owner where relevant. Change a row to `RECONCILED` only when the current tracked candidate supports that conclusion. Leave work owned by an unmerged concurrent branch pending and add concise scope wording if the reason is otherwise unclear.

- [ ] **Step 2: Reconcile the client pointers**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File C:/Users/kiwun/Documents/ai/POKROV-app/test/docs-contract.ps1
powershell -ExecutionPolicy Bypass -File C:/Users/kiwun/Documents/ai/POKROV-app/scripts/validate-seed.ps1
```

If both pass and the scoped client docs diff is empty, mark the two client pointer rows `RECONCILED`. Do not convert manual device/signing/store/WARP gates into `PASS`.

- [ ] **Step 3: Close completed context-refactor planning material**

The July 10 roadmap must no longer claim that canon refresh or promotion never ran. The context-refactor design must no longer say `ACTIVE_EXECUTION ... pending owner review` after the owner-approved implementation. Prefer moving completed material into the already classified `docs/archive/superpowers-plans/` family with link updates; if a move would break a retained evidence contract, use an explicit implemented/historical header instead.

- [ ] **Step 4: Run documentation contracts**

```powershell
python -B -m pytest -p no:cacheprovider tests\test_agent_docs_contract.py tests\test_agent_context_packet_audit.py tests\test_pokrov_migration_defaults.py -q
python -B scripts/agent_context_packet_audit.py --platform-context-root .
python -B scripts/check-links.py
git diff --check
```

Expected: all tests/checks pass. `check-links.py` may refresh its canonical report only if the script contract requires it; review that diff as evidence, never as product canon.

- [ ] **Step 5: Commit the scoped task**

Stage only registry/canonical/history/link changes owned by this task. Commit with message `docs: close context renewal review states`.

---

### Task 3: Safe Cleanup, Final Review, And Handoff

**Files:**
- Move: `docs/superpowers/plans/2026-07-14-docs-finalization.md` to `docs/archive/superpowers-plans/2026-07-14-docs-finalization.md`
- Modify only links required by that move
- Delete: exact disposable cache/scratch paths inside `C:/Users/kiwun/Documents/ai/VPN-docs-finalization` after resolved-path verification

**Interfaces:**
- Consumes: reviewed commits from Tasks 1 and 2.
- Produces: a clean isolated worktree, archived completion plan, full verification evidence, and an integration-ready branch.

- [ ] **Step 1: Inventory without applying**

```powershell
python -B scripts/cleanup_inventory.py --dry-run --format json --root .
```

Classify every candidate. Never clean another worktree, the active root checkout, `.content-video-ad`, `.git`, evidence, release artifacts, secrets, `ops-local`, or retained workbook provenance.

- [ ] **Step 2: Remove only exact worktree-local disposable output**

Resolve each selected absolute path, prove it remains under `C:/Users/kiwun/Documents/ai/VPN-docs-finalization`, and remove only generated caches, scratch, test databases, or build outputs named by the dry-run inventory. Do not invoke `--apply` and do not delete the worktree itself.

- [ ] **Step 3: Archive this completed plan**

Move this plan into `docs/archive/superpowers-plans/`, update required links, and preserve it as historical execution evidence rather than an active reading route.

- [ ] **Step 4: Run the full documentation/evidence gate**

```powershell
python -B -m pytest -p no:cacheprovider tests\test_agent_docs_contract.py tests\test_agent_context_packet_audit.py tests\test_story_test_evidence_audit.py tests\test_code_function_inventory.py tests\test_pokrov_migration_defaults.py tests\test_check_script_manifest.py tests\test_cleanup_inventory.py -q
python -B scripts/agent_context_packet_audit.py --platform-context-root .
python -B scripts/check-links.py
powershell -ExecutionPolicy Bypass -File C:/Users/kiwun/Documents/ai/POKROV-app/test/docs-contract.ps1
powershell -ExecutionPolicy Bypass -File C:/Users/kiwun/Documents/ai/POKROV-app/scripts/validate-seed.ps1
git diff --check
git status --short --branch
```

Expected: all automated checks pass; any manual release/device/provider gates remain explicitly manual or blocked.

- [ ] **Step 5: Commit and hand off**

Commit the plan archive/link changes with message `docs: finalize repository context renewal`. Do not push, deploy, delete other branches/worktrees, or fast-forward `master` until the final independent review is clean and the root checkout is safe for integration.
