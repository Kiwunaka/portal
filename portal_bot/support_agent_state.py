from __future__ import annotations

import unicodedata
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import AbstractSet

from support_agent_safety import SafeSessionState


@dataclass(frozen=True, slots=True)
class ConversationSignals:
    attempted_steps: tuple[str, ...]
    outcome: str | None


STEP_PHRASES = MappingProxyType(
    {
        "reconnect": (
            "я переподключ",
            "отключил и включил",
            "подключил заново",
        ),
        "restart_app": (
            "перезапустил приложение",
            "закрыл и открыл клиент",
        ),
        "switch_route_mode": (
            "переключил режим",
            "сменил режим маршрутизации",
        ),
        "refresh_access": (
            "обновил доступ",
            "обновил подписку",
        ),
        "reimport_profile": (
            "импортировал заново",
            "переимпортировал",
            "добавил профиль заново",
        ),
        "update_client": (
            "обновил приложение",
            "обновил клиент",
        ),
        "check_device_time": (
            "проверил время",
            "проверил дату",
        ),
        "attach_diagnostics": (
            "приложил диагностику",
            "отправил диагностику",
        ),
        "contact_support": (
            "написал в поддержку",
            "обратился к оператору",
        ),
    }
)
OUTCOME_PHRASES = (
    ("resolved", ("все заработало", "всё заработало", "проблема решена", "теперь работает")),
    ("improved", ("стало лучше", "стало быстрее", "держится дольше")),
    ("worse", ("стало хуже", "работает хуже")),
    ("blocked", ("не могу выполнить", "нет такой кнопки", "добавить не удалось")),
    (
        "unchanged",
        (
            "не помогло",
            "без изменений",
            "ничего не изменилось",
            "все так же",
            "всё так же",
        ),
    ),
)
ATTEMPTED_STEP_CODES = frozenset(STEP_PHRASES)
OUTCOME_CODES = frozenset(
    {"not_reported", *(outcome for outcome, _ in OUTCOME_PHRASES)}
)
NEGATIVE_OUTCOMES = frozenset({"unchanged", "worse", "blocked"})
POSITIVE_OUTCOMES = frozenset({"resolved", "improved"})


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold().replace("ё", "е")
    return " ".join(
        "".join(character if character.isalnum() else " " for character in normalized).split()
    )


_NORMALIZED_STEP_PHRASES = MappingProxyType(
    {
        code: tuple(_normalize(phrase) for phrase in phrases)
        for code, phrases in STEP_PHRASES.items()
    }
)
_NORMALIZED_OUTCOME_PHRASES = tuple(
    (outcome, tuple(_normalize(phrase) for phrase in phrases))
    for outcome, phrases in OUTCOME_PHRASES
)


def classify_conversation_signals(redacted_message: str) -> ConversationSignals:
    text = _normalize(redacted_message)
    attempted = tuple(
        code
        for code, phrases in _NORMALIZED_STEP_PHRASES.items()
        if any(phrase in text for phrase in phrases)
    )[:8]
    outcome = next(
        (
            code
            for code, phrases in _NORMALIZED_OUTCOME_PHRASES
            if any(phrase in text for phrase in phrases)
        ),
        None,
    )
    return ConversationSignals(attempted_steps=attempted, outcome=outcome)


def sanitize_prior_state(
    prior: SafeSessionState | None,
    allowed_topic_ids: AbstractSet[str],
) -> SafeSessionState | None:
    if prior is None:
        return None
    if prior.issue_topic_id is None or prior.issue_topic_id in allowed_topic_ids:
        return prior
    return SafeSessionState(
        issue_topic_id=None,
        attempted_steps=(),
        last_outcome="not_reported",
        escalation_requested=prior.escalation_requested,
        unsuccessful_turns=0,
    )


def _empty_state(issue_topic_id: str | None) -> SafeSessionState:
    return SafeSessionState(
        issue_topic_id=issue_topic_id,
        attempted_steps=(),
        last_outcome="not_reported",
        escalation_requested=False,
        unsuccessful_turns=0,
    )


def state_after_answer(
    prior: SafeSessionState | None,
    grounding_topic_id: str | None,
    signals: ConversationSignals,
) -> SafeSessionState:
    existing = prior or _empty_state(None)
    if grounding_topic_id is not None and grounding_topic_id != existing.issue_topic_id:
        working = _empty_state(grounding_topic_id)
        working = replace(
            working,
            escalation_requested=existing.escalation_requested,
        )
    else:
        working = existing

    attempted = list(working.attempted_steps)
    for step in signals.attempted_steps:
        if step not in attempted and len(attempted) < 8:
            attempted.append(step)

    outcome = working.last_outcome if signals.outcome is None else signals.outcome
    unsuccessful = working.unsuccessful_turns
    if signals.outcome in POSITIVE_OUTCOMES:
        unsuccessful = 0
    elif signals.outcome in NEGATIVE_OUTCOMES and working.issue_topic_id is not None:
        unsuccessful = min(3, unsuccessful + 1)

    return SafeSessionState(
        issue_topic_id=working.issue_topic_id,
        attempted_steps=tuple(attempted),
        last_outcome=outcome,
        escalation_requested=working.escalation_requested,
        unsuccessful_turns=unsuccessful,
    )


def would_repeat_failure(
    prior: SafeSessionState | None,
    signals: ConversationSignals,
) -> bool:
    return bool(
        prior is not None
        and prior.issue_topic_id is not None
        and not prior.escalation_requested
        and signals.outcome in NEGATIVE_OUTCOMES
        and prior.unsuccessful_turns + 1 >= 2
    )


def state_for_transfer(
    prior: SafeSessionState,
    signals: ConversationSignals,
) -> SafeSessionState:
    updated = state_after_answer(prior, None, signals)
    return replace(updated, escalation_requested=True)
