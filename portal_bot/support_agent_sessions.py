from __future__ import annotations

import asyncio
import base64
import hashlib
import math
import re
import secrets
from collections import OrderedDict, deque
from dataclasses import dataclass
from typing import Sequence

from support_agent_safety import SafeSessionState
from support_agent_state import ATTEMPTED_STEP_CODES, OUTCOME_CODES


_CLIENT_SESSION_RE = re.compile(r"^[A-Za-z0-9_-]{16,64}$")
_INTERNAL_KEY_RE = re.compile(r"^[0-9a-f]{64}$")
_TOPIC_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_SURFACES = frozenset({"app", "ticket", "helpbot"})


class SessionValidationError(ValueError):
    """Fixed-code rejection for invalid session or resource state."""


@dataclass(frozen=True, slots=True)
class SessionScope:
    surface: str
    owner_scope_hash: str
    internal_session_key: str
    client_session_id: str


@dataclass(frozen=True, slots=True)
class StoredMessage:
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class SessionState:
    messages: tuple[StoredMessage, ...]
    state: SafeSessionState
    last_access: float


@dataclass(frozen=True, slots=True)
class EvictionStats:
    expired: int
    lru: int


def _length_prefixed(parts: Sequence[str]) -> bytes:
    encoded = bytearray()
    for part in parts:
        raw = part.encode("utf-8")
        encoded.extend(len(raw).to_bytes(4, byteorder="big", signed=False))
        encoded.extend(raw)
    return bytes(encoded)


def _sha256_tuple(*parts: str) -> str:
    return hashlib.sha256(_length_prefixed(parts)).hexdigest()


def _stable_client_token(*parts: str) -> str:
    digest = hashlib.sha256(_length_prefixed(parts)).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")[:32]


class SupportSessionResolver:
    @staticmethod
    def _owner_scope(surface: str, owner_id: str) -> str:
        if surface not in _SURFACES or not isinstance(owner_id, str) or not 1 <= len(owner_id) <= 256:
            raise SessionValidationError("session_owner_scope_invalid")
        return _sha256_tuple(surface, owner_id)

    @staticmethod
    def _scope(surface: str, owner_id: str, client_session_id: str) -> SessionScope:
        owner_scope_hash = SupportSessionResolver._owner_scope(surface, owner_id)
        return SessionScope(
            surface=surface,
            owner_scope_hash=owner_scope_hash,
            internal_session_key=_sha256_tuple(owner_scope_hash, client_session_id),
            client_session_id=client_session_id,
        )

    def resolve_app(self, authenticated_owner_id: str, supplied_id: str | None) -> SessionScope:
        if not isinstance(authenticated_owner_id, str) or not authenticated_owner_id:
            raise SessionValidationError("session_owner_scope_invalid")
        client_session_id = (
            supplied_id
            if isinstance(supplied_id, str) and _CLIENT_SESSION_RE.fullmatch(supplied_id)
            else secrets.token_urlsafe(24)
        )
        return self._scope("app", authenticated_owner_id, client_session_id)

    def resolve_ticket(self, authenticated_owner_id: str, ticket_id: int) -> SessionScope:
        if (
            not isinstance(authenticated_owner_id, str)
            or not authenticated_owner_id
            or type(ticket_id) is not int
            or ticket_id <= 0
        ):
            raise SessionValidationError("ticket_session_invalid")
        owner_id = authenticated_owner_id
        token = _stable_client_token("ticket", owner_id, str(ticket_id))
        return self._scope("ticket", owner_id, token)

    def resolve_helpbot(self, validated_sender_id: int, ticket_id: int | None = None) -> SessionScope:
        if type(validated_sender_id) is not int or validated_sender_id <= 0:
            raise SessionValidationError("helpbot_session_invalid")
        owner_id = str(validated_sender_id)
        if ticket_id is not None and (type(ticket_id) is not int or ticket_id <= 0):
            raise SessionValidationError("helpbot_session_invalid")
        token = (_stable_client_token("helpbot", owner_id, str(ticket_id))
                 if ticket_id is not None else _stable_client_token("helpbot", owner_id))
        return self._scope("helpbot", owner_id, token)


class SupportSessionStore:
    def __init__(
        self,
        *,
        ttl_seconds: float = 3_600.0,
        max_sessions: int = 256,
        max_messages: int = 6,
        max_message_chars: int = 1_200,
    ) -> None:
        if (
            not math.isfinite(ttl_seconds)
            or not 1.0 <= ttl_seconds <= 3_600.0
            or type(max_sessions) is not int
            or not 1 <= max_sessions <= 256
            or type(max_messages) is not int
            or not 1 <= max_messages <= 6
            or type(max_message_chars) is not int
            or not 1 <= max_message_chars <= 1_200
        ):
            raise SessionValidationError("session_store_config_invalid")
        self.ttl_seconds = float(ttl_seconds)
        self.max_sessions = max_sessions
        self.max_messages = max_messages
        self.max_message_chars = max_message_chars
        self._sessions: OrderedDict[str, SessionState] = OrderedDict()

    @property
    def session_count(self) -> int:
        return len(self._sessions)

    @staticmethod
    def _validate_key(internal_key: str) -> None:
        if not isinstance(internal_key, str) or not _INTERNAL_KEY_RE.fullmatch(internal_key):
            raise SessionValidationError("internal_session_key_invalid")

    @staticmethod
    def _validate_now(now: float) -> float:
        try:
            value = float(now)
        except (TypeError, ValueError) as exc:
            raise SessionValidationError("session_time_invalid") from exc
        if not math.isfinite(value) or value < 0:
            raise SessionValidationError("session_time_invalid")
        return value

    @staticmethod
    def _validate_state(state: SafeSessionState) -> None:
        if not isinstance(state, SafeSessionState):
            raise SessionValidationError("session_state_invalid")
        issue_topic_id = state.issue_topic_id
        steps = state.attempted_steps
        if (
            (
                issue_topic_id is not None
                and (
                    not isinstance(issue_topic_id, str)
                    or not _TOPIC_ID_RE.fullmatch(issue_topic_id)
                )
            )
            or not isinstance(steps, tuple)
            or len(steps) > 8
            or len(set(steps)) != len(steps)
            or any(
                not isinstance(step, str) or step not in ATTEMPTED_STEP_CODES
                for step in steps
            )
            or not isinstance(state.last_outcome, str)
            or state.last_outcome not in OUTCOME_CODES
            or type(state.escalation_requested) is not bool
            or type(state.unsuccessful_turns) is not int
            or not 0 <= state.unsuccessful_turns <= 3
        ):
            raise SessionValidationError("session_state_invalid")

    def evict(self, now: float) -> EvictionStats:
        current = self._validate_now(now)
        expired_keys = [
            key
            for key, value in self._sessions.items()
            if current - value.last_access >= self.ttl_seconds
        ]
        for key in expired_keys:
            self._sessions.pop(key, None)
        lru = 0
        while len(self._sessions) > self.max_sessions:
            self._sessions.popitem(last=False)
            lru += 1
        return EvictionStats(expired=len(expired_keys), lru=lru)

    def get(self, internal_key: str, now: float) -> SessionState | None:
        self._validate_key(internal_key)
        current = self._validate_now(now)
        self.evict(current)
        existing = self._sessions.get(internal_key)
        if existing is None:
            return None
        refreshed = SessionState(
            messages=existing.messages,
            state=existing.state,
            last_access=current,
        )
        self._sessions[internal_key] = refreshed
        self._sessions.move_to_end(internal_key)
        return refreshed

    def append(
        self,
        internal_key: str,
        messages: Sequence[StoredMessage],
        state: SafeSessionState,
        now: float,
    ) -> None:
        self._validate_key(internal_key)
        current = self._validate_now(now)
        self._validate_state(state)
        incoming = tuple(messages)
        if not incoming:
            raise SessionValidationError("session_messages_invalid")
        for message in incoming:
            if (
                not isinstance(message, StoredMessage)
                or message.role not in {"user", "assistant"}
                or not isinstance(message.content, str)
                or not message.content
                or len(message.content) > self.max_message_chars
            ):
                raise SessionValidationError("session_message_invalid")
        self.evict(current)
        existing = self._sessions.get(internal_key)
        combined = (*(() if existing is None else existing.messages), *incoming)
        candidate = SessionState(
            messages=tuple(combined[-self.max_messages :]),
            state=state,
            last_access=current,
        )
        self._sessions[internal_key] = candidate
        self._sessions.move_to_end(internal_key)
        self.evict(current)


class OwnerRateLimiter:
    def __init__(
        self,
        *,
        limit: int = 6,
        window_seconds: float = 60.0,
        max_buckets: int = 1_024,
    ) -> None:
        if (
            type(limit) is not int
            or not 1 <= limit <= 6
            or not math.isfinite(window_seconds)
            or not 1.0 <= window_seconds <= 60.0
            or type(max_buckets) is not int
            or not 1 <= max_buckets <= 1_024
        ):
            raise SessionValidationError("owner_rate_config_invalid")
        self.limit = limit
        self.window_seconds = float(window_seconds)
        self.max_buckets = max_buckets
        self._buckets: OrderedDict[str, deque[float]] = OrderedDict()

    @property
    def bucket_count(self) -> int:
        return len(self._buckets)

    def _expire(self, now: float) -> None:
        threshold = now - self.window_seconds
        empty: list[str] = []
        for owner_hash, events in self._buckets.items():
            while events and events[0] <= threshold:
                events.popleft()
            if not events:
                empty.append(owner_hash)
        for owner_hash in empty:
            self._buckets.pop(owner_hash, None)

    def allow(self, owner_scope_hash: str, now: float) -> bool:
        if not isinstance(owner_scope_hash, str) or not _INTERNAL_KEY_RE.fullmatch(owner_scope_hash):
            raise SessionValidationError("owner_scope_hash_invalid")
        try:
            current = float(now)
        except (TypeError, ValueError) as exc:
            raise SessionValidationError("owner_rate_time_invalid") from exc
        if not math.isfinite(current) or current < 0:
            raise SessionValidationError("owner_rate_time_invalid")
        self._expire(current)
        events = self._buckets.get(owner_scope_hash)
        if events is None:
            while len(self._buckets) >= self.max_buckets:
                self._buckets.popitem(last=False)
            events = deque()
            self._buckets[owner_scope_hash] = events
        self._buckets.move_to_end(owner_scope_hash)
        if len(events) >= self.limit:
            return False
        events.append(current)
        return True


class SessionInFlightGuard:
    def __init__(self) -> None:
        self._active: set[str] = set()
        self._lock = asyncio.Lock()

    @property
    def in_flight_count(self) -> int:
        return len(self._active)

    async def acquire(self, internal_session_key: str) -> bool:
        if not isinstance(internal_session_key, str) or not _INTERNAL_KEY_RE.fullmatch(internal_session_key):
            raise SessionValidationError("internal_session_key_invalid")
        async with self._lock:
            if internal_session_key in self._active:
                return False
            self._active.add(internal_session_key)
            return True

    async def release(self, internal_session_key: str) -> None:
        if not isinstance(internal_session_key, str) or not _INTERNAL_KEY_RE.fullmatch(internal_session_key):
            raise SessionValidationError("internal_session_key_invalid")
        async with self._lock:
            self._active.discard(internal_session_key)
