from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
DEFAULT_RELEASE_METADATA = REPO_ROOT.parent / "POKROV-app" / "artifacts" / "releases" / "release-handoff.json"
LEGACY_DEFAULT_ENV_FILE = REPO_ROOT / "external" / "client-fork" / "release-links.env"
CANONICAL_INSTALL_URL = "https://pokrov.space/install/"
V2_ANDROID_ARTIFACTS = {
    "arm64-v8a": (
        "pokrov-android-arm64-v8a.apk",
        "APP_ANDROID_APK_ARM64_URL",
        "APP_ANDROID_ARM64_SHA256",
        "APP_ANDROID_ARM64_SIZE_BYTES",
    ),
    "armeabi-v7a": (
        "pokrov-android-armeabi-v7a.apk",
        "APP_ANDROID_APK_ARMEABI_V7A_URL",
        "APP_ANDROID_ARMEABI_V7A_SHA256",
        "APP_ANDROID_ARMEABI_V7A_SIZE_BYTES",
    ),
    "x86_64": (
        "pokrov-android-x86_64.apk",
        "APP_ANDROID_APK_X86_64_URL",
        "APP_ANDROID_X86_64_SHA256",
        "APP_ANDROID_X86_64_SIZE_BYTES",
    ),
    "universal": (
        "pokrov-android-universal.apk",
        "APP_ANDROID_APK_UNIVERSAL_URL",
        "APP_ANDROID_UNIVERSAL_SHA256",
        "APP_ANDROID_UNIVERSAL_SIZE_BYTES",
    ),
}
RELEASE_KEYS = (
    "APP_RELEASE_SCHEMA_VERSION",
    "APP_RELEASE_CHANNEL",
    "APP_RELEASE_CANDIDATE_LABEL",
    "APP_RELEASE_HANDOFF_SHA256",
    "APP_RELEASE_ARTIFACT_SET_SHA256",
    "APP_RELEASE_CORE_VERSION",
    "APP_RELEASE_CORE_DESKTOP_ABI",
    "APP_RELEASE_CORE_ANDROID_PACKAGE",
    "APP_ANDROID_PLAY_URL",
    "APP_ANDROID_APK_URL",
    "APP_ANDROID_APK_ARM64_URL",
    "APP_ANDROID_APK_ARMEABI_V7A_URL",
    "APP_ANDROID_APK_X86_64_URL",
    "APP_ANDROID_APK_UNIVERSAL_URL",
    "APP_ANDROID_MIRROR_URL",
    "APP_ANDROID_VERSION",
    "APP_ANDROID_MIN_SUPPORTED_VERSION",
    "APP_ANDROID_SHA256",
    "APP_ANDROID_SIZE_BYTES",
    "APP_ANDROID_ARM64_SHA256",
    "APP_ANDROID_ARM64_SIZE_BYTES",
    "APP_ANDROID_ARMEABI_V7A_SHA256",
    "APP_ANDROID_ARMEABI_V7A_SIZE_BYTES",
    "APP_ANDROID_X86_64_SHA256",
    "APP_ANDROID_X86_64_SIZE_BYTES",
    "APP_ANDROID_UNIVERSAL_SHA256",
    "APP_ANDROID_UNIVERSAL_SIZE_BYTES",
    "APP_ANDROID_RELEASE_NOTES",
    "APP_ANDROID_RELEASE_NOTES_URL",
    "APP_ANDROID_PUBLISHED_AT",
    "APP_WINDOWS_EXE_URL",
    "APP_WINDOWS_MIRROR_URL",
    "APP_WINDOWS_VERSION",
    "APP_WINDOWS_MIN_SUPPORTED_VERSION",
    "APP_WINDOWS_SHA256",
    "APP_WINDOWS_SIZE_BYTES",
    "APP_WINDOWS_RELEASE_NOTES",
    "APP_WINDOWS_RELEASE_NOTES_URL",
    "APP_WINDOWS_PUBLISHED_AT",
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


def _load_paramiko() -> tuple[Any, Any]:
    try:
        import paramiko
        from ssh_host_keys import configure_ssh_host_key_policy
    except ModuleNotFoundError as exc:
        raise SystemExit("Missing optional dependency: paramiko. Install ops requirements before applying remote handoff.") from exc
    return paramiko, configure_ssh_host_key_policy


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


def _validate_v2_metadata(payload: dict[str, Any]) -> None:
    scripts_root = str(Path(__file__).resolve().parent)
    if scripts_root not in sys.path:
        sys.path.insert(0, scripts_root)
    from validate_release_handoff_metadata import ValidationIssue, validate_metadata

    try:
        validate_metadata(payload)
    except ValidationIssue as exc:
        raise SystemExit(f"Invalid strict release-handoff v2 metadata: {exc.code}") from exc


def _v2_runtime_values(payload: dict[str, Any], path: Path) -> dict[str, str]:
    _validate_v2_metadata(payload)
    values = {key: "" for key in RELEASE_KEYS}
    release = payload["release"]
    release_notes = release["release_notes"]
    compatibility = payload["compatibility"]
    core_abi = compatibility["core_abi"]
    promotion = payload["promotion"]

    values.update(
        {
            "APP_RELEASE_SCHEMA_VERSION": "2",
            "APP_RELEASE_CHANNEL": str(release["channel"]),
            "APP_RELEASE_CANDIDATE_LABEL": str(release["candidate_label"]),
            "APP_RELEASE_HANDOFF_SHA256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "APP_RELEASE_ARTIFACT_SET_SHA256": str(
                promotion["source_artifact_set_sha256"]
            ).lower(),
            "APP_RELEASE_CORE_VERSION": str(compatibility["core_version"]),
            "APP_RELEASE_CORE_DESKTOP_ABI": str(core_abi["desktop"]),
            "APP_RELEASE_CORE_ANDROID_PACKAGE": str(core_abi["android_package"]),
            "APP_ANDROID_VERSION": str(release["version"]),
            "APP_ANDROID_RELEASE_NOTES": str(release_notes["summary"]),
            "APP_ANDROID_RELEASE_NOTES_URL": str(release_notes["url"]),
            "APP_ANDROID_PUBLISHED_AT": str(release["created_at_utc"]),
            "APP_WINDOWS_VERSION": str(release["version"]),
            "APP_WINDOWS_RELEASE_NOTES": str(release_notes["summary"]),
            "APP_WINDOWS_RELEASE_NOTES_URL": str(release_notes["url"]),
            "APP_WINDOWS_PUBLISHED_AT": str(release["created_at_utc"]),
            "APP_DOCS_URL": CANONICAL_INSTALL_URL,
        }
    )

    android_candidates: dict[str, dict[str, Any]] = {}
    for artifact in payload["artifacts"]:
        platform = str(artifact["platform"])
        kind = str(artifact["kind"])
        architecture = str(artifact["architecture"])
        file_name = str(artifact["file_name"])
        if platform == "android" and kind == "apk":
            mapping = V2_ANDROID_ARTIFACTS.get(architecture)
            if mapping is None or file_name != mapping[0]:
                continue
            android_candidates[architecture] = artifact
            values[mapping[1]] = str(artifact["public_url"])
            values[mapping[2]] = str(artifact["sha256"]).lower()
            values[mapping[3]] = str(artifact["size_bytes"])
        elif (
            platform == "windows"
            and kind == "exe"
            and architecture == "x64"
            and file_name == "pokrov-windows-setup-x64.exe"
        ):
            values["APP_WINDOWS_EXE_URL"] = str(artifact["public_url"])
            values["APP_WINDOWS_SHA256"] = str(artifact["sha256"]).lower()
            values["APP_WINDOWS_SIZE_BYTES"] = str(artifact["size_bytes"])

    for architecture in ("arm64-v8a", "universal", "armeabi-v7a", "x86_64"):
        primary = android_candidates.get(architecture)
        if primary is None:
            continue
        values["APP_ANDROID_APK_URL"] = str(primary["public_url"])
        values["APP_ANDROID_SHA256"] = str(primary["sha256"]).lower()
        values["APP_ANDROID_SIZE_BYTES"] = str(primary["size_bytes"])
        break
    return values


def _read_release_metadata(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Release metadata must be a JSON object: {path}")
    if payload.get("schema_version") == 2:
        return _v2_runtime_values(payload, path)

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
        _set_if_blank("APP_ANDROID_APK_ARM64_URL", android.get("apk_arm64_url", ""))
        _set_if_blank("APP_ANDROID_APK_ARMEABI_V7A_URL", android.get("apk_armeabi_v7a_url", ""))
        _set_if_blank("APP_ANDROID_APK_X86_64_URL", android.get("apk_x86_64_url", ""))
        _set_if_blank("APP_ANDROID_APK_UNIVERSAL_URL", android.get("apk_universal_url", ""))
        _set_if_blank("APP_ANDROID_MIRROR_URL", android.get("mirror_url", ""))
        _set_if_blank("APP_ANDROID_VERSION", payload.get("version", ""))
        _set_if_blank("APP_ANDROID_SHA256", android.get("sha256", ""))
        _set_if_blank("APP_ANDROID_SIZE_BYTES", android.get("size_bytes", ""))
        variants = android.get("apk_variants", [])
        if isinstance(variants, list):
            for variant in variants:
                if not isinstance(variant, dict):
                    continue
                abi = str(variant.get("abi", "") or "").strip().lower()
                if abi == "arm64-v8a":
                    _set_if_blank("APP_ANDROID_APK_ARM64_URL", variant.get("url", ""))
                    _set_if_blank("APP_ANDROID_ARM64_SHA256", variant.get("sha256", ""))
                    _set_if_blank("APP_ANDROID_ARM64_SIZE_BYTES", variant.get("size_bytes", variant.get("size", "")))
                elif abi == "armeabi-v7a":
                    _set_if_blank("APP_ANDROID_APK_ARMEABI_V7A_URL", variant.get("url", ""))
                    _set_if_blank("APP_ANDROID_ARMEABI_V7A_SHA256", variant.get("sha256", ""))
                    _set_if_blank("APP_ANDROID_ARMEABI_V7A_SIZE_BYTES", variant.get("size_bytes", variant.get("size", "")))
                elif abi == "x86_64":
                    _set_if_blank("APP_ANDROID_APK_X86_64_URL", variant.get("url", ""))
                    _set_if_blank("APP_ANDROID_X86_64_SHA256", variant.get("sha256", ""))
                    _set_if_blank("APP_ANDROID_X86_64_SIZE_BYTES", variant.get("size_bytes", variant.get("size", "")))
                elif abi == "universal":
                    _set_if_blank("APP_ANDROID_APK_UNIVERSAL_URL", variant.get("url", ""))
                    _set_if_blank("APP_ANDROID_UNIVERSAL_SHA256", variant.get("sha256", ""))
                    _set_if_blank("APP_ANDROID_UNIVERSAL_SIZE_BYTES", variant.get("size_bytes", variant.get("size", "")))
        _set_if_blank("APP_WINDOWS_EXE_URL", windows.get("exe_url", ""))
        _set_if_blank("APP_WINDOWS_MIRROR_URL", windows.get("mirror_url", ""))
        _set_if_blank("APP_WINDOWS_VERSION", payload.get("version", ""))
        _set_if_blank("APP_WINDOWS_SHA256", windows.get("exe_sha256", ""))
        _set_if_blank("APP_WINDOWS_SIZE_BYTES", windows.get("exe_size_bytes", ""))
        _set_if_blank("APP_DOCS_URL", docs_url)

    for key in RELEASE_KEYS:
        values.setdefault(key, "")
    return values


def _validate_release_env(values: dict[str, str]) -> list[str]:
    failures: list[str] = []
    android_primary = (
        str(values.get("APP_ANDROID_PLAY_URL", "")).strip()
        or str(values.get("APP_ANDROID_APK_URL", "")).strip()
        or str(values.get("APP_ANDROID_APK_ARM64_URL", "")).strip()
        or str(values.get("APP_ANDROID_APK_ARMEABI_V7A_URL", "")).strip()
        or str(values.get("APP_ANDROID_APK_UNIVERSAL_URL", "")).strip()
        or str(values.get("APP_ANDROID_APK_X86_64_URL", "")).strip()
        or str(values.get("APP_ANDROID_MIRROR_URL", "")).strip()
    )
    windows_primary = (
        str(values.get("APP_WINDOWS_EXE_URL", "")).strip()
        or str(values.get("APP_WINDOWS_MIRROR_URL", "")).strip()
    )
    docs_url = str(values.get("APP_DOCS_URL", "")).strip()
    schema_version = str(values.get("APP_RELEASE_SCHEMA_VERSION", "")).strip()

    if not android_primary:
        failures.append("android release URL is missing")
    if not windows_primary:
        failures.append("windows release URL is missing")
    if not docs_url:
        failures.append("docs_url is missing")
    if schema_version:
        release_version = str(values.get("APP_ANDROID_VERSION", "")).strip()
        if (
            schema_version != "2"
            or str(values.get("APP_WINDOWS_VERSION", "")).strip()
            != release_version
            or str(values.get("APP_RELEASE_CANDIDATE_LABEL", "")).strip()
            != f"pokrov-{release_version}"
            or len(str(values.get("APP_RELEASE_HANDOFF_SHA256", "")).strip())
            != 64
            or len(
                str(values.get("APP_RELEASE_ARTIFACT_SET_SHA256", "")).strip()
            )
            != 64
        ):
            failures.append("strict v2 release identity is incomplete")
    return failures


def _release_values_preview(values: dict[str, str]) -> str:
    lines = []
    for key in RELEASE_KEYS:
        lines.append(f"{key}={values.get(key, '')}")
    return "\n".join(lines)


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
    ap.add_argument("--dry-run", action="store_true", help="Validate and print release values without SSH writes or restarts.")
    args = ap.parse_args()

    values, source_path = _resolve_release_values(args.metadata_file, args.env_file)
    failures = _validate_release_env(values)
    if failures:
        raise SystemExit("; ".join(failures))

    if args.dry_run:
        print(f"DRY-RUN release handoff from {source_path}")
        print(_release_values_preview(values))
        return 0

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_passwords(Path(args.passwords))
    if not pw:
        raise SystemExit("Missing brain password.")

    paramiko, configure_ssh_host_key_policy = _load_paramiko()
    ssh = paramiko.SSHClient()
    configure_ssh_host_key_policy(ssh)
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
