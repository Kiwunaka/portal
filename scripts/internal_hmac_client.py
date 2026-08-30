from __future__ import annotations

import errno
import os
import re
import secrets
import stat
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


SCRIPT_DIR = Path(__file__).resolve().parent
PORTAL_DIR = SCRIPT_DIR.parent / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))

from internal_request_auth import normalize_signed_path, sign_internal_request  # noqa: E402


MIN_SECRET_BYTES = 16
MAX_SECRET_BYTES = 512
MAX_RESPONSE_BYTES = 1024 * 1024
_KEY_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class InternalHmacClientError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = str(code)
        super().__init__(self.code)


@dataclass(frozen=True)
class InternalResponse:
    status: int
    body: bytes
    headers: Mapping[str, str]


class _RejectRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        request,
        fp,
        code,
        message,
        headers,
        new_url,
    ):
        return None


def _open_windows_secret_descriptor(path: Path) -> int:
    import ctypes
    import msvcrt
    from ctypes import wintypes

    generic_read = 0x80000000
    file_share_read = 0x00000001
    open_existing = 3
    file_attribute_directory = 0x00000010
    file_attribute_reparse_point = 0x00000400
    file_flag_open_reparse_point = 0x00200000
    file_flag_backup_semantics = 0x02000000
    file_attribute_tag_info_class = 9
    invalid_handle_value = ctypes.c_void_p(-1).value

    class FileAttributeTagInfo(ctypes.Structure):
        _fields_ = [
            ("file_attributes", wintypes.DWORD),
            ("reparse_tag", wintypes.DWORD),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE
    get_file_information = kernel32.GetFileInformationByHandleEx
    get_file_information.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    get_file_information.restype = wintypes.BOOL
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [wintypes.HANDLE]
    close_handle.restype = wintypes.BOOL

    handle_value = create_file(
        os.fspath(path),
        generic_read,
        file_share_read,
        None,
        open_existing,
        file_flag_open_reparse_point | file_flag_backup_semantics,
        None,
    )
    if handle_value == invalid_handle_value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        attribute_info = FileAttributeTagInfo()
        if not get_file_information(
            handle_value,
            file_attribute_tag_info_class,
            ctypes.byref(attribute_info),
            ctypes.sizeof(attribute_info),
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        if attribute_info.file_attributes & file_attribute_reparse_point:
            raise InternalHmacClientError("secret_file_symlink")
        if attribute_info.file_attributes & file_attribute_directory:
            raise InternalHmacClientError("secret_file_not_regular")
        descriptor = msvcrt.open_osfhandle(
            int(handle_value),
            os.O_RDONLY | getattr(os, "O_BINARY", 0),
        )
        handle_value = None
        return descriptor
    finally:
        if handle_value is not None:
            close_handle(handle_value)


def _open_secret_descriptor(path: Path) -> int:
    if os.name == "nt":
        return _open_windows_secret_descriptor(path)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if not nofollow:
        raise InternalHmacClientError("secret_file_no_follow_unavailable")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | nofollow
    return os.open(path, flags)


def _posix_secret_permissions_allowed(
    metadata,
    *,
    effective_gid: int,
    supplementary_groups: set[int],
) -> bool:
    mode = stat.S_IMODE(metadata.st_mode)
    if mode & 0o007:
        return False
    group_bits = mode & 0o070
    if group_bits == 0:
        return True
    return (
        group_bits == 0o040
        and int(metadata.st_uid) == 0
        and int(metadata.st_gid) in ({int(effective_gid)} | supplementary_groups)
    )


def read_secret_file(secret_file: str | Path) -> bytes:
    path = Path(secret_file)
    descriptor: int | None = None
    try:
        descriptor = _open_secret_descriptor(path)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise InternalHmacClientError("secret_file_not_regular")
        if os.name != "nt" and not _posix_secret_permissions_allowed(
            metadata,
            effective_gid=os.getegid(),
            supplementary_groups={int(value) for value in os.getgroups()},
        ):
            raise InternalHmacClientError("secret_file_permissions")
        chunks: list[bytes] = []
        remaining = MAX_SECRET_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        secret = b"".join(chunks)
    except InternalHmacClientError:
        raise
    except OSError as exc:
        if exc.errno in {errno.ELOOP, errno.EMLINK}:
            raise InternalHmacClientError("secret_file_symlink") from exc
        raise InternalHmacClientError("secret_file_unavailable") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    if not MIN_SECRET_BYTES <= len(secret) <= MAX_SECRET_BYTES:
        raise InternalHmacClientError("invalid_secret_length")
    return secret


def build_signed_headers(
    *,
    secret: bytes,
    key_id: str,
    method: str,
    path: str,
    raw_body: bytes,
) -> dict[str, str]:
    if not isinstance(key_id, str) or _KEY_ID_RE.fullmatch(key_id) is None:
        raise InternalHmacClientError("invalid_key_id")
    timestamp = str(int(time.time()))
    nonce = secrets.token_urlsafe(32)
    signature = sign_internal_request(
        secret,
        method,
        path,
        timestamp,
        nonce,
        raw_body,
    )
    return {
        "X-Internal-Key-Id": key_id,
        "X-Internal-Timestamp": timestamp,
        "X-Internal-Nonce": nonce,
        "X-Internal-Signature": signature,
    }


def _request_url(api_base_url: str, path: str) -> str:
    parsed = urllib.parse.urlsplit(str(api_base_url or "").strip())
    if (
        parsed.scheme.lower() != "https"
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise InternalHmacClientError("invalid_api_base_url")
    return urllib.parse.urlunsplit(
        ("https", parsed.netloc, path, "", "")
    )


def _read_response_body(response) -> bytes:
    body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise InternalHmacClientError("response_too_large")
    return body


def _response_headers(response) -> dict[str, str]:
    headers = getattr(response, "headers", None)
    if headers is None:
        return {}
    items = getattr(headers, "items", None)
    if callable(items):
        return {str(name): str(value) for name, value in items()}
    if isinstance(headers, Mapping):
        return {str(name): str(value) for name, value in headers.items()}
    return {}


def signed_request(
    *,
    api_base_url: str,
    method: str,
    path: str,
    key_id: str,
    secret_file: str | Path,
    raw_body: bytes,
    timeout_sec: float,
) -> InternalResponse:
    if not isinstance(method, str) or method not in {"GET", "POST"}:
        raise InternalHmacClientError("unsupported_method")
    canonical_method = method
    try:
        canonical_path = normalize_signed_path(path)
    except (TypeError, ValueError) as exc:
        raise InternalHmacClientError("invalid_signed_path") from exc
    if canonical_path != path:
        raise InternalHmacClientError("noncanonical_signed_path")
    if not isinstance(raw_body, bytes):
        raise TypeError("raw_body must be bytes")
    if canonical_method == "GET" and raw_body:
        raise InternalHmacClientError("get_body_not_allowed")
    secret = read_secret_file(secret_file)
    headers = build_signed_headers(
        secret=secret,
        key_id=key_id,
        method=canonical_method,
        path=canonical_path,
        raw_body=raw_body,
    )
    headers["Accept"] = "application/json"
    request_data = None if canonical_method == "GET" else raw_body
    if canonical_method == "POST":
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        _request_url(api_base_url, canonical_path),
        data=request_data,
        headers=headers,
        method=canonical_method,
    )
    opener = urllib.request.build_opener(_RejectRedirectHandler())
    try:
        with opener.open(request, timeout=float(timeout_sec)) as response:
            status_value = getattr(response, "status", None)
            if status_value is None:
                status_value = response.getcode()
            status = int(status_value)
            return InternalResponse(
                status=status,
                body=_read_response_body(response),
                headers=_response_headers(response),
            )
    except urllib.error.HTTPError as exc:
        try:
            body = _read_response_body(exc)
        finally:
            exc.close()
        return InternalResponse(
            status=int(exc.code),
            body=body,
            headers=_response_headers(exc),
        )
