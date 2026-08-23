#!/usr/bin/env python3
"""Build, verify and locally restore one complete commercial revision bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_SCHEMA = "pokrov-commercial-revision-bundle-v1"
BUNDLE_FILES = (
    "shared/product-facts.json",
    "shared/product-facts.ts",
    "shared/tariff-catalog.json",
    "shared/tariff-catalog.ts",
    "shared/commercial-contract.json",
    "shared/commercial-contract.schema.json",
    "shared/commercial-contract.ts",
    "docs/generated/commercial-contract.md",
)
MANIFEST_NAME = "commercial-revision-bundle.json"


class CommercialRevisionBundleError(RuntimeError):
    """Raised when a commercial revision bundle is incomplete or unsafe."""


@dataclass(frozen=True)
class BundleFile:
    """Immutable file record stored in the bundle manifest."""

    path: str
    sha256: str
    size_bytes: int


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            dict(value),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _resolved_repo_root(value: str | Path) -> Path:
    root = Path(value).resolve()
    if not root.is_dir():
        raise CommercialRevisionBundleError("repository_root_missing")
    return root


def _repository_path(root: Path, relative: str) -> Path:
    candidate = (root / PurePosixPath(relative)).resolve()
    if root != candidate and root not in candidate.parents:
        raise CommercialRevisionBundleError("bundle_path_outside_repository")
    return candidate


def _semantic_json_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return _sha256(encoded)


def _commercial_contract(
    contents: Mapping[str, bytes],
    *,
    validate_sources: bool = True,
) -> dict[str, Any]:
    try:
        decoded = json.loads(contents["shared/commercial-contract.json"].decode("utf-8"))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CommercialRevisionBundleError("commercial_contract_invalid") from exc
    if not isinstance(decoded, dict):
        raise CommercialRevisionBundleError("commercial_contract_invalid")
    revision = str(decoded.get("commercial_revision") or "").strip()
    digest = str(decoded.get("contract_sha256") or "").strip().lower()
    if not revision or len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise CommercialRevisionBundleError("commercial_contract_identity_invalid")
    contract_without_digest = dict(decoded)
    contract_without_digest.pop("contract_sha256", None)
    if _semantic_json_digest(contract_without_digest) != digest:
        raise CommercialRevisionBundleError("commercial_contract_digest_mismatch")
    if validate_sources:
        try:
            product_facts = json.loads(contents["shared/product-facts.json"].decode("utf-8"))
            tariff_catalog = json.loads(contents["shared/tariff-catalog.json"].decode("utf-8"))
        except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CommercialRevisionBundleError("commercial_source_invalid") from exc
        source_contracts = decoded.get("source_contracts")
        source_digests = decoded.get("source_sha256")
        if source_contracts != {
            "product_facts": "shared/product-facts.json",
            "tariff_catalog": "shared/tariff-catalog.json",
        } or source_digests != {
            "product_facts": _semantic_json_digest(product_facts),
            "tariff_catalog": _semantic_json_digest(tariff_catalog),
        }:
            raise CommercialRevisionBundleError("commercial_source_digest_mismatch")
        document = contents.get("docs/generated/commercial-contract.md", b"")
        try:
            document_text = document.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CommercialRevisionBundleError("commercial_document_invalid") from exc
        if revision not in document_text or digest not in document_text:
            raise CommercialRevisionBundleError("commercial_document_identity_mismatch")
    return decoded


def _load_repository_files(root: Path) -> dict[str, bytes]:
    contents: dict[str, bytes] = {}
    for relative in BUNDLE_FILES:
        path = _repository_path(root, relative)
        if not path.is_file():
            raise CommercialRevisionBundleError(f"bundle_source_missing:{relative}")
        contents[relative] = path.read_bytes()
    return contents


def _manifest_for(contents: Mapping[str, bytes]) -> dict[str, Any]:
    contract = _commercial_contract(contents)
    files = [
        BundleFile(path=relative, sha256=_sha256(contents[relative]), size_bytes=len(contents[relative]))
        for relative in BUNDLE_FILES
    ]
    return {
        "schema": BUNDLE_SCHEMA,
        "commercial_revision": str(contract["commercial_revision"]),
        "commercial_contract_sha256": str(contract["contract_sha256"]),
        "source_effective_from": str(contract.get("effective_from") or ""),
        "files": [asdict(item) for item in files],
    }


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(filename=name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


def snapshot_bundle(*, repo_root: str | Path, output: str | Path) -> dict[str, Any]:
    """Write a deterministic ZIP containing every file owned by one revision."""

    root = _resolved_repo_root(repo_root)
    destination = Path(output).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    contents = _load_repository_files(root)
    manifest = _manifest_for(contents)
    descriptor: int | None = None
    temporary_name = ""
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=str(destination.parent),
        )
        os.close(descriptor)
        descriptor = None
        with zipfile.ZipFile(
            temporary_name,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            archive.writestr(_zip_info(MANIFEST_NAME), _canonical_json(manifest))
            for relative in BUNDLE_FILES:
                archive.writestr(_zip_info(relative), contents[relative])
        os.replace(temporary_name, destination)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_name and Path(temporary_name).exists():
            Path(temporary_name).unlink()
    return {
        **manifest,
        "bundle_path": str(destination),
        "bundle_sha256": _sha256(destination.read_bytes()),
        "mode": "snapshot",
    }


def _validated_bundle(bundle: str | Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    source = Path(bundle).resolve()
    if not source.is_file():
        raise CommercialRevisionBundleError("bundle_missing")
    try:
        with zipfile.ZipFile(source, mode="r") as archive:
            names = archive.namelist()
            expected_names = [MANIFEST_NAME, *BUNDLE_FILES]
            if names != expected_names or len(set(names)) != len(names):
                raise CommercialRevisionBundleError("bundle_member_set_invalid")
            if any(
                info.is_dir()
                or PurePosixPath(info.filename).is_absolute()
                or ".." in PurePosixPath(info.filename).parts
                for info in archive.infolist()
            ):
                raise CommercialRevisionBundleError("bundle_member_path_invalid")
            manifest_bytes = archive.read(MANIFEST_NAME)
            contents = {relative: archive.read(relative) for relative in BUNDLE_FILES}
    except zipfile.BadZipFile as exc:
        raise CommercialRevisionBundleError("bundle_zip_invalid") from exc
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CommercialRevisionBundleError("bundle_manifest_invalid") from exc
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema",
        "commercial_revision",
        "commercial_contract_sha256",
        "source_effective_from",
        "files",
    }:
        raise CommercialRevisionBundleError("bundle_manifest_shape_invalid")
    if manifest.get("schema") != BUNDLE_SCHEMA:
        raise CommercialRevisionBundleError("bundle_schema_invalid")
    raw_files = manifest.get("files")
    if not isinstance(raw_files, list) or len(raw_files) != len(BUNDLE_FILES):
        raise CommercialRevisionBundleError("bundle_file_manifest_invalid")
    expected_entries = _manifest_for(contents)["files"]
    if raw_files != expected_entries:
        raise CommercialRevisionBundleError("bundle_file_digest_mismatch")
    contract = _commercial_contract(contents)
    if (
        str(manifest.get("commercial_revision") or "")
        != str(contract.get("commercial_revision") or "")
        or str(manifest.get("commercial_contract_sha256") or "")
        != str(contract.get("contract_sha256") or "")
    ):
        raise CommercialRevisionBundleError("bundle_contract_identity_mismatch")
    return manifest, contents


def readback_bundle(*, bundle: str | Path) -> dict[str, Any]:
    """Validate a bundle and return only bounded revision/checksum evidence."""

    source = Path(bundle).resolve()
    manifest, _contents = _validated_bundle(source)
    return {
        **manifest,
        "bundle_path": str(source),
        "bundle_sha256": _sha256(source.read_bytes()),
        "mode": "readback",
        "valid": True,
    }


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor: int | None = None
    temporary_name = ""
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=str(path.parent),
        )
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_name and Path(temporary_name).exists():
            Path(temporary_name).unlink()


def restore_bundle(
    *,
    repo_root: str | Path,
    bundle: str | Path,
    apply: bool = False,
    expect_current_revision: str | None = None,
    expect_bundle_sha256: str | None = None,
) -> dict[str, Any]:
    """Plan or apply a guarded local repository restore from a verified bundle."""

    root = _resolved_repo_root(repo_root)
    source = Path(bundle).resolve()
    manifest, contents = _validated_bundle(source)
    bundle_sha256 = _sha256(source.read_bytes())
    current_contents = _load_repository_files(root)
    current_contract = _commercial_contract(current_contents, validate_sources=False)
    changes = [
        {
            "path": relative,
            "current_sha256": _sha256(current_contents[relative]),
            "bundle_sha256": _sha256(contents[relative]),
            "change": "replace"
            if current_contents[relative] != contents[relative]
            else "unchanged",
        }
        for relative in BUNDLE_FILES
    ]
    result = {
        "schema": BUNDLE_SCHEMA,
        "mode": "apply" if apply else "dry_run",
        "applied": False,
        "current_revision": str(current_contract["commercial_revision"]),
        "target_revision": str(manifest["commercial_revision"]),
        "target_contract_sha256": str(manifest["commercial_contract_sha256"]),
        "bundle_sha256": bundle_sha256,
        "changed_file_count": sum(item["change"] == "replace" for item in changes),
        "files": changes,
    }
    if not apply:
        return result
    if not expect_current_revision or expect_current_revision != result["current_revision"]:
        raise CommercialRevisionBundleError("current_revision_guard_mismatch")
    if not expect_bundle_sha256 or expect_bundle_sha256.lower() != bundle_sha256:
        raise CommercialRevisionBundleError("bundle_sha256_guard_mismatch")

    backups = dict(current_contents)
    replaced: list[str] = []
    try:
        for relative in BUNDLE_FILES:
            if current_contents[relative] == contents[relative]:
                continue
            _atomic_write(_repository_path(root, relative), contents[relative])
            replaced.append(relative)
        verified = _load_repository_files(root)
        if any(verified[relative] != contents[relative] for relative in BUNDLE_FILES):
            raise CommercialRevisionBundleError("restore_readback_mismatch")
    except Exception:
        for relative in reversed(replaced):
            _atomic_write(_repository_path(root, relative), backups[relative])
        raise
    result["applied"] = True
    result["restored_file_count"] = len(replaced)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot = subparsers.add_parser("snapshot")
    snapshot.add_argument("--output", required=True)

    readback = subparsers.add_parser("readback")
    readback.add_argument("--bundle", required=True)

    restore = subparsers.add_parser("restore")
    restore.add_argument("--bundle", required=True)
    restore.add_argument("--apply", action="store_true")
    restore.add_argument("--expect-current-revision")
    restore.add_argument("--expect-bundle-sha256")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Execute the snapshot, readback or guarded restore command."""

    args = _parser().parse_args(argv)
    try:
        if args.command == "snapshot":
            result = snapshot_bundle(repo_root=args.repo_root, output=args.output)
        elif args.command == "readback":
            result = readback_bundle(bundle=args.bundle)
        else:
            result = restore_bundle(
                repo_root=args.repo_root,
                bundle=args.bundle,
                apply=bool(args.apply),
                expect_current_revision=args.expect_current_revision,
                expect_bundle_sha256=args.expect_bundle_sha256,
            )
    except CommercialRevisionBundleError as exc:
        print(
            json.dumps(
                {"ok": False, "error_code": str(exc)},
                ensure_ascii=True,
                separators=(",", ":"),
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps({"ok": True, **result}, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
