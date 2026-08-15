#!/usr/bin/env python3
"""Create server-owned emergency keys and configure the worker without printing secrets."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
from pathlib import Path

try:
    from node_access import DEFAULT_PASSWORDS, connect_node
except ImportError:  # pragma: no cover - package import
    from .node_access import DEFAULT_PASSWORDS, connect_node


PROBE_URL = "https://connect.pokrov.space/api/emergency-probe/payload-v1"
PROBE_PAYLOAD = b"POKROV emergency probe payload v1\n"
PROBE_DIGEST = hashlib.sha256(PROBE_PAYLOAD).hexdigest()
REMOTE_ENV = "/root/portal_bot/.env"
REMOTE_ADAPTER = "/root/portal_bot/emergency_linux_probe_adapter.py"


def _remote_script(*, enable_worker: bool) -> str:
    enabled = "1" if enable_worker else "0"
    values = {
        "EMERGENCY_CATALOG_WORKER_ENABLED": enabled,
        "EMERGENCY_CATALOG_PROBE_ADAPTER_PATH": REMOTE_ADAPTER,
        "EMERGENCY_CATALOG_PROBE_URL": PROBE_URL,
        "EMERGENCY_CATALOG_EXPECTED_PAYLOAD_SHA256": PROBE_DIGEST,
        "EMERGENCY_CATALOG_WORKER_INTERVAL_SECONDS": "7200",
        "EMERGENCY_CATALOG_PROBE_CONCURRENCY": "4",
        "EMERGENCY_CATALOG_PROBE_TIMEOUT_SECONDS": "30",
    }
    return f"""
import base64
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

env_path = Path({REMOTE_ENV!r})
if not env_path.is_file():
    raise SystemExit("env_missing")
raw = env_path.read_text(encoding="utf-8")
lines = raw.splitlines()
parsed = {{}}
for line in lines:
    if not line or line.lstrip().startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    parsed[key.strip()] = value.strip()

secret_names = (
    "EMERGENCY_CATALOG_MATERIAL_KEY_B64",
    "EMERGENCY_CATALOG_SIGNING_PRIVATE_KEY_B64",
)
present = [bool(parsed.get(name)) for name in secret_names]
key_id_present = bool(parsed.get("EMERGENCY_CATALOG_SIGNING_KEY_ID"))
if any(present) or key_id_present:
    if not all(present) or not key_id_present:
        raise SystemExit("partial_emergency_key_state")
    created = False
    key_id = parsed["EMERGENCY_CATALOG_SIGNING_KEY_ID"]
    if re.fullmatch(r"[a-z0-9][a-z0-9._-]{{0,63}}", key_id) is None:
        raise SystemExit("invalid_existing_key_id")
    try:
        private_raw = base64.urlsafe_b64decode(
            parsed["EMERGENCY_CATALOG_SIGNING_PRIVATE_KEY_B64"] + "=" * 3
        )
        material_raw = base64.urlsafe_b64decode(
            parsed["EMERGENCY_CATALOG_MATERIAL_KEY_B64"] + "=" * 3
        )
    except Exception as exc:
        raise SystemExit("invalid_existing_key_encoding") from exc
    if len(private_raw) != 32 or len(material_raw) != 32:
        raise SystemExit("invalid_existing_key_size")
else:
    created = True
    key_id = "emg-20260815-v1"
    private = Ed25519PrivateKey.generate()
    private_raw = private.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    material_raw = os.urandom(32)
    parsed["EMERGENCY_CATALOG_SIGNING_KEY_ID"] = key_id
    parsed["EMERGENCY_CATALOG_SIGNING_PRIVATE_KEY_B64"] = base64.urlsafe_b64encode(private_raw).decode("ascii").rstrip("=")
    parsed["EMERGENCY_CATALOG_MATERIAL_KEY_B64"] = base64.urlsafe_b64encode(material_raw).decode("ascii").rstrip("=")

private = Ed25519PrivateKey.from_private_bytes(private_raw)
public_raw = private.public_key().public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw,
)
updates = {values!r}
updates["EMERGENCY_CATALOG_SIGNING_KEY_ID"] = key_id
for key, value in updates.items():
    parsed[key] = value

keys_to_replace = set(updates) | set(secret_names)
out = []
seen = set()
for line in lines:
    if line and not line.lstrip().startswith("#") and "=" in line:
        key = line.split("=", 1)[0].strip()
        if key in keys_to_replace:
            if key not in seen:
                out.append(f"{{key}}={{parsed[key]}}")
                seen.add(key)
            continue
    out.append(line)
for key in sorted(keys_to_replace - seen):
    out.append(f"{{key}}={{parsed[key]}}")
payload = "\\n".join(out).rstrip("\\n") + "\\n"

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backup = env_path.with_name(env_path.name + f".pre-emergency.{{stamp}}.bak")
shutil.copy2(env_path, backup)
os.chmod(backup, 0o600)
fd, tmp_name = tempfile.mkstemp(prefix=".env.emergency.", dir=str(env_path.parent), text=True)
try:
    with os.fdopen(fd, "w", encoding="utf-8", newline="\\n") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(tmp_name, 0o600)
    os.replace(tmp_name, env_path)
finally:
    if os.path.exists(tmp_name):
        os.unlink(tmp_name)

print(json.dumps({{
    "ok": True,
    "created": created,
    "key_id": key_id,
    "public_key_b64": base64.urlsafe_b64encode(public_raw).decode("ascii").rstrip("="),
    "worker_enabled": {enable_worker!r},
    "probe_digest": {PROBE_DIGEST!r},
    "backup_name": backup.name,
}}, sort_keys=True))
""".strip()


def _valid_key_id(value: str) -> bool:
    return re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", value) is not None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brain-ip", required=True)
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--enable-worker", action="store_true")
    args = parser.parse_args()

    ssh, auth_method = connect_node(
        code="brain",
        host=args.brain_ip,
        user=args.ssh_user,
        port=args.ssh_port,
        passwords_path=Path(args.passwords),
    )
    try:
        command = (
            "/root/portal_bot/venv/bin/python -c "
            + shlex.quote(_remote_script(enable_worker=bool(args.enable_worker)))
        )
        _stdin, stdout, stderr = ssh.exec_command(command, timeout=120)
        exit_code = int(stdout.channel.recv_exit_status())
        output = stdout.read().decode("utf-8", errors="replace").strip()
        error = stderr.read().decode("utf-8", errors="replace").strip()
        if exit_code != 0:
            safe_code = error.splitlines()[-1].strip() if error else "remote_prepare_failed"
            raise SystemExit(f"remote_prepare_failed:{safe_code[:80]}")
        result = json.loads(output)
        if (
            result.get("ok") is not True
            or not _valid_key_id(str(result.get("key_id") or ""))
            or len(str(result.get("public_key_b64") or "")) != 43
            or str(result.get("probe_digest") or "") != PROBE_DIGEST
        ):
            raise SystemExit("remote_prepare_invalid_readback")
        print(f"brain auth: {auth_method}")
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
