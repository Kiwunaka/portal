from __future__ import annotations

import hashlib
import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))

import migrations  # noqa: E402
import models  # noqa: E402
from release_evidence_service import (  # noqa: E402
    ReleaseEvidenceConflict,
    ReleaseEvidenceValidationError,
    compute_candidate_id,
    get_release_readiness,
    import_release_evidence,
    list_release_candidates,
)


NOW = datetime(2026, 7, 15, 12, 10, tzinfo=timezone.utc)


@pytest.fixture
def session(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'release-evidence.db').as_posix()}")
    models.Base.metadata.create_all(engine)
    migrations.run_migrations(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    value = factory()
    try:
        yield value
    finally:
        value.close()
        engine.dispose()


def _candidate(*, artifact: str = "1" * 64, version: str = "2026.07.15.1") -> dict:
    return {
        "component": "adminapp",
        "version": version,
        "revision": "9da042c9da042c9da042c9da042c9da042c9da0",
        "artifact_sha256": artifact,
    }


def _evidence(
    origin: str,
    status: str,
    marker: str,
    *,
    run_id: str | None = None,
) -> dict:
    result = {
        "origin": origin,
        "check_name": f"{origin}_release_check",
        "status": status,
        "observed_at": "2026-07-15T12:00:00Z",
        "evidence_sha256": marker * 64,
        "detail": {"source": "retained-run"},
    }
    if run_id is not None:
        result["ru_probe_run_id"] = run_id
    return result


def _payload(candidate: dict, evidence: list[dict]) -> dict:
    return {
        "schema_version": 1,
        "candidate_id": compute_candidate_id(candidate),
        "candidate": candidate,
        "evidence": evidence,
    }


def _full_ru_run(session, *, release_verdict: str = "pass", eligible: bool = True):
    run = models.RuProbeRun(
        run_id=str(uuid.uuid4()),
        schema_version=2,
        origin="ru",
        probe_host_id="mini",
        probe_host_label="Мини",
        runner_version="2.0.0",
        started_at=NOW - timedelta(minutes=2),
        finished_at=NOW - timedelta(minutes=1),
        received_at=NOW,
        manifest_revision="a" * 64,
        execution_status="completed",
        environment_verdict="available",
        release_verdict=release_verdict,
        current_eligible=eligible,
        artifact_sha256="b" * 64,
        ingest_key_id="ru-test",
        retention_hold=False,
    )
    session.add(run)
    session.flush()
    session.add(
        models.RuProbeTargetResult(
            run_db_id=run.id,
            target_id="node:nl",
            target_kind="delivery_node",
            scope="release_required",
            node_code="nl",
            endpoint_fingerprint="c" * 64,
            endpoint_host="nl.example.test",
            endpoint_port=443,
            requested_address_families_json=["ipv4"],
            transport_metadata_json={},
            transport_profile="legacy_reality_fallback",
            probe_mode="delivery_tls",
            observed_at=run.finished_at,
            overall_status="pass",
            current_eligible=eligible,
            dns_status="pass",
            tcp_status="pass",
            tls_status="pass",
            http_large_body_status="not_applicable",
            transport_handshake_status="pass",
            ipv4_status="pass",
            ipv6_status="not_applicable",
            reported_transport_handshake_status="pass",
            reported_transport_classification="ok",
        )
    )
    session.flush()
    return run


def test_candidate_hash_idempotency_isolation_and_status_honesty(session) -> None:
    candidate_a = _candidate()
    expected = hashlib.sha256(
        json.dumps(
            candidate_a,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    assert compute_candidate_id(candidate_a) == expected

    mismatched = _payload(candidate_a, [])
    mismatched["candidate_id"] = "f" * 64
    with pytest.raises(ReleaseEvidenceConflict, match="candidate_id_mismatch"):
        import_release_evidence(
            session,
            mismatched,
            ingest_key_id="release-v1",
            imported_at=NOW,
        )

    payload_a = _payload(
        candidate_a,
        [
            _evidence("current", "PASS", "2"),
            _evidence("brain", "OPERATOR_ATTESTED", "3"),
            _evidence("ru", "SKIPPED_BY_OWNER", "4"),
        ],
    )
    first = import_release_evidence(
        session,
        payload_a,
        ingest_key_id="release-v1",
        imported_at=NOW,
    )
    retry = import_release_evidence(
        session,
        payload_a,
        ingest_key_id="release-v2",
        imported_at=NOW + timedelta(seconds=1),
    )
    assert (first.created, first.evidence_created) == (True, 3)
    assert (retry.created, retry.evidence_created) == (False, 0)
    readiness_a = get_release_readiness(session, payload_a["candidate_id"], now=NOW)
    assert readiness_a["ready"] is False
    assert [item["status"] for item in readiness_a["origins"]] == [
        "PASS",
        "OPERATOR_ATTESTED",
        "SKIPPED_BY_OWNER",
    ]

    candidate_b = _candidate(artifact="5" * 64)
    payload_b = _payload(candidate_b, [])
    import_release_evidence(
        session,
        payload_b,
        ingest_key_id="release-v1",
        imported_at=NOW,
    )
    readiness_b = get_release_readiness(session, payload_b["candidate_id"], now=NOW)
    assert readiness_b["status"] == "MISSING"
    assert all(item["status"] == "MISSING" for item in readiness_b["origins"])

    unsafe = _payload(_candidate(version="2026.07.15.2"), [_evidence("current", "PASS", "6")])
    unsafe["evidence"][0]["detail"] = {"client_secret": "must-not-store"}
    with pytest.raises(ReleaseEvidenceValidationError, match="unsafe_detail"):
        import_release_evidence(
            session,
            unsafe,
            ingest_key_id="release-v1",
            imported_at=NOW,
        )


def test_ru_pass_atomically_holds_exact_full_run_and_fk_restricts_delete(session) -> None:
    run = _full_ru_run(session)
    payload = _payload(
        _candidate(),
        [
            _evidence("current", "PASS", "7"),
            _evidence("brain", "PASS", "8"),
            _evidence("ru", "PASS", "9", run_id=run.run_id),
        ],
    )
    stored = import_release_evidence(
        session,
        payload,
        ingest_key_id="release-v1",
        imported_at=NOW,
    )
    session.commit()
    session.refresh(run)

    assert stored.created is True
    assert run.retention_hold is True
    assert run.retention_held_at.replace(tzinfo=timezone.utc) == NOW
    assert payload["candidate_id"] in run.retention_hold_reason
    assert "ru_release_check" in run.retention_hold_reason
    assert get_release_readiness(session, payload["candidate_id"], now=NOW)["status"] == "PASS"

    session.delete(run)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_ineligible_ru_pass_rolls_back_candidate_and_cursor_is_deterministic(session) -> None:
    incomplete = _full_ru_run(session, release_verdict="incomplete", eligible=False)
    session.commit()
    rejected = _payload(
        _candidate(),
        [_evidence("ru", "PASS", "a", run_id=incomplete.run_id)],
    )
    with pytest.raises(ReleaseEvidenceConflict, match="ru_probe_run_ineligible"):
        import_release_evidence(
            session,
            rejected,
            ingest_key_id="release-v1",
            imported_at=NOW,
        )
    session.rollback()
    assert session.query(models.ReleaseCandidate).count() == 0
    assert session.query(models.ReleaseOriginEvidence).count() == 0

    older = _payload(_candidate(version="2026.07.15.2"), [])
    newer = _payload(_candidate(version="2026.07.15.3"), [])
    import_release_evidence(
        session,
        older,
        ingest_key_id="release-v1",
        imported_at=NOW,
    )
    import_release_evidence(
        session,
        newer,
        ingest_key_id="release-v1",
        imported_at=NOW,
    )
    first = list_release_candidates(session, limit=1, now=NOW)
    second = list_release_candidates(
        session,
        limit=1,
        cursor=first["next_cursor"],
        now=NOW,
    )
    assert [first["items"][0]["candidate_id"], second["items"][0]["candidate_id"]] == [
        newer["candidate_id"],
        older["candidate_id"],
    ]
