from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import os
import re
import secrets
import shutil
import stat
import sys
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
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
    "created",
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
_RUN_SUCCESS_KEYS = {
    "code",
    "run_db_id",
    "run_id",
    "created",
    "current_eligible",
    "correlation_id",
}
_HEARTBEAT_SUCCESS_KEYS = {"code", "correlation_id"}
_ERROR_RESPONSE_CODES_BY_STATUS = {
    400: {"invalid_request"},
    401: {"key_disabled", "key_scope_forbidden"},
    403: {"key_disabled", "key_scope_forbidden"},
    408: {"temporary"},
    409: {"payload_conflict", "replayed_nonce"},
    413: {"request_too_large"},
    422: {"invalid_payload", "unsupported_schema"},
    425: {"temporary"},
    429: {"temporary"},
}
_RETRY_STATE_KEYS = {
    "attempt",
    "next_attempt_at",
    "last_http_status",
    "last_code",
}
_RETRYABLE_CODES = {
    "invalid_success_response",
    "network_error",
    "response_too_large",
    "temporary",
    "unexpected_response",
}
_ALLOWED_LAST_ERROR_CODES = {
    "archive_write_failed",
    "artifact_hash_mismatch",
    "artifact_invalid",
    "blocked_key",
    "disk_critical",
    "disk_low",
    "heartbeat_failed",
    "invalid_success_response",
    "network_error",
    "quarantine_present",
    "response_too_large",
    "spool_recovery_failed",
    "spool_transition_failed",
    "unexpected_response",
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


@dataclass(frozen=True)
class RetryState:
    attempt: int
    next_attempt_at: datetime
    last_http_status: int | None
    last_code: str


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


def recover_pending(
    spool_root: str | Path,
    *,
    now: datetime | None = None,
) -> list[RecoveryIssue]:
    root = ensure_spool_layout(spool_root)
    observed_now = now or datetime.now(timezone.utc)
    pending = root / "pending"
    issues: list[RecoveryIssue] = []
    with _spool_lock(root):
        for artifact_path in sorted(pending.glob("*.json")):
            if artifact_path.name.endswith(".retry.json"):
                continue
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
        for retry_path in sorted(pending.glob("*.retry.json")):
            try:
                run_id = _retry_run_id(retry_path)
                artifact_path = pending / f"{run_id}.json"
                if not artifact_path.exists():
                    issues.append(
                        RecoveryIssue("retry_without_artifact", retry_path)
                    )
                    continue
                _read_retry_state(artifact_path, now=observed_now)
            except SpoolError:
                issues.append(
                    RecoveryIssue("retry_state_invalid", retry_path)
                )
    return issues


def scan_pending(
    spool_root: str | Path,
    *,
    now: datetime | None = None,
) -> list[Path]:
    root = ensure_spool_layout(spool_root)
    observed_now = now or datetime.now(timezone.utc)
    recovery_issues = recover_pending(root, now=observed_now)
    return _scan_complete_pending(
        root,
        now=observed_now,
        excluded_run_ids=_recovery_issue_run_ids(recovery_issues),
    )


def _spool_member_run_id(path: Path) -> str | None:
    for suffix in (".retry.json", ".reason.json", ".sha256", ".json"):
        if not path.name.endswith(suffix):
            continue
        try:
            return _validate_run_id(path.name[: -len(suffix)])
        except SpoolError:
            return None
    return None


def _recovery_issue_run_ids(
    issues: list[RecoveryIssue],
) -> set[str]:
    return {
        run_id
        for issue in issues
        if (run_id := _spool_member_run_id(issue.path)) is not None
    }


def _scan_complete_pending(
    root: Path,
    *,
    now: datetime,
    excluded_run_ids: set[str] | None = None,
) -> list[Path]:
    excluded = excluded_run_ids or set()
    result: list[Path] = []
    for artifact_path in sorted((root / "pending").glob("*.json")):
        if artifact_path.name.endswith((".reason.json", ".retry.json")):
            continue
        try:
            run_id = _validate_run_id(artifact_path.stem)
        except SpoolError:
            continue
        if run_id in excluded:
            continue
        if not artifact_path.with_suffix(".sha256").is_file():
            continue
        try:
            retry_state, _ = _read_retry_state(
                artifact_path,
                now=now,
            )
        except SpoolError:
            continue
        if (
            retry_state is not None
            and _retry_seconds_remaining(retry_state, now=now) > 0
        ):
            continue
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


def _response_status(response: object) -> int | None:
    status = getattr(response, "status", None)
    if (
        isinstance(status, bool)
        or not isinstance(status, int)
        or not 100 <= status <= 599
    ):
        return None
    return status


def _strict_response_object(response: object) -> dict[str, object] | None:
    raw = getattr(response, "body", b"")
    if (
        not isinstance(raw, bytes)
        or not raw
        or len(raw) > MAX_RESPONSE_METADATA_BYTES
    ):
        return None
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except (UnicodeError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def _safe_correlation_id(value: object) -> str | None:
    if (
        isinstance(value, str)
        and _CORRELATION_RE.fullmatch(value) is not None
    ):
        return value
    return None


def _parse_run_success_response(
    response: object,
    *,
    status: int,
    expected_run_id: str,
) -> str | None:
    payload = _strict_response_object(response)
    if payload is None or set(payload) != _RUN_SUCCESS_KEYS:
        return None
    run_db_id = payload["run_db_id"]
    expected_created = status == 201
    if (
        payload["code"] != "created"
        or isinstance(run_db_id, bool)
        or not isinstance(run_db_id, int)
        or run_db_id <= 0
        or run_db_id > 9_223_372_036_854_775_807
        or payload["run_id"] != expected_run_id
        or not isinstance(payload["created"], bool)
        or payload["created"] is not expected_created
        or not isinstance(payload["current_eligible"], bool)
    ):
        return None
    return _safe_correlation_id(payload["correlation_id"])


def _parse_heartbeat_success_response(response: object) -> str | None:
    payload = _strict_response_object(response)
    if payload is None or set(payload) != _HEARTBEAT_SUCCESS_KEYS:
        return None
    if payload["code"] != "created":
        return None
    return _safe_correlation_id(payload["correlation_id"])


def _parse_error_response(
    response: object,
    *,
    status: int,
) -> tuple[str | None, str | None]:
    payload = _strict_response_object(response)
    allowed_codes = (
        {"temporary"}
        if 500 <= status <= 599
        else _ERROR_RESPONSE_CODES_BY_STATUS.get(status, set())
    )
    if payload is None or set(payload) not in (
        {"code"},
        {"code", "correlation_id"},
    ):
        return None, None
    code = payload["code"]
    if not isinstance(code, str) or code not in allowed_codes:
        return None, None
    if "correlation_id" not in payload:
        return code, None
    correlation_id = _safe_correlation_id(payload["correlation_id"])
    if correlation_id is None:
        return None, None
    return code, correlation_id


def _retryable_http_status(status: int) -> bool:
    return status in {408, 425, 429} or 500 <= status <= 599


def _terminal_destination(status: int, code: str) -> str | None:
    if (
        status in {401, 403}
        and code in {"key_disabled", "key_scope_forbidden"}
    ):
        return "blocked"
    if (
        (status == 400 and code == "invalid_request")
        or (
            status == 409
            and code in {"payload_conflict", "replayed_nonce"}
        )
        or (status == 413 and code == "request_too_large")
        or (
            status == 422
            and code in {"invalid_payload", "unsupported_schema"}
        )
    ):
        return "quarantine"
    return None


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


def _parse_utc_text(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    normalized = parsed.astimezone(timezone.utc)
    if normalized.utcoffset() != timezone.utc.utcoffset(normalized):
        return None
    return normalized


def _retry_path(artifact_path: Path) -> Path:
    return artifact_path.with_suffix(".retry.json")


def _retry_run_id(path: Path) -> str:
    suffix = ".retry.json"
    if not path.name.endswith(suffix):
        raise SpoolError("retry_state_invalid")
    return _validate_run_id(path.name[: -len(suffix)])


def _retry_state_bytes(
    *,
    attempt: int,
    next_attempt_at: datetime,
    last_http_status: int | None,
    last_code: str,
) -> bytes:
    return _canonical_json_bytes(
        {
            "attempt": attempt,
            "next_attempt_at": _utc_text(next_attempt_at),
            "last_http_status": last_http_status,
            "last_code": last_code,
        }
    )


def _parse_retry_state(
    raw: bytes,
    *,
    now: datetime | None = None,
) -> RetryState:
    if not raw or len(raw) > 512:
        raise SpoolError("retry_state_invalid")
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except (UnicodeError, ValueError) as exc:
        raise SpoolError("retry_state_invalid") from exc
    if not isinstance(payload, dict) or set(payload) != _RETRY_STATE_KEYS:
        raise SpoolError("retry_state_invalid")
    attempt = payload["attempt"]
    status = payload["last_http_status"]
    code = payload["last_code"]
    next_attempt_at = _parse_utc_text(payload["next_attempt_at"])
    if (
        isinstance(attempt, bool)
        or not isinstance(attempt, int)
        or not 1 <= attempt <= 63
        or (
            status is not None
            and (
                isinstance(status, bool)
                or not isinstance(status, int)
                or not 100 <= status <= 599
            )
        )
        or not isinstance(code, str)
        or code not in _RETRYABLE_CODES
        or next_attempt_at is None
    ):
        raise SpoolError("retry_state_invalid")
    status_is_retryable = (
        status in {408, 425, 429}
        or (
            isinstance(status, int)
            and not isinstance(status, bool)
            and 500 <= status <= 599
        )
    )
    if (
        (code in {"network_error", "response_too_large"} and status is not None)
        or (
            code == "invalid_success_response"
            and status not in {200, 201}
        )
        or (code == "temporary" and not status_is_retryable)
    ):
        raise SpoolError("retry_state_invalid")
    if now is not None:
        if now.tzinfo is None or now.utcoffset() is None:
            raise SpoolError("invalid_clock")
        if (
            next_attempt_at
            > now.astimezone(timezone.utc) + timedelta(seconds=3660)
        ):
            raise SpoolError("retry_state_invalid")
    return RetryState(
        attempt=attempt,
        next_attempt_at=next_attempt_at,
        last_http_status=status,
        last_code=code,
    )


def _read_retry_state(
    artifact_path: Path,
    *,
    now: datetime | None = None,
) -> tuple[RetryState | None, bytes | None]:
    path = _retry_path(artifact_path)
    if not _path_exists(path):
        return None, None
    try:
        raw = _read_regular_file(
            path,
            maximum=512,
            symlink_code="retry_state_symlink",
            invalid_code="retry_state_invalid",
        )
    except SpoolError as exc:
        if exc.code == "artifact_missing":
            return None, None
        raise
    return _parse_retry_state(raw, now=now), raw


def _persist_retry_state(
    *,
    artifact_path: Path,
    root: Path,
    previous_attempts: int,
    now: datetime,
    status: int | None,
    code: str,
    jitter: Callable[[int], int] | None,
) -> int:
    if code not in _RETRYABLE_CODES:
        raise SpoolError("retry_state_invalid")
    delay = calculate_backoff(previous_attempts, jitter=jitter)
    next_attempt_at = now.astimezone(timezone.utc) + timedelta(
        seconds=delay
    )
    raw = _retry_state_bytes(
        attempt=min(63, previous_attempts + 1),
        next_attempt_at=next_attempt_at,
        last_http_status=status,
        last_code=code,
    )
    with _spool_lock(root):
        if not artifact_path.exists():
            raise SpoolError("artifact_missing")
        _atomic_write_private(_retry_path(artifact_path), raw)
    return delay


def _retry_seconds_remaining(state: RetryState, *, now: datetime) -> int:
    if now.tzinfo is None or now.utcoffset() is None:
        raise SpoolError("invalid_clock")
    remaining = (
        state.next_attempt_at - now.astimezone(timezone.utc)
    ).total_seconds()
    return max(0, int(math.ceil(remaining)))


def _reason_metadata(raw: bytes) -> dict[str, object] | None:
    if not raw or len(raw) > 1024:
        return None
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except (UnicodeError, ValueError):
        return None
    if not isinstance(payload, dict) or set(payload) != {
        "status",
        "code",
        "correlation_id",
        "observed_at",
    }:
        return None
    status = payload["status"]
    if (
        status is not None
        and (
            isinstance(status, bool)
            or not isinstance(status, int)
            or not 100 <= status <= 599
        )
    ):
        return None
    code = payload["code"]
    if (
        not isinstance(code, str)
        or code not in _KNOWN_RESPONSE_CODES | _ALLOWED_LAST_ERROR_CODES
    ):
        return None
    correlation_id = payload["correlation_id"]
    if (
        correlation_id is not None
        and _safe_correlation_id(correlation_id) is None
    ):
        return None
    if _parse_utc_text(payload["observed_at"]) is None:
        return None
    return payload


def _reason_is_compatible(existing_raw: bytes, requested_raw: bytes) -> bool:
    existing = _reason_metadata(existing_raw)
    requested = _reason_metadata(requested_raw)
    return (
        existing is not None
        and requested is not None
        and existing["status"] == requested["status"]
        and existing["code"] == requested["code"]
    )


def _path_exists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _read_transition_member(path: Path, *, maximum: int) -> bytes:
    return _read_regular_file(
        path,
        maximum=maximum,
        symlink_code="destination_symlink",
        invalid_code="destination_invalid",
    )


def _cleanup_created_members(
    members: list[tuple[Path, bytes]],
    *,
    directory: Path,
) -> None:
    for path, expected_raw in reversed(members):
        try:
            existing = _read_transition_member(
                path,
                maximum=max(len(expected_raw), 128),
            )
            if existing == expected_raw:
                path.unlink()
        except (OSError, SpoolError):
            pass
    try:
        _fsync_directory(directory)
    except OSError:
        pass


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
    source_retry = _retry_path(artifact_path)
    destination_members: list[tuple[Path, bytes, bool]] = []
    if reason_raw is not None:
        destination_members.append((destination_reason, reason_raw, True))
    destination_members.extend(
        [
            (destination_artifact, artifact_raw, False),
            (destination_sidecar, sidecar_raw, False),
        ]
    )
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
        retry_raw: bytes | None = None
        if _path_exists(source_retry):
            retry_raw = _read_regular_file(
                source_retry,
                maximum=512,
                symlink_code="retry_state_symlink",
                invalid_code="retry_state_invalid",
            )
        created_members: list[tuple[Path, bytes]] = []
        try:
            for (
                destination_path,
                destination_raw,
                is_reason,
            ) in destination_members:
                existed = _path_exists(destination_path)
                if existed:
                    existing = _read_transition_member(
                        destination_path,
                        maximum=max(len(destination_raw), 1024),
                    )
                    if is_reason:
                        if not _reason_is_compatible(
                            existing,
                            destination_raw,
                        ):
                            raise SpoolError("destination_reason_conflict")
                    elif existing != destination_raw:
                        raise SpoolError("destination_conflict")
                    continue
                try:
                    _atomic_write_private(
                        destination_path,
                        destination_raw,
                    )
                except SpoolError:
                    if _path_exists(destination_path):
                        created_members.append(
                            (destination_path, destination_raw)
                        )
                    raise
                created_members.append((destination_path, destination_raw))
            _fsync_directory(destination_dir)
        except (OSError, SpoolError) as exc:
            _cleanup_created_members(
                created_members,
                directory=destination_dir,
            )
            raise SpoolError("destination_durability_failed") from exc
        try:
            if retry_raw is not None:
                source_retry.unlink()
            source_sidecar.unlink()
            artifact_path.unlink()
            _fsync_directory(artifact_path.parent)
        except OSError as exc:
            restore_members = [
                (artifact_path, artifact_raw),
                (source_sidecar, sidecar_raw),
            ]
            if retry_raw is not None:
                restore_members.append((source_retry, retry_raw))
            for source_path, source_raw in restore_members:
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


def _terminal_reason_matches_destination(
    destination: str,
    metadata: dict[str, object],
) -> bool:
    status = metadata["status"]
    code = metadata["code"]
    if destination == "blocked":
        return (
            status in {401, 403}
            or (status is None and code == "blocked_key")
        )
    if destination == "quarantine":
        return not (
            status in {200, 201, 401, 403, 408, 425, 429}
            or (isinstance(status, int) and 500 <= status <= 599)
        )
    return False


def _resume_terminal_transition(
    *,
    artifact_path: Path,
    root: Path,
    run_id: str,
    artifact_raw: bytes,
    sidecar_raw: bytes,
) -> UploadOutcome | None:
    existing_states: list[
        tuple[str, Path, Path, Path, bytes | None]
    ] = []
    for destination in ("archive", "blocked", "quarantine"):
        destination_dir = root / destination
        destination_artifact = destination_dir / f"{run_id}.json"
        destination_sidecar = destination_dir / f"{run_id}.sha256"
        destination_reason = destination_dir / f"{run_id}.reason.json"
        members_exist = any(
            _path_exists(path)
            for path in (
                destination_artifact,
                destination_sidecar,
                destination_reason,
            )
        )
        if not members_exist:
            continue
        reason_raw: bytes | None = None
        if destination == "archive":
            if _path_exists(destination_reason):
                raise SpoolError("archive_reason_conflict")
        else:
            if not _path_exists(destination_reason):
                raise SpoolError("terminal_reason_missing")
            reason_raw = _read_transition_member(
                destination_reason,
                maximum=1024,
            )
            metadata = _reason_metadata(reason_raw)
            if (
                metadata is None
                or not _terminal_reason_matches_destination(
                    destination,
                    metadata,
                )
            ):
                raise SpoolError("terminal_reason_invalid")
        existing_states.append(
            (
                destination,
                destination_artifact,
                destination_sidecar,
                destination_reason,
                reason_raw,
            )
        )
    if not existing_states:
        return None
    if len(existing_states) != 1:
        raise SpoolError("multiple_terminal_states")
    destination, _, _, _, reason_raw = existing_states[0]
    destination_path = _transition_pair(
        artifact_path=artifact_path,
        root=root,
        run_id=run_id,
        artifact_raw=artifact_raw,
        sidecar_raw=sidecar_raw,
        destination=destination,
        reason_raw=reason_raw,
    )
    if reason_raw is None:
        return UploadOutcome(
            destination=destination,
            status=None,
            code="created",
            correlation_id=None,
            attempts=0,
            path=destination_path,
        )
    metadata = _reason_metadata(reason_raw)
    if metadata is None:  # pragma: no cover - checked above
        raise SpoolError("terminal_reason_invalid")
    return UploadOutcome(
        destination=destination,
        status=(
            int(metadata["status"])
            if metadata["status"] is not None
            else None
        ),
        code=str(metadata["code"]),
        correlation_id=(
            str(metadata["correlation_id"])
            if metadata["correlation_id"] is not None
            else None
        ),
        attempts=0,
        path=destination_path,
    )


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


def _retryable_pending_outcome(
    *,
    artifact_path: Path,
    root: Path,
    code: str,
    status: int | None,
    correlation_id: str | None,
    attempts: int,
    previous_attempts: int,
    now: datetime,
    jitter: Callable[[int], int] | None,
) -> UploadOutcome:
    try:
        delay = _persist_retry_state(
            artifact_path=artifact_path,
            root=root,
            previous_attempts=previous_attempts,
            now=now,
            status=status,
            code=code,
            jitter=jitter,
        )
    except SpoolError:
        return UploadOutcome(
            destination="pending",
            status=status,
            code="spool_recovery_failed",
            correlation_id=correlation_id,
            attempts=attempts,
            path=artifact_path,
        )
    return UploadOutcome(
        destination="pending",
        status=status,
        code=code,
        correlation_id=correlation_id,
        attempts=attempts,
        retry_after_seconds=delay,
        path=artifact_path,
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
    _utc_text(now)
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

        try:
            resumed = _resume_terminal_transition(
                artifact_path=artifact_path,
                root=root,
                run_id=run_id,
                artifact_raw=artifact_raw,
                sidecar_raw=sidecar_raw,
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
        if resumed is not None:
            return resumed

        try:
            retry_state, _ = _read_retry_state(
                artifact_path,
                now=now,
            )
        except SpoolError:
            return UploadOutcome(
                destination="pending",
                status=None,
                code="spool_recovery_failed",
                correlation_id=None,
                attempts=0,
                path=artifact_path,
            )
        if retry_state is not None:
            remaining = _retry_seconds_remaining(retry_state, now=now)
            if remaining > 0:
                return UploadOutcome(
                    destination="pending",
                    status=retry_state.last_http_status,
                    code="retry_not_due",
                    correlation_id=None,
                    attempts=0,
                    retry_after_seconds=remaining,
                    path=artifact_path,
                )
            previous_attempts = retry_state.attempt
        else:
            previous_attempts = attempt

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
            except internal_hmac_client.InternalHmacClientError as exc:
                if exc.code == "response_too_large":
                    return _retryable_pending_outcome(
                        artifact_path=artifact_path,
                        root=root,
                        code="response_too_large",
                        status=None,
                        correlation_id=None,
                        attempts=attempts,
                        previous_attempts=previous_attempts,
                        now=now,
                        jitter=jitter,
                    )
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
                return _retryable_pending_outcome(
                    artifact_path=artifact_path,
                    root=root,
                    code="network_error",
                    status=None,
                    correlation_id=None,
                    attempts=attempts,
                    previous_attempts=previous_attempts,
                    now=now,
                    jitter=jitter,
                )
            status = _response_status(response)
            if status in {200, 201}:
                correlation_id = _parse_run_success_response(
                    response,
                    status=status,
                    expected_run_id=run_id,
                )
                if correlation_id is None:
                    return _retryable_pending_outcome(
                        artifact_path=artifact_path,
                        root=root,
                        code="invalid_success_response",
                        status=status,
                        correlation_id=None,
                        attempts=attempts,
                        previous_attempts=previous_attempts,
                        now=now,
                        jitter=jitter,
                    )
                code = "created"
                destination = "archive"
            else:
                if status is None:
                    return _retryable_pending_outcome(
                        artifact_path=artifact_path,
                        root=root,
                        code="unexpected_response",
                        status=None,
                        correlation_id=None,
                        attempts=attempts,
                        previous_attempts=previous_attempts,
                        now=now,
                        jitter=jitter,
                    )
                code, correlation_id = _parse_error_response(
                    response,
                    status=status,
                )
                if code is None:
                    return _retryable_pending_outcome(
                        artifact_path=artifact_path,
                        root=root,
                        code="unexpected_response",
                        status=status,
                        correlation_id=None,
                        attempts=attempts,
                        previous_attempts=previous_attempts,
                        now=now,
                        jitter=jitter,
                    )
                if status == 409 and code == "replayed_nonce" and attempts == 1:
                    continue
                if _retryable_http_status(status):
                    return _retryable_pending_outcome(
                        artifact_path=artifact_path,
                        root=root,
                        code=code,
                        status=status,
                        correlation_id=correlation_id,
                        attempts=attempts,
                        previous_attempts=previous_attempts,
                        now=now,
                        jitter=jitter,
                    )
                destination = _terminal_destination(status, code)
                if destination is None:
                    return _retryable_pending_outcome(
                        artifact_path=artifact_path,
                        root=root,
                        code="unexpected_response",
                        status=status,
                        correlation_id=None,
                        attempts=attempts,
                        previous_attempts=previous_attempts,
                        now=now,
                        jitter=jitter,
                    )
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


def _state_artifacts(
    root: Path,
    state: str,
    *,
    require_sidecar: bool = True,
) -> list[Path]:
    result: list[Path] = []
    for path in sorted((root / state).glob("*.json")):
        if path.name.endswith(".reason.json"):
            continue
        try:
            _validate_run_id(path.stem)
        except SpoolError:
            continue
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            continue
        if require_sidecar and not path.with_suffix(".sha256").is_file():
            continue
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
    recovery_failed: bool = False,
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
    recovery_issues = recover_pending(root, now=now)
    recovery_failed = recovery_failed or bool(recovery_issues)
    pending = _state_artifacts(root, "pending", require_sidecar=False)
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
    if recovery_failed:
        archive_write_ok = False
        safe_last_error = "spool_recovery_failed"
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
    recovery_failed: bool = False,
) -> UploadOutcome:
    heartbeat = build_heartbeat(
        spool_root,
        probe_host_id=probe_host_id,
        now=now,
        service_version=service_version,
        archive_write_ok=archive_write_ok,
        last_error_code=last_error_code,
        disk_usage=disk_usage,
        recovery_failed=recovery_failed,
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
    status = _response_status(response)
    if status in {200, 201}:
        correlation_id = _parse_heartbeat_success_response(response)
        if correlation_id is None:
            return UploadOutcome(
                destination="failed",
                status=status,
                code="invalid_success_response",
                correlation_id=None,
                attempts=1,
                disk_state=disk_state,
            )
        code = "created"
    else:
        if status is None:
            code, correlation_id = "unexpected_response", None
        else:
            code, correlation_id = _parse_error_response(
                response,
                status=status,
            )
            if code is None:
                code, correlation_id = "unexpected_response", None
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
    jitter: Callable[[int], int] | None = None,
) -> tuple[list[UploadOutcome], UploadOutcome]:
    root = ensure_spool_layout(spool_root)
    recovery_issues = recover_pending(root, now=now)
    outcomes: list[UploadOutcome] = [
        UploadOutcome(
            destination="pending",
            status=None,
            code="spool_recovery_failed",
            correlation_id=None,
            attempts=0,
            path=issue.path,
        )
        for issue in recovery_issues
    ]
    archive_write_ok = not recovery_issues
    last_error_code: str | None = (
        "spool_recovery_failed" if recovery_issues else None
    )
    for artifact_path in _scan_complete_pending(
        root,
        now=now,
        excluded_run_ids=_recovery_issue_run_ids(recovery_issues),
    ):
        try:
            outcome = upload_one(
                artifact_path,
                transport=transport,
                now=now,
                api_base_url=api_base_url,
                key_id=key_id,
                secret_file=secret_file,
                timeout_sec=timeout_sec,
                jitter=jitter,
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
        recovery_failed=bool(recovery_issues),
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
        outcome.code
        in {
            "archive_write_failed",
            "spool_recovery_failed",
            "spool_transition_failed",
        }
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
