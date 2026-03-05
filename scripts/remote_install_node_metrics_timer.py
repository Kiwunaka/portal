from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
SERVICE_TEMPLATE = (REPO_ROOT / "infra" / "portal-node-metrics.service").read_text(encoding="utf-8")
TIMER_TEMPLATE = (REPO_ROOT / "infra" / "portal-node-metrics.timer").read_text(encoding="utf-8")


def _parse_password(path: Path) -> str:
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8", errors="replace").splitlines()]
    for i, ln in enumerate(lines):
        if "BRAINnode" in ln:
            for j in range(i + 1, min(i + 20, len(lines))):
                v = lines[j]
                if v and not v.startswith("ssh-ed25519 "):
                    return v
    return ""


def _run(ssh: paramiko.SSHClient, cmd: str, timeout: int = 120) -> tuple[int, str, str]:
    _stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    return code, stdout.read().decode(errors="replace"), stderr.read().decode(errors="replace")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Install and enable portal-node-metrics systemd timer on brain.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--workdir", default="/root/portal_bot")
    ap.add_argument("--collector-cmd", default="")
    ap.add_argument("--run-now", action="store_true", help="Trigger one immediate collection run after timer install.")
    args = ap.parse_args()

    password = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_password(Path(args.passwords))
    if not password:
        raise SystemExit("Missing brain password")

    collector_cmd = args.collector_cmd.strip() or f"{args.workdir.rstrip('/')}/venv/bin/python {args.workdir.rstrip('/')}/collect_node_metrics.py"
    service_body = SERVICE_TEMPLATE.replace("WorkingDirectory=/root/portal_bot", f"WorkingDirectory={args.workdir.rstrip('/')}").replace(
        "ExecStart=/root/portal_bot/venv/bin/python /root/portal_bot/collect_node_metrics.py", f"ExecStart={collector_cmd}"
    )
    timer_body = TIMER_TEMPLATE

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(args.brain_ip, port=args.ssh_port, username=args.ssh_user, password=password, timeout=30, banner_timeout=30, auth_timeout=30)
    try:
        sftp = ssh.open_sftp()
        try:
            with sftp.file("/etc/systemd/system/portal-node-metrics.service", "w") as f:
                f.write(service_body)
            with sftp.file("/etc/systemd/system/portal-node-metrics.timer", "w") as f:
                f.write(timer_body)
        finally:
            sftp.close()

        _run(ssh, "systemctl daemon-reload", timeout=30)
        _run(ssh, "systemctl enable portal-node-metrics.timer", timeout=30)
        _run(ssh, "systemctl restart portal-node-metrics.timer", timeout=30)
        if args.run_now:
            _run(ssh, "systemctl start portal-node-metrics.service", timeout=300)
        code, out, err = _run(ssh, "systemctl is-active portal-node-metrics.timer", timeout=30)
        print(f"timer={((out.strip() or err.strip()).strip() or 'unknown')}")
        if args.run_now:
            _, out_last_sqlite, err_last_sqlite = _run(
                ssh,
                "sqlite3 /root/portal_bot/portal.db \"select coalesce(max(sampled_at),'') from node_health_samples;\"",
                timeout=60,
            )
            _, out_last_pg, err_last_pg = _run(
                ssh,
                "runuser -u postgres -- psql -d portal -tAc \"select coalesce(to_char(max(sampled_at),'YYYY-MM-DD HH24:MI:SS.US'),'') from node_health_samples;\" 2>/dev/null || true",
                timeout=60,
            )
            sqlite_last = (out_last_sqlite.strip() or err_last_sqlite.strip()).strip()
            pg_last = (out_last_pg.strip() or err_last_pg.strip()).strip()
            print(f"last_sample_at_postgres={(pg_last or '-')}")
            print(f"last_sample_at_sqlite={(sqlite_last or '-')}")
            _, out_svc, err_svc = _run(
                ssh,
                "systemctl status portal-node-metrics.service --no-pager -l | head -n 25 || true",
                timeout=60,
            )
            status_text = (out_svc.strip() or err_svc.strip()).strip()
            if status_text:
                print(status_text)
        return 0 if code == 0 else 2
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
