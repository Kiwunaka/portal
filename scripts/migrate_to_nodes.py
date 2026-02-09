from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path


async def main_async() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "portal_bot"))

    from db import SessionLocal, init_db
    from models import User
    from nodes_repo import enabled_nodes
    from panel_client import PanelClient

    parser = argparse.ArgumentParser(description="Ensure all users exist on all enabled nodes")
    parser.add_argument("--node", default="", help="limit to node code (optional)")
    parser.add_argument("--only-active", action="store_true", help="sync only active users")
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()

    init_db()
    s = SessionLocal()
    try:
        nodes = enabled_nodes(s)
        if args.node:
            nodes = [n for n in nodes if n.code == args.node]
        if not nodes:
            print("No nodes to sync.")
            return 1

        q = s.query(User)
        if args.only_active:
            q = q.filter_by(is_active=True)
        users = q.order_by(User.created_at.asc()).all()
    finally:
        s.close()

    sem = asyncio.Semaphore(args.concurrency)

    async def sync_one(panel: PanelClient, u: User) -> bool:
        async with sem:
            sub_id = u.sub_token or str(u.tg_id)
            return await panel.ensure_client(
                tg_id=u.tg_id, client_uuid=u.uuid, email=u.email, sub_id=sub_id, enable=bool(u.is_active)
            )

    panels = [PanelClient(n) for n in nodes]
    try:
        for p in panels:
            ok = await p.login()
            if not ok:
                print(f"WARNING: login failed for node={p.node.code}")

        ok_total = 0
        fail_total = 0
        for p in panels:
            results = await asyncio.gather(*(sync_one(p, u) for u in users))
            ok = sum(1 for r in results if r)
            fail = sum(1 for r in results if not r)
            ok_total += ok
            fail_total += fail
            print(f"node={p.node.code}: ok={ok} fail={fail}")

        print(f"DONE: ok={ok_total} fail={fail_total}")
        return 0 if fail_total == 0 else 2
    finally:
        for p in panels:
            await p.close()


def main() -> int:
    return asyncio.run(main_async())


if __name__ == "__main__":
    raise SystemExit(main())

