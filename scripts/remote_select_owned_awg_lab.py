from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shlex
from pathlib import Path
from typing import Any

from node_access import DEFAULT_PASSWORDS, connect_node
from remote_activate_owned_awg_labs import (
    _load_emulator_identity,
    _psql,
    _resolve_target_user,
)


COHORT_NAME = "candidate4-awg-lab"
ALLOWED_PROFILES = ("default", "awg2_lab", "awg31_lab")


_REMOTE_HELPER = r'''
import hashlib
import hmac
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

payload = json.loads(sys.stdin.read())
pid = subprocess.check_output(
    ["systemctl", "show", "portal-api", "-p", "MainPID", "--value"], text=True
).strip()
with open(f"/proc/{pid}/environ", "rb") as handle:
    env = {}
    for item in handle.read().split(b"\0"):
        if b"=" in item:
            key, value = item.split(b"=", 1)
            env[key.decode("utf-8", "replace")] = value.decode("utf-8", "replace")
bot_token = env.get("BOT_TOKEN", "").strip()
admin_id = env.get("ADMIN_ID", "").strip()
if not bot_token or not admin_id.isdigit():
    raise SystemExit("portal admin runtime identity unavailable")

params = {
    "auth_date": str(int(time.time())),
    "query_id": "POKROVAWGLABSELECT",
    "user": json.dumps(
        {"id": int(admin_id), "first_name": "POKROV", "username": "operator"},
        separators=(",", ":"),
    ),
}
check = "\n".join(f"{key}={value}" for key, value in sorted(params.items()))
secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
params["hash"] = hmac.new(secret_key, check.encode(), hashlib.sha256).hexdigest()
init_data = urllib.parse.urlencode(params)

def request(method, path, body=None, headers=None):
    data = None if body is None else json.dumps(body, separators=(",", ":")).encode()
    merged = {
        "X-Telegram-Init-Data": init_data,
        "User-Agent": "pokrov-awg-lab-selector/1",
    }
    if data is not None:
        merged["Content-Type"] = "application/json"
    merged.update(headers or {})
    req = urllib.request.Request(
        "https://api.pokrov.space" + path,
        data=data,
        headers=merged,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            raw = response.read()
            return json.loads(raw.decode()) if raw else {}
    except urllib.error.HTTPError as exc:
        safe_path = re.sub(r"/users/[^/]+", "/users/{id}", path)
        raise RuntimeError(f"admin api {method} {safe_path} failed HTTP {exc.code}") from None

def guarded(body):
    prepared = request(
        "POST",
        "/api/admin/action-intents",
        {
            "action": "network_rollout_config.update",
            "target": {"type": "config", "id": "network-rollout"},
            "payload": body,
        },
    )
    challenge = str(prepared.get("confirmation_challenge") or "")
    intent_id = str(prepared.get("intent_id") or "")
    if not challenge or not intent_id:
        raise RuntimeError("network rollout intent prepare failed")
    return request(
        "PUT",
        "/api/admin/network-rollout-config",
        body,
        {
            "X-Admin-Intent-Id": intent_id,
            "X-Admin-Idempotency-Key": str(uuid.uuid4()),
            "X-Admin-Confirmation-SHA256": hashlib.sha256(challenge.encode()).hexdigest(),
        },
    )

profile = str(payload["profile"])
install_id = str(payload["install_id"])
tg_id = int(payload["tg_id"])
current = request("GET", "/api/admin/network-rollout-config")["network_rollout_config"]
cohorts = dict(current.get("cohort_overrides") or {})
cohort = dict(cohorts.get("candidate4-awg-lab") or {})
if profile == "default":
    cohort["install_ids"] = [
        value for value in list(cohort.get("install_ids") or []) if value != install_id
    ]
    cohort["tg_ids"] = [
        value for value in list(cohort.get("tg_ids") or []) if int(value) != tg_id
    ]
    cohort["linked_tg_ids"] = [
        value for value in list(cohort.get("linked_tg_ids") or []) if int(value) != tg_id
    ]
    if not any(
        list(cohort.get(field) or [])
        for field in ("install_ids", "tg_ids", "linked_tg_ids")
    ):
        cohorts.pop("candidate4-awg-lab", None)
    else:
        cohorts["candidate4-awg-lab"] = cohort
    for lab_name in ("awg2_lab", "awg31_lab"):
        lab = dict(current.get(lab_name) or {})
        lab["allowlist_install_ids"] = [
            value
            for value in list(lab.get("allowlist_install_ids") or [])
            if value != install_id
        ]
        lab["allowlist_tg_ids"] = [
            value
            for value in list(lab.get("allowlist_tg_ids") or [])
            if int(value) != tg_id
        ]
        current[lab_name] = lab
else:
    cohort.update({
        "transport_profile": profile,
        "install_ids": [install_id],
        "tg_ids": [tg_id],
        "linked_tg_ids": [],
        "platforms": ["android"],
    })
    cohorts["candidate4-awg-lab"] = cohort
current["cohort_overrides"] = cohorts
guarded(current)
readback = request("GET", "/api/admin/network-rollout-config")["network_rollout_config"]
readback_cohort = dict(
    (readback.get("cohort_overrides") or {}).get("candidate4-awg-lab") or {}
)
identity_present = bool(
    install_id in list(readback_cohort.get("install_ids") or [])
    or tg_id in [int(value) for value in list(readback_cohort.get("tg_ids") or [])]
    or tg_id in [int(value) for value in list(readback_cohort.get("linked_tg_ids") or [])]
)
lab_identity_present = False
for lab_name in ("awg2_lab", "awg31_lab"):
    lab = dict(readback.get(lab_name) or {})
    lab_identity_present = bool(
        lab_identity_present
        or install_id in list(lab.get("allowlist_install_ids") or [])
        or tg_id in [int(value) for value in list(lab.get("allowlist_tg_ids") or [])]
    )
print(json.dumps({
    "selected_profile": profile,
    "cohort_identity_present": identity_present,
    "lab_allowlist_identity_present": lab_identity_present,
}))
'''


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Guarded selector for the isolated owned AWG2/AWG3.1 cohort; "
            "default removes the exact device from the lab."
        )
    )
    parser.add_argument("profile", choices=ALLOWED_PROFILES)
    parser.add_argument("--brain-ip", default="82.21.114.104")
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--known-hosts", required=True)
    parser.add_argument("--adb", required=True)
    parser.add_argument("--adb-serial", default="emulator-5554")
    parser.add_argument("--confirm-install-sha256", default="")
    parser.add_argument("--json-out", default="")
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def _emit_result(result: dict[str, Any], raw_output_path: str) -> None:
    encoded = json.dumps(result, indent=2, sort_keys=True)
    output_path = str(raw_output_path or "").strip()
    if output_path:
        target = Path(output_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
        try:
            temporary.write_text(encoded + "\n", encoding="utf-8")
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
    print(encoded)


def _run_remote_helper(
    brain: Any, *, tg_id: int, install_id: str, profile: str
) -> dict[str, Any]:
    encoded = base64.b64encode(_REMOTE_HELPER.encode("utf-8")).decode("ascii")
    command = "python3 -c " + shlex.quote(
        "import base64;exec(base64.b64decode(" + repr(encoded) + "))"
    )
    stdin, stdout, stderr = brain.exec_command(command, timeout=240)
    stdin.write(
        json.dumps(
            {"tg_id": tg_id, "install_id": install_id, "profile": profile},
            separators=(",", ":"),
        )
    )
    stdin.channel.shutdown_write()
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", "replace").strip()
    err = stderr.read().decode("utf-8", "replace").strip()
    if code != 0:
        raise RuntimeError((err or "guarded AWG lab selection failed")[:800])
    return json.loads(out)


def main() -> int:
    args = _parse_args()
    adb = Path(args.adb).resolve()
    known_hosts = Path(args.known_hosts).resolve()
    passwords = Path(args.passwords).resolve()
    for path, label in (
        (adb, "adb"),
        (known_hosts, "known_hosts"),
        (passwords, "passwords"),
    ):
        if not path.is_file():
            raise SystemExit(f"{label} is missing")
    install_id, _account_id = _load_emulator_identity(adb, str(args.adb_serial))
    install_hash = hashlib.sha256(install_id.encode()).hexdigest()
    if args.confirm_install_sha256.strip().lower() != install_hash:
        raise SystemExit("install identity confirmation failed")
    report: dict[str, Any] = {
        "schema_version": "pokrov-owned-awg-lab-selection-v1",
        "mode": "APPLY" if args.apply else "PLAN",
        "profile": args.profile,
        "adb_target_supplied": bool(str(args.adb_serial).strip()),
        "install_id_sha256": install_hash,
        "raw_identifiers_returned": False,
    }
    if not args.apply:
        _emit_result(report, args.json_out)
        return 0
    os.environ["POKROV_SSH_KNOWN_HOSTS"] = str(known_hosts)
    brain, _auth = connect_node(
        code="brain", host=str(args.brain_ip), passwords_path=passwords
    )
    try:
        tg_id = _resolve_target_user(brain, install_id)
        result = _run_remote_helper(
            brain,
            tg_id=tg_id,
            install_id=install_id,
            profile=args.profile,
        )
        report["selected_profile"] = result.get("selected_profile")
        report["cohort_identity_present"] = bool(
            result.get("cohort_identity_present")
        )
        report["lab_allowlist_identity_present"] = bool(
            result.get("lab_allowlist_identity_present")
        )
        if args.profile == "default":
            report["readback_match"] = not report["cohort_identity_present"] and not report[
                "lab_allowlist_identity_present"
            ]
        else:
            selected = _psql(
                brain,
                "select coalesce(value_json::jsonb#>>'{cohort_overrides,candidate4-awg-lab,transport_profile}','') "
                "from app_settings where key='network_rollout_config';",
            )
            report["readback_match"] = (
                selected == args.profile and report["cohort_identity_present"]
            )
        report["ok"] = (
            report["selected_profile"] == args.profile and report["readback_match"]
        )
        _emit_result(report, args.json_out)
        return 0 if report["ok"] else 1
    finally:
        brain.close()


if __name__ == "__main__":
    raise SystemExit(main())
