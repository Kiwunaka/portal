from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import shlex
import subprocess
import sys
import tarfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

import paramiko
from sqlalchemy.engine import URL, make_url

from ssh_host_keys import configure_ssh_host_key_policy


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
BRAIN_SSH_PORT = 29374
GATE_NAME = "postgres_candidate_rehearsal"
REMOTE_SCRATCH_ROOT = "/tmp/pokrov-postgres-candidate-gates"
REMOTE_PYTHON = "/root/portal_bot/venv/bin/python"
REMOTE_RUNNER_TIMEOUT_SECONDS = 29 * 60

SQL_IDENTIFIER_RE = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
COMMIT_RE = re.compile(r"^[a-f0-9]{40}$")
SCRATCH_TOKEN_RE = re.compile(r"^[a-f0-9]{32}$")
RUNNER_ERROR_RE = re.compile(r"^[a-z0-9_]{1,96}$")
SENSITIVE_PATH_RE = re.compile(
    r"(?i)(?:^|/)(?:\.env(?:\..*)?|id_(?:rsa|dsa|ecdsa|ed25519)|"
    r"(?:credentials?|secrets?|passwords?|client_secret)(?:\.[^/]*)?)(?:$|/)|"
    r"(?:\.(?:key|pem|p12|pfx|jks|keystore|kdbx))$"
)
SENSITIVE_KEY_RE = re.compile(
    r"(?i)(?:password|passwd|passphrase|secret|authorization|credential|api[_-]?key|"
    r"private[_-]?key|database[_-]?url|connection[_-]?(?:url|uri|dsn)|(?:^|_)nonce(?:_|$)|"
    r"(?:^|_)(?:customer_id|row_id|row_value)(?:_|$))"
)
SENSITIVE_VALUE_RE = re.compile(
    r"(?i)(?:[a-z][a-z0-9+.-]{1,31}://|"
    r"(?:database_url|password|passwd|passphrase|secret|authorization|credential|api[_-]?key)\s*[:=]|"
    r"bearer\s+[a-z0-9._~+/=-]+|"
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)"
)
MAX_PROTOCOL_FRAME = 16 * 1024 * 1024
MAX_CANDIDATE_ARCHIVE_BYTES = 128 * 1024 * 1024
MAX_CANDIDATE_FILES = 20_000


class GateError(RuntimeError):
    pass


def _is_sensitive_candidate_path(value: str) -> bool:
    normalized = str(PurePosixPath(str(value)))
    if normalized == ".env.example" or normalized.endswith("/.env.example"):
        return False
    return SENSITIVE_PATH_RE.search(normalized) is not None


class RemoteGateError(GateError):
    def __init__(self, error_class: str) -> None:
        self.error_class = error_class
        super().__init__(f"remote_{error_class}_failed")

    def __repr__(self) -> str:
        return f"RemoteGateError({self.error_class!r})"


class ProtocolError(GateError):
    pass


def remote_error(error_class: str, _cause: BaseException | None = None) -> RemoteGateError:
    safe_class = re.sub(r"[^a-z0-9_]+", "_", str(error_class).lower()).strip("_")
    return RemoteGateError(safe_class or "operation")


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, _message: str) -> None:
        self.print_usage(sys.stderr)
        raise SystemExit("invalid_arguments")


@dataclass(frozen=True)
class CandidateArchive:
    path: Path
    sha256: str
    commit: str
    tracked_files: int
    size_bytes: int


@dataclass(frozen=True)
class ProtocolFrame:
    kind: bytes | None
    payload: bytes
    raw: bytes


class PostgresProtocolParser:
    def __init__(self, *, expect_startup: bool) -> None:
        self._buffer = bytearray()
        self._expect_startup = bool(expect_startup)

    def __repr__(self) -> str:
        return (
            f"PostgresProtocolParser(expect_startup={self._expect_startup!r}, "
            f"buffered_bytes={len(self._buffer)})"
        )

    def feed(self, data: bytes) -> list[ProtocolFrame]:
        self._buffer.extend(data)
        frames: list[ProtocolFrame] = []
        while True:
            if self._expect_startup:
                if len(self._buffer) < 4:
                    break
                length = int.from_bytes(self._buffer[:4], "big")
                if length < 8 or length > MAX_PROTOCOL_FRAME:
                    raise ProtocolError("malformed_startup_length")
                if len(self._buffer) < length:
                    break
                raw = bytes(self._buffer[:length])
                del self._buffer[:length]
                frames.append(ProtocolFrame(None, raw[4:], raw))
                self._expect_startup = False
                continue

            if len(self._buffer) < 5:
                break
            length = int.from_bytes(self._buffer[1:5], "big")
            if length < 4 or length > MAX_PROTOCOL_FRAME:
                raise ProtocolError("malformed_packet_length")
            total = 1 + length
            if len(self._buffer) < total:
                break
            raw = bytes(self._buffer[:total])
            del self._buffer[:total]
            frames.append(ProtocolFrame(raw[:1], raw[5:], raw))
        return frames


def is_frontend_commit(frame: ProtocolFrame) -> bool:
    if frame.kind != b"Q":
        return False
    payload = frame.payload[:-1] if frame.payload.endswith(b"\0") else frame.payload
    try:
        statement = payload.decode("ascii")
    except UnicodeDecodeError:
        return False
    return statement.strip().rstrip(";").strip().upper() == "COMMIT"


class CommitAckDropState:
    def __init__(self) -> None:
        self._frontend = PostgresProtocolParser(expect_startup=True)
        self._backend = PostgresProtocolParser(expect_startup=False)
        self.commit_forwarded = False
        self.response_dropped = False

    def __repr__(self) -> str:
        return (
            f"CommitAckDropState(commit_forwarded={self.commit_forwarded!r}, "
            f"response_dropped={self.response_dropped!r})"
        )

    def process_frontend(self, data: bytes) -> bytes:
        for frame in self._frontend.feed(data):
            if is_frontend_commit(frame):
                self.commit_forwarded = True
        return data

    def process_backend(self, data: bytes) -> bytes:
        if self.response_dropped:
            return b""
        delivered = bytearray()
        for frame in self._backend.feed(data):
            command = frame.payload[:-1] if frame.payload.endswith(b"\0") else frame.payload
            if self.commit_forwarded and frame.kind == b"C" and command.strip().upper() == b"COMMIT":
                self.response_dropped = True
                continue
            if not self.response_dropped:
                delivered.extend(frame.raw)
        return bytes(delivered)


def validate_database_selection(
    source: str,
    confirm_source: str,
    target: str,
    confirm_target: str,
) -> tuple[str, str]:
    if source != "portal" or confirm_source != source:
        raise GateError("source_database_guard")
    if not SQL_IDENTIFIER_RE.fullmatch(target):
        raise GateError("target_database_identifier")
    if target != confirm_target:
        raise GateError("target_database_confirmation")
    if not target.endswith("_rehearsal") or target == source:
        raise GateError("target_database_not_rehearsal")
    return source, target


def _git(repo_root: Path, *args: str, text: bool = True) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=text,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise GateError("candidate_git_validation_failed") from exc


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise GateError("candidate_archive_unreadable") from exc
    return digest.hexdigest()


def _validate_tar_member(member: tarfile.TarInfo, *, allowed_roots: set[str]) -> str | None:
    raw_name = str(member.name)
    if "\\" in raw_name or not raw_name or raw_name.startswith("/"):
        raise GateError("candidate_archive_path")
    path = PurePosixPath(raw_name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise GateError("candidate_archive_path")
    if not path.parts or path.parts[0] not in allowed_roots:
        raise GateError("candidate_archive_scope")
    normalized = str(path)
    if normalized != raw_name.rstrip("/"):
        raise GateError("candidate_archive_path")
    if _is_sensitive_candidate_path(normalized):
        raise GateError("candidate_archive_sensitive_path")
    if member.isdir():
        return None
    if not member.isfile() or member.islnk() or member.issym():
        raise GateError("candidate_archive_special_member")
    return normalized


def validate_candidate_archive(
    archive_path: Path | str,
    expected_sha256: str,
    candidate_commit: str,
    *,
    repo_root: Path = REPO_ROOT,
) -> CandidateArchive:
    archive = Path(archive_path).expanduser().resolve()
    root = Path(repo_root).expanduser().resolve()
    expected_digest = str(expected_sha256 or "").lower()
    commit = str(candidate_commit or "").lower()
    if not SHA256_RE.fullmatch(expected_digest):
        raise GateError("candidate_sha256_invalid")
    if not COMMIT_RE.fullmatch(commit):
        raise GateError("candidate_commit_invalid")
    if not archive.is_file() or archive.is_symlink():
        raise GateError("candidate_archive_missing")
    if archive.stat().st_size > MAX_CANDIDATE_ARCHIVE_BYTES:
        raise GateError("candidate_archive_too_large")
    actual_digest = _hash_file(archive)
    if actual_digest != expected_digest:
        raise GateError("candidate_sha256_mismatch")

    head = _git(root, "rev-parse", "HEAD").stdout.strip().lower()
    if head != commit:
        raise GateError("candidate_commit_not_head")
    shared_output = _git(root, "ls-tree", "-r", "--name-only", commit, "--", "shared").stdout
    scopes = ("portal_bot", "shared") if shared_output.strip() else ("portal_bot",)
    dirty = _git(
        root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--",
        *scopes,
    ).stdout
    if dirty.strip():
        raise GateError("candidate_tree_dirty")

    tracked_output = _git(root, "ls-tree", "-r", "--name-only", commit, "--", *scopes).stdout
    tracked = tuple(line.strip() for line in tracked_output.splitlines() if line.strip())
    if not tracked:
        raise GateError("candidate_archive_empty")
    for name in tracked:
        if _is_sensitive_candidate_path(name):
            raise GateError("candidate_archive_sensitive_path")

    try:
        with tarfile.open(archive, "r:*") as candidate_tar:
            archive_files_list: list[str] = []
            total_member_bytes = 0
            for member_index, member in enumerate(candidate_tar, 1):
                if member_index > MAX_CANDIDATE_FILES:
                    raise GateError("candidate_archive_too_many_files")
                total_member_bytes += max(0, int(member.size or 0))
                if total_member_bytes > MAX_CANDIDATE_ARCHIVE_BYTES:
                    raise GateError("candidate_archive_expanded_too_large")
                name = _validate_tar_member(member, allowed_roots=set(scopes))
                if name is not None:
                    archive_files_list.append(name)
            archive_files = tuple(archive_files_list)
    except GateError:
        raise
    except (OSError, tarfile.TarError) as exc:
        raise GateError("candidate_archive_invalid") from exc
    if len(archive_files) != len(set(archive_files)) or tuple(sorted(archive_files)) != tuple(sorted(tracked)):
        raise GateError("candidate_archive_manifest_mismatch")

    expected_archive = _git(root, "archive", "--format=tar", commit, *scopes, text=False).stdout
    if hashlib.sha256(expected_archive).hexdigest() != actual_digest:
        raise GateError("candidate_archive_not_exact_git_archive")
    return CandidateArchive(archive, actual_digest, commit, len(tracked), archive.stat().st_size)


def derive_target_url(live_database_url: str, source: str, target: str) -> URL:
    validate_database_selection(source, source, target, target)
    try:
        live = make_url(str(live_database_url))
    except Exception as exc:
        raise GateError("database_url_invalid") from exc
    if not live.drivername.startswith("postgresql") or live.database != source:
        raise GateError("database_url_source_mismatch")
    return live.set(database=target)


def assert_report_safe(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if SENSITIVE_KEY_RE.search(str(key)):
                raise GateError("report_sensitive_key")
            assert_report_safe(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_report_safe(item)
        return
    if isinstance(value, str) and SENSITIVE_VALUE_RE.search(value):
        raise GateError("report_sensitive_value")


def validate_report_path(path: Path | str) -> Path:
    target = Path(path).expanduser().resolve()
    if target.suffix.lower() != ".json":
        raise GateError("report_extension")
    if target.exists():
        raise GateError("report_exists")
    for candidate in (target.parent, *target.parent.parents):
        if (candidate / ".git").exists():
            raise GateError("report_inside_git")
    return target


def _fsync_parent_directory(path: Path) -> None:
    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _windows_current_user_sid() -> str:
    if os.name != "nt":
        raise GateError("windows_sid_unavailable")
    import ctypes
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    token = wintypes.HANDLE()
    advapi32.OpenProcessToken.argtypes = (
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    )
    advapi32.OpenProcessToken.restype = wintypes.BOOL
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    advapi32.GetTokenInformation.argtypes = (
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    )
    advapi32.GetTokenInformation.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = (ctypes.c_void_p,)
    kernel32.LocalFree.restype = ctypes.c_void_p
    if not advapi32.OpenProcessToken(kernel32.GetCurrentProcess(), 0x0008, ctypes.byref(token)):
        raise GateError("report_owner_unavailable")
    try:
        required = wintypes.DWORD()
        advapi32.GetTokenInformation(token, 1, None, 0, ctypes.byref(required))
        if required.value == 0:
            raise GateError("report_owner_unavailable")
        buffer = ctypes.create_string_buffer(required.value)
        if not advapi32.GetTokenInformation(token, 1, buffer, required, ctypes.byref(required)):
            raise GateError("report_owner_unavailable")
        sid_pointer = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_void_p))[0]
        sid_string = wintypes.LPWSTR()
        advapi32.ConvertSidToStringSidW.argtypes = (
            ctypes.c_void_p,
            ctypes.POINTER(wintypes.LPWSTR),
        )
        advapi32.ConvertSidToStringSidW.restype = wintypes.BOOL
        if not advapi32.ConvertSidToStringSidW(sid_pointer, ctypes.byref(sid_string)):
            raise GateError("report_owner_unavailable")
        try:
            return sid_string.value
        finally:
            kernel32.LocalFree(sid_string)
    finally:
        kernel32.CloseHandle(token)


def _open_private_report_temp(path: Path) -> int:
    if os.name != "nt":
        return os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    import ctypes
    import msvcrt
    from ctypes import wintypes

    descriptor = ctypes.c_void_p()
    sddl = f"D:P(A;;GA;;;{_windows_current_user_sid()})"
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    convert = advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW
    convert.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(wintypes.ULONG),
    )
    convert.restype = wintypes.BOOL
    if not convert(sddl, 1, ctypes.byref(descriptor), None):
        raise GateError("report_temp_security_failed")

    class SecurityAttributes(ctypes.Structure):
        _fields_ = (
            ("nLength", wintypes.DWORD),
            ("lpSecurityDescriptor", ctypes.c_void_p),
            ("bInheritHandle", wintypes.BOOL),
        )

    attributes = SecurityAttributes(ctypes.sizeof(SecurityAttributes), descriptor, False)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(SecurityAttributes),
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE
    handle = create_file(str(path), 0x40000000, 0, ctypes.byref(attributes), 1, 0x80, None)
    kernel32.LocalFree.argtypes = (ctypes.c_void_p,)
    kernel32.LocalFree.restype = ctypes.c_void_p
    kernel32.LocalFree(descriptor)
    if handle == ctypes.c_void_p(-1).value:
        if ctypes.get_last_error() in {80, 183}:
            raise FileExistsError(str(path))
        raise GateError("report_temp_create_failed")
    try:
        return msvcrt.open_osfhandle(int(handle), os.O_WRONLY | os.O_BINARY)
    except Exception:
        kernel32.CloseHandle(handle)
        raise GateError("report_temp_open_failed") from None


def _windows_file_dacl_sddl(path: Path | str) -> str:
    if os.name != "nt":
        raise GateError("windows_dacl_unavailable")
    import ctypes
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    security_descriptor = ctypes.c_void_p()
    advapi32.GetNamedSecurityInfoW.argtypes = (
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    )
    advapi32.GetNamedSecurityInfoW.restype = wintypes.DWORD
    advapi32.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes = (
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.LPWSTR),
        ctypes.POINTER(wintypes.ULONG),
    )
    advapi32.ConvertSecurityDescriptorToStringSecurityDescriptorW.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = (ctypes.c_void_p,)
    kernel32.LocalFree.restype = ctypes.c_void_p
    result = advapi32.GetNamedSecurityInfoW(
        str(path), 1, 0x00000004, None, None, None, None, ctypes.byref(security_descriptor)
    )
    if result != 0:
        raise GateError("report_dacl_inspection_failed")
    rendered = wintypes.LPWSTR()
    try:
        if not advapi32.ConvertSecurityDescriptorToStringSecurityDescriptorW(
            security_descriptor, 1, 0x00000004, ctypes.byref(rendered), None
        ):
            raise GateError("report_dacl_inspection_failed")
        try:
            return rendered.value
        finally:
            kernel32.LocalFree(rendered)
    finally:
        kernel32.LocalFree(security_descriptor)


def write_report_atomic(path: Path | str, report: Mapping[str, Any]) -> None:
    target = validate_report_path(path)
    assert_report_safe(report)
    payload = json.dumps(dict(report), ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    assert_report_safe(payload)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
    descriptor: int | None = None
    try:
        descriptor = _open_private_report_temp(temporary)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            descriptor = None
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError:
            raise GateError("report_exists") from None
        except OSError:
            raise GateError("report_publish_failed") from None
        _fsync_parent_directory(target.parent)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)
        _fsync_parent_directory(target.parent)


def _parse_password(path: Path) -> str:
    try:
        lines = [line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines()]
    except OSError:
        return ""
    for index, line in enumerate(lines):
        if "BRAINnode" not in line:
            continue
        in_key_block = False
        for candidate in lines[index + 1 : index + 30]:
            if candidate.startswith("-----BEGIN ") and candidate.endswith(" KEY-----"):
                in_key_block = True
                continue
            if in_key_block:
                if candidate.startswith("-----END ") and candidate.endswith(" KEY-----"):
                    in_key_block = False
                continue
            if re.search(r"(?:^|\s)(?:ssh-(?:ed25519|rsa|dss)|ecdsa-sha2-|sk-ssh-)", candidate):
                continue
            if candidate:
                return candidate
    return ""


def _connect_ssh(brain_ip: str, password: str) -> paramiko.SSHClient:
    ssh = paramiko.SSHClient()
    configure_ssh_host_key_policy(ssh, allow_trust_on_first_use=False)
    try:
        ssh.connect(
            hostname=brain_ip,
            port=BRAIN_SSH_PORT,
            username="root",
            password=password,
            look_for_keys=False,
            allow_agent=False,
            timeout=15,
            banner_timeout=15,
            auth_timeout=15,
        )
    except Exception as exc:
        try:
            ssh.close()
        finally:
            raise remote_error("ssh_connect", exc) from None
    return ssh


def _drain_channel(channel: Any, *, error_class: str, timeout: float, max_output_bytes: int) -> bytes:
    deadline = time.monotonic() + float(timeout)
    stdout = bytearray()
    stderr_bytes = 0
    while True:
        drained = False
        if channel.recv_ready():
            chunk = channel.recv(32768)
            if chunk:
                stdout.extend(chunk)
                drained = True
        if channel.recv_stderr_ready():
            chunk = channel.recv_stderr(32768)
            if chunk:
                stderr_bytes += len(chunk)
                drained = True
        if len(stdout) + stderr_bytes > max_output_bytes:
            channel.close()
            raise remote_error(f"{error_class}_output")
        if channel.exit_status_ready():
            if not channel.recv_ready() and not channel.recv_stderr_ready():
                code = channel.recv_exit_status()
                if code != 0:
                    raise remote_error(error_class)
                return bytes(stdout)
        if time.monotonic() >= deadline:
            channel.close()
            raise remote_error(f"{error_class}_timeout")
        if not drained:
            time.sleep(0.01)


def _remote_run(
    ssh: paramiko.SSHClient,
    command: str,
    *,
    error_class: str = "operation",
    timeout: float = 60,
    stdin_data: str | None = None,
    max_output_bytes: int = 2 * 1024 * 1024,
) -> str:
    try:
        stdin, stdout, _stderr = ssh.exec_command(command, timeout=timeout)
        if stdin_data is not None:
            stdin.write(stdin_data)
            stdin.flush()
        stdin.close()
        output = _drain_channel(
            stdout.channel,
            error_class=error_class,
            timeout=timeout,
            max_output_bytes=max_output_bytes,
        )
    except RemoteGateError:
        raise
    except Exception as exc:
        raise remote_error(error_class, exc) from None
    return output.decode("utf-8", errors="strict")


def build_remote_command(scratch: str) -> str:
    _validate_scratch_path(scratch)
    return (
        "umask 077; exec timeout --signal=TERM --kill-after=15s "
        f"{REMOTE_RUNNER_TIMEOUT_SECONDS}s {REMOTE_PYTHON} {scratch}/runner.py"
    )


def _validate_scratch_path(path: str) -> str:
    prefix = REMOTE_SCRATCH_ROOT + "/"
    if not path.startswith(prefix) or not SCRATCH_TOKEN_RE.fullmatch(path[len(prefix) :]):
        raise GateError("remote_scratch_path_invalid")
    return path


# The runner is uploaded as a standalone source artifact so the exact candidate
# archive never imports code from the live checkout.
REMOTE_RUNNER_SOURCE = Path(__file__).with_name(
    "remote_postgres_candidate_runner.py"
).read_text(encoding="utf-8")
REMOTE_RUNNER_SHA256 = hashlib.sha256(REMOTE_RUNNER_SOURCE.encode("utf-8")).hexdigest()


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise GateError(f"remote_report_{field}")
    return value


def _exact_keys(value: Any, expected: set[str], field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise GateError(f"remote_report_{field}")
    return value


def _validate_counts(value: Any) -> None:
    counts = _exact_keys(
        value,
        {
            "users",
            "accounts",
            "account_identities",
            "account_devices",
            "auth_sessions",
            "entitlement_grants",
            "account_entitlement_grants",
            "support_tickets",
            "support_ticket_messages",
            "support_attachments",
        },
        "counts",
    )
    for name in (
        "accounts",
        "account_identities",
        "account_devices",
        "auth_sessions",
        "entitlement_grants",
        "account_entitlement_grants",
        "support_ticket_messages",
    ):
        _nonnegative_int(counts[name], name)
    for name in ("users", "support_tickets"):
        group = _exact_keys(counts[name], {"total", "bound", "unbound"}, name)
        total = _nonnegative_int(group["total"], f"{name}_total")
        if _nonnegative_int(group["bound"], f"{name}_bound") + _nonnegative_int(group["unbound"], f"{name}_unbound") != total:
            raise GateError(f"remote_report_{name}_partition")
    attachments = _exact_keys(
        counts["support_attachments"], {"total", "bound", "unbound", "dangling"}, "attachments"
    )
    total = _nonnegative_int(attachments["total"], "attachments_total")
    partition = sum(
        _nonnegative_int(attachments[key], f"attachments_{key}")
        for key in ("bound", "unbound", "dangling")
    )
    if partition != total:
        raise GateError("remote_report_attachments_partition")


def _validate_legacy_entitlement_fingerprint(value: Any, field: str) -> Mapping[str, Any]:
    fingerprint = _exact_keys(
        value,
        {"status", "rows_sha256", "schema_sha256"},
        field,
    )
    if fingerprint["status"] != "PASS":
        raise GateError(f"remote_report_{field}_status")
    for key in ("rows_sha256", "schema_sha256"):
        if not isinstance(fingerprint[key], str) or not SHA256_RE.fullmatch(fingerprint[key]):
            raise GateError(f"remote_report_{field}_{key}")
    return fingerprint


def validate_remote_report(
    report: Any,
    *,
    source: str,
    target: str,
    commit: str,
    archive_sha256: str,
    runner_sha256: str = REMOTE_RUNNER_SHA256,
) -> dict[str, Any]:
    assert_report_safe(report)
    top = _exact_keys(
        report,
        {
            "schema_version",
            "gate",
            "status",
            "candidate",
            "source_database",
            "target_database",
            "checks",
            "durations_ms",
            "synthetic_cleanup",
        },
        "top_level",
    )
    if top["schema_version"] != 1 or top["gate"] != GATE_NAME or top["status"] != "PASS":
        raise GateError("remote_report_identity")
    if top["source_database"] != source or top["target_database"] != target:
        raise GateError("remote_report_database")
    candidate = _exact_keys(
        top["candidate"],
        {"commit", "archive_sha256", "runner_sha256"},
        "candidate",
    )
    if candidate != {
        "commit": commit,
        "archive_sha256": archive_sha256,
        "runner_sha256": runner_sha256,
    }:
        raise GateError("remote_report_candidate")
    if top["synthetic_cleanup"] != "confirmed":
        raise GateError("remote_report_cleanup")

    checks = _exact_keys(
        top["checks"],
        {
            "target_access",
            "pre_migration",
            "ddl_lock_impact",
            "advisory_lock",
            "migration_first",
            "migration_second",
            "schema_contract",
            "post_migration",
            "skip_locked",
            "bind_retry",
            "commit_ack_loss",
        },
        "checks",
    )
    for name in checks:
        if not isinstance(checks[name], Mapping) or checks[name].get("status") != "PASS":
            raise GateError(f"remote_report_check_{name}")
    target_access = _exact_keys(
        checks["target_access"],
        {
            "status",
            "database_identity",
            "session_identity",
            "ordinary_login",
            "database_owner",
            "database_public_access_revoked",
            "schema_usage",
            "schema_create",
            "schema_public_access_revoked",
            "users_select",
            "public_objects_total",
            "public_objects_owned",
        },
        "target_access",
    )
    for name in (
        "database_identity",
        "session_identity",
        "ordinary_login",
        "database_owner",
        "database_public_access_revoked",
        "schema_usage",
        "schema_create",
        "schema_public_access_revoked",
        "users_select",
    ):
        if target_access[name] is not True:
            raise GateError(f"remote_report_target_access_{name}")
    access_total = _nonnegative_int(
        target_access["public_objects_total"], "target_access_objects_total"
    )
    access_owned = _nonnegative_int(
        target_access["public_objects_owned"], "target_access_objects_owned"
    )
    if access_total <= 0 or access_owned != access_total:
        raise GateError("remote_report_target_access_ownership")
    pre = _exact_keys(
        checks["pre_migration"],
        {"status", "schema", "counts", "legacy_entitlement_grants"},
        "pre_migration",
    )
    pre_schema = _exact_keys(pre["schema"], {"tables_present"}, "pre_migration_schema")
    _nonnegative_int(pre_schema["tables_present"], "pre_migration_tables")
    _validate_counts(pre["counts"])
    pre_legacy_entitlements = _validate_legacy_entitlement_fingerprint(
        pre["legacy_entitlement_grants"],
        "pre_legacy_entitlement_grants",
    )
    post = _exact_keys(
        checks["post_migration"],
        {"status", "counts", "legacy_entitlement_grants"},
        "post_migration",
    )
    _validate_counts(post["counts"])
    post_legacy_entitlements = _validate_legacy_entitlement_fingerprint(
        post["legacy_entitlement_grants"],
        "post_legacy_entitlement_grants",
    )
    pre_counts = pre["counts"]
    post_counts = post["counts"]
    for name in ("users", "support_tickets", "support_attachments"):
        if pre_counts[name]["total"] != post_counts[name]["total"]:
            raise GateError(f"remote_report_{name}_total_changed")
    if pre_counts["support_ticket_messages"] != post_counts["support_ticket_messages"]:
        raise GateError("remote_report_support_messages_changed")
    if pre_counts["entitlement_grants"] != post_counts["entitlement_grants"]:
        raise GateError("remote_report_legacy_entitlement_grants_changed")
    if pre_legacy_entitlements != post_legacy_entitlements:
        raise GateError("remote_report_legacy_entitlement_grants_fingerprint_changed")
    if post_counts["users"]["total"] and post_counts["users"]["unbound"] != 0:
        raise GateError("remote_report_users_unbound")
    for name in (
        "accounts",
        "account_identities",
        "account_devices",
        "auth_sessions",
        "account_entitlement_grants",
    ):
        if post_counts[name] < pre_counts[name]:
            raise GateError(f"remote_report_{name}_decreased")

    ddl = _exact_keys(checks["ddl_lock_impact"], {"status", "milliseconds", "sqlstate_class"}, "ddl")
    _nonnegative_int(ddl["milliseconds"], "ddl_milliseconds")
    if ddl["sqlstate_class"] != "55":
        raise GateError("remote_report_ddl_sqlstate")
    _exact_keys(checks["advisory_lock"], {"status"}, "advisory")
    for name in ("migration_first", "migration_second"):
        item = _exact_keys(checks[name], {"status", "milliseconds"}, name)
        _nonnegative_int(item["milliseconds"], f"{name}_milliseconds")
    schema = _exact_keys(
        checks["schema_contract"], {"status", "tables", "columns", "indexes", "markers"}, "schema_contract"
    )
    for key in ("tables", "columns", "indexes", "markers"):
        _nonnegative_int(schema[key], f"schema_{key}")
    if (
        schema["tables"] != 12
        or schema["columns"] != 4
        or schema["indexes"] != 7
        or schema["markers"] != 2
    ):
        raise GateError("remote_report_schema_contract_incomplete")
    skip = _exact_keys(checks["skip_locked"], {"status", "selected", "distinct"}, "skip_locked")
    if _nonnegative_int(skip["selected"], "skip_selected") != 2 or skip["distinct"] is not True:
        raise GateError("remote_report_skip_locked")
    bind = _exact_keys(
        checks["bind_retry"],
        {"status", "winners", "losers", "loser_state", "retry_state", "messages"},
        "bind_retry",
    )
    if (
        bind["winners"] != 1
        or bind["losers"] != 1
        or bind["loser_state"] != "already_bound"
        or bind["retry_state"] != "canonical_existing"
        or bind["messages"] != 1
    ):
        raise GateError("remote_report_bind_retry")
    ack = _exact_keys(
        checks["commit_ack_loss"],
        {"status", "commit_forwarded", "response_dropped", "commit_error", "committed_rows"},
        "commit_ack_loss",
    )
    if (
        ack["commit_forwarded"] is not True
        or ack["response_dropped"] is not True
        or ack["commit_error"] is not True
        or ack["committed_rows"] != 1
    ):
        raise GateError("remote_report_commit_ack")
    durations = _exact_keys(top["durations_ms"], {"total"}, "durations")
    _nonnegative_int(durations["total"], "duration_total")
    return dict(report)


def _execute_remote_gate(
    ssh: paramiko.SSHClient,
    *,
    candidate: CandidateArchive,
    source: str,
    target: str,
) -> dict[str, Any]:
    token = secrets.token_hex(16)
    if not SCRATCH_TOKEN_RE.fullmatch(token):
        raise GateError("remote_scratch_token_invalid")
    scratch = _validate_scratch_path(f"{REMOTE_SCRATCH_ROOT}/{token}")
    sftp = None
    primary_error: RemoteGateError | None = None
    result: dict[str, Any] | None = None
    try:
        create = (
            f"umask 077; install -d -m 0700 -- {shlex.quote(REMOTE_SCRATCH_ROOT)}; "
            f"mkdir -m 0700 -- {shlex.quote(scratch)}"
        )
        _remote_run(ssh, create, error_class="scratch_create", timeout=15)
        try:
            sftp = ssh.open_sftp()
            get_channel = getattr(sftp, "get_channel", None)
            sftp_channel = get_channel() if callable(get_channel) else None
            if sftp_channel is not None:
                sftp_channel.settimeout(120)
            archive_partial = f"{scratch}/candidate.tar.partial"
            archive_final = f"{scratch}/candidate.tar"
            sftp.put(str(candidate.path), archive_partial)
            sftp.chmod(archive_partial, 0o600)
            observed = _remote_run(
                ssh,
                f"sha256sum -- {shlex.quote(archive_partial)}",
                error_class="archive_hash",
                timeout=60,
                max_output_bytes=4096,
            ).strip().split()
            if not observed or observed[0] != candidate.sha256:
                raise remote_error("archive_hash")
            sftp.posix_rename(archive_partial, archive_final)
            runner_partial = f"{scratch}/runner.py.partial"
            runner_final = f"{scratch}/runner.py"
            with sftp.file(runner_partial, "wb") as handle:
                handle.write(REMOTE_RUNNER_SOURCE.encode("utf-8"))
            sftp.chmod(runner_partial, 0o600)
            sftp.posix_rename(runner_partial, runner_final)
        except RemoteGateError:
            raise
        except Exception as exc:
            raise remote_error("archive_upload", exc) from None
        finally:
            if sftp is not None:
                try:
                    sftp.close()
                except Exception:
                    pass

        request = json.dumps(
            {
                "schema_version": 1,
                "source_database": source,
                "target_database": target,
                "candidate": {
                    "commit": candidate.commit,
                    "archive_sha256": candidate.sha256,
                    "runner_sha256": REMOTE_RUNNER_SHA256,
                },
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        raw = _remote_run(
            ssh,
            build_remote_command(scratch),
            error_class="runner",
            timeout=30 * 60,
            stdin_data=request,
            max_output_bytes=2 * 1024 * 1024,
        )
        try:
            decoded = json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise remote_error("runner_report", exc) from None
        if isinstance(decoded, Mapping) and decoded.get("status") == "FAIL":
            if set(decoded) != {
                "schema_version",
                "gate",
                "status",
                "error",
                "synthetic_cleanup",
            }:
                raise remote_error("runner_report")
            safe_error = str(decoded.get("error") or "")
            if (
                decoded.get("schema_version") != 1
                or decoded.get("gate") != GATE_NAME
                or decoded.get("synthetic_cleanup") != "unknown"
                or not RUNNER_ERROR_RE.fullmatch(safe_error)
            ):
                raise remote_error("runner_report")
            raise remote_error(f"runner_{safe_error}")
        result = validate_remote_report(
            decoded,
            source=source,
            target=target,
            commit=candidate.commit,
            archive_sha256=candidate.sha256,
            runner_sha256=REMOTE_RUNNER_SHA256,
        )
    except RemoteGateError as exc:
        primary_error = exc
    except GateError as exc:
        primary_error = remote_error("runner_report", exc)
    finally:
        try:
            _remote_run(
                ssh,
                f"rm -rf -- {scratch}",
                error_class="scratch_cleanup",
                timeout=30,
                max_output_bytes=4096,
            )
        except RemoteGateError as cleanup_error:
            if primary_error is None:
                primary_error = cleanup_error
    if primary_error is not None:
        raise primary_error
    if result is None:
        raise remote_error("runner_report")
    return result


def _apply_gate(
    brain_ip: str,
    password: str,
    *,
    candidate: CandidateArchive,
    source: str,
    target: str,
) -> dict[str, Any]:
    ssh = _connect_ssh(brain_ip, password)
    try:
        return _execute_remote_gate(
            ssh,
            candidate=candidate,
            source=source,
            target=target,
        )
    finally:
        ssh.close()


def _build_parser() -> SafeArgumentParser:
    parser = SafeArgumentParser(description="Run the PostgreSQL candidate gate on a rehearsal database")
    parser.add_argument("--brain-ip", required=True)
    parser.add_argument("--passwords", type=Path, default=DEFAULT_PASSWORDS)
    parser.add_argument("--candidate-archive", type=Path, required=True)
    parser.add_argument("--candidate-sha256", required=True)
    parser.add_argument("--candidate-commit", required=True)
    parser.add_argument("--source-db", required=True)
    parser.add_argument("--confirm-source", required=True)
    parser.add_argument("--target-db", required=True)
    parser.add_argument("--confirm-target", required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        report_path = validate_report_path(args.report)
    except GateError as exc:
        raise SystemExit(str(exc)) from None

    try:
        source, target = validate_database_selection(
            args.source_db,
            args.confirm_source,
            args.target_db,
            args.confirm_target,
        )
        candidate = validate_candidate_archive(
            args.candidate_archive,
            args.candidate_sha256,
            args.candidate_commit,
            repo_root=REPO_ROOT,
        )
        if not args.apply:
            write_report_atomic(
                report_path,
                {
                    "schema_version": 1,
                    "gate": GATE_NAME,
                    "status": "PLAN_ONLY",
                    "ssh": "NOT_REQUESTED",
                    "source_database": source,
                    "target_database": target,
                    "candidate": {
                        "commit": candidate.commit,
                        "archive_sha256": candidate.sha256,
                        "runner_sha256": REMOTE_RUNNER_SHA256,
                        "tracked_files": candidate.tracked_files,
                    },
                },
            )
            sys.stdout.write("PLAN_ONLY\n")
            return 0

        password = _parse_password(args.passwords)
        if not password:
            raise GateError("brain_password_missing")
        result = _apply_gate(
            args.brain_ip,
            password,
            candidate=candidate,
            source=source,
            target=target,
        )
        write_report_atomic(report_path, result)
        sys.stdout.write("PASS\n")
        return 0
    except GateError as exc:
        if args.apply:
            error = str(exc)
            error_class = exc.error_class if isinstance(exc, RemoteGateError) else "local_validation"
            failure = {
                "schema_version": 1,
                "gate": GATE_NAME,
                "status": "FAIL",
                "phase": f"remote_{error_class}" if isinstance(exc, RemoteGateError) else error_class,
                "state": "failed",
                "synthetic_cleanup": "unknown" if isinstance(exc, RemoteGateError) else "not_started",
                "error": error,
            }
            try:
                write_report_atomic(report_path, failure)
            except GateError:
                pass
        raise SystemExit(str(exc)) from None


if __name__ == "__main__":
    raise SystemExit(main())
