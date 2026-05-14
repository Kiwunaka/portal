from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
DEFAULT_RELEASE_METADATA = REPO_ROOT.parent / "POKROV-app" / "artifacts" / "releases" / "release-handoff.json"
LEGACY_DEFAULT_ENV_FILE = REPO_ROOT / "external" / "client-fork" / "release-links.env"
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


def _load_paramiko() -> Any:
    try:
        import paramiko
    except ModuleNotFoundError as exc:
        raise SystemExit("Missing optional dependency: paramiko. Install ops requirements before applying remote handoff.") from exc
    return paramiko


def _run(ssh: Any, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
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


def _read_release_metadata(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Release metadata must be a JSON object: {path}")

    runtime_env = payload.get("runtime_env", {})
    values: dict[str, str] = {}
    if isinstance(runtime_env, dict):
        for key in RELEASE_KEYS:
            values[key] = str(runtime_env.get(key, "") or "").strip()

    def _set_if_blank(key: str, raw_value: object) -> None:
        if not str(values.get(key, "") or "").strip():
            values[key] = str(raw_value or "").strip()

    downloads = payload.get("downloads", {})
    if isinstance(downloads, dict):
        android = downloads.get("android", {}) if isinstance(downloads.get("android"), dict) else {}
        windows = downloads.get("windows", {}) if isinstance(downloads.get("windows"), dict) else {}
        docs_url = downloads.get("docs_url", payload.get("docs_url", ""))
        _set_if_blank("APP_ANDROID_PLAY_URL", android.get("play_url", ""))
        _set_if_blank("APP_ANDROID_APK_URL", android.get("apk_url", ""))
        _set_if_blank("APP_ANDROID_MIRROR_URL", android.get("mirror_url", ""))
        _set_if_blank("APP_WINDOWS_EXE_URL", windows.get("exe_url", ""))
        _set_if_blank("APP_WINDOWS_MIRROR_URL", windows.get("mirror_url", ""))
        _set_if_blank("APP_DOCS_URL", docs_url)

    for key in RELEASE_KEYS:
        values.setdefault(key, "")
    return values


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


def _resolve_release_values(metadata_file: str, env_file: str) -> tuple[dict[str, str], Path]:
    metadata_text = str(metadata_file or "").strip()
    env_text = str(env_file or "").strip()

    if metadata_text:
        path = Path(metadata_text)
        if not path.exists():
            raise SystemExit(f"Missing release metadata file: {path}")
        return _read_release_metadata(path), path

    if env_text:
        path = Path(env_text)
        if not path.exists():
            raise SystemExit(f"Missing release env file: {path}")
        return _read_release_env(path), path

    if DEFAULT_RELEASE_METADATA.exists():
        return _read_release_metadata(DEFAULT_RELEASE_METADATA), DEFAULT_RELEASE_METADATA

    if LEGACY_DEFAULT_ENV_FILE.exists():
        return _read_release_env(LEGACY_DEFAULT_ENV_FILE), LEGACY_DEFAULT_ENV_FILE

    raise SystemExit(
        "Missing release handoff input. Provide --metadata-file, --env-file, or create "
        f"{DEFAULT_RELEASE_METADATA}"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply client-owned release handoff metadata to /root/portal_bot/.env on brain.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument(
        "--metadata-file",
        default="",
        help="Client-owned release-handoff.json path. Defaults to the canonical POKROV-app metadata location when present.",
    )
    ap.add_argument(
        "--env-file",
        default="",
        help="Legacy release-links.env path for compatibility fallback.",
    )
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--remote-env-file", default="/root/portal_bot/.env")
    ap.add_argument("--restart", default="portal-api,portal-bot")
    args = ap.parse_args()

    values, source_path = _resolve_release_values(args.metadata_file, args.env_file)
    failures = _validate_release_env(values)
    if failures:
        raise SystemExit("; ".join(failures))

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_passwords(Path(args.passwords))
    if not pw:
        raise SystemExit("Missing brain password.")

    paramiko = _load_paramiko()
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
        print(f"Updated release handoff from {source_path}")
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
