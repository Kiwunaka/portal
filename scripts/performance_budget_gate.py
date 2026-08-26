"""Validate POKROV performance budgets and exact-environment evidence.

The gate is deliberately offline and standard-library only. It computes every
result from samples; an evidence producer cannot self-assert PASS.
"""

from __future__ import annotations

import argparse
import hashlib
from ipaddress import ip_address
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    REPO_ROOT
    / "shared"
    / "contracts"
    / "performance"
    / "performance-budgets.v1.json"
)
MAX_JSON_BYTES = 2 * 1024 * 1024
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
METRIC_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]{3,127}$")

SCOPES = frozenset(
    {
        "browser_lab",
        "candidate_artifact",
        "candidate_device",
        "controlled_origin",
        "local_static",
    }
)
STATISTICS = frozenset({"max", "mean", "p50", "p75", "p95", "p99", "sum"})
MEASUREMENT_STATES = frozenset(
    {"MEASURED", "MANUAL_OWNER_TEST", "BLOCKED_BY_ACCESS", "NOT_REQUESTED"}
)
WORKTREE_STATES = frozenset({"clean", "dirty"})
PLATFORMS = frozenset({"android", "client", "web", "windows"})
ENVIRONMENT_FIELDS = frozenset(
    {
        "architecture",
        "artifact_sha256",
        "build_mode",
        "captured_at_utc",
        "collector_id",
        "collector_version",
        "device_model",
        "idle_window_seconds",
        "interaction_scenario",
        "network_profile",
        "origin",
        "os_version",
        "platform",
        "power_mode",
        "proxy_policy",
        "source_address",
        "toolchain",
    }
)
REQUIRED_EVIDENCE_FIELDS = ENVIRONMENT_FIELDS | {"source_revision"}
BASE_ENVIRONMENT_FIELDS = frozenset(
    {
        "architecture",
        "build_mode",
        "captured_at_utc",
        "collector_id",
        "collector_version",
        "device_model",
        "network_profile",
        "origin",
        "os_version",
        "platform",
        "toolchain",
    }
)
FINGERPRINT_FIELDS = (
    "architecture",
    "build_mode",
    "collector_id",
    "collector_version",
    "device_model",
    "interaction_scenario",
    "network_profile",
    "origin",
    "os_version",
    "platform",
    "power_mode",
    "proxy_policy",
    "source_address",
    "toolchain",
)


class DuplicateJsonKey(ValueError):
    pass


class ContractError(ValueError):
    pass


@dataclass(frozen=True)
class GateOutcome:
    summary: dict[str, Any]
    has_budget_failure: bool


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKey("duplicate JSON object key")
        result[key] = value
    return result


def _load_json(path: Path) -> dict[str, Any]:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ContractError(f"cannot read {path}") from exc
    if size > MAX_JSON_BYTES:
        raise ContractError(f"JSON exceeds {MAX_JSON_BYTES} bytes")
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda _: (_ for _ in ()).throw(
                ValueError("non-finite number")
            ),
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ContractError(f"invalid JSON in {path}") from exc
    if not isinstance(value, dict):
        raise ContractError("top-level JSON value must be an object")
    return value


def _exact_keys(value: dict[str, Any], expected: Iterable[str], path: str) -> None:
    expected_set = set(expected)
    actual_set = set(value)
    missing = sorted(expected_set - actual_set)
    unknown = sorted(actual_set - expected_set)
    if missing or unknown:
        details = []
        if missing:
            details.append(f"missing={','.join(missing)}")
        if unknown:
            details.append(f"unknown={','.join(unknown)}")
        raise ContractError(f"{path}: {'; '.join(details)}")


def _nonempty_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{path}: expected non-empty string")
    return value.strip()


def _finite_number(value: Any, path: str, *, minimum: float = 0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{path}: expected number")
    result = float(value)
    if not math.isfinite(result) or result < minimum:
        raise ContractError(f"{path}: expected finite number >= {minimum}")
    return result


def _positive_int(value: Any, path: str, *, allow_zero: bool = False) -> int:
    minimum = 0 if allow_zero else 1
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ContractError(f"{path}: expected integer >= {minimum}")
    return value


def contract_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_collection(value: Any, path: str) -> None:
    if not isinstance(value, dict):
        raise ContractError(f"{path}: expected object")
    kind = value.get("kind")
    if kind == "critical_route_js_gzip":
        _exact_keys(value, {"kind", "routes"}, path)
        routes = value["routes"]
        if (
            not isinstance(routes, list)
            or not routes
            or any(not isinstance(route, str) or not route.startswith("/") for route in routes)
            or len(set(routes)) != len(routes)
        ):
            raise ContractError(f"{path}.routes: expected unique absolute route list")
        return
    if kind == "extension_sum":
        _exact_keys(value, {"extensions", "kind"}, path)
        extensions = value["extensions"]
        if (
            not isinstance(extensions, list)
            or not extensions
            or any(
                not isinstance(extension, str)
                or not extension.startswith(".")
                or extension.lower() != extension
                for extension in extensions
            )
            or len(set(extensions)) != len(extensions)
        ):
            raise ContractError(f"{path}.extensions: expected unique lowercase extensions")
        return
    raise ContractError(f"{path}.kind: unsupported collection kind")


def validate_budget_contract(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    _exact_keys(
        contract,
        {
            "budgets",
            "contract_id",
            "contract_version",
            "evidence_schema_version",
            "methodology",
            "release_line",
        },
        "contract",
    )
    if contract["contract_id"] != "pokrov.performance-budgets":
        raise ContractError("contract.contract_id: unsupported value")
    if not isinstance(contract["contract_version"], str) or not VERSION_RE.fullmatch(
        contract["contract_version"]
    ):
        raise ContractError("contract.contract_version: expected semantic version")
    if contract["evidence_schema_version"] != 1:
        raise ContractError("contract.evidence_schema_version: unsupported version")
    _nonempty_string(contract["release_line"], "contract.release_line")

    methodology = contract["methodology"]
    if not isinstance(methodology, dict):
        raise ContractError("contract.methodology: expected object")
    _exact_keys(
        methodology,
        {
            "comparison_rule",
            "measured_state",
            "non_measured_states",
            "percentile_method",
            "regression_formula",
        },
        "contract.methodology",
    )
    if methodology["percentile_method"] != "nearest_rank":
        raise ContractError("contract.methodology.percentile_method: unsupported value")
    if methodology["measured_state"] != "MEASURED":
        raise ContractError("contract.methodology.measured_state: unsupported value")
    if set(methodology["non_measured_states"]) != (
        MEASUREMENT_STATES - {"MEASURED"}
    ):
        raise ContractError("contract.methodology.non_measured_states: incomplete set")

    budgets = contract["budgets"]
    if not isinstance(budgets, list) or not budgets:
        raise ContractError("contract.budgets: expected non-empty array")
    by_id: dict[str, dict[str, Any]] = {}
    required = {
        "collector_id",
        "id",
        "max_regression_percent",
        "platform",
        "required_environment",
        "sampling",
        "scope",
        "statistic",
        "surface",
        "unit",
    }
    optional = {"collection", "stop_lte", "target_lte"}
    for index, budget in enumerate(budgets):
        path = f"contract.budgets[{index}]"
        if not isinstance(budget, dict):
            raise ContractError(f"{path}: expected object")
        actual = set(budget)
        missing = required - actual
        unknown = actual - required - optional
        if missing or unknown:
            raise ContractError(
                f"{path}: invalid keys missing={sorted(missing)} unknown={sorted(unknown)}"
            )
        metric_id = _nonempty_string(budget["id"], f"{path}.id")
        if not METRIC_ID_RE.fullmatch(metric_id) or metric_id in by_id:
            raise ContractError(f"{path}.id: invalid or duplicate metric id")
        if budget["scope"] not in SCOPES:
            raise ContractError(f"{path}.scope: unsupported scope")
        if budget["statistic"] not in STATISTICS:
            raise ContractError(f"{path}.statistic: unsupported statistic")
        if budget["platform"] not in PLATFORMS:
            raise ContractError(f"{path}.platform: unsupported platform")
        _nonempty_string(budget["surface"], f"{path}.surface")
        _nonempty_string(budget["unit"], f"{path}.unit")
        _nonempty_string(budget["collector_id"], f"{path}.collector_id")
        _finite_number(
            budget["max_regression_percent"],
            f"{path}.max_regression_percent",
        )
        if "target_lte" in budget:
            _finite_number(budget["target_lte"], f"{path}.target_lte")
        if "stop_lte" in budget:
            _finite_number(budget["stop_lte"], f"{path}.stop_lte")
        if "target_lte" in budget and "stop_lte" in budget:
            if float(budget["target_lte"]) > float(budget["stop_lte"]):
                raise ContractError(f"{path}: target_lte cannot exceed stop_lte")

        sampling = budget["sampling"]
        if not isinstance(sampling, dict):
            raise ContractError(f"{path}.sampling: expected object")
        _exact_keys(sampling, {"min_samples", "warmups"}, f"{path}.sampling")
        _positive_int(
            sampling["warmups"], f"{path}.sampling.warmups", allow_zero=True
        )
        _positive_int(sampling["min_samples"], f"{path}.sampling.min_samples")

        required_environment = budget["required_environment"]
        if (
            not isinstance(required_environment, list)
            or len(required_environment) != len(set(required_environment))
            or any(
                field not in REQUIRED_EVIDENCE_FIELDS
                for field in required_environment
            )
        ):
            raise ContractError(f"{path}.required_environment: invalid field list")
        if "collection" in budget:
            if budget["scope"] != "local_static":
                raise ContractError(f"{path}.collection: only local_static supports it")
            _validate_collection(budget["collection"], f"{path}.collection")
        elif budget["scope"] == "local_static":
            raise ContractError(f"{path}.collection: required for local_static")
        by_id[metric_id] = budget
    return by_id


def environment_fingerprint(environment: dict[str, Any]) -> str:
    normalized = {
        field: environment.get(field, "")
        for field in FINGERPRINT_FIELDS
    }
    payload = json.dumps(
        normalized, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _nearest_rank(samples: list[float], percentile: int) -> float:
    ordered = sorted(samples)
    index = max(0, math.ceil(len(ordered) * percentile / 100) - 1)
    return ordered[index]


def calculate_statistic(samples: list[float], statistic: str) -> float:
    if statistic == "max":
        return max(samples)
    if statistic == "mean":
        return sum(samples) / len(samples)
    if statistic == "sum":
        return sum(samples)
    if statistic.startswith("p"):
        return _nearest_rank(samples, int(statistic[1:]))
    raise ContractError(f"unsupported statistic: {statistic}")


def _validate_release(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("evidence.release: expected object")
    _exact_keys(
        value,
        {"candidate_label", "source_revision", "version", "working_tree_state"},
        "evidence.release",
    )
    _nonempty_string(value["candidate_label"], "evidence.release.candidate_label")
    _nonempty_string(value["version"], "evidence.release.version")
    source_revision = _nonempty_string(
        value["source_revision"], "evidence.release.source_revision"
    ).lower()
    if not REVISION_RE.fullmatch(source_revision):
        raise ContractError("evidence.release.source_revision: expected 40 hex chars")
    if value["working_tree_state"] not in WORKTREE_STATES:
        raise ContractError("evidence.release.working_tree_state: unsupported state")
    return value


def _validate_environment(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("evidence.environment: expected object")
    unknown = set(value) - ENVIRONMENT_FIELDS
    missing = BASE_ENVIRONMENT_FIELDS - set(value)
    if missing or unknown:
        raise ContractError(
            f"evidence.environment: missing={sorted(missing)} unknown={sorted(unknown)}"
        )
    for key, item in value.items():
        if key in {"idle_window_seconds"}:
            _finite_number(item, f"evidence.environment.{key}", minimum=1)
        else:
            _nonempty_string(item, f"evidence.environment.{key}")
    if value["platform"] not in {"android", "web", "windows"}:
        raise ContractError("evidence.environment.platform: unsupported platform")
    artifact_sha = value.get("artifact_sha256")
    if artifact_sha is not None and not SHA256_RE.fullmatch(artifact_sha):
        raise ContractError("evidence.environment.artifact_sha256: expected sha256")
    source_address = value.get("source_address")
    if source_address is not None:
        try:
            parsed_source_address = ip_address(source_address)
        except ValueError as exc:
            raise ContractError(
                "evidence.environment.source_address: expected literal IP"
            ) from exc
        if parsed_source_address.is_unspecified or parsed_source_address.is_multicast:
            raise ContractError(
                "evidence.environment.source_address: unsupported address"
            )
    proxy_policy = value.get("proxy_policy")
    if proxy_policy is not None and proxy_policy != "disabled_for_source_bound_probe":
        raise ContractError("evidence.environment.proxy_policy: unsupported policy")
    if (source_address is None) != (proxy_policy is None):
        raise ContractError(
            "evidence.environment: source_address and proxy_policy must appear together"
        )
    return value


def _validate_baseline(value: Any, path: str) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ContractError(f"{path}: expected object or null")
    _exact_keys(
        value,
        {"candidate_label", "environment_fingerprint", "source_revision", "value"},
        path,
    )
    _nonempty_string(value["candidate_label"], f"{path}.candidate_label")
    if not REVISION_RE.fullmatch(
        _nonempty_string(value["source_revision"], f"{path}.source_revision")
    ):
        raise ContractError(f"{path}.source_revision: expected 40 hex chars")
    if not SHA256_RE.fullmatch(
        _nonempty_string(
            value["environment_fingerprint"], f"{path}.environment_fingerprint"
        )
    ):
        raise ContractError(f"{path}.environment_fingerprint: expected sha256")
    _finite_number(value["value"], f"{path}.value")
    return value


def evaluate_evidence(
    contract: dict[str, Any],
    evidence: dict[str, Any],
    *,
    contract_path: Path,
    required_scopes: set[str] | None = None,
) -> GateOutcome:
    budgets = validate_budget_contract(contract)
    _exact_keys(
        evidence,
        {"budget_contract", "environment", "measurements", "release", "schema_version"},
        "evidence",
    )
    if evidence["schema_version"] != contract["evidence_schema_version"]:
        raise ContractError("evidence.schema_version: incompatible version")

    contract_ref = evidence["budget_contract"]
    if not isinstance(contract_ref, dict):
        raise ContractError("evidence.budget_contract: expected object")
    _exact_keys(
        contract_ref,
        {"id", "sha256", "version"},
        "evidence.budget_contract",
    )
    if contract_ref["id"] != contract["contract_id"]:
        raise ContractError("evidence.budget_contract.id: mismatch")
    if contract_ref["version"] != contract["contract_version"]:
        raise ContractError("evidence.budget_contract.version: mismatch")
    if contract_ref["sha256"] != contract_sha256(contract_path):
        raise ContractError("evidence.budget_contract.sha256: mismatch")

    release = _validate_release(evidence["release"])
    environment = _validate_environment(evidence["environment"])
    fingerprint = environment_fingerprint(environment)
    measurements = evidence["measurements"]
    if not isinstance(measurements, list):
        raise ContractError("evidence.measurements: expected array")

    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, measurement in enumerate(measurements):
        path = f"evidence.measurements[{index}]"
        if not isinstance(measurement, dict):
            raise ContractError(f"{path}: expected object")
        _exact_keys(
            measurement,
            {
                "baseline",
                "budget_id",
                "samples",
                "state",
                "unit",
                "warmup_samples_discarded",
            },
            path,
        )
        budget_id = _nonempty_string(measurement["budget_id"], f"{path}.budget_id")
        if budget_id in seen:
            raise ContractError(f"{path}.budget_id: duplicate measurement")
        seen.add(budget_id)
        budget = budgets.get(budget_id)
        if budget is None:
            raise ContractError(f"{path}.budget_id: unknown budget")
        if measurement["unit"] != budget["unit"]:
            raise ContractError(f"{path}.unit: budget mismatch")
        state = measurement["state"]
        if state not in MEASUREMENT_STATES:
            raise ContractError(f"{path}.state: unsupported state")
        warmups = _positive_int(
            measurement["warmup_samples_discarded"],
            f"{path}.warmup_samples_discarded",
            allow_zero=True,
        )
        samples_raw = measurement["samples"]
        if not isinstance(samples_raw, list):
            raise ContractError(f"{path}.samples: expected array")
        baseline = _validate_baseline(measurement["baseline"], f"{path}.baseline")

        result: dict[str, Any] = {
            "budget_id": budget_id,
            "scope": budget["scope"],
            "state": state,
            "gate_status": state,
            "sample_count": len(samples_raw),
            "statistic": budget["statistic"],
            "unit": budget["unit"],
        }
        if state != "MEASURED":
            if samples_raw or warmups or baseline is not None:
                raise ContractError(
                    f"{path}: non-measured evidence cannot carry samples, warmups or baseline"
                )
            results.append(result)
            continue

        if environment["collector_id"] != budget["collector_id"]:
            raise ContractError(f"{path}: collector_id does not own budget")
        budget_platform = budget["platform"]
        environment_platform = environment["platform"]
        if budget_platform in {"android", "windows", "web"}:
            if environment_platform != budget_platform:
                raise ContractError(f"{path}: environment platform mismatch")
        elif budget_platform == "client" and environment_platform not in {
            "android",
            "windows",
        }:
            raise ContractError(f"{path}: client metric requires Android or Windows")
        for field in budget["required_environment"]:
            if field == "source_revision":
                if not release["source_revision"]:
                    raise ContractError(f"{path}: missing source_revision")
            elif field not in environment or environment[field] in {"", None}:
                raise ContractError(f"{path}: missing environment field {field}")
        if warmups < budget["sampling"]["warmups"]:
            raise ContractError(f"{path}: insufficient discarded warmup samples")
        if len(samples_raw) < budget["sampling"]["min_samples"]:
            raise ContractError(f"{path}: insufficient retained samples")
        samples = [
            _finite_number(sample, f"{path}.samples[{sample_index}]")
            for sample_index, sample in enumerate(samples_raw)
        ]
        value = calculate_statistic(samples, budget["statistic"])
        stop_met = (
            True
            if "stop_lte" not in budget
            else value <= float(budget["stop_lte"])
        )
        target_met = (
            None
            if "target_lte" not in budget
            else value <= float(budget["target_lte"])
        )
        regression_percent: float | None = None
        regression_met = True
        if baseline is not None:
            if baseline["environment_fingerprint"] != fingerprint:
                raise ContractError(f"{path}.baseline: environment fingerprint mismatch")
            baseline_value = float(baseline["value"])
            if baseline_value <= 0:
                raise ContractError(f"{path}.baseline.value: must be > 0")
            regression_percent = ((value - baseline_value) / baseline_value) * 100
            regression_met = regression_percent <= float(
                budget["max_regression_percent"]
            )
        if "stop_lte" not in budget and baseline is None:
            gate_status = "BASELINE_RECORDED"
        else:
            gate_status = "PASS" if stop_met and regression_met else "FAIL"
        result.update(
            {
                "baseline_compared": baseline is not None,
                "environment_fingerprint": fingerprint,
                "gate_status": gate_status,
                "max_regression_percent": budget["max_regression_percent"],
                "regression_met": regression_met,
                "regression_percent": regression_percent,
                "stop_lte": budget.get("stop_lte"),
                "stop_met": stop_met,
                "target_lte": budget.get("target_lte"),
                "target_met": target_met,
                "value": value,
            }
        )
        results.append(result)

    required_scopes = required_scopes or set()
    unknown_scopes = required_scopes - SCOPES
    if unknown_scopes:
        raise ContractError(f"unsupported required scopes: {sorted(unknown_scopes)}")
    missing_required = sorted(
        budget_id
        for budget_id, budget in budgets.items()
        if budget["scope"] in required_scopes and budget_id not in seen
    )
    nonpassing_required = sorted(
        result["budget_id"]
        for result in results
        if result["scope"] in required_scopes
        and result["gate_status"] not in {"PASS", "BASELINE_RECORDED"}
    )
    failed = sorted(
        result["budget_id"]
        for result in results
        if result["gate_status"] == "FAIL"
    )
    has_budget_failure = bool(missing_required or nonpassing_required or failed)
    summary = {
        "schema_version": 1,
        "contract": {
            "id": contract["contract_id"],
            "sha256": contract_sha256(contract_path),
            "version": contract["contract_version"],
        },
        "release": release,
        "environment_fingerprint": fingerprint,
        "required_scopes": sorted(required_scopes),
        "results": results,
        "counts": {
            "baseline_recorded": sum(
                result["gate_status"] == "BASELINE_RECORDED" for result in results
            ),
            "failed": len(failed),
            "measured": sum(result["state"] == "MEASURED" for result in results),
            "non_measured": sum(result["state"] != "MEASURED" for result in results),
            "passed": sum(result["gate_status"] == "PASS" for result in results),
            "total": len(results),
        },
        "missing_required_budget_ids": missing_required,
        "nonpassing_required_budget_ids": nonpassing_required,
        "overall_status": "FAIL" if has_budget_failure else "PASS",
    }
    return GateOutcome(summary=summary, has_budget_failure=has_budget_failure)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument(
        "--required-scope", action="append", default=[], choices=sorted(SCOPES)
    )
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    contract_path = args.contract.resolve()
    try:
        contract = _load_json(contract_path)
        budgets = validate_budget_contract(contract)
        if args.evidence is None:
            summary = {
                "budget_count": len(budgets),
                "contract_id": contract["contract_id"],
                "contract_version": contract["contract_version"],
                "sha256": contract_sha256(contract_path),
                "status": "PASS",
            }
            has_failure = False
        else:
            evidence = _load_json(args.evidence.resolve())
            outcome = evaluate_evidence(
                contract,
                evidence,
                contract_path=contract_path,
                required_scopes=set(args.required_scope),
            )
            summary = outcome.summary
            has_failure = outcome.has_budget_failure
    except ContractError as exc:
        print(f"PERFORMANCE_CONTRACT_INVALID: {exc}", file=sys.stderr)
        return 2

    if args.output:
        _write_json(args.output.resolve(), summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 1 if has_failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
