from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _npm_exec() -> str:
    return "npm.cmd" if os.name == "nt" else "npm"


@dataclass
class GateResult:
    name: str
    command: str
    returncode: int
    duration_sec: float
    output_tail: str


def _run_cmd(*, name: str, command: list[str], cwd: Path) -> GateResult:
    started = time.perf_counter()
    proc = subprocess.run(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    duration = time.perf_counter() - started
    out = (proc.stdout or "").strip()
    tail = "\n".join(out.splitlines()[-40:]) if out else ""
    return GateResult(
        name=name,
        command=" ".join(command),
        returncode=int(proc.returncode),
        duration_sec=duration,
        output_tail=tail,
    )


def _render_markdown(results: list[GateResult]) -> str:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ok = all(r.returncode == 0 for r in results)
    lines: list[str] = []
    lines.append("# Release Gate Report")
    lines.append("")
    lines.append(f"- Generated at: `{created_at}`")
    lines.append(f"- Status: `{'PASS' if ok else 'FAIL'}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Gate | Exit code | Duration (s) |")
    lines.append("|---|---:|---:|")
    for r in results:
        lines.append(f"| {r.name} | {r.returncode} | {r.duration_sec:.2f} |")
    lines.append("")
    lines.append("## Command Tails")
    lines.append("")
    for r in results:
        lines.append(f"### {r.name}")
        lines.append("")
        lines.append(f"- Command: `{r.command}`")
        lines.append(f"- Exit: `{r.returncode}`")
        lines.append("")
        lines.append("```text")
        lines.append(r.output_tail or "<no output>")
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local release gates and save markdown report.")
    parser.add_argument(
        "--output",
        default="docs/audit-artifacts/release_gate_report.md",
        help="Output markdown file path (relative to repository root).",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run a shorter gate set.",
    )
    args = parser.parse_args()

    gates: list[tuple[str, list[str], Path]] = [
        ("Backend unit tests", [sys.executable, "-m", "unittest", "discover", "tests"], REPO_ROOT),
        ("Admin/auth regressions", [sys.executable, "-m", "unittest", "tests.test_api_auth_and_tickets"], REPO_ROOT),
        ("Public link checks", [sys.executable, "scripts/check-links.py"], REPO_ROOT),
        ("Marketing production build", [_npm_exec(), "run", "build"], REPO_ROOT / "marketing"),
        ("Admin webapp smoke", [sys.executable, "scripts/admin_webapp_smoke.py"], REPO_ROOT),
        ("WebApp production build", [_npm_exec(), "run", "build"], REPO_ROOT / "webapp"),
        ("UI visual smoke", [sys.executable, "scripts/ui_visual_smoke.py"], REPO_ROOT),
    ]
    if args.quick:
        gates = [
            ("Critical worker regression", [sys.executable, "-m", "unittest", "tests.test_worker_retention"], REPO_ROOT),
            ("Public link checks", [sys.executable, "scripts/check-links.py"], REPO_ROOT),
            ("Marketing production build", [_npm_exec(), "run", "build"], REPO_ROOT / "marketing"),
            ("Admin webapp smoke", [sys.executable, "scripts/admin_webapp_smoke.py"], REPO_ROOT),
            ("WebApp production build", [_npm_exec(), "run", "build"], REPO_ROOT / "webapp"),
            ("UI visual smoke", [sys.executable, "scripts/ui_visual_smoke.py"], REPO_ROOT),
        ]

    results: list[GateResult] = []
    for name, cmd, cwd in gates:
        print(f"[gate] {name}: {' '.join(cmd)}")
        results.append(_run_cmd(name=name, command=cmd, cwd=cwd))

    output_path = (REPO_ROOT / args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_render_markdown(results), encoding="utf-8")

    print(f"[report] {output_path}")
    for r in results:
        print(f"[result] {r.name}: exit={r.returncode} duration={r.duration_sec:.2f}s")

    return 0 if all(r.returncode == 0 for r in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
