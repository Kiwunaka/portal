from __future__ import annotations

import io
import os
import base64
import struct
import socket
import logging
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa

try:
    import paramiko
except ModuleNotFoundError:
    paramiko = None  # type: ignore[assignment]

try:
    from puttykeys import ppkraw_to_openssh
except ModuleNotFoundError:
    ppkraw_to_openssh = None

from node_passwords import parse_password_candidates, parse_passwords


logging.getLogger("paramiko.transport").setLevel(logging.CRITICAL)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
DEFAULT_KEY_DIR = REPO_ROOT / "VPN NODE SSH KEYS"

KEY_STEMS: dict[str, list[str]] = {
    "brain": ["BRAINnode"],
    "de": ["DEnodeMAX", "DEMAX", "DEnode", "GermanyNode"],
    "us": ["USnode"],
    "ru": ["RUnode", "RUSSIA", "Russia"],
    "ru_spb": ["RUnodeSPB", "RUSSIA", "Russia"],
    "ruspb": ["RUnodeSPB", "RUSSIA", "Russia"],
    "pl": ["PLnode"],
    "it": ["ITnode"],
    "nl": ["NLnode", "Low ping v2", "LowPingV2"],
    "free": ["FREEnode", "FreeNode", "FREE"],
    "mini": ["RUSSIA", "Russia", "RFMINI"],
    "rf1": ["RFRESERVE1", "rf1"],
}

DEFAULT_USERS: dict[str, list[str]] = {
    # mini/RFMINI currently exposes the operator account on port 22. Keep
    # root as a fallback for older notes and emergency reconfiguration.
    "mini": ["kiwunaka", "root"],
}

DEFAULT_PORTS: dict[str, list[int]] = {
    # DEMAX currently exposes SSH on the raw IP through tcp/22, while the DNS
    # route may still answer on the operator port.
    "de": [22, 29374],
    # Fresh 2026-07 replacement nodes expose SSH on the provider-default port.
    "us": [22, 29374],
    "ru": [22, 29374],
    "ru_spb": [22, 29374],
    "ruspb": [22, 29374],
    "nl": [22, 29374],
    "mini": [22, 29374],
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
    if paramiko is None:
        return None
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
    if paramiko is None:
        return None
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


def _load_putty_ed25519_v2(raw: str) -> paramiko.PKey | None:
    if paramiko is None:
        return None
    lines = [line.strip() for line in str(raw or "").strip().splitlines()]
    if not lines or not lines[0].startswith("PuTTY-User-Key-File-2: ssh-ed25519"):
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
    key_type, public_offset = _read_ppk_string(public_blob, 0)
    public_key, public_offset = _read_ppk_string(public_blob, public_offset)
    private_key, private_offset = _read_ppk_string(private_blob, 0)
    if (
        key_type != b"ssh-ed25519"
        or len(public_key) != 32
        or len(private_key) != 32
        or public_offset != len(public_blob)
        or private_offset != len(private_blob)
    ):
        return None

    key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key)
    derived_public = key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    if derived_public != public_key:
        return None
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return paramiko.Ed25519Key.from_private_key(io.StringIO(pem.decode("ascii")))


def _load_putty_key_from_text(raw: str) -> paramiko.PKey | None:
    if ppkraw_to_openssh is not None:
        try:
            key = _load_key_from_text(ppkraw_to_openssh(raw))
            if key:
                return key
        except Exception:
            pass
    try:
        return _load_putty_rsa_v2(raw) or _load_putty_ed25519_v2(raw)
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


def _bind_source_for_node(code: str) -> str:
    code_key = str(code or "").strip().upper()
    node_value = os.getenv(f"POKROV_SSH_BIND_SOURCE_{code_key}", "").strip() if code_key else ""
    return node_value or os.getenv("POKROV_SSH_BIND_SOURCE", "").strip()


def _resolve_ssh_host(host: str) -> str:
    value = str(host or "").strip()
    try:
        socket.inet_pton(socket.AF_INET, value)
        return value
    except OSError:
        pass
    try:
        for family, socktype, _proto, _canonname, sockaddr in socket.getaddrinfo(
            value,
            None,
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
        ):
            if family == socket.AF_INET and socktype == socket.SOCK_STREAM and sockaddr:
                resolved = str(sockaddr[0] or "").strip()
                if resolved:
                    return resolved
    except OSError:
        pass
    return value


def connect_node(
    *,
    code: str,
    host: str,
    user: str = "root",
    port: int = 29374,
    passwords_path: Path | None = None,
    key_dir: Path | None = None,
) -> tuple[paramiko.SSHClient, str]:
    if paramiko is None:
        raise RuntimeError("Paramiko is required for SSH operations")

    from ssh_host_keys import configure_ssh_host_key_policy

    passwords_path = passwords_path or DEFAULT_PASSWORDS
    code_key = str(code or "").lower().strip()
    password_values: list[str] = []
    env_password = os.getenv(f"NODE_PASS_{str(code or '').upper()}", "").strip()
    if env_password:
        password_values.append(env_password)
    if not password_values:
        try:
            password_values.extend(parse_password_candidates(passwords_path, requested_codes=[code]).get(code_key, []))
        except Exception:
            password_values = []
    if not password_values:
        pw_map = parse_passwords(passwords_path, requested_codes=[code])
        file_password = pw_map.get(code_key, "").strip()
        if file_password:
            password_values.append(file_password)
    unique_passwords: list[str] = []
    seen_passwords: set[str] = set()
    for password in password_values:
        if not password or password in seen_passwords:
            continue
        seen_passwords.add(password)
        unique_passwords.append(password)

    pkey = load_private_key(str(code or ""), key_dir=key_dir or passwords_path.parent)

    attempts: list[tuple[str, dict[str, object]]] = []
    if pkey is not None:
        attempts.append(("key", {"pkey": pkey}))
    for idx, password in enumerate(unique_passwords, 1):
        method = "password" if len(unique_passwords) == 1 else f"password#{idx}"
        attempts.append((method, {"password": password}))
    if not attempts:
        raise RuntimeError(f"No SSH auth material found for node {code}")

    ports: list[int] = []
    preferred_ports = DEFAULT_PORTS.get(code_key, [int(port), 22]) if int(port) == 29374 else [int(port), 22]
    for candidate in preferred_ports:
        if candidate not in ports:
            ports.append(candidate)

    users: list[str] = []
    preferred_users = DEFAULT_USERS.get(code_key, [str(user or "root")]) if str(user or "root") == "root" else [str(user)]
    for candidate_user in preferred_users:
        candidate_user = str(candidate_user or "").strip()
        if candidate_user and candidate_user not in users:
            users.append(candidate_user)

    last_error: Exception | None = None
    bind_source = _bind_source_for_node(code)
    connect_host = _resolve_ssh_host(host)
    for target_user in users:
        for target_port in ports:
            for method, auth in attempts:
                cli = paramiko.SSHClient()
                configure_ssh_host_key_policy(cli)
                sock = None
                try:
                    connect_kwargs = dict(auth)
                    if bind_source:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(30)
                        sock.bind((bind_source, 0))
                        sock.connect((connect_host, target_port))
                        connect_kwargs["sock"] = sock
                    cli.connect(
                        connect_host,
                        port=target_port,
                        username=target_user,
                        timeout=30,
                        banner_timeout=30,
                        auth_timeout=30,
                        allow_agent=False,
                        look_for_keys=False,
                        **connect_kwargs,
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
                    if sock is not None:
                        try:
                            sock.close()
                        except Exception:
                            pass
    raise RuntimeError(f"SSH auth failed for node {code}: {last_error}")
