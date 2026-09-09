from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import shlex
from pathlib import Path
from typing import Any

from node_access import DEFAULT_PASSWORDS, connect_node
from remote_activate_owned_awg_labs import _load_emulator_identity


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
exact_install_id = str(payload.get("exact_install_id") or "").strip()
extend_target_entitlement_days = int(
    payload.get("extend_target_entitlement_days") or 0
)
confirm_target_install_sha256 = str(
    payload.get("confirm_target_install_sha256") or ""
).strip().lower()
target_confirmation_invalid = bool(confirm_target_install_sha256) and (
    len(confirm_target_install_sha256) != 64
    or any(value not in "0123456789abcdef" for value in confirm_target_install_sha256)
)
if (
    (not label_fragment and not confirm_target_install_sha256)
    or candidate_rank < 1
    or candidate_rank > 4
    or selected_profile not in {"default", "awg2_lab", "awg31_lab"}
    or carrier_context not in {"none", "beeline"}
    or extend_target_entitlement_days not in {0, 1}
    or (
        extend_target_entitlement_days
        and (not exact_install_id or selected_profile == "default")
    )
    or target_confirmation_invalid
    or (apply_changes and not confirm_target_install_sha256)
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
from awg2_lab_service import _decrypt_endpoint as decrypt_awg2, _ready_material as ready_awg2
from awg31_lab_service import _decrypt_endpoint as decrypt_awg31, _ready_material as ready_awg31
from awg_lab_key_binding import AwgDeviceKeyError, require_awg_device_key_binding
from account_foundation_service import _load_account_component_users
from db import SessionLocal
from models import AccountDevice, Awg2LabMaterial, Awg31LabMaterial, Event, User
from network_rollout import load_network_rollout_config, resolved_client_policy

def load_target_materials(session, tg_id, install_id):
    policy = load_network_rollout_config(session=session)
    rows = (
        ready_awg2(session, tg_id=tg_id, install_id=install_id, rollout_value=policy.get("awg2_lab")),
        ready_awg31(session, tg_id=tg_id, install_id=install_id, rollout_value=policy.get("awg31_lab")),
    )
    for row, model, decrypt in zip(rows, (Awg2LabMaterial, Awg31LabMaterial), (decrypt_awg2, decrypt_awg31)):
        if row is not None:
            require_awg_device_key_binding(
                session, model=model, decrypt_endpoint=decrypt,
                endpoint=decrypt(row.endpoint_ciphertext), tg_id=tg_id,
                install_id=install_id, for_update=False,
            )
    return rows

def blocked(reason, **safe_fields):
    print(
        json.dumps(
            {
                "ok": False,
                "blocker": str(reason),
                **safe_fields,
                "raw_identifiers_returned": False,
            },
            sort_keys=True,
        )
    )
    raise SystemExit(0)

now = datetime.now(timezone.utc).replace(tzinfo=None)
with SessionLocal() as session:
    runtime_owner_users = (
        session.query(User)
        .filter(User.tg_id == int(admin_id))
        .order_by(User.tg_id.asc())
        .all()
    )
    runtime_owner_entitled_users = [
        row
        for row in runtime_owner_users
        if bool(row.is_active) and row.expiry_at is not None and row.expiry_at > now
    ]
    if exact_install_id:
        candidates = (
            session.query(AccountDevice)
            .filter(AccountDevice.install_id == exact_install_id)
            .filter(AccountDevice.state == "active")
            .filter(AccountDevice.revoked_at.is_(None))
            .order_by(AccountDevice.last_seen_at.desc(), AccountDevice.id.desc())
            .limit(2)
            .all()
        )
        if len(candidates) > 1:
            blocked(
                "exact_install_device_resolution_ambiguous",
                matched_device_count=len(candidates),
                target_selection_mode="exact_local_install",
            )
        device = candidates[0] if candidates else None
        install_id = exact_install_id
        target_selection_mode = "exact_local_install"
    elif label_fragment:
        candidates = (
            session.query(AccountDevice)
            .filter(AccountDevice.label.ilike(f"%{label_fragment}%"))
            .filter(AccountDevice.state == "active")
            .filter(AccountDevice.revoked_at.is_(None))
            .order_by(AccountDevice.last_seen_at.desc(), AccountDevice.id.desc())
            .limit(4)
            .all()
        )
        if len(candidates) < candidate_rank:
            blocked(
                "device_candidate_unavailable",
                candidate_rank=candidate_rank,
                matched_device_count=len(candidates),
                target_selection_mode="device_label_rank",
            )
        device = candidates[candidate_rank - 1]
        install_id = str(device.install_id or "").strip()
        target_selection_mode = "device_label_rank"
    else:
        active_devices = (
            session.query(AccountDevice)
            .filter(AccountDevice.install_id.isnot(None))
            .filter(AccountDevice.state == "active")
            .filter(AccountDevice.revoked_at.is_(None))
            .order_by(AccountDevice.last_seen_at.desc(), AccountDevice.id.desc())
            .limit(1000)
            .all()
        )
        candidates = [
            row
            for row in active_devices
            if str(row.install_id or "").strip()
            and hmac.compare_digest(
                hashlib.sha256(str(row.install_id).strip().encode()).hexdigest(),
                confirm_target_install_sha256,
            )
        ]
        if len(candidates) != 1:
            blocked(
                "confirmed_install_hash_resolution",
                matched_device_count=len(candidates),
                target_selection_mode="confirmed_install_hash",
            )
        device = candidates[0]
        install_id = str(device.install_id or "").strip()
        target_selection_mode = "confirmed_install_hash"
    target_install_sha256 = (
        hashlib.sha256(install_id.encode()).hexdigest() if install_id else ""
    )
    if confirm_target_install_sha256 and not hmac.compare_digest(
        confirm_target_install_sha256,
        target_install_sha256,
    ):
        blocked(
            "target_install_confirmation_failed",
            candidate_rank=candidate_rank,
            matched_device_count=len(candidates),
            target_selection_mode=target_selection_mode,
            target_install_sha256=target_install_sha256 or None,
            target_install_confirmation_match=False,
        )
    global_install_users = (
        session.query(User)
        .filter(User.app_install_id == install_id)
        .filter(User.tg_id > 0)
        .order_by(User.tg_id.asc())
        .all()
        if install_id
        else []
    )
    target_users = (
        session.query(User)
        .filter(User.account_id == device.account_id)
        .filter(User.tg_id > 0)
        .order_by(User.tg_id.asc())
        .all()
        if device is not None
        else list(global_install_users)
    )
    device_account_matches_global_install_user = bool(
        device is not None
        and len(global_install_users) == 1
        and str(global_install_users[0].account_id or "")
        == str(device.account_id or "")
    )
    if len(global_install_users) > 1:
        blocked(
            "global_install_user_resolution_ambiguous",
            candidate_rank=candidate_rank,
            matched_device_count=len(candidates),
            target_install_sha256=hashlib.sha256(install_id.encode()).hexdigest(),
            account_user_count=len(target_users),
            global_install_user_count=len(global_install_users),
        )
    if global_install_users:
        target_user = global_install_users[0]
        target_user_resolution = "exact_install_global"
    elif len(target_users) == 1:
        target_user = target_users[0]
        target_user_resolution = "account_single_user"
    elif target_users:
        target_user = None
        target_user_resolution = "account_component_entitled"
    else:
        blocked(
            "account_user_resolution_unavailable",
            candidate_rank=candidate_rank,
            matched_device_count=len(candidates),
            target_install_sha256=(
                hashlib.sha256(install_id.encode()).hexdigest()
                if install_id
                else None
            ),
            account_user_count=len(target_users),
            global_install_user_count=len(global_install_users),
        )
    account_component_users = _load_account_component_users(
        session,
        [int(row.tg_id) for row in (target_users or global_install_users)],
    )
    entitled = [
        row
        for row in account_component_users
        if bool(row.is_active) and row.expiry_at is not None and row.expiry_at > now
    ]
    if len(entitled) > 1:
        blocked(
            "entitled_user_resolution_ambiguous",
            candidate_rank=candidate_rank,
            matched_device_count=len(candidates),
            target_install_sha256=(
                hashlib.sha256(install_id.encode()).hexdigest()
                if install_id
                else None
            ),
            account_user_count=len(target_users),
            account_component_user_count=len(account_component_users),
            entitled_user_count=len(entitled),
            runtime_owner_user_count=len(runtime_owner_users),
            runtime_owner_entitled_user_count=len(runtime_owner_entitled_users),
            global_install_user_count=len(global_install_users),
            device_account_matches_global_install_user=device_account_matches_global_install_user,
            device_app_version=(
                str(device.app_version or "").strip() or None
                if device is not None
                else None
            ),
        )
    if len(entitled) == 1:
        entitled_user = entitled[0]
        entitlement_resolution = "device_account_component"
        if target_user is None:
            target_user = entitled_user
    elif (
        extend_target_entitlement_days == 1
        and target_selection_mode == "exact_local_install"
        and device is not None
        and len(global_install_users) == 1
        and target_user is global_install_users[0]
        and device_account_matches_global_install_user
    ):
        entitled_user = target_user
        entitlement_resolution = "exact_install_one_day_extension"
    elif (
        (target_selection_mode == "exact_local_install" or len(candidates) == 1)
        and len(global_install_users) == 1
        and len(runtime_owner_users) == 1
        and len(runtime_owner_entitled_users) == 1
    ):
        entitled_user = runtime_owner_entitled_users[0]
        entitlement_resolution = "runtime_admin_owner_fallback"
    else:
        blocked(
            "entitled_user_resolution",
            candidate_rank=candidate_rank,
            matched_device_count=len(candidates),
            target_install_sha256=(
                hashlib.sha256(install_id.encode()).hexdigest()
                if install_id
                else None
            ),
            account_user_count=len(target_users),
            account_component_user_count=len(account_component_users),
            entitled_user_count=len(entitled),
            runtime_owner_user_count=len(runtime_owner_users),
            runtime_owner_entitled_user_count=len(runtime_owner_entitled_users),
            global_install_user_count=len(global_install_users),
            device_account_matches_global_install_user=device_account_matches_global_install_user,
            device_app_version=(
                str(device.app_version or "").strip() or None
                if device is not None
                else None
            ),
        )
    entitled_user_owns_install = bool(
        install_id == str(entitled_user.app_install_id or "").strip()
        or (
            device is not None
            and str(device.account_id or "")
            and str(device.account_id or "") == str(entitled_user.account_id or "")
        )
    )
    if not entitled_user_owns_install:
        target_user_is_currently_entitled = bool(
            target_user is not None
            and bool(target_user.is_active)
            and target_user.expiry_at is not None
            and target_user.expiry_at > now
        )
        target_user_matches_runtime_owner = bool(
            target_user is not None and int(target_user.tg_id) == int(admin_id)
        )
        device_account_matches_runtime_owner = bool(
            device is not None
            and len(runtime_owner_users) == 1
            and str(device.account_id or "")
            and str(device.account_id or "")
            == str(runtime_owner_users[0].account_id or "")
        )
        blocked(
            "entitled_user_install_ownership",
            candidate_rank=candidate_rank,
            matched_device_count=len(candidates),
            target_install_sha256=(
                hashlib.sha256(install_id.encode()).hexdigest()
                if install_id
                else None
            ),
            account_user_count=len(target_users),
            account_component_user_count=len(account_component_users),
            global_install_user_count=len(global_install_users),
            entitlement_resolution=entitlement_resolution,
            device_record_present=device is not None,
            device_account_matches_global_install_user=(
                device_account_matches_global_install_user
            ),
            device_account_matches_runtime_owner=device_account_matches_runtime_owner,
            target_user_resolution=target_user_resolution,
            target_user_is_currently_entitled=target_user_is_currently_entitled,
            target_user_matches_runtime_owner=target_user_matches_runtime_owner,
            runtime_owner_user_count=len(runtime_owner_users),
            runtime_owner_entitled_user_count=len(runtime_owner_entitled_users),
            device_app_version=(
                str(device.app_version or "").strip() or None
                if device is not None
                else None
            ),
            last_seen_age_seconds=(
                None
                if device is None or device.last_seen_at is None
                else max(0, int((now - device.last_seen_at).total_seconds()))
            ),
        )
    entitlement_extension_needed = bool(
        entitlement_resolution == "exact_install_one_day_extension"
    )
    target_user_currently_entitled = bool(
        target_user is not None
        and bool(target_user.is_active)
        and target_user.expiry_at is not None
        and target_user.expiry_at > now
    )
    tg_id = int(entitled_user.tg_id)
    if not install_id or tg_id <= 0:
        blocked(
            "device_target_identity_incomplete",
            candidate_rank=candidate_rank,
            matched_device_count=len(candidates),
            install_identity_present=bool(install_id),
            positive_user_identity_present=tg_id > 0,
        )

    awg2_row = awg31_row = None
    if selected_profile != "default":
        try:
            awg2_row, awg31_row = load_target_materials(session, tg_id, install_id)
        except AwgDeviceKeyError as error:
            blocked(error.code)
    source_material_available = awg2_row is not None and awg31_row is not None
    if selected_profile != "default" and not source_material_available:
        blocked(
            "owned_awg_device_material_not_ready",
            candidate_rank=candidate_rank,
            matched_device_count=len(candidates),
            target_install_sha256=hashlib.sha256(install_id.encode()).hexdigest(),
            target_tg_id_sha256=hashlib.sha256(str(tg_id).encode()).hexdigest(),
            awg2_source_material_available=awg2_row is not None,
            awg31_source_material_available=awg31_row is not None,
        )

    recent_events = (
        session.query(Event)
        .filter(Event.device_id == device.id)
        .filter(Event.created_at >= now - timedelta(minutes=10))
        .order_by(Event.created_at.desc(), Event.id.desc())
        .limit(12)
        .all()
        if device is not None
        else []
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
        "target_selection_mode": target_selection_mode,
        "device_record_present": device is not None,
        "target_install_sha256": hashlib.sha256(install_id.encode()).hexdigest(),
        "target_install_confirmation_match": (
            hmac.compare_digest(confirm_target_install_sha256, target_install_sha256)
            if confirm_target_install_sha256
            else None
        ),
        "target_tg_id_sha256": hashlib.sha256(str(tg_id).encode()).hexdigest(),
        "account_user_count": len(target_users),
        "account_component_user_count": len(account_component_users),
        "exact_legacy_install_user_count": len(global_install_users),
        "target_user_resolution": target_user_resolution,
        "entitlement_resolution": entitlement_resolution,
        "target_user_is_entitled": target_user_currently_entitled,
        "entitlement_subject_matches_target_user": target_user is entitled_user,
        "entitlement_extension_requested_days": extend_target_entitlement_days,
        "entitlement_extension_needed": entitlement_extension_needed,
        "entitlement_extension_applied": False,
        "target_user_platform": str(target_user.app_platform or "").strip().lower() or None,
        "device_app_version": (
            str(device.app_version or "").strip() or None
            if device is not None
            else None
        ),
        "device_os_version_sha256": (
            hashlib.sha256(str(device.os_version).strip().encode()).hexdigest()
            if device is not None and str(device.os_version or "").strip()
            else None
        ),
        "device_locale_sha256": (
            hashlib.sha256(str(device.locale).strip().encode()).hexdigest()
            if device is not None and str(device.locale or "").strip()
            else None
        ),
        "device_time_zone_sha256": (
            hashlib.sha256(str(device.time_zone).strip().encode()).hexdigest()
            if device is not None and str(device.time_zone or "").strip()
            else None
        ),
        "last_seen_age_seconds": (
            None
            if device is None or device.last_seen_at is None
            else max(0, int((now - device.last_seen_at).total_seconds()))
        ),
        "recent_safe_events": safe_recent_events,
        "source_material_available": source_material_available,
        "raw_identifiers_returned": False,
    }
    if not apply_changes:
        print(json.dumps(safe_target, sort_keys=True))
        raise SystemExit(0)

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

def require_isolated_lab_scope(config, target_install):
    # This helper replaces a single legacy lab cohort and both lab gates. It is
    # not a shared-rollout editor: account selectors can match other installs.
    labs = {"awg2_lab", "awg31_lab"}
    for rule in [config.get("defaults") or {}, *(config.get("carrier_overrides") or {}).values()]:
        if rule.get("transport_profile") in labs:
            raise ValueError("shared AWG scope requires separate review")
    for name, rule in (config.get("cohort_overrides") or {}).items():
        if name != "candidate4-awg-lab" and rule.get("transport_profile") not in labs:
            continue
        if (name != "candidate4-awg-lab"
                or any(value != target_install for value in rule.get("install_ids") or [])
                or any(rule.get(field) for field in ("tg_ids", "linked_tg_ids", "platforms"))):
            raise ValueError("shared AWG scope requires separate review")
    for name in labs:
        lab = config.get(name) or {}
        if (any(value != target_install for value in lab.get("allowlist_install_ids") or [])
                or lab.get("allowlist_tg_ids")):
            raise ValueError("shared AWG scope requires separate review")


current = request("GET", "/api/admin/network-rollout-config")["network_rollout_config"]
try:
    require_isolated_lab_scope(current, install_id)
except ValueError:
    blocked("shared_awg_scope_requires_separate_review")

entitlement_extension_applied = False
if entitlement_extension_needed:
    guarded(
        "user.extend",
        "user",
        tg_id,
        "POST",
        f"/api/admin/users/{tg_id}/manual/extend",
        {"days": 1, "delta_days": 1, "allow_deactivate": False},
    )
    entitlement_extension_applied = True

latest = request("GET", "/api/admin/network-rollout-config")["network_rollout_config"]
if latest != current:
    blocked("network_rollout_changed_during_bind")
expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat().replace(
    "+00:00", "Z"
)
cohorts = dict(current.get("cohort_overrides") or {})
if selected_profile == "default":
    cleanup_tg_ids = {tg_id, int(target_user.tg_id)}
    cohort = dict(cohorts.get("candidate4-awg-lab") or {})
    cohort["install_ids"] = [
        value for value in list(cohort.get("install_ids") or []) if value != install_id
    ]
    cohort["tg_ids"] = [
        value
        for value in list(cohort.get("tg_ids") or [])
        if int(value) not in cleanup_tg_ids
    ]
    cohort["linked_tg_ids"] = [
        value
        for value in list(cohort.get("linked_tg_ids") or [])
        if int(value) not in cleanup_tg_ids
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
        "tg_ids": [],
        "linked_tg_ids": [],
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
            if int(value) not in cleanup_tg_ids
        ]
    else:
        lab.update(
            {
                "enabled": True,
                "kill_switch_engaged": False,
                "allowlist_install_ids": [install_id],
                "allowlist_tg_ids": [],
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
    live_user_entitled = bool(
        live_user is not None
        and bool(live_user.is_active)
        and live_user.expiry_at is not None
        and live_user.expiry_at > now
    )
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
        and list(selected.get("install_ids") or []) == [install_id]
        and not any(selected.get(field) for field in ("tg_ids", "linked_tg_ids", "platforms"))
        and list(selected_lab.get("allowlist_install_ids") or []) == [install_id]
        and not selected_lab.get("allowlist_tg_ids")
        and live_user_entitled
        and resolved_profile == selected_profile
    )
print(
    json.dumps(
        {
            **safe_target,
            "ok": ok,
            "awg2_material_provisioned": False,
            "awg31_material_provisioned": False,
            "existing_device_material_reused": selected_profile != "default",
            "selected_profile": selected_profile,
            "resolved_profile": resolved_profile,
            "carrier_context": carrier_context,
            "cohort_identity_present": cohort_identity_present,
            "lab_allowlist_identity_present": lab_allowlist_identity_present,
            "entitlement_extension_applied": entitlement_extension_applied,
            "target_user_is_entitled": live_user_entitled,
            "target_user_entitled_after_apply": live_user_entitled,
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
    parser.add_argument("--device-label-fragment", default="")
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
    parser.add_argument("--confirm-target-install-sha256", default="")
    parser.add_argument(
        "--extend-target-entitlement-days",
        type=int,
        choices=(0, 1),
        default=0,
        help=(
            "Optionally grant one test day only to the exact root-verified local "
            "install before selecting an AWG lab profile."
        ),
    )
    parser.add_argument(
        "--adb",
        default="",
        help=(
            "Optional root-capable ADB used to select the exact local install; "
            "the raw install ID is sent only through SSH stdin."
        ),
    )
    parser.add_argument("--adb-serial", default="emulator-5554")
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
    label_sha256 = hashlib.sha256(label.encode("utf-8")).hexdigest() if label else ""
    target_confirmation = str(args.confirm_target_install_sha256).strip().lower()
    target_confirmation_invalid = bool(target_confirmation) and (
        len(target_confirmation) != 64
        or any(value not in "0123456789abcdef" for value in target_confirmation)
    )
    if target_confirmation_invalid or (args.apply and not target_confirmation):
        raise SystemExit("target install confirmation is required for apply")
    if not 1 <= int(args.candidate_rank) <= 4 or (not label and not target_confirmation):
        raise SystemExit("device selector invalid")
    if label and str(args.confirm_device_label_sha256).strip().lower() != label_sha256:
        raise SystemExit("device label confirmation failed")
    extension_days = int(args.extend_target_entitlement_days)
    if extension_days and str(args.profile) == "default":
        raise SystemExit("entitlement extension requires an AWG lab profile")
    exact_install_id = ""
    adb_path = str(args.adb or "").strip()
    if adb_path:
        adb = Path(adb_path).resolve()
        if not adb.is_file():
            raise SystemExit("adb is missing")
        exact_install_id, _account_id = _load_emulator_identity(
            adb,
            str(args.adb_serial),
        )
        local_install_sha256 = hashlib.sha256(exact_install_id.encode()).hexdigest()
        if not hmac.compare_digest(target_confirmation, local_install_sha256):
            raise SystemExit("local install identity confirmation failed")
    if extension_days and not exact_install_id:
        raise SystemExit("entitlement extension requires exact root-verified local install")
    known_hosts = Path(args.known_hosts).resolve()
    passwords = Path(args.passwords).resolve()
    if not known_hosts.is_file() or not passwords.is_file():
        raise SystemExit("SSH trust or authentication input is missing")
    report: dict[str, Any] = {
        "schema_version": "pokrov-owned-awg-device-bind-v1",
        "mode": "APPLY" if args.apply else "PLAN",
        "profile": str(args.profile),
        "carrier_context": str(args.carrier_context),
        "device_label_sha256": label_sha256 or None,
        "candidate_rank": int(args.candidate_rank),
        "target_selection_mode": (
            "exact_local_install" if exact_install_id else "device_label_rank"
        ),
        "local_install_confirmation_match": True if exact_install_id else None,
        "raw_identifiers_returned": False,
        "entitlement_extension_requested_days": extension_days,
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
                    "exact_install_id": exact_install_id,
                    "confirm_target_install_sha256": target_confirmation,
                    "extend_target_entitlement_days": extension_days,
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
        if result.get("raw_identifiers_returned") is not False:
            raise SystemExit("owned AWG device bind readback failed")
        report.update(result)
        _emit_result(report, args.json_out)
        return 0 if report.get("ok") is True else 1
    finally:
        brain.close()


if __name__ == "__main__":
    raise SystemExit(main())
