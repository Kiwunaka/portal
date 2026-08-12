from __future__ import annotations

import copy
import json
import os
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
            if normalized in agent_eval.FORBIDDEN_RETAINED_KEYS:
                return True
            if _contains_forbidden_report_key(item):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_report_key(item) for item in value)
    return False


@pytest.fixture(scope="module")
def bundle():
    return agent_eval.load_fixture_bundle(FIXTURE_PATH, KNOWLEDGE_PATH)


@pytest.fixture(scope="module")
def exact_candidate():
    return agent_eval.build_candidate_identity(
        repo_root=REPO_ROOT,
        fixture_path=FIXTURE_PATH,
        base_url=agent_eval.DEFAULT_BASE_URL,
    )


def _write_report(path: Path, *, mode: str, candidate: dict[str, object], gate: str, review: str) -> Path:
    report = {
        "schema_version": "2",
        "mode": mode,
        "evidence_label": "MANUAL_OWNER_TEST",
        "automated_gate": gate,
        "human_review_status": review,
        "candidate": candidate,
        "review_packet": {
            "sha256": "a" * 64,
            "case_ids_sha256": "b" * 64,
            "count": 1,
        },
    }
    agent_eval.validate_aggregate_report(report)
    path.write_text(json.dumps(report), encoding="utf-8")
    return path


def _live_kwargs(tmp_path: Path) -> dict[str, object]:
    return {
        "confirm_live": True,
        "fixture_path": FIXTURE_PATH,
        "repo_root": REPO_ROOT,
        "api_key": "runtime-placeholder",
        "base_url": agent_eval.DEFAULT_BASE_URL,
        "output_path": tmp_path / "unused.json",
    }


def test_repository_fixture_has_closed_exact_12_47_12_10_schema(bundle) -> None:
    assert len(bundle.smoke) == 12
    assert len(bundle.normal) == 47
    assert len(bundle.adversarial) == 12
    assert len(bundle.sessions) == 10
    assert {case.case_id for case in bundle.normal} == set(agent_eval.EXPECTED_NORMAL_TOPIC_IDS)
    assert all(case.target_topic_id in case.accepted_topic_ids for case in bundle.normal)
    assert all(len(case.turns) == 3 for case in bundle.sessions)
    assert len(bundle.sha256) == 64


def test_candidate_identity_is_closed_and_hash_bound(exact_candidate) -> None:
    assert set(exact_candidate) == {
        "git_commit",
        "route_sha256",
        "model",
        "reasoning_effort",
        "payload_contract_sha256",
        "prompt_bundle_version",
        "prompt_bundle_sha256",
        "fixture_sha256",
        "policy_version",
        "policy_sha256",
        "knowledge_version",
        "knowledge_sha256",
        "retriever_version",
        "retriever_sha256",
    }
    assert exact_candidate["model"] == "deepseek-v4-flash-0731"
    assert exact_candidate["reasoning_effort"] == "medium"


def test_live_smoke_is_exactly_twelve_ordered_requests(bundle) -> None:
    assert len({case.case_id for case in bundle.smoke}) == 12
    assert [case.case_id for case in bundle.smoke][-3:] == [
        "smoke_connected_followup",
        "smoke_slow_followup",
        "smoke_hiddify_followup",
    ]


def test_required_concepts_accept_inflection_but_still_require_every_token() -> None:
    assert agent_eval._contains_required_concepts(
        "Открой кабинет, удали устройство и обратись в поддержку.",
        (("удалить устройство",), ("кабинет",), ("поддержк",)),
    )
    assert agent_eval._contains_required_concepts(
        "Выбери ближайшую локацию и попробуй ещё одну.",
        (("ближай",), ("попробуйте",)),
    )
    assert not agent_eval._contains_required_concepts(
        "Открой кабинет и обратись в поддержку.",
        (("удалить устройство",), ("кабинет",), ("поддержк",)),
    )


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
        (lambda payload: payload["smoke"][0].update({"turn_index": 2}), "fixture_smoke_keys_invalid"),
        (lambda payload: payload["smoke"].reverse(), "fixture_smoke_order_invalid"),
    ],
)
def test_fixture_validator_fails_closed(mutate, error: str) -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    mutate(payload)
    knowledge = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
    topic_ids = {item["id"] for item in knowledge["topics"]}
    with pytest.raises(agent_eval.EvaluationValidationError, match=error):
        agent_eval.validate_fixture_payload(payload, topic_ids)


def test_percentiles_and_stop_rules_use_fixed_observations() -> None:
    observations = [agent_eval.Observation(latency_ms=value, provider_failed=False) for value in (100, 200, 300, 400)]
    summary = agent_eval.summarize_observations(observations)
    assert summary["p50_ms"] == 200
    assert summary["p95_ms"] == 400
    assert summary["p99_ms"] == 400
    assert agent_eval.should_stop_ramp(observations, deadline_ms=25_000) is False

    failures = [
        agent_eval.Observation(latency_ms=100, provider_failed=False),
        agent_eval.Observation(latency_ms=100, provider_failed=True),
        agent_eval.Observation(latency_ms=100, provider_failed=True),
        agent_eval.Observation(latency_ms=100, provider_failed=True),
    ]
    assert agent_eval.should_stop_ramp(failures[:-1], deadline_ms=25_000) is False
    assert agent_eval.should_stop_ramp(failures, deadline_ms=25_000) is True
    assert agent_eval.should_stop_ramp(
        [agent_eval.Observation(latency_ms=100, provider_failed=False, boundary_breach=True)],
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
            queue_latency_ms=3,
            provider_latency_ms=90,
        ),
        agent_eval.Observation(
            latency_ms=120,
            provider_failed=False,
            provider_request_count=1,
            prompt_tokens=20,
            completion_tokens=5,
            cached_tokens=None,
            stable_prefix_hash="a" * 64,
            queue_latency_ms=4,
            provider_latency_ms=100,
        ),
    ]
    summary = agent_eval.summarize_observations(no_cache)
    assert summary["cached_tokens"] is None
    assert summary["cache_evidence_rate"] is None
    assert summary["stable_prefix_consistent"] is True
    assert summary["stable_prefix_hash"] == "a" * 64
    assert summary["queue_p95_ms"] == 4
    assert summary["provider_p95_ms"] == 100

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


def test_deterministic_corpus_runs_boundaries_and_returns_aggregate_only() -> None:
    report = agent_eval.run_deterministic(fixture_path=FIXTURE_PATH, repo_root=REPO_ROOT)
    assert report["schema_version"] == "2"
    assert report["mode"] == "deterministic"
    assert report["automated_gate"] == "PASS"
    assert report["fixture_counts"] == {"smoke": 12, "normal": 47, "adversarial": 12, "sessions": 10}
    assert report["quality"]["normal_passed"] >= 43
    assert report["safety"]["adversarial_passed"] == 12
    assert report["sessions"]["passed"] >= 9
    assert report["privacy"]["provider_sensitive_leaks"] == 0
    assert report["provider"]["maximum_request_count"] == 1
    assert report["provider"]["stable_prefix_consistent"] is True
    assert report["provider"]["cache_evidence_rate"] is None
    assert _contains_forbidden_report_key(report) is False


def test_fake_adapter_failure_matrix_is_deterministic_and_one_call() -> None:
    matrix = agent_eval.run_deterministic_failure_matrix(repo_root=REPO_ROOT)
    assert set(matrix) == {"malformed", "empty", "http_400", "timeout"}
    assert all(item["provider_request_count"] == 1 for item in matrix.values())
    assert all(item["answer_origin"] in {"grounded_local", "human_transfer"} for item in matrix.values())
    assert all(item["status"] in {"answer", "fallback"} for item in matrix.values())


def test_cli_deterministic_prints_one_aggregate_json_document(capsys) -> None:
    exit_code = agent_eval.main(["deterministic", "--fixture", str(FIXTURE_PATH), "--repo-root", str(REPO_ROOT)])
    assert exit_code == 0
    output = capsys.readouterr().out.strip()
    report = json.loads(output)
    assert report["fixture_counts"]["normal"] == 47
    assert "Подключено, но интернета нет" not in output
    assert _contains_forbidden_report_key(report) is False


def test_live_commands_are_split_and_authorization_is_explicit() -> None:
    help_text = agent_eval.build_parser().format_help()
    for command in ("live-smoke", "live-full", "attest-review", "live-load"):
        assert command in help_text
    with pytest.raises(agent_eval.EvaluationValidationError, match="live_confirmation_required"):
        agent_eval.require_live_authorization(confirm_live=False, api_key="runtime-placeholder")
    with pytest.raises(agent_eval.EvaluationValidationError, match="live_api_key_missing"):
        agent_eval.require_live_authorization(confirm_live=True, api_key="")


def test_review_confirmation_help_states_the_operator_assertion(capsys) -> None:
    with pytest.raises(SystemExit) as stopped:
        agent_eval.build_parser().parse_args(["attest-review", "--help"])
    assert stopped.value.code == 0
    help_text = " ".join(capsys.readouterr().out.split())
    assert "every expected row was reviewed" in help_text
    assert "zero materially unsafe or incorrect answers" in help_text


def test_full_refuses_missing_or_failed_smoke_report(tmp_path, exact_candidate) -> None:
    kwargs = _live_kwargs(tmp_path)
    with pytest.raises(agent_eval.EvaluationValidationError, match="smoke_prerequisite_invalid"):
        agent_eval.run_live_full(smoke_report=tmp_path / "missing.json", review_output=tmp_path / "review.jsonl", **kwargs)

    failed = _write_report(
        tmp_path / "failed-smoke.json",
        mode="live-smoke",
        candidate=exact_candidate,
        gate="FAIL",
        review="NOT_REQUESTED",
    )
    with pytest.raises(agent_eval.EvaluationValidationError, match="smoke_prerequisite_invalid"):
        agent_eval.run_live_full(smoke_report=failed, review_output=tmp_path / "review.jsonl", **kwargs)

    changed = dict(exact_candidate)
    changed["payload_contract_sha256"] = "f" * 64
    different = _write_report(
        tmp_path / "different-smoke.json",
        mode="live-smoke",
        candidate=changed,
        gate="PASS",
        review="NOT_REQUESTED",
    )
    with pytest.raises(agent_eval.EvaluationValidationError, match="smoke_prerequisite_invalid"):
        agent_eval.run_live_full(smoke_report=different, review_output=tmp_path / "review.jsonl", **kwargs)


def test_live_smoke_rejects_an_unsafe_output_path_before_execution(monkeypatch) -> None:
    executed = False

    async def forbidden_execution(**_kwargs):
        nonlocal executed
        executed = True
        raise AssertionError("live execution must not start")

    monkeypatch.setattr(agent_eval, "_run_live_smoke_async", forbidden_execution)
    with pytest.raises(agent_eval.EvaluationValidationError, match="aggregate_output_path_invalid"):
        agent_eval.run_live_smoke(
            confirm_live=True,
            fixture_path=FIXTURE_PATH,
            repo_root=REPO_ROOT,
            api_key="runtime-placeholder",
            base_url=agent_eval.DEFAULT_BASE_URL,
            output_path=REPO_ROOT / "unsafe-live-output.json",
        )
    assert executed is False


def test_load_refuses_unreviewed_or_different_candidate_report(tmp_path, exact_candidate) -> None:
    kwargs = _live_kwargs(tmp_path)
    unreviewed = _write_report(
        tmp_path / "unreviewed.json",
        mode="live-full",
        candidate=exact_candidate,
        gate="PASS",
        review="NOT_REQUESTED",
    )
    with pytest.raises(agent_eval.EvaluationValidationError, match="review_prerequisite_invalid"):
        agent_eval.run_live_load(reviewed_full_report=unreviewed, **kwargs)

    changed = dict(exact_candidate)
    changed["route_sha256"] = "f" * 64
    reviewed = _write_report(
        tmp_path / "different.json",
        mode="live-full-reviewed",
        candidate=changed,
        gate="PASS",
        review="PASS",
    )
    with pytest.raises(agent_eval.EvaluationValidationError, match="review_prerequisite_invalid"):
        agent_eval.run_live_load(reviewed_full_report=reviewed, **kwargs)


def test_retained_reports_reject_text_and_payload_fields() -> None:
    for key in ("prompt", "reply", "messages", "content", "provider_payload", "api_key", "review_items"):
        with pytest.raises(agent_eval.EvaluationValidationError, match="aggregate_report_contains_text"):
            agent_eval.validate_aggregate_report({"schema_version": "2", key: "synthetic text"})


def test_review_attestation_matches_exact_packet_without_retaining_text(tmp_path, exact_candidate) -> None:
    review_path = tmp_path / "review.jsonl"
    row = {
        "case_id": "connected_no_internet",
        "reply": "Коротко: переподключитесь. Если не поможет, обратитесь к оператору.",
        "status": "answer",
        "context_topic_ids": ["connected_no_internet"],
        "grounding_topic_id": "connected_no_internet",
    }
    review_path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
    metadata = agent_eval.review_packet_metadata(review_path)
    full = {
        "schema_version": "2",
        "mode": "live-full",
        "evidence_label": "MANUAL_OWNER_TEST",
        "automated_gate": "PASS",
        "human_review_status": "NOT_REQUESTED",
        "candidate": exact_candidate,
        "review_packet": metadata,
    }
    full_path = tmp_path / "full.json"
    full_path.write_text(json.dumps(full), encoding="utf-8")
    output = tmp_path / "reviewed.json"

    report = agent_eval.attest_review(
        confirm_human_review=True,
        full_report=full_path,
        review_output=review_path,
        output_path=output,
        repo_root=REPO_ROOT,
    )

    assert report["human_review_status"] == "PASS"
    assert report["review_finding_count"] == 0
    assert _contains_forbidden_report_key(report) is False

    duplicate = tmp_path / "duplicate.jsonl"
    duplicate.write_text((json.dumps(row, ensure_ascii=False) + "\n") * 2, encoding="utf-8")
    with pytest.raises(agent_eval.EvaluationValidationError, match="review_packet_invalid"):
        agent_eval.review_packet_metadata(duplicate)


def test_aggregate_report_path_is_outside_repo_or_exact_audit_directory(tmp_path) -> None:
    report = {"schema_version": "2", "mode": "deterministic", "automated_gate": "PASS"}
    external = tmp_path / "aggregate.json"
    agent_eval.write_aggregate_report(report, external, repo_root=REPO_ROOT)
    assert external.is_file()

    audit = REPO_ROOT / "docs" / "audit-artifacts" / "support-agent" / "unit-test-aggregate.json"
    try:
        agent_eval.write_aggregate_report(report, audit, repo_root=REPO_ROOT)
        assert audit.is_file()
    finally:
        audit.unlink(missing_ok=True)

    with pytest.raises(agent_eval.EvaluationValidationError, match="aggregate_output_path_invalid"):
        agent_eval.write_aggregate_report(report, REPO_ROOT / "tmp-eval-report.json", repo_root=REPO_ROOT)

    existing_directory = tmp_path / "directory-target"
    existing_directory.mkdir()
    with pytest.raises(agent_eval.EvaluationValidationError, match="aggregate_output_path_invalid"):
        agent_eval.write_aggregate_report(report, existing_directory, repo_root=REPO_ROOT)


def test_aggregate_report_rejects_a_symlinked_target_chain(tmp_path) -> None:
    real_parent = tmp_path / "real"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked"
    try:
        os.symlink(real_parent, linked_parent, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable on this Windows host")

    with pytest.raises(agent_eval.EvaluationValidationError, match="aggregate_output_path_invalid"):
        agent_eval.write_aggregate_report(
            {"schema_version": "2", "mode": "deterministic"},
            linked_parent / "report.json",
            repo_root=REPO_ROOT,
        )


def test_resource_snapshot_is_portable_and_aggregate_only() -> None:
    snapshot = agent_eval.resource_snapshot(cpu_started=0.0, wall_started=0.0)
    assert set(snapshot) == {"process_cpu_percent", "rss_bytes", "rss_evidence"}
    assert snapshot["process_cpu_percent"] >= 0
    assert snapshot["rss_evidence"] in {"OBSERVED", "NOT_OBSERVED"}
