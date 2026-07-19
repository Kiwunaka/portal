import asyncio
import re
import sys
from dataclasses import replace
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))


def _safe_state(issue: str | None = "connected_no_internet"):
    from support_agent_safety import SafeSessionState

    return SafeSessionState(
        issue_topic_id=issue,
        attempted_steps=("reconnect",),
        last_outcome="not_reported",
        escalation_requested=False,
    )


def test_app_session_is_stable_but_isolated_by_owner_and_surface() -> None:
    from support_agent_sessions import SupportSessionResolver

    resolver = SupportSessionResolver()
    visible_id = "session_abcdefghijklmnop"
    first = resolver.resolve_app("owner-alpha", visible_id)
    same = resolver.resolve_app("owner-alpha", visible_id)
    other_owner = resolver.resolve_app("owner-beta", visible_id)
    ticket = resolver.resolve_ticket("owner-alpha", 17)

    assert first == same
    assert first.internal_session_key != other_owner.internal_session_key
    assert first.owner_scope_hash != other_owner.owner_scope_hash
    assert first.owner_scope_hash != ticket.owner_scope_hash
    assert first.internal_session_key != ticket.internal_session_key
    assert re.fullmatch(r"[0-9a-f]{64}", first.owner_scope_hash)
    assert re.fullmatch(r"[0-9a-f]{64}", first.internal_session_key)
    serialized = repr((first, same, other_owner, ticket))
    assert "owner-alpha" not in serialized
    assert "owner-beta" not in serialized


def test_invalid_app_session_id_is_replaced_with_secure_opaque_id() -> None:
    from support_agent_sessions import SessionValidationError, SupportSessionResolver

    resolver = SupportSessionResolver()
    scope = resolver.resolve_app("owner-alpha", "../../bad")

    assert re.fullmatch(r"[A-Za-z0-9_-]{16,64}", scope.client_session_id)
    assert scope.client_session_id != "../../bad"
    with pytest.raises(SessionValidationError):
        resolver.resolve_app("", "session_abcdefghijklmnop")
    with pytest.raises(SessionValidationError):
        resolver.resolve_app(None, "session_abcdefghijklmnop")


def test_ticket_and_helpbot_tokens_are_stable_surface_scoped_and_32_chars() -> None:
    from support_agent_sessions import SupportSessionResolver

    resolver = SupportSessionResolver()
    ticket_a = resolver.resolve_ticket("owner-alpha", 17)
    ticket_same = resolver.resolve_ticket("owner-alpha", 17)
    ticket_other = resolver.resolve_ticket("owner-alpha", 18)
    helpbot_a = resolver.resolve_helpbot(1001)
    helpbot_same = resolver.resolve_helpbot(1001)
    helpbot_other = resolver.resolve_helpbot(1002)

    assert ticket_a == ticket_same
    assert helpbot_a == helpbot_same
    assert ticket_a.client_session_id != ticket_other.client_session_id
    assert helpbot_a.client_session_id != helpbot_other.client_session_id
    assert len(ticket_a.client_session_id) == 32
    assert len(helpbot_a.client_session_id) == 32
    assert ticket_a.internal_session_key != helpbot_a.internal_session_key
    assert "1001" not in repr(helpbot_a)


def test_owner_rate_limit_cannot_be_bypassed_by_rotating_session_ids() -> None:
    from support_agent_sessions import OwnerRateLimiter, SupportSessionResolver

    resolver = SupportSessionResolver()
    limiter = OwnerRateLimiter(limit=6, window_seconds=60.0, max_buckets=1024)
    scopes = [resolver.resolve_app("owner-alpha", f"session_{index:016d}") for index in range(7)]

    assert all(limiter.allow(scope.owner_scope_hash, float(index)) for index, scope in enumerate(scopes[:6]))
    assert not limiter.allow(scopes[6].owner_scope_hash, 6.0)
    assert limiter.allow(scopes[6].owner_scope_hash, 60.0)


def test_rate_limiter_bounds_and_expires_owner_buckets() -> None:
    from support_agent_sessions import OwnerRateLimiter

    limiter = OwnerRateLimiter(limit=6, window_seconds=60.0, max_buckets=1024)
    for index in range(1025):
        assert limiter.allow(f"{index:064x}", 0.0)

    assert limiter.bucket_count == 1024
    assert limiter.allow(f"{2048:064x}", 61.0)
    assert limiter.bucket_count == 1


def test_session_store_enforces_ttl_lru_and_six_message_bound() -> None:
    from support_agent_sessions import StoredMessage, SupportSessionStore

    store = SupportSessionStore(ttl_seconds=3600.0, max_sessions=256, max_messages=6)
    keys = [f"{index:064x}" for index in range(257)]
    for index, key in enumerate(keys[:256]):
        store.append(
            key,
            [StoredMessage(role="user", content=f"message-{index}")],
            _safe_state(),
            float(index),
        )

    assert store.session_count == 256
    assert store.get(keys[0], 300.0) is not None
    store.append(keys[256], [StoredMessage(role="user", content="new")], _safe_state(), 301.0)
    assert store.get(keys[1], 301.0) is None
    assert store.get(keys[0], 301.0) is not None

    conversation_key = f"{9999:064x}"
    messages = [StoredMessage(role="user" if index % 2 == 0 else "assistant", content=f"turn-{index}") for index in range(8)]
    store.append(conversation_key, messages, _safe_state(), 400.0)
    conversation = store.get(conversation_key, 400.0)
    assert conversation is not None
    assert [message.content for message in conversation.messages] == [f"turn-{index}" for index in range(2, 8)]

    expiring = SupportSessionStore(ttl_seconds=3600.0, max_sessions=256, max_messages=6)
    expiring.append(keys[0], [StoredMessage(role="user", content="safe")], _safe_state(), 0.0)
    assert expiring.get(keys[0], 3600.0) is None


def test_session_store_rejects_unbounded_or_non_internal_state() -> None:
    from support_agent_sessions import SessionValidationError, StoredMessage, SupportSessionStore

    store = SupportSessionStore()
    with pytest.raises(SessionValidationError):
        store.append("visible-session-id", [StoredMessage(role="user", content="safe")], _safe_state(), 0.0)
    with pytest.raises(SessionValidationError):
        store.append(f"{1:064x}", [StoredMessage(role="system", content="unsafe role")], _safe_state(), 0.0)
    with pytest.raises(SessionValidationError):
        store.append(f"{1:064x}", [StoredMessage(role="user", content="x" * 1201)], _safe_state(), 0.0)


def test_session_append_validates_complete_state_before_mutating_existing_state() -> None:
    from support_agent_sessions import SessionValidationError, StoredMessage, SupportSessionStore

    store = SupportSessionStore()
    internal_key = "a" * 64
    prior = replace(_safe_state(), unsuccessful_turns=1)
    store.append(
        internal_key,
        [StoredMessage(role="user", content="безопасно")],
        prior,
        1.0,
    )
    before = store.get(internal_key, 1.0)

    with pytest.raises(SessionValidationError, match="session_state_invalid"):
        store.append(
            internal_key,
            [StoredMessage(role="assistant", content="тоже безопасно")],
            replace(prior, unsuccessful_turns=4),
            2.0,
        )

    after = store.get(internal_key, 2.0)
    assert before is not None and after is not None
    assert after.messages == before.messages
    assert after.state == before.state


def test_one_in_flight_guard_releases_session_key() -> None:
    from support_agent_sessions import SessionInFlightGuard

    async def scenario() -> None:
        guard = SessionInFlightGuard()
        key = f"{123:064x}"
        assert await guard.acquire(key)
        assert not await guard.acquire(key)
        await guard.release(key)
        assert await guard.acquire(key)
        await guard.release(key)
        assert guard.in_flight_count == 0

    asyncio.run(scenario())
