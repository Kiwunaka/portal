import base64
import hashlib
import importlib
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

service = importlib.import_module("support_bundle_upload_service")
models = importlib.import_module("models")
Base = models.Base
SupportBundleChunk = models.SupportBundleChunk
SupportBundleUpload = models.SupportBundleUpload
SupportTicket = models.SupportTicket
SupportTicketMessage = models.SupportTicketMessage


SIGNING_SECRET = b"support-bundle-test-secret-32bytes!!"
NOW = datetime(2026, 8, 21, 12, 0, 0)


@pytest.fixture()
def session(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'support-bundle.db').as_posix()}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    value = factory()
    try:
        yield value
    finally:
        value.close()
        engine.dispose()


def _spec(
    payload: bytes,
    *,
    idempotency_key: str = "desktop-attempt-001",
    bundle_id: str = "diag-0123456789abcdef01234567",
):
    return service.normalize_upload_spec(
        idempotency_key=idempotency_key,
        bundle_id=bundle_id,
        size_bytes=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        content_type=service.SUPPORT_BUNDLE_CONTENT_TYPE,
        case_summary="Версия 1.2.0; Windows; код CORE-START-01.",
    )


def _issue(session, payload: bytes, **overrides):
    return service.issue_upload_ticket(
        session,
        owner_tg_id=1001,
        owner_account_id="account-001",
        owner_binding=service.owner_binding_hash(
            owner_tg_id=1001,
            owner_account_id="account-001",
        ),
        spec=_spec(payload, **overrides),
        signing_secret=SIGNING_SECRET,
        now=NOW,
    )


def _put(session, tmp_path: Path, issued, payload: bytes, offset: int, size: int):
    chunk = payload[offset : offset + size]
    return service.accept_upload_chunk(
        session,
        upload_id=issued.upload_id,
        upload_ticket=issued.upload_ticket,
        owner_binding=service.owner_binding_hash(
            owner_tg_id=1001,
            owner_account_id="account-001",
        ),
        offset_bytes=offset,
        chunk_sha256=hashlib.sha256(chunk).hexdigest(),
        chunk=chunk,
        signing_secret=SIGNING_SECRET,
        quarantine_root=tmp_path / "quarantine",
        now=NOW,
    )


def test_ticket_issue_is_idempotent_and_creates_one_case(session) -> None:
    payload = b"opaque-encrypted-envelope"

    first = _issue(session, payload)
    session.commit()
    second = _issue(session, payload)

    assert second == first
    assert session.query(SupportTicket).count() == 1
    assert session.query(SupportTicketMessage).count() == 1
    assert session.query(SupportBundleUpload).count() == 1
    assert "Версия 1.2.0" in session.query(SupportTicketMessage).one().body


def test_idempotency_key_and_case_binding_conflicts_are_stable(session) -> None:
    first_payload = b"ciphertext-one"
    _issue(session, first_payload)
    session.commit()

    with pytest.raises(
        service.SupportBundleUploadError, match="idempotency_conflict"
    ) as caught:
        _issue(session, b"ciphertext-two")
    assert caught.value.status_code == 409

    first = session.query(SupportBundleUpload).one()
    conflict_spec = _spec(
        b"different-attempt",
        idempotency_key="desktop-attempt-002",
    )
    with pytest.raises(
        service.SupportBundleUploadError, match="bundle_binding_conflict"
    ) as caught:
        service.issue_upload_ticket(
            session,
            owner_tg_id=1001,
            owner_account_id="account-001",
            owner_binding=first.owner_binding_hash,
            spec=conflict_spec,
            signing_secret=SIGNING_SECRET,
            ticket_id=first.ticket_id,
            now=NOW,
        )
    assert caught.value.status_code == 409


def test_chunk_resume_replay_conflict_and_completion_are_deterministic(
    session,
    tmp_path: Path,
) -> None:
    payload = (b"opaque-ciphertext-" * 20_000)[:300_000]
    issued = _issue(session, payload)
    session.commit()

    first = _put(session, tmp_path, issued, payload, 0, service.MAX_CHUNK_BYTES)
    session.commit()
    replay = _put(session, tmp_path, issued, payload, 0, service.MAX_CHUNK_BYTES)

    assert first.next_offset == service.MAX_CHUNK_BYTES
    assert replay.repeated is True
    assert replay.next_offset == first.next_offset

    wrong = b"x" * service.MAX_CHUNK_BYTES
    with pytest.raises(
        service.SupportBundleUploadError, match="chunk_replay_conflict"
    ) as caught:
        service.accept_upload_chunk(
            session,
            upload_id=issued.upload_id,
            upload_ticket=issued.upload_ticket,
            owner_binding=service.owner_binding_hash(
                owner_tg_id=1001,
                owner_account_id="account-001",
            ),
            offset_bytes=0,
            chunk_sha256=hashlib.sha256(wrong).hexdigest(),
            chunk=wrong,
            signing_secret=SIGNING_SECRET,
            quarantine_root=tmp_path / "quarantine",
            now=NOW,
        )
    assert caught.value.status_code == 409

    final = _put(
        session,
        tmp_path,
        issued,
        payload,
        service.MAX_CHUNK_BYTES,
        len(payload) - service.MAX_CHUNK_BYTES,
    )
    assert final.complete is True
    assert session.query(SupportBundleChunk).count() == 2

    queued = service.complete_upload(
        session,
        upload_id=issued.upload_id,
        upload_ticket=issued.upload_ticket,
        owner_binding=service.owner_binding_hash(
            owner_tg_id=1001,
            owner_account_id="account-001",
        ),
        signing_secret=SIGNING_SECRET,
        now=NOW,
    )
    session.commit()
    repeated = service.complete_upload(
        session,
        upload_id=issued.upload_id,
        upload_ticket=issued.upload_ticket,
        owner_binding=queued.owner_binding_hash,
        signing_secret=SIGNING_SECRET,
        now=NOW + timedelta(hours=1),
    )

    assert repeated.status == "queued"
    assert repeated.object_name == f"{issued.upload_id}.pokrov-support"
    assert session.query(SupportBundleUpload).count() == 1


def test_interrupted_upload_reports_offset_and_rejects_gap(
    session, tmp_path: Path
) -> None:
    payload = b"encrypted" * 40_000
    issued = _issue(session, payload)
    first = _put(session, tmp_path, issued, payload, 0, 100_000)
    session.commit()

    resumed = _issue(session, payload)
    assert resumed.next_offset == first.next_offset == 100_000

    with pytest.raises(
        service.SupportBundleUploadError, match="unexpected_chunk_offset"
    ) as caught:
        _put(session, tmp_path, issued, payload, 100_001, 20_000)
    assert caught.value.status_code == 409

    with pytest.raises(
        service.SupportBundleUploadError, match="upload_incomplete"
    ) as caught:
        service.complete_upload(
            session,
            upload_id=issued.upload_id,
            upload_ticket=issued.upload_ticket,
            owner_binding=service.owner_binding_hash(
                owner_tg_id=1001,
                owner_account_id="account-001",
            ),
            signing_secret=SIGNING_SECRET,
            now=NOW,
        )
    assert caught.value.status_code == 409


def test_expired_ticket_and_owner_mismatch_are_rejected(
    session, tmp_path: Path
) -> None:
    payload = b"opaque"
    issued = _issue(session, payload)

    with pytest.raises(
        service.SupportBundleUploadError, match="upload_owner_mismatch"
    ) as caught:
        service.accept_upload_chunk(
            session,
            upload_id=issued.upload_id,
            upload_ticket=issued.upload_ticket,
            owner_binding="f" * 64,
            offset_bytes=0,
            chunk_sha256=hashlib.sha256(payload).hexdigest(),
            chunk=payload,
            signing_secret=SIGNING_SECRET,
            quarantine_root=tmp_path / "quarantine",
            now=NOW,
        )
    assert caught.value.status_code == 403

    with pytest.raises(
        service.SupportBundleUploadError, match="upload_ticket_expired"
    ) as caught:
        service.accept_upload_chunk(
            session,
            upload_id=issued.upload_id,
            upload_ticket=issued.upload_ticket,
            owner_binding=service.owner_binding_hash(
                owner_tg_id=1001,
                owner_account_id="account-001",
            ),
            offset_bytes=0,
            chunk_sha256=hashlib.sha256(payload).hexdigest(),
            chunk=payload,
            signing_secret=SIGNING_SECRET,
            quarantine_root=tmp_path / "quarantine",
            now=NOW + timedelta(minutes=16),
        )
    assert caught.value.status_code == 410


def test_expired_incomplete_ticket_renews_without_duplicate_case(session) -> None:
    payload = b"opaque-renewal"
    issued = _issue(session, payload)
    session.commit()

    renewed = service.issue_upload_ticket(
        session,
        owner_tg_id=1001,
        owner_account_id="account-001",
        owner_binding=service.owner_binding_hash(
            owner_tg_id=1001,
            owner_account_id="account-001",
        ),
        spec=_spec(payload),
        signing_secret=SIGNING_SECRET,
        now=NOW + timedelta(minutes=16),
    )

    assert renewed.upload_id == issued.upload_id
    assert renewed.upload_ticket != issued.upload_ticket
    assert renewed.expires_at == NOW + timedelta(minutes=31)
    assert session.query(SupportTicket).count() == 1
    assert session.query(SupportBundleUpload).count() == 1


def test_input_contract_rejects_secrets_and_unconfigured_key_sets() -> None:
    with pytest.raises(service.SupportBundleUploadError, match="invalid_case_summary"):
        service.normalize_upload_spec(
            idempotency_key="desktop-attempt-001",
            bundle_id="diag-0123456789abcdef01234567",
            size_bytes=20,
            sha256="a" * 64,
            content_type=service.SUPPORT_BUNDLE_CONTENT_TYPE,
            case_summary="Authorization: Bearer planted-secret",
        )

    with pytest.raises(
        service.SupportBundleUploadError, match="support_key_set_unavailable"
    ):
        service.load_configured_signed_key_set("{}")

    encoded_payload = base64.urlsafe_b64encode(b"signed-key-set").decode().rstrip("=")
    encoded_signature = base64.urlsafe_b64encode(b"s" * 64).decode().rstrip("=")
    raw = json.dumps(
        {
            "algorithm": "Ed25519",
            "key_id": "support-root-v1",
            "payload_b64": encoded_payload,
            "schema_version": 1,
            "signature_b64": encoded_signature,
        }
    )
    assert service.load_configured_signed_key_set(raw)["key_id"] == "support-root-v1"


def test_chunk_storage_rejects_symlink_root(session, tmp_path: Path) -> None:
    target = tmp_path / "real"
    target.mkdir()
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is unavailable")

    payload = b"opaque"
    issued = _issue(session, payload)
    with pytest.raises(
        service.SupportBundleUploadError, match="quarantine_unavailable"
    ) as caught:
        service.accept_upload_chunk(
            session,
            upload_id=issued.upload_id,
            upload_ticket=issued.upload_ticket,
            owner_binding=service.owner_binding_hash(
                owner_tg_id=1001,
                owner_account_id="account-001",
            ),
            offset_bytes=0,
            chunk_sha256=hashlib.sha256(payload).hexdigest(),
            chunk=payload,
            signing_secret=SIGNING_SECRET,
            quarantine_root=alias,
            now=NOW,
        )
    assert caught.value.status_code == 503
