"""Strict aggregate release-health projection validation and persistence."""

from __future__ import annotations

import json
import re
import uuid
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

try:
    from .models import ReleaseHealthEvent, ReleaseHealthIngestCounter
    from .request_correlation import RequestCorrelation
except ImportError:
    from models import ReleaseHealthEvent, ReleaseHealthIngestCounter
    from request_correlation import RequestCorrelation


MAX_BATCH_EVENTS = 100
MAX_IDENTITY_BODY_BYTES = 256 * 1024
MAX_GZIP_BODY_BYTES = 64 * 1024
MAX_DECODED_BODY_BYTES = 256 * 1024

_BATCH_FIELDS = frozenset({"schema_version", "events"})
_EVENT_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "event_id",
        "occurred_at_utc",
        "component",
        "subsystem",
        "stage",
        "name",
        "severity",
        "outcome",
        "privacy_class",
        "build",
        "error",
    }
)
_EVENT_FIELDS = _EVENT_REQUIRED_FIELDS | frozenset({"attributes"})
_BUILD_FIELDS = frozenset(
    {
        "app_version",
        "build_number",
        "channel",
        "candidate_label",
        "git_revision",
        "core_version",
        "core_abi",
        "platform",
        "architecture",
    }
)
_ERROR_FIELDS = frozenset({"code", "origin"})
_FORBIDDEN_FIELDS = frozenset(
    {
        "account_id",
        "address",
        "authorization",
        "body",
        "cookie",
        "correlation",
        "credential",
        "destination",
        "device_id",
        "domain",
        "endpoint",
        "headers",
        "host",
        "install_id",
        "ip",
        "metadata",
        "package",
        "package_name",
        "private_key",
        "query",
        "raw_config",
        "run_id",
        "session_id",
        "span_id",
        "support_case_id",
        "telegram_id",
        "tg_id",
        "token",
        "trace_id",
        "uri",
        "url",
    }
)


class ReleaseHealthIngestError(ValueError):
    def __init__(
        self,
        reason: str,
        *,
        status_code: int = 422,
        catalog_code: str = "API-008",
    ) -> None:
        super().__init__(reason)
        self.reason = reason
        self.status_code = int(status_code)
        self.catalog_code = catalog_code


class _DuplicateJsonKey(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ReleaseHealthProjection:
    event_id: str
    occurred_at: datetime
    component: str
    subsystem: str
    stage: str
    event_name: str
    severity: str
    outcome: str
    app_version: str
    build_number: str
    channel: str
    candidate_label: str
    git_revision: str
    core_version: str | None
    core_abi: int | None
    platform: str
    architecture: str
    error_code: str | None
    error_origin: str | None
    selected_app_count: int | None


@dataclass(frozen=True, slots=True)
class ReleaseHealthIngestResult:
    accepted: int
    duplicates: int


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_contracts() -> tuple[dict[str, Any], frozenset[str]]:
    contract_dir = _repo_root() / "shared" / "contracts" / "observability"
    event_schema = json.loads(
        (contract_dir / "observability-event.schema.json").read_text(encoding="utf-8")
    )
    catalog = json.loads(
        (contract_dir / "error-catalog.json").read_text(encoding="utf-8")
    )
    codes = frozenset(str(entry["code"]) for entry in catalog["entries"])
    if event_schema.get("x-pokrov-contract", {}).get("version") != "1.0.0":
        raise RuntimeError("Unsupported observability event contract")
    if catalog.get("schema_version") != 1 or not codes:
        raise RuntimeError("Unsupported observability error catalog")
    return event_schema, codes


_EVENT_SCHEMA, _CATALOG_CODES = _load_contracts()
_EVENT_PROPERTIES = _EVENT_SCHEMA["properties"]
_DEFS = _EVENT_SCHEMA["$defs"]


def _enum(property_name: str) -> frozenset[str]:
    return frozenset(str(value) for value in _EVENT_PROPERTIES[property_name]["enum"])


_COMPONENTS = _enum("component")
_SUBSYSTEMS = _enum("subsystem")
_STAGES = _enum("stage")
_SEVERITIES = _enum("severity")
_OUTCOMES = _enum("outcome")
_BUILD_PROPERTIES = _DEFS["buildIdentity"]["properties"]
_CHANNELS = frozenset(str(value) for value in _BUILD_PROPERTIES["channel"]["enum"])
_PLATFORMS = frozenset(str(value) for value in _BUILD_PROPERTIES["platform"]["enum"])
_ERROR_ORIGINS = frozenset(
    str(value) for value in _DEFS["errorIdentity"]["properties"]["origin"]["enum"]
)
_UUID_RE = re.compile(_DEFS["uuid"]["pattern"])
_NAME_RE = re.compile(_EVENT_PROPERTIES["name"]["pattern"])
_VERSION_RE = re.compile(_DEFS["version"]["pattern"])
_BUILD_NUMBER_RE = re.compile(_BUILD_PROPERTIES["build_number"]["pattern"])
_CANDIDATE_RE = re.compile(_BUILD_PROPERTIES["candidate_label"]["pattern"])
_GIT_REVISION_RE = re.compile(_BUILD_PROPERTIES["git_revision"]["pattern"])
_ARCHITECTURE_RE = re.compile(_BUILD_PROPERTIES["architecture"]["pattern"])


def encoded_body_limit(content_encoding: str) -> int:
    normalized = str(content_encoding or "identity").strip().lower()
    if normalized in {"", "identity"}:
        return MAX_IDENTITY_BODY_BYTES
    if normalized == "gzip":
        return MAX_GZIP_BODY_BYTES
    raise ReleaseHealthIngestError(
        "unsupported_content_encoding",
        status_code=415,
    )


def decode_batch_body(body: bytes, *, content_encoding: str) -> bytes:
    limit = encoded_body_limit(content_encoding)
    if not body:
        raise ReleaseHealthIngestError("empty_body", status_code=400)
    if len(body) > limit:
        raise ReleaseHealthIngestError("encoded_body_too_large", status_code=413)

    normalized = str(content_encoding or "identity").strip().lower()
    if normalized in {"", "identity"}:
        return body

    try:
        decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
        decoded = decompressor.decompress(body, MAX_DECODED_BODY_BYTES + 1)
        if len(decoded) > MAX_DECODED_BODY_BYTES or decompressor.unconsumed_tail:
            raise ReleaseHealthIngestError("decoded_body_too_large", status_code=413)
        decoded += decompressor.flush(MAX_DECODED_BODY_BYTES + 1 - len(decoded))
    except ReleaseHealthIngestError:
        raise
    except (zlib.error, ValueError):
        raise ReleaseHealthIngestError("invalid_gzip", status_code=400) from None

    if len(decoded) > MAX_DECODED_BODY_BYTES:
        raise ReleaseHealthIngestError("decoded_body_too_large", status_code=413)
    if not decompressor.eof or decompressor.unused_data:
        raise ReleaseHealthIngestError("invalid_gzip", status_code=400)
    return decoded


def _reject_duplicate_keys(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKey(key)
        result[key] = value
    return result


def _parse_json(body: bytes) -> Any:
    if len(body) > MAX_DECODED_BODY_BYTES:
        raise ReleaseHealthIngestError("decoded_body_too_large", status_code=413)
    try:
        text = body.decode("utf-8", errors="strict")
        return json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except _DuplicateJsonKey:
        raise ReleaseHealthIngestError("duplicate_json_key", status_code=400) from None
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ReleaseHealthIngestError("invalid_json", status_code=400) from None


def _mapping(value: Any, *, reason: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ReleaseHealthIngestError(reason)
    return value


def _check_fields(
    value: Mapping[str, Any],
    *,
    allowed: frozenset[str],
    required: frozenset[str] | None = None,
) -> None:
    keys = frozenset(str(key) for key in value)
    forbidden = sorted(keys & _FORBIDDEN_FIELDS)
    if forbidden:
        raise ReleaseHealthIngestError("forbidden_field")
    if keys - allowed:
        raise ReleaseHealthIngestError("unknown_field")
    if (required or allowed) - keys:
        raise ReleaseHealthIngestError("missing_field")


def _string(
    value: Any,
    *,
    reason: str,
    pattern: re.Pattern[str] | None = None,
    allowed: frozenset[str] | None = None,
    max_length: int | None = None,
) -> str:
    if not isinstance(value, str) or not value:
        raise ReleaseHealthIngestError(reason)
    if max_length is not None and len(value) > max_length:
        raise ReleaseHealthIngestError(reason)
    if pattern is not None and pattern.fullmatch(value) is None:
        raise ReleaseHealthIngestError(reason)
    if allowed is not None and value not in allowed:
        raise ReleaseHealthIngestError(reason)
    return value


def _integer(
    value: Any,
    *,
    reason: str,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReleaseHealthIngestError(reason)
    if minimum is not None and value < minimum:
        raise ReleaseHealthIngestError(reason)
    if maximum is not None and value > maximum:
        raise ReleaseHealthIngestError(reason)
    return value


def _timestamp(value: Any) -> datetime:
    raw = _string(value, reason="invalid_timestamp", max_length=40)
    if not raw.endswith("Z"):
        raise ReleaseHealthIngestError("invalid_timestamp")
    try:
        parsed = datetime.fromisoformat(raw[:-1] + "+00:00")
    except ValueError:
        raise ReleaseHealthIngestError("invalid_timestamp") from None
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ReleaseHealthIngestError("invalid_timestamp")
    return parsed.astimezone(timezone.utc)


def _uuid(value: Any) -> str:
    raw = _string(value, reason="invalid_event_id", pattern=_UUID_RE, max_length=36)
    try:
        parsed = uuid.UUID(raw)
    except ValueError:
        raise ReleaseHealthIngestError("invalid_event_id") from None
    if str(parsed) != raw:
        raise ReleaseHealthIngestError("invalid_event_id")
    return raw


def _validate_build(value: Any) -> dict[str, Any]:
    build = _mapping(value, reason="invalid_build")
    _check_fields(build, allowed=_BUILD_FIELDS)
    core_version_raw = build["core_version"]
    if core_version_raw is not None:
        core_version = _string(
            core_version_raw,
            reason="invalid_build",
            pattern=_VERSION_RE,
            max_length=64,
        )
    else:
        core_version = None
    core_abi_raw = build["core_abi"]
    core_abi = (
        _integer(core_abi_raw, reason="invalid_build", minimum=1)
        if core_abi_raw is not None
        else None
    )
    return {
        "app_version": _string(
            build["app_version"],
            reason="invalid_build",
            pattern=_VERSION_RE,
            max_length=64,
        ),
        "build_number": _string(
            build["build_number"],
            reason="invalid_build",
            pattern=_BUILD_NUMBER_RE,
            max_length=32,
        ),
        "channel": _string(build["channel"], reason="invalid_build", allowed=_CHANNELS),
        "candidate_label": _string(
            build["candidate_label"],
            reason="invalid_build",
            pattern=_CANDIDATE_RE,
            max_length=64,
        ),
        "git_revision": _string(
            build["git_revision"],
            reason="invalid_build",
            pattern=_GIT_REVISION_RE,
            max_length=40,
        ),
        "core_version": core_version,
        "core_abi": core_abi,
        "platform": _string(build["platform"], reason="invalid_build", allowed=_PLATFORMS),
        "architecture": _string(
            build["architecture"],
            reason="invalid_build",
            pattern=_ARCHITECTURE_RE,
            max_length=32,
        ),
    }


def _validate_error(value: Any) -> tuple[str | None, str | None]:
    if value is None:
        return None, None
    error = _mapping(value, reason="invalid_error")
    _check_fields(error, allowed=_ERROR_FIELDS)
    code = _string(error["code"], reason="unknown_error_code", max_length=24)
    if code not in _CATALOG_CODES:
        raise ReleaseHealthIngestError("unknown_error_code")
    origin = _string(error["origin"], reason="invalid_error", allowed=_ERROR_ORIGINS)
    return code, origin


def _validate_release_health_attributes(
    value: Any,
    *,
    component: str,
    subsystem: str,
    stage: str,
    event_name: str,
    outcome: str,
    platform: str,
) -> int | None:
    is_android_routing_count = (
        component == "app"
        and subsystem == "routing"
        and stage == "complete"
        and event_name == "app.routing.selection.finished"
        and outcome == "observed"
        and platform == "android"
    )
    if value is None:
        if is_android_routing_count:
            raise ReleaseHealthIngestError("missing_field")
        return None
    attributes = _mapping(value, reason="invalid_attributes")
    if not is_android_routing_count:
        raise ReleaseHealthIngestError("forbidden_field")
    _check_fields(
        attributes,
        allowed=frozenset({"selected_app_count"}),
    )
    return _integer(
        attributes["selected_app_count"],
        reason="invalid_selected_app_count",
        minimum=0,
        maximum=128,
    )


def _validate_event(value: Any) -> ReleaseHealthProjection:
    event = _mapping(value, reason="invalid_event")
    _check_fields(
        event,
        allowed=_EVENT_FIELDS,
        required=_EVENT_REQUIRED_FIELDS,
    )
    if _integer(event["schema_version"], reason="unsupported_schema_version") != 1:
        raise ReleaseHealthIngestError(
            "unsupported_schema_version",
            status_code=409,
            catalog_code="API-009",
        )
    if event["privacy_class"] != "release_health":
        raise ReleaseHealthIngestError("invalid_privacy_class")
    build = _validate_build(event["build"])
    error_code, error_origin = _validate_error(event["error"])
    component = _string(
        event["component"], reason="invalid_component", allowed=_COMPONENTS
    )
    subsystem = _string(
        event["subsystem"], reason="invalid_subsystem", allowed=_SUBSYSTEMS
    )
    stage = _string(event["stage"], reason="invalid_stage", allowed=_STAGES)
    event_name = _string(
        event["name"],
        reason="invalid_event_name",
        pattern=_NAME_RE,
        max_length=96,
    )
    outcome = _string(event["outcome"], reason="invalid_outcome", allowed=_OUTCOMES)
    selected_app_count = _validate_release_health_attributes(
        event.get("attributes"),
        component=component,
        subsystem=subsystem,
        stage=stage,
        event_name=event_name,
        outcome=outcome,
        platform=build["platform"],
    )
    return ReleaseHealthProjection(
        event_id=_uuid(event["event_id"]),
        occurred_at=_timestamp(event["occurred_at_utc"]),
        component=component,
        subsystem=subsystem,
        stage=stage,
        event_name=event_name,
        severity=_string(event["severity"], reason="invalid_severity", allowed=_SEVERITIES),
        outcome=outcome,
        error_code=error_code,
        error_origin=error_origin,
        selected_app_count=selected_app_count,
        **build,
    )


def parse_release_health_batch(body: bytes) -> tuple[ReleaseHealthProjection, ...]:
    payload = _mapping(_parse_json(body), reason="invalid_batch")
    _check_fields(payload, allowed=_BATCH_FIELDS)
    if _integer(payload["schema_version"], reason="unsupported_schema_version") != 1:
        raise ReleaseHealthIngestError(
            "unsupported_schema_version",
            status_code=409,
            catalog_code="API-009",
        )
    events = payload["events"]
    if not isinstance(events, list) or not events:
        raise ReleaseHealthIngestError("invalid_event_count")
    if len(events) > MAX_BATCH_EVENTS:
        raise ReleaseHealthIngestError("too_many_events", status_code=413)
    return tuple(_validate_event(event) for event in events)


def _counter_upsert(session: Any, values: Mapping[str, int]) -> None:
    dialect = str(session.get_bind().dialect.name or "").lower()
    now = datetime.now(timezone.utc)
    for reason, delta in values.items():
        if delta <= 0:
            continue
        row = {"reason": reason, "count": int(delta), "updated_at": now}
        if dialect == "sqlite":
            statement = sqlite_insert(ReleaseHealthIngestCounter).values(**row)
            statement = statement.on_conflict_do_update(
                index_elements=["reason"],
                set_={
                    "count": ReleaseHealthIngestCounter.count + int(delta),
                    "updated_at": now,
                },
            )
            session.execute(statement)
        elif dialect == "postgresql":
            statement = postgresql_insert(ReleaseHealthIngestCounter).values(**row)
            statement = statement.on_conflict_do_update(
                index_elements=["reason"],
                set_={
                    "count": ReleaseHealthIngestCounter.count + int(delta),
                    "updated_at": now,
                },
            )
            session.execute(statement)
        else:
            counter = session.get(ReleaseHealthIngestCounter, reason)
            if counter is None:
                session.add(ReleaseHealthIngestCounter(**row))
            else:
                counter.count = int(counter.count or 0) + int(delta)
                counter.updated_at = now


def record_quarantine_counter(session: Any, reason: str) -> None:
    safe_reason = str(reason or "invalid_batch").strip().lower()
    if re.fullmatch(r"[a-z0-9_]{1,48}", safe_reason) is None:
        safe_reason = "invalid_batch"
    _counter_upsert(session, {f"quarantine.{safe_reason}": 1})


def _event_rows(events: Iterable[ReleaseHealthProjection]) -> list[dict[str, Any]]:
    received_at = datetime.now(timezone.utc)
    return [
        {
            "schema_version": 1,
            "event_id": event.event_id,
            "occurred_at": event.occurred_at,
            "received_at": received_at,
            "component": event.component,
            "subsystem": event.subsystem,
            "stage": event.stage,
            "event_name": event.event_name,
            "severity": event.severity,
            "outcome": event.outcome,
            "app_version": event.app_version,
            "build_number": event.build_number,
            "channel": event.channel,
            "candidate_label": event.candidate_label,
            "git_revision": event.git_revision,
            "core_version": event.core_version,
            "core_abi": event.core_abi,
            "platform": event.platform,
            "architecture": event.architecture,
            "error_code": event.error_code,
            "error_origin": event.error_origin,
            "selected_app_count": event.selected_app_count,
        }
        for event in events
    ]


def _projection_matches_row(
    event: ReleaseHealthProjection,
    row: ReleaseHealthEvent,
) -> bool:
    occurred_at = row.occurred_at
    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=timezone.utc)
    else:
        occurred_at = occurred_at.astimezone(timezone.utc)
    return (
        occurred_at == event.occurred_at
        and row.component == event.component
        and row.subsystem == event.subsystem
        and row.stage == event.stage
        and row.event_name == event.event_name
        and row.severity == event.severity
        and row.outcome == event.outcome
        and row.app_version == event.app_version
        and row.build_number == event.build_number
        and row.channel == event.channel
        and row.candidate_label == event.candidate_label
        and row.git_revision == event.git_revision
        and row.core_version == event.core_version
        and row.core_abi == event.core_abi
        and row.platform == event.platform
        and row.architecture == event.architecture
        and row.error_code == event.error_code
        and row.error_origin == event.error_origin
        and row.selected_app_count == event.selected_app_count
    )


def ingest_release_health_batch(
    session: Any,
    events: Sequence[ReleaseHealthProjection],
    *,
    request_context: RequestCorrelation,
) -> ReleaseHealthIngestResult:
    if not isinstance(request_context, RequestCorrelation):
        raise TypeError("request_context must be RequestCorrelation")
    unique: dict[str, ReleaseHealthProjection] = {}
    duplicates = 0
    for event in events:
        if event.event_id in unique:
            if unique[event.event_id] != event:
                raise ReleaseHealthIngestError("event_id_conflict", status_code=409)
            duplicates += 1
        else:
            unique[event.event_id] = event

    event_ids = tuple(unique)
    existing_rows = {
        row.event_id: row
        for row in session.scalars(
            select(ReleaseHealthEvent).where(ReleaseHealthEvent.event_id.in_(event_ids))
        ).all()
    }
    for event_id, row in existing_rows.items():
        if not _projection_matches_row(unique[event_id], row):
            raise ReleaseHealthIngestError("event_id_conflict", status_code=409)
    existing = set(existing_rows)
    duplicates += len(existing)
    rows = _event_rows(unique[event_id] for event_id in event_ids if event_id not in existing)
    dialect = str(session.get_bind().dialect.name or "").lower()
    accepted = 0
    if rows:
        if dialect == "sqlite":
            result = session.execute(
                sqlite_insert(ReleaseHealthEvent)
                .values(rows)
                .on_conflict_do_nothing(index_elements=["event_id"])
            )
            accepted = max(0, int(result.rowcount or 0))
        elif dialect == "postgresql":
            result = session.execute(
                postgresql_insert(ReleaseHealthEvent)
                .values(rows)
                .on_conflict_do_nothing(index_elements=["event_id"])
            )
            accepted = max(0, int(result.rowcount or 0))
        else:
            for row in rows:
                session.add(ReleaseHealthEvent(**row))
            session.flush()
            accepted = len(rows)
        duplicates += len(rows) - accepted

    persisted_rows = {
        row.event_id: row
        for row in session.scalars(
            select(ReleaseHealthEvent).where(ReleaseHealthEvent.event_id.in_(event_ids))
        ).all()
    }
    for event_id, row in persisted_rows.items():
        if not _projection_matches_row(unique[event_id], row):
            raise ReleaseHealthIngestError("event_id_conflict", status_code=409)

    _counter_upsert(
        session,
        {
            "accepted.batches": 1,
            "accepted.events": accepted,
            "duplicate.events": duplicates,
        },
    )
    return ReleaseHealthIngestResult(accepted=accepted, duplicates=duplicates)
