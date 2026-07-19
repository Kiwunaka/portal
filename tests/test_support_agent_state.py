import sys
from dataclasses import replace
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))


@pytest.fixture
def prior_state():
    from support_agent_safety import SafeSessionState

    return SafeSessionState(
        issue_topic_id="connected_no_internet",
        attempted_steps=("reconnect",),
        last_outcome="unchanged",
        escalation_requested=False,
        unsuccessful_turns=1,
    )


def test_suggestion_text_is_not_an_attempt_but_explicit_user_report_is():
    from support_agent_state import classify_conversation_signals

    assert (
        classify_conversation_signals("Попробуйте переподключиться").attempted_steps
        == ()
    )
    assert classify_conversation_signals(
        "Я переподключился, но не помогло"
    ).attempted_steps == ("reconnect",)


def test_new_confident_issue_resets_old_steps_outcome_and_count(prior_state):
    from support_agent_state import classify_conversation_signals, state_after_answer

    result = state_after_answer(
        prior_state,
        "slow_speed",
        classify_conversation_signals("Теперь соединение просто медленное"),
    )

    assert result.issue_topic_id == "slow_speed"
    assert result.attempted_steps == ()
    assert result.last_outcome == "not_reported"
    assert result.unsuccessful_turns == 0


def test_second_negative_turn_transfers_and_persists_sticky_escalation(
    prior_state,
):
    from support_agent_state import (
        classify_conversation_signals,
        state_for_transfer,
        would_repeat_failure,
    )

    signals = classify_conversation_signals(
        "После переподключения ничего не изменилось"
    )
    assert would_repeat_failure(prior_state, signals) is True
    state = state_for_transfer(prior_state, signals)
    assert state.last_outcome == "unchanged"
    assert state.unsuccessful_turns == 2
    assert state.escalation_requested is True


def test_candidate_answer_does_not_replace_established_issue(prior_state):
    from support_agent_state import classify_conversation_signals, state_after_answer

    result = state_after_answer(
        prior_state,
        None,
        classify_conversation_signals("Покажите следующий шаг"),
    )
    assert result.issue_topic_id == prior_state.issue_topic_id
    assert result.attempted_steps == prior_state.attempted_steps
    assert result.unsuccessful_turns == prior_state.unsuccessful_turns


def test_removed_issue_is_cleared_without_losing_sticky_escalation(prior_state):
    from support_agent_state import sanitize_prior_state

    stale = replace(prior_state, escalation_requested=True)
    result = sanitize_prior_state(stale, {"slow_speed"})

    assert result is not None
    assert result.issue_topic_id is None
    assert result.attempted_steps == ()
    assert result.last_outcome == "not_reported"
    assert result.unsuccessful_turns == 0
    assert result.escalation_requested is True


def test_resolved_or_improved_outcome_resets_unsuccessful_count(prior_state):
    from support_agent_state import classify_conversation_signals, state_after_answer

    resolved = state_after_answer(
        prior_state,
        None,
        classify_conversation_signals("Теперь всё заработало"),
    )
    improved = state_after_answer(
        prior_state,
        None,
        classify_conversation_signals("Стало лучше"),
    )

    assert resolved.last_outcome == "resolved"
    assert resolved.unsuccessful_turns == 0
    assert improved.last_outcome == "improved"
    assert improved.unsuccessful_turns == 0


def test_negative_count_is_bounded_and_requires_an_established_issue(prior_state):
    from support_agent_safety import SafeSessionState
    from support_agent_state import classify_conversation_signals, state_after_answer

    signals = classify_conversation_signals("Ничего не изменилось")
    capped = state_after_answer(
        replace(prior_state, unsuccessful_turns=3),
        None,
        signals,
    )
    no_issue = state_after_answer(
        SafeSessionState(
            issue_topic_id=None,
            attempted_steps=(),
            last_outcome="not_reported",
            escalation_requested=False,
            unsuccessful_turns=0,
        ),
        None,
        signals,
    )

    assert capped.unsuccessful_turns == 3
    assert no_issue.unsuccessful_turns == 0


def test_step_codes_are_unique_ordered_and_bounded():
    from support_agent_state import classify_conversation_signals

    signals = classify_conversation_signals(
        "Я переподключился, перезапустил приложение, переключил режим, "
        "обновил доступ, импортировал заново, обновил клиент, проверил время, "
        "приложил диагностику и написал в поддержку."
    )

    assert signals.attempted_steps == (
        "reconnect",
        "restart_app",
        "switch_route_mode",
        "refresh_access",
        "reimport_profile",
        "update_client",
        "check_device_time",
        "attach_diagnostics",
    )
