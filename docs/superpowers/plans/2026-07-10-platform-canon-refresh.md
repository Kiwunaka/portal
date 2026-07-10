# Platform Canonical Documentation Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reconcile every important active platform contract with current code/tests/shared facts, give each domain one owner, and reclassify old plans/evidence/history without rewriting the past.

**Architecture:** Run collision/snapshot gates first, then correct high-confidence current facts, consolidate domain owners, clean operations/design boundaries, and finish with one registry-backed consistency epoch. Developer-guide/repository-map changes belong to the orchestration plan, not this plan.

**Tech Stack:** Markdown, JSON, existing Python/pytest guardrails, `scripts/check-links.py`, Git moves for explicitly approved archive transitions.

## Global Constraints

- Start only after account-foundation is committed and the docs branch is replayed onto that baseline.
- Run cleanup-plan Stage A before editing any path that overlaps stale worktrees.
- Do not edit `docs/developer/developer-guide.md` or `docs/developer/repository-map.md` here.
- Current beta: `1.0.0-beta`; target candidate: `1.0.0-rc.1`; stable `1.0.0`: not proven.
- Current economics remain five trial days plus ten Telegram days until implemented migration evidence changes them.
- Current smart-connect contract is shortlist eight and 20% stickiness unless the landed implementation changes it.
- `adminapp` is primary operator write surface; web admin is parity fallback.
- `mini` is probe/sandbox plus opt-in emergency bridge, never normal delivery/control plane.
- SEO/search-intent surfaces may use visible `VPN`/`ВПН`; normal shared copy remains stricter.
- Lava.top beta checkout does not prove stable refund/chargeback/reconciliation maturity.
- Ad filtering remains `UNRESOLVED_OWNER_DECISION`; do not normalize code or canon here.
- Do not modify contents of `docs/audit-artifacts/**`, completed WO evidence, generated design assets, release artifacts, `ops-local/**`, or `reference-atlas/**`.
- Archive moves preserve content; only links/classification/pointer text changes.
- No new dependency, service, database, vector index, or documentation generator.

---

## Domain Owners After This Plan

| Domain | Owner |
| --- | --- |
| product identity/economics/current availability | `docs/product/portal-vpn-product.md` plus machine-readable shared facts |
| payments/access | `docs/product/payment-and-access-key-contract.md` and `docs/architecture/payment-state-machine.md` |
| current beta limitations | `shared/beta-known-limitations.json` mirrored by product limitations and launch known issues |
| component/data ownership | `docs/architecture/system-overview.md` |
| identity/trial/bonus/pools | `docs/architecture/app-first-and-bonus-flows.md` |
| API domain navigation | `docs/architecture/api-contracts.md` |
| downloads/update content | `docs/architecture/client-downloads-flow.md` plus operations delivery plan |
| support/feedback/runtime AI | `docs/architecture/support-feedback-flow.md` |
| deployment/access | `docs/operations/deployment-and-access.md` |
| monitoring/origins | `docs/operations/monitoring-and-visibility.md` |
| publishing/signing/artifact metadata | `docs/operations/publishing-and-signing-guide.md` |
| design | root `DESIGN.md` plus shared token JSON/schema |
| generated asset policy | `docs/design/generated-assets-policy.md` |
| current user guidance | `docs/user/portal-vpn-user-guide-ru.md` |

---

### Task 1: Run Collision And Current-Truth Gate

**Files:**
- Read: active platform integration diff
- Read: stale platform worktree snapshots
- Read: current platform/client registry and config facts
- Modify: none

**Interfaces:**
- Consumes: cleanup Stage A and landed account-foundation commit
- Produces: go/no-go decision for every planned write path

- [ ] **Step 1: Verify active work is committed**

```powershell
git -C ..\market-ready-cis-integration status --short
git -C ..\market-ready-cis-integration log -1 --oneline
git status --short --branch
```

Expected: integration worktree clean; its account-foundation commit is present
in the current baseline. Otherwise stop.

- [ ] **Step 2: Compare stale snapshots with the planned write set**

Review saved tracked/untracked patches from:

- `premium-bank-app-portal`;
- `release-hardening-platform`.

For each overlapping file, classify the dirty change as:

```text
replay_current
retain_history_only
already_landed
superseded_with_evidence
unresolved
```

Any `unresolved` path blocks its task.

- [ ] **Step 3: Confirm current machine-readable facts**

```powershell
python -m pytest tests/test_shared_surface_facts.py tests/test_pokrov_migration_defaults.py -q
git diff --check
```

Expected: baseline tests pass before canon edits.

### Task 2: Add Failing Known-Drift Assertions

**Files:**
- Modify: `tests/test_agent_docs_contract.py`

**Interfaces:**
- Consumes: current registry test
- Produces: executable checks for high-confidence stale claims

- [ ] **Step 1: Add the current-canon test**

Append:

```python
def test_active_platform_canon_has_no_known_stale_claims() -> None:
    active_paths = (
        "docs/product/portal-vpn-product.md",
        "docs/product/beta-known-limitations.md",
        "docs/architecture/api-contracts.md",
        "docs/architecture/payment-state-machine.md",
        "docs/operations/publishing-and-signing-guide.md",
        "docs/design/design-system-sync.md",
        "docs/launch/known-issues.md",
        "docs/launch/open-source-client-rollout-plan.md",
        "docs/user/portal-vpn-user-guide-ru.md",
    )
    combined = "\n".join(
        (REPO_ROOT / path).read_text(encoding="utf-8")
        for path in active_paths
    )
    for stale in (
        "webapp is also the primary admin operator surface",
        "web admin is the primary operator surface",
        "0.x.x-beta",
        "avoids direct public `VPN` wording",
        "release repository remains private",
        "up to `5` eligible non-free nodes",
        "`15%` stickiness threshold",
        "must not enable public paid checkout",
    ):
        assert stale.casefold() not in combined.casefold()

    product = (
        REPO_ROOT / "docs" / "product" / "portal-vpn-product.md"
    ).read_text(encoding="utf-8")
    assert "up to `8`" in product
    assert "`20%` stickiness" in product
    assert "`adminapp`" in product


def test_beta_limitations_use_public_release_truth() -> None:
    import json

    payload = json.loads(
        (REPO_ROOT / "shared" / "beta-known-limitations.json").read_text(
            encoding="utf-8"
        )
    )
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "release repository remains private" not in serialized
    assert "GitHub Releases" in serialized
    assert set(payload["source_docs"]) == {
        "docs/product/beta-known-limitations.md",
        "docs/launch/known-issues.md",
    }
```

- [ ] **Step 2: Run RED**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py -q
```

Expected: failures on version/admin/smart-connect/payment/VPN/download claims.

### Task 3: Reconcile High-Confidence Current Facts

**Files:**
- Modify: `shared/beta-known-limitations.json`
- Modify: `docs/product/beta-known-limitations.md`
- Modify: `docs/launch/known-issues.md`
- Modify: `docs/product/portal-vpn-product.md`
- Modify: `docs/architecture/api-contracts.md`
- Modify: `docs/architecture/payment-state-machine.md`
- Modify: `docs/operations/publishing-and-signing-guide.md`
- Modify: `docs/design/design-system-sync.md`
- Modify: `docs/launch/open-source-client-rollout-plan.md`
- Modify: `docs/user/portal-vpn-user-guide-ru.md`
- Modify: `docs/README.md`
- Test: `tests/test_agent_docs_contract.py`

**Interfaces:**
- Consumes: landed code/tests/shared facts and current client release seed
- Produces: consistent current beta/admin/smart-connect/payment/wording truth

- [ ] **Step 1: Fix the structured limitation owner**

Set:

```json
"version": "2026-07-10",
"source_docs": [
  "docs/product/beta-known-limitations.md",
  "docs/launch/known-issues.md"
]
```

Replace the private-repository note with:

```json
{
  "id": "downloads_limited",
  "severity": "release_check",
  "summary": "Published beta binaries are publicly reachable through the official cabinet and GitHub Releases, but every new candidate still requires exact URL and runtime handoff verification.",
  "operator_note": "Do not claim store availability or a newly published candidate without current unauthenticated URL, /api/client/apps, and manual install/connect evidence."
}
```

Mirror the same boundary in product limitations and launch known issues.
`open-beta-release-notes.md` is no longer a structured-source mirror; classify
it as `EVIDENCE` and do not rewrite its dated release narrative.

- [ ] **Step 2: Fix product/admin/version/smart-connect truth**

In `portal-vpn-product.md`:

- replace webapp-primary-admin with standalone `adminapp` primary and
  `webapp/src/app/(admin)/admin/` fallback;
- set current distributed beta line to `1.0.0-beta`;
- describe `1.0.0-rc.1` as target candidate and stable `1.0.0` as unproven;
- change smart shortlist from five to eight;
- change stickiness from 15% to 20%;
- preserve current five-day trial and ten-day Telegram reward;
- retain the scoped visible SEO/search-intent `VPN`/`ВПН` allowance.

Apply the same current beta line to:

- `publishing-and-signing-guide.md`;
- `open-source-client-rollout-plan.md`;
- `portal-vpn-user-guide-ru.md`.

- [ ] **Step 3: Fix architecture and payment boundaries**

In `api-contracts.md`, state that `adminapp` is primary and legacy web admin
is parity fallback.

Replace the payment-state precondition with:

```markdown
Lava.top paid checkout is enabled for the current outside-store beta on the
retained evidence-backed path. Stable payment maturity remains unproven until
refund, chargeback, reconciliation, and fulfillment-ledger evidence is current
for the exact candidate.
```

Do not rewrite current `tg_id`/anonymous-email fulfillment into future
`account_id` ownership unless the landed account work actually changed it.

- [ ] **Step 4: Fix design wording scope**

Replace the design checklist's global direct-`VPN` prohibition with:

```markdown
- Public copy uses `POKROV` as the product line. Visible `VPN` / `ВПН`
  wording is allowed on approved SEO/search-intent surfaces; hidden text,
  cloaking, stuffing, unsupported “best”, store, stable, signing, device-audit,
  and RU-origin claims remain forbidden.
```

Classify the old growth/competitor note and Atlas material as reference/history
instead of changing historical prose to match the new policy.

- [ ] **Step 5: Update registry review states**

Mark only the files actually reconciled in this task `RECONCILED`. Mark
`open-beta-release-notes.md` `EVIDENCE`. Keep ad filtering
`UNRESOLVED_OWNER_DECISION`.

- [ ] **Step 6: Run focused tests**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_shared_surface_facts.py tests/test_public_copy_guardrails.py tests/test_frontend_text_integrity.py -q
python scripts/check-links.py
git diff --check
```

Expected: all checks pass and no historical/evidence content other than
explicit registry classification changed.

- [ ] **Step 7: Commit**

```powershell
git add shared/beta-known-limitations.json docs/product/beta-known-limitations.md docs/launch/known-issues.md docs/product/portal-vpn-product.md docs/architecture/api-contracts.md docs/architecture/payment-state-machine.md docs/operations/publishing-and-signing-guide.md docs/design/design-system-sync.md docs/launch/open-source-client-rollout-plan.md docs/user/portal-vpn-user-guide-ru.md docs/README.md tests/test_agent_docs_contract.py
git commit -m "docs: reconcile current beta and platform facts"
```

### Task 4: Consolidate Product And Architecture Owners

**Files:**
- Modify: `docs/README.md`
- Modify: `docs/product/portal-vpn-product.md`
- Modify: `docs/product/platform-availability.md` before move
- Move: `docs/product/platform-availability.md` to `docs/archive/flat-docs/platform-availability-2026-05-26.md`
- Reclassify only: `docs/product/public-beta-prd.md`
- Reclassify only: `docs/product/pokrov-growth-and-competitor-notes.md`
- Modify: `docs/architecture/api-contracts.md`
- Modify: `docs/archive/README.md`
- Modify: `scripts/pokrov_ai_docs_assistant.py`
- Modify: `tests/test_pokrov_ai_docs_assistant.py`

**Interfaces:**
- Consumes: reconciled current facts
- Produces: one product owner and concise architecture-domain index

- [ ] **Step 1: Merge unique current availability facts**

Copy only still-current platform availability facts into
`portal-vpn-product.md` or `beta-known-limitations.md`. Do not copy dated
release evidence or duplicate full status tables.

- [ ] **Step 2: Move the superseded availability snapshot**

```powershell
git mv docs/product/platform-availability.md docs/archive/flat-docs/platform-availability-2026-05-26.md
```

Update live links to the current product owner; archive/history links may point
to the moved snapshot.

Remove `docs/product/platform-availability.md` from
`DEFAULT_SOURCE_PATHS` in `scripts/pokrov_ai_docs_assistant.py`; the
experimental helper already includes `portal-vpn-product.md` and
`beta-known-limitations.md`. Add:

```python
def test_every_default_source_path_resolves() -> None:
    module = _load_module()
    assert all(
        (module.REPO_ROOT / relative_path).exists()
        for relative_path in module.DEFAULT_SOURCE_PATHS
    )
```

- [ ] **Step 3: Reclassify without rewriting evidence**

- `public-beta-prd.md`: `EVIDENCE`, retained 2026-05-15 beta decision
  baseline;
- `pokrov-growth-and-competitor-notes.md`: `HISTORICAL_REFERENCE`;
- `api-contracts.md`: short index linking identity, payments, downloads,
  support, admin, and client contract owners; it must not masquerade as a
  complete endpoint inventory.

- [ ] **Step 4: Record the historical retrieval boundary**

In `docs/archive/README.md`, define:

1. current registry and canonical docs first;
2. `rg`/`rg --files`;
3. Git log/search/blame;
4. targeted archive/work-order/audit/spec reads;
5. archive explains why but never decides current action.

State that no index is part of the current architecture. A separate future
benchmark may evaluate a local generated/ignored SQLite FTS/BM25 index with
repository, subsystem, class, date, `superseded_by`, work-order, and release
metadata. Embeddings may be evaluated only after a fixed historical-query
benchmark proves material lexical-search misses.

- [ ] **Step 5: Verify and commit**

```powershell
python scripts/check-links.py
python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_shared_surface_facts.py tests/test_pokrov_ai_docs_assistant.py -q
git diff --check
git add docs/README.md docs/product/portal-vpn-product.md docs/archive/README.md docs/archive/flat-docs/platform-availability-2026-05-26.md docs/architecture/api-contracts.md scripts/pokrov_ai_docs_assistant.py tests/test_pokrov_ai_docs_assistant.py
git commit -m "docs: assign product and architecture owners"
```

Expected: the old product path no longer exists, every link resolves, and
evidence/history contents are unchanged.

### Task 5: Separate Current Operations From Handoffs And History

**Files:**
- Modify: `docs/operations/deployment-and-access.md`
- Modify: `docs/operations/monitoring-and-visibility.md`
- Modify: `docs/operations/publishing-and-signing-guide.md`
- Modify: `docs/operations/client-delivery-update-content-plan.md`
- Modify: `docs/operations/public-beta-release-runbook.md`
- Reclassify only: `docs/operations/release-links-and-final-handoff.md`
- Reclassify only: `docs/operations/2026-06-06-plans-decisions-closure-audit.md`
- Reclassify only: current manual handoff files under `docs/operations/`
- Modify: `docs/README.md`
- Modify: `tests/test_agent_docs_contract.py`

**Interfaces:**
- Consumes: current release metadata owner in `POKROV-app`
- Produces: deployment/monitoring/publishing owners without legacy active commands

- [ ] **Step 1: Add failing active-operations assertions**

Append:

```python
def test_active_operations_use_current_client_release_path() -> None:
    active_paths = (
        "docs/operations/deployment-and-access.md",
        "docs/operations/monitoring-and-visibility.md",
        "docs/operations/publishing-and-signing-guide.md",
        "docs/operations/client-delivery-update-content-plan.md",
        "docs/operations/public-beta-release-runbook.md",
    )
    combined = "\n".join(
        (REPO_ROOT / path).read_text(encoding="utf-8")
        for path in active_paths
    )
    assert "external/client-fork/scripts/release_handoff.ps1" not in combined
    assert "external/client-fork/scripts/check_release_urls.py" not in combined
    assert "POKROV-app/artifacts/releases/pokrov-app/" in combined
    assert "stable 1.0.0 is not proven" in combined.casefold()
```

Run and expect RED on legacy bridge commands/current-path wording.

- [ ] **Step 2: Make deployment the deploy/access owner**

In `Active Client Release Path`:

- remove legacy bridge commands from the active procedure;
- point current release metadata to
  `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/`;
- link publishing/signing for artifact creation/signing/handoff;
- keep `external/client-fork/**` only in clearly labeled rollback/archive
  context;
- preserve current account-foundation runtime/deploy additions from the landed
  branch.

- [ ] **Step 3: Make monitoring the origin/telemetry owner**

Keep current-origin, brain-origin, and RU-origin distinct. Preserve
`mini` as probe/sandbox plus opt-in emergency bridge. Remove release-handoff
procedure duplication and link publishing/deployment owners.

- [ ] **Step 4: Make publishing the artifact/signing owner**

Own:

- current GitHub Releases public binary policy;
- current client release metadata root;
- signing/manual/store boundaries;
- exact candidate and handoff verification;
- beta `1.0.0-beta`, target RC, and unproven stable distinction.

Do not make dated handoffs current authority.

- [ ] **Step 5: Reduce delivery plan and classify handoffs**

In `client-delivery-update-content-plan.md`, keep current runtime contract,
remaining execution items, dynamic-content safety, and manual gates. Move
completed P0/P1/P4 narratives to links on retained evidence rather than
repeating them.

Classify:

- `public-beta-release-runbook.md`: `ACTIVE_EXECUTION`, beta only;
- `release-links-and-final-handoff.md`: `EVIDENCE`, retained in place to
  avoid rewriting linked handoff evidence;
- `2026-06-06-plans-decisions-closure-audit.md`: `EVIDENCE`;
- Android/signing/email/RU handoff docs: `ACTIVE_EXECUTION` when a manual gate
  remains open, otherwise `EVIDENCE`.

- [ ] **Step 6: Verify and commit**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_check_script_manifest.py tests/test_shared_surface_facts.py -q
python scripts/check-links.py
git diff --check
git add docs/operations/deployment-and-access.md docs/operations/monitoring-and-visibility.md docs/operations/publishing-and-signing-guide.md docs/operations/client-delivery-update-content-plan.md docs/operations/public-beta-release-runbook.md docs/README.md tests/test_agent_docs_contract.py
git commit -m "docs: separate current operations from release evidence"
```

Expected: active operations point only to current scripts/metadata; retained
handoff/evidence files have no content diff.

### Task 6: Normalize Design And Surface Ownership

**Files:**
- Modify: `DESIGN.md`
- Modify: `docs/design/design-system-sync.md`
- Modify: `docs/design/generated-assets-policy.md`
- Reclassify only: `docs/design/atlas-glass/**`
- Modify: `webapp/README.md`
- Modify: `adminapp/README.md`
- Modify: `marketing/README.md`
- Modify: `docs/README.md`
- Modify: `tests/test_agent_docs_contract.py`
- Do not modify: `docs/design/generated/**`
- Do not modify: `docs/design/assets/**`

**Interfaces:**
- Consumes: scoped wording and admin ownership from Task 3
- Produces: one current design owner and explicit surface boundaries

- [ ] **Step 1: Add design/surface assertions**

Append:

```python
def test_design_and_surface_docs_have_current_owners() -> None:
    design = (REPO_ROOT / "DESIGN.md").read_text(encoding="utf-8")
    sync = (
        REPO_ROOT / "docs" / "design" / "design-system-sync.md"
    ).read_text(encoding="utf-8")
    admin = (REPO_ROOT / "adminapp" / "README.md").read_text(encoding="utf-8")
    web = (REPO_ROOT / "webapp" / "README.md").read_text(encoding="utf-8")
    marketing = (REPO_ROOT / "marketing" / "README.md").read_text(encoding="utf-8")

    assert "Document class: CANONICAL" in design
    assert "SEO/search-intent" in sync
    assert "avoids direct public `VPN` wording" not in sync
    assert "primary operator" in admin.casefold()
    assert "parity fallback" in web.casefold()
    assert "acquisition" in marketing.casefold()
```

- [ ] **Step 2: Add explicit document classes**

- root `DESIGN.md`: `CANONICAL`, sole root design direction;
- generated-assets policy: `CANONICAL`;
- design-system sync: current sync checklist;
- Atlas Glass subtree: `HISTORICAL_REFERENCE` in the registry, retained in
  place;
- generated/assets trees: `EVIDENCE`, no content edits;
- `adminapp/README.md`: primary operator surface;
- `webapp/README.md`: cabinet plus retained admin parity fallback;
- `marketing/README.md`: acquisition/SEO/public copy surface.

- [ ] **Step 3: Verify and commit**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_admin_design_guardrails.py tests/test_frontend_text_integrity.py tests/test_public_copy_guardrails.py -q
python scripts/check-links.py
git diff --check
git diff --name-only -- docs/design/generated docs/design/assets
git add DESIGN.md docs/design/design-system-sync.md docs/design/generated-assets-policy.md webapp/README.md adminapp/README.md marketing/README.md docs/README.md tests/test_agent_docs_contract.py
git commit -m "docs: normalize design and surface ownership"
```

Expected: no generated/assets diff and all design/surface checks pass.

### Task 7: Run The Platform Canon Validation Epoch

**Files:**
- Verify only

- [ ] **Step 1: Run the complete focused suite**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_shared_surface_facts.py tests/test_pokrov_migration_defaults.py tests/test_check_script_manifest.py tests/test_public_copy_guardrails.py tests/test_frontend_text_integrity.py tests/test_admin_design_guardrails.py tests/test_pokrov_ai_docs_assistant.py -q
python scripts/check-links.py
git diff --check
```

- [ ] **Step 2: Run stale-active-text search**

```powershell
rg.exe -n "webapp/src/app/\(dashboard\)/admin/|release repository remains private|avoids direct public VPN wording|external/client-fork/scripts/release_handoff\.ps1|0\.x\.x-beta" docs/product docs/architecture docs/operations docs/design docs/launch docs/user DESIGN.md webapp/README.md adminapp/README.md marketing/README.md
```

Expected: no match in active canonical documents. Matches inside explicitly
classified evidence/history are reported, not rewritten.

- [ ] **Step 3: Confirm protected zones are unchanged**

```powershell
git diff --name-only -- docs/audit-artifacts docs/design/generated docs/design/assets docs/developer/work-orders reference-atlas ops-local
```

Expected: empty, except the active work-order continuity file committed by its
own neighboring task before this plan began.
