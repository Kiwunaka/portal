from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

import pytest

from scripts.reward_rollout import (
    PAID_FORTNIGHTLY_DISCOUNTS_V3,
    ConfigMutation,
    InstanceReport,
    RolloutRuntimeError,
    RuntimeSnapshot,
    canonical_json,
    main,
    run_preflight,
)


CANDIDATE = "a" * 40


@dataclass
class FakeRuntime:
    unresolved_users: int = 0
    invalid_merge_chains: int = 0
    wheel_enabled: bool = False
    calendar_enabled: bool = False
    wrong_candidate: bool = False
    legacy_bot_mutator_count: int = 0
    reward_state_accounts: int = 4
    previous_wheel_config: dict[str, object] | None = None
    readback_override: dict[str, object] | None = None

    def __post_init__(self) -> None:
        self.previous_wheel_config = deepcopy(self.previous_wheel_config)
        self.backfill_calls = 0
        self.configure_calls = 0

    def snapshot(self) -> RuntimeSnapshot:
        instance_candidate = "b" * 40 if self.wrong_candidate else CANDIDATE
        instances = [
            InstanceReport(
                component="api",
                candidate=instance_candidate,
                wheel_enabled=self.wheel_enabled,
                calendar_enabled=self.calendar_enabled,
                legacy_reward_mutator_accepting=False,
            ),
            InstanceReport(
                component="bot",
                candidate=instance_candidate,
                wheel_enabled=self.wheel_enabled,
                calendar_enabled=self.calendar_enabled,
                legacy_reward_mutator_accepting=False,
            ),
        ]
        instances.extend(
            InstanceReport(
                component="bot",
                candidate=CANDIDATE,
                wheel_enabled=False,
                calendar_enabled=False,
                legacy_reward_mutator_accepting=True,
            )
            for _ in range(self.legacy_bot_mutator_count)
        )
        return RuntimeSnapshot(
            instances=tuple(instances),
            unresolved_users=self.unresolved_users,
            invalid_merge_chains=self.invalid_merge_chains,
            canonical_accounts=4,
            reward_state_accounts=self.reward_state_accounts,
        )

    def backfill_reward_states(self) -> dict[str, int]:
        self.backfill_calls += 1
        return {
            "canonical_accounts": 4,
            "states_created": 0,
            "wheel_sources_seen": 2,
            "wheel_states_updated": 0,
            "unresolved_users": 0,
            "invalid_merge_chains": 0,
        }

    def configure_wheel(self, payload: dict[str, object]) -> ConfigMutation:
        self.configure_calls += 1
        readback = deepcopy(self.readback_override if self.readback_override is not None else payload)
        return ConfigMutation(
            previous=deepcopy(self.previous_wheel_config),
            readback=readback,
            committed=readback == payload,
        )

    def read_wheel_config(self) -> dict[str, object] | None:
        if self.readback_override is not None:
            return deepcopy(self.readback_override)
        if self.configure_calls:
            return deepcopy(PAID_FORTNIGHTLY_DISCOUNTS_V3)
        return deepcopy(self.previous_wheel_config)


def fake_runtime(**overrides: object) -> FakeRuntime:
    return FakeRuntime(**overrides)


def test_preflight_blocks_unresolved_accounts_and_running_legacy_bot(tmp_path: Path) -> None:
    result = run_preflight(
        fake_runtime(unresolved_users=1, legacy_bot_mutator_count=1),
        candidate=CANDIDATE,
        evidence_dir=tmp_path,
    )

    assert result.status == "BLOCKED"
    assert result.codes == ("account_foundation_unresolved", "legacy_bot_not_quiesced")
    evidence = json.loads((tmp_path / "preflight.json").read_text(encoding="utf-8"))
    assert evidence["status"] == "BLOCKED"
    assert evidence["counts"]["unresolved_users"] == 1


@pytest.mark.parametrize(
    ("runtime", "expected_code"),
    [
        (fake_runtime(wheel_enabled=True), "reward_flags_not_disabled"),
        (fake_runtime(calendar_enabled=True), "reward_flags_not_disabled"),
        (fake_runtime(wrong_candidate=True), "candidate_mismatch"),
    ],
)
def test_preflight_requires_disabled_flags_and_exact_candidate(
    runtime: FakeRuntime,
    expected_code: str,
    tmp_path: Path,
) -> None:
    result = run_preflight(runtime, candidate=CANDIDATE, evidence_dir=tmp_path)

    assert result.status == "BLOCKED"
    assert expected_code in result.codes


@pytest.mark.parametrize(
    ("command", "wrong_confirmation"),
    [("backfill", "reward-state-V1"), ("configure", "paid-weekly-v1")],
)
def test_apply_requires_exact_confirmation(
    command: str,
    wrong_confirmation: str,
    tmp_path: Path,
) -> None:
    runtime = fake_runtime()
    with pytest.raises(SystemExit, match="explicit confirmation required"):
        main(
            [
                command,
                "--candidate",
                CANDIDATE,
                "--confirm-apply",
                wrong_confirmation,
                "--evidence-dir",
                str(tmp_path),
            ],
            runtime=runtime,
        )

    assert runtime.backfill_calls == 0
    assert runtime.configure_calls == 0


def test_backfill_runs_once_after_preflight_and_retains_counts(tmp_path: Path) -> None:
    runtime = fake_runtime()

    result = main(
        [
            "backfill",
            "--candidate",
            CANDIDATE,
            "--confirm-apply",
            "reward-state-v1",
            "--evidence-dir",
            str(tmp_path),
        ],
        runtime=runtime,
    )

    assert result.status == "PASS"
    assert runtime.backfill_calls == 1
    evidence = json.loads((tmp_path / "reward-state-backfill.json").read_text(encoding="utf-8"))
    assert evidence["candidate"] == CANDIDATE
    assert evidence["counts"]["canonical_accounts"] == 4
    assert evidence["counts"]["unresolved_users"] == 0


def test_configure_snapshots_and_hashes_exact_preset_without_secrets(tmp_path: Path) -> None:
    runtime = fake_runtime(previous_wheel_config={"preset": "legacy", "token": "must-not-leak"})

    result = main(
        [
            "configure",
            "--candidate",
            CANDIDATE,
            "--confirm-apply",
            "paid_fortnightly_discounts_v3",
            "--evidence-dir",
            str(tmp_path),
        ],
        runtime=runtime,
    )

    assert result.status == "PASS"
    assert result.readback == PAID_FORTNIGHTLY_DISCOUNTS_V3
    evidence = json.loads((tmp_path / "wheel-config.json").read_text(encoding="utf-8"))
    expected_hash = hashlib.sha256(
        canonical_json(PAID_FORTNIGHTLY_DISCOUNTS_V3)
    ).hexdigest()
    assert evidence["preset"] == "paid_fortnightly_discounts_v3"
    assert evidence["sha256"] == expected_hash
    assert evidence["readback"]["sha256"] == expected_hash
    assert evidence["previous"]["key_count"] == 2
    assert "must-not-leak" not in json.dumps(evidence).lower()
    assert '"token"' not in json.dumps(evidence).lower()


def test_configure_fails_closed_when_exact_readback_does_not_match(tmp_path: Path) -> None:
    runtime = fake_runtime(readback_override={"preset": "unexpected"})

    result = main(
        [
            "configure",
            "--candidate",
            CANDIDATE,
            "--confirm-apply",
            "paid_fortnightly_discounts_v3",
            "--evidence-dir",
            str(tmp_path),
        ],
        runtime=runtime,
    )

    assert result.status == "BLOCKED"
    assert result.codes == ("wheel_config_readback_mismatch",)
    assert result.readback == {"preset": "unexpected"}


def test_configure_requires_completed_reward_state_backfill(tmp_path: Path) -> None:
    runtime = fake_runtime(reward_state_accounts=3)

    result = main(
        [
            "configure",
            "--candidate",
            CANDIDATE,
            "--confirm-apply",
            "paid_fortnightly_discounts_v3",
            "--evidence-dir",
            str(tmp_path),
        ],
        runtime=runtime,
    )

    assert result.status == "BLOCKED"
    assert result.codes == ("reward_state_backfill_incomplete",)
    assert runtime.configure_calls == 0


def test_verify_requires_backfill_state_and_exact_config(tmp_path: Path) -> None:
    runtime = fake_runtime(
        previous_wheel_config=deepcopy(PAID_FORTNIGHTLY_DISCOUNTS_V3)
    )

    result = main(
        ["verify", "--candidate", CANDIDATE, "--evidence-dir", str(tmp_path)],
        runtime=runtime,
    )

    assert result.status == "PASS"
    evidence = json.loads((tmp_path / "verify.json").read_text(encoding="utf-8"))
    assert evidence["checks"]["reward_state_complete"] is True
    assert evidence["checks"]["wheel_config_exact"] is True


def test_cli_rejects_secret_bearing_options(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        main(
            [
                "preflight",
                "--candidate",
                CANDIDATE,
                "--evidence-dir",
                str(tmp_path),
                "--token",
                "secret",
            ],
            runtime=fake_runtime(),
        )


def test_evidence_is_never_overwritten(tmp_path: Path) -> None:
    run_preflight(fake_runtime(), candidate=CANDIDATE, evidence_dir=tmp_path)

    with pytest.raises(RolloutRuntimeError, match="evidence_file_exists"):
        run_preflight(fake_runtime(), candidate=CANDIDATE, evidence_dir=tmp_path)

    evidence = json.loads((tmp_path / "preflight.json").read_text(encoding="utf-8"))
    assert evidence["status"] == "PASS"


def test_candidate_requires_full_git_sha(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="full 40-character hexadecimal Git SHA"):
        main(
            [
                "preflight",
                "--candidate",
                "a" * 7,
                "--evidence-dir",
                str(tmp_path),
            ],
            runtime=fake_runtime(),
        )
