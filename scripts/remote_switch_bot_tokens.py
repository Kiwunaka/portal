from __future__ import annotations

import argparse
import os
import posixpath
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"


def _parse_password(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in raw.splitlines()]
    for i, ln in enumerate(lines):
        if "BRAINnode" not in ln:
            continue
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


def _parse_env_lines(raw: str) -> tuple[list[str], dict[str, int]]:
    lines = raw.splitlines()
    mapping: dict[str, int] = {}
    for idx, ln in enumerate(lines):
        if not ln or ln.lstrip().startswith("#") or "=" not in ln:
            continue
        key = ln.split("=", 1)[0].strip()
        if key:
            mapping[key] = idx
    return lines, mapping


def _upsert(lines: list[str], mapping: dict[str, int], key: str, value: str) -> None:
    row = f"{key}={value}"
    if key in mapping:
        lines[mapping[key]] = row
        return
    mapping[key] = len(lines)
    lines.append(row)


def apply_bot_switch(
    env_raw: str,
    *,
    new_bot_token: str,
    new_bot_username: str,
    migration_target_url: str,
    public_channel: str,
    profile_update_hours: int,
    help_bot_token: str = "",
    support_username: str = "",
) -> str:
    lines, mapping = _parse_env_lines(env_raw)

    old_token = ""
    if "BOT_TOKEN" in mapping:
        old_line = lines[mapping["BOT_TOKEN"]]
        old_token = old_line.split("=", 1)[1].strip()

    _upsert(lines, mapping, "BOT_TOKEN", new_bot_token.strip())
    _upsert(lines, mapping, "BOT_USERNAME", new_bot_username.strip().lstrip("@"))
    _upsert(lines, mapping, "BOT_MIGRATION_TARGET_URL", migration_target_url.strip())
    _upsert(lines, mapping, "PUBLIC_CHANNEL", public_channel.strip().lstrip("@"))
    _upsert(lines, mapping, "PROFILE_UPDATE_INTERVAL_HOURS", str(max(1, int(profile_update_hours))))
    _upsert(lines, mapping, "WORKER_EMBEDDED", "false")

    normalized_support_username = support_username.strip().lstrip("@")
    if help_bot_token.strip():
        _upsert(lines, mapping, "HELP_BOT_TOKEN", help_bot_token.strip())
    if normalized_support_username:
        _upsert(lines, mapping, "SUPPORT_USERNAME", normalized_support_username)
        _upsert(lines, mapping, "SUPPORT_BOT_USERNAME", normalized_support_username)

    if old_token and old_token != new_bot_token.strip():
        _upsert(lines, mapping, "LEGACY_BOT_TOKEN", old_token)

    return "\n".join(lines).rstrip("\n") + "\n"


def _ensure_dir(sftp: paramiko.SFTPClient, remote_dir: str) -> None:
    parts: list[str] = []
    cur = remote_dir
    while cur not in {"", "/"}:
        parts.append(cur)
        cur = posixpath.dirname(cur)
    for d in reversed(parts):
        try:
            sftp.stat(d)
        except IOError:
            try:
                sftp.mkdir(d)
            except IOError:
                pass


def _put_text(sftp: paramiko.SFTPClient, remote_path: str, content: str) -> None:
    _ensure_dir(sftp, posixpath.dirname(remote_path))
    with sftp.file(remote_path, "w") as f:
        f.write(content)


def main() -> int:
    ap = argparse.ArgumentParser(description="Switch main Telegram bot token and enable legacy redirect bot service.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--new-bot-token", required=True, help="Token for new main bot (not persisted in repo).")
    ap.add_argument("--new-bot-username", default="portal_service_bot")
    ap.add_argument("--migration-target-url", default="https://t.me/portal_service_bot")
    ap.add_argument("--public-channel", default="pokrov_vpn")
    ap.add_argument("--profile-update-hours", type=int, default=6)
    ap.add_argument("--help-bot-token", default="", help="Token for dedicated support bot.")
    ap.add_argument("--support-username", default="portal_privacy_helpbot")
    ap.add_argument("--enable-legacy-redirect", action="store_true")
    args = ap.parse_args()

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_password(Path(args.passwords))
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
            env_path = "/root/portal_bot/.env"
            with sftp.file(env_path, "r") as f:
                env_raw = f.read().decode("utf-8", errors="replace")
            new_env = apply_bot_switch(
                env_raw,
                new_bot_token=str(args.new_bot_token),
                new_bot_username=str(args.new_bot_username),
                migration_target_url=str(args.migration_target_url),
                public_channel=str(args.public_channel),
                profile_update_hours=int(args.profile_update_hours),
                help_bot_token=str(args.help_bot_token),
                support_username=str(args.support_username),
            )
            with sftp.file(env_path, "w") as f:
                f.write(new_env)

            if args.enable_legacy_redirect:
                unit = """[Unit]
Description=Portal legacy bot redirect
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/portal_bot
EnvironmentFile=-/root/portal_bot/.env
ExecStart=/root/portal_bot/venv/bin/python /root/portal_bot/legacy_redirect_bot.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
                _put_text(sftp, "/etc/systemd/system/portal-legacy-redirect.service", unit)
        finally:
            sftp.close()

        _run(ssh, "systemctl daemon-reload", timeout=60)
        _run(ssh, "systemctl restart portal-api portal-bot portal-helpbot portal-worker", timeout=120)
        if args.enable_legacy_redirect:
            _run(ssh, "systemctl enable portal-legacy-redirect >/dev/null 2>&1 || true", timeout=60)
            _run(ssh, "systemctl restart portal-legacy-redirect", timeout=60)

        services = ["portal-api", "portal-bot", "portal-helpbot", "portal-worker"]
        if args.enable_legacy_redirect:
            services.append("portal-legacy-redirect")
        for unit in services:
            _, out, err = _run(ssh, f"systemctl is-active {unit} || true", timeout=30)
            print(f"{unit}: {(out.strip() or err.strip()).strip()}")
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
