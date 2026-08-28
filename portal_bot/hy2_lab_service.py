"""Device-bound Hysteria2 owner-lab material and fail-closed rollout contract."""

from __future__ import annotations

import base64
import hashlib
import ipaddress
import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from cryptography.fernet import Fernet, InvalidToken

from models import Hy2LabMaterial
from transport_catalog import HY2_LAB


HY2_CONTRACT_ID = "pokrov.hy2.outbound.v1"
HY2_CONTRACT_SHA256 = (
    "c96b38e58ea33f838f23b80a65f3a9a264e932b7248f206798df9a0b8fa0fb98"
)
HY2_ENDPOINT_REVISION = "hy2-v1"
HY2_OUTBOUND_TAG = "pokrov-hy2-lab"
HY2_ALLOWED_PLATFORMS = frozenset({"android", "windows"})

_SAFE_TOKEN_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_DNS_NAME_RE = re.compile(
    r"^(?=.{1,253}\Z)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)*"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$"
)
_DEFAULT_MATERIAL_MAX_AGE_HOURS = 24 * 7
_MATERIAL_SECRET_ENV_KEY = "HY2_LAB_MATERIAL_SECRET"
_ENDPOINT_FIELDS = frozenset(
    {
        "server",
        "server_port",
        "password",
        "up_mbps",
        "down_mbps",
        "obfs",
        "tls",
    }
)
_TLS_FIELDS = frozenset({"enabled", "server_name", "insecure", "alpn"})
_OBFS_FIELDS = frozenset({"type", "password"})


class Hy2LabError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = str(code or "hy2_lab_invalid")
        super().__init__(self.code)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return _clean_text(value).lower() in {"1", "true", "yes", "y", "on"}


def _safe_token(value: Any, *, code: str) -> str:
    token = _clean_text(value).lower()
    if not _SAFE_TOKEN_RE.fullmatch(token):
        raise Hy2LabError(code)
    return token


def _safe_string_list(value: Any, *, lower: bool = False) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = _clean_text(item)
        if lower:
            text = text.lower()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text[:128])
    return result


def _safe_int_list(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    result: list[int] = []
    seen: set[int] = set()
    for item in value:
        try:
            number = int(item)
        except Exception:
            continue
        if number <= 0 or number in seen:
            continue
        seen.add(number)
        result.append(number)
    return result


def default_hy2_lab_config() -> dict[str, Any]:
    return {
        "enabled": False,
        "kill_switch_engaged": True,
        "allowlist_install_ids": [],
        "allowlist_tg_ids": [],
        "allowlist_node_codes": [],
        "allowed_platforms": sorted(HY2_ALLOWED_PLATFORMS),
        "expires_at": None,
        "contract_id": HY2_CONTRACT_ID,
        "contract_sha256": HY2_CONTRACT_SHA256,
        "generation": "hy2-lab-v1",
        "endpoint_revision": HY2_ENDPOINT_REVISION,
        "server_record_id": "",
        "server_owner": "pokrov",
        "server_state": "disabled",
        "material_max_age_hours": _DEFAULT_MATERIAL_MAX_AGE_HOURS,
    }


def normalize_hy2_lab_config(value: Any) -> dict[str, Any]:
    source = value if isinstance(value, Mapping) else {}
    defaults = default_hy2_lab_config()
    try:
        max_age = int(
            source.get("material_max_age_hours")
            or defaults["material_max_age_hours"]
        )
    except Exception:
        max_age = int(defaults["material_max_age_hours"])
    platforms = _safe_string_list(source.get("allowed_platforms"), lower=True)
    if not platforms:
        platforms = list(defaults["allowed_platforms"])
    return {
        "enabled": _as_bool(source.get("enabled")),
        "kill_switch_engaged": (
            _as_bool(source.get("kill_switch_engaged"))
            if "kill_switch_engaged" in source
            else True
        ),
        "allowlist_install_ids": _safe_string_list(source.get("allowlist_install_ids")),
        "allowlist_tg_ids": _safe_int_list(source.get("allowlist_tg_ids")),
        "allowlist_node_codes": _safe_string_list(
            source.get("allowlist_node_codes"), lower=True
        ),
        "allowed_platforms": [
            item for item in platforms if item in HY2_ALLOWED_PLATFORMS
        ],
        "expires_at": _clean_text(source.get("expires_at")) or None,
        "contract_id": _clean_text(source.get("contract_id")) or HY2_CONTRACT_ID,
        "contract_sha256": _clean_text(source.get("contract_sha256")).lower()
        or HY2_CONTRACT_SHA256,
        "generation": _clean_text(source.get("generation")).lower()
        or defaults["generation"],
        "endpoint_revision": _clean_text(source.get("endpoint_revision")).lower()
        or HY2_ENDPOINT_REVISION,
        "server_record_id": _clean_text(source.get("server_record_id")).lower(),
        "server_owner": _clean_text(source.get("server_owner")).lower() or "pokrov",
        "server_state": _clean_text(source.get("server_state")).lower()
        or "disabled",
        "material_max_age_hours": max(1, min(24 * 365, max_age)),
    }


def _not_expired(expires_at: Any, *, now: datetime) -> bool:
    raw = _clean_text(expires_at)
    if not raw:
        return True
    try:
        deadline = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if deadline.tzinfo is not None and deadline.utcoffset() is not None:
            deadline = deadline.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        return False
    return now <= deadline


def hy2_lab_rollout_access(
    value: Any,
    *,
    install_id: str,
    tg_ids: list[int],
    platform: str,
    now: datetime | None = None,
) -> bool:
    config = normalize_hy2_lab_config(value)
    current = now or _utcnow()
    if not config["enabled"] or config["kill_switch_engaged"]:
        return False
    if config["contract_id"] != HY2_CONTRACT_ID:
        return False
    if config["contract_sha256"] != HY2_CONTRACT_SHA256:
        return False
    if config["endpoint_revision"] != HY2_ENDPOINT_REVISION:
        return False
    if config["server_owner"] != "pokrov" or config["server_state"] != "ready":
        return False
    try:
        _safe_token(config["generation"], code="generation_invalid")
        _safe_token(config["server_record_id"], code="server_record_invalid")
    except Hy2LabError:
        return False
    if not _not_expired(config["expires_at"], now=current):
        return False
    if _clean_text(platform).lower() not in set(config["allowed_platforms"]):
        return False
    install = _clean_text(install_id)
    identities_match = bool(
        (install and install in set(config["allowlist_install_ids"]))
        or set(config["allowlist_tg_ids"]).intersection(
            {int(item) for item in tg_ids}
        )
    )
    return identities_match and bool(config["allowlist_node_codes"])


def _material_fernet() -> Fernet:
    secret = _clean_text(os.getenv(_MATERIAL_SECRET_ENV_KEY))
    if not secret:
        raise Hy2LabError("material_secret_unavailable")
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _encrypt_endpoint(value: Mapping[str, Any]) -> str:
    return (
        _material_fernet()
        .encrypt(_canonical_json(dict(value)).encode("utf-8"))
        .decode("ascii")
    )


def _decrypt_endpoint(value: Any) -> dict[str, Any]:
    try:
        decoded = _material_fernet().decrypt(_clean_text(value).encode("ascii"))
        loaded = json.loads(decoded.decode("utf-8"))
    except (
        InvalidToken,
        UnicodeDecodeError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ) as exc:
        raise Hy2LabError("material_decryption_failed") from exc
    if not isinstance(loaded, dict):
        raise Hy2LabError("material_payload_invalid")
    return loaded


def _bounded_int(value: Any, *, code: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        raise Hy2LabError(code)
    try:
        number = int(value)
    except Exception as exc:
        raise Hy2LabError(code) from exc
    if number < minimum or number > maximum:
        raise Hy2LabError(code)
    return number


def _bounded_secret(value: Any, *, code: str) -> str:
    text = _clean_text(value)
    length = len(text.encode("utf-8"))
    if length < 16 or length > 128 or any(ord(char) < 33 for char in text):
        raise Hy2LabError(code)
    return text


def _endpoint_host(value: Any) -> str:
    host = _clean_text(value)
    if not host or len(host) > 253 or "://" in host or any(char.isspace() for char in host):
        raise Hy2LabError("server_invalid")
    try:
        if ipaddress.ip_address(host).version != 4:
            raise Hy2LabError("server_invalid")
        return host
    except ValueError:
        if not _DNS_NAME_RE.fullmatch(host):
            raise Hy2LabError("server_invalid") from None
    return host.lower()


def _tls_server_name(value: Any) -> str:
    name = _clean_text(value).lower()
    if not _DNS_NAME_RE.fullmatch(name):
        raise Hy2LabError("tls_server_name_invalid")
    return name


def validate_hy2_endpoint(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise Hy2LabError("endpoint_invalid")
    endpoint = dict(value)
    if set(endpoint) != _ENDPOINT_FIELDS:
        raise Hy2LabError("endpoint_fields_invalid")

    tls_value = endpoint.get("tls")
    if not isinstance(tls_value, Mapping) or set(tls_value) != _TLS_FIELDS:
        raise Hy2LabError("tls_fields_invalid")
    tls = dict(tls_value)
    if tls.get("enabled") is not True or tls.get("insecure") is not False:
        raise Hy2LabError("tls_verification_required")
    if tls.get("alpn") != ["h3"]:
        raise Hy2LabError("tls_alpn_invalid")

    obfs_value = endpoint.get("obfs")
    normalized_obfs: dict[str, str] | None = None
    if obfs_value is not None:
        if not isinstance(obfs_value, Mapping) or set(obfs_value) != _OBFS_FIELDS:
            raise Hy2LabError("obfs_fields_invalid")
        obfs = dict(obfs_value)
        if _clean_text(obfs.get("type")).lower() != "salamander":
            raise Hy2LabError("obfs_type_invalid")
        normalized_obfs = {
            "type": "salamander",
            "password": _bounded_secret(
                obfs.get("password"), code="obfs_password_invalid"
            ),
        }

    return {
        "server": _endpoint_host(endpoint.get("server")),
        "server_port": _bounded_int(
            endpoint.get("server_port"),
            code="server_port_invalid",
            minimum=1,
            maximum=65535,
        ),
        "password": _bounded_secret(endpoint.get("password"), code="password_invalid"),
        "up_mbps": _bounded_int(
            endpoint.get("up_mbps"), code="bandwidth_invalid", minimum=1, maximum=1000
        ),
        "down_mbps": _bounded_int(
            endpoint.get("down_mbps"), code="bandwidth_invalid", minimum=1, maximum=1000
        ),
        "obfs": normalized_obfs,
        "tls": {
            "enabled": True,
            "server_name": _tls_server_name(tls.get("server_name")),
            "insecure": False,
            "alpn": ["h3"],
        },
    }


def replace_hy2_lab_material(
    session,
    *,
    tg_id: int,
    install_id: str,
    generation: str,
    endpoint_revision: str,
    server_record_id: str,
    node_code: str,
    endpoint: Mapping[str, Any],
    now: datetime | None = None,
) -> Hy2LabMaterial:
    install = _clean_text(install_id)
    if not install or len(install) > 128:
        raise Hy2LabError("install_id_invalid")
    generation_value = _safe_token(generation, code="generation_invalid")
    revision_value = _safe_token(endpoint_revision, code="endpoint_revision_invalid")
    if revision_value != HY2_ENDPOINT_REVISION:
        raise Hy2LabError("endpoint_revision_stale")
    server_record = _safe_token(server_record_id, code="server_record_invalid")
    node = _safe_token(node_code, code="node_code_invalid")
    normalized_endpoint = validate_hy2_endpoint(endpoint)
    canonical = _canonical_json(normalized_endpoint)
    material_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    current = now or _utcnow()

    session.query(Hy2LabMaterial).filter(
        Hy2LabMaterial.tg_id == int(tg_id),
        Hy2LabMaterial.install_id == install,
        Hy2LabMaterial.is_active.is_(True),
    ).update(
        {
            Hy2LabMaterial.is_active: False,
            Hy2LabMaterial.state: "rotated",
            Hy2LabMaterial.revoked_at: current,
            Hy2LabMaterial.updated_at: current,
        },
        synchronize_session=False,
    )
    row = Hy2LabMaterial(
        tg_id=int(tg_id),
        install_id=install,
        contract_id=HY2_CONTRACT_ID,
        contract_sha256=HY2_CONTRACT_SHA256,
        generation=generation_value,
        endpoint_revision=revision_value,
        server_record_id=server_record,
        node_code=node,
        endpoint_ciphertext=_encrypt_endpoint(normalized_endpoint),
        material_hash=material_hash,
        state="ready",
        is_active=True,
        provisioned_at=current,
        updated_at=current,
    )
    session.add(row)
    session.flush()
    return row


def _active_material(session, *, tg_id: int, install_id: str) -> Hy2LabMaterial | None:
    install = _clean_text(install_id)
    if not install:
        return None
    return (
        session.query(Hy2LabMaterial)
        .filter(
            Hy2LabMaterial.tg_id == int(tg_id),
            Hy2LabMaterial.install_id == install,
            Hy2LabMaterial.is_active.is_(True),
            Hy2LabMaterial.state == "ready",
        )
        .order_by(Hy2LabMaterial.provisioned_at.desc(), Hy2LabMaterial.id.desc())
        .first()
    )


def hy2_lab_material_ready(
    session,
    *,
    tg_id: int,
    install_id: str,
    rollout_value: Any,
    now: datetime | None = None,
) -> bool:
    config = normalize_hy2_lab_config(rollout_value)
    row = _active_material(session, tg_id=tg_id, install_id=install_id)
    if row is None:
        return False
    current = now or _utcnow()
    provisioned_at = row.provisioned_at
    if not isinstance(provisioned_at, datetime):
        return False
    if provisioned_at.tzinfo is not None and provisioned_at.utcoffset() is not None:
        provisioned_at = provisioned_at.astimezone(timezone.utc).replace(tzinfo=None)
    if provisioned_at < current - timedelta(
        hours=int(config["material_max_age_hours"])
    ):
        return False
    return bool(
        row.contract_id == config["contract_id"] == HY2_CONTRACT_ID
        and row.contract_sha256 == config["contract_sha256"] == HY2_CONTRACT_SHA256
        and row.generation == config["generation"]
        and row.endpoint_revision == config["endpoint_revision"] == HY2_ENDPOINT_REVISION
        and row.server_record_id == config["server_record_id"]
        and row.node_code in set(config["allowlist_node_codes"])
    )


def build_managed_hy2_lab_config(
    session,
    *,
    tg_id: int,
    install_id: str,
    rollout_value: Any,
    title: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    if not hy2_lab_material_ready(
        session,
        tg_id=tg_id,
        install_id=install_id,
        rollout_value=rollout_value,
        now=now,
    ):
        raise Hy2LabError("material_not_ready")
    config = normalize_hy2_lab_config(rollout_value)
    row = _active_material(session, tg_id=tg_id, install_id=install_id)
    if row is None:
        raise Hy2LabError("material_not_ready")
    endpoint = validate_hy2_endpoint(_decrypt_endpoint(row.endpoint_ciphertext))
    if hashlib.sha256(_canonical_json(endpoint).encode("utf-8")).hexdigest() != row.material_hash:
        raise Hy2LabError("material_hash_mismatch")
    outbound = {
        "type": "hysteria2",
        "tag": HY2_OUTBOUND_TAG,
        **endpoint,
    }
    if outbound.get("obfs") is None:
        outbound.pop("obfs", None)
    return {
        "log": {"level": "warn", "timestamp": True},
        "dns": {
            "servers": [
                {"tag": "bootstrap", "address": "local"},
                {"tag": "google", "address": "8.8.8.8", "detour": HY2_OUTBOUND_TAG},
            ],
            "final": "google",
        },
        "inbounds": [],
        "outbounds": [
            outbound,
            {"type": "direct", "tag": "direct"},
            {"type": "block", "tag": "block"},
            {"type": "dns", "tag": "dns-out"},
        ],
        "route": {
            "rules": [
                {"protocol": "dns", "outbound": "dns-out"},
                {"ip_is_private": True, "outbound": "direct"},
            ],
            "auto_detect_interface": True,
            "default_domain_resolver": {
                "server": "bootstrap",
                "strategy": "prefer_ipv4",
            },
            "final": HY2_OUTBOUND_TAG,
        },
        "experimental": {"cache_file": {"enabled": True}},
        "_meta": {
            "title": _clean_text(title)[:64] or "POKROV",
            "transport_contract": {
                "id": HY2_CONTRACT_ID,
                "sha256": HY2_CONTRACT_SHA256,
                "profile": HY2_LAB,
                "state": "enabled",
                "generation": config["generation"],
            },
        },
    }


def safe_hy2_material_summary(row: Hy2LabMaterial) -> dict[str, Any]:
    return {
        "id": int(row.id or 0),
        "tg_id": int(row.tg_id),
        "install_id_sha256": hashlib.sha256(
            f"pokrov-hy2-lab-install\0{row.install_id}".encode("utf-8")
        ).hexdigest(),
        "generation": str(row.generation),
        "endpoint_revision": str(row.endpoint_revision),
        "server_record_id": str(row.server_record_id),
        "node_code": str(row.node_code),
        "material_hash": str(row.material_hash),
        "state": str(row.state),
        "is_active": bool(row.is_active),
        "provisioned_at": (
            row.provisioned_at.isoformat()
            if isinstance(row.provisioned_at, datetime)
            else None
        ),
    }
