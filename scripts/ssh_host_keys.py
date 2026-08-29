from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KNOWN_HOSTS = REPO_ROOT / "VPN NODE SSH KEYS" / "known_hosts"
SSH_CONFIG_ALIAS_RE = re.compile(r"^[A-Za-z0-9_.@:-]+$")


@dataclass(frozen=True)
class OpenSshConfigSession:
    """Run bounded commands through an already trusted OpenSSH config alias."""

    alias: str
    config_path: Path | None = None

    def __post_init__(self) -> None:
        alias = str(self.alias or "").strip()
        if not SSH_CONFIG_ALIAS_RE.fullmatch(alias) or alias.startswith("-"):
            raise ValueError("SSH config alias must be a safe configured alias")
        object.__setattr__(self, "alias", alias)
        if self.config_path is not None:
            config_path = Path(self.config_path).expanduser()
            if not config_path.is_file():
                raise ValueError("SSH config path must name a readable file")
            object.__setattr__(self, "config_path", config_path)

    def run(
        self,
        command: str,
        *,
        timeout: int = 120,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        argv = ["ssh"]
        if self.config_path is not None:
            argv.extend(["-F", str(self.config_path)])
        argv.extend(
            [
                "-T",
                "-o",
                "BatchMode=yes",
                "-o",
                "StrictHostKeyChecking=yes",
                "-o",
                "ClearAllForwardings=yes",
                "-o",
                "RequestTTY=no",
                self.alias,
                command,
            ]
        )
        return subprocess.run(
            argv,
            input=input_text,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def close(self) -> None:
        """Match the Paramiko session lifecycle without persistent state."""


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
