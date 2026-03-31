from __future__ import annotations

import argparse
import secrets
import shlex
import sys
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from node_access import DEFAULT_PASSWORDS, connect_node


SERVICE_TEMPLATE = (REPO_ROOT / "infra" / "portal-node-observer.service").read_text(encoding="utf-8")
TIMER_TEMPLATE = (REPO_ROOT / "infra" / "portal-node-observer.timer").read_text(encoding="utf-8")
LOGROTATE_TEMPLATE = (REPO_ROOT / "infra" / "portal-node-observer.logrotate").read_text(encoding="utf-8")
COLLECTOR_SCRIPT = REPO_ROOT / "scripts" / "collect_xray_observer.py"


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
    _stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    return code, stdout.read().decode(errors="replace"), stderr.read().decode(errors="replace")


def _sql_quote(value: str) -> str:
    return "'" + str(value or "").replace("'", "''") + "'"


def _load_node_row(ssh: paramiko.SSHClient, *, node_code: str) -> tuple[str, str]:
    sql_text = (
        "select coalesce(host,''), coalesce(observer_push_secret,'') "
        f"from nodes where lower(code)={_sql_quote(str(node_code).strip().lower())};"
    )
    sql = "runuser -u postgres -- psql -d portal -Atc " + shlex.quote(sql_text)
    code, out, err = _run(ssh, sql, timeout=60)
    if code != 0:
        raise RuntimeError((err or out or "failed to query node observer state").strip())
    line = str(out or "").strip().splitlines()
    if not line or not line[0]:
        raise RuntimeError(f"node {node_code} is missing in control-plane")
    parts = line[0].split("|", 1)
    host = str(parts[0] or "").strip()
    secret = str(parts[1] or "").strip() if len(parts) > 1 else ""
    if not host:
        raise RuntimeError(f"node {node_code} has no host configured")
    return host, secret


def _ensure_observer_secret(ssh: paramiko.SSHClient, *, node_code: str) -> tuple[str, str, bool]:
    host, secret = _load_node_row(ssh, node_code=node_code)
    if secret:
        return host, secret, False

    generated = secrets.token_urlsafe(32)
    sql_text = (
        "update nodes "
        f"set observer_push_secret={_sql_quote(generated)} "
        f"where lower(code)={_sql_quote(str(node_code).strip().lower())} "
        "returning coalesce(host,''), coalesce(observer_push_secret,'');"
    )
    sql = "runuser -u postgres -- psql -d portal -Atc " + shlex.quote(sql_text)
    code, out, err = _run(ssh, sql, timeout=60)
    if code != 0:
        raise RuntimeError((err or out or "failed to save observer push secret").strip())
    line = str(out or "").strip().splitlines()
    if not line or not line[0]:
        raise RuntimeError(f"node {node_code} update returned no row")
    parts = line[0].split("|", 1)
    saved_host = str(parts[0] or "").strip() or host
    saved_secret = str(parts[1] or "").strip() if len(parts) > 1 else generated
    return saved_host, saved_secret, True


def _render_service(*, workdir: str) -> str:
    normalized = workdir.rstrip("/")
    return (
        SERVICE_TEMPLATE.replace("WorkingDirectory=/root/portal-node-observer", f"WorkingDirectory={normalized}")
        .replace("EnvironmentFile=-/root/portal-node-observer/observer.env", f"EnvironmentFile=-{normalized}/observer.env")
        .replace(
            "ExecStart=/usr/bin/env python3 /root/portal-node-observer/collect_xray_observer.py",
            f"ExecStart=/usr/bin/env python3 {normalized}/collect_xray_observer.py",
        )
    )


def _render_logrotate(*, log_path: str) -> str:
    return LOGROTATE_TEMPLATE.replace("/var/log/xray/access.log", str(log_path).strip())


def _render_env(
    *,
    api_url: str,
    node_code: str,
    secret: str,
    log_path: str,
    cursor_path: str,
) -> str:
    return "\n".join(
        [
            f"PORTAL_OBSERVER_API_URL={str(api_url).strip()}",
            f"PORTAL_OBSERVER_NODE_CODE={str(node_code).strip().lower()}",
            f"PORTAL_OBSERVER_SECRET={str(secret).strip()}",
            f"PORTAL_OBSERVER_LOG_PATH={str(log_path).strip()}",
            f"PORTAL_OBSERVER_CURSOR_PATH={str(cursor_path).strip()}",
            "",
        ]
    )


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Install portal-node-observer collector on a delivery node and wire its secret in control-plane.")
    parser.add_argument("--brain-ip", required=True)
    parser.add_argument("--node-code", required=True)
    parser.add_argument("--node-host", default="", help="Override node SSH host instead of reading nodes.host from control-plane")
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--api-url", default="https://api.pokrov.space/api/internal/observer/batches")
    parser.add_argument("--workdir", default="/root/portal-node-observer")
    parser.add_argument("--log-path", default="/var/log/xray/access.log")
    parser.add_argument("--cursor-path", default="/var/lib/portal-node-observer/cursor.json")
    parser.add_argument("--run-now", action="store_true")
    args = parser.parse_args()

    node_code = str(args.node_code or "").strip().lower()
    if not node_code:
        raise SystemExit("--node-code is required")

    brain_ssh, brain_auth = connect_node(
        code="brain",
        host=str(args.brain_ip).strip(),
        user=args.ssh_user,
        port=int(args.ssh_port),
        passwords_path=Path(args.passwords),
    )
    try:
        print(f"brain auth: {brain_auth}")
        db_host, secret, created = _ensure_observer_secret(brain_ssh, node_code=node_code)
    finally:
        brain_ssh.close()

    target_host = str(args.node_host or "").strip() or db_host
    target_ssh, node_auth = connect_node(
        code=node_code,
        host=target_host,
        user=args.ssh_user,
        port=int(args.ssh_port),
        passwords_path=Path(args.passwords),
    )
    try:
        print(f"node auth: {node_auth}")
        workdir = str(args.workdir).rstrip("/")
        cursor_parent = str(Path(args.cursor_path).parent).replace("\\", "/")
        log_parent = str(Path(args.log_path).parent).replace("\\", "/")
        service_body = _render_service(workdir=workdir)
        timer_body = TIMER_TEMPLATE
        env_body = _render_env(
            api_url=args.api_url,
            node_code=node_code,
            secret=secret,
            log_path=args.log_path,
            cursor_path=args.cursor_path,
        )
        logrotate_body = _render_logrotate(log_path=args.log_path)

        _run(
            target_ssh,
            f"mkdir -p {workdir} {cursor_parent} {log_parent} && touch {str(args.log_path).strip()}",
            timeout=60,
        )
        sftp = target_ssh.open_sftp()
        try:
            sftp.put(str(COLLECTOR_SCRIPT), f"{workdir}/collect_xray_observer.py")
            with sftp.file(f"{workdir}/observer.env", "w") as handle:
                handle.write(env_body)
            with sftp.file("/etc/systemd/system/portal-node-observer.service", "w") as handle:
                handle.write(service_body)
            with sftp.file("/etc/systemd/system/portal-node-observer.timer", "w") as handle:
                handle.write(timer_body)
            with sftp.file("/etc/logrotate.d/portal-node-observer", "w") as handle:
                handle.write(logrotate_body)
        finally:
            sftp.close()

        _run(target_ssh, f"chmod 700 {workdir} && chmod 600 {workdir}/observer.env {workdir}/collect_xray_observer.py", timeout=30)
        _run(target_ssh, "systemctl daemon-reload", timeout=30)
        _run(target_ssh, "systemctl enable portal-node-observer.timer", timeout=30)
        _run(target_ssh, "systemctl restart portal-node-observer.timer", timeout=30)
        if args.run_now:
            _run(target_ssh, "systemctl start portal-node-observer.service", timeout=300)

        code, out, err = _run(target_ssh, "systemctl is-active portal-node-observer.timer || true", timeout=30)
        timer_state = (out.strip() or err.strip()).strip() or "unknown"
        print(f"observer_secret_created={'yes' if created else 'no'}")
        print(f"target_host={target_host}")
        print(f"timer={timer_state}")

        if args.run_now:
            _, svc_out, svc_err = _run(
                target_ssh,
                "systemctl status portal-node-observer.service --no-pager -l | head -n 25 || true",
                timeout=60,
            )
            status_text = (svc_out.strip() or svc_err.strip()).strip()
            if status_text:
                print(status_text)
        return 0 if code == 0 else 2
    finally:
        target_ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
