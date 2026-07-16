from __future__ import annotations

import ast
import copy
import inspect
import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))

from ru_probe_contract import (  # noqa: E402
    ALLOWED_ADDRESS_FAMILIES,
    ALLOWED_PROBE_MODES,
    ALLOWED_STAGES,
    MANIFEST_SCHEMA_VERSION,
    RUN_SCHEMA_VERSION,
    RuProbeContractError,
    canonical_json_bytes,
    endpoint_fingerprint,
    manifest_revision,
    validate_run_payload,
)


VECTOR = json.loads(
    (REPO_ROOT / "tests" / "fixtures" / "ru_probe_manifest_vector.json").read_text(
        encoding="utf-8"
    )
)
SCHEMA_PATH = REPO_ROOT / "scripts" / "ru_probe_payload.schema.json"
SAFE_OPERATOR_DETAIL = "TLS-проверка отклонена удалённой стороной"


def _endpoint(*, mode: str = "delivery_tls") -> dict[str, object]:
    return {
        "host": "nl.example.net",
        "port": 443,
        "sni": "front.example.net",
        "address_families": ["ipv4", "ipv6"],
        "transport_profile": "legacy_reality_fallback",
        "probe_mode": mode,
        "http_path": None,
        "min_body_bytes": None,
        "local_probe_profile_id": None,
    }


def _target(*, target_id: str = "node:nl") -> dict[str, object]:
    endpoint = _endpoint()
    return {
        "target_id": target_id,
        "target_kind": "delivery_node",
        "scope": "release_required",
        "node_code": "nl",
        "endpoint": endpoint,
        "endpoint_fingerprint": endpoint_fingerprint(endpoint),
        "stages": {
            "dns": {"status": "pass", "latency_ms": 12, "code": None},
            "tcp": {"status": "pass", "latency_ms": 34, "code": None},
            "tls": {"status": "pass", "latency_ms": 51, "code": None},
            "http_large_body": {
                "status": "not_applicable",
                "latency_ms": None,
                "code": None,
            },
            "transport_handshake": {
                "status": "not_applicable",
                "latency_ms": None,
                "code": None,
            },
        },
        "address_family_status": {"ipv4": "pass", "ipv6": "not_run"},
        "transport": {
            "profile_code": "legacy_reality_fallback",
            "handshake_status": "not_applicable",
            "classification": "ok",
            "detail_code": None,
        },
        "detail_code": None,
        "detail": None,
    }


def valid_payload(*, now: datetime | None = None) -> dict[str, object]:
    finished = (now or datetime.now(timezone.utc)).replace(microsecond=0) - timedelta(
        minutes=1
    )
    return {
        "schema_version": 2,
        "run_id": "9f83025a-d31e-4ac3-a0b8-6065b063e89d",
        "origin": "ru",
        "probe_host": {
            "id": "mini",
            "label": "Мини — российская проба",
            "public_ip": "203.0.113.10",
        },
        "runner_version": "2.0.0",
        "manifest_revision": "a" * 64,
        "started_at": (finished - timedelta(minutes=2)).isoformat().replace(
            "+00:00", "Z"
        ),
        "finished_at": finished.isoformat().replace("+00:00", "Z"),
        "execution_status": "completed",
        "evidence_code": None,
        "targets": [_target()],
    }


def _assert_error(payload: object, code: str) -> None:
    with pytest.raises(RuProbeContractError) as exc:
        validate_run_payload(payload)
    assert exc.value.code == code


def test_public_contract_constants_and_signatures_are_stable() -> None:
    assert MANIFEST_SCHEMA_VERSION == 1
    assert RUN_SCHEMA_VERSION == 2
    assert ALLOWED_ADDRESS_FAMILIES == ("ipv4", "ipv6")
    assert ALLOWED_STAGES == (
        "dns",
        "tcp",
        "tls",
        "http_large_body",
        "transport_handshake",
    )
    assert ALLOWED_PROBE_MODES == (
        "google_https",
        "canonical_https_large_body",
        "delivery_tls",
        "xhttp_handshake",
        "hysteria_handshake",
    )
    assert str(inspect.signature(canonical_json_bytes)) == "(value: 'object') -> 'bytes'"
    assert str(inspect.signature(endpoint_fingerprint)) == (
        "(endpoint: 'dict[str, object]') -> 'str'"
    )
    assert str(inspect.signature(manifest_revision)) == (
        "(targets: 'list[dict[str, object]]') -> 'str'"
    )
    assert str(inspect.signature(validate_run_payload)) == (
        "(payload: 'object') -> 'dict[str, object]'"
    )


def test_manifest_revision_uses_literal_utf8_golden_oracle_and_normalizes_sets() -> None:
    targets = [VECTOR["targets"][1], VECTOR["targets"][0]]
    assert manifest_revision(targets) == VECTOR["manifest_revision"]
    assert endpoint_fingerprint(VECTOR["targets"][0]["endpoint"]) == (
        VECTOR["endpoint_fingerprints"]["environment:google"]
    )

    normalized = copy.deepcopy(targets)
    for target in normalized:
        target["required_stages"].reverse()
        target["endpoint"]["address_families"].reverse()
    assert manifest_revision(normalized) == VECTOR["manifest_revision"]


def test_canonical_json_is_exact_utf8_and_rejects_non_json_values() -> None:
    assert canonical_json_bytes({"я": "да", "a": 1}) == (
        b'{"a":1,"\xd1\x8f":"\xd0\xb4\xd0\xb0"}'
    )
    for value in (math.nan, math.inf, -math.inf, {"bad": {1, 2}}, {1: "bad"}):
        with pytest.raises(RuProbeContractError) as exc:
            canonical_json_bytes(value)
        assert exc.value.code == "non_canonical_value"


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (lambda p: p.update(unexpected=True), "unknown_field"),
        (lambda p: p.update(schema_version=1), "unsupported_schema_version"),
        (lambda p: p.update(run_id="not-a-uuid"), "invalid_run_id"),
        (lambda p: p.update(origin="brain"), "invalid_origin"),
        (lambda p: p["probe_host"].update(id="bad id"), "invalid_code"),
        (lambda p: p["probe_host"].update(public_ip="127.0.0.999"), "invalid_ip"),
        (lambda p: p.update(runner_version="2/secret"), "invalid_code"),
        (lambda p: p.update(manifest_revision="A" * 64), "invalid_hash"),
        (lambda p: p.update(started_at="2026-07-15T10:00:00+00:00"), "invalid_timestamp"),
        (lambda p: p.update(finished_at="2026-07-15T10:00:00"), "invalid_timestamp"),
        (lambda p: p["targets"][0].update(extra=True), "unknown_field"),
        (lambda p: p["targets"][0]["endpoint"].update(port=0), "invalid_port"),
        (lambda p: p["targets"][0]["endpoint"].update(host="https://nl.example.net"), "invalid_host"),
        (lambda p: p["targets"][0]["endpoint"].update(sni="bad sni"), "invalid_sni"),
        (lambda p: p["targets"][0]["endpoint"].update(http_path="no-slash"), "invalid_path"),
        (lambda p: p["targets"][0]["stages"].pop("dns"), "missing_field"),
        (lambda p: p["targets"][0]["stages"]["tcp"].update(extra=True), "unknown_field"),
        (lambda p: p["targets"][0]["stages"]["tcp"].update(latency_ms=-1), "invalid_latency"),
        (
            lambda p: p["targets"][0]["transport"].update(classification=None),
            "invalid_code",
        ),
        (lambda p: p["targets"][0].update(detail="x" * 501), "invalid_detail"),
    ],
)
def test_validate_run_payload_fails_closed_on_structural_and_semantic_mutations(
    mutation, code: str
) -> None:
    payload = valid_payload()
    mutation(payload)
    _assert_error(payload, code)


def test_validate_run_payload_enforces_cardinality_uniqueness_and_exact_hash() -> None:
    payload = valid_payload()
    payload["targets"] = [_target(target_id=f"diagnostic:{index}") for index in range(257)]
    _assert_error(payload, "too_many_targets")

    payload = valid_payload()
    payload["targets"].append(copy.deepcopy(payload["targets"][0]))
    _assert_error(payload, "duplicate_target_id")

    payload = valid_payload()
    payload["targets"][0]["endpoint"]["port"] = 8443
    _assert_error(payload, "endpoint_fingerprint_mismatch")


def test_validate_run_payload_enforces_timestamp_order_duration_and_future_skew() -> None:
    payload = valid_payload()
    payload["started_at"], payload["finished_at"] = (
        payload["finished_at"],
        payload["started_at"],
    )
    _assert_error(payload, "invalid_time_range")

    payload = valid_payload()
    finished = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=1)
    payload["started_at"] = (finished - timedelta(minutes=61)).isoformat().replace(
        "+00:00", "Z"
    )
    payload["finished_at"] = finished.isoformat().replace("+00:00", "Z")
    _assert_error(payload, "run_too_long")

    payload = valid_payload()
    future = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(minutes=6)
    payload["started_at"] = (future - timedelta(minutes=1)).isoformat().replace(
        "+00:00", "Z"
    )
    payload["finished_at"] = future.isoformat().replace("+00:00", "Z")
    _assert_error(payload, "future_timestamp")


def test_blocked_by_access_requires_allowlisted_evidence_and_contains_no_pass() -> None:
    payload = valid_payload()
    payload["execution_status"] = "blocked_by_access"
    payload["evidence_code"] = "network_access_blocked"
    _assert_error(payload, "blocked_target_pass")

    for target in payload["targets"]:
        for stage in target["stages"].values():
            stage["status"] = "not_run"
            stage["latency_ms"] = None
        target["address_family_status"] = {"ipv4": "not_run", "ipv6": "not_run"}
        target["transport"]["handshake_status"] = "not_run"
    assert validate_run_payload(payload)["evidence_code"] == "network_access_blocked"

    payload["evidence_code"] = "free_text_is_not_evidence"
    _assert_error(payload, "invalid_evidence_code")

    payload = valid_payload()
    payload["evidence_code"] = "network_access_blocked"
    _assert_error(payload, "unexpected_evidence_code")


def test_validation_returns_detached_normalized_payload() -> None:
    payload = valid_payload()
    validated = validate_run_payload(payload)
    assert validated == payload
    assert validated is not payload
    assert validated["targets"] is not payload["targets"]


@pytest.mark.parametrize(
    ("detail", "code"),
    [
        ("Bearer SYNTHETIC_REDACTED", "sensitive_detail"),
        ("api_key=SYNTHETIC_REDACTED", "sensitive_detail"),
        ("panel_pass=SYNTHETIC_REDACTED", "sensitive_detail"),
        (
            "https://example.invalid/subscription/SYNTHETIC_REDACTED",
            "sensitive_detail",
        ),
        (
            "subscription_url=https://example.invalid/SYNTHETIC_REDACTED",
            "sensitive_detail",
        ),
        ("auth_token=SYNTHETIC_REDACTED", "sensitive_detail"),
        ("accessToken=SYNTHETIC_REDACTED", "sensitive_detail"),
        ("credential=SYNTHETIC_REDACTED", "sensitive_detail"),
        ("Cookie: sessionid=SYNTHETIC_REDACTED", "sensitive_detail"),
        ("jwt=SYNTHETIC_REDACTED", "sensitive_detail"),
        ("AUTH TOKEN = SYNTHETIC_REDACTED", "sensitive_detail"),
        ("hTTps : //example.invalid/SYNTHETIC_REDACTED", "sensitive_detail"),
        (
            "eyJhbGciOiJIUzI1NiJ9."
            "eyJzdWIiOiJTWU5USEVUSUNfUkVEQUNURUQifQ."
            "SYNTHETIC_REDACTED",
            "sensitive_detail",
        ),
        ('{"credential":"SYNTHETIC_REDACTED"}', "sensitive_detail"),
        (
            "certificate names do not match expected reality target",
            "sensitive_detail",
        ),
        ("cookie\u000bsessionid=SYNTHETIC_REDACTED", "invalid_detail"),
    ],
)
def test_detail_is_fail_closed_to_server_owned_safe_text(
    detail: str, code: str
) -> None:
    payload = valid_payload()
    payload["targets"][0]["detail"] = detail
    _assert_error(payload, code)


def test_detail_accepts_only_exact_server_owned_operator_reason() -> None:
    payload = valid_payload()
    payload["targets"][0]["detail"] = SAFE_OPERATOR_DETAIL
    assert (
        validate_run_payload(payload)["targets"][0]["detail"]
        == SAFE_OPERATOR_DETAIL
    )

    for mutation in (
        SAFE_OPERATOR_DETAIL.lower(),
        f" {SAFE_OPERATOR_DETAIL}",
        f"{SAFE_OPERATOR_DETAIL} ",
    ):
        payload["targets"][0]["detail"] = mutation
        _assert_error(payload, "sensitive_detail")


def test_contract_module_is_stdlib_only() -> None:
    source = (PORTAL_DIR / "ru_probe_contract.py").read_text(encoding="utf-8")
    imports = {
        node.names[0].name.split(".")[0]
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Import)
    }
    imports.update(
        node.module.split(".")[0]
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert not ({"sqlalchemy", "jsonschema", "pydantic"} & imports)


def test_json_schema_mirrors_exact_nested_contract() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {
        "schema_version",
        "run_id",
        "origin",
        "probe_host",
        "runner_version",
        "manifest_revision",
        "started_at",
        "finished_at",
        "execution_status",
        "evidence_code",
        "targets",
    }
    assert schema["properties"]["schema_version"] == {"const": 2}
    assert schema["properties"]["origin"] == {"const": "ru"}
    targets = schema["properties"]["targets"]
    assert targets["minItems"] == 1
    assert targets["maxItems"] == 256
    target = schema["$defs"]["target"]
    endpoint = schema["$defs"]["endpoint"]
    stage = schema["$defs"]["stage"]
    assert target["additionalProperties"] is False
    assert endpoint["additionalProperties"] is False
    assert stage["additionalProperties"] is False
    assert set(target["properties"]["stages"]["required"]) == set(ALLOWED_STAGES)
    assert target["properties"]["stages"]["additionalProperties"] is False
    assert endpoint["properties"]["probe_mode"]["enum"] == list(ALLOWED_PROBE_MODES)
    assert endpoint["properties"]["address_families"]["items"]["enum"] == list(
        ALLOWED_ADDRESS_FAMILIES
    )
    assert target["properties"]["detail"]["anyOf"][1] == {
        "enum": [SAFE_OPERATOR_DETAIL]
    }
    assert target["properties"]["transport"]["properties"]["classification"] == {
        "$ref": "#/$defs/code64"
    }
    assert schema["properties"]["started_at"]["pattern"].endswith("Z$")
    assert {branch.get("format") for branch in schema["$defs"]["host"]["anyOf"]} == {
        "hostname",
        "ipv4",
        "ipv6",
    }
    blocked_then = schema["allOf"][0]["then"]
    assert blocked_then["properties"]["targets"]["items"] == {
        "$ref": "#/$defs/blocked_target"
    }
    assert schema["$defs"]["blocked_target"]["allOf"][0] == {
        "$ref": "#/$defs/target"
    }
