"""Validate POKROV operational observability contracts without network access."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EXIT_VALID = 0
EXIT_INVALID = 2
MAX_CONTRACT_BYTES = 2 * 1024 * 1024

CONTRACT_ROOT = (
    Path(__file__).resolve().parents[1]
    / "shared"
    / "contracts"
    / "observability"
)
EVENT_SCHEMA_PATH = CONTRACT_ROOT / "observability-event.schema.json"
CATALOG_SCHEMA_PATH = CONTRACT_ROOT / "error-catalog.schema.json"
CATALOG_PATH = CONTRACT_ROOT / "error-catalog.json"

EVENT_CONTRACT_ID = "observability-event"
EVENT_CONTRACT_VERSION = "1.0.0"
CATALOG_CONTRACT_ID = "error-catalog"
CATALOG_CONTRACT_VERSION = "1.2.0"

EVENT_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "event_id",
        "occurred_at_utc",
        "component",
        "subsystem",
        "stage",
        "name",
        "severity",
        "outcome",
        "privacy_class",
        "correlation",
        "build",
        "error",
        "attributes",
    }
)
CORRELATION_REQUIRED_FIELDS = frozenset(
    {
        "trace_id",
        "span_id",
        "parent_span_id",
        "run_id",
        "attempt_id",
        "generation",
        "sequence",
    }
)
BUILD_REQUIRED_FIELDS = frozenset(
    {
        "app_version",
        "build_number",
        "channel",
        "candidate_label",
        "git_revision",
        "core_version",
        "core_abi",
        "platform",
        "architecture",
    }
)
CATALOG_ENTRY_FIELDS = frozenset(
    {
        "code",
        "severity",
        "owner",
        "public_message_key",
        "public_message_ru",
        "operator_action",
        "retry_policy",
        "release_blocking",
    }
)
REQUIRED_ERROR_FAMILIES = frozenset(
    {
        "APP-BOOT",
        "AUTH",
        "API",
        "ENT",
        "CONN",
        "CORE",
        "TUN",
        "ROUTE",
        "DNS",
        "EGRESS",
        "RECON",
        "WIN-SVC",
        "WIN-TUN",
        "WIN-DNS",
        "AND-VPN",
        "AND-BG",
        "AND-UPD",
        "LNX-SVC",
        "LNX-IPC",
        "LNX-POLKIT",
        "LNX-NM",
        "LNX-DNS",
        "LNX-NFT",
        "UPD",
        "CRASH",
        "HANG",
        "PERF",
        "SUP",
        "SEC",
    }
)

CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]{1,23}-[0-9]{3}$")
MESSAGE_KEY_PATTERN = re.compile(r"^error\.[a-z0-9_]{3,64}$")
ACTION_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

FORBIDDEN_EVENT_FIELD_MARKERS = frozenset(
    {
        "authorization",
        "cookie",
        "url",
        "destination",
        "raw_config",
        "config_payload",
        "private_key",
        "secret",
        "access_token",
        "refresh_token",
        "request_body",
        "response_body",
        "headers",
        "hostname",
        "domain",
        "ip_address",
        "account_id",
        "user_id",
        "machine_name",
        "file_path",
        "profile_payload",
    }
)
UNSAFE_PUBLIC_COPY_PATTERNS = (
    re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://"),
    re.compile(r"\b(?:Bearer|Basic)\s+[A-Za-z0-9._~-]+", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]+-----"),
    re.compile(r"\b[A-Za-z]:\\"),
    re.compile(r"/(?:home|Users|var|etc)/", re.IGNORECASE),
    re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"),
    re.compile(r"\b[A-Za-z0-9_-]{48,}\b"),
)


JsonObject = dict[str, Any]


class ValidationIssue(ValueError):
    """Safe validation error containing only a stable code and field path."""

    def __init__(self, code: str, path: str) -> None:
        super().__init__(code)
        self.code = code
        self.path = path


class DuplicateJsonKey(ValueError):
    """Signal duplicate JSON keys without retaining the input value."""


@dataclass(frozen=True)
class ContractSummary:
    """Safe digest summary for release and cross-repository checks."""

    event_contract_id: str
    event_contract_version: str
    event_schema_sha256: str
    catalog_contract_id: str
    catalog_contract_version: str
    catalog_sha256: str
    catalog_entry_count: int


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> JsonObject:
    result: JsonObject = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKey("duplicate_json_key")
        result[key] = value
    return result


def load_json(path: Path) -> JsonObject:
    """Load one bounded UTF-8 JSON object with duplicate-key rejection."""
    try:
        if path.stat().st_size > MAX_CONTRACT_BYTES:
            raise ValidationIssue("contract_too_large", "$")
        raw = path.read_text(encoding="utf-8")
    except ValidationIssue:
        raise
    except (OSError, UnicodeError) as exc:
        raise ValidationIssue("contract_unreadable", "$") from exc
    try:
        value = json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
    except DuplicateJsonKey as exc:
        raise ValidationIssue("duplicate_json_key", "$") from exc
    except json.JSONDecodeError as exc:
        raise ValidationIssue("invalid_json", "$") from exc
    if not isinstance(value, dict):
        raise ValidationIssue("root_not_object", "$")
    return value


def file_sha256(path: Path) -> str:
    """Return the lowercase SHA-256 of canonical UTF-8 text bytes."""
    try:
        canonical = (
            path.read_text(encoding="utf-8")
            .replace("\r\n", "\n")
            .replace("\r", "\n")
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    except (OSError, UnicodeError) as exc:
        raise ValidationIssue("contract_unreadable", "$") from exc


def _expect_exact_keys(value: JsonObject, expected: frozenset[str], path: str) -> None:
    actual = frozenset(value)
    if actual != expected:
        if expected - actual:
            raise ValidationIssue("required_field_missing", path)
        raise ValidationIssue("unknown_field", path)


def _expect_object(value: Any, path: str) -> JsonObject:
    if not isinstance(value, dict):
        raise ValidationIssue("object_required", path)
    return value


def _expect_closed_object_schema(
    schema: JsonObject, *, required: frozenset[str], path: str
) -> JsonObject:
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        raise ValidationIssue("closed_object_required", path)
    declared = schema.get("required")
    properties = schema.get("properties")
    if not isinstance(declared, list) or frozenset(declared) != required:
        raise ValidationIssue("schema_required_fields_mismatch", path)
    if not isinstance(properties, dict) or frozenset(properties) != required:
        raise ValidationIssue("schema_properties_mismatch", path)
    return properties


def _scan_property_names(schema: Any, path: str = "$") -> None:
    if isinstance(schema, dict):
        properties = schema.get("properties")
        if isinstance(properties, dict):
            for field_name in properties:
                normalized = field_name.lower()
                if normalized in FORBIDDEN_EVENT_FIELD_MARKERS:
                    raise ValidationIssue("forbidden_event_field", path)
        for value in schema.values():
            _scan_property_names(value, path)
    elif isinstance(schema, list):
        for value in schema:
            _scan_property_names(value, path)


def validate_event_schema(schema: JsonObject) -> None:
    """Validate the canonical schema shape and privacy closure."""
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValidationIssue("unsupported_meta_schema", "$.$schema")
    descriptor = _expect_object(schema.get("x-pokrov-contract"), "$.x-pokrov-contract")
    _expect_exact_keys(descriptor, frozenset({"id", "version"}), "$.x-pokrov-contract")
    if descriptor.get("id") != EVENT_CONTRACT_ID or descriptor.get("version") != EVENT_CONTRACT_VERSION:
        raise ValidationIssue("event_contract_identity_mismatch", "$.x-pokrov-contract")
    properties = _expect_closed_object_schema(
        schema, required=EVENT_REQUIRED_FIELDS, path="$"
    )
    if _expect_object(properties.get("schema_version"), "$.properties.schema_version").get("const") != 1:
        raise ValidationIssue("event_schema_version_mismatch", "$.properties.schema_version")

    definitions = _expect_object(schema.get("$defs"), "$.$defs")
    for definition_name in (
        "uuid",
        "utcTimestamp",
        "sha256",
        "version",
        "correlation",
        "buildIdentity",
        "errorIdentity",
        "attributes",
    ):
        if definition_name not in definitions:
            raise ValidationIssue("schema_definition_missing", "$.$defs")

    _expect_closed_object_schema(
        _expect_object(definitions["correlation"], "$.$defs.correlation"),
        required=CORRELATION_REQUIRED_FIELDS,
        path="$.$defs.correlation",
    )
    _expect_closed_object_schema(
        _expect_object(definitions["buildIdentity"], "$.$defs.buildIdentity"),
        required=BUILD_REQUIRED_FIELDS,
        path="$.$defs.buildIdentity",
    )
    _expect_closed_object_schema(
        _expect_object(definitions["errorIdentity"], "$.$defs.errorIdentity"),
        required=frozenset({"code", "origin"}),
        path="$.$defs.errorIdentity",
    )
    attributes = _expect_object(definitions["attributes"], "$.$defs.attributes")
    if attributes.get("type") != "object" or attributes.get("additionalProperties") is not False:
        raise ValidationIssue("closed_object_required", "$.$defs.attributes")
    if not isinstance(attributes.get("properties"), dict) or not attributes["properties"]:
        raise ValidationIssue("attribute_allowlist_required", "$.$defs.attributes")
    maximum = attributes.get("maxProperties")
    if type(maximum) is not int or maximum < 1 or maximum > 16:
        raise ValidationIssue("attribute_budget_invalid", "$.$defs.attributes.maxProperties")
    _scan_property_names(schema)


def _validate_public_copy(value: Any, path: str) -> None:
    if not isinstance(value, str) or not 8 <= len(value) <= 180:
        raise ValidationIssue("unsafe_public_message", path)
    if any(pattern.search(value) for pattern in UNSAFE_PUBLIC_COPY_PATTERNS):
        raise ValidationIssue("unsafe_public_message", path)


def validate_catalog_schema(schema: JsonObject) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValidationIssue("unsupported_meta_schema", "$.$schema")
    properties = _expect_closed_object_schema(
        schema,
        required=frozenset({"schema_version", "catalog_version", "entries"}),
        path="$",
    )
    if _expect_object(properties["schema_version"], "$.properties.schema_version").get("const") != 1:
        raise ValidationIssue("catalog_schema_version_mismatch", "$.properties.schema_version")
    if _expect_object(properties["catalog_version"], "$.properties.catalog_version").get("const") != CATALOG_CONTRACT_VERSION:
        raise ValidationIssue("catalog_version_mismatch", "$.properties.catalog_version")
    definitions = _expect_object(schema.get("$defs"), "$.$defs")
    entry = _expect_object(definitions.get("entry"), "$.$defs.entry")
    _expect_closed_object_schema(entry, required=CATALOG_ENTRY_FIELDS, path="$.$defs.entry")


def validate_catalog(catalog: JsonObject) -> set[str]:
    """Validate the versioned error catalog and return its known codes."""
    _expect_exact_keys(
        catalog,
        frozenset({"schema_version", "catalog_version", "entries"}),
        "$",
    )
    if catalog.get("schema_version") != 1:
        raise ValidationIssue("catalog_schema_version_mismatch", "$.schema_version")
    if catalog.get("catalog_version") != CATALOG_CONTRACT_VERSION:
        raise ValidationIssue("catalog_version_mismatch", "$.catalog_version")
    entries = catalog.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValidationIssue("catalog_entries_required", "$.entries")

    codes: set[str] = set()
    message_keys: set[str] = set()
    families: set[str] = set()
    severities = {"info", "warn", "error", "fatal"}
    owners = {
        "app",
        "release",
        "portal",
        "network",
        "security",
        "runtime",
        "node",
        "core",
        "platform",
        "windows",
        "android",
        "linux",
        "support",
    }
    retry_policies = {"none", "user_action", "bounded_backoff", "once_after_recovery"}
    for raw_entry in entries:
        entry = _expect_object(raw_entry, "$.entries")
        _expect_exact_keys(entry, CATALOG_ENTRY_FIELDS, "$.entries")
        code = entry.get("code")
        if not isinstance(code, str) or not CODE_PATTERN.fullmatch(code):
            raise ValidationIssue("invalid_error_code", "$.entries.code")
        if code in codes:
            raise ValidationIssue("duplicate_error_code", "$.entries.code")
        codes.add(code)
        families.add(code.rsplit("-", 1)[0])

        severity = entry.get("severity")
        if severity not in severities:
            raise ValidationIssue("invalid_error_severity", "$.entries.severity")
        if entry.get("owner") not in owners:
            raise ValidationIssue("invalid_error_owner", "$.entries.owner")
        message_key = entry.get("public_message_key")
        if not isinstance(message_key, str) or not MESSAGE_KEY_PATTERN.fullmatch(message_key):
            raise ValidationIssue("invalid_public_message_key", "$.entries.public_message_key")
        if message_key in message_keys:
            raise ValidationIssue("duplicate_public_message_key", "$.entries.public_message_key")
        message_keys.add(message_key)
        _validate_public_copy(entry.get("public_message_ru"), "$.entries.public_message_ru")
        action = entry.get("operator_action")
        if not isinstance(action, str) or not ACTION_PATTERN.fullmatch(action):
            raise ValidationIssue("invalid_operator_action", "$.entries.operator_action")
        if entry.get("retry_policy") not in retry_policies:
            raise ValidationIssue("invalid_retry_policy", "$.entries.retry_policy")
        release_blocking = entry.get("release_blocking")
        if type(release_blocking) is not bool:
            raise ValidationIssue("invalid_release_blocking", "$.entries.release_blocking")
        if severity == "fatal" and not release_blocking:
            raise ValidationIssue("fatal_must_block_release", "$.entries.release_blocking")

    if not REQUIRED_ERROR_FAMILIES.issubset(families):
        raise ValidationIssue("required_error_family_missing", "$.entries")
    return codes


def _resolve_schema_ref(root_schema: JsonObject, reference: str) -> JsonObject:
    if not reference.startswith("#/$defs/"):
        raise ValidationIssue("unsupported_schema_reference", "$")
    name = reference.removeprefix("#/$defs/")
    definitions = _expect_object(root_schema.get("$defs"), "$.$defs")
    return _expect_object(definitions.get(name), f"$.$defs.{name}")


def _validate_instance_value(
    value: Any, schema: JsonObject, root_schema: JsonObject, path: str
) -> None:
    reference = schema.get("$ref")
    if isinstance(reference, str):
        _validate_instance_value(value, _resolve_schema_ref(root_schema, reference), root_schema, path)
        return
    one_of = schema.get("oneOf")
    if isinstance(one_of, list):
        matched = 0
        for candidate in one_of:
            try:
                _validate_instance_value(value, _expect_object(candidate, path), root_schema, path)
            except ValidationIssue:
                continue
            matched += 1
        if matched != 1:
            raise ValidationIssue("event_value_invalid", path)
        return
    if "const" in schema and value != schema["const"]:
        raise ValidationIssue("event_value_invalid", path)
    allowed = schema.get("enum")
    if isinstance(allowed, list) and value not in allowed:
        raise ValidationIssue("event_value_invalid", path)

    expected_type = schema.get("type")
    if expected_type == "null" and value is not None:
        raise ValidationIssue("event_value_invalid", path)
    if expected_type == "string":
        if not isinstance(value, str):
            raise ValidationIssue("event_value_invalid", path)
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and not re.search(pattern, value):
            raise ValidationIssue("event_value_invalid", path)
        if isinstance(schema.get("minLength"), int) and len(value) < schema["minLength"]:
            raise ValidationIssue("event_value_invalid", path)
        if isinstance(schema.get("maxLength"), int) and len(value) > schema["maxLength"]:
            raise ValidationIssue("event_value_invalid", path)
    elif expected_type == "integer":
        if type(value) is not int:
            raise ValidationIssue("event_value_invalid", path)
        if isinstance(schema.get("minimum"), int) and value < schema["minimum"]:
            raise ValidationIssue("event_value_invalid", path)
        if isinstance(schema.get("maximum"), int) and value > schema["maximum"]:
            raise ValidationIssue("event_value_invalid", path)
    elif expected_type == "boolean" and type(value) is not bool:
        raise ValidationIssue("event_value_invalid", path)
    elif expected_type == "object":
        object_value = _expect_object(value, path)
        properties = _expect_object(schema.get("properties"), path)
        required = schema.get("required", [])
        if not isinstance(required, list):
            raise ValidationIssue("event_value_invalid", path)
        if not set(required).issubset(object_value):
            raise ValidationIssue("required_field_missing", path)
        if schema.get("additionalProperties") is False and not set(object_value).issubset(properties):
            raise ValidationIssue("unknown_field", path)
        maximum = schema.get("maxProperties")
        if isinstance(maximum, int) and len(object_value) > maximum:
            raise ValidationIssue("event_attribute_budget_exceeded", path)
        for key, nested in object_value.items():
            _validate_instance_value(
                nested,
                _expect_object(properties[key], path),
                root_schema,
                f"{path}.{key}",
            )


def validate_event(event: JsonObject, schema: JsonObject, catalog_codes: set[str]) -> None:
    """Validate one operational event against the closed canonical subset."""
    _validate_instance_value(event, schema, schema, "$")
    error = event.get("error")
    if isinstance(error, dict) and error.get("code") not in catalog_codes:
        raise ValidationIssue("unknown_error_code", "$.error.code")
    if error is None and event.get("outcome") in {"failed", "blocked"}:
        raise ValidationIssue("error_required_for_failure", "$.error")
    if error is not None and event.get("outcome") not in {"failed", "blocked", "degraded"}:
        raise ValidationIssue("error_outcome_mismatch", "$.error")


def validate_contracts(
    *,
    event_schema_path: Path = EVENT_SCHEMA_PATH,
    catalog_schema_path: Path = CATALOG_SCHEMA_PATH,
    catalog_path: Path = CATALOG_PATH,
    event_path: Path | None = None,
) -> ContractSummary:
    """Validate canonical contracts and optionally one event instance."""
    event_schema = load_json(event_schema_path)
    catalog_schema = load_json(catalog_schema_path)
    catalog = load_json(catalog_path)
    validate_event_schema(event_schema)
    validate_catalog_schema(catalog_schema)
    codes = validate_catalog(catalog)
    if event_path is not None:
        validate_event(load_json(event_path), event_schema, codes)
    event_hash = file_sha256(event_schema_path)
    catalog_hash = file_sha256(catalog_path)
    if not SHA256_PATTERN.fullmatch(event_hash) or not SHA256_PATTERN.fullmatch(catalog_hash):
        raise ValidationIssue("digest_generation_failed", "$")
    return ContractSummary(
        event_contract_id=EVENT_CONTRACT_ID,
        event_contract_version=EVENT_CONTRACT_VERSION,
        event_schema_sha256=event_hash,
        catalog_contract_id=CATALOG_CONTRACT_ID,
        catalog_contract_version=CATALOG_CONTRACT_VERSION,
        catalog_sha256=catalog_hash,
        catalog_entry_count=len(codes),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate POKROV operational observability contracts."
    )
    parser.add_argument("--event-schema", type=Path, default=EVENT_SCHEMA_PATH)
    parser.add_argument("--catalog-schema", type=Path, default=CATALOG_SCHEMA_PATH)
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--event-file", type=Path)
    args = parser.parse_args(argv)
    try:
        summary = validate_contracts(
            event_schema_path=args.event_schema,
            catalog_schema_path=args.catalog_schema,
            catalog_path=args.catalog,
            event_path=args.event_file,
        )
    except ValidationIssue as exc:
        print(
            json.dumps(
                {"status": "INVALID", "code": exc.code, "path": exc.path},
                separators=(",", ":"),
                sort_keys=True,
            )
        )
        return EXIT_INVALID
    print(
        json.dumps(
            {
                "catalog_entry_count": summary.catalog_entry_count,
                "catalog_sha256": summary.catalog_sha256,
                "event_schema_sha256": summary.event_schema_sha256,
                "status": "VALID",
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return EXIT_VALID


if __name__ == "__main__":
    sys.exit(main())
