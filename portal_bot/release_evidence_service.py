from __future__ import annotations

import base64
import hashlib
import json
import re
import struct
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping

from sqlalchemy.exc import IntegrityError

try:
    from models import (
        ReleaseCandidate,
        ReleaseOriginEvidence,
        RuProbeRun,
        RuProbeTargetResult,
    )
except ImportError:  # pragma: no cover - package import
    from .models import (
        ReleaseCandidate,
        ReleaseOriginEvidence,
        RuProbeRun,
        RuProbeTargetResult,
    )


ALLOWED_STATUSES = frozenset(
    {
        "PASS",
        "FAIL",
        "MANUAL_OWNER_TEST",
        "OPERATOR_ATTESTED",
        "SKIPPED_BY_OWNER",
        "SKIPPED_BY_OPERATOR",
        "BLOCKED_BY_ACCESS",
        "MISSING",
    }
)
REQUIRED_ORIGINS = ("current", "brain", "ru")
DEFAULT_PAGE_LIMIT = 50
MAX_PAGE_LIMIT = 100

_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_COMPONENT_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}\Z")
_REVISION_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_CHECK_RE = re.compile(r"[a-z0-9][a-z0-9._:-]{0,127}\Z")
_DETAIL_KEY_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
_CURSOR_RE = re.compile(r"[A-Za-z0-9_-]+\Z")
_UNSAFE_DETAIL_KEYS = frozenset(
    {
        "authorization",
        "client_secret",
        "cookie",
        "credential",
        "credentials",
        "password",
        "payload",
        "private_key",
        "provider_payload",
        "raw",
        "raw_body",
        "raw_payload",
        "secret",
        "signature",
        "signing_key",
        "token",
    }
)
_STATUS_PRECEDENCE = {
    "FAIL": 0,
    "BLOCKED_BY_ACCESS": 1,
    "MISSING": 2,
    "MANUAL_OWNER_TEST": 3,
    "OPERATOR_ATTESTED": 4,
    "SKIPPED_BY_OWNER": 5,
    "SKIPPED_BY_OPERATOR": 6,
    "PASS": 7,
}


class ReleaseEvidenceError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = str(code)
        super().__init__(self.code)


class ReleaseEvidenceValidationError(ReleaseEvidenceError):
    pass


class ReleaseEvidenceConflict(ReleaseEvidenceError):
    pass


class ReleaseEvidenceNotFound(ReleaseEvidenceError):
    pass


class ReleaseEvidenceReadError(ReleaseEvidenceError):
    pass


@dataclass(frozen=True)
class ReleaseEvidenceImportResult:
    candidate_id: str
    created: bool
    candidate_created: bool
    evidence_created: int


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def compute_candidate_id(candidate: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_json(dict(candidate)).encode("utf-8")).hexdigest()


def _fail(code: str) -> None:
    raise ReleaseEvidenceValidationError(code)


def _plain_string(value: object, *, maximum: int, code: str) -> str:
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= maximum
        or value != value.strip()
        or any(ord(character) < 0x20 for character in value)
    ):
        _fail(code)
    return value


def _utc(value: datetime, *, code: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        _fail(code)
    return value.astimezone(timezone.utc)


def _timestamp(value: object, *, code: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z") or len(value) > 40:
        _fail(code)
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except (ValueError, OverflowError):
        _fail(code)
    return _utc(parsed, code=code)


def _normalize_detail(value: object, *, depth: int = 0) -> object:
    if depth > 4:
        _fail("invalid_detail")
    if value is None or isinstance(value, (bool, int, float)):
        if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
            _fail("invalid_detail")
        return value
    if isinstance(value, str):
        if len(value) > 500 or any(ord(character) < 0x20 and character not in "\t\n\r" for character in value):
            _fail("invalid_detail")
        return value
    if isinstance(value, list):
        if len(value) > 32:
            _fail("invalid_detail")
        return [_normalize_detail(item, depth=depth + 1) for item in value]
    if isinstance(value, dict):
        if len(value) > 32:
            _fail("invalid_detail")
        result: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str) or _DETAIL_KEY_RE.fullmatch(key) is None:
                _fail("invalid_detail")
            normalized_key = key.lower().replace("-", "_")
            if normalized_key in _UNSAFE_DETAIL_KEYS or normalized_key.endswith("_secret"):
                _fail("unsafe_detail")
            result[key] = _normalize_detail(item, depth=depth + 1)
        return result
    _fail("invalid_detail")
    raise AssertionError("unreachable")


def _validated_candidate(value: object) -> tuple[dict[str, str], str, str]:
    if not isinstance(value, dict) or set(value) != {
        "component",
        "version",
        "revision",
        "artifact_sha256",
    }:
        _fail("invalid_candidate")
    component = _plain_string(value["component"], maximum=64, code="invalid_candidate")
    version = _plain_string(value["version"], maximum=128, code="invalid_candidate")
    revision = _plain_string(value["revision"], maximum=128, code="invalid_candidate")
    artifact_sha256 = _plain_string(
        value["artifact_sha256"], maximum=64, code="invalid_candidate"
    )
    if _COMPONENT_RE.fullmatch(component) is None:
        _fail("invalid_candidate")
    if _REVISION_RE.fullmatch(revision) is None:
        _fail("invalid_candidate")
    if _SHA256_RE.fullmatch(artifact_sha256) is None:
        _fail("invalid_candidate")
    descriptor = {
        "component": component,
        "version": version,
        "revision": revision,
        "artifact_sha256": artifact_sha256,
    }
    canonical = canonical_json(descriptor)
    descriptor_sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return descriptor, canonical, descriptor_sha256


def _validated_evidence(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        _fail("invalid_evidence")
    required = {
        "origin",
        "check_name",
        "status",
        "observed_at",
        "evidence_sha256",
    }
    if not required.issubset(value) or not set(value).issubset(
        required | {"ru_probe_run_id", "detail"}
    ):
        _fail("invalid_evidence")
    origin = _plain_string(value["origin"], maximum=16, code="invalid_evidence")
    check_name = _plain_string(
        value["check_name"], maximum=128, code="invalid_evidence"
    )
    status = _plain_string(value["status"], maximum=32, code="invalid_evidence")
    evidence_sha256 = _plain_string(
        value["evidence_sha256"], maximum=64, code="invalid_evidence"
    )
    if origin not in REQUIRED_ORIGINS or _CHECK_RE.fullmatch(check_name) is None:
        _fail("invalid_evidence")
    if status not in ALLOWED_STATUSES or _SHA256_RE.fullmatch(evidence_sha256) is None:
        _fail("invalid_evidence")
    ru_probe_run_id = value.get("ru_probe_run_id")
    if isinstance(ru_probe_run_id, bool) or not (
        ru_probe_run_id is None
        or (isinstance(ru_probe_run_id, int) and ru_probe_run_id > 0)
        or (
            isinstance(ru_probe_run_id, str)
            and 1 <= len(ru_probe_run_id) <= 36
            and ru_probe_run_id == ru_probe_run_id.strip()
            and _REVISION_RE.fullmatch(ru_probe_run_id) is not None
        )
    ):
        _fail("invalid_evidence")
    if origin != "ru" and ru_probe_run_id is not None:
        _fail("invalid_ru_probe_binding")
    detail = _normalize_detail(value.get("detail", {}))
    detail_json = canonical_json(detail)
    if len(detail_json.encode("utf-8")) > 4096:
        _fail("invalid_detail")
    return {
        "origin": origin,
        "check_name": check_name,
        "status": status,
        "observed_at": _timestamp(value["observed_at"], code="invalid_evidence"),
        "evidence_sha256": evidence_sha256,
        "ru_probe_run_ref": ru_probe_run_id,
        "detail_json": detail_json,
    }


def validate_import_payload(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version",
        "candidate_id",
        "candidate",
        "evidence",
    }:
        _fail("invalid_payload")
    if isinstance(payload["schema_version"], bool) or payload["schema_version"] != 1:
        _fail("unsupported_schema")
    supplied_id = payload["candidate_id"]
    if not isinstance(supplied_id, str) or _SHA256_RE.fullmatch(supplied_id) is None:
        _fail("invalid_candidate_id")
    descriptor, descriptor_json, descriptor_sha256 = _validated_candidate(
        payload["candidate"]
    )
    if supplied_id != descriptor_sha256:
        raise ReleaseEvidenceConflict("candidate_id_mismatch")
    evidence = payload["evidence"]
    if not isinstance(evidence, list) or len(evidence) > 128:
        _fail("invalid_evidence")
    normalized_evidence = [_validated_evidence(item) for item in evidence]
    return {
        "candidate_id": supplied_id,
        "candidate": descriptor,
        "canonical_descriptor_json": descriptor_json,
        "descriptor_sha256": descriptor_sha256,
        "evidence": normalized_evidence,
    }


def _candidate_unique_error(error: IntegrityError) -> bool:
    original = getattr(error, "orig", None)
    diagnostic = getattr(original, "diag", None)
    constraint_name = getattr(diagnostic, "constraint_name", None)
    if constraint_name is not None:
        return constraint_name == "uq_release_candidates_candidate_id"
    return str(original) == "UNIQUE constraint failed: release_candidates.candidate_id"


def _evidence_unique_error(error: IntegrityError) -> bool:
    original = getattr(error, "orig", None)
    diagnostic = getattr(original, "diag", None)
    constraint_name = getattr(diagnostic, "constraint_name", None)
    if constraint_name is not None:
        return constraint_name == "uq_release_origin_evidence_candidate_origin_check_hash"
    return str(original) == (
        "UNIQUE constraint failed: release_origin_evidence.candidate_id, "
        "release_origin_evidence.origin, release_origin_evidence.check_name, "
        "release_origin_evidence.evidence_sha256"
    )


def _candidate_matches(row: ReleaseCandidate, normalized: Mapping[str, object]) -> bool:
    descriptor = normalized["candidate"]
    return bool(
        isinstance(descriptor, dict)
        and row.candidate_id == normalized["candidate_id"]
        and row.component == descriptor["component"]
        and row.version == descriptor["version"]
        and row.revision == descriptor["revision"]
        and row.artifact_sha256 == descriptor["artifact_sha256"]
        and row.canonical_descriptor_json == normalized["canonical_descriptor_json"]
        and row.descriptor_sha256 == normalized["descriptor_sha256"]
    )


def _resolve_ru_run(session, reference: object) -> RuProbeRun | None:
    if reference is None:
        return None
    query = session.query(RuProbeRun)
    if isinstance(reference, int):
        return query.filter(RuProbeRun.id == reference).one_or_none()
    return query.filter(RuProbeRun.run_id == reference).one_or_none()


def _require_ru_pass_run(session, row: RuProbeRun | None) -> None:
    if row is None:
        raise ReleaseEvidenceConflict("ru_probe_run_not_found")
    if (
        not bool(row.current_eligible)
        or str(row.execution_status or "").lower() != "completed"
        or str(row.environment_verdict or "").lower() not in {"pass", "available"}
        or str(row.release_verdict or "").lower() != "pass"
    ):
        raise ReleaseEvidenceConflict("ru_probe_run_ineligible")
    required_targets = (
        session.query(RuProbeTargetResult)
        .filter(RuProbeTargetResult.run_db_id == row.id)
        .filter(RuProbeTargetResult.scope == "release_required")
        .all()
    )
    if not required_targets or any(
        not bool(target.current_eligible)
        or str(target.overall_status or "").lower() != "pass"
        for target in required_targets
    ):
        raise ReleaseEvidenceConflict("ru_probe_run_incomplete")


def _evidence_matches(
    row: ReleaseOriginEvidence,
    entry: Mapping[str, object],
    *,
    run_db_id: int | None,
) -> bool:
    return bool(
        row.status == entry["status"]
        and _as_utc(row.observed_at) == entry["observed_at"]
        and row.detail_json == entry["detail_json"]
        and row.ru_probe_run_id == run_db_id
    )


def import_release_evidence(
    session,
    payload: object,
    *,
    ingest_key_id: str,
    imported_at: datetime,
) -> ReleaseEvidenceImportResult:
    normalized = validate_import_payload(payload)
    key_id = _plain_string(ingest_key_id, maximum=128, code="invalid_ingest_key")
    if _REVISION_RE.fullmatch(key_id) is None:
        _fail("invalid_ingest_key")
    now = _utc(imported_at, code="invalid_imported_at")
    candidate_id = str(normalized["candidate_id"])
    candidate = (
        session.query(ReleaseCandidate)
        .filter(ReleaseCandidate.candidate_id == candidate_id)
        .one_or_none()
    )
    candidate_created = False
    if candidate is None:
        descriptor = normalized["candidate"]
        assert isinstance(descriptor, dict)
        candidate = ReleaseCandidate(
            candidate_id=candidate_id,
            component=descriptor["component"],
            version=descriptor["version"],
            revision=descriptor["revision"],
            artifact_sha256=descriptor["artifact_sha256"],
            canonical_descriptor_json=normalized["canonical_descriptor_json"],
            descriptor_sha256=normalized["descriptor_sha256"],
            ingest_key_id=key_id,
            imported_at=now,
        )
        try:
            with session.begin_nested():
                session.add(candidate)
                session.flush()
            candidate_created = True
        except IntegrityError as error:
            if not _candidate_unique_error(error):
                raise
            session.expire_all()
            candidate = (
                session.query(ReleaseCandidate)
                .filter(ReleaseCandidate.candidate_id == candidate_id)
                .one_or_none()
            )
            if candidate is None:
                raise
    if not _candidate_matches(candidate, normalized):
        raise ReleaseEvidenceConflict("candidate_descriptor_conflict")

    evidence_created = 0
    for entry in normalized["evidence"]:
        assert isinstance(entry, dict)
        run = _resolve_ru_run(session, entry["ru_probe_run_ref"])
        if entry["ru_probe_run_ref"] is not None and run is None:
            raise ReleaseEvidenceConflict("ru_probe_run_not_found")
        if entry["origin"] == "ru" and entry["status"] == "PASS":
            if entry["ru_probe_run_ref"] is None:
                raise ReleaseEvidenceConflict("ru_probe_run_required")
            _require_ru_pass_run(session, run)
        run_db_id = int(run.id) if run is not None else None
        existing = (
            session.query(ReleaseOriginEvidence)
            .filter(ReleaseOriginEvidence.candidate_id == candidate_id)
            .filter(ReleaseOriginEvidence.origin == entry["origin"])
            .filter(ReleaseOriginEvidence.check_name == entry["check_name"])
            .filter(
                ReleaseOriginEvidence.evidence_sha256 == entry["evidence_sha256"]
            )
            .one_or_none()
        )
        if existing is not None:
            if not _evidence_matches(existing, entry, run_db_id=run_db_id):
                raise ReleaseEvidenceConflict("evidence_conflict")
        else:
            evidence_row = ReleaseOriginEvidence(
                candidate_id=candidate_id,
                origin=entry["origin"],
                check_name=entry["check_name"],
                status=entry["status"],
                evidence_sha256=entry["evidence_sha256"],
                observed_at=entry["observed_at"],
                detail_json=entry["detail_json"],
                ru_probe_run_id=run_db_id,
                imported_at=now,
            )
            try:
                with session.begin_nested():
                    session.add(evidence_row)
                    session.flush()
                evidence_created += 1
            except IntegrityError as error:
                if not _evidence_unique_error(error):
                    raise
                session.expire_all()
                existing = (
                    session.query(ReleaseOriginEvidence)
                    .filter(ReleaseOriginEvidence.candidate_id == candidate_id)
                    .filter(ReleaseOriginEvidence.origin == entry["origin"])
                    .filter(ReleaseOriginEvidence.check_name == entry["check_name"])
                    .filter(
                        ReleaseOriginEvidence.evidence_sha256
                        == entry["evidence_sha256"]
                    )
                    .one_or_none()
                )
                if existing is None or not _evidence_matches(
                    existing, entry, run_db_id=run_db_id
                ):
                    raise ReleaseEvidenceConflict("evidence_conflict") from None
        if run is not None:
            run.retention_hold = True
            run.retention_hold_reason = (
                f"release_evidence:{candidate_id}:{entry['check_name']}"
            )[:500]
            if run.retention_held_at is None:
                run.retention_held_at = now
    session.flush()
    return ReleaseEvidenceImportResult(
        candidate_id=candidate_id,
        created=bool(candidate_created or evidence_created),
        candidate_created=candidate_created,
        evidence_created=evidence_created,
    )


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    normalized = _as_utc(value)
    if normalized is None:
        return None
    return normalized.isoformat(timespec="seconds").replace("+00:00", "Z")


def _encode_cursor(*, imported_at: datetime, row_id: int) -> str:
    normalized = _as_utc(imported_at)
    if normalized is None or row_id <= 0:
        raise ReleaseEvidenceReadError("invalid_cursor")
    raw = struct.pack(">qQ", int(normalized.timestamp() * 1_000_000), int(row_id))
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_cursor(value: str) -> tuple[datetime, int]:
    raw_value = str(value or "").strip()
    if not raw_value or len(raw_value) > 128 or _CURSOR_RE.fullmatch(raw_value) is None:
        raise ReleaseEvidenceReadError("invalid_cursor")
    try:
        raw = base64.urlsafe_b64decode(raw_value + "=" * (-len(raw_value) % 4))
        if len(raw) != 16:
            raise ValueError
        micros, row_id = struct.unpack(">qQ", raw)
        if row_id <= 0:
            raise ValueError
        imported_at = datetime.fromtimestamp(micros / 1_000_000, tz=timezone.utc)
    except (ValueError, OverflowError, struct.error) as exc:
        raise ReleaseEvidenceReadError("invalid_cursor") from exc
    return imported_at, int(row_id)


def _candidate_summary(row: ReleaseCandidate, *, now: datetime) -> dict[str, object]:
    imported_at = _as_utc(row.imported_at)
    return {
        "candidate_id": str(row.candidate_id),
        "component": str(row.component),
        "version": str(row.version),
        "revision": str(row.revision),
        "artifact_sha256": str(row.artifact_sha256),
        "descriptor_sha256": str(row.descriptor_sha256),
        "imported_at": _iso(imported_at),
        "age_seconds": (
            max(0, int((now - imported_at).total_seconds()))
            if imported_at is not None
            else None
        ),
    }


def list_release_candidates(
    session,
    *,
    limit: int = DEFAULT_PAGE_LIMIT,
    cursor: str | None = None,
    now: datetime | None = None,
) -> dict[str, object]:
    try:
        normalized_limit = int(limit)
    except (TypeError, ValueError) as exc:
        raise ReleaseEvidenceReadError("invalid_limit") from exc
    if not 1 <= normalized_limit <= MAX_PAGE_LIMIT:
        raise ReleaseEvidenceReadError("invalid_limit")
    normalized_now = _as_utc(now or datetime.now(timezone.utc))
    assert normalized_now is not None
    query = session.query(ReleaseCandidate)
    if cursor:
        cursor_time, cursor_id = _decode_cursor(cursor)
        query = query.filter(
            (ReleaseCandidate.imported_at < cursor_time)
            | (
                (ReleaseCandidate.imported_at == cursor_time)
                & (ReleaseCandidate.id < cursor_id)
            )
        )
    rows = (
        query.order_by(
            ReleaseCandidate.imported_at.desc(),
            ReleaseCandidate.id.desc(),
        )
        .limit(normalized_limit + 1)
        .all()
    )
    page = rows[:normalized_limit]
    next_cursor = None
    if len(rows) > normalized_limit and page:
        next_cursor = _encode_cursor(
            imported_at=page[-1].imported_at,
            row_id=int(page[-1].id),
        )
    return {
        "items": [_candidate_summary(row, now=normalized_now) for row in page],
        "next_cursor": next_cursor,
        "limit": normalized_limit,
    }


def _aggregate_status(statuses: list[str]) -> str:
    if statuses and all(status == "PASS" for status in statuses):
        return "PASS"
    return min(statuses or ["MISSING"], key=lambda item: _STATUS_PRECEDENCE[item])


def get_release_readiness(
    session,
    candidate_id: str,
    *,
    now: datetime | None = None,
) -> dict[str, object]:
    if not isinstance(candidate_id, str) or _SHA256_RE.fullmatch(candidate_id) is None:
        raise ReleaseEvidenceReadError("invalid_candidate_id")
    candidate = (
        session.query(ReleaseCandidate)
        .filter(ReleaseCandidate.candidate_id == candidate_id)
        .one_or_none()
    )
    if candidate is None:
        raise ReleaseEvidenceNotFound("candidate_not_found")
    rows = (
        session.query(ReleaseOriginEvidence)
        .filter(ReleaseOriginEvidence.candidate_id == candidate_id)
        .order_by(
            ReleaseOriginEvidence.origin.asc(),
            ReleaseOriginEvidence.check_name.asc(),
            ReleaseOriginEvidence.observed_at.desc(),
            ReleaseOriginEvidence.id.desc(),
        )
        .all()
    )
    latest: dict[tuple[str, str], ReleaseOriginEvidence] = {}
    for row in rows:
        latest.setdefault((str(row.origin), str(row.check_name)), row)
    run_ids = {
        int(row.ru_probe_run_id)
        for row in latest.values()
        if row.ru_probe_run_id is not None
    }
    run_refs = {
        int(row.id): str(row.run_id)
        for row in (
            session.query(RuProbeRun).filter(RuProbeRun.id.in_(run_ids)).all()
            if run_ids
            else []
        )
    }
    origins: list[dict[str, object]] = []
    for origin in REQUIRED_ORIGINS:
        origin_rows = [
            row for (row_origin, _check), row in latest.items() if row_origin == origin
        ]
        origin_rows.sort(key=lambda row: (str(row.check_name), int(row.id)))
        checks: list[dict[str, object]] = []
        if not origin_rows:
            checks.append(
                {
                    "origin": origin,
                    "check_name": "origin_evidence",
                    "status": "MISSING",
                    "observed_at": None,
                    "evidence_ref": None,
                    "evidence_sha256": None,
                    "ru_probe_run_id": None,
                    "detail": {},
                    "reason": "missing_origin_evidence",
                }
            )
        for row in origin_rows:
            try:
                detail = json.loads(str(row.detail_json or "{}"))
            except (TypeError, ValueError):
                detail = {}
            checks.append(
                {
                    "origin": origin,
                    "check_name": str(row.check_name),
                    "status": str(row.status),
                    "observed_at": _iso(row.observed_at),
                    "evidence_ref": str(row.evidence_sha256),
                    "evidence_sha256": str(row.evidence_sha256),
                    "ru_probe_run_id": (
                        run_refs.get(int(row.ru_probe_run_id))
                        if row.ru_probe_run_id is not None
                        else None
                    ),
                    "detail": detail if isinstance(detail, dict) else {},
                    "reason": (
                        "evidence_pass"
                        if str(row.status) == "PASS"
                        else f"reported_{str(row.status).lower()}"
                    ),
                }
            )
        origins.append(
            {
                "origin": origin,
                "status": _aggregate_status([str(check["status"]) for check in checks]),
                "checks": checks,
            }
        )
    overall_status = _aggregate_status([str(item["status"]) for item in origins])
    normalized_now = _as_utc(now or datetime.now(timezone.utc))
    assert normalized_now is not None
    return {
        "candidate": _candidate_summary(candidate, now=normalized_now),
        "candidate_id": candidate_id,
        "status": overall_status,
        "ready": overall_status == "PASS",
        "generated_at": _iso(normalized_now),
        "origins": origins,
    }
