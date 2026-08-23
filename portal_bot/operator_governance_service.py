"""Governance read models for operators, audit lineage and privacy controls."""

from __future__ import annotations

import csv
import io
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, func, or_

try:
    from .admin_v2.roles import ROLE_REGISTRY
    from .antiabuse_privacy_service import antiabuse_retention_status
    from .models import (
        AdminActionIntent,
        AdminAudit,
        AdminOperator,
        AdminOperatorAudit,
        AdminOperatorRole,
        AdminOperatorSession,
        Event,
        ExternalPaymentEvent,
        FunnelEvent,
        PayAttempt,
        RenderedSubscriptionSnapshot,
        SubscriptionFetchEvent,
        SupportBundleAccessAudit,
        SupportBundleUpload,
    )
except ImportError:
    from admin_v2.roles import ROLE_REGISTRY
    from antiabuse_privacy_service import antiabuse_retention_status
    from models import (
        AdminActionIntent,
        AdminAudit,
        AdminOperator,
        AdminOperatorAudit,
        AdminOperatorRole,
        AdminOperatorSession,
        Event,
        ExternalPaymentEvent,
        FunnelEvent,
        PayAttempt,
        RenderedSubscriptionSnapshot,
        SubscriptionFetchEvent,
        SupportBundleAccessAudit,
        SupportBundleUpload,
    )


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_list(value: str | None) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def role_is_active(row: AdminOperatorRole, *, now: datetime | None = None) -> bool:
    current = now or _now()
    return row.revoked_at is None and (row.expires_at is None or row.expires_at > current)


def role_payload(row: AdminOperatorRole, *, now: datetime | None = None) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "role_code": str(row.role_code),
        "environment": str(row.environment_scope),
        "grant_kind": str(row.grant_kind or "standing"),
        "grant_reason": str(row.grant_reason or "") or None,
        "granted_by_operator_id": str(row.granted_by_operator_id or "") or None,
        "granted_at": _iso(row.granted_at),
        "expires_at": _iso(row.expires_at),
        "active": role_is_active(row, now=now),
        "review_status": str(row.review_status or "not_required"),
        "reviewed_by_operator_id": str(row.reviewed_by_operator_id or "") or None,
        "reviewed_at": _iso(row.reviewed_at),
        "review_note": str(row.review_note or "") or None,
        "revoked_at": _iso(row.revoked_at),
        "revoke_reason": str(row.revoke_reason or "") or None,
    }


def role_catalog() -> dict[str, Any]:
    return {
        "roles": [
            {"code": code, "permissions": sorted(permissions)}
            for code, permissions in sorted(ROLE_REGISTRY.items())
        ],
        "grant_kinds": ["standing", "jit", "break_glass"],
        "temporal_limits_minutes": {"jit": {"min": 15, "max": 1440}, "break_glass": {"min": 5, "max": 60}},
        "rules": {
            "self_role_change": "denied",
            "last_superadmin_revoke": "denied",
            "temporal_post_review": "required",
            "break_glass_superadmin": "denied",
        },
    }


def _operator_rows(session, *, environment: str):
    return (
        session.query(AdminOperator)
        .order_by(AdminOperator.status.asc(), AdminOperator.created_at.asc(), AdminOperator.id.asc())
        .all()
    )


def list_operators(
    session,
    *,
    environment: str,
    q: str = "",
    status: str = "",
    role: str = "",
    limit: int = 100,
) -> dict[str, Any]:
    current = _now()
    query = str(q or "").strip().casefold()
    wanted_status = str(status or "").strip().lower()
    wanted_role = str(role or "").strip().lower()
    result: list[dict[str, Any]] = []
    for operator in _operator_rows(session, environment=environment):
        roles = (
            session.query(AdminOperatorRole)
            .filter(
                AdminOperatorRole.operator_id == str(operator.id),
                AdminOperatorRole.environment_scope == environment,
            )
            .order_by(AdminOperatorRole.role_code.asc())
            .all()
        )
        active_roles = [row for row in roles if role_is_active(row, now=current)]
        sessions = (
            session.query(AdminOperatorSession)
            .filter(
                AdminOperatorSession.operator_id == str(operator.id),
                AdminOperatorSession.environment_scope == environment,
            )
            .order_by(AdminOperatorSession.last_seen_at.desc())
            .all()
        )
        if not roles and not sessions:
            continue
        if wanted_status and str(operator.status) != wanted_status:
            continue
        if wanted_role and not any(str(row.role_code) == wanted_role for row in active_roles):
            continue
        haystack = " ".join(
            [str(operator.id), str(operator.display_name or ""), str(operator.legacy_actor_tg_id or "")]
        ).casefold()
        if query and query not in haystack:
            continue
        active_sessions = [
            row
            for row in sessions
            if row.revoked_at is None
            and row.idle_expires_at > current
            and row.absolute_expires_at > current
        ]
        result.append(
            {
                "id": str(operator.id),
                "legacy_actor_tg_id": int(operator.legacy_actor_tg_id) if operator.legacy_actor_tg_id else None,
                "display_name": str(operator.display_name or "") or None,
                "identity_source": str(operator.identity_source),
                "status": str(operator.status),
                "created_at": _iso(operator.created_at),
                "updated_at": _iso(operator.updated_at),
                "suspended_at": _iso(operator.suspended_at),
                "active_roles": [role_payload(row, now=current) for row in active_roles],
                "pending_reviews": sum(
                    1 for row in roles if str(row.review_status or "") == "pending_review"
                ),
                "active_sessions": len(active_sessions),
                "last_seen_at": _iso(sessions[0].last_seen_at) if sessions else None,
            }
        )
        if len(result) >= max(1, min(int(limit), 200)):
            break
    return {
        "items": result,
        "count": len(result),
        "environment": environment,
        "generated_at": _iso(current),
    }


def operator_detail(session, *, operator_id: str, environment: str) -> dict[str, Any] | None:
    operator = session.query(AdminOperator).filter(AdminOperator.id == str(operator_id)).one_or_none()
    if operator is None:
        return None
    current = _now()
    roles = (
        session.query(AdminOperatorRole)
        .filter(
            AdminOperatorRole.operator_id == str(operator.id),
            AdminOperatorRole.environment_scope == environment,
        )
        .order_by(AdminOperatorRole.granted_at.desc())
        .all()
    )
    sessions = (
        session.query(AdminOperatorSession)
        .filter(
            AdminOperatorSession.operator_id == str(operator.id),
            AdminOperatorSession.environment_scope == environment,
        )
        .order_by(AdminOperatorSession.created_at.desc())
        .limit(100)
        .all()
    )
    if not roles and not sessions:
        return None
    return {
        "operator": {
            "id": str(operator.id),
            "legacy_actor_tg_id": int(operator.legacy_actor_tg_id) if operator.legacy_actor_tg_id else None,
            "display_name": str(operator.display_name or "") or None,
            "identity_source": str(operator.identity_source),
            "status": str(operator.status),
            "created_at": _iso(operator.created_at),
            "updated_at": _iso(operator.updated_at),
            "suspended_at": _iso(operator.suspended_at),
        },
        "roles": [role_payload(row, now=current) for row in roles],
        "sessions": [
            {
                "id": str(row.id),
                "environment": str(row.environment_scope),
                "created_at": _iso(row.created_at),
                "last_seen_at": _iso(row.last_seen_at),
                "idle_expires_at": _iso(row.idle_expires_at),
                "absolute_expires_at": _iso(row.absolute_expires_at),
                "step_up_at": _iso(row.step_up_at),
                "revoked_at": _iso(row.revoked_at),
                "revoke_reason": str(row.revoke_reason or "") or None,
                "active": row.revoked_at is None and row.idle_expires_at > current and row.absolute_expires_at > current,
            }
            for row in sessions
        ],
        "generated_at": _iso(current),
    }


def audit_explorer(
    session,
    *,
    environment: str,
    actor: str = "",
    role: str = "",
    permission: str = "",
    action: str = "",
    result: str = "",
    resource_type: str = "",
    resource_id: str = "",
    command_intent_id: str = "",
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    query = (
        session.query(AdminOperatorAudit, AdminOperator)
        .join(AdminOperator, AdminOperator.id == AdminOperatorAudit.operator_id)
        .filter(AdminOperatorAudit.environment_scope == environment)
    )
    actor_value = str(actor or "").strip()
    if actor_value:
        filters = [AdminOperator.id == actor_value, AdminOperator.display_name.ilike(f"%{actor_value}%")]
        if actor_value.isdigit():
            filters.append(AdminOperator.legacy_actor_tg_id == int(actor_value))
        query = query.filter(or_(*filters))
    if role:
        query = query.filter(AdminOperatorAudit.roles_json.contains(f'"{str(role).strip()}"'))
    if permission:
        query = query.filter(AdminOperatorAudit.permissions_json.contains(f'"{str(permission).strip()}"'))
    if action:
        query = query.filter(AdminOperatorAudit.action == str(action).strip())
    if result:
        query = query.filter(AdminOperatorAudit.result == str(result).strip())
    if resource_type:
        query = query.filter(AdminOperatorAudit.resource_type == str(resource_type).strip())
    if resource_id:
        query = query.filter(AdminOperatorAudit.resource_id == str(resource_id).strip())
    if command_intent_id:
        query = query.filter(AdminOperatorAudit.command_intent_id == str(command_intent_id).strip())
    if since is not None:
        query = query.filter(AdminOperatorAudit.created_at >= since)
    if until is not None:
        query = query.filter(AdminOperatorAudit.created_at <= until)
    rows = query.order_by(AdminOperatorAudit.created_at.desc()).limit(max(1, min(int(limit), 1000))).all()
    items = [
        {
            "id": str(audit.id),
            "operator_id": str(audit.operator_id),
            "operator_name": str(operator.display_name or "") or None,
            "legacy_actor_tg_id": int(operator.legacy_actor_tg_id) if operator.legacy_actor_tg_id else None,
            "session_id": str(audit.session_id or "") or None,
            "action": str(audit.action),
            "result": str(audit.result),
            "reason_code": str(audit.reason_code or "") or None,
            "environment": str(audit.environment_scope),
            "roles": _json_list(audit.roles_json),
            "permissions": _json_list(audit.permissions_json),
            "trace_id": str(audit.trace_id or "") or None,
            "resource": (
                {"type": str(audit.resource_type), "id": str(audit.resource_id or "") or None}
                if audit.resource_type
                else None
            ),
            "command_intent_id": str(audit.command_intent_id or "") or None,
            "legacy_audit_id": int(audit.legacy_audit_id) if audit.legacy_audit_id is not None else None,
            "created_at": _iso(audit.created_at),
        }
        for audit, operator in rows
    ]
    return {"items": items, "count": len(items), "generated_at": _iso(_now())}


def audit_export_csv(payload: dict[str, Any]) -> str:
    buffer = io.StringIO(newline="")
    fields = [
        "id", "created_at", "operator_id", "operator_name", "legacy_actor_tg_id",
        "session_id", "action", "result", "reason_code", "environment", "roles",
        "permissions", "resource_type", "resource_id", "command_intent_id", "legacy_audit_id",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()

    def safe_cell(value: Any) -> Any:
        text = str(value or "")
        return "'" + text if text[:1] in {"=", "+", "-", "@"} else text

    for item in payload.get("items") or []:
        resource = item.get("resource") or {}
        writer.writerow(
            {key: safe_cell(value) for key, value in {
                **item,
                "roles": " ".join(item.get("roles") or []),
                "permissions": " ".join(item.get("permissions") or []),
                "resource_type": resource.get("type"),
                "resource_id": resource.get("id"),
            }.items()}
        )
    return buffer.getvalue()


def command_lineage(session, *, intent_id: str, environment: str) -> dict[str, Any] | None:
    intent = session.query(AdminActionIntent).filter(AdminActionIntent.id == str(intent_id)).one_or_none()
    if intent is None:
        return None
    operator_audits = (
        session.query(AdminOperatorAudit)
        .filter(
            AdminOperatorAudit.command_intent_id == str(intent.id),
            AdminOperatorAudit.environment_scope == environment,
        )
        .order_by(AdminOperatorAudit.created_at.asc())
        .all()
    )
    try:
        canonical_payload = json.loads(str(intent.canonical_payload_json or "{}"))
    except (TypeError, ValueError, json.JSONDecodeError):
        canonical_payload = {}
    intent_environment = (
        str(canonical_payload.get("_environment") or "").strip().lower()
        if isinstance(canonical_payload, dict)
        else ""
    )
    if (intent_environment and intent_environment != environment) or (
        not intent_environment and not operator_audits
    ):
        return None
    legacy = (
        session.query(AdminAudit).filter(AdminAudit.id == intent.admin_audit_id).one_or_none()
        if intent.admin_audit_id is not None
        else None
    )
    return {
        "intent": {
            "id": str(intent.id),
            "actor_tg_id": int(intent.actor_tg_id),
            "action": str(intent.action),
            "target": {"type": str(intent.target_type), "id": str(intent.target_id)},
            "risk_level": str(intent.risk_level),
            "executor_kind": str(intent.executor_kind),
            "payload_hash": str(intent.payload_hash),
            "snapshot_hash": str(intent.snapshot_hash),
            "entity_version_hash": str(intent.entity_version_hash),
            "status": str(intent.status),
            "result_code": str(intent.result_code or "") or None,
            "result_hash": str(intent.result_hash or "") or None,
            "admin_audit_id": int(intent.admin_audit_id) if intent.admin_audit_id is not None else None,
            "created_at": _iso(intent.created_at),
            "consumed_at": _iso(intent.consumed_at),
            "updated_at": _iso(intent.updated_at),
        },
        "legacy_audit": (
            {"id": int(legacy.id), "action": str(legacy.action), "created_at": _iso(legacy.created_at)}
            if legacy is not None
            else None
        ),
        "operator_audits": [
            {
                "id": str(row.id),
                "operator_id": str(row.operator_id),
                "session_id": str(row.session_id or "") or None,
                "action": str(row.action),
                "result": str(row.result),
                "created_at": _iso(row.created_at),
            }
            for row in operator_audits
        ],
    }


def sensitive_access_log(
    session,
    *,
    actor_tg_id: int | None = None,
    action: str = "",
    ticket_id: int | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    query = session.query(SupportBundleAccessAudit)
    if actor_tg_id is not None:
        query = query.filter(SupportBundleAccessAudit.actor_tg_id == int(actor_tg_id))
    if action:
        query = query.filter(SupportBundleAccessAudit.action == str(action).strip())
    if ticket_id is not None:
        query = query.filter(SupportBundleAccessAudit.ticket_id == int(ticket_id))
    rows = query.order_by(SupportBundleAccessAudit.created_at.desc()).limit(max(1, min(int(limit), 1000))).all()
    return {
        "items": [
            {
                "grant_id": str(row.grant_id),
                "upload_id": str(row.upload_id),
                "ticket_id": int(row.ticket_id),
                "actor_tg_id": int(row.actor_tg_id),
                "actor_role": str(row.actor_role),
                "action": str(row.action),
                "reason_code": str(row.reason_code),
                "expires_at": _iso(row.expires_at),
                "used_at": _iso(row.used_at),
                "retention_hold": bool(row.retention_hold),
                "created_at": _iso(row.created_at),
            }
            for row in rows
        ],
        "count": len(rows),
        "source_scope": "global_legacy_support_bundle_authority",
        "generated_at": _iso(_now()),
    }


def _env_days(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return default


def privacy_retention_status(session) -> dict[str, Any]:
    current = _now()
    families = [
        ("events", Event, Event.created_at, "EVENT_RETENTION_DAYS", 90, "delete"),
        ("funnel_events", FunnelEvent, FunnelEvent.created_at, "FUNNEL_EVENT_RETENTION_DAYS", 90, "delete"),
        ("subscription_fetch_events", SubscriptionFetchEvent, SubscriptionFetchEvent.created_at, "SUBSCRIPTION_EVENT_RETENTION_DAYS", 90, "delete"),
        ("rendered_subscription_snapshots", RenderedSubscriptionSnapshot, RenderedSubscriptionSnapshot.created_at, "SUBSCRIPTION_EVENT_RETENTION_DAYS", 90, "delete"),
        ("pay_attempts", PayAttempt, PayAttempt.started_at, "PAY_ATTEMPT_RETENTION_DAYS", 365, "delete"),
        ("external_payment_events", ExternalPaymentEvent, ExternalPaymentEvent.created_at, "EXTERNAL_PAYMENT_EVENT_RETENTION_DAYS", 180, "delete"),
    ]
    retention = []
    for code, model, column, env_name, default, disposition in families:
        days = _env_days(env_name, default)
        count, oldest = session.query(func.count(model.id), func.min(column)).one()
        backlog = session.query(func.count(model.id)).filter(column < current - timedelta(days=days)).scalar()
        retention.append(
            {
                "code": code,
                "raw_retention_days": days,
                "policy_source": env_name,
                "disposition": disposition,
                "rows": int(count or 0),
                "oldest_at": _iso(oldest),
                "expired_backlog": int(backlog or 0),
            }
        )
    accepted_days = _env_days("SUPPORT_BUNDLE_ACCEPTED_RETENTION_DAYS", 30)
    quarantine_days = _env_days("SUPPORT_BUNDLE_QUARANTINE_RETENTION_DAYS", 7)
    access_days = _env_days("SUPPORT_BUNDLE_ACCESS_AUDIT_RETENTION_DAYS", 365)
    try:
        incomplete_grace_days = max(
            0, int(os.getenv("SUPPORT_BUNDLE_INCOMPLETE_GRACE_DAYS", "1"))
        )
    except (TypeError, ValueError):
        incomplete_grace_days = 1
    eligible_bundles = session.query(SupportBundleUpload).filter(
        or_(
            and_(
                SupportBundleUpload.status == "validated",
                SupportBundleUpload.validated_at < current - timedelta(days=accepted_days),
            ),
            and_(
                SupportBundleUpload.status.in_(("rejected", "queued")),
                SupportBundleUpload.updated_at < current - timedelta(days=quarantine_days),
            ),
            and_(
                SupportBundleUpload.status.in_(("issued", "uploading")),
                SupportBundleUpload.expires_at
                < current - timedelta(days=incomplete_grace_days),
            ),
        )
    )
    access_cutoff = current - timedelta(days=access_days)
    bundles = {
        "accepted_retention_days": accepted_days,
        "quarantine_retention_days": quarantine_days,
        "incomplete_grace_days": incomplete_grace_days,
        "access_audit_retention_days": access_days,
        "uploads": int(session.query(func.count(SupportBundleUpload.id)).scalar() or 0),
        "retention_holds": int(
            session.query(func.count(SupportBundleUpload.id))
            .filter(SupportBundleUpload.retention_hold.is_(True))
            .scalar()
            or 0
        ),
        "access_audits": int(session.query(func.count(SupportBundleAccessAudit.id)).scalar() or 0),
        "expired_unheld_backlog": int(
            eligible_bundles.filter(SupportBundleUpload.retention_hold.is_(False)).count()
        ),
        "expired_held": int(
            eligible_bundles.filter(SupportBundleUpload.retention_hold.is_(True)).count()
        ),
        "access_audit_unheld_backlog": int(
            session.query(func.count(SupportBundleAccessAudit.id))
            .filter(
                SupportBundleAccessAudit.created_at < access_cutoff,
                SupportBundleAccessAudit.retention_hold.is_(False),
            )
            .scalar()
            or 0
        ),
        "access_audit_held": int(
            session.query(func.count(SupportBundleAccessAudit.id))
            .filter(
                SupportBundleAccessAudit.created_at < access_cutoff,
                SupportBundleAccessAudit.retention_hold.is_(True),
            )
            .scalar()
            or 0
        ),
    }
    return {
        "raw_policy": {
            "default_days": 90,
            "longer_lived_data": "only purpose-bound payment, security, release and access-audit records",
            "cleanup_authority": "worker.run_telemetry_retention_once",
            "mode": "delete_or_bounded_hmac_anonymization",
        },
        "retention": retention,
        "deletion_anonymization": antiabuse_retention_status(session, now=current),
        "diagnostic_bundles": bundles,
        "field_inventory": [
            {"family": "operator_identity", "fields": ["operator_id", "display_name", "legacy_actor_tg_id", "identity_source"], "classification": "restricted"},
            {"family": "operator_session", "fields": ["session_id", "environment", "timestamps", "step_up_at", "revoke_reason"], "classification": "restricted", "excluded": ["token", "token_hash", "csrf"]},
            {"family": "operator_audit", "fields": ["role_permission_snapshot", "action", "result", "reason", "resource", "command_intent_id", "trace_id", "timestamp"], "classification": "audit"},
            {"family": "diagnostic_bundle", "fields": ["upload_id", "ticket_id", "profile", "version", "error_code", "expiry", "retention_hold"], "classification": "sensitive", "excluded": ["bundle_content", "access_token_hash", "owner_binding_hash"]},
            {"family": "telemetry", "fields": ["event_id", "occurred_at", "version", "stage", "result", "error_code", "trace", "allowlisted_metadata"], "classification": "raw_90_day"},
        ],
        "generated_at": _iso(current),
    }


__all__ = [
    "audit_explorer",
    "audit_export_csv",
    "command_lineage",
    "list_operators",
    "operator_detail",
    "privacy_retention_status",
    "role_catalog",
    "role_is_active",
    "role_payload",
    "sensitive_access_log",
]
