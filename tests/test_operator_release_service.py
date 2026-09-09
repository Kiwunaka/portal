from __future__ import annotations

import asyncio
import hashlib
import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


PORTAL_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
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
    RELEASE_GATE_NAMES,
    release_gate_matrix,
    load_release_rollout_registry,
    public_client_rollout_policy,
    rollout_state,
    version_adoption,
)
from operator_work_service import add_admin_audit  # noqa: E402
from release_evidence_service import get_release_readiness  # noqa: E402


NOW = datetime(2026, 8, 22, 12, 0, 0)
ACTOR = 9999


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


@pytest.fixture
def factory(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'operator-release.db').as_posix()}")
    models.Base.metadata.create_all(engine)
    migrations.run_migrations(engine)
    value = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        yield value
    finally:
        engine.dispose()


def _candidate(session, marker: str, version: str) -> str:
    candidate_id = marker * 64
    descriptor = {
        "component": "client",
        "version": version,
        "revision": marker * 40,
        "artifact_sha256": marker * 64,
    }
    session.add(
        models.ReleaseCandidate(
            candidate_id=candidate_id,
            component="client",
            version=version,
            revision=marker * 40,
            artifact_sha256=marker * 64,
            canonical_descriptor_json=json.dumps(descriptor, sort_keys=True),
            descriptor_sha256=hashlib.sha256(
                json.dumps(descriptor, sort_keys=True).encode("utf-8")
            ).hexdigest(),
            ingest_key_id="release-test",
            imported_at=NOW,
        )
    )
    checks = [
        ("current", "current_origin_reachability"),
        ("brain", "brain_origin_reachability"),
        ("ru", "ru_origin_reachability"),
        *(("current", name) for name in RELEASE_GATE_NAMES),
    ]
    for origin, check_name in checks:
        evidence_hash = hashlib.sha256(
            f"{candidate_id}:{origin}:{check_name}".encode("utf-8")
        ).hexdigest()
        session.add(
            models.ReleaseOriginEvidence(
                candidate_id=candidate_id,
                origin=origin,
                check_name=check_name,
                status="PASS",
                evidence_sha256=evidence_hash,
                observed_at=NOW,
                detail_json='{"source":"retained-test"}',
                imported_at=NOW,
            )
        )
    session.flush()
    return candidate_id


def _payload(platform: str, **values) -> dict:
    return {
        "_environment": "staging",
        "_operator_id": "operator-test",
        "_actor_tg_id": ACTOR,
        "platform": platform,
        **values,
    }


def _prepare(factory, *, action: str, candidate_id: str, payload: dict) -> dict:
    session = factory()
    try:
        result = prepare_action_intent(
            session=session,
            actor_tg_id=ACTOR,
            action=action,
            target={"type": "release_candidate", "id": candidate_id},
            payload=payload,
        )
        session.commit()
        return result
    finally:
        session.close()


def _execute(factory, prepared: dict, *, action: str, candidate_id: str, payload: dict) -> dict:
    return asyncio.run(
        execute_action_intent(
            session_factory=factory,
            actor_tg_id=ACTOR,
            intent_id=str(prepared["intent_id"]),
            idempotency_key=str(uuid.uuid4()),
            confirmation_sha256_header=confirmation_sha256(
                str(prepared["confirmation_challenge"])
            ),
            action=action,
            target={"type": "release_candidate", "id": candidate_id},
            payload=payload,
            audit_writer=add_admin_audit,
        )
    )


def _start(factory, candidate_id: str, *, percent: int) -> dict:
    payload = _payload(
        "android",
        rollout_percent=percent,
        min_supported_version="1.1.0",
        observation_hours=1,
        thresholds={
            "crash_failures": 0,
            "connect_failures": 0,
            "update_failures": 0,
        },
    )
    prepared = _prepare(
        factory,
        action="release.rollout.start",
        candidate_id=candidate_id,
        payload=payload,
    )
    return _execute(
        factory,
        prepared,
        action="release.rollout.start",
        candidate_id=candidate_id,
        payload=payload,
    )


def test_rollout_close_and_rollback_are_guarded_and_drive_public_policy(factory) -> None:
    session = factory()
    try:
        old_candidate = _candidate(session, "a", "1.1.0")
        new_candidate = _candidate(session, "b", "1.2.0")
        session.commit()
    finally:
        session.close()

    first = _start(factory, old_candidate, percent=25)
    assert first["rollout"]["rollout_percent"] == 25

    session = factory()
    try:
        row, registry = load_release_rollout_registry(session, for_update=True)
        old_state = rollout_state(registry, candidate_id=old_candidate, platform="android")
        assert old_state is not None
        old_state["observation_ends_at"] = (_utcnow() - timedelta(minutes=1)).isoformat() + "Z"
        registry["states"][f"android:{old_candidate}"] = old_state
        row.value_json = json.dumps(registry, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        session.add(
            models.ReleaseHealthEvent(
                schema_version=1,
                event_id=str(uuid.uuid4()),
                occurred_at=_utcnow(),
                received_at=_utcnow(),
                component="client",
                subsystem="connection",
                stage="connected",
                event_name="connection_attempt",
                severity="info",
                outcome="success",
                app_version="1.1.0",
                build_number="110",
                channel="stable",
                candidate_label="1.1.0",
                git_revision="a" * 40,
                platform="android",
                architecture="arm64-v8a",
            )
        )
        session.commit()
    finally:
        session.close()

    close_payload = _payload("android")
    close = _prepare(
        factory,
        action="release.observation.close",
        candidate_id=old_candidate,
        payload=close_payload,
    )
    closed = _execute(
        factory,
        close,
        action="release.observation.close",
        candidate_id=old_candidate,
        payload=close_payload,
    )
    assert closed["rollout"]["status"] == "current"
    assert closed["rollout"]["rollout_percent"] == 100

    _start(factory, new_candidate, percent=10)
    rollback_payload = _payload("android", rollback_candidate_id=old_candidate)
    rollback = _prepare(
        factory,
        action="release.rollout.rollback",
        candidate_id=new_candidate,
        payload=rollback_payload,
    )
    rolled_back = _execute(
        factory,
        rollback,
        action="release.rollout.rollback",
        candidate_id=new_candidate,
        payload=rollback_payload,
    )
    assert rolled_back["external_artifact_switch"] == "NOT_PERFORMED"
    assert rolled_back["rollout"]["status"] == "rollback_requested"

    session = factory()
    try:
        blocked_new = public_client_rollout_policy(
            session,
            platform="android",
            configured_version="1.2.0",
            configured_min_supported_version="1.0.0",
        )
        restored_old = public_client_rollout_policy(
            session,
            platform="android",
            configured_version="1.1.0",
            configured_min_supported_version="1.0.0",
        )
    finally:
        session.close()
    assert blocked_new["status"] == "artifact_configuration_mismatch"
    assert blocked_new["rollout_percent"] == 0
    assert restored_old["status"] == "current"
    assert restored_old["rollout_percent"] == 100


@pytest.mark.parametrize(
    ("marker", "subsystem", "error_code"),
    [
        ("c", "crash", "CRASH-001"),
        ("d", "connection", "CONN-008"),
        ("e", "update", "UPD-004"),
    ],
)
def test_health_regression_blocks_staged_promotion_and_preserves_rollout(
    factory, marker: str, subsystem: str, error_code: str
) -> None:
    session = factory()
    try:
        candidate_id = _candidate(session, marker, "1.2.0")
        session.commit()
    finally:
        session.close()

    _start(factory, candidate_id, percent=10)
    session = factory()
    try:
        row, registry = load_release_rollout_registry(session, for_update=True)
        state = rollout_state(registry, candidate_id=candidate_id, platform="android")
        assert row is not None and state is not None
        state["observation_ends_at"] = (_utcnow() - timedelta(minutes=1)).isoformat() + "Z"
        registry["states"][f"android:{candidate_id}"] = state
        row.value_json = json.dumps(
            registry, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        session.add(
            models.ReleaseHealthEvent(
                schema_version=1,
                event_id=str(uuid.uuid4()),
                occurred_at=_utcnow(),
                received_at=_utcnow(),
                component="client",
                subsystem=subsystem,
                stage=subsystem,
                event_name=f"{subsystem}.failed",
                severity="error",
                outcome="failed",
                app_version="1.2.0",
                build_number="30",
                channel="stable",
                candidate_label="1.2.0",
                git_revision="c" * 40,
                core_version="1.1.0",
                core_abi=2,
                platform="android",
                architecture="arm64-v8a",
                error_code=error_code,
                error_origin="client",
            )
        )
        session.commit()
    finally:
        session.close()

    close_payload = _payload("android")
    with pytest.raises(ActionIntentError) as caught:
        _prepare(
            factory,
            action="release.observation.close",
            candidate_id=candidate_id,
            payload=close_payload,
        )
    assert caught.value.code == "release_health_gate_failed"

    session = factory()
    try:
        _, registry = load_release_rollout_registry(session)
        retained = rollout_state(
            registry, candidate_id=candidate_id, platform="android"
        )
    finally:
        session.close()
    assert retained is not None
    assert retained["status"] == "staged"
    assert retained["rollout_percent"] == 10


def test_version_adoption_is_aggregated_without_account_identity(factory) -> None:
    session = factory()
    try:
        session.add_all(
            [
                models.AccountDevice(
                    id=str(uuid.uuid4()),
                    account_id=str(uuid.uuid4()),
                    install_id=f"install-{index}",
                    platform="android",
                    app_version="1.2.0" if index < 2 else "1.1.0",
                    state="active",
                    credential_version=1,
                    first_seen_at=NOW,
                    last_seen_at=_utcnow(),
                    created_at=NOW,
                    updated_at=NOW,
                )
                for index in range(3)
            ]
        )
        session.commit()
        adoption = version_adoption(session, days=30)
    finally:
        session.close()
    assert adoption["platform_totals"] == {"android": 3}
    assert [item["observed_installations"] for item in adoption["cohorts"]] == [2, 1]
    assert all("account_id" not in item and "install_id" not in item for item in adoption["cohorts"])


def test_operational_green_never_claims_a_gate_f_decision() -> None:
    readiness = {
        "ready": True, "status": "PASS",
        "origins": [{"checks": [
            {"check_name": name, "status": "PASS"} for name in RELEASE_GATE_NAMES
        ]}],
    }
    matrix = release_gate_matrix(readiness)
    assert matrix["ready"] is True
    assert len(matrix["checks"]) == 11
    assert matrix["policy_version"] == "pokrov.operator-cockpit-gates/v2"
    assert matrix["gate_f_decision"] == "NOT_EVALUATED"
    readiness["origins"][0]["checks"].pop()
    assert release_gate_matrix(readiness)["ready"] is False


def test_later_origin_failure_blocks_cockpit_and_rollout(factory) -> None:
    with factory() as session:
        candidate_id = _candidate(session, "c", "1.2.0")
        session.add(models.ReleaseOriginEvidence(
            candidate_id=candidate_id, origin="brain", check_name="payment_proof",
            status="FAIL", evidence_sha256="f" * 64, observed_at=NOW,
            detail_json='{"source":"retained-test"}', imported_at=NOW,
        ))
        session.commit()
        readiness = get_release_readiness(session, candidate_id)
    # Reachability is complete; the failed diagnostic must still stop rollout.
    assert readiness["ready"] is True
    matrix = release_gate_matrix(readiness)
    assert matrix["ready"] is False
    assert matrix["status"] == "FAIL"
    payment = next(row for row in matrix["checks"] if row["check_name"] == "payment_proof")
    assert payment["status"] == "FAIL"
    with pytest.raises(ActionIntentError, match="release_gates_incomplete"):
        _start(factory, candidate_id, percent=10)
