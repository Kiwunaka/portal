from __future__ import annotations

import io
import logging
import os
import base64
import struct
from pathlib import Path

import paramiko
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
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


def _quiet_paramiko_transport_logger() -> None:
    logging.getLogger("paramiko.transport").setLevel(logging.CRITICAL)


_quiet_paramiko_transport_logger()


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


def _read_ppk_string(blob: bytes, offset: int) -> tuple[bytes, int]:
    if offset + 4 > len(blob):
        raise ValueError("truncated PPK string")
    size = struct.unpack(">I", blob[offset : offset + 4])[0]
    offset += 4
    if offset + size > len(blob):
        raise ValueError("truncated PPK string payload")
    return blob[offset : offset + size], offset + size


def _mpint_to_int(value: bytes) -> int:
    return int.from_bytes(value or b"\x00", "big", signed=False)


def _load_putty_rsa_v2(raw: str) -> paramiko.PKey | None:
    lines = [line.strip() for line in str(raw or "").strip().splitlines()]
    if not lines or not lines[0].startswith("PuTTY-User-Key-File-2: ssh-rsa"):
        return None

    public_lines = private_lines = 0
    public_start = private_start = -1
    encryption = ""
    for idx, line in enumerate(lines):
        if line.startswith("Encryption:"):
            encryption = line.split(":", 1)[1].strip().lower()
        elif line.startswith("Public-Lines:"):
            public_lines = int(line.split(":", 1)[1].strip())
            public_start = idx + 1
        elif line.startswith("Private-Lines:"):
            private_lines = int(line.split(":", 1)[1].strip())
            private_start = idx + 1

    if encryption not in {"", "none"}:
        return None
    if public_start < 0 or private_start < 0 or public_lines <= 0 or private_lines <= 0:
        return None

    public_blob = base64.b64decode("".join(lines[public_start : public_start + public_lines]))
    private_blob = base64.b64decode("".join(lines[private_start : private_start + private_lines]))

    offset = 0
    key_type, offset = _read_ppk_string(public_blob, offset)
    if key_type != b"ssh-rsa":
        return None
    public_e, offset = _read_ppk_string(public_blob, offset)
    public_n, offset = _read_ppk_string(public_blob, offset)

    private_offset = 0
    private_d, private_offset = _read_ppk_string(private_blob, private_offset)
    private_p, private_offset = _read_ppk_string(private_blob, private_offset)
    private_q, private_offset = _read_ppk_string(private_blob, private_offset)
    private_iqmp, private_offset = _read_ppk_string(private_blob, private_offset)

    p = _mpint_to_int(private_p)
    q = _mpint_to_int(private_q)
    d = _mpint_to_int(private_d)
    e = _mpint_to_int(public_e)
    n = _mpint_to_int(public_n)
    numbers = rsa.RSAPrivateNumbers(
        p=p,
        q=q,
        d=d,
        dmp1=d % (p - 1),
        dmq1=d % (q - 1),
        iqmp=_mpint_to_int(private_iqmp),
        public_numbers=rsa.RSAPublicNumbers(e=e, n=n),
    )
    pem = numbers.private_key().private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return paramiko.RSAKey.from_private_key(io.StringIO(pem.decode("ascii")))


def _load_putty_key_from_text(raw: str) -> paramiko.PKey | None:
    try:
        key = _load_key_from_text(ppkraw_to_openssh(raw))
        if key:
            return key
    except Exception:
        pass
    try:
        return _load_putty_rsa_v2(raw)
    except Exception:
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
            key = _load_putty_key_from_text(raw)
            if key:
                return key
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
