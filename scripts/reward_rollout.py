"""Guarded, secret-safe operator controls for the paid-rewards rollout."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

from rewards_service import (  # noqa: E402
    PAID_FORTNIGHTLY_DISCOUNTS_V3 as _SERVICE_PAID_FORTNIGHTLY_DISCOUNTS_V3,
)


PAID_FORTNIGHTLY_DISCOUNTS_V3: dict[str, object] = deepcopy(
    _SERVICE_PAID_FORTNIGHTLY_DISCOUNTS_V3
)
PASS = "PASS"
BLOCKED = "BLOCKED"
RUNTIME_MANIFEST_ENV = "REWARD_ROLLOUT_RUNTIME_MANIFEST"
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SENSITIVE_KEY_RE = re.compile(
    r"(?:authorization|cookie|credential|init[_-]?data|password|private[_-]?key|qr|secret|subscription[_-]?url|token)",
    re.IGNORECASE,
)
_TERMINAL_MERGE_REVIEW_STATUSES = ("closed", "dismissed", "resolved")


class RolloutRuntimeError(RuntimeError):
    """Stable fail-closed error raised by a rollout runtime boundary."""

    def __init__(self, code: str):
        self.code = str(code)
        super().__init__(self.code)


@dataclass(frozen=True, slots=True)
class InstanceReport:
    """Secret-free state reported by one API or bot instance."""

    component: str
    candidate: str
    wheel_enabled: bool
    calendar_enabled: bool
    legacy_reward_mutator_accepting: bool
    instance_id: str = ""


@dataclass(frozen=True, slots=True)
class RuntimeSnapshot:
    """Aggregated runtime and account-foundation state used by rollout guards."""

    instances: tuple[InstanceReport, ...]
    unresolved_users: int
    invalid_merge_chains: int
    canonical_accounts: int
    reward_state_accounts: int


@dataclass(frozen=True, slots=True)
class ConfigMutation:
    """Transactional wheel-config result retained in memory for verification."""

    previous: dict[str, object] | None
    readback: dict[str, object] | None
    committed: bool


@dataclass(frozen=True, slots=True)
class RolloutResult:
    """Safe command result whose summary excludes raw configuration values."""

    operation: str
    status: str
    candidate: str
    codes: tuple[str, ...] = ()
    evidence_path: Path | None = None
    counts: Mapping[str, int] = field(default_factory=dict)
    readback: dict[str, object] | None = None

    def safe_summary(self) -> dict[str, object]:
        return {
            "operation": self.operation,
            "status": self.status,
            "candidate": self.candidate,
            "codes": list(self.codes),
            "evidence_path": str(self.evidence_path) if self.evidence_path else None,
            "counts": dict(self.counts),
        }


class RewardRolloutRuntime(Protocol):
    """Runtime operations required by the rollout command functions."""

    def snapshot(self) -> RuntimeSnapshot: ...

    def backfill_reward_states(self) -> Mapping[str, int]: ...

    def configure_wheel(self, payload: dict[str, object]) -> ConfigMutation: ...

    def read_wheel_config(self) -> dict[str, object] | None: ...


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def canonical_json(payload: object) -> bytes:
    """Encode a value deterministically for comparison and SHA-256 evidence."""

    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _hash_summary(payload: object) -> dict[str, object]:
    key_count = len(payload) if isinstance(payload, Mapping) else 0
    return {
        "present": payload is not None,
        "key_count": int(key_count),
        "sha256": hashlib.sha256(canonical_json(payload)).hexdigest(),
    }


def _write_evidence(evidence_dir: Path, filename: str, payload: Mapping[str, object]) -> Path:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    if evidence_dir.is_symlink():
        raise RolloutRuntimeError("evidence_dir_symlink_rejected")
    destination = evidence_dir / filename
    if destination.exists():
        if destination.is_symlink():
            raise RolloutRuntimeError("evidence_file_symlink_rejected")
        raise RolloutRuntimeError("evidence_file_exists")
    if destination.is_symlink():
        raise RolloutRuntimeError("evidence_file_symlink_rejected")
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
    except FileExistsError as exc:
        raise RolloutRuntimeError("evidence_file_exists") from exc
    except OSError as exc:
        raise RolloutRuntimeError("evidence_write_failed") from exc
    return destination


def _base_evidence(*, operation: str, candidate: str, status: str, codes: Sequence[str]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "operation": operation,
        "candidate": candidate,
        "observed_at": _utcnow().isoformat(),
        "status": status,
        "codes": list(codes),
    }


def _snapshot_counts(snapshot: RuntimeSnapshot) -> dict[str, int]:
    components = Counter(report.component for report in snapshot.instances)
    return {
        "api_instances": int(components.get("api", 0)),
        "bot_instances": int(components.get("bot", 0)),
        "canonical_accounts": int(snapshot.canonical_accounts),
        "reward_state_accounts": int(snapshot.reward_state_accounts),
        "unresolved_users": int(snapshot.unresolved_users),
        "invalid_merge_chains": int(snapshot.invalid_merge_chains),
        "legacy_bot_mutator_count": sum(
            1 for report in snapshot.instances if report.legacy_reward_mutator_accepting
        ),
        "enabled_wheel_instance_count": sum(1 for report in snapshot.instances if report.wheel_enabled),
        "enabled_calendar_instance_count": sum(1 for report in snapshot.instances if report.calendar_enabled),
    }


def _preflight_codes(snapshot: RuntimeSnapshot, *, candidate: str) -> tuple[str, ...]:
    codes: list[str] = []
    if snapshot.unresolved_users or snapshot.invalid_merge_chains:
        codes.append("account_foundation_unresolved")

    relevant = tuple(report for report in snapshot.instances if report.component in {"api", "bot"})
    components = {report.component for report in relevant}
    if components != {"api", "bot"}:
        codes.append("runtime_instance_reports_incomplete")
    if any(report.wheel_enabled or report.calendar_enabled for report in relevant):
        codes.append("reward_flags_not_disabled")
    if any(report.candidate.lower() != candidate for report in relevant):
        codes.append("candidate_mismatch")
    if any(report.legacy_reward_mutator_accepting for report in relevant):
        codes.append("legacy_bot_not_quiesced")
    return tuple(codes)


def _snapshot_or_block(runtime: RewardRolloutRuntime) -> tuple[RuntimeSnapshot | None, tuple[str, ...]]:
    try:
        return runtime.snapshot(), ()
    except RolloutRuntimeError as exc:
        return None, (exc.code,)
    except Exception:
        return None, ("runtime_snapshot_unavailable",)


def run_preflight(
    runtime: RewardRolloutRuntime,
    *,
    candidate: str,
    evidence_dir: Path,
) -> RolloutResult:
    """Evaluate read-only fleet/account guards and retain one preflight record."""

    candidate = _normalize_candidate(candidate)
    snapshot, snapshot_codes = _snapshot_or_block(runtime)
    codes = snapshot_codes if snapshot is None else _preflight_codes(snapshot, candidate=candidate)
    status = PASS if not codes else BLOCKED
    counts = {} if snapshot is None else _snapshot_counts(snapshot)
    evidence = _base_evidence(operation="preflight", candidate=candidate, status=status, codes=codes)
    evidence["counts"] = counts
    evidence_path = _write_evidence(Path(evidence_dir), "preflight.json", evidence)
    return RolloutResult(
        operation="preflight",
        status=status,
        candidate=candidate,
        codes=codes,
        evidence_path=evidence_path,
        counts=counts,
    )


def run_backfill(
    runtime: RewardRolloutRuntime,
    *,
    candidate: str,
    evidence_dir: Path,
) -> RolloutResult:
    """Run the transactional reward-state backfill after a fresh preflight."""

    candidate = _normalize_candidate(candidate)
    snapshot, snapshot_codes = _snapshot_or_block(runtime)
    codes = list(snapshot_codes if snapshot is None else _preflight_codes(snapshot, candidate=candidate))
    counts: dict[str, int] = {} if snapshot is None else _snapshot_counts(snapshot)

    if not codes:
        try:
            backfill_counts = {str(key): int(value) for key, value in runtime.backfill_reward_states().items()}
            counts.update(backfill_counts)
            if backfill_counts.get("unresolved_users", 0) or backfill_counts.get("invalid_merge_chains", 0):
                codes.append("account_foundation_unresolved")
        except RolloutRuntimeError as exc:
            codes.append(exc.code)
        except Exception:
            codes.append("reward_state_backfill_failed")

    codes_tuple = tuple(dict.fromkeys(codes))
    status = PASS if not codes_tuple else BLOCKED
    evidence = _base_evidence(operation="backfill", candidate=candidate, status=status, codes=codes_tuple)
    evidence["counts"] = counts
    evidence_path = _write_evidence(Path(evidence_dir), "reward-state-backfill.json", evidence)
    return RolloutResult(
        operation="backfill",
        status=status,
        candidate=candidate,
        codes=codes_tuple,
        evidence_path=evidence_path,
        counts=counts,
    )


def run_configure(
    runtime: RewardRolloutRuntime,
    *,
    candidate: str,
    evidence_dir: Path,
) -> RolloutResult:
    """Write and read back the exact paid-fortnightly preset after all guards pass."""

    candidate = _normalize_candidate(candidate)
    snapshot, snapshot_codes = _snapshot_or_block(runtime)
    codes = list(snapshot_codes if snapshot is None else _preflight_codes(snapshot, candidate=candidate))
    counts = {} if snapshot is None else _snapshot_counts(snapshot)
    mutation: ConfigMutation | None = None

    if snapshot is not None and snapshot.reward_state_accounts != snapshot.canonical_accounts:
        codes.append("reward_state_backfill_incomplete")

    if not codes:
        try:
            mutation = runtime.configure_wheel(deepcopy(PAID_FORTNIGHTLY_DISCOUNTS_V3))
            if (
                not mutation.committed
                or mutation.readback != PAID_FORTNIGHTLY_DISCOUNTS_V3
            ):
                codes.append("wheel_config_readback_mismatch")
        except RolloutRuntimeError as exc:
            codes.append(exc.code)
        except Exception:
            codes.append("wheel_config_write_failed")

    codes_tuple = tuple(dict.fromkeys(codes))
    status = PASS if not codes_tuple else BLOCKED
    target_hash = _hash_summary(PAID_FORTNIGHTLY_DISCOUNTS_V3)
    evidence = _base_evidence(operation="configure", candidate=candidate, status=status, codes=codes_tuple)
    evidence.update(
        {
            "preset": "paid_fortnightly_discounts_v3",
            "sha256": target_hash["sha256"],
            "counts": counts,
            "previous": _hash_summary(mutation.previous if mutation else None),
            "target": target_hash,
            "readback": _hash_summary(mutation.readback if mutation else None),
            "committed": bool(mutation and mutation.committed),
        }
    )
    evidence_path = _write_evidence(Path(evidence_dir), "wheel-config.json", evidence)
    return RolloutResult(
        operation="configure",
        status=status,
        candidate=candidate,
        codes=codes_tuple,
        evidence_path=evidence_path,
        counts=counts,
        readback=deepcopy(mutation.readback) if mutation else None,
    )


def run_verify(
    runtime: RewardRolloutRuntime,
    *,
    candidate: str,
    evidence_dir: Path,
) -> RolloutResult:
    """Verify the disabled candidate, completed backfill, and exact config."""

    candidate = _normalize_candidate(candidate)
    snapshot, snapshot_codes = _snapshot_or_block(runtime)
    codes = list(snapshot_codes if snapshot is None else _preflight_codes(snapshot, candidate=candidate))
    counts = {} if snapshot is None else _snapshot_counts(snapshot)
    config: dict[str, object] | None = None

    if snapshot is not None and snapshot.reward_state_accounts != snapshot.canonical_accounts:
        codes.append("reward_state_backfill_incomplete")
    try:
        config = runtime.read_wheel_config()
        if config != PAID_FORTNIGHTLY_DISCOUNTS_V3:
            codes.append("wheel_config_readback_mismatch")
    except RolloutRuntimeError as exc:
        codes.append(exc.code)
    except Exception:
        codes.append("wheel_config_read_failed")

    codes_tuple = tuple(dict.fromkeys(codes))
    status = PASS if not codes_tuple else BLOCKED
    evidence = _base_evidence(operation="verify", candidate=candidate, status=status, codes=codes_tuple)
    evidence.update(
        {
            "counts": counts,
            "checks": {
                "preflight": snapshot is not None and not _preflight_codes(snapshot, candidate=candidate),
                "reward_state_complete": bool(
                    snapshot is not None and snapshot.reward_state_accounts == snapshot.canonical_accounts
                ),
                "wheel_config_exact": config == PAID_FORTNIGHTLY_DISCOUNTS_V3,
            },
            "wheel_config": _hash_summary(config),
        }
    )
    evidence_path = _write_evidence(Path(evidence_dir), "verify.json", evidence)
    return RolloutResult(
        operation="verify",
        status=status,
        candidate=candidate,
        codes=codes_tuple,
        evidence_path=evidence_path,
        counts=counts,
        readback=deepcopy(config),
    )


def _normalize_candidate(value: str) -> str:
    candidate = str(value or "").strip().lower()
    if not _SHA_RE.fullmatch(candidate):
        raise SystemExit("candidate must be a full 40-character hexadecimal Git SHA")
    return candidate


def _assert_secret_free_manifest(value: object, *, path: str = "manifest") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if _SENSITIVE_KEY_RE.search(key_text):
                raise RolloutRuntimeError("runtime_manifest_sensitive_field")
            _assert_secret_free_manifest(item, path=f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_secret_free_manifest(item, path=f"{path}[{index}]")
    elif isinstance(value, str) and len(value) > 4096:
        raise RolloutRuntimeError("runtime_manifest_value_too_large")


def _strict_bool(value: object, *, code: str) -> bool:
    if type(value) is not bool:
        raise RolloutRuntimeError(code)
    return bool(value)


class LiveRuntime:
    """Production adapter backed by a local fleet manifest and application DB."""

    def __init__(self, *, environ: Mapping[str, str] | None = None) -> None:
        self._environ = dict(os.environ if environ is None else environ)

    def _manifest_instances(self) -> tuple[InstanceReport, ...]:
        raw_path = str(self._environ.get(RUNTIME_MANIFEST_ENV) or "").strip()
        if not raw_path:
            raise RolloutRuntimeError("runtime_manifest_missing")
        path = Path(raw_path).expanduser()
        if not path.is_absolute() or not path.is_file() or path.is_symlink():
            raise RolloutRuntimeError("runtime_manifest_unavailable")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RolloutRuntimeError("runtime_manifest_invalid") from exc
        if not isinstance(payload, Mapping):
            raise RolloutRuntimeError("runtime_manifest_invalid")
        _assert_secret_free_manifest(payload)
        rows = payload.get("instances")
        if not isinstance(rows, list) or not rows:
            raise RolloutRuntimeError("runtime_manifest_instances_missing")

        reports: list[InstanceReport] = []
        instance_ids: set[str] = set()
        for raw in rows:
            if not isinstance(raw, Mapping):
                raise RolloutRuntimeError("runtime_manifest_instance_invalid")
            component = str(raw.get("component") or "").strip().lower()
            instance_id = str(raw.get("instance_id") or "").strip()
            candidate = str(raw.get("candidate") or "").strip().lower()
            if component not in {"api", "bot"} or not instance_id or instance_id in instance_ids:
                raise RolloutRuntimeError("runtime_manifest_instance_invalid")
            if not _SHA_RE.fullmatch(candidate):
                raise RolloutRuntimeError("runtime_manifest_candidate_invalid")
            instance_ids.add(instance_id)
            reports.append(
                InstanceReport(
                    component=component,
                    instance_id=instance_id,
                    candidate=candidate,
                    wheel_enabled=_strict_bool(
                        raw.get("bonus_wheel_enabled"),
                        code="runtime_manifest_flag_invalid",
                    ),
                    calendar_enabled=_strict_bool(
                        raw.get("bonus_calendar_enabled"),
                        code="runtime_manifest_flag_invalid",
                    ),
                    legacy_reward_mutator_accepting=_strict_bool(
                        raw.get("legacy_reward_mutator_accepting"),
                        code="runtime_manifest_legacy_state_invalid",
                    ),
                )
            )
        return tuple(reports)

    @staticmethod
    def _session_factory():
        from db import SessionLocal

        return SessionLocal

    @staticmethod
    def _account_counts(session: Any) -> tuple[int, int, int, int]:
        from economy_service import resolve_canonical_account_id
        from models import Account, AccountMergeReview, RewardAccountState, User

        account_ids = [str(row.id) for row in session.query(Account.id).order_by(Account.id.asc()).all()]
        known_account_ids = set(account_ids)
        resolutions: dict[str, str | None] = {}
        invalid_account_ids: set[str] = set()
        canonical_account_ids: set[str] = set()
        for account_id in account_ids:
            try:
                canonical_id = str(resolve_canonical_account_id(session, account_id=account_id))
            except ValueError:
                resolutions[account_id] = None
                invalid_account_ids.add(account_id)
                continue
            resolutions[account_id] = canonical_id
            canonical_account_ids.add(canonical_id)

        unresolved_users = 0
        for row in session.query(User.account_id).all():
            account_id = str(row.account_id or "").strip()
            if not account_id or account_id not in known_account_ids or resolutions.get(account_id) is None:
                unresolved_users += 1

        open_merge_reviews = (
            session.query(AccountMergeReview.id)
            .filter(~AccountMergeReview.status.in_(_TERMINAL_MERGE_REVIEW_STATUSES))
            .count()
        )
        state_ids = {
            str(row.account_id)
            for row in session.query(RewardAccountState.account_id)
            .filter(RewardAccountState.account_id.in_(sorted(canonical_account_ids)))
            .all()
        }
        return (
            unresolved_users,
            len(invalid_account_ids) + int(open_merge_reviews),
            len(canonical_account_ids),
            len(state_ids & canonical_account_ids),
        )

    def snapshot(self) -> RuntimeSnapshot:
        instances = self._manifest_instances()
        SessionLocal = self._session_factory()
        try:
            with SessionLocal() as session:
                unresolved, invalid_chains, canonical_accounts, reward_states = self._account_counts(session)
        except RolloutRuntimeError:
            raise
        except Exception as exc:
            raise RolloutRuntimeError("account_foundation_read_failed") from exc
        return RuntimeSnapshot(
            instances=instances,
            unresolved_users=unresolved,
            invalid_merge_chains=invalid_chains,
            canonical_accounts=canonical_accounts,
            reward_state_accounts=reward_states,
        )

    def backfill_reward_states(self) -> Mapping[str, int]:
        from rewards_service import backfill_reward_account_states

        SessionLocal = self._session_factory()
        try:
            with SessionLocal() as session:
                with session.begin():
                    result = backfill_reward_account_states(session, now=_utcnow())
                    if not result.ready:
                        raise RolloutRuntimeError("account_foundation_unresolved")
                return {str(key): int(value) for key, value in asdict(result).items()}
        except RolloutRuntimeError:
            raise
        except Exception as exc:
            raise RolloutRuntimeError("reward_state_backfill_failed") from exc

    @staticmethod
    def _decode_setting(raw: object) -> dict[str, object] | None:
        if raw is None or str(raw).strip() == "":
            return None
        try:
            payload = json.loads(str(raw))
        except Exception as exc:
            raise RolloutRuntimeError("wheel_config_stored_json_invalid") from exc
        if not isinstance(payload, dict):
            raise RolloutRuntimeError("wheel_config_stored_shape_invalid")
        return payload

    def configure_wheel(self, payload: dict[str, object]) -> ConfigMutation:
        from models import AppSetting
        from rewards_service import parse_paid_weekly_config

        if payload != PAID_FORTNIGHTLY_DISCOUNTS_V3:
            raise RolloutRuntimeError("wheel_config_target_not_exact")
        parse_paid_weekly_config(payload, explicit=True)
        SessionLocal = self._session_factory()
        previous: dict[str, object] | None = None
        readback: dict[str, object] | None = None

        class _ReadbackMismatch(RuntimeError):
            pass

        try:
            with SessionLocal() as session:
                try:
                    with session.begin():
                        row = (
                            session.query(AppSetting)
                            .filter(AppSetting.key == "wheel_config")
                            .with_for_update()
                            .one_or_none()
                        )
                        previous = self._decode_setting(row.value_json if row is not None else None)
                        encoded = canonical_json(payload).decode("utf-8")
                        if row is None:
                            row = AppSetting(key="wheel_config", value_json=encoded)
                            session.add(row)
                        else:
                            row.value_json = encoded
                            row.updated_at = _utcnow().replace(tzinfo=None)
                        session.flush()
                        readback_row = (
                            session.query(AppSetting)
                            .filter(AppSetting.key == "wheel_config")
                            .one()
                        )
                        readback = self._decode_setting(readback_row.value_json)
                        if readback != payload:
                            raise _ReadbackMismatch()
                except _ReadbackMismatch:
                    return ConfigMutation(previous=previous, readback=readback, committed=False)
        except RolloutRuntimeError:
            raise
        except Exception as exc:
            raise RolloutRuntimeError("wheel_config_write_failed") from exc
        return ConfigMutation(previous=previous, readback=readback, committed=True)

    def read_wheel_config(self) -> dict[str, object] | None:
        from models import AppSetting

        SessionLocal = self._session_factory()
        try:
            with SessionLocal() as session:
                row = session.query(AppSetting).filter(AppSetting.key == "wheel_config").one_or_none()
                return self._decode_setting(row.value_json if row is not None else None)
        except RolloutRuntimeError:
            raise
        except Exception as exc:
            raise RolloutRuntimeError("wheel_config_read_failed") from exc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Guarded POKROV paid-reward rollout operations. Secrets are never accepted on the CLI.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("preflight", "backfill", "configure", "verify"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--candidate", required=True)
        subparser.add_argument("--evidence-dir", required=True, type=Path)
        if command in {"backfill", "configure"}:
            subparser.add_argument("--confirm-apply", default="")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    runtime: RewardRolloutRuntime | None = None,
) -> RolloutResult:
    """Parse one supported subcommand and return its secret-free result."""

    args = _build_parser().parse_args(list(argv) if argv is not None else None)
    candidate = _normalize_candidate(args.candidate)
    selected_runtime = runtime or LiveRuntime()

    expected_confirmation = {
        "backfill": "reward-state-v1",
        "configure": "paid_fortnightly_discounts_v3",
    }.get(args.command)
    if expected_confirmation is not None and args.confirm_apply != expected_confirmation:
        raise SystemExit(f"explicit confirmation required: --confirm-apply {expected_confirmation}")

    if args.command == "preflight":
        return run_preflight(selected_runtime, candidate=candidate, evidence_dir=args.evidence_dir)
    if args.command == "backfill":
        return run_backfill(selected_runtime, candidate=candidate, evidence_dir=args.evidence_dir)
    if args.command == "configure":
        return run_configure(selected_runtime, candidate=candidate, evidence_dir=args.evidence_dir)
    if args.command == "verify":
        return run_verify(selected_runtime, candidate=candidate, evidence_dir=args.evidence_dir)
    raise SystemExit("unsupported command")


if __name__ == "__main__":
    try:
        outcome = main()
    except RolloutRuntimeError as exc:
        print(json.dumps({"status": BLOCKED, "codes": [exc.code]}, ensure_ascii=False, sort_keys=True))
        raise SystemExit(1) from None
    print(json.dumps(outcome.safe_summary(), ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if outcome.status == PASS else 1)
