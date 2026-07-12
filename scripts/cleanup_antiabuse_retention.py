from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


from antiabuse_privacy_service import drain_antiabuse_retention, read_retention_backlog  # noqa: E402
from db import SessionLocal  # noqa: E402


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect or drain overdue first-party antiabuse raw-IP/HMAC fields.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Commit cleanup batches. Without this flag the command is read-only.",
    )
    parser.add_argument("--batch-limit", type=int, default=1000)
    args = parser.parse_args(argv)
    batch_limit = max(1, min(10_000, int(args.batch_limit)))
    now = _utcnow()
    before = read_retention_backlog(SessionLocal, now=now)

    drain = None
    after = dict(before)
    if args.apply:
        drain = drain_antiabuse_retention(
            SessionLocal,
            now=now,
            batch_limit=batch_limit,
        )
        after = read_retention_backlog(SessionLocal, now=now)

    payload = {
        "status": "APPLIED" if args.apply else "DRY_RUN",
        "observed_at": now.isoformat() + "Z",
        "batch_limit": batch_limit,
        "before": before,
        "after": after,
        "drain": drain,
    }
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
    return 0 if not args.apply or not any(after.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
