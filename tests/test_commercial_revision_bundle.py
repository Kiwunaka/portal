from __future__ import annotations

import json
import shutil
import sys
import zipfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import commercial_revision_bundle as bundle_module  # noqa: E402
from commercial_revision_bundle import (  # noqa: E402
    BUNDLE_FILES,
    CommercialRevisionBundleError,
    readback_bundle,
    restore_bundle,
    snapshot_bundle,
)


def _copy_commercial_tree(destination: Path) -> None:
    for relative in BUNDLE_FILES:
        source = REPO_ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def test_snapshot_is_deterministic_and_readback_validates_complete_revision(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    _copy_commercial_tree(repo)
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"

    first_result = snapshot_bundle(repo_root=repo, output=first)
    second_result = snapshot_bundle(repo_root=repo, output=second)
    readback = readback_bundle(bundle=first)

    assert first.read_bytes() == second.read_bytes()
    assert first_result["bundle_sha256"] == second_result["bundle_sha256"]
    assert readback["valid"] is True
    assert readback["commercial_revision"] == "2026-08-21.1"
    assert [item["path"] for item in readback["files"]] == list(BUNDLE_FILES)


def test_readback_rejects_extra_or_tampered_members(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _copy_commercial_tree(repo)
    bundle = tmp_path / "bundle.zip"
    snapshot_bundle(repo_root=repo, output=bundle)

    with zipfile.ZipFile(bundle, mode="a") as archive:
        archive.writestr("unexpected.txt", b"not part of the revision")

    with pytest.raises(CommercialRevisionBundleError, match="bundle_member_set_invalid"):
        readback_bundle(bundle=bundle)


def test_snapshot_rejects_stale_source_contract(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _copy_commercial_tree(repo)
    product_facts = repo / "shared/product-facts.json"
    changed = json.loads(product_facts.read_text(encoding="utf-8"))
    changed["stale_test_marker"] = True
    product_facts.write_text(json.dumps(changed), encoding="utf-8")

    with pytest.raises(
        CommercialRevisionBundleError,
        match="commercial_source_digest_mismatch",
    ):
        snapshot_bundle(repo_root=repo, output=tmp_path / "stale.zip")


def test_restore_is_dry_run_by_default_and_requires_exact_apply_guards(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    _copy_commercial_tree(repo)
    bundle = tmp_path / "bundle.zip"
    snapshot = snapshot_bundle(repo_root=repo, output=bundle)
    product_facts = repo / "shared/product-facts.json"
    expected = product_facts.read_bytes()
    product_facts.write_bytes(expected + b"\n")

    plan = restore_bundle(repo_root=repo, bundle=bundle)
    assert plan["mode"] == "dry_run"
    assert plan["changed_file_count"] == 1
    assert product_facts.read_bytes() != expected

    with pytest.raises(
        CommercialRevisionBundleError,
        match="current_revision_guard_mismatch",
    ):
        restore_bundle(repo_root=repo, bundle=bundle, apply=True)
    with pytest.raises(
        CommercialRevisionBundleError,
        match="bundle_sha256_guard_mismatch",
    ):
        restore_bundle(
            repo_root=repo,
            bundle=bundle,
            apply=True,
            expect_current_revision="2026-08-21.1",
            expect_bundle_sha256="0" * 64,
        )

    applied = restore_bundle(
        repo_root=repo,
        bundle=bundle,
        apply=True,
        expect_current_revision="2026-08-21.1",
        expect_bundle_sha256=snapshot["bundle_sha256"],
    )
    assert applied["applied"] is True
    assert applied["restored_file_count"] == 1
    assert product_facts.read_bytes() == expected


def test_failed_multi_file_restore_rolls_back_already_replaced_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    _copy_commercial_tree(repo)
    bundle = tmp_path / "bundle.zip"
    snapshot = snapshot_bundle(repo_root=repo, output=bundle)
    first = repo / BUNDLE_FILES[0]
    second = repo / BUNDLE_FILES[1]
    first_modified = first.read_bytes() + b"\n"
    second_modified = second.read_bytes() + b"\n"
    first.write_bytes(first_modified)
    second.write_bytes(second_modified)

    original_atomic_write = bundle_module._atomic_write
    calls = 0

    def fail_second_write(path: Path, content: bytes) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("planted second-file failure")
        original_atomic_write(path, content)

    monkeypatch.setattr(bundle_module, "_atomic_write", fail_second_write)
    with pytest.raises(OSError, match="planted second-file failure"):
        restore_bundle(
            repo_root=repo,
            bundle=bundle,
            apply=True,
            expect_current_revision="2026-08-21.1",
            expect_bundle_sha256=snapshot["bundle_sha256"],
        )

    assert first.read_bytes() == first_modified
    assert second.read_bytes() == second_modified
