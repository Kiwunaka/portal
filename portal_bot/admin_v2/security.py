"""Persistent operator sessions and deny-by-default permission checks."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from sqlalchemy import or_

from .roles import PERMISSIONS, ROLE_REGISTRY, permissions_for_roles


ADMIN_SESSION_COOKIE = "__Host-pokrov_admin_session"
ADMIN_CSRF_HEADER = "X-Pokrov-Admin-CSRF"
_ENVIRONMENT_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _bounded_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(str(os.getenv(name) or default))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(value, maximum))


def _env_bool(name: str, default: bool) -> bool:
    raw = str(os.getenv(name) or ("true" if default else "false")).strip().lower()
    return raw in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class OperatorSessionConfig:
    secret: str
    environment: str
    idle_ttl_seconds: int
    absolute_ttl_seconds: int
    step_up_ttl_seconds: int
    max_active_sessions: int
    trusted_origins: frozenset[str]
    legacy_bootstrap_enabled: bool = True

    @classmethod
    def from_env(cls) -> "OperatorSessionConfig":
        environment = str(
            os.getenv("ADMIN_OPERATOR_ENVIRONMENT")
            or os.getenv("POKROV_ENVIRONMENT")
            or "local"
        ).strip().lower()
        origins = {
            value.strip().rstrip("/")
            for value in str(
                os.getenv("ADMIN_OPERATOR_TRUSTED_ORIGINS")
                or "https://admin.pokrov.space,https://www.admin.pokrov.space,http://localhost:3105,http://127.0.0.1:3105"
            ).split(",")
            if value.strip()
        }
        idle = _bounded_int("ADMIN_OPERATOR_SESSION_IDLE_SECONDS", 1800, 300, 86400)
        absolute = _bounded_int("ADMIN_OPERATOR_SESSION_ABSOLUTE_SECONDS", 43200, 900, 604800)
        return cls(
            secret=str(os.getenv("ADMIN_OPERATOR_SESSION_SECRET") or "").strip(),
            environment=environment,
            idle_ttl_seconds=min(idle, absolute),
            absolute_ttl_seconds=absolute,
            step_up_ttl_seconds=_bounded_int("ADMIN_OPERATOR_STEP_UP_SECONDS", 600, 60, 3600),
            max_active_sessions=_bounded_int("ADMIN_OPERATOR_MAX_ACTIVE_SESSIONS", 10, 1, 50),
            trusted_origins=frozenset(origins),
            legacy_bootstrap_enabled=_env_bool("ADMIN_OPERATOR_LEGACY_BOOTSTRAP_ENABLED", True),
        )

    def validate(self) -> None:
        if len(self.secret.encode("utf-8")) < 32:
            raise AdminV2Error(
                status_code=503,
                code="operator_session_not_configured",
                message="Operator session secret is not configured.",
            )
        if not _ENVIRONMENT_RE.fullmatch(self.environment):
            raise AdminV2Error(
                status_code=503,
                code="operator_environment_invalid",
                message="Operator environment scope is invalid.",
            )


class AdminV2Error(Exception):
    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = int(status_code)
        self.code = str(code)
        self.message = str(message)


@dataclass(frozen=True)
class OperatorContext:
    operator_id: str
    actor_tg_id: int
    display_name: str | None
    session_id: str
    environment: str
    roles: tuple[str, ...]
    permissions: frozenset[str]
    created_at: datetime
    idle_expires_at: datetime
    absolute_expires_at: datetime
    step_up_at: datetime | None
    csrf_token: str

    def has(self, permission: str) -> bool:
        return permission in self.permissions


@dataclass(frozen=True)
class IssuedOperatorSession:
    token: str
    context: OperatorContext


SessionFactory = Callable[[], Any]


def _models():
    try:
        from ..models import AdminOperator, AdminOperatorAudit, AdminOperatorRole, AdminOperatorSession
    except ImportError:
        from models import AdminOperator, AdminOperatorAudit, AdminOperatorRole, AdminOperatorSession
    return AdminOperator, AdminOperatorAudit, AdminOperatorRole, AdminOperatorSession


def _digest(config: OperatorSessionConfig, purpose: str, value: str) -> str:
    return hmac.new(
        config.secret.encode("utf-8"),
        f"{purpose}:{value}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def csrf_token_for(config: OperatorSessionConfig, token: str) -> str:
    config.validate()
    return _digest(config, "csrf-v1", token)


def _token_hash(config: OperatorSessionConfig, token: str) -> str:
    config.validate()
    return _digest(config, "session-v1", token)


def _active_roles(db, *, operator_id: str, environment: str) -> tuple[str, ...]:
    _, _, AdminOperatorRole, _ = _models()
    now = _utcnow()
    rows = (
        db.query(AdminOperatorRole)
        .filter(
            AdminOperatorRole.operator_id == operator_id,
            AdminOperatorRole.environment_scope == environment,
            AdminOperatorRole.revoked_at.is_(None),
            or_(AdminOperatorRole.expires_at.is_(None), AdminOperatorRole.expires_at > now),
        )
        .order_by(AdminOperatorRole.role_code.asc())
        .all()
    )
    role_codes = tuple(sorted({str(row.role_code) for row in rows if str(row.role_code) in ROLE_REGISTRY}))
    return role_codes


def _context_from_rows(
    *,
    config: OperatorSessionConfig,
    operator,
    session_row,
    roles: tuple[str, ...],
    token: str,
) -> OperatorContext:
    return OperatorContext(
        operator_id=str(operator.id),
        actor_tg_id=int(operator.legacy_actor_tg_id or 0),
        display_name=str(operator.display_name or "").strip() or None,
        session_id=str(session_row.id),
        environment=str(session_row.environment_scope),
        roles=roles,
        permissions=permissions_for_roles(roles),
        created_at=session_row.created_at,
        idle_expires_at=session_row.idle_expires_at,
        absolute_expires_at=session_row.absolute_expires_at,
        step_up_at=session_row.step_up_at,
        csrf_token=csrf_token_for(config, token),
    )


def _ensure_bootstrap_operator(db, *, actor: dict[str, Any], config: OperatorSessionConfig):
    AdminOperator, _, AdminOperatorRole, _ = _models()
    actor_id = int(actor.get("actor_tg_id") or actor.get("id") or 0)
    if actor_id <= 0:
        raise AdminV2Error(status_code=403, code="operator_identity_invalid", message="Operator identity is invalid.")
    operator = db.query(AdminOperator).filter(AdminOperator.legacy_actor_tg_id == actor_id).first()
    now = _utcnow()
    if operator is None:
        operator = AdminOperator(
            id=str(uuid.uuid4()),
            legacy_actor_tg_id=actor_id,
            display_name=str(actor.get("username") or "").strip() or f"operator-{actor_id}",
            identity_source="legacy_bootstrap",
            status="active",
            created_at=now,
            updated_at=now,
        )
        db.add(operator)
        db.flush()
        db.add(
            AdminOperatorRole(
                id=str(uuid.uuid4()),
                operator_id=str(operator.id),
                role_code="superadmin",
                environment_scope=config.environment,
                granted_at=now,
            )
        )
        db.flush()
    if str(operator.status) != "active":
        raise AdminV2Error(status_code=403, code="operator_suspended", message="Operator access is suspended.")
    roles = _active_roles(db, operator_id=str(operator.id), environment=config.environment)
    if not roles:
        raise AdminV2Error(status_code=403, code="operator_role_missing", message="No active role for this environment.")
    return operator, roles


def issue_operator_session(
    session_factory: SessionFactory,
    *,
    actor: dict[str, Any],
    config: OperatorSessionConfig,
    trace_id: str | None = None,
) -> IssuedOperatorSession:
    config.validate()
    db = session_factory()
    try:
        operator, roles = _ensure_bootstrap_operator(db, actor=actor, config=config)
        issued = _issue_session_for_operator(
            db,
            config=config,
            operator=operator,
            roles=roles,
            trace_id=trace_id,
            audit_action="session.bootstrap",
            audit_reason="legacy_admin_verified",
        )
        db.commit()
        return issued
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def issue_operator_oidc_session(
    session_factory: SessionFactory,
    *,
    actor_tg_id: int,
    display_name: str | None,
    config: OperatorSessionConfig,
    trace_id: str | None = None,
) -> IssuedOperatorSession:
    """Issue a session only for an already provisioned Telegram-linked operator."""
    config.validate()
    AdminOperator, _, _, _ = _models()
    external_id = int(actor_tg_id or 0)
    if external_id <= 0:
        raise AdminV2Error(status_code=403, code="operator_identity_invalid", message="Operator identity is invalid.")
    db = session_factory()
    try:
        operator = db.query(AdminOperator).filter(AdminOperator.legacy_actor_tg_id == external_id).first()
        if operator is None:
            raise AdminV2Error(
                status_code=403,
                code="operator_not_provisioned",
                message="Operator identity is not provisioned.",
            )
        if str(operator.status) != "active":
            raise AdminV2Error(status_code=403, code="operator_suspended", message="Operator access is suspended.")
        roles = _active_roles(db, operator_id=str(operator.id), environment=config.environment)
        if not roles:
            raise AdminV2Error(status_code=403, code="operator_role_missing", message="No active role for this environment.")
        if str(operator.identity_source) not in {"legacy_bootstrap", "telegram_oidc"}:
            raise AdminV2Error(
                status_code=403,
                code="operator_identity_source_mismatch",
                message="Operator identity source does not match.",
            )
        operator.identity_source = "telegram_oidc"
        if not str(operator.display_name or "").strip() and str(display_name or "").strip():
            operator.display_name = str(display_name).strip()[:120]
        operator.updated_at = _utcnow()
        issued = _issue_session_for_operator(
            db,
            config=config,
            operator=operator,
            roles=roles,
            trace_id=trace_id,
            audit_action="session.oidc",
            audit_reason="telegram_oidc_verified",
        )
        db.commit()
        return issued
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _issue_session_for_operator(
    db,
    *,
    config: OperatorSessionConfig,
    operator,
    roles: tuple[str, ...],
    trace_id: str | None,
    audit_action: str,
    audit_reason: str,
) -> IssuedOperatorSession:
    _, _, _, AdminOperatorSession = _models()
    now = _utcnow()
    active_rows = (
        db.query(AdminOperatorSession)
        .filter(
            AdminOperatorSession.operator_id == str(operator.id),
            AdminOperatorSession.environment_scope == config.environment,
            AdminOperatorSession.revoked_at.is_(None),
        )
        .order_by(AdminOperatorSession.created_at.desc())
        .all()
    )
    for stale in active_rows[max(0, config.max_active_sessions - 1) :]:
        stale.revoked_at = now
        stale.revoke_reason = "active_session_limit"
    token = secrets.token_urlsafe(48)
    absolute_expires_at = now + timedelta(seconds=config.absolute_ttl_seconds)
    session_row = AdminOperatorSession(
        id=str(uuid.uuid4()),
        operator_id=str(operator.id),
        token_hash=_token_hash(config, token),
        environment_scope=config.environment,
        created_at=now,
        last_seen_at=now,
        idle_expires_at=min(now + timedelta(seconds=config.idle_ttl_seconds), absolute_expires_at),
        absolute_expires_at=absolute_expires_at,
        step_up_at=None,
    )
    db.add(session_row)
    db.flush()
    context = _context_from_rows(
        config=config,
        operator=operator,
        session_row=session_row,
        roles=roles,
        token=token,
    )
    _add_audit_row(
        db,
        context=context,
        action=audit_action,
        result="success",
        reason_code=audit_reason,
        trace_id=trace_id,
    )
    return IssuedOperatorSession(token=token, context=context)


def validate_operator_origin(request, config: OperatorSessionConfig) -> None:
    origin = str(request.headers.get("origin") or "").strip().rstrip("/")
    if origin and origin not in config.trusted_origins:
        raise AdminV2Error(status_code=403, code="operator_origin_forbidden", message="Operator origin is not trusted.")


def authenticate_operator_request(
    session_factory: SessionFactory,
    *,
    request,
    config: OperatorSessionConfig,
    require_csrf: bool | None = None,
) -> OperatorContext:
    config.validate()
    token = str(request.cookies.get(ADMIN_SESSION_COOKIE) or "").strip()
    if not token:
        raise AdminV2Error(status_code=401, code="operator_session_missing", message="Operator session is required.")
    AdminOperator, _, _, AdminOperatorSession = _models()
    db = session_factory()
    try:
        session_row = (
            db.query(AdminOperatorSession)
            .filter(AdminOperatorSession.token_hash == _token_hash(config, token))
            .first()
        )
        now = _utcnow()
        if session_row is None or str(session_row.environment_scope) != config.environment:
            raise AdminV2Error(status_code=401, code="operator_session_invalid", message="Operator session is invalid.")
        if session_row.revoked_at is not None:
            raise AdminV2Error(status_code=401, code="operator_session_revoked", message="Operator session was revoked.")
        if session_row.idle_expires_at <= now or session_row.absolute_expires_at <= now:
            session_row.revoked_at = now
            session_row.revoke_reason = (
                "absolute_expired"
                if session_row.absolute_expires_at <= session_row.idle_expires_at
                else "idle_expired"
            )
            db.commit()
            raise AdminV2Error(status_code=401, code="operator_session_expired", message="Operator session expired.")
        operator = db.query(AdminOperator).filter(AdminOperator.id == str(session_row.operator_id)).first()
        if operator is None or str(operator.status) != "active":
            raise AdminV2Error(status_code=403, code="operator_inactive", message="Operator is not active.")
        roles = _active_roles(db, operator_id=str(operator.id), environment=config.environment)
        permissions = permissions_for_roles(roles)
        if not roles or not permissions:
            raise AdminV2Error(status_code=403, code="operator_permission_missing", message="Operator has no active permission.")
        csrf_required = (
            str(request.method or "GET").upper() not in _SAFE_METHODS
            if require_csrf is None
            else bool(require_csrf)
        )
        if csrf_required:
            validate_operator_origin(request, config)
            supplied = str(request.headers.get(ADMIN_CSRF_HEADER) or "").strip()
            expected = csrf_token_for(config, token)
            if not supplied or not hmac.compare_digest(supplied, expected):
                raise AdminV2Error(status_code=403, code="operator_csrf_invalid", message="Operator CSRF token is invalid.")
        new_idle = min(now + timedelta(seconds=config.idle_ttl_seconds), session_row.absolute_expires_at)
        session_row.last_seen_at = now
        session_row.idle_expires_at = new_idle
        db.commit()
        return _context_from_rows(
            config=config,
            operator=operator,
            session_row=session_row,
            roles=roles,
            token=token,
        )
    except AdminV2Error:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def require_permission(
    context: OperatorContext,
    permission: str,
    *,
    config: OperatorSessionConfig,
    step_up: bool = False,
) -> None:
    if permission not in PERMISSIONS or permission not in context.permissions:
        raise AdminV2Error(status_code=403, code="operator_permission_denied", message="Permission is denied.")
    if step_up:
        cutoff = _utcnow() - timedelta(seconds=config.step_up_ttl_seconds)
        if context.step_up_at is None or context.step_up_at < cutoff:
            raise AdminV2Error(status_code=403, code="operator_step_up_required", message="Fresh step-up is required.")


def _add_audit_row(
    db,
    *,
    context: OperatorContext,
    action: str,
    result: str,
    reason_code: str | None,
    trace_id: str | None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    command_intent_id: str | None = None,
    legacy_audit_id: int | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    _, AdminOperatorAudit, _, _ = _models()
    db.add(
        AdminOperatorAudit(
            id=str(uuid.uuid4()),
            operator_id=context.operator_id,
            session_id=context.session_id,
            action=str(action)[:96],
            result=str(result)[:24],
            reason_code=str(reason_code or "")[:96] or None,
            environment_scope=context.environment,
            roles_json=json.dumps(list(context.roles), ensure_ascii=False, separators=(",", ":")),
            permissions_json=json.dumps(sorted(context.permissions), ensure_ascii=False, separators=(",", ":")),
            trace_id=str(trace_id or "")[:128] or None,
            resource_type=str(resource_type or "")[:32] or None,
            resource_id=str(resource_id or "")[:128] or None,
            command_intent_id=str(command_intent_id or "")[:36] or None,
            legacy_audit_id=int(legacy_audit_id) if legacy_audit_id is not None else None,
            details_json=(
                json.dumps(details, ensure_ascii=False, sort_keys=True, separators=(",", ":"))[:4000]
                if details
                else None
            ),
            created_at=_utcnow(),
        )
    )


def add_operator_command_audit(
    db,
    *,
    context: OperatorContext,
    action: str,
    meta: dict[str, Any],
    legacy_audit_id: int,
) -> None:
    """Attach an authenticated operator/session snapshot to the canonical command audit."""
    _add_audit_row(
        db,
        context=context,
        action=action,
        result=str(meta.get("outcome") or "completed")[:24],
        reason_code=str(meta.get("reason") or meta.get("grant_reason") or "")[:96] or None,
        trace_id=None,
        resource_type=str(meta.get("target_type") or "")[:32] or None,
        resource_id=str(meta.get("target_id") or "")[:128] or None,
        command_intent_id=str(meta.get("action_intent_id") or "")[:36] or None,
        legacy_audit_id=legacy_audit_id,
        details={
            key: value
            for key, value in meta.items()
            if key
            in {
                "action_intent_id",
                "risk_level",
                "target_type",
                "target_id",
                "payload_hash",
                "snapshot_hash",
                "entity_version_hash",
                "outcome",
                "environment",
                "role_code",
                "grant_kind",
                "expires_at",
                "reason",
                "grant_reason",
                "review_status",
            }
        },
    )


def add_operator_read_audit(
    db,
    *,
    context: OperatorContext,
    action: str,
    trace_id: str | None,
    resource_type: str,
    resource_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Record access to governance exports or restricted read models."""
    _add_audit_row(
        db,
        context=context,
        action=action,
        result="success",
        reason_code="governance_read",
        trace_id=trace_id,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )


def list_operator_sessions(
    session_factory: SessionFactory,
    *,
    context: OperatorContext,
    limit: int = 50,
) -> list[dict[str, Any]]:
    _, _, _, AdminOperatorSession = _models()
    db = session_factory()
    try:
        rows = (
            db.query(AdminOperatorSession)
            .filter(
                AdminOperatorSession.operator_id == context.operator_id,
                AdminOperatorSession.environment_scope == context.environment,
            )
            .order_by(AdminOperatorSession.created_at.desc())
            .limit(max(1, min(int(limit), 50)))
            .all()
        )
        return [
            {
                "id": str(row.id),
                "current": str(row.id) == context.session_id,
                "created_at": row.created_at,
                "last_seen_at": row.last_seen_at,
                "idle_expires_at": row.idle_expires_at,
                "absolute_expires_at": row.absolute_expires_at,
                "step_up_at": row.step_up_at,
                "revoked_at": row.revoked_at,
                "revoke_reason": str(row.revoke_reason or "") or None,
            }
            for row in rows
        ]
    finally:
        db.close()


def revoke_operator_session(
    session_factory: SessionFactory,
    *,
    context: OperatorContext,
    session_id: str,
    reason: str,
    trace_id: str | None,
) -> bool:
    _, _, _, AdminOperatorSession = _models()
    db = session_factory()
    try:
        row = (
            db.query(AdminOperatorSession)
            .filter(
                AdminOperatorSession.id == str(session_id),
                AdminOperatorSession.operator_id == context.operator_id,
                AdminOperatorSession.environment_scope == context.environment,
            )
            .first()
        )
        if row is None:
            raise AdminV2Error(status_code=404, code="operator_session_not_found", message="Operator session was not found.")
        if row.revoked_at is None:
            row.revoked_at = _utcnow()
            row.revoke_reason = str(reason or "operator_revoke")[:96]
        _add_audit_row(
            db,
            context=context,
            action="session.revoke",
            result="success",
            reason_code=row.revoke_reason,
            trace_id=trace_id,
        )
        db.commit()
        return str(row.id) == context.session_id
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def mark_operator_step_up(
    session_factory: SessionFactory,
    *,
    context: OperatorContext,
    trace_id: str | None,
    method: str = "legacy_admin_reverified",
) -> datetime:
    _, _, _, AdminOperatorSession = _models()
    db = session_factory()
    try:
        row = db.query(AdminOperatorSession).filter(AdminOperatorSession.id == context.session_id).first()
        if row is None or row.revoked_at is not None:
            raise AdminV2Error(status_code=401, code="operator_session_invalid", message="Operator session is invalid.")
        now = _utcnow()
        row.step_up_at = now
        stepped_context = OperatorContext(**{**context.__dict__, "step_up_at": now})
        _add_audit_row(
            db,
            context=stepped_context,
            action="session.step_up",
            result="success",
            reason_code=str(method or "")[:96] or "step_up_verified",
            trace_id=trace_id,
        )
        db.commit()
        return now
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def legacy_actor_from_context(context: OperatorContext) -> dict[str, Any]:
    return {
        "id": context.actor_tg_id,
        "account_id": context.actor_tg_id,
        "actor_tg_id": context.actor_tg_id,
        "username": context.display_name,
        "auth_type": "admin_operator_session",
        "auth_origin": "operator_center_v2",
        "operator_id": context.operator_id,
        "operator_session_id": context.session_id,
        "operator_roles": list(context.roles),
        "operator_permissions": sorted(context.permissions),
    }
