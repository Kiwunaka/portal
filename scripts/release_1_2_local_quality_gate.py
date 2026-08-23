"""Run the bounded local quality gate for the POKROV 1.2.0 worktree set.

The result proves local source/worktree quality only. Physical devices, signed
exact candidates, provider flows and current/brain/RU origins stay explicit
manual or access-blocked lanes in the emitted report.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
GATE_VERSION = "1.0.0"
FORBIDDEN_EVIDENCE_SEGMENTS = ("artifacts", "releases")


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
        raise ValueError("local quality evidence cannot be written under artifacts/releases")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def build_steps(
    *,
    platform_root: Path,
    client_root: Path,
    core_root: Path,
    evidence_dir: Path,
) -> list[GateStep]:
    python = sys.executable
    flutter = _executable("flutter.bat", "flutter")
    npm = _executable("npm.cmd", "npm")
    powershell = _executable("pwsh.exe", "pwsh", "powershell.exe", "powershell")
    web_evidence = evidence_dir / "010I-local-web-performance-evidence.json"
    web_gate = evidence_dir / "010I-local-web-performance-gate.json"
    performance_tests = (
        "tests/test_performance_budget_gate.py",
        "tests/test_collect_web_performance.py",
        "tests/test_api_latency_probe.py",
        "tests/test_new_performance_evidence.py",
        "tests/test_release_1_2_local_quality_gate.py",
    )
    return [
        GateStep(
            "performance-contract",
            "performance",
            (python, "scripts/performance_budget_gate.py"),
            platform_root,
        ),
        GateStep(
            "performance-contract-tests",
            "unit",
            (python, "-m", "pytest", "-q", *performance_tests),
            platform_root,
        ),
        GateStep(
            "client-analyze",
            "client-static",
            (flutter, "analyze"),
            client_root / "packages" / "app_shell",
        ),
        GateStep(
            "client-widget-suite",
            "client-widget",
            (flutter, "test"),
            client_root / "packages" / "app_shell",
        ),
        GateStep(
            "client-seed-contract",
            "client-contract",
            (
                powershell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(client_root / "scripts" / "validate-seed.ps1"),
                "-PlatformRoot",
                str(platform_root),
                "-CoreRoot",
                str(core_root),
            ),
            client_root,
        ),
        GateStep(
            "client-docs-contract",
            "client-contract",
            (
                powershell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(client_root / "test" / "docs-contract.ps1"),
            ),
            client_root,
        ),
        GateStep(
            "webapp-lint",
            "web-component",
            (npm, "run", "lint"),
            platform_root / "webapp",
        ),
        GateStep(
            "webapp-build",
            "web-build",
            (npm, "run", "build"),
            platform_root / "webapp",
        ),
        GateStep(
            "webapp-cabinet-e2e",
            "web-e2e-a11y-responsive",
            (npm, "run", "test:e2e:cabinet"),
            platform_root / "webapp",
        ),
        GateStep(
            "marketing-build",
            "marketing-build",
            (npm, "run", "build"),
            platform_root / "marketing",
        ),
        GateStep(
            "marketing-seo",
            "marketing-contract",
            (npm, "run", "check:seo"),
            platform_root / "marketing",
        ),
        GateStep(
            "marketing-responsive-reduced-motion",
            "marketing-e2e-a11y-responsive",
            (npm, "run", "check:responsive"),
            platform_root / "marketing",
        ),
        GateStep(
            "adminapp-build-for-static-budget",
            "performance-input",
            (npm, "run", "build"),
            platform_root / "adminapp",
        ),
        GateStep(
            "web-static-performance-collect",
            "performance",
            (
                python,
                "scripts/collect_web_performance.py",
                "--candidate-label",
                "local-working-tree",
                "--output",
                str(web_evidence),
            ),
            platform_root,
        ),
        GateStep(
            "web-static-performance-gate",
            "performance",
            (
                python,
                "scripts/performance_budget_gate.py",
                "--evidence",
                str(web_evidence),
                "--required-scope",
                "local_static",
                "--output",
                str(web_gate),
            ),
            platform_root,
        ),
    ]


def _run_step(
    step: GateStep,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> StepResult:
    print(f"\n[RUN] {step.id}", flush=True)
    started = time.perf_counter()
    completed = runner(list(step.command), cwd=step.cwd, check=False)
    duration = round(time.perf_counter() - started, 3)
    status = "PASS" if completed.returncode == 0 else "FAIL"
    print(f"[{status}] {step.id} ({duration:.3f}s)", flush=True)
    return StepResult(
        id=step.id,
        category=step.category,
        status=status,
        exit_code=completed.returncode,
        duration_seconds=duration,
    )


def manual_lanes() -> list[dict[str, object]]:
    return [
        {
            "id": "candidate-device-performance",
            "status": "MANUAL_OWNER_TEST",
            "required_for_promotion": True,
            "reason": "Android/Windows cold start, connect, frame, idle CPU and memory require release artifacts on reference devices.",
        },
        {
            "id": "candidate-artifact-size-regression",
            "status": "MANUAL_OWNER_TEST",
            "required_for_promotion": True,
            "reason": "APK/installer observations require the exact candidate artifacts and a comparable prior baseline.",
        },
        {
            "id": "browser-lab-page-performance",
            "status": "MANUAL_OWNER_TEST",
            "required_for_promotion": True,
            "reason": "LCP, CLS, TBT and route-content latency require the selected browser/network lab environment.",
        },
        {
            "id": "controlled-origin-api-performance",
            "status": "BLOCKED_BY_ACCESS",
            "required_for_promotion": True,
            "reason": "Current-origin authenticated API samples need explicit environment and state-changing probe authorization.",
        },
        {
            "id": "exact-candidate-signing-device-origin",
            "status": "MANUAL_OWNER_TEST",
            "required_for_promotion": True,
            "reason": "Signing, physical device, current/brain/RU origin and post-promotion proof remain Phase 11.",
        },
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
            results.append(
                StepResult(
                    id=step.id,
                    category=step.category,
                    status="NOT_RUN",
                    exit_code=None,
                    duration_seconds=0,
                )
            )
            continue
        result = _run_step(step, runner=runner)
        results.append(result)
        if result.status == "FAIL" and not keep_going:
            stopped = True
    return results


def _write_report(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--client-root", type=Path, required=True)
    parser.add_argument("--core-root", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--keep-going", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        platform_root = _validate_root(
            args.platform_root, Path("shared/product-facts.json"), "platform"
        )
        client_root = _validate_root(
            args.client_root, Path("packages/app_shell/pubspec.yaml"), "client"
        )
        core_root = _validate_root(args.core_root, Path("go.mod"), "core")
        evidence_dir = _validate_evidence_dir(args.evidence_dir, platform_root)
        steps = build_steps(
            platform_root=platform_root,
            client_root=client_root,
            core_root=core_root,
            evidence_dir=evidence_dir,
        )
        sources = {
            "client": _git_identity(client_root),
            "core": _git_identity(core_root),
            "platform": _git_identity(platform_root),
        }
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"LOCAL_QUALITY_GATE_PREFLIGHT_FAILED: {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        results = [
            StepResult(step.id, step.category, "NOT_RUN", None, 0) for step in steps
        ]
    else:
        results = run_gate(steps=steps, keep_going=args.keep_going)
    local_status = (
        "PASS"
        if results and all(result.status == "PASS" for result in results)
        else "NOT_RUN"
        if all(result.status == "NOT_RUN" for result in results)
        else "FAIL"
    )
    payload: dict[str, object] = {
        "schema_version": 1,
        "gate_id": "pokrov.release-1.2.local-quality",
        "gate_version": GATE_VERSION,
        "captured_at_utc": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "scope": "local_worktree_only",
        "sources": sources,
        "steps": [asdict(result) for result in results],
        "local_status": local_status,
        "manual_lanes": manual_lanes(),
        "candidate_proven": False,
        "promotion_status": "MANUAL_OWNER_TEST",
    }
    report_path = evidence_dir / "010I-local-quality-gate.json"
    _write_report(report_path, payload)
    print(
        json.dumps(
            {
                "candidate_proven": False,
                "local_status": local_status,
                "promotion_status": "MANUAL_OWNER_TEST",
                "report": str(report_path),
            },
            sort_keys=True,
        )
    )
    if args.dry_run:
        return 3
    return 0 if local_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
