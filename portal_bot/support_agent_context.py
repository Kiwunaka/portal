from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Mapping, Sequence

from support_agent_grounding import (
    RETRIEVER_RULES_SHA256,
    RETRIEVER_VERSION,
    RetrievalDecision,
)
from support_agent_knowledge import KnowledgeHit, KnowledgeSnapshot
from support_agent_policy import PolicySnapshot, render_synthesis_policy_prompt
from support_agent_safety import SafeSessionState
from support_agent_sessions import SessionState, StoredMessage
from support_agent_state import ATTEMPTED_STEP_CODES, OUTCOME_CODES


PROMPT_BUNDLE_VERSION = "3"
MAX_PROVIDER_REQUEST_CHARS = 30_000
PROVIDER_ENVELOPE_RESERVE_CHARS = 512
MAX_STABLE_PREFIX_CHARS = 18_000
MAX_RETRIEVAL_ZONE_CHARS = 3_600
MAX_SESSION_ZONE_CHARS = 6_000
MAX_CURRENT_MESSAGE_CHARS = 1_200

_VERSION_RE = re.compile(r"[A-Za-z0-9._-]{1,32}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_TOPIC_ID_RE = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}")


class ContextBuildError(ValueError):
    """Fixed-code rejection raised before a provider request can be made."""


@dataclass(frozen=True, slots=True)
class SynthesisContext:
    stable_prefix: str
    stable_prefix_hash: str
    prompt_bundle_sha256: str
    messages: tuple[Mapping[str, object], Mapping[str, object]]
    context_topic_ids: tuple[str, ...]
    grounding_topic_id: str | None
    serialized_chars: int


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=False,
    )


def _request_chars(messages: Sequence[Mapping[str, object]]) -> int:
    return len(_canonical_json(tuple(messages))) + PROVIDER_ENVELOPE_RESERVE_CHARS


def _prompt_contract(policy: PolicySnapshot, prompt_bundle_version: str) -> str:
    sections = (
        ("SYNTHESIS_POLICY", render_synthesis_policy_prompt(policy.policy)),
        (
            "MESSAGE_LAYOUT",
            "Exactly two provider messages: one system message containing this stable prefix, "
            "then one user message containing UNTRUSTED_SUPPORT_CONTEXT_JSON. "
            "The volatile JSON keys are selected_topics, session_state, recent_messages, "
            "current_question in that exact order.",
        ),
        ("PROMPT_BUNDLE_VERSION", prompt_bundle_version),
    )
    return "\n\n".join(f"[{name}]\n{body}" for name, body in sections)


def _stable_prefix(
    policy: PolicySnapshot,
    knowledge: KnowledgeSnapshot,
    *,
    prompt_contract: str,
    prompt_bundle_sha256: str,
    prompt_bundle_version: str,
    retriever_sha256: str,
) -> str:
    sections = (
        ("PROMPT_CONTRACT", prompt_contract),
        ("PUBLIC_SUPPORT_KB_INDEX", knowledge.compact_index),
        (
            "BUNDLE_VERSIONS",
            _canonical_json(
                {
                    "prompt_bundle": prompt_bundle_version,
                    "prompt_bundle_sha256": prompt_bundle_sha256,
                    "policy_sha256": policy.sha256,
                    "knowledge_version": knowledge.version,
                    "knowledge_sha256": knowledge.sha256,
                    "retriever_version": RETRIEVER_VERSION,
                    "retriever_sha256": retriever_sha256,
                }
            ),
        ),
    )
    prefix = "\n\n".join(f"[{name}]\n{body}" for name, body in sections)
    if len(prefix) > MAX_STABLE_PREFIX_CHARS:
        raise ContextBuildError("stable_prefix_too_large")
    return prefix


def _session_payload(
    session: SessionState | None,
) -> tuple[Mapping[str, object] | None, tuple[Mapping[str, object], ...]]:
    if session is None:
        return None, ()
    if not isinstance(session, SessionState) or not isinstance(session.state, SafeSessionState):
        raise ContextBuildError("session_state_invalid")
    state = session.state
    if (
        (
            state.issue_topic_id is not None
            and (
                not isinstance(state.issue_topic_id, str)
                or not _TOPIC_ID_RE.fullmatch(state.issue_topic_id)
            )
        )
        or not isinstance(state.attempted_steps, tuple)
        or len(state.attempted_steps) > 8
        or any(not isinstance(step, str) for step in state.attempted_steps)
        or len(set(state.attempted_steps)) != len(state.attempted_steps)
        or any(step not in ATTEMPTED_STEP_CODES for step in state.attempted_steps)
        or not isinstance(state.last_outcome, str)
        or state.last_outcome not in OUTCOME_CODES
        or type(state.unsuccessful_turns) is not int
        or not 0 <= state.unsuccessful_turns <= 3
        or type(state.escalation_requested) is not bool
    ):
        raise ContextBuildError("session_state_invalid")
    if not isinstance(session.messages, tuple) or len(session.messages) > 6:
        raise ContextBuildError("session_message_invalid")
    messages: list[Mapping[str, object]] = []
    for message in session.messages:
        if (
            not isinstance(message, StoredMessage)
            or message.role not in {"user", "assistant"}
            or not isinstance(message.content, str)
            or not 1 <= len(message.content) <= MAX_CURRENT_MESSAGE_CHARS
        ):
            raise ContextBuildError("session_message_invalid")
        messages.append({"role": message.role, "content": message.content})
    return (
        {
            "issue_topic_id": state.issue_topic_id,
            "attempted_steps": list(state.attempted_steps),
            "last_outcome": state.last_outcome,
            "unsuccessful_turns": state.unsuccessful_turns,
            "escalation_requested": state.escalation_requested,
        },
        tuple(messages),
    )


def _messages(
    stable_prefix: str,
    selected_topics: Sequence[Mapping[str, object]],
    session_state: Mapping[str, object] | None,
    recent_messages: Sequence[Mapping[str, object]],
    current_question: str,
) -> tuple[Mapping[str, object], Mapping[str, object]]:
    volatile = {
        "selected_topics": list(selected_topics),
        "session_state": session_state,
        "recent_messages": list(recent_messages),
        "current_question": current_question,
    }
    return (
        {"role": "system", "content": stable_prefix},
        {
            "role": "user",
            "content": "UNTRUSTED_SUPPORT_CONTEXT_JSON\n"
            + _canonical_json(volatile)
            + "\nEND_UNTRUSTED_SUPPORT_CONTEXT_JSON",
        },
    )


class SupportContextBuilder:
    def __init__(
        self,
        *,
        max_provider_request_chars: int = MAX_PROVIDER_REQUEST_CHARS,
        max_retrieval_zone_chars: int = MAX_RETRIEVAL_ZONE_CHARS,
        prompt_bundle_version: str = PROMPT_BUNDLE_VERSION,
        retriever_sha256: str = RETRIEVER_RULES_SHA256,
    ) -> None:
        if (
            type(max_provider_request_chars) is not int
            or not 1_000 <= max_provider_request_chars <= MAX_PROVIDER_REQUEST_CHARS
            or type(max_retrieval_zone_chars) is not int
            or not 1 <= max_retrieval_zone_chars <= MAX_RETRIEVAL_ZONE_CHARS
            or not isinstance(prompt_bundle_version, str)
            or not _VERSION_RE.fullmatch(prompt_bundle_version)
            or not isinstance(retriever_sha256, str)
            or not _SHA256_RE.fullmatch(retriever_sha256)
        ):
            raise ContextBuildError("context_limits_invalid")
        self.max_provider_request_chars = max_provider_request_chars
        self.max_retrieval_zone_chars = max_retrieval_zone_chars
        self.prompt_bundle_version = prompt_bundle_version
        self.retriever_sha256 = retriever_sha256

    def build_synthesis(
        self,
        *,
        policy: PolicySnapshot,
        knowledge: KnowledgeSnapshot,
        session: SessionState | None,
        redacted_message: str,
        decision: RetrievalDecision,
    ) -> SynthesisContext:
        if not isinstance(policy, PolicySnapshot) or not isinstance(knowledge, KnowledgeSnapshot):
            raise ContextBuildError("bundle_snapshot_invalid")
        if (
            not isinstance(redacted_message, str)
            or not 1 <= len(redacted_message) <= MAX_CURRENT_MESSAGE_CHARS
        ):
            raise ContextBuildError("current_message_invalid")
        if not isinstance(decision, RetrievalDecision):
            raise ContextBuildError("retrieval_decision_invalid")
        if (
            decision.retriever_version != RETRIEVER_VERSION
            or decision.retriever_sha256 != self.retriever_sha256
        ):
            raise ContextBuildError("retrieval_snapshot_mismatch")
        if (
            not isinstance(decision.context_topics, tuple)
            or not isinstance(decision.context_topic_ids, tuple)
            or not decision.context_topics
        ):
            raise ContextBuildError("missing_source")
        if any(not isinstance(hit, KnowledgeHit) for hit in decision.context_topics):
            raise ContextBuildError("retrieval_snapshot_mismatch")
        decision_topic_ids = tuple(hit.topic_id for hit in decision.context_topics)
        if (
            decision.context_topic_ids != decision_topic_ids
            or len(set(decision_topic_ids)) != len(decision_topic_ids)
            or (
                decision.grounding_topic_id is not None
                and decision.grounding_topic_id not in decision_topic_ids
            )
        ):
            raise ContextBuildError("retrieval_snapshot_mismatch")
        for hit in decision.context_topics:
            source = knowledge.topics_by_id.get(hit.topic_id)
            if (
                not isinstance(source, KnowledgeHit)
                or source.topic_id != hit.topic_id
                or source.keywords != hit.keywords
                or source.body != hit.body
            ):
                raise ContextBuildError("retrieval_snapshot_mismatch")

        prompt_contract = _prompt_contract(policy, self.prompt_bundle_version)
        prompt_bundle_sha256 = hashlib.sha256(prompt_contract.encode("utf-8")).hexdigest()
        stable_prefix = _stable_prefix(
            policy,
            knowledge,
            prompt_contract=prompt_contract,
            prompt_bundle_sha256=prompt_bundle_sha256,
            prompt_bundle_version=self.prompt_bundle_version,
            retriever_sha256=self.retriever_sha256,
        )
        stable_prefix_hash = hashlib.sha256(stable_prefix.encode("utf-8")).hexdigest()

        admitted_topics: list[Mapping[str, object]] = []
        admitted_topic_ids: list[str] = []
        for hit in decision.context_topics[:3]:
            candidate_topics = [
                *admitted_topics,
                {"id": hit.topic_id, "body": hit.body},
            ]
            if len(_canonical_json(candidate_topics)) > self.max_retrieval_zone_chars:
                break
            candidate_messages = _messages(
                stable_prefix,
                candidate_topics,
                None,
                (),
                redacted_message,
            )
            if _request_chars(candidate_messages) > self.max_provider_request_chars:
                break
            admitted_topics = candidate_topics
            admitted_topic_ids.append(hit.topic_id)
        if not admitted_topics:
            raise ContextBuildError("provider_request_too_large")
        if (
            decision.grounding_topic_id is not None
            and decision.grounding_topic_id not in admitted_topic_ids
        ):
            raise ContextBuildError("provider_request_too_large")

        session_state, history = _session_payload(session)
        session_zone = {
            "session_state": session_state,
            "recent_messages": [],
        }
        if len(_canonical_json(session_zone)) > MAX_SESSION_ZONE_CHARS:
            raise ContextBuildError("session_state_invalid")
        messages = _messages(
            stable_prefix,
            admitted_topics,
            session_state,
            (),
            redacted_message,
        )
        if _request_chars(messages) > self.max_provider_request_chars:
            raise ContextBuildError("provider_request_too_large")

        admitted_newest_first: list[Mapping[str, object]] = []
        for message in reversed(history):
            candidate_newest_first = [*admitted_newest_first, message]
            candidate_history = list(reversed(candidate_newest_first))
            candidate_zone = {
                "session_state": session_state,
                "recent_messages": candidate_history,
            }
            if len(_canonical_json(candidate_zone)) > MAX_SESSION_ZONE_CHARS:
                break
            candidate_messages = _messages(
                stable_prefix,
                admitted_topics,
                session_state,
                candidate_history,
                redacted_message,
            )
            if _request_chars(candidate_messages) > self.max_provider_request_chars:
                break
            admitted_newest_first = candidate_newest_first
            messages = candidate_messages

        return SynthesisContext(
            stable_prefix=stable_prefix,
            stable_prefix_hash=stable_prefix_hash,
            prompt_bundle_sha256=prompt_bundle_sha256,
            messages=messages,
            context_topic_ids=tuple(admitted_topic_ids),
            grounding_topic_id=decision.grounding_topic_id,
            serialized_chars=_request_chars(messages),
        )
