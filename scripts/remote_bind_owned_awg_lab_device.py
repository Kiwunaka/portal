from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
from pathlib import Path
from typing import Any

from node_access import DEFAULT_PASSWORDS, connect_node


_REMOTE_HELPER = r'''
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone

payload = json.loads(sys.stdin.read())
label_fragment = str(payload["device_label_fragment"]).strip()
candidate_rank = int(payload["candidate_rank"])
selected_profile = str(payload["profile"]).strip()
carrier_context = str(payload.get("carrier_context") or "none").strip().lower()
apply_changes = bool(payload.get("apply"))
if (
    not label_fragment
    or candidate_rank < 1
    or candidate_rank > 4
    or selected_profile not in {"default", "awg2_lab", "awg31_lab"}
    or carrier_context not in {"none", "beeline"}
):
    raise SystemExit("device selector invalid")

pid = subprocess.check_output(
    ["systemctl", "show", "portal-api", "-p", "MainPID", "--value"],
    text=True,
).strip()
with open(f"/proc/{pid}/environ", "rb") as handle:
    env = {}
    for item in handle.read().split(b"\0"):
        if b"=" in item:
            key, value = item.split(b"=", 1)
            env[key.decode("utf-8", "replace")] = value.decode("utf-8", "replace")
os.environ.update(env)

bot_token = env.get("BOT_TOKEN", "").strip()
admin_id = env.get("ADMIN_ID", "").strip()
if not bot_token or not admin_id.isdigit():
    raise SystemExit("portal admin runtime identity unavailable")

os.chdir("/root/portal_bot")
sys.path.insert(0, "/root/portal_bot")
from awg2_lab_service import _decrypt_endpoint as decrypt_awg2
from awg31_lab_service import _decrypt_endpoint as decrypt_awg31
from db import SessionLocal
from models import AccountDevice, Awg2LabMaterial, Awg31LabMaterial, Event, User
from network_rollout import resolved_client_policy

now = datetime.now(timezone.utc).replace(tzinfo=None)
with SessionLocal() as session:
    candidates = (
        session.query(AccountDevice)
        .filter(AccountDevice.label.ilike(f"%{label_fragment}%"))
        .filter(AccountDevice.state == "active")
        .order_by(AccountDevice.last_seen_at.desc(), AccountDevice.id.desc())
        .limit(4)
        .all()
    )
    if len(candidates) < candidate_rank:
        raise SystemExit("device candidate unavailable")
    device = candidates[candidate_rank - 1]
    target_users = (
        session.query(User)
        .filter(User.account_id == device.account_id)
        .filter(User.tg_id > 0)
        .order_by(User.tg_id.asc())
        .all()
    )
    entitled = [
        row
        for row in target_users
        if bool(row.is_active) and row.expiry_at is not None and row.expiry_at > now
    ]
    if len(entitled) != 1:
        raise SystemExit("device account does not resolve to one entitled user")
    install_id = str(device.install_id or "").strip()
    exact_install_users = [
        row
        for row in target_users
        if str(row.app_install_id or "").strip() == install_id
    ]
    if len(exact_install_users) > 1 or not target_users:
        raise SystemExit("device account user resolution is ambiguous")
    target_user = exact_install_users[0] if exact_install_users else target_users[0]
    entitled_user = entitled[0]
    tg_id = int(target_user.tg_id)
    if not install_id or tg_id <= 0:
        raise SystemExit("device target identity incomplete")

    awg2_row = (
        session.query(Awg2LabMaterial)
        .filter(Awg2LabMaterial.is_active.is_(True))
        .filter(Awg2LabMaterial.state == "ready")
        .order_by(Awg2LabMaterial.provisioned_at.desc(), Awg2LabMaterial.id.desc())
        .first()
    )
    awg31_row = (
        session.query(Awg31LabMaterial)
        .filter(Awg31LabMaterial.is_active.is_(True))
        .filter(Awg31LabMaterial.state == "ready")
        .order_by(Awg31LabMaterial.provisioned_at.desc(), Awg31LabMaterial.id.desc())
        .first()
    )
    source_material_available = awg2_row is not None and awg31_row is not None
    if selected_profile != "default" and not source_material_available:
        raise SystemExit("owned AWG source material unavailable")

    recent_events = (
        session.query(Event)
        .filter(Event.device_id == device.id)
        .filter(Event.created_at >= now - timedelta(minutes=10))
        .order_by(Event.created_at.desc(), Event.id.desc())
        .limit(12)
        .all()
    )
    safe_recent_events = [
        {
            "event_name": str(row.event_name or "").strip()[:64] or None,
            "app_version": str(row.app_version or "").strip()[:32] or None,
            "stage": str(row.stage or "").strip()[:64] or None,
            "result": str(row.result or "").strip()[:24] or None,
            "error_code": str(row.error_code or "").strip()[:64] or None,
            "age_seconds": max(0, int((now - row.created_at).total_seconds())),
        }
        for row in recent_events
    ]

    safe_target = {
        "ok": True,
        "candidate_rank": candidate_rank,
        "matched_device_count": len(candidates),
        "target_install_sha256": hashlib.sha256(install_id.encode()).hexdigest(),
        "target_tg_id_sha256": hashlib.sha256(str(tg_id).encode()).hexdigest(),
        "account_user_count": len(target_users),
        "exact_legacy_install_user_count": len(exact_install_users),
        "target_user_resolution": "exact_install" if exact_install_users else "account_first_tg",
        "target_user_is_entitled": target_user is entitled_user,
        "target_user_platform": str(target_user.app_platform or "").strip().lower() or None,
        "device_app_version": str(device.app_version or "").strip() or None,
        "device_os_version_sha256": (
            hashlib.sha256(str(device.os_version).strip().encode()).hexdigest()
            if str(device.os_version or "").strip()
            else None
        ),
        "device_locale_sha256": (
            hashlib.sha256(str(device.locale).strip().encode()).hexdigest()
            if str(device.locale or "").strip()
            else None
        ),
        "device_time_zone_sha256": (
            hashlib.sha256(str(device.time_zone).strip().encode()).hexdigest()
            if str(device.time_zone or "").strip()
            else None
        ),
        "last_seen_age_seconds": (
            None
            if device.last_seen_at is None
            else max(0, int((now - device.last_seen_at).total_seconds()))
        ),
        "recent_safe_events": safe_recent_events,
        "source_material_available": source_material_available,
        "raw_identifiers_returned": False,
    }
    if not apply_changes:
        print(json.dumps(safe_target, sort_keys=True))
        raise SystemExit(0)

    if selected_profile != "default":
        awg2_endpoint = decrypt_awg2(awg2_row.endpoint_ciphertext)
        awg31_endpoint = decrypt_awg31(awg31_row.endpoint_ciphertext)

params = {
    "auth_date": str(int(time.time())),
    "query_id": "POKROVAWGDEVICEBIND",
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
        "User-Agent": "pokrov-awg-device-binder/1",
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
        marker = "unknown"
        try:
            error_payload = json.loads(exc.read().decode("utf-8", "replace"))
            detail = error_payload.get("detail") if isinstance(error_payload, dict) else None
            if isinstance(detail, dict):
                marker = str(detail.get("code") or detail.get("error") or "object")
            elif isinstance(detail, list):
                parts = []
                for item in detail[:4]:
                    if not isinstance(item, dict):
                        continue
                    error_type = str(item.get("type") or "validation")
                    location = item.get("loc") if isinstance(item.get("loc"), list) else []
                    safe_location = ".".join(
                        "index" if isinstance(value, int) else str(value) for value in location
                    )
                    parts.append(f"{error_type}@{safe_location}")
                marker = ",".join(parts) or "validation"
        except Exception:
            marker = "unreadable"
        marker = re.sub(r"[^A-Za-z0-9_.@,-]", "_", marker)[:240]
        safe_path = re.sub(r"/users/[^/]+", "/users/{id}", path)
        raise RuntimeError(
            f"admin api {method} {safe_path} failed HTTP {exc.code} detail={marker}"
        ) from None

def guarded(action, target_type, target_id, method, path, body):
    prepared = request(
        "POST",
        "/api/admin/action-intents",
        {
            "action": action,
            "target": {"type": target_type, "id": str(target_id)},
            "payload": body,
        },
    )
    challenge = str(prepared.get("confirmation_challenge") or "")
    intent_id = str(prepared.get("intent_id") or "")
    if not challenge or not intent_id:
        raise RuntimeError(f"intent prepare failed for {action}")
    return request(
        method,
        path,
        body,
        {
            "X-Admin-Intent-Id": intent_id,
            "X-Admin-Idempotency-Key": str(uuid.uuid4()),
            "X-Admin-Confirmation-SHA256": hashlib.sha256(challenge.encode()).hexdigest(),
        },
    )

if selected_profile != "default":
    guarded(
        "awg2_lab_material.replace",
        "awg2_lab_material",
        tg_id,
        "PUT",
        "/api/admin/client/awg2-lab/material",
        {
            "tg_id": tg_id,
            "install_id": install_id,
            "generation": "awg2-lab-v1",
            "endpoint_revision": "awg2-v1",
            "server_record_id": "de-awg2-20260827-01",
            "node_code": "de",
            "endpoint": awg2_endpoint,
        },
    )
    guarded(
        "awg31_lab_material.replace",
        "awg31_lab_material",
        tg_id,
        "PUT",
        "/api/admin/client/awg31-lab/material",
        {
            "tg_id": tg_id,
            "install_id": install_id,
            "generation": "awg31-lab-v3-randomized-trailers",
            "endpoint_revision": "awg31-v1",
            "server_record_id": "de-awg31-20260828-03-randomized-trailers",
            "node_code": "de",
            "endpoint": awg31_endpoint,
        },
    )

current = request("GET", "/api/admin/network-rollout-config")["network_rollout_config"]
expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat().replace(
    "+00:00", "Z"
)
cohorts = dict(current.get("cohort_overrides") or {})
if selected_profile == "default":
    cohort = dict(cohorts.get("candidate4-awg-lab") or {})
    cohort["install_ids"] = [
        value for value in list(cohort.get("install_ids") or []) if value != install_id
    ]
    cohort["tg_ids"] = [
        value for value in list(cohort.get("tg_ids") or []) if int(value) != tg_id
    ]
    cohort["linked_tg_ids"] = [
        value
        for value in list(cohort.get("linked_tg_ids") or [])
        if int(value) not in {tg_id, int(entitled_user.tg_id)}
    ]
    if not any(
        list(cohort.get(field) or [])
        for field in ("install_ids", "tg_ids", "linked_tg_ids")
    ):
        cohorts.pop("candidate4-awg-lab", None)
    else:
        cohorts["candidate4-awg-lab"] = cohort
else:
    cohorts["candidate4-awg-lab"] = {
        "transport_profile": selected_profile,
        "install_ids": [install_id],
        "tg_ids": [tg_id],
        "linked_tg_ids": [] if target_user is entitled_user else [int(entitled_user.tg_id)],
        "platforms": [],
    }
current["cohort_overrides"] = cohorts
for name in ("awg2_lab", "awg31_lab"):
    lab = dict(current.get(name) or {})
    if selected_profile == "default":
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
    else:
        lab.update(
            {
                "enabled": True,
                "kill_switch_engaged": False,
                "allowlist_install_ids": [install_id],
                "allowlist_tg_ids": [tg_id],
                "allowlist_node_codes": ["de"],
                "allowed_platforms": ["android", "windows"],
                "expires_at": expires_at,
            }
        )
    current[name] = lab
guarded(
    "network_rollout_config.update",
    "config",
    "network-rollout",
    "PUT",
    "/api/admin/network-rollout-config",
    current,
)

readback = request("GET", "/api/admin/network-rollout-config")["network_rollout_config"]
selected = dict((readback.get("cohort_overrides") or {}).get("candidate4-awg-lab") or {})
selected_lab = dict(readback.get(selected_profile) or {})
cohort_identity_present = bool(
    install_id in list(selected.get("install_ids") or [])
    or tg_id in [int(value) for value in list(selected.get("tg_ids") or [])]
    or tg_id in [int(value) for value in list(selected.get("linked_tg_ids") or [])]
    or int(entitled_user.tg_id)
    in [int(value) for value in list(selected.get("linked_tg_ids") or [])]
)
lab_allowlist_identity_present = False
for name in ("awg2_lab", "awg31_lab"):
    lab = dict(readback.get(name) or {})
    lab_allowlist_identity_present = bool(
        lab_allowlist_identity_present
        or install_id in list(lab.get("allowlist_install_ids") or [])
        or tg_id in [int(value) for value in list(lab.get("allowlist_tg_ids") or [])]
    )
with SessionLocal() as read_session:
    live_user = read_session.query(User).filter(User.tg_id == tg_id).first()
    resolved_profile = (
        resolved_client_policy(
            session=read_session,
            user=live_user,
            install_id=install_id,
            carrier=None if carrier_context == "none" else carrier_context,
            rollout_config=readback,
        ).get("transport_profile")
        if live_user is not None
        else None
    )
if selected_profile == "default":
    ok = bool(
        not cohort_identity_present
        and not lab_allowlist_identity_present
        and resolved_profile not in {"awg2_lab", "awg31_lab"}
    )
else:
    ok = bool(
        selected.get("transport_profile") == selected_profile
        and install_id in list(selected.get("install_ids") or [])
        and install_id in list(selected_lab.get("allowlist_install_ids") or [])
        and tg_id in list(selected_lab.get("allowlist_tg_ids") or [])
        and resolved_profile == selected_profile
    )
print(
    json.dumps(
        {
            **safe_target,
            "ok": ok,
            "awg2_material_provisioned": selected_profile != "default",
            "awg31_material_provisioned": selected_profile != "default",
            "selected_profile": selected_profile,
            "resolved_profile": resolved_profile,
            "carrier_context": carrier_context,
            "cohort_identity_present": cohort_identity_present,
            "lab_allowlist_identity_present": lab_allowlist_identity_present,
            "raw_identifiers_returned": False,
        },
        sort_keys=True,
    )
)
'''


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bind one uniquely ranked owned Android device to the isolated AWG lab."
    )
    parser.add_argument("--brain-ip", default="82.21.114.104")
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--known-hosts", required=True)
    parser.add_argument("--device-label-fragment", required=True)
    parser.add_argument("--candidate-rank", type=int, default=1)
    parser.add_argument(
        "--profile",
        choices=("default", "awg2_lab", "awg31_lab"),
        default="awg31_lab",
    )
    parser.add_argument(
        "--carrier-context",
        choices=("none", "beeline"),
        default="none",
        help="Policy carrier context used for exact post-apply readback.",
    )
    parser.add_argument("--confirm-device-label-sha256", default="")
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


def main() -> int:
    args = _parse_args()
    label = str(args.device_label_fragment).strip()
    label_sha256 = hashlib.sha256(label.encode("utf-8")).hexdigest()
    if not label or not 1 <= int(args.candidate_rank) <= 4:
        raise SystemExit("device selector invalid")
    if str(args.confirm_device_label_sha256).strip().lower() != label_sha256:
        raise SystemExit("device label confirmation failed")
    known_hosts = Path(args.known_hosts).resolve()
    passwords = Path(args.passwords).resolve()
    if not known_hosts.is_file() or not passwords.is_file():
        raise SystemExit("SSH trust or authentication input is missing")
    report: dict[str, Any] = {
        "schema_version": "pokrov-owned-awg-device-bind-v1",
        "mode": "APPLY" if args.apply else "PLAN",
        "profile": str(args.profile),
        "carrier_context": str(args.carrier_context),
        "device_label_sha256": label_sha256,
        "candidate_rank": int(args.candidate_rank),
        "raw_identifiers_returned": False,
    }
    os.environ["POKROV_SSH_KNOWN_HOSTS"] = str(known_hosts)
    brain, _auth = connect_node(
        code="brain",
        host=str(args.brain_ip),
        passwords_path=passwords,
    )
    try:
        command = "/root/portal_bot/venv/bin/python -c " + shlex.quote(_REMOTE_HELPER)
        stdin, stdout, stderr = brain.exec_command(command, timeout=300)
        stdin.write(
            json.dumps(
                {
                    "device_label_fragment": label,
                    "candidate_rank": int(args.candidate_rank),
                    "profile": str(args.profile),
                    "carrier_context": str(args.carrier_context),
                    "apply": bool(args.apply),
                },
                separators=(",", ":"),
            )
        )
        stdin.channel.shutdown_write()
        code = stdout.channel.recv_exit_status()
        output = stdout.read().decode("utf-8", "replace").strip()
        error = stderr.read().decode("utf-8", "replace").strip()
        if code != 0:
            raise SystemExit((error or "owned AWG device bind failed")[:300])
        result = json.loads(output)
        if result.get("ok") is not True or result.get("raw_identifiers_returned") is not False:
            raise SystemExit("owned AWG device bind readback failed")
        report.update(result)
        _emit_result(report, args.json_out)
        return 0
    finally:
        brain.close()


if __name__ == "__main__":
    raise SystemExit(main())
