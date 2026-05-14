from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from text_integrity import scan_mojibake


REPO_ROOT = Path(__file__).resolve().parents[1]
WEBAPP_ROOT = REPO_ROOT / "webapp"
ADMIN_ROOT = WEBAPP_ROOT / "src" / "app" / "(dashboard)" / "admin"
API_CLIENT = WEBAPP_ROOT / "src" / "lib" / "api.ts"

REQUIRED_ADMIN_ROUTES = [
    "dashboard/page.tsx",
    "users/page.tsx",
    "nodes/page.tsx",
    "tickets/page.tsx",
    "promos/page.tsx",
    "broadcast/page.tsx",
    "referrals/page.tsx",
    "bonuses/page.tsx",
]

REQUIRED_API_EXPORTS = [
    "adminSummary",
    "adminUsers",
    "adminUserCard",
    "adminTickets",
    "adminTicketReply",
    "adminBroadcast",
    "adminPlans",
    "adminLiveUpdates",
    "adminStartLinks",
    "adminWheelConfig",
    "adminMetricsTimeseries",
    "adminNodesTraffic",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _collect_admin_files() -> list[Path]:
    return sorted(p for p in ADMIN_ROOT.rglob("*.tsx") if p.is_file())


def _check_required_files() -> list[str]:
    issues: list[str] = []
    for rel in REQUIRED_ADMIN_ROUTES:
        path = ADMIN_ROOT / rel
        if not path.exists():
            issues.append(f"missing admin route file: {path}")
    return issues


def _check_api_exports() -> list[str]:
    issues: list[str] = []
    text = _read(API_CLIENT)
    for fn in REQUIRED_API_EXPORTS:
        if not re.search(rf"export\s+(?:async\s+)?function\s+{re.escape(fn)}\s*\(", text):
            issues.append(f"missing API export in api.ts: {fn}")
    return issues


def _check_legacy_bot_links() -> list[str]:
    issues: list[str] = []
    legacy_link_re = re.compile(r"(https?://t\.me/|@)portal_privacy_bot\b", re.IGNORECASE)
    source_roots = [
        WEBAPP_ROOT / "src",
        REPO_ROOT / "marketing" / "src",
    ]
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.suffix.lower() not in {".ts", ".tsx", ".js", ".jsx", ".md", ".html"}:
                continue
            text = _read(path)
            if legacy_link_re.search(text):
                issues.append(f"legacy bot link found: {path}")
    return issues


def _check_mojibake() -> list[str]:
    return [issue.format(REPO_ROOT) for issue in scan_mojibake(_collect_admin_files())]


def _run_webapp_build() -> tuple[int, str]:
    npm = "npm.cmd" if sys.platform.startswith("win") else "npm"
    proc = subprocess.run(
        [npm, "run", "build"],
        cwd=str(WEBAPP_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (proc.stdout or "").strip()
    tail = "\n".join(output.splitlines()[-60:]) if output else ""
    return int(proc.returncode), tail


def main() -> int:
    parser = argparse.ArgumentParser(description="Static smoke checks for Admin WebApp routes and bindings.")
    parser.add_argument("--build", action="store_true", help="Also run `npm run build` in webapp/")
    args = parser.parse_args()

    failures: list[str] = []
    failures.extend(_check_required_files())
    failures.extend(_check_api_exports())
    failures.extend(_check_legacy_bot_links())
    failures.extend(_check_mojibake())

    if args.build:
        code, tail = _run_webapp_build()
        if code != 0:
            failures.append("webapp build failed")
            if tail:
                print("[build tail]")
                print(tail)

    if failures:
        print("Admin WebApp smoke failed:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Admin WebApp smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
