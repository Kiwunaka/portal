from __future__ import annotations

import copy
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))

import models  # noqa: E402
import ru_probe_service as ru_probe_service_module  # noqa: E402
from ru_probe_contract import RuProbeContractError, endpoint_fingerprint  # noqa: E402
from ru_probe_service import (  # noqa: E402
    DEFAULT_MANIFEST_MAX_CACHE_AGE_SECONDS,
    RU_RUN_STALE_AFTER_SECONDS,
    RU_UPLOADER_HEARTBEAT_STALE_AFTER_SECONDS,
    DeliveryNodeScopeDecision,
    EvaluatedRuRun,
    RuProbeConfigurationError,
    build_ru_manifest,
    classify_delivery_node_scope,
    evaluate_ru_run,
    get_latest_ru_status,
    get_ru_run_history,
    get_ru_uploader_status,
    store_evaluated_ru_run,
)


ENV_NAMES = (
    "RU_PROBE_CANONICAL_TARGETS_JSON",
    "RU_PROBE_RESERVE_TARGETS_JSON",
    "RU_PROBE_MANIFEST_MAX_CACHE_AGE_SECONDS",
)


@pytest.fixture(autouse=True)
def clean_ru_probe_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ENV_NAMES:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def session(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'ru-service.db').as_posix()}")
    models.Node.__table__.create(engine)
    models.UserNode.__table__.create(engine)
    models.RuProbeRun.__table__.create(engine)
    models.RuProbeTargetResult.__table__.create(engine)
    models.RuProbeUploaderHeartbeat.__table__.create(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    value = factory()
    try:
        yield value
    finally:
        value.close()
        engine.dispose()


def _node(
    code: str,
    *,
    enabled: bool = False,
    draining: bool = False,
    provisioned: int = 0,
) -> models.Node:
    return models.Node(
        code=code,
        name=code.upper(),
        host=f"{code}.nodes.example.net",
        vless_port=443,
        reality_sni=f"front-{code}.example.net",
        reality_pbk=f"SECRET-PBK-{code}",
        reality_sid=f"SECRET-SID-{code}",
        panel_user=f"secret-user-{code}",
        panel_pass=f"secret-pass-{code}",
        inbound_id=1,
        enabled=enabled,
        is_draining=draining,
        provisioned_clients_count=provisioned,
    )


def _targets_by_id(manifest: dict[str, object]) -> dict[str, dict[str, object]]:
    return {target["target_id"]: target for target in manifest["targets"]}


def _stored_run(
    session,
    *,
    run_id: str,
    finished_at: datetime,
    received_at: datetime,
    current_eligible: bool,
    release_verdict: str,
    environment_verdict: str = "available",
    node_code: str = "nl",
    node_status: str = "pass",
    scope: str = "release_required",
) -> models.RuProbeRun:
    run = models.RuProbeRun(
        run_id=run_id,
        schema_version=2,
        origin="ru",
        probe_host_id="mini",
        probe_host_label="Мини",
        probe_public_ip=None,
        runner_version="2.0.0",
        started_at=finished_at - timedelta(minutes=2),
        finished_at=finished_at,
        received_at=received_at,
        manifest_revision="a" * 64,
        execution_status="completed" if current_eligible else "partial",
        evidence_code=None,
        environment_verdict=environment_verdict,
        release_verdict=release_verdict,
        current_eligible=current_eligible,
        ineligible_reason=None if current_eligible else "partial_execution",
        google_reachable=environment_verdict == "available",
        xhttp_alive=False,
        hysteria_alive=False,
        server_reason=None,
        server_summary="fixture",
        artifact_sha256=(run_id.replace("-", "") + ("0" * 64))[:64],
        ingest_key_id="ru-test",
        retention_hold=False,
    )
    session.add(run)
    session.flush()
    session.add(
        models.RuProbeTargetResult(
            run_db_id=run.id,
            target_id=f"node:{node_code}",
            target_kind="delivery_node",
            scope=scope,
            node_code=node_code,
            endpoint_fingerprint="b" * 64,
            endpoint_host=f"{node_code}.example.test",
            endpoint_port=443,
            endpoint_sni=f"front-{node_code}.example.test",
            requested_address_families_json=["ipv4", "ipv6"],
            transport_metadata_json={
                "address_family_status": {"ipv4": "pass", "ipv6": "not_run"},
                "transport": {
                    "handshake_status": "pass",
                    "classification": "ok",
                },
            },
            transport_profile="legacy_reality_fallback",
            probe_mode="delivery_tls",
            http_path=None,
            min_body_bytes=None,
            local_probe_profile_id=None,
            observed_at=finished_at,
            overall_status=node_status,
            current_eligible=current_eligible,
            ineligible_reason=None if current_eligible else "partial_execution",
            dns_status="pass",
            dns_latency_ms=10,
            tcp_status="pass",
            tcp_latency_ms=20,
            tls_status="pass" if node_status == "pass" else "fail",
            tls_latency_ms=30 if node_status == "pass" else None,
            http_large_body_status="not_applicable",
            http_large_body_latency_ms=None,
            transport_handshake_status="not_applicable",
            transport_handshake_latency_ms=None,
            ipv4_status="pass",
            ipv6_status="not_run",
            reported_transport_handshake_status="not_applicable",
            reported_transport_classification="ok",
            server_reason_code=(
                "google_unavailable"
                if node_status == "unavailable_probe_host"
                else None
            ),
            server_detail=None,
        )
    )
    session.flush()
    return run


def _payload_from_manifest(
    manifest: dict[str, object],
    *,
    now: datetime,
    execution_status: str = "completed",
) -> dict[str, object]:
    targets: list[dict[str, object]] = []
    for expected in manifest["targets"]:
        stages = {}
        for stage_name in ("dns", "tcp", "tls", "http_large_body", "transport_handshake"):
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
    finished = now - timedelta(minutes=1)
    return {
        "schema_version": 2,
        "run_id": "6fb8ce89-b5c4-4d1d-a4dc-041f53ba7f11",
        "origin": "ru",
        "probe_host": {"id": "mini", "label": "Мини", "public_ip": None},
        "runner_version": "2.0.0",
        "manifest_revision": manifest["manifest_revision"],
        "started_at": (finished - timedelta(minutes=2)).isoformat().replace(
            "+00:00", "Z"
        ),
        "finished_at": finished.isoformat().replace("+00:00", "Z"),
        "execution_status": execution_status,
        "evidence_code": None,
        "targets": targets,
        "ok": False,
        "google_reachable": False,
        "xhttp_alive": False,
        "hysteria_alive": False,
        "classifications": ["client_lie"],
    }


def _store_manifest_run(
    session,
    *,
    manifest: dict[str, object],
    now: datetime,
    run_id: str,
    finished_at: datetime | None = None,
    received_at: datetime | None = None,
    execution_status: str = "completed",
    google_available: bool = True,
) -> models.RuProbeRun:
    effective_finished_at = finished_at or (now - timedelta(minutes=1))
    payload = _payload_from_manifest(
        manifest,
        now=effective_finished_at + timedelta(minutes=1),
        execution_status=execution_status,
    )
    payload["run_id"] = run_id
    if not google_available:
        google = next(
            target
            for target in payload["targets"]
            if target["target_id"] == "environment:google"
        )
        google["stages"]["http_large_body"].update(
            status="fail",
            latency_ms=None,
            code="network_unavailable",
        )
    evaluated = evaluate_ru_run(session, payload, now=now)
    stored = store_evaluated_ru_run(
        session,
        evaluated,
        artifact_sha256=(run_id.replace("-", "") + ("0" * 64))[:64],
        ingest_key_id="ru-test",
        received_at=received_at or now,
    )
    session.commit()
    return session.query(models.RuProbeRun).filter_by(id=stored.run_db_id).one()


def _store_current_manifest_run(
    session,
    *,
    now: datetime,
    run_id: str,
) -> tuple[models.RuProbeRun, dict[str, object]]:
    manifest = build_ru_manifest(session, now=now)
    row = _store_manifest_run(
        session,
        manifest=manifest,
        now=now,
        run_id=run_id,
    )
    return row, manifest


def _copy_target_result(
    row: models.RuProbeTargetResult,
    **overrides: object,
) -> models.RuProbeTargetResult:
    values = {
        column.name: copy.deepcopy(getattr(row, column.name))
        for column in models.RuProbeTargetResult.__table__.columns
        if column.name != "id"
    }
    values.update(overrides)
    return models.RuProbeTargetResult(**values)


def test_manifest_membership_is_bulk_and_includes_only_delivery_scope(session) -> None:
    enabled = _node("enabled", enabled=True)
    draining = _node("draining", draining=True)
    mapped = _node("mapped")
    provisioned = _node("provisioned", provisioned=2)
    omitted = _node("omitted")
    session.add_all([enabled, draining, mapped, provisioned, omitted])
    session.flush()
    session.add(
        models.UserNode(
            tg_id=1001,
            node_id=mapped.id,
            client_uuid="11111111-1111-4111-8111-111111111111",
            panel_email="mapped@example.net",
        )
    )
    session.commit()

    selects: list[str] = []

    def record_select(_conn, _cursor, statement, _parameters, _context, _executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            selects.append(statement)

    event.listen(session.bind, "before_cursor_execute", record_select)
    try:
        manifest = build_ru_manifest(
            session, now=datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
        )
    finally:
        event.remove(session.bind, "before_cursor_execute", record_select)

    targets = _targets_by_id(manifest)
    assert {key for key in targets if key.startswith("node:")} == {
        "node:enabled",
        "node:draining",
        "node:mapped",
        "node:provisioned",
    }
    assert "node:omitted" not in targets
    assert len(selects) == 2
    decision = classify_delivery_node_scope(omitted, mapped_client_count=0)
    assert decision == DeliveryNodeScopeDecision(included=False, reason="not_in_scope")
    for code in ("enabled", "draining", "mapped", "provisioned"):
        target = targets[f"node:{code}"]
        assert target["target_kind"] == "delivery_node"
        assert target["scope"] == "release_required"
        assert target["node_code"] == code
        assert target["required_stages"] == ["dns", "tcp", "tls"]


def test_manifest_has_exact_google_and_default_canonical_targets_without_secrets(session) -> None:
    node = _node("nl", enabled=True)
    node.transport_profiles_json = json.dumps(
        {"operator_lab": {"name": "operator_lab", "token": "SECRET-TOKEN"}}
    )
    session.add(node)
    session.commit()
    now = datetime(2026, 7, 16, 9, 0, 0, 987654, tzinfo=timezone.utc)
    manifest = build_ru_manifest(session, now=now)
    targets = _targets_by_id(manifest)

    assert manifest["manifest_schema_version"] == 1
    assert manifest["generated_at"] == "2026-07-16T09:00:00Z"
    assert manifest["max_cache_age_seconds"] == DEFAULT_MANIFEST_MAX_CACHE_AGE_SECONDS
    google = targets["environment:google"]
    assert google["endpoint"] == {
        "host": "google.com",
        "port": 443,
        "sni": "google.com",
        "address_families": ["ipv4", "ipv6"],
        "transport_profile": "https",
        "probe_mode": "google_https",
        "http_path": "/",
        "min_body_bytes": 65536,
        "local_probe_profile_id": None,
    }
    assert google["required_stages"] == ["dns", "tcp", "tls", "http_large_body"]
    assert targets["node:nl"]["endpoint"]["transport_profile"] == (
        "legacy_reality_fallback"
    )
    assert {
        targets[key]["endpoint"]["host"]
        for key in targets
        if key.startswith("canonical:")
    } == {"pokrov.space", "app.pokrov.space", "api.pokrov.space"}
    serialized = json.dumps(manifest, ensure_ascii=False).lower()
    for forbidden in (
        "secret-pbk",
        "secret-sid",
        "secret-user",
        "secret-pass",
        "secret-token",
        "reality_pbk",
        "reality_sid",
        "panel_pass",
    ):
        assert forbidden not in serialized


def test_manifest_config_is_deterministic_public_strict_and_timestamp_independent(
    session, monkeypatch: pytest.MonkeyPatch
) -> None:
    canonical = [
        {
            "target_id": "canonical:cdn",
            "host": "cdn.pokrov.space",
            "port": 443,
            "sni": "cdn.pokrov.space",
            "address_families": ["ipv6", "ipv4"],
            "transport_profile": "https",
            "http_path": "/probe.bin",
            "min_body_bytes": 65536,
        }
    ]
    reserves = [
        {
            "target_id": "reserve:xhttp",
            "probe_mode": "xhttp_handshake",
            "host": "xhttp.pokrov.space",
            "port": 443,
            "sni": "xhttp.pokrov.space",
            "address_families": ["ipv4", "ipv6"],
            "transport_profile": "reserve_xhttp_cdn",
            "local_probe_profile_id": "xhttp-canary-v1",
            "http_path": "/probe",
        },
        {
            "target_id": "reserve:hysteria",
            "probe_mode": "hysteria_handshake",
            "host": "hy.pokrov.space",
            "port": 443,
            "sni": "hy.pokrov.space",
            "address_families": ["ipv4"],
            "transport_profile": "hysteria2",
            "local_probe_profile_id": "hysteria-canary-v1",
            "http_path": None,
        },
    ]
    monkeypatch.setenv("RU_PROBE_CANONICAL_TARGETS_JSON", json.dumps(canonical))
    monkeypatch.setenv("RU_PROBE_RESERVE_TARGETS_JSON", json.dumps(reserves))
    monkeypatch.setenv("RU_PROBE_MANIFEST_MAX_CACHE_AGE_SECONDS", "7200")

    first = build_ru_manifest(
        session, now=datetime(2026, 7, 16, 8, 0, tzinfo=timezone.utc)
    )
    second = build_ru_manifest(
        session, now=datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    )
    assert first["manifest_revision"] == second["manifest_revision"]
    assert first["generated_at"] != second["generated_at"]
    assert first["max_cache_age_seconds"] == 7200
    targets = _targets_by_id(first)
    assert set(targets) == {
        "environment:google",
        "canonical:cdn",
        "reserve:xhttp",
        "reserve:hysteria",
    }
    assert targets["canonical:cdn"]["scope"] == "release_required"
    assert targets["canonical:cdn"]["endpoint"]["min_body_bytes"] == 65536
    for target_id in ("reserve:xhttp", "reserve:hysteria"):
        assert "transport_handshake" in targets[target_id]["required_stages"]
        assert targets[target_id]["endpoint"]["local_probe_profile_id"].endswith(
            "-canary-v1"
        )


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("sni", "203.0.113.10", "invalid_sni"),
        ("http_path", "/probe\nnext", "invalid_path"),
    ],
)
def test_manifest_config_cannot_publish_endpoint_rejected_by_payload_contract(
    session,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: str,
    code: str,
) -> None:
    target = {
        "target_id": "canonical:self-check",
        "host": "self-check.example.net",
        "port": 443,
        "sni": "self-check.example.net",
        "address_families": ["ipv4", "ipv6"],
        "transport_profile": "https",
        "http_path": "/probe",
        "min_body_bytes": 65536,
    }
    target[field] = value
    monkeypatch.setenv("RU_PROBE_CANONICAL_TARGETS_JSON", json.dumps([target]))
    with pytest.raises(RuProbeConfigurationError) as exc:
        build_ru_manifest(
            session, now=datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
        )
    assert exc.value.code == code


@pytest.mark.parametrize(
    ("env_name", "value", "code"),
    [
        ("RU_PROBE_CANONICAL_TARGETS_JSON", "not-json", "invalid_json"),
        ("RU_PROBE_CANONICAL_TARGETS_JSON", "{}", "invalid_config_shape"),
        (
            "RU_PROBE_CANONICAL_TARGETS_JSON",
            '[{"target_id":"canonical:x","host":"x.example","panel_pass":"secret"}]',
            "secret_field",
        ),
        (
            "RU_PROBE_RESERVE_TARGETS_JSON",
            '[{"target_id":"reserve:x","probe_mode":"delivery_tls","host":"x.example",'
            '"transport_profile":"reserve_xhttp_cdn",'
            '"local_probe_profile_id":"xhttp-canary-v1"}]',
            "invalid_probe_mode",
        ),
        ("RU_PROBE_MANIFEST_MAX_CACHE_AGE_SECONDS", "10", "invalid_cache_age"),
    ],
)
def test_manifest_public_config_fails_closed(
    session,
    monkeypatch: pytest.MonkeyPatch,
    env_name: str,
    value: str,
    code: str,
) -> None:
    monkeypatch.setenv(env_name, value)
    with pytest.raises(RuProbeConfigurationError) as exc:
        build_ru_manifest(
            session, now=datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
        )
    assert exc.value.code == code


def test_manifest_rejects_node_code_outside_public_code_allowlist(session) -> None:
    session.add(_node("bad:node", enabled=True))
    session.commit()
    with pytest.raises(RuProbeConfigurationError) as exc:
        build_ru_manifest(
            session, now=datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
        )
    assert exc.value.code == "invalid_code"


def test_manifest_rejects_explicit_zero_delivery_port(session) -> None:
    node = _node("zero-port", enabled=True)
    node.vless_port = 0
    session.add(node)
    session.commit()
    with pytest.raises(RuProbeConfigurationError) as exc:
        build_ru_manifest(
            session, now=datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
        )
    assert exc.value.code == "invalid_endpoint"


def test_delivery_target_uses_first_normalized_active_transport_profile_without_material(
    session,
) -> None:
    node = _node("grpc", enabled=True)
    node.inbound_id = 0
    node.transport_profiles_json = json.dumps(
        [
            {
                "name": "grpc_443_primary",
                "enabled": True,
                "kind": "grpc",
                "grpc_service_name": "synthetic-grpc-service",
                "token": "SYNTHETIC-SECRET-NOT-FOR-MANIFEST",
            }
        ]
    )
    session.add(node)
    session.commit()

    manifest = build_ru_manifest(
        session, now=datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    )
    target = _targets_by_id(manifest)["node:grpc"]
    assert target["endpoint"]["transport_profile"] == "grpc_443_primary"
    serialized = json.dumps(target, ensure_ascii=False)
    assert "synthetic-grpc-service" not in serialized
    assert "SYNTHETIC-SECRET-NOT-FOR-MANIFEST" not in serialized


def test_delivery_target_without_active_transport_profile_fails_closed(session) -> None:
    node = _node("inactive", enabled=True)
    node.inbound_id = 0
    node.transport_profiles_json = json.dumps(
        [{"name": "grpc_443_primary", "enabled": False, "kind": "grpc"}]
    )
    session.add(node)
    session.commit()
    with pytest.raises(RuProbeConfigurationError) as exc:
        build_ru_manifest(
            session, now=datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
        )
    assert exc.value.code == "no_active_transport_profile"


def test_manifest_rejects_more_targets_than_payload_contract_can_return(session) -> None:
    nodes = [_node(f"n{index:03d}", enabled=True) for index in range(253)]
    session.add_all(nodes[:252])
    session.commit()
    at_limit = build_ru_manifest(
        session, now=datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
    )
    assert len(at_limit["targets"]) == 256

    session.add(nodes[252])
    session.commit()
    with pytest.raises(RuProbeConfigurationError) as exc:
        build_ru_manifest(
            session, now=datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
        )
    assert exc.value.code == "too_many_targets"


def test_evaluate_exact_current_run_ignores_client_aggregates(session) -> None:
    session.add(_node("nl", enabled=True))
    session.commit()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    manifest = build_ru_manifest(session, now=now)
    payload = _payload_from_manifest(manifest, now=now)
    result = evaluate_ru_run(session, payload, now=now)

    assert isinstance(result, EvaluatedRuRun)
    assert result.environment_verdict == "available"
    assert result.release_verdict == "pass"
    assert result.current_eligible is True
    assert result.ineligible_reason is None
    assert result.google_reachable is True
    assert result.xhttp_alive is False
    assert result.hysteria_alive is False
    assert all(item.overall_status == "pass" for item in result.target_results)
    assert "client_lie" not in result.server_summary


@pytest.mark.parametrize("mutation", ["revision", "endpoint"])
def test_old_revision_or_changed_endpoint_is_superseded(session, mutation: str) -> None:
    session.add(_node("nl", enabled=True))
    session.commit()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    manifest = build_ru_manifest(session, now=now)
    payload = _payload_from_manifest(manifest, now=now)
    if mutation == "revision":
        payload["manifest_revision"] = "f" * 64
    else:
        node = next(item for item in payload["targets"] if item["target_id"] == "node:nl")
        node["endpoint"]["port"] = 8443
        node["endpoint_fingerprint"] = endpoint_fingerprint(node["endpoint"])

    result = evaluate_ru_run(session, payload, now=now)
    assert result.release_verdict == "superseded_manifest"
    assert result.current_eligible is False
    assert result.ineligible_reason == "superseded_manifest"
    assert all(item.current_eligible is False for item in result.target_results)


def test_reordered_address_families_is_not_exact_current_endpoint(session) -> None:
    session.add(_node("nl", enabled=True))
    session.commit()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    manifest = build_ru_manifest(session, now=now)
    payload = _payload_from_manifest(manifest, now=now)
    node = next(item for item in payload["targets"] if item["target_id"] == "node:nl")
    node["endpoint"]["address_families"].reverse()
    node["endpoint_fingerprint"] = endpoint_fingerprint(node["endpoint"])

    result = evaluate_ru_run(session, payload, now=now)
    assert result.release_verdict == "superseded_manifest"
    assert result.current_eligible is False


def test_missing_target_is_incomplete_and_extra_diagnostic_never_changes_release(session) -> None:
    session.add(_node("nl", enabled=True))
    session.commit()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    manifest = build_ru_manifest(session, now=now)
    complete = _payload_from_manifest(manifest, now=now)
    missing = copy.deepcopy(complete)
    missing["targets"] = [
        item for item in missing["targets"] if item["target_id"] != "node:nl"
    ]
    result = evaluate_ru_run(session, missing, now=now)
    assert result.release_verdict == "incomplete"
    assert result.current_eligible is False
    assert result.ineligible_reason == "missing_required_target"

    diagnostic = copy.deepcopy(complete["targets"][0])
    diagnostic.update(
        target_id="diagnostic:extra",
        target_kind="diagnostic",
        scope="diagnostic",
        node_code=None,
    )
    diagnostic["endpoint_fingerprint"] = endpoint_fingerprint(diagnostic["endpoint"])
    for stage in diagnostic["stages"].values():
        stage["status"] = "fail"
        stage["code"] = "diagnostic_failure"
    diagnostic["transport"]["handshake_status"] = "fail"
    complete["targets"].append(diagnostic)
    result = evaluate_ru_run(session, complete, now=now)
    assert result.release_verdict == "pass"
    extra = next(item for item in result.target_results if item.target_id == "diagnostic:extra")
    assert extra.overall_status == "failed"
    assert extra.current_eligible is False
    assert extra.ineligible_reason == "diagnostic_only"


def test_required_target_cannot_be_relabelled_as_diagnostic(session) -> None:
    session.add(_node("nl", enabled=True))
    session.commit()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    manifest = build_ru_manifest(session, now=now)
    payload = _payload_from_manifest(manifest, now=now)
    node = next(item for item in payload["targets"] if item["target_id"] == "node:nl")
    node["scope"] = "diagnostic"

    result = evaluate_ru_run(session, payload, now=now)
    assert result.release_verdict == "superseded_manifest"
    assert result.current_eligible is False


def test_diagnostic_protocol_target_cannot_set_server_alive_aggregate(session) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    manifest = build_ru_manifest(session, now=now)
    payload = _payload_from_manifest(manifest, now=now)
    diagnostic = copy.deepcopy(payload["targets"][0])
    diagnostic.update(
        target_id="diagnostic:xhttp",
        target_kind="diagnostic",
        scope="diagnostic",
        node_code=None,
    )
    diagnostic["endpoint"].update(
        host="diag.example.net",
        sni="diag.example.net",
        probe_mode="xhttp_handshake",
        transport_profile="diagnostic_xhttp",
        http_path="/probe",
        min_body_bytes=None,
        local_probe_profile_id="diagnostic-canary-v1",
    )
    diagnostic["endpoint_fingerprint"] = endpoint_fingerprint(diagnostic["endpoint"])
    diagnostic["stages"]["transport_handshake"].update(
        status="pass", latency_ms=10, code=None
    )
    diagnostic["transport"].update(
        profile_code="diagnostic_xhttp", handshake_status="pass"
    )
    payload["targets"].append(diagnostic)

    result = evaluate_ru_run(session, payload, now=now)
    assert result.release_verdict == "pass"
    assert result.xhttp_alive is False


def test_unknown_release_target_fails_closed(session) -> None:
    session.add(_node("nl", enabled=True))
    session.commit()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    manifest = build_ru_manifest(session, now=now)
    payload = _payload_from_manifest(manifest, now=now)
    unknown = copy.deepcopy(
        next(item for item in payload["targets"] if item["target_id"] == "node:nl")
    )
    unknown["target_id"] = "node:unknown"
    unknown["target_kind"] = "delivery_node"
    unknown["scope"] = "release_required"
    unknown["node_code"] = "unknown"
    payload["targets"].append(unknown)
    with pytest.raises(RuProbeContractError) as exc:
        evaluate_ru_run(session, payload, now=now)
    assert exc.value.code == "unknown_release_target"


@pytest.mark.parametrize(
    "detail",
    [
        "auth_token=SYNTHETIC_REDACTED",
        "Cookie: sessionid=SYNTHETIC_REDACTED",
        "certificate names do not match expected reality target",
    ],
)
def test_evaluator_never_copies_untrusted_runner_detail_to_result(
    session, detail: str
) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    manifest = build_ru_manifest(session, now=now)
    payload = _payload_from_manifest(manifest, now=now)
    payload["targets"][0]["detail"] = detail

    with pytest.raises(RuProbeContractError) as exc:
        evaluate_ru_run(session, payload, now=now)
    assert exc.value.code == "sensitive_detail"


def test_google_failure_marks_environment_and_every_node_unavailable(session) -> None:
    session.add_all([_node("nl", enabled=True), _node("de", enabled=True)])
    session.commit()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    manifest = build_ru_manifest(session, now=now)
    payload = _payload_from_manifest(manifest, now=now)
    google = next(item for item in payload["targets"] if item["target_id"] == "environment:google")
    google["stages"]["tls"].update(status="fail", code="tls_failed")
    result = evaluate_ru_run(session, payload, now=now)
    assert result.environment_verdict == "unavailable"
    assert result.google_reachable is False
    assert result.release_verdict == "fail"
    nodes = [item for item in result.target_results if item.target_kind == "delivery_node"]
    assert {item.overall_status for item in nodes} == {"unavailable_probe_host"}
    assert {item.reason_code for item in nodes} == {"google_unavailable"}


@pytest.mark.parametrize(
    ("stage_status", "expected_status", "reason_code"),
    [
        ("fail", "failed", "required_stage_failed"),
        ("not_run", "incomplete", "required_stage_not_run"),
        ("not_applicable", "failed", "required_stage_not_applicable"),
    ],
)
def test_required_stage_status_drives_server_target_verdict(
    session, stage_status: str, expected_status: str, reason_code: str
) -> None:
    session.add(_node("nl", enabled=True))
    session.commit()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    manifest = build_ru_manifest(session, now=now)
    payload = _payload_from_manifest(manifest, now=now)
    node = next(item for item in payload["targets"] if item["target_id"] == "node:nl")
    node["stages"]["tls"].update(status=stage_status, latency_ms=None, code="tls_result")
    result = evaluate_ru_run(session, payload, now=now)
    evaluated = next(item for item in result.target_results if item.target_id == "node:nl")
    assert evaluated.overall_status == expected_status
    assert evaluated.reason_code == reason_code
    assert result.release_verdict in {"fail", "incomplete"}


@pytest.mark.parametrize(
    ("execution_status", "evidence_code", "release_verdict", "reason"),
    [
        ("partial", None, "incomplete", "partial_execution"),
        ("runner_error", None, "incomplete", "runner_error"),
        (
            "blocked_by_access",
            "network_access_blocked",
            "blocked_by_access",
            "network_access_blocked",
        ),
    ],
)
def test_noncompleted_execution_is_never_current_eligible(
    session,
    execution_status: str,
    evidence_code: str | None,
    release_verdict: str,
    reason: str,
) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    manifest = build_ru_manifest(session, now=now)
    payload = _payload_from_manifest(manifest, now=now, execution_status=execution_status)
    payload["evidence_code"] = evidence_code
    if execution_status == "blocked_by_access":
        for target in payload["targets"]:
            for stage in target["stages"].values():
                stage.update(status="not_run", latency_ms=None, code=None)
            target["address_family_status"] = {"ipv4": "not_run", "ipv6": "not_run"}
            target["transport"]["handshake_status"] = "not_run"
    result = evaluate_ru_run(session, payload, now=now)
    assert result.release_verdict == release_verdict
    assert result.current_eligible is False
    assert result.ineligible_reason == reason


def test_protocol_alive_requires_protocol_handshake_not_tls_or_client_hint(
    session, monkeypatch: pytest.MonkeyPatch
) -> None:
    reserves = [
        {
            "target_id": "reserve:xhttp",
            "probe_mode": "xhttp_handshake",
            "host": "xhttp.pokrov.space",
            "port": 443,
            "sni": "xhttp.pokrov.space",
            "address_families": ["ipv4"],
            "transport_profile": "reserve_xhttp_cdn",
            "local_probe_profile_id": "xhttp-canary-v1",
            "http_path": "/probe",
        },
        {
            "target_id": "reserve:hysteria",
            "probe_mode": "hysteria_handshake",
            "host": "hy.pokrov.space",
            "port": 443,
            "sni": "hy.pokrov.space",
            "address_families": ["ipv4"],
            "transport_profile": "hysteria2",
            "local_probe_profile_id": "hysteria-canary-v1",
            "http_path": None,
        },
    ]
    monkeypatch.setenv("RU_PROBE_RESERVE_TARGETS_JSON", json.dumps(reserves))
    now = datetime.now(timezone.utc).replace(microsecond=0)
    manifest = build_ru_manifest(session, now=now)
    payload = _payload_from_manifest(manifest, now=now)
    xhttp = next(item for item in payload["targets"] if item["target_id"] == "reserve:xhttp")
    hysteria = next(
        item for item in payload["targets"] if item["target_id"] == "reserve:hysteria"
    )
    xhttp["stages"]["transport_handshake"].update(
        status="not_run", latency_ms=None, code="profile_missing"
    )
    xhttp["stages"]["tls"].update(status="pass", latency_ms=1, code=None)
    xhttp["transport"]["handshake_status"] = "not_run"
    payload["xhttp_alive"] = True
    hysteria["stages"]["transport_handshake"].update(status="pass", code=None)
    hysteria["transport"]["handshake_status"] = "pass"
    payload["hysteria_alive"] = False

    result = evaluate_ru_run(session, payload, now=now)
    assert result.xhttp_alive is False
    assert result.hysteria_alive is True
    assert result.release_verdict == "incomplete"


def test_latest_eligible_uses_finished_at_not_received_at(session) -> None:
    now = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)
    session.add(_node("nl", enabled=True))
    session.commit()
    manifest = build_ru_manifest(session, now=now)
    newer = _store_manifest_run(
        session,
        manifest=manifest,
        now=now,
        run_id="00000000-0000-4000-8000-000000000101",
        finished_at=now,
        received_at=now,
    )
    late_old = _store_manifest_run(
        session,
        manifest=manifest,
        now=now,
        run_id="00000000-0000-4000-8000-000000000102",
        finished_at=now - timedelta(hours=2),
        received_at=now + timedelta(minutes=1),
    )

    latest = get_latest_ru_status(session, now=now + timedelta(minutes=2))

    assert latest["latest_eligible_run"]["run_id"] == newer.run_id
    assert latest["eligible_run"]["run_id"] == newer.run_id
    assert latest["latest_received_attempt"]["run_id"] == late_old.run_id
    assert latest["status"] == "ok"
    assert latest["threshold_seconds"] == RU_RUN_STALE_AFTER_SECONDS


def test_latest_pass_is_not_current_after_enabled_node_changes_manifest(session) -> None:
    now = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)
    session.add(_node("nl", enabled=True))
    session.commit()
    stored, _manifest = _store_current_manifest_run(
        session,
        now=now,
        run_id="00000000-0000-4000-8000-000000000109",
    )

    session.add(_node("de", enabled=True))
    session.commit()

    latest = get_latest_ru_status(session, now=now + timedelta(minutes=1))

    assert latest["status"] != "ok"
    assert latest["reason_code"] == "superseded_manifest"
    assert latest["latest_received_attempt"]["run_id"] == stored.run_id
    assert latest["latest_eligible_run"] is None
    nodes = {row["node_code"]: row for row in latest["nodes"]}
    assert nodes["de"]["status"] == "missing"
    assert nodes["de"]["reason_code"] == "target_missing"


@pytest.mark.parametrize(
    ("transition", "expected_node_status", "expected_node_reason"),
    [
        ("enable", "missing", "target_missing"),
        ("disable", "not_in_scope", "not_in_scope"),
        ("drain", "missing", "target_missing"),
    ],
)
def test_latest_revalidates_node_scope_transitions_against_live_manifest(
    session,
    transition: str,
    expected_node_status: str,
    expected_node_reason: str,
) -> None:
    now = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)
    node = _node("nl", enabled=transition == "disable")
    session.add(node)
    session.commit()
    stored, _manifest = _store_current_manifest_run(
        session,
        now=now,
        run_id=f"00000000-0000-4000-8000-00000000011{len(transition)}",
    )

    if transition == "enable":
        node.enabled = True
    elif transition == "disable":
        node.enabled = False
    else:
        node.is_draining = True
    session.commit()

    latest = get_latest_ru_status(session, now=now + timedelta(minutes=1))

    assert latest["status"] != "ok"
    assert latest["reason_code"] == "superseded_manifest"
    assert latest["latest_received_attempt"]["run_id"] == stored.run_id
    assert latest["latest_eligible_run"] is None
    node_row = next(row for row in latest["nodes"] if row["node_code"] == "nl")
    assert node_row["status"] == expected_node_status
    assert node_row["reason_code"] == expected_node_reason


@pytest.mark.parametrize("target_family", ["canonical", "reserve"])
def test_latest_revalidates_canonical_and_reserve_endpoint_revisions(
    session,
    monkeypatch: pytest.MonkeyPatch,
    target_family: str,
) -> None:
    now = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)
    if target_family == "canonical":
        env_name = "RU_PROBE_CANONICAL_TARGETS_JSON"
        before = [
            {
                "target_id": "canonical:read-check",
                "host": "old-read.example.net",
                "http_path": "/probe",
                "min_body_bytes": 65536,
            }
        ]
        after = copy.deepcopy(before)
        after[0]["host"] = "new-read.example.net"
    else:
        env_name = "RU_PROBE_RESERVE_TARGETS_JSON"
        before = [
            {
                "target_id": "reserve:read-check",
                "probe_mode": "xhttp_handshake",
                "host": "old-reserve.example.net",
                "transport_profile": "reserve_xhttp_cdn",
                "local_probe_profile_id": "xhttp-canary-v1",
                "http_path": "/probe",
            }
        ]
        after = copy.deepcopy(before)
        after[0]["http_path"] = "/probe-v2"
    monkeypatch.setenv(env_name, json.dumps(before))
    stored, old_manifest = _store_current_manifest_run(
        session,
        now=now,
        run_id=(
            "00000000-0000-4000-8000-000000000121"
            if target_family == "canonical"
            else "00000000-0000-4000-8000-000000000122"
        ),
    )
    monkeypatch.setenv(env_name, json.dumps(after))
    current_manifest = build_ru_manifest(session, now=now + timedelta(minutes=1))
    assert current_manifest["manifest_revision"] != old_manifest["manifest_revision"]

    latest = get_latest_ru_status(session, now=now + timedelta(minutes=1))

    assert latest["status"] != "ok"
    assert latest["reason_code"] == "superseded_manifest"
    assert latest["latest_received_attempt"]["run_id"] == stored.run_id
    assert latest["latest_eligible_run"] is None


@pytest.mark.parametrize(
    ("corruption", "expected_reason"),
    [
        ("missing", "current_target_missing"),
        ("fingerprint", "superseded_manifest"),
        ("extra", "superseded_manifest"),
        ("endpoint", "superseded_manifest"),
        ("target_flag", "superseded_manifest"),
    ],
)
def test_latest_rejects_corrupt_missing_and_extra_release_target_rows(
    session,
    corruption: str,
    expected_reason: str,
) -> None:
    now = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)
    session.add(_node("nl", enabled=True))
    session.commit()
    stored, _manifest = _store_current_manifest_run(
        session,
        now=now,
        run_id=(
            "00000000-0000-4000-8000-000000000123"
            if corruption == "missing"
            else "00000000-0000-4000-8000-000000000124"
            if corruption == "fingerprint"
            else "00000000-0000-4000-8000-000000000125"
        ),
    )
    target = (
        session.query(models.RuProbeTargetResult)
        .filter_by(run_db_id=stored.id, target_id="node:nl")
        .one()
    )
    if corruption == "missing":
        session.delete(target)
    elif corruption == "fingerprint":
        target.endpoint_fingerprint = "f" * 64
    elif corruption == "extra":
        session.add(
            _copy_target_result(
                target,
                target_id="node:unknown-release-target",
                node_code="unknown-release-target",
            )
        )
    elif corruption == "endpoint":
        target.endpoint_host = "corrupt-endpoint.example.net"
    else:
        target.current_eligible = False
    session.commit()

    latest = get_latest_ru_status(session, now=now + timedelta(minutes=1))

    assert latest["status"] != "ok"
    assert latest["reason_code"] == expected_reason
    assert latest["latest_received_attempt"]["run_id"] == stored.run_id
    assert latest["latest_eligible_run"] is None
    assert {row["status"] for row in latest["nodes"]} != {"unavailable"}
    if corruption == "missing":
        node_row = next(row for row in latest["nodes"] if row["node_code"] == "nl")
        assert node_row["status"] == "missing"
        assert node_row["reason_code"] == "target_missing"


def test_latest_stale_boundary_is_strictly_after_seven_hours(session) -> None:
    now = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)
    session.add(_node("nl", enabled=True))
    session.commit()
    manifest = build_ru_manifest(session, now=now)
    stored = _store_manifest_run(
        session,
        manifest=manifest,
        now=now,
        run_id="00000000-0000-4000-8000-000000000126",
        finished_at=now - timedelta(seconds=RU_RUN_STALE_AFTER_SECONDS),
        received_at=now,
    )

    at_boundary = get_latest_ru_status(session, now=now)
    after_boundary = get_latest_ru_status(session, now=now + timedelta(seconds=1))

    assert at_boundary["status"] == "ok"
    assert at_boundary["age_seconds"] == RU_RUN_STALE_AFTER_SECONDS
    assert at_boundary["latest_eligible_run"]["run_id"] == stored.run_id
    assert after_boundary["status"] == "stale"
    assert after_boundary["reason_code"] == "eligible_run_stale"


def test_latest_builds_manifest_once_and_has_constant_query_count(
    session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)
    session.add_all([_node(f"n{index:02d}", enabled=True) for index in range(32)])
    session.commit()
    stored, _manifest = _store_current_manifest_run(
        session,
        now=now,
        run_id="00000000-0000-4000-8000-000000000127",
    )
    original_build = ru_probe_service_module.build_ru_manifest
    manifest_calls = 0

    def tracked_build(current_session, *, now: datetime):
        nonlocal manifest_calls
        manifest_calls += 1
        return original_build(current_session, now=now)

    monkeypatch.setattr(
        ru_probe_service_module,
        "build_ru_manifest",
        tracked_build,
    )
    selects: list[str] = []

    def record_select(_conn, _cursor, statement, _parameters, _context, _executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            selects.append(statement)

    event.listen(session.bind, "before_cursor_execute", record_select)
    try:
        latest = get_latest_ru_status(session, now=now + timedelta(minutes=1))
    finally:
        event.remove(session.bind, "before_cursor_execute", record_select)

    assert latest["latest_eligible_run"]["run_id"] == stored.run_id
    assert len(latest["nodes"]) == 32
    assert manifest_calls == 1
    assert len(selects) <= 7


def test_latest_keeps_incomplete_attempt_separate_and_stales_last_eligible(
    session,
) -> None:
    now = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)
    session.add(_node("nl", enabled=True))
    session.commit()
    manifest = build_ru_manifest(session, now=now)
    eligible = _store_manifest_run(
        session,
        manifest=manifest,
        now=now,
        run_id="00000000-0000-4000-8000-000000000103",
        finished_at=now - timedelta(seconds=RU_RUN_STALE_AFTER_SECONDS + 1),
        received_at=now - timedelta(hours=7),
    )
    attempt = _store_manifest_run(
        session,
        manifest=manifest,
        now=now,
        run_id="00000000-0000-4000-8000-000000000104",
        finished_at=now - timedelta(minutes=5),
        received_at=now - timedelta(minutes=4),
        execution_status="partial",
    )

    latest = get_latest_ru_status(session, now=now)

    assert latest["latest_received_attempt"]["run_id"] == attempt.run_id
    assert latest["latest_eligible_run"]["run_id"] == eligible.run_id
    assert latest["status"] == "stale"
    assert latest["reason_code"] == "eligible_run_stale"
    assert latest["nodes"][0]["status"] == "stale"
    assert latest["nodes"][0]["sampled_at"].startswith("2026-07-16T04:59:59")


def test_latest_missing_and_google_failure_are_honest(session) -> None:
    now = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)
    session.add_all([_node("nl", enabled=True), _node("de", enabled=True)])
    session.commit()

    missing = get_latest_ru_status(session, now=now)
    assert missing["status"] == "missing"
    assert missing["latest_received_attempt"] is None
    assert {row["status"] for row in missing["nodes"]} == {"missing"}

    manifest = build_ru_manifest(session, now=now)
    _store_manifest_run(
        session,
        manifest=manifest,
        now=now,
        run_id="00000000-0000-4000-8000-000000000105",
        finished_at=now - timedelta(minutes=1),
        received_at=now,
        google_available=False,
    )

    unavailable = get_latest_ru_status(session, now=now)
    assert unavailable["environment_verdict"] == "unavailable"
    assert unavailable["environment"]["status"] == "unavailable"
    assert {row["node_code"] for row in unavailable["nodes"]} == {"nl", "de"}
    assert {row["status"] for row in unavailable["nodes"]} == {"unavailable"}
    assert {row["reason_code"] for row in unavailable["nodes"]} == {
        "google_unavailable"
    }


def test_ru_history_cursor_is_opaque_deterministic_and_filters_unknown_node(
    session,
) -> None:
    now = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)
    session.add(_node("nl", enabled=True))
    session.flush()
    first = _stored_run(
        session,
        run_id="00000000-0000-4000-8000-000000000106",
        finished_at=now,
        received_at=now,
        current_eligible=True,
        release_verdict="pass",
    )
    second = _stored_run(
        session,
        run_id="00000000-0000-4000-8000-000000000107",
        finished_at=now,
        received_at=now + timedelta(seconds=1),
        current_eligible=True,
        release_verdict="fail",
        node_code="ghost",
        node_status="failed",
        scope="diagnostic",
    )
    third = _stored_run(
        session,
        run_id="00000000-0000-4000-8000-000000000108",
        finished_at=now - timedelta(hours=1),
        received_at=now + timedelta(seconds=2),
        current_eligible=True,
        release_verdict="pass",
    )
    session.commit()

    page_one = get_ru_run_history(session, limit=2)
    assert [row["run_id"] for row in page_one["items"]] == [
        second.run_id,
        first.run_id,
    ]
    assert page_one["next_cursor"]
    assert "2026-07-16" not in page_one["next_cursor"]
    assert all("targets" not in row for row in page_one["items"])
    assert "endpoint_host" not in json.dumps(page_one, ensure_ascii=False)
    assert "artifact_sha256" not in json.dumps(page_one, ensure_ascii=False)

    page_two = get_ru_run_history(
        session,
        limit=2,
        cursor=page_one["next_cursor"],
    )
    assert [row["run_id"] for row in page_two["items"]] == [third.run_id]
    assert page_two["next_cursor"] is None

    diagnostic = get_ru_run_history(
        session,
        node_code="ghost",
        from_at=now - timedelta(minutes=1),
        to_at=now + timedelta(minutes=1),
        verdict="fail",
        limit=10,
    )
    assert [row["run_id"] for row in diagnostic["items"]] == [second.run_id]
    assert diagnostic["items"][0]["targets"][0]["node_code"] == "ghost"


def test_unfiltered_ru_history_does_not_load_target_matrix_at_max_page_size(
    session,
) -> None:
    now = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)
    for index in range(200):
        run = _stored_run(
            session,
            run_id=f"00000000-0000-4000-8000-{1000 + index:012d}",
            finished_at=now - timedelta(minutes=index),
            received_at=now - timedelta(minutes=index),
            current_eligible=True,
            release_verdict="pass",
        )
        seed_target = (
            session.query(models.RuProbeTargetResult)
            .filter_by(run_db_id=run.id, target_id="node:nl")
            .one()
        )
        base_values = {
            column.name: copy.deepcopy(getattr(seed_target, column.name))
            for column in models.RuProbeTargetResult.__table__.columns
            if column.name != "id"
        }
        session.execute(
            models.RuProbeTargetResult.__table__.insert(),
            [
                {
                    **base_values,
                    "target_id": f"diagnostic:{target_index:03d}",
                    "target_kind": "diagnostic",
                    "scope": "diagnostic",
                    "node_code": None,
                    "current_eligible": False,
                    "ineligible_reason": "diagnostic_only",
                }
                for target_index in range(1, 256)
            ],
        )
    session.commit()
    selects: list[str] = []

    def record_select(_conn, _cursor, statement, _parameters, _context, _executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            selects.append(statement)

    event.listen(session.bind, "before_cursor_execute", record_select)
    try:
        history = get_ru_run_history(session, limit=200)
    finally:
        event.remove(session.bind, "before_cursor_execute", record_select)

    serialized = json.dumps(history, ensure_ascii=False)
    assert len(history["items"]) == 200
    assert all("targets" not in row for row in history["items"])
    assert len(serialized.encode("utf-8")) < 350_000
    assert not any(
        "ru_probe_target_results" in statement.lower()
        for statement in selects
    )


def test_node_filtered_ru_history_includes_only_requested_target_detail(
    session,
) -> None:
    now = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)
    session.add_all([_node("de", enabled=True), _node("nl", enabled=True)])
    session.commit()
    stored, _manifest = _store_current_manifest_run(
        session,
        now=now,
        run_id="00000000-0000-4000-8000-000000000128",
    )

    history = get_ru_run_history(session, node_code="nl", limit=200)

    assert [row["run_id"] for row in history["items"]] == [stored.run_id]
    assert [
        target["node_code"]
        for target in history["items"][0]["targets"]
    ] == ["nl"]


def test_uploader_status_uses_latest_observed_heartbeat_and_server_freshness(
    session,
) -> None:
    now = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)
    missing = get_ru_uploader_status(session, now=now)
    assert missing["status"] == "missing"
    assert missing["heartbeat"] is None

    newest = models.RuProbeUploaderHeartbeat(
        probe_host_id="mini",
        observed_at=now - timedelta(minutes=10),
        received_at=now - timedelta(minutes=9),
        service_version="2.0.0",
        pending_count=3,
        blocked_count=1,
        quarantine_count=2,
        oldest_pending_at=now - timedelta(hours=3),
        archive_write_ok=False,
        disk_free_bytes=1_000_000,
        disk_state="low",
        last_error_code="archive_write_failed",
        ingest_key_id="ru-test",
    )
    late_old = models.RuProbeUploaderHeartbeat(
        probe_host_id="mini",
        observed_at=now - timedelta(hours=2),
        received_at=now,
        service_version="1.9.0",
        pending_count=99,
        blocked_count=0,
        quarantine_count=0,
        oldest_pending_at=now - timedelta(hours=4),
        archive_write_ok=True,
        disk_free_bytes=9_000_000,
        disk_state="ok",
        last_error_code=None,
        ingest_key_id="ru-test",
    )
    session.add_all([newest, late_old])
    session.commit()

    fresh = get_ru_uploader_status(session, now=now)
    assert fresh["status"] == "ok"
    assert fresh["threshold_seconds"] == RU_UPLOADER_HEARTBEAT_STALE_AFTER_SECONDS
    assert fresh["heartbeat"]["service_version"] == "2.0.0"
    assert fresh["heartbeat"]["pending_count"] == 3
    assert fresh["heartbeat"]["archive_write_ok"] is False

    stale = get_ru_uploader_status(
        session,
        now=now + timedelta(seconds=RU_UPLOADER_HEARTBEAT_STALE_AFTER_SECONDS + 1),
    )
    assert stale["status"] == "stale"
    assert stale["reason_code"] == "uploader_heartbeat_stale"
    assert stale["heartbeat"]["last_error_code"] == "archive_write_failed"
