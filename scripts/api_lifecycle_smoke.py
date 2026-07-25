from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_ROOT = REPO_ROOT / "tests"
DEFAULT_TARGET = "test_api_lifecycle_smoke.ApiLifecycleSmokeTests.test_api_only_lifecycle_covers_trial_connect_support_bonuses_and_purchase"


def _print_output(output: str) -> None:
    try:
        print(output)
    except UnicodeEncodeError:
        encoding = str(getattr(sys.stdout, "encoding", "") or "utf-8")
        escaped = output.encode(encoding, errors="backslashreplace").decode(encoding)
        print(escaped)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the API-only lifecycle smoke contour.")
    parser.add_argument(
        "--target",
        default=DEFAULT_TARGET,
        help="unittest target to execute.",
    )
    args = parser.parse_args()

    command = [sys.executable, "-m", "unittest", args.target]
    env = os.environ.copy()
    existing_pythonpath = str(env.get("PYTHONPATH") or "")
    env["PYTHONPATH"] = (
        str(TESTS_ROOT)
        if not existing_pythonpath
        else f"{TESTS_ROOT}{os.pathsep}{existing_pythonpath}"
    )
    proc = subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (proc.stdout or "").strip()
    if output:
        _print_output(output)
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
