import asyncio
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))


def _config(*, enabled: bool = True, key: str = "sk-test"):
    from support_ai_service import SupportAIConfig

    return SupportAIConfig(
        enabled=enabled,
        api_key=key,
        api_base_url="https://enterprise.xcody.dev/v1",
        model="minimax-m3",
        reasoning_effort="medium",
    )


def _agent_result(*, status: str = "answer", topic: str = "connected_no_internet", reason=None):
    from support_agent_harness import SupportAgentResult
    from support_agent_provider import ProviderUsage
    from support_agent_safety import SafeSessionState

    return SupportAgentResult(
        status=status,
        reply="Безопасный ответ модели, который не управляет метаданными.",
        source_topic_ids=(topic,) if status == "answer" else (),
        session_state=(
            SafeSessionState(
                issue_topic_id=topic,
                attempted_steps=("reconnect",),
                last_outcome="not_reported",
                escalation_requested=False,
            )
            if status == "answer"
            else None
        ),
        provider_request_count=1,
        tool_call_count=0,
        retry_count=0,
        escalation_reason=reason,
        usage=ProviderUsage(prompt_tokens=100, completion_tokens=20, cached_tokens=80),
        latency_ms=50,
    )


class _HarnessSpy:
    def __init__(self, outcome=None, error: BaseException | None = None) -> None:
        self.outcome = outcome or _agent_result()
        self.error = error
        self.requests = []

    async def run(self, request):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return self.outcome


class _HarnessFactory:
    def __init__(self, harness: _HarnessSpy) -> None:
        self.harness = harness
        self.calls = []

    def __call__(self, config, settings):
        self.calls.append((config, settings))
        return self.harness


def _generate(service, **overrides):
    values = {
        "surface": "app",
        "authenticated_owner_id": "owner-1",
        "message": "Подключено, но сайты не открываются",
        "assistant_session_id": "abcdefghijklmnop",
    }
    values.update(overrides)
    return asyncio.run(service.generate(**values))


@pytest.mark.parametrize(
    ("provider_enabled", "agent_enabled", "expected_source", "legacy_calls", "harness_calls"),
    (
        (False, False, "local_fallback", 0, 0),
        (False, True, "local_fallback", 0, 0),
        (True, False, "support_ai", 1, 0),
        (True, True, "support_agent", 0, 1),
    ),
)
def test_exact_mode_table_runs_one_path_only(
    provider_enabled: bool,
    agent_enabled: bool,
    expected_source: str,
    legacy_calls: int,
    harness_calls: int,
) -> None:
    from support_agent_service import SupportAgentService

    legacy_requests = []

    async def legacy(message, *, ticket_id, user_tg_id, config):
        legacy_requests.append((message, ticket_id, user_tg_id, config))
        return "Безопасная legacy-подсказка."

    harness = _HarnessSpy()
    factory = _HarnessFactory(harness)
    service = SupportAgentService(
        config=_config(enabled=provider_enabled),
        env={"SUPPORT_AI_AGENT_ENABLED": str(agent_enabled).lower()},
        legacy_generate=legacy,
        harness_factory=factory,
    )

    result = _generate(service)

    assert result.source == expected_source
    assert len(legacy_requests) == legacy_calls
    assert len(factory.calls) == harness_calls
    assert len(harness.requests) == harness_calls


def test_missing_key_and_invalid_agent_limits_fail_before_harness_construction() -> None:
    from support_agent_service import SupportAgentService

    invalid_envs = (
        {"SUPPORT_AI_AGENT_ENABLED": "true", "SUPPORT_AI_MAX_CONCURRENCY": "3"},
        {"SUPPORT_AI_AGENT_ENABLED": "true", "SUPPORT_AI_RUN_DEADLINE_SECONDS": "not-a-number"},
        {"SUPPORT_AI_AGENT_ENABLED": "true", "SUPPORT_AI_CONCURRENCY_WAIT_MS": "0"},
        {"SUPPORT_AI_AGENT_ENABLED": "true", "SUPPORT_AI_MAX_PROVIDER_REQUESTS": "-1"},
        {"SUPPORT_AI_AGENT_ENABLED": "true", "SUPPORT_AI_TIMEOUT_SECONDS": "nan"},
    )
    for env in invalid_envs:
        factory = _HarnessFactory(_HarnessSpy())
        result = _generate(
            SupportAgentService(
                config=_config(),
                env=env,
                harness_factory=factory,
            )
        )
        assert result.source == "local_fallback"
        assert factory.calls == []

    missing_key_factory = _HarnessFactory(_HarnessSpy())
    missing_key = _generate(
        SupportAgentService(
            config=_config(key=""),
            env={"SUPPORT_AI_AGENT_ENABLED": "true"},
            harness_factory=missing_key_factory,
        )
    )
    assert missing_key.source == "local_fallback"
    assert missing_key_factory.calls == []

    legacy_calls = []

    async def legacy(*args, **kwargs):
        legacy_calls.append((args, kwargs))
        return "must not run"

    invalid_flag_factory = _HarnessFactory(_HarnessSpy())
    invalid_flag = _generate(
        SupportAgentService(
            config=_config(),
            env={"SUPPORT_AI_AGENT_ENABLED": "maybe"},
            legacy_generate=legacy,
            harness_factory=invalid_flag_factory,
        )
    )
    assert invalid_flag.source == "local_fallback"
    assert legacy_calls == []
    assert invalid_flag_factory.calls == []


@pytest.mark.parametrize(
    "outcome",
    (
        _agent_result(status="fallback", reason="provider_timeout"),
        _agent_result(status="escalate", reason="human_requested"),
    ),
)
def test_agent_failure_or_escalation_uses_fixed_local_copy(outcome) -> None:
    from support_agent_service import SupportAgentService, support_fallback_reply

    harness = _HarnessSpy(outcome=outcome)
    service = SupportAgentService(
        config=_config(),
        env={"SUPPORT_AI_AGENT_ENABLED": "true"},
        harness_factory=_HarnessFactory(harness),
    )

    result = _generate(service)

    assert result.source == "local_fallback"
    assert result.reply == support_fallback_reply("Подключено, но сайты не открываются")
    assert result.should_escalate is True
    assert {item["key"] for item in result.suggested_actions} == {"send_diagnostics", "create_ticket"}


def test_harness_exception_is_contained_and_does_not_expose_exception_text() -> None:
    from support_agent_service import SupportAgentService

    secret = "vless://private-profile sk-private-token"
    service = SupportAgentService(
        config=_config(),
        env={"SUPPORT_AI_AGENT_ENABLED": "true"},
        harness_factory=_HarnessFactory(_HarnessSpy(error=RuntimeError(secret))),
    )

    result = _generate(service)

    assert result.source == "local_fallback"
    assert secret not in result.reply
    assert result.should_escalate is True


def test_validated_topic_owns_actions_source_and_escalation_not_model_text() -> None:
    from support_agent_service import SupportAgentService

    harness = _HarnessSpy(outcome=_agent_result(topic="connected_no_internet"))
    service = SupportAgentService(
        config=_config(),
        env={"SUPPORT_AI_AGENT_ENABLED": "true"},
        harness_factory=_HarnessFactory(harness),
    )

    result = _generate(service)

    assert result.source == "support_agent"
    assert result.reply == "Безопасный ответ модели, который не управляет метаданными."
    assert result.should_escalate is False
    assert [item["key"] for item in result.suggested_actions] == [
        "retry_connect",
        "send_diagnostics",
        "create_ticket",
    ]


def test_visible_session_is_owner_and_surface_scoped_before_harness() -> None:
    from support_agent_service import SupportAgentService

    harness = _HarnessSpy()
    service = SupportAgentService(
        config=_config(),
        env={"SUPPORT_AI_AGENT_ENABLED": "true"},
        harness_factory=_HarnessFactory(harness),
    )

    first = _generate(service, authenticated_owner_id="owner-a")
    second = _generate(service, authenticated_owner_id="owner-b")
    ticket_first = _generate(
        service,
        surface="ticket",
        authenticated_owner_id="owner-a",
        assistant_session_id=None,
        ticket_id=42,
    )
    ticket_second = _generate(
        service,
        surface="ticket",
        authenticated_owner_id="owner-a",
        assistant_session_id=None,
        ticket_id=42,
    )
    helpbot = _generate(
        service,
        surface="helpbot",
        authenticated_owner_id="owner-a",
        assistant_session_id=None,
        validated_sender_id=1001,
    )

    assert first.assistant_session_id == second.assistant_session_id == "abcdefghijklmnop"
    assert harness.requests[0].session_scope.internal_session_key != harness.requests[1].session_scope.internal_session_key
    assert harness.requests[0].session_scope.internal_session_key != harness.requests[2].session_scope.internal_session_key
    assert ticket_first.assistant_session_id == ticket_second.assistant_session_id
    assert harness.requests[2].session_scope.internal_session_key == harness.requests[3].session_scope.internal_session_key
    assert harness.requests[4].session_scope.surface == "helpbot"
    assert helpbot.assistant_session_id == harness.requests[4].session_scope.client_session_id


def test_invalid_app_session_id_is_replaced_with_bounded_opaque_id() -> None:
    from support_agent_service import SupportAgentService

    harness = _HarnessSpy()
    service = SupportAgentService(
        config=_config(),
        env={"SUPPORT_AI_AGENT_ENABLED": "true"},
        harness_factory=_HarnessFactory(harness),
    )

    result = _generate(service, assistant_session_id="../../not-valid")

    assert 16 <= len(result.assistant_session_id) <= 64
    assert result.assistant_session_id != "../../not-valid"
    assert harness.requests[0].session_scope.client_session_id == result.assistant_session_id
