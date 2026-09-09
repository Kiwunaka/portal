from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import math
import re
import secrets
import time
from dataclasses import dataclass, field, replace
from typing import Awaitable, Callable, Mapping, Sequence

from support_agent_context import (
    MAX_CURRENT_MESSAGE_CHARS,
    PROMPT_BUNDLE_VERSION,
    ContextBuildError,
    SupportContextBuilder,
)
from support_agent_grounding import (
    DIRECT_RENDER_TOPICS,
    RETRIEVER_RULES_SHA256,
    RETRIEVER_VERSION,
    RetrievalDecision,
    RetrievalDisposition,
)
from support_agent_knowledge import KnowledgeSnapshot
from support_agent_policy import PolicySnapshot
from support_agent_provider import (
    ProviderCallError,
    ProviderUsage,
    SynthesisTurn,
)
from support_agent_safety import (
    InputBoundaryResult,
    InputDisposition,
    SafeSessionState,
    SafetyValidationError,
    classify_support_input,
    validate_model_output,
    validate_safe_reply,
)
from support_agent_sessions import (
    OwnerRateLimiter,
    SessionInFlightGuard,
    SessionScope,
    SessionState,
    StoredMessage,
    SupportSessionStore,
)
from support_agent_state import (
    ConversationSignals,
    NEGATIVE_OUTCOMES,
    classify_conversation_signals,
    sanitize_prior_state,
    state_after_answer,
    state_for_transfer,
    would_repeat_failure,
)


logger = logging.getLogger(__name__)

SAFE_FALLBACK_REPLY = (
    "Не нашёл подтверждённого ответа. Могу подключить специалиста поддержки."
)
RESOLVED_ACK_REPLY = "Хорошо, проблема решена. Если появится новый вопрос, напишите в поддержку."
PROGRESS_ACK_REPLY = (
    "Коротко\nШаг отмечен.\n\n"
    "Что сделать\nПроверьте, сохранилась ли проблема, и напишите результат.\n\n"
    "Если не поможет\nНапишите в поддержку."
)
NEGATIVE_ACK_REPLY = (
    "Коротко\nПонял, выполненный шаг не помог.\n\n"
    "Что сделать\nПроверьте оставшиеся шаги из предыдущего ответа и напишите результат.\n\n"
    "Если не поможет\nНапишите в поддержку."
)
_HASH_RE = re.compile(r"[0-9a-f]{64}")
_CODE_RE = re.compile(r"[A-Za-z0-9._/-]{1,64}")
_SURFACES = frozenset({"app", "ticket", "helpbot"})
_CONTINUING_PROBLEM_RE = re.compile(
    r"\b(?:но|однако|при\s+этом|кроме)\b|"
    r"\b(?:не\s+работ\w*|не\s+открыва\w*|не\s+могу|ошибк\w*)\b"
)
_MIXED_FOLLOWUP_RE = re.compile(
    r"\b(?:но|однако|при\s+этом|кроме|а\s+ещ[её])\b"
)
_MIN_PROVIDER_WINDOW_SECONDS = 0.1
_MAX_PROVIDER_TIMEOUT_SECONDS = 45.0
_MAX_RUN_DEADLINE_SECONDS = 50.0
_EMPTY_HASH = "0" * 64
_SAFE_DIAGNOSTIC_KEYS = (
    "account_access_state",
    "account_days_left",
    "account_device_count",
    "account_plan",
    "account_telegram_linked",
    "public_promo_state",
    "public_promo_codes",
    "platform",
    "app_version",
    "connection_status",
    "connection_active",
    "current_location_label",
    "route_mode",
    "enhanced_protection_state",
    "enhanced_protection_consent",
    "enhanced_protection_available",
    "panel_active_connections",
    "panel_last_online_age_seconds",
    "panel_runtime_state",
    "telegram_bonus_state",
)
_CURRENT_LOCATION_QUESTION_RE = re.compile(
    r"(?:\b(?:к|на)\s+какой\s+(?:я\s+)?(?:нод\w*|локаци\w*|сервер\w*|стран\w*)"
    r"(?:\s+я)?(?:\s+сейчас)?\s+подключ\w*|\bкуда\s+(?:я\s+)?подключ[её]н\w*|"
    r"\bка(?:кая|кой)\s+(?:у\s+меня\s+)?(?:сейчас\s+)?(?:активн\w*|текущ\w*)\s+"
    r"(?:нод\w*|локаци\w*|сервер\w*|стран\w*)|"
    r"\bка(?:кая|кой)\s+(?:нод\w*|локаци\w*|сервер\w*|стран\w*)\s+сейчас\b|"
    r"\b(?:текущ\w*|активн\w*)\s+(?:нод\w*|локаци\w*|сервер\w*|стран\w*)\b)",
    re.IGNORECASE,
)
_PROMO_QUESTION_RE = re.compile(
    r"\b(?:промокод\w*|промо\s*код\w*|купон\w*)\b",
    re.IGNORECASE,
)
_PROMO_CODE_RE = re.compile(r"[A-Z0-9][A-Z0-9_-]{1,19}")
_SAFE_LOCATION_LABEL_RE = re.compile(
    r"[0-9A-Za-zА-Яа-яЁё][0-9A-Za-zА-Яа-яЁё .()·_\-/]{0,79}"
)
_REDACTION_CATEGORIES = frozenset(
    {
        "private_link",
        "credential",
        "jwt",
        "telegram_init_data",
        "uuid",
        "private_key",
        "raw_config",
        "high_entropy",
        "payment_card",
        "email",
        "url",
        "ip",
        "private_host",
        "phone",
        "legacy_redaction",
        "other",
    }
)
_FIXED_ERROR_CODES = frozenset(
    {
        "agent_output_duplicate_key",
        "agent_output_json_invalid",
        "agent_output_reply_unsafe",
        "agent_output_root_invalid",
        "agent_output_size_invalid",
        "agent_output_source_invalid",
        "agent_output_status_invalid",
        "agent_output_unsupported_action",
        "bundle_snapshot_invalid",
        "context_limits_invalid",
        "current_message_invalid",
        "deadline_exhausted",
        "final_finish_reason_invalid",
        "harness_internal_error",
        "missing_source",
        "provider_choice_count_invalid",
        "provider_choice_invalid",
        "provider_content_invalid",
        "provider_http_error",
        "provider_request_error",
        "provider_request_invalid",
        "provider_request_too_large",
        "provider_response_invalid",
        "provider_response_too_large",
        "provider_timeout",
        "provider_tool_calls_invalid",
        "provider_transport_error",
        "provider_turn_invalid",
        "retrieval_decision_invalid",
        "retrieval_snapshot_mismatch",
        "session_message_invalid",
        "session_state_invalid",
        "session_write_failed",
        "stable_prefix_too_large",
    }
)


@dataclass(frozen=True, slots=True)
class SupportAgentRequest:
    surface: str
    session_scope: SessionScope
    message: str
    now: float
    safe_diagnostics: tuple[tuple[str, str | int | bool | None], ...] = ()
    case_loader: Callable[[], Awaitable[dict]] | None = field(default=None, repr=False)


@dataclass(frozen=True, slots=True)
class SupportAgentResult:
    status: str
    reply: str = field(repr=False)
    context_topic_ids: tuple[str, ...]
    grounding_topic_id: str | None
    session_state: SafeSessionState | None
    answer_origin: str
    provider_request_count: int
    escalation_reason: str | None
    usage: ProviderUsage
    latency_ms: int


@dataclass(frozen=True, slots=True)
class SupportAgentTrace:
    run_id: str
    surface: str
    session_id_hash: str
    provider: str
    model: str
    reasoning_effort: str
    policy_version: str
    policy_sha256: str
    prompt_bundle_version: str
    prompt_bundle_sha256: str
    knowledge_version: str
    knowledge_sha256: str
    retriever_version: str
    retriever_sha256: str
    stable_prefix_hash: str
    retrieval_disposition: str
    context_topic_ids: tuple[str, ...]
    grounding_topic_id: str | None
    provider_request_count: int
    prompt_tokens: int | None
    completion_tokens: int | None
    cached_tokens: int | None
    queue_latency_ms: int
    provider_latency_ms: int | None
    latency_ms: int
    input_redaction_counts: tuple[tuple[str, int], ...]
    output_redaction_counts: tuple[tuple[str, int], ...]
    error_code: str | None
    status: str
    answer_origin: str
    escalation_reason: str | None


@dataclass(frozen=True, slots=True)
class _Outcome:
    status: str
    reply: str = field(repr=False)
    context_topic_ids: tuple[str, ...]
    grounding_topic_id: str | None
    session_state: SafeSessionState | None
    answer_origin: str
    escalation_reason: str | None


class _HarnessFailure(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(slots=True)
class _RunStats:
    provider_request_count: int = 0
    stable_prefix_hash: str = _EMPTY_HASH
    prompt_bundle_sha256: str = _EMPTY_HASH
    retrieval_disposition: str = "not_run"
    context_topic_ids: tuple[str, ...] = ()
    grounding_topic_id: str | None = None
    input_redaction_counts: tuple[tuple[str, int], ...] = ()
    output_redaction_counts: tuple[tuple[str, int], ...] = ()
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cached_tokens: int | None = None
    queue_latency_ms: int = 0
    provider_latency_ms: int | None = None
    error_code: str | None = None

    def record_decision(self, decision: RetrievalDecision) -> None:
        self.retrieval_disposition = decision.disposition.value
        self.context_topic_ids = decision.context_topic_ids
        self.grounding_topic_id = decision.grounding_topic_id

    def add_turn(self, turn: SynthesisTurn) -> None:
        self.provider_latency_ms = turn.latency_ms
        self.prompt_tokens = turn.usage.prompt_tokens
        self.completion_tokens = turn.usage.completion_tokens
        self.cached_tokens = turn.usage.cached_tokens

    def usage(self) -> ProviderUsage:
        return ProviderUsage(
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            cached_tokens=self.cached_tokens,
        )


def _closed_counts(values: Mapping[str, int]) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for raw_category, raw_count in values.items():
        category = raw_category if raw_category in _REDACTION_CATEGORIES else "other"
        count = raw_count if type(raw_count) is int and raw_count >= 0 else 0
        counts[category] = counts.get(category, 0) + count
    return tuple(sorted(counts.items()))


def _valid_safe_diagnostics(
    values: tuple[tuple[str, str | int | bool | None], ...],
) -> bool:
    if not isinstance(values, tuple) or len(values) > len(_SAFE_DIAGNOSTIC_KEYS):
        return False
    seen: set[str] = set()
    for item in values:
        if not isinstance(item, tuple) or len(item) != 2:
            return False
        key, value = item
        if key not in _SAFE_DIAGNOSTIC_KEYS or key in seen:
            return False
        seen.add(key)
        if isinstance(value, str):
            if len(value) > 512 or any(
                ord(character) < 32 and character not in "\t\n\r"
                for character in value
            ):
                return False
        elif type(value) not in {int, bool} and value is not None:
            return False
    return True


def _synthesis_question_with_diagnostics(
    message: str,
    diagnostics: tuple[tuple[str, str | int | bool | None], ...],
) -> str:
    if not diagnostics:
        return message
    by_key = dict(diagnostics)
    admitted: dict[str, str | int | bool] = {}
    marker = "\n\nAPP_DIAGNOSTICS_JSON\n"
    for key in _SAFE_DIAGNOSTIC_KEYS:
        value = by_key.get(key)
        if value is None:
            continue
        candidate = {**admitted, key: value}
        encoded = json.dumps(
            candidate,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        if len(message) + len(marker) + len(encoded) > MAX_CURRENT_MESSAGE_CHARS:
            continue
        admitted = candidate
    if not admitted:
        return message
    encoded = json.dumps(
        admitted,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return f"{message}{marker}{encoded}"


def _safe_location_label(value: object) -> str:
    candidate = " ".join(str(value or "").split())
    if not candidate or not _SAFE_LOCATION_LABEL_RE.fullmatch(candidate):
        return ""
    return candidate


def _safe_promo_codes(value: object) -> tuple[str, ...]:
    if not isinstance(value, str):
        return ()
    codes: list[str] = []
    for raw in value.split(","):
        code = raw.strip().upper()
        if _PROMO_CODE_RE.fullmatch(code) and code not in codes:
            codes.append(code)
        if len(codes) >= 3:
            break
    return tuple(codes)


def _code_owned_snapshot_reply(
    message: str,
    diagnostics: tuple[tuple[str, str | int | bool | None], ...],
) -> tuple[str, str] | None:
    """Render exact read-only account/client facts without a provider guess."""

    by_key = dict(diagnostics)
    if _CURRENT_LOCATION_QUESTION_RE.search(message):
        connected = by_key.get("connection_active") is True
        location = _safe_location_label(by_key.get("current_location_label"))
        if connected and location and location.casefold() not in {
            "локация проверяется",
            "выбранная локация",
        }:
            reply = (
                f"Коротко\nНа этом устройстве POKROV сейчас подключён: {location}.\n\n"
                "Что это значит\nЭто подтверждённая активная локация клиента, без адреса ноды и приватных данных."
            )
        elif connected:
            reply = (
                "Коротко\nVPN подключён, но приложение ещё не подтвердило точную активную локацию.\n\n"
                "Что сделать\nОткройте «Локации» и дождитесь окончания проверки соединения."
            )
        elif location and location.casefold() not in {
            "автоматически",
            "локация проверяется",
            "выбранная локация",
        }:
            reply = (
                f"Коротко\nСейчас VPN выключен; выбрана локация {location}, но активной ноды нет.\n\n"
                "Что сделать\nПодключите POKROV, чтобы приложение подтвердило фактическую ноду."
            )
        else:
            reply = (
                "Коротко\nСейчас нет подтверждённой активной ноды.\n\n"
                "Что сделать\nПодключите POKROV и повторите вопрос после проверки соединения."
            )
        return "current_connection_snapshot", reply

    if _PROMO_QUESTION_RE.search(message):
        codes = _safe_promo_codes(by_key.get("public_promo_codes"))
        promo_state = str(by_key.get("public_promo_state") or "unknown").strip().lower()
        if codes:
            reply = (
                f"Коротко\nДля этого аккаунта сейчас доступны промокоды: {', '.join(codes)}.\n\n"
                "Что сделать\nВведите нужный код в разделе «Бонусы». Условия и итог проверит сервер до применения."
            )
        elif promo_state == "none":
            reply = (
                "Коротко\nДля этого аккаунта сейчас нет опубликованного активного промокода.\n\n"
                "Что сделать\nЕсли код уже пришёл в баннере, уведомлении или официальном боте, введите его в разделе «Бонусы»."
            )
        else:
            reply = (
                "Коротко\nНе удалось безопасно проверить доступные этому аккаунту промокоды.\n\n"
                "Что сделать\nИспользуйте только код из баннера, уведомления или официального бота и введите его в разделе «Бонусы»."
            )
        return "promo_codes", reply
    return None


def _safe_config_code(adapter: object, name: str, default: str) -> str:
    config = getattr(adapter, "config", None)
    value = getattr(config, name, default)
    return value if isinstance(value, str) and _CODE_RE.fullmatch(value) else default


def _fixed_error_code(exc: BaseException) -> str:
    if isinstance(exc, ProviderCallError):
        candidate = exc.code
        fallback = "provider_request_error"
    elif isinstance(exc, _HarnessFailure):
        candidate = exc.code
        fallback = "harness_internal_error"
    elif isinstance(exc, ContextBuildError):
        candidate = str(exc)
        fallback = "provider_request_invalid"
    elif isinstance(exc, SafetyValidationError):
        candidate = str(exc)
        fallback = "agent_output_root_invalid"
    else:
        return "harness_internal_error"
    return candidate if candidate in _FIXED_ERROR_CODES else fallback


def _human_transfer(
    reason: str,
    *,
    status: str,
    session_state: SafeSessionState | None = None,
) -> _Outcome:
    return _Outcome(
        status=status,
        reply=SAFE_FALLBACK_REPLY,
        context_topic_ids=(),
        grounding_topic_id=None,
        session_state=session_state,
        answer_origin="human_transfer",
        escalation_reason=reason,
    )


def _state_for_any_transfer(
    prior: SafeSessionState | None,
    signals: ConversationSignals,
) -> SafeSessionState:
    if prior is not None:
        return state_for_transfer(prior, signals)
    return replace(
        state_after_answer(None, None, signals),
        escalation_requested=True,
    )


class SupportAgentHarness:
    def __init__(
        self,
        *,
        policy: PolicySnapshot,
        knowledge: KnowledgeSnapshot,
        grounding_engine: object,
        session_store: SupportSessionStore,
        rate_limiter: OwnerRateLimiter,
        in_flight_guard: SessionInFlightGuard,
        adapter: object,
        context_builder: SupportContextBuilder | None = None,
        max_concurrency: int = 2,
        concurrency_wait_seconds: float = 0.25,
        run_deadline_seconds: float = 25.0,
        provider_timeout_seconds: float = 20.0,
        monotonic: Callable[[], float] | None = None,
        trace_callback: Callable[[SupportAgentTrace], object] | None = None,
    ) -> None:
        if (
            not isinstance(policy, PolicySnapshot)
            or not isinstance(knowledge, KnowledgeSnapshot)
            or type(max_concurrency) is not int
            or not 1 <= max_concurrency <= 2
            or not math.isfinite(concurrency_wait_seconds)
            or not 0.001 <= concurrency_wait_seconds <= 0.25
            or not math.isfinite(run_deadline_seconds)
            or not 0.1 <= run_deadline_seconds <= _MAX_RUN_DEADLINE_SECONDS
            or not math.isfinite(provider_timeout_seconds)
            or not 0.1 <= provider_timeout_seconds <= _MAX_PROVIDER_TIMEOUT_SECONDS
        ):
            raise ValueError("harness_config_invalid")
        self.policy = policy
        self.knowledge = knowledge
        self.grounding_engine = grounding_engine
        self.session_store = session_store
        self.rate_limiter = rate_limiter
        self.in_flight_guard = in_flight_guard
        self.adapter = adapter
        self.context_builder = context_builder or SupportContextBuilder()
        self.max_concurrency = max_concurrency
        self.process_semaphore = asyncio.Semaphore(max_concurrency)
        self.concurrency_wait_seconds = float(concurrency_wait_seconds)
        self.run_deadline_seconds = float(run_deadline_seconds)
        self.provider_timeout_seconds = float(provider_timeout_seconds)
        self.monotonic = monotonic or time.monotonic
        self.trace_callback = trace_callback
        self.model_code = _safe_config_code(adapter, "model", "configured_model")
        self.reasoning_effort = _safe_config_code(adapter, "reasoning_effort", "configured")

    @property
    def available_concurrency(self) -> int:
        return int(getattr(self.process_semaphore, "_value", 0))

    def _remaining(self, started: float) -> float:
        return self.run_deadline_seconds - max(0.0, self.monotonic() - started)

    @staticmethod
    def _valid_request_scope(request: SupportAgentRequest) -> bool:
        scope = request.session_scope
        return bool(
            isinstance(scope, SessionScope)
            and request.surface in _SURFACES
            and scope.surface == request.surface
            and isinstance(scope.owner_scope_hash, str)
            and _HASH_RE.fullmatch(scope.owner_scope_hash)
            and isinstance(scope.internal_session_key, str)
            and _HASH_RE.fullmatch(scope.internal_session_key)
            and isinstance(request.now, (int, float))
            and not isinstance(request.now, bool)
            and math.isfinite(float(request.now))
            and request.now >= 0
            and _valid_safe_diagnostics(request.safe_diagnostics)
        )

    def _append_pair(
        self,
        request: SupportAgentRequest,
        user_text: str,
        assistant_text: str,
        state: SafeSessionState,
    ) -> bool:
        try:
            self.session_store.append(
                request.session_scope.internal_session_key,
                (
                    StoredMessage(role="user", content=user_text),
                    StoredMessage(role="assistant", content=assistant_text),
                ),
                state,
                request.now,
            )
        except Exception:
            return False
        return True

    def _persist_transfer_or_unstored(
        self,
        request: SupportAgentRequest,
        user_text: str,
        state: SafeSessionState,
        reason: str,
        stats: _RunStats,
    ) -> _Outcome:
        if not self._append_pair(request, user_text, SAFE_FALLBACK_REPLY, state):
            stats.error_code = "session_write_failed"
            return _human_transfer("session_write_failed", status="escalate")
        return _human_transfer(reason, status="escalate", session_state=state)

    def _persist_soft_transfer_or_unstored(
        self,
        request: SupportAgentRequest,
        user_text: str,
        state: SafeSessionState,
        reason: str,
        stats: _RunStats,
    ) -> _Outcome:
        """Offer a human for one turn without disabling later AI questions."""

        if not self._append_pair(request, user_text, SAFE_FALLBACK_REPLY, state):
            stats.error_code = "session_write_failed"
            return _human_transfer("session_write_failed", status="escalate")
        return _human_transfer(reason, status="escalate", session_state=state)

    def _persist_answer_or_transfer(
        self,
        request: SupportAgentRequest,
        user_text: str,
        reply: str,
        state: SafeSessionState,
        decision: RetrievalDecision,
        answer_origin: str,
        stats: _RunStats,
    ) -> _Outcome:
        if not self._append_pair(request, user_text, reply, state):
            stats.error_code = "session_write_failed"
            return _human_transfer("session_write_failed", status="fallback")
        return _Outcome(
            status="answer",
            reply=reply,
            context_topic_ids=decision.context_topic_ids,
            grounding_topic_id=decision.grounding_topic_id,
            session_state=state,
            answer_origin=answer_origin,
            escalation_reason=None,
        )

    def _persist_code_owned_resolution(
        self,
        request: SupportAgentRequest,
        user_text: str,
        state: SafeSessionState,
        stats: _RunStats,
    ) -> _Outcome:
        try:
            reply = validate_safe_reply(RESOLVED_ACK_REPLY, self.policy)
        except SafetyValidationError as exc:
            stats.error_code = _fixed_error_code(exc)
            return _human_transfer(stats.error_code, status="fallback")
        if not self._append_pair(request, user_text, reply, state):
            stats.error_code = "session_write_failed"
            return _human_transfer("session_write_failed", status="fallback")
        return _Outcome(
            status="answer",
            reply=reply,
            context_topic_ids=(),
            grounding_topic_id=None,
            session_state=state,
            answer_origin="code_owned",
            escalation_reason=None,
        )

    def _persist_code_owned_progress(
        self,
        request: SupportAgentRequest,
        user_text: str,
        state: SafeSessionState,
        decision: RetrievalDecision,
        stats: _RunStats,
        reply_text: str = PROGRESS_ACK_REPLY,
    ) -> _Outcome:
        try:
            reply = validate_safe_reply(reply_text, self.policy)
        except SafetyValidationError as exc:
            stats.error_code = _fixed_error_code(exc)
            return _human_transfer(stats.error_code, status="fallback")
        if not self._append_pair(request, user_text, reply, state):
            stats.error_code = "session_write_failed"
            return _human_transfer("session_write_failed", status="fallback")
        return _Outcome(
            status="answer",
            reply=reply,
            context_topic_ids=decision.context_topic_ids,
            grounding_topic_id=None,
            session_state=state,
            answer_origin="code_owned",
            escalation_reason=None,
        )

    def _persist_code_owned_snapshot(
        self,
        request: SupportAgentRequest,
        user_text: str,
        state: SafeSessionState,
        topic_id: str,
        reply_text: str,
        stats: _RunStats,
    ) -> _Outcome:
        try:
            reply = validate_safe_reply(reply_text, self.policy)
        except SafetyValidationError as exc:
            stats.error_code = _fixed_error_code(exc)
            return _human_transfer(stats.error_code, status="fallback")
        if not self._append_pair(request, user_text, reply, state):
            stats.error_code = "session_write_failed"
            return _human_transfer("session_write_failed", status="fallback")
        return _Outcome(
            status="answer",
            reply=reply,
            context_topic_ids=(topic_id,),
            grounding_topic_id=topic_id,
            session_state=state,
            answer_origin="code_owned",
            escalation_reason=None,
        )

    async def _execute_case(self, request, boundary, session, stats, started) -> _Outcome:
        from support_case_context import CASE_PROMPT, case_fallback

        case = await asyncio.wait_for(request.case_loader(), timeout=min(25.0, self._remaining(started)))
        if case.get("operator_handling"):
            return _Outcome("silent", "", (), None, None, "code_owned", "operator_handling")
        decision = self.grounding_engine.select(boundary.model_text, session)
        stats.stable_prefix_hash = hashlib.sha256(CASE_PROMPT.encode("utf-8")).hexdigest()
        stats.prompt_bundle_sha256 = stats.stable_prefix_hash
        topics = [{"id": hit.topic_id, "body": hit.body} for hit in decision.context_topics[:2]]
        payload = json.dumps({"question": boundary.model_text, "case": case, "knowledge": topics},
                             ensure_ascii=False, separators=(",", ":"))
        messages = ({"role": "system", "content": CASE_PROMPT},
                    {"role": "user", "content": payload})
        remaining = self._remaining(started)
        if remaining < _MIN_PROVIDER_WINDOW_SECONDS:
            return _human_transfer("deadline_exhausted", status="fallback")
        stats.provider_request_count = 1
        try:
            turn = await self.adapter.complete_synthesis(messages=messages,
                request_timeout=min(self.provider_timeout_seconds, remaining))
            stats.add_turn(turn)
            model = validate_model_output(turn.content, self.policy,
                source_text=(CASE_PROMPT + "\n" + "\n".join(t["body"] for t in topics))[:3600])
        except (ProviderCallError, SafetyValidationError) as exc:
            stats.error_code = _fixed_error_code(exc)
            reply = validate_safe_reply(case_fallback(case), self.policy)
            return _Outcome("escalate", reply, (), None, None, "case_local", stats.error_code)
        state = state_after_answer(None if session is None else session.state, None,
                                   classify_conversation_signals(boundary.model_text))
        if not self._append_pair(request, boundary.model_text, model.reply, state):
            return _human_transfer("session_write_failed", status="fallback")
        return _Outcome(model.status, model.reply, (), None, state, "case_model",
                        "model_escalation" if model.status == "escalate" else None)

    async def _execute_locked(
        self,
        request: SupportAgentRequest,
        boundary: InputBoundaryResult,
        session: SessionState | None,
        stats: _RunStats,
        started: float,
    ) -> _Outcome:
        if session is not None:
            session = replace(
                session,
                state=sanitize_prior_state(
                    session.state,
                    frozenset(self.knowledge.topics_by_id),
                ),
            )
        if session is not None and session.state.escalation_requested:
            return _human_transfer(
                "escalation_already_requested",
                status="escalate",
                session_state=session.state,
            )

        if request.case_loader is not None:
            return await self._execute_case(request, boundary, session, stats, started)

        signals = classify_conversation_signals(boundary.model_text)
        snapshot_answer = _code_owned_snapshot_reply(
            boundary.model_text,
            request.safe_diagnostics,
        )
        if snapshot_answer is not None:
            topic_id, reply = snapshot_answer
            state = state_after_answer(
                None if session is None else session.state,
                topic_id if topic_id in self.knowledge.topics_by_id else None,
                signals,
            )
            return self._persist_code_owned_snapshot(
                request,
                boundary.model_text,
                state,
                topic_id,
                reply,
                stats,
            )
        normalized_resolution = boundary.model_text.casefold().replace("ё", "е")
        if (
            signals.outcome == "resolved"
            and "?" not in boundary.model_text
            and not _CONTINUING_PROBLEM_RE.search(normalized_resolution)
        ):
            state = state_after_answer(
                None if session is None else session.state,
                None,
                signals,
            )
            return self._persist_code_owned_resolution(
                request,
                boundary.model_text,
                state,
                stats,
            )

        decision = self.grounding_engine.select(boundary.model_text, session)
        if not isinstance(decision, RetrievalDecision):
            stats.error_code = "retrieval_decision_invalid"
            return _human_transfer("retrieval_decision_invalid", status="fallback")
        stats.record_decision(decision)

        if session is not None and (
            would_repeat_failure(session.state, signals)
            or (
                signals.outcome in NEGATIVE_OUTCOMES
                and "contact_support" in session.state.attempted_steps
            )
        ):
            state = state_for_transfer(session.state, signals)
            return self._persist_transfer_or_unstored(
                request,
                boundary.model_text,
                state,
                "repeated_unsuccessful",
                stats,
            )
        if (
            session is not None
            and session.state.issue_topic_id is not None
            and signals.outcome in NEGATIVE_OUTCOMES
            and len(normalized_resolution) <= 160
            and "?" not in boundary.model_text
            and not _MIXED_FOLLOWUP_RE.search(normalized_resolution)
            and decision.grounding_topic_id
            in {None, session.state.issue_topic_id}
        ):
            state = state_after_answer(session.state, None, signals)
            return self._persist_code_owned_progress(
                request,
                boundary.model_text,
                state,
                decision,
                stats,
                NEGATIVE_ACK_REPLY,
            )
        if (
            session is not None
            and session.state.issue_topic_id is not None
            and signals.outcome is None
            and "?" not in boundary.model_text
            and not _CONTINUING_PROBLEM_RE.search(normalized_resolution)
            and any(
                step not in session.state.attempted_steps
                for step in signals.attempted_steps
            )
            and decision.grounding_topic_id
            in {None, session.state.issue_topic_id}
        ):
            state = state_after_answer(session.state, None, signals)
            return self._persist_code_owned_progress(
                request,
                boundary.model_text,
                state,
                decision,
                stats,
            )
        if decision.disposition is RetrievalDisposition.NONE:
            return _human_transfer("missing_source", status="escalate")
        if (
            session is None
            and decision.grounding_topic_id in DIRECT_RENDER_TOPICS
        ):
            direct_reply = self.grounding_engine.render_local(decision, self.policy)
            if direct_reply is not None:
                state = state_after_answer(None, decision.grounding_topic_id, signals)
                return self._persist_answer_or_transfer(
                    request,
                    boundary.model_text,
                    direct_reply,
                    state,
                    decision,
                    "grounded_local",
                    stats,
                )

        try:
            context = self.context_builder.build_synthesis(
                policy=self.policy,
                knowledge=self.knowledge,
                session=session,
                redacted_message=_synthesis_question_with_diagnostics(
                    boundary.model_text,
                    request.safe_diagnostics,
                ),
                decision=decision,
            )
        except ContextBuildError as exc:
            stats.error_code = _fixed_error_code(exc)
            return _human_transfer(stats.error_code, status="fallback")

        stats.stable_prefix_hash = context.stable_prefix_hash
        stats.prompt_bundle_sha256 = context.prompt_bundle_sha256
        remaining = self._remaining(started)
        if remaining < _MIN_PROVIDER_WINDOW_SECONDS:
            stats.error_code = "deadline_exhausted"
            return _human_transfer("deadline_exhausted", status="fallback")
        stats.provider_request_count = 1
        try:
            turn = await self.adapter.complete_synthesis(
                messages=context.messages,
                request_timeout=min(self.provider_timeout_seconds, remaining),
            )
            if not isinstance(turn, SynthesisTurn):
                raise _HarnessFailure("provider_turn_invalid")
            stats.add_turn(turn)
            if turn.finish_reason != "stop":
                raise _HarnessFailure("final_finish_reason_invalid")
            source_text = "\n".join(
                self.knowledge.topics_by_id[topic_id].body
                for topic_id in context.context_topic_ids
            )
            model = validate_model_output(
                turn.content,
                self.policy,
                source_text=source_text,
            )
            if model.status == "escalate":
                state = state_after_answer(
                    None if session is None else session.state,
                    decision.grounding_topic_id,
                    signals,
                )
                return self._persist_soft_transfer_or_unstored(
                    request,
                    boundary.model_text,
                    state,
                    "model_escalation",
                    stats,
                )
            state = state_after_answer(
                None if session is None else session.state,
                decision.grounding_topic_id,
                signals,
            )
            return self._persist_answer_or_transfer(
                request,
                boundary.model_text,
                model.reply,
                state,
                decision,
                "model",
                stats,
            )
        except (ProviderCallError, SafetyValidationError, _HarnessFailure) as exc:
            stats.error_code = _fixed_error_code(exc)
            if isinstance(exc, SafetyValidationError):
                stats.output_redaction_counts = (("other", 1),)
            try:
                local_reply = self.grounding_engine.render_local(decision, self.policy)
                if local_reply is not None:
                    local_reply = validate_safe_reply(local_reply, self.policy)
            except Exception:
                stats.error_code = "harness_internal_error"
                return _human_transfer("harness_internal_error", status="fallback")
            if local_reply is None:
                return _human_transfer(stats.error_code, status="fallback")
            state = state_after_answer(
                None if session is None else session.state,
                decision.grounding_topic_id,
                signals,
            )
            return self._persist_answer_or_transfer(
                request,
                boundary.model_text,
                local_reply,
                state,
                decision,
                "grounded_local",
                stats,
            )
        except Exception:
            stats.error_code = "harness_internal_error"
            logger.warning("support agent run failed code=harness_internal_error")
            return _human_transfer("harness_internal_error", status="fallback")

    def _finish(
        self,
        *,
        request: SupportAgentRequest,
        started: float,
        stats: _RunStats,
        outcome: _Outcome,
    ) -> SupportAgentResult:
        latency_ms = max(
            0,
            int(round(max(0.0, self.monotonic() - started) * 1000)),
        )
        result = SupportAgentResult(
            status=outcome.status,
            reply=outcome.reply,
            context_topic_ids=outcome.context_topic_ids,
            grounding_topic_id=outcome.grounding_topic_id,
            session_state=outcome.session_state,
            answer_origin=outcome.answer_origin,
            provider_request_count=stats.provider_request_count,
            escalation_reason=outcome.escalation_reason,
            usage=stats.usage(),
            latency_ms=latency_ms,
        )
        if self.trace_callback is None:
            return result
        scope = request.session_scope
        internal_key = getattr(scope, "internal_session_key", "")
        session_hash = (
            hashlib.sha256(internal_key.encode("ascii")).hexdigest()
            if isinstance(internal_key, str) and _HASH_RE.fullmatch(internal_key)
            else _EMPTY_HASH
        )
        trace = SupportAgentTrace(
            run_id=secrets.token_hex(8),
            surface=request.surface if request.surface in _SURFACES else "invalid",
            session_id_hash=session_hash,
            provider="xcody",
            model=self.model_code,
            reasoning_effort=self.reasoning_effort,
            policy_version=self.policy.policy.schema_version,
            policy_sha256=self.policy.sha256,
            prompt_bundle_version=PROMPT_BUNDLE_VERSION,
            prompt_bundle_sha256=stats.prompt_bundle_sha256,
            knowledge_version=self.knowledge.version,
            knowledge_sha256=self.knowledge.sha256,
            retriever_version=RETRIEVER_VERSION,
            retriever_sha256=RETRIEVER_RULES_SHA256,
            stable_prefix_hash=stats.stable_prefix_hash,
            retrieval_disposition=stats.retrieval_disposition,
            context_topic_ids=stats.context_topic_ids,
            grounding_topic_id=stats.grounding_topic_id,
            provider_request_count=stats.provider_request_count,
            prompt_tokens=stats.prompt_tokens,
            completion_tokens=stats.completion_tokens,
            cached_tokens=stats.cached_tokens,
            queue_latency_ms=stats.queue_latency_ms,
            provider_latency_ms=stats.provider_latency_ms,
            latency_ms=latency_ms,
            input_redaction_counts=stats.input_redaction_counts,
            output_redaction_counts=stats.output_redaction_counts,
            error_code=stats.error_code,
            status=outcome.status,
            answer_origin=outcome.answer_origin,
            escalation_reason=outcome.escalation_reason,
        )
        try:
            self.trace_callback(trace)
        except Exception:
            logger.warning("support agent trace callback failed code=trace_callback_error")
        return result

    async def run(self, request: SupportAgentRequest) -> SupportAgentResult:
        if not isinstance(request, SupportAgentRequest):
            raise TypeError("support_agent_request_invalid")
        started = self.monotonic()
        stats = _RunStats()
        boundary = classify_support_input(request.message, allow_case_reads=request.case_loader is not None)
        stats.input_redaction_counts = _closed_counts(boundary.category_counts)

        if not self._valid_request_scope(request):
            outcome = _human_transfer("request_scope_invalid", status="fallback")
            return self._finish(request=request, started=started, stats=stats, outcome=outcome)
        scope = request.session_scope
        try:
            allowed = self.rate_limiter.allow(scope.owner_scope_hash, request.now)
        except Exception:
            allowed = False
        if not allowed:
            outcome = _human_transfer("owner_rate_limited", status="fallback")
            return self._finish(request=request, started=started, stats=stats, outcome=outcome)
        try:
            acquired = await self.in_flight_guard.acquire(scope.internal_session_key)
        except Exception:
            acquired = False
        if not acquired:
            outcome = _human_transfer("session_busy", status="fallback")
            return self._finish(request=request, started=started, stats=stats, outcome=outcome)

        process_acquired = False
        try:
            try:
                await asyncio.wait_for(
                    self.process_semaphore.acquire(),
                    timeout=min(
                        self.concurrency_wait_seconds,
                        max(0.001, self._remaining(started)),
                    ),
                )
                process_acquired = True
                stats.queue_latency_ms = max(
                    0,
                    int(round(max(0.0, self.monotonic() - started) * 1000)),
                )
            except asyncio.TimeoutError:
                outcome = _human_transfer("process_busy", status="fallback")
                return self._finish(
                    request=request,
                    started=started,
                    stats=stats,
                    outcome=outcome,
                )

            try:
                session = self.session_store.get(scope.internal_session_key, request.now)
            except Exception:
                stats.error_code = "session_read_failed"
                outcome = _human_transfer("session_read_failed", status="fallback")
                return self._finish(
                    request=request,
                    started=started,
                    stats=stats,
                    outcome=outcome,
                )

            if boundary.disposition is InputDisposition.HARD_REJECT:
                outcome = _human_transfer(
                    boundary.escalation_reason or "sensitive_input",
                    status="escalate",
                )
            elif boundary.disposition is InputDisposition.LOCAL_ESCALATE:
                reason = boundary.escalation_reason or "local_escalation"
                if reason == "human_requested" and boundary.model_text:
                    prior = sanitize_prior_state(
                        None if session is None else session.state,
                        frozenset(self.knowledge.topics_by_id),
                    )
                    signals = classify_conversation_signals(boundary.model_text)
                    state = _state_for_any_transfer(prior, signals)
                    outcome = self._persist_transfer_or_unstored(
                        request,
                        boundary.model_text,
                        state,
                        reason,
                        stats,
                    )
                else:
                    outcome = _human_transfer(reason, status="escalate")
            else:
                outcome = await self._execute_locked(
                    request,
                    boundary,
                    session,
                    stats,
                    started,
                )
            return self._finish(
                request=request,
                started=started,
                stats=stats,
                outcome=outcome,
            )
        finally:
            if process_acquired:
                self.process_semaphore.release()
            try:
                await self.in_flight_guard.release(scope.internal_session_key)
            except Exception:
                logger.warning("support agent guard release failed code=guard_release_error")
