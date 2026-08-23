from __future__ import annotations

import hashlib
import importlib
import json
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

models = importlib.import_module("models")
service = importlib.import_module("operator_observability_service")
NOW = datetime(2026, 8, 21, 12, 0, 0)


@pytest.fixture()
def session(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'operator.db').as_posix()}")
    models.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    value = factory()
    try:
        yield value
    finally:
        value.close()
        engine.dispose()


def _ticket(session, *, owner: int = 1001) -> models.SupportTicket:
    row = models.SupportTicket(user_tg_id=owner, subject="Diagnostics")
    session.add(row)
    session.flush()
    return row


def _upload(
    session,
    *,
    payload: bytes,
    status: str = "validated",
    age_days: int = 0,
    hold: bool = False,
) -> models.SupportBundleUpload:
    ticket = _ticket(session)
    upload_id = str(uuid.uuid4())
    timestamp = NOW - timedelta(days=age_days)
    row = models.SupportBundleUpload(
        upload_id=upload_id,
        ticket_id=ticket.id,
        owner_tg_id=1001,
        owner_account_id=str(uuid.uuid4()),
        owner_binding_hash=hashlib.sha256(upload_id.encode()).hexdigest(),
        idempotency_key=f"attempt-{upload_id}",
        bundle_id=f"diag-{uuid.uuid4().hex[:24]}",
        expected_size_bytes=len(payload),
        expected_sha256=hashlib.sha256(payload).hexdigest(),
        content_type="application/vnd.pokrov.support-bundle+json",
        received_size_bytes=len(payload),
        status=status,
        object_name=f"{upload_id}.pokrov-support" if status == "validated" else None,
        diagnostic_profile="standard",
        app_version="1.2.0",
        build_number="45",
        platform="windows",
        architecture="x86_64",
        last_phase="verify",
        last_error_code="CORE-START-01",
        proof_outcome="failed",
        observed_attempts=2,
        retention_hold=hold,
        expires_at=timestamp + timedelta(hours=1),
        completed_at=timestamp,
        validated_at=timestamp if status == "validated" else None,
        created_at=timestamp,
        updated_at=timestamp,
    )
    session.add(row)
    session.flush()
    return row


def _health_event(
    *,
    received_at: datetime,
    subsystem: str,
    outcome: str,
    platform: str = "windows",
    selected_app_count: int | None = None,
) -> models.ReleaseHealthEvent:
    return models.ReleaseHealthEvent(
        schema_version=1,
        event_id=str(uuid.uuid4()),
        occurred_at=received_at,
        received_at=received_at,
        component="app",
        subsystem=subsystem,
        stage=subsystem,
        event_name=f"client.{subsystem}.result",
        severity="error" if outcome == "failed" else "info",
        outcome=outcome,
        app_version="1.2.0",
        build_number="45",
        channel="beta",
        candidate_label="pokrov-1.2.0-beta.45",
        git_revision="a" * 40,
        core_version="1.2.0",
        core_abi=2,
        platform=platform,
        architecture="arm64-v8a" if platform == "android" else "x86_64",
        error_code="CORE-START-01" if outcome == "failed" else None,
        error_origin="core" if outcome == "failed" else None,
        selected_app_count=selected_app_count,
    )


def _audit(
    *,
    upload: models.SupportBundleUpload,
    created_at: datetime,
    hold: bool,
) -> models.SupportBundleAccessAudit:
    return models.SupportBundleAccessAudit(
        grant_id=str(uuid.uuid4()),
        upload_id=upload.upload_id,
        ticket_id=upload.ticket_id,
        actor_tg_id=2002,
        actor_role="l2_sre",
        action="downloaded",
        reason_code="customer_case",
        expires_at=created_at,
        used_at=created_at,
        retention_hold=hold,
        created_at=created_at,
    )


def test_l1_summary_is_closed_and_l2_grant_is_actor_bound_single_use(
    session,
    tmp_path: Path,
) -> None:
    payload = b"opaque encrypted support object"
    upload = _upload(session, payload=payload)
    accepted = tmp_path / "accepted"
    accepted.mkdir()
    object_path = accepted / upload.object_name
    object_path.write_bytes(payload)
    session.commit()

    summary = service.support_bundle_summary(session, upload_id=upload.upload_id)
    rendered = json.dumps(summary, sort_keys=True)
    assert summary["build"]["platform"] == "windows"
    assert summary["timeline"][-1]["phase"] == "validated"
    assert not {
        "owner_tg_id",
        "owner_account_id",
        "owner_binding_hash",
        "object_name",
        "access_token_hash",
    } & set(summary)
    assert str(upload.owner_tg_id) not in rendered
    assert upload.owner_account_id not in rendered

    with pytest.raises(
        service.OperatorObservabilityError, match="support_bundle_l2_required"
    ):
        service.issue_bundle_access_grant(
            session,
            upload_id=upload.upload_id,
            actor_tg_id=1001,
            privileged_ids={2002},
            reason_code="customer_case",
            now=NOW,
        )

    grant = service.issue_bundle_access_grant(
        session,
        upload_id=upload.upload_id,
        actor_tg_id=2002,
        privileged_ids={2002},
        reason_code="customer_case",
        now=NOW,
    )
    session.commit()
    issued_audit = session.query(models.SupportBundleAccessAudit).one()
    assert issued_audit.access_token_hash != grant.token

    with pytest.raises(
        service.OperatorObservabilityError, match="support_bundle_l2_required"
    ):
        service.consume_bundle_access_grant(
            session,
            upload_id=upload.upload_id,
            token=grant.token,
            actor_tg_id=1001,
            privileged_ids={2002},
            accepted_root=accepted,
            now=NOW,
        )

    item = service.consume_bundle_access_grant(
        session,
        upload_id=upload.upload_id,
        token=grant.token,
        actor_tg_id=2002,
        privileged_ids={2002},
        accepted_root=accepted,
        now=NOW,
    )
    session.commit()
    assert item.path == object_path
    assert session.query(models.SupportBundleAccessAudit).count() == 2
    with pytest.raises(
        service.OperatorObservabilityError,
        match="support_bundle_access_grant_invalid",
    ):
        service.consume_bundle_access_grant(
            session,
            upload_id=upload.upload_id,
            token=grant.token,
            actor_tg_id=2002,
            privileged_ids={2002},
            accepted_root=accepted,
            now=NOW,
        )


def test_retention_hold_is_l2_only_and_audited(session) -> None:
    upload = _upload(session, payload=b"ciphertext")
    with pytest.raises(
        service.OperatorObservabilityError, match="support_bundle_l2_required"
    ):
        service.set_bundle_retention_hold(
            session,
            upload_id=upload.upload_id,
            actor_tg_id=1001,
            privileged_ids={2002},
            hold=True,
            reason_code="incident_review",
            now=NOW,
        )

    summary = service.set_bundle_retention_hold(
        session,
        upload_id=upload.upload_id,
        actor_tg_id=2002,
        privileged_ids={2002},
        hold=True,
        reason_code="incident_review",
        now=NOW,
    )
    session.commit()
    audit = session.query(models.SupportBundleAccessAudit).one()
    assert summary["retention_hold"] is True
    assert audit.action == "retention_hold_set"
    assert audit.reason_code == "incident_review"


def test_ciphertext_access_rejects_an_in_root_symlink(session, tmp_path: Path) -> None:
    payload = b"opaque encrypted support object"
    upload = _upload(session, payload=payload)
    accepted = tmp_path / "accepted"
    accepted.mkdir()
    target = accepted / "real-object.bin"
    target.write_bytes(payload)
    try:
        (accepted / upload.object_name).symlink_to(target)
    except OSError:
        pytest.skip("symlink creation is unavailable")
    grant = service.issue_bundle_access_grant(
        session,
        upload_id=upload.upload_id,
        actor_tg_id=2002,
        privileged_ids={2002},
        reason_code="security_review",
        now=NOW,
    )
    session.commit()

    with pytest.raises(
        service.OperatorObservabilityError,
        match="support_bundle_object_invalid",
    ):
        service.consume_bundle_access_grant(
            session,
            upload_id=upload.upload_id,
            token=grant.token,
            actor_tg_id=2002,
            privileged_ids={2002},
            accepted_root=accepted,
            now=NOW,
        )
    audit = session.query(models.SupportBundleAccessAudit).one()
    assert audit.used_at is None
    assert audit.access_token_hash is not None


def test_release_health_snapshot_has_version_scoped_failure_deltas(session) -> None:
    session.add_all(
        [
            _health_event(
                received_at=NOW - timedelta(hours=1),
                subsystem="crash",
                outcome="failed",
            ),
            _health_event(
                received_at=NOW - timedelta(hours=2),
                subsystem="connection",
                outcome="succeeded",
            ),
            _health_event(
                received_at=NOW - timedelta(hours=25),
                subsystem="connection",
                outcome="failed",
            ),
        ]
    )
    session.commit()

    snapshot = service.release_health_snapshot(session, hours=24, now=NOW)
    group = snapshot["groups"][0]
    assert group["candidate_label"] == "pokrov-1.2.0-beta.45"
    assert group["build_number"] == "45"
    assert group["channel"] == "beta"
    assert group["core_abi"] == "2"
    assert group["platform"] == "windows"
    assert group["crash_failures"] == 1
    assert group["delta"] == {
        "crash_failures": 1,
        "connect_failures": -1,
        "update_failures": 0,
    }
    assert not {"event_id", "error_origin", "occurred_at"} & set(group)


def test_release_health_snapshot_exposes_only_android_routing_count_aggregates(
    session,
) -> None:
    first = _health_event(
        received_at=NOW - timedelta(hours=1),
        subsystem="routing",
        outcome="observed",
        platform="android",
        selected_app_count=3,
    )
    first.stage = "complete"
    first.event_name = "app.routing.selection.finished"
    second = _health_event(
        received_at=NOW - timedelta(hours=2),
        subsystem="routing",
        outcome="observed",
        platform="android",
        selected_app_count=5,
    )
    second.stage = "complete"
    second.event_name = "app.routing.selection.finished"
    unrelated = _health_event(
        received_at=NOW - timedelta(hours=3),
        subsystem="connection",
        outcome="observed",
        platform="android",
        selected_app_count=99,
    )
    session.add_all([first, second, unrelated])
    session.commit()

    snapshot = service.release_health_snapshot(session, hours=24, now=NOW)
    group = snapshot["groups"][0]
    rendered = json.dumps(snapshot, sort_keys=True)

    assert group["routing_count_events"] == 2
    assert group["selected_app_count_total"] == 8
    assert "package_name" not in rendered
    assert "selected_apps" not in rendered


def test_known_issue_registry_is_version_scoped_and_links_are_observational(
    session,
) -> None:
    payload = {
        "candidate_label": "pokrov-1.2.0-beta.45",
        "issue_code": "REL-120",
        "app_version": "1.2.0",
        "build_number": "45",
        "platform": "windows",
        "severity": "error",
        "status": "open",
        "title": "Windows startup regression",
        "safe_summary": "Some Windows starts fail before the connection phase.",
        "error_code": "CORE-001",
        "incident_ref": "incident:INC-120",
        "release_ref": "release:pokrov-1.2.0-beta.45",
    }
    missing_error = dict(payload, error_code=None)
    with pytest.raises(
        service.OperatorObservabilityError, match="known_issue_error_required"
    ):
        service.upsert_known_issue(
            session,
            actor_tg_id=2002,
            payload=missing_error,
            now=NOW,
        )
    unknown_error = dict(payload, error_code="CORE-START-01")
    with pytest.raises(
        service.OperatorObservabilityError, match="known_issue_error_invalid"
    ):
        service.upsert_known_issue(
            session,
            actor_tg_id=2002,
            payload=unknown_error,
            now=NOW,
        )

    first = service.upsert_known_issue(
        session,
        actor_tg_id=2002,
        payload=payload,
        now=NOW,
    )
    payload["status"] = "monitoring"
    second = service.upsert_known_issue(
        session,
        actor_tg_id=2003,
        payload=payload,
        now=NOW + timedelta(minutes=5),
    )
    session.commit()

    assert first["status"] == "open"
    assert second["status"] == "monitoring"
    assert session.query(models.ReleaseKnownIssue).count() == 1
    assert service.known_issues(
        session,
        candidate_label="pokrov-1.2.0-beta.45",
        status="monitoring",
    ) == [second]
    assert service.known_issues(
        session,
        status="monitoring",
        error_code="CORE-001",
        app_version="1.2.0",
        build_number="45",
        platform="windows",
    ) == [second]
    assert service.known_issues(
        session,
        status="monitoring",
        error_code="CORE-001",
        app_version="1.2.0",
        build_number="46",
        platform="windows",
    ) == []


def test_retention_deletes_only_eligible_unheld_rows_and_exact_owned_files(
    session,
    tmp_path: Path,
) -> None:
    accepted = tmp_path / "accepted"
    quarantine = tmp_path / "quarantine"
    accepted.mkdir()
    quarantine.mkdir()
    old = NOW - timedelta(days=400)
    session.add(
        _health_event(
            received_at=old,
            subsystem="connection",
            outcome="failed",
        )
    )

    accepted_upload = _upload(session, payload=b"old accepted", age_days=40)
    (accepted / accepted_upload.object_name).write_bytes(b"old accepted")
    held_upload = _upload(session, payload=b"held accepted", age_days=40, hold=True)
    (accepted / held_upload.object_name).write_bytes(b"held accepted")
    rejected_upload = _upload(
        session,
        payload=b"old quarantine",
        status="rejected",
        age_days=10,
    )
    chunk_name = f"{rejected_upload.upload_id}.0000000000.{'a' * 16}.chunk"
    chunk_path = quarantine / chunk_name
    chunk_path.write_bytes(b"old quarantine")
    session.add(
        models.SupportBundleChunk(
            upload_id=rejected_upload.id,
            offset_bytes=0,
            size_bytes=len(b"old quarantine"),
            sha256=hashlib.sha256(b"old quarantine").hexdigest(),
            stored_name=chunk_name,
            created_at=old,
        )
    )
    session.add_all(
        [
            _audit(upload=accepted_upload, created_at=old, hold=False),
            _audit(upload=held_upload, created_at=old, hold=True),
        ]
    )
    session.commit()

    counters = service.run_operator_retention_once(
        session,
        now=NOW,
        quarantine_root=quarantine,
        accepted_root=accepted,
        release_health_days=90,
        accepted_bundle_days=30,
        rejected_bundle_days=7,
        incomplete_grace_days=1,
        access_audit_days=365,
    )
    session.commit()

    assert counters == {
        "release_health_events_deleted": 1,
        "bundle_rows_deleted": 2,
        "accepted_objects_deleted": 1,
        "quarantine_chunks_deleted": 1,
        "access_audits_deleted": 1,
        "held_bundles_skipped": 1,
        "held_audits_skipped": 1,
        "files_missing": 0,
        "file_errors": 0,
    }
    assert not (accepted / accepted_upload.object_name).exists()
    assert not chunk_path.exists()
    assert (accepted / held_upload.object_name).exists()
    assert (
        session.query(models.SupportBundleUpload).one().upload_id
        == held_upload.upload_id
    )
    assert session.query(models.SupportBundleAccessAudit).one().retention_hold is True
