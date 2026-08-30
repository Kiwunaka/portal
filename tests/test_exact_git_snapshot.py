from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import zlib
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import exact_git_snapshot as exact_snapshot  # noqa: E402
from exact_git_snapshot import (  # noqa: E402
    ExactGitSnapshotError,
    assert_sparse_repository_clean,
    canonical_requested_paths,
    materialize_paths,
    materialize_sparse_repository,
)


def _git() -> Path:
    raw = shutil.which("git.exe") or shutil.which("git")
    assert raw is not None
    return Path(raw).resolve()


def _run(git: Path, root: Path, *arguments: str, input_bytes: bytes | None = None):
    return subprocess.run(
        [str(git), "-C", str(root), *arguments],
        input=input_bytes,
        check=True,
        capture_output=True,
    )


def _commit_fixture(root: Path) -> tuple[Path, str]:
    git = _git()
    module = root / "engine" / "sing-box"
    module.mkdir(parents=True)
    (module / "go.mod").write_text(
        "module example.invalid/exact\n// $Format:%H$\n",
        encoding="utf-8",
    )
    (module / "kept.go").write_text("package exact\n", encoding="utf-8")
    (root / ".gitattributes").write_text(
        "engine/sing-box/go.mod export-subst\n"
        "engine/sing-box/kept.go export-ignore\n",
        encoding="utf-8",
    )
    _run(git, root, "init", "-q")
    _run(git, root, "add", ".")
    _run(
        git,
        root,
        "-c",
        "user.name=POKROV Test",
        "-c",
        "user.email=test@pokrov.invalid",
        "commit",
        "-qm",
        "fixture",
    )
    revision = _run(git, root, "rev-parse", "HEAD").stdout.decode().strip()
    return git, revision


def test_raw_object_materialization_ignores_archive_filters_and_worktree_bytes(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    git, revision = _commit_fixture(source)
    sentinel = source / "archive-filter-ran"
    _run(
        git,
        source,
        "config",
        "tar.tar.command",
        f"cmd.exe /c echo ran>{sentinel}" if sys.platform == "win32" else f"touch {sentinel}",
    )
    go_mod = source / "engine" / "sing-box" / "go.mod"
    _run(
        git,
        source,
        "update-index",
        "--assume-unchanged",
        "engine/sing-box/go.mod",
    )
    go_mod.write_text("module example.invalid/changed\n", encoding="utf-8")
    (source / "engine" / "sing-box" / "untracked.go").write_text(
        "package changed\n", encoding="utf-8"
    )

    destination = tmp_path / "snapshot"
    materialize_paths(
        git,
        source,
        revision,
        destination,
        ("engine/sing-box",),
    )

    assert not sentinel.exists()
    assert (destination / "engine/sing-box/go.mod").read_text(encoding="utf-8") == (
        "module example.invalid/exact\n// $Format:%H$\n"
    )
    assert (destination / "engine/sing-box/kept.go").is_file()
    assert not (destination / "engine/sing-box/untracked.go").exists()


def test_sparse_repository_is_exact_clean_and_detects_post_materialization_change(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    git, revision = _commit_fixture(source)
    destination = tmp_path / "snapshot"

    materialize_sparse_repository(
        git,
        source,
        revision,
        destination,
        ("engine/sing-box/go.mod",),
    )

    assert (destination / "engine/sing-box/go.mod").is_file()
    assert not (destination / "engine/sing-box/kept.go").exists()
    assert_sparse_repository_clean(
        git,
        destination,
        revision,
        ("engine/sing-box/go.mod",),
    )
    _run(
        git,
        destination,
        "update-index",
        "--skip-worktree",
        "engine/sing-box/go.mod",
    )
    (destination / "engine/sing-box/go.mod").write_text(
        "module example.invalid/tampered\n", encoding="utf-8"
    )
    with pytest.raises(ExactGitSnapshotError, match="changed during use"):
        assert_sparse_repository_clean(
            git,
            destination,
            revision,
            ("engine/sing-box/go.mod",),
        )


def test_materializer_rejects_corrupt_blob_under_original_object_id(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    git, revision = _commit_fixture(source)
    object_id = _run(
        git,
        source,
        "rev-parse",
        f"{revision}:engine/sing-box/go.mod",
    ).stdout.decode().strip()
    object_path = source / ".git" / "objects" / object_id[:2] / object_id[2:]
    original = (source / "engine/sing-box/go.mod").read_bytes()
    replacement = original.replace(b"/exact\n", b"/other\n")
    assert len(replacement) == len(original)
    object_path.chmod(0o600)
    object_path.write_bytes(zlib.compress(f"blob {len(replacement)}\0".encode() + replacement))

    with pytest.raises(ExactGitSnapshotError, match="materialization failed"):
        materialize_paths(
            git,
            source,
            revision,
            tmp_path / "snapshot",
            ("engine/sing-box/go.mod",),
        )


def test_inventory_rejects_corrupt_tree_under_original_object_id(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    git, revision = _commit_fixture(source)
    tree_id = _run(git, source, "rev-parse", f"{revision}^{{tree}}").stdout.decode().strip()
    original = _run(git, source, "cat-file", "tree", tree_id).stdout
    replacement = original.replace(b"engine\0", b"enginE\0")
    assert replacement != original and len(replacement) == len(original)
    object_path = source / ".git" / "objects" / tree_id[:2] / tree_id[2:]
    object_path.chmod(0o600)
    object_path.write_bytes(
        zlib.compress(f"tree {len(replacement)}\0".encode() + replacement)
    )

    with pytest.raises(ExactGitSnapshotError, match="object integrity"):
        exact_snapshot._tree_entries(
            git,
            source,
            revision,
            ("engine/sing-box/go.mod",),
        )


def test_sparse_repository_rejects_nested_source_root(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    git, revision = _commit_fixture(source)

    with pytest.raises(ExactGitSnapshotError, match="root mismatch"):
        materialize_sparse_repository(
            git,
            source / "engine",
            revision,
            tmp_path / "snapshot",
            ("sing-box/go.mod",),
        )


def test_sparse_repository_materializes_and_rechecks_exact_lfs_object(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    git, _revision = _commit_fixture(source)
    value = b"exact-lfs-runtime-bytes"
    lfs_object_id = hashlib.sha256(value).hexdigest()
    pointer = (
        "version https://git-lfs.github.com/spec/v1\n"
        f"oid sha256:{lfs_object_id}\n"
        f"size {len(value)}\n"
    ).encode("ascii")
    runtime_path = source / "runtime" / "core.bin"
    runtime_path.parent.mkdir()
    runtime_path.write_bytes(pointer)
    _run(git, source, "add", "runtime/core.bin")
    _run(
        git,
        source,
        "-c",
        "user.name=POKROV Test",
        "-c",
        "user.email=test@pokrov.invalid",
        "commit",
        "-qm",
        "LFS fixture",
    )
    revision = _run(git, source, "rev-parse", "HEAD").stdout.decode().strip()
    lfs_object = (
        source
        / ".git"
        / "lfs"
        / "objects"
        / lfs_object_id[:2]
        / lfs_object_id[2:4]
        / lfs_object_id
    )
    lfs_object.parent.mkdir(parents=True)
    lfs_object.write_bytes(value)
    destination = tmp_path / "snapshot"

    materialize_sparse_repository(
        git,
        source,
        revision,
        destination,
        ("runtime/core.bin",),
        ("runtime/core.bin",),
    )

    materialized = destination / "runtime" / "core.bin"
    assert materialized.read_bytes() == value
    assert_sparse_repository_clean(
        git,
        destination,
        revision,
        ("runtime/core.bin",),
        ("runtime/core.bin",),
    )
    materialized.write_bytes(b"changed-lfs-runtime")
    assert _run(
        git,
        destination,
        "status",
        "--porcelain",
        "--untracked-files=all",
    ).stdout == b""
    with pytest.raises(ExactGitSnapshotError, match="changed during use"):
        assert_sparse_repository_clean(
            git,
            destination,
            revision,
            ("runtime/core.bin",),
            ("runtime/core.bin",),
        )


@pytest.mark.parametrize(
    "pointer",
    (
        b"version https://git-lfs.github.com/spec/v1\r\n"
        b"oid sha256:" + (b"a" * 64) + b"\r\nsize 1\r\n",
        b"version https://git-lfs.github.com/spec/v1\n"
        b"oid sha256:" + (b"a" * 64) + b"\nsize 1",
        b"version https://git-lfs.github.com/spec/v1\n"
        b"oid sha256:" + (b"A" * 64) + b"\nsize 1\n",
        b"version https://git-lfs.github.com/spec/v1\n"
        b"oid sha256:" + (b"a" * 64) + b"\nsize +1\n",
        b"version https://git-lfs.github.com/spec/v1\n"
        b"oid sha256:" + (b"a" * 64) + b"\nsize 01\n",
    ),
)
def test_lfs_pointer_parser_rejects_noncanonical_forms(pointer: bytes) -> None:
    with pytest.raises(ExactGitSnapshotError, match="LFS pointer is invalid"):
        exact_snapshot._parse_lfs_pointer(pointer)


def test_materializer_rejects_symlink_mode_without_touching_target(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    git, _revision = _commit_fixture(source)
    object_id = _run(
        git,
        source,
        "hash-object",
        "-w",
        "--stdin",
        input_bytes=b"../outside",
    ).stdout.decode().strip()
    _run(
        git,
        source,
        "update-index",
        "--add",
        "--cacheinfo",
        f"120000,{object_id},engine/sing-box/link",
    )
    _run(
        git,
        source,
        "-c",
        "user.name=POKROV Test",
        "-c",
        "user.email=test@pokrov.invalid",
        "commit",
        "-qm",
        "symlink fixture",
    )
    revision = _run(git, source, "rev-parse", "HEAD").stdout.decode().strip()

    with pytest.raises(ExactGitSnapshotError, match="unsafe"):
        materialize_paths(
            git,
            source,
            revision,
            tmp_path / "snapshot",
            ("engine/sing-box",),
        )


@pytest.mark.parametrize(
    "path",
    (
        ".git/config",
        "engine/.GIT/config",
        "C:/escape",
        "engine/C:escape",
        "/absolute",
        "engine//duplicate",
        "engine/control\tname",
    ),
)
def test_requested_path_rejects_git_metadata_and_colons(path: str) -> None:
    with pytest.raises(ExactGitSnapshotError, match="path is invalid"):
        canonical_requested_paths((path,))
