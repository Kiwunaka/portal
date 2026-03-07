from __future__ import annotations

import importlib
import json
from datetime import datetime, timezone
from typing import Any

MAX_META_JSON = 3800


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _meta_to_json(meta: dict[str, Any] | None) -> str | None:
    if not meta:
        return None
    try:
        payload = json.dumps(meta, ensure_ascii=False, separators=(",", ":"))
        if len(payload) > MAX_META_JSON:
            payload = payload[:MAX_META_JSON]
        return payload
    except Exception:
        return None


def track_event(
    *,
    tg_id: int,
    event_name: str,
    source: str = "unknown",
    session_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> int | None:
    if not event_name:
        return None
    db_module = importlib.import_module("db")
    event_model = importlib.import_module("models").Event
    s = db_module.SessionLocal()
    try:
        row = event_model(
            tg_id=int(tg_id),
            event_name=str(event_name).strip()[:64],
            source=str(source or "unknown").strip()[:32],
            session_id=(str(session_id).strip()[:64] if session_id else None),
            meta_json=_meta_to_json(meta),
            created_at=_utcnow(),
        )
        s.add(row)
        s.commit()
        s.refresh(row)
        return int(row.id)
    except Exception:
        s.rollback()
        return None
    finally:
        s.close()
