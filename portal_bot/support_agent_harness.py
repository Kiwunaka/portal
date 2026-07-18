from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import math
import random
import re
import secrets
import time
from dataclasses import dataclass, field, replace
from typing import Any, Awaitable, Callable, Mapping, Sequence

from support_agent_context import AgentContext, SupportContextBuilder, ToolContinuation
from support_agent_knowledge import KnowledgeHit, KnowledgeSnapshot, SupportKnowledgeStore
from support_agent_policy import PolicySnapshot
from support_agent_provider import ModelTurn, ProviderCallError, ProviderUsage, ToolCall
from support_agent_safety import (
    InputBoundaryResult,
    InputDisposition,
    SafeSessionState,
    SafetyValidationError,
    ValidatedAgentAnswer,
    classify_support_input,
    validate_agent_output,
)
from support_agent_sessions import (
    OwnerRateLimiter,
    SessionInFlightGuard,
    SessionScope,
    SessionState,
    StoredMessage,
    SupportSessionStore,
)


logger = logging.getLogger(__name__)

SAFE_FALLBACK_REPLY = "Не удалось безопасно подготовить ответ. Передаю вопрос специалисту поддержки."
_TOOL_NAME = "search_support_docs"
_TOOL_CALL_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_MODEL_CODE_RE = re.compile(r"^[A-Za-z0-9._/-]{1,64}$")
_SURFACES = frozenset({"app", "ticket", "helpbot"})
_MIN_PROVIDER_WINDOW_SECONDS = 0.1


@dataclass(frozen=True, slots=True)
class SupportAgentRequest:
    surface: str
    session_scope: SessionScope
    message: str
    now: float


@dataclass(frozen=True, slots=True)
class SupportAgentResult:
    status: str
    reply: str
    source_topic_ids: tuple[str, ...]
    session_state: SafeSessionState | None
    provider_request_count: int
    tool_call_count: int
    retry_count: int
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
    policy_sha256: str
    knowledge_version: str
    knowledge_sha256: str
    stable_prefix_hash: str
    provider_request_count: int
    tool_call_count: int
    retry_count: int
    retrieved_topic_ids: tuple[str, ...]
    redaction_categories: tuple[tuple[str, int], ...]
    prompt_tokens: int | None
    completion_tokens: int | None
    cached_tokens: int | None
    provider_latencies_ms: tuple[int, ...]
    latency_ms: int
    error_code: str | None
    status: str
    escalation_reason: str | None


class _HarnessFailure(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(slots=True)
class _RunStats:
    provider_request_count: int = 0
    tool_call_count: int = 0
    retry_count: int = 0
    stable_prefix_hash: str = ""
    retrieved_topic_ids: list[str] = field(default_factory=list)
    redaction_categories: tuple[tuple[str, int], ...] = ()
    prompt_tokens: list[int] = field(default_factory=list)
    completion_tokens: list[int] = field(default_factory=list)
    cached_tokens: list[int] = field(default_factory=list)
    provider_latencies_ms: list[int] = field(default_factory=list)
    error_code: str | None = None

    def add_turn(self, turn: ModelTurn) -> None:
        self.provider_latencies_ms.append(turn.latency_ms)
        if turn.usage.prompt_tokens is not None:
            self.prompt_tokens.append(turn.usage.prompt_tokens)
        if turn.usage.completion_tokens is not None:
            self.completion_tokens.append(turn.usage.completion_tokens)
        if turn.usage.cached_tokens is not None:
            self.cached_tokens.append(turn.usage.cached_tokens)

    def add_topics(self, topic_ids: Sequence[str]) -> None:
        for topic_id in topic_ids:
            if topic_id not in self.retrieved_topic_ids:
                self.retrieved_topic_ids.append(topic_id)

    def usage(self) -> ProviderUsage:
        return ProviderUsage(
            prompt_tokens=sum(self.prompt_tokens) if self.prompt_tokens else None,
            completion_tokens=sum(self.completion_tokens) if self.completion_tokens else None,
            cached_tokens=sum(self.cached_tokens) if self.cached_tokens else None,
        )


def _reject_duplicate_tool_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _HarnessFailure("tool_arguments_invalid")
        result[key] = value
    return result


def _sum_or_none(values: Sequence[int]) -> int | None:
    return sum(values) if values else None


def _safe_model_code(adapter: object) -> str:
    config = getattr(adapter, "config", None)
    value = getattr(config, "model", "minimax-m3")
    return value if isinstance(value, str) and _MODEL_CODE_RE.fullmatch(value) else "configured_model"


class SupportAgentHarness:
    def __init__(
        self,
        *,
        policy: PolicySnapshot,
        knowledge_store: SupportKnowledgeStore,
        knowledge: KnowledgeSnapshot,
        session_store: SupportSessionStore,
        rate_limiter: OwnerRateLimiter,
        in_flight_guard: SessionInFlightGuard,
        adapter: object,
        context_builder: SupportContextBuilder | None = None,
        max_concurrency: int = 2,
        concurrency_wait_seconds: float = 0.25,
        run_deadline_seconds: float = 25.0,
        provider_timeout_seconds: float = 12.0,
        pre_retrieval_limit: int = 3,
        tool_result_limit: int = 5,
        monotonic: Callable[[], float] | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        jitter: Callable[[], float] = random.random,
        trace_callback: Callable[[SupportAgentTrace], object] | None = None,
    ) -> None:
        if (
            type(max_concurrency) is not int
            or not 1 <= max_concurrency <= 2
            or not math.isfinite(concurrency_wait_seconds)
            or not 0.001 <= concurrency_wait_seconds <= 0.25
            or not math.isfinite(run_deadline_seconds)
            or not 0.1 <= run_deadline_seconds <= 25.0
            or not math.isfinite(provider_timeout_seconds)
            or not 0.1 <= provider_timeout_seconds <= 12.0
            or type(pre_retrieval_limit) is not int
            or not 1 <= pre_retrieval_limit <= 3
            or type(tool_result_limit) is not int
            or not 1 <= tool_result_limit <= 5
        ):
            raise ValueError("harness_config_invalid")
        self.policy = policy
        self.knowledge_store = knowledge_store
        self.knowledge = knowledge
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
        self.pre_retrieval_limit = pre_retrieval_limit
        self.tool_result_limit = tool_result_limit
        self.monotonic = monotonic or time.monotonic
        self.sleep = sleep
        self.jitter = jitter
        self.trace_callback = trace_callback
        self.model_code = _safe_model_code(adapter)

    @property
    def available_concurrency(self) -> int:
        return int(getattr(self.process_semaphore, "_value", 0))

    def _remaining(self, started: float) -> float:
        return self.run_deadline_seconds - max(0.0, self.monotonic() - started)

    async def _provider_call(
        self,
        context: AgentContext,
        stats: _RunStats,
        started: float,
    ) -> ModelTurn:
        if stats.provider_request_count >= 2:
            raise _HarnessFailure("provider_request_budget_exhausted")
        remaining = self._remaining(started)
        if remaining < _MIN_PROVIDER_WINDOW_SECONDS:
            raise _HarnessFailure("deadline_exhausted")
        request_timeout = min(self.provider_timeout_seconds, remaining)
        stats.provider_request_count += 1
        turn = await self.adapter.complete(
            messages=context.messages,
            tools=context.tools,
            tool_choice=context.tool_choice,
            request_timeout=request_timeout,
        )
        if not isinstance(turn, ModelTurn):
            raise _HarnessFailure("provider_turn_invalid")
        stats.add_turn(turn)
        return turn

    def _pre_retrieve(self, message: str, session: SessionState | None) -> tuple[KnowledgeHit, ...]:
        selected: list[KnowledgeHit] = []
        if session is not None and session.state.issue_topic_id in self.knowledge.topics_by_id:
            pinned = self.knowledge.topics_by_id[session.state.issue_topic_id]
            selected.append(replace(pinned, score=2_147_483_647))
        remaining = self.pre_retrieval_limit - len(selected)
        if remaining and len(message) >= 2:
            selected.extend(
                self.knowledge_store.search(
                    message,
                    limit=remaining,
                    exclude_ids=tuple(item.topic_id for item in selected),
                )
            )
        return tuple(selected)

    @staticmethod
    def _validate_tool_turn(turn: ModelTurn) -> tuple[ToolCall, str]:
        if turn.finish_reason != "tool_calls":
            raise _HarnessFailure("tool_finish_reason_invalid")
        if len(turn.tool_calls) != 1:
            raise _HarnessFailure("tool_call_count_invalid")
        call = turn.tool_calls[0]
        if call.name != _TOOL_NAME:
            raise _HarnessFailure("tool_name_invalid")
        if not _TOOL_CALL_ID_RE.fullmatch(call.call_id):
            raise _HarnessFailure("tool_call_id_invalid")
        try:
            arguments = json.loads(call.arguments_json, object_pairs_hook=_reject_duplicate_tool_keys)
        except _HarnessFailure:
            raise
        except (json.JSONDecodeError, TypeError) as exc:
            raise _HarnessFailure("tool_arguments_invalid") from exc
        if not isinstance(arguments, dict) or set(arguments) != {"query"}:
            raise _HarnessFailure("tool_arguments_invalid")
        query = arguments["query"]
        if not isinstance(query, str) or not 2 <= len(query) <= 200:
            raise _HarnessFailure("tool_arguments_invalid")
        expected_message = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": call.call_id,
                    "type": "function",
                    "function": {"name": call.name, "arguments": call.arguments_json},
                }
            ],
        }
        if dict(turn.normalized_assistant_message) != expected_message:
            raise _HarnessFailure("tool_replay_invalid")
        boundary = classify_support_input(query)
        if boundary.disposition is not InputDisposition.CONTINUE or boundary.model_text != query:
            raise _HarnessFailure("tool_query_unsafe")
        return call, query

    def _validate_final(self, turn: ModelTurn, supplied_topic_ids: Sequence[str]) -> ValidatedAgentAnswer:
        if turn.tool_calls:
            raise _HarnessFailure("final_tool_call_forbidden")
        if turn.finish_reason != "stop":
            raise _HarnessFailure("final_finish_reason_invalid")
        if not isinstance(turn.content, str):
            raise _HarnessFailure("final_content_missing")
        try:
            return validate_agent_output(turn.content, supplied_topic_ids, self.policy)
        except SafetyValidationError as exc:
            raise _HarnessFailure(str(exc)) from exc

    async def _execute(
        self,
        request: SupportAgentRequest,
        boundary: InputBoundaryResult,
        stats: _RunStats,
        started: float,
    ) -> ValidatedAgentAnswer:
        session = self.session_store.get(request.session_scope.internal_session_key, request.now)
        pre_hits = self._pre_retrieve(boundary.model_text, session)
        first_context = self.context_builder.build(
            policy=self.policy,
            knowledge=self.knowledge,
            session=session,
            redacted_message=boundary.model_text,
            retrieved_hits=pre_hits,
            tool_choice="auto",
        )
        stats.stable_prefix_hash = first_context.stable_prefix_hash
        stats.add_topics(first_context.supplied_topic_ids)

        try:
            first_turn = await self._provider_call(first_context, stats, started)
        except ProviderCallError as exc:
            stats.error_code = exc.code
            if not exc.retryable or stats.provider_request_count >= 2:
                raise _HarnessFailure(exc.code) from exc
            remaining = self._remaining(started)
            backoff = min(0.05 + max(0.0, min(float(self.jitter()), 1.0)) * 0.05, max(0.0, remaining - 0.1))
            if remaining - backoff < _MIN_PROVIDER_WINDOW_SECONDS:
                raise _HarnessFailure("deadline_exhausted") from exc
            if backoff:
                await self.sleep(backoff)
            stats.retry_count = 1
            try:
                retried_turn = await self._provider_call(first_context, stats, started)
            except ProviderCallError as retry_exc:
                stats.error_code = retry_exc.code
                raise _HarnessFailure(retry_exc.code) from retry_exc
            if retried_turn.tool_calls or retried_turn.finish_reason == "tool_calls":
                raise _HarnessFailure("retry_tool_forbidden")
            return self._validate_final(retried_turn, first_context.supplied_topic_ids)

        if first_turn.tool_calls or first_turn.finish_reason == "tool_calls":
            call, query = self._validate_tool_turn(first_turn)
            stats.tool_call_count = 1
            try:
                tool_hits = self.knowledge_store.search(
                    query,
                    limit=self.tool_result_limit,
                    exclude_ids=first_context.supplied_topic_ids,
                )
                tool_result = self.knowledge_store.render_hits(tool_hits)
                rendered = json.loads(tool_result)
                rendered_topics = rendered.get("topics") if isinstance(rendered, dict) else None
                if not isinstance(rendered_topics, list) or not rendered_topics:
                    raise _HarnessFailure("tool_no_results")
                tool_topic_ids = tuple(
                    item["id"]
                    for item in rendered_topics
                    if isinstance(item, dict) and isinstance(item.get("id"), str)
                )
                if len(tool_topic_ids) != len(rendered_topics):
                    raise _HarnessFailure("tool_result_invalid")
            except _HarnessFailure:
                raise
            except Exception as exc:
                raise _HarnessFailure("tool_execution_failed") from exc
            stats.add_topics(tool_topic_ids)
            continuation = self.context_builder.build(
                policy=self.policy,
                knowledge=self.knowledge,
                session=session,
                redacted_message=boundary.model_text,
                retrieved_hits=(),
                tool_choice="none",
                continuation=ToolContinuation(
                    assistant_message=first_turn.normalized_assistant_message,
                    tool_call_id=call.call_id,
                    tool_name=call.name,
                    tool_result=tool_result,
                    supplied_topic_ids=tool_topic_ids,
                ),
            )
            try:
                final_turn = await self._provider_call(continuation, stats, started)
            except ProviderCallError as exc:
                stats.error_code = exc.code
                raise _HarnessFailure(exc.code) from exc
            if final_turn.tool_calls or final_turn.finish_reason == "tool_calls":
                raise _HarnessFailure("second_tool_call_forbidden")
            return self._validate_final(final_turn, continuation.supplied_topic_ids)

        return self._validate_final(first_turn, first_context.supplied_topic_ids)

    def _finish(
        self,
        *,
        request: SupportAgentRequest,
        started: float,
        stats: _RunStats,
        status: str,
        reply: str,
        source_topic_ids: tuple[str, ...] = (),
        session_state: SafeSessionState | None = None,
        escalation_reason: str | None = None,
    ) -> SupportAgentResult:
        latency_ms = max(0, int(round(max(0.0, self.monotonic() - started) * 1000)))
        result = SupportAgentResult(
            status=status,
            reply=reply,
            source_topic_ids=source_topic_ids,
            session_state=session_state,
            provider_request_count=stats.provider_request_count,
            tool_call_count=stats.tool_call_count,
            retry_count=stats.retry_count,
            escalation_reason=escalation_reason,
            usage=stats.usage(),
            latency_ms=latency_ms,
        )
        if self.trace_callback is not None:
            scope = request.session_scope
            internal_key = getattr(scope, "internal_session_key", "")
            session_hash = (
                hashlib.sha256(internal_key.encode("ascii")).hexdigest()
                if isinstance(internal_key, str) and _HASH_RE.fullmatch(internal_key)
                else "0" * 64
            )
            trace = SupportAgentTrace(
                run_id=secrets.token_hex(8),
                surface=request.surface if request.surface in _SURFACES else "invalid",
                session_id_hash=session_hash,
                provider="xcody",
                model=self.model_code,
                policy_sha256=self.policy.sha256,
                knowledge_version=self.knowledge.version,
                knowledge_sha256=self.knowledge.sha256,
                stable_prefix_hash=stats.stable_prefix_hash,
                provider_request_count=stats.provider_request_count,
                tool_call_count=stats.tool_call_count,
                retry_count=stats.retry_count,
                retrieved_topic_ids=tuple(stats.retrieved_topic_ids),
                redaction_categories=stats.redaction_categories,
                prompt_tokens=_sum_or_none(stats.prompt_tokens),
                completion_tokens=_sum_or_none(stats.completion_tokens),
                cached_tokens=_sum_or_none(stats.cached_tokens),
                provider_latencies_ms=tuple(stats.provider_latencies_ms),
                latency_ms=latency_ms,
                error_code=stats.error_code,
                status=status,
                escalation_reason=escalation_reason,
            )
            try:
                self.trace_callback(trace)
            except Exception:
                logger.warning("support agent trace callback failed code=trace_callback_error")
        return result

    async def run(self, request: SupportAgentRequest) -> SupportAgentResult:
        started = self.monotonic()
        stats = _RunStats()
        if not isinstance(request, SupportAgentRequest):
            raise TypeError("support_agent_request_invalid")

        boundary = classify_support_input(request.message)
        stats.redaction_categories = tuple(sorted(boundary.category_counts.items()))
        if boundary.disposition is InputDisposition.HARD_REJECT:
            return self._finish(
                request=request,
                started=started,
                stats=stats,
                status="fallback",
                reply=SAFE_FALLBACK_REPLY,
                escalation_reason=boundary.escalation_reason or "sensitive_input",
            )
        if boundary.disposition is InputDisposition.LOCAL_ESCALATE:
            return self._finish(
                request=request,
                started=started,
                stats=stats,
                status="escalate",
                reply=SAFE_FALLBACK_REPLY,
                escalation_reason=boundary.escalation_reason or "local_escalation",
            )

        scope = request.session_scope
        if (
            not isinstance(scope, SessionScope)
            or request.surface not in _SURFACES
            or scope.surface != request.surface
            or not _HASH_RE.fullmatch(scope.owner_scope_hash)
            or not _HASH_RE.fullmatch(scope.internal_session_key)
            or not isinstance(request.now, (int, float))
            or not math.isfinite(float(request.now))
            or request.now < 0
        ):
            return self._finish(
                request=request,
                started=started,
                stats=stats,
                status="fallback",
                reply=SAFE_FALLBACK_REPLY,
                escalation_reason="request_scope_invalid",
            )
        if not self.rate_limiter.allow(scope.owner_scope_hash, request.now):
            return self._finish(
                request=request,
                started=started,
                stats=stats,
                status="fallback",
                reply=SAFE_FALLBACK_REPLY,
                escalation_reason="owner_rate_limited",
            )
        if not await self.in_flight_guard.acquire(scope.internal_session_key):
            return self._finish(
                request=request,
                started=started,
                stats=stats,
                status="fallback",
                reply=SAFE_FALLBACK_REPLY,
                escalation_reason="session_busy",
            )

        process_acquired = False
        try:
            try:
                await asyncio.wait_for(
                    self.process_semaphore.acquire(),
                    timeout=min(self.concurrency_wait_seconds, max(0.001, self._remaining(started))),
                )
                process_acquired = True
            except asyncio.TimeoutError:
                return self._finish(
                    request=request,
                    started=started,
                    stats=stats,
                    status="fallback",
                    reply=SAFE_FALLBACK_REPLY,
                    escalation_reason="process_busy",
                )

            try:
                answer = await self._execute(request, boundary, stats, started)
                self.session_store.append(
                    scope.internal_session_key,
                    (
                        StoredMessage(role="user", content=boundary.model_text),
                        StoredMessage(role="assistant", content=answer.reply),
                    ),
                    answer.session_state,
                    request.now,
                )
                return self._finish(
                    request=request,
                    started=started,
                    stats=stats,
                    status=answer.status,
                    reply=answer.reply,
                    source_topic_ids=answer.source_topic_ids,
                    session_state=answer.session_state,
                    escalation_reason="model_escalation" if answer.status == "escalate" else None,
                )
            except _HarnessFailure as exc:
                stats.error_code = stats.error_code or exc.code
                return self._finish(
                    request=request,
                    started=started,
                    stats=stats,
                    status="fallback",
                    reply=SAFE_FALLBACK_REPLY,
                    escalation_reason=exc.code,
                )
            except Exception:
                stats.error_code = "harness_internal_error"
                logger.warning("support agent run failed code=harness_internal_error")
                return self._finish(
                    request=request,
                    started=started,
                    stats=stats,
                    status="fallback",
                    reply=SAFE_FALLBACK_REPLY,
                    escalation_reason="harness_internal_error",
                )
        finally:
            if process_acquired:
                self.process_semaphore.release()
            await self.in_flight_guard.release(scope.internal_session_key)
