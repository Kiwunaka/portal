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
from ru_probe_contract import RuProbeContractError, endpoint_fingerprint  # noqa: E402
from ru_probe_service import (  # noqa: E402
    DEFAULT_MANIFEST_MAX_CACHE_AGE_SECONDS,
    DeliveryNodeScopeDecision,
    EvaluatedRuRun,
    RuProbeConfigurationError,
    build_ru_manifest,
    classify_delivery_node_scope,
    evaluate_ru_run,
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
