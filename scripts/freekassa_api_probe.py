from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from node_access import connect_node


def _remote_python(source: str, method: str, payload: dict[str, object]) -> str:
    payload_json = json.dumps(payload, ensure_ascii=True)
    return (
        "cd /root/portal_bot && "
        "PYBIN=/root/portal_bot/venv/bin/python; "
        "if [ ! -x \"$PYBIN\" ]; then PYBIN=$(command -v python3); fi; "
        "\"$PYBIN\" - <<'PY'\n"
        "import asyncio, json\n"
        "import api\n"
        f"payload = json.loads({payload_json!r})\n"
        "async def run():\n"
        "    async with api.PaymentHttpRegistry() as registry:\n"
        f"        return await api._freekassa_api_request(source={source!r}, method={method!r}, data=payload, http_registry=registry)\n"
        "body = asyncio.run(run())\n"
        "print(json.dumps(body, ensure_ascii=False))\n"
        "PY"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Probe live FreeKassa orders/create from the brain host.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default="", help="Optional PASSWORDS.txt path for worktree-local node access.")
    ap.add_argument("--source", default="bot", choices=["bot", "site"])
    ap.add_argument("--method", default="orders/create")
    ap.add_argument("--amount", type=float, default=99.0)
    ap.add_argument("--currency", default="RUB")
    ap.add_argument("--description", default="PORTAL Start 30 days")
    ap.add_argument("--email", default="test@example.com")
    ap.add_argument("--ip", default="127.0.0.1")
    ap.add_argument("--payment-system-id", type=int, default=0)
    ap.add_argument("--data-json", default="")
    args = ap.parse_args()

    if args.data_json.strip():
        payload = json.loads(args.data_json)
    else:
        payload = {
            "paymentId": f"codex_api_{int(time.time())}_{uuid.uuid4().hex[:6]}",
            "amount": float(args.amount),
            "currency": str(args.currency or "RUB").strip().upper(),
            "description": args.description,
            "email": args.email,
        }
        if int(args.payment_system_id or 0) > 0:
            payload["i"] = int(args.payment_system_id)
        if str(args.ip or "").strip():
            payload["ip"] = str(args.ip).strip()

    ssh, auth_method = connect_node(
        code="brain",
        host=args.brain_ip,
        user=args.ssh_user,
        port=args.ssh_port,
        passwords_path=Path(args.passwords) if str(args.passwords or "").strip() else None,
    )
    try:
        print(f"brain auth: {auth_method}", file=sys.stderr)
        cmd = _remote_python(args.source, args.method, payload)
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=90)
        code = stdout.channel.recv_exit_status()
        out = stdout.read().decode(errors="replace")
        err = stderr.read().decode(errors="replace")
        if out.strip():
            print(out.strip())
        if err.strip():
            print(err.strip(), file=sys.stderr)
        return int(code or 0)
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
