from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import pokrov_support_agent_eval as agent_eval


FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "support-agent-live-eval.json"
KNOWLEDGE_PATH = REPO_ROOT / "shared" / "support-ai-knowledge.json"


def _contains_forbidden_report_key(value: object) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).casefold().replace("-", "_")
            if normalized in {
                "prompt",
                "prompts",
                "reply",
                "replies",
                "message",
                "messages",
                "content",
                "tool_arguments",
                "api_key",
                "session_id",
                "owner_id",
            }:
                return True
            if _contains_forbidden_report_key(item):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_report_key(item) for item in value)
    return False


def test_repository_fixture_has_closed_exact_48_12_10_schema() -> None:
    bundle = agent_eval.load_fixture_bundle(FIXTURE_PATH, KNOWLEDGE_PATH)

    assert len(bundle.normal) == 48
    assert len(bundle.adversarial) == 12
    assert len(bundle.sessions) == 10
    assert {case.case_id for case in bundle.normal} == set(agent_eval.EXPECTED_NORMAL_TOPIC_IDS)
    assert all(case.target_topic_id in case.accepted_topic_ids for case in bundle.normal)
    assert all(len(case.turns) == 3 for case in bundle.sessions)
    assert len(bundle.sha256) == 64


@pytest.mark.parametrize(
    "mutate, error",
    [
        (lambda payload: payload["normal"][0].update({"extra": True}), "fixture_normal_keys_invalid"),
        (
            lambda payload: payload["normal"][0].update({"prompt": "Вот vless://private-user@example.invalid:443"}),
            "fixture_sensitive_text",
        ),
        (lambda payload: payload["normal"][0].update({"accepted_topic_ids": ["missing_topic"]}), "fixture_topic_unknown"),
        (lambda payload: payload["sessions"][0].update({"turns": ["one", "two"]}), "fixture_session_turns_invalid"),
    ],
)
def test_fixture_validator_fails_closed(mutate, error: str) -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    mutate(payload)
    knowledge = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
    topic_ids = {item["id"] for item in knowledge["topics"]}

    with pytest.raises(agent_eval.EvaluationValidationError, match=error):
        agent_eval.validate_fixture_payload(payload, topic_ids)


def test_percentiles_and_sustained_failure_stop_use_fixed_observations() -> None:
    observations = [
        agent_eval.Observation(latency_ms=value, provider_failed=False)
        for value in (100, 200, 300, 400)
    ]
    summary = agent_eval.summarize_observations(observations)

    assert summary["p50_ms"] == 200
    assert summary["p95_ms"] == 400
    assert agent_eval.should_stop_ramp(observations, deadline_ms=25_000) is False

    two_failures = [
        agent_eval.Observation(latency_ms=100, provider_failed=False),
        agent_eval.Observation(latency_ms=100, provider_failed=True),
        agent_eval.Observation(latency_ms=100, provider_failed=True),
    ]
    assert agent_eval.should_stop_ramp(two_failures, deadline_ms=25_000) is False
    assert agent_eval.should_stop_ramp(
        [*two_failures, agent_eval.Observation(latency_ms=100, provider_failed=True)],
        deadline_ms=25_000,
    ) is True
    assert agent_eval.should_stop_ramp(
        [agent_eval.Observation(latency_ms=25_001, provider_failed=False)],
        deadline_ms=25_000,
    ) is True


def test_summary_keeps_missing_cache_evidence_null_and_prefix_consistency_honest() -> None:
    no_cache = [
        agent_eval.Observation(
            latency_ms=100,
            provider_failed=False,
            provider_request_count=1,
            prompt_tokens=20,
            completion_tokens=5,
            cached_tokens=None,
            stable_prefix_hash="a" * 64,
        ),
        agent_eval.Observation(
            latency_ms=120,
            provider_failed=False,
            provider_request_count=1,
            prompt_tokens=20,
            completion_tokens=5,
            cached_tokens=None,
            stable_prefix_hash="a" * 64,
        ),
    ]

    summary = agent_eval.summarize_observations(no_cache)

    assert summary["cached_tokens"] is None
    assert summary["cache_evidence_rate"] is None
    assert summary["stable_prefix_consistent"] is True
    assert summary["stable_prefix_hash"] == "a" * 64

    mixed = copy.deepcopy(no_cache)
    mixed[1] = agent_eval.Observation(
        latency_ms=120,
        provider_failed=False,
        provider_request_count=1,
        cached_tokens=10,
        stable_prefix_hash="b" * 64,
    )
    mixed_summary = agent_eval.summarize_observations(mixed)
    assert mixed_summary["cache_evidence_rate"] == 0.5
    assert mixed_summary["stable_prefix_consistent"] is False
    assert mixed_summary["stable_prefix_hash"] is None


def test_deterministic_corpus_runs_all_boundaries_and_returns_aggregate_only() -> None:
    report = agent_eval.run_deterministic(
        fixture_path=FIXTURE_PATH,
        repo_root=REPO_ROOT,
    )

    assert report["mode"] == "deterministic"
    assert report["evidence_label"] == "PASS"
    assert report["fixture_counts"] == {"normal": 48, "adversarial": 12, "sessions": 10}
    assert report["quality"]["normal_passed"] == 48
    assert report["safety"]["adversarial_passed"] == 12
    assert report["sessions"]["passed"] == 10
    assert report["privacy"]["provider_sensitive_leaks"] == 0
    assert report["provider"]["stable_prefix_consistent"] is True
    assert report["provider"]["cache_evidence_rate"] is None
    assert _contains_forbidden_report_key(report) is False
    serialized = json.dumps(report, ensure_ascii=False)
    fixture_payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert all(case["prompt"] not in serialized for case in fixture_payload["normal"])
    assert all(turn not in serialized for case in fixture_payload["sessions"] for turn in case["turns"])


def test_cli_deterministic_prints_one_aggregate_json_document(capsys) -> None:
    exit_code = agent_eval.main(
        [
            "deterministic",
            "--fixture",
            str(FIXTURE_PATH),
            "--repo-root",
            str(REPO_ROOT),
        ]
    )

    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    report = json.loads(output)
    assert report["fixture_counts"]["normal"] == 48
    assert "Подключено, но интернета нет" not in output
    assert "reply" not in output.casefold()
    assert _contains_forbidden_report_key(report) is False


def test_live_mode_requires_both_explicit_confirmation_and_runtime_key() -> None:
    with pytest.raises(agent_eval.EvaluationValidationError, match="live_confirmation_required"):
        agent_eval.require_live_authorization(confirm_live=False, api_key="sk-placeholder")
    with pytest.raises(agent_eval.EvaluationValidationError, match="live_api_key_missing"):
        agent_eval.require_live_authorization(confirm_live=True, api_key="")
    assert agent_eval.require_live_authorization(confirm_live=True, api_key="runtime-secret") is None
