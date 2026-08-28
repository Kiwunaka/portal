from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

import models  # noqa: E402
import release_health_baseline_service as baseline  # noqa: E402


NOW = datetime(2026, 8, 26, 12, 0, tzinfo=timezone.utc)
SECRET = "release-health-cohort-test-secret-v1"


@pytest.fixture
def session(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'baseline.db').as_posix()}")
    models.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    value = factory()
    try:
        yield value
    finally:
        value.close()
        engine.dispose()


def _identity(**updates: object) -> baseline.ReleaseHealthCohortIdentity:
    payload: dict[str, object] = {
        "app_version": "1.2.0",
        "build_number": "4046",
        "channel": "beta",
        "candidate_label": "pokrov-1.2.0-beta.4046",
        "git_revision": "a" * 40,
        "core_abi": 2,
        "platform": "android",
        "architecture": "arm64-v8a",
    }
    payload.update(updates)
    return baseline.normalize_cohort_identity(payload)


def _event(*, outcome: str = "succeeded", family: str = "connect") -> object:
    if family == "connect":
        component, subsystem, stage, name, code = (
            "app",
            "connection",
            "verify",
            "client.connection.verify",
            None,
        )
    elif family == "crash":
        component, subsystem, stage, name, code = (
            "app",
            "crash",
            "persist",
            "app.crash.persisted",
            "CRASH-001" if outcome == "failed" else None,
        )
    else:
        component, subsystem, stage, name, code = (
            "app",
            "update",
            "complete",
            "update.completed",
            "UPD-001" if outcome == "failed" else None,
        )
    identity = _identity()
    return SimpleNamespace(
        **{
            **{
                key: value
                for key, value in asdict(identity).items()
            },
            "component": component,
            "subsystem": subsystem,
            "stage": stage,
            "event_name": name,
            "outcome": outcome,
            "error_code": code,
        }
    )


def test_bucket_store_has_no_identity_and_caps_one_contributor(session) -> None:
    baseline.record_cohort_contribution(
        session,
        [_event(outcome="failed") for _ in range(100)],
        contributor_key="account-one",
        secret=SECRET,
        now=NOW,
    )
    session.commit()

    row = session.query(models.ReleaseHealthCohortBucket).one()
    assert row.event_count == baseline.MAX_EVENTS_PER_BUCKET
    assert row.failure_count == baseline.MAX_EVENTS_PER_BUCKET
    assert row.connect_event_count == baseline.MAX_FAMILY_EVENTS_PER_BUCKET
    assert row.connect_failure_count == baseline.MAX_FAMILY_EVENTS_PER_BUCKET
    assert not {
        "account_id",
        "tg_id",
        "install_id",
        "device_id",
        "session_id",
        "contributor_hash",
        "ip",
    } & set(models.ReleaseHealthCohortBucket.__table__.columns.keys())


def test_minimum_cohort_is_fail_closed_and_available_response_is_banded(session) -> None:
    for index in range(baseline.MINIMUM_COHORT_BUCKETS - 1):
        baseline.record_cohort_contribution(
            session,
            [_event() for _ in range(4)],
            contributor_key=f"account-{index}",
            secret=SECRET,
            now=NOW,
        )
    session.commit()

    hidden = baseline.client_baseline_snapshot(
        session,
        identity=_identity(),
        secret=SECRET,
        now=NOW,
    )
    assert hidden["state"] == "insufficient_cohort"
    assert hidden["baseline"] is None
    assert hidden["privacy"] == {
        "minimum_contributors": 10,
        "minimum_satisfied": False,
        "contribution_cap_per_window": 64,
    }
    assert "observed_contributors" not in str(hidden)

    baseline.record_cohort_contribution(
        session,
        [_event() for _ in range(4)],
        contributor_key="account-nine",
        secret=SECRET,
        now=NOW,
    )
    session.commit()
    visible = baseline.client_baseline_snapshot(
        session,
        identity=_identity(),
        secret=SECRET,
        now=NOW,
    )

    assert visible["state"] == "available"
    assert visible["privacy"]["minimum_satisfied"] is True
    assert visible["baseline"]["overall"] == {
        "state": "available",
        "sample_band": "30_to_99",
        "failure_rate_band": "none_observed",
    }
    assert visible["baseline"]["families"]["connect"] == visible["baseline"]["overall"]
    assert visible["baseline"]["families"]["crash"]["state"] == "insufficient_samples"
    rendered = str(visible)
    assert "account-" not in rendered
    assert "bucket_index" not in rendered
    assert "event_count" not in rendered
    assert "failure_count" not in rendered

    schema = json.loads(
        (
            REPO_ROOT
            / "shared/contracts/observability/release-health-baseline.v1.schema.json"
        ).read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    validator.validate(hidden)
    validator.validate(visible)


def test_week_and_cohort_rotation_prevent_cross_scope_linkage(session) -> None:
    baseline.record_cohort_contribution(
        session,
        [_event()],
        contributor_key="same-account",
        secret=SECRET,
        now=NOW,
    )
    baseline.record_cohort_contribution(
        session,
        [_event()],
        contributor_key="same-account",
        secret=SECRET,
        now=NOW + timedelta(hours=1),
    )
    next_week = NOW + timedelta(days=7)
    baseline.record_cohort_contribution(
        session,
        [_event()],
        contributor_key="same-account",
        secret=SECRET,
        now=next_week,
    )
    session.commit()

    rows = session.query(models.ReleaseHealthCohortBucket).all()
    assert len(rows) == 2
    assert rows[0].event_count == 2
    assert rows[0].window_started_at != rows[1].window_started_at


@pytest.mark.parametrize(
    "updates",
    [
        {"git_revision": "not-a-revision"},
        {"candidate_label": "foreign-candidate"},
        {"platform": "browser"},
        {"core_abi": 0},
        {"account_id": "forbidden"},
    ],
)
def test_scope_is_closed(updates: dict[str, object]) -> None:
    with pytest.raises(baseline.ReleaseHealthBaselineError) as caught:
        _identity(**updates)
    assert caught.value.reason == "baseline_scope_invalid"


def test_missing_or_short_privacy_secret_fails_closed(session) -> None:
    for secret in (None, "short"):
        with pytest.raises(baseline.ReleaseHealthBaselineError) as caught:
            baseline.client_baseline_snapshot(
                session,
                identity=_identity(),
                secret=secret,
                now=NOW,
            )
        assert caught.value.reason == "baseline_privacy_unavailable"
        assert caught.value.status_code == 503
