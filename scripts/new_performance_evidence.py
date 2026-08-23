"""Create one normalized POKROV performance evidence record from raw samples."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from performance_budget_gate import (
    DEFAULT_CONTRACT,
    MEASUREMENT_STATES,
    ContractError,
    _load_json,
    contract_sha256,
    evaluate_evidence,
    validate_budget_contract,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _git_identity(repo_root: Path) -> tuple[str, str]:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip().lower()
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip()
    return revision, "dirty" if status else "clean"


def _load_samples(path: Path | None, *, state: str) -> list[float]:
    if state != "MEASURED":
        if path is not None:
            raise ContractError("non-measured evidence cannot use --samples")
        return []
    if path is None:
        raise ContractError("MEASURED evidence requires --samples")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not value:
        raise ContractError("samples JSON must be a non-empty numeric array")
    if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in value):
        raise ContractError("samples JSON must contain only numbers")
    return [float(item) for item in value]


def _baseline_from_summary(
    path: Path | None, *, budget_id: str
) -> dict[str, Any] | None:
    if path is None:
        return None
    summary = _load_json(path)
    release = summary.get("release")
    results = summary.get("results")
    if not isinstance(release, dict) or not isinstance(results, list):
        raise ContractError("baseline gate summary is incomplete")
    matches = [
        result
        for result in results
        if isinstance(result, dict) and result.get("budget_id") == budget_id
    ]
    if len(matches) != 1:
        raise ContractError("baseline gate summary does not contain one matching result")
    result = matches[0]
    if result.get("gate_status") not in {"PASS", "BASELINE_RECORDED"}:
        raise ContractError("baseline result is not an accepted measurement")
    return {
        "candidate_label": release.get("candidate_label"),
        "environment_fingerprint": result.get("environment_fingerprint"),
        "source_revision": release.get("source_revision"),
        "value": result.get("value"),
    }


def create_evidence(
    *,
    contract_path: Path,
    budget_id: str,
    environment_path: Path,
    samples_path: Path | None,
    state: str,
    warmups: int,
    baseline_summary_path: Path | None,
    repo_root: Path,
    candidate_label: str,
    release_version: str,
) -> dict[str, Any]:
    contract = _load_json(contract_path)
    budgets = validate_budget_contract(contract)
    budget = budgets.get(budget_id)
    if budget is None:
        raise ContractError("unknown budget id")
    if state not in MEASUREMENT_STATES:
        raise ContractError("unsupported measurement state")
    environment = _load_json(environment_path)
    samples = _load_samples(samples_path, state=state)
    baseline = _baseline_from_summary(baseline_summary_path, budget_id=budget_id)
    if state != "MEASURED":
        if warmups != 0 or baseline is not None:
            raise ContractError("non-measured evidence cannot carry warmups or baseline")
    revision, working_tree_state = _git_identity(repo_root)
    evidence = {
        "schema_version": contract["evidence_schema_version"],
        "budget_contract": {
            "id": contract["contract_id"],
            "sha256": contract_sha256(contract_path),
            "version": contract["contract_version"],
        },
        "release": {
            "candidate_label": candidate_label,
            "source_revision": revision,
            "version": release_version,
            "working_tree_state": working_tree_state,
        },
        "environment": environment,
        "measurements": [
            {
                "baseline": baseline,
                "budget_id": budget_id,
                "samples": samples,
                "state": state,
                "unit": budget["unit"],
                "warmup_samples_discarded": warmups,
            }
        ],
    }
    evaluate_evidence(
        contract,
        evidence,
        contract_path=contract_path,
        required_scopes=set(),
    )
    return evidence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--budget-id", required=True)
    parser.add_argument("--environment", type=Path, required=True)
    parser.add_argument("--samples", type=Path)
    parser.add_argument(
        "--state", choices=sorted(MEASUREMENT_STATES), default="MEASURED"
    )
    parser.add_argument("--warmups", type=int, default=0)
    parser.add_argument("--baseline-summary", type=Path)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--candidate-label", required=True)
    parser.add_argument("--release-version", default="1.2.0")
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = create_evidence(
            contract_path=args.contract.resolve(),
            budget_id=args.budget_id,
            environment_path=args.environment.resolve(),
            samples_path=args.samples.resolve() if args.samples else None,
            state=args.state,
            warmups=args.warmups,
            baseline_summary_path=(
                args.baseline_summary.resolve() if args.baseline_summary else None
            ),
            repo_root=args.repo_root.resolve(),
            candidate_label=args.candidate_label,
            release_version=args.release_version,
        )
    except (
        ContractError,
        OSError,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
    ) as exc:
        print(f"PERFORMANCE_EVIDENCE_CREATE_FAILED: {exc}", file=sys.stderr)
        return 2
    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"PERFORMANCE_EVIDENCE: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
