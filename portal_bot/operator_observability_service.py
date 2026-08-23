"""Privacy-bounded release health and support-bundle operator read models."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from sqlalchemy import or_

try:
    from .models import (
        ReleaseHealthEvent,
        ReleaseKnownIssue,
        SupportBundleAccessAudit,
        SupportBundleChunk,
        SupportBundleUpload,
    )
except ImportError:
    from models import (
        ReleaseHealthEvent,
        ReleaseKnownIssue,
        SupportBundleAccessAudit,
        SupportBundleChunk,
        SupportBundleUpload,
    )


_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
_ISSUE_CODE = re.compile(r"^[A-Z][A-Z0-9_-]{2,31}$")
_VERSION = re.compile(r"^[0-9A-Za-z.+-]{1,64}$")
_BUILD = re.compile(r"^[0-9A-Za-z._-]{1,80}$")
_CANDIDATE = re.compile(r"^[0-9A-Za-z._-]{1,64}$")
_REFERENCE = re.compile(r"^[0-9A-Za-z._:/-]{1,64}$")
_OBJECT_NAME = re.compile(r"^(?P<upload>[0-9a-f-]{36})\.pokrov-support$")
_CHUNK_NAME = re.compile(
    r"^(?P<upload>[0-9a-f-]{36})\.(?P<offset>[0-9]{10})\.(?P<digest>[0-9a-f]{16})\.chunk$"
)
_FAILURE_OUTCOMES = frozenset({"cancelled", "crashed", "failed", "timeout"})
_ISSUE_SEVERITIES = frozenset({"info", "warn", "error", "fatal"})
_ISSUE_STATUSES = frozenset({"open", "monitoring", "mitigated", "resolved"})
_ISSUE_PLATFORMS = frozenset({"all", "android", "windows"})
_ACCESS_REASONS = frozenset(
    {"customer_case", "incident_review", "release_validation", "security_review"}
)


def _load_known_error_codes() -> frozenset[str]:
    path = (
        Path(__file__).resolve().parents[1]
        / "shared/contracts/observability/error-catalog.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1 or not isinstance(payload.get("entries"), list):
        raise RuntimeError("observability_error_catalog_invalid")
    codes = frozenset(
        str(entry.get("code") or "")
        for entry in payload["entries"]
        if isinstance(entry, Mapping)
    )
    if not codes or "CORE-001" not in codes or "CRASH-001" not in codes:
        raise RuntimeError("observability_error_catalog_invalid")
    return codes


_KNOWN_ERROR_CODES = _load_known_error_codes()


class OperatorObservabilityError(ValueError):
    def __init__(self, code: str, *, status_code: int = 422) -> None:
        super().__init__(code)
        self.code = code
        self.status_code = int(status_code)


@dataclass(frozen=True, slots=True)
class BundleAccessGrant:
    upload_id: str
    ticket_id: int
    token: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class BundleAccessObject:
    upload_id: str
    ticket_id: int
    object_name: str
    path: Path
    expected_size_bytes: int
    expected_sha256: str
    content_type: str


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_privileged_actor_ids(raw: object) -> frozenset[int]:
    values: set[int] = set()
    for item in str(raw or "").split(","):
        text = item.strip()
        if not text:
            continue
        if re.fullmatch(r"[1-9][0-9]{0,18}", text) is None:
            raise OperatorObservabilityError(
                "support_operator_role_config_invalid", status_code=503
            )
        values.add(int(text))
    return frozenset(values)


def operator_role(actor_tg_id: int, privileged_ids: Iterable[int]) -> str:
    return (
        "l2_sre"
        if int(actor_tg_id) in {int(value) for value in privileged_ids}
        else "l1"
    )


def require_l2(actor_tg_id: int, privileged_ids: Iterable[int]) -> None:
    if operator_role(actor_tg_id, privileged_ids) != "l2_sre":
        raise OperatorObservabilityError("support_bundle_l2_required", status_code=403)


def support_bundle_summary(session, *, upload_id: str) -> dict[str, Any]:
    row = _upload_row(session, upload_id)
    timeline = [{"phase": "issued", "at": _iso(row.created_at)}]
    if int(row.received_size_bytes or 0) > 0:
        timeline.append({"phase": "uploading", "at": _iso(row.updated_at)})
    if row.completed_at is not None:
        timeline.append({"phase": "queued", "at": _iso(row.completed_at)})
    if row.validated_at is not None:
        timeline.append({"phase": str(row.status), "at": _iso(row.validated_at)})
    return {
        "upload_id": row.upload_id,
        "ticket_id": int(row.ticket_id),
        "diagnostic_id": row.bundle_id,
        "status": row.status,
        "failure_code": row.failure_code,
        "profile": row.diagnostic_profile,
        "build": {
            "app_version": row.app_version,
            "build_number": row.build_number,
            "platform": row.platform,
            "architecture": row.architecture,
        },
        "last_phase": row.last_phase,
        "last_error_code": row.last_error_code,
        "proof_outcome": row.proof_outcome,
        "observed_attempts": row.observed_attempts,
        "bytes": {
            "expected": int(row.expected_size_bytes),
            "received": int(row.received_size_bytes),
        },
        "retention_hold": bool(row.retention_hold),
        "timeline": timeline,
    }


def issue_bundle_access_grant(
    session,
    *,
    upload_id: str,
    actor_tg_id: int,
    privileged_ids: Iterable[int],
    reason_code: object,
    actor_role: str = "l2_sre",
    now: datetime | None = None,
    ttl_seconds: int = 600,
) -> BundleAccessGrant:
    require_l2(actor_tg_id, privileged_ids)
    row = _upload_row(session, upload_id)
    if row.status != "validated" or not row.object_name:
        raise OperatorObservabilityError(
            "support_bundle_not_available", status_code=409
        )
    reason = _choice(reason_code, _ACCESS_REASONS, "support_bundle_reason_invalid")
    normalized_role = str(actor_role or "").strip().lower()
    if normalized_role not in {
        "l2_sre",
        "support_l2",
        "sre",
        "security_auditor",
        "superadmin",
    }:
        raise OperatorObservabilityError("support_bundle_actor_role_invalid")
    ttl = max(60, min(int(ttl_seconds), 900))
    current = now or utcnow()
    token = secrets.token_urlsafe(32)
    expires_at = current + timedelta(seconds=ttl)
    session.add(
        SupportBundleAccessAudit(
            grant_id=str(uuid.uuid4()),
            upload_id=row.upload_id,
            ticket_id=int(row.ticket_id),
            actor_tg_id=int(actor_tg_id),
            actor_role=normalized_role,
            action="grant_issued",
            reason_code=reason,
            access_token_hash=_token_hash(token),
            expires_at=expires_at,
            retention_hold=bool(row.retention_hold),
            created_at=current,
        )
    )
    session.flush()
    return BundleAccessGrant(
        upload_id=row.upload_id,
        ticket_id=int(row.ticket_id),
        token=token,
        expires_at=expires_at,
    )


def consume_bundle_access_grant(
    session,
    *,
    upload_id: str,
    token: object,
    actor_tg_id: int,
    privileged_ids: Iterable[int],
    accepted_root: Path,
    now: datetime | None = None,
) -> BundleAccessObject:
    require_l2(actor_tg_id, privileged_ids)
    current = now or utcnow()
    token_hash = _token_hash(str(token or ""))
    grant = (
        session.query(SupportBundleAccessAudit)
        .filter(
            SupportBundleAccessAudit.upload_id == str(upload_id),
            SupportBundleAccessAudit.actor_tg_id == int(actor_tg_id),
            SupportBundleAccessAudit.action == "grant_issued",
            SupportBundleAccessAudit.access_token_hash == token_hash,
        )
        .first()
    )
    if grant is None or grant.used_at is not None or grant.expires_at <= current:
        raise OperatorObservabilityError(
            "support_bundle_access_grant_invalid", status_code=403
        )
    row = _upload_row(session, upload_id)
    if row.status != "validated" or not row.object_name:
        raise OperatorObservabilityError(
            "support_bundle_not_available", status_code=409
        )
    path = _owned_object_path(accepted_root, row.upload_id, row.object_name)
    if path.stat().st_size != int(row.expected_size_bytes):
        raise OperatorObservabilityError(
            "support_bundle_object_invalid", status_code=503
        )
    actual_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    if not hmac.compare_digest(actual_sha256, str(row.expected_sha256)):
        raise OperatorObservabilityError(
            "support_bundle_object_invalid", status_code=503
        )
    claimed = (
        session.query(SupportBundleAccessAudit)
        .filter(
            SupportBundleAccessAudit.id == int(grant.id),
            SupportBundleAccessAudit.used_at.is_(None),
            SupportBundleAccessAudit.access_token_hash == token_hash,
            SupportBundleAccessAudit.expires_at > current,
        )
        .update(
            {
                SupportBundleAccessAudit.used_at: current,
                SupportBundleAccessAudit.access_token_hash: None,
            },
            synchronize_session=False,
        )
    )
    if int(claimed or 0) != 1:
        raise OperatorObservabilityError(
            "support_bundle_access_grant_invalid", status_code=403
        )
    session.add(
        SupportBundleAccessAudit(
            grant_id=str(uuid.uuid4()),
            upload_id=row.upload_id,
            ticket_id=int(row.ticket_id),
            actor_tg_id=int(actor_tg_id),
            actor_role=str(grant.actor_role),
            action="downloaded",
            reason_code=grant.reason_code,
            access_token_hash=None,
            expires_at=current,
            used_at=current,
            retention_hold=bool(row.retention_hold),
            created_at=current,
        )
    )
    session.flush()
    return BundleAccessObject(
        upload_id=row.upload_id,
        ticket_id=int(row.ticket_id),
        object_name=row.object_name,
        path=path,
        expected_size_bytes=int(row.expected_size_bytes),
        expected_sha256=row.expected_sha256,
        content_type=row.content_type,
    )


def set_bundle_retention_hold(
    session,
    *,
    upload_id: str,
    actor_tg_id: int,
    privileged_ids: Iterable[int],
    hold: bool,
    reason_code: object,
    now: datetime | None = None,
) -> dict[str, Any]:
    require_l2(actor_tg_id, privileged_ids)
    row = _upload_row(session, upload_id)
    current = now or utcnow()
    reason = _choice(reason_code, _ACCESS_REASONS, "support_bundle_reason_invalid")
    row.retention_hold = bool(hold)
    row.retention_hold_reason = reason if hold else None
    row.retention_held_at = current if hold else None
    (
        session.query(SupportBundleAccessAudit)
        .filter(SupportBundleAccessAudit.upload_id == row.upload_id)
        .update(
            {SupportBundleAccessAudit.retention_hold: bool(hold)},
            synchronize_session=False,
        )
    )
    session.add(
        SupportBundleAccessAudit(
            grant_id=str(uuid.uuid4()),
            upload_id=row.upload_id,
            ticket_id=int(row.ticket_id),
            actor_tg_id=int(actor_tg_id),
            actor_role="l2_sre",
            action="retention_hold_set" if hold else "retention_hold_cleared",
            reason_code=reason,
            access_token_hash=None,
            expires_at=current,
            used_at=current,
            retention_hold=bool(hold),
            created_at=current,
        )
    )
    session.flush()
    return support_bundle_summary(session, upload_id=row.upload_id)


def release_health_snapshot(
    session,
    *,
    hours: int = 24,
    now: datetime | None = None,
    row_limit: int = 10_000,
) -> dict[str, Any]:
    window_hours = max(1, min(int(hours), 168))
    limit = max(100, min(int(row_limit), 20_000))
    current = now or utcnow()
    start = current - timedelta(hours=window_hours)
    previous_start = start - timedelta(hours=window_hours)
    rows = (
        session.query(ReleaseHealthEvent)
        .filter(ReleaseHealthEvent.received_at >= previous_start)
        .order_by(ReleaseHealthEvent.received_at.desc(), ReleaseHealthEvent.id.desc())
        .limit(limit)
        .all()
    )
    current_rows = [row for row in rows if row.received_at >= start]
    previous_rows = [row for row in rows if row.received_at < start]
    current_groups = _health_groups(current_rows)
    previous_groups = _health_groups(previous_rows)
    output = []
    for key in sorted(current_groups):
        item = current_groups[key]
        prior = previous_groups.get(key, _empty_health_counts())
        output.append(
            {
                **dict(zip(_HEALTH_KEY_FIELDS, key, strict=True)),
                **item,
                "delta": {
                    name: item[name] - prior[name]
                    for name in (
                        "crash_failures",
                        "connect_failures",
                        "update_failures",
                    )
                },
            }
        )
    return {
        "window_hours": window_hours,
        "window_start": _iso(start),
        "observed_rows": len(rows),
        "truncated": len(rows) == limit,
        "groups": output,
    }


_HEALTH_KEY_FIELDS = (
    "app_version",
    "build_number",
    "channel",
    "candidate_label",
    "git_revision",
    "core_abi",
    "platform",
    "architecture",
)


def _health_groups(
    rows: Iterable[ReleaseHealthEvent],
) -> dict[tuple[str, ...], dict[str, int]]:
    result: dict[tuple[str, ...], dict[str, int]] = defaultdict(_empty_health_counts)
    for row in rows:
        key = tuple(str(getattr(row, field)) for field in _HEALTH_KEY_FIELDS)
        counters = result[key]
        counters["events"] += 1
        failed = row.outcome in _FAILURE_OUTCOMES
        if failed:
            counters["failures"] += 1
        family = _event_family(row)
        if family:
            counters[f"{family}_events"] += 1
            if failed:
                counters[f"{family}_failures"] += 1
        if (
            row.selected_app_count is not None
            and row.component == "app"
            and row.subsystem == "routing"
            and row.stage == "complete"
            and row.event_name == "app.routing.selection.finished"
            and row.outcome == "observed"
            and row.platform == "android"
        ):
            counters["routing_count_events"] += 1
            counters["selected_app_count_total"] += int(row.selected_app_count)
    return dict(result)


def _empty_health_counts() -> dict[str, int]:
    return {
        "events": 0,
        "failures": 0,
        "crash_events": 0,
        "crash_failures": 0,
        "connect_events": 0,
        "connect_failures": 0,
        "update_events": 0,
        "update_failures": 0,
        "routing_count_events": 0,
        "selected_app_count_total": 0,
    }


def _event_family(row: ReleaseHealthEvent) -> str | None:
    values = {str(row.component), str(row.subsystem), str(row.stage)}
    code = str(row.error_code or "")
    name = str(row.event_name)
    if "crash" in values or code.startswith("CRASH-") or ".crash" in name:
        return "crash"
    if "update" in values or code.startswith("UPD-") or name.startswith("update."):
        return "update"
    if "connection" in values or "connect" in values or name.startswith("connection."):
        return "connect"
    return None


def upsert_known_issue(
    session,
    *,
    actor_tg_id: int,
    payload: Mapping[str, Any],
    now: datetime | None = None,
) -> dict[str, Any]:
    normalized = _known_issue_payload(payload)
    row = (
        session.query(ReleaseKnownIssue)
        .filter(
            ReleaseKnownIssue.candidate_label == normalized["candidate_label"],
            ReleaseKnownIssue.issue_code == normalized["issue_code"],
        )
        .first()
    )
    current = now or utcnow()
    if row is None:
        row = ReleaseKnownIssue(
            **normalized,
            created_by_tg_id=int(actor_tg_id),
            updated_by_tg_id=int(actor_tg_id),
            created_at=current,
            updated_at=current,
        )
        session.add(row)
    else:
        for field, value in normalized.items():
            setattr(row, field, value)
        row.updated_by_tg_id = int(actor_tg_id)
        row.updated_at = current
    session.flush()
    return _known_issue_view(row)


def known_issues(
    session,
    *,
    candidate_label: str | None = None,
    status: str | None = None,
    error_code: str | None = None,
    app_version: str | None = None,
    build_number: str | None = None,
    platform: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = session.query(ReleaseKnownIssue)
    if candidate_label is not None:
        candidate = _pattern(
            candidate_label, _CANDIDATE, "known_issue_candidate_invalid"
        )
        query = query.filter(ReleaseKnownIssue.candidate_label == candidate)
    if status is not None:
        normalized_status = _choice(
            status, _ISSUE_STATUSES, "known_issue_status_invalid"
        )
        query = query.filter(ReleaseKnownIssue.status == normalized_status)
    if error_code is not None:
        query = query.filter(ReleaseKnownIssue.error_code == _known_error_code(error_code))
    if app_version is not None:
        query = query.filter(
            ReleaseKnownIssue.app_version
            == _pattern(app_version, _VERSION, "known_issue_version_invalid")
        )
    if build_number is not None:
        normalized_build = _pattern(
            build_number, _BUILD, "known_issue_build_invalid"
        )
        query = query.filter(
            or_(
                ReleaseKnownIssue.build_number.is_(None),
                ReleaseKnownIssue.build_number == normalized_build,
            )
        )
    if platform is not None:
        normalized_platform = _choice(
            platform, _ISSUE_PLATFORMS, "known_issue_platform_invalid"
        )
        query = query.filter(
            ReleaseKnownIssue.platform.in_({"all", normalized_platform})
        )
    rows = (
        query.order_by(ReleaseKnownIssue.updated_at.desc(), ReleaseKnownIssue.id.desc())
        .limit(max(1, min(int(limit), 200)))
        .all()
    )
    return [_known_issue_view(row) for row in rows]


def run_operator_retention_once(
    session,
    *,
    now: datetime,
    quarantine_root: Path | None,
    accepted_root: Path | None,
    release_health_days: int = 90,
    accepted_bundle_days: int = 30,
    rejected_bundle_days: int = 7,
    incomplete_grace_days: int = 1,
    access_audit_days: int = 365,
    batch_limit: int = 100,
) -> dict[str, int]:
    limit = max(1, min(int(batch_limit), 1000))
    counters = {
        "release_health_events_deleted": 0,
        "bundle_rows_deleted": 0,
        "accepted_objects_deleted": 0,
        "quarantine_chunks_deleted": 0,
        "access_audits_deleted": 0,
        "held_bundles_skipped": 0,
        "held_audits_skipped": 0,
        "files_missing": 0,
        "file_errors": 0,
    }
    health_ids = [
        row[0]
        for row in session.query(ReleaseHealthEvent.id)
        .filter(
            ReleaseHealthEvent.received_at
            < now - timedelta(days=max(1, int(release_health_days)))
        )
        .order_by(ReleaseHealthEvent.id.asc())
        .limit(limit)
        .all()
    ]
    if health_ids:
        counters["release_health_events_deleted"] = int(
            session.query(ReleaseHealthEvent)
            .filter(ReleaseHealthEvent.id.in_(health_ids))
            .delete(synchronize_session=False)
            or 0
        )

    audit_cutoff = now - timedelta(days=max(1, int(access_audit_days)))
    counters["held_audits_skipped"] = int(
        session.query(SupportBundleAccessAudit)
        .filter(
            SupportBundleAccessAudit.created_at < audit_cutoff,
            SupportBundleAccessAudit.retention_hold.is_(True),
        )
        .count()
    )
    audit_ids = [
        row[0]
        for row in session.query(SupportBundleAccessAudit.id)
        .filter(
            SupportBundleAccessAudit.created_at < audit_cutoff,
            SupportBundleAccessAudit.retention_hold.is_(False),
        )
        .order_by(SupportBundleAccessAudit.id.asc())
        .limit(limit)
        .all()
    ]
    if audit_ids:
        counters["access_audits_deleted"] = int(
            session.query(SupportBundleAccessAudit)
            .filter(SupportBundleAccessAudit.id.in_(audit_ids))
            .delete(synchronize_session=False)
            or 0
        )

    eligible = _eligible_bundle_query(
        session,
        now=now,
        accepted_days=accepted_bundle_days,
        rejected_days=rejected_bundle_days,
        incomplete_grace_days=incomplete_grace_days,
    )
    counters["held_bundles_skipped"] = int(
        eligible.filter(SupportBundleUpload.retention_hold.is_(True)).count()
    )
    rows = (
        eligible.filter(SupportBundleUpload.retention_hold.is_(False))
        .order_by(SupportBundleUpload.id.asc())
        .limit(limit)
        .all()
    )
    if rows and (quarantine_root is None or accepted_root is None):
        counters["file_errors"] += len(rows)
        return counters
    for row in rows:
        try:
            if row.status == "validated" and row.object_name:
                path = _owned_deletion_path(
                    accepted_root,
                    row.object_name,
                    pattern=_OBJECT_NAME,
                    upload_id=row.upload_id,
                )
                if path.exists():
                    if path.is_symlink() or not path.is_file():
                        raise OperatorObservabilityError(
                            "support_bundle_object_invalid"
                        )
                    path.unlink()
                    counters["accepted_objects_deleted"] += 1
                else:
                    counters["files_missing"] += 1
            chunks = (
                session.query(SupportBundleChunk)
                .filter(SupportBundleChunk.upload_id == int(row.id))
                .all()
            )
            for chunk in chunks:
                target = _owned_deletion_path(
                    quarantine_root,
                    chunk.stored_name,
                    pattern=_CHUNK_NAME,
                    upload_id=row.upload_id,
                )
                if target.exists():
                    if target.is_symlink() or not target.is_file():
                        raise OperatorObservabilityError(
                            "support_bundle_chunk_path_invalid"
                        )
                    target.unlink()
                    counters["quarantine_chunks_deleted"] += 1
                else:
                    counters["files_missing"] += 1
            session.query(SupportBundleChunk).filter(
                SupportBundleChunk.upload_id == int(row.id)
            ).delete(synchronize_session=False)
            session.delete(row)
            counters["bundle_rows_deleted"] += 1
        except (OSError, OperatorObservabilityError):
            counters["file_errors"] += 1
    session.flush()
    return counters


def _eligible_bundle_query(
    session,
    *,
    now: datetime,
    accepted_days: int,
    rejected_days: int,
    incomplete_grace_days: int,
):
    from sqlalchemy import and_, or_

    return session.query(SupportBundleUpload).filter(
        or_(
            and_(
                SupportBundleUpload.status == "validated",
                SupportBundleUpload.validated_at
                < now - timedelta(days=max(1, int(accepted_days))),
            ),
            and_(
                SupportBundleUpload.status.in_(("rejected", "queued")),
                SupportBundleUpload.updated_at
                < now - timedelta(days=max(1, int(rejected_days))),
            ),
            and_(
                SupportBundleUpload.status.in_(("issued", "uploading")),
                SupportBundleUpload.expires_at
                < now - timedelta(days=max(0, int(incomplete_grace_days))),
            ),
        )
    )


def _known_issue_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    expected = frozenset(
        {
            "candidate_label",
            "issue_code",
            "app_version",
            "build_number",
            "platform",
            "severity",
            "status",
            "title",
            "safe_summary",
            "error_code",
            "incident_ref",
            "release_ref",
        }
    )
    if set(payload) != expected:
        raise OperatorObservabilityError("known_issue_shape_invalid")
    build_number = payload.get("build_number")
    error_code = payload.get("error_code")
    incident_ref = payload.get("incident_ref")
    release_ref = payload.get("release_ref")
    return {
        "candidate_label": _pattern(
            payload.get("candidate_label"), _CANDIDATE, "known_issue_candidate_invalid"
        ),
        "issue_code": _pattern(
            payload.get("issue_code"), _ISSUE_CODE, "known_issue_code_invalid"
        ),
        "app_version": _pattern(
            payload.get("app_version"), _VERSION, "known_issue_version_invalid"
        ),
        "build_number": None
        if build_number is None
        else _pattern(build_number, _BUILD, "known_issue_build_invalid"),
        "platform": _choice(
            payload.get("platform"), _ISSUE_PLATFORMS, "known_issue_platform_invalid"
        ),
        "severity": _choice(
            payload.get("severity"), _ISSUE_SEVERITIES, "known_issue_severity_invalid"
        ),
        "status": _choice(
            payload.get("status"), _ISSUE_STATUSES, "known_issue_status_invalid"
        ),
        "title": _safe_text(payload.get("title"), 120, "known_issue_title_invalid"),
        "safe_summary": _safe_text(
            payload.get("safe_summary"), 500, "known_issue_summary_invalid"
        ),
        "error_code": _known_error_code(error_code),
        "incident_ref": None
        if incident_ref is None
        else _pattern(incident_ref, _REFERENCE, "known_issue_incident_ref_invalid"),
        "release_ref": None
        if release_ref is None
        else _pattern(release_ref, _REFERENCE, "known_issue_release_ref_invalid"),
    }


def _known_error_code(value: object) -> str:
    code = _pattern(value, _ISSUE_CODE, "known_issue_error_required")
    if code not in _KNOWN_ERROR_CODES:
        raise OperatorObservabilityError("known_issue_error_invalid")
    return code


def _known_issue_view(row: ReleaseKnownIssue) -> dict[str, Any]:
    return {
        "candidate_label": row.candidate_label,
        "issue_code": row.issue_code,
        "app_version": row.app_version,
        "build_number": row.build_number,
        "platform": row.platform,
        "severity": row.severity,
        "status": row.status,
        "title": row.title,
        "safe_summary": row.safe_summary,
        "error_code": row.error_code,
        "incident_ref": row.incident_ref,
        "release_ref": row.release_ref,
        "updated_at": _iso(row.updated_at),
    }


def _upload_row(session, upload_id: object) -> SupportBundleUpload:
    normalized = str(upload_id or "").strip().lower()
    if _UUID.fullmatch(normalized) is None:
        raise OperatorObservabilityError("support_bundle_upload_id_invalid")
    row = (
        session.query(SupportBundleUpload)
        .filter(SupportBundleUpload.upload_id == normalized)
        .first()
    )
    if row is None:
        raise OperatorObservabilityError("support_bundle_not_found", status_code=404)
    return row


def _private_root(value: Path | None) -> Path:
    if value is None:
        raise OperatorObservabilityError(
            "support_bundle_storage_unavailable", status_code=503
        )
    root = Path(value)
    if (
        not root.is_absolute()
        or not root.exists()
        or not root.is_dir()
        or root.is_symlink()
    ):
        raise OperatorObservabilityError(
            "support_bundle_storage_unavailable", status_code=503
        )
    if callable(getattr(root, "is_junction", None)) and root.is_junction():
        raise OperatorObservabilityError(
            "support_bundle_storage_unavailable", status_code=503
        )
    return root.resolve(strict=True)


def _owned_object_path(
    root_value: Path | None, upload_id: str, object_name: str
) -> Path:
    root = _private_root(root_value)
    match = _OBJECT_NAME.fullmatch(str(object_name))
    if match is None or match.group("upload") != upload_id:
        raise OperatorObservabilityError(
            "support_bundle_object_invalid", status_code=503
        )
    candidate = root / object_name
    if candidate.is_symlink() or (
        callable(getattr(candidate, "is_junction", None)) and candidate.is_junction()
    ):
        raise OperatorObservabilityError(
            "support_bundle_object_invalid", status_code=503
        )
    path = candidate.resolve(strict=True)
    if path.parent != root or not path.is_file():
        raise OperatorObservabilityError(
            "support_bundle_object_invalid", status_code=503
        )
    return path


def _owned_deletion_path(
    root_value: Path | None,
    name: object,
    *,
    pattern: re.Pattern[str],
    upload_id: str,
) -> Path:
    root = _private_root(root_value)
    normalized = str(name)
    match = pattern.fullmatch(normalized)
    if match is None or match.group("upload") != upload_id:
        raise OperatorObservabilityError("support_bundle_storage_name_invalid")
    candidate = root / normalized
    if candidate.is_symlink() or (
        callable(getattr(candidate, "is_junction", None)) and candidate.is_junction()
    ):
        raise OperatorObservabilityError("support_bundle_storage_name_invalid")
    path = candidate.resolve(strict=False)
    if path.parent != root:
        raise OperatorObservabilityError("support_bundle_storage_name_invalid")
    return path


def _token_hash(token: str) -> str:
    if (
        not isinstance(token, str)
        or not 32 <= len(token) <= 128
        or re.fullmatch(r"[0-9A-Za-z_-]+", token) is None
    ):
        raise OperatorObservabilityError(
            "support_bundle_access_grant_invalid", status_code=403
        )
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def _choice(value: object, allowed: frozenset[str], code: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized not in allowed:
        raise OperatorObservabilityError(code)
    return normalized


def _pattern(value: object, pattern: re.Pattern[str], code: str) -> str:
    normalized = str(value or "").strip()
    if pattern.fullmatch(normalized) is None:
        raise OperatorObservabilityError(code)
    return normalized


def _safe_text(value: object, maximum: int, code: str) -> str:
    normalized = " ".join(str(value or "").strip().split())
    if not 3 <= len(normalized) <= maximum or any(
        ord(char) < 32 for char in normalized
    ):
        raise OperatorObservabilityError(code)
    lowered = normalized.lower()
    if any(
        marker in lowered
        for marker in (
            "http://",
            "https://",
            "bearer ",
            "authorization",
            "cookie",
            "token=",
        )
    ):
        raise OperatorObservabilityError(code)
    return normalized


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
