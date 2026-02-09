from __future__ import annotations

import argparse
import os
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"


def _parse_passwords(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in raw.splitlines()]
    for i, ln in enumerate(lines):
        if "BRAINnode" in ln:
            for j in range(i + 1, min(i + 30, len(lines))):
                v = lines[j].strip()
                if v and not v.startswith("ssh-ed25519 "):
                    return v
    return ""


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def _set_kv(text: str, key: str, value: str) -> str:
    key = key.strip()
    if not key:
        return text
    lines = text.splitlines()
    out: list[str] = []
    seen = False
    for ln in lines:
        if ln.strip().startswith(f"{key}="):
            out.append(f"{key}={value}")
            seen = True
        else:
            out.append(ln)
    if not seen:
        if out and out[-1].strip() != "":
            out.append("")
        out.append(f"{key}={value}")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Set KEY=VALUE in /root/portal_bot/.env on brain and restart services.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--env-file", default="/root/portal_bot/.env")
    ap.add_argument("--key", required=True)
    ap.add_argument("--value", required=True)
    ap.add_argument("--restart", default="portal-api,portal-bot")
    args = ap.parse_args()

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_passwords(Path(args.passwords))
    if not pw:
        raise SystemExit("Missing brain password.")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        args.brain_ip,
        port=args.ssh_port,
        username=args.ssh_user,
        password=pw,
        timeout=30,
        banner_timeout=30,
        auth_timeout=30,
    )
    try:
        sftp = ssh.open_sftp()
        try:
            try:
                with sftp.file(args.env_file, "r") as f:
                    raw = f.read().decode("utf-8", errors="replace")
            except IOError:
                raw = ""
            updated = _set_kv(raw, args.key, args.value)
            with sftp.file(args.env_file, "w") as f:
                f.write(updated.encode("utf-8"))
        finally:
            sftp.close()

        for unit in [u.strip() for u in (args.restart or "").split(",") if u.strip()]:
            _run(ssh, f"systemctl restart {unit} >/dev/null 2>&1 || true", timeout=60)
            _, out, err = _run(ssh, f"systemctl is-active {unit} || true", timeout=30)
            print(f"{unit}: {(out.strip() or err.strip()).strip()}")
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())

