from __future__ import annotations

import argparse
import hashlib
import os
import shlex
from datetime import datetime, timezone
from pathlib import Path

try:
    from node_access import DEFAULT_PASSWORDS, connect_node
except ImportError:  # pragma: no cover - package import for tests
    from .node_access import DEFAULT_PASSWORDS, connect_node


REPO_ROOT = Path(__file__).resolve().parents[1]
PINNED_ENGINE_SHA256 = (
    "d97cdb22be9f69843241f3d1589be2c63dbb18a281cb357e9f9141e6e886ddb2"
)
PINNED_ENGINE_SIZE = 73_756_820
REMOTE_ENGINE = "/usr/local/lib/pokrov-emergency/pokrov-sing-box-linux-amd64"
REMOTE_SERVICE = "/etc/systemd/system/pokrov-emergency-geoip-refresh.service"
REMOTE_TIMER = "/etc/systemd/system/pokrov-emergency-geoip-refresh.timer"
REMOTE_BACKUP_ROOT = "/root/pokrov-emergency-runtime-backups"


def _q(value: str) -> str:
    return shlex.quote(str(value))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_local_engine(path: Path) -> Path:
    resolved = path.resolve(strict=True)
    if (
        not resolved.is_file()
        or resolved.stat().st_size != PINNED_ENGINE_SIZE
        or _sha256_file(resolved) != PINNED_ENGINE_SHA256
    ):
        raise SystemExit("Emergency engine artifact does not match the release pin.")
    return resolved


def _run(ssh, command: str, *, timeout: int = 300) -> tuple[int, str, str]:
    _stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    return (
        code,
        stdout.read().decode("utf-8", errors="replace"),
        stderr.read().decode("utf-8", errors="replace"),
    )


def _require_ok(ssh, command: str, *, label: str, timeout: int = 300) -> str:
    code, out, _err = _run(ssh, command, timeout=timeout)
    if code != 0:
        raise RuntimeError(f"{label}_failed")
    return out.strip()


def _release_id() -> str:
    return f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{os.getpid()}"


def _backup_command(*, backup_root: str) -> str:
    targets = (REMOTE_ENGINE, REMOTE_SERVICE, REMOTE_TIMER)
    lines = ["set -e", f"mkdir -p {_q(backup_root)}"]
    for target in targets:
        name = Path(target).name
        lines.extend(
            [
                f"if [ -e {_q(target)} ]; then",
                f"  cp -a {_q(target)} {_q(f'{backup_root}/{name}')}",
                "else",
                f"  : > {_q(f'{backup_root}/{name}.missing')}",
                "fi",
            ]
        )
    lines.append(
        "systemctl is-enabled pokrov-emergency-geoip-refresh.timer "
        f"> {_q(f'{backup_root}/timer-enabled')} 2>/dev/null || true"
    )
    return "\n".join(lines)


def _restore_command(*, backup_root: str) -> str:
    targets = (REMOTE_ENGINE, REMOTE_SERVICE, REMOTE_TIMER)
    modes = ("0755", "0644", "0644")
    lines = ["set -e"]
    for target, mode in zip(targets, modes, strict=True):
        name = Path(target).name
        backup = f"{backup_root}/{name}"
        lines.extend(
            [
                f"if [ -e {_q(backup)} ]; then",
                f"  install -D -m {mode} {_q(backup)} {_q(target)}",
                "else",
                f"  rm -f {_q(target)}",
                "fi",
            ]
        )
    lines.extend(
        [
            "systemctl daemon-reload",
            f"if grep -qx enabled {_q(f'{backup_root}/timer-enabled')}; then",
            "  systemctl enable --now pokrov-emergency-geoip-refresh.timer",
            "else",
            "  systemctl disable --now pokrov-emergency-geoip-refresh.timer || true",
            "fi",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install the pinned emergency probe engine and GeoIP timer on brain."
    )
    parser.add_argument("--brain-ip", required=True)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", default=29374, type=int)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    args = parser.parse_args()

    engine = _validate_local_engine(args.binary)
    service = (REPO_ROOT / "infra" / "pokrov-emergency-geoip-refresh.service").resolve(
        strict=True
    )
    timer = (REPO_ROOT / "infra" / "pokrov-emergency-geoip-refresh.timer").resolve(
        strict=True
    )
    release_id = _release_id()
    stage_root = f"/root/pokrov-emergency-runtime-stage/{release_id}"
    backup_root = f"{REMOTE_BACKUP_ROOT}/{release_id}"

    ssh, auth_method = connect_node(
        code="brain",
        host=args.brain_ip,
        user=args.ssh_user,
        port=args.ssh_port,
        passwords_path=Path(args.passwords),
    )
    try:
        print(f"brain auth: {auth_method}")
        _require_ok(
            ssh,
            "test -x /root/portal_bot/venv/bin/python && "
            "test -f /root/portal_bot/emergency_geoip_refresh.py && "
            "/root/portal_bot/venv/bin/python -c 'import geoip2.database'",
            label="runtime_preflight",
            timeout=60,
        )
        _require_ok(
            ssh,
            f"install -d -m 0700 {_q(stage_root)}",
            label="stage_prepare",
        )
        sftp = ssh.open_sftp()
        try:
            sftp.put(str(engine), f"{stage_root}/{Path(REMOTE_ENGINE).name}")
            sftp.put(str(service), f"{stage_root}/{Path(REMOTE_SERVICE).name}")
            sftp.put(str(timer), f"{stage_root}/{Path(REMOTE_TIMER).name}")
        finally:
            sftp.close()

        stage_engine = f"{stage_root}/{Path(REMOTE_ENGINE).name}"
        _require_ok(
            ssh,
            "set -e; "
            f"test $(stat -c %s {_q(stage_engine)}) -eq {PINNED_ENGINE_SIZE}; "
            f"test $(sha256sum {_q(stage_engine)} | awk '{{print $1}}') = {PINNED_ENGINE_SHA256}",
            label="stage_engine_validation",
            timeout=180,
        )
        _require_ok(
            ssh,
            _backup_command(backup_root=backup_root),
            label="runtime_backup",
        )
        try:
            _require_ok(
                ssh,
                "set -e; "
                f"install -D -m 0755 {_q(stage_engine)} {_q(REMOTE_ENGINE)}; "
                f"install -D -m 0644 {_q(f'{stage_root}/{Path(REMOTE_SERVICE).name}')} {_q(REMOTE_SERVICE)}; "
                f"install -D -m 0644 {_q(f'{stage_root}/{Path(REMOTE_TIMER).name}')} {_q(REMOTE_TIMER)}; "
                "systemctl daemon-reload; "
                "systemctl enable --now pokrov-emergency-geoip-refresh.timer; "
                "systemctl start pokrov-emergency-geoip-refresh.service",
                label="runtime_install",
                timeout=240,
            )
            installed = _require_ok(
                ssh,
                "set -e; "
                f"test $(stat -c %s {_q(REMOTE_ENGINE)}) -eq {PINNED_ENGINE_SIZE}; "
                f"test $(sha256sum {_q(REMOTE_ENGINE)} | awk '{{print $1}}') = {PINNED_ENGINE_SHA256}; "
                "test $(systemctl is-active pokrov-emergency-geoip-refresh.timer) = active; "
                "test $(systemctl show pokrov-emergency-geoip-refresh.service -p Result --value) = success; "
                "test -s /var/lib/pokrov-geoip/dbip-country-lite.mmdb; "
                "printf ready",
                label="runtime_readback",
                timeout=180,
            )
        except Exception:
            _require_ok(
                ssh,
                _restore_command(backup_root=backup_root),
                label="runtime_rollback",
            )
            raise
        print(f"emergency runtime: {installed}")
        print(f"rollback snapshot: {backup_root}")
        return 0
    finally:
        _run(ssh, f"rm -rf -- {_q(stage_root)}", timeout=60)
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
