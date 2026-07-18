import asyncio
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))


def _snapshots():
    from support_agent_knowledge import SupportKnowledgeStore
    from support_agent_policy import SupportAgentPolicyStore

    policy = SupportAgentPolicyStore().load(REPO_ROOT / "shared" / "support-agent-policy.json")
    knowledge_store = SupportKnowledgeStore()
    knowledge = knowledge_store.load(REPO_ROOT / "shared" / "support-ai-knowledge.json")
    return policy, knowledge_store, knowledge


def _scope(owner: str = "owner-1", session_id: str = "abcdefghijklmnop"):
    from support_agent_sessions import SupportSessionResolver

    return SupportSessionResolver().resolve_app(owner, session_id)


def _usage(prompt: int = 10, completion: int = 2, cached: int | None = 8):
    from support_agent_provider import ProviderUsage

    return ProviderUsage(prompt_tokens=prompt, completion_tokens=completion, cached_tokens=cached)


def _final_turn(source_id: str, *, raw_content: str | None = None):
    from support_agent_provider import ModelTurn

    content = raw_content or json.dumps(
        {
            "schema_version": "1",
            "status": "answer",
            "reply": "Переподключитесь и проверьте доступ ещё раз.",
            "source_topic_ids": [source_id],
            "session_state": {
                "issue_topic_id": source_id,
                "attempted_steps": ["reconnect"],
                "last_outcome": "not_reported",
                "escalation_requested": False,
            },
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return ModelTurn(
        content=content,
        finish_reason="stop",
        tool_calls=(),
        normalized_assistant_message={"role": "assistant", "content": content},
        usage=_usage(),
        latency_ms=20,
    )


def _tool_turn(
    *,
    call_id: str = "call_1",
    name: str = "search_support_docs",
    arguments: str = '{"query":"private dns фильтр"}',
    parallel: bool = False,
    finish_reason: str = "tool_calls",
):
    from support_agent_provider import ModelTurn, ToolCall

    calls = [ToolCall(call_id=call_id, name=name, arguments_json=arguments)]
    raw_calls = [
        {
            "id": call_id,
            "type": "function",
            "function": {"name": name, "arguments": arguments},
        }
    ]
    if parallel:
        calls.append(ToolCall(call_id="call_2", name=name, arguments_json=arguments))
        raw_calls.append(
            {
                "id": "call_2",
                "type": "function",
                "function": {"name": name, "arguments": arguments},
            }
        )
    return ModelTurn(
        content=None,
        finish_reason=finish_reason,
        tool_calls=tuple(calls),
        normalized_assistant_message={"role": "assistant", "content": None, "tool_calls": raw_calls},
        usage=_usage(),
        latency_ms=20,
    )


class _SequenceAdapter:
    def __init__(self, outcomes, *, clock=None, advances=()) -> None:
        self.outcomes = list(outcomes)
        self.requests: list[dict[str, object]] = []
        self.clock = clock
        self.advances = list(advances)

    async def complete(self, *, messages, tools, tool_choice, request_timeout):
        self.requests.append(
            {
                "messages": tuple(messages),
                "tools": tuple(tools),
                "tool_choice": tool_choice,
                "request_timeout": request_timeout,
            }
        )
        if not self.outcomes:
            raise AssertionError("unexpected provider request")
        outcome = self.outcomes.pop(0)
        if self.clock is not None and self.advances:
            self.clock.value += self.advances.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


async def _no_sleep(_delay: float) -> None:
    return None


def _harness(adapter, *, trace_callback=None, **overrides):
    from support_agent_harness import SupportAgentHarness
    from support_agent_sessions import OwnerRateLimiter, SessionInFlightGuard, SupportSessionStore

    policy, knowledge_store, knowledge = _snapshots()
    session_store = overrides.pop("session_store", SupportSessionStore())
    guard = overrides.pop("in_flight_guard", SessionInFlightGuard())
    harness = SupportAgentHarness(
        policy=policy,
        knowledge_store=knowledge_store,
        knowledge=knowledge,
        session_store=session_store,
        rate_limiter=overrides.pop("rate_limiter", OwnerRateLimiter()),
        in_flight_guard=guard,
        adapter=adapter,
        sleep=_no_sleep,
        jitter=lambda: 0.0,
        trace_callback=trace_callback,
        **overrides,
    )
    return harness, session_store, guard, knowledge_store


def _run(harness, *, scope=None, message="Подключено, но интернета нет", now=100.0):
    from support_agent_harness import SupportAgentRequest

    return asyncio.run(
        harness.run(
            SupportAgentRequest(
                surface="app",
                session_scope=scope or _scope(),
                message=message,
                now=now,
            )
        )
    )


def test_fast_answer_is_validated_stored_and_traced_without_text() -> None:
    traces = []
    adapter = _SequenceAdapter([_final_turn("connected_no_internet")])
    harness, session_store, guard, _ = _harness(adapter, trace_callback=traces.append)
    scope = _scope()

    result = _run(harness, scope=scope)

    assert result.status == "answer"
    assert result.source_topic_ids == ("connected_no_internet",)
    assert result.provider_request_count == 1
    assert result.tool_call_count == 0
    assert result.retry_count == 0
    assert result.usage == _usage()
    stored = session_store.get(scope.internal_session_key, 101.0)
    assert stored is not None
    assert [item.role for item in stored.messages] == ["user", "assistant"]
    assert stored.messages[0].content == "Подключено, но интернета нет"
    assert stored.messages[1].content == result.reply
    assert guard.in_flight_count == 0
    assert harness.available_concurrency == 2
    assert len(traces) == 1
    trace_json = json.dumps(asdict(traces[0]), ensure_ascii=False)
    assert "Подключено, но интернета нет" not in trace_json
    assert result.reply not in trace_json
    assert scope.client_session_id not in trace_json


def test_one_transient_failure_uses_second_and_final_slot_without_tool() -> None:
    from support_agent_provider import ProviderCallError

    adapter = _SequenceAdapter(
        [
            ProviderCallError(retryable=True, code="provider_http_error", status=503),
            _final_turn("connected_no_internet"),
        ]
    )
    harness, _, guard, _ = _harness(adapter)

    result = _run(harness)

    assert result.status == "answer"
    assert result.provider_request_count == 2
    assert result.retry_count == 1
    assert result.tool_call_count == 0
    assert result.usage.prompt_tokens == 10
    assert [item["tool_choice"] for item in adapter.requests] == ["auto", "auto"]
    assert adapter.requests[0]["messages"] == adapter.requests[1]["messages"]
    assert guard.in_flight_count == 0


def test_retry_response_cannot_start_a_tool_path() -> None:
    from support_agent_provider import ProviderCallError

    adapter = _SequenceAdapter(
        [
            ProviderCallError(retryable=True, code="provider_timeout", status=0),
            _tool_turn(),
        ]
    )
    harness, session_store, _, knowledge_store = _harness(adapter)

    result = _run(harness)

    assert result.status == "fallback"
    assert result.escalation_reason == "retry_tool_forbidden"
    assert result.provider_request_count == 2
    assert result.retry_count == 1
    assert result.tool_call_count == 0
    assert session_store.get(_scope().internal_session_key, 101.0) is None
    assert len(knowledge_store.search("private dns фильтр", 5)) == 1


def test_one_tool_call_replays_exact_message_and_forces_final_turn() -> None:
    first = _tool_turn()
    adapter = _SequenceAdapter([first, _final_turn("private_dns_and_filters")])
    harness, _, guard, knowledge_store = _harness(adapter)
    pre_bodies = [hit.body for hit in knowledge_store.search("Подключено, но интернета нет", 3)]

    result = _run(harness)

    assert result.status == "answer"
    assert result.source_topic_ids == ("private_dns_and_filters",)
    assert result.provider_request_count == 2
    assert result.tool_call_count == 1
    assert result.retry_count == 0
    assert [item["tool_choice"] for item in adapter.requests] == ["auto", "none"]
    second_messages = adapter.requests[1]["messages"]
    assert second_messages[-2] == first.normalized_assistant_message
    assert second_messages[-1]["role"] == "tool"
    assert second_messages[-1]["tool_call_id"] == "call_1"
    assert second_messages[-1]["name"] == "search_support_docs"
    assert "private_dns_and_filters" in second_messages[-1]["content"]
    serialized_second = json.dumps(second_messages, ensure_ascii=False)
    assert all(body not in serialized_second for body in pre_bodies)
    assert guard.in_flight_count == 0


def test_tool_path_second_failure_never_retries() -> None:
    from support_agent_provider import ProviderCallError

    adapter = _SequenceAdapter(
        [
            _tool_turn(),
            ProviderCallError(retryable=True, code="provider_http_error", status=503),
        ]
    )
    harness, _, guard, _ = _harness(adapter)

    result = _run(harness)

    assert result.status == "fallback"
    assert result.escalation_reason == "provider_http_error"
    assert result.provider_request_count == 2
    assert result.tool_call_count == 1
    assert result.retry_count == 0
    assert len(adapter.requests) == 2
    assert guard.in_flight_count == 0


@pytest.mark.parametrize(
    ("turn", "reason"),
    (
        (_tool_turn(name="read_account"), "tool_name_invalid"),
        (_tool_turn(arguments='{"query":"dns","extra":true}'), "tool_arguments_invalid"),
        (_tool_turn(parallel=True), "tool_call_count_invalid"),
        (_tool_turn(call_id="bad id"), "tool_call_id_invalid"),
        (_tool_turn(finish_reason="stop"), "tool_finish_reason_invalid"),
    ),
)
def test_invalid_tool_requests_execute_nothing(turn, reason: str) -> None:
    adapter = _SequenceAdapter([turn])
    harness, session_store, _, _ = _harness(adapter)

    result = _run(harness)

    assert result.status == "fallback"
    assert result.escalation_reason == reason
    assert result.provider_request_count == 1
    assert result.tool_call_count == 0
    assert len(adapter.requests) == 1
    assert session_store.get(_scope().internal_session_key, 101.0) is None


@pytest.mark.parametrize("variant", ("malformed", "unsafe", "unsourced"))
def test_invalid_final_output_fails_closed_without_memory(variant: str) -> None:
    if variant == "malformed":
        raw = "not-json"
    else:
        raw = json.dumps(
            {
                "schema_version": "1",
                "status": "answer",
                "reply": (
                    "Секрет sk-abcdefghijklmnopqrstuvwxyz1234567890"
                    if variant == "unsafe"
                    else "Переподключитесь и повторите проверку."
                ),
                "source_topic_ids": [] if variant == "unsourced" else ["connected_no_internet"],
                "session_state": {
                    "issue_topic_id": None,
                    "attempted_steps": [],
                    "last_outcome": "not_reported",
                    "escalation_requested": False,
                },
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
    adapter = _SequenceAdapter([_final_turn("connected_no_internet", raw_content=raw)])
    harness, session_store, guard, _ = _harness(adapter)

    result = _run(harness)

    assert result.status == "fallback"
    assert result.escalation_reason.startswith("agent_output_")
    assert result.provider_request_count == 1
    assert session_store.get(_scope().internal_session_key, 101.0) is None
    assert guard.in_flight_count == 0


class _Exploding:
    def __getattr__(self, name):
        raise AssertionError(f"unsafe input touched {name}")


@pytest.mark.parametrize(
    ("message", "status", "reason"),
    (
        ("Вот ключ vless://private-profile", "fallback", "sensitive_input"),
        ("Позовите оператора поддержки", "escalate", "human_requested"),
    ),
)
def test_input_rejection_precedes_memory_retrieval_concurrency_and_provider(
    message: str,
    status: str,
    reason: str,
) -> None:
    from support_agent_harness import SupportAgentHarness

    policy, _, knowledge = _snapshots()
    traces = []
    adapter = _SequenceAdapter([])
    harness = SupportAgentHarness(
        policy=policy,
        knowledge_store=_Exploding(),
        knowledge=knowledge,
        session_store=_Exploding(),
        rate_limiter=_Exploding(),
        in_flight_guard=_Exploding(),
        adapter=adapter,
        trace_callback=traces.append,
    )

    result = _run(harness, message=message)

    assert result.status == status
    assert result.escalation_reason == reason
    assert result.provider_request_count == 0
    assert adapter.requests == []
    assert len(traces) == 1
    assert message not in json.dumps(asdict(traces[0]), ensure_ascii=False)


class _Clock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value


def test_each_provider_timeout_is_capped_by_remaining_wall_deadline() -> None:
    clock = _Clock()
    adapter = _SequenceAdapter(
        [_tool_turn(), _final_turn("private_dns_and_filters")],
        clock=clock,
        advances=(0.75, 0.25),
    )
    harness, _, _, _ = _harness(
        adapter,
        monotonic=clock,
        run_deadline_seconds=2.0,
        provider_timeout_seconds=12.0,
    )

    result = _run(harness)

    assert result.status == "answer"
    assert [item["request_timeout"] for item in adapter.requests] == pytest.approx([2.0, 1.25])
    assert result.latency_ms == 1000


def test_lower_runtime_request_and_tool_budgets_are_enforced() -> None:
    from support_agent_provider import ProviderCallError

    retry_adapter = _SequenceAdapter(
        [
            ProviderCallError(retryable=True, code="provider_timeout", status=0),
            _final_turn("connected_no_internet"),
        ]
    )
    retry_harness, _, _, _ = _harness(retry_adapter, max_provider_requests=1)
    retry_result = _run(retry_harness)

    assert retry_result.status == "fallback"
    assert retry_result.provider_request_count == 1
    assert retry_result.retry_count == 0
    assert len(retry_adapter.requests) == 1

    tool_adapter = _SequenceAdapter([_tool_turn()])
    tool_harness, _, _, _ = _harness(tool_adapter, max_tool_calls=0)
    tool_result = _run(tool_harness)

    assert tool_result.status == "fallback"
    assert tool_result.escalation_reason == "tool_call_budget_exhausted"
    assert tool_result.provider_request_count == 1
    assert tool_result.tool_call_count == 0
    assert tool_adapter.requests[0]["tool_choice"] == "none"


class _BlockingAdapter:
    def __init__(self, turn) -> None:
        self.turn = turn
        self.active = 0
        self.max_active = 0
        self.two_started = asyncio.Event()
        self.release = asyncio.Event()
        self.requests = 0

    async def complete(self, **_kwargs):
        self.requests += 1
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        if self.active == 2:
            self.two_started.set()
        try:
            await self.release.wait()
            return self.turn
        finally:
            self.active -= 1


def test_process_concurrency_is_two_busy_wait_is_bounded_and_guards_release() -> None:
    from support_agent_harness import SupportAgentRequest

    async def scenario():
        adapter = _BlockingAdapter(_final_turn("connected_no_internet"))
        harness, _, guard, _ = _harness(adapter, concurrency_wait_seconds=0.02)
        requests = [
            SupportAgentRequest(
                surface="app",
                session_scope=_scope(f"owner-{index}", f"abcdefghijklmn{index:02d}"),
                message="Подключено, но интернета нет",
                now=100.0,
            )
            for index in range(3)
        ]
        first = asyncio.create_task(harness.run(requests[0]))
        second = asyncio.create_task(harness.run(requests[1]))
        await asyncio.wait_for(adapter.two_started.wait(), timeout=1.0)
        started = time.monotonic()
        busy = await harness.run(requests[2])
        busy_elapsed = time.monotonic() - started
        adapter.release.set()
        completed = await asyncio.gather(first, second)
        return harness, guard, adapter, busy, busy_elapsed, completed

    harness, guard, adapter, busy, busy_elapsed, completed = asyncio.run(scenario())

    assert busy.status == "fallback"
    assert busy.escalation_reason == "process_busy"
    assert busy.provider_request_count == 0
    assert busy_elapsed < 0.15
    assert [item.status for item in completed] == ["answer", "answer"]
    assert adapter.requests == 2
    assert adapter.max_active == 2
    assert guard.in_flight_count == 0
    assert harness.available_concurrency == 2
