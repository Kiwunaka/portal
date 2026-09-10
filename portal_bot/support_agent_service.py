from __future__ import annotations

import logging
import math
import os
import secrets
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Awaitable, Callable, Mapping

from support_ai_service import (
    DEFAULT_API_BASE_URL,
    DEEPSEEK_41_MODEL,
    SUPPORTED_MODELS,
    SupportAIConfig,
    canonical_support_model,
    generate_support_reply,
    is_exact_openrouter_route,
    provider_run_deadline_ceiling,
    provider_timeout_ceiling,
)
from support_agent_context import SupportContextBuilder
from support_agent_grounding import SupportGroundingEngine
from support_agent_harness import (
    SAFE_FALLBACK_REPLY,
    SupportAgentHarness,
    SupportAgentRequest,
    SupportAgentResult,
)
from support_agent_knowledge import SupportKnowledgeStore
from support_agent_policy import SupportAgentPolicyStore
from support_agent_provider import XCodyChatAdapter
from support_agent_sessions import (
    OwnerRateLimiter,
    SessionInFlightGuard,
    SessionScope,
    SupportSessionResolver,
    SupportSessionStore,
)


logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_POLICY_PATH = _REPO_ROOT / "shared" / "support-agent-policy.json"
_KNOWLEDGE_PATH = _REPO_ROOT / "shared" / "support-ai-knowledge.json"
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off"})
_SURFACES = frozenset({"app", "ticket", "helpbot"})
_CONNECTION_TOPIC_MARKERS = (
    "connect",
    "internet",
    "network",
    "dns",
    "route",
    "warp",
    "варп",
    "enhanced protection",
    "усиленная защита",
    "slow",
    "hiddify",
    "v2ray",
    "happ",
    "streisand",
)
_ACCESS_TOPIC_MARKERS = ("payment", "trial", "bonus", "access", "subscription", "key")


@dataclass(frozen=True, slots=True)
class SupportReplyResult:
    reply: str
    assistant_session_id: str
    suggested_actions: tuple[Mapping[str, str], ...]
    should_escalate: bool
    source: str
    case_actions: tuple = ()


@dataclass(frozen=True, slots=True)
class SupportAgentRuntimeSettings:
    agent_enabled: bool
    valid: bool
    invalid_reason: str | None
    run_deadline_seconds: float
    provider_timeout_seconds: float
    max_concurrency: int
    concurrency_wait_ms: int
    session_ttl_seconds: float
    max_sessions: int
    owner_rate_limit_per_minute: int
    max_rate_buckets: int
    pre_retrieval_limit: int
    max_input_chars: int

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "SupportAgentRuntimeSettings":
        source = os.environ if env is None else env
        errors: list[str] = []

        def boolean(name: str, default: bool) -> bool:
            raw = source.get(name)
            if raw is None or not str(raw).strip():
                return default
            normalized = str(raw).strip().casefold()
            if normalized in _TRUE_VALUES:
                return True
            if normalized in _FALSE_VALUES:
                return False
            errors.append(f"{name.lower()}_invalid")
            return default

        def integer(name: str, default: int, minimum: int, maximum: int) -> int:
            raw = source.get(name)
            if raw is None or not str(raw).strip():
                return default
            try:
                value = int(str(raw).strip())
            except (TypeError, ValueError):
                errors.append(f"{name.lower()}_invalid")
                return default
            if value < minimum or value > maximum:
                errors.append(f"{name.lower()}_invalid")
                return default
            return value

        def number(name: str, default: float, minimum: float, maximum: float) -> float:
            raw = source.get(name)
            if raw is None or not str(raw).strip():
                return default
            try:
                value = float(str(raw).strip())
            except (TypeError, ValueError):
                errors.append(f"{name.lower()}_invalid")
                return default
            if not math.isfinite(value) or value < minimum or value > maximum:
                errors.append(f"{name.lower()}_invalid")
                return default
            return value

        api_base_url = str(source.get("SUPPORT_AI_API_BASE_URL") or DEFAULT_API_BASE_URL)
        provider_timeout_max = provider_timeout_ceiling(api_base_url)
        run_deadline_max = provider_run_deadline_ceiling(api_base_url)
        settings = cls(
            agent_enabled=boolean("SUPPORT_AI_AGENT_ENABLED", False),
            valid=True,
            invalid_reason=None,
            run_deadline_seconds=number(
                "SUPPORT_AI_RUN_DEADLINE_SECONDS",
                run_deadline_max,
                0.1,
                run_deadline_max,
            ),
            provider_timeout_seconds=number(
                "SUPPORT_AI_TIMEOUT_SECONDS",
                provider_timeout_max,
                0.1,
                provider_timeout_max,
            ),
            max_concurrency=integer("SUPPORT_AI_MAX_CONCURRENCY", 2, 1, 2),
            concurrency_wait_ms=integer("SUPPORT_AI_CONCURRENCY_WAIT_MS", 250, 1, 250),
            session_ttl_seconds=number("SUPPORT_AI_SESSION_TTL_SECONDS", 3600.0, 1.0, 3600.0),
            max_sessions=integer("SUPPORT_AI_MAX_SESSIONS", 256, 1, 256),
            owner_rate_limit_per_minute=integer("SUPPORT_AI_OWNER_RATE_LIMIT_PER_MINUTE", 6, 1, 6),
            max_rate_buckets=integer("SUPPORT_AI_MAX_RATE_BUCKETS", 1024, 1, 1024),
            pre_retrieval_limit=integer("SUPPORT_AI_PRE_RETRIEVAL_LIMIT", 3, 1, 3),
            max_input_chars=integer("SUPPORT_AI_MAX_INPUT_CHARS", 30000, 1000, 30000),
        )
        if errors:
            return replace(settings, valid=False, invalid_reason=sorted(errors)[0])
        return settings


def support_fallback_reply(message: str) -> str:
    text = str(message or "").strip().casefold()
    if "err_connection_closed" in text or "не откры" in text or "не работает" in text:
        return (
            "Похоже, подключение поднялось, но трафик не проходит. "
            "Отключите POKROV, включите снова и приложите диагностику из чата поддержки, если ошибка повторится."
        )
    if "оплат" in text or "ключ" in text or "подпис" in text:
        return (
            "Проверим доступ по аккаунту. Если есть код активации или письмо с ключом, вставьте код в приложении, "
            "а данные карты отправлять не нужно."
        )
    return "Я рядом. Опишите, что нажали и что увидели на экране, а POKROV приложит безопасную диагностику к обращению."


def _fixed_actions(*, connection: bool, access: bool) -> tuple[Mapping[str, str], ...]:
    actions: list[Mapping[str, str]] = []
    if connection:
        actions.append({"key": "retry_connect", "label": "Reconnect"})
    actions.append({"key": "send_diagnostics", "label": "Attach diagnostics"})
    if access:
        actions.append({"key": "open_subscription", "label": "Check access"})
    actions.append({"key": "create_ticket", "label": "Write to support"})
    return tuple(actions)


def _fallback_actions() -> tuple[Mapping[str, str], ...]:
    return (
        {"key": "send_diagnostics", "label": "Attach diagnostics"},
        {"key": "create_ticket", "label": "Write to support"},
    )


def _legacy_actions(message: str) -> tuple[Mapping[str, str], ...]:
    text = str(message or "").casefold()
    return _fixed_actions(
        connection=any(marker in text for marker in ("err_connection_closed", "не откры", "не работает")),
        access=any(marker in text for marker in ("оплат", "ключ", "подпис")),
    )


def _agent_actions(grounding_topic_id: str | None) -> tuple[Mapping[str, str], ...]:
    if not isinstance(grounding_topic_id, str) or not grounding_topic_id:
        return _fallback_actions()
    normalized = grounding_topic_id.casefold()
    return _fixed_actions(
        connection=any(marker in normalized for marker in _CONNECTION_TOPIC_MARKERS),
        access=any(marker in normalized for marker in _ACCESS_TOPIC_MARKERS),
    )


def _default_harness_factory(
    config: SupportAIConfig,
    settings: SupportAgentRuntimeSettings,
) -> SupportAgentHarness:
    policy = SupportAgentPolicyStore().load(_POLICY_PATH)
    knowledge_store = SupportKnowledgeStore()
    knowledge = knowledge_store.load(_KNOWLEDGE_PATH)
    bounded_config = replace(
        config,
        timeout_seconds=min(
            config.timeout_seconds,
            settings.provider_timeout_seconds,
            settings.run_deadline_seconds,
            provider_timeout_ceiling(config.api_base_url),
        ),
        max_context_chars=min(config.max_context_chars, settings.max_input_chars),
    )
    return SupportAgentHarness(
        policy=policy,
        knowledge=knowledge,
        grounding_engine=SupportGroundingEngine(
            knowledge_store,
            knowledge,
            retrieval_limit=settings.pre_retrieval_limit,
        ),
        session_store=SupportSessionStore(
            ttl_seconds=settings.session_ttl_seconds,
            max_sessions=settings.max_sessions,
        ),
        rate_limiter=OwnerRateLimiter(
            limit=settings.owner_rate_limit_per_minute,
            max_buckets=settings.max_rate_buckets,
        ),
        in_flight_guard=SessionInFlightGuard(),
        adapter=XCodyChatAdapter(config=bounded_config),
        context_builder=SupportContextBuilder(
            max_provider_request_chars=settings.max_input_chars,
        ),
        max_concurrency=settings.max_concurrency,
        concurrency_wait_seconds=settings.concurrency_wait_ms / 1000.0,
        run_deadline_seconds=settings.run_deadline_seconds,
        provider_timeout_seconds=min(bounded_config.timeout_seconds, settings.run_deadline_seconds),
    )


class SupportAgentService:
    def __init__(
        self,
        *,
        config: SupportAIConfig | None = None,
        env: Mapping[str, str] | None = None,
        legacy_generate: Callable[..., Awaitable[str | None]] = generate_support_reply,
        harness_factory: Callable[[SupportAIConfig, SupportAgentRuntimeSettings], object] = _default_harness_factory,
        time_source: Callable[[], float] = time.monotonic,
    ) -> None:
        self.config = config or SupportAIConfig.from_env(env)
        self.settings = SupportAgentRuntimeSettings.from_env(env)
        self.legacy_generate = legacy_generate
        self.harness_factory = harness_factory
        self.time_source = time_source
        self.resolver = SupportSessionResolver()
        self._harness: object | None = None

    def _resolve_scope(
        self,
        *,
        surface: str,
        authenticated_owner_id: str,
        assistant_session_id: str | None,
        ticket_id: int | None,
        validated_sender_id: int | None,
    ) -> SessionScope:
        if surface == "app":
            return self.resolver.resolve_app(authenticated_owner_id, assistant_session_id)
        if surface == "ticket":
            if ticket_id is None:
                raise ValueError("ticket_session_missing")
            return self.resolver.resolve_ticket(authenticated_owner_id, ticket_id)
        if surface == "helpbot":
            if validated_sender_id is None:
                raise ValueError("helpbot_session_missing")
            return self.resolver.resolve_helpbot(validated_sender_id, ticket_id)
        raise ValueError("support_surface_invalid")

    def _local_result(self, message: str, session_id: str) -> SupportReplyResult:
        return SupportReplyResult(
            reply=support_fallback_reply(message),
            assistant_session_id=session_id,
            suggested_actions=_fallback_actions(),
            should_escalate=True,
            source="local_fallback",
        )

    @staticmethod
    def _agent_transfer_result(session_id: str) -> SupportReplyResult:
        return SupportReplyResult(
            reply=SAFE_FALLBACK_REPLY,
            assistant_session_id=session_id,
            suggested_actions=_fallback_actions(),
            should_escalate=True,
            source="local_fallback",
        )

    async def generate(
        self,
        *,
        surface: str,
        authenticated_owner_id: str,
        message: str,
        assistant_session_id: str | None = None,
        ticket_id: int | None = None,
        validated_sender_id: int | None = None,
        safe_diagnostics: Mapping[str, str | int | bool | None] | None = None,
        attachment_bot: object | None = None,
        case_context_enabled: bool = True,
    ) -> SupportReplyResult:
        try:
            scope = self._resolve_scope(
                surface=surface,
                authenticated_owner_id=authenticated_owner_id,
                assistant_session_id=assistant_session_id,
                ticket_id=ticket_id,
                validated_sender_id=validated_sender_id,
            )
        except Exception:
            opaque = secrets.token_urlsafe(24)
            logger.warning("support agent scope rejected code=session_scope_invalid")
            return self._local_result(message, opaque)

        if not self.config.enabled or not self.config.api_key:
            return self._local_result(message, scope.client_session_id)

        if not self.settings.valid:
            logger.warning("support agent disabled code=agent_settings_invalid")
            return self._local_result(message, scope.client_session_id)

        if (
            not is_exact_openrouter_route(self.config.api_base_url)
            or canonical_support_model(self.config.model) not in SUPPORTED_MODELS
            or self.config.reasoning_effort != (
                "high" if canonical_support_model(self.config.model) == DEEPSEEK_41_MODEL else "medium")
        ):
            logger.warning("support agent disabled code=agent_profile_invalid")
            return self._local_result(message, scope.client_session_id)

        if not self.settings.agent_enabled:
            try:
                owner_number = int(authenticated_owner_id) if str(authenticated_owner_id).isdigit() else 0
                reply = await self.legacy_generate(
                    message,
                    ticket_id=int(ticket_id or 0),
                    user_tg_id=owner_number,
                    config=self.config,
                )
            except Exception:
                logger.warning("support legacy generation failed code=legacy_provider_error")
                reply = None
            if not reply:
                return self._local_result(message, scope.client_session_id)
            text = str(message or "").casefold()
            should_escalate = any(
                marker in text for marker in ("err_", "не работает", "не откры", "оплат", "ключ")
            )
            return SupportReplyResult(
                reply=str(reply)[:self.config.max_answer_chars],
                assistant_session_id=scope.client_session_id,
                suggested_actions=_legacy_actions(message),
                should_escalate=should_escalate,
                source="support_ai",
            )

        if self._harness is None:
            try:
                self._harness = self.harness_factory(self.config, self.settings)
            except Exception:
                logger.warning("support agent startup failed code=agent_runtime_unavailable")
                return self._local_result(message, scope.client_session_id)

        case_loader = None
        case_tools = None
        if case_context_enabled and ticket_id is not None and surface in {"ticket", "helpbot"}:
            from support_case_context import load_case
            async def case_loader(analyze_attachment):
                return await load_case(int(authenticated_owner_id), int(ticket_id), attachment_bot,
                                       analyze_attachment=analyze_attachment)
            if canonical_support_model(self.config.model) == DEEPSEEK_41_MODEL:
                from support_case_tools import CaseTools
                case_tools = CaseTools(int(authenticated_owner_id), int(ticket_id), attachment_bot)

        try:
            result = await self._harness.run(
                SupportAgentRequest(
                    surface=surface,
                    session_scope=scope,
                    message=message,
                    now=float(self.time_source()),
                    case_loader=case_loader,
                    case_tools=case_tools,
                    safe_diagnostics=tuple(
                        sorted((safe_diagnostics or {}).items())
                    ),
                )
            )
        except Exception:
            logger.warning("support agent generation failed code=agent_run_error")
            return self._local_result(message, scope.client_session_id)
        if isinstance(result, SupportAgentResult) and result.status == "silent":
            return SupportReplyResult("", scope.client_session_id, (), False, "support_agent")
        if (case_tools is not None and isinstance(result, SupportAgentResult)
                and result.status == "escalate" and not result.case_actions):
            result = replace(result, case_actions=({"name": "request_operator", "queue": "general",
                                                   "reason": "Нужна проверка оператором поддержки."},))
        if isinstance(result, SupportAgentResult) and result.answer_origin in {"case_model", "case_local"}:
            return SupportReplyResult(result.reply, scope.client_session_id, _fallback_actions(),
                                      result.status == "escalate", "support_agent", result.case_actions)
        if not isinstance(result, SupportAgentResult) or result.status != "answer":
            transfer = self._agent_transfer_result(scope.client_session_id)
            return replace(transfer, case_actions=result.case_actions) if isinstance(result, SupportAgentResult) else transfer
        if result.answer_origin not in {"model", "grounded_local", "code_owned"}:
            return self._agent_transfer_result(scope.client_session_id)
        return SupportReplyResult(
            reply=result.reply,
            assistant_session_id=scope.client_session_id,
            suggested_actions=_agent_actions(result.grounding_topic_id),
            should_escalate=False,
            source="support_agent",
        )
