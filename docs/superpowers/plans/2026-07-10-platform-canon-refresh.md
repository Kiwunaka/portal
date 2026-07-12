# Platform Canonical Documentation Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reconcile every important active platform contract with current code/tests/shared facts, give each domain one owner, and reclassify old plans/evidence/history without rewriting the past.

**Architecture:** Run collision/snapshot gates first, then correct high-confidence current facts, consolidate domain owners, clean operations/design boundaries, and finish with one registry-backed consistency epoch. Developer-guide/repository-map changes belong to the orchestration plan, not this plan.

**Tech Stack:** Markdown, JSON, existing Python/pytest guardrails, `scripts/check-links.py`, Git moves for explicitly approved archive transitions.

## Execution Status — 2026-07-12

- Account foundation landed as `db00e1e`; local platform `master` reached that
  commit.
- The documentation branch replayed cleanly onto `db00e1e` through
  `8cec9ba`: all 27 documentation patches retained identical stable patch IDs.
- The platform-canon write set is no longer blocked by the former branch
  collision, but none of the canon tasks below has executed.
- Orchestration-plan Tasks 5 and 6 must finish before this plan's Task 2
  because both plans modify `tests/test_agent_docs_contract.py`.
- Cleanup Stage B/C, promotion, push, deploy, and every destructive cleanup
  action remain deferred and unauthorized by this plan.

## Global Constraints

- Start only after account-foundation is committed and the docs branch is replayed onto that baseline.
- Run cleanup-plan Stage A before editing any path that overlaps stale worktrees.
- Complete `2026-07-10-platform-docs-orchestration-renewal.md` Tasks 5 and 6
  before Task 2 here; do not interleave edits to
  `tests/test_agent_docs_contract.py`.
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
- Use `C:/Users/kiwun/Documents/ai/VPN/.venv/Scripts/python.exe` for every
  pytest command added or changed by this amendment; do not install packages.
- Do not deploy, push, promote, or run destructive cleanup from this plan.

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
git status --short --branch
git rev-parse --short master
git merge-base --is-ancestor db00e1e HEAD
git merge-base --is-ancestor 8cec9ba HEAD
git rev-list --count db00e1e..8cec9ba
```

Expected: the branch is `codex/agent-context-refactor`; local `master` is
`db00e1e`; both ancestry checks exit `0`; the replay count is `27`; the 27
replayed documentation patches retain their already reviewed identical stable
patch IDs. The amendment commit may follow `8cec9ba`; it does not change the
recorded replay count. Otherwise stop.

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
& 'C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe' -B -m pytest -p no:cacheprovider tests/test_shared_surface_facts.py tests/test_account_foundation.py -q
git diff --check
```

Expected: baseline shared/account tests pass before canon edits. The client
resolver suite intentionally starts in Task 1A because its current sibling
lookup is not worktree-safe.

### Task 1A: Make The Client Repository Resolver Worktree-Safe

**Files:**
- Modify: `tests/test_pokrov_migration_defaults.py`
- Test: `tests/test_pokrov_migration_defaults.py`

**Interfaces:**
- Consumes: the clean collision gate and the platform checkout's common Git directory
- Produces: one validated absolute `POKROV_APP_ROOT` from either an explicit override or the platform repository sibling

- [ ] **Step 1: Add failing resolver coverage**

Add `os`, `subprocess`, and `pytest` imports and append these tests. The
temporary override fixture uses the same marker set required by the resolver:

```python
def _write_client_repo_markers(root: Path) -> None:
    for relative_path in (
        "README.md",
        "melos.yaml",
        "config/product-contract.seed.json",
        "docs/README.md",
    ):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("test marker\n", encoding="utf-8")


def test_pokrov_app_repo_override_is_absolute_validated_and_skips_git(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    client_root = tmp_path / "client" / "POKROV-app"
    _write_client_repo_markers(client_root)
    override = client_root.parent / "unused" / ".." / client_root.name
    monkeypatch.setenv("POKROV_APP_REPO", str(override))

    def fail_git(*args: object, **kwargs: object) -> object:
        raise AssertionError("git must not run when POKROV_APP_REPO is present")

    monkeypatch.setattr(subprocess, "run", fail_git)
    assert _resolve_pokrov_app_repo(ROOT) == client_root.resolve()


@pytest.mark.parametrize("override", ["", " ", "\t"])
def test_pokrov_app_repo_present_blank_override_is_rejected_before_path_lookup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    override: str,
) -> None:
    valid_cwd = tmp_path / "cwd-with-client-markers"
    _write_client_repo_markers(valid_cwd)
    monkeypatch.chdir(valid_cwd)
    monkeypatch.setenv("POKROV_APP_REPO", override)

    def fail_git(*args: object, **kwargs: object) -> object:
        raise AssertionError("present POKROV_APP_REPO must not fall back to Git")

    monkeypatch.setattr(subprocess, "run", fail_git)
    with pytest.raises(
        AssertionError,
        match=r"POKROV_APP_REPO must be a non-blank path when present",
    ):
        _resolve_pokrov_app_repo(ROOT)


def test_pokrov_app_repo_resolves_from_root_and_linked_worktree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("POKROV_APP_REPO", raising=False)
    completed = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    platform_root = Path(completed.stdout.strip()).resolve().parent
    expected = (platform_root.parent / "POKROV-app").resolve()

    assert _resolve_pokrov_app_repo(platform_root) == expected
    assert _resolve_pokrov_app_repo(ROOT) == expected


def test_pokrov_app_repo_missing_sibling_has_useful_assertion(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("POKROV_APP_REPO", raising=False)
    platform_root = tmp_path / "workspace" / "VPN"
    platform_root.mkdir(parents=True)
    subprocess.run(
        ["git", "init", "--quiet"],
        cwd=platform_root,
        check=True,
        capture_output=True,
        text=True,
    )

    with pytest.raises(
        AssertionError,
        match=r"POKROV-app sibling repository is absent.*POKROV-app",
    ):
        _resolve_pokrov_app_repo(platform_root)
```

- [ ] **Step 2: Run RED**

```powershell
& 'C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe' -B -m pytest -p no:cacheprovider tests/test_pokrov_migration_defaults.py tests/test_shared_surface_facts.py tests/test_account_foundation.py -q
```

Expected: FAIL because `_resolve_pokrov_app_repo` is not defined and the old
`ROOT.parent / "POKROV-app"` lookup cannot resolve the sibling from
`.worktrees/**`.

- [ ] **Step 3: Implement the bounded resolver in the test contract**

Replace the static `POKROV_APP_ROOT` assignment with this helper and keep every
client read routed through the resulting constant:

```python
CLIENT_REPO_MARKERS = (
    "README.md",
    "melos.yaml",
    "config/product-contract.seed.json",
    "docs/README.md",
)


def _validated_client_repo(candidate: Path, *, source: str) -> Path:
    resolved = candidate.expanduser().resolve()
    assert resolved.is_dir(), f"POKROV-app {source} repository is absent at {resolved}"
    missing = [
        marker for marker in CLIENT_REPO_MARKERS
        if not (resolved / marker).exists()
    ]
    assert not missing, (
        f"POKROV-app {source} repository at {resolved} is missing markers: "
        + ", ".join(missing)
    )
    return resolved


def _resolve_pokrov_app_repo(platform_checkout: Path = ROOT) -> Path:
    if "POKROV_APP_REPO" in os.environ:
        override = os.environ["POKROV_APP_REPO"]
        assert override.strip(), (
            "POKROV_APP_REPO must be a non-blank path when present"
        )
        return _validated_client_repo(
            Path(override),
            source="override",
        )

    completed = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=platform_checkout,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, (
        "cannot resolve the platform common Git directory from "
        f"{platform_checkout.resolve()}: {completed.stderr.strip()}"
    )
    common_git_dir = Path(completed.stdout.strip()).resolve()
    assert common_git_dir.name == ".git" and (common_git_dir / "HEAD").exists(), (
        f"unexpected platform common Git directory: {common_git_dir}"
    )
    platform_repo_root = common_git_dir.parent
    sibling = platform_repo_root.parent / "POKROV-app"
    assert sibling.is_dir(), (
        f"POKROV-app sibling repository is absent at {sibling.resolve()}"
    )
    return _validated_client_repo(sibling, source="sibling")


POKROV_APP_ROOT = _resolve_pokrov_app_repo()
```

- [ ] **Step 4: Run GREEN**

```powershell
& 'C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe' -B -m pytest -p no:cacheprovider tests/test_pokrov_migration_defaults.py tests/test_shared_surface_facts.py tests/test_account_foundation.py -q
```

Expected: PASS from the linked worktree; every present non-blank explicit
override is resolved and marker-validated without falling back to Git; blank
or whitespace-only values fail before `Path` conversion even when the current
directory has valid client markers; the root checkout and `.worktrees/**`
resolve the same sibling; and the absent sibling case exposes its absolute
expected path.

- [ ] **Step 5: Check and commit the isolated resolver change**

```powershell
git diff --check
git add tests/test_pokrov_migration_defaults.py
git commit -m "test: resolve client repo from platform common git dir"
```

Expected: the commit contains only `tests/test_pokrov_migration_defaults.py`.

### Task 2: Add Failing Known-Drift Assertions

**Files:**
- Modify: `tests/test_agent_docs_contract.py`
- Modify: `tests/test_beta_known_limitations_contract.py`

**Interfaces:**
- Consumes: current registry test
- Produces: executable checks for high-confidence stale claims and the exact live limitation mirrors

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


def test_account_foundation_owners_preserve_dual_identity_truth() -> None:
    owner_paths = (
        "docs/product/portal-vpn-product.md",
        "docs/product/payment-and-access-key-contract.md",
        "docs/architecture/api-contracts.md",
        "docs/architecture/payment-state-machine.md",
    )
    required = (
        "UUID `accounts.id`",
        "`users.account_id` is a nullable projection",
        "public numeric `account_id`",
        "stateless bearer",
        "Production deployment of account foundation is not proven",
        "Rotating sessions",
        "recovery exchange",
        "entitlement-ledger authority",
        "must not be claimed",
    )
    for relative_path in owner_paths:
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        for phrase in required:
            assert phrase.casefold() in text.casefold(), (
                f"{relative_path} is missing account boundary: {phrase}"
            )
```

- [ ] **Step 2: Derive limitation mirrors from the structured owner**

In `tests/test_beta_known_limitations_contract.py`, add this constant/helper
and replace the hard-coded three-document mirror loop with the shown test:

```python
EXPECTED_LIVE_MIRRORS = {
    "docs/product/beta-known-limitations.md",
    "docs/launch/known-issues.md",
}


def _live_mirror_paths(payload: dict) -> tuple[Path, ...]:
    source_docs = payload["source_docs"]
    assert set(source_docs) == EXPECTED_LIVE_MIRRORS
    return tuple(ROOT / relative_path for relative_path in source_docs)


def test_beta_known_limitations_are_mirrored_in_live_source_docs() -> None:
    payload = _contract()
    doc_paths = _live_mirror_paths(payload)

    missing: list[str] = []
    for path in doc_paths:
        text = path.read_text(encoding="utf-8")
        if "shared/beta-known-limitations.json" not in text:
            missing.append(f"{path.relative_to(ROOT)} missing shared contract reference")
        for limitation_id in EXPECTED_IDS:
            if f"`{limitation_id}`" not in text:
                missing.append(f"{path.relative_to(ROOT)} missing `{limitation_id}`")

    assert not missing, "\n".join(missing)
```

In `test_beta_known_limitations_preserve_claim_boundaries()`, replace the
hard-coded path list with:

```python
payload = _contract()
combined = "\n".join(
    path.read_text(encoding="utf-8")
    for path in (CONTRACT, *_live_mirror_paths(payload))
)
```

Do not include `docs/launch/open-beta-release-notes.md`: it remains unchanged
dated `EVIDENCE`, not a live mirror.

- [ ] **Step 3: Run RED**

```powershell
& 'C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe' -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_beta_known_limitations_contract.py -q
```

Expected: failures on version/admin/smart-connect/payment/VPN/download claims.

### Task 3: Reconcile High-Confidence Current Facts

**Files:**
- Modify: `shared/beta-known-limitations.json`
- Modify: `docs/product/beta-known-limitations.md`
- Modify: `docs/product/payment-and-access-key-contract.md`
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
- Test: `tests/test_beta_known_limitations_contract.py`
- Read only: `docs/architecture/system-overview.md`
- Read only: `docs/architecture/app-first-and-bonus-flows.md`
- Read only: `portal_bot/account_foundation_service.py`
- Read only: `tests/test_account_foundation.py`

**Interfaces:**
- Consumes: landed code/tests/shared facts, current client release seed, and the replayed account-foundation truth
- Produces: consistent current beta/admin/smart-connect/payment/wording truth without overstating the additive identity foundation

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

- [ ] **Step 3: Re-read landed account truth, then fix architecture and payment boundaries**

Before editing product/API/payment owners, read but do not modify:

```text
docs/architecture/system-overview.md
docs/architecture/app-first-and-bonus-flows.md
portal_bot/account_foundation_service.py
tests/test_account_foundation.py
```

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

Add this dual-identity boundary to `portal-vpn-product.md`,
`payment-and-access-key-contract.md`, `api-contracts.md`, and
`payment-state-machine.md`, adapting only surrounding headings:

```markdown
The repository now implements additive account foundation: UUID
`accounts.id` is persisted and `users.account_id` is a nullable projection.
The public numeric `account_id`, stateless bearer flow, payment fulfillment,
and entitlement authority remain on the legacy-compatible path. Production
deployment of account foundation is not proven. Rotating sessions, recovery
exchange, payment ownership cutover, and entitlement-ledger authority are not
implemented current truth and must not be claimed.
```

After the edits, require this read-only boundary:

```powershell
git diff --exit-code -- docs/architecture/system-overview.md docs/architecture/app-first-and-bonus-flows.md portal_bot/account_foundation_service.py tests/test_account_foundation.py
```

Expected: no diff in the four replayed account-foundation sources.

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
& 'C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe' -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_beta_known_limitations_contract.py tests/test_shared_surface_facts.py tests/test_public_copy_guardrails.py tests/test_frontend_text_integrity.py tests/test_account_foundation.py -q
& 'C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe' scripts/check-links.py
git diff --check
```

Expected: all checks pass and no historical/evidence content other than
explicit registry classification changed.

- [ ] **Step 7: Commit**

```powershell
git add shared/beta-known-limitations.json docs/product/beta-known-limitations.md docs/product/payment-and-access-key-contract.md docs/launch/known-issues.md docs/product/portal-vpn-product.md docs/architecture/api-contracts.md docs/architecture/payment-state-machine.md docs/operations/publishing-and-signing-guide.md docs/design/design-system-sync.md docs/launch/open-source-client-rollout-plan.md docs/user/portal-vpn-user-guide-ru.md docs/README.md tests/test_agent_docs_contract.py tests/test_beta_known_limitations_contract.py
git commit -m "docs: reconcile current beta and platform facts"
```

### Task 4: Consolidate Product And Architecture Owners

**Files:**
- Modify: `docs/README.md`
- Modify: `docs/product/portal-vpn-product.md`
- Modify: `docs/product/beta-known-limitations.md`
- Move only: `docs/product/platform-availability.md` to `docs/archive/flat-docs/platform-availability-2026-05-26.md`
- Reclassify only: `docs/product/public-beta-prd.md`
- Reclassify only: `docs/product/pokrov-growth-and-competitor-notes.md`
- Modify: `docs/architecture/api-contracts.md`
- Modify: `docs/archive/README.md`
- Modify: `scripts/pokrov_ai_docs_assistant.py`
- Modify: `tests/test_pokrov_ai_docs_assistant.py`
- Test: `tests/test_beta_known_limitations_contract.py`

**Interfaces:**
- Consumes: reconciled current facts
- Produces: one product owner and concise architecture-domain index

- [ ] **Step 1: Merge unique current availability facts**

Copy still-current product/availability facts into `portal-vpn-product.md` and
copy only still-current limitation boundaries into
`beta-known-limitations.md`. Do not copy dated release evidence or duplicate
full status tables.

- [ ] **Step 2: Move the superseded availability snapshot**

```powershell
git mv docs/product/platform-availability.md docs/archive/flat-docs/platform-availability-2026-05-26.md
$sourceBlob = git rev-parse 'HEAD:docs/product/platform-availability.md'
if ($LASTEXITCODE -ne 0 -or -not $sourceBlob) {
  throw 'platform availability source blob lookup failed'
}
$movedBlob = git hash-object docs/archive/flat-docs/platform-availability-2026-05-26.md
if ($LASTEXITCODE -ne 0 -or -not $movedBlob) {
  throw 'platform availability moved blob lookup failed'
}
if ($sourceBlob -ne $movedBlob) {
  throw 'platform availability archive must be a content-identical move'
}
```

Update live links to the current product owner; archive/history links may point
to the moved snapshot. Do not edit the moved snapshot before or after `git mv`.

Remove all four evidence/history paths from `DEFAULT_SOURCE_PATHS` in
`scripts/pokrov_ai_docs_assistant.py`:

```text
docs/product/platform-availability.md
docs/product/public-beta-prd.md
docs/developer/work-orders/2026-04-open-beta-v4/13-launch-decision.md
docs/launch/open-beta-release-notes.md
```

The experimental helper must retain the canonical current product and
limitations owners. Replace the inventory test and add the resolution/default
authority tests with:

```python
def test_inventory_uses_allowlisted_canonical_sources_only() -> None:
    module = _load_module()

    inventory = module.build_inventory()
    paths = {source["path"] for source in inventory["sources"]}

    assert "AGENTS.md" in paths
    assert "docs/product/portal-vpn-product.md" in paths
    assert "docs/product/beta-known-limitations.md" in paths
    assert "docs/launch/known-issues.md" in paths
    assert {
        "docs/product/platform-availability.md",
        "docs/product/public-beta-prd.md",
        "docs/developer/work-orders/2026-04-open-beta-v4/13-launch-decision.md",
        "docs/launch/open-beta-release-notes.md",
    }.isdisjoint(paths)
    assert "portal_bot/.env" not in paths
    assert not any(path.startswith("ops-local/") for path in paths)
    assert not any("VPN NODE SSH KEYS" in path for path in paths)
    assert inventory["source_count"] == len(paths)
    assert inventory["total_bytes"] > 0


def test_every_default_source_path_resolves() -> None:
    module = _load_module()
    assert all(
        (module.REPO_ROOT / relative_path).exists()
        for relative_path in module.DEFAULT_SOURCE_PATHS
    )


def test_default_sources_keep_current_owners_and_exclude_dated_evidence() -> None:
    module = _load_module()
    paths = set(module.DEFAULT_SOURCE_PATHS)

    assert {
        "docs/product/portal-vpn-product.md",
        "docs/product/beta-known-limitations.md",
        "docs/launch/known-issues.md",
    } <= paths
    assert paths.isdisjoint(
        {
            "docs/product/platform-availability.md",
            "docs/product/public-beta-prd.md",
            "docs/developer/work-orders/2026-04-open-beta-v4/13-launch-decision.md",
            "docs/launch/open-beta-release-notes.md",
        }
    )
```

Align `OPENAI_INSTRUCTIONS` with the approved public wording boundary:

```text
- Visible `VPN` / `ВПН` wording is allowed on dedicated SEO/search-intent
  surfaces when it is useful to users and tied to the real POKROV app flow.
  Hidden text, cloaking, keyword stuffing, unsupported “best” claims, and
  unsupported release, payment, or store claims remain forbidden.
```

Replace the wording-specific assertions in
`test_openai_instructions_preserve_release_and_secret_boundaries()` with:

```python
for required in (
    "SEO/search-intent",
    "VPN",
    "ВПН",
    "Hidden text",
    "cloaking",
    "keyword stuffing",
    "unsupported release, payment, or store claims",
):
    assert required in instructions
assert "direct-meaning public" not in instructions
```

Keep the existing release/secret assertions.

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

This plan neither creates nor authorizes that future benchmark or any index;
it would require a separate owner-approved plan.

- [ ] **Step 5: Verify and commit**

```powershell
& 'C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe' scripts/check-links.py
& 'C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe' -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_beta_known_limitations_contract.py tests/test_shared_surface_facts.py tests/test_pokrov_ai_docs_assistant.py -q
git diff --check
git add docs/README.md docs/product/portal-vpn-product.md docs/product/beta-known-limitations.md docs/archive/README.md docs/archive/flat-docs/platform-availability-2026-05-26.md docs/architecture/api-contracts.md scripts/pokrov_ai_docs_assistant.py tests/test_pokrov_ai_docs_assistant.py
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
- Modify: `docs/operations/android-production-signing-handoff.md`
- Reclassify only: `docs/operations/release-links-and-final-handoff.md`
- Reclassify only: `docs/operations/2026-06-06-plans-decisions-closure-audit.md`
- Reclassify only: `docs/operations/android-physical-device-audit-handoff.md`
- Reclassify only: `docs/operations/email-delivery-webhook-handoff.md`
- Reclassify only: `docs/operations/ru-origin-probe-handoff.md`
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
        "docs/operations/android-production-signing-handoff.md",
    )
    combined = "\n".join(
        (REPO_ROOT / path).read_text(encoding="utf-8")
        for path in active_paths
    )
    assert "external/client-fork/scripts/release_handoff.ps1" not in combined
    assert "external/client-fork/scripts/check_release_urls.py" not in combined
    assert "pokrov-android-universal.apk" not in combined
    assert "pokrov-android-arm64-v8a.apk" in combined
    assert "pokrov-android-armeabi-v7a.apk" in combined
    assert "POKROV-app/artifacts/releases/pokrov-app/" in combined
    assert "stable 1.0.0 is not proven" in combined.casefold()
```

Run:

```powershell
& 'C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe' -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py::test_active_operations_use_current_client_release_path -q
```

Expected: FAIL because active deployment/publishing documentation still names
the retired `external/client-fork/scripts/release_handoff.ps1` and
`check_release_urls.py` commands, and active deployment, publishing, and
`android-production-signing-handoff.md` still contain
`pokrov-android-universal.apk`. The split-ARM presence assertions may already
pass through the delivery plan; RED is specifically the stale active authority
and retired-command boundary.

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
- `pokrov-android-arm64-v8a.apk` as the default Android download and
  `pokrov-android-armeabi-v7a.apk` as the legacy ARMv7 variant;
- current client release metadata root;
- signing/manual/store boundaries;
- exact candidate and handoff verification;
- beta `1.0.0-beta`, target RC, and unproven stable distinction.

Remove every active reference to `pokrov-android-universal.apk` and the retired
`external/client-fork` release-handoff/check-URL commands. Do not make dated
handoffs current authority.

In `android-production-signing-handoff.md`, replace the universal-APK artifact
entry with both exact direct-download artifacts:

```text
pokrov-android-arm64-v8a.apk = default Android APK
pokrov-android-armeabi-v7a.apk = legacy ARMv7 APK
pokrov-android-market.aab = market handoff only; no store availability claim
```

Keep the signing/manual/store gates unchanged; this content edit corrects the
active artifact names and does not claim that production signing is complete.

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
- `android-production-signing-handoff.md`: `ACTIVE_EXECUTION`;
- `android-physical-device-audit-handoff.md`: `ACTIVE_EXECUTION`;
- `ru-origin-probe-handoff.md`: `ACTIVE_EXECUTION`;
- `email-delivery-webhook-handoff.md`: `EVIDENCE`.

Give every listed path its own `docs/README.md` row. Delete the wildcard row
for `docs/operations/*-handoff.md`; no wildcard may assign one class to every
handoff. Preserve `current-origin`, `brain-origin`, and `RU-origin` as three
separate terms and preserve `mini` as an opt-in emergency bridge only.

- [ ] **Step 6: Verify and commit**

```powershell
& 'C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe' -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_check_script_manifest.py tests/test_shared_surface_facts.py -q
& 'C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe' scripts/check-links.py
git diff --check
git add docs/operations/deployment-and-access.md docs/operations/monitoring-and-visibility.md docs/operations/publishing-and-signing-guide.md docs/operations/client-delivery-update-content-plan.md docs/operations/public-beta-release-runbook.md docs/operations/android-production-signing-handoff.md docs/README.md tests/test_agent_docs_contract.py
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
    generated_policy = (
        REPO_ROOT / "docs" / "design" / "generated-assets-policy.md"
    ).read_text(encoding="utf-8")
    admin = (REPO_ROOT / "adminapp" / "README.md").read_text(encoding="utf-8")
    web = (REPO_ROOT / "webapp" / "README.md").read_text(encoding="utf-8")
    marketing = (REPO_ROOT / "marketing" / "README.md").read_text(encoding="utf-8")

    assert "Document class: CANONICAL" in design
    assert "retained history" in design.casefold()
    assert "SEO/search-intent" in design
    assert "SEO/search-intent" in sync
    assert "avoids direct public `VPN` wording" not in sync
    assert "SEO/search-intent" in generated_policy
    assert "legacy public `VPN` product wording outside unavoidable" not in generated_policy
    assert "primary operator" in admin.casefold()
    assert "parity fallback" in web.casefold()
    assert "acquisition" in marketing.casefold()
    assert "docs/archive/design-plans/2026-06-06-web-admin-site-density-plan.md" in marketing
    assert "docs/design/2026-06-06-web-admin-site-density-plan.md" not in marketing


def test_surface_readme_repo_doc_pointers_resolve() -> None:
    import re

    for source_path in (
        "adminapp/README.md",
        "webapp/README.md",
        "marketing/README.md",
    ):
        text = (REPO_ROOT / source_path).read_text(encoding="utf-8")
        pointers = re.findall(
            r"`((?:docs|shared)/[^`\s]+(?:\.md|\.json))`",
            text,
        )
        for pointer in pointers:
            assert (REPO_ROOT / pointer).exists(), (
                f"{source_path} points to missing repository file {pointer}"
            )
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

Apply this scoped wording boundary in both `DESIGN.md` and
`docs/design/generated-assets-policy.md` (and keep the matching sync checklist):

```markdown
Visible `VPN` / `ВПН` wording is allowed on dedicated SEO/search-intent
surfaces when it is useful to users and tied to the real POKROV app flow.
Hidden text, cloaking, keyword stuffing, unsupported “best” claims, and
unsupported release, payment, store, signing, device-audit, or RU-origin
claims remain forbidden.
```

In `DESIGN.md`, label
`docs/superpowers/specs/2026-07-04-design-foundation-redesign-design.md` as a
retained historical redesign spec, not current authority. In
`marketing/README.md`, replace the nonexistent
`docs/design/2026-06-06-web-admin-site-density-plan.md` pointer with
`docs/archive/design-plans/2026-06-06-web-admin-site-density-plan.md` and label
it retained guidance.

- [ ] **Step 3: Make registry rows path-exact**

Remove broad rows where an exact path below replaces them. Require these
explicit `docs/README.md` rows and review states:

| Class | Document | Review state |
| --- | --- | --- |
| `CANONICAL` | `docs/product/beta-known-limitations.md` | `RECONCILED` |
| `CANONICAL` | `docs/launch/known-issues.md` | `RECONCILED` |
| `EVIDENCE` | `docs/launch/open-beta-release-notes.md` | `REVIEWED_NO_CHANGE` |
| `EVIDENCE` | `docs/product/public-beta-prd.md` | `REVIEWED_NO_CHANGE` |
| `HISTORICAL_REFERENCE` | `docs/archive/flat-docs/platform-availability-2026-05-26.md` | `RECONCILED` |
| `ACTIVE_EXECUTION` | `docs/operations/android-production-signing-handoff.md` | `RECONCILED` |
| `ACTIVE_EXECUTION` | `docs/operations/android-physical-device-audit-handoff.md` | `RECONCILED` |
| `ACTIVE_EXECUTION` | `docs/operations/ru-origin-probe-handoff.md` | `RECONCILED` |
| `EVIDENCE` | `docs/operations/email-delivery-webhook-handoff.md` | `REVIEWED_NO_CHANGE` |
| `EVIDENCE` | `docs/operations/release-links-and-final-handoff.md` | `REVIEWED_NO_CHANGE` |
| `EVIDENCE` | `docs/operations/2026-06-06-plans-decisions-closure-audit.md` | `REVIEWED_NO_CHANGE` |
| `HISTORICAL_REFERENCE` | `docs/design/atlas-glass/` | `REVIEWED_NO_CHANGE` |
| `EVIDENCE` | `docs/design/generated/` | `REVIEWED_NO_CHANGE` |
| `EVIDENCE` | `docs/design/assets/` | `REVIEWED_NO_CHANGE` |
| `CANONICAL` | `adminapp/README.md` | `RECONCILED` |
| `CANONICAL` | `webapp/README.md` | `RECONCILED` |
| `CANONICAL` | `marketing/README.md` | `RECONCILED` |

The registry changes classification only. Do not edit protected contents under
`docs/design/atlas-glass/**`, `docs/design/generated/**`, or
`docs/design/assets/**`.

- [ ] **Step 4: Verify and commit**

```powershell
& 'C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe' -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_admin_design_guardrails.py tests/test_frontend_text_integrity.py tests/test_public_copy_guardrails.py -q
& 'C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe' scripts/check-links.py
git diff --check
git diff --name-only -- docs/design/atlas-glass docs/design/generated docs/design/assets
git add DESIGN.md docs/design/design-system-sync.md docs/design/generated-assets-policy.md webapp/README.md adminapp/README.md marketing/README.md docs/README.md tests/test_agent_docs_contract.py
git commit -m "docs: normalize design and surface ownership"
```

Expected: no Atlas Glass/generated/assets content diff and all design/surface
checks, including direct README pointer resolution, pass.

### Task 7: Run The Platform Canon Validation Epoch

**Files:**
- Verify only

- [ ] **Step 1: Run the complete focused suite**

```powershell
& 'C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe' -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_beta_known_limitations_contract.py tests/test_shared_surface_facts.py tests/test_pokrov_migration_defaults.py tests/test_account_foundation.py tests/test_check_script_manifest.py tests/test_public_copy_guardrails.py tests/test_frontend_text_integrity.py tests/test_admin_design_guardrails.py tests/test_pokrov_ai_docs_assistant.py -q
& 'C:\Users\kiwun\Documents\ai\VPN\.venv\Scripts\python.exe' scripts/check-links.py
git diff --check
```

Expected: every test passes through the existing repository venv; no package
installation is attempted.

- [ ] **Step 2: Search active canon without mixing in evidence/history**

```powershell
$stale = 'webapp/src/app/\(dashboard\)/admin/|release repository remains private|avoids direct public.*VPN.*wording|legacy public.*VPN.*outside unavoidable|external/client-fork/scripts/(release_handoff\.ps1|check_release_urls\.py)|pokrov-android-universal\.apk|0\.x\.x-beta'
$activeCanon = @(
  'docs/product/portal-vpn-product.md',
  'docs/product/payment-and-access-key-contract.md',
  'docs/product/beta-known-limitations.md',
  'docs/architecture',
  'docs/operations/deployment-and-access.md',
  'docs/operations/monitoring-and-visibility.md',
  'docs/operations/publishing-and-signing-guide.md',
  'docs/operations/client-delivery-update-content-plan.md',
  'docs/operations/public-beta-release-runbook.md',
  'docs/design/design-system-sync.md',
  'docs/design/generated-assets-policy.md',
  'docs/launch/known-issues.md',
  'docs/launch/open-source-client-rollout-plan.md',
  'docs/user',
  'DESIGN.md',
  'webapp/README.md',
  'adminapp/README.md',
  'marketing/README.md'
)
& rg.exe -n $stale @activeCanon
if ($LASTEXITCODE -eq 0) { throw 'stale wording remains in active canon' }
if ($LASTEXITCODE -ne 1) { throw "active canon search failed with exit $LASTEXITCODE" }
```

Expected: no active-canon match. The two `.*VPN.*` alternatives intentionally
match stale wording whether or not Markdown backticks surround `VPN`.

- [ ] **Step 3: Report evidence/history matches separately**

```powershell
$evidenceAndHistory = @(
  'docs/archive',
  'docs/audit-artifacts',
  'docs/developer/work-orders',
  'docs/launch/open-beta-release-notes.md',
  'docs/product/public-beta-prd.md',
  'docs/design/atlas-glass',
  'docs/design/generated',
  'docs/design/assets',
  'reference-atlas'
)
& rg.exe -n $stale @evidenceAndHistory
if ($LASTEXITCODE -notin @(0, 1)) {
  throw "evidence/history search failed with exit $LASTEXITCODE"
}
```

Expected: matches, when present, are reported as retained evidence/history and
are not rewritten.

- [ ] **Step 4: Confirm protected zones are unchanged**

```powershell
$task1aCommit = git rev-list -1 --grep='^test: resolve client repo from platform common git dir$' HEAD
if ($LASTEXITCODE -ne 0 -or -not $task1aCommit) {
  throw 'Task 1A commit lookup failed'
}
$canonStart = git rev-parse "$task1aCommit^"
if ($LASTEXITCODE -ne 0 -or -not $canonStart) {
  throw 'Canon baseline resolution failed'
}
$orchestrationCommit = git rev-list -1 --grep='^docs: reduce developer entrypoints to current ownership$' HEAD
if ($LASTEXITCODE -ne 0 -or -not $orchestrationCommit) {
  throw 'Reviewed orchestration commit lookup failed'
}
& git merge-base --is-ancestor $task1aCommit $orchestrationCommit
if ($LASTEXITCODE -ne 0) {
  throw 'Task 1A is not an ancestor of the reviewed orchestration commit'
}

$protectedPaths = @(
  'docs/audit-artifacts',
  'docs/design/atlas-glass',
  'docs/design/generated',
  'docs/design/assets',
  'docs/developer/work-orders',
  'reference-atlas',
  'ops-local',
  'artifacts',
  'docs/launch/open-beta-release-notes.md',
  'docs/product/public-beta-prd.md',
  'docs/product/pokrov-growth-and-competitor-notes.md',
  'docs/operations/release-links-and-final-handoff.md',
  'docs/operations/2026-06-06-plans-decisions-closure-audit.md',
  'docs/operations/android-physical-device-audit-handoff.md',
  'docs/operations/email-delivery-webhook-handoff.md',
  'docs/operations/ru-origin-probe-handoff.md'
)
$moveOnlyPaths = @(
  'docs/product/platform-availability.md',
  'docs/archive/flat-docs/platform-availability-2026-05-26.md'
)
$workingTreeProtected = $protectedPaths + $moveOnlyPaths
$expectedReviewedProtectedDelta = 'docs/developer/work-orders/2026-07-09-growth-megapass/INDEX.md'
$reviewedProtectedDelta = @(
  & git diff --name-only "$canonStart..$orchestrationCommit" -- @protectedPaths
)
if ($LASTEXITCODE -ne 0) {
  throw "reviewed protected delta check failed with exit $LASTEXITCODE"
}
if (
  $reviewedProtectedDelta.Count -ne 1 -or
  $reviewedProtectedDelta[0] -ne $expectedReviewedProtectedDelta
) {
  throw 'reviewed protected delta is not the exact growth-megapass INDEX path'
}
$protectedRangeStart = $orchestrationCommit

& git diff --quiet -- @workingTreeProtected
if ($LASTEXITCODE -ne 0) {
  throw "protected tracked-unstaged check failed with exit $LASTEXITCODE"
}
& git diff --cached --quiet -- @workingTreeProtected
if ($LASTEXITCODE -ne 0) {
  throw "protected staged check failed with exit $LASTEXITCODE"
}
$untracked = @(& git ls-files --others --exclude-standard -- @workingTreeProtected)
if ($LASTEXITCODE -ne 0) {
  throw "protected untracked check failed with exit $LASTEXITCODE"
}
if ($untracked.Count -ne 0) {
  throw "protected untracked check found $($untracked.Count) path(s)"
}
& git diff --quiet "$protectedRangeStart..HEAD" -- @protectedPaths
if ($LASTEXITCODE -ne 0) {
  throw "protected committed-range check failed with exit $LASTEXITCODE"
}

$sourceSpec = '{0}:docs/product/platform-availability.md' -f $canonStart
$sourceBlob = git rev-parse $sourceSpec
if ($LASTEXITCODE -ne 0 -or -not $sourceBlob) {
  throw 'move-only source blob lookup failed'
}
$archiveBlob = git rev-parse 'HEAD:docs/archive/flat-docs/platform-availability-2026-05-26.md'
if ($LASTEXITCODE -ne 0 -or -not $archiveBlob) {
  throw 'move-only archive blob lookup failed'
}
if ($sourceBlob -ne $archiveBlob) {
  throw 'platform availability archive content changed during move'
}
```

Expected: every Git command exits `0`; the reviewed pre-baseline protected
delta is exactly the growth-megapass `INDEX.md`; protected tracked-unstaged,
staged, untracked, and post-baseline committed-range checks are empty; the
move-only source/archive blob IDs are identical. No protected file contents
are read or printed. The account-foundation continuity file was already landed
before Task 1A and is therefore part of `$canonStart`, not an allowed exception
in this range.
