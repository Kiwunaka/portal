from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    # Allow importing portal_bot modules when running from repo root.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "portal_bot"))

    from db import SessionLocal, init_db
    from models import Node

    parser = argparse.ArgumentParser(description="Add or update a node in portal.db")
    parser.add_argument("--code", required=True, help="short code, e.g. us/de/nl")
    parser.add_argument("--name", required=True, help="display name, e.g. United States")
    parser.add_argument("--host", required=True, help="public host, e.g. us.<your-domain>")
    parser.add_argument("--vless-port", type=int, default=443)
    parser.add_argument("--reality-sni", required=True)
    parser.add_argument("--reality-pbk", required=True)
    parser.add_argument("--reality-sid", required=True)
    parser.add_argument("--fingerprint", default="firefox")
    parser.add_argument("--flow", default="xtls-rprx-vision")
    parser.add_argument("--panel-base-url", required=True, help="e.g. https://us.<your-domain>:8444")
    parser.add_argument("--panel-path", required=True, help="3x-ui path prefix")
    parser.add_argument("--panel-user", default="", help="prefer env NODE_<CODE>_PANEL_USER on control-plane")
    parser.add_argument("--panel-pass", default="", help="prefer env NODE_<CODE>_PANEL_PASS on control-plane")
    parser.add_argument("--inbound-id", type=int, required=True)
    parser.add_argument("--disabled", action="store_true")
    parser.add_argument("--weight", type=int, default=100)
    args = parser.parse_args()

    init_db()
    s = SessionLocal()
    try:
        n = s.query(Node).filter_by(code=args.code).first()
        if not n:
            n = Node(code=args.code)
            s.add(n)

        n.name = args.name
        n.host = args.host
        n.vless_port = args.vless_port
        n.reality_sni = args.reality_sni
        n.reality_pbk = args.reality_pbk
        n.reality_sid = args.reality_sid
        n.fingerprint = args.fingerprint
        n.flow = args.flow
        n.panel_base_url = args.panel_base_url
        n.panel_path = args.panel_path
        n.panel_user = args.panel_user
        n.panel_pass = args.panel_pass
        n.inbound_id = args.inbound_id
        n.enabled = not args.disabled
        n.weight = args.weight

        s.commit()
        print(f"OK: node {args.code} saved (enabled={n.enabled})")
        return 0
    finally:
        s.close()


if __name__ == "__main__":
    raise SystemExit(main())
