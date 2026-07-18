import json
import sys
from dataclasses import replace
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


def test_stable_prefix_is_identical_when_only_volatile_context_changes() -> None:
    from support_agent_context import SupportContextBuilder
    from support_agent_sessions import SessionState, StoredMessage
    from support_agent_safety import SafeSessionState

    policy, store, knowledge = _snapshots()
    first_hits = store.search("подключено но нет интернета", limit=3)
    second_hits = store.search("медленно работает подключение", limit=3)
    session = SessionState(
        messages=(StoredMessage(role="user", content="Раньше уже переподключался"),),
        state=SafeSessionState(
            issue_topic_id="connected_no_internet",
            attempted_steps=("reconnect",),
            last_outcome="unchanged",
            escalation_requested=False,
        ),
        last_access=999999.0,
    )
    builder = SupportContextBuilder()

    first = builder.build(
        policy=policy,
        knowledge=knowledge,
        session=None,
        redacted_message="Сайты не открываются",
        retrieved_hits=first_hits,
        tool_choice="auto",
    )
    second = builder.build(
        policy=policy,
        knowledge=knowledge,
        session=session,
        redacted_message="Теперь всё ещё медленно",
        retrieved_hits=second_hits,
        tool_choice="auto",
    )

    assert first.stable_prefix == second.stable_prefix
    assert first.stable_prefix_hash == second.stable_prefix_hash
    assert first.messages[0] == second.messages[0]
    assert "999999" not in json.dumps(second.messages, ensure_ascii=False)
    assert first.serialized_chars <= 36_000
    assert second.serialized_chars <= 36_000


def test_policy_or_knowledge_change_intentionally_changes_prefix_hash() -> None:
    from support_agent_context import SupportContextBuilder

    policy, store, knowledge = _snapshots()
    builder = SupportContextBuilder()
    base = builder.build(
        policy=policy,
        knowledge=knowledge,
        session=None,
        redacted_message="Не подключается",
        retrieved_hits=store.search("не подключается", limit=3),
        tool_choice="auto",
    )
    changed_policy = replace(
        policy,
        rendered_prompt=policy.rendered_prompt + "\nAdditional stricter fixed rule.",
        sha256="1" * 64,
    )
    changed_knowledge = replace(
        knowledge,
        version=knowledge.version + ".next",
        sha256="2" * 64,
    )

    policy_context = builder.build(
        policy=changed_policy,
        knowledge=knowledge,
        session=None,
        redacted_message="Не подключается",
        retrieved_hits=(),
        tool_choice="auto",
    )
    knowledge_context = builder.build(
        policy=policy,
        knowledge=changed_knowledge,
        session=None,
        redacted_message="Не подключается",
        retrieved_hits=(),
        tool_choice="auto",
    )

    assert base.stable_prefix_hash != policy_context.stable_prefix_hash
    assert base.stable_prefix_hash != knowledge_context.stable_prefix_hash


def test_context_uses_one_closed_tool_schema_and_deterministic_topic_order() -> None:
    from support_agent_context import SEARCH_SUPPORT_DOCS_TOOL, SupportContextBuilder

    policy, store, knowledge = _snapshots()
    hits = tuple(reversed(store.search("подключено но нет интернета", limit=3)))
    context = SupportContextBuilder().build(
        policy=policy,
        knowledge=knowledge,
        session=None,
        redacted_message="Сайты не открываются",
        retrieved_hits=hits,
        tool_choice="auto",
    )

    assert context.tools == (SEARCH_SUPPORT_DOCS_TOOL,)
    parameters = SEARCH_SUPPORT_DOCS_TOOL["function"]["parameters"]
    assert parameters["additionalProperties"] is False
    assert list(parameters["properties"]) == ["query"]
    assert context.supplied_topic_ids == tuple(hit.topic_id for hit in sorted(hits, key=lambda item: (-item.score, item.topic_id)))
    assert knowledge.compact_index.splitlines() == sorted(knowledge.compact_index.splitlines())


def test_builder_rejects_oversized_stable_prefix_before_provider_request() -> None:
    from support_agent_context import ContextBuildError, SupportContextBuilder

    policy, _, knowledge = _snapshots()
    oversized = replace(policy, rendered_prompt="x" * 18_001, sha256="3" * 64)

    with pytest.raises(ContextBuildError, match="stable_prefix_too_large"):
        SupportContextBuilder().build(
            policy=oversized,
            knowledge=knowledge,
            session=None,
            redacted_message="Безопасный вопрос",
            retrieved_hits=(),
            tool_choice="auto",
        )


def test_full_request_admission_keeps_current_message_then_topics_then_newest_history() -> None:
    from support_agent_context import SupportContextBuilder
    from support_agent_knowledge import KnowledgeHit
    from support_agent_sessions import SessionState, StoredMessage
    from support_agent_safety import SafeSessionState

    policy, _, knowledge = _snapshots()
    session = SessionState(
        messages=tuple(
            StoredMessage(role="user" if index % 2 == 0 else "assistant", content=f"history-{index}-" + ("\\" * 1180))
            for index in range(6)
        ),
        state=SafeSessionState(
            issue_topic_id=None,
            attempted_steps=(),
            last_outcome="not_reported",
            escalation_requested=False,
        ),
        last_access=1.0,
    )
    hits = tuple(
        KnowledgeHit(
            topic_id=f"bounded_topic_{index}",
            keywords=("bounded",),
            body=f"topic-{index}-" + ('"' * 1180),
            score=100 - index,
        )
        for index in range(5)
    )
    current = "current-message-" + ("я" * 1180)

    context = SupportContextBuilder().build(
        policy=policy,
        knowledge=knowledge,
        session=session,
        redacted_message=current,
        retrieved_hits=hits,
        tool_choice="auto",
    )
    serialized = json.dumps(context.messages, ensure_ascii=False)

    assert context.serialized_chars <= 36_000
    assert context.messages[-1] == {"role": "user", "content": current[:1200]}
    assert "topic-0-" in serialized
    if "topic-4-" not in serialized:
        assert "history-0-" not in serialized
    retained_history = [index for index in range(6) if f"history-{index}-" in serialized]
    assert retained_history == sorted(retained_history)
    if retained_history:
        assert retained_history[-1] == 5


def test_tool_continuation_replays_exact_call_and_removes_pre_retrieval_bodies() -> None:
    from support_agent_context import SupportContextBuilder, ToolContinuation

    policy, store, knowledge = _snapshots()
    pre_hits = store.search("подключено но нет интернета", limit=3)
    tool_hits = store.search("private dns фильтр", limit=3)
    tool_result = store.render_hits(tool_hits)
    assistant_message = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "search_support_docs", "arguments": '{"query":"private dns фильтр"}'},
            }
        ],
    }

    first = SupportContextBuilder().build(
        policy=policy,
        knowledge=knowledge,
        session=None,
        redacted_message="Подключено, но интернета нет",
        retrieved_hits=pre_hits,
        tool_choice="auto",
    )
    continuation = SupportContextBuilder().build(
        policy=policy,
        knowledge=knowledge,
        session=None,
        redacted_message="Подключено, но интернета нет",
        retrieved_hits=(),
        tool_choice="none",
        continuation=ToolContinuation(
            assistant_message=assistant_message,
            tool_call_id="call_1",
            tool_name="search_support_docs",
            tool_result=tool_result,
            supplied_topic_ids=tuple(hit.topic_id for hit in tool_hits),
        ),
    )
    serialized = json.dumps(continuation.messages, ensure_ascii=False)

    assert continuation.stable_prefix_hash == first.stable_prefix_hash
    assert continuation.messages[-2] == assistant_message
    assert continuation.messages[-1] == {
        "role": "tool",
        "tool_call_id": "call_1",
        "name": "search_support_docs",
        "content": tool_result,
    }
    assert continuation.supplied_topic_ids == tuple(hit.topic_id for hit in tool_hits)
    assert all(hit.body not in serialized for hit in pre_hits if hit.topic_id not in continuation.supplied_topic_ids)


def test_lower_runtime_context_and_retrieval_ceilings_are_honored() -> None:
    from support_agent_context import ContextBuildError, SupportContextBuilder

    policy, store, knowledge = _snapshots()
    baseline = SupportContextBuilder().build(
        policy=policy,
        knowledge=knowledge,
        session=None,
        redacted_message="Безопасный вопрос",
        retrieved_hits=(),
        tool_choice="auto",
    )

    with pytest.raises(ContextBuildError, match="provider_request_too_large"):
        SupportContextBuilder(max_provider_request_chars=baseline.serialized_chars - 1).build(
            policy=policy,
            knowledge=knowledge,
            session=None,
            redacted_message="Безопасный вопрос",
            retrieved_hits=(),
            tool_choice="auto",
        )

    hits = store.search("подключено но нет интернета", limit=3)
    bounded = SupportContextBuilder(max_retrieval_zone_chars=100).build(
        policy=policy,
        knowledge=knowledge,
        session=None,
        redacted_message="Подключено, но интернета нет",
        retrieved_hits=hits,
        tool_choice="auto",
    )
    assert bounded.supplied_topic_ids == ()
    assert all(hit.body not in json.dumps(bounded.messages, ensure_ascii=False) for hit in hits)
