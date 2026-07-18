from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ru_probe_uploader import (  # noqa: E402
    RUNS_PATH,
    SpoolError,
    build_heartbeat,
    calculate_backoff,
    recover_pending,
    scan_pending,
    send_heartbeat,
    upload_one,
    write_pending_artifact,
)


NOW = datetime(2026, 7, 16, 6, 30, tzinfo=timezone.utc)
RUN_ID = "00000000-0000-4000-8000-000000000001"
OTHER_RUN_ID = "00000000-0000-4000-8000-000000000002"


def _artifact(run_id: str = RUN_ID) -> bytes:
    return (
        b'{"schema_version":2,"run_id":"'
        + run_id.encode("ascii")
        + b'","origin":"ru"}'
    )


def _run_success_body(
    *,
    status: int,
    run_id: str = RUN_ID,
    **overrides: object,
) -> dict[str, object]:
    body: dict[str, object] = {
        "code": "created",
        "run_db_id": 17,
        "run_id": run_id,
        "created": status == 201,
        "current_eligible": True,
        "correlation_id": "corr-created",
    }
    body.update(overrides)
    return body


def _heartbeat_success_body() -> dict[str, object]:
    return {
        "code": "created",
        "correlation_id": "corr-heartbeat",
    }


class FakeTransport:
    def __init__(self) -> None:
        self.responses: list[object] = []
        self.calls: list[dict[str, object]] = []
        self._lock = threading.Lock()

    def respond(
        self,
        *,
        status: object,
        body: dict[str, object] | bytes | None = None,
    ) -> None:
        if body is None:
            raw = b"{}"
        elif isinstance(body, bytes):
            raw = body
        else:
            raw = json.dumps(body, separators=(",", ":")).encode("utf-8")
        self.responses.append(
            SimpleNamespace(status=status, body=raw, headers={})
        )

    def send(self, **kwargs):
        with self._lock:
            self.calls.append(dict(kwargs))
            if not self.responses:
                raise OSError("network unavailable")
            response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def _pending(tmp_path: Path, raw: bytes | None = None) -> Path:
    return write_pending_artifact(
        tmp_path,
        RUN_ID,
        _artifact() if raw is None else raw,
    )


def _reason(path: Path) -> dict[str, object]:
    return json.loads(
        path.with_name(f"{RUN_ID}.reason.json").read_text(encoding="utf-8")
    )


def _terminalize(
    tmp_path: Path,
    destination: str,
    *,
    raw: bytes | None = None,
) -> Path:
    artifact_raw = _artifact() if raw is None else raw
    pending = write_pending_artifact(tmp_path, RUN_ID, artifact_raw)
    transport = FakeTransport()
    if destination == "archive":
        transport.respond(status=201, body=_run_success_body(status=201))
    elif destination == "blocked":
        transport.respond(
            status=401,
            body={"code": "key_disabled", "correlation_id": "corr-terminal"},
        )
    elif destination == "quarantine":
        transport.respond(
            status=422,
            body={"code": "invalid_payload", "correlation_id": "corr-terminal"},
        )
    else:  # pragma: no cover - test helper contract
        raise AssertionError(destination)
    outcome = upload_one(pending, transport=transport, now=NOW)
    assert outcome.destination == destination
    assert outcome.path is not None
    return outcome.path


def _load_runner():
    module_path = SCRIPTS_DIR / "ru_probe_runner.py"
    spec = importlib.util.spec_from_file_location("ru_probe_runner_task8", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_write_artifact_is_atomic_and_hash_matches_exact_bytes(
    tmp_path: Path,
) -> None:
    artifact = _artifact()

    path = write_pending_artifact(tmp_path, RUN_ID, artifact)

    assert path.read_bytes() == artifact
    if os.name != "nt":
        assert path.stat().st_mode & 0o777 == 0o600
        assert path.parent.stat().st_mode & 0o777 == 0o700
    assert (
        path.with_suffix(".sha256").read_text(encoding="ascii").strip()
        == hashlib.sha256(artifact).hexdigest()
    )
    assert not list(tmp_path.rglob("*.tmp"))


def test_same_run_same_bytes_is_idempotent_and_different_bytes_fail_closed(
    tmp_path: Path,
) -> None:
    first = write_pending_artifact(tmp_path, RUN_ID, _artifact())
    second = write_pending_artifact(tmp_path, RUN_ID, _artifact())

    assert second == first
    with pytest.raises(SpoolError, match="run_id_conflict"):
        write_pending_artifact(tmp_path, RUN_ID, _artifact() + b"\n")
    assert first.read_bytes() == _artifact()


@pytest.mark.parametrize(
    "run_id",
    [
        "../escape",
        "00000000-0000-4000-8000-000000000001.json",
        "00000000-0000-4000-8000-00000000000Z",
    ],
)
def test_write_rejects_noncanonical_or_traversal_run_id(
    tmp_path: Path,
    run_id: str,
) -> None:
    with pytest.raises(SpoolError, match="invalid_run_id"):
        write_pending_artifact(tmp_path, run_id, _artifact())


def test_recovery_repairs_artifact_only_and_ignores_partial_temp(
    tmp_path: Path,
) -> None:
    pending = tmp_path / "pending"
    pending.mkdir(mode=0o700)
    artifact = pending / f"{RUN_ID}.json"
    artifact.write_bytes(_artifact())
    artifact.chmod(0o600)
    partial = pending / f".{OTHER_RUN_ID}.json.crash.tmp"
    partial.write_bytes(b'{"partial":')

    issues = recover_pending(tmp_path)

    assert artifact.with_suffix(".sha256").read_text(encoding="ascii").strip() == (
        hashlib.sha256(_artifact()).hexdigest()
    )
    assert scan_pending(tmp_path) == [artifact]
    assert all(issue.code != "artifact_without_sidecar" for issue in issues)
    assert partial.exists()


def test_recovery_does_not_upload_or_delete_sidecar_without_artifact(
    tmp_path: Path,
) -> None:
    pending = tmp_path / "pending"
    pending.mkdir(mode=0o700)
    orphan = pending / f"{RUN_ID}.sha256"
    orphan.write_text("a" * 64 + "\n", encoding="ascii")
    orphan.chmod(0o600)

    issues = recover_pending(tmp_path)

    assert orphan.exists()
    assert scan_pending(tmp_path) == []
    assert [issue.code for issue in issues] == ["sidecar_without_artifact"]


def test_conflicting_orphan_sidecar_cannot_create_partial_artifact(
    tmp_path: Path,
) -> None:
    pending = tmp_path / "pending"
    pending.mkdir(mode=0o700)
    sidecar = pending / f"{RUN_ID}.sha256"
    sidecar.write_bytes(b"0" * 64 + b"\n")

    with pytest.raises(SpoolError, match="run_id_conflict"):
        write_pending_artifact(tmp_path, RUN_ID, _artifact())

    assert sidecar.exists()
    assert not sidecar.with_suffix(".json").exists()


def test_concurrent_writers_never_mix_artifact_and_sidecar(
    tmp_path: Path,
) -> None:
    first_raw = _artifact()
    second_raw = _artifact() + b" "
    barrier = threading.Barrier(2)

    def writer(raw: bytes) -> str:
        barrier.wait()
        try:
            write_pending_artifact(tmp_path, RUN_ID, raw)
            return "written"
        except SpoolError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(writer, (first_raw, second_raw)))

    assert sorted(results) == ["run_id_conflict", "written"]
    artifact = tmp_path / "pending" / f"{RUN_ID}.json"
    raw = artifact.read_bytes()
    assert raw in {first_raw, second_raw}
    assert artifact.with_suffix(".sha256").read_text(encoding="ascii").strip() == (
        hashlib.sha256(raw).hexdigest()
    )


@pytest.mark.parametrize("destination", ["archive", "blocked", "quarantine"])
def test_same_terminal_artifact_is_idempotent_without_pending_requeue(
    tmp_path: Path,
    destination: str,
) -> None:
    terminal_path = _terminalize(tmp_path, destination)

    returned = write_pending_artifact(tmp_path, RUN_ID, _artifact())

    assert returned == terminal_path
    assert returned.exists()
    assert not (tmp_path / "pending" / f"{RUN_ID}.json").exists()
    assert not (tmp_path / "pending" / f"{RUN_ID}.sha256").exists()


@pytest.mark.parametrize("destination", ["archive", "blocked", "quarantine"])
def test_different_terminal_artifact_rejects_run_id_reuse(
    tmp_path: Path,
    destination: str,
) -> None:
    terminal_path = _terminalize(tmp_path, destination)

    with pytest.raises(SpoolError, match="run_id_conflict"):
        write_pending_artifact(tmp_path, RUN_ID, _artifact() + b" ")

    assert terminal_path.read_bytes() == _artifact()
    assert not (tmp_path / "pending" / f"{RUN_ID}.json").exists()


@pytest.mark.parametrize(
    ("member", "error_code"),
    [
        ("artifact_only", "terminal_pair_incomplete"),
        ("sidecar_only", "terminal_pair_incomplete"),
        ("artifact_only_different", "run_id_conflict"),
        ("sidecar_only_different", "run_id_conflict"),
        ("bad_hash", "artifact_hash_mismatch"),
    ],
)
def test_partial_or_tampered_terminal_pair_blocks_pending_creation(
    tmp_path: Path,
    member: str,
    error_code: str,
) -> None:
    for state in ("pending", "blocked", "quarantine", "archive"):
        (tmp_path / state).mkdir(parents=True, exist_ok=True)
    artifact_path = tmp_path / "archive" / f"{RUN_ID}.json"
    sidecar_path = artifact_path.with_suffix(".sha256")
    if member in {"artifact_only", "artifact_only_different", "bad_hash"}:
        artifact_path.write_bytes(
            _artifact() + b" "
            if member == "artifact_only_different"
            else _artifact()
        )
    if member in {"sidecar_only", "sidecar_only_different", "bad_hash"}:
        sidecar_path.write_bytes(
            (b"0" * 64 + b"\n")
            if member == "bad_hash"
            else hashlib.sha256(
                _artifact() + b" "
                if member == "sidecar_only_different"
                else _artifact()
            ).hexdigest().encode("ascii")
            + b"\n"
        )

    with pytest.raises(SpoolError, match=error_code):
        write_pending_artifact(tmp_path, RUN_ID, _artifact())

    assert not (tmp_path / "pending" / f"{RUN_ID}.json").exists()


def test_terminal_symlink_blocks_pending_creation_without_touching_target(
    tmp_path: Path,
) -> None:
    for state in ("pending", "blocked", "quarantine", "archive"):
        (tmp_path / state).mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside.json"
    outside.write_bytes(_artifact())
    terminal = tmp_path / "archive" / f"{RUN_ID}.json"
    try:
        terminal.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks unavailable")
    terminal.with_suffix(".sha256").write_bytes(
        hashlib.sha256(_artifact()).hexdigest().encode("ascii") + b"\n"
    )

    with pytest.raises(SpoolError, match="destination_symlink"):
        write_pending_artifact(tmp_path, RUN_ID, _artifact())

    assert outside.read_bytes() == _artifact()
    assert terminal.is_symlink()
    assert not (tmp_path / "pending" / f"{RUN_ID}.json").exists()


def test_multiple_terminal_states_fail_closed_without_pending_creation(
    tmp_path: Path,
) -> None:
    archive = _terminalize(tmp_path, "archive")
    quarantine = tmp_path / "quarantine" / archive.name
    quarantine.write_bytes(archive.read_bytes())
    quarantine.with_suffix(".sha256").write_bytes(
        archive.with_suffix(".sha256").read_bytes()
    )
    (tmp_path / "quarantine" / f"{RUN_ID}.reason.json").write_text(
        '{"status":422,"code":"invalid_payload",'
        '"correlation_id":"corr-old",'
        '"observed_at":"2026-07-16T06:00:00Z"}',
        encoding="utf-8",
    )

    with pytest.raises(SpoolError, match="multiple_terminal_states"):
        write_pending_artifact(tmp_path, RUN_ID, _artifact())

    assert not (tmp_path / "pending" / f"{RUN_ID}.json").exists()


def test_two_writers_after_archive_keep_single_immutable_run_identity(
    tmp_path: Path,
) -> None:
    archive = _terminalize(tmp_path, "archive")
    barrier = threading.Barrier(2)

    def writer(raw: bytes) -> str:
        barrier.wait()
        try:
            path = write_pending_artifact(tmp_path, RUN_ID, raw)
            return path.parent.name
        except SpoolError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(writer, (_artifact(), _artifact() + b" ")))

    assert sorted(results) == ["archive", "run_id_conflict"]
    assert archive.read_bytes() == _artifact()
    assert not (tmp_path / "pending" / f"{RUN_ID}.json").exists()


@pytest.mark.parametrize(
    ("status", "code", "destination"),
    [
        (201, "created", "archive"),
        (200, "created", "archive"),
        (503, "temporary", "pending"),
        (401, "key_disabled", "blocked"),
        (401, "key_scope_forbidden", "blocked"),
        (403, "key_disabled", "blocked"),
        (403, "key_scope_forbidden", "blocked"),
        (400, "invalid_request", "quarantine"),
        (413, "request_too_large", "quarantine"),
        (422, "invalid_payload", "quarantine"),
        (422, "unsupported_schema", "quarantine"),
        (409, "payload_conflict", "quarantine"),
    ],
)
def test_upload_transition_matrix(
    tmp_path: Path,
    status: int,
    code: str,
    destination: str,
) -> None:
    pending = _pending(tmp_path)
    transport = FakeTransport()
    response_body = (
        _run_success_body(status=status)
        if status in {200, 201}
        else {"code": code, "correlation_id": "corr-1"}
    )
    transport.respond(
        status=status,
        body=response_body,
    )

    outcome = upload_one(
        pending,
        transport=transport,
        now=NOW,
        jitter=lambda _upper: 0,
    )

    assert outcome.destination == destination
    assert outcome.code == code
    if destination != "pending":
        assert (tmp_path / destination / pending.name).exists()
    assert pending.exists() is (destination == "pending")
    if destination in {"blocked", "quarantine"}:
        assert _reason(tmp_path / destination / pending.name) == {
            "status": status,
            "code": code,
            "correlation_id": "corr-1",
            "observed_at": "2026-07-16T06:30:00Z",
        }
    elif destination == "archive":
        assert not (
            tmp_path / destination / f"{RUN_ID}.reason.json"
        ).exists()


@pytest.mark.parametrize(
    ("status", "body"),
    [
        (200, b"<html>proxy login</html>"),
        (201, {"code": "invalid_payload"}),
        (
            201,
            b'{"code":"created","run_db_id":17,"run_id":"'
            + RUN_ID.encode("ascii")
            + b'","created":true,"current_eligible":true,'
            + b'"correlation_id":"corr","code":"created"}',
        ),
        (
            201,
            {
                **_run_success_body(status=201),
                "unexpected": "field",
            },
        ),
        (
            201,
            _run_success_body(status=201, run_id=OTHER_RUN_ID),
        ),
        (
            201,
            _run_success_body(status=201, run_db_id=0),
        ),
        (
            201,
            _run_success_body(status=201, run_db_id=True),
        ),
        (
            201,
            _run_success_body(status=201, run_db_id=2**63),
        ),
        (
            201,
            _run_success_body(status=201, created=False),
        ),
        (
            200,
            _run_success_body(status=200, created=True),
        ),
        (
            201,
            _run_success_body(status=201, current_eligible=1),
        ),
        (
            201,
            _run_success_body(status=201, correlation_id="bad correlation"),
        ),
        (
            201,
            b"{" + b'"padding":"' + b"x" * (64 * 1024) + b'"}',
        ),
    ],
    ids=[
        "html",
        "wrong-code",
        "duplicate-code",
        "additional-field",
        "wrong-run-id",
        "zero-db-id",
        "bool-db-id",
        "oversized-db-id",
        "201-created-false",
        "200-created-true",
        "non-bool-eligibility",
        "unsafe-correlation",
        "oversized",
    ],
)
def test_success_response_must_be_strict_and_bound_to_pending_run(
    tmp_path: Path,
    status: int,
    body: dict[str, object] | bytes,
) -> None:
    pending = _pending(tmp_path)
    transport = FakeTransport()
    transport.respond(status=status, body=body)

    outcome = upload_one(
        pending,
        transport=transport,
        now=NOW,
        jitter=lambda _upper: 0,
    )

    assert outcome.destination == "pending"
    assert outcome.code == "invalid_success_response"
    assert pending.exists()
    assert not (tmp_path / "archive" / pending.name).exists()


@pytest.mark.parametrize("status", [200, 201])
def test_valid_success_response_archives_only_consistent_run_dto(
    tmp_path: Path,
    status: int,
) -> None:
    pending = _pending(tmp_path)
    transport = FakeTransport()
    transport.respond(
        status=status,
        body=_run_success_body(status=status),
    )

    outcome = upload_one(pending, transport=transport, now=NOW)

    assert outcome.destination == "archive"
    assert outcome.code == "created"


@pytest.mark.parametrize(
    ("status", "body"),
    [
        (202, _run_success_body(status=202)),
        (204, b""),
        (206, _run_success_body(status=206)),
        (301, b""),
        (302, b"<html>moved</html>"),
        (307, b""),
        (308, b""),
        (404, {"code": "invalid_request", "correlation_id": "corr-404"}),
        (405, {"code": "invalid_request", "correlation_id": "corr-405"}),
        (418, {"code": "invalid_request", "correlation_id": "corr-418"}),
        (0, b""),
        (99, b""),
        (600, b""),
        (999, b""),
        (True, b""),
        ("201", _run_success_body(status=201)),
        (None, b""),
    ],
    ids=[
        "202",
        "204",
        "206",
        "301",
        "302",
        "307",
        "308",
        "404",
        "405",
        "418",
        "zero",
        "below-http",
        "above-http",
        "large-odd",
        "bool",
        "string-201",
        "none",
    ],
)
def test_unsupported_http_status_keeps_pending_with_durable_retry(
    tmp_path: Path,
    status: object,
    body: dict[str, object] | bytes,
) -> None:
    pending = _pending(tmp_path)
    transport = FakeTransport()
    transport.respond(status=status, body=body)

    outcome = upload_one(
        pending,
        transport=transport,
        now=NOW,
        jitter=lambda _upper: 0,
    )

    assert outcome.destination == "pending"
    assert outcome.code == "unexpected_response"
    assert outcome.retry_after_seconds == 60
    assert pending.exists()
    assert not any(
        (tmp_path / state / pending.name).exists()
        for state in ("archive", "blocked", "quarantine")
    )
    retry = json.loads(
        pending.with_suffix(".retry.json").read_text(encoding="utf-8")
    )
    assert retry["attempt"] == 1
    assert retry["next_attempt_at"] == "2026-07-16T06:31:00Z"
    assert retry["last_code"] == "unexpected_response"
    assert retry["last_http_status"] == (
        status
        if isinstance(status, int)
        and not isinstance(status, bool)
        and 100 <= status <= 599
        else None
    )


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (400, "key_disabled"),
        (401, "invalid_payload"),
        (403, "payload_conflict"),
        (409, "invalid_payload"),
        (413, "invalid_payload"),
        (422, "key_disabled"),
        (503, "payload_conflict"),
    ],
)
def test_status_code_contradiction_is_retryable_not_terminal(
    tmp_path: Path,
    status: int,
    code: str,
) -> None:
    pending = _pending(tmp_path)
    transport = FakeTransport()
    transport.respond(
        status=status,
        body={"code": code, "correlation_id": "corr-contradiction"},
    )

    outcome = upload_one(
        pending,
        transport=transport,
        now=NOW,
        jitter=lambda _upper: 0,
    )

    assert outcome.destination == "pending"
    assert outcome.code == "unexpected_response"
    assert pending.exists()


@pytest.mark.parametrize(
    ("status", "body"),
    [
        (204, b""),
        (302, b"<html>moved</html>"),
        (404, {"code": "invalid_request", "correlation_id": "corr-route"}),
        (0, b""),
    ],
    ids=["204", "302", "404", "zero"],
)
def test_unexpected_status_retry_attempt_advances_across_invocations(
    tmp_path: Path,
    status: object,
    body: dict[str, object] | bytes,
) -> None:
    pending = _pending(tmp_path)
    first_transport = FakeTransport()
    first_transport.respond(
        status=status,
        body=body,
    )

    first = upload_one(
        pending,
        transport=first_transport,
        now=NOW,
        jitter=lambda _upper: 0,
    )

    assert first.retry_after_seconds == 60
    second_transport = FakeTransport()
    second_transport.respond(
        status=status,
        body=body,
    )
    second = upload_one(
        pending,
        transport=second_transport,
        now=NOW.replace(minute=31, second=1),
        jitter=lambda _upper: 0,
    )

    assert second.destination == "pending"
    assert second.code == "unexpected_response"
    assert second.retry_after_seconds == 120
    retry = json.loads(
        pending.with_suffix(".retry.json").read_text(encoding="utf-8")
    )
    assert retry["attempt"] == 2
    assert retry["next_attempt_at"] == "2026-07-16T06:33:01Z"
    assert retry["last_http_status"] == (
        status
        if isinstance(status, int)
        and not isinstance(status, bool)
        and 100 <= status <= 599
        else None
    )


def test_shared_client_oversized_response_is_retryable_not_blocked(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    import ru_probe_uploader

    class OversizedTransport:
        def send(self, **_kwargs):
            raise ru_probe_uploader.internal_hmac_client.InternalHmacClientError(
                "response_too_large"
            )

    outcome = upload_one(
        pending,
        transport=OversizedTransport(),
        now=NOW,
        jitter=lambda _upper: 0,
    )

    assert outcome.destination == "pending"
    assert outcome.code == "response_too_large"
    assert not (tmp_path / "blocked" / pending.name).exists()


@pytest.mark.parametrize("status", [408, 425, 429, 500, 502, 599])
def test_retryable_status_keeps_pending_and_returns_exponential_delay(
    tmp_path: Path,
    status: int,
) -> None:
    pending = _pending(tmp_path)
    transport = FakeTransport()
    transport.respond(status=status, body={"code": "temporary"})

    outcome = upload_one(
        pending,
        transport=transport,
        now=NOW,
        attempt=3,
        jitter=lambda upper: upper,
    )

    assert outcome.destination == "pending"
    assert outcome.retry_after_seconds == 480 + 30
    assert pending.exists()


def test_network_failure_keeps_pending_without_response_leak(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    transport = FakeTransport()
    transport.responses.append(OSError("https://token:secret@example.test"))

    outcome = upload_one(
        pending,
        transport=transport,
        now=NOW,
        jitter=lambda _upper: 0,
    )

    assert outcome.destination == "pending"
    assert outcome.code == "network_error"
    assert "secret" not in repr(outcome)
    assert pending.exists()


def test_replayed_nonce_resigns_once_with_exact_same_artifact_bytes(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    transport = FakeTransport()
    transport.respond(
        status=409,
        body={"code": "replayed_nonce", "correlation_id": "corr-1"},
    )
    transport.respond(
        status=201,
        body=_run_success_body(
            status=201,
            correlation_id="corr-2",
        ),
    )

    outcome = upload_one(pending, transport=transport, now=NOW)

    assert outcome.destination == "archive"
    assert outcome.attempts == 2
    assert [call["raw_body"] for call in transport.calls] == [
        _artifact(),
        _artifact(),
    ]
    assert all(call["path"] == RUNS_PATH for call in transport.calls)


def test_replayed_nonce_twice_is_quarantined(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    transport = FakeTransport()
    for correlation_id in ("corr-1", "corr-2"):
        transport.respond(
            status=409,
            body={
                "code": "replayed_nonce",
                "correlation_id": correlation_id,
            },
        )

    outcome = upload_one(pending, transport=transport, now=NOW)

    assert outcome.destination == "quarantine"
    assert outcome.attempts == 2
    assert _reason(tmp_path / "quarantine" / pending.name) == {
        "status": 409,
        "code": "replayed_nonce",
        "correlation_id": "corr-2",
        "observed_at": "2026-07-16T06:30:00Z",
    }


def test_duplicate_error_members_cannot_trigger_nonce_replay(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    transport = FakeTransport()
    transport.respond(
        status=409,
        body=(
            b'{"code":"replayed_nonce",'
            b'"code":"payload_conflict",'
            b'"correlation_id":"corr-unsafe"}'
        ),
    )

    outcome = upload_one(pending, transport=transport, now=NOW)

    assert outcome.destination == "pending"
    assert outcome.code == "unexpected_response"
    assert outcome.attempts == 1
    assert len(transport.calls) == 1
    retry_raw = pending.with_suffix(".retry.json").read_text(
        encoding="utf-8"
    )
    assert "corr-unsafe" not in retry_raw
    assert json.loads(retry_raw)["last_code"] == "unexpected_response"


def test_oversized_error_body_is_unexpected_and_never_persists_body(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    transport = FakeTransport()
    transport.respond(
        status=503,
        body=b"x" * (64 * 1024 + 1),
    )

    outcome = upload_one(
        pending,
        transport=transport,
        now=NOW,
        jitter=lambda _upper: 0,
    )

    assert outcome.destination == "pending"
    assert outcome.code == "unexpected_response"
    retry_raw = pending.with_suffix(".retry.json").read_text(
        encoding="utf-8"
    )
    assert "x" * 100 not in retry_raw
    assert json.loads(retry_raw)["last_code"] == "unexpected_response"


def test_replayed_nonce_rechecks_sidecar_before_second_send(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)

    class TamperingTransport(FakeTransport):
        def send(self, **kwargs):
            response = super().send(**kwargs)
            pending.with_suffix(".sha256").write_bytes(b"0" * 64 + b"\n")
            return response

    transport = TamperingTransport()
    transport.respond(status=409, body={"code": "replayed_nonce"})
    transport.respond(status=201, body=_run_success_body(status=201))

    outcome = upload_one(pending, transport=transport, now=NOW)

    assert outcome.destination == "quarantine"
    assert outcome.code == "artifact_hash_mismatch"
    assert len(transport.calls) == 1


def test_sidecar_is_verified_before_send_and_mismatch_is_quarantined(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    pending.with_suffix(".sha256").write_text("0" * 64 + "\n", encoding="ascii")
    transport = FakeTransport()
    transport.respond(status=201, body=_run_success_body(status=201))

    outcome = upload_one(pending, transport=transport, now=NOW)

    assert outcome.destination == "quarantine"
    assert outcome.code == "artifact_hash_mismatch"
    assert transport.calls == []
    assert (tmp_path / "quarantine" / pending.name).read_bytes() == _artifact()


def test_reason_sidecar_is_allowlisted_and_does_not_copy_response_payload(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    transport = FakeTransport()
    transport.respond(
        status=422,
        body={
            "code": "invalid_payload",
            "correlation_id": "corr-safe",
        },
    )

    upload_one(pending, transport=transport, now=NOW)

    reason_path = tmp_path / "quarantine" / f"{RUN_ID}.reason.json"
    raw = reason_path.read_text(encoding="utf-8")
    assert set(json.loads(raw)) == {
        "status",
        "code",
        "correlation_id",
        "observed_at",
    }
    assert "secret-token" not in raw
    assert "signature" not in raw
    assert json.loads(raw)["correlation_id"] == "corr-safe"
    if os.name != "nt":
        assert reason_path.stat().st_mode & 0o777 == 0o600


def test_error_response_with_extra_fields_stays_pending_without_payload_leak(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    transport = FakeTransport()
    transport.respond(
        status=422,
        body={
            "code": "invalid_payload",
            "correlation_id": "corr-safe",
            "detail": "secret-token-provider-payload",
            "signature": "must-not-copy",
        },
    )

    outcome = upload_one(
        pending,
        transport=transport,
        now=NOW,
        jitter=lambda _upper: 0,
    )

    assert outcome.destination == "pending"
    assert outcome.code == "unexpected_response"
    retry_raw = pending.with_suffix(".retry.json").read_text(
        encoding="utf-8"
    )
    assert "secret-token" not in retry_raw
    assert "signature" not in retry_raw
    assert "corr-safe" not in retry_raw
    assert not (tmp_path / "quarantine" / pending.name).exists()


def test_complete_quarantine_triplet_resumes_without_network(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    quarantine = tmp_path / "quarantine"
    destination = quarantine / pending.name
    destination.write_bytes(_artifact())
    destination.with_suffix(".sha256").write_bytes(
        pending.with_suffix(".sha256").read_bytes()
    )
    reason_path = quarantine / f"{RUN_ID}.reason.json"
    reason_raw = json.dumps(
        {
            "status": 422,
            "code": "invalid_payload",
            "correlation_id": "corr-old",
            "observed_at": "2026-07-16T06:00:00Z",
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    reason_path.write_bytes(reason_raw)
    retry_path = pending.with_suffix(".retry.json")
    retry_path.write_text(
        '{"attempt":1,"next_attempt_at":"2026-07-16T06:31:00Z",'
        '"last_http_status":201,"last_code":"invalid_success_response"}',
        encoding="utf-8",
    )
    transport = FakeTransport()
    transport.respond(
        status=422,
        body={"code": "invalid_payload", "correlation_id": "corr-new"},
    )

    outcome = upload_one(pending, transport=transport, now=NOW)

    assert outcome.destination == "quarantine"
    assert outcome.code == "invalid_payload"
    assert transport.calls == []
    assert destination.read_bytes() == _artifact()
    assert reason_path.read_bytes() == reason_raw
    assert not pending.exists()
    assert not retry_path.exists()


def test_terminal_conflict_never_deletes_preexisting_destination_pair(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    quarantine = tmp_path / "quarantine"
    destination = quarantine / pending.name
    destination.write_bytes(_artifact())
    destination_hash = destination.with_suffix(".sha256")
    destination_hash.write_bytes(pending.with_suffix(".sha256").read_bytes())
    (quarantine / f"{RUN_ID}.reason.json").write_text(
        '{"status":403,"code":"key_disabled",'
        '"correlation_id":"corr-old",'
        '"observed_at":"2026-07-16T06:00:00Z"}',
        encoding="utf-8",
    )
    transport = FakeTransport()
    transport.respond(
        status=422,
        body={"code": "invalid_payload", "correlation_id": "corr-new"},
    )

    outcome = upload_one(pending, transport=transport, now=NOW)

    assert outcome.destination == "pending"
    assert outcome.code == "spool_transition_failed"
    assert destination.read_bytes() == _artifact()
    assert destination_hash.exists()
    assert pending.exists()


def test_orphan_terminal_reason_recovers_pair_without_network(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    quarantine = tmp_path / "quarantine"
    reason_path = quarantine / f"{RUN_ID}.reason.json"
    reason_path.write_text(
        '{"status":422,"code":"invalid_payload",'
        '"correlation_id":"corr-old",'
        '"observed_at":"2026-07-16T06:00:00Z"}',
        encoding="utf-8",
    )
    transport = FakeTransport()

    outcome = upload_one(pending, transport=transport, now=NOW)

    assert outcome.destination == "quarantine"
    assert transport.calls == []
    assert (quarantine / pending.name).read_bytes() == _artifact()
    assert (quarantine / pending.with_suffix(".sha256").name).exists()
    assert not pending.exists()


@pytest.mark.parametrize(
    (
        "destination",
        "status",
        "code",
        "correlation_id",
        "observed_at",
    ),
    [
        (
            "quarantine",
            404,
            "invalid_request",
            "corr-route",
            "2026-07-16T06:00:00Z",
        ),
        (
            "quarantine",
            400,
            "key_disabled",
            "corr-contradiction",
            "2026-07-16T06:00:00Z",
        ),
        (
            "blocked",
            401,
            "invalid_payload",
            "corr-contradiction",
            "2026-07-16T06:00:00Z",
        ),
        (
            "blocked",
            403,
            "payload_conflict",
            "corr-contradiction",
            "2026-07-16T06:00:00Z",
        ),
        (
            "quarantine",
            422,
            "invalid_payload",
            "corr-fractional",
            "2026-07-16T06:00:00.123Z",
        ),
    ],
    ids=[
        "unsupported-404",
        "quarantine-status-code-contradiction",
        "blocked-401-code-contradiction",
        "blocked-403-code-contradiction",
        "noncanonical-time",
    ],
)
def test_orphan_terminal_reason_requires_exact_live_authorization(
    tmp_path: Path,
    destination: str,
    status: int | None,
    code: str,
    correlation_id: str | None,
    observed_at: str,
) -> None:
    pending = _pending(tmp_path)
    reason_path = tmp_path / destination / f"{RUN_ID}.reason.json"
    reason_path.write_text(
        json.dumps(
            {
                "status": status,
                "code": code,
                "correlation_id": correlation_id,
                "observed_at": observed_at,
            },
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    transport = FakeTransport()
    transport.respond(status=201, body=_run_success_body(status=201))

    outcome = upload_one(pending, transport=transport, now=NOW)

    assert outcome.destination == "pending"
    assert outcome.code == "spool_transition_failed"
    assert transport.calls == []
    assert pending.read_bytes() == _artifact()
    assert pending.with_suffix(".sha256").exists()
    assert reason_path.exists()
    assert not (tmp_path / destination / pending.name).exists()
    assert not (
        tmp_path / destination / pending.with_suffix(".sha256").name
    ).exists()


@pytest.mark.parametrize(
    "reason_raw",
    [
        (
            b'{"status":422,"code":"invalid_payload",'
            b'"correlation_id":"bad correlation",'
            b'"observed_at":"2026-07-16T06:00:00Z"}'
        ),
        (
            b'{"status":422,"code":"invalid_payload",'
            b'"correlation_id":"corr-valid",'
            b'"observed_at":"2026-07-16T06:00:00Z","extra":true}'
        ),
        (
            b'{"status":422,"code":"invalid_payload",'
            b'"correlation_id":"corr-valid"}'
        ),
        (
            b'{"status":422,"code":"invalid_payload",'
            b'"code":"unsupported_schema",'
            b'"correlation_id":"corr-valid",'
            b'"observed_at":"2026-07-16T06:00:00Z"}'
        ),
    ],
    ids=[
        "invalid-correlation",
        "extra-field",
        "missing-time",
        "duplicate-code",
    ],
)
def test_orphan_terminal_reason_requires_strict_schema_fields(
    tmp_path: Path,
    reason_raw: bytes,
) -> None:
    pending = _pending(tmp_path)
    reason_path = tmp_path / "quarantine" / f"{RUN_ID}.reason.json"
    reason_path.write_bytes(reason_raw)
    transport = FakeTransport()

    outcome = upload_one(pending, transport=transport, now=NOW)

    assert outcome.destination == "pending"
    assert outcome.code == "spool_transition_failed"
    assert transport.calls == []
    assert pending.exists()
    assert reason_path.read_bytes() == reason_raw
    assert not (tmp_path / "quarantine" / pending.name).exists()


@pytest.mark.parametrize(
    ("destination", "status", "code"),
    [
        ("blocked", 401, "key_disabled"),
        ("blocked", 403, "key_scope_forbidden"),
        ("quarantine", 400, "invalid_request"),
        ("quarantine", 409, "payload_conflict"),
        ("quarantine", 409, "replayed_nonce"),
        ("quarantine", 413, "request_too_large"),
        ("quarantine", 422, "invalid_payload"),
        ("quarantine", 422, "unsupported_schema"),
    ],
)
def test_orphan_terminal_reason_uses_exact_live_destination_matrix(
    tmp_path: Path,
    destination: str,
    status: int,
    code: str,
) -> None:
    pending = _pending(tmp_path)
    reason_path = tmp_path / destination / f"{RUN_ID}.reason.json"
    reason_path.write_text(
        json.dumps(
            {
                "status": status,
                "code": code,
                "correlation_id": "corr-exact",
                "observed_at": "2026-07-16T06:00:00Z",
            },
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    transport = FakeTransport()

    outcome = upload_one(pending, transport=transport, now=NOW)

    assert outcome.destination == destination
    assert outcome.status == status
    assert outcome.code == code
    assert transport.calls == []
    assert (tmp_path / destination / pending.name).exists()
    assert not pending.exists()


def test_partial_archive_pair_recovers_without_network(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    archive = tmp_path / "archive"
    archived_artifact = archive / pending.name
    archived_artifact.write_bytes(_artifact())
    transport = FakeTransport()

    outcome = upload_one(pending, transport=transport, now=NOW)

    assert outcome.destination == "archive"
    assert transport.calls == []
    assert archived_artifact.with_suffix(".sha256").exists()
    assert not pending.exists()


def test_archive_fsync_failure_keeps_complete_pending_pair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pending = _pending(tmp_path)
    transport = FakeTransport()
    transport.respond(status=201, body=_run_success_body(status=201))
    import ru_probe_uploader

    original = ru_probe_uploader._fsync_directory

    def fail_archive(directory: Path) -> None:
        if directory.name == "archive":
            raise OSError("synthetic archive fsync failure")
        original(directory)

    monkeypatch.setattr(ru_probe_uploader, "_fsync_directory", fail_archive)

    outcome = upload_one(pending, transport=transport, now=NOW)

    assert outcome.destination == "pending"
    assert outcome.code == "archive_write_failed"
    assert pending.read_bytes() == _artifact()
    assert pending.with_suffix(".sha256").exists()
    assert not (tmp_path / "archive" / pending.name).exists()
    assert not (
        tmp_path / "archive" / pending.with_suffix(".sha256").name
    ).exists()


def test_pending_fsync_failure_restores_both_source_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pending = _pending(tmp_path)
    transport = FakeTransport()
    transport.respond(status=201, body=_run_success_body(status=201))
    import ru_probe_uploader

    original = ru_probe_uploader._fsync_directory

    def fail_pending(directory: Path) -> None:
        if directory.name == "pending":
            raise OSError("synthetic pending fsync failure")
        original(directory)

    monkeypatch.setattr(ru_probe_uploader, "_fsync_directory", fail_pending)

    outcome = upload_one(pending, transport=transport, now=NOW)

    assert outcome.destination == "pending"
    assert outcome.code == "archive_write_failed"
    assert pending.read_bytes() == _artifact()
    assert pending.with_suffix(".sha256").read_text(
        encoding="ascii"
    ).strip() == hashlib.sha256(_artifact()).hexdigest()


def test_writer_waiting_on_archive_transition_cannot_requeue_same_run_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pending = _pending(tmp_path)
    transport = FakeTransport()
    transport.respond(status=201, body=_run_success_body(status=201))
    import ru_probe_uploader

    transition_holds_lock = threading.Event()
    release_transition = threading.Event()
    writer_started = threading.Event()
    writer_done = threading.Event()
    original = ru_probe_uploader._atomic_write_private

    def pause_archive_write(path: Path, raw: bytes) -> None:
        if path.parent.name == "archive" and path.name == pending.name:
            transition_holds_lock.set()
            assert release_transition.wait(5)
        original(path, raw)

    monkeypatch.setattr(
        ru_probe_uploader,
        "_atomic_write_private",
        pause_archive_write,
    )
    upload_outcomes: list[object] = []
    writer_results: list[str] = []

    def uploader() -> None:
        upload_outcomes.append(
            upload_one(pending, transport=transport, now=NOW)
        )

    def writer() -> None:
        writer_started.set()
        try:
            write_pending_artifact(tmp_path, RUN_ID, _artifact() + b" ")
            writer_results.append("written")
        except SpoolError as exc:
            writer_results.append(exc.code)
        finally:
            writer_done.set()

    upload_thread = threading.Thread(target=uploader)
    writer_thread = threading.Thread(target=writer)
    upload_thread.start()
    assert transition_holds_lock.wait(5)
    writer_thread.start()
    assert writer_started.wait(5)
    assert not writer_done.wait(0.1)
    release_transition.set()
    upload_thread.join(5)
    writer_thread.join(5)

    assert [outcome.destination for outcome in upload_outcomes] == ["archive"]
    assert writer_results == ["run_id_conflict"]
    assert (tmp_path / "archive" / pending.name).read_bytes() == _artifact()
    assert not pending.exists()


def test_concurrent_upload_claim_sends_artifact_at_most_once(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    entered = threading.Event()
    release = threading.Event()

    class BlockingTransport(FakeTransport):
        def send(self, **kwargs):
            with self._lock:
                self.calls.append(dict(kwargs))
            entered.set()
            assert release.wait(5)
            return SimpleNamespace(
                status=201,
                body=json.dumps(
                    _run_success_body(status=201),
                    separators=(",", ":"),
                ).encode("utf-8"),
                headers={},
            )

    transport = BlockingTransport()
    outcomes: list[object] = []

    def worker() -> None:
        outcomes.append(upload_one(pending, transport=transport, now=NOW))

    first = threading.Thread(target=worker)
    second = threading.Thread(target=worker)
    first.start()
    assert entered.wait(5)
    second.start()
    second.join(5)
    release.set()
    first.join(5)

    assert len(transport.calls) == 1
    assert sorted(outcome.destination for outcome in outcomes) == [
        "archive",
        "pending",
    ]


def test_calculate_backoff_is_capped_and_jitter_is_bounded() -> None:
    assert calculate_backoff(0, jitter=lambda upper: upper) == 90
    assert calculate_backoff(12, jitter=lambda upper: upper) == 3600
    with pytest.raises(SpoolError, match="invalid_retry_attempt"):
        calculate_backoff(-1)


def test_build_heartbeat_is_separate_redacted_allowlisted_dto(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    os.utime(pending, (NOW.timestamp() - 300, NOW.timestamp() - 300))
    write_pending_artifact(tmp_path, OTHER_RUN_ID, _artifact(OTHER_RUN_ID))
    (tmp_path / "blocked" / "ignore.secret").write_text(
        "provider-token",
        encoding="utf-8",
    )

    heartbeat = build_heartbeat(
        tmp_path,
        probe_host_id="mini",
        now=NOW,
        service_version="2.0.0",
        archive_write_ok=False,
        last_error_code="archive_write_failed",
        disk_usage=lambda _path: SimpleNamespace(free=9 * 1024 * 1024 * 1024),
    )

    assert set(heartbeat) == {
        "schema_version",
        "probe_host_id",
        "observed_at",
        "service_version",
        "pending_count",
        "blocked_count",
        "quarantine_count",
        "oldest_pending_at",
        "archive_write_ok",
        "disk_free_bytes",
        "disk_state",
        "last_error_code",
    }
    assert heartbeat["pending_count"] == 2
    assert heartbeat["blocked_count"] == 0
    assert heartbeat["oldest_pending_at"] == "2026-07-16T06:25:00Z"
    assert heartbeat["disk_state"] == "ok"
    serialized = json.dumps(heartbeat)
    assert "provider-token" not in serialized
    assert "ignore.secret" not in serialized


def test_heartbeat_recovers_and_counts_complete_artifact_only_crash(
    tmp_path: Path,
) -> None:
    pending = tmp_path / "pending"
    pending.mkdir(mode=0o700)
    artifact = pending / f"{RUN_ID}.json"
    artifact.write_bytes(_artifact())

    heartbeat = build_heartbeat(
        tmp_path,
        probe_host_id="mini",
        now=NOW,
    )

    assert heartbeat["pending_count"] == 1
    assert artifact.with_suffix(".sha256").exists()


def test_invalid_last_error_is_not_reflected_into_heartbeat(
    tmp_path: Path,
) -> None:
    heartbeat = build_heartbeat(
        tmp_path,
        probe_host_id="mini",
        now=NOW,
        last_error_code="secret=/etc/pokrov-ru-probe/hmac.key",
    )

    assert heartbeat["last_error_code"] is None


def test_send_heartbeat_uses_distinct_body_and_endpoint(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    before = pending.read_bytes()
    transport = FakeTransport()
    transport.respond(status=201, body=_heartbeat_success_body())

    outcome = send_heartbeat(
        tmp_path,
        probe_host_id="mini",
        now=NOW,
        transport=transport,
    )

    assert outcome.destination == "sent"
    assert len(transport.calls) == 1
    call = transport.calls[0]
    assert call["path"].endswith("/heartbeat")
    assert call["raw_body"] != before
    assert json.loads(call["raw_body"])["schema_version"] == 1
    assert pending.read_bytes() == before


@pytest.mark.parametrize(
    "body",
    [
        b"",
        b"<html>ok</html>",
        {"code": "created"},
        {"code": "created", "correlation_id": "corr", "extra": True},
        b"{" + b'"padding":"' + b"x" * (64 * 1024) + b'"}',
    ],
    ids=[
        "empty",
        "html",
        "missing-correlation",
        "additional-field",
        "oversized",
    ],
)
def test_heartbeat_success_requires_strict_bounded_response(
    tmp_path: Path,
    body: dict[str, object] | bytes,
) -> None:
    transport = FakeTransport()
    transport.respond(status=201, body=body)

    outcome = send_heartbeat(
        tmp_path,
        probe_host_id="mini",
        now=NOW,
        transport=transport,
    )

    assert outcome.destination == "failed"
    assert outcome.code == "invalid_success_response"


@pytest.mark.parametrize(
    ("status", "body"),
    [
        (204, b""),
        (302, b"<html>moved</html>"),
        (404, {"code": "invalid_request", "correlation_id": "corr-404"}),
        (503, {"code": "payload_conflict", "correlation_id": "corr-503"}),
        (None, b""),
    ],
    ids=["204", "302", "404", "503-contradiction", "none"],
)
def test_heartbeat_unsupported_or_contradictory_response_is_unexpected(
    tmp_path: Path,
    status: object,
    body: dict[str, object] | bytes,
) -> None:
    transport = FakeTransport()
    transport.respond(status=status, body=body)

    outcome = send_heartbeat(
        tmp_path,
        probe_host_id="mini",
        now=NOW,
        transport=transport,
    )

    assert outcome.destination == "failed"
    assert outcome.code == "unexpected_response"
    assert outcome.status == (
        status
        if isinstance(status, int)
        and not isinstance(status, bool)
        and 100 <= status <= 599
        else None
    )
    assert outcome.correlation_id is None


def test_recovery_failure_reaches_outcome_heartbeat_and_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pending = tmp_path / "pending"
    pending.mkdir(mode=0o700)
    artifact = pending / f"{RUN_ID}.json"
    artifact.write_bytes(_artifact())
    import ru_probe_uploader

    original = ru_probe_uploader._atomic_write_private

    def fail_sidecar(path: Path, raw: bytes) -> None:
        if path.suffix == ".sha256":
            raise SpoolError("atomic_write_failed")
        original(path, raw)

    monkeypatch.setattr(
        ru_probe_uploader,
        "_atomic_write_private",
        fail_sidecar,
    )
    transport = FakeTransport()
    transport.respond(status=201, body=_heartbeat_success_body())

    outcomes, heartbeat = ru_probe_uploader.run_uploader_once(
        spool_root=tmp_path,
        probe_host_id="mini",
        now=NOW,
        transport=transport,
    )

    assert [outcome.code for outcome in outcomes] == [
        "spool_recovery_failed"
    ]
    assert heartbeat.destination == "sent"
    assert ru_probe_uploader._local_service_failed(outcomes, heartbeat)
    assert len(transport.calls) == 1
    sent_heartbeat = json.loads(transport.calls[0]["raw_body"])
    assert sent_heartbeat["pending_count"] == 1
    assert sent_heartbeat["archive_write_ok"] is False
    assert sent_heartbeat["last_error_code"] == "spool_recovery_failed"
    assert artifact.exists()


def test_recovery_fsync_failure_does_not_upload_repaired_pair_same_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pending = tmp_path / "pending"
    pending.mkdir(mode=0o700)
    artifact = pending / f"{RUN_ID}.json"
    artifact.write_bytes(_artifact())
    import ru_probe_uploader

    original = ru_probe_uploader._fsync_directory
    failures = 0

    def fail_first_pending(directory: Path) -> None:
        nonlocal failures
        if directory.name == "pending" and failures == 0:
            failures += 1
            raise OSError("synthetic recovery fsync failure")
        original(directory)

    monkeypatch.setattr(
        ru_probe_uploader,
        "_fsync_directory",
        fail_first_pending,
    )
    transport = FakeTransport()
    transport.respond(status=201, body=_heartbeat_success_body())

    outcomes, heartbeat = ru_probe_uploader.run_uploader_once(
        spool_root=tmp_path,
        probe_host_id="mini",
        now=NOW,
        transport=transport,
    )

    assert [outcome.code for outcome in outcomes] == [
        "spool_recovery_failed"
    ]
    assert heartbeat.destination == "sent"
    assert artifact.with_suffix(".sha256").exists()
    assert [call["path"] for call in transport.calls] == [
        ru_probe_uploader.HEARTBEAT_PATH
    ]


def test_critical_disk_heartbeat_marks_local_service_failed(
    tmp_path: Path,
) -> None:
    transport = FakeTransport()
    transport.respond(status=201, body=_heartbeat_success_body())
    import ru_probe_uploader

    outcome = send_heartbeat(
        tmp_path,
        probe_host_id="mini",
        now=NOW,
        transport=transport,
        disk_usage=lambda _path: SimpleNamespace(free=0),
    )

    assert outcome.destination == "sent"
    assert outcome.disk_state == "critical"
    assert ru_probe_uploader._local_service_failed([], outcome)


def test_retry_state_persists_and_enforces_due_time_across_invocations(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    retry_path = pending.with_suffix(".retry.json")
    artifact_before = pending.read_bytes()
    hash_before = pending.with_suffix(".sha256").read_bytes()
    first_transport = FakeTransport()
    first_transport.respond(
        status=503,
        body={"code": "temporary", "correlation_id": "corr-1"},
    )
    first_transport.respond(status=201, body=_heartbeat_success_body())
    import ru_probe_uploader

    first, first_heartbeat = ru_probe_uploader.run_uploader_once(
        spool_root=tmp_path,
        probe_host_id="mini",
        now=NOW,
        transport=first_transport,
        jitter=lambda _upper: 0,
    )

    assert first[0].retry_after_seconds == 60
    assert first_heartbeat.destination == "sent"
    assert json.loads(retry_path.read_text(encoding="utf-8")) == {
        "attempt": 1,
        "next_attempt_at": "2026-07-16T06:31:00Z",
        "last_http_status": 503,
        "last_code": "temporary",
    }
    assert pending.read_bytes() == artifact_before
    assert pending.with_suffix(".sha256").read_bytes() == hash_before
    assert not list(tmp_path.rglob("*.tmp"))
    if os.name != "nt":
        assert retry_path.stat().st_mode & 0o777 == 0o600

    early_transport = FakeTransport()
    early_transport.respond(status=201, body=_heartbeat_success_body())
    early, early_heartbeat = ru_probe_uploader.run_uploader_once(
        spool_root=tmp_path,
        probe_host_id="mini",
        now=NOW.replace(second=30),
        transport=early_transport,
        jitter=lambda _upper: 0,
    )

    assert early == []
    assert early_heartbeat.destination == "sent"
    assert [call["path"] for call in early_transport.calls] == [
        ru_probe_uploader.HEARTBEAT_PATH
    ]

    second_transport = FakeTransport()
    second_transport.respond(
        status=503,
        body={"code": "temporary", "correlation_id": "corr-2"},
    )
    second_transport.respond(status=201, body=_heartbeat_success_body())
    second_now = NOW.replace(minute=31, second=1)
    second, _ = ru_probe_uploader.run_uploader_once(
        spool_root=tmp_path,
        probe_host_id="mini",
        now=second_now,
        transport=second_transport,
        jitter=lambda _upper: 0,
    )

    assert second[0].retry_after_seconds == 120
    assert json.loads(retry_path.read_text(encoding="utf-8")) == {
        "attempt": 2,
        "next_attempt_at": "2026-07-16T06:33:01Z",
        "last_http_status": 503,
        "last_code": "temporary",
    }

    terminal_transport = FakeTransport()
    terminal_transport.respond(
        status=201,
        body=_run_success_body(status=201),
    )
    terminal_transport.respond(status=201, body=_heartbeat_success_body())
    terminal, terminal_heartbeat = ru_probe_uploader.run_uploader_once(
        spool_root=tmp_path,
        probe_host_id="mini",
        now=NOW.replace(minute=33, second=2),
        transport=terminal_transport,
        jitter=lambda _upper: 0,
    )

    assert terminal[0].destination == "archive"
    assert terminal_heartbeat.destination == "sent"
    assert not retry_path.exists()
    assert (tmp_path / "archive" / pending.name).exists()


def test_malformed_retry_state_fails_closed_without_reset_or_upload(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    retry_path = pending.with_suffix(".retry.json")
    retry_path.write_text(
        '{"attempt":-1,"next_attempt_at":"secret",'
        '"last_http_status":503,"last_code":"temporary"}',
        encoding="utf-8",
    )
    raw_before = retry_path.read_bytes()
    transport = FakeTransport()
    transport.respond(status=201, body=_heartbeat_success_body())
    import ru_probe_uploader

    outcomes, heartbeat = ru_probe_uploader.run_uploader_once(
        spool_root=tmp_path,
        probe_host_id="mini",
        now=NOW,
        transport=transport,
    )

    assert [outcome.code for outcome in outcomes] == [
        "spool_recovery_failed"
    ]
    assert heartbeat.destination == "sent"
    assert retry_path.read_bytes() == raw_before
    assert [call["path"] for call in transport.calls] == [
        ru_probe_uploader.HEARTBEAT_PATH
    ]


def test_retry_state_symlink_fails_closed_without_touching_target(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    outside = tmp_path / "outside-retry.json"
    outside.write_text(
        '{"attempt":1,"next_attempt_at":"2026-07-16T06:31:00Z",'
        '"last_http_status":503,"last_code":"temporary"}',
        encoding="utf-8",
    )
    retry_path = pending.with_suffix(".retry.json")
    try:
        retry_path.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks unavailable")
    outside_before = outside.read_bytes()
    transport = FakeTransport()
    transport.respond(status=201, body=_heartbeat_success_body())
    import ru_probe_uploader

    outcomes, heartbeat = ru_probe_uploader.run_uploader_once(
        spool_root=tmp_path,
        probe_host_id="mini",
        now=NOW,
        transport=transport,
    )

    assert [outcome.code for outcome in outcomes] == [
        "spool_recovery_failed"
    ]
    assert heartbeat.destination == "sent"
    assert outside.read_bytes() == outside_before
    assert [call["path"] for call in transport.calls] == [
        ru_probe_uploader.HEARTBEAT_PATH
    ]


def test_retry_state_far_future_is_tampered_and_fails_closed(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    retry_path = pending.with_suffix(".retry.json")
    retry_path.write_text(
        '{"attempt":1,"next_attempt_at":"2026-07-17T06:30:00Z",'
        '"last_http_status":503,"last_code":"temporary"}',
        encoding="utf-8",
    )
    transport = FakeTransport()
    transport.respond(status=201, body=_heartbeat_success_body())
    import ru_probe_uploader

    outcomes, _ = ru_probe_uploader.run_uploader_once(
        spool_root=tmp_path,
        probe_host_id="mini",
        now=NOW,
        transport=transport,
    )

    assert [outcome.code for outcome in outcomes] == [
        "spool_recovery_failed"
    ]
    assert [call["path"] for call in transport.calls] == [
        ru_probe_uploader.HEARTBEAT_PATH
    ]


def test_retry_state_fsync_failure_keeps_artifact_and_reports_local_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pending = _pending(tmp_path)
    artifact_before = pending.read_bytes()
    hash_before = pending.with_suffix(".sha256").read_bytes()
    transport = FakeTransport()
    transport.respond(status=503, body={"code": "temporary"})
    import ru_probe_uploader

    original = ru_probe_uploader._fsync_directory

    def fail_pending(directory: Path) -> None:
        if directory.name == "pending":
            raise OSError("synthetic retry fsync failure")
        original(directory)

    monkeypatch.setattr(ru_probe_uploader, "_fsync_directory", fail_pending)

    outcome = upload_one(
        pending,
        transport=transport,
        now=NOW,
        jitter=lambda _upper: 0,
    )

    assert outcome.destination == "pending"
    assert outcome.code == "spool_recovery_failed"
    assert pending.read_bytes() == artifact_before
    assert pending.with_suffix(".sha256").read_bytes() == hash_before
    assert pending.with_suffix(".retry.json").exists()


def test_concurrent_retry_writers_advance_state_once(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    entered = threading.Event()
    release = threading.Event()

    class BlockingRetryTransport(FakeTransport):
        def send(self, **kwargs):
            with self._lock:
                self.calls.append(dict(kwargs))
            entered.set()
            assert release.wait(5)
            return SimpleNamespace(
                status=503,
                body=b'{"code":"temporary"}',
                headers={},
            )

    transport = BlockingRetryTransport()
    outcomes: list[object] = []

    def worker() -> None:
        outcomes.append(
            upload_one(
                pending,
                transport=transport,
                now=NOW,
                jitter=lambda _upper: 0,
            )
        )

    first = threading.Thread(target=worker)
    second = threading.Thread(target=worker)
    first.start()
    assert entered.wait(5)
    second.start()
    second.join(5)
    release.set()
    first.join(5)

    assert len(transport.calls) == 1
    assert sorted(outcome.code for outcome in outcomes) == [
        "temporary",
        "upload_in_progress",
    ]
    retry = json.loads(
        pending.with_suffix(".retry.json").read_text(encoding="utf-8")
    )
    assert retry["attempt"] == 1


def test_runner_defaults_to_pending_spool_and_explicit_out_stays_manual(
    tmp_path: Path,
) -> None:
    runner = _load_runner()
    payload = {
        "schema_version": 2,
        "run_id": RUN_ID,
        "origin": "ru",
    }

    spooled = runner.write_run_artifact(
        payload,
        spool_root=tmp_path,
        out_path=None,
    )
    manual = runner.write_run_artifact(
        {**payload, "run_id": OTHER_RUN_ID},
        spool_root=tmp_path,
        out_path=tmp_path / "manual.json",
    )

    assert spooled == tmp_path / "pending" / f"{RUN_ID}.json"
    assert spooled.with_suffix(".sha256").exists()
    assert manual == tmp_path / "manual.json"
    assert not (tmp_path / "pending" / f"{OTHER_RUN_ID}.json").exists()


def test_runner_main_reports_existing_terminal_path_without_requeue(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = _load_runner()
    payload = {
        "schema_version": 2,
        "run_id": RUN_ID,
        "origin": "ru",
        "execution_status": "completed",
    }
    pending = runner.write_run_artifact(
        payload,
        spool_root=tmp_path,
        out_path=None,
    )
    transport = FakeTransport()
    transport.respond(status=201, body=_run_success_body(status=201))
    archived = upload_one(pending, transport=transport, now=NOW).path
    assert archived is not None
    args = SimpleNamespace(
        api_base_url="https://api.example.test",
        key_id="ru-mini-v1",
        secret_file=str(tmp_path / "secret"),
        manifest_cache=str(tmp_path / "manifest.json"),
        spool_root=str(tmp_path),
        probe_host_id="mini",
        probe_host_label="mini",
        probe_public_ip="",
        profile_registry=str(tmp_path / "profiles.json"),
        timeout_sec=5.0,
        out="",
    )

    with (
        mock.patch.object(
            runner,
            "build_parser",
            return_value=SimpleNamespace(parse_args=lambda: args),
        ),
        mock.patch.object(runner, "fetch_manifest", return_value={}),
        mock.patch.object(runner, "run_manifest", return_value=payload),
    ):
        exit_code = runner.main()

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == str(archived)
    assert captured.err == ""
    assert archived.exists()
    assert not (tmp_path / "pending" / f"{RUN_ID}.json").exists()


def test_uploader_rejects_pending_symlink_without_sending(
    tmp_path: Path,
) -> None:
    pending_dir = tmp_path / "pending"
    pending_dir.mkdir(mode=0o700)
    target = tmp_path / "outside.json"
    target.write_bytes(_artifact())
    symlink = pending_dir / f"{RUN_ID}.json"
    try:
        symlink.symlink_to(target)
    except OSError:
        pytest.skip("symlinks unavailable")
    symlink.with_suffix(".sha256").write_text(
        hashlib.sha256(_artifact()).hexdigest() + "\n",
        encoding="ascii",
    )
    transport = FakeTransport()

    with pytest.raises(SpoolError, match="artifact_symlink"):
        upload_one(symlink, transport=transport, now=NOW)
    assert transport.calls == []


def test_systemd_templates_are_hardened_and_schedules_are_exact() -> None:
    probe_service = (REPO_ROOT / "infra" / "pokrov-ru-probe.service").read_text(
        encoding="utf-8"
    )
    probe_timer = (REPO_ROOT / "infra" / "pokrov-ru-probe.timer").read_text(
        encoding="utf-8"
    )
    uploader_service = (
        REPO_ROOT / "infra" / "pokrov-ru-probe-uploader.service"
    ).read_text(encoding="utf-8")
    uploader_timer = (
        REPO_ROOT / "infra" / "pokrov-ru-probe-uploader.timer"
    ).read_text(encoding="utf-8")

    assert "OnCalendar=*-*-* 00,06,12,18:00:00" in probe_timer
    assert "Persistent=true" in probe_timer
    assert "RandomizedDelaySec=5m" in probe_timer
    assert "OnBootSec=2m" in uploader_timer
    assert "OnUnitActiveSec=15m" in uploader_timer
    assert "Persistent=true" in uploader_timer
    for service in (probe_service, uploader_service):
        assert "User=pokrov-ru-probe" in service
        assert "StateDirectory=pokrov-ru-probe" in service
        assert "StateDirectoryMode=0700" in service
        assert "UMask=0077" in service
        assert "NoNewPrivileges=true" in service
        assert "PrivateTmp=true" in service
        assert "ProtectSystem=strict" in service
        assert "ReadWritePaths=/var/lib/pokrov-ru-probe" in service
        assert "EnvironmentFile=/etc/pokrov-ru-probe/" in service
        assert "secret=" not in service.lower()
        assert "token=" not in service.lower()


def test_static_task8_files_are_registered_in_manifest() -> None:
    manifest = json.loads(
        (SCRIPTS_DIR / "manifest.yaml").read_text(encoding="utf-8")
    )
    active = set(manifest["active"])
    assert {
        "scripts/ru_probe_runner.py",
        "scripts/ru_probe_uploader.py",
        "scripts/ru_probe_payload.schema.json",
        "infra/pokrov-ru-probe.service",
        "infra/pokrov-ru-probe.timer",
        "infra/pokrov-ru-probe-uploader.service",
        "infra/pokrov-ru-probe-uploader.timer",
    }.issubset(active)


def test_default_transport_delegates_each_attempt_to_shared_hmac_client(
    tmp_path: Path,
) -> None:
    pending = _pending(tmp_path)
    responses = [
        SimpleNamespace(
            status=409,
            body=b'{"code":"replayed_nonce"}',
            headers={},
        ),
        SimpleNamespace(
            status=201,
            body=json.dumps(
                _run_success_body(status=201),
                separators=(",", ":"),
            ).encode("utf-8"),
            headers={},
        ),
    ]
    import ru_probe_uploader

    with mock.patch.object(
        ru_probe_uploader.internal_hmac_client,
        "signed_request",
        side_effect=responses,
    ) as signed:
        outcome = upload_one(
            pending,
            transport=None,
            now=NOW,
            api_base_url="https://api.example.test",
            key_id="mini-v1",
            secret_file=tmp_path / "hmac.key",
        )

    assert outcome.destination == "archive"
    assert signed.call_count == 2
    assert [call.kwargs["raw_body"] for call in signed.call_args_list] == [
        _artifact(),
        _artifact(),
    ]
