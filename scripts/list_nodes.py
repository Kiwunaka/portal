from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="List nodes from the configured DATABASE_URL (or a provided sqlite DB path).")
    ap.add_argument(
        "--db",
        default="",
        help="path to sqlite portal DB (optional). If set, DATABASE_URL will be set to sqlite:///<db> for this run.",
    )
    args = ap.parse_args()

    if args.db:
        p = Path(args.db)
        if not p.exists():
            raise SystemExit(f"DB not found: {p}")
        os.environ["DATABASE_URL"] = f"sqlite:///{p.as_posix()}"

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "portal_bot"))

    from db import SessionLocal, init_db
    from models import Node

    init_db()
    s = SessionLocal()
    try:
        nodes = s.query(Node).order_by(Node.weight.desc()).all()
        if not nodes:
            print("No nodes in DB (legacy single-node fallback will be used).")
            return 0
        for n in nodes:
            print(
                f"{n.code:6} enabled={bool(n.enabled):5} weight={n.weight:4} "
                f"host={n.host} vless={n.vless_port} inbound={n.inbound_id} panel={n.panel_base_url}/{n.panel_path}"
            )
        return 0
    finally:
        s.close()


if __name__ == "__main__":
    raise SystemExit(main())
