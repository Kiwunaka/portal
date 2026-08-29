"""Prove the PB-14 health-stop control against one exact signed candidate.

The command is deliberately local-only. It verifies the retained detached
release-index signature against the public keyring at the manifest-bound
release-index revision, then exercises the real rollout action-intent and
release-health services in an isolated temporary SQLite database. It never
publishes assets, changes a stable pointer, or mutates a deployed runtime.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any, Mapping
import uuid

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))

import migrations  # noqa: E402
import models  # noqa: E402
from admin_action_intent_service import (  # noqa: E402
    ActionIntentError,
    confirmation_sha256,
    execute_action_intent,
    prepare_action_intent,
)
from operator_release_service import (  # noqa: E402
    RELEASE_ROLLOUT_SETTING_KEY,
    load_release_rollout_registry,
    public_client_rollout_policy,
    rollout_state,
)
from operator_work_service import add_admin_audit  # noqa: E402
from release_evidence_service import canonical_json, compute_candidate_id  # noqa: E402


EVIDENCE_ROOT = (
    REPO_ROOT
    / "docs/developer/work-orders/2026-08-21--release-1.2.0-megaplan"
    / "evidence/013Y-signed-candidate-manifest"
)
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
GIT_REVISION_RE = re.compile(r"[0-9a-f]{40}\Z")
PACKAGE_VERSION_RE = re.compile(
    r"(?P<version>[0-9]+\.[0-9]+\.[0-9]+)\+(?P<build>[1-9][0-9]*)\Z"
)
ACTOR_TG_ID = 1200


class Pb14GateError(RuntimeError):
    """The retained candidate or isolated PB-14 control is invalid."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _iso(value: datetime) -> str:
    return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_json_bytes(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Pb14GateError(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise Pb14GateError(f"JSON root must be an object: {path}")
    return value, raw


def _signed_android_build_number(
    signed_evidence: Mapping[str, Any], product_version: str
) -> str:
    install = signed_evidence.get("physical_phone_install_binding")
    if not isinstance(install, Mapping) or install.get("arm64_artifact_sha256_match") is not True:
        raise Pb14GateError("exact installed Android build identity is absent")
    package_version = str(install.get("package_version") or "")
    match = PACKAGE_VERSION_RE.fullmatch(package_version)
    if match is None or match.group("version") != product_version:
        raise Pb14GateError("installed Android package version does not match candidate")
    return match.group("build")


def _git_keyring(release_index_root: Path, revision: str) -> dict[str, Any]:
    if GIT_REVISION_RE.fullmatch(revision) is None:
        raise Pb14GateError("release-index revision is invalid")
    result = subprocess.run(
        [
            "git",
            "show",
            f"{revision}:trusted/release-signing-keys.json",
        ],
        cwd=release_index_root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise Pb14GateError("manifest-bound release-index keyring is unavailable")
    try:
        value = json.loads(result.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Pb14GateError("manifest-bound release-index keyring is invalid") from exc
    if not isinstance(value, dict):
        raise Pb14GateError("manifest-bound release-index keyring must be an object")
    return value


def _verify_detached_signature(
    *,
    manifest_bytes: bytes,
    signature_bytes: bytes,
    keyring: Mapping[str, Any],
    key_id: str,
) -> dict[str, str]:
    if keyring.get("schema") != "pokrov.release-index.keyring/v1":
        raise Pb14GateError("release-index keyring schema is invalid")
    selected = None
    for item in keyring.get("keys") or []:
        if isinstance(item, Mapping) and str(item.get("id") or "") == key_id:
            selected = dict(item)
            break
    if selected is None:
        raise Pb14GateError("signing key is absent from the manifest-bound keyring")
    if selected.get("state") != "active" or selected.get("algorithm") != "ed25519":
        raise Pb14GateError("signing key is not an active Ed25519 key")
    try:
        public_key = base64.b64decode(
            str(selected.get("public_key_base64") or ""), validate=True
        )
    except (ValueError, TypeError) as exc:
        raise Pb14GateError("signing public key encoding is invalid") from exc
    if len(public_key) != 32 or len(signature_bytes) != 64:
        raise Pb14GateError("Ed25519 key or signature size is invalid")
    public_key_sha256 = _sha256_bytes(public_key)
    declared_key_sha256 = str(selected.get("public_key_sha256") or "").lower()
    if declared_key_sha256 != public_key_sha256:
        raise Pb14GateError("signing public key hash mismatch")
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(
            signature_bytes, manifest_bytes
        )
    except (ValueError, InvalidSignature) as exc:
        raise Pb14GateError("detached candidate signature verification failed") from exc
    return {
        "status": "PASS",
        "algorithm": "ed25519",
        "key_id": key_id,
        "public_key_sha256": public_key_sha256,
    }


def _output_record(evidence: Mapping[str, Any], filename: str) -> Mapping[str, Any]:
    for item in evidence.get("outputs") or []:
        if (
            isinstance(item, Mapping)
            and Path(str(item.get("path") or "")).name == filename
        ):
            return item
    raise Pb14GateError(f"signed-candidate evidence lacks {filename}")


def _validate_retained_candidate(
    *,
    manifest_path: Path,
    signature_path: Path,
    receipt_path: Path,
    signed_evidence_path: Path,
    release_index_root: Path,
) -> dict[str, Any]:
    manifest, manifest_bytes = _read_json_bytes(manifest_path)
    receipt, receipt_bytes = _read_json_bytes(receipt_path)
    signed_evidence, _ = _read_json_bytes(signed_evidence_path)
    signature_bytes = signature_path.read_bytes()

    actual = {
        manifest_path.name: {
            "sha256": _sha256_bytes(manifest_bytes),
            "size": len(manifest_bytes),
        },
        signature_path.name: {
            "sha256": _sha256_bytes(signature_bytes),
            "size": len(signature_bytes),
        },
        receipt_path.name: {
            "sha256": _sha256_bytes(receipt_bytes),
            "size": len(receipt_bytes),
        },
    }
    for filename, values in actual.items():
        retained = _output_record(signed_evidence, filename)
        if (
            str(retained.get("sha256") or "").lower() != values["sha256"]
            or int(retained.get("size_bytes") or -1) != values["size"]
        ):
            raise Pb14GateError(f"retained signed-candidate output drift: {filename}")

    if receipt.get("schema") != "pokrov.release-index.signing-receipt/v1":
        raise Pb14GateError("signing receipt schema is invalid")
    if manifest.get("schema") != "pokrov.release-index.manifest/v2":
        raise Pb14GateError("candidate manifest schema is invalid")
    if manifest.get("candidate_created") is not True:
        raise Pb14GateError("candidate manifest is not created")
    if manifest.get("promotion_authorized") is not False:
        raise Pb14GateError("PB-14 local gate refuses a promotion-authorized manifest")
    candidate_label = str(manifest.get("candidate_id") or "")
    if candidate_label != str(receipt.get("candidate_id") or ""):
        raise Pb14GateError("candidate label does not match the signing receipt")
    if (
        str(receipt.get("manifest_sha256") or "").lower()
        != actual[manifest_path.name]["sha256"]
    ):
        raise Pb14GateError("signing receipt manifest hash mismatch")
    if (
        str(receipt.get("signature_sha256") or "").lower()
        != actual[signature_path.name]["sha256"]
    ):
        raise Pb14GateError("signing receipt signature hash mismatch")

    independent = signed_evidence.get("independent_validation")
    if not isinstance(independent, Mapping):
        raise Pb14GateError("independent signed-candidate validation is absent")
    if (
        independent.get("status") != "READY_SIGNED_MANIFEST"
        or independent.get("receipt_matches_outputs") is not True
        or independent.get("detached_signature_verified_with_public_keyring")
        is not True
    ):
        raise Pb14GateError("retained independent signature validation did not pass")

    sources = manifest.get("sources")
    product = manifest.get("product")
    promotion = manifest.get("promotion")
    artifacts = manifest.get("artifacts")
    if not all(
        isinstance(value, Mapping) for value in (sources, product, promotion)
    ) or not isinstance(artifacts, list):
        raise Pb14GateError("candidate manifest structure is incomplete")
    release_source = sources.get("release_index")
    client_source = sources.get("client")
    if not isinstance(release_source, Mapping) or not isinstance(
        client_source, Mapping
    ):
        raise Pb14GateError("candidate source tuple is incomplete")
    release_revision = str(release_source.get("commit") or "").lower()
    client_revision = str(client_source.get("commit") or "").lower()
    if GIT_REVISION_RE.fullmatch(client_revision) is None:
        raise Pb14GateError("candidate client revision is invalid")
    if release_revision != str(receipt.get("release_index_commit") or "").lower():
        raise Pb14GateError("candidate release-index revision drift")

    key_id = str(receipt.get("signing_key_id") or "")
    keyring = _git_keyring(release_index_root, release_revision)
    signature = _verify_detached_signature(
        manifest_bytes=manifest_bytes,
        signature_bytes=signature_bytes,
        keyring=keyring,
        key_id=key_id,
    )

    x86_artifact = next(
        (
            dict(item)
            for item in artifacts
            if isinstance(item, Mapping) and item.get("id") == "android-x86-64"
        ),
        None,
    )
    if (
        x86_artifact is None
        or SHA256_RE.fullmatch(str(x86_artifact.get("sha256") or "").lower()) is None
    ):
        raise Pb14GateError("candidate Android x86_64 artifact binding is absent")

    version = str(product.get("version") or "")
    rollback_target = str(promotion.get("rollback_target") or "")
    if version != "1.2.0" or not rollback_target:
        raise Pb14GateError("candidate product or rollback target is invalid")
    android_build_number = _signed_android_build_number(signed_evidence, version)
    descriptor = {
        "component": "client",
        "version": version,
        "revision": client_revision,
        "artifact_sha256": actual[manifest_path.name]["sha256"],
    }
    return {
        "candidate_label": candidate_label,
        "candidate_id": compute_candidate_id(descriptor),
        "candidate_descriptor": descriptor,
        "manifest_sha256": actual[manifest_path.name]["sha256"],
        "signature_sha256": actual[signature_path.name]["sha256"],
        "signing": signature,
        "release_index_revision": release_revision,
        "client_revision": client_revision,
        "core_version": str(
            (manifest.get("compatibility") or {}).get("core_version") or ""
        ),
        "android_x86_64_sha256": str(x86_artifact["sha256"]).lower(),
        "android_build_number": android_build_number,
        "version": version,
        "rollback_target": rollback_target,
    }


def _candidate_row(
    *, descriptor: Mapping[str, str], candidate_id: str, now: datetime
) -> models.ReleaseCandidate:
    canonical = canonical_json(dict(descriptor))
    descriptor_sha256 = _sha256_bytes(canonical.encode("utf-8"))
    if candidate_id != descriptor_sha256:
        raise Pb14GateError("candidate descriptor id mismatch")
    return models.ReleaseCandidate(
        candidate_id=candidate_id,
        component=str(descriptor["component"]),
        version=str(descriptor["version"]),
        revision=str(descriptor["revision"]),
        artifact_sha256=str(descriptor["artifact_sha256"]),
        canonical_descriptor_json=canonical,
        descriptor_sha256=descriptor_sha256,
        ingest_key_id="pb14-local-control-fixture",
        imported_at=now,
    )


def _action_payload(platform: str, **values: Any) -> dict[str, Any]:
    return {
        "_environment": "isolated-local-pb14",
        "_operator_id": "pb14-local-control",
        "_actor_tg_id": ACTOR_TG_ID,
        "platform": platform,
        **values,
    }


def _prepare_action(
    session_factory,
    *,
    action: str,
    candidate_id: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    session = session_factory()
    try:
        result = prepare_action_intent(
            session=session,
            actor_tg_id=ACTOR_TG_ID,
            action=action,
            target={"type": "release_candidate", "id": candidate_id},
            payload=dict(payload),
        )
        session.commit()
        return result
    finally:
        session.close()


def _execute_action(
    session_factory,
    *,
    prepared: Mapping[str, Any],
    action: str,
    candidate_id: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    return asyncio.run(
        execute_action_intent(
            session_factory=session_factory,
            actor_tg_id=ACTOR_TG_ID,
            intent_id=str(prepared["intent_id"]),
            idempotency_key=str(uuid.uuid4()),
            confirmation_sha256_header=confirmation_sha256(
                str(prepared["confirmation_challenge"])
            ),
            action=action,
            target={"type": "release_candidate", "id": candidate_id},
            payload=dict(payload),
            audit_writer=add_admin_audit,
        )
    )


def _run_isolated_control(
    binding: Mapping[str, Any], *, now: datetime | None = None
) -> dict[str, Any]:
    current = now or _utcnow()
    exact_descriptor = dict(binding["candidate_descriptor"])
    exact_candidate_id = str(binding["candidate_id"])
    rollback_target = str(binding["rollback_target"])
    rollback_descriptor = {
        "component": "client",
        "version": rollback_target,
        "revision": f"retained-fixture-{rollback_target}",
        "artifact_sha256": _sha256_bytes(
            f"pb14-local-retained-control:{rollback_target}".encode("utf-8")
        ),
    }
    rollback_candidate_id = compute_candidate_id(rollback_descriptor)

    with tempfile.TemporaryDirectory(prefix="pokrov-pb14-") as directory:
        database_path = Path(directory) / "pb14.db"
        engine = create_engine(f"sqlite:///{database_path.as_posix()}")
        factory = sessionmaker(bind=engine, expire_on_commit=False)
        try:
            models.Base.metadata.create_all(engine)
            migrations.run_migrations(engine)
            session = factory()
            try:
                session.add_all(
                    [
                        _candidate_row(
                            descriptor=exact_descriptor,
                            candidate_id=exact_candidate_id,
                            now=current,
                        ),
                        _candidate_row(
                            descriptor=rollback_descriptor,
                            candidate_id=rollback_candidate_id,
                            now=current,
                        ),
                    ]
                )
                observation_started = current - timedelta(hours=2)
                observation_ended = current - timedelta(minutes=1)
                registry = {
                    "schema_version": 1,
                    "active_by_platform": {"android": exact_candidate_id},
                    "states": {
                        f"android:{rollback_candidate_id}": {
                            "candidate_id": rollback_candidate_id,
                            "candidate_version": rollback_target,
                            "platform": "android",
                            "status": "current",
                            "rollout_percent": 100,
                            "paused": False,
                        },
                        f"android:{exact_candidate_id}": {
                            "candidate_id": exact_candidate_id,
                            "candidate_version": str(binding["version"]),
                            "platform": "android",
                            "status": "staged",
                            "rollout_percent": 10,
                            "paused": False,
                            "observation_hours": 1,
                            "observation_started_at": _iso(observation_started),
                            "observation_ends_at": _iso(observation_ended),
                            "thresholds": {
                                "crash_failures": 0,
                                "connect_failures": 0,
                                "update_failures": 0,
                            },
                        },
                    },
                    "history": [],
                }
                session.add(
                    models.AppSetting(
                        key=RELEASE_ROLLOUT_SETTING_KEY,
                        value_json=canonical_json(registry),
                        updated_at=current,
                    )
                )
                event_id = str(
                    uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        f"pokrov:pb14:{binding['manifest_sha256']}:update-failure",
                    )
                )
                session.add(
                    models.ReleaseHealthEvent(
                        schema_version=1,
                        event_id=event_id,
                        occurred_at=current,
                        received_at=current,
                        component="client",
                        subsystem="update",
                        stage="verification",
                        event_name="update.failed",
                        severity="error",
                        outcome="failed",
                        app_version=str(binding["version"]),
                        build_number=str(binding["android_build_number"]),
                        channel="candidate",
                        candidate_label=str(binding["candidate_label"]),
                        git_revision=str(binding["client_revision"]),
                        core_version=str(binding["core_version"]),
                        core_abi=2,
                        platform="android",
                        architecture="x86_64",
                        error_code="UPD-004",
                        error_origin="client",
                    )
                )
                session.commit()
            finally:
                session.close()

            close_payload = _action_payload("android")
            close_error = None
            try:
                _prepare_action(
                    factory,
                    action="release.observation.close",
                    candidate_id=exact_candidate_id,
                    payload=close_payload,
                )
            except ActionIntentError as exc:
                close_error = str(exc.code)
            if close_error != "release_health_gate_failed":
                raise Pb14GateError(
                    "exact-candidate health breach did not stop observation close"
                )

            session = factory()
            try:
                _, retained_registry = load_release_rollout_registry(session)
                retained = rollout_state(
                    retained_registry,
                    candidate_id=exact_candidate_id,
                    platform="android",
                )
            finally:
                session.close()
            if (
                retained is None
                or retained.get("status") != "staged"
                or int(retained.get("rollout_percent") or 0) != 10
            ):
                raise Pb14GateError("failed promotion mutated the staged rollout")

            rollback_payload = _action_payload(
                "android", rollback_candidate_id=rollback_candidate_id
            )
            prepared = _prepare_action(
                factory,
                action="release.rollout.rollback",
                candidate_id=exact_candidate_id,
                payload=rollback_payload,
            )
            rollback_result = _execute_action(
                factory,
                prepared=prepared,
                action="release.rollout.rollback",
                candidate_id=exact_candidate_id,
                payload=rollback_payload,
            )

            session = factory()
            try:
                _, final_registry = load_release_rollout_registry(session)
                exact_final = rollout_state(
                    final_registry,
                    candidate_id=exact_candidate_id,
                    platform="android",
                )
                rollback_final = rollout_state(
                    final_registry,
                    candidate_id=rollback_candidate_id,
                    platform="android",
                )
                exact_public = public_client_rollout_policy(
                    session,
                    platform="android",
                    configured_version=str(binding["version"]),
                    configured_min_supported_version="1.0.0",
                )
                rollback_public = public_client_rollout_policy(
                    session,
                    platform="android",
                    configured_version=rollback_target,
                    configured_min_supported_version="1.0.0",
                )
            finally:
                session.close()

            if (
                rollback_result.get("external_artifact_switch") != "NOT_PERFORMED"
                or exact_final is None
                or exact_final.get("status") != "rollback_requested"
                or int(exact_final.get("rollout_percent") or 0) != 0
                or rollback_final is None
                or rollback_final.get("status") != "current"
                or int(rollback_final.get("rollout_percent") or 0) != 100
                or int(exact_public.get("rollout_percent") or 0) != 0
                or int(rollback_public.get("rollout_percent") or 0) != 100
            ):
                raise Pb14GateError("rollback request did not fail closed")

            return {
                "database": "TEMPORARY_SQLITE_DESTROYED_AFTER_GATE",
                "cohort": "ISOLATED_LOCAL_CONTROL_FIXTURE",
                "candidate_id": exact_candidate_id,
                "rollback_candidate_id": rollback_candidate_id,
                "injected_event": {
                    "event_id": event_id,
                    "event_name": "update.failed",
                    "error_code": "UPD-004",
                    "app_version": str(binding["version"]),
                    "build_number": str(binding["android_build_number"]),
                    "platform": "android",
                    "architecture": "x86_64",
                    "identity_fields_retained": False,
                },
                "promotion_stop": {
                    "status": "PASS",
                    "error_code": close_error,
                    "staged_state_preserved": True,
                },
                "rollback_request": {
                    "status": "PASS",
                    "exact_candidate_status": str(exact_final["status"]),
                    "exact_candidate_rollout_percent": int(
                        exact_final["rollout_percent"]
                    ),
                    "rollback_candidate_status": str(rollback_final["status"]),
                    "rollback_candidate_rollout_percent": int(
                        rollback_final["rollout_percent"]
                    ),
                    "external_artifact_switch": "NOT_PERFORMED",
                },
                "public_policy": {
                    "exact_candidate_rollout_percent": int(
                        exact_public["rollout_percent"]
                    ),
                    "rollback_candidate_rollout_percent": int(
                        rollback_public["rollout_percent"]
                    ),
                },
            }
        finally:
            engine.dispose()


def run_gate(args: argparse.Namespace) -> dict[str, Any]:
    binding = _validate_retained_candidate(
        manifest_path=args.manifest,
        signature_path=args.signature,
        receipt_path=args.receipt,
        signed_evidence_path=args.signed_evidence,
        release_index_root=args.release_index_root,
    )
    control = _run_isolated_control(binding)
    return {
        "schema": "pokrov.release-1.2.0.pb14-candidate-gate-evidence/v1",
        "recorded_at": _iso(_utcnow()),
        "status": "PASS_LOCAL_EXACT_CANDIDATE_HEALTH_STOP_AND_ROLLBACK_REQUEST",
        "candidate": {
            "label": binding["candidate_label"],
            "candidate_id": binding["candidate_id"],
            "version": binding["version"],
            "manifest_sha256": binding["manifest_sha256"],
            "signature_sha256": binding["signature_sha256"],
            "release_index_revision": binding["release_index_revision"],
            "client_revision": binding["client_revision"],
            "android_x86_64_sha256": binding["android_x86_64_sha256"],
            "android_build_number": binding["android_build_number"],
            "promotion_authorized": False,
        },
        "signature_verification": binding["signing"],
        "control": control,
        "mutations": {
            "production": False,
            "deployment": False,
            "public_assets": False,
            "stable_pointer": False,
            "external_artifact_switch": False,
        },
        "ledger": {
            "row": "OBS_PB/PB-14",
            "from": "I2",
            "to": "I3",
        },
        "evidence_ceiling": (
            "LOCAL_CONTROL_PROOF_ONLY_NO_RUNTIME_COHORT_NO_PUBLIC_PROMOTION_"
            "NO_EXTERNAL_ARTIFACT_ROLLBACK_COMPLETION"
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prove PB-14 locally against the retained exact signed candidate."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=EVIDENCE_ROOT / "release-index.json",
    )
    parser.add_argument(
        "--signature",
        type=Path,
        default=EVIDENCE_ROOT / "release-index.json.sig",
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        default=EVIDENCE_ROOT / "signing-receipt.json",
    )
    parser.add_argument(
        "--signed-evidence",
        type=Path,
        default=EVIDENCE_ROOT / "013Y-signed-candidate-manifest.json",
    )
    parser.add_argument("--release-index-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = run_gate(args)
    except (OSError, Pb14GateError) as exc:
        print(f"PB-14 candidate gate: FAIL: {exc}", file=sys.stderr)
        return 1
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(encoded.encode("utf-8"))
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
