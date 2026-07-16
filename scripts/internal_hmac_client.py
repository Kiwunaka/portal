from __future__ import annotations

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


def read_secret_file(secret_file: str | Path) -> bytes:
    path = Path(secret_file)
    try:
        with path.open("rb") as handle:
            metadata = os.fstat(handle.fileno())
            if not stat.S_ISREG(metadata.st_mode):
                raise InternalHmacClientError("secret_file_not_regular")
            if os.name != "nt" and stat.S_IMODE(metadata.st_mode) & 0o077:
                raise InternalHmacClientError("secret_file_permissions")
            secret = handle.read(MAX_SECRET_BYTES + 1)
    except InternalHmacClientError:
        raise
    except OSError as exc:
        raise InternalHmacClientError("secret_file_unavailable") from exc
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
    try:
        with urllib.request.urlopen(request, timeout=float(timeout_sec)) as response:
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
