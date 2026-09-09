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
        api_base_url="https://openrouter.ai/api/v1",
        model="deepseek-v4-flash-0731",
        reasoning_effort="medium",
    )


def test_recovery_ticket_does_not_load_case_or_files():
    from support_agent_service import SupportAgentService
    harness = _HarnessSpy()
    service = SupportAgentService(config=_config(), env={"SUPPORT_AI_AGENT_ENABLED": "true"},
                                  harness_factory=_HarnessFactory(harness))
    asyncio.run(service.generate(surface="ticket", authenticated_owner_id="123", ticket_id=42,
                                  message="Помогите восстановить доступ", case_context_enabled=False))
    assert harness.requests[0].case_loader is None


def test_helpbot_conversation_is_scoped_to_ticket():
    from support_agent_sessions import SupportSessionResolver
    resolver = SupportSessionResolver()
    first, second = resolver.resolve_helpbot(123, 41), resolver.resolve_helpbot(123, 42)
    assert first.owner_scope_hash == second.owner_scope_hash
    assert first.internal_session_key != second.internal_session_key


def test_vision_profile_and_case_escalation_preserve_collected_reply():
    from dataclasses import replace
    from support_agent_service import SupportAgentService
    from support_ai_service import provider_wire_model, provider_response_controls
    config = replace(_config(), model="deepseek-v4-flash-vision-exp")
    harness = _HarnessSpy(_agent_result(status="escalate", answer_origin="case_model", grounding_topic_id=None))
    service = SupportAgentService(config=config, env={"SUPPORT_AI_AGENT_ENABLED": "true"},
                                  harness_factory=_HarnessFactory(harness))
    result = asyncio.run(service.generate(surface="ticket", authenticated_owner_id="123", ticket_id=42,
                                         message="Оплата прошла, а доступа нет"))
    assert result.reply == "Безопасный ответ агента." and result.should_escalate
    assert harness.requests[0].case_loader is not None
    assert provider_wire_model(config) == "deepseek/deepseek-v4-flash-vision-exp"
    assert provider_response_controls(config)["provider"]["data_collection"] == "deny"


def _agent_result(
    *,
    status="answer",
    answer_origin="model",
    context_topic_ids=("connected_no_internet",),
    grounding_topic_id="connected_no_internet",
    reason=None,
):
    from support_agent_harness import SupportAgentResult
    from support_agent_provider import ProviderUsage
    from support_agent_safety import SafeSessionState

    return SupportAgentResult(
        status=status,
        reply="Безопасный ответ агента.",
        context_topic_ids=tuple(context_topic_ids),
        grounding_topic_id=grounding_topic_id,
        session_state=(
            SafeSessionState(
                issue_topic_id=grounding_topic_id,
                attempted_steps=(),
                last_outcome="not_reported",
                unsuccessful_turns=0,
                escalation_requested=status == "escalate",
            )
            if grounding_topic_id is not None
            else None
        ),
        answer_origin=answer_origin,
        provider_request_count=1,
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


def generate_with(outcome):
    from support_agent_service import SupportAgentService

    harness = _HarnessSpy(outcome=outcome)
    service = SupportAgentService(
        config=_config(),
        env={"SUPPORT_AI_AGENT_ENABLED": "true"},
        harness_factory=_HarnessFactory(harness),
    )
    return _generate(service)


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


def test_exact_openrouter_route_allows_long_reasoning_runtime_window() -> None:
    from support_agent_service import SupportAgentRuntimeSettings

    openrouter = SupportAgentRuntimeSettings.from_env(
        {
            "SUPPORT_AI_AGENT_ENABLED": "true",
            "SUPPORT_AI_API_BASE_URL": "https://openrouter.ai/api/v1",
            "SUPPORT_AI_TIMEOUT_SECONDS": "45",
            "SUPPORT_AI_RUN_DEADLINE_SECONDS": "50",
        }
    )
    other_provider = SupportAgentRuntimeSettings.from_env(
        {
            "SUPPORT_AI_AGENT_ENABLED": "true",
            "SUPPORT_AI_API_BASE_URL": "https://provider.example/v1",
            "SUPPORT_AI_TIMEOUT_SECONDS": "45",
            "SUPPORT_AI_RUN_DEADLINE_SECONDS": "50",
        }
    )

    assert openrouter.valid is True
    assert openrouter.provider_timeout_seconds == 45.0
    assert openrouter.run_deadline_seconds == 50.0
    assert other_provider.valid is False
    assert other_provider.invalid_reason == "support_ai_run_deadline_seconds_invalid"


def test_exact_openrouter_route_defaults_to_long_reasoning_runtime_window() -> None:
    from support_agent_service import SupportAgentRuntimeSettings

    settings = SupportAgentRuntimeSettings.from_env(
        {
            "SUPPORT_AI_AGENT_ENABLED": "true",
        }
    )

    assert settings.valid is True
    assert settings.provider_timeout_seconds == 45.0
    assert settings.run_deadline_seconds == 50.0


def test_agent_output_budget_defaults_to_1200_and_rejects_higher_values() -> None:
    from support_agent_service import SupportAgentRuntimeSettings

    default_settings = SupportAgentRuntimeSettings.from_env({})
    allowed_settings = SupportAgentRuntimeSettings.from_env(
        {"SUPPORT_AI_MAX_OUTPUT_TOKENS": "1200"}
    )
    oversized_settings = SupportAgentRuntimeSettings.from_env(
        {"SUPPORT_AI_MAX_OUTPUT_TOKENS": "1201"}
    )

    assert default_settings.valid is True
    assert default_settings.max_output_tokens == 1200
    assert allowed_settings.valid is True
    assert allowed_settings.max_output_tokens == 1200
    assert oversized_settings.valid is False
    assert oversized_settings.invalid_reason == "support_ai_max_output_tokens_invalid"


def test_confident_model_answer_uses_topic_actions() -> None:
    result = generate_with(
        _agent_result(
            status="answer",
            answer_origin="model",
            context_topic_ids=("connected_no_internet", "private_dns_and_filters"),
            grounding_topic_id="connected_no_internet",
        )
    )
    assert result.source == "support_agent"
    assert result.should_escalate is False
    assert [item["key"] for item in result.suggested_actions] == [
        "retry_connect",
        "send_diagnostics",
        "create_ticket",
    ]


def test_candidate_model_answer_has_generic_actions_and_no_topic_claim() -> None:
    result = generate_with(
        _agent_result(
            status="answer",
            answer_origin="model",
            context_topic_ids=("connected_no_internet", "private_dns_and_filters"),
            grounding_topic_id=None,
        )
    )
    assert result.source == "support_agent"
    assert result.should_escalate is False
    assert [item["key"] for item in result.suggested_actions] == [
        "send_diagnostics",
        "create_ticket",
    ]


def test_grounded_local_answer_is_still_agent_source() -> None:
    result = generate_with(
        _agent_result(
            status="answer",
            answer_origin="grounded_local",
            context_topic_ids=("slow_speed",),
            grounding_topic_id="slow_speed",
        )
    )
    assert result.source == "support_agent"
    assert result.should_escalate is False


def test_code_owned_answer_is_still_agent_source() -> None:
    result = generate_with(
        _agent_result(
            status="answer",
            answer_origin="code_owned",
            context_topic_ids=(),
            grounding_topic_id=None,
        )
    )
    assert result.source == "support_agent"
    assert result.should_escalate is False


def test_human_transfer_uses_fixed_harness_reply_and_existing_action_objects() -> None:
    outcome = _agent_result(
        status="fallback",
        answer_origin="human_transfer",
        context_topic_ids=(),
        grounding_topic_id=None,
        reason="provider_timeout",
    )
    result = generate_with(outcome)
    assert result.reply == (
        "Не нашёл подтверждённого ответа. Могу подключить специалиста поддержки."
    )
    assert result.source == "local_fallback"
    assert result.should_escalate is True
    assert all(set(item) == {"key", "label"} for item in result.suggested_actions)
    assert [item["key"] for item in result.suggested_actions] == [
        "send_diagnostics",
        "create_ticket",
    ]


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


def test_obsolete_tool_loop_env_values_have_no_effect() -> None:
    from support_agent_service import SupportAgentRuntimeSettings

    settings = SupportAgentRuntimeSettings.from_env(
        {
            "SUPPORT_AI_AGENT_ENABLED": "true",
            "SUPPORT_AI_MAX_PROVIDER_REQUESTS": "999",
            "SUPPORT_AI_MAX_TOOL_CALLS": "999",
            "SUPPORT_AI_TOOL_RESULT_LIMIT": "999",
        }
    )
    assert settings.valid is True
    assert not hasattr(settings, "max_provider_requests")
    assert not hasattr(settings, "max_tool_calls")


@pytest.mark.parametrize(
    ("model", "reasoning"),
    (("other-model", "medium"), ("deepseek-v4-flash-0731", "high")),
)
def test_agent_mode_refuses_a_non_locked_synthesis_profile(model, reasoning) -> None:
    from dataclasses import replace

    from support_agent_service import SupportAgentService

    config = replace(_config(), model=model, reasoning_effort=reasoning)
    factory = _HarnessFactory(_HarnessSpy())
    service = SupportAgentService(
        config=config,
        env={"SUPPORT_AI_AGENT_ENABLED": "true"},
        harness_factory=factory,
    )
    result = _generate(service)
    assert result.source == "local_fallback"
    assert factory.calls == []


def test_agent_mode_refuses_non_openrouter_provider_before_harness() -> None:
    from dataclasses import replace

    from support_agent_service import SupportAgentService

    config = replace(_config(), api_base_url="https://provider.example/v1")
    factory = _HarnessFactory(_HarnessSpy())
    service = SupportAgentService(
        config=config,
        env={
            "SUPPORT_AI_AGENT_ENABLED": "true",
            "SUPPORT_AI_API_BASE_URL": "https://provider.example/v1",
        },
        harness_factory=factory,
    )

    result = _generate(service)

    assert result.source == "local_fallback"
    assert factory.calls == []


def test_legacy_mode_refuses_non_openrouter_provider_before_request() -> None:
    from dataclasses import replace

    from support_agent_service import SupportAgentService

    legacy_calls = []

    async def legacy(*args, **kwargs):
        legacy_calls.append((args, kwargs))
        return "must not run"

    service = SupportAgentService(
        config=replace(_config(), api_base_url="https://provider.example/v1"),
        env={
            "SUPPORT_AI_AGENT_ENABLED": "false",
            "SUPPORT_AI_API_BASE_URL": "https://provider.example/v1",
        },
        legacy_generate=legacy,
    )

    result = _generate(service)

    assert result.source == "local_fallback"
    assert legacy_calls == []


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
