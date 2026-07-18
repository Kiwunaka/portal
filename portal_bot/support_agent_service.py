from __future__ import annotations

import logging
import math
import os
import secrets
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Awaitable, Callable, Mapping

from support_ai_service import SupportAIConfig, generate_support_reply
from support_agent_context import SupportContextBuilder
from support_agent_harness import SupportAgentHarness, SupportAgentRequest, SupportAgentResult
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


@dataclass(frozen=True, slots=True)
class SupportAgentRuntimeSettings:
    agent_enabled: bool
    valid: bool
    invalid_reason: str | None
    run_deadline_seconds: float
    provider_timeout_seconds: float
    max_provider_requests: int
    max_tool_calls: int
    max_concurrency: int
    concurrency_wait_ms: int
    session_ttl_seconds: float
    max_sessions: int
    owner_rate_limit_per_minute: int
    max_rate_buckets: int
    pre_retrieval_limit: int
    tool_result_limit: int
    max_retrieved_chars: int
    max_input_chars: int
    max_output_tokens: int

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

        settings = cls(
            agent_enabled=boolean("SUPPORT_AI_AGENT_ENABLED", False),
            valid=True,
            invalid_reason=None,
            run_deadline_seconds=number("SUPPORT_AI_RUN_DEADLINE_SECONDS", 25.0, 0.1, 25.0),
            provider_timeout_seconds=number("SUPPORT_AI_TIMEOUT_SECONDS", 12.0, 0.1, 12.0),
            max_provider_requests=integer("SUPPORT_AI_MAX_PROVIDER_REQUESTS", 2, 1, 2),
            max_tool_calls=integer("SUPPORT_AI_MAX_TOOL_CALLS", 1, 0, 1),
            max_concurrency=integer("SUPPORT_AI_MAX_CONCURRENCY", 2, 1, 2),
            concurrency_wait_ms=integer("SUPPORT_AI_CONCURRENCY_WAIT_MS", 250, 1, 250),
            session_ttl_seconds=number("SUPPORT_AI_SESSION_TTL_SECONDS", 3600.0, 1.0, 3600.0),
            max_sessions=integer("SUPPORT_AI_MAX_SESSIONS", 256, 1, 256),
            owner_rate_limit_per_minute=integer("SUPPORT_AI_OWNER_RATE_LIMIT_PER_MINUTE", 6, 1, 6),
            max_rate_buckets=integer("SUPPORT_AI_MAX_RATE_BUCKETS", 1024, 1, 1024),
            pre_retrieval_limit=integer("SUPPORT_AI_PRE_RETRIEVAL_LIMIT", 3, 1, 3),
            tool_result_limit=integer("SUPPORT_AI_TOOL_RESULT_LIMIT", 5, 1, 5),
            max_retrieved_chars=integer("SUPPORT_AI_MAX_RETRIEVED_CHARS", 6000, 1, 6000),
            max_input_chars=integer("SUPPORT_AI_MAX_INPUT_CHARS", 36000, 1000, 36000),
            max_output_tokens=integer("SUPPORT_AI_MAX_OUTPUT_TOKENS", 1200, 1, 1200),
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


def _agent_actions(topic_ids: tuple[str, ...]) -> tuple[Mapping[str, str], ...]:
    normalized = tuple(item.casefold() for item in topic_ids)
    return _fixed_actions(
        connection=any(marker in topic for topic in normalized for marker in _CONNECTION_TOPIC_MARKERS),
        access=any(marker in topic for topic in normalized for marker in _ACCESS_TOPIC_MARKERS),
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
            12.0,
        ),
        max_context_chars=min(config.max_context_chars, settings.max_input_chars),
        max_output_tokens=min(config.max_output_tokens, settings.max_output_tokens),
    )
    return SupportAgentHarness(
        policy=policy,
        knowledge_store=knowledge_store,
        knowledge=knowledge,
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
            max_retrieval_zone_chars=settings.max_retrieved_chars,
        ),
        max_provider_requests=settings.max_provider_requests,
        max_tool_calls=settings.max_tool_calls,
        max_concurrency=settings.max_concurrency,
        concurrency_wait_seconds=settings.concurrency_wait_ms / 1000.0,
        run_deadline_seconds=settings.run_deadline_seconds,
        provider_timeout_seconds=min(bounded_config.timeout_seconds, settings.run_deadline_seconds),
        pre_retrieval_limit=settings.pre_retrieval_limit,
        tool_result_limit=settings.tool_result_limit,
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
            return self.resolver.resolve_helpbot(validated_sender_id)
        raise ValueError("support_surface_invalid")

    def _local_result(self, message: str, session_id: str) -> SupportReplyResult:
        return SupportReplyResult(
            reply=support_fallback_reply(message),
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
                reply=str(reply)[:1200],
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

        try:
            result = await self._harness.run(
                SupportAgentRequest(
                    surface=surface,
                    session_scope=scope,
                    message=message,
                    now=float(self.time_source()),
                )
            )
        except Exception:
            logger.warning("support agent generation failed code=agent_run_error")
            return self._local_result(message, scope.client_session_id)
        if not isinstance(result, SupportAgentResult) or result.status != "answer":
            return self._local_result(message, scope.client_session_id)

        should_escalate = any(
            marker in topic.casefold()
            for topic in result.source_topic_ids
            for marker in _ACCESS_TOPIC_MARKERS
        )
        return SupportReplyResult(
            reply=result.reply,
            assistant_session_id=scope.client_session_id,
            suggested_actions=_agent_actions(result.source_topic_ids),
            should_escalate=should_escalate,
            source="support_agent",
        )
