from __future__ import annotations

import copy
import hashlib
import importlib
import json
import sys
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


MANIFEST_PATH = "/api/internal/probes/ru-origin/manifest"
RUNS_PATH = "/api/internal/probes/ru-origin/runs"
HEARTBEAT_PATH = "/api/internal/probes/ru-origin/heartbeat"
ACTIVE_KEY_ID = "ru-mini-active"
ACTIVE_SECRET = b"ru-mini-test-secret-material"
SAFE_CORRELATION_ID = "probe-request-001"


def _registry_payload() -> dict[str, object]:
    return {
        "keys": [
            {
                "key_id": ACTIVE_KEY_ID,
                "secret": ACTIVE_SECRET.decode("ascii"),
                "subject": "mini",
                "scopes": [
                    "ru_probe:manifest",
                    "ru_probe:ingest",
                    "ru_probe:heartbeat",
                ],
                "origins": ["ru"],
                "enabled": True,
            },
            {
                "key_id": "ru-wrong-scope",
                "secret": "wrong-scope-secret-material",
                "subject": "mini",
                "scopes": ["release:ingest"],
                "origins": ["ru"],
                "enabled": True,
            },
            {
                "key_id": "ru-wrong-origin",
                "secret": "wrong-origin-secret-material",
                "subject": "mini",
                "scopes": ["ru_probe:ingest"],
                "origins": ["current"],
                "enabled": True,
            },
            {
                "key_id": "ru-disabled",
                "secret": "disabled-key-secret-material",
                "subject": "mini",
                "scopes": ["ru_probe:ingest"],
                "origins": ["ru"],
                "enabled": False,
            },
            {
                "key_id": "ru-manifest-only",
                "secret": "manifest-only-secret-material",
                "subject": "mini",
                "scopes": ["ru_probe:manifest"],
                "origins": ["ru"],
                "enabled": True,
            },
            {
                "key_id": "ru-heartbeat-only",
                "secret": "heartbeat-only-secret-material",
                "subject": "mini",
                "scopes": ["ru_probe:heartbeat"],
                "origins": ["ru"],
                "enabled": True,
            },
        ]
    }


def _load_api(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "ru-probe-ingest.db"
    registry_path = tmp_path / "internal-keys.json"
    registry_path.write_text(
        json.dumps(_registry_payload(), separators=(",", ":")),
        encoding="utf-8",
    )
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("INTERNAL_HMAC_KEYS_FILE", str(registry_path))
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "ru-probe-web-secret")
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.pokrov.test")
    monkeypatch.setenv("PUBLIC_WEB_DOMAIN", "pokrov.test")
    monkeypatch.setenv("PUBLIC_CHANNEL", "pokrov_vpn")
    monkeypatch.setenv("BOT_USERNAME", "pokrov_vpnbot")
    monkeypatch.setenv("SUPPORT_BOT_USERNAME", "pokrov_supportbot")
    monkeypatch.setenv("BOT_TOKEN", "test_bot_token_123")
    monkeypatch.setenv("ADMIN_ID", "9999")
    monkeypatch.setenv("ADMIN_IDS", "9999")
    monkeypatch.delenv("RU_PROBE_CANONICAL_TARGETS_JSON", raising=False)
    monkeypatch.delenv("RU_PROBE_RESERVE_TARGETS_JSON", raising=False)
    monkeypatch.delenv("RU_PROBE_RETENTION_DAYS", raising=False)

    for name in [
        "api",
        "admin_ops_service",
        "app_first_service",
        "config",
        "db",
        "migrations",
        "models",
        "web_auth_service",
        "control_panel",
        "nodes_repo",
        "tickets_repo",
        "events_service",
        "offers_service",
        "pay_attempts_service",
        "points_service",
        "free_cycle_service",
        "gift_cards_service",
        "payment_providers",
        "shared_surface_facts",
        "transport_catalog",
        "node_policy",
        "internal_request_auth",
        "ru_probe_contract",
        "ru_probe_service",
    ]:
        sys.modules.pop(name, None)
    return importlib.import_module("api")


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    return _load_api(monkeypatch, tmp_path)


@pytest.fixture
def client(api):
    with TestClient(api.app) as value:
        yield value


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _key_secret(key_id: str) -> bytes:
    for entry in _registry_payload()["keys"]:
        if entry["key_id"] == key_id:
            return str(entry["secret"]).encode("ascii")
    raise AssertionError(f"unknown test key {key_id}")


def _signed_headers(
    *,
    method: str,
    path: str,
    raw_body: bytes,
    nonce: str,
    key_id: str = ACTIVE_KEY_ID,
    secret: bytes | None = None,
    correlation_id: str = SAFE_CORRELATION_ID,
    timestamp: datetime | None = None,
) -> dict[str, str]:
    from internal_request_auth import sign_internal_request

    timestamp_text = str(int((timestamp or _utc_now()).timestamp()))
    signing_secret = secret if secret is not None else _key_secret(key_id)
    return {
        "X-Internal-Key-Id": key_id,
        "X-Internal-Timestamp": timestamp_text,
        "X-Internal-Nonce": nonce,
        "X-Internal-Signature": sign_internal_request(
            signing_secret,
            method,
            path,
            timestamp_text,
            nonce,
            raw_body,
        ),
        "X-Correlation-ID": correlation_id,
    }


def _manifest(api, *, now: datetime | None = None) -> dict[str, object]:
    from ru_probe_service import build_ru_manifest

    session = api.SessionLocal()
    try:
        return build_ru_manifest(session, now=now or _utc_now())
    finally:
        session.close()


def _payload_from_manifest(
    manifest: dict[str, object],
    *,
    now: datetime | None = None,
    run_id: str | None = None,
    execution_status: str = "completed",
) -> dict[str, object]:
    finished_at = (now or _utc_now()) - timedelta(minutes=1)
    targets: list[dict[str, object]] = []
    for expected in manifest["targets"]:
        stages: dict[str, dict[str, object]] = {}
        for stage_name in (
            "dns",
            "tcp",
            "tls",
            "http_large_body",
            "transport_handshake",
        ):
            required = stage_name in expected["required_stages"]
            stages[stage_name] = {
                "status": "pass" if required else "not_applicable",
                "latency_ms": 10 if required else None,
                "code": None,
            }
        families = expected["endpoint"]["address_families"]
        targets.append(
            {
                "target_id": expected["target_id"],
                "target_kind": expected["target_kind"],
                "scope": expected["scope"],
                "node_code": expected["node_code"],
                "endpoint": copy.deepcopy(expected["endpoint"]),
                "endpoint_fingerprint": expected["endpoint_fingerprint"],
                "stages": stages,
                "address_family_status": {
                    "ipv4": "pass" if "ipv4" in families else "not_applicable",
                    "ipv6": "pass" if "ipv6" in families else "not_applicable",
                },
                "transport": {
                    "profile_code": expected["endpoint"]["transport_profile"],
                    "handshake_status": stages["transport_handshake"]["status"],
                    "classification": "ok",
                    "detail_code": None,
                },
                "detail_code": None,
                "detail": None,
            }
        )
    return {
        "schema_version": 2,
        "run_id": run_id or str(uuid.uuid4()),
        "origin": "ru",
        "probe_host": {"id": "mini", "label": "Мини", "public_ip": None},
        "runner_version": "2.0.0",
        "manifest_revision": manifest["manifest_revision"],
        "started_at": (finished_at - timedelta(minutes=2))
        .isoformat()
        .replace("+00:00", "Z"),
        "finished_at": finished_at.isoformat().replace("+00:00", "Z"),
        "execution_status": execution_status,
        "evidence_code": None,
        "targets": targets,
    }


def _post_run(
    client: TestClient,
    raw_body: bytes,
    *,
    nonce: str,
    key_id: str = ACTIVE_KEY_ID,
    secret: bytes | None = None,
    correlation_id: str = SAFE_CORRELATION_ID,
):
    return client.post(
        RUNS_PATH,
        content=raw_body,
        headers=_signed_headers(
            method="POST",
            path=RUNS_PATH,
            raw_body=raw_body,
            nonce=nonce,
            key_id=key_id,
            secret=secret,
            correlation_id=correlation_id,
        ),
    )


def _heartbeat_payload(
    *,
    observed_at: datetime | None = None,
    probe_host_id: str = "mini",
    pending_count: int = 0,
) -> dict[str, object]:
    observed = observed_at or (_utc_now() - timedelta(seconds=5))
    return {
        "schema_version": 1,
        "probe_host_id": probe_host_id,
        "observed_at": observed.isoformat().replace("+00:00", "Z"),
        "service_version": "2.0.0",
        "pending_count": pending_count,
        "blocked_count": 0,
        "quarantine_count": 0,
        "oldest_pending_at": (
            (observed - timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
            if pending_count
            else None
        ),
        "archive_write_ok": True,
        "disk_free_bytes": 10 * 1024 * 1024 * 1024,
        "disk_state": "ok",
        "last_error_code": None,
    }


def _post_heartbeat(client: TestClient, raw_body: bytes, *, nonce: str):
    return client.post(
        HEARTBEAT_PATH,
        content=raw_body,
        headers=_signed_headers(
            method="POST",
            path=HEARTBEAT_PATH,
            raw_body=raw_body,
            nonce=nonce,
        ),
    )


def test_manifest_get_authenticates_exact_empty_body_and_returns_server_manifest(
    api, client: TestClient
) -> None:
    response = client.request(
        "GET",
        MANIFEST_PATH,
        content=b"",
        headers=_signed_headers(
            method="GET",
            path=MANIFEST_PATH,
            raw_body=b"",
            nonce="manifest-001",
        ),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {
        "manifest_schema_version",
        "manifest_revision",
        "generated_at",
        "max_cache_age_seconds",
        "targets",
    }
    assert body["manifest_schema_version"] == 1
    assert body["targets"]
    from models import InternalIngestNonce

    session = api.SessionLocal()
    try:
        assert session.query(InternalIngestNonce).count() == 1
    finally:
        session.close()


@pytest.mark.parametrize(
    ("key_id", "secret", "expected_status", "expected_code"),
    [
        ("ru-wrong-scope", None, 403, "key_scope_forbidden"),
        ("ru-wrong-origin", None, 403, "key_scope_forbidden"),
        ("ru-disabled", None, 401, "key_disabled"),
        (ACTIVE_KEY_ID, b"incorrect-secret-material", 401, "key_disabled"),
    ],
)
def test_run_auth_failures_use_bounded_stable_errors(
    api,
    client: TestClient,
    key_id: str,
    secret: bytes | None,
    expected_status: int,
    expected_code: str,
) -> None:
    raw = _json_bytes(_payload_from_manifest(_manifest(api)))
    response = _post_run(
        client,
        raw,
        nonce=f"auth-{key_id}",
        key_id=key_id,
        secret=secret,
        correlation_id="corr-auth",
    )

    assert response.status_code == expected_status
    assert response.json() == {
        "code": expected_code,
        "correlation_id": "corr-auth",
    }
    assert "signature" not in response.text.lower()
    assert "secret" not in response.text.lower()


def test_missing_auth_header_is_401_and_does_not_store_nonce(
    api, client: TestClient
) -> None:
    raw = _json_bytes(_payload_from_manifest(_manifest(api)))
    response = client.post(RUNS_PATH, content=raw)

    assert response.status_code == 401
    assert set(response.json()) == {"code", "correlation_id"}
    assert response.json()["code"] == "key_disabled"
    from models import InternalIngestNonce

    session = api.SessionLocal()
    try:
        assert session.query(InternalIngestNonce).count() == 0
    finally:
        session.close()


def test_endpoint_scopes_are_not_interchangeable(client: TestClient) -> None:
    empty = b""
    manifest_allowed = client.request(
        "GET",
        MANIFEST_PATH,
        content=empty,
        headers=_signed_headers(
            method="GET",
            path=MANIFEST_PATH,
            raw_body=empty,
            nonce="manifest-only-ok",
            key_id="ru-manifest-only",
        ),
    )
    assert manifest_allowed.status_code == 200

    heartbeat_raw = _json_bytes(_heartbeat_payload())
    manifest_key_on_heartbeat = client.post(
        HEARTBEAT_PATH,
        content=heartbeat_raw,
        headers=_signed_headers(
            method="POST",
            path=HEARTBEAT_PATH,
            raw_body=heartbeat_raw,
            nonce="manifest-on-heartbeat",
            key_id="ru-manifest-only",
        ),
    )
    assert manifest_key_on_heartbeat.status_code == 403
    assert manifest_key_on_heartbeat.json()["code"] == "key_scope_forbidden"

    heartbeat_key_on_manifest = client.request(
        "GET",
        MANIFEST_PATH,
        content=empty,
        headers=_signed_headers(
            method="GET",
            path=MANIFEST_PATH,
            raw_body=empty,
            nonce="heartbeat-on-manifest",
            key_id="ru-heartbeat-only",
        ),
    )
    assert heartbeat_key_on_manifest.status_code == 403
    assert heartbeat_key_on_manifest.json()["code"] == "key_scope_forbidden"


def test_signed_internal_routes_reject_query_string_alias(
    client: TestClient,
) -> None:
    headers = _signed_headers(
        method="GET",
        path=MANIFEST_PATH,
        raw_body=b"",
        nonce="manifest-query",
    )
    rejected = client.request(
        "GET",
        f"{MANIFEST_PATH}?cache=1",
        content=b"",
        headers=headers,
    )
    assert rejected.status_code == 400
    assert rejected.json()["code"] == "invalid_request"

    accepted = client.request(
        "GET",
        MANIFEST_PATH,
        content=b"",
        headers=headers,
    )
    assert accepted.status_code == 200


@pytest.mark.parametrize(
    ("path", "limit"),
    [(RUNS_PATH, 512 * 1024), (HEARTBEAT_PATH, 64 * 1024)],
)
def test_raw_body_limits_accept_limit_and_reject_limit_plus_one(
    client: TestClient, path: str, limit: int
) -> None:
    exact = b"{" + (b" " * (limit - 2)) + b"}"
    exact_response = client.post(
        path,
        content=exact,
        headers=_signed_headers(
            method="POST",
            path=path,
            raw_body=exact,
            nonce=f"limit-{limit}",
        ),
    )
    assert exact_response.status_code == 422
    assert exact_response.json()["code"] == "invalid_payload"

    oversized = exact + b"x"
    oversized_response = client.post(
        path,
        content=oversized,
        headers=_signed_headers(
            method="POST",
            path=path,
            raw_body=oversized,
            nonce=f"over-{limit}",
        ),
    )
    assert oversized_response.status_code == 413
    assert oversized_response.json()["code"] == "request_too_large"


@pytest.mark.parametrize(
    "invalid_raw",
    [
        b"{",
        b'{"schema_version":2,"schema_version":2}',
        b'{"schema_version":NaN}',
        b"\xff",
    ],
)
def test_malformed_or_duplicate_json_rolls_back_nonce(
    api, client: TestClient, invalid_raw: bytes
) -> None:
    nonce = f"invalid-json-{hashlib.sha256(invalid_raw).hexdigest()[:12]}"
    rejected = _post_run(client, invalid_raw, nonce=nonce)
    assert rejected.status_code == 422
    assert rejected.json()["code"] == "invalid_payload"

    valid_raw = _json_bytes(_payload_from_manifest(_manifest(api)))
    accepted = _post_run(client, valid_raw, nonce=nonce)
    assert accepted.status_code == 201, accepted.text


def test_empty_body_and_duplicate_target_are_422_before_commit(
    api, client: TestClient
) -> None:
    empty = _post_run(client, b"", nonce="empty-body")
    assert empty.status_code == 422
    assert empty.json()["code"] == "invalid_payload"

    payload = _payload_from_manifest(_manifest(api))
    payload["targets"].append(copy.deepcopy(payload["targets"][0]))
    duplicate_raw = _json_bytes(payload)
    duplicate = _post_run(client, duplicate_raw, nonce="duplicate-target")
    assert duplicate.status_code == 422
    assert duplicate.json()["code"] == "invalid_payload"

    payload["targets"].pop()
    accepted = _post_run(
        client,
        _json_bytes(payload),
        nonce="duplicate-target",
    )
    assert accepted.status_code == 201, accepted.text


def test_same_run_same_exact_bytes_is_idempotent_and_maps_all_db_rows(
    api, client: TestClient
) -> None:
    payload = _payload_from_manifest(_manifest(api))
    raw = _json_bytes(payload)

    first = _post_run(client, raw, nonce="run-idempotent-1")
    second = _post_run(client, raw, nonce="run-idempotent-2")

    assert first.status_code == 201, first.text
    assert second.status_code == 200, second.text
    expected_keys = {
        "code",
        "run_db_id",
        "run_id",
        "created",
        "current_eligible",
        "correlation_id",
    }
    assert set(first.json()) == expected_keys
    assert set(second.json()) == expected_keys
    assert first.json()["code"] == "created"
    assert first.json()["run_id"] == payload["run_id"]
    assert first.json()["run_db_id"] > 0
    assert first.json()["created"] is True
    assert first.json()["current_eligible"] is True
    assert second.json()["run_db_id"] == first.json()["run_db_id"]
    assert second.json()["created"] is False

    from models import InternalIngestNonce, RuProbeRun, RuProbeTargetResult

    session = api.SessionLocal()
    try:
        run = session.query(RuProbeRun).one()
        targets = (
            session.query(RuProbeTargetResult)
            .filter(RuProbeTargetResult.run_db_id == run.id)
            .order_by(RuProbeTargetResult.target_id.asc())
            .all()
        )
        assert run.artifact_sha256 == hashlib.sha256(raw).hexdigest()
        assert run.ingest_key_id == ACTIVE_KEY_ID
        assert run.probe_host_id == "mini"
        assert run.current_eligible is True
        assert run.release_verdict == "pass"
        assert len(targets) == len(payload["targets"])
        assert targets[0].requested_address_families_json == ["ipv4", "ipv6"]
        assert set(targets[0].transport_metadata_json) == {
            "address_family_status",
            "transport",
        }
        assert session.query(InternalIngestNonce).count() == 2
        session.delete(run)
        session.commit()
        assert session.query(RuProbeTargetResult).count() == 0
    finally:
        session.close()


def test_same_run_different_exact_bytes_is_payload_conflict(
    api, client: TestClient
) -> None:
    payload = _payload_from_manifest(_manifest(api))
    raw = _json_bytes(payload)
    changed = copy.deepcopy(payload)
    changed["ok"] = False
    changed_raw = _json_bytes(changed)

    assert _post_run(client, raw, nonce="run-conflict-1").status_code == 201
    conflict = _post_run(client, changed_raw, nonce="run-conflict-2")

    assert conflict.status_code == 409
    assert conflict.json() == {
        "code": "payload_conflict",
        "correlation_id": SAFE_CORRELATION_ID,
    }
    idempotent_after_conflict = _post_run(
        client,
        raw,
        nonce="run-conflict-2",
    )
    assert idempotent_after_conflict.status_code == 200


def test_storage_failure_returns_temporary_and_rolls_back_nonce(
    api, client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = _json_bytes(_payload_from_manifest(_manifest(api)))
    original_store = api.store_evaluated_ru_run

    def fail_storage(*_args, **_kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(api, "store_evaluated_ru_run", fail_storage)
    failed = _post_run(client, raw, nonce="storage-rollback")
    assert failed.status_code == 500
    assert failed.json() == {
        "code": "temporary",
        "correlation_id": SAFE_CORRELATION_ID,
    }
    assert "database unavailable" not in failed.text

    monkeypatch.setattr(api, "store_evaluated_ru_run", original_store)
    accepted = _post_run(client, raw, nonce="storage-rollback")
    assert accepted.status_code == 201, accepted.text


def test_replayed_nonce_is_committed_with_successful_domain_write(
    api, client: TestClient
) -> None:
    raw = _json_bytes(_payload_from_manifest(_manifest(api)))
    assert _post_run(client, raw, nonce="run-replay").status_code == 201

    replay = _post_run(client, raw, nonce="run-replay")
    assert replay.status_code == 409
    assert replay.json()["code"] == "replayed_nonce"


def test_probe_host_binding_mismatch_is_403_and_rolls_back_nonce(
    api, client: TestClient
) -> None:
    payload = _payload_from_manifest(_manifest(api))
    payload["probe_host"]["id"] = "other-host"
    mismatched_raw = _json_bytes(payload)
    nonce = "host-binding"

    rejected = _post_run(client, mismatched_raw, nonce=nonce)
    assert rejected.status_code == 403
    assert rejected.json()["code"] == "key_scope_forbidden"

    payload["probe_host"]["id"] = "mini"
    accepted = _post_run(client, _json_bytes(payload), nonce=nonce)
    assert accepted.status_code == 201, accepted.text


@pytest.mark.parametrize(
    ("kind", "expected_verdict", "expected_reason"),
    [
        ("partial", "incomplete", "partial_execution"),
        ("superseded", "superseded_manifest", "superseded_manifest"),
        ("old", "pass", "outside_retention_window"),
    ],
)
def test_ineligible_runs_are_stored_honestly(
    api,
    client: TestClient,
    kind: str,
    expected_verdict: str,
    expected_reason: str,
) -> None:
    manifest = _manifest(api)
    now = _utc_now()
    payload = _payload_from_manifest(
        manifest,
        now=(
            now - timedelta(days=181)
            if kind == "old"
            else now
        ),
        execution_status="partial" if kind == "partial" else "completed",
    )
    if kind == "superseded":
        payload["manifest_revision"] = "f" * 64
    raw = _json_bytes(payload)

    response = _post_run(client, raw, nonce=f"ineligible-{kind}")
    assert response.status_code == 201, response.text
    assert response.json()["current_eligible"] is False

    from models import RuProbeRun, RuProbeTargetResult

    session = api.SessionLocal()
    try:
        run = session.query(RuProbeRun).filter_by(run_id=payload["run_id"]).one()
        targets = (
            session.query(RuProbeTargetResult)
            .filter_by(run_db_id=run.id)
            .all()
        )
        assert run.release_verdict == expected_verdict
        assert run.current_eligible is False
        assert run.ineligible_reason == expected_reason
        assert targets
        assert all(target.current_eligible is False for target in targets)
        assert all(
            target.ineligible_reason == expected_reason
            for target in targets
            if target.scope == "release_required"
        )
    finally:
        session.close()


def test_heartbeat_is_idempotent_conflict_safe_and_never_mutates_runs(
    api, client: TestClient
) -> None:
    run_raw = _json_bytes(_payload_from_manifest(_manifest(api)))
    created_run = _post_run(client, run_raw, nonce="heartbeat-run")
    assert created_run.status_code == 201

    heartbeat = _heartbeat_payload(pending_count=2)
    raw = _json_bytes(heartbeat)
    first = _post_heartbeat(client, raw, nonce="heartbeat-1")
    second = _post_heartbeat(client, raw, nonce="heartbeat-2")
    changed = copy.deepcopy(heartbeat)
    changed["blocked_count"] = 1
    conflict = _post_heartbeat(
        client,
        _json_bytes(changed),
        nonce="heartbeat-3",
    )

    assert first.status_code == 201, first.text
    assert second.status_code == 200, second.text
    assert first.json() == {
        "code": "created",
        "correlation_id": SAFE_CORRELATION_ID,
    }
    assert second.json() == first.json()
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "payload_conflict"
    after_conflict = _post_heartbeat(
        client,
        raw,
        nonce="heartbeat-3",
    )
    assert after_conflict.status_code == 200

    from models import RuProbeRun, RuProbeTargetResult, RuProbeUploaderHeartbeat

    session = api.SessionLocal()
    try:
        assert session.query(RuProbeRun).count() == 1
        assert session.query(RuProbeTargetResult).count() == len(
            _payload_from_manifest(_manifest(api))["targets"]
        )
        row = session.query(RuProbeUploaderHeartbeat).one()
        assert row.probe_host_id == "mini"
        assert row.pending_count == 2
        assert row.blocked_count == 0
    finally:
        session.close()


@pytest.mark.parametrize(
    "mutation",
    [
        "extra",
        "bad_schema_type",
        "future",
        "bad_count",
        "bad_disk",
        "bad_disk_type",
        "bad_error",
        "bad_error_type",
        "oldest_without_pending",
    ],
)
def test_heartbeat_schema_is_exact_and_bounded(
    client: TestClient, mutation: str
) -> None:
    payload = _heartbeat_payload()
    if mutation == "extra":
        payload["secret"] = "must-not-pass"
    elif mutation == "bad_schema_type":
        payload["schema_version"] = 1.0
    elif mutation == "future":
        payload["observed_at"] = (
            _utc_now() + timedelta(minutes=6)
        ).isoformat().replace("+00:00", "Z")
    elif mutation == "bad_count":
        payload["pending_count"] = -1
    elif mutation == "bad_disk":
        payload["disk_state"] = "healthy"
    elif mutation == "bad_disk_type":
        payload["disk_state"] = ["ok"]
    elif mutation == "bad_error":
        payload["last_error_code"] = "raw_provider_error"
    elif mutation == "bad_error_type":
        payload["last_error_code"] = ["network_error"]
    else:
        payload["oldest_pending_at"] = (
            _utc_now() - timedelta(hours=1)
        ).isoformat().replace("+00:00", "Z")
    raw = _json_bytes(payload)

    response = _post_heartbeat(client, raw, nonce=f"heartbeat-invalid-{mutation}")
    assert response.status_code == 422
    assert response.json()["code"] == "invalid_payload"


def test_heartbeat_host_binding_mismatch_is_forbidden(
    client: TestClient,
) -> None:
    raw = _json_bytes(_heartbeat_payload(probe_host_id="not-mini"))
    response = _post_heartbeat(client, raw, nonce="heartbeat-host")
    assert response.status_code == 403
    assert response.json()["code"] == "key_scope_forbidden"


def test_unsafe_correlation_id_is_replaced_and_never_echoed(
    api, client: TestClient
) -> None:
    raw = _json_bytes(_payload_from_manifest(_manifest(api)))
    response = _post_run(
        client,
        raw,
        nonce="unsafe-correlation",
        correlation_id="unsafe correlation\nsecret",
    )

    assert response.status_code == 201
    correlation_id = response.json()["correlation_id"]
    assert correlation_id != "unsafe correlation\nsecret"
    assert correlation_id
    assert all(character.isalnum() or character in "._:-" for character in correlation_id)


@pytest.mark.parametrize("different_bytes", [False, True])
def test_concurrent_run_id_race_returns_201_then_200_or_409_without_500(
    api, different_bytes: bool
) -> None:
    for iteration in range(5):
        payload = _payload_from_manifest(_manifest(api))
        first_raw = _json_bytes(payload)
        second_payload = copy.deepcopy(payload)
        if different_bytes:
            second_payload["ok"] = False
        second_raw = _json_bytes(second_payload)
        barrier = threading.Barrier(2)
        results: list[tuple[int, str]] = []
        errors: list[BaseException] = []

        def post(raw: bytes, nonce: str) -> None:
            try:
                with TestClient(api.app) as thread_client:
                    barrier.wait(timeout=10)
                    response = _post_run(thread_client, raw, nonce=nonce)
                    results.append((response.status_code, response.json()["code"]))
            except BaseException as exc:  # pragma: no cover - retained for diagnosis
                errors.append(exc)

        threads = [
            threading.Thread(
                target=post,
                args=(first_raw, f"race-{iteration}-1"),
            ),
            threading.Thread(
                target=post,
                args=(second_raw, f"race-{iteration}-2"),
            ),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=20)

        assert not errors
        assert all(not thread.is_alive() for thread in threads)
        expected = (
            [(200, "created"), (201, "created")]
            if not different_bytes
            else [(201, "created"), (409, "payload_conflict")]
        )
        assert sorted(results) == expected
