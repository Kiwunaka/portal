"""Validate exact POKROV candidate artifacts, SBOM, and provenance offline."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import quote


EXIT_VALID = 0
EXIT_INVALID = 2
MAX_JSON_BYTES = 8 * 1024 * 1024
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
REVISION_PATTERN = re.compile(r"^[a-f0-9]{40}$")
CANDIDATE_ID_PATTERN = re.compile(r"^pokrov-1\.2\.0-candidate\.[1-9][0-9]*$")
CANDIDATE_REFERENCE_PATTERN = re.compile(r"candidate[._-]?([1-9][0-9]*)", re.IGNORECASE)
EXPECTED_REPOSITORIES = {
    "platform": "Kiwunaka/portal",
    "client": "Kiwunaka/POKROV-app",
    "core": "Kiwunaka/pokrov-core",
    "release_index": "Kiwunaka/pokrov",
}
EXPECTED_ARTIFACTS = {
    "pokrov-android-market.aab": ("android", "aab", "universal"),
    "pokrov-android-arm64-v8a.apk": ("android", "apk", "arm64-v8a"),
    "pokrov-android-armeabi-v7a.apk": ("android", "apk", "armeabi-v7a"),
    "pokrov-android-universal.apk": ("android", "apk", "universal"),
    "pokrov-android-x86_64.apk": ("android", "apk", "x86_64"),
    "pokrov-windows-setup-x64.exe": ("windows", "exe", "x64"),
}
PROVENANCE_ARTIFACT_ORDER = (
    "pokrov-android-arm64-v8a.apk",
    "pokrov-android-armeabi-v7a.apk",
    "pokrov-android-market.aab",
    "pokrov-android-universal.apk",
    "pokrov-android-x86_64.apk",
    "pokrov-windows-setup-x64.exe",
)
EXPECTED_SBOM_FORMAT = "CycloneDX"
EXPECTED_SBOM_SPEC_VERSION = "1.5"
EXPECTED_PROVENANCE_TYPE = "https://in-toto.io/Statement/v1"
EXPECTED_PROVENANCE_PREDICATE = "https://slsa.dev/provenance/v1"
EXPECTED_PROVENANCE_BUILD_TYPE = "https://pokrov.space/build-types/client-release/v1"

JsonObject = dict[str, Any]


class SupplyChainIssue(ValueError):
    """Represent a safe validation failure without retaining input values."""

    def __init__(self, code: str, path: str) -> None:
        """Create an issue with a stable code and non-sensitive path."""
        super().__init__(code)
        self.code = code
        self.path = path


class DuplicateJsonKey(ValueError):
    """Signal a duplicate JSON key."""


@dataclass(frozen=True)
class ExpectedIdentity:
    """Exact candidate and source identity supplied by the operator."""

    candidate_id: str
    product_version: str
    package_version: str
    platform_revision: str
    client_revision: str
    core_revision: str
    release_index_revision: str
    android_core_artifact_sha256: str
    windows_core_artifact_sha256: str


@dataclass(frozen=True)
class ValidationSummary:
    """Secret-free validation result suitable for retained evidence."""

    status: str
    candidate_id: str
    artifact_count: int
    windows_runtime_file_count: int
    source_revisions: dict[str, str]
    release_handoff_sha256: str
    sbom_sha256: str
    provenance_sha256: str
    windows_manifest_sha256: str


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> JsonObject:
    result: JsonObject = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKey("duplicate_json_key")
        result[key] = value
    return result


def _load_json(path: Path, label: str) -> JsonObject:
    try:
        stat = path.lstat()
    except OSError as exc:
        raise SupplyChainIssue("json_file_unreadable", label) from exc
    if path.is_symlink() or not path.is_file():
        raise SupplyChainIssue("json_file_not_regular", label)
    if stat.st_size > MAX_JSON_BYTES:
        raise SupplyChainIssue("json_file_too_large", label)
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle, object_pairs_hook=_reject_duplicate_keys)
    except DuplicateJsonKey as exc:
        raise SupplyChainIssue("duplicate_json_key", label) from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SupplyChainIssue("invalid_json", label) from exc
    if not isinstance(payload, dict):
        raise SupplyChainIssue("json_object_required", label)
    return payload


def _object(value: Any, path: str) -> JsonObject:
    if not isinstance(value, dict):
        raise SupplyChainIssue("object_required", path)
    return value


def _array(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise SupplyChainIssue("array_required", path)
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise SupplyChainIssue("string_required", path)
    return value


def _positive_int(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise SupplyChainIssue("positive_integer_required", path)
    return value


def _sha256(value: Any, path: str) -> str:
    digest = _string(value, path).lower()
    if SHA256_PATTERN.fullmatch(digest) is None:
        raise SupplyChainIssue("invalid_sha256", path)
    return digest


def _revision(value: Any, path: str) -> str:
    revision = _string(value, path).lower()
    if REVISION_PATTERN.fullmatch(revision) is None:
        raise SupplyChainIssue("invalid_revision", path)
    return revision


def _file_sha256(path: Path) -> str:
    algorithm = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                algorithm.update(chunk)
    except OSError as exc:
        raise SupplyChainIssue("file_unreadable", path.name) from exc
    return algorithm.hexdigest()


def _provenance_artifact_set_sha256(artifacts: dict[str, JsonObject]) -> str:
    lines: list[str] = []
    for name in PROVENANCE_ARTIFACT_ORDER:
        artifact = artifacts[name]
        size = _positive_int(artifact.get("size_bytes"), f"artifact.{name}.size_bytes")
        digest = _sha256(artifact.get("sha256"), f"artifact.{name}.sha256")
        lines.append(f"{name}|{size}|{digest}\n")
    return hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()


def _candidate_ordinal(candidate_id: str) -> str:
    return candidate_id.rsplit(".", maxsplit=1)[1]


def _sbom_root_bom_ref(expected: ExpectedIdentity) -> str:
    package_version = quote(expected.package_version, safe="")
    return (
        f"pkg:generic/pokrov-release-candidate@{package_version}"
        f"?candidate={_candidate_ordinal(expected.candidate_id)}"
    )


def _validate_candidate_references(
    value: Any,
    *,
    expected_ordinal: str,
    path: str,
) -> None:
    if isinstance(value, dict):
        for index, (key, child) in enumerate(value.items()):
            _validate_candidate_references(
                key,
                expected_ordinal=expected_ordinal,
                path=f"{path}.key[{index}]",
            )
            _validate_candidate_references(
                child,
                expected_ordinal=expected_ordinal,
                path=f"{path}.value[{index}]",
            )
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _validate_candidate_references(
                child,
                expected_ordinal=expected_ordinal,
                path=f"{path}[{index}]",
            )
        return
    if not isinstance(value, str):
        return
    if any(match != expected_ordinal for match in CANDIDATE_REFERENCE_PATTERN.findall(value)):
        raise SupplyChainIssue(
            "provenance_internal_candidate_reference_mismatch",
            path,
        )


def _require_under_root(path: Path, root: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise SupplyChainIssue("path_outside_candidate_root", label) from exc
    if path.is_symlink() or not resolved.is_file():
        raise SupplyChainIssue("input_file_not_regular", label)
    return resolved


def _property_map(value: Any, path: str) -> dict[str, str]:
    properties: dict[str, str] = {}
    for index, item in enumerate(_array(value, path)):
        entry = _object(item, f"{path}[{index}]")
        name = _string(entry.get("name"), f"{path}[{index}].name")
        property_value = _string(entry.get("value"), f"{path}[{index}].value")
        if name in properties:
            raise SupplyChainIssue("duplicate_property", path)
        properties[name] = property_value
    return properties


def _component_sha256(component: JsonObject, path: str) -> str:
    found: str | None = None
    for index, item in enumerate(_array(component.get("hashes"), f"{path}.hashes")):
        digest = _object(item, f"{path}.hashes[{index}]")
        if _string(digest.get("alg"), f"{path}.hashes[{index}].alg").upper() != "SHA-256":
            continue
        if found is not None:
            raise SupplyChainIssue("duplicate_component_sha256", path)
        found = _sha256(digest.get("content"), f"{path}.hashes[{index}].content")
    if found is None:
        raise SupplyChainIssue("component_sha256_missing", path)
    return found


def _source_revisions(handoff: JsonObject, expected: ExpectedIdentity) -> dict[str, str]:
    sources = _object(handoff.get("sources"), "release_handoff.sources")
    expected_revisions = {
        "platform": expected.platform_revision,
        "client": expected.client_revision,
        "core": expected.core_revision,
        "release_index": expected.release_index_revision,
    }
    actual: dict[str, str] = {}
    if set(sources) != set(EXPECTED_REPOSITORIES):
        raise SupplyChainIssue("source_set_mismatch", "release_handoff.sources")
    for name, repository in EXPECTED_REPOSITORIES.items():
        source = _object(sources.get(name), f"release_handoff.sources.{name}")
        if _string(source.get("repository"), f"release_handoff.sources.{name}.repository") != repository:
            raise SupplyChainIssue("source_repository_mismatch", f"release_handoff.sources.{name}")
        revision = _revision(source.get("revision"), f"release_handoff.sources.{name}.revision")
        if revision != expected_revisions[name]:
            raise SupplyChainIssue("source_revision_mismatch", f"release_handoff.sources.{name}")
        actual[name] = revision
    return actual


def _artifact_map(
    handoff: JsonObject,
    candidate_root: Path,
    expected: ExpectedIdentity,
) -> tuple[dict[str, JsonObject], set[str], set[str]]:
    artifacts: dict[str, JsonObject] = {}
    sbom_digests: set[str] = set()
    provenance_digests: set[str] = set()
    for index, value in enumerate(_array(handoff.get("artifacts"), "release_handoff.artifacts")):
        artifact = _object(value, f"release_handoff.artifacts[{index}]")
        name = _string(artifact.get("file_name"), f"release_handoff.artifacts[{index}].file_name")
        if Path(name).name != name or name in artifacts:
            raise SupplyChainIssue("invalid_or_duplicate_artifact_name", "release_handoff.artifacts")
        descriptor = EXPECTED_ARTIFACTS.get(name)
        if descriptor is None:
            raise SupplyChainIssue("artifact_set_mismatch", "release_handoff.artifacts")
        for field_name, expected_value in zip(
            ("platform", "kind", "architecture"),
            descriptor,
            strict=True,
        ):
            if _string(
                artifact.get(field_name),
                f"release_handoff.artifacts[{index}].{field_name}",
            ) != expected_value:
                raise SupplyChainIssue("artifact_descriptor_mismatch", name)
        if _revision(artifact.get("source_revision"), f"release_handoff.artifacts[{index}].source_revision") != expected.client_revision:
            raise SupplyChainIssue("artifact_source_revision_mismatch", name)
        expected_core_digest = (
            expected.android_core_artifact_sha256
            if descriptor[0] == "android"
            else expected.windows_core_artifact_sha256
        )
        if _sha256(
            artifact.get("core_artifact_sha256"),
            f"release_handoff.artifacts[{index}].core_artifact_sha256",
        ) != expected_core_digest:
            raise SupplyChainIssue("artifact_core_digest_mismatch", name)
        expected_size = _positive_int(artifact.get("size_bytes"), f"release_handoff.artifacts[{index}].size_bytes")
        expected_digest = _sha256(artifact.get("sha256"), f"release_handoff.artifacts[{index}].sha256")
        artifact_path = candidate_root / name
        if artifact_path.is_symlink() or not artifact_path.is_file():
            raise SupplyChainIssue("artifact_missing_or_not_regular", name)
        if artifact_path.stat().st_size != expected_size:
            raise SupplyChainIssue("artifact_size_mismatch", name)
        if _file_sha256(artifact_path) != expected_digest:
            raise SupplyChainIssue("artifact_sha256_mismatch", name)
        sbom_ref = _object(artifact.get("sbom"), f"release_handoff.artifacts[{index}].sbom")
        provenance_ref = _object(
            artifact.get("provenance"),
            f"release_handoff.artifacts[{index}].provenance",
        )
        if _string(sbom_ref.get("status"), f"release_handoff.artifacts[{index}].sbom.status") != "PASS":
            raise SupplyChainIssue("sbom_status_not_pass", name)
        if _string(provenance_ref.get("status"), f"release_handoff.artifacts[{index}].provenance.status") != "PASS":
            raise SupplyChainIssue("provenance_status_not_pass", name)
        sbom_digests.add(_sha256(sbom_ref.get("sha256"), f"release_handoff.artifacts[{index}].sbom.sha256"))
        provenance_digests.add(
            _sha256(
                provenance_ref.get("sha256"),
                f"release_handoff.artifacts[{index}].provenance.sha256",
            )
        )
        artifacts[name] = artifact
    if set(artifacts) != set(EXPECTED_ARTIFACTS):
        raise SupplyChainIssue("artifact_set_mismatch", "release_handoff.artifacts")
    if len(sbom_digests) != 1:
        raise SupplyChainIssue("sbom_digest_set_mismatch", "release_handoff.artifacts")
    if len(provenance_digests) != 1:
        raise SupplyChainIssue("provenance_digest_set_mismatch", "release_handoff.artifacts")
    return artifacts, sbom_digests, provenance_digests


def _component_index(
    sbom: JsonObject,
) -> tuple[dict[str, list[JsonObject]], dict[str, JsonObject]]:
    by_name: dict[str, list[JsonObject]] = {}
    by_ref: dict[str, JsonObject] = {}
    for index, value in enumerate(_array(sbom.get("components"), "sbom.components")):
        component = _object(value, f"sbom.components[{index}]")
        name = _string(component.get("name"), f"sbom.components[{index}].name")
        reference = _string(component.get("bom-ref"), f"sbom.components[{index}].bom-ref")
        if reference in by_ref:
            raise SupplyChainIssue("duplicate_sbom_bom_ref", "sbom.components")
        by_name.setdefault(name, []).append(component)
        by_ref[reference] = component
    return by_name, by_ref


def _unique_named_component(
    by_name: dict[str, list[JsonObject]],
    name: str,
) -> JsonObject:
    matches = by_name.get(name, [])
    if not matches:
        raise SupplyChainIssue("sbom_source_component_missing", name)
    if len(matches) != 1:
        raise SupplyChainIssue("duplicate_sbom_source_component", name)
    return matches[0]


def _validate_sbom(
    sbom: JsonObject,
    artifacts: dict[str, JsonObject],
    windows_manifest: JsonObject,
    expected: ExpectedIdentity,
) -> int:
    if _string(sbom.get("bomFormat"), "sbom.bomFormat") != EXPECTED_SBOM_FORMAT:
        raise SupplyChainIssue("sbom_format_mismatch", "sbom.bomFormat")
    if _string(sbom.get("specVersion"), "sbom.specVersion") != EXPECTED_SBOM_SPEC_VERSION:
        raise SupplyChainIssue("sbom_spec_version_mismatch", "sbom.specVersion")
    metadata = _object(sbom.get("metadata"), "sbom.metadata")
    root_component = _object(metadata.get("component"), "sbom.metadata.component")
    if _string(root_component.get("version"), "sbom.metadata.component.version") != expected.package_version:
        raise SupplyChainIssue("sbom_package_version_mismatch", "sbom.metadata.component")
    if (
        _string(root_component.get("bom-ref"), "sbom.metadata.component.bom-ref")
        != _sbom_root_bom_ref(expected)
    ):
        raise SupplyChainIssue("sbom_root_bom_ref_mismatch", "sbom.metadata.component.bom-ref")
    root_properties = _property_map(root_component.get("properties"), "sbom.metadata.component.properties")
    artifact_set_sha256 = _provenance_artifact_set_sha256(artifacts)
    expected_properties = {
        "pokrov:candidate-id": expected.candidate_id,
        "pokrov:platform-commit": expected.platform_revision,
        "pokrov:client-commit": expected.client_revision,
        "pokrov:core-commit": expected.core_revision,
    }
    for name, value in expected_properties.items():
        if root_properties.get(name) != value:
            raise SupplyChainIssue("sbom_source_revision_mismatch", name)
    if root_properties.get("pokrov:artifact-set-sha256") != artifact_set_sha256:
        raise SupplyChainIssue(
            "sbom_artifact_set_digest_mismatch",
            "pokrov:artifact-set-sha256",
        )

    by_name, by_ref = _component_index(sbom)
    artifact_references = {
        reference for reference in by_ref if reference.startswith("file:")
    }
    expected_artifact_references = {f"file:{name}" for name in artifacts}
    if artifact_references != expected_artifact_references:
        raise SupplyChainIssue("sbom_artifact_set_mismatch", "sbom.components")
    for name, artifact in artifacts.items():
        component = by_ref.get(f"file:{name}")
        if component is None or _string(component.get("name"), f"sbom.artifact.{name}.name") != name:
            raise SupplyChainIssue("sbom_artifact_component_missing", name)
        if _component_sha256(component, f"sbom.artifact.{name}") != _sha256(artifact.get("sha256"), name):
            raise SupplyChainIssue("sbom_artifact_digest_mismatch", name)
        properties = _property_map(component.get("properties"), f"sbom.artifact.{name}.properties")
        if properties.get("pokrov:size-bytes") != str(artifact.get("size_bytes")):
            raise SupplyChainIssue("sbom_artifact_size_mismatch", name)
        if properties.get("pokrov:candidate-id") != expected.candidate_id:
            raise SupplyChainIssue("sbom_candidate_id_mismatch", name)

    client_component = _unique_named_component(by_name, "POKROV client")
    core_component = _unique_named_component(by_name, "POKROV Core")
    client_properties = _property_map(client_component.get("properties"), "sbom.client.properties")
    core_properties = _property_map(core_component.get("properties"), "sbom.core.properties")
    if client_properties.get("pokrov:git-commit") != expected.client_revision:
        raise SupplyChainIssue("sbom_source_revision_mismatch", "sbom.client")
    if core_properties.get("pokrov:git-commit") != expected.core_revision:
        raise SupplyChainIssue("sbom_source_revision_mismatch", "sbom.core")
    android_core_digests = {
        _sha256(artifact.get("core_artifact_sha256"), name)
        for name, artifact in artifacts.items()
        if artifact.get("platform") == "android"
    }
    windows_core_digests = {
        _sha256(artifact.get("core_artifact_sha256"), name)
        for name, artifact in artifacts.items()
        if artifact.get("platform") == "windows"
    }
    if android_core_digests != {expected.android_core_artifact_sha256}:
        raise SupplyChainIssue("sbom_core_artifact_mismatch", "sbom.core.android")
    if windows_core_digests != {expected.windows_core_artifact_sha256}:
        raise SupplyChainIssue("sbom_core_artifact_mismatch", "sbom.core.windows")
    if core_properties.get("pokrov:android-aar-sha256") != expected.android_core_artifact_sha256:
        raise SupplyChainIssue("sbom_core_artifact_mismatch", "sbom.core.android")
    if core_properties.get("pokrov:windows-dll-sha256") != expected.windows_core_artifact_sha256:
        raise SupplyChainIssue("sbom_core_artifact_mismatch", "sbom.core.windows")

    required_files = _array(windows_manifest.get("required_files"), "windows_manifest.required_files")
    seen_runtime: set[str] = set()
    windows_core_runtime_digest: str | None = None
    for index, value in enumerate(required_files):
        runtime = _object(value, f"windows_manifest.required_files[{index}]")
        name = _string(runtime.get("path"), f"windows_manifest.required_files[{index}].path")
        if name in seen_runtime:
            raise SupplyChainIssue("duplicate_windows_runtime_file", "windows_manifest.required_files")
        seen_runtime.add(name)
        component = by_ref.get(f"windows-runtime:{name}")
        if component is None:
            raise SupplyChainIssue("sbom_windows_runtime_missing", name)
        if _component_sha256(component, f"sbom.windows_runtime.{name}") != _sha256(runtime.get("sha256"), name):
            raise SupplyChainIssue("sbom_windows_runtime_digest_mismatch", name)
        if name == "pokrov-core.dll":
            windows_core_runtime_digest = _sha256(runtime.get("sha256"), name)
        properties = _property_map(component.get("properties"), f"sbom.windows_runtime.{name}.properties")
        if properties.get("pokrov:size-bytes") != str(_positive_int(runtime.get("size_bytes"), name)):
            raise SupplyChainIssue("sbom_windows_runtime_size_mismatch", name)
    if not seen_runtime:
        raise SupplyChainIssue("windows_runtime_set_empty", "windows_manifest.required_files")
    runtime_references = {
        reference for reference in by_ref if reference.startswith("windows-runtime:")
    }
    expected_runtime_references = {
        f"windows-runtime:{name}" for name in seen_runtime
    }
    if runtime_references != expected_runtime_references:
        raise SupplyChainIssue("sbom_windows_runtime_set_mismatch", "sbom.components")
    if windows_core_runtime_digest != expected.windows_core_artifact_sha256:
        raise SupplyChainIssue("windows_core_digest_mismatch", "windows_manifest.required_files")
    return len(seen_runtime)


def _validate_windows_manifest(
    manifest: JsonObject,
    artifacts: dict[str, JsonObject],
    expected: ExpectedIdentity,
) -> None:
    if _string(manifest.get("version"), "windows_manifest.version") != expected.package_version:
        raise SupplyChainIssue("windows_manifest_version_mismatch", "windows_manifest.version")
    windows_artifacts = [
        artifact for artifact in artifacts.values() if artifact.get("platform") == "windows"
    ]
    if len(windows_artifacts) != 1:
        raise SupplyChainIssue("windows_artifact_count_mismatch", "release_handoff.artifacts")
    expected_digest = _sha256(windows_artifacts[0].get("sha256"), "windows_artifact.sha256")
    if _sha256(manifest.get("installer_sha256"), "windows_manifest.installer_sha256") != expected_digest:
        raise SupplyChainIssue("windows_installer_digest_mismatch", "windows_manifest")


def _validate_provenance(
    provenance: JsonObject,
    artifacts: dict[str, JsonObject],
    expected: ExpectedIdentity,
    sbom_name: str,
    sbom_digest: str,
) -> None:
    if _string(provenance.get("_type"), "provenance._type") != EXPECTED_PROVENANCE_TYPE:
        raise SupplyChainIssue("provenance_type_mismatch", "provenance._type")
    if (
        _string(provenance.get("predicateType"), "provenance.predicateType")
        != EXPECTED_PROVENANCE_PREDICATE
    ):
        raise SupplyChainIssue("provenance_predicate_type_mismatch", "provenance.predicateType")
    subjects: dict[str, str] = {}
    for index, value in enumerate(_array(provenance.get("subject"), "provenance.subject")):
        subject = _object(value, f"provenance.subject[{index}]")
        name = _string(subject.get("name"), f"provenance.subject[{index}].name")
        if name in subjects:
            raise SupplyChainIssue("duplicate_provenance_subject", "provenance.subject")
        digest = _object(subject.get("digest"), f"provenance.subject[{index}].digest")
        subjects[name] = _sha256(digest.get("sha256"), f"provenance.subject[{index}].digest.sha256")
    expected_subjects = {
        name: _sha256(artifact.get("sha256"), name) for name, artifact in artifacts.items()
    }
    if subjects != expected_subjects:
        raise SupplyChainIssue("provenance_subject_set_mismatch", "provenance.subject")

    predicate = _object(provenance.get("predicate"), "provenance.predicate")
    build = _object(predicate.get("buildDefinition"), "provenance.predicate.buildDefinition")
    if (
        _string(build.get("buildType"), "provenance.buildDefinition.buildType")
        != EXPECTED_PROVENANCE_BUILD_TYPE
    ):
        raise SupplyChainIssue("provenance_build_type_mismatch", "provenance.buildDefinition")
    external = _object(build.get("externalParameters"), "provenance.externalParameters")
    if _string(external.get("candidate_id"), "provenance.externalParameters.candidate_id") != expected.candidate_id:
        raise SupplyChainIssue("provenance_candidate_id_mismatch", "provenance.externalParameters")
    if _string(external.get("product_version"), "provenance.externalParameters.product_version") != expected.package_version:
        raise SupplyChainIssue("provenance_package_version_mismatch", "provenance.externalParameters")
    internal = build.get("internalParameters")
    if internal is not None:
        _validate_candidate_references(
            _object(internal, "provenance.internalParameters"),
            expected_ordinal=_candidate_ordinal(expected.candidate_id),
            path="provenance.internalParameters",
        )

    dependencies = _array(build.get("resolvedDependencies"), "provenance.resolvedDependencies")
    dependency_uri_list = [
        _string(_object(value, "provenance.dependency").get("uri"), "provenance.dependency.uri")
        for value in dependencies
    ]
    if len(dependency_uri_list) != len(set(dependency_uri_list)):
        raise SupplyChainIssue("duplicate_provenance_dependency", "provenance.resolvedDependencies")
    source_dependency_uris = {
        uri for uri in dependency_uri_list if uri.startswith("git+")
    }
    expected_uris = {
        f"git+https://github.com/{EXPECTED_REPOSITORIES['platform']}@{expected.platform_revision}",
        f"git+https://github.com/{EXPECTED_REPOSITORIES['client']}@{expected.client_revision}",
        f"git+https://github.com/{EXPECTED_REPOSITORIES['core']}@{expected.core_revision}",
        f"git+https://github.com/{EXPECTED_REPOSITORIES['release_index']}@{expected.release_index_revision}",
    }
    if source_dependency_uris != expected_uris:
        raise SupplyChainIssue("provenance_source_revision_mismatch", "provenance.resolvedDependencies")

    run_details = _object(predicate.get("runDetails"), "provenance.predicate.runDetails")
    metadata = _object(run_details.get("metadata"), "provenance.runDetails.metadata")
    expected_invocation_id = (
        f"{expected.candidate_id}/{_provenance_artifact_set_sha256(artifacts)}"
    )
    if (
        _string(metadata.get("invocationId"), "provenance.metadata.invocationId")
        != expected_invocation_id
    ):
        raise SupplyChainIssue(
            "provenance_invocation_artifact_set_mismatch",
            "provenance.metadata.invocationId",
        )
    byproducts = _array(run_details.get("byproducts"), "provenance.byproducts")
    sbom_byproducts = []
    for value in byproducts:
        byproduct = _object(value, "provenance.byproduct")
        if byproduct.get("name") == sbom_name:
            sbom_byproducts.append(byproduct)
    if len(sbom_byproducts) != 1:
        raise SupplyChainIssue("provenance_sbom_byproduct_missing", "provenance.byproducts")
    digest = _object(sbom_byproducts[0].get("digest"), "provenance.sbom.digest")
    if _sha256(digest.get("sha256"), "provenance.sbom.digest.sha256") != sbom_digest:
        raise SupplyChainIssue("provenance_sbom_digest_mismatch", "provenance.byproducts")


def validate_candidate(
    *,
    candidate_root: Path,
    handoff_path: Path,
    sbom_path: Path,
    provenance_path: Path,
    windows_manifest_path: Path,
    expected: ExpectedIdentity,
) -> ValidationSummary:
    """Validate one exact candidate directory without network access.

    Args:
        candidate_root: Directory containing immutable candidate artifacts.
        handoff_path: Strict-v2 handoff generated for the candidate.
        sbom_path: CycloneDX candidate SBOM.
        provenance_path: SLSA/in-toto candidate provenance.
        windows_manifest_path: Exact Windows bundle manifest.
        expected: Operator-supplied exact source and candidate identity.

    Returns:
        Secret-free validation summary.

    Raises:
        SupplyChainIssue: If any artifact or supply-chain binding differs.
    """
    root = candidate_root.resolve()
    if candidate_root.is_symlink() or not root.is_dir():
        raise SupplyChainIssue("candidate_root_not_directory", "candidate_root")
    paths = {
        "release_handoff": _require_under_root(handoff_path, root, "release_handoff"),
        "sbom": _require_under_root(sbom_path, root, "sbom"),
        "provenance": _require_under_root(provenance_path, root, "provenance"),
        "windows_manifest": _require_under_root(
            windows_manifest_path,
            root,
            "windows_manifest",
        ),
    }
    handoff = _load_json(paths["release_handoff"], "release_handoff")
    sbom = _load_json(paths["sbom"], "sbom")
    provenance = _load_json(paths["provenance"], "provenance")
    windows_manifest = _load_json(paths["windows_manifest"], "windows_manifest")

    if handoff.get("schema_version") != 2:
        raise SupplyChainIssue("release_handoff_schema_mismatch", "release_handoff.schema_version")
    release = _object(handoff.get("release"), "release_handoff.release")
    if _string(release.get("version"), "release_handoff.release.version") != expected.product_version:
        raise SupplyChainIssue("product_version_mismatch", "release_handoff.release")
    sources = _source_revisions(handoff, expected)
    artifacts, sbom_refs, provenance_refs = _artifact_map(handoff, root, expected)

    sbom_digest = _file_sha256(paths["sbom"])
    provenance_digest = _file_sha256(paths["provenance"])
    if sbom_refs != {sbom_digest}:
        raise SupplyChainIssue("sbom_digest_mismatch", "release_handoff.artifacts")
    if provenance_refs != {provenance_digest}:
        raise SupplyChainIssue("provenance_digest_mismatch", "release_handoff.artifacts")

    _validate_windows_manifest(windows_manifest, artifacts, expected)
    runtime_count = _validate_sbom(sbom, artifacts, windows_manifest, expected)
    _validate_provenance(
        provenance,
        artifacts,
        expected,
        paths["sbom"].name,
        sbom_digest,
    )
    return ValidationSummary(
        status="PASS",
        candidate_id=expected.candidate_id,
        artifact_count=len(artifacts),
        windows_runtime_file_count=runtime_count,
        source_revisions=sources,
        release_handoff_sha256=_file_sha256(paths["release_handoff"]),
        sbom_sha256=sbom_digest,
        provenance_sha256=provenance_digest,
        windows_manifest_sha256=_file_sha256(paths["windows_manifest"]),
    )


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate exact POKROV candidate artifacts, SBOM, and provenance."
    )
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--release-handoff", type=Path, required=True)
    parser.add_argument("--sbom", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--windows-manifest", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--product-version", required=True)
    parser.add_argument("--package-version", required=True)
    parser.add_argument("--platform-revision", required=True)
    parser.add_argument("--client-revision", required=True)
    parser.add_argument("--core-revision", required=True)
    parser.add_argument("--release-index-revision", required=True)
    parser.add_argument("--android-core-artifact-sha256", required=True)
    parser.add_argument("--windows-core-artifact-sha256", required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def _expected_from_args(args: argparse.Namespace) -> ExpectedIdentity:
    candidate_id = _string(args.candidate_id, "candidate_id")
    if CANDIDATE_ID_PATTERN.fullmatch(candidate_id) is None:
        raise SupplyChainIssue("invalid_candidate_id", "candidate_id")
    return ExpectedIdentity(
        candidate_id=candidate_id,
        product_version=_string(args.product_version, "product_version"),
        package_version=_string(args.package_version, "package_version"),
        platform_revision=_revision(args.platform_revision, "platform_revision"),
        client_revision=_revision(args.client_revision, "client_revision"),
        core_revision=_revision(args.core_revision, "core_revision"),
        release_index_revision=_revision(
            args.release_index_revision,
            "release_index_revision",
        ),
        android_core_artifact_sha256=_sha256(
            args.android_core_artifact_sha256,
            "android_core_artifact_sha256",
        ),
        windows_core_artifact_sha256=_sha256(
            args.windows_core_artifact_sha256,
            "windows_core_artifact_sha256",
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the offline verifier and emit only normalized output."""
    args = _parse_args(argv)
    try:
        expected = _expected_from_args(args)
        summary = validate_candidate(
            candidate_root=args.candidate_root,
            handoff_path=args.release_handoff,
            sbom_path=args.sbom,
            provenance_path=args.provenance,
            windows_manifest_path=args.windows_manifest,
            expected=expected,
        )
        payload = asdict(summary)
        if args.output is not None:
            if args.output.exists():
                raise SupplyChainIssue("output_already_exists", "output")
            if not args.output.parent.is_dir():
                raise SupplyChainIssue("output_parent_missing", "output")
            args.output.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        print(json.dumps(payload, sort_keys=True))
        return EXIT_VALID
    except (OSError, SupplyChainIssue) as exc:
        issue = exc if isinstance(exc, SupplyChainIssue) else SupplyChainIssue("io_error", "filesystem")
        print(
            json.dumps(
                {"status": "FAIL", "code": issue.code, "path": issue.path},
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return EXIT_INVALID


if __name__ == "__main__":
    raise SystemExit(main())
