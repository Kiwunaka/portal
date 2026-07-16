from __future__ import annotations

import ast
import hashlib
import hmac
import inspect
import json
import sqlite3
import sys
import threading
from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from pathlib import Path
from queue import Queue
from types import SimpleNamespace

import pytest
from sqlalchemy import Column, Integer, String, create_engine, event, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declarative_base, sessionmaker


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))

import internal_request_auth as auth_module  # noqa: E402
import models  # noqa: E402
from internal_request_auth import (  # noqa: E402
    AuthenticatedInternalRequest,
    InternalAuthError,
    InternalServiceKey,
    authenticate_internal_request,
    load_internal_service_key_registry,
    normalize_signed_path,
    sign_internal_request,
    signature_preimage,
)


RUNS_PATH = "/api/internal/probes/ru-origin/runs"
NOW = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
RAW_BODY = b'{"schema_version":2,"probe_host":{"id":"mini"}}'
ACTIVE_KEY = InternalServiceKey(
    key_id="ru-probe-mini-v1",
    secret=b"test-secret-not-for-production",
    subject="mini",
    scopes=frozenset({"ru_probe:ingest", "ru_probe:manifest"}),
    origins=frozenset({"ru"}),
    enabled=True,
)

_TEST_BASE = declarative_base()


class PendingUnrelatedRow(_TEST_BASE):
    __tablename__ = "test_pending_unrelated_rows"

    id = Column(Integer, primary_key=True)
    value = Column(String(32), unique=True, nullable=False)


@pytest.fixture
def registry() -> dict[str, InternalServiceKey]:
    return {ACTIVE_KEY.key_id: ACTIVE_KEY}


@pytest.fixture
def session_factory(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'internal-auth.db').as_posix()}")
    models.InternalIngestNonce.__table__.create(engine)
    PendingUnrelatedRow.__table__.create(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        engine.dispose()


@pytest.fixture
def session(session_factory):
    value = session_factory()
    try:
        yield value
    finally:
        value.close()


def _timestamp(offset_seconds: int = 0) -> str:
    return str(int((NOW + timedelta(seconds=offset_seconds)).timestamp()))


def _signed_headers(
    *,
    key: InternalServiceKey = ACTIVE_KEY,
    method: str = "POST",
    path: str = RUNS_PATH,
    raw_body: bytes = RAW_BODY,
    timestamp: str | None = None,
    nonce: str = "nonce-001",
) -> dict[str, str]:
    signed_timestamp = timestamp or _timestamp()
    return {
        "X-Internal-Key-Id": key.key_id,
        "X-Internal-Timestamp": signed_timestamp,
        "X-Internal-Nonce": nonce,
        "X-Internal-Signature": sign_internal_request(
            key.secret,
            method,
            path,
            signed_timestamp,
            nonce,
            raw_body,
        ),
    }


def _authenticate(
    session,
    registry,
    headers: dict[str, str],
    *,
    method: str = "POST",
    path: str = RUNS_PATH,
    raw_body: bytes = RAW_BODY,
    required_scope: str = "ru_probe:ingest",
    required_origin: str = "ru",
    now: datetime = NOW,
) -> AuthenticatedInternalRequest:
    return authenticate_internal_request(
        session,
        registry,
        method=method,
        path=path,
        raw_body=raw_body,
        headers=headers,
        required_scope=required_scope,
        required_origin=required_origin,
        now=now,
    )


def _nonce_count(session) -> int:
    return int(
        session.scalar(select(func.count()).select_from(models.InternalIngestNonce))
        or 0
    )


def test_security_dataclasses_are_frozen_and_keep_the_exact_contract() -> None:
    assert [field.name for field in fields(InternalServiceKey)] == [
        "key_id",
        "secret",
        "subject",
        "scopes",
        "origins",
        "enabled",
    ]
    assert [field.name for field in fields(AuthenticatedInternalRequest)] == [
        "key_id",
        "subject",
        "nonce",
        "request_timestamp",
        "body_sha256",
    ]
    with pytest.raises(FrozenInstanceError):
        ACTIVE_KEY.subject = "changed"  # type: ignore[misc]


def test_public_function_signatures_match_the_approved_contract() -> None:
    assert str(inspect.signature(normalize_signed_path)) == "(path: 'str') -> 'str'"
    assert str(inspect.signature(signature_preimage)) == (
        "(method: 'str', path: 'str', timestamp: 'str', nonce: 'str', "
        "raw_body: 'bytes') -> 'bytes'"
    )
    assert str(inspect.signature(sign_internal_request)) == (
        "(secret: 'bytes', method: 'str', path: 'str', timestamp: 'str', "
        "nonce: 'str', raw_body: 'bytes') -> 'str'"
    )
    assert str(inspect.signature(authenticate_internal_request)) == (
        "(session, registry, *, method, path, raw_body, headers, required_scope, "
        "required_origin, now) -> 'AuthenticatedInternalRequest'"
    )


def test_signature_binds_exact_bytes_method_path_timestamp_and_nonce() -> None:
    secret = b"test-secret-not-for-production"
    body = b'{"label":"\xd0\xbc\xd0\xb8\xd0\xbd\xd0\xb8"}'

    signature = sign_internal_request(
        secret,
        "POST",
        RUNS_PATH,
        "1784102400",
        "nonce-001",
        body,
    )

    assert signature == hmac.new(
        secret,
        b"POST\n/api/internal/probes/ru-origin/runs\n1784102400\nnonce-001\n" + body,
        hashlib.sha256,
    ).hexdigest()
    assert signature == signature.lower()


def test_signature_preimage_normalizes_path_but_keeps_exact_uppercase_method() -> None:
    assert signature_preimage(
        "POST",
        "//api//internal/probes/ru-origin/runs/",
        "1784102400",
        "nonce-001",
        b"{ }\n",
    ) == b"POST\n/api/internal/probes/ru-origin/runs\n1784102400\nnonce-001\n{ }\n"


@pytest.mark.parametrize("method", ["post", "Post", "pOST"])
def test_signature_preimage_rejects_non_uppercase_method(method: str) -> None:
    with pytest.raises(ValueError):
        signature_preimage(
            method,
            RUNS_PATH,
            "1784102400",
            "nonce-001",
            RAW_BODY,
        )


def test_authentication_rejects_lowercase_method_before_hmac(session, registry) -> None:
    with pytest.raises(InternalAuthError) as caught:
        _authenticate(
            session,
            registry,
            _signed_headers(method="POST"),
            method="post",
        )

    assert (caught.value.status_code, caught.value.code) == (
        400,
        "invalid_method",
    )
    assert _nonce_count(session) == 0


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/", "/"),
        ("////", "/"),
        (RUNS_PATH, RUNS_PATH),
        ("//api///internal/probes/ru-origin/runs/", RUNS_PATH),
    ],
)
def test_normalize_signed_path_accepts_only_canonicalizable_absolute_paths(
    path: str, expected: str
) -> None:
    assert normalize_signed_path(path) == expected


@pytest.mark.parametrize(
    "path",
    [
        "",
        "relative/path",
        "/path?query=1",
        "/path#fragment",
        "/path\\child",
        "/./path",
        "/path/../child",
        "/%2e%2e/child",
        "/path%2fchild",
        "/path\nchild",
        "/path\x00child",
        "/path child",
    ],
)
def test_normalize_signed_path_rejects_ambiguous_paths(path: str) -> None:
    with pytest.raises(ValueError):
        normalize_signed_path(path)


@pytest.mark.parametrize(
    ("method", "timestamp", "nonce"),
    [
        ("POST\nGET", "1784102400", "nonce-001"),
        ("POST", "1784102400\n0", "nonce-001"),
        ("POST", "1784102400", "nonce\n001"),
        ("POST", "+1784102400", "nonce-001"),
        ("POST", "01784102400", "nonce-001"),
        ("POST", "1784102400", ""),
    ],
)
def test_signature_preimage_rejects_delimiter_ambiguity(
    method: str, timestamp: str, nonce: str
) -> None:
    with pytest.raises((TypeError, ValueError)):
        signature_preimage(method, RUNS_PATH, timestamp, nonce, RAW_BODY)


def test_pure_helpers_have_no_module_level_orm_imports() -> None:
    source = Path(auth_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    top_level_modules: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            top_level_modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            top_level_modules.add(node.module.split(".")[0])

    assert "sqlalchemy" not in top_level_modules
    assert "models" not in top_level_modules


def test_load_registry_reads_dummy_keys_only_from_the_configured_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    key_file = tmp_path / "internal-hmac-keys.json"
    key_file.write_text(
        json.dumps(
            {
                "keys": [
                    {
                        "key_id": ACTIVE_KEY.key_id,
                        "secret": ACTIVE_KEY.secret.decode("ascii"),
                        "subject": ACTIVE_KEY.subject,
                        "scopes": sorted(ACTIVE_KEY.scopes),
                        "origins": sorted(ACTIVE_KEY.origins),
                        "enabled": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("INTERNAL_HMAC_KEYS_FILE", str(key_file))
    monkeypatch.setenv("INTERNAL_HMAC_SECRET", "must-not-be-read")

    loaded = load_internal_service_key_registry()

    assert loaded == {ACTIVE_KEY.key_id: ACTIVE_KEY}


def test_load_registry_fails_closed_without_the_file_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("INTERNAL_HMAC_KEYS_FILE", raising=False)
    monkeypatch.setenv("INTERNAL_HMAC_SECRET", ACTIVE_KEY.secret.decode("ascii"))

    with pytest.raises(InternalAuthError) as caught:
        load_internal_service_key_registry()

    assert (caught.value.status_code, caught.value.code) == (
        500,
        "key_registry_unavailable",
    )
    assert ACTIVE_KEY.secret.decode("ascii") not in str(caught.value)


@pytest.mark.parametrize(
    "payload",
    [
        "not-json",
        json.dumps({}),
        json.dumps({"keys": []}),
        json.dumps(
            {
                "keys": [
                    {
                        "key_id": "bad\nkey",
                        "secret": "dummy-secret-with-enough-bytes",
                        "subject": "mini",
                        "scopes": ["ru_probe:ingest"],
                        "origins": ["ru"],
                        "enabled": True,
                    }
                ]
            }
        ),
        json.dumps(
            {
                "keys": [
                    {
                        "key_id": "duplicate",
                        "secret": "dummy-secret-with-enough-bytes",
                        "subject": "mini",
                        "scopes": ["ru_probe:ingest"],
                        "origins": ["ru"],
                        "enabled": True,
                    },
                    {
                        "key_id": "duplicate",
                        "secret": "another-dummy-secret-value",
                        "subject": "mini",
                        "scopes": ["ru_probe:ingest"],
                        "origins": ["ru"],
                        "enabled": True,
                    },
                ]
            }
        ),
    ],
)
def test_load_registry_rejects_malformed_content_without_leaking_it(
    payload: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    key_file = tmp_path / "invalid-keys.json"
    key_file.write_text(payload, encoding="utf-8")
    monkeypatch.setenv("INTERNAL_HMAC_KEYS_FILE", str(key_file))

    with pytest.raises(InternalAuthError) as caught:
        load_internal_service_key_registry()

    assert (caught.value.status_code, caught.value.code) == (
        500,
        "invalid_key_registry",
    )
    assert "dummy-secret" not in str(caught.value)
    assert payload not in repr(caught.value)


@pytest.mark.parametrize(
    "payload",
    [
        (
            '{"keys":[],"keys":[{'
            '"key_id":"ru-probe-mini-v1",'
            '"secret":"dummy-secret-with-enough-bytes",'
            '"subject":"mini",'
            '"scopes":["ru_probe:ingest"],'
            '"origins":["ru"],'
            '"enabled":true}]}'
        ),
        (
            '{"keys":[{'
            '"key_id":"ru-probe-mini-v1",'
            '"secret":"first-dummy-secret-value",'
            '"secret":"second-dummy-secret-value",'
            '"subject":"mini",'
            '"scopes":["ru_probe:ingest"],'
            '"origins":["ru"],'
            '"enabled":true}]}'
        ),
        (
            '{"keys":[{'
            '"key_id":"ru-probe-mini-v1",'
            '"secret":"dummy-secret-with-enough-bytes",'
            '"subject":"mini",'
            '"scopes":["ru_probe:ingest"],'
            '"origins":["ru"],'
            '"enabled":true,'
            '"enabled":false}]}'
        ),
    ],
    ids=["root-keys", "entry-secret", "entry-enabled"],
)
def test_load_registry_rejects_duplicate_json_members(
    payload: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    key_file = tmp_path / "duplicate-members.json"
    key_file.write_text(payload, encoding="utf-8")
    monkeypatch.setenv("INTERNAL_HMAC_KEYS_FILE", str(key_file))

    with pytest.raises(InternalAuthError) as caught:
        load_internal_service_key_registry()

    assert (caught.value.status_code, caught.value.code) == (
        500,
        "invalid_key_registry",
    )
    assert "dummy-secret" not in str(caught.value)
    assert payload not in repr(caught.value)


def test_registry_uses_one_handle_fstat_and_a_64_kib_plus_one_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    key_file = tmp_path / "single-handle-keys.json"
    key_file.write_text(
        json.dumps(
            {
                "keys": [
                    {
                        "key_id": ACTIVE_KEY.key_id,
                        "secret": ACTIVE_KEY.secret.decode("ascii"),
                        "subject": ACTIVE_KEY.subject,
                        "scopes": sorted(ACTIVE_KEY.scopes),
                        "origins": sorted(ACTIVE_KEY.origins),
                        "enabled": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("INTERNAL_HMAC_KEYS_FILE", str(key_file))
    original_open = Path.open
    read_sizes: list[int] = []
    fileno_calls: list[int] = []

    class RecordingHandle:
        def __init__(self, handle) -> None:
            self._handle = handle

        def __enter__(self):
            self._handle.__enter__()
            return self

        def __exit__(self, *args):
            return self._handle.__exit__(*args)

        def __getattr__(self, name):
            return getattr(self._handle, name)

        def read(self, size: int = -1):
            read_sizes.append(size)
            return self._handle.read(size)

        def fileno(self) -> int:
            file_descriptor = self._handle.fileno()
            fileno_calls.append(file_descriptor)
            return file_descriptor

    class RecordingPath:
        def stat(self):
            raise AssertionError("registry must fstat the opened handle")

        def open(self, *args, **kwargs):
            return RecordingHandle(original_open(key_file, *args, **kwargs))

    monkeypatch.setattr(auth_module, "Path", lambda _path: RecordingPath())

    assert load_internal_service_key_registry() == {ACTIVE_KEY.key_id: ACTIVE_KEY}
    assert read_sizes == [64 * 1024 + 1]
    assert len(fileno_calls) == 1


def test_registry_scope_length_matches_nonce_model_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert models.InternalIngestNonce.__table__.c.key_scope.type.length == 64

    def write_registry(scope: str) -> None:
        key_file.write_text(
            json.dumps(
                {
                    "keys": [
                        {
                            "key_id": ACTIVE_KEY.key_id,
                            "secret": ACTIVE_KEY.secret.decode("ascii"),
                            "subject": ACTIVE_KEY.subject,
                            "scopes": [scope],
                            "origins": ["ru"],
                            "enabled": True,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

    key_file = tmp_path / "scope-boundary-keys.json"
    monkeypatch.setenv("INTERNAL_HMAC_KEYS_FILE", str(key_file))
    maximum_scope = "s" * 64
    write_registry(maximum_scope)
    assert load_internal_service_key_registry()[ACTIVE_KEY.key_id].scopes == frozenset(
        {maximum_scope}
    )

    write_registry("s" * 65)
    with pytest.raises(InternalAuthError) as caught:
        load_internal_service_key_registry()
    assert (caught.value.status_code, caught.value.code) == (
        500,
        "invalid_key_registry",
    )


def test_authentication_is_case_insensitive_and_returns_service_identity(
    session, registry
) -> None:
    headers = {
        name.swapcase(): value for name, value in _signed_headers().items()
    }

    authenticated = _authenticate(session, registry, headers)

    assert authenticated == AuthenticatedInternalRequest(
        key_id=ACTIVE_KEY.key_id,
        subject="mini",
        nonce="nonce-001",
        request_timestamp=datetime.fromtimestamp(
            int(_timestamp()), tz=timezone.utc
        ),
        body_sha256=hashlib.sha256(RAW_BODY).hexdigest(),
    )
    row = session.scalar(select(models.InternalIngestNonce))
    assert row is not None
    assert row.key_scope == "ru_probe:ingest"
    assert row.key_id == ACTIVE_KEY.key_id
    assert row.nonce_hash == hashlib.sha256(b"nonce-001").hexdigest()
    assert row.request_path == RUNS_PATH
    assert row.body_sha256 == hashlib.sha256(RAW_BODY).hexdigest()
    assert not hasattr(row, "nonce")


def test_authentication_stores_the_normalized_path(session, registry) -> None:
    noncanonical_path = "//api//internal/probes/ru-origin/runs/"
    headers = _signed_headers(path=noncanonical_path)

    _authenticate(session, registry, headers, path=noncanonical_path)

    row = session.scalar(select(models.InternalIngestNonce))
    assert row is not None
    assert row.request_path == RUNS_PATH


def test_generic_verifier_does_not_parse_or_host_bind_the_payload(
    session, registry
) -> None:
    raw_body = b"not-json-and-no-host"
    headers = _signed_headers(raw_body=raw_body)

    authenticated = _authenticate(
        session, registry, headers, raw_body=raw_body
    )

    assert authenticated.subject == "mini"
    assert authenticated.body_sha256 == hashlib.sha256(raw_body).hexdigest()


@pytest.mark.parametrize(
    ("changed", "value"),
    [
        ("method", "PUT"),
        ("path", "/api/internal/probes/ru-origin/heartbeat"),
        ("raw_body", b'{ "schema_version":2,"probe_host":{"id":"mini"}}'),
    ],
)
def test_authentication_rejects_modified_exact_request_components(
    changed: str, value, session, registry
) -> None:
    kwargs = {
        "method": "POST",
        "path": RUNS_PATH,
        "raw_body": RAW_BODY,
    }
    kwargs[changed] = value

    with pytest.raises(InternalAuthError) as caught:
        _authenticate(session, registry, _signed_headers(), **kwargs)

    assert (caught.value.status_code, caught.value.code) == (
        401,
        "invalid_signature",
    )
    assert _nonce_count(session) == 0


def test_authentication_rejects_signature_bound_to_other_timestamp_or_nonce(
    session, registry
) -> None:
    headers = _signed_headers()
    headers["X-Internal-Timestamp"] = _timestamp(1)
    headers["X-Internal-Nonce"] = "nonce-002"

    with pytest.raises(InternalAuthError) as caught:
        _authenticate(session, registry, headers)

    assert caught.value.code == "invalid_signature"
    assert _nonce_count(session) == 0


@pytest.mark.parametrize(
    "missing_header",
    [
        "X-Internal-Key-Id",
        "X-Internal-Timestamp",
        "X-Internal-Nonce",
        "X-Internal-Signature",
    ],
)
def test_authentication_requires_every_header(
    missing_header: str, session, registry
) -> None:
    headers = _signed_headers()
    del headers[missing_header]

    with pytest.raises(InternalAuthError) as caught:
        _authenticate(session, registry, headers)

    assert (caught.value.status_code, caught.value.code) == (
        401,
        "missing_auth_header",
    )


def test_authentication_rejects_case_variant_duplicate_header(session, registry) -> None:
    headers = _signed_headers()
    headers["x-internal-nonce"] = headers["X-Internal-Nonce"]

    with pytest.raises(InternalAuthError) as caught:
        _authenticate(session, registry, headers)

    assert (caught.value.status_code, caught.value.code) == (
        401,
        "malformed_auth_header",
    )


@pytest.mark.parametrize(
    ("header_name", "bad_value"),
    [
        ("X-Internal-Key-Id", "bad\nkey"),
        ("X-Internal-Key-Id", "k" * 129),
        ("X-Internal-Timestamp", "1784102400.0"),
        ("X-Internal-Timestamp", "+1784102400"),
        ("X-Internal-Nonce", "bad\rnonce"),
        ("X-Internal-Nonce", "n" * 129),
        ("X-Internal-Signature", "A" * 64),
        ("X-Internal-Signature", "0" * 63),
        ("X-Internal-Signature", "g" * 64),
    ],
)
def test_authentication_rejects_malformed_header_values(
    header_name: str, bad_value: str, session, registry
) -> None:
    headers = _signed_headers()
    headers[header_name] = bad_value

    with pytest.raises(InternalAuthError) as caught:
        _authenticate(session, registry, headers)

    assert caught.value.status_code == 401
    assert caught.value.code == "malformed_auth_header"
    assert _nonce_count(session) == 0


@pytest.mark.parametrize("offset", [-300, 300])
def test_authentication_accepts_inclusive_timestamp_skew_boundary(
    offset: int, session, registry
) -> None:
    nonce = f"nonce-{offset:+d}"
    headers = _signed_headers(timestamp=_timestamp(offset), nonce=nonce)

    authenticated = _authenticate(session, registry, headers)

    assert authenticated.nonce == nonce


@pytest.mark.parametrize("offset", [-301, 301])
def test_authentication_rejects_timestamp_outside_skew_boundary(
    offset: int, session, registry
) -> None:
    headers = _signed_headers(timestamp=_timestamp(offset), nonce=f"nonce-{offset:+d}")

    with pytest.raises(InternalAuthError) as caught:
        _authenticate(session, registry, headers)

    assert (caught.value.status_code, caught.value.code) == (
        401,
        "stale_timestamp",
    )
    assert _nonce_count(session) == 0


def test_authentication_accepts_512_kib_and_rejects_one_more_byte(
    session, registry
) -> None:
    maximum = b"x" * (512 * 1024)
    _authenticate(
        session,
        registry,
        _signed_headers(raw_body=maximum, nonce="nonce-max"),
        raw_body=maximum,
    )
    too_large = maximum + b"x"

    with pytest.raises(InternalAuthError) as caught:
        _authenticate(
            session,
            registry,
            _signed_headers(raw_body=too_large, nonce="nonce-too-large"),
            raw_body=too_large,
        )

    assert (caught.value.status_code, caught.value.code) == (
        413,
        "body_too_large",
    )
    assert _nonce_count(session) == 1


def test_authentication_rejects_unknown_and_disabled_keys(session) -> None:
    unknown = InternalServiceKey(
        key_id="unknown-v1",
        secret=b"unknown-dummy-secret-value",
        subject="mini",
        scopes=frozenset({"ru_probe:ingest"}),
        origins=frozenset({"ru"}),
        enabled=True,
    )
    with pytest.raises(InternalAuthError) as unknown_error:
        _authenticate(session, {}, _signed_headers(key=unknown))
    assert (unknown_error.value.status_code, unknown_error.value.code) == (
        401,
        "unknown_key",
    )

    disabled = InternalServiceKey(
        key_id="disabled-v1",
        secret=b"disabled-dummy-secret-value",
        subject="mini",
        scopes=frozenset({"ru_probe:ingest"}),
        origins=frozenset({"ru"}),
        enabled=False,
    )
    with pytest.raises(InternalAuthError) as disabled_error:
        _authenticate(
            session,
            {disabled.key_id: disabled},
            _signed_headers(key=disabled),
        )
    assert (disabled_error.value.status_code, disabled_error.value.code) == (
        401,
        "disabled_key",
    )
    assert _nonce_count(session) == 0


def test_authentication_enforces_scope_and_origin_allowlists(session, registry) -> None:
    with pytest.raises(InternalAuthError) as scope_error:
        _authenticate(
            session,
            registry,
            _signed_headers(),
            required_scope="release:evidence",
        )
    assert (scope_error.value.status_code, scope_error.value.code) == (
        403,
        "forbidden_scope",
    )

    with pytest.raises(InternalAuthError) as origin_error:
        _authenticate(
            session,
            registry,
            _signed_headers(),
            required_origin="brain",
        )
    assert (origin_error.value.status_code, origin_error.value.code) == (
        403,
        "forbidden_origin",
    )
    assert _nonce_count(session) == 0


def test_verifier_accepts_scope_64_and_rejects_scope_65(session) -> None:
    maximum_scope = "s" * 64
    oversized_scope = "s" * 65
    key = InternalServiceKey(
        key_id=ACTIVE_KEY.key_id,
        secret=ACTIVE_KEY.secret,
        subject=ACTIVE_KEY.subject,
        scopes=frozenset({maximum_scope, oversized_scope}),
        origins=ACTIVE_KEY.origins,
        enabled=True,
    )
    registry = {key.key_id: key}

    _authenticate(
        session,
        registry,
        _signed_headers(key=key, nonce="nonce-scope-64"),
        required_scope=maximum_scope,
    )

    with pytest.raises(InternalAuthError) as caught:
        _authenticate(
            session,
            registry,
            _signed_headers(key=key, nonce="nonce-scope-65"),
            required_scope=oversized_scope,
        )
    assert (caught.value.status_code, caught.value.code) == (
        500,
        "invalid_auth_requirement",
    )
    assert _nonce_count(session) == 1


def test_auth_error_never_contains_secret_or_signature(session, registry) -> None:
    headers = _signed_headers()
    supplied_signature = "0" * 64
    headers["X-Internal-Signature"] = supplied_signature

    with pytest.raises(InternalAuthError) as caught:
        _authenticate(session, registry, headers)

    rendered = f"{caught.value!r} {caught.value}"
    assert caught.value.code == "invalid_signature"
    assert ACTIVE_KEY.secret.decode("ascii") not in rendered
    assert supplied_signature not in rendered


def test_authentication_honors_compare_digest_result(
    session, registry, monkeypatch: pytest.MonkeyPatch
) -> None:
    compared: list[tuple[str, str]] = []

    def rejecting_compare_digest(expected: str, supplied: str) -> bool:
        compared.append((expected, supplied))
        return False

    headers = _signed_headers(nonce="nonce-compare-digest")
    monkeypatch.setattr(auth_module.hmac, "compare_digest", rejecting_compare_digest)

    with pytest.raises(InternalAuthError) as caught:
        _authenticate(session, registry, headers)

    assert (caught.value.status_code, caught.value.code) == (
        401,
        "invalid_signature",
    )
    assert compared == [
        (headers["X-Internal-Signature"], headers["X-Internal-Signature"])
    ]
    assert _nonce_count(session) == 0


def test_authentication_rejects_naive_clock(session, registry) -> None:
    with pytest.raises(InternalAuthError) as caught:
        _authenticate(
            session,
            registry,
            _signed_headers(nonce="nonce-naive-clock"),
            now=NOW.replace(tzinfo=None),
        )

    assert (caught.value.status_code, caught.value.code) == (
        500,
        "invalid_auth_clock",
    )
    assert _nonce_count(session) == 0


def test_microseconds_are_not_truncated_at_timestamp_skew_boundary(
    session, registry
) -> None:
    outside_headers = _signed_headers(
        timestamp=_timestamp(-300),
        nonce="nonce-microsecond-outside",
    )
    with pytest.raises(InternalAuthError) as caught:
        _authenticate(
            session,
            registry,
            outside_headers,
            now=NOW + timedelta(microseconds=1),
        )
    assert (caught.value.status_code, caught.value.code) == (
        401,
        "stale_timestamp",
    )

    inside_headers = _signed_headers(
        timestamp=_timestamp(300),
        nonce="nonce-microsecond-inside",
    )
    authenticated = _authenticate(
        session,
        registry,
        inside_headers,
        now=NOW + timedelta(microseconds=999_999),
    )
    assert authenticated.nonce == "nonce-microsecond-inside"
    assert _nonce_count(session) == 1


@pytest.mark.parametrize(
    ("pending_value", "seed_value"),
    [(None, None), ("already-used", "already-used")],
    ids=["not-null", "unique"],
)
def test_nonce_insert_does_not_preflush_unrelated_pending_orm_failure(
    pending_value: str | None,
    seed_value: str | None,
    session_factory,
    registry,
) -> None:
    if seed_value is not None:
        seed_session = session_factory()
        try:
            seed_session.add(PendingUnrelatedRow(value=seed_value))
            seed_session.commit()
        finally:
            seed_session.close()

    caller = session_factory()
    pending = PendingUnrelatedRow(value=pending_value)
    caller.add(pending)
    try:
        authenticated = _authenticate(
            caller,
            registry,
            _signed_headers(nonce=f"nonce-pending-{pending_value}"),
        )

        assert authenticated.key_id == ACTIVE_KEY.key_id
        assert pending in caller.new
        caller.expunge(pending)
        assert caller.execute(text("SELECT 1")).scalar_one() == 1
        assert _nonce_count(caller) == 1
        caller.rollback()
    finally:
        caller.close()

    observer = session_factory()
    try:
        assert _nonce_count(observer) == 0
    finally:
        observer.close()


def test_non_replay_integrity_error_from_nonce_insert_is_not_masked(
    session, registry
) -> None:
    blocked_nonce = "nonce-blocked-by-trigger"
    blocked_hash = hashlib.sha256(blocked_nonce.encode("ascii")).hexdigest()
    session.execute(
        text(
            "CREATE TRIGGER reject_selected_nonce "
            "BEFORE INSERT ON internal_ingest_nonces "
            f"WHEN NEW.nonce_hash = '{blocked_hash}' "
            "BEGIN SELECT RAISE(ABORT, 'blocked nonce insert'); END"
        )
    )
    session.commit()

    with pytest.raises(IntegrityError, match="blocked nonce insert"):
        _authenticate(
            session,
            registry,
            _signed_headers(nonce=blocked_nonce),
        )

    assert session.execute(text("SELECT 1")).scalar_one() == 1
    _authenticate(
        session,
        registry,
        _signed_headers(nonce="nonce-after-trigger"),
    )
    assert _nonce_count(session) == 1
    session.rollback()


def test_postgres_replay_classification_requires_exact_constraint_name() -> None:
    class PgOriginalError(RuntimeError):
        def __init__(self, constraint_name: str) -> None:
            super().__init__("duplicate key")
            self.diag = SimpleNamespace(constraint_name=constraint_name)

    def pg_error(constraint_name: str) -> IntegrityError:
        return IntegrityError("INSERT", {}, PgOriginalError(constraint_name))

    assert auth_module._is_replayed_nonce_integrity_error(
        pg_error("uq_internal_ingest_nonce_scope_key_hash")
    )
    assert not auth_module._is_replayed_nonce_integrity_error(
        pg_error("uq_unrelated_constraint")
    )


def test_sqlite_replay_classification_requires_exact_unique_columns() -> None:
    prefix = "UNIQUE constraint failed: "
    exact_columns = (
        "internal_ingest_nonces.key_scope, "
        "internal_ingest_nonces.key_id, "
        "internal_ingest_nonces.nonce_hash"
    )

    def sqlite_error(detail: str) -> IntegrityError:
        return IntegrityError("INSERT", {}, sqlite3.IntegrityError(detail))

    assert auth_module._is_replayed_nonce_integrity_error(
        sqlite_error(prefix + exact_columns)
    )
    assert not auth_module._is_replayed_nonce_integrity_error(
        sqlite_error(
            prefix
            + "internal_ingest_nonces.key_id, "
            + "internal_ingest_nonces.key_scope, "
            + "internal_ingest_nonces.nonce_hash"
        )
    )
    assert not auth_module._is_replayed_nonce_integrity_error(
        sqlite_error(prefix + exact_columns + ", internal_ingest_nonces.id")
    )


def test_nonce_is_not_durable_until_caller_commit_and_rollback_removes_it(
    session_factory, registry
) -> None:
    writer = session_factory()
    try:
        _authenticate(writer, registry, _signed_headers())
        assert _nonce_count(writer) == 1

        observer = session_factory()
        try:
            assert _nonce_count(observer) == 0
        finally:
            observer.close()

        writer.rollback()
    finally:
        writer.close()

    observer = session_factory()
    try:
        assert _nonce_count(observer) == 0
    finally:
        observer.close()


def test_nonce_is_durable_after_caller_commit(session_factory, registry) -> None:
    writer = session_factory()
    try:
        _authenticate(writer, registry, _signed_headers())
        writer.commit()
    finally:
        writer.close()

    observer = session_factory()
    try:
        row = observer.scalar(select(models.InternalIngestNonce))
        assert row is not None
        assert row.nonce_hash == hashlib.sha256(b"nonce-001").hexdigest()
        assert row.expires_at.replace(tzinfo=timezone.utc) == NOW + timedelta(hours=24)
    finally:
        observer.close()


def test_nonce_replay_is_rejected_inside_the_same_caller_transaction(
    session, registry
) -> None:
    headers = _signed_headers()
    _authenticate(session, registry, headers)

    with pytest.raises(InternalAuthError) as caught:
        _authenticate(session, registry, headers)

    assert (caught.value.status_code, caught.value.code) == (
        409,
        "replayed_nonce",
    )
    assert session.execute(text("SELECT 1")).scalar_one() == 1
    assert _nonce_count(session) == 1


def test_concurrent_nonce_unique_race_returns_409_and_keeps_session_usable(
    session_factory, registry
) -> None:
    winner = session_factory()
    engine = session_factory.kw["bind"]
    loser_reached_insert = threading.Event()
    outcome: Queue[tuple[object, ...]] = Queue()
    main_thread_id = threading.get_ident()

    def observe_loser_insert(
        _connection, _cursor, statement, _parameters, _context, _executemany
    ) -> None:
        if (
            threading.get_ident() != main_thread_id
            and "INSERT INTO internal_ingest_nonces" in str(statement)
        ):
            loser_reached_insert.set()

    def run_loser() -> None:
        loser = session_factory()
        try:
            _authenticate(loser, registry, _signed_headers())
            outcome.put(("unexpected_success",))
        except InternalAuthError as caught:
            usable = loser.execute(text("SELECT 1")).scalar_one()
            _authenticate(
                loser,
                registry,
                _signed_headers(nonce="nonce-after-race"),
            )
            outcome.put(
                (
                    "auth_error",
                    caught.status_code,
                    caught.code,
                    usable,
                    _nonce_count(loser),
                )
            )
            loser.rollback()
        except BaseException as caught:  # pragma: no cover - assertion transport
            outcome.put(("unexpected_exception", type(caught).__name__))
        finally:
            loser.close()

    try:
        _authenticate(winner, registry, _signed_headers())
        event.listen(engine, "before_cursor_execute", observe_loser_insert)
        loser_thread = threading.Thread(target=run_loser, daemon=True)
        loser_thread.start()
        assert loser_reached_insert.wait(timeout=5)
        winner.commit()
        loser_thread.join(timeout=5)
        assert not loser_thread.is_alive()
    finally:
        event.remove(engine, "before_cursor_execute", observe_loser_insert)
        if winner.in_transaction():
            winner.rollback()
        winner.close()

    assert outcome.get_nowait() == (
        "auth_error",
        409,
        "replayed_nonce",
        1,
        2,
    )

    observer = session_factory()
    try:
        assert _nonce_count(observer) == 1
    finally:
        observer.close()
