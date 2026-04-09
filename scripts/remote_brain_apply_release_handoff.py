from __future__ import annotations

import argparse
import os
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
RELEASE_KEYS = (
    "APP_ANDROID_PLAY_URL",
    "APP_ANDROID_APK_URL",
    "APP_ANDROID_MIRROR_URL",
    "APP_WINDOWS_EXE_URL",
    "APP_WINDOWS_MIRROR_URL",
    "APP_DOCS_URL",
)


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


def _read_release_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip()
    for key in RELEASE_KEYS:
        out.setdefault(key, "")
    return out


def _validate_release_env(values: dict[str, str]) -> list[str]:
    failures: list[str] = []
    android_primary = (
        str(values.get("APP_ANDROID_PLAY_URL", "")).strip()
        or str(values.get("APP_ANDROID_APK_URL", "")).strip()
        or str(values.get("APP_ANDROID_MIRROR_URL", "")).strip()
    )
    windows_primary = (
        str(values.get("APP_WINDOWS_EXE_URL", "")).strip()
        or str(values.get("APP_WINDOWS_MIRROR_URL", "")).strip()
    )
    docs_url = str(values.get("APP_DOCS_URL", "")).strip()

    if not android_primary:
        failures.append("android release URL is missing")
    if not windows_primary:
        failures.append("windows release URL is missing")
    if not docs_url:
        failures.append("docs_url is missing")
    return failures


def _rewrite_env(text: str, values: dict[str, str]) -> str:
    lines = text.splitlines()
    out: list[str] = []
    seen: set[str] = set()
    for ln in lines:
        stripped = ln.strip()
        matched = False
        for key in RELEASE_KEYS:
            if stripped.startswith(f"{key}="):
                out.append(f"{key}={values.get(key, '')}")
                seen.add(key)
                matched = True
                break
        if not matched:
            out.append(ln)

    if out and out[-1].strip() != "":
        out.append("")
    for key in RELEASE_KEYS:
        if key not in seen:
            out.append(f"{key}={values.get(key, '')}")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply release-links.env values to /root/portal_bot/.env on brain.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--env-file", default=str(REPO_ROOT / "external" / "client-fork" / "release-links.env"))
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--remote-env-file", default="/root/portal_bot/.env")
    ap.add_argument("--restart", default="portal-api,portal-bot")
    args = ap.parse_args()

    env_file = Path(args.env_file)
    if not env_file.exists():
        raise SystemExit(f"Missing release env file: {env_file}")

    values = _read_release_env(env_file)
    failures = _validate_release_env(values)
    if failures:
        raise SystemExit("; ".join(failures))

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
                with sftp.file(args.remote_env_file, "r") as f:
                    raw = f.read().decode("utf-8", errors="replace")
            except IOError:
                raw = ""
            updated = _rewrite_env(raw, values)
            with sftp.file(args.remote_env_file, "w") as f:
                f.write(updated.encode("utf-8"))
        finally:
            sftp.close()

        for unit in [u.strip() for u in (args.restart or "").split(",") if u.strip()]:
            _run(ssh, f"systemctl restart {unit} >/dev/null 2>&1 || true", timeout=60)
            _, out, err = _run(ssh, f"systemctl is-active {unit} || true", timeout=30)
            print(f"{unit}: {(out.strip() or err.strip()).strip()}")
        print(f"Updated release handoff from {env_file}")
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
