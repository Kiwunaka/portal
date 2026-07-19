import asyncio
import json
import logging
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))


CASES = (
    # name, input_mode, retrieval, provider_plan, store_plan, calls, status, origin, reason
    ("hard_reject", "hard_reject", "none", "unused", "ok", 0, "escalate", "human_transfer", "sensitive_input"),
    ("local_escalate", "local_escalate", "none", "unused", "ok", 0, "escalate", "human_transfer", "out_of_scope"),
    ("explicit_human", "explicit_human", "none", "unused", "ok", 0, "escalate", "human_transfer", "human_requested"),
    ("fixed_transfer_write_failure", "explicit_human", "none", "unused", "write_error", 0, "escalate", "human_transfer", "session_write_failed"),
    ("sticky_escalation", "safe", "confident", "unused", "sticky", 0, "escalate", "human_transfer", "escalation_already_requested"),
    ("second_failure", "safe_negative", "confident", "unused", "ok", 0, "escalate", "human_transfer", "repeated_unsuccessful"),
    ("rate_limited", "safe", "confident", "unused", "rate_limited", 0, "fallback", "human_transfer", "owner_rate_limited"),
    ("session_busy", "safe", "confident", "unused", "session_busy", 0, "fallback", "human_transfer", "session_busy"),
    ("process_busy", "safe", "confident", "unused", "process_busy", 0, "fallback", "human_transfer", "process_busy"),
    ("session_read_failure", "safe", "confident", "unused", "read_error", 0, "fallback", "human_transfer", "session_read_failed"),
    ("no_topic", "safe", "none", "unused", "ok", 0, "escalate", "human_transfer", "missing_source"),
    ("context_overflow", "safe", "confident", "unused", "context_error", 0, "fallback", "human_transfer", "provider_request_too_large"),
    ("model_confident", "safe", "confident", "answer", "ok", 1, "answer", "model", None),
    ("model_candidate", "safe", "candidate", "answer", "ok", 1, "answer", "model", None),
    ("model_escalate", "safe", "confident", "escalate", "ok", 1, "escalate", "human_transfer", "model_escalation"),
    ("timeout_confident", "safe", "confident", "timeout", "ok", 1, "answer", "grounded_local", None),
    ("http_400_confident", "safe", "confident", "http_400", "ok", 1, "answer", "grounded_local", None),
    ("invalid_json_confident", "safe", "confident", "invalid_json", "ok", 1, "answer", "grounded_local", None),
    ("unsafe_output_confident", "safe", "confident", "unsafe", "ok", 1, "answer", "grounded_local", None),
    ("unsupported_action_confident", "safe", "confident", "unsupported_action", "ok", 1, "answer", "grounded_local", None),
    ("timeout_candidate", "safe", "candidate", "timeout", "ok", 1, "fallback", "human_transfer", "provider_timeout"),
    ("fingerprint_missing", "safe", "candidate", "invalid_json", "ok", 1, "fallback", "human_transfer", "agent_output_json_invalid"),
    ("post_answer_write_failure", "safe", "confident", "answer", "write_error", 1, "fallback", "human_transfer", "session_write_failed"),
)

INPUT_MESSAGES = {
    "hard_reject": "vless://private-profile-value",
    "local_escalate": "Проверьте мой аккаунт и базу данных",
    "explicit_human": "Соедините меня с живым оператором поддержки",
    "safe": "POKROV подключён, но интернета нет.",
    "safe_negative": "Не помогло, всё так же.",
}
PROVIDER_PLANS = frozenset(
    {
        "unused",
        "answer",
        "escalate",
        "timeout",
        "http_400",
        "invalid_json",
        "unsafe",
        "unsupported_action",
        "metadata",
        "runtime_error",
    }
)
STORE_PLANS = frozenset(
    {
        "ok",
        "write_error",
        "sticky",
        "rate_limited",
        "session_busy",
        "process_busy",
        "read_error",
        "context_error",
    }
)
RETRIEVAL_PLANS = frozenset({"confident", "candidate", "none"})

MODEL_REPLY = (
    "Коротко\nПроверьте подключение.\n\n"
    "Что сделать\nПереподключитесь.\n\n"
    "Если не поможет\nНапишите в поддержку."
)


class _Adapter:
    def __init__(self, plan: str, *, secret: str = "") -> None:
        assert plan in PROVIDER_PLANS
        self.plan = plan
        self.secret = secret
        self.call_count = 0
        self.config = SimpleNamespace(model="minimax-m3", reasoning_effort="medium")

    async def complete_synthesis(self, *, messages, request_timeout):
        from support_agent_provider import ProviderCallError, ProviderUsage, SynthesisTurn

        self.call_count += 1
        if self.plan == "unused":
            raise AssertionError("unused_adapter_called")
        if self.plan == "timeout":
            raise ProviderCallError(retryable=True, code="provider_timeout", status=0)
        if self.plan == "http_400":
            raise ProviderCallError(retryable=False, code="provider_http_error", status=400)
        if self.plan == "runtime_error":
            raise RuntimeError(self.secret)
        if self.plan == "invalid_json":
            content = "not-json"
        elif self.plan == "unsafe":
            content = json.dumps(
                {"schema_version": "1", "status": "answer", "reply": "Ответ vless://secret"},
                ensure_ascii=False,
            )
        elif self.plan == "unsupported_action":
            content = json.dumps(
                {
                    "schema_version": "1",
                    "status": "answer",
                    "reply": "Удалите старые VPN-профили и очистите кэш.",
                },
                ensure_ascii=False,
            )
        elif self.plan == "metadata":
            content = json.dumps(
                {
                    "schema_version": "1",
                    "status": "answer",
                    "reply": MODEL_REPLY,
                    "source_topic_ids": ["connected_no_internet"],
                },
                ensure_ascii=False,
            )
        else:
            content = json.dumps(
                {
                    "schema_version": "1",
                    "status": "escalate" if self.plan == "escalate" else "answer",
                    "reply": MODEL_REPLY,
                },
                ensure_ascii=False,
            )
        return SynthesisTurn(
            content=content,
            finish_reason="stop",
            usage=ProviderUsage(prompt_tokens=100, completion_tokens=20, cached_tokens=80),
            latency_ms=37,
        )


class _Store:
    def __init__(self, plan: str) -> None:
        from support_agent_sessions import SupportSessionStore

        assert plan in STORE_PLANS
        self.plan = plan
        self.real = SupportSessionStore()
        self.append_calls = 0

    def get(self, key, now):
        if self.plan == "read_error":
            raise RuntimeError("private read failure")
        return self.real.get(key, now)

    def append(self, key, messages, state, now):
        self.append_calls += 1
        if self.plan == "write_error":
            raise RuntimeError("private write failure")
        return self.real.append(key, messages, state, now)


class _RateLimiter:
    def __init__(self, allowed: bool) -> None:
        self.allowed = allowed

    def allow(self, owner_scope_hash, now):
        return self.allowed


class _Guard:
    def __init__(self, *, busy: bool = False) -> None:
        self.busy = busy
        self.active: set[str] = set()
        self.release_count = 0

    @property
    def in_flight_count(self) -> int:
        return len(self.active)

    async def acquire(self, key):
        if self.busy:
            return False
        self.active.add(key)
        return True

    async def release(self, key):
        self.active.discard(key)
        self.release_count += 1


class _BusySemaphore:
    _value = 0

    async def acquire(self):
        raise asyncio.TimeoutError

    def release(self):
        raise AssertionError("busy semaphore was never acquired")


class _Grounding:
    def __init__(self, decision, delegate) -> None:
        self.decision = decision
        self.delegate = delegate
        self.render_calls = 0

    def select(self, redacted_message, session):
        return self.decision

    def render_local(self, decision, policy):
        self.render_calls += 1
        return self.delegate.render_local(decision, policy)


class _ContextBuilder:
    def __init__(self, *, fail: bool = False) -> None:
        from support_agent_context import SupportContextBuilder

        self.delegate = SupportContextBuilder()
        self.fail = fail

    def build_synthesis(self, **kwargs):
        from support_agent_context import ContextBuildError

        if self.fail:
            raise ContextBuildError("provider_request_too_large")
        return self.delegate.build_synthesis(**kwargs)


class _StepClock:
    def __init__(self) -> None:
        self.value = 10.0

    def __call__(self) -> float:
        self.value += 0.01
        return self.value


@dataclass
class HarnessCase:
    harness: object
    request: object
    adapter: _Adapter
    session_store: _Store
    guard: _Guard
    grounding: _Grounding
    traces: list[object]


def _snapshots_and_decisions():
    from support_agent_grounding import (
        RETRIEVER_RULES_SHA256,
        RetrievalDecision,
        RetrievalDisposition,
        SupportGroundingEngine,
    )
    from support_agent_knowledge import SupportKnowledgeStore
    from support_agent_policy import SupportAgentPolicyStore

    policy = SupportAgentPolicyStore().load(REPO_ROOT / "shared" / "support-agent-policy.json")
    store = SupportKnowledgeStore()
    knowledge = store.load(REPO_ROOT / "shared" / "support-ai-knowledge.json")
    engine = SupportGroundingEngine(store, knowledge)
    confident = engine.select("POKROV подключён, но интернета нет.", None)
    candidate_topics = store.search("импортировать профиль в приложение", limit=3)
    candidate = RetrievalDecision(
        disposition=RetrievalDisposition.CANDIDATE,
        context_topics=candidate_topics,
        context_topic_ids=tuple(hit.topic_id for hit in candidate_topics),
        grounding_topic_id=None,
        retriever_sha256=RETRIEVER_RULES_SHA256,
    )
    none = RetrievalDecision(
        disposition=RetrievalDisposition.NONE,
        context_topics=(),
        context_topic_ids=(),
        grounding_topic_id=None,
        retriever_sha256=RETRIEVER_RULES_SHA256,
    )
    return policy, knowledge, engine, {
        "confident": confident,
        "candidate": candidate,
        "none": none,
    }


@pytest.fixture
def harness_case_factory():
    def factory(
        *,
        name: str,
        input_mode: str,
        retrieval: str,
        provider_plan: str,
        store_plan: str,
        secret: str = "",
        clock=None,
    ) -> HarnessCase:
        from support_agent_harness import SupportAgentHarness, SupportAgentRequest
        from support_agent_safety import SafeSessionState
        from support_agent_sessions import SessionScope, StoredMessage

        assert isinstance(name, str) and name
        assert input_mode in INPUT_MESSAGES
        assert retrieval in RETRIEVAL_PLANS
        assert provider_plan in PROVIDER_PLANS
        assert store_plan in STORE_PLANS
        policy, knowledge, engine, decisions = _snapshots_and_decisions()
        adapter = _Adapter(provider_plan, secret=secret)
        store = _Store(store_plan)
        guard = _Guard(busy=store_plan == "session_busy")
        grounding = _Grounding(decisions[retrieval], engine)
        traces: list[object] = []
        owner_hash = "1" * 64
        internal_key = "2" * 64
        scope = SessionScope(
            surface="app",
            owner_scope_hash=owner_hash,
            internal_session_key=internal_key,
            client_session_id="A" * 16,
        )
        if store_plan == "sticky":
            store.real.append(
                internal_key,
                (
                    StoredMessage(role="user", content="Прошлый вопрос"),
                    StoredMessage(role="assistant", content="Прошлый ответ"),
                ),
                SafeSessionState(
                    issue_topic_id="connected_no_internet",
                    attempted_steps=(),
                    last_outcome="not_reported",
                    escalation_requested=True,
                    unsuccessful_turns=0,
                ),
                99.0,
            )
        if input_mode == "safe_negative":
            store.real.append(
                internal_key,
                (
                    StoredMessage(role="user", content="Первый шаг не помог"),
                    StoredMessage(role="assistant", content="Безопасный ответ"),
                ),
                SafeSessionState(
                    issue_topic_id="connected_no_internet",
                    attempted_steps=("reconnect",),
                    last_outcome="unchanged",
                    escalation_requested=False,
                    unsuccessful_turns=1,
                ),
                99.0,
            )
        harness = SupportAgentHarness(
            policy=policy,
            knowledge=knowledge,
            grounding_engine=grounding,
            session_store=store,
            rate_limiter=_RateLimiter(store_plan != "rate_limited"),
            in_flight_guard=guard,
            adapter=adapter,
            context_builder=_ContextBuilder(fail=store_plan == "context_error"),
            monotonic=clock,
            trace_callback=traces.append,
        )
        if store_plan == "process_busy":
            harness.process_semaphore = _BusySemaphore()
        request = SupportAgentRequest(
            surface="app",
            session_scope=scope,
            message=INPUT_MESSAGES[input_mode],
            now=100.0,
        )
        return HarnessCase(
            harness=harness,
            request=request,
            adapter=adapter,
            session_store=store,
            guard=guard,
            grounding=grounding,
            traces=traces,
        )

    return factory


@pytest.mark.parametrize(
    "name,input_mode,retrieval,provider_plan,store_plan,calls,status,origin,reason",
    CASES,
)
def test_exhaustive_zero_one_call_truth_table(
    name,
    input_mode,
    retrieval,
    provider_plan,
    store_plan,
    calls,
    status,
    origin,
    reason,
    harness_case_factory,
):
    case = harness_case_factory(
        name=name,
        input_mode=input_mode,
        retrieval=retrieval,
        provider_plan=provider_plan,
        store_plan=store_plan,
    )
    result = asyncio.run(case.harness.run(case.request))
    assert result.provider_request_count == calls
    assert result.status == status
    assert result.answer_origin == origin
    assert result.escalation_reason == reason
    assert case.adapter.call_count == calls
    assert case.adapter.call_count <= 1


def test_factory_rejects_unknown_closed_plans(harness_case_factory) -> None:
    with pytest.raises(AssertionError):
        harness_case_factory(
            name="unknown",
            input_mode="safe",
            retrieval="confident",
            provider_plan="second_call",
            store_plan="ok",
        )


def test_code_owned_provenance_and_candidate_state_are_not_model_owned(
    harness_case_factory,
) -> None:
    from support_agent_safety import SafeSessionState
    from support_agent_sessions import StoredMessage

    candidate = harness_case_factory(
        name="candidate-state",
        input_mode="safe",
        retrieval="candidate",
        provider_plan="answer",
        store_plan="ok",
    )
    candidate.session_store.real.append(
        candidate.request.session_scope.internal_session_key,
        (
            StoredMessage(role="user", content="Старый вопрос"),
            StoredMessage(role="assistant", content="Старый ответ"),
        ),
        SafeSessionState(
            issue_topic_id="connected_no_internet",
            attempted_steps=("reconnect",),
            last_outcome="not_reported",
            escalation_requested=False,
            unsuccessful_turns=0,
        ),
        99.0,
    )
    candidate_result = asyncio.run(candidate.harness.run(candidate.request))
    assert candidate_result.context_topic_ids == candidate.grounding.decision.context_topic_ids
    assert candidate_result.grounding_topic_id is None
    assert candidate_result.session_state.issue_topic_id == "connected_no_internet"

    confident = harness_case_factory(
        name="confident-provenance",
        input_mode="safe",
        retrieval="confident",
        provider_plan="answer",
        store_plan="ok",
    )
    confident_result = asyncio.run(confident.harness.run(confident.request))
    assert confident_result.grounding_topic_id == "connected_no_internet"
    assert confident_result.grounding_topic_id in confident_result.context_topic_ids


def test_resolved_followup_is_acknowledged_by_code_without_provider_or_promotion(
    harness_case_factory,
) -> None:
    from support_agent_safety import SafeSessionState
    from support_agent_sessions import StoredMessage

    case = harness_case_factory(
        name="resolved-code-owned",
        input_mode="safe",
        retrieval="confident",
        provider_plan="unused",
        store_plan="ok",
    )
    case.session_store.real.append(
        case.request.session_scope.internal_session_key,
        (
            StoredMessage(role="user", content="После продления срок не обновился."),
            StoredMessage(role="assistant", content="Обновите доступ в приложении."),
        ),
        SafeSessionState(
            issue_topic_id="refresh_after_renewal",
            attempted_steps=("refresh_access",),
            last_outcome="not_reported",
            escalation_requested=False,
            unsuccessful_turns=0,
        ),
        99.0,
    )
    case.request = replace(case.request, message="Новый срок появился, всё решено.")

    result = asyncio.run(case.harness.run(case.request))

    assert result.status == "answer"
    assert result.answer_origin == "code_owned"
    assert result.provider_request_count == 0
    assert case.adapter.call_count == 0
    assert result.session_state.issue_topic_id == "refresh_after_renewal"
    assert result.session_state.last_outcome == "resolved"
    assert "бонус" not in result.reply.casefold()


def test_mixed_resolution_and_new_failure_is_not_closed_by_code(
    harness_case_factory,
) -> None:
    case = harness_case_factory(
        name="mixed-resolution",
        input_mode="safe",
        retrieval="confident",
        provider_plan="answer",
        store_plan="ok",
    )
    case.request = replace(
        case.request,
        message="Подключение заработало, но один сайт не открывается.",
    )

    result = asyncio.run(case.harness.run(case.request))

    assert result.answer_origin == "model"
    assert result.provider_request_count == 1
    assert case.adapter.call_count == 1


def test_model_metadata_is_rejected_and_model_escalation_never_renders_local(
    harness_case_factory,
) -> None:
    metadata = harness_case_factory(
        name="metadata",
        input_mode="safe",
        retrieval="confident",
        provider_plan="metadata",
        store_plan="ok",
    )
    metadata_result = asyncio.run(metadata.harness.run(metadata.request))
    assert metadata_result.answer_origin == "grounded_local"
    assert metadata.grounding.render_calls == 1

    escalation = harness_case_factory(
        name="escalate-no-local",
        input_mode="safe",
        retrieval="confident",
        provider_plan="escalate",
        store_plan="ok",
    )
    escalation_result = asyncio.run(escalation.harness.run(escalation.request))
    assert escalation_result.answer_origin == "human_transfer"
    assert escalation_result.reply != MODEL_REPLY
    assert escalation.grounding.render_calls == 0


def test_transfer_persistence_is_exact_and_sensitive_or_out_of_scope_is_not_stored(
    harness_case_factory,
) -> None:
    from support_agent_harness import SAFE_FALLBACK_REPLY

    human = harness_case_factory(
        name="human-store",
        input_mode="explicit_human",
        retrieval="none",
        provider_plan="unused",
        store_plan="ok",
    )
    asyncio.run(human.harness.run(human.request))
    stored = human.session_store.real.get(
        human.request.session_scope.internal_session_key,
        101.0,
    )
    assert [(item.role, item.content) for item in stored.messages] == [
        ("user", INPUT_MESSAGES["explicit_human"]),
        ("assistant", SAFE_FALLBACK_REPLY),
    ]
    assert stored.state.escalation_requested is True

    for input_mode, reason in (("hard_reject", "sensitive"), ("local_escalate", "scope")):
        case = harness_case_factory(
            name=reason,
            input_mode=input_mode,
            retrieval="none",
            provider_plan="unused",
            store_plan="ok",
        )
        asyncio.run(case.harness.run(case.request))
        assert case.session_store.real.get(
            case.request.session_scope.internal_session_key,
            101.0,
        ) is None


def test_second_failure_and_write_failure_have_one_atomic_persistence_attempt(
    harness_case_factory,
) -> None:
    from support_agent_harness import SAFE_FALLBACK_REPLY

    repeated = harness_case_factory(
        name="repeat-store",
        input_mode="safe_negative",
        retrieval="confident",
        provider_plan="unused",
        store_plan="ok",
    )
    result = asyncio.run(repeated.harness.run(repeated.request))
    stored = repeated.session_store.real.get(
        repeated.request.session_scope.internal_session_key,
        101.0,
    )
    assert result.escalation_reason == "repeated_unsuccessful"
    assert [(item.role, item.content) for item in stored.messages[-2:]] == [
        ("user", INPUT_MESSAGES["safe_negative"]),
        ("assistant", SAFE_FALLBACK_REPLY),
    ]
    assert stored.state.escalation_requested is True
    assert repeated.session_store.append_calls == 1

    failed = harness_case_factory(
        name="write-once",
        input_mode="safe",
        retrieval="confident",
        provider_plan="answer",
        store_plan="write_error",
    )
    failed_result = asyncio.run(failed.harness.run(failed.request))
    assert failed_result.reply == SAFE_FALLBACK_REPLY
    assert failed_result.escalation_reason == "session_write_failed"
    assert failed.session_store.append_calls == 1
    assert failed.adapter.call_count == 1


def test_trace_is_numeric_bounded_and_contains_no_conversation_or_runtime_secret(
    harness_case_factory,
    caplog,
) -> None:
    secret = "sk-runtime-secret-must-not-escape"
    clock = _StepClock()
    case = harness_case_factory(
        name="runtime-secret",
        input_mode="safe",
        retrieval="confident",
        provider_plan="runtime_error",
        store_plan="ok",
        secret=secret,
        clock=clock,
    )
    caplog.set_level(logging.WARNING, logger="support_agent_harness")
    result = asyncio.run(case.harness.run(case.request))

    assert result.escalation_reason == "harness_internal_error"
    assert result.provider_request_count == 1
    assert len(case.traces) == 1
    trace = case.traces[0]
    trace_text = repr(trace)
    assert trace.error_code == "harness_internal_error"
    assert trace.provider_request_count == 1
    assert isinstance(trace.queue_latency_ms, int)
    assert isinstance(trace.latency_ms, int)
    assert trace.provider_latency_ms is None
    assert trace.input_redaction_counts == tuple(sorted(trace.input_redaction_counts))
    assert trace.output_redaction_counts == tuple(sorted(trace.output_redaction_counts))
    assert all(type(count) is int and count >= 0 for _, count in trace.input_redaction_counts)
    for forbidden in (
        secret,
        case.request.message,
        case.request.session_scope.client_session_id,
        MODEL_REPLY,
    ):
        assert forbidden not in trace_text
        assert forbidden not in repr(result)
        assert forbidden not in caplog.text


def test_guards_and_process_slots_release_on_failure_and_busy_paths(
    harness_case_factory,
) -> None:
    failure = harness_case_factory(
        name="release-runtime",
        input_mode="safe",
        retrieval="confident",
        provider_plan="runtime_error",
        store_plan="ok",
        secret="private",
    )
    asyncio.run(failure.harness.run(failure.request))
    assert failure.guard.in_flight_count == 0
    assert failure.guard.release_count == 1
    assert failure.harness.available_concurrency == 2

    busy = harness_case_factory(
        name="release-busy",
        input_mode="safe",
        retrieval="confident",
        provider_plan="unused",
        store_plan="process_busy",
    )
    asyncio.run(busy.harness.run(busy.request))
    assert busy.guard.in_flight_count == 0
    assert busy.guard.release_count == 1
