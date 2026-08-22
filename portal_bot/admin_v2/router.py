"""FastAPI installation boundary for Operator Center v2."""

from __future__ import annotations

import hmac
import os
import inspect
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit, urlunsplit

from fastapi import Depends, Header, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from .contracts import (
    AdminV2ContractRouter,
    COMMON_ERROR_RESPONSES,
    admin_v2_operation_id,
)
from .meta import ADMIN_V2_SCHEMA, build_admin_v2_meta_response
from .security import (
    ADMIN_CSRF_HEADER,
    ADMIN_SESSION_COOKIE,
    AdminV2Error,
    OperatorContext,
    OperatorSessionConfig,
    SessionFactory,
    add_operator_command_audit,
    add_operator_read_audit,
    authenticate_operator_request,
    issue_operator_oidc_session,
    issue_operator_session,
    legacy_actor_from_context,
    list_operator_sessions,
    mark_operator_step_up,
    require_permission,
    revoke_operator_session,
    validate_operator_origin,
)

try:
    from ..web_auth_service import (
        TELEGRAM_OAUTH_STATE_TTL_SECONDS,
        build_telegram_oidc_authorize_url,
        exchange_telegram_oidc_code,
        verify_telegram_oidc_state_token,
    )
except ImportError:
    from web_auth_service import (
        TELEGRAM_OAUTH_STATE_TTL_SECONDS,
        build_telegram_oidc_authorize_url,
        exchange_telegram_oidc_code,
        verify_telegram_oidc_state_token,
    )

try:
    from ..admin_action_intent_service import (
        ActionIntentError,
        execute_action_intent,
        get_action_intent_status,
        prepare_action_intent,
    )
    from ..operator_work_service import (
        add_admin_audit,
        build_shift_read_model,
        incident_detail,
        list_incidents,
        list_tasks,
    )
    from ..operator_network_service import (
        build_network_fleet,
        build_provider_read_model,
        build_traffic_read_model,
        list_network_alerts,
        node_360,
    )
    from ..operator_money_service import (
        access_overview,
        bonus_configuration,
        free_archive,
        payment_360,
        payment_orders,
        payment_summary,
        program_applications,
        promo_rows,
    )
    from ..operator_release_actions import RELEASE_ACTIONS
    from ..operator_governance_actions import GOVERNANCE_ACTIONS
    from ..operator_governance_service import (
        audit_explorer,
        audit_export_csv,
        command_lineage,
        list_operators,
        operator_detail,
        privacy_retention_status,
        role_catalog,
        sensitive_access_log,
    )
    from ..operator_release_service import (
        OperatorReleaseError,
        candidate_cockpit,
        release_candidates,
        version_adoption,
    )
    from ..release_evidence_service import ReleaseEvidenceNotFound, ReleaseEvidenceReadError
    from ..operator_growth_service import (
        OperatorGrowthError,
        broadcast_delivery,
        live_updates,
        news_drafts,
    )
    from ..emergency_catalog_admin_service import build_emergency_catalog_admin_status
    from ..ru_probe_service import (
        RuProbeConfigurationError,
        RuProbeReadModelError,
        get_latest_ru_status,
        get_ru_run_history,
        get_ru_uploader_status,
    )
    from .. import operator_observability_service as operator_observability
    from .. import support_mode_service
    from ..support_work_service import (
        SUPPORT_MACROS,
        attempt_explorer,
        list_support_tickets,
        search_support_cases,
        support_bundle_upload_id_for_ref,
        support_ticket_detail,
        user_360,
    )
except ImportError:
    from admin_action_intent_service import (
        ActionIntentError,
        execute_action_intent,
        get_action_intent_status,
        prepare_action_intent,
    )
    from operator_work_service import (
        add_admin_audit,
        build_shift_read_model,
        incident_detail,
        list_incidents,
        list_tasks,
    )
    from operator_network_service import (
        build_network_fleet,
        build_provider_read_model,
        build_traffic_read_model,
        list_network_alerts,
        node_360,
    )
    from operator_money_service import (
        access_overview,
        bonus_configuration,
        free_archive,
        payment_360,
        payment_orders,
        payment_summary,
        program_applications,
        promo_rows,
    )
    from operator_release_actions import RELEASE_ACTIONS
    from operator_governance_actions import GOVERNANCE_ACTIONS
    from operator_governance_service import (
        audit_explorer,
        audit_export_csv,
        command_lineage,
        list_operators,
        operator_detail,
        privacy_retention_status,
        role_catalog,
        sensitive_access_log,
    )
    from operator_release_service import (
        OperatorReleaseError,
        candidate_cockpit,
        release_candidates,
        version_adoption,
    )
    from release_evidence_service import ReleaseEvidenceNotFound, ReleaseEvidenceReadError
    from operator_growth_service import (
        OperatorGrowthError,
        broadcast_delivery,
        live_updates,
        news_drafts,
    )
    from emergency_catalog_admin_service import build_emergency_catalog_admin_status
    from ru_probe_service import (
        RuProbeConfigurationError,
        RuProbeReadModelError,
        get_latest_ru_status,
        get_ru_run_history,
        get_ru_uploader_status,
    )
    import operator_observability_service as operator_observability
    import support_mode_service
    from support_work_service import (
        SUPPORT_MACROS,
        attempt_explorer,
        list_support_tickets,
        search_support_cases,
        support_bundle_upload_id_for_ref,
        support_ticket_detail,
        user_360,
    )


LegacyAdminResolver = Callable[..., dict[str, Any]]
ADMIN_OIDC_TRANSACTION_COOKIE = "__Host-pokrov_admin_oidc"
ADMIN_OIDC_LOGIN_PURPOSE = "admin_operator_login"
ADMIN_OIDC_STEP_UP_PURPOSE = "admin_operator_step_up"


class OperatorActionTarget(BaseModel):
    type: str = Field(min_length=1, max_length=32)
    id: str = Field(min_length=1, max_length=128)


class OperatorActionCommand(BaseModel):
    action: str = Field(min_length=1, max_length=64)
    target: OperatorActionTarget
    payload: dict[str, Any] = Field(default_factory=dict)


class SupportBundleGrantCommand(BaseModel):
    reason_code: str = Field(pattern=r"^(customer_case|incident_review|release_validation|security_review)$")


class OperatorOidcFinishCommand(BaseModel):
    code: str = Field(min_length=4, max_length=4096)
    state: str = Field(min_length=16, max_length=4096)


def _operator_oidc_redirect_uri() -> str:
    raw = str(
        os.getenv("ADMIN_OPERATOR_OIDC_REDIRECT_URI")
        or "https://admin.pokrov.space/"
    ).strip()
    parsed = urlsplit(raw)
    if parsed.scheme != "https" or not parsed.netloc:
        raise AdminV2Error(
            status_code=503,
            code="operator_oidc_not_configured",
            message="Operator OIDC redirect is not configured.",
        )
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", "", ""))


SHIFT_ACTIONS = frozenset({"operator_task.create", "operator_task.update"})
INCIDENT_ACTIONS = frozenset(
    {
        "incident.create",
        "incident.update",
        "incident.link",
        "incident.compensate",
        "alert.ack",
        "alert.create_incident",
        "alert.link_incident",
        "alert.false_positive",
    }
)
SUPPORT_ACTIONS = frozenset(
    {"ticket.claim", "ticket.assign", "ticket.update", "support.mode.issue"}
)
NETWORK_ACTIONS = frozenset(
    {
        "provider_quota.create",
        "provider_quota.update",
        "provider_quota.delete",
        "node.sync_global",
        "node.drain",
        "node.undrain",
        "node.enable",
        "node.disable",
        "node.resync",
        "emergency_catalog.stage",
        "emergency_catalog.promote",
        "emergency_catalog.disable",
        "emergency_catalog.rollback",
        "alert.silence",
    }
)
MONEY_ACTIONS = frozenset(
    {
        "payment.reconcile",
        "user.extend",
        "access_key.issue",
        "gift_code.create",
        "promo.create",
        "promo.update",
        "promo.delete",
        "promo_slots.update",
    }
)
GROWTH_ACCESS_ACTIONS = frozenset(
    {
        "program_application.review",
        "user.loyalty_grant",
        "wheel_config.update",
        "loyalty_config.update",
        "broadcast.send",
        "live_update.create",
        "live_update.update",
        "live_update.delete",
        "referral.process",
    }
)
CONTEXT_BOUND_ACTIONS = (
    SHIFT_ACTIONS
    | INCIDENT_ACTIONS
    | SUPPORT_ACTIONS
    | RELEASE_ACTIONS
    | GOVERNANCE_ACTIONS
    | frozenset({"alert.silence", "program_application.review"})
)
HIGH_RISK_ACTIONS = frozenset(
    {
        "incident.compensate",
        "provider_quota.delete",
        "node.sync_global",
        "node.disable",
        "emergency_catalog.promote",
        "emergency_catalog.disable",
        "emergency_catalog.rollback",
        "user.extend",
        "access_key.issue",
        "gift_code.create",
        "promo.delete",
        "program_application.review",
        "user.loyalty_grant",
        "broadcast.send",
        "release.rollout.start",
        "release.rollout.change",
        "release.rollout.rollback",
        "release.min_supported.set",
        "operator.role.grant",
        "operator.role.revoke",
        "operator.suspend",
        "operator.activate",
        "operator.session.revoke",
    }
)

ROUTE_PERMISSIONS = {
    "GET /auth/oidc/start": "session.bootstrap",
    "POST /auth/oidc/finish": "session.bootstrap",
    "POST /auth/bootstrap": "session.bootstrap",
    "GET /auth/me": "session.self.read",
    "GET /auth/sessions": "session.self.read",
    "POST /auth/sessions/{session_id}/revoke": "session.self.revoke",
    "POST /auth/step-up": "session.step_up",
    "POST /auth/logout": "session.self.revoke",
    "GET /meta": "system.meta.read",
    "GET /shift": "shift.read",
    "GET /shift/overview": "shift.read",
    "GET /tasks": "shift.read",
    "POST /shift/action-intents": "shift.manage",
    "POST /shift/action-intents/{intent_id}/execute": "shift.manage",
    "GET /incidents": "incident.read",
    "GET /incidents/{incident_id}": "incident.read",
    "POST /incidents/action-intents": "incident.manage",
    "POST /incidents/action-intents/{intent_id}/execute": "incident.manage",
    "GET /support/tickets": "support.read",
    "GET /support/tickets/{ticket_id}": "support.read",
    "GET /support/macros": "support.read",
    "GET /support/users/{tg_id}": "support.read",
    "GET /support/attempts": "support.sensitive.read",
    "GET /support/search": "support.read",
    "GET /support/known-issues": "support.read",
    "GET /support/diagnostic-codes/{code}": "support.read",
    "POST /support/tickets/{ticket_id}/bundles/{bundle_ref}/access-grants": "support.sensitive.read",
    "GET /support/tickets/{ticket_id}/bundles/{bundle_ref}/content": "support.sensitive.read",
    "GET /support/online": "support.read",
    "POST /support/action-intents": "support.write",
    "POST /support/action-intents/{intent_id}/execute": "support.write",
    "GET /network/fleet": "network.read",
    "GET /network/nodes/{node_code}": "network.read",
    "GET /network/traffic": "network.read",
    "GET /network/alerts": "network.read",
    "GET /network/providers": "network.read",
    "GET /network/ru/latest": "network.read",
    "GET /network/ru/runs": "network.read",
    "GET /network/ru/uploader": "network.read",
    "GET /network/emergency": "network.read",
    "POST /network/action-intents": "network.write",
    "POST /network/action-intents/{intent_id}/execute": "network.write",
    "GET /money/payments/summary": "money.read",
    "GET /money/payments/orders": "money.read",
    "GET /money/payments/orders/{provider}/{order_id}": "money.read",
    "GET /money/access": "money.read",
    "GET /money/free-archive": "money.read",
    "GET /money/promos": "money.read",
    "POST /money/action-intents": "money.write",
    "POST /money/action-intents/{intent_id}/execute": "money.write",
    "GET /growth/bonuses": "growth.read",
    "GET /growth/programs": "growth.read",
    "GET /growth/funnel": "growth.read",
    "GET /growth/referrals": "growth.read",
    "GET /growth/broadcasts/{intent_id}/delivery": "growth.read",
    "GET /growth/news-drafts": "growth.read",
    "GET /growth/live-updates": "growth.read",
    "GET /growth/action-intents/{intent_id}": "growth.read",
    "POST /growth/action-intents": "growth.write",
    "POST /growth/action-intents/{intent_id}/execute": "growth.write",
    "GET /releases/candidates": "releases.read",
    "GET /releases/candidates/{candidate_id}/cockpit": "releases.read",
    "GET /releases/adoption": "releases.read",
    "POST /releases/action-intents": "releases.write",
    "POST /releases/action-intents/{intent_id}/execute": "releases.write",
    "GET /governance/roles": "governance.operators.read",
    "GET /governance/operators": "governance.operators.read",
    "GET /governance/operators/{operator_id}": "governance.operators.read",
    "GET /governance/audit": "governance.audit.read",
    "GET /governance/audit/export": "governance.audit.read",
    "GET /governance/audit/commands/{intent_id}": "governance.audit.read",
    "GET /governance/sensitive-access": "governance.audit.read",
    "GET /governance/privacy": "governance.sources.read",
    "POST /governance/action-intents": "governance.operators.manage",
    "POST /governance/action-intents/{intent_id}/execute": "governance.operators.manage",
}


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _read_datetime(value: str | None, *, field: str) -> datetime | None:
    normalized = str(value or "").strip()
    if not normalized:
        return None
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except (ValueError, OverflowError) as error:
        raise AdminV2Error(
            status_code=400,
            code="operator_invalid_time_range",
            message=f"Field {field} is not a valid timestamp.",
        ) from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return parsed
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def _trace_id(request: Request) -> str | None:
    correlation = getattr(request.state, "request_correlation", None)
    return str(
        getattr(correlation, "correlation_id", "")
        or getattr(request.state, "correlation_id", "")
        or ""
    ).strip() or None


def _meta(request: Request) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "trace_id": _trace_id(request),
        "schema_version": ADMIN_V2_SCHEMA,
        "query_ms": 0,
    }


def _envelope(
    request: Request,
    *,
    data: Any,
    sources: list[dict[str, Any]] | None = None,
    warnings: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "data": data,
        "meta": _meta(request),
        "sources": list(sources or []),
        "warnings": list(warnings or []),
    }


def _operator_payload(context: OperatorContext) -> dict[str, Any]:
    return {
        "id": context.operator_id,
        "legacy_actor_tg_id": context.actor_tg_id,
        "display_name": context.display_name,
        "environment": context.environment,
        "roles": list(context.roles),
        "permissions": sorted(context.permissions),
    }


def _session_payload(context: OperatorContext) -> dict[str, Any]:
    return {
        "id": context.session_id,
        "created_at": _iso(context.created_at),
        "idle_expires_at": _iso(context.idle_expires_at),
        "absolute_expires_at": _iso(context.absolute_expires_at),
        "step_up_at": _iso(context.step_up_at),
        "csrf_token": context.csrf_token,
    }


def _http_error_to_admin_v2(error: HTTPException) -> AdminV2Error:
    detail = error.detail
    if isinstance(detail, dict):
        code = str(detail.get("code") or "legacy_admin_rejected")
        message = str(detail.get("message") or detail.get("detail") or "Legacy administrator verification failed.")
    else:
        code = "legacy_admin_rejected"
        message = str(detail or "Legacy administrator verification failed.")
    return AdminV2Error(status_code=int(error.status_code), code=code[:96], message=message[:240])


def _action_error_to_admin_v2(error: ActionIntentError) -> AdminV2Error:
    return AdminV2Error(
        status_code=int(error.status_code),
        code=str(error.code)[:96],
        message=str(error.message)[:240],
    )


def _release_error_to_admin_v2(error: Exception) -> AdminV2Error:
    if isinstance(error, OperatorReleaseError):
        return AdminV2Error(
            status_code=int(error.status_code),
            code=str(error.code)[:96],
            message=str(error.message)[:240],
        )
    if isinstance(error, ReleaseEvidenceNotFound):
        return AdminV2Error(
            status_code=404,
            code=str(error)[:96] or "release_candidate_not_found",
            message="Release candidate was not found.",
        )
    return AdminV2Error(
        status_code=400,
        code=str(error)[:96] or "release_evidence_invalid",
        message="Release evidence request is invalid.",
    )


def _growth_error_to_admin_v2(error: OperatorGrowthError) -> AdminV2Error:
    return AdminV2Error(
        status_code=int(error.status_code),
        code=str(error.code)[:96],
        message=str(error.message)[:240],
    )


def _observability_error_to_admin_v2(
    error: operator_observability.OperatorObservabilityError,
) -> AdminV2Error:
    return AdminV2Error(
        status_code=int(error.status_code),
        code=str(error.code)[:96],
        message="Support evidence request was rejected.",
    )


async def admin_v2_error_handler(request: Request, error: AdminV2Error) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "data": None,
            "meta": _meta(request),
            "sources": [],
            "warnings": [],
            "error": {"code": error.code, "message": error.message},
        },
        headers={"Cache-Control": "no-store"},
    )


@dataclass(frozen=True)
class AdminV2Runtime:
    session_factory: SessionFactory
    config: OperatorSessionConfig

    def authenticate_legacy_bridge(self, request: Request) -> dict[str, Any] | None:
        if not str(request.cookies.get(ADMIN_SESSION_COOKIE) or "").strip():
            return None
        context = authenticate_operator_request(
            self.session_factory,
            request=request,
            config=self.config,
        )
        route = (getattr(request, "scope", None) or {}).get("route")
        route_path = str(getattr(route, "path", "") or "")
        method = str(getattr(request, "method", "GET") or "GET").upper()
        permission_rule = {
            ("GET", "/api/admin/users"): ("all", ("support.read",)),
            ("GET", "/api/admin/users/{tg_id}"): ("all", ("support.read",)),
            ("GET", "/api/admin/users/{tg_id}/investigation"): (
                "all",
                ("support.sensitive.read",),
            ),
            ("GET", "/api/admin/search"): (
                "any",
                ("support.read", "network.read", "money.read"),
            ),
            ("GET", "/api/admin/promo-slots"): ("all", ("money.read",)),
            ("POST", "/api/admin/promo-media"): ("all", ("money.write",)),
        }.get((method, route_path), ("all", ("legacy.admin.access",)))
        mode, permissions = permission_rule
        if mode == "any":
            if not any(context.has(permission) for permission in permissions):
                raise AdminV2Error(
                    status_code=403,
                    code="operator_permission_denied",
                    message="Permission is denied.",
                )
        else:
            for permission in permissions:
                require_permission(context, permission, config=self.config)
        return legacy_actor_from_context(context)


def install_admin_v2(
    app,
    *,
    session_factory: SessionFactory,
    legacy_admin_resolver: LegacyAdminResolver,
    legacy_db_executor: Callable[..., dict[str, Any]] | None = None,
    legacy_external_executor: Callable[[dict[str, Any]], Any] | None = None,
    legacy_post_commit_executor: Callable[[dict[str, Any]], Any] | None = None,
    legacy_read_executor: Callable[[dict[str, Any]], Any] | None = None,
) -> AdminV2Runtime:
    config = OperatorSessionConfig.from_env()
    runtime = AdminV2Runtime(session_factory=session_factory, config=config)
    router = AdminV2ContractRouter(
        prefix="/api/admin/v2",
        tags=["admin-v2"],
        responses=COMMON_ERROR_RESPONSES,
        generate_unique_id_function=admin_v2_operation_id,
    )

    def authenticated(request: Request) -> OperatorContext:
        return authenticate_operator_request(
            session_factory,
            request=request,
            config=config,
        )

    def permitted(permission: str, *, step_up: bool = False):
        def dependency(context: OperatorContext = Depends(authenticated)) -> OperatorContext:
            require_permission(context, permission, config=config, step_up=step_up)
            return context

        return dependency

    def legacy_permitted(permission: str):
        def dependency(
            request: Request,
            x_telegram_init_data: str = Header(default=""),
        ) -> dict[str, Any]:
            if permission != "session.bootstrap":
                raise AdminV2Error(
                    status_code=403,
                    code="operator_permission_denied",
                    message="Permission is denied.",
                )
            if not config.legacy_bootstrap_enabled:
                raise AdminV2Error(
                    status_code=403,
                    code="operator_legacy_bootstrap_disabled",
                    message="Compatibility bootstrap is disabled.",
                )
            validate_operator_origin(request, config)
            try:
                return legacy_admin_resolver(x_telegram_init_data, request=request)
            except HTTPException as error:
                raise _http_error_to_admin_v2(error) from error

        return dependency

    def set_operator_session_cookie(response: Response, *, token: str) -> None:
        response.set_cookie(
            key=ADMIN_SESSION_COOKIE,
            value=token,
            max_age=config.absolute_ttl_seconds,
            secure=True,
            httponly=True,
            samesite="strict",
            path="/",
        )

    def set_oidc_transaction_cookie(response: Response, *, state: str) -> None:
        response.set_cookie(
            key=ADMIN_OIDC_TRANSACTION_COOKIE,
            value=state,
            max_age=TELEGRAM_OAUTH_STATE_TTL_SECONDS,
            secure=True,
            httponly=True,
            samesite="strict",
            path="/",
        )

    async def exchange_operator_oidc(
        *,
        request: Request,
        payload: OperatorOidcFinishCommand,
        purpose: str,
    ) -> dict[str, Any]:
        validate_operator_origin(request, config)
        transaction = str(request.cookies.get(ADMIN_OIDC_TRANSACTION_COOKIE) or "").strip()
        if not transaction:
            raise AdminV2Error(
                status_code=403,
                code="operator_oidc_transaction_invalid",
                message="Operator OIDC transaction is invalid or expired.",
            )
        public_state = verify_telegram_oidc_state_token(
            payload.state,
            expected_purpose=purpose,
            require_code_verifier=False,
            signing_secret=config.secret,
        )
        private_state = verify_telegram_oidc_state_token(
            transaction,
            expected_purpose=purpose,
            signing_secret=config.secret,
        )
        if not public_state or not private_state:
            raise AdminV2Error(
                status_code=403,
                code="operator_oidc_state_invalid",
                message="Operator OIDC state is invalid or expired.",
            )
        for field in ("csrf", "redirect_uri", "purpose"):
            if not hmac.compare_digest(
                str(public_state.get(field) or ""),
                str(private_state.get(field) or ""),
            ):
                raise AdminV2Error(
                    status_code=403,
                    code="operator_oidc_transaction_mismatch",
                    message="Operator OIDC transaction does not match state.",
                )
        try:
            return await exchange_telegram_oidc_code(
                code=payload.code,
                state_token=payload.state,
                expected_purpose=purpose,
                transaction_token=transaction,
                state_signing_secret=config.secret,
            )
        except ValueError as error:
            raise AdminV2Error(
                status_code=403,
                code="operator_oidc_identity_invalid",
                message="Operator OIDC identity could not be verified.",
            ) from error
        except RuntimeError as error:
            raise AdminV2Error(
                status_code=503,
                code="operator_oidc_unavailable",
                message="Operator OIDC is temporarily unavailable.",
            ) from error

    def operator_payload(command: OperatorActionCommand, context: OperatorContext) -> dict[str, Any]:
        payload = dict(command.payload)
        if str(command.action or "").strip().lower() in CONTEXT_BOUND_ACTIONS:
            payload.update(
                {
                    "_environment": context.environment,
                    "_operator_id": context.operator_id,
                    "_actor_tg_id": context.actor_tg_id,
                }
            )
        return payload

    def require_production_commerce(context: OperatorContext) -> None:
        if str(context.environment or "").strip().lower() != "production":
            raise AdminV2Error(
                status_code=409,
                code="money_environment_unavailable",
                message="Money and growth access records are unavailable in this environment.",
            )

    async def read_legacy_projection(
        *,
        kind: str,
        context: OperatorContext,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        if legacy_read_executor is None:
            raise AdminV2Error(
                status_code=503,
                code="operator_projection_unavailable",
                message="The authoritative projection is unavailable.",
            )
        try:
            result = legacy_read_executor(
                {
                    "kind": kind,
                    "environment": context.environment,
                    "params": dict(params),
                }
            )
            if inspect.isawaitable(result):
                result = await result
        except AdminV2Error:
            raise
        except Exception as error:
            raise AdminV2Error(
                status_code=503,
                code="operator_projection_unavailable",
                message="The authoritative projection is unavailable.",
            ) from error
        if not isinstance(result, dict):
            raise AdminV2Error(
                status_code=503,
                code="operator_projection_invalid",
                message="The authoritative projection returned an invalid response.",
            )
        return result

    def authorize_action(
        context: OperatorContext,
        *,
        action: str,
        allowed: frozenset[str],
        permission: str,
    ) -> str:
        normalized = str(action or "").strip().lower()
        if normalized not in allowed:
            raise AdminV2Error(
                status_code=403,
                code="operator_action_not_allowed",
                message="Action is not available through this operator workspace.",
            )
        require_permission(context, permission, config=config)
        if normalized in HIGH_RISK_ACTIONS:
            require_permission(context, "command.high_risk", config=config, step_up=True)
        return normalized

    def prepare_operator_action(
        *,
        command: OperatorActionCommand,
        context: OperatorContext,
        allowed: frozenset[str],
        permission: str,
    ) -> dict[str, Any]:
        action = authorize_action(
            context,
            action=command.action,
            allowed=allowed,
            permission=permission,
        )
        db = session_factory()
        try:
            result = prepare_action_intent(
                session=db,
                actor_tg_id=context.actor_tg_id,
                action=action,
                target={"type": command.target.type, "id": command.target.id},
                payload=operator_payload(command, context),
            )
            db.commit()
            return result
        except ActionIntentError as error:
            db.rollback()
            raise _action_error_to_admin_v2(error) from error
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    async def execute_operator_action(
        *,
        intent_id: str,
        command: OperatorActionCommand,
        context: OperatorContext,
        allowed: frozenset[str],
        permission: str,
        idempotency_key: str,
        confirmation_sha256: str,
    ) -> dict[str, Any]:
        action = authorize_action(
            context,
            action=command.action,
            allowed=allowed,
            permission=permission,
        )

        def write_authenticated_operator_audit(**kwargs):
            audit = add_admin_audit(**kwargs)
            add_operator_command_audit(
                kwargs["session"],
                context=context,
                action=str(kwargs.get("action") or action),
                meta=dict(kwargs.get("meta") or {}),
                legacy_audit_id=int(audit.id),
            )
            return audit

        try:
            return await execute_action_intent(
                session_factory=session_factory,
                actor_tg_id=context.actor_tg_id,
                intent_id=intent_id,
                idempotency_key=idempotency_key,
                confirmation_sha256_header=confirmation_sha256,
                action=action,
                target={"type": command.target.type, "id": command.target.id},
                payload=operator_payload(command, context),
                audit_writer=write_authenticated_operator_audit,
                db_executor=(
                    lambda session, state, payload, runtime_payload: legacy_db_executor(
                        session,
                        state,
                        payload,
                        runtime_payload,
                        actor_tg_id=context.actor_tg_id,
                        action=action,
                    )
                    if legacy_db_executor is not None
                    else None
                ),
                external_executor=legacy_external_executor,
                post_commit_executor=legacy_post_commit_executor,
            )
        except ActionIntentError as error:
            raise _action_error_to_admin_v2(error) from error

    @router.get("/auth/oidc/start")
    def oidc_start(
        request: Request,
        response: Response,
        mode: str = Query(default="login", pattern=r"^(login|step_up)$"),
    ) -> dict[str, Any]:
        validate_operator_origin(request, config)
        purpose = ADMIN_OIDC_STEP_UP_PURPOSE if mode == "step_up" else ADMIN_OIDC_LOGIN_PURPOSE
        try:
            oidc = build_telegram_oidc_authorize_url(
                redirect_uri=_operator_oidc_redirect_uri(),
                purpose=purpose,
                cookie_bound=True,
                state_signing_secret=config.secret,
            )
        except (RuntimeError, ValueError) as error:
            raise AdminV2Error(
                status_code=503,
                code="operator_oidc_unavailable",
                message="Operator OIDC is temporarily unavailable.",
            ) from error
        set_oidc_transaction_cookie(response, state=oidc["transaction"])
        response.headers["Cache-Control"] = "no-store"
        return _envelope(
            request,
            data={
                "mode": mode,
                "provider": "telegram_oidc",
                "auth_url": oidc["auth_url"],
                "redirect_uri": oidc["redirect_uri"],
            },
        )

    @router.post("/auth/oidc/finish")
    async def oidc_finish(
        payload: OperatorOidcFinishCommand,
        request: Request,
        response: Response,
    ) -> dict[str, Any]:
        verified = await exchange_operator_oidc(
            request=request,
            payload=payload,
            purpose=ADMIN_OIDC_LOGIN_PURPOSE,
        )
        issued = issue_operator_oidc_session(
            session_factory,
            actor_tg_id=int(verified.get("id") or 0),
            display_name=str(
                verified.get("preferred_username")
                or verified.get("name")
                or ""
            ).strip() or None,
            config=config,
            trace_id=_trace_id(request),
        )
        set_operator_session_cookie(response, token=issued.token)
        response.delete_cookie(
            key=ADMIN_OIDC_TRANSACTION_COOKIE,
            path="/",
            secure=True,
            httponly=True,
            samesite="strict",
        )
        response.headers["Cache-Control"] = "no-store"
        return _envelope(
            request,
            data={
                "operator": _operator_payload(issued.context),
                "session": _session_payload(issued.context),
                "token_transport": "http_only_cookie",
                "identity_method": "telegram_oidc",
            },
        )

    @router.post("/auth/bootstrap")
    def bootstrap(
        request: Request,
        response: Response,
        actor: dict[str, Any] = Depends(
            legacy_permitted(ROUTE_PERMISSIONS["POST /auth/bootstrap"])
        ),
    ) -> dict[str, Any]:
        issued = issue_operator_session(
            session_factory,
            actor=actor,
            config=config,
            trace_id=_trace_id(request),
        )
        set_operator_session_cookie(response, token=issued.token)
        response.headers["Cache-Control"] = "no-store"
        return _envelope(
            request,
            data={
                "operator": _operator_payload(issued.context),
                "session": _session_payload(issued.context),
                "token_transport": "http_only_cookie",
            },
            warnings=[
                {
                    "code": "compatibility_bootstrap",
                    "message": "Legacy administrator identity was exchanged; external IdP proof is not claimed.",
                }
            ],
        )

    @router.get("/auth/me")
    def me(
        request: Request,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /auth/me"])
        ),
    ) -> dict[str, Any]:
        return _envelope(
            request,
            data={
                "operator": _operator_payload(context),
                "session": _session_payload(context),
            },
        )

    @router.get("/auth/sessions")
    def sessions(
        request: Request,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /auth/sessions"])
        ),
    ) -> dict[str, Any]:
        rows = list_operator_sessions(session_factory, context=context)
        for row in rows:
            for field in (
                "created_at",
                "last_seen_at",
                "idle_expires_at",
                "absolute_expires_at",
                "step_up_at",
                "revoked_at",
            ):
                row[field] = _iso(row[field])
        return _envelope(request, data={"items": rows, "count": len(rows)})

    @router.post("/auth/sessions/{session_id}/revoke")
    def revoke_session(
        session_id: str,
        request: Request,
        response: Response,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["POST /auth/sessions/{session_id}/revoke"])
        ),
    ) -> dict[str, Any]:
        current = revoke_operator_session(
            session_factory,
            context=context,
            session_id=session_id,
            reason="operator_revoke",
            trace_id=_trace_id(request),
        )
        if current:
            response.delete_cookie(
                key=ADMIN_SESSION_COOKIE,
                path="/",
                secure=True,
                httponly=True,
                samesite="strict",
            )
        response.headers["Cache-Control"] = "no-store"
        return _envelope(request, data={"session_id": session_id, "revoked": True, "current": current})

    @router.post("/auth/step-up")
    async def step_up(
        request: Request,
        response: Response,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["POST /auth/step-up"])
        ),
        payload: OperatorOidcFinishCommand | None = None,
        x_telegram_init_data: str = Header(default=""),
    ) -> dict[str, Any]:
        if payload is not None:
            verified = await exchange_operator_oidc(
                request=request,
                payload=payload,
                purpose=ADMIN_OIDC_STEP_UP_PURPOSE,
            )
            if int(verified.get("id") or 0) != context.actor_tg_id:
                raise AdminV2Error(
                    status_code=403,
                    code="operator_step_up_identity_mismatch",
                    message="Step-up identity does not match the operator session.",
                )
            step_up_at = mark_operator_step_up(
                session_factory,
                context=context,
                trace_id=_trace_id(request),
                method="telegram_oidc_verified",
            )
            response.delete_cookie(
                key=ADMIN_OIDC_TRANSACTION_COOKIE,
                path="/",
                secure=True,
                httponly=True,
                samesite="strict",
            )
            response.headers["Cache-Control"] = "no-store"
            return _envelope(
                request,
                data={
                    "step_up_at": _iso(step_up_at),
                    "valid_for_seconds": config.step_up_ttl_seconds,
                    "method": "telegram_oidc",
                },
            )
        if not config.legacy_bootstrap_enabled:
            raise AdminV2Error(
                status_code=403,
                code="operator_legacy_step_up_disabled",
                message="Compatibility step-up is disabled.",
            )
        try:
            legacy_actor = legacy_admin_resolver(x_telegram_init_data, request=request)
        except HTTPException as error:
            raise _http_error_to_admin_v2(error) from error
        legacy_actor_id = int(legacy_actor.get("actor_tg_id") or legacy_actor.get("id") or 0)
        if legacy_actor_id != context.actor_tg_id:
            raise AdminV2Error(
                status_code=403,
                code="operator_step_up_identity_mismatch",
                message="Step-up identity does not match the operator session.",
            )
        step_up_at = mark_operator_step_up(
            session_factory,
            context=context,
            trace_id=_trace_id(request),
        )
        return _envelope(
            request,
            data={
                "step_up_at": _iso(step_up_at),
                "valid_for_seconds": config.step_up_ttl_seconds,
                "method": "legacy_admin_reverified",
            },
            warnings=[
                {
                    "code": "compatibility_step_up",
                    "message": "External IdP/passkey assurance remains unproved.",
                }
            ],
        )

    @router.post("/auth/logout")
    def logout(
        request: Request,
        response: Response,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["POST /auth/logout"])
        ),
    ) -> dict[str, Any]:
        revoke_operator_session(
            session_factory,
            context=context,
            session_id=context.session_id,
            reason="operator_logout",
            trace_id=_trace_id(request),
        )
        response.delete_cookie(
            key=ADMIN_SESSION_COOKIE,
            path="/",
            secure=True,
            httponly=True,
            samesite="strict",
        )
        response.headers["Clear-Site-Data"] = '"cookies", "storage"'
        response.headers["Cache-Control"] = "no-store"
        return _envelope(request, data={"logged_out": True})

    @router.get("/shift")
    def shift(
        request: Request,
        limit: int = Query(default=100, ge=1, le=200),
        context: OperatorContext = Depends(permitted(ROUTE_PERMISSIONS["GET /shift"])),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            data = build_shift_read_model(
                db,
                environment=context.environment,
                operator_id=context.operator_id,
                actor_tg_id=context.actor_tg_id,
                teams=context.roles,
                limit=limit,
            )
            return _envelope(request, data=data)
        finally:
            db.close()

    @router.get("/shift/overview")
    async def shift_overview(
        request: Request,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /shift/overview"])
        ),
    ) -> dict[str, Any]:
        if str(context.environment or "").strip().lower() != "production":
            raise AdminV2Error(
                status_code=409,
                code="shift_overview_environment_unavailable",
                message="The production overview is unavailable in this environment.",
            )
        data = await read_legacy_projection(
            kind="shift.overview",
            context=context,
            params={},
        )
        return _envelope(
            request,
            data=data,
            sources=[
                {
                    "authority": "ops_metrics_capacity_and_alert_read_models",
                    "mode": "compatibility_projection",
                }
            ],
        )

    @router.get("/tasks")
    def tasks(
        request: Request,
        limit: int = Query(default=200, ge=1, le=500),
        context: OperatorContext = Depends(permitted(ROUTE_PERMISSIONS["GET /tasks"])),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            items = list_tasks(db, environment=context.environment, limit=limit)
            return _envelope(request, data={"items": items, "count": len(items)})
        finally:
            db.close()

    @router.post("/shift/action-intents")
    def prepare_shift_action(
        command: OperatorActionCommand,
        request: Request,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["POST /shift/action-intents"])
        ),
    ) -> dict[str, Any]:
        result = prepare_operator_action(
            command=command,
            context=context,
            allowed=SHIFT_ACTIONS,
            permission="shift.manage",
        )
        return _envelope(request, data=result)

    @router.post("/shift/action-intents/{intent_id}/execute")
    async def execute_shift_action(
        intent_id: str,
        command: OperatorActionCommand,
        request: Request,
        idempotency_key: str = Header(default="", alias="X-Admin-Idempotency-Key"),
        confirmation_sha256: str = Header(default="", alias="X-Admin-Confirmation-SHA256"),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["POST /shift/action-intents/{intent_id}/execute"])
        ),
    ) -> dict[str, Any]:
        result = await execute_operator_action(
            intent_id=intent_id,
            command=command,
            context=context,
            allowed=SHIFT_ACTIONS,
            permission="shift.manage",
            idempotency_key=idempotency_key,
            confirmation_sha256=confirmation_sha256,
        )
        return _envelope(request, data=result)

    @router.get("/incidents")
    def incidents(
        request: Request,
        limit: int = Query(default=100, ge=1, le=300),
        context: OperatorContext = Depends(permitted(ROUTE_PERMISSIONS["GET /incidents"])),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            items = list_incidents(db, environment=context.environment, limit=limit)
            return _envelope(request, data={"items": items, "count": len(items)})
        finally:
            db.close()

    @router.get("/incidents/{incident_id}")
    def incident(
        incident_id: str,
        request: Request,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /incidents/{incident_id}"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            data = incident_detail(
                db,
                environment=context.environment,
                incident_id=incident_id,
            )
            if data is None:
                raise AdminV2Error(
                    status_code=404,
                    code="incident_not_found",
                    message="Incident was not found in this environment.",
                )
            return _envelope(request, data=data)
        finally:
            db.close()

    @router.post("/incidents/action-intents")
    def prepare_incident_action(
        command: OperatorActionCommand,
        request: Request,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["POST /incidents/action-intents"])
        ),
    ) -> dict[str, Any]:
        result = prepare_operator_action(
            command=command,
            context=context,
            allowed=INCIDENT_ACTIONS,
            permission="incident.manage",
        )
        return _envelope(request, data=result)

    @router.post("/incidents/action-intents/{intent_id}/execute")
    async def execute_incident_action(
        intent_id: str,
        command: OperatorActionCommand,
        request: Request,
        idempotency_key: str = Header(default="", alias="X-Admin-Idempotency-Key"),
        confirmation_sha256: str = Header(default="", alias="X-Admin-Confirmation-SHA256"),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["POST /incidents/action-intents/{intent_id}/execute"])
        ),
    ) -> dict[str, Any]:
        result = await execute_operator_action(
            intent_id=intent_id,
            command=command,
            context=context,
            allowed=INCIDENT_ACTIONS,
            permission="incident.manage",
            idempotency_key=idempotency_key,
            confirmation_sha256=confirmation_sha256,
        )
        return _envelope(request, data=result)

    @router.get("/support/tickets")
    def support_tickets(
        request: Request,
        status: str | None = Query(default="active", max_length=20),
        priority: str | None = Query(default=None, max_length=16),
        queue: str | None = Query(default=None, max_length=48),
        assignment: str | None = Query(default=None, max_length=24),
        limit: int = Query(default=100, ge=1, le=300),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /support/tickets"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            items = list_support_tickets(
                db,
                environment=context.environment,
                status=status,
                priority=priority,
                queue=queue,
                assignment=assignment,
                actor_tg_id=context.actor_tg_id,
                limit=limit,
            )
            return _envelope(request, data={"items": items, "count": len(items)})
        finally:
            db.close()

    @router.get("/support/tickets/{ticket_id}")
    def support_ticket(
        ticket_id: int,
        request: Request,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /support/tickets/{ticket_id}"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            data = support_ticket_detail(
                db, environment=context.environment, ticket_id=int(ticket_id)
            )
            if data is None:
                raise AdminV2Error(
                    status_code=404,
                    code="ticket_not_found",
                    message="Ticket was not found in this environment.",
                )
            return _envelope(request, data=data)
        finally:
            db.close()

    @router.get("/support/macros")
    def support_macros(
        request: Request,
        _context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /support/macros"])
        ),
    ) -> dict[str, Any]:
        return _envelope(request, data={"items": [dict(row) for row in SUPPORT_MACROS]})

    @router.get("/support/users/{tg_id}")
    def support_user_360(
        tg_id: int,
        request: Request,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /support/users/{tg_id}"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            include_sensitive_diagnostics = context.has("support.sensitive.read")
            data = user_360(
                db,
                environment=context.environment,
                tg_id=int(tg_id),
                include_sensitive_diagnostics=include_sensitive_diagnostics,
            )
            if data is None:
                raise AdminV2Error(
                    status_code=404,
                    code="user_not_found",
                    message="User was not found.",
                )
            warnings = []
            if not include_sensitive_diagnostics:
                warnings.append(
                    {
                        "code": "field_redacted",
                        "message": "Support diagnostics require support.sensitive.read.",
                    }
                )
            return _envelope(request, data=data, warnings=warnings)
        finally:
            db.close()

    @router.get("/support/attempts")
    def support_attempts(
        request: Request,
        ticket_id: int | None = Query(default=None, ge=1),
        tg_id: int | None = Query(default=None),
        attempt_ref: str | None = Query(default=None, max_length=64),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /support/attempts"])
        ),
    ) -> dict[str, Any]:
        if ticket_id is None and tg_id is None:
            raise AdminV2Error(
                status_code=422,
                code="attempt_scope_required",
                message="ticket_id or tg_id is required.",
            )
        db = session_factory()
        try:
            data = attempt_explorer(
                db,
                environment=context.environment,
                ticket_id=ticket_id,
                tg_id=tg_id,
                attempt_ref=attempt_ref,
            )
            if data is None:
                raise AdminV2Error(
                    status_code=404,
                    code="attempt_scope_not_found",
                    message="Attempt scope was not found.",
                )
            return _envelope(request, data=data)
        finally:
            db.close()

    @router.get("/support/search")
    def support_search(
        request: Request,
        q: str = Query(min_length=2, max_length=128),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /support/search"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            try:
                results = search_support_cases(
                    db,
                    environment=context.environment,
                    query=q,
                    limit=12,
                )
            except ValueError as error:
                raise AdminV2Error(
                    status_code=400,
                    code=str(error)[:96],
                    message="Support search query is invalid.",
                ) from error
            return _envelope(request, data={"results": results})
        finally:
            db.close()

    @router.get("/support/known-issues")
    def support_known_issues(
        request: Request,
        error_code: str | None = Query(default=None, max_length=32),
        app_version: str | None = Query(default=None, max_length=64),
        build_number: str | None = Query(default=None, max_length=80),
        platform: str | None = Query(default=None, max_length=16),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /support/known-issues"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            try:
                issues = operator_observability.known_issues(
                    db,
                    status="open",
                    error_code=error_code,
                    app_version=app_version,
                    build_number=build_number,
                    platform=platform,
                    limit=20,
                )
            except operator_observability.OperatorObservabilityError as error:
                raise _observability_error_to_admin_v2(error) from error
            return _envelope(
                request,
                data={"issues": issues, "count": len(issues)},
                sources=[
                    {
                        "authority": "release_known_issues",
                        "mode": "version_scoped_read_model",
                    }
                ],
            )
        finally:
            db.close()

    @router.post("/support/tickets/{ticket_id}/bundles/{bundle_ref}/access-grants")
    def issue_support_bundle_grant(
        ticket_id: int,
        bundle_ref: str,
        command: SupportBundleGrantCommand,
        request: Request,
        context: OperatorContext = Depends(
            permitted(
                ROUTE_PERMISSIONS[
                    "POST /support/tickets/{ticket_id}/bundles/{bundle_ref}/access-grants"
                ],
                step_up=True,
            )
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            upload_id = support_bundle_upload_id_for_ref(
                db,
                environment=context.environment,
                ticket_id=int(ticket_id),
                bundle_ref=bundle_ref,
            )
            if upload_id is None:
                raise AdminV2Error(
                    status_code=404,
                    code="support_bundle_not_found",
                    message="Support bundle was not found in this ticket.",
                )
            try:
                grant = operator_observability.issue_bundle_access_grant(
                    db,
                    upload_id=upload_id,
                    actor_tg_id=context.actor_tg_id,
                    privileged_ids={context.actor_tg_id},
                    reason_code=command.reason_code,
                    actor_role=next(
                        (
                            role
                            for role in (
                                "security_auditor",
                                "sre",
                                "support_l2",
                                "superadmin",
                            )
                            if role in context.roles
                        ),
                        "l2_sre",
                    ),
                )
                db.commit()
            except operator_observability.OperatorObservabilityError as error:
                db.rollback()
                raise _observability_error_to_admin_v2(error) from error
            return _envelope(
                request,
                data={
                    "bundle_ref": bundle_ref,
                    "access_grant": grant.token,
                    "expires_at": grant.expires_at.replace(tzinfo=timezone.utc).isoformat(),
                },
            )
        finally:
            db.close()

    @router.get(
        "/support/tickets/{ticket_id}/bundles/{bundle_ref}/content",
        response_model=None,
        responses={
            200: {
                "content": {
                    "application/octet-stream": {
                        "schema": {"type": "string", "format": "binary"}
                    }
                }
            }
        },
    )
    def download_support_bundle(
        ticket_id: int,
        bundle_ref: str,
        request: Request,
        x_pokrov_support_grant: str = Header(
            default="", alias="X-Pokrov-Support-Grant", max_length=128
        ),
        context: OperatorContext = Depends(
            permitted(
                ROUTE_PERMISSIONS[
                    "GET /support/tickets/{ticket_id}/bundles/{bundle_ref}/content"
                ],
                step_up=True,
            )
        ),
    ) -> FileResponse:
        db = session_factory()
        try:
            upload_id = support_bundle_upload_id_for_ref(
                db,
                environment=context.environment,
                ticket_id=int(ticket_id),
                bundle_ref=bundle_ref,
            )
            if upload_id is None:
                raise AdminV2Error(
                    status_code=404,
                    code="support_bundle_not_found",
                    message="Support bundle was not found in this ticket.",
                )
            accepted_root = Path(
                os.getenv("POKROV_SUPPORT_BUNDLE_ACCEPTED_DIR")
                or Path(__file__).resolve().parents[1]
                / "private"
                / "support-bundle-accepted"
            ).resolve()
            try:
                item = operator_observability.consume_bundle_access_grant(
                    db,
                    upload_id=upload_id,
                    token=x_pokrov_support_grant,
                    actor_tg_id=context.actor_tg_id,
                    privileged_ids={context.actor_tg_id},
                    accepted_root=accepted_root,
                )
                db.commit()
            except operator_observability.OperatorObservabilityError as error:
                db.rollback()
                raise _observability_error_to_admin_v2(error) from error
            return FileResponse(
                path=item.path,
                media_type="application/octet-stream",
                filename=f"pokrov-support-{bundle_ref}.bin",
                headers={
                    "Cache-Control": "no-store",
                    "X-Content-Type-Options": "nosniff",
                },
            )
        finally:
            db.close()

    @router.get("/support/online")
    async def support_online(
        request: Request,
        limit: int = Query(default=200, ge=1, le=500),
        only: str = Query(default="", max_length=512),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /support/online"])
        ),
    ) -> dict[str, Any]:
        if str(context.environment or "").strip().lower() != "production":
            raise AdminV2Error(
                status_code=409,
                code="support_online_environment_unavailable",
                message="Live online state is unavailable in this environment.",
            )
        data = await read_legacy_projection(
            kind="support.online",
            context=context,
            params={"limit": int(limit), "only": str(only or "")},
        )
        return _envelope(
            request,
            data=data,
            sources=[
                {
                    "authority": "control_panel_online_and_account_read_model",
                    "mode": "compatibility_projection",
                }
            ],
        )

    @router.get("/support/diagnostic-codes/{code}")
    def decode_support_diagnostic_code(
        code: str,
        request: Request,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /support/diagnostic-codes/{code}"])
        ),
    ) -> dict[str, Any]:
        del context
        try:
            decoded = support_mode_service.decode_diagnostic_code(code)
        except support_mode_service.SupportModeError as error:
            raise AdminV2Error(
                status_code=error.status_code,
                code=error.code,
                message="Короткий код диагностики недействителен.",
            ) from error
        return _envelope(
            request,
            data=decoded,
            sources=[
                {
                    "authority": "versioned_support_diagnostic_code_v1",
                    "mode": "local_decode_without_bundle_upload",
                }
            ],
        )

    @router.post("/support/action-intents")
    def prepare_support_action(
        command: OperatorActionCommand,
        request: Request,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["POST /support/action-intents"])
        ),
    ) -> dict[str, Any]:
        result = prepare_operator_action(
            command=command,
            context=context,
            allowed=SUPPORT_ACTIONS,
            permission="support.write",
        )
        return _envelope(request, data=result)

    @router.post("/support/action-intents/{intent_id}/execute")
    async def execute_support_action(
        intent_id: str,
        command: OperatorActionCommand,
        request: Request,
        idempotency_key: str = Header(default="", alias="X-Admin-Idempotency-Key"),
        confirmation_sha256: str = Header(default="", alias="X-Admin-Confirmation-SHA256"),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["POST /support/action-intents/{intent_id}/execute"])
        ),
    ) -> dict[str, Any]:
        result = await execute_operator_action(
            intent_id=intent_id,
            command=command,
            context=context,
            allowed=SUPPORT_ACTIONS,
            permission="support.write",
            idempotency_key=idempotency_key,
            confirmation_sha256=confirmation_sha256,
        )
        return _envelope(request, data=result)

    @router.get("/network/fleet")
    def network_fleet(
        request: Request,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /network/fleet"])
        ),
    ) -> dict[str, Any]:
        del context
        db = session_factory()
        try:
            data = build_network_fleet(
                db,
                now=_utcnow(),
                metrics_stale_after_seconds=max(
                    300, int(os.getenv("NODE_METRICS_STALE_AFTER_SECONDS", "900"))
                ),
            )
            return _envelope(
                request,
                data=data,
                sources=[
                    {"authority": "nodes", "mode": "database"},
                    {"authority": "node_health_samples", "mode": "database"},
                    {"authority": "node_runtime_metrics", "mode": "database"},
                    {"authority": "ru_probe_runs", "mode": "database"},
                ],
            )
        finally:
            db.close()

    @router.get("/network/nodes/{node_code}")
    def network_node_360(
        node_code: str,
        request: Request,
        include_ru_history: bool = Query(default=False),
        _context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /network/nodes/{node_code}"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            data = node_360(
                db,
                node_code=node_code,
                now=_utcnow(),
                metrics_stale_after_seconds=max(
                    300, int(os.getenv("NODE_METRICS_STALE_AFTER_SECONDS", "900"))
                ),
                include_ru_history=include_ru_history,
            )
            if data is None:
                raise AdminV2Error(
                    status_code=404,
                    code="node_not_found",
                    message="Node was not found.",
                )
            return _envelope(
                request,
                data=data,
                sources=[{"authority": "node_360", "mode": "composed_read_model"}],
            )
        finally:
            db.close()

    @router.get("/network/traffic")
    def network_traffic(
        request: Request,
        from_at: str | None = Query(default=None, alias="from"),
        to_at: str | None = Query(default=None, alias="to"),
        _context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /network/traffic"])
        ),
    ) -> dict[str, Any]:
        now = _utcnow()
        start = _read_datetime(from_at, field="from") or now - timedelta(days=30)
        end = _read_datetime(to_at, field="to") or now
        if start > end or end - start > timedelta(days=120):
            raise AdminV2Error(
                status_code=400,
                code="operator_invalid_time_range",
                message="Traffic range must be ordered and no longer than 120 days.",
            )
        db = session_factory()
        try:
            data = build_traffic_read_model(db, from_dt=start, to_dt=end)
            return _envelope(
                request,
                data=data,
                sources=[{"authority": "key_usage_rollups", "mode": "database"}],
            )
        finally:
            db.close()

    @router.get("/network/alerts")
    def network_alerts(
        request: Request,
        status: str = Query(default="active", max_length=24),
        limit: int = Query(default=300, ge=1, le=500),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /network/alerts"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            data = list_network_alerts(
                db,
                environment=context.environment,
                status=status,
                now=_utcnow(),
                limit=limit,
            )
            return _envelope(
                request,
                data=data,
                sources=[{"authority": "ops_alerts", "mode": "read_only"}],
            )
        finally:
            db.close()

    @router.get("/network/providers")
    def network_providers(
        request: Request,
        _context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /network/providers"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            data = build_provider_read_model(db, now=_utcnow())
            return _envelope(
                request,
                data=data,
                sources=[
                    {"authority": "provider_traffic_quotas", "mode": "database"},
                    {"authority": "node_health_samples", "mode": "counter_delta"},
                ],
            )
        finally:
            db.close()

    @router.get("/network/ru/latest")
    def network_ru_latest(
        request: Request,
        _context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /network/ru/latest"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            try:
                data = get_latest_ru_status(db, now=_utcnow())
            except RuProbeConfigurationError as error:
                raise AdminV2Error(
                    status_code=503,
                    code="ru_configuration_invalid",
                    message="RU-origin configuration is invalid.",
                ) from error
            return _envelope(
                request,
                data=data,
                sources=[{"authority": "ru_probe_runs", "mode": "signed_ingest"}],
            )
        finally:
            db.close()

    @router.get("/network/ru/runs")
    def network_ru_runs(
        request: Request,
        node_code: str | None = Query(default=None, max_length=32),
        from_at: str | None = Query(default=None, alias="from"),
        to_at: str | None = Query(default=None, alias="to"),
        verdict: str | None = Query(default=None, max_length=32),
        limit: int = Query(default=50, ge=1, le=200),
        cursor: str | None = Query(default=None, max_length=512),
        _context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /network/ru/runs"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            try:
                data = get_ru_run_history(
                    db,
                    node_code=node_code,
                    from_at=_read_datetime(from_at, field="from"),
                    to_at=_read_datetime(to_at, field="to"),
                    verdict=verdict,
                    limit=limit,
                    cursor=cursor,
                )
            except RuProbeReadModelError as error:
                raise AdminV2Error(
                    status_code=400,
                    code=str(error.code),
                    message="RU-origin history request is invalid.",
                ) from error
            return _envelope(
                request,
                data=data,
                sources=[{"authority": "ru_probe_runs", "mode": "signed_ingest"}],
            )
        finally:
            db.close()

    @router.get("/network/ru/uploader")
    def network_ru_uploader(
        request: Request,
        _context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /network/ru/uploader"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            return _envelope(
                request,
                data=get_ru_uploader_status(db, now=_utcnow()),
                sources=[{"authority": "ru_probe_uploader_heartbeats", "mode": "signed_ingest"}],
            )
        finally:
            db.close()

    @router.get("/network/emergency")
    def network_emergency(
        request: Request,
        limit: int = Query(default=20, ge=1, le=50),
        _context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /network/emergency"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            return _envelope(
                request,
                data=build_emergency_catalog_admin_status(db, limit=limit),
                sources=[{"authority": "emergency_catalog_snapshots", "mode": "database"}],
            )
        finally:
            db.close()

    @router.post("/network/action-intents")
    def prepare_network_action(
        command: OperatorActionCommand,
        request: Request,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["POST /network/action-intents"])
        ),
    ) -> dict[str, Any]:
        result = prepare_operator_action(
            command=command,
            context=context,
            allowed=NETWORK_ACTIONS,
            permission="network.write",
        )
        return _envelope(request, data=result)

    @router.post("/network/action-intents/{intent_id}/execute")
    async def execute_network_action(
        intent_id: str,
        command: OperatorActionCommand,
        request: Request,
        idempotency_key: str = Header(default="", alias="X-Admin-Idempotency-Key"),
        confirmation_sha256: str = Header(default="", alias="X-Admin-Confirmation-SHA256"),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["POST /network/action-intents/{intent_id}/execute"])
        ),
    ) -> dict[str, Any]:
        result = await execute_operator_action(
            intent_id=intent_id,
            command=command,
            context=context,
            allowed=NETWORK_ACTIONS,
            permission="network.write",
            idempotency_key=idempotency_key,
            confirmation_sha256=confirmation_sha256,
        )
        return _envelope(request, data=result)

    @router.get("/money/payments/summary")
    def money_payment_summary(
        request: Request,
        period: str = Query(default="7d", pattern="^(today|7d|30d)$"),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /money/payments/summary"])
        ),
    ) -> dict[str, Any]:
        require_production_commerce(context)
        db = session_factory()
        try:
            return _envelope(
                request,
                data=payment_summary(
                    db,
                    environment=context.environment,
                    period=period,
                    now=_utcnow(),
                ),
                sources=[
                    {"authority": "external_orders", "mode": "database"},
                    {"authority": "signed_payment_callbacks", "mode": "immutable_events"},
                    {"authority": "account_entitlement_grants", "mode": "database"},
                ],
            )
        finally:
            db.close()

    @router.get("/money/payments/orders")
    def money_payment_orders(
        request: Request,
        status: str = Query(default="", max_length=24),
        provider: str = Query(default="", max_length=32),
        query_text: str = Query(default="", alias="q", max_length=128),
        limit: int = Query(default=100, ge=1, le=250),
        offset: int = Query(default=0, ge=0, le=100_000),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /money/payments/orders"])
        ),
    ) -> dict[str, Any]:
        require_production_commerce(context)
        db = session_factory()
        try:
            return _envelope(
                request,
                data=payment_orders(
                    db,
                    environment=context.environment,
                    status=status,
                    provider=provider,
                    query_text=query_text,
                    limit=limit,
                    offset=offset,
                    now=_utcnow(),
                ),
                sources=[{"authority": "external_orders", "mode": "database"}],
            )
        finally:
            db.close()

    @router.get("/money/payments/orders/{provider}/{order_id}")
    def money_payment_detail(
        provider: str,
        order_id: str,
        request: Request,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /money/payments/orders/{provider}/{order_id}"])
        ),
    ) -> dict[str, Any]:
        require_production_commerce(context)
        db = session_factory()
        try:
            data = payment_360(
                db,
                environment=context.environment,
                provider=provider,
                order_id=order_id,
                now=_utcnow(),
            )
            if data is None:
                raise AdminV2Error(
                    status_code=404,
                    code="payment_order_not_found",
                    message="Payment order was not found.",
                )
            return _envelope(
                request,
                data=data,
                sources=[
                    {"authority": "external_orders", "mode": "database"},
                    {"authority": "signed_payment_callbacks", "mode": "immutable_events"},
                    {"authority": "payment_entitlement_claims", "mode": "lineage"},
                    {"authority": "account_entitlement_grants", "mode": "lineage"},
                    {"authority": "payment_entitlement_outbox", "mode": "delivery_state"},
                ],
            )
        finally:
            db.close()

    @router.get("/money/access")
    def money_access(
        request: Request,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /money/access"])
        ),
    ) -> dict[str, Any]:
        require_production_commerce(context)
        db = session_factory()
        try:
            return _envelope(
                request,
                data=access_overview(db, environment=context.environment, now=_utcnow()),
                sources=[
                    {"authority": "payment_entitlement_claims", "mode": "database"},
                    {"authority": "account_entitlement_grants", "mode": "database"},
                    {"authority": "payment_entitlement_outbox", "mode": "database"},
                    {"authority": "shared_tariff_catalog", "mode": "repository_contract"},
                ],
            )
        finally:
            db.close()

    @router.get("/money/free-archive")
    def money_free_archive(
        request: Request,
        query_text: str = Query(default="", alias="q", max_length=128),
        limit: int = Query(default=500, ge=1, le=1000),
        offset: int = Query(default=0, ge=0, le=100_000),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /money/free-archive"])
        ),
    ) -> dict[str, Any]:
        require_production_commerce(context)
        db = session_factory()
        try:
            return _envelope(
                request,
                data=free_archive(
                    db,
                    environment=context.environment,
                    query_text=query_text,
                    limit=limit,
                    offset=offset,
                    now=_utcnow(),
                ),
                sources=[
                    {"authority": "legacy_user_projection", "mode": "read_only_archive"},
                    {"authority": "shared_access_matrix", "mode": "repository_contract"},
                ],
            )
        finally:
            db.close()

    @router.get("/money/promos")
    def money_promos(
        request: Request,
        limit: int = Query(default=200, ge=1, le=500),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /money/promos"])
        ),
    ) -> dict[str, Any]:
        require_production_commerce(context)
        db = session_factory()
        try:
            return _envelope(
                request,
                data={"promos": promo_rows(db, environment=context.environment, limit=limit)},
                sources=[{"authority": "promo_codes", "mode": "database"}],
            )
        finally:
            db.close()

    @router.post("/money/action-intents")
    def prepare_money_action(
        command: OperatorActionCommand,
        request: Request,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["POST /money/action-intents"])
        ),
    ) -> dict[str, Any]:
        require_production_commerce(context)
        return _envelope(
            request,
            data=prepare_operator_action(
                command=command,
                context=context,
                allowed=MONEY_ACTIONS,
                permission="money.write",
            ),
        )

    @router.post("/money/action-intents/{intent_id}/execute")
    async def execute_money_action(
        intent_id: str,
        command: OperatorActionCommand,
        request: Request,
        idempotency_key: str = Header(default="", alias="X-Admin-Idempotency-Key"),
        confirmation_sha256: str = Header(default="", alias="X-Admin-Confirmation-SHA256"),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["POST /money/action-intents/{intent_id}/execute"])
        ),
    ) -> dict[str, Any]:
        require_production_commerce(context)
        return _envelope(
            request,
            data=await execute_operator_action(
                intent_id=intent_id,
                command=command,
                context=context,
                allowed=MONEY_ACTIONS,
                permission="money.write",
                idempotency_key=idempotency_key,
                confirmation_sha256=confirmation_sha256,
            ),
        )

    @router.get("/growth/funnel")
    async def growth_funnel(
        request: Request,
        from_: str = Query(default="", alias="from", max_length=64),
        to: str = Query(default="", max_length=64),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /growth/funnel"])
        ),
    ) -> dict[str, Any]:
        require_production_commerce(context)
        data = await read_legacy_projection(
            kind="growth.funnel",
            context=context,
            params={"from": from_, "to": to},
        )
        return _envelope(
            request,
            data=data,
            sources=[
                {
                    "authority": "acquisition_commerce_and_event_read_models",
                    "mode": "compatibility_projection",
                }
            ],
        )

    @router.get("/growth/referrals")
    async def growth_referrals(
        request: Request,
        limit: int = Query(default=100, ge=1, le=1000),
        status: str = Query(default="", max_length=48),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /growth/referrals"])
        ),
    ) -> dict[str, Any]:
        require_production_commerce(context)
        data = await read_legacy_projection(
            kind="growth.referrals",
            context=context,
            params={"limit": int(limit), "status": status},
        )
        return _envelope(
            request,
            data=data,
            sources=[
                {
                    "authority": "referral_bonus_queue",
                    "mode": "compatibility_projection",
                }
            ],
        )

    @router.get("/growth/bonuses")
    def growth_bonuses(
        request: Request,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /growth/bonuses"])
        ),
    ) -> dict[str, Any]:
        require_production_commerce(context)
        db = session_factory()
        try:
            return _envelope(
                request,
                data=bonus_configuration(db, environment=context.environment),
                sources=[{"authority": "app_settings", "mode": "allowlisted_configuration"}],
            )
        finally:
            db.close()

    @router.get("/growth/programs")
    def growth_programs(
        request: Request,
        status: str = Query(default="", max_length=24),
        kind: str = Query(default="", max_length=32),
        limit: int = Query(default=200, ge=1, le=300),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /growth/programs"])
        ),
    ) -> dict[str, Any]:
        require_production_commerce(context)
        db = session_factory()
        try:
            try:
                rows = program_applications(
                    db,
                    environment=context.environment,
                    status=status,
                    kind=kind,
                    limit=limit,
                )
            except ValueError as error:
                raise AdminV2Error(
                    status_code=400,
                    code=str(error)[:96],
                    message="Program filter is invalid.",
                ) from error
            return _envelope(
                request,
                data={"applications": rows},
                sources=[{"authority": "program_applications", "mode": "database"}],
            )
        finally:
            db.close()

    @router.get("/growth/broadcasts/{intent_id}/delivery")
    def growth_broadcast_delivery(
        intent_id: str,
        request: Request,
        _context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /growth/broadcasts/{intent_id}/delivery"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            try:
                data = broadcast_delivery(db, intent_id=intent_id)
            except OperatorGrowthError as error:
                raise _growth_error_to_admin_v2(error) from error
            return _envelope(
                request,
                data=data,
                sources=[{"authority": "broadcast_delivery_attempts", "mode": "aggregate"}],
            )
        finally:
            db.close()

    @router.get("/growth/news-drafts")
    def growth_news_drafts(
        request: Request,
        status: str = Query(default="all", max_length=24),
        limit: int = Query(default=100, ge=1, le=200),
        _context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /growth/news-drafts"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            try:
                data = news_drafts(db, status=status, limit=limit)
            except OperatorGrowthError as error:
                raise _growth_error_to_admin_v2(error) from error
            return _envelope(
                request,
                data=data,
                sources=[{"authority": "news_drafts", "mode": "database"}],
            )
        finally:
            db.close()

    @router.get("/growth/live-updates")
    def growth_live_updates(
        request: Request,
        include_inactive: bool = Query(default=True),
        _context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /growth/live-updates"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            return _envelope(
                request,
                data=live_updates(db, include_inactive=include_inactive),
                sources=[{"authority": "live_updates", "mode": "database"}],
            )
        finally:
            db.close()

    @router.get("/growth/action-intents/{intent_id}")
    def growth_action_intent_status(
        intent_id: str,
        request: Request,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /growth/action-intents/{intent_id}"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            try:
                data = get_action_intent_status(
                    session=db,
                    actor_tg_id=context.actor_tg_id,
                    intent_id=intent_id,
                )
            except ActionIntentError as error:
                raise _action_error_to_admin_v2(error) from error
            return _envelope(request, data=data)
        finally:
            db.close()

    @router.post("/growth/action-intents")
    def prepare_growth_access_action(
        command: OperatorActionCommand,
        request: Request,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["POST /growth/action-intents"])
        ),
    ) -> dict[str, Any]:
        require_production_commerce(context)
        return _envelope(
            request,
            data=prepare_operator_action(
                command=command,
                context=context,
                allowed=GROWTH_ACCESS_ACTIONS,
                permission="growth.write",
            ),
        )

    @router.post("/growth/action-intents/{intent_id}/execute")
    async def execute_growth_access_action(
        intent_id: str,
        command: OperatorActionCommand,
        request: Request,
        idempotency_key: str = Header(default="", alias="X-Admin-Idempotency-Key"),
        confirmation_sha256: str = Header(default="", alias="X-Admin-Confirmation-SHA256"),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["POST /growth/action-intents/{intent_id}/execute"])
        ),
    ) -> dict[str, Any]:
        require_production_commerce(context)
        return _envelope(
            request,
            data=await execute_operator_action(
                intent_id=intent_id,
                command=command,
                context=context,
                allowed=GROWTH_ACCESS_ACTIONS,
                permission="growth.write",
                idempotency_key=idempotency_key,
                confirmation_sha256=confirmation_sha256,
            ),
        )

    @router.get("/releases/candidates")
    def releases_candidates(
        request: Request,
        limit: int = Query(default=50, ge=1, le=100),
        cursor: str = Query(default="", max_length=2048),
        _context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /releases/candidates"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            try:
                data = release_candidates(db, limit=limit, cursor=cursor or None)
            except (ReleaseEvidenceReadError, ReleaseEvidenceNotFound, OperatorReleaseError) as error:
                raise _release_error_to_admin_v2(error) from error
            return _envelope(
                request,
                data=data,
                sources=[{"authority": "release_evidence", "mode": "database"}],
            )
        finally:
            db.close()

    @router.get("/releases/candidates/{candidate_id}/cockpit")
    def release_candidate_cockpit(
        candidate_id: str,
        request: Request,
        hours: int = Query(default=24, ge=1, le=168),
        _context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /releases/candidates/{candidate_id}/cockpit"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            try:
                data = candidate_cockpit(db, candidate_id=candidate_id, hours=hours)
            except (ReleaseEvidenceReadError, ReleaseEvidenceNotFound, OperatorReleaseError) as error:
                raise _release_error_to_admin_v2(error) from error
            return _envelope(
                request,
                data=data,
                sources=[
                    {"authority": "release_evidence", "mode": "database"},
                    {"authority": "release_rollout_v1", "mode": "app_setting"},
                    {"authority": "release_health_events", "mode": "aggregate"},
                    {"authority": "account_devices", "mode": "aggregate"},
                ],
            )
        finally:
            db.close()

    @router.get("/releases/adoption")
    def releases_adoption(
        request: Request,
        days: int = Query(default=30, ge=1, le=90),
        _context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /releases/adoption"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            return _envelope(
                request,
                data=version_adoption(db, days=days),
                sources=[{"authority": "account_devices", "mode": "aggregate"}],
            )
        finally:
            db.close()

    @router.post("/releases/action-intents")
    def prepare_release_action(
        command: OperatorActionCommand,
        request: Request,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["POST /releases/action-intents"])
        ),
    ) -> dict[str, Any]:
        return _envelope(
            request,
            data=prepare_operator_action(
                command=command,
                context=context,
                allowed=RELEASE_ACTIONS,
                permission="releases.write",
            ),
        )

    @router.post("/releases/action-intents/{intent_id}/execute")
    async def execute_release_action(
        intent_id: str,
        command: OperatorActionCommand,
        request: Request,
        idempotency_key: str = Header(default="", alias="X-Admin-Idempotency-Key"),
        confirmation_sha256: str = Header(default="", alias="X-Admin-Confirmation-SHA256"),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["POST /releases/action-intents/{intent_id}/execute"])
        ),
    ) -> dict[str, Any]:
        return _envelope(
            request,
            data=await execute_operator_action(
                intent_id=intent_id,
                command=command,
                context=context,
                allowed=RELEASE_ACTIONS,
                permission="releases.write",
                idempotency_key=idempotency_key,
                confirmation_sha256=confirmation_sha256,
            ),
        )

    @router.get("/governance/roles")
    def governance_roles(
        request: Request,
        _context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /governance/roles"])
        ),
    ) -> dict[str, Any]:
        return _envelope(
            request,
            data=role_catalog(),
            sources=[{"authority": "admin_v2.role_registry", "mode": "code"}],
        )

    @router.get("/governance/operators")
    def governance_operators(
        request: Request,
        q: str = Query(default="", max_length=120),
        status: str = Query(default="", max_length=24),
        role: str = Query(default="", max_length=48),
        limit: int = Query(default=100, ge=1, le=200),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /governance/operators"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            return _envelope(
                request,
                data=list_operators(
                    db,
                    environment=context.environment,
                    q=q,
                    status=status,
                    role=role,
                    limit=limit,
                ),
                sources=[{"authority": "admin_operators", "mode": "database"}],
            )
        finally:
            db.close()

    @router.get("/governance/operators/{operator_id}")
    def governance_operator_detail(
        operator_id: str,
        request: Request,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /governance/operators/{operator_id}"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            data = operator_detail(db, operator_id=operator_id, environment=context.environment)
            if data is None:
                raise AdminV2Error(
                    status_code=404,
                    code="operator_not_found",
                    message="Operator was not found.",
                )
            return _envelope(
                request,
                data=data,
                sources=[
                    {"authority": "admin_operators", "mode": "database"},
                    {"authority": "admin_operator_roles", "mode": "database"},
                    {"authority": "admin_operator_sessions", "mode": "database"},
                ],
            )
        finally:
            db.close()

    def read_governance_audit(
        db,
        *,
        context: OperatorContext,
        actor: str,
        role: str,
        permission: str,
        action: str,
        result: str,
        resource_type: str,
        resource_id: str,
        command_intent_id: str,
        since: str,
        until: str,
        limit: int,
    ) -> dict[str, Any]:
        return audit_explorer(
            db,
            environment=context.environment,
            actor=actor,
            role=role,
            permission=permission,
            action=action,
            result=result,
            resource_type=resource_type,
            resource_id=resource_id,
            command_intent_id=command_intent_id,
            since=_read_datetime(since, field="since"),
            until=_read_datetime(until, field="until"),
            limit=limit,
        )

    @router.get("/governance/audit")
    def governance_audit(
        request: Request,
        actor: str = Query(default="", max_length=120),
        role: str = Query(default="", max_length=48),
        permission: str = Query(default="", max_length=96),
        action: str = Query(default="", max_length=96),
        result: str = Query(default="", max_length=24),
        resource_type: str = Query(default="", max_length=32),
        resource_id: str = Query(default="", max_length=128),
        command_intent_id: str = Query(default="", max_length=36),
        since: str = Query(default="", max_length=40),
        until: str = Query(default="", max_length=40),
        limit: int = Query(default=200, ge=1, le=1000),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /governance/audit"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            return _envelope(
                request,
                data=read_governance_audit(
                    db,
                    context=context,
                    actor=actor,
                    role=role,
                    permission=permission,
                    action=action,
                    result=result,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    command_intent_id=command_intent_id,
                    since=since,
                    until=until,
                    limit=limit,
                ),
                sources=[{"authority": "admin_operator_audit", "mode": "database"}],
            )
        finally:
            db.close()

    @router.get(
        "/governance/audit/export",
        response_model=None,
        responses={
            200: {
                "content": {
                    "text/csv": {"schema": {"type": "string", "format": "binary"}}
                }
            }
        },
    )
    def governance_audit_export(
        request: Request,
        actor: str = Query(default="", max_length=120),
        role: str = Query(default="", max_length=48),
        permission: str = Query(default="", max_length=96),
        action: str = Query(default="", max_length=96),
        result: str = Query(default="", max_length=24),
        resource_type: str = Query(default="", max_length=32),
        resource_id: str = Query(default="", max_length=128),
        command_intent_id: str = Query(default="", max_length=36),
        since: str = Query(default="", max_length=40),
        until: str = Query(default="", max_length=40),
        limit: int = Query(default=1000, ge=1, le=1000),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /governance/audit/export"])
        ),
    ) -> Response:
        db = session_factory()
        try:
            payload = read_governance_audit(
                db,
                context=context,
                actor=actor,
                role=role,
                permission=permission,
                action=action,
                result=result,
                resource_type=resource_type,
                resource_id=resource_id,
                command_intent_id=command_intent_id,
                since=since,
                until=until,
                limit=limit,
            )
            add_operator_read_audit(
                db,
                context=context,
                action="governance.audit.export",
                trace_id=_trace_id(request),
                resource_type="audit_export",
                resource_id=command_intent_id or None,
                details={
                    "row_count": len(payload.get("items") or []),
                    "limit": limit,
                    "filters": [
                        name
                        for name, value in {
                            "actor": actor,
                            "role": role,
                            "permission": permission,
                            "action": action,
                            "result": result,
                            "resource_type": resource_type,
                            "resource_id": resource_id,
                            "command_intent_id": command_intent_id,
                            "since": since,
                            "until": until,
                        }.items()
                        if value
                    ],
                },
            )
            db.commit()
            return Response(
                content="\ufeff" + audit_export_csv(payload),
                media_type="text/csv; charset=utf-8",
                headers={
                    "Cache-Control": "no-store",
                    "Content-Disposition": "attachment; filename=pokrov-operator-audit.csv",
                    "X-Content-Type-Options": "nosniff",
                },
            )
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @router.get("/governance/audit/commands/{intent_id}")
    def governance_command_lineage(
        intent_id: str,
        request: Request,
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /governance/audit/commands/{intent_id}"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            data = command_lineage(db, intent_id=intent_id, environment=context.environment)
            if data is None:
                raise AdminV2Error(
                    status_code=404,
                    code="command_intent_not_found",
                    message="Command intent was not found.",
                )
            return _envelope(
                request,
                data=data,
                sources=[
                    {"authority": "admin_action_intents", "mode": "database"},
                    {"authority": "admin_operator_audit", "mode": "database"},
                ],
            )
        finally:
            db.close()

    @router.get("/governance/sensitive-access")
    def governance_sensitive_access(
        request: Request,
        actor_tg_id: int | None = Query(default=None, ge=1),
        action: str = Query(default="", max_length=24),
        ticket_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=200, ge=1, le=1000),
        context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /governance/sensitive-access"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            payload = sensitive_access_log(
                db,
                actor_tg_id=actor_tg_id,
                action=action,
                ticket_id=ticket_id,
                limit=limit,
            )
            add_operator_read_audit(
                db,
                context=context,
                action="governance.sensitive_access.read",
                trace_id=_trace_id(request),
                resource_type="support_bundle_access_log",
                resource_id=str(ticket_id) if ticket_id is not None else None,
                details={
                    "row_count": len(payload.get("items") or []),
                    "limit": limit,
                    "filters": [
                        name
                        for name, value in {
                            "actor_tg_id": actor_tg_id,
                            "action": action,
                            "ticket_id": ticket_id,
                        }.items()
                        if value not in (None, "")
                    ],
                },
            )
            db.commit()
            return _envelope(
                request,
                data=payload,
                sources=[{"authority": "support_bundle_access_audits", "mode": "database"}],
            )
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @router.get("/governance/privacy")
    def governance_privacy(
        request: Request,
        _context: OperatorContext = Depends(
            permitted(ROUTE_PERMISSIONS["GET /governance/privacy"])
        ),
    ) -> dict[str, Any]:
        db = session_factory()
        try:
            return _envelope(
                request,
                data=privacy_retention_status(db),
                sources=[
                    {"authority": "worker.retention_policy", "mode": "code_and_environment"},
                    {"authority": "telemetry_and_support_bundle_tables", "mode": "database_aggregate"},
                ],
            )
        finally:
            db.close()

    @router.post("/governance/action-intents")
    def prepare_governance_action(
        command: OperatorActionCommand,
        request: Request,
        context: OperatorContext = Depends(
            permitted(
                ROUTE_PERMISSIONS["POST /governance/action-intents"],
                step_up=True,
            )
        ),
    ) -> dict[str, Any]:
        return _envelope(
            request,
            data=prepare_operator_action(
                command=command,
                context=context,
                allowed=GOVERNANCE_ACTIONS,
                permission="governance.operators.manage",
            ),
        )

    @router.post("/governance/action-intents/{intent_id}/execute")
    async def execute_governance_action(
        intent_id: str,
        command: OperatorActionCommand,
        request: Request,
        idempotency_key: str = Header(default="", alias="X-Admin-Idempotency-Key"),
        confirmation_sha256: str = Header(default="", alias="X-Admin-Confirmation-SHA256"),
        context: OperatorContext = Depends(
            permitted(
                ROUTE_PERMISSIONS["POST /governance/action-intents/{intent_id}/execute"],
                step_up=True,
            )
        ),
    ) -> dict[str, Any]:
        return _envelope(
            request,
            data=await execute_operator_action(
                intent_id=intent_id,
                command=command,
                context=context,
                allowed=GOVERNANCE_ACTIONS,
                permission="governance.operators.manage",
                idempotency_key=idempotency_key,
                confirmation_sha256=confirmation_sha256,
            ),
        )

    @router.get("/meta")
    def meta(
        request: Request,
        _context: OperatorContext = Depends(permitted(ROUTE_PERMISSIONS["GET /meta"])),
    ) -> dict[str, Any]:
        return build_admin_v2_meta_response(trace_id=_trace_id(request))

    app.add_exception_handler(AdminV2Error, admin_v2_error_handler)
    app.include_router(router)
    return runtime


__all__ = [
    "ADMIN_CSRF_HEADER",
    "ADMIN_SESSION_COOKIE",
    "AdminV2Runtime",
    "ROUTE_PERMISSIONS",
    "install_admin_v2",
]
