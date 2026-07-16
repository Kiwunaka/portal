from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import secrets
import shutil
import stat
import sys
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import internal_hmac_client  # noqa: E402


UPLOADER_VERSION = "2.0.0"
RUNS_PATH = "/api/internal/probes/ru-origin/runs"
HEARTBEAT_PATH = "/api/internal/probes/ru-origin/heartbeat"
DEFAULT_API_BASE_URL = "https://api.pokrov.space"
DEFAULT_KEY_ID = "ru-mini-v1"
DEFAULT_SECRET_FILE = Path("/etc/pokrov-ru-probe/hmac.key")
DEFAULT_SPOOL_ROOT = Path("/var/lib/pokrov-ru-probe")
DEFAULT_PROBE_HOST_ID = "mini"
DEFAULT_TIMEOUT_SEC = 15.0
MAX_ARTIFACT_BYTES = 512 * 1024
MAX_RESPONSE_METADATA_BYTES = 64 * 1024
SPOOL_STATES = ("pending", "blocked", "quarantine", "archive")
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_CORRELATION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_HOST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")
_KNOWN_RESPONSE_CODES = {
    "accepted",
    "created",
    "idempotent",
    "invalid_payload",
    "invalid_request",
    "key_disabled",
    "key_scope_forbidden",
    "payload_conflict",
    "replayed_nonce",
    "request_too_large",
    "temporary",
    "unsupported_schema",
}
_ALLOWED_LAST_ERROR_CODES = {
    "archive_write_failed",
    "artifact_hash_mismatch",
    "artifact_invalid",
    "blocked_key",
    "disk_critical",
    "disk_low",
    "heartbeat_failed",
    "network_error",
    "quarantine_present",
    "spool_transition_failed",
}
_THREAD_LOCKS: dict[str, threading.RLock] = {}
_THREAD_LOCKS_GUARD = threading.Lock()
_ACTIVE_UPLOADS: set[str] = set()
_ACTIVE_UPLOADS_GUARD = threading.Lock()


class SpoolError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = str(code)
        super().__init__(self.code)


@dataclass(frozen=True)
class RecoveryIssue:
    code: str
    path: Path


@dataclass(frozen=True)
class UploadOutcome:
    destination: str
    status: int | None
    code: str
    correlation_id: str | None
    attempts: int
    retry_after_seconds: int | None = None
    path: Path | None = None
    disk_state: str | None = None


def _utc_text(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise SpoolError("invalid_clock")
    return (
        value.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate JSON member")
        result[name] = value
    return result


def _validate_run_id(run_id: object) -> str:
    if not isinstance(run_id, str):
        raise SpoolError("invalid_run_id")
    try:
        parsed = uuid.UUID(run_id)
    except (ValueError, AttributeError) as exc:
        raise SpoolError("invalid_run_id") from exc
    if str(parsed) != run_id or parsed.version != 4:
        raise SpoolError("invalid_run_id")
    return run_id


def _artifact_run_id(raw: bytes) -> str:
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_ARTIFACT_BYTES:
        raise SpoolError("artifact_invalid")
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except (UnicodeError, ValueError) as exc:
        raise SpoolError("artifact_invalid") from exc
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != 2
        or payload.get("origin") != "ru"
    ):
        raise SpoolError("artifact_invalid")
    return _validate_run_id(payload.get("run_id"))


def _thread_lock(root: Path) -> threading.RLock:
    key = os.path.normcase(str(root.absolute()))
    with _THREAD_LOCKS_GUARD:
        return _THREAD_LOCKS.setdefault(key, threading.RLock())


def _ensure_private_directory(path: Path) -> None:
    try:
        path.mkdir(parents=True, mode=0o700, exist_ok=True)
        metadata = path.lstat()
    except OSError as exc:
        raise SpoolError("spool_directory_invalid") from exc
    if stat.S_ISLNK(metadata.st_mode):
        raise SpoolError("spool_directory_symlink")
    if not stat.S_ISDIR(metadata.st_mode):
        raise SpoolError("spool_directory_invalid")
    try:
        path.chmod(0o700)
    except OSError as exc:
        raise SpoolError("spool_directory_permissions") from exc


def ensure_spool_layout(spool_root: str | Path) -> Path:
    root = Path(spool_root)
    _ensure_private_directory(root)
    for state in SPOOL_STATES:
        _ensure_private_directory(root / state)
    return root


def _open_lock_file(path: Path) -> int:
    flags = (
        os.O_RDWR
        | os.O_CREAT
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_BINARY", 0)
    )
    if getattr(os, "O_NOFOLLOW", 0):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        raise SpoolError("spool_lock_unavailable") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise SpoolError("spool_lock_invalid")
        os.chmod(path, 0o600)
        if metadata.st_size == 0:
            os.write(descriptor, b"0")
            os.fsync(descriptor)
        os.lseek(descriptor, 0, os.SEEK_SET)
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _lock_descriptor(descriptor: int, *, blocking: bool) -> bool:
    if os.name == "nt":
        import msvcrt

        mode = msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK
        try:
            msvcrt.locking(descriptor, mode, 1)
            return True
        except OSError:
            return False
    import fcntl

    flags = fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB)
    try:
        fcntl.flock(descriptor, flags)
        return True
    except BlockingIOError:
        return False


def _unlock_descriptor(descriptor: int) -> None:
    if os.name == "nt":
        import msvcrt

        os.lseek(descriptor, 0, os.SEEK_SET)
        try:
            msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        return
    import fcntl

    fcntl.flock(descriptor, fcntl.LOCK_UN)


@contextlib.contextmanager
def _spool_lock(root: Path) -> Iterator[None]:
    ensure_spool_layout(root)
    with _thread_lock(root):
        descriptor = _open_lock_file(root / ".spool.lock")
        try:
            if not _lock_descriptor(descriptor, blocking=True):
                raise SpoolError("spool_lock_unavailable")
            yield
        finally:
            _unlock_descriptor(descriptor)
            os.close(descriptor)


@contextlib.contextmanager
def _upload_claim(root: Path, run_id: str) -> Iterator[bool]:
    claim_key = f"{os.path.normcase(str(root.absolute()))}:{run_id}"
    with _ACTIVE_UPLOADS_GUARD:
        if claim_key in _ACTIVE_UPLOADS:
            yield False
            return
        _ACTIVE_UPLOADS.add(claim_key)
    descriptor: int | None = None
    locked = False
    try:
        ensure_spool_layout(root)
        descriptor = _open_lock_file(root / "pending" / f".{run_id}.upload.lock")
        locked = _lock_descriptor(descriptor, blocking=False)
        yield locked
    finally:
        if descriptor is not None:
            if locked:
                _unlock_descriptor(descriptor)
            os.close(descriptor)
        with _ACTIVE_UPLOADS_GUARD:
            _ACTIVE_UPLOADS.discard(claim_key)


def _fsync_directory(directory: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(directory, flags)
    except OSError:
        if os.name == "nt":
            return
        raise
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_all(descriptor: int, raw: bytes) -> None:
    offset = 0
    while offset < len(raw):
        written = os.write(descriptor, raw[offset:])
        if written <= 0:
            raise OSError("short write")
        offset += written


def _atomic_write_private(path: Path, raw: bytes) -> None:
    _ensure_private_directory(path.parent)
    descriptor: int | None = None
    temporary: Path | None = None
    try:
        for _attempt in range(32):
            candidate = path.with_name(
                f".{path.name}.{os.getpid()}.{secrets.token_hex(12)}.tmp"
            )
            flags = (
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_BINARY", 0)
            )
            if getattr(os, "O_NOFOLLOW", 0):
                flags |= os.O_NOFOLLOW
            try:
                descriptor = os.open(candidate, flags, 0o600)
            except FileExistsError:
                continue
            temporary = candidate
            break
        if descriptor is None or temporary is None:
            raise OSError("temporary file unavailable")
        _write_all(descriptor, raw)
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        temporary.chmod(0o600)
        os.replace(temporary, path)
        temporary = None
        path.chmod(0o600)
        _fsync_directory(path.parent)
    except OSError as exc:
        raise SpoolError("atomic_write_failed") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def _read_regular_file(
    path: Path,
    *,
    maximum: int,
    symlink_code: str,
    invalid_code: str,
) -> bytes:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        raise SpoolError("artifact_missing")
    if stat.S_ISLNK(metadata.st_mode):
        raise SpoolError(symlink_code)
    if not stat.S_ISREG(metadata.st_mode):
        raise SpoolError(invalid_code)
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_BINARY", 0)
    )
    if getattr(os, "O_NOFOLLOW", 0):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise SpoolError(invalid_code) from exc
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or opened.st_size > maximum:
            raise SpoolError(invalid_code)
        chunks: list[bytes] = []
        remaining = maximum + 1
        while remaining:
            chunk = os.read(descriptor, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) > maximum:
            raise SpoolError(invalid_code)
        return raw
    finally:
        os.close(descriptor)


def _sidecar_bytes(raw: bytes) -> bytes:
    return hashlib.sha256(raw).hexdigest().encode("ascii") + b"\n"


def _sidecar_digest(raw: bytes) -> str | None:
    try:
        text = raw.decode("ascii")
    except UnicodeError:
        return None
    if text.endswith("\n"):
        text = text[:-1]
    return text if _HASH_RE.fullmatch(text) is not None else None


def _ensure_exact_file(path: Path, raw: bytes) -> None:
    if path.exists() or path.is_symlink():
        existing = _read_regular_file(
            path,
            maximum=max(len(raw), 128),
            symlink_code="artifact_symlink",
            invalid_code="artifact_invalid",
        )
        if existing != raw:
            raise SpoolError("destination_conflict")
        return
    _atomic_write_private(path, raw)


def write_pending_artifact(
    spool_root: str | Path,
    run_id: str,
    artifact: bytes,
) -> Path:
    validated_run_id = _validate_run_id(run_id)
    if _artifact_run_id(artifact) != validated_run_id:
        raise SpoolError("artifact_run_id_mismatch")
    root = ensure_spool_layout(spool_root)
    artifact_path = root / "pending" / f"{validated_run_id}.json"
    sidecar_path = artifact_path.with_suffix(".sha256")
    expected_sidecar = _sidecar_bytes(artifact)
    with _spool_lock(root):
        artifact_exists = artifact_path.exists() or artifact_path.is_symlink()
        sidecar_exists = sidecar_path.exists() or sidecar_path.is_symlink()
        if artifact_exists:
            existing = _read_regular_file(
                artifact_path,
                maximum=MAX_ARTIFACT_BYTES,
                symlink_code="artifact_symlink",
                invalid_code="artifact_invalid",
            )
            if existing != artifact:
                raise SpoolError("run_id_conflict")
        if sidecar_exists:
            existing_sidecar = _read_regular_file(
                sidecar_path,
                maximum=65,
                symlink_code="sidecar_symlink",
                invalid_code="sidecar_invalid",
            )
            if existing_sidecar != expected_sidecar:
                raise SpoolError("run_id_conflict")
        if not artifact_exists:
            _atomic_write_private(artifact_path, artifact)
        if not sidecar_exists:
            _atomic_write_private(sidecar_path, expected_sidecar)
    return artifact_path


def recover_pending(spool_root: str | Path) -> list[RecoveryIssue]:
    root = ensure_spool_layout(spool_root)
    pending = root / "pending"
    issues: list[RecoveryIssue] = []
    with _spool_lock(root):
        for artifact_path in sorted(pending.glob("*.json")):
            try:
                run_id = _validate_run_id(artifact_path.stem)
                raw = _read_regular_file(
                    artifact_path,
                    maximum=MAX_ARTIFACT_BYTES,
                    symlink_code="artifact_symlink",
                    invalid_code="artifact_invalid",
                )
                if _artifact_run_id(raw) != run_id:
                    issues.append(
                        RecoveryIssue("artifact_run_id_mismatch", artifact_path)
                    )
                    continue
                sidecar_path = artifact_path.with_suffix(".sha256")
                if not sidecar_path.exists() and not sidecar_path.is_symlink():
                    _atomic_write_private(sidecar_path, _sidecar_bytes(raw))
            except SpoolError as exc:
                issues.append(RecoveryIssue(exc.code, artifact_path))
        for sidecar_path in sorted(pending.glob("*.sha256")):
            try:
                _validate_run_id(sidecar_path.stem)
            except SpoolError:
                continue
            if not sidecar_path.with_suffix(".json").exists():
                issues.append(
                    RecoveryIssue("sidecar_without_artifact", sidecar_path)
                )
    return issues


def scan_pending(spool_root: str | Path) -> list[Path]:
    root = ensure_spool_layout(spool_root)
    recover_pending(root)
    result: list[Path] = []
    for artifact_path in sorted((root / "pending").glob("*.json")):
        try:
            _validate_run_id(artifact_path.stem)
        except SpoolError:
            continue
        if artifact_path.with_suffix(".sha256").is_file():
            result.append(artifact_path)
    return result


def calculate_backoff(
    attempt: int,
    *,
    jitter: Callable[[int], int] | None = None,
) -> int:
    if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 0:
        raise SpoolError("invalid_retry_attempt")
    base = min(3600, 60 * (2**min(attempt, 20)))
    if base >= 3600:
        return 3600
    jitter_fn = jitter or (lambda upper: secrets.randbelow(upper + 1))
    try:
        jitter_value = int(jitter_fn(30))
    except (TypeError, ValueError) as exc:
        raise SpoolError("invalid_retry_jitter") from exc
    return min(3600, base + max(0, min(30, jitter_value)))


def _validate_pending_artifact_path(path: str | Path) -> tuple[Path, Path, str]:
    artifact_path = Path(path).absolute()
    if artifact_path.parent.name != "pending":
        raise SpoolError("invalid_pending_path")
    root = artifact_path.parent.parent
    ensure_spool_layout(root)
    expected_pending = (root / "pending").resolve()
    if artifact_path.parent.resolve() != expected_pending:
        raise SpoolError("invalid_pending_path")
    if artifact_path.suffix != ".json":
        raise SpoolError("invalid_pending_path")
    run_id = _validate_run_id(artifact_path.stem)
    try:
        metadata = artifact_path.lstat()
    except FileNotFoundError:
        raise SpoolError("artifact_missing")
    if stat.S_ISLNK(metadata.st_mode):
        raise SpoolError("artifact_symlink")
    if not stat.S_ISREG(metadata.st_mode):
        raise SpoolError("artifact_invalid")
    return artifact_path, root, run_id


def _read_artifact_pair(
    artifact_path: Path,
    *,
    expected_run_id: str,
) -> tuple[bytes, bytes, bool]:
    raw = _read_regular_file(
        artifact_path,
        maximum=MAX_ARTIFACT_BYTES,
        symlink_code="artifact_symlink",
        invalid_code="artifact_invalid",
    )
    if _artifact_run_id(raw) != expected_run_id:
        raise SpoolError("artifact_run_id_mismatch")
    sidecar_path = artifact_path.with_suffix(".sha256")
    sidecar_raw = _read_regular_file(
        sidecar_path,
        maximum=128,
        symlink_code="sidecar_symlink",
        invalid_code="sidecar_invalid",
    )
    digest = _sidecar_digest(sidecar_raw)
    return raw, sidecar_raw, digest == hashlib.sha256(raw).hexdigest()


def _safe_response_metadata(response: object) -> tuple[int, str, str | None]:
    try:
        status_value = int(getattr(response, "status"))
    except (TypeError, ValueError, AttributeError):
        status_value = 0
    raw = getattr(response, "body", b"")
    if not isinstance(raw, bytes) or len(raw) > MAX_RESPONSE_METADATA_BYTES:
        raw = b""
    payload: object = {}
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except (UnicodeError, ValueError):
        payload = {}
    code: str | None = None
    correlation_id: str | None = None
    if isinstance(payload, dict):
        reported_code = payload.get("code")
        if (
            isinstance(reported_code, str)
            and reported_code in _KNOWN_RESPONSE_CODES
        ):
            code = reported_code
        reported_correlation = payload.get("correlation_id")
        if (
            isinstance(reported_correlation, str)
            and _CORRELATION_RE.fullmatch(reported_correlation) is not None
        ):
            correlation_id = reported_correlation
    if code is None:
        if status_value in {200, 201}:
            code = "accepted"
        elif status_value in {408, 425, 429} or 500 <= status_value <= 599:
            code = "temporary"
        elif status_value in {401, 403}:
            code = "key_disabled"
        elif status_value == 413:
            code = "request_too_large"
        elif status_value == 422:
            code = "invalid_payload"
        else:
            code = "invalid_request"
    return status_value, code, correlation_id


def _reason_bytes(
    *,
    status: int | None,
    code: str,
    correlation_id: str | None,
    now: datetime,
) -> bytes:
    safe_code = code if code in _ALLOWED_LAST_ERROR_CODES or code in _KNOWN_RESPONSE_CODES else "invalid_request"
    safe_correlation = (
        correlation_id
        if isinstance(correlation_id, str)
        and _CORRELATION_RE.fullmatch(correlation_id) is not None
        else None
    )
    return _canonical_json_bytes(
        {
            "status": status,
            "code": safe_code,
            "correlation_id": safe_correlation,
            "observed_at": _utc_text(now),
        }
    )


def _transition_pair(
    *,
    artifact_path: Path,
    root: Path,
    run_id: str,
    artifact_raw: bytes,
    sidecar_raw: bytes,
    destination: str,
    reason_raw: bytes | None,
) -> Path:
    if destination not in {"archive", "blocked", "quarantine"}:
        raise SpoolError("invalid_destination")
    destination_dir = root / destination
    destination_artifact = destination_dir / f"{run_id}.json"
    destination_sidecar = destination_dir / f"{run_id}.sha256"
    destination_reason = destination_dir / f"{run_id}.reason.json"
    source_sidecar = artifact_path.with_suffix(".sha256")
    destination_members = [
        (destination_artifact, artifact_raw),
        (destination_sidecar, sidecar_raw),
    ]
    if reason_raw is not None:
        destination_members.append((destination_reason, reason_raw))
    with _spool_lock(root):
        current_artifact = _read_regular_file(
            artifact_path,
            maximum=MAX_ARTIFACT_BYTES,
            symlink_code="artifact_symlink",
            invalid_code="artifact_invalid",
        )
        current_sidecar = _read_regular_file(
            source_sidecar,
            maximum=128,
            symlink_code="sidecar_symlink",
            invalid_code="sidecar_invalid",
        )
        if current_artifact != artifact_raw or current_sidecar != sidecar_raw:
            raise SpoolError("source_changed")
        try:
            for destination_path, destination_raw in destination_members:
                _ensure_exact_file(destination_path, destination_raw)
            _fsync_directory(destination_dir)
        except (OSError, SpoolError) as exc:
            for destination_path, destination_raw in reversed(
                destination_members
            ):
                try:
                    existing = _read_regular_file(
                        destination_path,
                        maximum=max(len(destination_raw), 128),
                        symlink_code="artifact_symlink",
                        invalid_code="artifact_invalid",
                    )
                    if existing == destination_raw:
                        destination_path.unlink()
                except (OSError, SpoolError):
                    pass
            try:
                _fsync_directory(destination_dir)
            except OSError:
                pass
            raise SpoolError("destination_durability_failed") from exc
        try:
            source_sidecar.unlink()
            artifact_path.unlink()
            _fsync_directory(artifact_path.parent)
        except OSError as exc:
            for source_path, source_raw in (
                (artifact_path, artifact_raw),
                (source_sidecar, sidecar_raw),
            ):
                try:
                    _ensure_exact_file(source_path, source_raw)
                except SpoolError:
                    pass
            try:
                _fsync_directory(artifact_path.parent)
            except OSError:
                pass
            raise SpoolError("transition_cleanup_failed") from exc
    return destination_artifact


def _invoke_transport(
    transport: object | None,
    *,
    api_base_url: str,
    path: str,
    key_id: str,
    secret_file: str | Path,
    raw_body: bytes,
    timeout_sec: float,
):
    kwargs = {
        "api_base_url": api_base_url,
        "method": "POST",
        "path": path,
        "key_id": key_id,
        "secret_file": secret_file,
        "raw_body": raw_body,
        "timeout_sec": timeout_sec,
    }
    if transport is None:
        return internal_hmac_client.signed_request(**kwargs)
    sender = getattr(transport, "send", None)
    if callable(sender):
        return sender(**kwargs)
    if callable(transport):
        return transport(**kwargs)
    raise SpoolError("invalid_transport")


def _pending_outcome(
    *,
    code: str,
    status: int | None,
    correlation_id: str | None,
    attempts: int,
    attempt: int,
    jitter: Callable[[int], int] | None,
    path: Path,
) -> UploadOutcome:
    return UploadOutcome(
        destination="pending",
        status=status,
        code=code,
        correlation_id=correlation_id,
        attempts=attempts,
        retry_after_seconds=calculate_backoff(attempt, jitter=jitter),
        path=path,
    )


def upload_one(
    pending_artifact: str | Path,
    *,
    transport: object | None = None,
    now: datetime,
    attempt: int = 0,
    jitter: Callable[[int], int] | None = None,
    api_base_url: str = DEFAULT_API_BASE_URL,
    key_id: str = DEFAULT_KEY_ID,
    secret_file: str | Path = DEFAULT_SECRET_FILE,
    timeout_sec: float = DEFAULT_TIMEOUT_SEC,
) -> UploadOutcome:
    artifact_path, root, run_id = _validate_pending_artifact_path(
        pending_artifact
    )
    with _upload_claim(root, run_id) as claimed:
        if not claimed:
            return UploadOutcome(
                destination="pending",
                status=None,
                code="upload_in_progress",
                correlation_id=None,
                attempts=0,
                retry_after_seconds=None,
                path=artifact_path,
            )
        try:
            artifact_raw, sidecar_raw, hash_matches = _read_artifact_pair(
                artifact_path,
                expected_run_id=run_id,
            )
        except SpoolError as exc:
            if exc.code in {"artifact_missing", "sidecar_invalid"}:
                return UploadOutcome(
                    destination="pending",
                    status=None,
                    code=exc.code,
                    correlation_id=None,
                    attempts=0,
                    path=artifact_path,
                )
            raise
        if not hash_matches:
            reason = _reason_bytes(
                status=None,
                code="artifact_hash_mismatch",
                correlation_id=None,
                now=now,
            )
            try:
                destination_path = _transition_pair(
                    artifact_path=artifact_path,
                    root=root,
                    run_id=run_id,
                    artifact_raw=artifact_raw,
                    sidecar_raw=sidecar_raw,
                    destination="quarantine",
                    reason_raw=reason,
                )
            except SpoolError:
                return _pending_outcome(
                    code="spool_transition_failed",
                    status=None,
                    correlation_id=None,
                    attempts=0,
                    attempt=attempt,
                    jitter=jitter,
                    path=artifact_path,
                )
            return UploadOutcome(
                destination="quarantine",
                status=None,
                code="artifact_hash_mismatch",
                correlation_id=None,
                attempts=0,
                path=destination_path,
            )

        original_artifact = artifact_raw
        attempts = 0
        while attempts < 2:
            attempts += 1
            try:
                current_artifact, current_sidecar, current_hash_matches = (
                    _read_artifact_pair(
                        artifact_path,
                        expected_run_id=run_id,
                    )
                )
            except SpoolError as exc:
                return _pending_outcome(
                    code=exc.code,
                    status=None,
                    correlation_id=None,
                    attempts=attempts - 1,
                    attempt=attempt,
                    jitter=jitter,
                    path=artifact_path,
                )
            if (
                not current_hash_matches
                or current_artifact != original_artifact
                or current_sidecar != sidecar_raw
            ):
                reason = _reason_bytes(
                    status=None,
                    code="artifact_hash_mismatch",
                    correlation_id=None,
                    now=now,
                )
                try:
                    destination_path = _transition_pair(
                        artifact_path=artifact_path,
                        root=root,
                        run_id=run_id,
                        artifact_raw=current_artifact,
                        sidecar_raw=current_sidecar,
                        destination="quarantine",
                        reason_raw=reason,
                    )
                except SpoolError:
                    return _pending_outcome(
                        code="spool_transition_failed",
                        status=None,
                        correlation_id=None,
                        attempts=attempts - 1,
                        attempt=attempt,
                        jitter=jitter,
                        path=artifact_path,
                    )
                return UploadOutcome(
                    destination="quarantine",
                    status=None,
                    code="artifact_hash_mismatch",
                    correlation_id=None,
                    attempts=attempts - 1,
                    path=destination_path,
                )
            try:
                response = _invoke_transport(
                    transport,
                    api_base_url=api_base_url,
                    path=RUNS_PATH,
                    key_id=key_id,
                    secret_file=secret_file,
                    raw_body=original_artifact,
                    timeout_sec=timeout_sec,
                )
            except internal_hmac_client.InternalHmacClientError:
                reason = _reason_bytes(
                    status=None,
                    code="blocked_key",
                    correlation_id=None,
                    now=now,
                )
                try:
                    destination_path = _transition_pair(
                        artifact_path=artifact_path,
                        root=root,
                        run_id=run_id,
                        artifact_raw=original_artifact,
                        sidecar_raw=sidecar_raw,
                        destination="blocked",
                        reason_raw=reason,
                    )
                except SpoolError:
                    return _pending_outcome(
                        code="spool_transition_failed",
                        status=None,
                        correlation_id=None,
                        attempts=attempts,
                        attempt=attempt,
                        jitter=jitter,
                        path=artifact_path,
                    )
                return UploadOutcome(
                    destination="blocked",
                    status=None,
                    code="blocked_key",
                    correlation_id=None,
                    attempts=attempts,
                    path=destination_path,
                )
            except (OSError, TimeoutError):
                return _pending_outcome(
                    code="network_error",
                    status=None,
                    correlation_id=None,
                    attempts=attempts,
                    attempt=attempt,
                    jitter=jitter,
                    path=artifact_path,
                )
            status, code, correlation_id = _safe_response_metadata(response)
            if status == 409 and code == "replayed_nonce" and attempts == 1:
                continue
            if status in {200, 201}:
                destination = "archive"
            elif status in {408, 425, 429} or 500 <= status <= 599:
                return _pending_outcome(
                    code=code,
                    status=status,
                    correlation_id=correlation_id,
                    attempts=attempts,
                    attempt=attempt,
                    jitter=jitter,
                    path=artifact_path,
                )
            elif status in {401, 403}:
                destination = "blocked"
            else:
                destination = "quarantine"
            reason = (
                None
                if destination == "archive"
                else _reason_bytes(
                    status=status,
                    code=code,
                    correlation_id=correlation_id,
                    now=now,
                )
            )
            try:
                destination_path = _transition_pair(
                    artifact_path=artifact_path,
                    root=root,
                    run_id=run_id,
                    artifact_raw=original_artifact,
                    sidecar_raw=sidecar_raw,
                    destination=destination,
                    reason_raw=reason,
                )
            except SpoolError:
                failure_code = (
                    "archive_write_failed"
                    if destination == "archive"
                    else "spool_transition_failed"
                )
                return _pending_outcome(
                    code=failure_code,
                    status=status,
                    correlation_id=correlation_id,
                    attempts=attempts,
                    attempt=attempt,
                    jitter=jitter,
                    path=artifact_path,
                )
            return UploadOutcome(
                destination=destination,
                status=status,
                code=code,
                correlation_id=correlation_id,
                attempts=attempts,
                path=destination_path,
            )
    raise SpoolError("upload_state_unreachable")


def _state_artifacts(root: Path, state: str) -> list[Path]:
    result: list[Path] = []
    for path in sorted((root / state).glob("*.json")):
        if path.name.endswith(".reason.json"):
            continue
        try:
            _validate_run_id(path.stem)
        except SpoolError:
            continue
        if path.with_suffix(".sha256").is_file() and path.is_file():
            result.append(path)
    return result


def build_heartbeat(
    spool_root: str | Path,
    *,
    probe_host_id: str,
    now: datetime,
    service_version: str = UPLOADER_VERSION,
    archive_write_ok: bool = True,
    last_error_code: str | None = None,
    disk_usage: Callable[[str | Path], object] = shutil.disk_usage,
) -> dict[str, object]:
    if (
        not isinstance(probe_host_id, str)
        or _HOST_ID_RE.fullmatch(probe_host_id) is None
    ):
        raise SpoolError("invalid_probe_host_id")
    if (
        not isinstance(service_version, str)
        or not 1 <= len(service_version) <= 64
        or any(ord(character) < 33 or ord(character) > 126 for character in service_version)
    ):
        raise SpoolError("invalid_service_version")
    root = ensure_spool_layout(spool_root)
    recover_pending(root)
    pending = _state_artifacts(root, "pending")
    blocked = _state_artifacts(root, "blocked")
    quarantine = _state_artifacts(root, "quarantine")
    oldest_pending_at: str | None = None
    if pending:
        oldest_timestamp = min(path.stat().st_mtime for path in pending)
        oldest_pending_at = _utc_text(
            datetime.fromtimestamp(oldest_timestamp, tz=timezone.utc)
        )
    try:
        usage = disk_usage(root)
        disk_free_bytes = int(getattr(usage, "free"))
        if disk_free_bytes < 1024 * 1024 * 1024:
            disk_state = "critical"
        elif disk_free_bytes < 5 * 1024 * 1024 * 1024:
            disk_state = "low"
        else:
            disk_state = "ok"
    except (OSError, TypeError, ValueError, AttributeError):
        disk_free_bytes = None
        disk_state = "unknown"
    safe_last_error = (
        last_error_code
        if isinstance(last_error_code, str)
        and last_error_code in _ALLOWED_LAST_ERROR_CODES
        else None
    )
    return {
        "schema_version": 1,
        "probe_host_id": probe_host_id,
        "observed_at": _utc_text(now),
        "service_version": service_version,
        "pending_count": len(pending),
        "blocked_count": len(blocked),
        "quarantine_count": len(quarantine),
        "oldest_pending_at": oldest_pending_at,
        "archive_write_ok": bool(archive_write_ok),
        "disk_free_bytes": disk_free_bytes,
        "disk_state": disk_state,
        "last_error_code": safe_last_error,
    }


def send_heartbeat(
    spool_root: str | Path,
    *,
    probe_host_id: str,
    now: datetime,
    service_version: str = UPLOADER_VERSION,
    archive_write_ok: bool = True,
    last_error_code: str | None = None,
    transport: object | None = None,
    api_base_url: str = DEFAULT_API_BASE_URL,
    key_id: str = DEFAULT_KEY_ID,
    secret_file: str | Path = DEFAULT_SECRET_FILE,
    timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    disk_usage: Callable[[str | Path], object] = shutil.disk_usage,
) -> UploadOutcome:
    heartbeat = build_heartbeat(
        spool_root,
        probe_host_id=probe_host_id,
        now=now,
        service_version=service_version,
        archive_write_ok=archive_write_ok,
        last_error_code=last_error_code,
        disk_usage=disk_usage,
    )
    disk_state = str(heartbeat["disk_state"])
    raw = _canonical_json_bytes(heartbeat)
    try:
        response = _invoke_transport(
            transport,
            api_base_url=api_base_url,
            path=HEARTBEAT_PATH,
            key_id=key_id,
            secret_file=secret_file,
            raw_body=raw,
            timeout_sec=timeout_sec,
        )
    except (
        internal_hmac_client.InternalHmacClientError,
        OSError,
        TimeoutError,
    ):
        return UploadOutcome(
            destination="failed",
            status=None,
            code="heartbeat_failed",
            correlation_id=None,
            attempts=1,
            disk_state=disk_state,
        )
    status, code, correlation_id = _safe_response_metadata(response)
    return UploadOutcome(
        destination="sent" if status in {200, 201} else "failed",
        status=status,
        code=code,
        correlation_id=correlation_id,
        attempts=1,
        disk_state=disk_state,
    )


def run_uploader_once(
    *,
    spool_root: str | Path,
    probe_host_id: str,
    now: datetime,
    transport: object | None = None,
    api_base_url: str = DEFAULT_API_BASE_URL,
    key_id: str = DEFAULT_KEY_ID,
    secret_file: str | Path = DEFAULT_SECRET_FILE,
    timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    disk_usage: Callable[[str | Path], object] = shutil.disk_usage,
) -> tuple[list[UploadOutcome], UploadOutcome]:
    outcomes: list[UploadOutcome] = []
    archive_write_ok = True
    last_error_code: str | None = None
    for artifact_path in scan_pending(spool_root):
        try:
            outcome = upload_one(
                artifact_path,
                transport=transport,
                now=now,
                api_base_url=api_base_url,
                key_id=key_id,
                secret_file=secret_file,
                timeout_sec=timeout_sec,
            )
        except SpoolError:
            outcome = UploadOutcome(
                destination="pending",
                status=None,
                code="spool_transition_failed",
                correlation_id=None,
                attempts=0,
                path=artifact_path,
            )
        outcomes.append(outcome)
        if outcome.code == "archive_write_failed":
            archive_write_ok = False
        if outcome.destination in {"pending", "blocked", "quarantine"}:
            last_error_code = (
                outcome.code
                if outcome.code in _ALLOWED_LAST_ERROR_CODES
                else last_error_code
            )
    heartbeat = send_heartbeat(
        spool_root,
        probe_host_id=probe_host_id,
        now=now,
        archive_write_ok=archive_write_ok,
        last_error_code=last_error_code,
        transport=transport,
        api_base_url=api_base_url,
        key_id=key_id,
        secret_file=secret_file,
        timeout_sec=timeout_sec,
        disk_usage=disk_usage,
    )
    return outcomes, heartbeat


def _local_service_failed(
    outcomes: list[UploadOutcome],
    heartbeat: UploadOutcome,
) -> bool:
    if heartbeat.destination != "sent":
        return True
    if heartbeat.disk_state in {"critical", "unknown"}:
        return True
    return any(
        outcome.code in {"archive_write_failed", "spool_transition_failed"}
        for outcome in outcomes
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Upload immutable RU-origin spool artifacts and heartbeat."
    )
    parser.add_argument("--spool-root", default=str(DEFAULT_SPOOL_ROOT))
    parser.add_argument("--probe-host-id", default=DEFAULT_PROBE_HOST_ID)
    parser.add_argument("--api-base-url", default=DEFAULT_API_BASE_URL)
    parser.add_argument("--key-id", default=DEFAULT_KEY_ID)
    parser.add_argument("--secret-file", default=str(DEFAULT_SECRET_FILE))
    parser.add_argument("--timeout-sec", type=float, default=DEFAULT_TIMEOUT_SEC)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        outcomes, heartbeat = run_uploader_once(
            spool_root=Path(args.spool_root),
            probe_host_id=str(args.probe_host_id),
            now=datetime.now(timezone.utc),
            api_base_url=str(args.api_base_url),
            key_id=str(args.key_id),
            secret_file=Path(args.secret_file),
            timeout_sec=float(args.timeout_sec),
        )
    except SpoolError as exc:
        print(exc.code, file=sys.stderr)
        return 1
    if heartbeat.destination != "sent":
        print(heartbeat.code, file=sys.stderr)
        return 1
    if heartbeat.disk_state in {"critical", "unknown"}:
        print(f"disk_{heartbeat.disk_state}", file=sys.stderr)
    return 1 if _local_service_failed(outcomes, heartbeat) else 0


if __name__ == "__main__":
    raise SystemExit(main())
