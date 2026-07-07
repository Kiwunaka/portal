from __future__ import annotations

import argparse
import posixpath
import shlex
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
DEFAULT_SOURCE = REPO_ROOT / "infra" / "Caddyfile.internal"
DEFAULT_REMOTE_CONFIG = "/etc/caddy/Caddyfile"

if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from node_access import connect_node


class DeployError(RuntimeError):
    pass


def _run(ssh, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
    _stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    return code, out, err


def _require_ok(ssh, cmd: str, *, timeout: int = 120) -> tuple[str, str]:
    code, out, err = _run(ssh, cmd, timeout=timeout)
    if code != 0:
        raise DeployError(f"remote command failed ({code}): {cmd}\n{out}\n{err}")
    return out, err


def _upload_caddy_config(*, ssh, source: Path, remote_config: str, release_id: str) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"missing Caddy source config: {source}")

    remote_dir = posixpath.dirname(remote_config)
    remote_tmp = f"/tmp/pokrov-caddy-{release_id}.Caddyfile"
    backup = f"{remote_config}.bak-{release_id}"
    q_tmp = shlex.quote(remote_tmp)
    q_remote = shlex.quote(remote_config)
    q_backup = shlex.quote(backup)
    installed = False

    sftp = ssh.open_sftp()
    try:
        sftp.put(str(source), remote_tmp)
    finally:
        sftp.close()

    try:
        _require_ok(ssh, f"caddy validate --adapter caddyfile --config {q_tmp}", timeout=120)
        _require_ok(
            ssh,
            f"mkdir -p {shlex.quote(remote_dir)}; test ! -f {q_remote} || cp -a {q_remote} {q_backup}",
            timeout=120,
        )
        _require_ok(ssh, f"install -m 0644 {q_tmp} {q_remote}", timeout=120)
        installed = True
        _require_ok(ssh, f"caddy validate --adapter caddyfile --config {q_remote}", timeout=120)
        _require_ok(ssh, "systemctl reload caddy || systemctl restart caddy", timeout=180)
        _require_ok(ssh, "systemctl is-active caddy", timeout=60)
    except Exception:
        if installed:
            _run(
                ssh,
                f"test ! -f {q_backup} || (cp -a {q_backup} {q_remote} && systemctl restart caddy)",
                timeout=180,
            )
        raise
    finally:
        _run(ssh, f"rm -f {q_tmp}", timeout=60)


def deploy(
    *,
    brain_ip: str,
    ssh_user: str,
    ssh_port: int,
    passwords_path: Path,
    source: Path,
    remote_config: str,
) -> str:
    release_id = time.strftime("%Y%m%d%H%M%S")
    ssh, _auth_method = connect_node(
        code="brain",
        host=brain_ip,
        user=ssh_user,
        port=ssh_port,
        passwords_path=passwords_path,
    )
    try:
        _upload_caddy_config(ssh=ssh, source=source, remote_config=remote_config, release_id=release_id)
    finally:
        ssh.close()
    return release_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and deploy the repo Caddy config to brain.")
    parser.add_argument("--brain-ip", required=True)
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", type=Path, default=DEFAULT_PASSWORDS)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--remote-config", default=DEFAULT_REMOTE_CONFIG)
    args = parser.parse_args()

    release_id = deploy(
        brain_ip=args.brain_ip,
        ssh_user=args.ssh_user,
        ssh_port=args.ssh_port,
        passwords_path=args.passwords,
        source=args.source,
        remote_config=args.remote_config,
    )
    print(f"brain caddy config deployed: {release_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
