"""Run the local-only POKROV 1.2.0 marketing-pilot readiness gate.

This gate never approves legal status, consent, a production provider, deploy,
user contact, campaign launch, pilot outcome or release-candidate promotion.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
GATE_VERSION = "1.0.0"


@dataclass(frozen=True)
class GateStep:
    id: str
    category: str
    command: tuple[str, ...]
    cwd: Path


@dataclass(frozen=True)
class StepResult:
    id: str
    category: str
    status: str
    exit_code: int | None
    duration_seconds: float


def _executable(*names: str) -> str:
    for name in names:
        resolved = shutil.which(name)
        if resolved:
            return resolved
    return names[-1]


def _git_identity(repo_root: Path) -> dict[str, str]:
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
    return {"revision": revision, "working_tree_state": "dirty" if status else "clean"}


def _validate_root(path: Path, marker: Path, label: str) -> Path:
    resolved = path.resolve()
    if not (resolved / marker).exists():
        raise ValueError(f"{label} root is missing {marker}")
    return resolved


def _validate_evidence_dir(path: Path, platform_root: Path) -> Path:
    resolved = path.resolve()
    forbidden = (platform_root / "artifacts" / "releases").resolve()
    try:
        resolved.relative_to(forbidden)
    except ValueError:
        pass
    else:
        raise ValueError("marketing pilot evidence cannot be written under artifacts/releases")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def build_steps(*, platform_root: Path, client_root: Path) -> list[GateStep]:
    python = sys.executable
    npm = _executable("npm.cmd", "npm")
    flutter = _executable("flutter.bat", "flutter")
    focused_tests = (
        "tests/test_marketing_governance.py",
        "tests/test_winback_pilot.py",
        "tests/test_winback_pilot_vectors.py",
        "tests/test_commercial_campaign_policy.py",
        "tests/test_commercial_offer_service.py",
        "tests/test_commercial_order_service.py",
        "tests/test_commercial_promo_surface_service.py",
        "tests/test_commercial_pilot_decision_service.py",
    )
    return [
        GateStep("commercial-contract-current", "contract", (python, "scripts/generate_commercial_contract.py", "--check"), platform_root),
        GateStep("marketing-governance-current", "contract", (python, "scripts/generate_marketing_governance.py", "--check"), platform_root),
        GateStep("marketing-governance-scan", "copy-legal", (python, "scripts/validate_marketing_governance.py"), platform_root),
        GateStep("winback-pilot-current", "contract", (python, "scripts/generate_winback_pilot.py", "--check"), platform_root),
        GateStep("script-manifest", "repository", (python, "scripts/check_script_manifest.py"), platform_root),
        GateStep("pilot-backend-contracts", "backend", (python, "-m", "pytest", "-q", *focused_tests), platform_root),
        GateStep(
            "pilot-operator-api",
            "backend-api",
            (
                python,
                "-m",
                "pytest",
                "-q",
                "tests/test_backend_route_gap_coverage.py::BackendRouteGapCoverageTests::test_admin_winback_pilot_decision_fails_closed_without_live_evidence",
            ),
            platform_root,
        ),
        GateStep("marketing-lint", "owned-web", (npm, "run", "lint"), platform_root / "marketing"),
        GateStep("marketing-build", "owned-web", (npm, "run", "build"), platform_root / "marketing"),
        GateStep("marketing-seo", "owned-web", (npm, "run", "check:seo"), platform_root / "marketing"),
        GateStep("marketing-responsive", "owned-web", (npm, "run", "check:responsive"), platform_root / "marketing"),
        GateStep("cabinet-lint", "owned-cabinet", (npm, "run", "lint"), platform_root / "webapp"),
        GateStep("cabinet-build", "owned-cabinet", (npm, "run", "build"), platform_root / "webapp"),
        GateStep("operator-center-lint", "operator-center", (npm, "run", "lint"), platform_root / "adminapp"),
        GateStep("operator-center-build", "operator-center", (npm, "run", "build"), platform_root / "adminapp"),
        GateStep("client-promo-analyze", "owned-app", (flutter, "analyze"), client_root / "packages" / "app_shell"),
        GateStep(
            "client-promo-tests",
            "owned-app",
            (flutter, "test", "test/app_first_runtime_bootstrap_test.dart"),
            client_root / "packages" / "app_shell",
        ),
        GateStep(
            "client-promo-render-test",
            "owned-app",
            (
                flutter,
                "test",
                "test/pokrov_seed_app_test.dart",
                "--plain-name",
                "home renders exact ready winback commercial terms",
            ),
            client_root / "packages" / "app_shell",
        ),
        GateStep(
            "docs-contract",
            "documentation",
            (
                python,
                "-m",
                "pytest",
                "-q",
                "tests/test_agent_docs_contract.py",
                "tests/test_check_script_manifest.py",
            ),
            platform_root,
        ),
        GateStep("docs-links", "documentation", (python, "scripts/check-links.py"), platform_root),
    ]


def manual_lanes() -> list[dict[str, object]]:
    return [
        {"id": "owner-legal-and-channel-approval", "status": "BLOCKED_BY_OWNER_DECISION", "required_for_external_pilot": True},
        {"id": "seller-offer-terms-publication", "status": "BLOCKED_BY_ACCESS", "required_for_external_pilot": True},
        {"id": "production-payment-provider", "status": "BLOCKED_BY_ACCESS", "required_for_external_pilot": True},
        {"id": "deployed-revision-and-live-capacity", "status": "BLOCKED_BY_ACCESS", "required_for_external_pilot": True},
        {"id": "holdout-percentage", "status": "BLOCKED_BY_OWNER_DECISION", "required_for_external_pilot": True},
        {"id": "channel-consent-support-and-rollback", "status": "MANUAL_OWNER_TEST", "required_for_external_pilot": True},
        {"id": "send-spend-launch", "status": "NOT_AUTHORIZED", "required_for_external_pilot": True},
        {"id": "d30-refund-support-incident-outcome", "status": "NOT_AUTHORIZED", "required_for_external_pilot": True},
    ]


def run_gate(
    *,
    steps: list[GateStep],
    keep_going: bool,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> list[StepResult]:
    results: list[StepResult] = []
    stopped = False
    for step in steps:
        if stopped:
            results.append(StepResult(step.id, step.category, "NOT_RUN", None, 0))
            continue
        print(f"\n[RUN] {step.id}", flush=True)
        started = time.perf_counter()
        completed = runner(list(step.command), cwd=step.cwd, check=False)
        duration = round(time.perf_counter() - started, 3)
        status = "PASS" if completed.returncode == 0 else "FAIL"
        print(f"[{status}] {step.id} ({duration:.3f}s)", flush=True)
        results.append(StepResult(step.id, step.category, status, completed.returncode, duration))
        if status == "FAIL" and not keep_going:
            stopped = True
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--client-root", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--keep-going", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        platform_root = _validate_root(args.platform_root, Path("shared/product-facts.json"), "platform")
        client_root = _validate_root(args.client_root, Path("packages/app_shell/pubspec.yaml"), "client")
        evidence_dir = _validate_evidence_dir(args.evidence_dir, platform_root)
        steps = build_steps(platform_root=platform_root, client_root=client_root)
        sources = {"platform": _git_identity(platform_root), "client": _git_identity(client_root)}
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"MARKETING_PILOT_GATE_PREFLIGHT_FAILED: {exc}", file=sys.stderr)
        return 2

    results = (
        [StepResult(step.id, step.category, "NOT_RUN", None, 0) for step in steps]
        if args.dry_run
        else run_gate(steps=steps, keep_going=args.keep_going)
    )
    local_status = (
        "PASS"
        if results and all(result.status == "PASS" for result in results)
        else "NOT_RUN"
        if all(result.status == "NOT_RUN" for result in results)
        else "FAIL"
    )
    report = {
        "schema_version": 1,
        "gate_id": "pokrov.release-1.2.marketing-pilot.local",
        "gate_version": GATE_VERSION,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "scope": "local_worktree_only",
        "sources": sources,
        "steps": [asdict(result) for result in results],
        "local_status": local_status,
        "external_pilot_status": "NOT_AUTHORIZED",
        "manual_lanes": manual_lanes(),
        "candidate_proven": False,
        "promotion_status": "NOT_REQUESTED",
    }
    report_path = evidence_dir / "011F-local-marketing-pilot-gate.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_proven": False, "local_status": local_status, "report": str(report_path)}, sort_keys=True))
    if args.dry_run:
        return 3
    return 0 if local_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
