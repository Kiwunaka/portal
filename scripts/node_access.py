from __future__ import annotations

import io
import os
from pathlib import Path

import paramiko
from puttykeys import ppkraw_to_openssh

from node_passwords import parse_passwords


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
DEFAULT_KEY_DIR = REPO_ROOT / "VPN NODE SSH KEYS"

KEY_STEMS: dict[str, list[str]] = {
    "brain": ["BRAINnode"],
    "us": ["USnode"],
    "pl": ["PLnode"],
    "it": ["ITnode"],
    "nl": ["NLnode", "Low ping v2", "LowPingV2"],
    "free": ["FREEnode", "FreeNode", "FREE"],
    "mini": ["RUSSIA", "Russia", "RFMINI"],
    "rf1": ["RFRESERVE1", "rf1"],
}


def _private_key_candidates(code: str, key_dir: Path) -> list[Path]:
    code = str(code or "").strip().lower()
    candidates: list[Path] = []
    for stem in KEY_STEMS.get(code, []):
        candidates.append(key_dir / f"{stem}_private.ppk")
        candidates.append(key_dir / f"{stem}_private")
        candidates.append(key_dir / f"{stem}.ppk")
        candidates.append(key_dir / f"{stem}")
    candidates.extend(sorted(key_dir.glob(f"*{code}*_private.ppk")))
    candidates.extend(sorted(key_dir.glob(f"*{code}*_private")))
    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def _load_key_from_text(text: str) -> paramiko.PKey | None:
    for key_cls in (paramiko.Ed25519Key, paramiko.RSAKey, paramiko.ECDSAKey):
        try:
            return key_cls.from_private_key(io.StringIO(text))
        except Exception:
            continue
    return None


def load_private_key(code: str, *, key_dir: Path | None = None) -> paramiko.PKey | None:
    key_dir = key_dir or DEFAULT_KEY_DIR
    env_path = os.getenv(f"NODE_KEY_{str(code or '').upper()}", "").strip()
    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(_private_key_candidates(str(code or ""), key_dir))

    for path in candidates:
        try:
            if not path.exists() or not path.is_file():
                continue
            raw = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        text = raw
        if raw.lstrip().startswith("PuTTY-User-Key-File-"):
            try:
                text = ppkraw_to_openssh(raw)
            except Exception:
                continue
        key = _load_key_from_text(text)
        if key:
            return key
    return None


def connect_node(
    *,
    code: str,
    host: str,
    user: str = "root",
    port: int = 29374,
    passwords_path: Path | None = None,
    key_dir: Path | None = None,
) -> tuple[paramiko.SSHClient, str]:
    passwords_path = passwords_path or DEFAULT_PASSWORDS
    pw_map = parse_passwords(passwords_path, requested_codes=[code])
    password = os.getenv(f"NODE_PASS_{str(code or '').upper()}", "").strip() or pw_map.get(str(code or "").lower(), "").strip()
    pkey = load_private_key(str(code or ""), key_dir=key_dir or passwords_path.parent)

    attempts: list[tuple[str, dict[str, object]]] = []
    if pkey is not None:
        attempts.append(("key", {"pkey": pkey}))
    if password:
        attempts.append(("password", {"password": password}))
    if not attempts:
        raise RuntimeError(f"No SSH auth material found for node {code}")

    ports: list[int] = []
    for candidate in (int(port), 22):
        if candidate not in ports:
            ports.append(candidate)

    last_error: Exception | None = None
    for target_port in ports:
        for method, auth in attempts:
            cli = paramiko.SSHClient()
            cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                cli.connect(
                    host,
                    port=target_port,
                    username=user,
                    timeout=30,
                    banner_timeout=30,
                    auth_timeout=30,
                    allow_agent=False,
                    look_for_keys=False,
                    **auth,
                )
                t = cli.get_transport()
                if t:
                    t.set_keepalive(30)
                return cli, method
            except Exception as exc:
                last_error = exc
                try:
                    cli.close()
                except Exception:
                    pass
    raise RuntimeError(f"SSH auth failed for node {code}: {last_error}")
