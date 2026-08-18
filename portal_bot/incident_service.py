from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from models import EntitlementGrant, Event, ServiceIncident, User
from economy_service import grant_internal_bonus_days, resolve_canonical_account_id


ALLOWED_COMPENSATION_DAYS = frozenset({0, 1, 3, 7, 30})


@dataclass(frozen=True)
class IncidentCompensationPreview:
    incident_id: str
    incident_key: str
    impacted_account_ids: tuple[str, ...]
    compensation_days: int

    @property
    def impacted_accounts(self) -> int:
        return len(self.impacted_account_ids)


@dataclass(frozen=True)
class IncidentCompensationResult:
    incident_id: str
    incident_key: str
    impacted_accounts: int
    granted_accounts: int
    existing_grants: int
    compensation_days: int
    completed_at: datetime


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def normalize_node_codes(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, ValueError):
            value = []
    if not isinstance(value, (list, tuple, set)):
        return ()
    return tuple(
        sorted(
            {
                str(item or "").strip().lower()[:32]
                for item in value
                if str(item or "").strip()
            }
        )
    )[:100]


def incident_node_codes(incident: ServiceIncident) -> tuple[str, ...]:
    return normalize_node_codes(incident.affected_node_codes_json)


def incident_payload(incident: ServiceIncident) -> dict[str, Any]:
    return {
        "id": str(incident.id),
        "key": str(incident.incident_key),
        "title": str(incident.title),
        "summary": str(incident.summary),
        "severity": str(incident.severity),
        "status": str(incident.status),
        "startedAt": _safe_iso(incident.started_at),
        "endedAt": _safe_iso(incident.ended_at),
        "affectedNodeCodes": list(incident_node_codes(incident)),
        "compensationDays": int(incident.compensation_days or 0),
        "compensationState": (
            "completed"
            if incident.compensation_completed_at is not None
            else "pending"
            if str(incident.status) == "resolved" and int(incident.compensation_days or 0) > 0
            else "not_applicable"
        ),
        "impactedAccounts": int(incident.impacted_accounts_count or 0),
        "grantedAccounts": int(incident.granted_accounts_count or 0),
        "confirmedAt": _safe_iso(incident.confirmed_at),
        "resolvedAt": _safe_iso(incident.resolved_at),
        "compensationCompletedAt": _safe_iso(incident.compensation_completed_at),
    }


def preview_incident_compensation(
    session,
    *,
    incident: ServiceIncident,
) -> IncidentCompensationPreview:
    _validate_compensable_incident(incident)
    affected_nodes = set(incident_node_codes(incident))
    rows = (
        session.query(Event)
        .filter(
            Event.event_name.in_(("client_runtime_stats", "connected_ok")),
            Event.created_at >= incident.started_at,
            Event.created_at <= incident.ended_at,
        )
        .order_by(Event.created_at.asc(), Event.id.asc())
        .all()
    )
    tg_ids: set[int] = set()
    for row in rows:
        try:
            meta = json.loads(str(row.meta_json or "{}"))
        except (TypeError, ValueError):
            continue
        if not isinstance(meta, dict) or meta.get("connected") is not True:
            continue
        node_code = str(meta.get("selected_node_code") or "").strip().lower()
        if affected_nodes and node_code not in affected_nodes:
            continue
        tg_ids.add(int(row.tg_id))

    account_ids: set[str] = set()
    if tg_ids:
        users = session.query(User).filter(User.tg_id.in_(sorted(tg_ids))).all()
        for user in users:
            account_id = str(user.account_id or "").strip()
            if account_id:
                account_ids.add(
                    resolve_canonical_account_id(session, account_id=account_id)
                )
    return IncidentCompensationPreview(
        incident_id=str(incident.id),
        incident_key=str(incident.incident_key),
        impacted_account_ids=tuple(sorted(account_ids)),
        compensation_days=int(incident.compensation_days or 0),
    )


def apply_incident_compensation(
    session,
    *,
    incident_id: str,
    now: datetime | None = None,
) -> IncidentCompensationResult:
    current = _naive_utc(now or utcnow())
    incident = (
        session.query(ServiceIncident)
        .filter(ServiceIncident.id == str(incident_id))
        .with_for_update()
        .one()
    )
    preview = preview_incident_compensation(session, incident=incident)
    prefix = f"incident-compensation:v1:{incident.id}:"
    if incident.compensation_completed_at is not None:
        existing_count = (
            session.query(EntitlementGrant)
            .filter(EntitlementGrant.idempotency_key.like(f"{prefix}%"))
            .count()
        )
        return IncidentCompensationResult(
            incident_id=str(incident.id),
            incident_key=str(incident.incident_key),
            impacted_accounts=int(incident.impacted_accounts_count or preview.impacted_accounts),
            granted_accounts=int(incident.granted_accounts_count or existing_count),
            existing_grants=existing_count,
            compensation_days=int(incident.compensation_days or 0),
            completed_at=incident.compensation_completed_at,
        )

    incident.compensation_started_at = incident.compensation_started_at or current
    created = 0
    existing = 0
    if preview.compensation_days > 0:
        users_by_account = {
            resolve_canonical_account_id(session, account_id=str(user.account_id)): user
            for user in session.query(User)
            .filter(User.account_id.in_(list(preview.impacted_account_ids)))
            .order_by(User.created_at.asc(), User.tg_id.asc())
            .all()
            if str(user.account_id or "").strip()
        }
        for account_id in preview.impacted_account_ids:
            idempotency_key = f"{prefix}{account_id}"
            existed = (
                session.query(EntitlementGrant.id)
                .filter(EntitlementGrant.idempotency_key == idempotency_key)
                .first()
                is not None
            )
            owner = users_by_account.get(account_id)
            grant_internal_bonus_days(
                session,
                account_id=account_id,
                source="incident_compensation",
                plan_code="incident_compensation",
                idempotency_key=idempotency_key,
                days=preview.compensation_days,
                legacy_tg_id=int(owner.tg_id) if owner is not None else None,
                metadata={
                    "incident_id": str(incident.id),
                    "incident_key": str(incident.incident_key),
                    "incident_title": str(incident.title)[:160],
                    "started_at": _safe_iso(incident.started_at),
                    "ended_at": _safe_iso(incident.ended_at),
                    "eligibility": "connected_runtime_event_in_incident_window",
                },
                now=current,
            )
            if existed:
                existing += 1
            else:
                created += 1

    incident.impacted_accounts_count = preview.impacted_accounts
    incident.granted_accounts_count = created + existing
    incident.compensation_completed_at = current
    incident.updated_at = current
    session.flush()
    return IncidentCompensationResult(
        incident_id=str(incident.id),
        incident_key=str(incident.incident_key),
        impacted_accounts=preview.impacted_accounts,
        granted_accounts=created,
        existing_grants=existing,
        compensation_days=preview.compensation_days,
        completed_at=current,
    )


def process_pending_incident_compensations(
    session,
    *,
    now: datetime | None = None,
    limit: int = 20,
) -> dict[str, int]:
    current = _naive_utc(now or utcnow())
    rows = (
        session.query(ServiceIncident.id)
        .filter(
            ServiceIncident.status == "resolved",
            ServiceIncident.compensation_completed_at.is_(None),
        )
        .order_by(ServiceIncident.resolved_at.asc(), ServiceIncident.created_at.asc())
        .limit(max(1, min(100, int(limit))))
        .all()
    )
    processed = 0
    impacted = 0
    granted = 0
    for (incident_id,) in rows:
        result = apply_incident_compensation(
            session,
            incident_id=str(incident_id),
            now=current,
        )
        processed += 1
        impacted += result.impacted_accounts
        granted += result.granted_accounts
    return {
        "processed": processed,
        "impacted_accounts": impacted,
        "granted_accounts": granted,
    }


def _validate_compensable_incident(incident: ServiceIncident) -> None:
    if str(incident.status or "") != "resolved" or incident.ended_at is None:
        raise ValueError("incident_not_resolved")
    if incident.ended_at < incident.started_at:
        raise ValueError("incident_window_invalid")
    if int(incident.compensation_days or 0) not in ALLOWED_COMPENSATION_DAYS:
        raise ValueError("incident_compensation_days_invalid")


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.replace(microsecond=0)


def _safe_iso(value: datetime | None) -> str | None:
    return _naive_utc(value).isoformat() if value is not None else None
