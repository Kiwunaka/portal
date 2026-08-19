from __future__ import annotations

import argparse
import json
import re
import shlex
from datetime import datetime, timezone
from pathlib import Path

from node_access import connect_node


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
UNIT_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")


def _q(value: str) -> str:
    return shlex.quote(str(value))


def _parse_when(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise SystemExit("--when must be an ISO-8601 timestamp with timezone") from exc
    if parsed.tzinfo is None:
        raise SystemExit("--when must include a timezone")
    parsed = parsed.astimezone(timezone.utc)
    now = datetime.now(timezone.utc)
    seconds = (parsed - now).total_seconds()
    if seconds < 120 or seconds > 86_400:
        raise SystemExit("--when must be between 2 minutes and 24 hours in the future")
    return parsed


def _run(ssh, command: str, *, timeout: int = 60) -> tuple[int, str, str]:
    _stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    return (
        code,
        stdout.read().decode("utf-8", errors="replace").strip(),
        stderr.read().decode("utf-8", errors="replace").strip(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Schedule one guarded in-app and Telegram release announcement on brain."
    )
    parser.add_argument("--brain-ip", required=True)
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--when", required=True)
    parser.add_argument("--schedule-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--link", required=True)
    parser.add_argument("--telegram-text", required=True)
    args = parser.parse_args()

    when = _parse_when(args.when)
    schedule_id = str(args.schedule_id).strip().lower()
    unit_suffix = re.sub(r"[^a-z0-9-]+", "-", schedule_id.replace(".", "-")).strip("-")
    if UNIT_RE.fullmatch(unit_suffix) is None:
        raise SystemExit("--schedule-id is not safe for a systemd unit")
    unit = f"pokrov-release-announcement-{unit_suffix}"
    config_path = f"/root/portal_bot/ops-schedules/{schedule_id}.json"
    payload = {
        "schema_version": 1,
        "schedule_id": schedule_id,
        "title": str(args.title),
        "summary": str(args.summary),
        "link": str(args.link),
        "telegram_text": str(args.telegram_text),
        "delete_after_success": True,
    }

    ssh = connect_node(
        host=args.brain_ip,
        port=int(args.ssh_port),
        username=str(args.ssh_user),
        passwords_path=Path(args.passwords),
        node_code="brain",
    )
    try:
        exists_code, exists_out, _exists_err = _run(
            ssh,
            f"systemctl show {_q(unit + '.timer')} --property=LoadState --value 2>/dev/null || true",
        )
        if exists_code != 0 or exists_out.strip() == "loaded":
            raise SystemExit("announcement timer already exists")
        _run(ssh, "install -d -m 0700 /root/portal_bot/ops-schedules")
        sftp = ssh.open_sftp()
        try:
            with sftp.file(config_path, "w") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            sftp.chmod(config_path, 0o600)
        finally:
            sftp.close()

        calendar = when.strftime("%Y-%m-%d %H:%M:%S UTC")
        command = " ".join(
            [
                "systemd-run",
                f"--unit={_q(unit)}",
                f"--description={_q('POKROV guarded release announcement')}",
                f"--on-calendar={_q(calendar)}",
                "--timer-property=AccuracySec=1s",
                "--timer-property=Persistent=true",
                "--property=Type=oneshot",
                "--property=WorkingDirectory=/root/portal_bot",
                "--property=RuntimeMaxSec=900",
                "/root/portal_bot/venv/bin/python",
                "-B",
                "/root/portal_bot/release_announcement_job.py",
                "--config",
                _q(config_path),
            ]
        )
        code, out, err = _run(ssh, command)
        if code != 0:
            _run(ssh, f"rm -f -- {_q(config_path)}")
            raise SystemExit(f"systemd-run failed: {(err or out)[:300]}")
        verify_code, verify_out, verify_err = _run(
            ssh,
            " ".join(
                [
                    "systemctl",
                    "show",
                    _q(unit + ".timer"),
                    "--property=ActiveState,NextElapseUSecRealtime,Unit",
                ]
            ),
        )
        if verify_code != 0 or "ActiveState=active" not in verify_out:
            raise SystemExit(f"timer verification failed: {(verify_err or verify_out)[:300]}")
        print(
            json.dumps(
                {
                    "ok": True,
                    "unit": unit,
                    "scheduled_at_utc": when.isoformat().replace("+00:00", "Z"),
                    "config_mode": "0600",
                    "guarded_actions": ["live_update.create", "broadcast.send"],
                },
                sort_keys=True,
            )
        )
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
