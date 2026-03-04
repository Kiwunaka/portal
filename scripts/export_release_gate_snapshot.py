from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = REPO_ROOT / "docs" / "audit-artifacts" / "release_gate_report.md"
DEFAULT_HISTORY_DIR = REPO_ROOT / "docs" / "audit-artifacts" / "history"


def main() -> int:
    parser = argparse.ArgumentParser(description="Export release gate report to dated history snapshot.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--history-dir", default=str(DEFAULT_HISTORY_DIR))
    parser.add_argument("--stamp", default="", help="Optional stamp YYYYMMDD or YYYYMMDD_HHMM")
    args = parser.parse_args()

    report = Path(args.report).resolve()
    if not report.exists():
        raise SystemExit(f"Report not found: {report}")

    now = datetime.now(timezone.utc)
    stamp = (args.stamp or "").strip() or now.strftime("%Y%m%d")
    history_dir = Path(args.history_dir).resolve()
    history_dir.mkdir(parents=True, exist_ok=True)

    target = history_dir / f"release_gate_report_{stamp}.md"
    body = report.read_text(encoding="utf-8", errors="replace")

    snapshot = []
    snapshot.append(f"# Weekly Release Gate Snapshot ({stamp})")
    snapshot.append("")
    snapshot.append(f"- Exported UTC: `{now.isoformat()}`")
    snapshot.append(f"- Source report: `{report}`")
    snapshot.append("")
    snapshot.append(body)
    snapshot.append("")

    target.write_text("\n".join(snapshot), encoding="utf-8")
    print(f"[snapshot] {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
