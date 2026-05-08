from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlparse

import paramiko


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
GITHUB_RELEASE_HOST = "github.com"
INSTALL_DOCS_HOST = "pokrov.space"
INSTALL_DOCS_PATH = "/install/"
GO_MARKER = "GO for public beta publication"
NO_GO_MARKER = "NO-GO"
RUNTIME_SYNC_MARKER = "RUNTIME LINK SYNC GO FOR APP-DOWNLOAD SMOKE"
OPERATOR_APPROVED_RUNTIME_SYNC_MARKER = "OPERATOR_APPROVED_RUNTIME_LINK_SYNC=true"
STAGED_REACHABILITY_MARKER = "STAGED GITHUB ASSET REACHABILITY GREEN"
NO_PUBLIC_ANNOUNCEMENT_MARKER = "NO PUBLIC ANNOUNCEMENT"
PAID_CHECKOUT_CLOSED_MARKER = "PAID CHECKOUT REMAINS CLOSED"
NO_RUNTIME_SYNC_MARKER = "NO RUNTIME SYNC OR ANNOUNCEMENT"
NO_RUNTIME_SYNC_DECISION_MARKER = "NO RUNTIME SYNC"
BLOCKED_CLASSIFICATION_MARKERS = (
    "BLOCKED_BY_ACCESS",
    "BLOCKED_BY_POLICY",
)
RUNTIME_SYNC_GUARD_TITLE_MARKER = "RUNTIME LINK SYNC GUARD EVIDENCE"


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
    if "downloads" not in payload and isinstance(payload.get("android"), dict) and isinstance(payload.get("windows"), dict):
        downloads = payload
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
    android_primary = str(values.get("APP_ANDROID_APK_URL", "")).strip() or str(
        values.get("APP_ANDROID_MIRROR_URL", "")
    ).strip()
    windows_primary = (
        str(values.get("APP_WINDOWS_EXE_URL", "")).strip()
        or str(values.get("APP_WINDOWS_MIRROR_URL", "")).strip()
    )
    docs_url = str(values.get("APP_DOCS_URL", "")).strip()

    play_url = str(values.get("APP_ANDROID_PLAY_URL", "")).strip()
    if play_url:
        failures.append("APP_ANDROID_PLAY_URL must be empty for outside-store public beta handoff")
    if not android_primary:
        failures.append("android release URL is missing")
    if not windows_primary:
        failures.append("windows release URL is missing")
    if not docs_url:
        failures.append("docs_url is missing")

    for key in ("APP_ANDROID_APK_URL", "APP_ANDROID_MIRROR_URL"):
        failures.extend(_validate_release_artifact_url(key, values.get(key, ""), suffix=".apk"))
    for key in ("APP_WINDOWS_EXE_URL", "APP_WINDOWS_MIRROR_URL"):
        failures.extend(_validate_release_artifact_url(key, values.get(key, ""), suffix=".exe"))
    failures.extend(_validate_docs_url("APP_DOCS_URL", docs_url))
    return failures


def _validate_release_artifact_url(key: str, raw_url: object, *, suffix: str) -> list[str]:
    url = str(raw_url or "").strip()
    if not url:
        return []
    parsed = urlparse(url)
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        return [f"{key} must be an https URL"]
    path = str(parsed.path or "").lower()
    host = str(parsed.hostname or "").lower()
    if host != GITHUB_RELEASE_HOST or "/releases/download/" not in path or not path.endswith(suffix):
        return [f"{key} must point to a GitHub Releases {suffix} artifact"]
    return []


def _validate_docs_url(key: str, raw_url: object) -> list[str]:
    url = str(raw_url or "").strip()
    if not url:
        return []
    parsed = urlparse(url)
    path = str(parsed.path or "")
    if (
        parsed.scheme.lower() != "https"
        or str(parsed.hostname or "").lower() != INSTALL_DOCS_HOST
        or not (path == INSTALL_DOCS_PATH.rstrip("/") or path.startswith(INSTALL_DOCS_PATH))
    ):
        return [f"{key} must point to https://{INSTALL_DOCS_HOST}{INSTALL_DOCS_PATH}"]
    return []


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


def _dry_run_report(values: dict[str, str], source_path: Path) -> dict[str, object]:
    return {
        "ok": True,
        "mode": "remote_brain_apply_release_handoff_dry_run",
        "source": str(source_path),
        "values": {key: str(values.get(key, "") or "") for key in RELEASE_KEYS},
        "note": "Validated release handoff values only; no SSH connection, env write, or service restart was performed.",
    }


def _release_handoff_evidence_failure(path: Path | None) -> str:
    if path is None:
        return "GO evidence file is required for runtime APP_* sync"
    evidence_path = Path(path)
    if not evidence_path.is_file():
        return f"GO evidence file not found: {evidence_path}"
    text = evidence_path.read_text(encoding="utf-8", errors="replace")
    upper_text = text.upper()
    if NO_RUNTIME_SYNC_DECISION_MARKER in upper_text:
        return f"runtime sync evidence contains no-sync decision `{NO_RUNTIME_SYNC_DECISION_MARKER}`"
    for marker in BLOCKED_CLASSIFICATION_MARKERS:
        if marker in upper_text:
            return f"runtime sync evidence contains blocked classification `{marker}`"
    if RUNTIME_SYNC_GUARD_TITLE_MARKER in upper_text:
        return "runtime sync evidence is a guard artifact, not an authorization"
    if GO_MARKER in text and NO_GO_MARKER not in text:
        return ""
    if RUNTIME_SYNC_MARKER in text:
        required = [
            OPERATOR_APPROVED_RUNTIME_SYNC_MARKER,
            STAGED_REACHABILITY_MARKER,
            NO_PUBLIC_ANNOUNCEMENT_MARKER,
            PAID_CHECKOUT_CLOSED_MARKER,
        ]
        for marker in required:
            if marker not in text:
                return f"runtime sync evidence must explicitly contain `{marker}`"
        if NO_RUNTIME_SYNC_MARKER in text:
            return f"runtime sync evidence still contains blocking marker `{NO_RUNTIME_SYNC_MARKER}`"
        return ""
    return "GO evidence file is not a public-beta GO handoff or runtime-link sync authorization"


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
    ap.add_argument("--dry-run", action="store_true", help="Validate and print the release handoff values without SSH, env writes, or restarts.")
    ap.add_argument(
        "--go-evidence-file",
        default="",
        help="Required unless --dry-run. Must be a GO handoff or a narrow runtime-link sync authorization.",
    )
    args = ap.parse_args()

    values, source_path = _resolve_release_values(args.metadata_file, args.env_file)
    failures = _validate_release_env(values)
    if failures:
        raise SystemExit("; ".join(failures))

    if args.dry_run:
        print(json.dumps(_dry_run_report(values, source_path), ensure_ascii=False, indent=2))
        return 0

    evidence_failure = _release_handoff_evidence_failure(Path(args.go_evidence_file) if str(args.go_evidence_file or "").strip() else None)
    if evidence_failure:
        raise SystemExit(evidence_failure)

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
        print(f"Updated release handoff from {source_path}")
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
