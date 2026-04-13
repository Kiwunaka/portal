#!/usr/bin/env python3
from __future__ import annotations

"""
Apply, inspect, or roll back repo-truth qdisc profiles on a node.

The script is intentionally split into small helpers so tests and operators can
reuse the same normalization and command-building logic.
"""

import argparse
import json
import os
import re
import shlex
import socket
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import paramiko

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from node_access import connect_node

DEFAULT_PROFILES_PATH = REPO_ROOT / "infra" / "node-qdisc-profiles.json"
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
SERVICE_NAME = "portal-node-qdisc.service"
REPO_SERVICE_PATH = "/root/portal_bot/infra/portal-node-qdisc.service"
SYSTEMD_SERVICE_PATH = f"/etc/systemd/system/{SERVICE_NAME}"

NODE_CODE_ALIASES: dict[str, str] = {
    "brain": "brain",
    "brainnode": "brain",
    "us": "us",
    "usnode": "us",
    "pl": "pl",
    "plnode": "pl",
    "it": "it",
    "itnode": "it",
    "nl": "nl",
    "nlnode": "nl",
    "free": "free",
    "freenode": "free",
    "freenlnode": "free",
}


@dataclass(frozen=True)
class QdiscProfile:
    node_code: str
    iface: str
    uplink_mbps: int
    target_rate_mbps: int
    preferred_qdisc: str
    enabled: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "node_code": self.node_code,
            "iface": self.iface,
            "uplink_mbps": self.uplink_mbps,
            "target_rate_mbps": self.target_rate_mbps,
            "preferred_qdisc": self.preferred_qdisc,
            "enabled": self.enabled,
        }


def normalize_node_code(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    short = text.split(".", 1)[0]
    compact = re.sub(r"[^a-z0-9]+", "", short)
    if compact in NODE_CODE_ALIASES:
        return NODE_CODE_ALIASES[compact]
    if compact.endswith("node") and compact[:-4] in NODE_CODE_ALIASES:
        return NODE_CODE_ALIASES[compact[:-4]]
    return compact or short


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return default
        return int(round(float(value)))
    except Exception:
        return default


def _coerce_bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        raw = value.strip().lower()
        if raw in {"1", "true", "yes", "on"}:
            return True
        if raw in {"0", "false", "no", "off"}:
            return False
    return bool(value)


def _normalize_profile(raw: dict[str, Any]) -> QdiscProfile:
    node_code = normalize_node_code(raw.get("node_code") or raw.get("code") or "")
    if not node_code:
        raise ValueError("qdisc profile is missing node_code")

    iface = str(raw.get("iface") or "").strip()
    if not iface:
        raise ValueError(f"qdisc profile {node_code} is missing iface")

    uplink_mbps = _coerce_int(raw.get("uplink_mbps"), 0)
    target_rate_mbps = _coerce_int(raw.get("target_rate_mbps"), 0)
    if target_rate_mbps <= 0 and uplink_mbps > 0:
        target_rate_mbps = max(1, int(round(uplink_mbps * 0.85)))

    preferred_qdisc = str(raw.get("preferred_qdisc") or "cake").strip().lower()
    if preferred_qdisc not in {"cake", "fq_codel"}:
        preferred_qdisc = "cake"

    return QdiscProfile(
        node_code=node_code,
        iface=iface,
        uplink_mbps=uplink_mbps,
        target_rate_mbps=target_rate_mbps,
        preferred_qdisc=preferred_qdisc,
        enabled=_coerce_bool(raw.get("enabled"), True),
    )


def load_profiles(path: Path | str | None = None) -> dict[str, dict[str, Any]]:
    source = Path(path or DEFAULT_PROFILES_PATH)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        if "profiles" in payload:
            payload = payload["profiles"]
        else:
            payload = list(payload.values())
    if not isinstance(payload, list):
        raise ValueError(f"Unexpected qdisc profile format in {source}")

    profiles: dict[str, dict[str, Any]] = {}
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError(f"Invalid qdisc profile entry in {source}")
        profile = _normalize_profile(item)
        if profile.node_code in profiles:
            raise ValueError(f"Duplicate qdisc profile for {profile.node_code}")
        profiles[profile.node_code] = profile.as_dict()
    return profiles


def _detect_local_node_code() -> str:
    env_code = normalize_node_code(os.getenv("NODE_CODE", ""))
    if env_code:
        return env_code
    host = socket.gethostname().strip()
    return normalize_node_code(host)


def _selected_qdisc(profile: dict[str, Any], *, has_cake: bool) -> str:
    preferred = str(profile.get("preferred_qdisc") or "cake").strip().lower()
    if preferred == "fq_codel":
        return "fq_codel"
    if has_cake:
        return "cake"
    return "fq_codel"


def _build_apply_commands(profile: dict[str, Any], has_cake: bool) -> list[str]:
    iface = str(profile["iface"]).strip()
    target_rate = _coerce_int(profile.get("target_rate_mbps"), 0)
    if target_rate <= 0:
        target_rate = max(1, _coerce_int(profile.get("uplink_mbps"), 0))
    selected_qdisc = _selected_qdisc(profile, has_cake=has_cake)

    commands = [f"tc qdisc del dev {shlex.quote(iface)} root 2>/dev/null || true"]
    if selected_qdisc == "cake":
        commands.append(
            "tc qdisc replace dev "
            f"{shlex.quote(iface)} root cake bandwidth {target_rate}mbit nat triple-isolate"
        )
    else:
        commands.append(f"tc qdisc replace dev {shlex.quote(iface)} root fq_codel")
    commands.append(f"tc -s qdisc show dev {shlex.quote(iface)}")
    return commands


def _build_show_commands(profile: dict[str, Any]) -> list[str]:
    iface = str(profile["iface"]).strip()
    return [f"tc -s qdisc show dev {shlex.quote(iface)}"]


def _build_rollback_commands(profile: dict[str, Any]) -> list[str]:
    iface = str(profile["iface"]).strip()
    return [
        *_build_persistence_commands("disable"),
        f"tc qdisc del dev {shlex.quote(iface)} root 2>/dev/null || true",
        f"tc -s qdisc show dev {shlex.quote(iface)} || true",
    ]


def _build_persistence_commands(action: str) -> list[str]:
    normalized = str(action or "").strip().lower()
    if normalized == "install":
        return [
            f"install -D -m 0644 {shlex.quote(REPO_SERVICE_PATH)} {shlex.quote(SYSTEMD_SERVICE_PATH)}",
            "systemctl daemon-reload",
            f"systemctl enable --now {SERVICE_NAME}",
        ]
    if normalized == "disable":
        return [
            f"systemctl disable --now {SERVICE_NAME} >/dev/null 2>&1 || true",
            "systemctl daemon-reload",
        ]
    if normalized == "uninstall":
        return [
            f"systemctl disable --now {SERVICE_NAME} >/dev/null 2>&1 || true",
            f"rm -f {shlex.quote(SYSTEMD_SERVICE_PATH)}",
            "systemctl daemon-reload",
            f"systemctl reset-failed {SERVICE_NAME} >/dev/null 2>&1 || true",
        ]
    raise ValueError(f"Unsupported persistence action: {action}")


def _probe_has_cake(executor) -> bool:
    result = executor("modprobe -n -q sch_cake >/dev/null 2>&1 && echo cake || true")
    if isinstance(result, tuple):
        _code, out, err = result
        text = out or err
    else:
        text = result or ""
    return "cake" in str(text).strip().lower()


def _run_local(cmd: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["bash", "-lc", cmd],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _run_remote(ssh: paramiko.SSHClient, cmd: str) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(f"bash -lc {shlex.quote(cmd)}", timeout=600)
    code = stdout.channel.recv_exit_status()
    return code, stdout.read().decode("utf-8", errors="replace"), stderr.read().decode("utf-8", errors="replace")


def _select_profile(profiles: dict[str, dict[str, Any]], node_code: str | None = None) -> dict[str, Any]:
    code = normalize_node_code(node_code or _detect_local_node_code())
    if code in profiles:
        return profiles[code]
    if len(profiles) == 1:
        return next(iter(profiles.values()))
    available = ", ".join(sorted(profiles))
    raise SystemExit(f"No qdisc profile found for node_code={code!r}. Available: {available}")


def _print(text: str) -> None:
    enc = sys.stdout.encoding or "utf-8"
    safe = str(text or "").encode(enc, errors="replace").decode(enc, errors="replace")
    print(safe)


def _should_use_cake(*, force_fq_codel: bool, executor) -> bool:
    if force_fq_codel:
        return False
    try:
        return _probe_has_cake(executor)
    except Exception:
        return False


def apply_profile(
    profile: dict[str, Any],
    *,
    force_fq_codel: bool = False,
    executor=_run_local,
) -> tuple[int, str]:
    if not _coerce_bool(profile.get("enabled"), True):
        commands = _build_rollback_commands(profile)
        outputs: list[str] = []
        for cmd in commands:
            code, out, err = executor(cmd)
            outputs.append((out.strip() or err.strip()).strip())
            if code != 0:
                raise SystemExit(out.strip() or err.strip() or f"qdisc disable failed: {cmd}")
        summary = f"node={profile['node_code']} iface={profile['iface']} status=disabled"
        return 0, summary + ("\n" + "\n".join(x for x in outputs if x) if outputs else "")

    has_cake = _should_use_cake(force_fq_codel=force_fq_codel, executor=executor)
    commands = _build_apply_commands(profile, has_cake=has_cake)
    outputs: list[str] = []
    for cmd in commands:
        code, out, err = executor(cmd)
        outputs.append((out.strip() or err.strip()).strip())
        if code != 0:
            raise SystemExit(out.strip() or err.strip() or f"qdisc apply failed: {cmd}")
    selected_qdisc = _selected_qdisc(profile, has_cake=has_cake)
    summary = f"node={profile['node_code']} iface={profile['iface']} qdisc={selected_qdisc}"
    if selected_qdisc != "cake" and str(profile.get("preferred_qdisc") or "cake").strip().lower() == "cake":
        summary += " fallback=fq_codel"
    return 0, summary + ("\n" + "\n".join(x for x in outputs if x) if outputs else "")


def show_profile(profile: dict[str, Any], *, executor=_run_local) -> tuple[int, str]:
    outputs: list[str] = []
    for cmd in _build_show_commands(profile):
        code, out, err = executor(cmd)
        outputs.append(out.strip() or err.strip())
        if code != 0:
            raise SystemExit(out.strip() or err.strip() or f"qdisc show failed: {cmd}")
    return 0, "\n".join(x for x in outputs if x)


def rollback_profile(profile: dict[str, Any], *, executor=_run_local) -> tuple[int, str]:
    outputs: list[str] = []
    for cmd in _build_rollback_commands(profile):
        code, out, err = executor(cmd)
        outputs.append(out.strip() or err.strip())
        if code != 0:
            raise SystemExit(out.strip() or err.strip() or f"qdisc rollback failed: {cmd}")
    return 0, "\n".join(x for x in outputs if x)


def persistence_action(action: str, *, executor=_run_local) -> tuple[int, str]:
    outputs: list[str] = []
    for cmd in _build_persistence_commands(action):
        code, out, err = executor(cmd)
        outputs.append(out.strip() or err.strip())
        if code != 0:
            raise SystemExit(out.strip() or err.strip() or f"qdisc persistence {action} failed: {cmd}")
    return 0, "\n".join(x for x in outputs if x)


def _build_ssh_executor(ssh: paramiko.SSHClient):
    def _exec(cmd: str) -> tuple[int, str, str]:
        return _run_remote(ssh, cmd)

    return _exec


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply or inspect node qdisc profiles.")
    ap.add_argument("action", choices=["apply", "show", "rollback", "install", "disable", "uninstall"], nargs="?", default="apply")
    ap.add_argument("--profiles", default=str(DEFAULT_PROFILES_PATH))
    ap.add_argument("--node-code", default="", help="node code from repo-truth profile catalog")
    ap.add_argument("--host", default="", help="remote host to connect to; omit for local execution")
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--force-fq-codel", action="store_true", help="skip CAKE even when available")
    args = ap.parse_args()

    profiles = load_profiles(Path(args.profiles))
    profile = _select_profile(profiles, args.node_code or None)

    if args.host.strip():
        ssh, _auth_method = connect_node(
            code=profile["node_code"],
            host=args.host.strip(),
            user=args.ssh_user,
            port=args.ssh_port,
            passwords_path=Path(args.passwords),
        )
        try:
            executor = _build_ssh_executor(ssh)
            if args.action == "apply":
                _code, text = apply_profile(profile, force_fq_codel=args.force_fq_codel, executor=executor)
            elif args.action == "show":
                _code, text = show_profile(profile, executor=executor)
            elif args.action == "rollback":
                _code, text = rollback_profile(profile, executor=executor)
            else:
                _code, text = persistence_action(args.action, executor=executor)
            _print(text)
            return 0
        finally:
            ssh.close()

    if args.action == "apply":
        _code, text = apply_profile(profile, force_fq_codel=args.force_fq_codel, executor=_run_local)
    elif args.action == "show":
        _code, text = show_profile(profile, executor=_run_local)
    elif args.action == "rollback":
        _code, text = rollback_profile(profile, executor=_run_local)
    else:
        _code, text = persistence_action(args.action, executor=_run_local)
    _print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
