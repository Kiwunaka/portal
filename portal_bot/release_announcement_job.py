from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse


_SCHEDULE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
_ALLOWED_LINK_HOSTS = frozenset({"pokrov.space", "www.pokrov.space"})


class AnnouncementConfigError(ValueError):
    pass


def _bounded_text(
    value: Any,
    *,
    field: str,
    minimum: int,
    maximum: int,
) -> str:
    text = str(value or "").strip()
    if not minimum <= len(text) <= maximum:
        raise AnnouncementConfigError(f"{field}_invalid")
    return text


def load_announcement_config(path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if not resolved.is_file():
        raise AnnouncementConfigError("config_not_file")
    if os.name != "nt" and resolved.stat().st_mode & 0o077:
        raise AnnouncementConfigError("config_permissions_too_open")
    try:
        raw = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AnnouncementConfigError("config_invalid") from exc
    if not isinstance(raw, dict) or set(raw) != {
        "schema_version",
        "schedule_id",
        "title",
        "summary",
        "link",
        "telegram_text",
        "delete_after_success",
    }:
        raise AnnouncementConfigError("config_shape_invalid")
    if raw.get("schema_version") != 1:
        raise AnnouncementConfigError("schema_version_invalid")
    schedule_id = str(raw.get("schedule_id") or "").strip().lower()
    if _SCHEDULE_ID_RE.fullmatch(schedule_id) is None:
        raise AnnouncementConfigError("schedule_id_invalid")
    link = _bounded_text(raw.get("link"), field="link", minimum=10, maximum=600)
    parsed = urlparse(link)
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_LINK_HOSTS:
        raise AnnouncementConfigError("link_not_allowed")
    if type(raw.get("delete_after_success")) is not bool:
        raise AnnouncementConfigError("delete_after_success_invalid")
    return {
        "schema_version": 1,
        "schedule_id": schedule_id,
        "title": _bounded_text(raw.get("title"), field="title", minimum=2, maximum=160),
        "summary": _bounded_text(raw.get("summary"), field="summary", minimum=2, maximum=600),
        "link": link,
        "telegram_text": _bounded_text(
            raw.get("telegram_text"),
            field="telegram_text",
            minimum=2,
            maximum=4000,
        ),
        "delete_after_success": bool(raw["delete_after_success"]),
    }


def _idempotency_key(schedule_id: str, action: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"pokrov:{schedule_id}:{action}"))


def _execution_facts(result: Mapping[str, Any]) -> dict[str, Any]:
    facts = result.get("result")
    return dict(facts) if isinstance(facts, Mapping) else {}


def _existing_outcome(api_module, *, key: str) -> dict[str, Any] | None:
    session = api_module.SessionLocal()
    try:
        row = (
            session.query(api_module.AdminActionIntent)
            .filter(api_module.AdminActionIntent.client_idempotency_key == key)
            .order_by(api_module.AdminActionIntent.created_at.desc())
            .first()
        )
        if row is None:
            return None
        return {
            "status": str(row.status or "unknown"),
            "intent_id": str(row.id),
        }
    finally:
        session.close()


async def _execute_guarded(
    api_module,
    *,
    actor_tg_id: int,
    action: str,
    target: Mapping[str, str],
    payload: Mapping[str, Any],
    idempotency_key: str,
) -> dict[str, Any]:
    from admin_action_intent_service import confirmation_sha256

    existing = _existing_outcome(api_module, key=idempotency_key)
    if existing is not None:
        return {"ok": existing["status"] == "completed", **existing, "replayed": True}

    session = api_module.SessionLocal()
    try:
        prepared = api_module._prepare_action_intent(
            session=session,
            actor_tg_id=actor_tg_id,
            action=action,
            target=target,
            payload=payload,
        )
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    result = await api_module._execute_action_intent(
        session_factory=api_module.SessionLocal,
        actor_tg_id=actor_tg_id,
        intent_id=str(prepared["intent_id"]),
        idempotency_key=idempotency_key,
        confirmation_sha256_header=confirmation_sha256(
            str(prepared["confirmation_challenge"])
        ),
        action=action,
        target=target,
        payload=payload,
        audit_writer=api_module._add_admin_audit,
        db_executor=lambda session, state, normalized, runtime: (
            api_module._execute_admin_client_action_db(
                session,
                state,
                dict(normalized),
                dict(runtime),
                actor_tg_id=actor_tg_id,
                action=action,
            )
        ),
        external_executor=api_module._execute_admin_client_action_external,
        post_commit_executor=api_module._execute_admin_post_commit,
        external_timeout_seconds=300.0 if action == "broadcast.send" else 30.0,
    )
    return dict(result)


async def run_announcement(config: Mapping[str, Any]) -> dict[str, Any]:
    import api as api_module

    actor_tg_id = int(api_module.Settings.ADMIN_ID or 0)
    if actor_tg_id <= 0:
        raise RuntimeError("admin_actor_unavailable")
    schedule_id = str(config["schedule_id"])
    published_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    live_update = await _execute_guarded(
        api_module,
        actor_tg_id=actor_tg_id,
        action="live_update.create",
        target={"type": "live_update", "id": "new"},
        payload={
            "title": str(config["title"]),
            "summary": str(config["summary"]),
            "link": str(config["link"]),
            "published_at": published_at,
            "is_active": True,
            "sort_order": 10,
        },
        idempotency_key=_idempotency_key(schedule_id, "live_update.create"),
    )
    broadcast = await _execute_guarded(
        api_module,
        actor_tg_id=actor_tg_id,
        action="broadcast.send",
        target={"type": "broadcast", "id": "broadcast"},
        payload={
            "segment": "all_active",
            "limit": 500,
            "tg_ids": [],
            "text": str(config["telegram_text"]),
        },
        idempotency_key=_idempotency_key(schedule_id, "broadcast.send"),
    )
    broadcast_facts = _execution_facts(broadcast)
    return {
        "ok": bool(live_update.get("ok")) and bool(broadcast.get("ok")),
        "schedule_id": schedule_id,
        "live_update_status": str(live_update.get("status") or "unknown"),
        "broadcast_status": str(broadcast.get("status") or "unknown"),
        "broadcast_sent": int(broadcast_facts.get("sent") or 0),
        "broadcast_failed": int(broadcast_facts.get("failed") or 0),
        "broadcast_reason_counts": dict(
            broadcast_facts.get("reason_counts") or {}
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute one guarded POKROV release announcement from a root-only config."
    )
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config_path = Path(args.config)
    try:
        config = load_announcement_config(config_path)
        result = asyncio.run(run_announcement(config))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        if result["ok"] and config["delete_after_success"]:
            config_path.resolve(strict=True).unlink()
        return 0 if result["ok"] else 2
    except AnnouncementConfigError as exc:
        print(json.dumps({"ok": False, "code": str(exc)}, sort_keys=True))
        return 2
    except Exception as exc:
        print(
            json.dumps(
                {"ok": False, "code": "announcement_failed", "error_type": type(exc).__name__},
                sort_keys=True,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
