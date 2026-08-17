from __future__ import annotations

import importlib
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

MAX_META_JSON = 3800
_SAFE_TOKEN_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]*$")
_DENIED_META_KEY_RE = re.compile(
    r"(?:secret|token|password|credential|private|config|payload|body|message|text|url|host|ip|email|phone|cookie|authorization)",
    re.IGNORECASE,
)
_DENIED_META_KEYS = {
    "code",
    "promo_code",
    "external_id",
    "order_id",
    "pairing_id",
    "application_id",
    "ticket_id",
    "actor_tg_id",
    "tg_id",
    "token_fp",
    "raw_reason",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _safe_meta_value(value: Any, *, depth: int = 0) -> Any:
    if value is None or type(value) in {bool, int}:
        return value
    if isinstance(value, float):
        return value if value == value and abs(value) != float("inf") else None
    if isinstance(value, str):
        normalized = value.strip().lower()[:160]
        return normalized if _SAFE_TOKEN_RE.fullmatch(normalized) else None
    if depth >= 2:
        return None
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for raw_key, raw_value in list(value.items())[:30]:
            key = str(raw_key or "").strip().lower()[:64]
            if (
                not _SAFE_TOKEN_RE.fullmatch(key)
                or key in _DENIED_META_KEYS
                or _DENIED_META_KEY_RE.search(key)
            ):
                continue
            safe_value = _safe_meta_value(raw_value, depth=depth + 1)
            if safe_value is not None:
                out[key] = safe_value
        return out
    if isinstance(value, (list, tuple)):
        return [
            safe
            for item in list(value)[:20]
            if (safe := _safe_meta_value(item, depth=depth + 1)) is not None
        ]
    return None


def _meta_to_json(meta: dict[str, Any] | None) -> str | None:
    if not meta:
        return None
    try:
        safe = _safe_meta_value(meta)
        if not isinstance(safe, dict) or not safe:
            return None
        payload = json.dumps(safe, ensure_ascii=False, separators=(",", ":"))
        if len(payload) > MAX_META_JSON:
            return None
        return payload
    except Exception:
        return None


def safe_event_meta_json(meta: dict[str, Any] | None) -> str | None:
    return _meta_to_json(meta)


def _token(value: object, *, maximum: int, default: str | None = None) -> str | None:
    normalized = str(value or "").strip().lower()[:maximum]
    if not normalized:
        return default
    return normalized if _SAFE_TOKEN_RE.fullmatch(normalized) else default


def _optional_text(value: object, *, maximum: int) -> str | None:
    normalized = str(value or "").strip()[:maximum]
    return normalized or None


def _normalize_time(value: datetime | None, *, fallback: datetime) -> datetime:
    if not isinstance(value, datetime):
        return fallback
    if value.tzinfo is not None and value.utcoffset() is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _clock_skew_state(*, occurred_at: datetime, received_at: datetime) -> str:
    delta = (occurred_at - received_at).total_seconds()
    if abs(delta) <= 300:
        return "ok"
    return "client_future" if delta > 0 else "client_late"


def track_event(
    *,
    tg_id: int,
    event_name: str,
    source: str = "unknown",
    session_id: str | None = None,
    meta: dict[str, Any] | None = None,
    event_id: str | None = None,
    occurred_at: datetime | None = None,
    account_id: str | None = None,
    device_id: str | None = None,
    platform: str | None = None,
    app_version: str | None = None,
    build_number: str | None = None,
    surface: str | None = None,
    subsystem: str | None = None,
    stage: str | None = None,
    result: str | None = None,
    error_category: str | None = None,
    error_code: str | None = None,
    retryable: bool | None = None,
    attempt_number: int | None = None,
    retry_after_seconds: int | None = None,
    duration_ms: int | None = None,
    trace_id: str | None = None,
    network_class: str | None = None,
) -> int | None:
    if not event_name:
        return None
    db_module = importlib.import_module("db")
    event_model = importlib.import_module("models").Event
    s = db_module.SessionLocal()
    received_at = _utcnow()
    normalized_occurred_at = _normalize_time(occurred_at, fallback=received_at)
    try:
        normalized_event_id = str(uuid.UUID(str(event_id))) if event_id else str(uuid.uuid4())
    except ValueError:
        return None
    try:
        row = event_model(
            tg_id=int(tg_id),
            event_name=str(event_name).strip()[:64],
            schema_version=1,
            event_id=normalized_event_id,
            source=str(source or "unknown").strip()[:32],
            session_id=(str(session_id).strip()[:64] if session_id else None),
            account_id=_optional_text(account_id, maximum=36),
            device_id=_optional_text(device_id, maximum=36),
            platform=_token(platform, maximum=24),
            app_version=_optional_text(app_version, maximum=32),
            build_number=_optional_text(build_number, maximum=24),
            surface=_token(surface or source, maximum=32, default="unknown"),
            subsystem=_token(subsystem, maximum=32),
            stage=_token(stage, maximum=64),
            result=_token(result, maximum=24),
            error_category=_token(error_category, maximum=32),
            error_code=_token(error_code, maximum=64),
            retryable=(bool(retryable) if retryable is not None else None),
            attempt_number=(
                max(1, min(int(attempt_number), 100))
                if attempt_number is not None
                else None
            ),
            retry_after_seconds=(
                max(0, min(int(retry_after_seconds), 86_400))
                if retry_after_seconds is not None
                else None
            ),
            duration_ms=(
                max(0, min(int(duration_ms), 3_600_000))
                if duration_ms is not None
                else None
            ),
            trace_id=_optional_text(trace_id, maximum=64),
            network_class=_token(network_class, maximum=24),
            occurred_at=normalized_occurred_at,
            received_at=received_at,
            clock_skew_state=_clock_skew_state(
                occurred_at=normalized_occurred_at,
                received_at=received_at,
            ),
            meta_json=_meta_to_json(meta),
            created_at=received_at,
        )
        s.add(row)
        s.commit()
        s.refresh(row)
        return int(row.id)
    except Exception:
        s.rollback()
        try:
            existing = (
                s.query(event_model.id)
                .filter(event_model.event_id == normalized_event_id)
                .first()
            )
            return int(existing[0]) if existing is not None else None
        except Exception:
            s.rollback()
            return None
    finally:
        s.close()
