"""Materialize bounded immutable Git snapshots without checkout/archive filters."""

from __future__ import annotations

import os
import re
import hashlib
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Mapping, Sequence


GIT_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
GIT_OBJECT_RE = re.compile(r"^[0-9a-f]{40}$")
LFS_OBJECT_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_TREE_LIST_BYTES = 8 * 1024 * 1024
MAX_SNAPSHOT_FILES = 10_000
MAX_BLOB_BYTES = 128 * 1024 * 1024
MAX_SNAPSHOT_BYTES = 256 * 1024 * 1024
MAX_COMMIT_BYTES = 2 * 1024 * 1024
MAX_TREE_DEPTH = 128


class ExactGitSnapshotError(RuntimeError):
    """Raised when an immutable Git snapshot cannot be proven or materialized."""


@dataclass(frozen=True)
class GitTreeEntry:
    mode: str
    object_id: str
    size: int
    path: str
    lfs_object_id: str | None = None
    lfs_size: int | None = None

    @property
    def materialized_size(self) -> int:
        return self.lfs_size if self.lfs_size is not None else self.size


def git_environment(
    base: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return a Git environment without inherited repository-selection/config state."""

    source = os.environ if base is None else base
    environment = {
        key: value for key, value in source.items() if not key.startswith("GIT_")
    }
    environment.update(
        {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
        }
    )
    return environment


def git_command(git_executable: Path, *arguments: str) -> list[str]:
    return [
        str(git_executable),
        "-c",
        "core.fsmonitor=false",
        "-c",
        f"core.hooksPath={os.devnull}",
        *arguments,
    ]


def _run_git(
    git_executable: Path,
    repository: Path,
    *arguments: str,
    input_bytes: bytes | None = None,
    timeout: int = 120,
) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            git_command(git_executable, *arguments),
            cwd=repository,
            env=git_environment(),
            input=input_bytes,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ExactGitSnapshotError("exact Git operation failed") from exc


def _validate_revision(revision: str) -> str:
    normalized = str(revision).strip().lower()
    if GIT_REVISION_RE.fullmatch(normalized) is None:
        raise ExactGitSnapshotError("exact Git revision is invalid")
    return normalized


def _normalize_requested_path(raw_path: str) -> str:
    raw_value = str(raw_path).replace("\\", "/")
    value = raw_value.rstrip("/")
    path = PurePosixPath(value)
    normalized = path.as_posix()
    if (
        not value
        or raw_value.startswith("/")
        or path.is_absolute()
        or normalized != value
        or any(part in {"", ".", ".."} for part in path.parts)
        or any(part.casefold() == ".git" or ":" in part for part in path.parts)
        or any(any(ord(character) < 32 for character in part) for part in path.parts)
    ):
        raise ExactGitSnapshotError("exact Git snapshot path is invalid")
    return normalized


def confirm_repository_revision(
    git_executable: Path,
    repository: Path,
    expected_revision: str,
) -> str:
    """Confirm that repository is the selected root and HEAD is the expected commit."""

    revision = _validate_revision(expected_revision)
    try:
        requested_root = repository.resolve(strict=True)
    except OSError as exc:
        raise ExactGitSnapshotError("exact Git repository is unavailable") from exc
    if not requested_root.is_dir():
        raise ExactGitSnapshotError("exact Git repository is unavailable")

    top_level = _run_git(git_executable, requested_root, "rev-parse", "--show-toplevel")
    if top_level.returncode != 0:
        raise ExactGitSnapshotError("exact Git repository root is unavailable")
    try:
        actual_root = Path(top_level.stdout.decode("utf-8").strip()).resolve(
            strict=True
        )
    except (OSError, UnicodeError) as exc:
        raise ExactGitSnapshotError("exact Git repository root is unavailable") from exc
    if actual_root != requested_root:
        raise ExactGitSnapshotError("exact Git repository root mismatch")

    head = _run_git(git_executable, requested_root, "rev-parse", "HEAD")
    try:
        actual_revision = head.stdout.decode("ascii").strip().lower()
    except UnicodeError as exc:
        raise ExactGitSnapshotError("exact Git HEAD is unavailable") from exc
    if head.returncode != 0 or actual_revision != revision:
        raise ExactGitSnapshotError("exact Git HEAD revision mismatch")

    commit = _run_git(
        git_executable,
        requested_root,
        "cat-file",
        "-e",
        f"{revision}^{{commit}}",
    )
    if commit.returncode != 0:
        raise ExactGitSnapshotError("exact Git commit object is unavailable")
    return revision


def _matches_requested_path(path: str, requested_paths: Sequence[str]) -> bool:
    return any(path == item or path.startswith(f"{item}/") for item in requested_paths)


def _intersects_requested_path(path: str, requested_paths: Sequence[str]) -> bool:
    return any(
        path == item
        or path.startswith(f"{item}/")
        or item.startswith(f"{path}/")
        for item in requested_paths
    )


def _object_id(object_type: str, value: bytes) -> str:
    digest = hashlib.sha1(usedforsecurity=False)
    digest.update(f"{object_type} {len(value)}\0".encode("ascii"))
    digest.update(value)
    return digest.hexdigest()


def _read_verified_object(
    git_executable: Path,
    repository: Path,
    object_type: str,
    object_id: str,
    *,
    max_bytes: int,
) -> bytes:
    if GIT_OBJECT_RE.fullmatch(object_id) is None:
        raise ExactGitSnapshotError("exact Git object identity is invalid")
    size_result = _run_git(
        git_executable,
        repository,
        "cat-file",
        "-s",
        object_id,
    )
    try:
        declared_size = int(size_result.stdout.decode("ascii").strip())
    except (UnicodeError, ValueError) as exc:
        raise ExactGitSnapshotError("exact Git object size is invalid") from exc
    if (
        size_result.returncode != 0
        or declared_size < 0
        or declared_size > max_bytes
    ):
        raise ExactGitSnapshotError("exact Git object size is invalid")
    completed = _run_git(
        git_executable,
        repository,
        "cat-file",
        object_type,
        object_id,
    )
    if (
        completed.returncode != 0
        or len(completed.stdout) != declared_size
        or _object_id(object_type, completed.stdout) != object_id
    ):
        raise ExactGitSnapshotError("exact Git object integrity check failed")
    return completed.stdout


def _parse_lfs_pointer(value: bytes) -> tuple[str, int]:
    try:
        text = value.decode("ascii")
    except UnicodeError as exc:
        raise ExactGitSnapshotError("exact Git LFS pointer is invalid") from exc
    lines = text.splitlines()
    if (
        len(lines) != 3
        or lines[0] != "version https://git-lfs.github.com/spec/v1"
        or not lines[1].startswith("oid sha256:")
        or not lines[2].startswith("size ")
    ):
        raise ExactGitSnapshotError("exact Git LFS pointer is invalid")
    object_id = lines[1].removeprefix("oid sha256:").lower()
    try:
        size = int(lines[2].removeprefix("size "))
    except ValueError as exc:
        raise ExactGitSnapshotError("exact Git LFS pointer is invalid") from exc
    if (
        LFS_OBJECT_RE.fullmatch(object_id) is None
        or size < 0
        or size > MAX_BLOB_BYTES
    ):
        raise ExactGitSnapshotError("exact Git LFS pointer is invalid")
    return object_id, size


def _root_tree_object(
    git_executable: Path,
    repository: Path,
    revision: str,
) -> str:
    commit = _read_verified_object(
        git_executable,
        repository,
        "commit",
        revision,
        max_bytes=MAX_COMMIT_BYTES,
    )
    first_line = commit.partition(b"\n")[0]
    if not first_line.startswith(b"tree "):
        raise ExactGitSnapshotError("exact Git commit tree is invalid")
    try:
        tree_object = first_line.removeprefix(b"tree ").decode("ascii").lower()
    except UnicodeError as exc:
        raise ExactGitSnapshotError("exact Git commit tree is invalid") from exc
    if GIT_OBJECT_RE.fullmatch(tree_object) is None:
        raise ExactGitSnapshotError("exact Git commit tree is invalid")
    return tree_object


def _parse_tree_object(raw_tree: bytes) -> list[tuple[str, str, str]]:
    entries: list[tuple[str, str, str]] = []
    cursor = 0
    while cursor < len(raw_tree):
        mode_end = raw_tree.find(b" ", cursor)
        name_end = raw_tree.find(b"\0", mode_end + 1)
        object_end = name_end + 21
        if mode_end <= cursor or name_end <= mode_end + 1 or object_end > len(raw_tree):
            raise ExactGitSnapshotError("exact Git tree object is invalid")
        try:
            mode = raw_tree[cursor:mode_end].decode("ascii")
            name = raw_tree[mode_end + 1 : name_end].decode("utf-8")
        except UnicodeError as exc:
            raise ExactGitSnapshotError("exact Git tree object is invalid") from exc
        object_id = raw_tree[name_end + 1 : object_end].hex()
        if not name or "/" in name or GIT_OBJECT_RE.fullmatch(object_id) is None:
            raise ExactGitSnapshotError("exact Git tree object is invalid")
        entries.append((mode, object_id, name))
        cursor = object_end
    return entries


def _batch_blob_sizes(
    git_executable: Path,
    repository: Path,
    object_ids: Sequence[str],
) -> list[int]:
    completed = _run_git(
        git_executable,
        repository,
        "cat-file",
        "--batch-check=%(objectname) %(objecttype) %(objectsize)",
        input_bytes=b"".join(object_id.encode("ascii") + b"\n" for object_id in object_ids),
        timeout=300,
    )
    lines = completed.stdout.splitlines()
    if completed.returncode != 0 or len(lines) != len(object_ids):
        raise ExactGitSnapshotError("exact Git blob inventory is unavailable")
    sizes: list[int] = []
    for expected_id, line in zip(object_ids, lines, strict=True):
        fields = line.split()
        try:
            observed_id = fields[0].decode("ascii").lower()
            object_type = fields[1].decode("ascii")
            size = int(fields[2].decode("ascii"))
        except (IndexError, UnicodeError, ValueError) as exc:
            raise ExactGitSnapshotError(
                "exact Git blob inventory is invalid"
            ) from exc
        if (
            len(fields) != 3
            or observed_id != expected_id
            or object_type != "blob"
            or size < 0
            or size > MAX_BLOB_BYTES
        ):
            raise ExactGitSnapshotError("exact Git blob inventory is invalid")
        sizes.append(size)
    return sizes


def _tree_entries(
    git_executable: Path,
    repository: Path,
    revision: str,
    requested_paths: Sequence[str],
    lfs_paths: Sequence[str] = (),
) -> list[GitTreeEntry]:
    normalized_revision = _validate_revision(revision)
    normalized_paths = tuple(_normalize_requested_path(path) for path in requested_paths)
    if not normalized_paths or len(set(normalized_paths)) != len(normalized_paths):
        raise ExactGitSnapshotError("exact Git snapshot path set is invalid")
    normalized_lfs_paths = tuple(_normalize_requested_path(path) for path in lfs_paths)
    if (
        len(set(normalized_lfs_paths)) != len(normalized_lfs_paths)
        or any(path not in normalized_paths for path in normalized_lfs_paths)
    ):
        raise ExactGitSnapshotError("exact Git LFS path set is invalid")

    pending_entries: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    total_tree_bytes = 0

    def visit_tree(tree_object: str, prefix: str, depth: int) -> None:
        nonlocal total_tree_bytes
        if depth > MAX_TREE_DEPTH:
            raise ExactGitSnapshotError("exact Git tree depth exceeds its bound")
        raw_tree = _read_verified_object(
            git_executable,
            repository,
            "tree",
            tree_object,
            max_bytes=MAX_TREE_LIST_BYTES,
        )
        total_tree_bytes += len(raw_tree)
        if total_tree_bytes > MAX_TREE_LIST_BYTES:
            raise ExactGitSnapshotError("exact Git tree inventory exceeds its bound")
        for mode, object_id, name in _parse_tree_object(raw_tree):
            path = f"{prefix}/{name}" if prefix else name
            normalized_path = _normalize_requested_path(path)
            if normalized_path != path:
                raise ExactGitSnapshotError("exact Git tree entry is unsafe")
            if not _intersects_requested_path(normalized_path, normalized_paths):
                continue
            if mode in {"40000", "040000"}:
                visit_tree(object_id, normalized_path, depth + 1)
                continue
            if mode not in {"100644", "100755"} or not _matches_requested_path(
                normalized_path, normalized_paths
            ):
                raise ExactGitSnapshotError("exact Git tree entry is unsafe")
            if normalized_path in seen:
                raise ExactGitSnapshotError("exact Git tree entry is unsafe")
            seen.add(normalized_path)
            if len(pending_entries) >= MAX_SNAPSHOT_FILES:
                raise ExactGitSnapshotError("exact Git snapshot exceeds its bound")
            pending_entries.append((mode, object_id, normalized_path))

    visit_tree(
        _root_tree_object(
            git_executable,
            repository,
            normalized_revision,
        ),
        "",
        0,
    )
    sizes = _batch_blob_sizes(
        git_executable,
        repository,
        [object_id for _mode, object_id, _path in pending_entries],
    )
    entries: list[GitTreeEntry] = []
    for (mode, object_id, path), size in zip(pending_entries, sizes, strict=True):
        lfs_object_id: str | None = None
        lfs_size: int | None = None
        if path in normalized_lfs_paths:
            pointer = _read_verified_object(
                git_executable,
                repository,
                "blob",
                object_id,
                max_bytes=1024,
            )
            lfs_object_id, lfs_size = _parse_lfs_pointer(pointer)
        entries.append(
            GitTreeEntry(
                mode=mode,
                object_id=object_id,
                size=size,
                path=path,
                lfs_object_id=lfs_object_id,
                lfs_size=lfs_size,
            )
        )
    if sum(entry.materialized_size for entry in entries) > MAX_SNAPSHOT_BYTES:
        raise ExactGitSnapshotError("exact Git snapshot exceeds its bound")

    missing = [
        requested
        for requested in normalized_paths
        if not any(
            entry.path == requested or entry.path.startswith(f"{requested}/")
            for entry in entries
        )
    ]
    if missing:
        raise ExactGitSnapshotError("exact Git snapshot input is missing")
    if any(path not in {entry.path for entry in entries} for path in normalized_lfs_paths):
        raise ExactGitSnapshotError("exact Git LFS snapshot input is missing")
    return entries


def read_blob(
    git_executable: Path,
    repository: Path,
    revision: str,
    path: str,
    *,
    max_bytes: int = 2 * 1024 * 1024,
) -> bytes:
    """Read one exact regular-file blob with an explicit byte bound."""

    entries = _tree_entries(
        git_executable,
        repository,
        revision,
        [_normalize_requested_path(path)],
    )
    requested = _normalize_requested_path(path)
    if len(entries) != 1 or entries[0].path != requested:
        raise ExactGitSnapshotError("exact Git blob path is not a regular file")
    entry = entries[0]
    if entry.size > max_bytes:
        raise ExactGitSnapshotError("exact Git blob exceeds its bound")
    completed = _run_git(
        git_executable,
        repository,
        "cat-file",
        "blob",
        entry.object_id,
    )
    if (
        completed.returncode != 0
        or len(completed.stdout) != entry.size
        or _object_id("blob", completed.stdout) != entry.object_id
    ):
        raise ExactGitSnapshotError("exact Git blob could not be read")
    return completed.stdout


def _verify_materialized_blob(
    path: Path,
    entry: GitTreeEntry,
    snapshot_root: Path,
) -> None:
    try:
        resolved_path = path.resolve(strict=True)
        resolved_path.relative_to(snapshot_root)
        metadata = path.lstat()
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_size != entry.materialized_size
        ):
            raise ExactGitSnapshotError("exact Git blob materialization failed")
        if entry.lfs_object_id is not None:
            digest = hashlib.sha256()
        else:
            digest = hashlib.sha1(usedforsecurity=False)
            digest.update(f"blob {entry.size}\0".encode("ascii"))
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
    except (OSError, ValueError) as exc:
        raise ExactGitSnapshotError("exact Git blob materialization failed") from exc
    expected_id = entry.lfs_object_id or entry.object_id
    if digest.hexdigest() != expected_id:
        raise ExactGitSnapshotError("exact Git blob materialization failed")


def _git_lfs_object(
    git_executable: Path,
    repository: Path,
    entry: GitTreeEntry,
) -> Path:
    if entry.lfs_object_id is None or entry.lfs_size is None:
        raise ExactGitSnapshotError("exact Git LFS object identity is missing")
    common = _run_git(git_executable, repository, "rev-parse", "--git-common-dir")
    if common.returncode != 0:
        raise ExactGitSnapshotError("exact Git LFS object store is unavailable")
    try:
        raw_common = common.stdout.decode("utf-8").strip()
        common_root = Path(raw_common)
        if not common_root.is_absolute():
            common_root = repository / common_root
        lfs_root = (common_root.resolve(strict=True) / "lfs" / "objects").resolve(
            strict=True
        )
        object_path = (
            lfs_root
            / entry.lfs_object_id[:2]
            / entry.lfs_object_id[2:4]
            / entry.lfs_object_id
        ).resolve(strict=True)
        object_path.relative_to(lfs_root)
        metadata = object_path.lstat()
    except (OSError, UnicodeError, ValueError) as exc:
        raise ExactGitSnapshotError(
            "exact Git LFS object is unavailable"
        ) from exc
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size != entry.lfs_size:
        raise ExactGitSnapshotError("exact Git LFS object is unavailable")
    return object_path


def materialize_paths(
    git_executable: Path,
    repository: Path,
    revision: str,
    destination: Path,
    requested_paths: Sequence[str],
    lfs_paths: Sequence[str] = (),
) -> tuple[str, ...]:
    """Materialize exact regular-file objects without checkout or archive filters."""

    entries = _tree_entries(
        git_executable,
        repository,
        revision,
        requested_paths,
        lfs_paths,
    )
    try:
        destination.mkdir(parents=True, exist_ok=False)
        resolved_destination = destination.resolve(strict=True)
    except OSError as exc:
        raise ExactGitSnapshotError("exact Git snapshot destination is unavailable") from exc

    batch = _run_git(
        git_executable,
        repository,
        "cat-file",
        "--batch",
        input_bytes=b"".join(
            entry.object_id.encode("ascii") + b"\n" for entry in entries
        ),
        timeout=300,
    )
    if batch.returncode != 0:
        raise ExactGitSnapshotError("exact Git blob materialization failed")
    payload = memoryview(batch.stdout)
    cursor = 0
    for entry in entries:
        header_end = batch.stdout.find(b"\n", cursor, cursor + 200)
        if header_end < 0:
            raise ExactGitSnapshotError("exact Git blob materialization failed")
        fields = batch.stdout[cursor:header_end].split()
        try:
            observed_id = fields[0].decode("ascii").lower()
            object_type = fields[1].decode("ascii")
            observed_size = int(fields[2].decode("ascii"))
        except (IndexError, UnicodeError, ValueError) as exc:
            raise ExactGitSnapshotError(
                "exact Git blob materialization failed"
            ) from exc
        content_start = header_end + 1
        content_end = content_start + entry.size
        if (
            len(fields) != 3
            or observed_id != entry.object_id
            or object_type != "blob"
            or observed_size != entry.size
            or content_end >= len(payload)
            or payload[content_end] != 10
        ):
            raise ExactGitSnapshotError("exact Git blob materialization failed")
        output = resolved_destination.joinpath(*PurePosixPath(entry.path).parts)
        try:
            output.parent.mkdir(parents=True, exist_ok=True)
            resolved_parent = output.parent.resolve(strict=True)
            resolved_parent.relative_to(resolved_destination)
        except (OSError, ValueError) as exc:
            raise ExactGitSnapshotError("exact Git snapshot destination escaped") from exc
        try:
            with output.open("xb") as stream:
                pointer_or_blob = payload[content_start:content_end]
                if _object_id("blob", pointer_or_blob) != entry.object_id:
                    raise ExactGitSnapshotError(
                        "exact Git blob materialization failed"
                    )
                if entry.lfs_object_id is None:
                    stream.write(pointer_or_blob)
                else:
                    lfs_object = _git_lfs_object(
                        git_executable,
                        repository,
                        entry,
                    )
                    with lfs_object.open("rb") as source:
                        while chunk := source.read(1024 * 1024):
                            stream.write(chunk)
        except OSError as exc:
            raise ExactGitSnapshotError("exact Git blob materialization failed") from exc
        _verify_materialized_blob(output, entry, resolved_destination)
        if os.name != "nt":
            output.chmod(0o755 if entry.mode == "100755" else 0o644)
        cursor = content_end + 1
    if cursor != len(payload):
        raise ExactGitSnapshotError("exact Git blob materialization failed")
    return tuple(entry.path for entry in entries)


def _git_object_directory(
    git_executable: Path,
    repository: Path,
) -> Path:
    completed = _run_git(git_executable, repository, "rev-parse", "--git-path", "objects")
    if completed.returncode != 0:
        raise ExactGitSnapshotError("exact Git object directory is unavailable")
    try:
        raw_path = completed.stdout.decode("utf-8").strip()
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = repository / candidate
        resolved = candidate.resolve(strict=True)
    except (OSError, UnicodeError) as exc:
        raise ExactGitSnapshotError("exact Git object directory is unavailable") from exc
    if not resolved.is_dir() or "\n" in str(resolved) or "\r" in str(resolved):
        raise ExactGitSnapshotError("exact Git object directory is unavailable")
    return resolved


def _require_git_success(
    completed: subprocess.CompletedProcess[bytes],
    message: str,
) -> None:
    if completed.returncode != 0:
        raise ExactGitSnapshotError(message)


def materialize_sparse_repository(
    git_executable: Path,
    repository: Path,
    revision: str,
    destination: Path,
    requested_paths: Sequence[str],
    lfs_paths: Sequence[str] = (),
) -> Path:
    """Create an exact sparse snapshot whose Git HEAD/status remain usable and clean."""

    normalized_revision = confirm_repository_revision(
        git_executable,
        repository,
        revision,
    )
    materialized = materialize_paths(
        git_executable,
        repository,
        normalized_revision,
        destination,
        requested_paths,
        lfs_paths,
    )
    object_directory = _git_object_directory(git_executable, repository)

    with tempfile.TemporaryDirectory(prefix="pokrov-empty-git-template-") as template:
        initialized = _run_git(
            git_executable,
            destination.parent,
            "init",
            "-q",
            f"--template={template}",
            str(destination),
        )
    _require_git_success(initialized, "exact Git snapshot repository init failed")

    git_directory = destination / ".git"
    alternates = git_directory / "objects" / "info" / "alternates"
    try:
        alternates.parent.mkdir(parents=True, exist_ok=True)
        alternates.write_bytes(f"{object_directory}\n".encode("utf-8"))
        (git_directory / "HEAD").write_bytes(
            f"{normalized_revision}\n".encode("ascii")
        )
    except OSError as exc:
        raise ExactGitSnapshotError("exact Git snapshot metadata failed") from exc

    _require_git_success(
        _run_git(git_executable, destination, "read-tree", normalized_revision),
        "exact Git snapshot index creation failed",
    )
    tracked = _run_git(git_executable, destination, "ls-files", "-z")
    if tracked.returncode != 0 or len(tracked.stdout) > MAX_TREE_LIST_BYTES:
        raise ExactGitSnapshotError("exact Git snapshot index inventory failed")
    _require_git_success(
        _run_git(
            git_executable,
            destination,
            "update-index",
            "-z",
            "--skip-worktree",
            "--stdin",
            input_bytes=tracked.stdout,
        ),
        "exact Git snapshot sparse index failed",
    )
    normalized_lfs_paths = set(canonical_requested_paths(lfs_paths)) if lfs_paths else set()
    selected_input = b"".join(
        path.encode("utf-8") + b"\0"
        for path in materialized
        if path not in normalized_lfs_paths
    )
    if selected_input:
        _require_git_success(
            _run_git(
                git_executable,
                destination,
                "update-index",
                "-z",
                "--no-skip-worktree",
                "--stdin",
                input_bytes=selected_input,
            ),
            "exact Git snapshot selected index failed",
        )
    assert_sparse_repository_clean(
        git_executable,
        destination,
        normalized_revision,
        requested_paths,
        lfs_paths,
    )
    return destination


def assert_sparse_repository_clean(
    git_executable: Path,
    repository: Path,
    expected_revision: str,
    requested_paths: Sequence[str],
    lfs_paths: Sequence[str] = (),
) -> None:
    """Fail if a sparse exact snapshot changed after materialization."""

    revision = _validate_revision(expected_revision)
    head = _run_git(git_executable, repository, "rev-parse", "HEAD")
    status = _run_git(
        git_executable,
        repository,
        "status",
        "--porcelain",
        "--untracked-files=all",
    )
    try:
        actual = head.stdout.decode("ascii").strip().lower()
    except UnicodeError as exc:
        raise ExactGitSnapshotError("exact Git snapshot HEAD is unavailable") from exc
    if (
        head.returncode != 0
        or actual != revision
        or status.returncode != 0
        or status.stdout
    ):
        raise ExactGitSnapshotError("exact Git sparse snapshot changed during use")
    try:
        resolved_repository = repository.resolve(strict=True)
        entries = _tree_entries(
            git_executable,
            repository,
            revision,
            requested_paths,
            lfs_paths,
        )
        for entry in entries:
            path = resolved_repository.joinpath(*PurePosixPath(entry.path).parts)
            _verify_materialized_blob(path, entry, resolved_repository)
    except ExactGitSnapshotError as exc:
        raise ExactGitSnapshotError(
            "exact Git sparse snapshot changed during use"
        ) from exc


def canonical_requested_paths(paths: Iterable[str]) -> tuple[str, ...]:
    """Normalize and de-duplicate a caller-computed exact path allowlist."""

    normalized = tuple(_normalize_requested_path(path) for path in paths)
    if not normalized or len(set(normalized)) != len(normalized):
        raise ExactGitSnapshotError("exact Git snapshot path set is invalid")
    return normalized
