from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate_release_candidate_supply_chain.py"
HANDOFF_SCRIPT_PATH = REPO_ROOT / "scripts" / "validate_release_handoff_metadata.py"


def _load_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "validate_release_candidate_supply_chain",
        SCRIPT_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


validator = _load_module()


def _load_handoff_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "validate_release_handoff_metadata_for_supply_tests",
        HANDOFF_SCRIPT_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


handoff_validator = _load_handoff_module()

PLATFORM = "a" * 40
CLIENT = "b" * 40
CORE = "c" * 40
RELEASE_INDEX = "d" * 40
CANDIDATE_ID = "pokrov-1.2.0-candidate.7"
PACKAGE_VERSION = "1.2.0+4046"


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> str:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return _digest(path.read_bytes())


def _component(
    *,
    name: str,
    reference: str,
    digest: str | None = None,
    size: int | None = None,
    properties: dict[str, str] | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {"type": "file", "name": name, "bom-ref": reference}
    if digest is not None:
        value["hashes"] = [{"alg": "SHA-256", "content": digest}]
    combined = dict(properties or {})
    if size is not None:
        combined["pokrov:size-bytes"] = str(size)
    if combined:
        value["properties"] = [
            {"name": key, "value": property_value}
            for key, property_value in combined.items()
        ]
    return value


def _fixture(tmp_path: Path) -> dict[str, Any]:
    artifact_specs = [
        ("pokrov-android-market.aab", "android", "aab", "universal"),
        ("pokrov-android-arm64-v8a.apk", "android", "apk", "arm64-v8a"),
        ("pokrov-android-armeabi-v7a.apk", "android", "apk", "armeabi-v7a"),
        ("pokrov-android-universal.apk", "android", "apk", "universal"),
        ("pokrov-android-x86_64.apk", "android", "apk", "x86_64"),
        ("pokrov-windows-setup-x64.exe", "windows", "exe", "x64"),
    ]
    artifact_data = {
        name: f"exact:{name}".encode() for name, _, _, _ in artifact_specs
    }
    artifact_digests = {
        name: _digest(data) for name, data in artifact_data.items()
    }
    runtime_bytes = b"exact-runtime"
    runtime_digest = _digest(runtime_bytes)
    android_core = "1" * 64
    windows_core = runtime_digest
    artifact_records = {
        name: {
            "platform": platform,
            "kind": kind,
            "architecture": architecture,
            "file_name": name,
            "size_bytes": len(artifact_data[name]),
            "sha256": artifact_digests[name],
            "core_abi": None if platform == "android" else 2,
            "core_artifact_sha256": (
                android_core if platform == "android" else windows_core
            ),
        }
        for name, platform, kind, architecture in artifact_specs
    }
    artifact_set_sha256 = validator._canonical_artifact_set_sha256(
        artifact_records
    )
    for name, data in artifact_data.items():
        (tmp_path / name).write_bytes(data)

    windows_manifest = {
        "version": PACKAGE_VERSION,
        "installer_sha256": artifact_digests["pokrov-windows-setup-x64.exe"],
        "required_files": [
            {
                "path": "pokrov-core.dll",
                "size_bytes": len(runtime_bytes),
                "sha256": runtime_digest,
            }
        ],
    }
    windows_manifest_path = tmp_path / "windows-manifest.json"
    _write_json(windows_manifest_path, windows_manifest)

    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "name": "POKROV 1.2.0 candidate 7",
                "version": PACKAGE_VERSION,
                "bom-ref": "pkg:generic/pokrov-release-candidate@1.2.0%2B4046?candidate=7",
                "properties": [
                    {"name": "pokrov:candidate-id", "value": CANDIDATE_ID},
                    {
                        "name": "pokrov:artifact-set-sha256",
                        "value": artifact_set_sha256,
                    },
                    {"name": "pokrov:platform-commit", "value": PLATFORM},
                    {"name": "pokrov:client-commit", "value": CLIENT},
                    {"name": "pokrov:core-commit", "value": CORE},
                ],
            }
        },
        "components": [
            *[
                _component(
                    name=name,
                    reference=f"file:{name}",
                    digest=artifact_digests[name],
                    size=len(artifact_data[name]),
                    properties={"pokrov:candidate-id": CANDIDATE_ID},
                )
                for name, _, _, _ in artifact_specs
            ],
            _component(
                name="POKROV client",
                reference="client",
                properties={"pokrov:git-commit": CLIENT},
            ),
            _component(
                name="POKROV Core",
                reference="core",
                properties={
                    "pokrov:git-commit": CORE,
                    "pokrov:android-aar-sha256": android_core,
                    "pokrov:windows-dll-sha256": windows_core,
                },
            ),
            _component(
                name="pokrov-core.dll",
                reference="windows-runtime:pokrov-core.dll",
                digest=runtime_digest,
                size=len(runtime_bytes),
            ),
        ],
    }
    sbom_path = tmp_path / "candidate7.cdx.json"
    sbom_digest = _write_json(sbom_path, sbom)

    provenance = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [
            {
                "name": name,
                "digest": {"sha256": artifact_digests[name]},
            }
            for name, _, _, _ in artifact_specs
        ],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": "https://pokrov.space/build-types/client-release/v1",
                "externalParameters": {
                    "candidate_id": CANDIDATE_ID,
                    "product_version": PACKAGE_VERSION,
                },
                "resolvedDependencies": [
                    {"uri": f"git+https://github.com/Kiwunaka/portal@{PLATFORM}"},
                    {"uri": f"git+https://github.com/Kiwunaka/POKROV-app@{CLIENT}"},
                    {"uri": f"git+https://github.com/Kiwunaka/pokrov-core@{CORE}"},
                    {"uri": f"git+https://github.com/Kiwunaka/pokrov@{RELEASE_INDEX}"},
                ],
            },
            "runDetails": {
                "metadata": {
                    "invocationId": f"{CANDIDATE_ID}/{artifact_set_sha256}"
                },
                "byproducts": [
                    {"name": sbom_path.name, "digest": {"sha256": sbom_digest}}
                ]
            },
        },
    }
    provenance_path = tmp_path / "candidate7.provenance.json"
    provenance_digest = _write_json(provenance_path, provenance)

    handoff = {
        "schema_version": 2,
        "release": {"version": "1.2.0"},
        "sources": {
            "platform": {"repository": "Kiwunaka/portal", "revision": PLATFORM},
            "client": {"repository": "Kiwunaka/POKROV-app", "revision": CLIENT},
            "core": {"repository": "Kiwunaka/pokrov-core", "revision": CORE},
            "release_index": {
                "repository": "Kiwunaka/pokrov",
                "revision": RELEASE_INDEX,
            },
        },
        "artifacts": [
            {
                **artifact_records[name],
                "source_revision": CLIENT,
                "sbom": {"status": "PASS", "sha256": sbom_digest},
                "provenance": {"status": "PASS", "sha256": provenance_digest},
            }
            for name, platform, kind, architecture in artifact_specs
        ],
        "promotion": {
            "source_artifact_set_sha256": artifact_set_sha256,
        },
    }
    handoff_path = tmp_path / "release-handoff.json"
    _write_json(handoff_path, handoff)
    return {
        "root": tmp_path,
        "handoff_path": handoff_path,
        "handoff": handoff,
        "sbom_path": sbom_path,
        "sbom": sbom,
        "provenance_path": provenance_path,
        "provenance": provenance,
        "windows_manifest_path": windows_manifest_path,
        "windows_manifest": windows_manifest,
        "android_core": android_core,
        "windows_core": windows_core,
    }


def _expected() -> Any:
    return validator.ExpectedIdentity(
        candidate_id=CANDIDATE_ID,
        product_version="1.2.0",
        package_version=PACKAGE_VERSION,
        platform_revision=PLATFORM,
        client_revision=CLIENT,
        core_revision=CORE,
        release_index_revision=RELEASE_INDEX,
        android_core_artifact_sha256="1" * 64,
        windows_core_artifact_sha256=_digest(b"exact-runtime"),
    )


def _validate(fixture: dict[str, Any]) -> Any:
    return validator.validate_candidate(
        candidate_root=fixture["root"],
        handoff_path=fixture["handoff_path"],
        sbom_path=fixture["sbom_path"],
        provenance_path=fixture["provenance_path"],
        windows_manifest_path=fixture["windows_manifest_path"],
        expected=_expected(),
    )


def _rewrite_supply_refs(fixture: dict[str, Any]) -> None:
    sbom_digest = _write_json(fixture["sbom_path"], fixture["sbom"])
    byproduct = fixture["provenance"]["predicate"]["runDetails"]["byproducts"][0]
    byproduct["digest"]["sha256"] = sbom_digest
    provenance_digest = _write_json(
        fixture["provenance_path"],
        fixture["provenance"],
    )
    for artifact in fixture["handoff"]["artifacts"]:
        artifact["sbom"]["sha256"] = sbom_digest
        artifact["provenance"]["sha256"] = provenance_digest
    _write_json(fixture["handoff_path"], fixture["handoff"])


def test_exact_candidate_supply_chain_passes(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)

    summary = _validate(fixture)

    assert summary.status == "PASS"
    assert summary.artifact_count == 6
    assert summary.windows_runtime_file_count == 1
    assert summary.source_revisions["platform"] == PLATFORM


def test_artifact_set_digest_matches_release_handoff_authority(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    artifacts = fixture["handoff"]["artifacts"]
    by_name = {artifact["file_name"]: artifact for artifact in artifacts}
    descriptors = [
        {
            key: artifact[key]
            for key in (
                "architecture",
                "core_abi",
                "core_artifact_sha256",
                "file_name",
                "kind",
                "platform",
                "sha256",
                "size_bytes",
            )
        }
        for artifact in artifacts
    ]

    assert validator._canonical_artifact_set_sha256(by_name) == (
        handoff_validator.compute_artifact_set_sha256(descriptors)
    )


def test_stale_handoff_artifact_set_digest_fails_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fixture["handoff"]["promotion"]["source_artifact_set_sha256"] = "0" * 64
    _write_json(fixture["handoff_path"], fixture["handoff"])

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == "handoff_artifact_set_digest_mismatch"


def test_changed_candidate_artifact_fails_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    (tmp_path / "pokrov-android-arm64-v8a.apk").write_bytes(b"changed-android")

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code in {"artifact_size_mismatch", "artifact_sha256_mismatch"}


def test_incomplete_exact_artifact_set_fails_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    omitted = "pokrov-android-x86_64.apk"
    fixture["handoff"]["artifacts"] = [
        item for item in fixture["handoff"]["artifacts"] if item["file_name"] != omitted
    ]
    fixture["sbom"]["components"] = [
        item
        for item in fixture["sbom"]["components"]
        if item["bom-ref"] != f"file:{omitted}"
    ]
    fixture["provenance"]["subject"] = [
        item for item in fixture["provenance"]["subject"] if item["name"] != omitted
    ]
    _rewrite_supply_refs(fixture)

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == "artifact_set_mismatch"


def test_wrong_artifact_descriptor_fails_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fixture["handoff"]["artifacts"][0]["architecture"] = "x64"
    _write_json(fixture["handoff_path"], fixture["handoff"])

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == "artifact_descriptor_mismatch"


def test_stale_sbom_artifact_digest_fails_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fixture["sbom"]["components"][0]["hashes"][0]["content"] = "0" * 64
    _rewrite_supply_refs(fixture)

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == "sbom_artifact_digest_mismatch"


def test_stale_sbom_windows_runtime_digest_fails_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    runtime = next(
        item
        for item in fixture["sbom"]["components"]
        if item["bom-ref"] == "windows-runtime:pokrov-core.dll"
    )
    runtime["hashes"][0]["content"] = "0" * 64
    _rewrite_supply_refs(fixture)

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == "sbom_windows_runtime_digest_mismatch"


def test_stale_sbom_source_revision_fails_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    client = next(
        item for item in fixture["sbom"]["components"] if item["name"] == "POKROV client"
    )
    client["properties"][0]["value"] = "e" * 40
    _rewrite_supply_refs(fixture)

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == "sbom_source_revision_mismatch"


def test_extra_sbom_artifact_component_fails_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fixture["sbom"]["components"].append(
        _component(
            name="stale.apk",
            reference="file:stale.apk",
            digest="0" * 64,
            size=1,
            properties={"pokrov:candidate-id": CANDIDATE_ID},
        )
    )
    _rewrite_supply_refs(fixture)

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == "sbom_artifact_set_mismatch"


def test_extra_sbom_windows_runtime_component_fails_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fixture["sbom"]["components"].append(
        _component(
            name="stale.dll",
            reference="windows-runtime:stale.dll",
            digest="0" * 64,
            size=1,
        )
    )
    _rewrite_supply_refs(fixture)

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == "sbom_windows_runtime_set_mismatch"


def test_self_referential_core_digests_fail_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fake_android = "8" * 64
    fake_windows = "9" * 64
    for artifact in fixture["handoff"]["artifacts"]:
        artifact["core_artifact_sha256"] = (
            fake_android if artifact["platform"] == "android" else fake_windows
        )
    core = next(
        item for item in fixture["sbom"]["components"] if item["name"] == "POKROV Core"
    )
    properties = {item["name"]: item for item in core["properties"]}
    properties["pokrov:android-aar-sha256"]["value"] = fake_android
    properties["pokrov:windows-dll-sha256"]["value"] = fake_windows
    _rewrite_supply_refs(fixture)

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == "artifact_core_digest_mismatch"


def test_unrelated_duplicate_component_names_are_allowed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fixture["sbom"]["components"].extend(
        [
            _component(
                name="example.invalid/dependency",
                reference="pkg:generic/dependency@1",
            ),
            _component(
                name="example.invalid/dependency",
                reference="pkg:generic/dependency@2",
            ),
        ]
    )
    _rewrite_supply_refs(fixture)

    summary = _validate(fixture)

    assert summary.status == "PASS"


def test_duplicate_sbom_bom_ref_fails_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    duplicate = dict(fixture["sbom"]["components"][0])
    duplicate["name"] = "different-name"
    fixture["sbom"]["components"].append(duplicate)
    _rewrite_supply_refs(fixture)

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == "duplicate_sbom_bom_ref"


def test_duplicate_sbom_source_component_fails_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    duplicate = dict(
        next(
            item
            for item in fixture["sbom"]["components"]
            if item["name"] == "POKROV client"
        )
    )
    duplicate["bom-ref"] = "git:client-copy"
    fixture["sbom"]["components"].append(duplicate)
    _rewrite_supply_refs(fixture)

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == "duplicate_sbom_source_component"


def test_stale_sbom_root_bom_ref_fails_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fixture["sbom"]["metadata"]["component"]["bom-ref"] = (
        "pkg:generic/pokrov-release-candidate@1.2.0%2B4046?candidate=6"
    )
    _rewrite_supply_refs(fixture)

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == "sbom_root_bom_ref_mismatch"


def test_stale_sbom_artifact_set_property_fails_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    properties = fixture["sbom"]["metadata"]["component"]["properties"]
    next(
        item for item in properties if item["name"] == "pokrov:artifact-set-sha256"
    )["value"] = "0" * 64
    _rewrite_supply_refs(fixture)

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == "sbom_artifact_set_digest_mismatch"


def test_stale_provenance_subject_fails_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fixture["provenance"]["subject"][0]["digest"]["sha256"] = "0" * 64
    _rewrite_supply_refs(fixture)

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == "provenance_subject_set_mismatch"


def test_stale_provenance_source_revision_fails_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fixture["provenance"]["predicate"]["buildDefinition"]["resolvedDependencies"][0][
        "uri"
    ] = f"git+https://github.com/Kiwunaka/portal@{'e' * 40}"
    _rewrite_supply_refs(fixture)

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == "provenance_source_revision_mismatch"


def test_stale_provenance_invocation_artifact_set_fails_closed(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    fixture["provenance"]["predicate"]["runDetails"]["metadata"][
        "invocationId"
    ] = f"{CANDIDATE_ID}/{'0' * 64}"
    _rewrite_supply_refs(fixture)

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == "provenance_invocation_artifact_set_mismatch"


def test_stale_provenance_internal_candidate_reference_fails_closed(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    fixture["provenance"]["predicate"]["buildDefinition"][
        "internalParameters"
    ] = {
        "client_hosted_ci_run": "NOT_RUN_EXACT_CANDIDATE6",
    }
    _rewrite_supply_refs(fixture)

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == "provenance_internal_candidate_reference_mismatch"


def test_extra_provenance_source_fails_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fixture["provenance"]["predicate"]["buildDefinition"][
        "resolvedDependencies"
    ].append({"uri": f"git+https://github.com/example/stale@{'e' * 40}"})
    _rewrite_supply_refs(fixture)

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == "provenance_source_revision_mismatch"


def test_wrong_release_handoff_schema_fails_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fixture["handoff"]["schema_version"] = 1
    _write_json(fixture["handoff_path"], fixture["handoff"])

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == "release_handoff_schema_mismatch"


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("bomFormat", "NotCycloneDX", "sbom_format_mismatch"),
        ("specVersion", "1.4", "sbom_spec_version_mismatch"),
    ],
)
def test_wrong_sbom_identity_fails_closed(
    tmp_path: Path,
    field: str,
    value: str,
    code: str,
) -> None:
    fixture = _fixture(tmp_path)
    fixture["sbom"][field] = value
    _rewrite_supply_refs(fixture)

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == code


@pytest.mark.parametrize(
    ("path", "value", "code"),
    [
        (("_type",), "not-in-toto", "provenance_type_mismatch"),
        (("predicateType",), "not-slsa", "provenance_predicate_type_mismatch"),
        (
            ("predicate", "buildDefinition", "buildType"),
            "unknown",
            "provenance_build_type_mismatch",
        ),
    ],
)
def test_wrong_provenance_identity_fails_closed(
    tmp_path: Path,
    path: tuple[str, ...],
    value: str,
    code: str,
) -> None:
    fixture = _fixture(tmp_path)
    target = fixture["provenance"]
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    _rewrite_supply_refs(fixture)

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == code


def test_handoff_supply_digest_mismatch_fails_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fixture["handoff"]["artifacts"][0]["sbom"]["sha256"] = "0" * 64
    _write_json(fixture["handoff_path"], fixture["handoff"])

    with pytest.raises(validator.SupplyChainIssue) as exc:
        _validate(fixture)

    assert exc.value.code == "sbom_digest_set_mismatch"


def test_cli_writes_secret_free_normalized_report(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    output = tmp_path / "report.json"

    result = validator.main(
        [
            "--candidate-root",
            str(tmp_path),
            "--release-handoff",
            str(fixture["handoff_path"]),
            "--sbom",
            str(fixture["sbom_path"]),
            "--provenance",
            str(fixture["provenance_path"]),
            "--windows-manifest",
            str(fixture["windows_manifest_path"]),
            "--candidate-id",
            CANDIDATE_ID,
            "--product-version",
            "1.2.0",
            "--package-version",
            PACKAGE_VERSION,
            "--platform-revision",
            PLATFORM,
            "--client-revision",
            CLIENT,
            "--core-revision",
            CORE,
            "--release-index-revision",
            RELEASE_INDEX,
            "--android-core-artifact-sha256",
            fixture["android_core"],
            "--windows-core-artifact-sha256",
            fixture["windows_core"],
            "--output",
            str(output),
        ]
    )

    assert result == validator.EXIT_VALID
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    assert set(report) == {
        "artifact_count",
        "candidate_id",
        "provenance_sha256",
        "release_handoff_sha256",
        "sbom_sha256",
        "source_revisions",
        "status",
        "windows_manifest_sha256",
        "windows_runtime_file_count",
    }
