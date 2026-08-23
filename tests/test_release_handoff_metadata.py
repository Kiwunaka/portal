from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate_release_handoff_metadata.py"
SCHEMA_PATH = REPO_ROOT / "scripts" / "release_handoff_metadata.schema.json"
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "release-handoff" / "valid-v2.json"


def _load_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "validate_release_handoff_metadata", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


validator = _load_module()


def valid_payload() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def assert_invalid(
    mutate: Callable[[dict[str, Any]], None],
    expected_code: str,
) -> None:
    payload = valid_payload()
    mutate(payload)
    with pytest.raises(validator.ValidationIssue) as exc:
        validator.validate_metadata(payload)
    assert exc.value.code == expected_code


def test_v2_fixture_returns_safe_normalized_summary() -> None:
    summary = validator.validate_metadata(valid_payload())

    assert summary.classification == "valid_v2"
    assert summary.schema_version == 2
    assert summary.release_version == "1.2.0-rc.1"
    assert summary.candidate_label == "pokrov-1.2.0-rc.1"
    assert summary.artifact_count == 2
    assert summary.blocking_gate_count == 1
    assert summary.source_revisions == {
        "platform": "a" * 40,
        "client": "b" * 40,
        "core": "c" * 40,
        "release_index": "d" * 40,
    }


def test_canonical_contract_digest_normalizes_line_endings(tmp_path: Path) -> None:
    lf_path = tmp_path / "lf.json"
    crlf_path = tmp_path / "crlf.json"
    lf_path.write_bytes(b'{\n  "schema": 1\n}\n')
    crlf_path.write_bytes(b'{\r\n  "schema": 1\r\n}\r\n')

    assert validator.canonical_text_sha256(lf_path) == validator.canonical_text_sha256(
        crlf_path
    )


def test_artifact_set_digest_is_order_independent() -> None:
    payload = valid_payload()
    descriptors = [
        {
            "architecture": artifact["architecture"],
            "file_name": artifact["file_name"],
            "kind": artifact["kind"],
            "platform": artifact["platform"],
            "sha256": artifact["sha256"],
            "size_bytes": artifact["size_bytes"],
            "core_abi": artifact["core_abi"],
            "core_artifact_sha256": artifact["core_artifact_sha256"],
        }
        for artifact in payload["artifacts"]
    ]

    forward = validator.compute_artifact_set_sha256(descriptors)
    reverse = validator.compute_artifact_set_sha256(list(reversed(descriptors)))

    assert forward == payload["promotion"]["source_artifact_set_sha256"]
    assert reverse == forward


def test_legacy_v1_requires_explicit_migration_flag() -> None:
    payload = {
        "schema_version": 1,
        "latest_repo_backed_release": {"version": "1.1.6"},
    }

    with pytest.raises(validator.ValidationIssue) as exc:
        validator.validate_metadata(payload)
    assert exc.value.code == "legacy_v1_not_allowed"

    summary = validator.validate_metadata(payload, allow_legacy_v1=True)
    assert summary.classification == "legacy_v1"
    assert summary.schema_version == 1


@pytest.mark.parametrize("size", [0, -1, 1.0, True])
def test_artifact_size_must_be_positive_integer(size: object) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["artifacts"][0]["size_bytes"] = size

    assert_invalid(mutate, "invalid_size_bytes")


def test_missing_source_revision_fails_closed() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        del payload["sources"]["client"]["revision"]

    assert_invalid(mutate, "missing_field")


def test_malformed_sha256_fails_closed() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["artifacts"][0]["sha256"] = "not-a-digest"

    assert_invalid(mutate, "invalid_sha256")


@pytest.mark.parametrize("contract_id", ["observability-event", "error-catalog"])
def test_observability_contract_is_required(contract_id: str) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["compatibility"]["contracts"] = [
            contract
            for contract in payload["compatibility"]["contracts"]
            if contract["id"] != contract_id
        ]

    assert_invalid(mutate, "required_contract_missing")


@pytest.mark.parametrize("contract_id", ["observability-event", "error-catalog"])
def test_observability_contract_digest_is_canonical(contract_id: str) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        contract = next(
            item
            for item in payload["compatibility"]["contracts"]
            if item["id"] == contract_id
        )
        contract["sha256"] = "0" * 64

    assert_invalid(mutate, "canonical_contract_digest_mismatch")


@pytest.mark.parametrize("contract_id", ["observability-event", "error-catalog"])
def test_observability_contract_version_is_canonical(contract_id: str) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        contract = next(
            item
            for item in payload["compatibility"]["contracts"]
            if item["id"] == contract_id
        )
        contract["version"] = "9.9.9"

    assert_invalid(mutate, "canonical_contract_version_mismatch")


def test_duplicate_artifact_identity_fails_closed() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        duplicate = copy.deepcopy(payload["artifacts"][0])
        duplicate["sha256"] = "0" * 64
        payload["artifacts"].append(duplicate)

    assert_invalid(mutate, "duplicate_artifact_identity")


def test_missing_core_abi_fails_closed() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        del payload["compatibility"]["core_abi"]["desktop"]

    assert_invalid(mutate, "missing_field")


def test_android_core_abi_must_not_invent_an_integer_contract() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["artifacts"][0]["core_abi"] = 2

    assert_invalid(mutate, "artifact_core_abi_mismatch")


def test_desktop_artifact_must_match_versioned_desktop_abi() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["artifacts"][1]["core_abi"] = 3

    assert_invalid(mutate, "artifact_core_abi_mismatch")


def test_core_artifact_sha256_is_required_and_valid() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["artifacts"][0]["core_artifact_sha256"] = "invalid"

    assert_invalid(mutate, "invalid_sha256")


def test_unknown_v2_field_fails_closed() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["release"]["notes"] = "synthetic"

    assert_invalid(mutate, "unknown_field")


def test_release_notes_are_required() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        del payload["release"]["release_notes"]

    assert_invalid(mutate, "missing_field")


def test_release_notes_url_must_match_candidate_version() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["release"]["release_notes"]["url"] = (
            "https://github.com/Kiwunaka/pokrov/releases/tag/v1.2.0"
        )

    assert_invalid(mutate, "invalid_release_notes_url")


def test_release_notes_summary_must_be_bounded_single_line() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["release"]["release_notes"]["summary"] = "line one\nline two"

    assert_invalid(mutate, "invalid_release_notes_summary")


def test_signed_claim_requires_signer_and_evidence() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        del payload["artifacts"][0]["signing"]["signer_identity"]

    assert_invalid(mutate, "signing_evidence_incomplete")


def test_pass_provenance_requires_hash_and_format() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        del payload["artifacts"][0]["provenance"]["sha256"]

    assert_invalid(mutate, "provenance_evidence_incomplete")


def test_invalid_manual_gate_status_is_not_coerced() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["manual_gates"][1]["status"] = "SKIPPED"

    assert_invalid(mutate, "invalid_evidence_status")


def test_secret_shaped_key_is_rejected_before_unknown_field() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["release"]["access_token"] = "synthetic"

    assert_invalid(mutate, "secret_material_forbidden")


@pytest.mark.parametrize(
    "secret",
    [
        "sk-" + ("x" * 24),
        "Bearer " + ("a" * 24),
        "vless://synthetic",
        "-----BEGIN PRIVATE KEY-----",
        "eyJ" + ("a" * 20) + "." + ("b" * 20) + ".sig",
    ],
)
def test_secret_shaped_value_is_rejected(secret: str) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["artifacts"][0]["signing"]["signer_identity"] = secret

    assert_invalid(mutate, "secret_material_forbidden")


def test_public_url_must_be_anonymous_canonical_release_url() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["artifacts"][0]["public_url"] += "?token=synthetic"

    assert_invalid(mutate, "invalid_public_url")


def test_artifact_source_must_match_client_revision() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["artifacts"][0]["source_revision"] = "0" * 40

    assert_invalid(mutate, "artifact_source_mismatch")


def test_artifact_set_digest_mismatch_fails_closed() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["promotion"]["source_artifact_set_sha256"] = "0" * 64

    assert_invalid(mutate, "artifact_set_digest_mismatch")


def test_stable_target_requires_all_required_gates_and_promotion_proof() -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["promotion"]["target_channel"] = "stable"

    assert_invalid(mutate, "stable_promotion_blocked")


def test_duplicate_json_object_key_is_rejected(tmp_path: Path) -> None:
    metadata = tmp_path / "release-handoff.json"
    metadata.write_text(
        '{"schema_version":2,"schema_version":2}',
        encoding="utf-8",
    )

    with pytest.raises(validator.ValidationIssue) as exc:
        validator.load_metadata(metadata)

    assert exc.value.code == "duplicate_json_key"


def test_cli_exit_codes_distinguish_v2_legacy_and_invalid(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert (
        validator.main(["--metadata-file", str(FIXTURE_PATH)])
        == validator.EXIT_VALID_V2
    )
    valid_output = capsys.readouterr()
    assert '"classification":"valid_v2"' in valid_output.out
    assert "github.com" not in valid_output.out

    legacy = tmp_path / "legacy.json"
    legacy.write_text('{"schema_version":1}', encoding="utf-8")
    assert (
        validator.main(
            [
                "--metadata-file",
                str(legacy),
                "--allow-legacy-v1",
            ]
        )
        == validator.EXIT_LEGACY_V1
    )
    legacy_output = capsys.readouterr()
    assert '"classification":"legacy_v1"' in legacy_output.out

    invalid = tmp_path / "invalid.json"
    invalid.write_text('{"schema_version":9}', encoding="utf-8")
    assert validator.main(["--metadata-file", str(invalid)]) == validator.EXIT_INVALID
    invalid_output = capsys.readouterr()
    assert '"classification":"invalid"' in invalid_output.err


def test_cli_error_does_not_echo_secret_or_public_url(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = valid_payload()
    secret = "sk-" + ("z" * 24)
    public_url = payload["artifacts"][0]["public_url"]
    payload["artifacts"][0]["signing"]["signer_identity"] = secret
    metadata = tmp_path / "invalid.json"
    metadata.write_text(json.dumps(payload), encoding="utf-8")

    assert validator.main(["--metadata-file", str(metadata)]) == validator.EXIT_INVALID
    output = capsys.readouterr()

    assert secret not in output.err
    assert public_url not in output.err
    assert '"error_code":"secret_material_forbidden"' in output.err


def test_schema_and_validator_contract_constants_do_not_drift() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    defs = schema["$defs"]
    release_v2 = defs["releaseV2"]
    properties = release_v2["properties"]

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["oneOf"] == [
        {"$ref": "#/$defs/legacyV1"},
        {"$ref": "#/$defs/releaseV2"},
    ]
    assert defs["legacyV1"]["properties"]["schema_version"] == {
        "const": 1,
        "type": "integer",
    }
    assert defs["legacyV1"]["additionalProperties"] is True
    assert release_v2["additionalProperties"] is False
    assert properties["schema_version"] == {
        "const": 2,
        "type": "integer",
    }
    assert set(release_v2["required"]) == validator.V2_REQUIRED_TOP_LEVEL
    assert set(properties["release"]["required"]) == validator.RELEASE_REQUIRED_FIELDS
    assert (
        set(properties["compatibility"]["required"])
        == validator.COMPATIBILITY_REQUIRED_FIELDS
    )
    required_contracts = {
        item["contains"]["properties"]["id"]["const"]: {
            "version": item["contains"]["properties"]["version"]["const"],
            "sha256": item["contains"]["properties"]["sha256"]["const"],
        }
        for item in properties["compatibility"]["properties"]["contracts"]["allOf"]
    }
    assert required_contracts == {
        contract_id: {
            "version": version,
            "sha256": validator.canonical_text_sha256(path),
        }
        for contract_id, (version, path) in validator.CANONICAL_CONTRACTS.items()
    }
    assert set(properties["compatibility"]["properties"]["core_abi"]["required"]) == {
        "desktop",
        "android_package",
    }
    assert set(defs["artifact"]["required"]) == validator.ARTIFACT_REQUIRED_FIELDS
    assert set(defs["manualGate"]["required"]) == validator.MANUAL_GATE_REQUIRED_FIELDS
    assert (
        set(properties["promotion"]["required"]) == validator.PROMOTION_REQUIRED_FIELDS
    )
    assert set(defs["evidenceStatus"]["enum"]) == validator.EVIDENCE_STATUSES


@pytest.mark.parametrize(
    "definition",
    [
        "artifact",
        "contractDescriptor",
        "manualGate",
        "releaseNotes",
        "releaseV2",
        "signingEvidence",
        "sourceRevision",
        "supplyEvidence",
    ],
)
def test_v2_owned_schema_definitions_are_strict(definition: str) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    assert schema["$defs"][definition]["additionalProperties"] is False
