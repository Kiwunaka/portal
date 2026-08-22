import base64
import hashlib
import importlib
import json
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

ingest = importlib.import_module("support_bundle_ingest_service")
upload = importlib.import_module("support_bundle_upload_service")
models = importlib.import_module("models")

SIGNING_SECRET = b"support-bundle-test-secret-32bytes!!"


@pytest.fixture()
def session(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'support-ingest.db').as_posix()}")
    models.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    value = factory()
    try:
        yield value
    finally:
        value.close()
        engine.dispose()


def _canonical(value) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _summary_payload(
    *, network_content: bytes | None = None, path_override: str | None = None
):
    build = {
        "app_version": "1.2.0",
        "build_id": "120-test",
        "channel": "direct",
        "platform": "windows",
    }
    removed = {
        "crashesTruncated": 0,
        "eventsTruncated": 0,
        "forbiddenField": 0,
        "invalidValue": 0,
        "optionalCategoryRemoved": 0,
    }
    redaction = {"removed": removed}
    contents = {
        "build/identity.json": _canonical(build),
        "network/summary.json": network_content
        or _canonical(
            {
                "connection_state": "degraded",
                "dns_state": "healthy",
                "egress_state": "failed",
                "host_health": "healthy",
                "route_mode": "all_except_ru",
                "warp_state": "fallback",
            }
        ),
        "redaction/report.json": _canonical(
            {
                "removed": removed,
                "schema_version": 1,
            }
        ),
    }
    paths = sorted(contents)
    descriptors = []
    entries = []
    for path in paths:
        descriptor_path = (
            path_override if path == "network/summary.json" and path_override else path
        )
        content = contents[path]
        descriptors.append(
            {
                "category": ingest._PATH_CATEGORY[path],
                "path": descriptor_path,
                "sha256": hashlib.sha256(content).hexdigest(),
                "size": len(content),
            }
        )
        entries.append({"content_b64": _b64(content), "path": descriptor_path})
    manifest_core = {
        "build": build,
        "files": descriptors,
        "profile": "summary",
        "redaction": redaction,
        "schema_version": 1,
    }
    diagnostic_id = f"diag-{hashlib.sha256(_canonical(manifest_core)).hexdigest()[:24]}"
    manifest = {**manifest_core, "diagnostic_id": diagnostic_id}
    payload = _canonical(
        {
            "files": entries,
            "manifest": manifest,
            "schema_version": 1,
        }
    )
    return diagnostic_id, manifest, payload


def _envelope(diagnostic_id: str, manifest, payload: bytes) -> bytes:
    value = {
        "algorithm": ingest.ALGORITHM,
        "bundle_sha256": hashlib.sha256(payload).hexdigest(),
        "ciphertext_b64": _b64(b"opaque-ciphertext"),
        "diagnostic_id": diagnostic_id,
        "ephemeral_public_key_b64": _b64(b"p" * 32),
        "mac_b64": _b64(b"m" * 16),
        "manifest_sha256": hashlib.sha256(_canonical(manifest)).hexdigest(),
        "nonce_b64": _b64(b"n" * 12),
        "recipient_key_id": "support-test-1",
        "schema_version": 1,
    }
    return _canonical(value)


def _queued(session, tmp_path: Path, envelope: bytes, diagnostic_id: str):
    spec = upload.normalize_upload_spec(
        idempotency_key="worker-attempt-001",
        bundle_id=diagnostic_id,
        size_bytes=len(envelope),
        sha256=hashlib.sha256(envelope).hexdigest(),
        content_type=upload.SUPPORT_BUNDLE_CONTENT_TYPE,
        case_summary="Версия 1.2.0; Windows; код CORE-START-01.",
    )
    owner = upload.owner_binding_hash(owner_tg_id=1001, owner_account_id="account-001")
    issued = upload.issue_upload_ticket(
        session,
        owner_tg_id=1001,
        owner_account_id="account-001",
        owner_binding=owner,
        spec=spec,
        signing_secret=SIGNING_SECRET,
    )
    upload.accept_upload_chunk(
        session,
        upload_id=issued.upload_id,
        upload_ticket=issued.upload_ticket,
        owner_binding=owner,
        offset_bytes=0,
        chunk_sha256=hashlib.sha256(envelope).hexdigest(),
        chunk=envelope,
        signing_secret=SIGNING_SECRET,
        quarantine_root=tmp_path / "quarantine",
    )
    upload.complete_upload(
        session,
        upload_id=issued.upload_id,
        upload_ticket=issued.upload_ticket,
        owner_binding=owner,
        signing_secret=SIGNING_SECRET,
    )
    session.commit()
    return issued


def test_worker_validates_in_memory_and_persists_only_encrypted_object(
    session,
    tmp_path: Path,
) -> None:
    diagnostic_id, manifest, payload = _summary_payload()
    encrypted = _envelope(diagnostic_id, manifest, payload)
    issued = _queued(session, tmp_path, encrypted, diagnostic_id)

    result = ingest.process_queued_support_bundle(
        session,
        upload_id=issued.upload_id,
        quarantine_root=tmp_path / "quarantine",
        accepted_root=tmp_path / "accepted",
        decryptor=lambda _envelope_value: payload,
    )
    session.commit()

    accepted = tmp_path / "accepted" / f"{issued.upload_id}.pokrov-support"
    assert result.status == "validated"
    assert accepted.read_bytes() == encrypted
    assert payload not in accepted.read_bytes()
    assert not list((tmp_path / "quarantine").glob("*.chunk"))
    assert not list(tmp_path.rglob("*.json"))
    row = (
        session.query(models.SupportBundleUpload)
        .filter_by(upload_id=issued.upload_id)
        .one()
    )
    assert {
        "diagnostic_profile": row.diagnostic_profile,
        "app_version": row.app_version,
        "build_number": row.build_number,
        "platform": row.platform,
        "last_phase": row.last_phase,
        "proof_outcome": row.proof_outcome,
        "observed_attempts": row.observed_attempts,
    } == {
        "diagnostic_profile": "summary",
        "app_version": "1.2.0",
        "build_number": "120-test",
        "platform": "windows",
        "last_phase": "egress",
        "proof_outcome": "failed",
        "observed_attempts": 1,
    }

    repeated = ingest.process_queued_support_bundle(
        session,
        upload_id=issued.upload_id,
        quarantine_root=tmp_path / "quarantine",
        accepted_root=tmp_path / "accepted",
        decryptor=lambda _value: pytest.fail("validated replay must not decrypt again"),
    )
    assert repeated == result


@pytest.mark.parametrize(
    ("payload_factory", "expected_code"),
    [
        (
            lambda: _summary_payload(path_override="../escape.json"),
            "unsafe_virtual_path",
        ),
        (
            lambda: _summary_payload(
                network_content=_canonical(
                    {"authorization": "Bearer planted-secret"},
                )
            ),
            "forbidden_content",
        ),
        (
            lambda: _summary_payload(
                network_content=b'PK\\x03\\x04{"archive":"bomb"}',
            ),
            "file_json_invalid",
        ),
        (
            lambda: _summary_payload(
                network_content=_canonical({"host": "api.attacker.example"}),
            ),
            "forbidden_content",
        ),
    ],
)
def test_malicious_corpus_is_rejected_without_leaving_quarantine(
    session,
    tmp_path: Path,
    payload_factory,
    expected_code: str,
) -> None:
    diagnostic_id, manifest, payload = payload_factory()
    encrypted = _envelope(diagnostic_id, manifest, payload)
    issued = _queued(session, tmp_path, encrypted, diagnostic_id)

    result = ingest.process_queued_support_bundle(
        session,
        upload_id=issued.upload_id,
        quarantine_root=tmp_path / "quarantine",
        accepted_root=tmp_path / "accepted",
        decryptor=lambda _value: payload,
    )
    session.commit()

    assert result.status == "rejected"
    assert result.failure_code == expected_code
    assert not (tmp_path / "accepted").exists()
    chunks = list((tmp_path / "quarantine").glob("*.chunk"))
    assert len(chunks) == 1
    assert chunks[0].parent.resolve() == (tmp_path / "quarantine").resolve()
    assert not (tmp_path / "escape.json").exists()


def test_tampered_chunk_is_rejected_before_decryption(session, tmp_path: Path) -> None:
    diagnostic_id, manifest, payload = _summary_payload()
    encrypted = _envelope(diagnostic_id, manifest, payload)
    issued = _queued(session, tmp_path, encrypted, diagnostic_id)
    chunk = next((tmp_path / "quarantine").glob("*.chunk"))
    chunk.write_bytes(b"tampered")
    called = False

    def decryptor(_value):
        nonlocal called
        called = True
        return payload

    result = ingest.process_queued_support_bundle(
        session,
        upload_id=issued.upload_id,
        quarantine_root=tmp_path / "quarantine",
        accepted_root=tmp_path / "accepted",
        decryptor=decryptor,
    )

    assert result.status == "rejected"
    assert result.failure_code == "chunk_checksum_mismatch"
    assert called is False
    assert not (tmp_path / "accepted").exists()


def test_noncanonical_or_wrong_mime_envelope_is_rejected(
    session, tmp_path: Path
) -> None:
    diagnostic_id, manifest, payload = _summary_payload()
    canonical = _envelope(diagnostic_id, manifest, payload)
    noncanonical = json.dumps(json.loads(canonical), indent=2).encode("utf-8")
    issued = _queued(session, tmp_path, noncanonical, diagnostic_id)

    result = ingest.process_queued_support_bundle(
        session,
        upload_id=issued.upload_id,
        quarantine_root=tmp_path / "quarantine",
        accepted_root=tmp_path / "accepted",
        decryptor=lambda _value: payload,
    )

    assert result.failure_code == "envelope_not_canonical"
    row = (
        session.query(models.SupportBundleUpload)
        .filter_by(upload_id=issued.upload_id)
        .one()
    )
    row.status = "queued"
    row.failure_code = None
    row.content_type = "application/zip"
    session.flush()
    result = ingest.process_queued_support_bundle(
        session,
        upload_id=issued.upload_id,
        quarantine_root=tmp_path / "quarantine",
        accepted_root=tmp_path / "accepted",
        decryptor=lambda _value: payload,
    )
    assert result.failure_code == "mime_mismatch"
