"""Run the local-only POKROV 1.2.0 FRKN/AWG2 reconciliation gate.

This gate proves source contracts, synthetic behavior and local host/control-
plane invariants. It never proves exact AAR/DLL network behavior, a physical
device, a live AWG server, RU-origin reachability, a cohort or RC promotion.
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
        raise ValueError("FRKN local evidence cannot be written under artifacts/releases")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


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


def build_steps(
    *,
    platform_root: Path,
    core_root: Path,
    client_root: Path,
    evidence_dir: Path,
    go_executable: str,
    flutter_executable: str,
) -> list[GateStep]:
    python = sys.executable
    pwsh = _executable("pwsh.exe", "pwsh")
    git = _executable("git.exe", "git")
    platform_tests = (
        "tests/test_awg2_lab_service.py",
        "tests/test_transport_catalog.py",
        "tests/test_network_rollout_api.py",
        "tests/test_admin_action_policy_coverage.py",
        "portal_bot/tests/test_app_first_service.py",
        "tests/test_client_ui_api_additions.py::test_awg2_owner_lab_is_device_bound_managed_only_and_kill_rolls_back",
        "tests/test_admin_action_intents.py::test_awg2_lab_material_intent_and_result_never_persist_endpoint_or_install",
    )
    return [
        GateStep(
            "cross-repo-contract-sync",
            "contract",
            (
                python,
                "scripts/verify_awg2_contract_sync.py",
                "--core-root",
                str(core_root),
                "--client-root",
                str(client_root),
                "--output",
                str(evidence_dir / "012-contract-sync.json"),
            ),
            platform_root,
        ),
        GateStep(
            "platform-awg-style",
            "platform",
            (
                python,
                "-m",
                "ruff",
                "check",
                "portal_bot/awg2_lab_service.py",
                "tests/test_awg2_lab_service.py",
                "scripts/verify_awg2_contract_sync.py",
                "tests/test_verify_awg2_contract_sync.py",
                "scripts/release_1_2_frkn_gate.py",
                "tests/test_release_1_2_frkn_gate.py",
            ),
            platform_root,
        ),
        GateStep(
            "platform-awg-contract-tests",
            "platform",
            (python, "-m", "pytest", "-q", *platform_tests),
            platform_root,
        ),
        GateStep(
            "platform-gate-tests",
            "platform",
            (
                python,
                "-m",
                "pytest",
                "-q",
                "tests/test_verify_awg2_contract_sync.py",
                "tests/test_release_1_2_frkn_gate.py",
            ),
            platform_root,
        ),
        GateStep(
            "platform-doc-contracts",
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
        GateStep(
            "platform-script-manifest",
            "documentation",
            (python, "scripts/check_script_manifest.py"),
            platform_root,
        ),
        GateStep(
            "platform-doc-links",
            "documentation",
            (python, "scripts/check-links.py"),
            platform_root,
        ),
        GateStep(
            "core-contract-and-tests",
            "core",
            (
                pwsh,
                "-NoProfile",
                "-File",
                "scripts/test.ps1",
                "-GoExecutable",
                go_executable,
            ),
            core_root,
        ),
        GateStep(
            "client-runtime-analyze",
            "client",
            (flutter_executable, "analyze"),
            client_root / "packages" / "runtime_engine",
        ),
        GateStep(
            "client-runtime-tests",
            "client",
            (flutter_executable, "test", "test/runtime_engine_test.dart"),
            client_root / "packages" / "runtime_engine",
        ),
        GateStep(
            "platform-diff-check",
            "repository",
            (git, "diff", "--check"),
            platform_root,
        ),
        GateStep(
            "core-diff-check",
            "repository",
            (git, "diff", "--check"),
            core_root,
        ),
        GateStep(
            "client-diff-check",
            "repository",
            (git, "diff", "--check"),
            client_root,
        ),
    ]


def manual_lanes() -> list[dict[str, object]]:
    return [
        {"id": "owned-awg-server", "status": "NOT_AUTHORIZED", "required_for_candidate": True},
        {"id": "exact-android-aar-network", "status": "MANUAL_OWNER_TEST", "required_for_candidate": True},
        {"id": "exact-windows-dll-network", "status": "MANUAL_OWNER_TEST", "required_for_candidate": True},
        {"id": "physical-device-lifecycle", "status": "MANUAL_OWNER_TEST", "required_for_candidate": True},
        {"id": "battery-cpu-thermal-baseline", "status": "MANUAL_OWNER_TEST", "required_for_candidate": True},
        {"id": "current-brain-ru-origin-matrix", "status": "BLOCKED_BY_ACCESS", "required_for_candidate": True},
        {"id": "bounded-opt-in-cohort", "status": "NOT_AUTHORIZED", "required_for_candidate": True},
        {"id": "exact-candidate-go-no-go", "status": "NOT_REQUESTED", "required_for_candidate": True},
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
    parser.add_argument("--core-root", type=Path, required=True)
    parser.add_argument("--client-root", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--go-executable", required=True)
    parser.add_argument("--flutter-executable", default=_executable("flutter.bat", "flutter"))
    parser.add_argument("--keep-going", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        platform_root = _validate_root(
            args.platform_root, Path("shared/product-facts.json"), "platform"
        )
        core_root = _validate_root(args.core_root, Path("config/release.json"), "Core")
        client_root = _validate_root(
            args.client_root, Path("packages/runtime_engine/pubspec.yaml"), "client"
        )
        evidence_dir = _validate_evidence_dir(args.evidence_dir, platform_root)
        steps = build_steps(
            platform_root=platform_root,
            core_root=core_root,
            client_root=client_root,
            evidence_dir=evidence_dir,
            go_executable=args.go_executable,
            flutter_executable=args.flutter_executable,
        )
        sources = {
            "platform": _git_identity(platform_root),
            "core": _git_identity(core_root),
            "client": _git_identity(client_root),
        }
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"FRKN_LOCAL_GATE_PREFLIGHT_FAILED: {exc}", file=sys.stderr)
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
        "gate_id": "pokrov.release-1.2.frkn-awg2.local",
        "gate_version": GATE_VERSION,
        "captured_at_utc": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "scope": "local_source_and_synthetic_only",
        "sources": sources,
        "steps": [asdict(result) for result in results],
        "local_status": local_status,
        "manual_lanes": manual_lanes(),
        "candidate_proven": False,
        "ru_ready": False,
        "cohort_status": "NOT_AUTHORIZED",
        "promotion_status": "NOT_REQUESTED",
    }
    report_path = evidence_dir / "012-local-frkn-awg2-gate.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "candidate_proven": False,
                "local_status": local_status,
                "report": str(report_path),
                "ru_ready": False,
            },
            sort_keys=True,
        )
    )
    if args.dry_run:
        return 3
    return 0 if local_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
