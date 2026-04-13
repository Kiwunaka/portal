from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"


def _parse_brain_password(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in raw.splitlines()]
    for i, line in enumerate(lines):
        if "BRAINnode" not in line:
            continue
        for j in range(i + 1, min(i + 30, len(lines))):
            value = lines[j].strip()
            if not value or value.startswith("ssh-ed25519 ") or value.startswith("ssh-rsa "):
                continue
            return value
    return ""


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 300) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


REMOTE_SCRIPT = r"""
import asyncio
import json
import os
from pathlib import Path
import sys

ROOT = Path.cwd()
for candidate in (ROOT, ROOT / "portal_bot"):
    text = str(candidate)
    if text not in sys.path:
        sys.path.insert(0, text)

ENV_PATH = ROOT / ".env"
if ENV_PATH.exists():
    loaded = False
    try:
        from dotenv import load_dotenv

        load_dotenv(ENV_PATH)
        loaded = True
    except Exception:
        loaded = False
    if not loaded:
        for raw_line in ENV_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if not key:
                continue
            os.environ.setdefault(key, value.strip().strip('"').strip("'"))

try:
    from portal_bot.db import SessionLocal
    from portal_bot.models import Node, User, UserNode
    from portal_bot.node_policy import canonical_free_node_code, node_is_free, paid_pool_node_codes, user_uses_free_pool

    def import_control_panel():
        from portal_bot.control_panel import ControlPanel

        return ControlPanel
except ModuleNotFoundError:
    from db import SessionLocal
    from models import Node, User, UserNode
    from node_policy import canonical_free_node_code, node_is_free, paid_pool_node_codes, user_uses_free_pool

    def import_control_panel():
        from control_panel import ControlPanel

        return ControlPanel


def node_base(code: str) -> str:
    raw = (code or "").strip().lower()
    for sep in ("_", "-", "."):
        if sep in raw:
            raw = raw.split(sep, 1)[0]
    if raw.endswith("free"):
        raw = raw[:-4]
    return raw


def active_paid_codes(session):
    rows = session.query(Node).order_by(Node.code.asc()).all()
    return sorted(dict.fromkeys(str(code or "").strip().lower() for code in paid_pool_node_codes(rows) if str(code or "").strip()))


def load_report(session, *, only_tg_id=None):
    target_codes = active_paid_codes(session)
    active_users = session.query(User).filter(User.is_active.is_(True)).order_by(User.created_at.asc(), User.tg_id.asc())
    if only_tg_id is not None:
        active_users = active_users.filter(User.tg_id == int(only_tg_id))
    active_user_rows = active_users.all()
    users = [
        user
        for user in active_user_rows
        if int(getattr(user, "tg_id", 0) or 0) > 0
        and not bool(getattr(user, "is_manual", False))
        and not user_uses_free_pool(user)
    ]

    mapped = {}
    rows = (
        session.query(UserNode.tg_id, Node.code)
        .join(Node, Node.id == UserNode.node_id)
        .all()
    )
    for tg_id, code in rows:
        mapped.setdefault(int(tg_id), set()).add((code or "").strip().lower())

    result_rows = []
    disallowed_rows = []
    free_code = str(canonical_free_node_code(session.query(Node).order_by(Node.code.asc()).all()) or "").strip().lower()
    missing_users = 0
    for user in users:
        user_codes = mapped.get(int(user.tg_id), set())
        missing = [code for code in target_codes if code not in user_codes]
        if user_uses_free_pool(user):
            disallowed = [code for code in sorted(user_codes) if code != free_code]
        else:
            disallowed = [code for code in sorted(user_codes) if node_is_free(code)]
        if missing:
            missing_users += 1
        if disallowed:
            disallowed_rows.append(
                {
                    "tg_id": int(user.tg_id),
                    "username": user.username,
                    "mapped": sorted(user_codes),
                    "disallowed": disallowed,
                }
            )
        result_rows.append(
            {
                "tg_id": int(user.tg_id),
                "username": user.username,
                "mapped": sorted(user_codes),
                "missing": sorted(missing),
            }
        )

    sub_type_counts = {}
    for user in active_user_rows:
        key = str(user.sub_type or "<null>")
        sub_type_counts[key] = int(sub_type_counts.get(key, 0)) + 1

    sample_active_users = [
        {
            "tg_id": int(user.tg_id),
            "username": user.username,
            "sub_type": user.sub_type,
            "current_plan_code": getattr(user, "current_plan_code", None),
            "is_active": bool(user.is_active),
        }
        for user in active_user_rows[:10]
    ]

    return {
        "active_paid_codes": target_codes,
        "paid_users": len(users),
        "missing_users": missing_users,
        "paid_users_with_disallowed_mappings": len(disallowed_rows),
        "disallowed_rows": disallowed_rows,
        "active_user_sub_type_counts": sub_type_counts,
        "sample_active_users": sample_active_users,
        "rows": result_rows,
    }


async def repair_missing(*, only_tg_id=None, limit=0):
    ControlPanel = import_control_panel()

    session = SessionLocal()
    try:
        report = load_report(session, only_tg_id=only_tg_id)
        rows = [row for row in report["rows"] if row["missing"]]
        if limit and limit > 0:
            rows = rows[:limit]
        if not rows:
            return {"planned": 0, "repaired": 0, "failed": 0, "details": []}

        user_index = {
            int(user.tg_id): user
            for user in session.query(User).filter(User.tg_id.in_([int(row["tg_id"]) for row in rows])).all()
        }
    finally:
        session.close()

    panel = ControlPanel()
    details = []
    repaired = 0
    failed = 0
    try:
        await panel.login()
        for row in rows:
            user = user_index.get(int(row["tg_id"]))
            if not user:
                failed += 1
                details.append(
                    {
                        "tg_id": int(row["tg_id"]),
                        "missing": row["missing"],
                        "ok": False,
                        "reason": "user_not_found",
                    }
                )
                continue
            sub_id = user.sub_token or str(user.tg_id)
            results = await panel.ensure_user_on_all_nodes(
                tg_id=int(user.tg_id),
                client_uuid=user.uuid,
                email=user.email,
                sub_id=sub_id,
                enable=bool(user.is_active),
                only_node_codes=list(row["missing"]),
            )
            ok = all(bool(results.get(code)) for code in row["missing"])
            if ok:
                repaired += 1
            else:
                failed += 1
            details.append(
                {
                    "tg_id": int(user.tg_id),
                    "missing": row["missing"],
                    "results": results,
                    "ok": ok,
                }
            )
    finally:
        await panel.close()
    return {"planned": len(rows), "repaired": repaired, "failed": failed, "details": details}


async def cleanup_disallowed(*, only_tg_id=None, limit=0):
    ControlPanel = import_control_panel()

    session = SessionLocal()
    try:
        report = load_report(session, only_tg_id=only_tg_id)
        rows = list(report["disallowed_rows"])
        if limit and limit > 0:
            rows = rows[:limit]
        if not rows:
            return {"planned": 0, "cleaned": 0, "failed": 0, "details": []}

        user_index = {
            int(user.tg_id): user
            for user in session.query(User).filter(User.tg_id.in_([int(row["tg_id"]) for row in rows])).all()
        }
        node_index = {
            str(node.code or "").strip().lower(): int(node.id)
            for node in session.query(Node).all()
            if getattr(node, "id", None) is not None
        }
    finally:
        session.close()

    panel = ControlPanel()
    details = []
    cleaned = 0
    failed = 0
    try:
        await panel.login()
        for row in rows:
            user = user_index.get(int(row["tg_id"]))
            if not user:
                failed += 1
                details.append(
                    {
                        "tg_id": int(row["tg_id"]),
                        "disallowed": row["disallowed"],
                        "ok": False,
                        "reason": "user_not_found",
                    }
                )
                continue

            results = await panel.set_existing_user_enabled_on_nodes(
                tg_id=int(user.tg_id),
                node_codes=list(row["disallowed"]),
                enable=False,
                sub_id=user.sub_token or str(user.tg_id),
            )

            session = SessionLocal()
            try:
                for code in row["disallowed"]:
                    node_id = node_index.get(str(code).lower())
                    if not node_id:
                        continue
                    session.query(UserNode).filter(
                        UserNode.tg_id == int(user.tg_id),
                        UserNode.node_id == int(node_id),
                    ).delete(synchronize_session=False)
                session.commit()
            finally:
                session.close()

            ok = all(bool(results.get(code)) for code in row["disallowed"])
            if ok:
                cleaned += 1
            else:
                failed += 1
            details.append(
                {
                    "tg_id": int(user.tg_id),
                    "disallowed": row["disallowed"],
                    "results": results,
                    "ok": ok,
                }
            )
    finally:
        await panel.close()
    return {"planned": len(rows), "cleaned": cleaned, "failed": failed, "details": details}


def main():
    raw_payload = sys.argv[1] if len(sys.argv) > 1 else globals().get("PAYLOAD", "{}")
    payload = json.loads(raw_payload)
    session = SessionLocal()
    try:
        before = load_report(session, only_tg_id=payload.get("only_tg_id"))
    finally:
        session.close()

    result = {"before": before}
    if payload.get("repair"):
        repair_result = asyncio.run(
            repair_missing(
                only_tg_id=payload.get("only_tg_id"),
                limit=int(payload.get("limit") or 0),
            )
        )
        session = SessionLocal()
        try:
            after = load_report(session, only_tg_id=payload.get("only_tg_id"))
        finally:
            session.close()
        result["repair"] = repair_result
        result["after"] = after
    if payload.get("cleanup_disallowed"):
        cleanup_result = asyncio.run(
            cleanup_disallowed(
                only_tg_id=payload.get("only_tg_id"),
                limit=int(payload.get("limit") or 0),
            )
        )
        session = SessionLocal()
        try:
            after_cleanup = load_report(session, only_tg_id=payload.get("only_tg_id"))
        finally:
            session.close()
        result["cleanup_disallowed"] = cleanup_result
        result["after_cleanup"] = after_cleanup
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit or repair premium user coverage across active paid nodes.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--repair", action="store_true")
    ap.add_argument("--cleanup-disallowed", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--tg-id", type=int, default=0)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    password = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_brain_password(Path(args.passwords))
    if not password:
        raise SystemExit("Missing brain password.")

    payload = {
        "repair": bool(args.repair),
        "cleanup_disallowed": bool(args.cleanup_disallowed),
        "limit": int(args.limit or 0),
        "only_tg_id": int(args.tg_id) if args.tg_id else None,
    }
    payload_b64 = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")
    remote = (
        "cd /root/portal_bot && "
        "/root/portal_bot/venv/bin/python - <<'PY'\n"
        "import base64\n"
        "import sys\n"
        f"PAYLOAD = base64.b64decode('{payload_b64}').decode('utf-8')\n"
        f"{REMOTE_SCRIPT}\n"
        "sys.argv = ['remote_paid_coverage', PAYLOAD]\n"
        "main()\n"
        "PY"
    )

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        args.brain_ip,
        port=args.ssh_port,
        username=args.ssh_user,
        password=password,
        timeout=30,
        banner_timeout=30,
        auth_timeout=30,
    )
    try:
        code, out, err = _run(ssh, remote, timeout=1800 if (args.repair or args.cleanup_disallowed) else 300)
    finally:
        ssh.close()

    if code != 0:
        raise SystemExit((err or out or "remote audit failed").strip())

    text = out.strip()
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(args.out)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
