"""K-anonymous, contribution-capped release-health baseline projection."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

try:
    from .models import ReleaseHealthCohortBucket
except ImportError:
    from models import ReleaseHealthCohortBucket


MINIMUM_COHORT_BUCKETS = 10
MINIMUM_BASELINE_EVENTS = 30
MINIMUM_FAMILY_EVENTS = 10
COHORT_BUCKET_SPACE = 4096
MAX_EVENTS_PER_BUCKET = 64
MAX_FAMILY_EVENTS_PER_BUCKET = 32

_FAILURE_OUTCOMES = frozenset({"cancelled", "crashed", "failed", "timeout"})
_CHANNELS = frozenset({"alpha", "beta", "rc", "stable", "local"})
_PLATFORMS = frozenset({"android", "windows", "server"})
_VERSION = re.compile(r"^[0-9A-Za-z.+-]{1,64}$")
_BUILD = re.compile(r"^[A-Za-z0-9._+-]{1,32}$")
_CANDIDATE = re.compile(r"^pokrov-[A-Za-z0-9][A-Za-z0-9._+-]{1,63}$")
_REVISION = re.compile(r"^[0-9a-f]{40}$")
_ARCHITECTURE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,31}$")


class ReleaseHealthBaselineError(ValueError):
    def __init__(self, reason: str, *, status_code: int = 422) -> None:
        super().__init__(reason)
        self.reason = reason
        self.status_code = int(status_code)


@dataclass(frozen=True, slots=True)
class ReleaseHealthCohortIdentity:
    app_version: str
    build_number: str
    channel: str
    candidate_label: str
    git_revision: str
    core_abi: int | None
    platform: str
    architecture: str


def normalize_cohort_identity(payload: Mapping[str, Any]) -> ReleaseHealthCohortIdentity:
    allowed = {
        "app_version",
        "build_number",
        "channel",
        "candidate_label",
        "git_revision",
        "core_abi",
        "platform",
        "architecture",
    }
    if set(payload) != allowed:
        raise ReleaseHealthBaselineError("baseline_scope_invalid")

    app_version = _closed_text(payload["app_version"], _VERSION)
    build_number = _closed_text(payload["build_number"], _BUILD)
    candidate_label = _closed_text(payload["candidate_label"], _CANDIDATE)
    git_revision = _closed_text(payload["git_revision"], _REVISION)
    architecture = _closed_text(payload["architecture"], _ARCHITECTURE)
    channel = str(payload["channel"] or "").strip().lower()
    platform = str(payload["platform"] or "").strip().lower()
    if channel not in _CHANNELS or platform not in _PLATFORMS:
        raise ReleaseHealthBaselineError("baseline_scope_invalid")
    core_abi_value = payload["core_abi"]
    if core_abi_value is None:
        core_abi = None
    elif (
        isinstance(core_abi_value, bool)
        or not isinstance(core_abi_value, int)
        or core_abi_value < 1
        or core_abi_value > 2_147_483_647
    ):
        raise ReleaseHealthBaselineError("baseline_scope_invalid")
    else:
        core_abi = int(core_abi_value)
    return ReleaseHealthCohortIdentity(
        app_version=app_version,
        build_number=build_number,
        channel=channel,
        candidate_label=candidate_label,
        git_revision=git_revision,
        core_abi=core_abi,
        platform=platform,
        architecture=architecture,
    )


def cohort_identity_from_event(event: object) -> ReleaseHealthCohortIdentity:
    return normalize_cohort_identity(
        {
            "app_version": getattr(event, "app_version", None),
            "build_number": getattr(event, "build_number", None),
            "channel": getattr(event, "channel", None),
            "candidate_label": getattr(event, "candidate_label", None),
            "git_revision": getattr(event, "git_revision", None),
            "core_abi": getattr(event, "core_abi", None),
            "platform": getattr(event, "platform", None),
            "architecture": getattr(event, "architecture", None),
        }
    )


def cohort_fingerprint(identity: ReleaseHealthCohortIdentity) -> str:
    canonical = json.dumps(
        asdict(identity),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return hashlib.sha256(b"pokrov-release-health-cohort-v1\0" + canonical).hexdigest()


def utc_week_window(now: datetime | None = None) -> tuple[datetime, datetime]:
    current = _utc(now or datetime.now(timezone.utc))
    started = (current - timedelta(days=current.weekday())).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    return started, started + timedelta(days=7)


def record_cohort_contribution(
    session: Any,
    events: Iterable[object],
    *,
    contributor_key: object,
    secret: object,
    now: datetime | None = None,
) -> int:
    key = str(contributor_key or "").strip()
    secret_bytes = _secret_bytes(secret)
    if not key:
        raise ReleaseHealthBaselineError(
            "baseline_contributor_unavailable",
            status_code=403,
        )
    started, _ended = utc_week_window(now)
    grouped: dict[str, dict[str, int]] = defaultdict(_empty_counts)
    for event in events:
        identity = cohort_identity_from_event(event)
        fingerprint = cohort_fingerprint(identity)
        counters = grouped[fingerprint]
        counters["event_count"] += 1
        failed = str(getattr(event, "outcome", "")) in _FAILURE_OUTCOMES
        if failed:
            counters["failure_count"] += 1
        family = _event_family(event)
        if family is not None:
            counters[f"{family}_event_count"] += 1
            if failed:
                counters[f"{family}_failure_count"] += 1

    for fingerprint, counters in grouped.items():
        bucket_index = _bucket_index(
            contributor_key=key,
            cohort=fingerprint,
            window_started_at=started,
            secret=secret_bytes,
        )
        _upsert_bucket(
            session,
            cohort=fingerprint,
            window_started_at=started,
            bucket_index=bucket_index,
            counters=counters,
            now=_utc(now or datetime.now(timezone.utc)),
        )
    return len(grouped)


def client_baseline_snapshot(
    session: Any,
    *,
    identity: ReleaseHealthCohortIdentity,
    secret: object,
    now: datetime | None = None,
) -> dict[str, Any]:
    _secret_bytes(secret)
    started, ended = utc_week_window(now)
    rows = (
        session.query(ReleaseHealthCohortBucket)
        .filter(
            ReleaseHealthCohortBucket.cohort_fingerprint
            == cohort_fingerprint(identity),
            ReleaseHealthCohortBucket.window_started_at == started,
        )
        .all()
    )
    common = {
        "schema_version": 1,
        "scope": asdict(identity),
        "window": {
            "kind": "utc_week",
            "started_at": _iso(started),
            "ends_at": _iso(ended),
        },
        "privacy": {
            "minimum_contributors": MINIMUM_COHORT_BUCKETS,
            "minimum_satisfied": len(rows) >= MINIMUM_COHORT_BUCKETS,
            "contribution_cap_per_window": MAX_EVENTS_PER_BUCKET,
        },
    }
    if len(rows) < MINIMUM_COHORT_BUCKETS:
        return {**common, "state": "insufficient_cohort", "baseline": None}

    counts = _sum_rows(rows)
    if counts["event_count"] < MINIMUM_BASELINE_EVENTS:
        return {**common, "state": "insufficient_samples", "baseline": None}

    return {
        **common,
        "state": "available",
        "baseline": {
            "overall": _metric_band(
                counts["event_count"],
                counts["failure_count"],
                minimum=MINIMUM_BASELINE_EVENTS,
            ),
            "families": {
                family: _metric_band(
                    counts[f"{family}_event_count"],
                    counts[f"{family}_failure_count"],
                    minimum=MINIMUM_FAMILY_EVENTS,
                )
                for family in ("crash", "connect", "update")
            },
        },
    }


def _closed_text(value: object, pattern: re.Pattern[str]) -> str:
    text = str(value or "").strip()
    if pattern.fullmatch(text) is None:
        raise ReleaseHealthBaselineError("baseline_scope_invalid")
    return text


def _secret_bytes(secret: object) -> bytes:
    value = str(secret or "").encode("utf-8")
    if len(value) < 32:
        raise ReleaseHealthBaselineError(
            "baseline_privacy_unavailable",
            status_code=503,
        )
    return value


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return _utc(value).isoformat(timespec="seconds").replace("+00:00", "Z")


def _bucket_index(
    *,
    contributor_key: str,
    cohort: str,
    window_started_at: datetime,
    secret: bytes,
) -> int:
    message = (
        "pokrov-release-health-bucket-v1\0"
        + cohort
        + "\0"
        + _iso(window_started_at)
        + "\0"
        + contributor_key
    ).encode("utf-8")
    digest = hmac.new(secret, message, hashlib.sha256).digest()
    return int.from_bytes(digest[:8], byteorder="big") % COHORT_BUCKET_SPACE


def _empty_counts() -> dict[str, int]:
    return {
        "event_count": 0,
        "failure_count": 0,
        "crash_event_count": 0,
        "crash_failure_count": 0,
        "connect_event_count": 0,
        "connect_failure_count": 0,
        "update_event_count": 0,
        "update_failure_count": 0,
    }


def _event_family(event: object) -> str | None:
    values = {
        str(getattr(event, "component", "")),
        str(getattr(event, "subsystem", "")),
        str(getattr(event, "stage", "")),
    }
    code = str(getattr(event, "error_code", "") or "")
    name = str(getattr(event, "event_name", ""))
    if "crash" in values or code.startswith("CRASH-") or ".crash" in name:
        return "crash"
    if "update" in values or code.startswith("UPD-") or name.startswith("update."):
        return "update"
    if "connection" in values or "connect" in values or name.startswith("connection."):
        return "connect"
    return None


def _upsert_bucket(
    session: Any,
    *,
    cohort: str,
    window_started_at: datetime,
    bucket_index: int,
    counters: Mapping[str, int],
    now: datetime,
) -> None:
    values = {
        "cohort_fingerprint": cohort,
        "window_started_at": window_started_at,
        "bucket_index": int(bucket_index),
        **{
            key: min(
                MAX_EVENTS_PER_BUCKET
                if key in {"event_count", "failure_count"}
                else MAX_FAMILY_EVENTS_PER_BUCKET,
                max(0, int(value)),
            )
            for key, value in counters.items()
        },
        "updated_at": now,
    }
    dialect = str(session.get_bind().dialect.name or "").lower()
    if dialect == "sqlite":
        statement = sqlite_insert(ReleaseHealthCohortBucket).values(**values)
        capped = func.min
    elif dialect == "postgresql":
        statement = postgresql_insert(ReleaseHealthCohortBucket).values(**values)
        capped = func.least
    else:
        row = (
            session.query(ReleaseHealthCohortBucket)
            .filter(
                ReleaseHealthCohortBucket.cohort_fingerprint == cohort,
                ReleaseHealthCohortBucket.window_started_at == window_started_at,
                ReleaseHealthCohortBucket.bucket_index == bucket_index,
            )
            .with_for_update()
            .first()
        )
        if row is None:
            session.add(ReleaseHealthCohortBucket(**values))
        else:
            for key, value in counters.items():
                limit = (
                    MAX_EVENTS_PER_BUCKET
                    if key in {"event_count", "failure_count"}
                    else MAX_FAMILY_EVENTS_PER_BUCKET
                )
                setattr(row, key, min(limit, int(getattr(row, key) or 0) + int(value)))
            row.updated_at = now
        return

    updates = {"updated_at": now}
    for key in counters:
        limit = (
            MAX_EVENTS_PER_BUCKET
            if key in {"event_count", "failure_count"}
            else MAX_FAMILY_EVENTS_PER_BUCKET
        )
        updates[key] = capped(
            limit,
            getattr(ReleaseHealthCohortBucket, key) + getattr(statement.excluded, key),
        )
    session.execute(
        statement.on_conflict_do_update(
            index_elements=["cohort_fingerprint", "window_started_at", "bucket_index"],
            set_=updates,
        )
    )


def _sum_rows(rows: Iterable[ReleaseHealthCohortBucket]) -> dict[str, int]:
    result = _empty_counts()
    for row in rows:
        for key in result:
            result[key] += max(0, int(getattr(row, key) or 0))
    return result


def _metric_band(events: int, failures: int, *, minimum: int) -> dict[str, Any]:
    if events < minimum:
        return {
            "state": "insufficient_samples",
            "sample_band": None,
            "failure_rate_band": None,
        }
    if events < 30:
        sample_band = "10_to_29"
    elif events < 100:
        sample_band = "30_to_99"
    elif events < 500:
        sample_band = "100_to_499"
    else:
        sample_band = "500_plus"
    basis_points = (max(0, failures) * 10_000) // max(1, events)
    if basis_points == 0:
        failure_band = "none_observed"
    elif basis_points < 100:
        failure_band = "below_1_percent"
    elif basis_points < 500:
        failure_band = "1_to_below_5_percent"
    elif basis_points < 2_000:
        failure_band = "5_to_below_20_percent"
    else:
        failure_band = "20_percent_or_more"
    return {
        "state": "available",
        "sample_band": sample_band,
        "failure_rate_band": failure_band,
    }
