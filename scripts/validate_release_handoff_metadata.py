"""Validate POKROV release-handoff metadata without network access.

Schema v1 is accepted only as an explicit migration input. Schema v2 is the
strict release-candidate contract and receives additional semantic checks that
JSON Schema cannot express safely on its own.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlsplit


EXIT_VALID_V2 = 0
EXIT_INVALID = 2
EXIT_LEGACY_V1 = 3
MAX_METADATA_BYTES = 2 * 1024 * 1024
REPO_ROOT = Path(__file__).resolve().parents[1]
OBSERVABILITY_CONTRACT_ROOT = REPO_ROOT / "shared" / "contracts" / "observability"

SHA256_PATTERN = re.compile(r"^[A-Fa-f0-9]{64}$")
GIT_REVISION_PATTERN = re.compile(r"^[A-Fa-f0-9]{40}$")
SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?$")
REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
CONTRACT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9._-]{1,63}$")
VERSION_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}$")
FORMAT_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._+-]{1,63}$")
GATE_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9_-]{2,63}$")
ARTIFACT_FILE_PATTERN = re.compile(r"^pokrov-[A-Za-z0-9][A-Za-z0-9._+-]{1,127}$")
SIGNER_IDENTITY_PATTERN = re.compile(r"^sha256:[A-Fa-f0-9]{64}$")

EVIDENCE_STATUSES = frozenset(
    {
        "PASS",
        "FAIL",
        "MANUAL_OWNER_TEST",
        "OPERATOR_ATTESTED",
        "SKIPPED_BY_OWNER",
        "SKIPPED_BY_OPERATOR",
        "BLOCKED_BY_ACCESS",
        "MISSING",
        "NOT_REQUESTED",
    }
)
CHANNELS = frozenset({"alpha", "beta", "rc", "stable"})
SOURCE_NAMES = ("platform", "client", "core", "release_index")
EXPECTED_REPOSITORIES = {
    "platform": "Kiwunaka/portal",
    "client": "Kiwunaka/POKROV-app",
    "core": "Kiwunaka/pokrov-core",
    "release_index": "Kiwunaka/pokrov",
}
ORIGINS = frozenset({"current", "brain", "ru", "owner", "provider"})
PLATFORM_KINDS = {
    "android": frozenset({"apk", "aab"}),
    "windows": frozenset({"exe", "msix", "zip"}),
    "linux": frozenset({"appimage", "deb", "rpm"}),
}
KIND_EXTENSIONS = {
    "apk": ".apk",
    "aab": ".aab",
    "exe": ".exe",
    "msix": ".msix",
    "zip": ".zip",
    "appimage": ".appimage",
    "deb": ".deb",
    "rpm": ".rpm",
}
REQUIRED_CONTRACT_IDS = frozenset(
    {
        "product-facts",
        "release-handoff",
        "observability-event",
        "error-catalog",
    }
)
CANONICAL_CONTRACTS = {
    "observability-event": (
        "1.0.0",
        OBSERVABILITY_CONTRACT_ROOT / "observability-event.schema.json",
    ),
    "error-catalog": (
        "1.2.0",
        OBSERVABILITY_CONTRACT_ROOT / "error-catalog.json",
    ),
}

V2_REQUIRED_TOP_LEVEL = frozenset(
    {
        "schema_version",
        "release",
        "sources",
        "compatibility",
        "artifacts",
        "manual_gates",
        "promotion",
    }
)
RELEASE_REQUIRED_FIELDS = frozenset(
    {
        "version",
        "channel",
        "candidate_label",
        "created_at_utc",
        "release_notes",
    }
)
COMPATIBILITY_REQUIRED_FIELDS = frozenset(
    {
        "core_version",
        "core_abi",
        "app_contract_version",
        "api_contract_version",
        "contracts",
    }
)
ARTIFACT_REQUIRED_FIELDS = frozenset(
    {
        "platform",
        "kind",
        "architecture",
        "file_name",
        "public_url",
        "sha256",
        "size_bytes",
        "source_revision",
        "core_version",
        "core_abi",
        "core_artifact_sha256",
        "signing",
        "sbom",
        "provenance",
    }
)
MANUAL_GATE_REQUIRED_FIELDS = frozenset(
    {"id", "origin", "status", "required_for_promotion"}
)
PROMOTION_REQUIRED_FIELDS = frozenset(
    {
        "target_channel",
        "same_byte_required",
        "source_artifact_set_sha256",
        "observed_status",
    }
)

_SECRET_KEY_MARKERS = (
    "account_id",
    "authorization",
    "config_payload",
    "cookie",
    "customer_id",
    "password",
    "private_key",
    "provider_payload",
    "secret",
    "tg_id",
    "token",
)
_SECRET_VALUE_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~-]{12,}", re.IGNORECASE),
    re.compile(r"\b(?:ss|trojan|vless|vmess|wg)://", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\."),
)


JsonObject = dict[str, Any]


class ValidationIssue(ValueError):
    """Represent a safe validation error without retaining input values."""

    def __init__(self, code: str, path: str) -> None:
        """Create an issue with a stable code and non-sensitive field path."""
        super().__init__(code)
        self.code = code
        self.path = path


class DuplicateJsonKey(ValueError):
    """Signal a duplicate JSON object key without exposing the key."""

    pass


@dataclass(frozen=True)
class ValidationSummary:
    """Safe normalized summary emitted by the validator."""

    classification: str
    schema_version: int
    release_version: str | None
    candidate_label: str | None
    source_revisions: dict[str, str]
    artifact_count: int
    blocking_gate_count: int


@dataclass(frozen=True)
class CoreCompatibility:
    """Versioned Core identity used by packaged client artifacts."""

    version: str
    desktop_abi: int
    android_package: str


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> JsonObject:
    result: JsonObject = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKey("duplicate_json_key")
        result[key] = value
    return result


def load_metadata(path: Path) -> JsonObject:
    """Load one bounded UTF-8 JSON object and reject duplicate keys.

    Args:
        path: Metadata file to read.

    Returns:
        Parsed top-level JSON object.

    Raises:
        ValidationIssue: If the file is unreadable, oversized, malformed, or
            does not contain a JSON object.
    """
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ValidationIssue("metadata_file_unreadable", "$") from exc
    if size > MAX_METADATA_BYTES:
        raise ValidationIssue("metadata_file_too_large", "$")

    try:
        with path.open("r", encoding="utf-8") as handle:
            raw = handle.read()
    except (OSError, UnicodeError) as exc:
        raise ValidationIssue("metadata_file_unreadable", "$") from exc

    try:
        payload = json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
    except DuplicateJsonKey as exc:
        raise ValidationIssue("duplicate_json_key", "$") from exc
    except json.JSONDecodeError as exc:
        raise ValidationIssue("invalid_json", "$") from exc

    if not isinstance(payload, dict):
        raise ValidationIssue("root_not_object", "$")
    return payload


def canonical_text_sha256(path: Path) -> str:
    """Return a line-ending-independent SHA-256 for a UTF-8 contract."""
    try:
        text = path.read_text(encoding="utf-8")
        canonical = text.replace("\r\n", "\n").replace("\r", "\n")
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    except (OSError, UnicodeError) as exc:
        raise ValidationIssue("canonical_contract_unreadable", "$") from exc


def _safe_path(parent: str, field: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_-]{1,64}", field):
        return f"{parent}.{field}"
    return parent


def _scan_for_secret_material(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized_key = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")
            if any(marker in normalized_key for marker in _SECRET_KEY_MARKERS):
                raise ValidationIssue("secret_material_forbidden", path)
            _scan_for_secret_material(nested, _safe_path(path, key))
        return
    if isinstance(value, list):
        for nested in value:
            _scan_for_secret_material(nested, path)
        return
    if isinstance(value, str) and any(
        pattern.search(value) for pattern in _SECRET_VALUE_PATTERNS
    ):
        raise ValidationIssue("secret_material_forbidden", path)


def _expect_object(value: Any, path: str) -> JsonObject:
    if not isinstance(value, dict):
        raise ValidationIssue("object_required", path)
    return value


def _expect_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationIssue("array_required", path)
    return value


def _check_exact_keys(
    value: JsonObject,
    required: frozenset[str] | set[str],
    optional: frozenset[str] | set[str],
    path: str,
) -> None:
    keys = set(value)
    if required - keys:
        raise ValidationIssue("missing_field", path)
    if keys - required - optional:
        raise ValidationIssue("unknown_field", path)


def _expect_string(
    value: JsonObject,
    field: str,
    path: str,
    *,
    pattern: re.Pattern[str] | None = None,
    code: str = "invalid_string",
) -> str:
    raw = value.get(field)
    field_path = f"{path}.{field}"
    if not isinstance(raw, str) or not raw:
        raise ValidationIssue(code, field_path)
    if pattern is not None and pattern.fullmatch(raw) is None:
        raise ValidationIssue(code, field_path)
    return raw


def _expect_integer(
    value: JsonObject,
    field: str,
    path: str,
    *,
    minimum: int = 1,
    code: str = "invalid_integer",
) -> int:
    raw = value.get(field)
    if type(raw) is not int or raw < minimum:
        raise ValidationIssue(code, f"{path}.{field}")
    return raw


def _expect_boolean(value: JsonObject, field: str, path: str) -> bool:
    raw = value.get(field)
    if type(raw) is not bool:
        raise ValidationIssue("invalid_boolean", f"{path}.{field}")
    return raw


def _expect_enum(
    value: JsonObject,
    field: str,
    path: str,
    allowed: frozenset[str],
    *,
    code: str,
) -> str:
    raw = value.get(field)
    if not isinstance(raw, str) or raw not in allowed:
        raise ValidationIssue(code, f"{path}.{field}")
    return raw


def _expect_sha256(value: JsonObject, field: str, path: str) -> str:
    return _expect_string(
        value,
        field,
        path,
        pattern=SHA256_PATTERN,
        code="invalid_sha256",
    ).lower()


def _expect_revision(value: JsonObject, field: str, path: str) -> str:
    return _expect_string(
        value,
        field,
        path,
        pattern=GIT_REVISION_PATTERN,
        code="invalid_git_revision",
    ).lower()


def _expect_utc_timestamp(value: JsonObject, field: str, path: str) -> str:
    raw = _expect_string(value, field, path, code="invalid_utc_timestamp")
    if not raw.endswith("Z"):
        raise ValidationIssue("invalid_utc_timestamp", f"{path}.{field}")
    try:
        datetime.fromisoformat(f"{raw[:-1]}+00:00")
    except ValueError as exc:
        raise ValidationIssue("invalid_utc_timestamp", f"{path}.{field}") from exc
    return raw


def _validate_release_notes(value: Any, *, version: str) -> None:
    path = "$.release.release_notes"
    release_notes = _expect_object(value, path)
    _check_exact_keys(
        release_notes,
        frozenset({"summary", "url"}),
        frozenset(),
        path,
    )
    summary = _expect_string(
        release_notes,
        "summary",
        path,
        code="invalid_release_notes_summary",
    )
    if (
        summary != summary.strip()
        or len(summary) > 1000
        or "\n" in summary
        or "\r" in summary
    ):
        raise ValidationIssue("invalid_release_notes_summary", f"{path}.summary")
    url = _expect_string(
        release_notes,
        "url",
        path,
        code="invalid_release_notes_url",
    )
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "github.com"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path != f"/Kiwunaka/pokrov/releases/tag/v{version}"
    ):
        raise ValidationIssue("invalid_release_notes_url", f"{path}.url")


def _validate_release(value: Any) -> tuple[str, str, str]:
    release = _expect_object(value, "$.release")
    _check_exact_keys(release, RELEASE_REQUIRED_FIELDS, frozenset(), "$.release")
    version = _expect_string(
        release,
        "version",
        "$.release",
        pattern=SEMVER_PATTERN,
        code="invalid_release_version",
    )
    channel = _expect_enum(
        release,
        "channel",
        "$.release",
        CHANNELS,
        code="invalid_release_channel",
    )
    candidate_label = _expect_string(
        release,
        "candidate_label",
        "$.release",
        code="invalid_candidate_label",
    )
    if candidate_label != f"pokrov-{version}":
        raise ValidationIssue("candidate_label_mismatch", "$.release.candidate_label")
    _expect_utc_timestamp(release, "created_at_utc", "$.release")
    _validate_release_notes(release.get("release_notes"), version=version)
    return version, channel, candidate_label


def _validate_sources(value: Any) -> dict[str, str]:
    sources = _expect_object(value, "$.sources")
    required = frozenset(SOURCE_NAMES)
    _check_exact_keys(sources, required, frozenset(), "$.sources")
    revisions: dict[str, str] = {}
    for name in SOURCE_NAMES:
        path = f"$.sources.{name}"
        source = _expect_object(sources[name], path)
        _check_exact_keys(
            source,
            frozenset({"repository", "revision"}),
            frozenset(),
            path,
        )
        repository = _expect_string(
            source,
            "repository",
            path,
            pattern=REPOSITORY_PATTERN,
            code="invalid_repository",
        )
        if repository != EXPECTED_REPOSITORIES[name]:
            raise ValidationIssue("repository_mismatch", f"{path}.repository")
        revisions[name] = _expect_revision(source, "revision", path)
    return revisions


def _validate_compatibility(value: Any) -> CoreCompatibility:
    compatibility = _expect_object(value, "$.compatibility")
    _check_exact_keys(
        compatibility,
        COMPATIBILITY_REQUIRED_FIELDS,
        frozenset(),
        "$.compatibility",
    )
    core_version = _expect_string(
        compatibility,
        "core_version",
        "$.compatibility",
        pattern=SEMVER_PATTERN,
        code="invalid_core_version",
    )
    core_abi = _expect_object(compatibility.get("core_abi"), "$.compatibility.core_abi")
    _check_exact_keys(
        core_abi,
        frozenset({"desktop", "android_package"}),
        frozenset(),
        "$.compatibility.core_abi",
    )
    desktop_abi = _expect_integer(
        core_abi,
        "desktop",
        "$.compatibility.core_abi",
        code="invalid_core_abi",
    )
    android_package = _expect_string(
        core_abi,
        "android_package",
        "$.compatibility.core_abi",
        code="invalid_android_core_package",
    )
    if android_package != "space.pokrov.core":
        raise ValidationIssue(
            "invalid_android_core_package",
            "$.compatibility.core_abi.android_package",
        )
    _expect_string(
        compatibility,
        "app_contract_version",
        "$.compatibility",
        pattern=VERSION_TOKEN_PATTERN,
        code="invalid_contract_version",
    )
    _expect_string(
        compatibility,
        "api_contract_version",
        "$.compatibility",
        pattern=VERSION_TOKEN_PATTERN,
        code="invalid_contract_version",
    )

    contracts = _expect_list(
        compatibility.get("contracts"), "$.compatibility.contracts"
    )
    if not contracts:
        raise ValidationIssue("contracts_required", "$.compatibility.contracts")
    contract_ids: set[str] = set()
    for item in contracts:
        contract = _expect_object(item, "$.compatibility.contracts")
        _check_exact_keys(
            contract,
            frozenset({"id", "version", "sha256"}),
            frozenset(),
            "$.compatibility.contracts",
        )
        contract_id = _expect_string(
            contract,
            "id",
            "$.compatibility.contracts",
            pattern=CONTRACT_ID_PATTERN,
            code="invalid_contract_id",
        )
        if contract_id in contract_ids:
            raise ValidationIssue("duplicate_contract_id", "$.compatibility.contracts")
        contract_ids.add(contract_id)
        contract_version = _expect_string(
            contract,
            "version",
            "$.compatibility.contracts",
            pattern=VERSION_TOKEN_PATTERN,
            code="invalid_contract_version",
        )
        contract_sha256 = _expect_sha256(
            contract, "sha256", "$.compatibility.contracts"
        )
        canonical = CANONICAL_CONTRACTS.get(contract_id)
        if canonical is not None:
            canonical_version, canonical_path = canonical
            if contract_version != canonical_version:
                raise ValidationIssue(
                    "canonical_contract_version_mismatch",
                    "$.compatibility.contracts",
                )
            try:
                canonical_sha256 = canonical_text_sha256(canonical_path)
            except ValidationIssue as exc:
                raise ValidationIssue(
                    "canonical_contract_unreadable",
                    "$.compatibility.contracts",
                ) from exc
            if contract_sha256 != canonical_sha256:
                raise ValidationIssue(
                    "canonical_contract_digest_mismatch",
                    "$.compatibility.contracts",
                )
    if not REQUIRED_CONTRACT_IDS.issubset(contract_ids):
        raise ValidationIssue("required_contract_missing", "$.compatibility.contracts")
    return CoreCompatibility(
        version=core_version,
        desktop_abi=desktop_abi,
        android_package=android_package,
    )


def _validate_signing(value: Any, path: str) -> str:
    signing = _expect_object(value, path)
    _check_exact_keys(
        signing,
        frozenset({"status"}),
        frozenset({"signer_identity", "evidence_sha256"}),
        path,
    )
    status = _expect_enum(
        signing,
        "status",
        path,
        EVIDENCE_STATUSES,
        code="invalid_evidence_status",
    )
    if status == "PASS":
        signer_identity = _expect_string(
            signing,
            "signer_identity",
            path,
            pattern=SIGNER_IDENTITY_PATTERN,
            code="signing_evidence_incomplete",
        )
        if not signer_identity:
            raise ValidationIssue("signing_evidence_incomplete", path)
        try:
            _expect_sha256(signing, "evidence_sha256", path)
        except ValidationIssue as exc:
            raise ValidationIssue("signing_evidence_incomplete", path) from exc
    return status


def _validate_supply_evidence(value: Any, path: str, kind: str) -> str:
    evidence = _expect_object(value, path)
    _check_exact_keys(
        evidence,
        frozenset({"status"}),
        frozenset({"format", "sha256"}),
        path,
    )
    status = _expect_enum(
        evidence,
        "status",
        path,
        EVIDENCE_STATUSES,
        code="invalid_evidence_status",
    )
    if status == "PASS":
        try:
            _expect_string(
                evidence,
                "format",
                path,
                pattern=FORMAT_PATTERN,
                code=f"{kind}_evidence_incomplete",
            )
            _expect_sha256(evidence, "sha256", path)
        except ValidationIssue as exc:
            raise ValidationIssue(f"{kind}_evidence_incomplete", path) from exc
    return status


def _validate_public_url(value: JsonObject, path: str) -> None:
    raw = _expect_string(value, "public_url", path, code="invalid_public_url")
    parsed = urlsplit(raw)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "github.com"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or not parsed.path.startswith("/Kiwunaka/pokrov/releases/download/")
    ):
        raise ValidationIssue("invalid_public_url", f"{path}.public_url")


def _validate_artifact(
    value: Any,
    *,
    source_revisions: dict[str, str],
    core: CoreCompatibility,
) -> tuple[
    tuple[str, str, str],
    JsonObject,
    tuple[str, str, str],
    str,
]:
    path = "$.artifacts"
    artifact = _expect_object(value, path)
    _check_exact_keys(artifact, ARTIFACT_REQUIRED_FIELDS, frozenset(), path)
    platform = _expect_enum(
        artifact,
        "platform",
        path,
        frozenset(PLATFORM_KINDS),
        code="invalid_artifact_platform",
    )
    kind = _expect_enum(
        artifact,
        "kind",
        path,
        PLATFORM_KINDS[platform],
        code="invalid_artifact_kind",
    )
    architecture = _expect_string(
        artifact,
        "architecture",
        path,
        pattern=VERSION_TOKEN_PATTERN,
        code="invalid_artifact_architecture",
    )
    file_name = _expect_string(
        artifact,
        "file_name",
        path,
        pattern=ARTIFACT_FILE_PATTERN,
        code="invalid_artifact_file_name",
    )
    if not file_name.lower().endswith(KIND_EXTENSIONS[kind]):
        raise ValidationIssue("artifact_extension_mismatch", f"{path}.file_name")
    _validate_public_url(artifact, path)
    artifact_sha256 = _expect_sha256(artifact, "sha256", path)
    size_bytes = _expect_integer(
        artifact,
        "size_bytes",
        path,
        code="invalid_size_bytes",
    )
    source_revision = _expect_revision(artifact, "source_revision", path)
    if source_revision != source_revisions["client"]:
        raise ValidationIssue("artifact_source_mismatch", f"{path}.source_revision")
    artifact_core_version = _expect_string(
        artifact,
        "core_version",
        path,
        pattern=SEMVER_PATTERN,
        code="invalid_core_version",
    )
    if artifact_core_version != core.version:
        raise ValidationIssue("artifact_core_mismatch", f"{path}.core_version")
    artifact_core_abi = artifact.get("core_abi")
    if platform == "android":
        if artifact_core_abi is not None:
            raise ValidationIssue("artifact_core_abi_mismatch", f"{path}.core_abi")
    elif type(artifact_core_abi) is not int or (artifact_core_abi != core.desktop_abi):
        raise ValidationIssue("artifact_core_abi_mismatch", f"{path}.core_abi")
    core_artifact_sha256 = _expect_sha256(artifact, "core_artifact_sha256", path)

    signing_status = _validate_signing(artifact.get("signing"), f"{path}.signing")
    sbom_status = _validate_supply_evidence(
        artifact.get("sbom"), f"{path}.sbom", "sbom"
    )
    provenance_status = _validate_supply_evidence(
        artifact.get("provenance"),
        f"{path}.provenance",
        "provenance",
    )
    descriptor = {
        "architecture": architecture,
        "file_name": file_name,
        "kind": kind,
        "platform": platform,
        "sha256": artifact_sha256,
        "size_bytes": size_bytes,
        "core_abi": artifact_core_abi,
        "core_artifact_sha256": core_artifact_sha256,
    }
    return (
        (platform, kind, architecture),
        descriptor,
        (signing_status, sbom_status, provenance_status),
        core_artifact_sha256,
    )


def compute_artifact_set_sha256(artifacts: Sequence[JsonObject]) -> str:
    """Compute the canonical digest for a validated artifact descriptor set."""
    canonical = json.dumps(
        sorted(
            artifacts,
            key=lambda item: (
                str(item["platform"]),
                str(item["kind"]),
                str(item["architecture"]),
            ),
        ),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _validate_manual_gates(
    value: Any,
) -> tuple[int, list[tuple[bool, str]]]:
    gates = _expect_list(value, "$.manual_gates")
    if not gates:
        raise ValidationIssue("manual_gates_required", "$.manual_gates")
    identities: set[tuple[str, str]] = set()
    normalized: list[tuple[bool, str]] = []
    for item in gates:
        path = "$.manual_gates"
        gate = _expect_object(item, path)
        _check_exact_keys(
            gate,
            MANUAL_GATE_REQUIRED_FIELDS,
            frozenset({"observed_at_utc", "evidence_sha256"}),
            path,
        )
        gate_id = _expect_string(
            gate,
            "id",
            path,
            pattern=GATE_ID_PATTERN,
            code="invalid_gate_id",
        )
        origin = _expect_enum(
            gate,
            "origin",
            path,
            ORIGINS,
            code="invalid_gate_origin",
        )
        identity = (gate_id, origin)
        if identity in identities:
            raise ValidationIssue("duplicate_manual_gate", path)
        identities.add(identity)
        status = _expect_enum(
            gate,
            "status",
            path,
            EVIDENCE_STATUSES,
            code="invalid_evidence_status",
        )
        required = _expect_boolean(gate, "required_for_promotion", path)
        if status == "PASS":
            try:
                _expect_utc_timestamp(gate, "observed_at_utc", path)
                _expect_sha256(gate, "evidence_sha256", path)
            except ValidationIssue as exc:
                raise ValidationIssue("gate_evidence_incomplete", path) from exc
        normalized.append((required, status))
    blocking_count = sum(
        1 for required, status in normalized if required and status != "PASS"
    )
    return blocking_count, normalized


def _validate_promotion(
    value: Any,
    artifact_descriptors: list[JsonObject],
) -> tuple[str, str]:
    promotion = _expect_object(value, "$.promotion")
    _check_exact_keys(
        promotion,
        PROMOTION_REQUIRED_FIELDS,
        frozenset({"observed_at_utc", "evidence_sha256"}),
        "$.promotion",
    )
    target_channel = _expect_enum(
        promotion,
        "target_channel",
        "$.promotion",
        CHANNELS,
        code="invalid_release_channel",
    )
    if not _expect_boolean(promotion, "same_byte_required", "$.promotion"):
        raise ValidationIssue(
            "same_byte_promotion_required", "$.promotion.same_byte_required"
        )
    expected_artifact_set = compute_artifact_set_sha256(artifact_descriptors)
    recorded_artifact_set = _expect_sha256(
        promotion, "source_artifact_set_sha256", "$.promotion"
    )
    if recorded_artifact_set != expected_artifact_set:
        raise ValidationIssue(
            "artifact_set_digest_mismatch",
            "$.promotion.source_artifact_set_sha256",
        )
    observed_status = _expect_enum(
        promotion,
        "observed_status",
        "$.promotion",
        EVIDENCE_STATUSES,
        code="invalid_evidence_status",
    )
    if observed_status == "PASS":
        try:
            _expect_utc_timestamp(promotion, "observed_at_utc", "$.promotion")
            _expect_sha256(promotion, "evidence_sha256", "$.promotion")
        except ValidationIssue as exc:
            raise ValidationIssue(
                "promotion_evidence_incomplete", "$.promotion"
            ) from exc
    return target_channel, observed_status


def validate_metadata(
    payload: JsonObject,
    *,
    allow_legacy_v1: bool = False,
) -> ValidationSummary:
    """Validate one release handoff and return a safe normalized summary.

    Args:
        payload: Parsed release-handoff object.
        allow_legacy_v1: Accept schema v1 as migration-only metadata.

    Returns:
        A summary that excludes URLs and raw metadata.

    Raises:
        ValidationIssue: If the payload is unsupported or invalid.
    """
    _scan_for_secret_material(payload)
    schema_version = payload.get("schema_version")
    if type(schema_version) is not int:
        raise ValidationIssue("invalid_schema_version", "$.schema_version")
    if schema_version == 1:
        if not allow_legacy_v1:
            raise ValidationIssue("legacy_v1_not_allowed", "$.schema_version")
        return ValidationSummary(
            classification="legacy_v1",
            schema_version=1,
            release_version=None,
            candidate_label=None,
            source_revisions={},
            artifact_count=0,
            blocking_gate_count=0,
        )
    if schema_version != 2:
        raise ValidationIssue("unsupported_schema_version", "$.schema_version")

    _check_exact_keys(payload, V2_REQUIRED_TOP_LEVEL, frozenset(), "$")
    release_version, release_channel, candidate_label = _validate_release(
        payload.get("release")
    )
    source_revisions = _validate_sources(payload.get("sources"))
    core = _validate_compatibility(payload.get("compatibility"))

    artifact_values = _expect_list(payload.get("artifacts"), "$.artifacts")
    if not artifact_values:
        raise ValidationIssue("artifacts_required", "$.artifacts")
    artifact_identities: set[tuple[str, str, str]] = set()
    artifact_descriptors: list[JsonObject] = []
    artifact_evidence: list[tuple[str, str, str]] = []
    platform_core_hashes: dict[str, str] = {}
    for item in artifact_values:
        identity, descriptor, evidence, core_artifact_sha256 = _validate_artifact(
            item,
            source_revisions=source_revisions,
            core=core,
        )
        if identity in artifact_identities:
            raise ValidationIssue("duplicate_artifact_identity", "$.artifacts")
        artifact_identities.add(identity)
        artifact_descriptors.append(descriptor)
        artifact_evidence.append(evidence)
        platform = identity[0]
        previous_core_hash = platform_core_hashes.setdefault(
            platform, core_artifact_sha256
        )
        if previous_core_hash != core_artifact_sha256:
            raise ValidationIssue("platform_core_artifact_mismatch", "$.artifacts")

    blocking_gate_count, gate_states = _validate_manual_gates(
        payload.get("manual_gates")
    )
    target_channel, observed_status = _validate_promotion(
        payload.get("promotion"), artifact_descriptors
    )

    stable_claim = release_channel == "stable" or target_channel == "stable"
    if stable_claim:
        if any(
            status != "PASS" for evidence in artifact_evidence for status in evidence
        ):
            raise ValidationIssue("stable_supply_evidence_incomplete", "$.artifacts")
        if any(required and status != "PASS" for required, status in gate_states):
            raise ValidationIssue("stable_promotion_blocked", "$.manual_gates")
        if observed_status != "PASS":
            raise ValidationIssue("stable_promotion_unproven", "$.promotion")

    return ValidationSummary(
        classification="valid_v2",
        schema_version=2,
        release_version=release_version,
        candidate_label=candidate_label,
        source_revisions={
            name: revision.lower() for name, revision in source_revisions.items()
        },
        artifact_count=len(artifact_values),
        blocking_gate_count=blocking_gate_count,
    )


def _render_summary(summary: ValidationSummary) -> str:
    return json.dumps(
        asdict(summary),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def _render_error(issue: ValidationIssue) -> str:
    return json.dumps(
        {
            "classification": "invalid",
            "error_code": issue.code,
            "path": issue.path,
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the release-handoff validator argument parser."""
    parser = argparse.ArgumentParser(
        description="Validate POKROV release-handoff metadata offline."
    )
    parser.add_argument(
        "--metadata-file",
        type=Path,
        required=True,
        help="Path to release-handoff JSON metadata.",
    )
    parser.add_argument(
        "--allow-legacy-v1",
        action="store_true",
        help=(
            "Classify schema v1 as migration-only metadata. "
            f"A valid v1 exits with code {EXIT_LEGACY_V1}."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the offline release-handoff validator CLI."""
    args = build_parser().parse_args(argv)
    try:
        payload = load_metadata(args.metadata_file)
        summary = validate_metadata(
            payload,
            allow_legacy_v1=bool(args.allow_legacy_v1),
        )
    except ValidationIssue as issue:
        print(_render_error(issue), file=sys.stderr)
        return EXIT_INVALID

    print(_render_summary(summary))
    if summary.classification == "legacy_v1":
        return EXIT_LEGACY_V1
    return EXIT_VALID_V2


if __name__ == "__main__":
    raise SystemExit(main())
