"""Device-bound AWG2 owner-lab material and fail-closed rollout contract."""

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

from models import Awg2LabMaterial
from transport_catalog import AWG2_LAB


AWG2_CONTRACT_ID = "pokrov.awg2.endpoint.v1"
AWG2_CONTRACT_SHA256 = (
    "c473c411025825bfef5a76c64990c5c921e9658b3581210d3a86d72e454fdea8"
)
AWG2_ENDPOINT_REVISION = "awg2-v1"
AWG2_ENDPOINT_TAG = "pokrov-awg2-lab"
AWG2_ALLOWED_PLATFORMS = frozenset({"android", "windows"})
AWG2_ALLOWED_MTU = frozenset({1280, 1400, 1408})

_SAFE_TOKEN_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_KEY_BYTES = 32
_DEFAULT_MATERIAL_MAX_AGE_HOURS = 24 * 7
_MATERIAL_SECRET_ENV_KEY = "AWG2_LAB_MATERIAL_SECRET"
_ENDPOINT_FIELDS = frozenset(
    {
        "useIntegratedTun",
        "private_key",
        "address",
        "mtu",
        "jc",
        "jmin",
        "jmax",
        "s1",
        "s2",
        "s3",
        "s4",
        "h1",
        "h2",
        "h3",
        "h4",
        "peers",
    }
)
_PEER_FIELDS = frozenset(
    {
        "address",
        "port",
        "public_key",
        "allowed_ips",
        "persistent_keepalive_interval",
    }
)


class Awg2LabError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = str(code or "awg2_lab_invalid")
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
        raise Awg2LabError(code)
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


def default_awg2_lab_config() -> dict[str, Any]:
    return {
        "enabled": False,
        "kill_switch_engaged": True,
        "allowlist_install_ids": [],
        "allowlist_tg_ids": [],
        "allowlist_node_codes": [],
        "allowed_platforms": sorted(AWG2_ALLOWED_PLATFORMS),
        "expires_at": None,
        "contract_id": AWG2_CONTRACT_ID,
        "contract_sha256": AWG2_CONTRACT_SHA256,
        "generation": "awg2-lab-v1",
        "endpoint_revision": AWG2_ENDPOINT_REVISION,
        "server_record_id": "",
        "server_owner": "pokrov",
        "server_state": "disabled",
        "material_max_age_hours": _DEFAULT_MATERIAL_MAX_AGE_HOURS,
    }


def normalize_awg2_lab_config(value: Any) -> dict[str, Any]:
    source = value if isinstance(value, Mapping) else {}
    defaults = default_awg2_lab_config()
    try:
        max_age = int(
            source.get("material_max_age_hours") or defaults["material_max_age_hours"]
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
            item for item in platforms if item in AWG2_ALLOWED_PLATFORMS
        ],
        "expires_at": _clean_text(source.get("expires_at")) or None,
        "contract_id": _clean_text(source.get("contract_id")) or AWG2_CONTRACT_ID,
        "contract_sha256": _clean_text(source.get("contract_sha256")).lower()
        or AWG2_CONTRACT_SHA256,
        "generation": _clean_text(source.get("generation")).lower()
        or defaults["generation"],
        "endpoint_revision": _clean_text(source.get("endpoint_revision")).lower()
        or AWG2_ENDPOINT_REVISION,
        "server_record_id": _clean_text(source.get("server_record_id")).lower(),
        "server_owner": _clean_text(source.get("server_owner")).lower() or "pokrov",
        "server_state": _clean_text(source.get("server_state")).lower() or "disabled",
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


def awg2_lab_rollout_access(
    value: Any,
    *,
    install_id: str,
    tg_ids: list[int],
    platform: str,
    now: datetime | None = None,
) -> bool:
    config = normalize_awg2_lab_config(value)
    current = now or _utcnow()
    if not config["enabled"] or config["kill_switch_engaged"]:
        return False
    if config["contract_id"] != AWG2_CONTRACT_ID:
        return False
    if config["contract_sha256"] != AWG2_CONTRACT_SHA256:
        return False
    if config["endpoint_revision"] != AWG2_ENDPOINT_REVISION:
        return False
    if config["server_owner"] != "pokrov" or config["server_state"] != "ready":
        return False
    try:
        _safe_token(config["generation"], code="generation_invalid")
        _safe_token(config["server_record_id"], code="server_record_invalid")
    except Awg2LabError:
        return False
    if not _not_expired(config["expires_at"], now=current):
        return False
    if _clean_text(platform).lower() not in set(config["allowed_platforms"]):
        return False
    install = _clean_text(install_id)
    allowed_installs = set(config["allowlist_install_ids"])
    allowed_tg_ids = set(config["allowlist_tg_ids"])
    identities_match = bool(
        (install and install in allowed_installs)
        or allowed_tg_ids.intersection({int(item) for item in tg_ids})
    )
    return identities_match and bool(config["allowlist_node_codes"])


def _material_fernet() -> Fernet:
    secret = _clean_text(os.getenv(_MATERIAL_SECRET_ENV_KEY))
    if not secret:
        raise Awg2LabError("material_secret_unavailable")
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
        raise Awg2LabError("material_decryption_failed") from exc
    if not isinstance(loaded, dict):
        raise Awg2LabError("material_payload_invalid")
    return loaded


def _int_field(value: Any, *, code: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        raise Awg2LabError(code)
    try:
        number = int(value)
    except Exception as exc:
        raise Awg2LabError(code) from exc
    if number < minimum or number > maximum:
        raise Awg2LabError(code)
    return number


def _base64_key(value: Any, *, code: str) -> str:
    raw = _clean_text(value)
    try:
        decoded = base64.b64decode(raw, validate=True)
    except Exception as exc:
        raise Awg2LabError(code) from exc
    if len(decoded) != _KEY_BYTES:
        raise Awg2LabError(code)
    return raw


def _prefixes(value: Any, *, code: str, minimum: int, maximum: int) -> list[str]:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise Awg2LabError(code)
    result: list[str] = []
    for item in value:
        raw = _clean_text(item)
        try:
            ipaddress.ip_interface(raw)
        except ValueError as exc:
            raise Awg2LabError(code) from exc
        result.append(raw)
    return result


def validate_awg2_endpoint(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise Awg2LabError("endpoint_invalid")
    endpoint = dict(value)
    if set(endpoint) != _ENDPOINT_FIELDS:
        raise Awg2LabError("endpoint_fields_invalid")
    if endpoint.get("useIntegratedTun") is not False:
        raise Awg2LabError("integrated_tun_forbidden")

    peers = endpoint.get("peers")
    if (
        not isinstance(peers, list)
        or len(peers) != 1
        or not isinstance(peers[0], Mapping)
    ):
        raise Awg2LabError("peer_count_invalid")
    peer = dict(peers[0])
    if set(peer) != _PEER_FIELDS:
        raise Awg2LabError("peer_fields_invalid")
    peer_address = _clean_text(peer.get("address"))
    try:
        ipaddress.ip_address(peer_address)
    except ValueError as exc:
        raise Awg2LabError("peer_address_invalid") from exc

    mtu = _int_field(endpoint.get("mtu"), code="mtu_invalid", minimum=1, maximum=65535)
    if mtu not in AWG2_ALLOWED_MTU:
        raise Awg2LabError("mtu_invalid")
    jc = _int_field(endpoint.get("jc"), code="junk_invalid", minimum=1, maximum=128)
    jmin = _int_field(
        endpoint.get("jmin"), code="junk_invalid", minimum=1, maximum=65535
    )
    jmax = _int_field(
        endpoint.get("jmax"), code="junk_invalid", minimum=1, maximum=65535
    )
    if jmin > jmax:
        raise Awg2LabError("junk_invalid")

    normalized: dict[str, Any] = {
        "useIntegratedTun": False,
        "private_key": _base64_key(
            endpoint.get("private_key"), code="private_key_invalid"
        ),
        "address": _prefixes(
            endpoint.get("address"), code="address_invalid", minimum=1, maximum=2
        ),
        "mtu": mtu,
        "jc": jc,
        "jmin": jmin,
        "jmax": jmax,
    }
    for field in ("s1", "s2", "s3", "s4"):
        normalized[field] = _int_field(
            endpoint.get(field), code="padding_invalid", minimum=0, maximum=65535
        )
    for field in ("h1", "h2", "h3", "h4"):
        normalized[field] = str(
            _int_field(
                endpoint.get(field), code="header_invalid", minimum=1, maximum=2**32 - 1
            )
        )

    allowed_ips = _prefixes(
        peer.get("allowed_ips"), code="allowed_ips_invalid", minimum=1, maximum=16
    )
    normalized["peers"] = [
        {
            "address": peer_address,
            "port": _int_field(
                peer.get("port"), code="peer_port_invalid", minimum=1, maximum=65535
            ),
            "public_key": _base64_key(
                peer.get("public_key"), code="public_key_invalid"
            ),
            "allowed_ips": allowed_ips,
            "persistent_keepalive_interval": _int_field(
                peer.get("persistent_keepalive_interval"),
                code="keepalive_invalid",
                minimum=0,
                maximum=600,
            ),
        }
    ]
    return normalized


def replace_awg2_lab_material(
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
) -> Awg2LabMaterial:
    install = _clean_text(install_id)
    if not install or len(install) > 128:
        raise Awg2LabError("install_id_invalid")
    generation_value = _safe_token(generation, code="generation_invalid")
    revision_value = _safe_token(endpoint_revision, code="endpoint_revision_invalid")
    if revision_value != AWG2_ENDPOINT_REVISION:
        raise Awg2LabError("endpoint_revision_stale")
    server_record = _safe_token(server_record_id, code="server_record_invalid")
    node = _safe_token(node_code, code="node_code_invalid")
    normalized_endpoint = validate_awg2_endpoint(endpoint)
    canonical = _canonical_json(normalized_endpoint)
    material_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    current = now or _utcnow()

    session.query(Awg2LabMaterial).filter(
        Awg2LabMaterial.tg_id == int(tg_id),
        Awg2LabMaterial.install_id == install,
        Awg2LabMaterial.is_active.is_(True),
    ).update(
        {
            Awg2LabMaterial.is_active: False,
            Awg2LabMaterial.state: "rotated",
            Awg2LabMaterial.revoked_at: current,
            Awg2LabMaterial.updated_at: current,
        },
        synchronize_session=False,
    )
    row = Awg2LabMaterial(
        tg_id=int(tg_id),
        install_id=install,
        contract_id=AWG2_CONTRACT_ID,
        contract_sha256=AWG2_CONTRACT_SHA256,
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


def _active_material(session, *, tg_id: int, install_id: str) -> Awg2LabMaterial | None:
    install = _clean_text(install_id)
    if not install:
        return None
    return (
        session.query(Awg2LabMaterial)
        .filter(
            Awg2LabMaterial.tg_id == int(tg_id),
            Awg2LabMaterial.install_id == install,
            Awg2LabMaterial.is_active.is_(True),
            Awg2LabMaterial.state == "ready",
        )
        .order_by(Awg2LabMaterial.provisioned_at.desc(), Awg2LabMaterial.id.desc())
        .first()
    )


def _ready_material(
    session,
    *,
    tg_id: int,
    install_id: str,
    rollout_value: Any,
    now: datetime | None = None,
) -> Awg2LabMaterial | None:
    config = normalize_awg2_lab_config(rollout_value)
    row = _active_material(session, tg_id=tg_id, install_id=install_id)
    if row is None:
        return None
    current = now or _utcnow()
    provisioned_at = row.provisioned_at
    if not isinstance(provisioned_at, datetime):
        return None
    if provisioned_at.tzinfo is not None and provisioned_at.utcoffset() is not None:
        provisioned_at = provisioned_at.astimezone(timezone.utc).replace(tzinfo=None)
    if provisioned_at < current - timedelta(
        hours=int(config["material_max_age_hours"])
    ):
        return None
    if (
        row.contract_id == config["contract_id"] == AWG2_CONTRACT_ID
        and row.contract_sha256 == config["contract_sha256"] == AWG2_CONTRACT_SHA256
        and row.generation == config["generation"]
        and row.endpoint_revision
        == config["endpoint_revision"]
        == AWG2_ENDPOINT_REVISION
        and row.server_record_id == config["server_record_id"]
        and row.node_code in set(config["allowlist_node_codes"])
    ):
        return row
    return None


def awg2_lab_material_ready(
    session,
    *,
    tg_id: int,
    install_id: str,
    rollout_value: Any,
    now: datetime | None = None,
) -> bool:
    return _ready_material(
        session, tg_id=tg_id, install_id=install_id,
        rollout_value=rollout_value, now=now,
    ) is not None


def build_managed_awg2_lab_config(
    session,
    *,
    tg_id: int,
    install_id: str,
    rollout_value: Any,
    title: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    # Validate and render the same selected row across a concurrent rotation.
    row = _ready_material(
        session,
        tg_id=tg_id,
        install_id=install_id,
        rollout_value=rollout_value,
        now=now,
    )
    if row is None:
        raise Awg2LabError("material_not_ready")
    config = normalize_awg2_lab_config(rollout_value)
    endpoint = validate_awg2_endpoint(_decrypt_endpoint(row.endpoint_ciphertext))
    if (
        hashlib.sha256(_canonical_json(endpoint).encode("utf-8")).hexdigest()
        != row.material_hash
    ):
        raise Awg2LabError("material_hash_mismatch")
    return {
        "log": {"level": "warn", "timestamp": True},
        "dns": {
            "strategy": "ipv4_only",
            "servers": [
                {"tag": "bootstrap", "address": "local"},
                {"tag": "google", "address": "8.8.8.8", "detour": AWG2_ENDPOINT_TAG},
            ],
            "final": "google",
        },
        "inbounds": [],
        "endpoints": [
            {
                "type": "awg",
                "tag": AWG2_ENDPOINT_TAG,
                **endpoint,
            }
        ],
        "outbounds": [
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
            "final": AWG2_ENDPOINT_TAG,
        },
        "experimental": {"cache_file": {"enabled": True}},
        "_meta": {
            "title": _clean_text(title)[:64] or "POKROV",
            "transport_contract": {
                "id": AWG2_CONTRACT_ID,
                "sha256": AWG2_CONTRACT_SHA256,
                "profile": AWG2_LAB,
                "state": "enabled",
                "generation": config["generation"],
            },
        },
    }


def safe_awg2_material_summary(row: Awg2LabMaterial) -> dict[str, Any]:
    return {
        "id": int(row.id or 0),
        "tg_id": int(row.tg_id),
        "install_id_sha256": hashlib.sha256(
            f"pokrov-awg2-lab-install\0{row.install_id}".encode("utf-8")
        ).hexdigest(),
        "generation": str(row.generation),
        "endpoint_revision": str(row.endpoint_revision),
        "server_record_id": str(row.server_record_id),
        "node_code": str(row.node_code),
        "material_hash": str(row.material_hash),
        "state": str(row.state),
        "is_active": bool(row.is_active),
        "provisioned_at": row.provisioned_at.isoformat()
        if isinstance(row.provisioned_at, datetime)
        else None,
    }
