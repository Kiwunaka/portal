from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = "tests.test_api_lifecycle_smoke.ApiLifecycleSmokeTests.test_api_only_lifecycle_covers_trial_connect_support_bonuses_and_purchase"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the API-only lifecycle smoke contour.")
    parser.add_argument(
        "--target",
        default=DEFAULT_TARGET,
        help="unittest target to execute.",
    )
    args = parser.parse_args()

    command = [sys.executable, "-m", "unittest", args.target]
    proc = subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (proc.stdout or "").strip()
    if output:
        print(output)
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
