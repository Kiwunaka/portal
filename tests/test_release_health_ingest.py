from __future__ import annotations

import gzip
import importlib
import json
import logging
import sys
import time
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

import migrations  # noqa: E402
import models  # noqa: E402
import observability_ingest as ingest  # noqa: E402
from request_correlation import (  # noqa: E402
    CORRELATION_ID_HEADER,
    REQUEST_ID_HEADER,
    RequestCorrelation,
    build_request_correlation,
    normalize_correlation_id,
)


def _event(*, event_id: str | None = None) -> dict[str, object]:
    return {
        "schema_version": 1,
        "event_id": event_id or str(uuid.uuid4()),
        "occurred_at_utc": "2026-08-21T08:10:00Z",
        "component": "app",
        "subsystem": "connection",
        "stage": "verify",
        "name": "client.connection.verify",
        "severity": "info",
        "outcome": "succeeded",
        "privacy_class": "release_health",
        "build": {
            "app_version": "1.2.0",
            "build_number": "45",
            "channel": "beta",
            "candidate_label": "pokrov-1.2.0-beta.45",
            "git_revision": "a" * 40,
            "core_version": "1.2.0",
            "core_abi": 2,
            "platform": "windows",
            "architecture": "x86_64",
        },
        "error": None,
    }


def _android_routing_event(
    *,
    selected_app_count: object = 3,
    attributes: dict[str, object] | None = None,
) -> dict[str, object]:
    event = _event()
    event.update(
        {
            "subsystem": "routing",
            "stage": "complete",
            "name": "app.routing.selection.finished",
            "outcome": "observed",
        }
    )
    build = dict(event["build"])
    build.update({"platform": "android", "architecture": "arm64-v8a"})
    event["build"] = build
    event["attributes"] = (
        {"selected_app_count": selected_app_count}
        if attributes is None
        else attributes
    )
    return event


def _batch(*events: dict[str, object]) -> bytes:
    return json.dumps(
        {"schema_version": 1, "events": list(events)},
        separators=(",", ":"),
    ).encode("utf-8")


@pytest.fixture
def session(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'release-health.db').as_posix()}")
    models.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    value = factory()
    try:
        yield value
    finally:
        value.close()
        engine.dispose()


def test_projection_is_identity_free_and_persists_only_closed_fields(session) -> None:
    event = _event()
    parsed = ingest.parse_release_health_batch(_batch(event))
    result = ingest.ingest_release_health_batch(
        session,
        parsed,
        request_context=RequestCorrelation(
            correlation_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
        ),
    )
    session.commit()

    assert result.accepted == 1
    assert result.duplicates == 0
    assert result.accepted_event_ids == (str(event["event_id"]),)
    stored = session.query(models.ReleaseHealthEvent).one()
    assert stored.event_id == event["event_id"]
    assert stored.event_name == "client.connection.verify"
    assert stored.platform == "windows"
    assert not {
        "tg_id",
        "account_id",
        "install_id",
        "device_id",
        "session_id",
        "trace_id",
        "meta_json",
    } & set(models.ReleaseHealthEvent.__table__.columns.keys())


def test_android_routing_projection_persists_only_bounded_count(session) -> None:
    event = _android_routing_event(selected_app_count=3)
    parsed = ingest.parse_release_health_batch(_batch(event))
    result = ingest.ingest_release_health_batch(
        session,
        parsed,
        request_context=build_request_correlation(None),
    )
    session.commit()

    stored = session.query(models.ReleaseHealthEvent).one()
    assert result.accepted == 1
    assert stored.selected_app_count == 3
    assert stored.platform == "android"
    assert not {
        "package",
        "package_name",
        "package_names",
        "selected_apps",
    } & set(models.ReleaseHealthEvent.__table__.columns.keys())


@pytest.mark.parametrize("selected_app_count", [-1, 129, True, "3"])
def test_android_routing_count_must_be_a_bounded_integer(
    selected_app_count: object,
) -> None:
    with pytest.raises(ingest.ReleaseHealthIngestError) as caught:
        ingest.parse_release_health_batch(
            _batch(_android_routing_event(selected_app_count=selected_app_count))
        )
    assert caught.value.reason == "invalid_selected_app_count"


@pytest.mark.parametrize(
    "event",
    [
        _android_routing_event(attributes={}),
        _android_routing_event(
            attributes={"selected_app_count": 3, "package_name": "org.example.app"}
        ),
        _android_routing_event(
            attributes={"selected_app_count": 3, "package_names": ["org.example.app"]}
        ),
    ],
)
def test_android_routing_projection_rejects_missing_or_identifying_attributes(
    event: dict[str, object],
) -> None:
    with pytest.raises(ingest.ReleaseHealthIngestError) as caught:
        ingest.parse_release_health_batch(_batch(event))
    assert caught.value.reason in {"missing_field", "forbidden_field", "unknown_field"}


def test_android_routing_count_is_forbidden_on_other_platforms() -> None:
    event = _android_routing_event()
    event["build"] = dict(event["build"], platform="windows", architecture="x86_64")
    with pytest.raises(ingest.ReleaseHealthIngestError) as caught:
        ingest.parse_release_health_batch(_batch(event))
    assert caught.value.reason == "forbidden_field"


def test_duplicate_event_ids_do_not_inflate_release_health(session) -> None:
    event_id = str(uuid.uuid4())
    parsed = ingest.parse_release_health_batch(_batch(_event(event_id=event_id), _event(event_id=event_id)))
    first = ingest.ingest_release_health_batch(
        session,
        parsed,
        request_context=build_request_correlation(None),
    )
    session.commit()
    second = ingest.ingest_release_health_batch(
        session,
        parsed[:1],
        request_context=build_request_correlation(None),
    )
    session.commit()

    assert (first.accepted, first.duplicates) == (1, 1)
    assert (second.accepted, second.duplicates) == (0, 1)
    assert session.query(models.ReleaseHealthEvent).count() == 1
    duplicate_counter = session.get(models.ReleaseHealthIngestCounter, "duplicate.events")
    assert duplicate_counter is not None
    assert duplicate_counter.count == 2


def test_event_id_reuse_with_different_projection_fails_closed(session) -> None:
    event_id = str(uuid.uuid4())
    first_event = _event(event_id=event_id)
    conflicting_event = _event(event_id=event_id)
    conflicting_event["outcome"] = "failed"

    with pytest.raises(ingest.ReleaseHealthIngestError) as same_batch:
        ingest.ingest_release_health_batch(
            session,
            ingest.parse_release_health_batch(_batch(first_event, conflicting_event)),
            request_context=build_request_correlation(None),
        )
    assert same_batch.value.reason == "event_id_conflict"

    ingest.ingest_release_health_batch(
        session,
        ingest.parse_release_health_batch(_batch(first_event)),
        request_context=build_request_correlation(None),
    )
    session.commit()
    with pytest.raises(ingest.ReleaseHealthIngestError) as persisted_conflict:
        ingest.ingest_release_health_batch(
            session,
            ingest.parse_release_health_batch(_batch(conflicting_event)),
            request_context=build_request_correlation(None),
        )
    assert persisted_conflict.value.reason == "event_id_conflict"


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda event: event.update({"account_id": "forbidden"}), "forbidden_field"),
        (lambda event: event.update({"destination": "example.test"}), "forbidden_field"),
        (lambda event: event.update({"future_field": "no"}), "unknown_field"),
        (lambda event: event.update({"attributes": {"duration_ms": 1}}), "forbidden_field"),
        (
            lambda event: event.update(
                {"error": {"code": "UNKNOWN-999", "origin": "client"}}
            ),
            "unknown_error_code",
        ),
    ],
)
def test_forbidden_identity_destination_and_unknown_contract_values_fail_closed(
    mutate,
    reason: str,
) -> None:
    event = _event()
    mutate(event)
    with pytest.raises(ingest.ReleaseHealthIngestError) as caught:
        ingest.parse_release_health_batch(_batch(event))
    assert caught.value.reason == reason


def test_unknown_schema_version_maps_to_release_catalog_code() -> None:
    payload = json.loads(_batch(_event()))
    payload["schema_version"] = 2
    with pytest.raises(ingest.ReleaseHealthIngestError) as caught:
        ingest.parse_release_health_batch(json.dumps(payload).encode("utf-8"))
    assert caught.value.catalog_code == "API-009"
    assert caught.value.status_code == 409


def test_duplicate_json_keys_fail_closed() -> None:
    payload = _batch(_event()).decode("utf-8").replace(
        '"schema_version":1',
        '"schema_version":1,"schema_version":1',
        1,
    )
    with pytest.raises(ingest.ReleaseHealthIngestError) as caught:
        ingest.parse_release_health_batch(payload.encode("utf-8"))
    assert caught.value.reason == "duplicate_json_key"


def test_event_and_encoded_byte_limits_are_hard() -> None:
    many = [_event() for _ in range(ingest.MAX_BATCH_EVENTS + 1)]
    with pytest.raises(ingest.ReleaseHealthIngestError) as count_error:
        ingest.parse_release_health_batch(_batch(*many))
    assert count_error.value.reason == "too_many_events"

    with pytest.raises(ingest.ReleaseHealthIngestError) as byte_error:
        ingest.decode_batch_body(
            b"x" * (ingest.MAX_IDENTITY_BODY_BYTES + 1),
            content_encoding="identity",
        )
    assert byte_error.value.reason == "encoded_body_too_large"


def test_maximum_batches_remain_bounded_under_local_load_and_replay(session) -> None:
    started = time.perf_counter()
    total = 0
    context = RequestCorrelation(
        correlation_id=str(uuid.uuid4()),
        request_id=str(uuid.uuid4()),
    )
    batches: list[tuple[ingest.ReleaseHealthProjection, ...]] = []
    for _ in range(20):
        parsed = ingest.parse_release_health_batch(
            _batch(*(_event() for _ in range(ingest.MAX_BATCH_EVENTS)))
        )
        batches.append(parsed)
        result = ingest.ingest_release_health_batch(
            session, parsed, request_context=context
        )
        total += result.accepted
    session.flush()
    first_duration = time.perf_counter() - started

    replay = ingest.ingest_release_health_batch(
        session, batches[-1], request_context=context
    )
    session.flush()

    assert total == 2000
    assert replay.accepted == 0
    assert replay.duplicates == ingest.MAX_BATCH_EVENTS
    assert session.query(models.ReleaseHealthEvent).count() == 2000
    assert first_duration < 10.0


def test_gzip_bomb_and_concatenated_stream_fail_closed() -> None:
    bomb = gzip.compress(b"x" * (ingest.MAX_DECODED_BODY_BYTES + 1), compresslevel=9)
    assert len(bomb) < ingest.MAX_GZIP_BODY_BYTES
    with pytest.raises(ingest.ReleaseHealthIngestError) as bomb_error:
        ingest.decode_batch_body(bomb, content_encoding="gzip")
    assert bomb_error.value.reason == "decoded_body_too_large"

    valid = gzip.compress(_batch(_event()))
    with pytest.raises(ingest.ReleaseHealthIngestError) as trailing_error:
        ingest.decode_batch_body(valid + gzip.compress(b"{}"), content_encoding="gzip")
    assert trailing_error.value.reason == "invalid_gzip"


def test_migration_bootstraps_release_health_tables_without_metadata(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{(tmp_path / 'legacy.db').as_posix()}")
    models.Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE release_health_cohort_buckets"))
        connection.execute(text("DROP TABLE release_health_ingest_counters"))
        connection.execute(text("DROP TABLE release_health_events"))
        connection.execute(text("DROP TABLE release_known_issues"))
    migrations.run_migrations(engine)
    with engine.connect() as connection:
        names = {
            row[0]
            for row in connection.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND "
                    "name IN ('release_health_events', "
                    "'release_health_cohort_buckets', "
                    "'release_health_ingest_counters', 'release_known_issues')"
                )
            )
        }
    engine.dispose()
    assert names == {
        "release_health_events",
        "release_health_cohort_buckets",
        "release_health_ingest_counters",
        "release_known_issues",
    }


def test_migration_adds_android_routing_count_to_existing_release_health_table(
    tmp_path: Path,
) -> None:
    engine = create_engine(f"sqlite:///{(tmp_path / 'legacy-column.db').as_posix()}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE release_health_events ("
                "id INTEGER PRIMARY KEY, "
                "schema_version INTEGER NOT NULL DEFAULT 1, "
                "event_id VARCHAR(36) NOT NULL, "
                "occurred_at DATETIME NOT NULL, "
                "received_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "
                "component VARCHAR(32) NOT NULL, "
                "subsystem VARCHAR(32) NOT NULL, "
                "stage VARCHAR(32) NOT NULL, "
                "event_name VARCHAR(96) NOT NULL, "
                "severity VARCHAR(16) NOT NULL, "
                "outcome VARCHAR(24) NOT NULL, "
                "app_version VARCHAR(64) NOT NULL, "
                "build_number VARCHAR(32) NOT NULL, "
                "channel VARCHAR(16) NOT NULL, "
                "candidate_label VARCHAR(64) NOT NULL, "
                "git_revision VARCHAR(40) NOT NULL, "
                "core_version VARCHAR(64), "
                "core_abi INTEGER, "
                "platform VARCHAR(16) NOT NULL, "
                "architecture VARCHAR(32) NOT NULL, "
                "error_code VARCHAR(32), "
                "error_origin VARCHAR(16))"
            )
        )
    with engine.begin() as connection:
        migrations._ensure_release_health_domain_sqlite(connection)
    with engine.connect() as connection:
        columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(release_health_events)"))
        }
    engine.dispose()

    assert "selected_app_count" in columns


@pytest.mark.parametrize(
    "value",
    [
        "",
        "UPPERCASE",
        "not-a-uuid",
        "11111111-1111-1111-8111-111111111111",
        "11111111-1111-6111-8111-111111111111",
        "11111111-1111-4111-7111-111111111111",
        "11111111-1111-4111-8111-111111111111\r\nX-Evil: yes",
    ],
)
def test_unsafe_client_correlation_is_rejected(value: str) -> None:
    assert normalize_correlation_id(value) is None
    context = build_request_correlation(value)
    assert context.correlation_id != value
    assert uuid.UUID(context.correlation_id).version == 4


class _FakePanel:
    async def add_client(self, **_kwargs):
        return True

    async def close(self):
        return None


def _load_api(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "portal-observability-api.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "portal-observability-test-secret")
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.pokrov.test")
    monkeypatch.setenv("PUBLIC_WEB_DOMAIN", "pokrov.test")
    monkeypatch.setenv("ANTIABUSE_HMAC_SECRET", "observability-antiabuse-test-secret")
    monkeypatch.setenv("ANTIABUSE_HMAC_VERSION", "2")
    monkeypatch.setenv(
        "RELEASE_HEALTH_COHORT_SECRET",
        "release-health-api-test-secret-v1",
    )
    for name in [
        "api",
        "api_observability_routes",
        "api_support_bundle_routes",
        "api_operator_observability_routes",
        "commercial_campaign_policy",
        "commercial_offer_service",
        "commercial_order_service",
        "commercial_attribution_service",
        "observability_ingest",
        "request_correlation",
        "account_experience_service",
        "app_first_service",
        "account_foundation_service",
        "antiabuse_privacy_service",
        "auth_session_service",
        "config",
        "db",
        "migrations",
        "models",
        "web_auth_service",
        "control_panel",
        "nodes_repo",
        "tickets_repo",
        "events_service",
    ]:
        monkeypatch.delitem(sys.modules, name, raising=False)
    api = importlib.import_module("api")
    monkeypatch.setattr(api, "ControlPanel", _FakePanel)
    return api


def _authenticated_client(api) -> tuple[TestClient, dict[str, str]]:
    client = TestClient(api.app)
    started = client.post(
        "/api/client/session/start-trial",
        json={
            "install_id": "release-health-test-install",
            "device_name": "Test device",
            "platform": "windows",
        },
    )
    assert started.status_code == 200
    return client, {"Authorization": f"Bearer {started.json()['session_token']}"}


def _baseline_params() -> dict[str, object]:
    return {
        "app_version": "1.2.0",
        "build_number": "45",
        "channel": "beta",
        "candidate_label": "pokrov-1.2.0-beta.45",
        "git_revision": "a" * 40,
        "core_abi": 2,
        "platform": "windows",
        "architecture": "x86_64",
    }


def test_api_authenticates_correlates_and_deduplicates(monkeypatch, tmp_path: Path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client, auth = _authenticated_client(api)
    event_id = str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())
    headers = {
        **auth,
        CORRELATION_ID_HEADER: correlation_id,
        "Content-Type": "application/json",
    }

    first = client.post(
        "/api/client/observability/release-health/batches",
        headers=headers,
        content=_batch(_event(event_id=event_id)),
    )
    second = client.post(
        "/api/client/observability/release-health/batches",
        headers=headers,
        content=_batch(_event(event_id=event_id)),
    )

    assert first.status_code == 202
    assert first.headers[CORRELATION_ID_HEADER] == correlation_id
    assert uuid.UUID(first.headers[REQUEST_ID_HEADER]).version == 4
    assert first.json()["accepted"] == 1
    assert second.json() == {
        "ok": True,
        "accepted": 0,
        "duplicates": 1,
        "request_id": second.headers[REQUEST_ID_HEADER],
    }
    with api.SessionLocal() as session:
        assert session.query(api.ReleaseHealthEvent).count() == 1
        bucket = session.query(api.release_health_baseline_service.ReleaseHealthCohortBucket).one()
        assert bucket.event_count == 1


def test_authenticated_client_baseline_hides_subminimum_cohort(
    monkeypatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client, auth = _authenticated_client(api)
    accepted = client.post(
        "/api/client/observability/release-health/batches",
        headers={**auth, "Content-Type": "application/json"},
        content=_batch(_event()),
    )
    response = client.get(
        "/api/client/observability/release-health/baseline",
        headers=auth,
        params=_baseline_params(),
    )

    assert accepted.status_code == 202
    assert response.status_code == 200
    assert response.json()["state"] == "insufficient_cohort"
    assert response.json()["baseline"] is None
    assert response.json()["privacy"] == {
        "minimum_contributors": 10,
        "minimum_satisfied": False,
        "contribution_cap_per_window": 64,
    }


def test_client_baseline_requires_auth_and_configured_privacy_secret(
    monkeypatch,
    tmp_path: Path,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client, auth = _authenticated_client(api)
    unauthenticated = client.get(
        "/api/client/observability/release-health/baseline",
        params=_baseline_params(),
    )
    monkeypatch.delenv("RELEASE_HEALTH_COHORT_SECRET", raising=False)
    unconfigured = client.get(
        "/api/client/observability/release-health/baseline",
        headers=auth,
        params=_baseline_params(),
    )

    assert unauthenticated.status_code == 401
    assert unconfigured.status_code == 503
    assert unconfigured.json()["detail"] == {
        "code": "API-007",
        "message": "Release-health baseline unavailable.",
        "reason": "baseline_privacy_unavailable",
    }


def test_api_replaces_unsafe_correlation_and_never_echoes_rejected_payload(
    monkeypatch,
    tmp_path: Path,
    caplog,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client, auth = _authenticated_client(api)
    planted = "authorization=Bearer-super-secret"
    unsafe_correlation = "unsafe\r\nCookie: planted-secret"
    event = _event()
    event["account_id"] = planted

    with caplog.at_level(logging.INFO):
        response = client.post(
            "/api/client/observability/release-health/batches",
            headers={
                **auth,
                CORRELATION_ID_HEADER: unsafe_correlation,
                "Content-Type": "application/json",
            },
            content=_batch(event),
        )

    rendered = response.text + str(dict(response.headers)) + caplog.text
    assert response.status_code == 422
    assert response.json()["detail"] == {
        "code": "API-008",
        "message": "Release-health batch rejected.",
        "reason": "forbidden_field",
    }
    assert response.headers[CORRELATION_ID_HEADER] != unsafe_correlation
    assert planted not in rendered
    assert "planted-secret" not in rendered
    with api.SessionLocal() as session:
        assert session.query(api.ReleaseHealthEvent).count() == 0
        counter = session.get(api.ReleaseHealthIngestCounter, "quarantine.forbidden_field")
        assert counter is not None
        assert counter.count == 1


def test_api_rejects_gzip_bomb_before_json_parse(monkeypatch, tmp_path: Path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client, auth = _authenticated_client(api)
    bomb = gzip.compress(b"x" * (ingest.MAX_DECODED_BODY_BYTES + 1), compresslevel=9)
    response = client.post(
        "/api/client/observability/release-health/batches",
        headers={**auth, "Content-Type": "application/json", "Content-Encoding": "gzip"},
        content=bomb,
    )
    assert response.status_code == 413
    assert response.json()["detail"]["reason"] == "decoded_body_too_large"


def test_api_requires_authentication_and_returns_request_ids(monkeypatch, tmp_path: Path) -> None:
    api = _load_api(monkeypatch, tmp_path)
    client = TestClient(api.app)
    response = client.post(
        "/api/client/observability/release-health/batches",
        headers={"Content-Type": "application/json"},
        content=_batch(_event()),
    )
    assert response.status_code == 401
    assert uuid.UUID(response.headers[CORRELATION_ID_HEADER]).version == 4
    assert uuid.UUID(response.headers[REQUEST_ID_HEADER]).version == 4


def test_unhandled_exception_maps_to_catalog_without_exception_echo(
    monkeypatch,
    tmp_path: Path,
    caplog,
) -> None:
    api = _load_api(monkeypatch, tmp_path)
    planted = "Bearer-unhandled-secret"

    @api.app.get("/__test_unhandled_release_health")
    async def _fail_safely():
        raise RuntimeError(planted)

    client = TestClient(api.app, raise_server_exceptions=False)
    with caplog.at_level(logging.ERROR):
        response = client.get("/__test_unhandled_release_health")

    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "API-007"
    assert response.json()["request_id"] == response.headers[REQUEST_ID_HEADER]
    assert planted not in response.text
    assert planted not in caplog.text
