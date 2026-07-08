from __future__ import annotations

import os
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KNOWN_HOSTS = REPO_ROOT / "VPN NODE SSH KEYS" / "known_hosts"


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return bool(default)
    return raw.strip().lower() in {"1", "true", "yes", "on", "y"}


def _known_hosts_path(raw: str | None = None) -> Path:
    value = str(raw or os.getenv("POKROV_SSH_KNOWN_HOSTS") or "").strip()
    return Path(value).expanduser() if value else DEFAULT_KNOWN_HOSTS


class ExplicitTrustOnFirstUsePolicy(paramiko.MissingHostKeyPolicy):
    def __init__(self, known_hosts_path: Path):
        self.known_hosts_path = known_hosts_path

    def missing_host_key(self, client: paramiko.SSHClient, hostname: str, key: paramiko.PKey) -> None:
        self.known_hosts_path.parent.mkdir(parents=True, exist_ok=True)
        client.get_host_keys().add(hostname, key.get_name(), key)
        client.save_host_keys(str(self.known_hosts_path))


def configure_ssh_host_key_policy(
    client: paramiko.SSHClient,
    *,
    known_hosts_path: str | Path | None = None,
    allow_trust_on_first_use: bool | None = None,
) -> paramiko.SSHClient:
    path = _known_hosts_path(str(known_hosts_path) if known_hosts_path is not None else None)
    try:
        client.load_system_host_keys()
    except Exception:
        pass
    if path.exists():
        try:
            client.load_host_keys(str(path))
        except AttributeError:
            pass

    allow_tofu = _env_bool("POKROV_SSH_TRUST_ON_FIRST_USE", False) if allow_trust_on_first_use is None else bool(allow_trust_on_first_use)
    if allow_tofu:
        client.set_missing_host_key_policy(ExplicitTrustOnFirstUsePolicy(path))
    else:
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
    return client
