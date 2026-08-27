from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate_observability_contracts.py"
CONTRACT_ROOT = REPO_ROOT / "shared" / "contracts" / "observability"
EVENT_SCHEMA_PATH = CONTRACT_ROOT / "observability-event.schema.json"
CATALOG_SCHEMA_PATH = CONTRACT_ROOT / "error-catalog.schema.json"
CATALOG_PATH = CONTRACT_ROOT / "error-catalog.json"
EVENT_FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "observability" / "valid-event.json"


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_observability_contracts", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


validator = _load_validator()


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_issue(code: str, callback) -> None:
    with pytest.raises(validator.ValidationIssue) as raised:
        callback()
    assert raised.value.code == code


def test_canonical_contracts_and_valid_event_pass() -> None:
    summary = validator.validate_contracts(event_path=EVENT_FIXTURE_PATH)

    assert summary.event_contract_id == "observability-event"
    assert summary.event_contract_version == "1.0.0"
    assert summary.catalog_contract_id == "error-catalog"
    assert summary.catalog_contract_version == "1.2.0"
    assert summary.catalog_entry_count == 121
    assert summary.event_schema_sha256 == validator.file_sha256(EVENT_SCHEMA_PATH)
    assert summary.catalog_sha256 == validator.file_sha256(CATALOG_PATH)


def test_contract_hash_is_stable_across_line_endings(tmp_path: Path) -> None:
    lf_path = tmp_path / "lf.json"
    crlf_path = tmp_path / "crlf.json"
    cr_path = tmp_path / "cr.json"
    canonical = b'{"schema_version":1}\n'
    lf_path.write_bytes(canonical)
    crlf_path.write_bytes(canonical.replace(b"\n", b"\r\n"))
    cr_path.write_bytes(canonical.replace(b"\n", b"\r"))

    expected = hashlib.sha256(canonical).hexdigest()
    assert validator.file_sha256(lf_path) == expected
    assert validator.file_sha256(crlf_path) == expected
    assert validator.file_sha256(cr_path) == expected


def test_unknown_top_level_event_field_fails_closed() -> None:
    event = _load(EVENT_FIXTURE_PATH)
    event["message"] = "unsafe free-form value"
    schema = _load(EVENT_SCHEMA_PATH)
    codes = validator.validate_catalog(_load(CATALOG_PATH))

    _assert_issue("unknown_field", lambda: validator.validate_event(event, schema, codes))


def test_unknown_attribute_fails_closed() -> None:
    event = _load(EVENT_FIXTURE_PATH)
    attributes = event["attributes"]
    assert isinstance(attributes, dict)
    attributes["destination"] = "planted"
    schema = _load(EVENT_SCHEMA_PATH)
    codes = validator.validate_catalog(_load(CATALOG_PATH))

    _assert_issue("unknown_field", lambda: validator.validate_event(event, schema, codes))


def test_unknown_catalog_code_fails_closed() -> None:
    event = _load(EVENT_FIXTURE_PATH)
    error = event["error"]
    assert isinstance(error, dict)
    error["code"] = "DNS-999"
    schema = _load(EVENT_SCHEMA_PATH)
    codes = validator.validate_catalog(_load(CATALOG_PATH))

    _assert_issue("unknown_error_code", lambda: validator.validate_event(event, schema, codes))


@pytest.mark.parametrize(
    "field_name",
    ["authorization", "cookie", "url", "destination", "raw_config", "private_key"],
)
def test_planted_forbidden_schema_fields_fail(field_name: str) -> None:
    schema = _load(EVENT_SCHEMA_PATH)
    definitions = schema["$defs"]
    assert isinstance(definitions, dict)
    attributes = definitions["attributes"]
    assert isinstance(attributes, dict)
    properties = attributes["properties"]
    assert isinstance(properties, dict)
    properties[field_name] = {"type": "string"}

    _assert_issue("forbidden_event_field", lambda: validator.validate_event_schema(schema))


def test_duplicate_catalog_code_fails() -> None:
    catalog = _load(CATALOG_PATH)
    entries = catalog["entries"]
    assert isinstance(entries, list)
    entries.append(copy.deepcopy(entries[0]))

    _assert_issue("duplicate_error_code", lambda: validator.validate_catalog(catalog))


def test_unsafe_public_copy_fails() -> None:
    catalog = _load(CATALOG_PATH)
    entries = catalog["entries"]
    assert isinstance(entries, list)
    first = entries[0]
    assert isinstance(first, dict)
    first["public_message_ru"] = "Откройте https://example.invalid/private"

    _assert_issue("unsafe_public_message", lambda: validator.validate_catalog(catalog))


def test_missing_error_family_fails() -> None:
    catalog = _load(CATALOG_PATH)
    entries = catalog["entries"]
    assert isinstance(entries, list)
    catalog["entries"] = [
        entry
        for entry in entries
        if isinstance(entry, dict) and not str(entry.get("code", "")).startswith("DNS-")
    ]

    _assert_issue("required_error_family_missing", lambda: validator.validate_catalog(catalog))


def test_failed_event_requires_catalog_error() -> None:
    event = _load(EVENT_FIXTURE_PATH)
    event["error"] = None
    schema = _load(EVENT_SCHEMA_PATH)
    codes = validator.validate_catalog(_load(CATALOG_PATH))

    _assert_issue("error_required_for_failure", lambda: validator.validate_event(event, schema, codes))


def test_duplicate_json_key_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.json"
    path.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")

    _assert_issue("duplicate_json_key", lambda: validator.load_json(path))


def test_catalog_schema_is_closed() -> None:
    schema = _load(CATALOG_SCHEMA_PATH)
    validator.validate_catalog_schema(schema)
    entry = schema["$defs"]["entry"]
    assert entry["additionalProperties"] is False
    assert set(entry["required"]) == set(entry["properties"])
