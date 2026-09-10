"""Provision the existing client-pinned signer to the owned Brain over restricted SSH.

The operator installs this receiver and the exact client public seed before
dispatch. The temporary SSH key must have a forced command for this receiver.
No signer secret is written on the runner or included in an artifact.
"""
from __future__ import annotations

import argparse
import base64
import hmac
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from typing import Any

import paramiko

from verify_support_signing_custody import verify_custody

BRAIN_HOST = "82.21.114.104"
BRAIN_PORT = 29374
# Read through the already authenticated operator connection, 2026-09-10.
BRAIN_HOST_KEY = "AAAAC3NzaC1lZDI1NTE5AAAAINazI4CgoOzUzd2HgzNa97+6DU1H9YVg/VAmsmKWTV5S"
ENVIRONMENT_PATH = Path("/etc/pokrov/support-mode.env")
INPUT_KEYS = {
    "platform_revision", "client_revision", "key_id", "private_key_b64url",
    "public_key_b64url", "code_secret",
}
RECEIPT_KEYS = {
    "status", "key_id", "public_key_sha256", "client_seed_sha256",
    "platform_revision", "client_revision", "environment_path",
    "environment_mode", "environment_uid", "created", "issuance_enabled",
}


class ProvisionError(ValueError):
    pass


def environment_bytes(payload: dict[str, Any], seed_path: Path) -> tuple[bytes, dict[str, Any]]:
    if not isinstance(payload, dict) or set(payload) != INPUT_KEYS or any(not isinstance(v, str) for v in payload.values()):
        raise ProvisionError("provisioning input shape invalid")
    receipt = verify_custody(client_seed_path=seed_path, **payload)
    # EnvironmentFile is line based. Refuse values that could add directives.
    values = {
        "POKROV_SUPPORT_MODE_SIGNING_KEY_ID": receipt["key_id"],
        "POKROV_SUPPORT_MODE_SIGNING_PRIVATE_KEY_B64": payload["private_key_b64url"].strip(),
        "POKROV_SUPPORT_MODE_CODE_SECRET": payload["code_secret"],
    }
    lines = []
    for key, value in values.items():
        if any(c in value for c in "\r\n\0"):
            raise ProvisionError("provisioning value is not a single environment line")
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'{key}="{escaped}"\n')
    return "".join(lines).encode("utf-8"), receipt


def install_environment(path: Path, raw: bytes) -> bool:
    """Atomic first installation; an existing different key is never overwritten."""
    if path.exists():
        if path.is_symlink() or not hmac.compare_digest(path.read_bytes(), raw):
            raise ProvisionError("existing runtime signing configuration differs")
        return False
    fd, temporary = tempfile.mkstemp(prefix=".support-mode-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        # link fails if another receiver creates the destination concurrently.
        os.link(temporary, path)
    finally:
        os.unlink(temporary)
    return True


def receive(seed_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    if os.geteuid() != 0:
        raise ProvisionError("runtime provisioning requires the root-owned receiver")
    parent = ENVIRONMENT_PATH.parent.stat()
    if parent.st_uid != 0 or parent.st_mode & 0o022 or ENVIRONMENT_PATH.parent.is_symlink():
        raise ProvisionError("runtime configuration directory ownership invalid")
    api_user = subprocess.check_output(
        ["systemctl", "show", "portal-api", "--property=User", "--value"], text=True
    ).strip()
    if api_user != "pokrov-api":
        raise ProvisionError("API identity isolation is not configured")
    pid = subprocess.check_output(
        ["systemctl", "show", "portal-api", "--property=MainPID", "--value"], text=True
    ).strip()
    status = dict(line.split(":", 1) for line in Path("/proc", pid, "status").read_text().splitlines() if ":" in line)
    if any(value == "0" for value in status["Uid"].split()) or int(status["CapEff"], 16):
        raise ProvisionError("running API identity isolation is not effective")
    raw, custody = environment_bytes(payload, seed_path)
    created = install_environment(ENVIRONMENT_PATH, raw)
    installed = ENVIRONMENT_PATH.stat()
    if installed.st_uid != 0 or stat.S_IMODE(installed.st_mode) != 0o600:
        raise ProvisionError("runtime signing file ownership invalid")
    return {
        "status": "PASS_PROVISIONED_NOT_ENABLED",
        **{k: custody[k] for k in ("key_id", "public_key_sha256", "client_seed_sha256", "platform_revision", "client_revision")},
        "environment_path": str(ENVIRONMENT_PATH),
        "environment_mode": "0600", "environment_uid": 0, "created": created,
        "issuance_enabled": False,
    }


def provision(seed_path: Path, platform_revision: str, client_revision: str) -> dict[str, Any]:
    payload = {
        "platform_revision": platform_revision, "client_revision": client_revision,
        "key_id": os.getenv("POKROV_SUPPORT_MODE_SIGNING_KEY_ID", ""),
        "private_key_b64url": os.getenv("POKROV_SUPPORT_MODE_SIGNING_PRIVATE_KEY_B64", ""),
        "public_key_b64url": os.getenv("POKROV_SUPPORT_MODE_SIGNING_PUBLIC_KEY_B64", ""),
        "code_secret": os.getenv("POKROV_SUPPORT_MODE_CODE_SECRET", ""),
    }
    _, custody = environment_bytes(payload, seed_path)
    ssh_key = os.getenv("POKROV_SUPPORT_PROVISION_SSH_KEY", "")
    if not ssh_key:
        raise ProvisionError("restricted provisioning SSH key is unavailable")
    key = paramiko.Ed25519Key.from_private_key(io.StringIO(ssh_key))
    with paramiko.SSHClient() as ssh:
        ssh.get_host_keys().add(
            f"[{BRAIN_HOST}]:{BRAIN_PORT}", "ssh-ed25519",
            paramiko.Ed25519Key(data=base64.b64decode(BRAIN_HOST_KEY)),
        )
        ssh.set_missing_host_key_policy(paramiko.RejectPolicy())
        ssh.connect(BRAIN_HOST, port=BRAIN_PORT, username="root", pkey=key,
                    allow_agent=False, look_for_keys=False, timeout=20, auth_timeout=20)
        stdin, stdout, stderr = ssh.exec_command("provision-support-mode", timeout=30)
        stdin.write(json.dumps(payload))
        stdin.flush()
        stdin.channel.shutdown_write()
        response = stdout.read(8193)
        error = stderr.read(8193)
        code = stdout.channel.recv_exit_status()
    if code != 0 or error or len(response) > 8192:
        raise ProvisionError("runtime receiver failed; inspect its public status on Brain")
    try:
        receipt = json.loads(response)
    except (ValueError, UnicodeError) as exc:
        raise ProvisionError("runtime receiver returned invalid public status") from exc
    if not isinstance(receipt, dict) or set(receipt) != RECEIPT_KEYS:
        raise ProvisionError("runtime receiver public status shape invalid")
    expected = {
        "status": "PASS_PROVISIONED_NOT_ENABLED", "environment_path": str(ENVIRONMENT_PATH),
        "environment_mode": "0600", "environment_uid": 0, "issuance_enabled": False,
        **{k: custody[k] for k in ("key_id", "public_key_sha256", "client_seed_sha256", "platform_revision", "client_revision")},
    }
    if any(receipt[k] != v for k, v in expected.items()) or type(receipt["created"]) is not bool:
        raise ProvisionError("runtime receiver public status binding mismatch")
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client-seed", type=Path, required=True)
    parser.add_argument("--receive", action="store_true")
    parser.add_argument("--platform-revision")
    parser.add_argument("--client-revision")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.receive:
            raw = sys.stdin.buffer.read(65537)
            if len(raw) > 65536:
                raise ProvisionError("provisioning input exceeds limit")
            result = receive(args.client_seed, json.loads(raw))
            print(json.dumps(result))
        else:
            if args.output is None:
                raise ProvisionError("public provisioning receipt path required")
            result = provision(args.client_seed, args.platform_revision or "", args.client_revision or "")
            args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            print("Support signer provisioned to Brain; issuance remains disabled.")
    except Exception:
        # SSH/library exceptions can carry request data. Never emit their text.
        print("Support signer provisioning failed; no secret output retained.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
