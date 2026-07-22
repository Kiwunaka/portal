from __future__ import annotations

import ipaddress
import json
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import String, func
from sqlalchemy.exc import IntegrityError

from models import (
    AccountDevice,
    Node,
    ObserverBatch,
    ObserverDailyObservation,
    ObserverUserState,
    ObserverWindowObservation,
    User,
    UserNode,
)
from economy_service import (
    activate_reserved_trial,
    observer_evidence_key,
    record_connection_evidence,
)
from account_experience_service import record_first_connection_verified


OBSERVER_RETENTION_DAYS = max(7, int(os.getenv("OBSERVER_RETENTION_DAYS", "30")))
OBSERVER_WINDOW_MINUTES = max(1, int(os.getenv("OBSERVER_WINDOW_MINUTES", "10")))
OBSERVER_PUSH_MAX_AGE_SECONDS = max(60, int(os.getenv("OBSERVER_PUSH_MAX_AGE_SECONDS", "300")))
OBSERVER_PUSH_STALE_AFTER_SECONDS = max(120, int(os.getenv("OBSERVER_PUSH_STALE_AFTER_SECONDS", "180")))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _safe_iso(value: datetime | None) -> str | None:
    if not value:
        return None
    return value.replace(microsecond=0).isoformat()


def _window_bucket(dt: datetime) -> datetime:
    minute = (dt.minute // OBSERVER_WINDOW_MINUTES) * OBSERVER_WINDOW_MINUTES
    return dt.replace(minute=minute, second=0, microsecond=0)


def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def observer_batch_replay_response(batch: ObserverBatch) -> dict[str, Any]:
    updated = json.loads(str(batch.updated_tg_ids_json or "[]") or "[]")
    return {
        "accepted_count": 0,
        "deduped_count": int(batch.observation_count or 0),
        "unmatched_count": int(batch.unmatched_count or 0),
        "updated_tg_ids": sorted({int(value) for value in updated}),
        "activated_trial_count": 0,
    }


def is_observer_batch_unique_conflict(exc: IntegrityError) -> bool:
    diag = getattr(getattr(exc, "orig", None), "diag", None)
    if str(getattr(diag, "constraint_name", "") or "") == "uq_observer_batches_node_batch":
        return True
    detail = " ".join(
        str(value or "")
        for value in (getattr(exc, "statement", None), getattr(exc, "orig", None), exc)
    ).lower()
    return "observer_batches" in detail and (
        "uq_observer_batches_node_batch" in detail
        or ("unique" in detail and "node_id" in detail and "batch_id" in detail)
        or "insert observer_batches" in detail
    )


def observer_stale_after_seconds() -> int:
    return OBSERVER_PUSH_STALE_AFTER_SECONDS


def normalize_source_ip(source_ip: str) -> dict[str, Any]:
    raw = str(source_ip or "").strip()
    if not raw:
        raise ValueError("source_ip is required")
    ip_obj = ipaddress.ip_address(raw)
    source_ip_raw = str(ip_obj)
    if ip_obj.version == 4:
        score_ip_key = source_ip_raw
    else:
        score_ip_key = str(ipaddress.ip_network(f"{source_ip_raw}/64", strict=False))
    counts_for_suspicion = bool(getattr(ip_obj, "is_global", False))
    return {
        "source_ip_raw": source_ip_raw,
        "score_ip_key": score_ip_key,
        "counts_for_suspicion": counts_for_suspicion,
    }


def parse_observer_datetime(value: str | None) -> datetime:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("occurred_at is required")
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.replace(microsecond=0)


def _resolve_user_for_observation(
    *,
    s,
    node_id: int,
    client_email: str,
    client_sub_id: str,
    client_tg_id: int | None,
) -> tuple[User | None, str]:
    email_norm = str(client_email or "").strip().lower()
    if email_norm:
        row = (
            s.query(UserNode.tg_id)
            .filter(UserNode.node_id == int(node_id), func.lower(UserNode.panel_email) == email_norm)
            .first()
        )
        if row:
            user = s.query(User).filter(User.tg_id == int(row[0])).first()
            if user:
                return user, "panel_email"

        user = s.query(User).filter(func.lower(User.email) == email_norm).first()
        if user:
            return user, "user_email"

    if client_tg_id is not None and int(client_tg_id) != 0:
        user = s.query(User).filter(User.tg_id == int(client_tg_id)).first()
        if user:
            return user, "tg_id"

    sub_id = str(client_sub_id or "").strip()
    if sub_id:
        user = (
            s.query(User)
            .filter(
                (User.sub_token == sub_id)
                | (func.cast(User.tg_id, String) == sub_id)
            )
            .first()
        )
        if user:
            return user, "sub_id"

    return None, ""


def _upsert_daily_observation(
    *,
    s,
    tg_id: int,
    node_id: int,
    source_ip_raw: str,
    score_ip_key: str,
    seen_at: datetime,
    identity_source: str,
    counts_for_suspicion: bool,
) -> None:
    bucket = seen_at.date()
    row = (
        s.query(ObserverDailyObservation)
        .filter(
            ObserverDailyObservation.tg_id == int(tg_id),
            ObserverDailyObservation.node_id == int(node_id),
            ObserverDailyObservation.source_ip_raw == source_ip_raw,
            ObserverDailyObservation.day_bucket == bucket,
        )
        .first()
    )
    if not row:
        s.add(
            ObserverDailyObservation(
                tg_id=int(tg_id),
                node_id=int(node_id),
                source_ip_raw=source_ip_raw,
                score_ip_key=score_ip_key,
                day_bucket=bucket,
                first_seen_at=seen_at,
                last_seen_at=seen_at,
                hit_count=1,
                identity_source=identity_source,
                counts_for_suspicion=bool(counts_for_suspicion),
            )
        )
        return
    row.first_seen_at = min(row.first_seen_at, seen_at)
    row.last_seen_at = max(row.last_seen_at, seen_at)
    row.hit_count = int(row.hit_count or 0) + 1
    row.identity_source = identity_source or row.identity_source
    row.counts_for_suspicion = bool(row.counts_for_suspicion or counts_for_suspicion)


def _upsert_window_observation(
    *,
    s,
    tg_id: int,
    node_id: int,
    source_ip_raw: str,
    score_ip_key: str,
    seen_at: datetime,
    counts_for_suspicion: bool,
) -> None:
    bucket = _window_bucket(seen_at)
    row = (
        s.query(ObserverWindowObservation)
        .filter(
            ObserverWindowObservation.tg_id == int(tg_id),
            ObserverWindowObservation.node_id == int(node_id),
            ObserverWindowObservation.score_ip_key == score_ip_key,
            ObserverWindowObservation.window_bucket_at == bucket,
        )
        .first()
    )
    if not row:
        s.add(
            ObserverWindowObservation(
                tg_id=int(tg_id),
                node_id=int(node_id),
                source_ip_raw=source_ip_raw,
                score_ip_key=score_ip_key,
                window_bucket_at=bucket,
                first_seen_at=seen_at,
                last_seen_at=seen_at,
                hit_count=1,
                counts_for_suspicion=bool(counts_for_suspicion),
            )
        )
        return
    row.first_seen_at = min(row.first_seen_at, seen_at)
    row.last_seen_at = max(row.last_seen_at, seen_at)
    row.hit_count = int(row.hit_count or 0) + 1
    row.counts_for_suspicion = bool(row.counts_for_suspicion or counts_for_suspicion)


def _distinct_counts(rows: list[ObserverDailyObservation], *, since: datetime) -> tuple[int, int]:
    score_keys = {
        str(row.score_ip_key or "")
        for row in rows
        if bool(row.counts_for_suspicion) and row.last_seen_at and row.last_seen_at >= since
    }
    node_ids = {
        int(row.node_id)
        for row in rows
        if bool(row.counts_for_suspicion) and row.last_seen_at and row.last_seen_at >= since
    }
    return len(score_keys), len(node_ids)


def _overlap_count_24h(*, window_rows: list[ObserverWindowObservation]) -> int:
    grouped: dict[datetime, dict[str, set[Any]]] = {}
    for row in window_rows:
        if not bool(row.counts_for_suspicion):
            continue
        bucket = row.window_bucket_at
        current = grouped.setdefault(bucket, {"nodes": set(), "score_keys": set()})
        current["nodes"].add(int(row.node_id))
        current["score_keys"].add(str(row.score_ip_key or ""))
    return sum(
        1
        for current in grouped.values()
        if len(current["nodes"]) >= 2 and len(current["score_keys"]) >= 2
    )


def _snapshot_to_dict(row: ObserverUserState | None) -> dict[str, Any]:
    if not row:
        return {
            "state": "ok",
            "reasons": [],
            "observed_ip_count_24h": 0,
            "observed_ip_count_7d": 0,
            "observed_ip_count_30d": 0,
            "observed_node_count_24h": 0,
            "observed_node_count_7d": 0,
            "observed_node_count_30d": 0,
            "overlap_count_24h": 0,
            "last_observed_at": None,
            "updated_at": None,
        }
    return {
        "state": str(row.state or "ok"),
        "reasons": json.loads(str(row.reasons_json or "[]") or "[]"),
        "observed_ip_count_24h": int(row.observed_ip_count_24h or 0),
        "observed_ip_count_7d": int(row.observed_ip_count_7d or 0),
        "observed_ip_count_30d": int(row.observed_ip_count_30d or 0),
        "observed_node_count_24h": int(row.observed_node_count_24h or 0),
        "observed_node_count_7d": int(row.observed_node_count_7d or 0),
        "observed_node_count_30d": int(row.observed_node_count_30d or 0),
        "overlap_count_24h": int(row.overlap_count_24h or 0),
        "last_observed_at": _safe_iso(row.last_observed_at),
        "updated_at": _safe_iso(row.updated_at),
    }


def recompute_user_observer_state(s, *, tg_id: int, now: datetime | None = None) -> dict[str, Any]:
    current_now = (now or _utcnow()).replace(microsecond=0)
    since_24h = current_now - timedelta(hours=24)
    since_7d = current_now - timedelta(days=7)
    since_30d = current_now - timedelta(days=OBSERVER_RETENTION_DAYS)

    daily_rows = (
        s.query(ObserverDailyObservation)
        .filter(ObserverDailyObservation.tg_id == int(tg_id), ObserverDailyObservation.last_seen_at >= since_30d)
        .all()
    )
    window_rows = (
        s.query(ObserverWindowObservation)
        .filter(ObserverWindowObservation.tg_id == int(tg_id), ObserverWindowObservation.last_seen_at >= since_24h)
        .all()
    )

    ip_count_24h, node_count_24h = _distinct_counts(daily_rows, since=since_24h)
    ip_count_7d, node_count_7d = _distinct_counts(daily_rows, since=since_7d)
    ip_count_30d, node_count_30d = _distinct_counts(daily_rows, since=since_30d)
    overlap_count = _overlap_count_24h(window_rows=window_rows)
    last_observed_candidates = [row.last_seen_at for row in daily_rows if row.last_seen_at]
    last_observed_at = max(last_observed_candidates) if last_observed_candidates else None

    reasons: list[str] = []
    state = "ok"
    if overlap_count >= 1:
        state = "suspicious"
        reasons.append("multi_node_overlap_10m")
    elif ip_count_24h >= 5 and node_count_24h >= 2 and overlap_count >= 2:
        state = "suspicious"
        reasons.append("repeated_multi_node_overlap")
    elif (ip_count_24h >= 3 and node_count_24h >= 2) or ip_count_7d >= 5:
        state = "watch"
        if ip_count_24h >= 3 and node_count_24h >= 2:
            reasons.append("multi_ip_multi_node_24h")
        if ip_count_7d >= 5:
            reasons.append("multi_ip_7d")

    row = s.query(ObserverUserState).filter(ObserverUserState.tg_id == int(tg_id)).first()
    if not row:
        row = ObserverUserState(tg_id=int(tg_id))
        s.add(row)
    row.state = state
    row.reasons_json = _json_dump(reasons)
    row.observed_ip_count_24h = int(ip_count_24h)
    row.observed_ip_count_7d = int(ip_count_7d)
    row.observed_ip_count_30d = int(ip_count_30d)
    row.observed_node_count_24h = int(node_count_24h)
    row.observed_node_count_7d = int(node_count_7d)
    row.observed_node_count_30d = int(node_count_30d)
    row.overlap_count_24h = int(overlap_count)
    row.last_observed_at = last_observed_at
    row.updated_at = current_now
    return _snapshot_to_dict(row)


def get_observer_state_map(s, *, tg_ids: list[int]) -> dict[int, dict[str, Any]]:
    wanted = sorted({int(tg_id) for tg_id in tg_ids if int(tg_id)})
    if not wanted:
        return {}
    rows = s.query(ObserverUserState).filter(ObserverUserState.tg_id.in_(wanted)).all()
    return {int(row.tg_id): _snapshot_to_dict(row) for row in rows}


def build_admin_observer_block(s, *, tg_id: int, limit: int = 8) -> dict[str, Any]:
    state_row = s.query(ObserverUserState).filter(ObserverUserState.tg_id == int(tg_id)).first()
    base = _snapshot_to_dict(state_row)
    daily_rows = (
        s.query(ObserverDailyObservation, Node.code, Node.name)
        .outerjoin(Node, Node.id == ObserverDailyObservation.node_id)
        .filter(ObserverDailyObservation.tg_id == int(tg_id))
        .order_by(ObserverDailyObservation.last_seen_at.desc(), ObserverDailyObservation.id.desc())
        .limit(max(1, min(int(limit), 20)))
        .all()
    )
    recent_ips = [
        {
            "source_ip_raw": str(row.source_ip_raw or ""),
            "score_ip_key": str(row.score_ip_key or ""),
            "node_code": str(node_code or "") or None,
            "node_name": str(node_name or "") or None,
            "last_seen_at": _safe_iso(row.last_seen_at),
            "counts_for_suspicion": bool(row.counts_for_suspicion),
        }
        for row, node_code, node_name in daily_rows
    ]

    node_rollup_rows = (
        s.query(
            ObserverDailyObservation.node_id,
            func.max(ObserverDailyObservation.last_seen_at).label("last_seen_at"),
            func.count(func.distinct(ObserverDailyObservation.score_ip_key)).label("score_ip_count"),
            Node.code,
            Node.name,
        )
        .outerjoin(Node, Node.id == ObserverDailyObservation.node_id)
        .filter(ObserverDailyObservation.tg_id == int(tg_id))
        .group_by(ObserverDailyObservation.node_id, Node.code, Node.name)
        .order_by(func.max(ObserverDailyObservation.last_seen_at).desc())
        .limit(max(1, min(int(limit), 20)))
        .all()
    )
    recent_nodes = [
        {
            "node_id": int(node_id),
            "node_code": str(node_code or "") or None,
            "node_name": str(node_name or "") or None,
            "last_seen_at": _safe_iso(last_seen_at),
            "score_ip_count": int(score_ip_count or 0),
        }
        for node_id, last_seen_at, score_ip_count, node_code, node_name in node_rollup_rows
    ]

    return {**base, "recent_ips": recent_ips, "recent_nodes": recent_nodes}


def ingest_observer_batch(
    s,
    *,
    node: Node,
    batch_id: str,
    cursor: dict[str, Any] | None,
    observations: list[dict[str, Any]],
    collector_parse_error_count: int = 0,
    received_at: datetime | None = None,
) -> dict[str, Any]:
    current_now = (received_at or _utcnow()).replace(microsecond=0)
    batch_key = str(batch_id or "").strip()
    if not batch_key:
        raise ValueError("batch_id is required")

    existing = (
        s.query(ObserverBatch)
        .filter(ObserverBatch.node_id == int(node.id), ObserverBatch.batch_id == batch_key)
        .first()
    )
    if existing:
        return observer_batch_replay_response(existing)

    accepted_count = 0
    unmatched_count = 0
    parse_error_count = max(0, int(collector_parse_error_count or 0))
    touched_tg_ids: set[int] = set()
    activated_trial_count = 0

    for item in list(observations or []):
        try:
            seen_at = parse_observer_datetime(item.get("occurred_at"))
            normalized = normalize_source_ip(item.get("source_ip"))
        except Exception:
            parse_error_count += 1
            continue

        client_tg_id_raw = item.get("client_tg_id")
        try:
            client_tg_id = int(client_tg_id_raw) if client_tg_id_raw is not None else None
        except Exception:
            client_tg_id = None

        user, identity_source = _resolve_user_for_observation(
            s=s,
            node_id=int(node.id),
            client_email=str(item.get("client_email") or ""),
            client_sub_id=str(item.get("client_sub_id") or ""),
            client_tg_id=client_tg_id,
        )
        if not user:
            unmatched_count += 1
            continue

        accepted_count += 1
        touched_tg_ids.add(int(user.tg_id))
        _upsert_daily_observation(
            s=s,
            tg_id=int(user.tg_id),
            node_id=int(node.id),
            source_ip_raw=str(normalized["source_ip_raw"]),
            score_ip_key=str(normalized["score_ip_key"]),
            seen_at=seen_at,
            identity_source=identity_source,
            counts_for_suspicion=bool(normalized["counts_for_suspicion"]),
        )
        _upsert_window_observation(
            s=s,
            tg_id=int(user.tg_id),
            node_id=int(node.id),
            source_ip_raw=str(normalized["source_ip_raw"]),
            score_ip_key=str(normalized["score_ip_key"]),
            seen_at=seen_at,
            counts_for_suspicion=bool(normalized["counts_for_suspicion"]),
        )
        account_id = str(getattr(user, "account_id", "") or "").strip()
        if account_id:
            device_id = None
            install_id = str(getattr(user, "app_install_id", "") or "").strip()
            if install_id:
                device_row = (
                    s.query(AccountDevice.id)
                    .filter(AccountDevice.account_id == account_id, AccountDevice.install_id == install_id)
                    .first()
                )
                device_id = str(device_row[0]) if device_row else None
            stable_key = observer_evidence_key(
                identity_key=f"legacy-user:{int(user.tg_id)}",
                node_id=int(node.id),
                observed_at=seen_at,
            )
            evidence = record_connection_evidence(
                s,
                account_id=account_id,
                device_id=device_id,
                node_id=int(node.id),
                evidence_kind="observer_connection",
                observed_at=seen_at,
                evidence_key=stable_key,
            )
            record_first_connection_verified(
                s,
                account_id=account_id,
                verified_at=evidence.observed_at,
            )
            activation = activate_reserved_trial(s, account_id=account_id, evidence=evidence)
            if activation.activated_now:
                activated_trial_count += 1

    for tg_id in sorted(touched_tg_ids):
        recompute_user_observer_state(s=s, tg_id=int(tg_id), now=current_now)

    node.observer_last_push_at = current_now
    node.observer_last_batch_id = batch_key
    node.observer_unmatched_count = int(unmatched_count)
    node.observer_parse_error_count = int(parse_error_count)

    s.add(
        ObserverBatch(
            node_id=int(node.id),
            batch_id=batch_key,
            cursor_json=_json_dump(cursor or {}),
            observation_count=int(len(observations or [])),
            accepted_count=int(accepted_count),
            deduped_count=0,
            unmatched_count=int(unmatched_count),
            parse_error_count=int(parse_error_count),
            updated_tg_ids_json=_json_dump(sorted(touched_tg_ids)),
            created_at=current_now,
        )
    )

    return {
        "accepted_count": int(accepted_count),
        "deduped_count": 0,
        "unmatched_count": int(unmatched_count),
        "updated_tg_ids": sorted(touched_tg_ids),
        "activated_trial_count": int(activated_trial_count),
    }


def cleanup_observer_retention(s, *, now: datetime | None = None) -> dict[str, int]:
    current_now = (now or _utcnow()).replace(microsecond=0)
    cutoff = current_now - timedelta(days=OBSERVER_RETENTION_DAYS)

    daily_tg_ids = [
        int(row[0])
        for row in s.query(ObserverDailyObservation.tg_id)
        .filter(ObserverDailyObservation.last_seen_at < cutoff)
        .distinct()
        .all()
    ]
    window_tg_ids = [
        int(row[0])
        for row in s.query(ObserverWindowObservation.tg_id)
        .filter(ObserverWindowObservation.last_seen_at < cutoff)
        .distinct()
        .all()
    ]
    stale_state_tg_ids = [
        int(row[0])
        for row in s.query(ObserverUserState.tg_id)
        .filter(ObserverUserState.last_observed_at.isnot(None), ObserverUserState.last_observed_at < cutoff)
        .all()
    ]
    touched_tg_ids = sorted(set(daily_tg_ids + window_tg_ids + stale_state_tg_ids))

    daily_deleted = (
        s.query(ObserverDailyObservation)
        .filter(ObserverDailyObservation.last_seen_at < cutoff)
        .delete(synchronize_session=False)
    )
    window_deleted = (
        s.query(ObserverWindowObservation)
        .filter(ObserverWindowObservation.last_seen_at < cutoff)
        .delete(synchronize_session=False)
    )
    batch_deleted = (
        s.query(ObserverBatch)
        .filter(ObserverBatch.created_at < cutoff)
        .delete(synchronize_session=False)
    )

    for tg_id in touched_tg_ids:
        recompute_user_observer_state(s=s, tg_id=int(tg_id), now=current_now)

    return {
        "daily_deleted": int(daily_deleted or 0),
        "window_deleted": int(window_deleted or 0),
        "batch_deleted": int(batch_deleted or 0),
        "users_recomputed": int(len(touched_tg_ids)),
    }
