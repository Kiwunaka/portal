from __future__ import annotations

import argparse
import posixpath
import re
import shlex
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
DEFAULT_SOURCE = REPO_ROOT / "infra" / "brain-haproxy-l4.cfg"
DEFAULT_REMOTE_CONFIG = "/etc/haproxy/haproxy.cfg"
DEFAULT_BACKUP_RETENTION_COUNT = 5

if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from node_access import connect_node  # noqa: E402


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


def _build_backup_prune_command(
    remote_config: str,
    retain_count: int = DEFAULT_BACKUP_RETENTION_COUNT,
) -> str:
    keep = int(retain_count)
    if not 1 <= keep <= 50:
        raise ValueError("retain_count must be between 1 and 50")
    remote_path = str(remote_config or "")
    remote_dir = posixpath.dirname(remote_path)
    basename = posixpath.basename(remote_path)
    if not remote_path.startswith("/") or not remote_dir or not re.fullmatch(r"[A-Za-z0-9._-]+", basename):
        raise ValueError("unsafe remote HAProxy config path")
    directory_q = shlex.quote(remote_dir)
    filename_re = re.escape(f"{basename}.bak-") + r"[0-9]{14}"
    return "\n".join(
        [
            "set -e",
            f"root={directory_q}",
            f'test "$root" = {directory_q}',
            'test -d "$root" || exit 0',
            'find "$root" -mindepth 1 -maxdepth 1 -type f -printf \'%f\\n\' |',
            f"  grep -E '^{filename_re}$' |",
            "  LC_ALL=C sort |",
            f"  head -n -{keep} |",
            "  while IFS= read -r name; do",
            '    test -n "$name" || continue',
            '    rm -f -- "$root/$name"',
            "  done",
        ]
    )


def _upload_haproxy_config(*, ssh, source: Path, remote_config: str, release_id: str) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"missing HAProxy source config: {source}")

    remote_dir = posixpath.dirname(remote_config)
    remote_tmp = f"/tmp/pokrov-haproxy-{release_id}.cfg"
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
        _require_ok(ssh, f"haproxy -c -f {q_tmp}", timeout=120)
        _require_ok(
            ssh,
            f"mkdir -p {shlex.quote(remote_dir)}; test ! -f {q_remote} || cp -a {q_remote} {q_backup}",
            timeout=120,
        )
        _require_ok(ssh, f"install -m 0644 {q_tmp} {q_remote}", timeout=120)
        installed = True
        _require_ok(ssh, f"haproxy -c -f {q_remote}", timeout=120)
        _require_ok(ssh, "systemctl reload haproxy || systemctl restart haproxy", timeout=180)
        _require_ok(ssh, "systemctl is-active haproxy", timeout=60)
        prune_code, prune_out, prune_err = _run(
            ssh,
            _build_backup_prune_command(remote_config),
            timeout=120,
        )
        if prune_code != 0:
            detail = (prune_out.strip() or prune_err.strip() or f"exit={prune_code}").strip()
            print(f"[warn] HAProxy backup retention failed: {detail}")
    except Exception:
        if installed:
            _run(
                ssh,
                f"test ! -f {q_backup} || (cp -a {q_backup} {q_remote} && haproxy -c -f {q_remote} && systemctl restart haproxy)",
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
        _upload_haproxy_config(
            ssh=ssh,
            source=source,
            remote_config=remote_config,
            release_id=release_id,
        )
    finally:
        ssh.close()
    return release_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and deploy the repo HAProxy config to brain.")
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
    print(f"brain HAProxy config deployed: {release_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
