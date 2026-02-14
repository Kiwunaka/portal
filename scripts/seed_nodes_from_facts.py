from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NODE_FACTS = sorted(REPO_ROOT.glob("node_facts-*.json"))[-1] if list(REPO_ROOT.glob("node_facts-*.json")) else None
DEFAULT_NODE_REALITY = sorted(REPO_ROOT.glob("node_reality-*.json"))[-1] if list(REPO_ROOT.glob("node_reality-*.json")) else None


DEFAULT_NAMES = {
    "pl": "Poland",
    "it": "Italy",
    "us": "United States",
    "nl": "Netherlands",
    "brain": "Germany",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def main() -> int:
    # Allow importing portal_bot modules when running from repo root.
    sys.path.insert(0, str(REPO_ROOT / "portal_bot"))

    from db import SessionLocal, init_db
    from models import Node

    ap = argparse.ArgumentParser(description="Seed nodes table from node_facts + node_reality files")
    ap.add_argument("--node-facts", default=str(DEFAULT_NODE_FACTS) if DEFAULT_NODE_FACTS else "", required=DEFAULT_NODE_FACTS is None)
    ap.add_argument("--node-reality", default=str(DEFAULT_NODE_REALITY) if DEFAULT_NODE_REALITY else "", required=DEFAULT_NODE_REALITY is None)
    ap.add_argument("--only", default="", help="comma-separated node codes")
    ap.add_argument("--host-mode", choices=["ip", "dns"], default="ip", help="host value to store in DB")
    ap.add_argument("--host-suffix", default="", help="if host-mode=dns: suffix like '.example.com' (host becomes code+suffix)")
    ap.add_argument(
        "--store-panel-creds",
        action="store_true",
        help="store panel user/pass in portal.db (NOT recommended for repo-tracked DB files). Prefer env vars NODE_<CODE>_PANEL_USER/PANEL_PASS.",
    )
    args = ap.parse_args()

    facts = _load(Path(args.node_facts))
    reality = _load(Path(args.node_reality))

    facts_map = {str(r.get("code")): r for r in facts.get("results", []) or []}
    reality_map = {str(r.get("code")): r for r in reality.get("results", []) or []}

    want = [c.strip() for c in args.only.split(",") if c.strip()]
    if not want:
        want = sorted(set(facts_map.keys()) & set(reality_map.keys()))

    init_db()
    s = SessionLocal()
    try:
        for code in want:
            if code not in facts_map:
                raise SystemExit(f"Missing {code} in node_facts ({args.node_facts})")
            if code not in reality_map:
                raise SystemExit(f"Missing {code} in node_reality ({args.node_reality})")

            f = facts_map[code]
            r = reality_map[code]

            ip = str(f.get("ip") or "").strip()
            if not ip:
                raise SystemExit(f"node_facts entry for {code} has no ip")

            panel_port = int(f["panel_port"])
            panel_path = str(f["panel_path"])
            panel_user = str(f.get("panel_user") or "")
            panel_pass = str(f.get("panel_pass") or "")

            host = ip
            if args.host_mode == "dns":
                if not args.host_suffix:
                    raise SystemExit("--host-suffix is required when --host-mode=dns")
                host = f"{code}{args.host_suffix}"

            n = s.query(Node).filter_by(code=code).first()
            if not n:
                n = Node(code=code)
                s.add(n)

            n.name = DEFAULT_NAMES.get(code, code.upper())
            n.host = host
            n.vless_port = int(r["vless_port"])
            n.reality_sni = str(r["reality_sni"])
            n.reality_pbk = str(r["reality_pbk"])
            n.reality_sid = str(r["reality_sid"])
            n.fingerprint = str(r.get("fingerprint") or "firefox")
            n.flow = str(r.get("flow") or "xtls-rprx-vision")
            n.panel_base_url = f"http://{ip}:{panel_port}"
            n.panel_path = panel_path
            if args.store_panel_creds:
                n.panel_user = panel_user
                n.panel_pass = panel_pass
            else:
                # Secrets must come from env on the control-plane host.
                n.panel_user = ""
                n.panel_pass = ""
            n.inbound_id = int(r["inbound_id"])
            n.enabled = True
            n.weight = 100

        s.commit()
        print(f"OK: seeded nodes: {', '.join(want)}")
        if args.store_panel_creds:
            print("Note: panel credentials were stored in portal.db.")
        else:
            print("Note: panel credentials were NOT stored in portal.db. Provide them via env vars on the control-plane host:")
            print("  NODE_<CODE>_PANEL_USER / NODE_<CODE>_PANEL_PASS (e.g. NODE_PL_PANEL_USER)")
        if args.host_mode == "dns":
            print("Reminder: ensure DNS A-records exist for each host.")
        return 0
    finally:
        s.close()


if __name__ == "__main__":
    raise SystemExit(main())
