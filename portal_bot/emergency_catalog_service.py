"""Versioned staging, signing, promotion, serving and rollback for emergency catalogs."""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Sequence

try:
    from emergency_catalog_crypto import (
        EmergencyCatalogCrypto,
        EmergencyCatalogCryptoError,
        canonical_catalog_bytes,
        catalog_sha256,
    )
    from emergency_catalog_source import EmergencyEndpointMaterial, SOURCE_CONTRACT
    from models import EmergencyCatalogEndpoint, EmergencyCatalogSnapshot
except ImportError:  # pragma: no cover - package import
    from .emergency_catalog_crypto import (
        EmergencyCatalogCrypto,
        EmergencyCatalogCryptoError,
        canonical_catalog_bytes,
        catalog_sha256,
    )
    from .emergency_catalog_source import EmergencyEndpointMaterial, SOURCE_CONTRACT
    from .models import EmergencyCatalogEndpoint, EmergencyCatalogSnapshot


CATALOG_SCHEMA_VERSION = "pokrov-emergency-catalog-v1"
SUPPORTED_CHAIN_MODES = (
    "reserve_direct",
    "reserve_foreign",
    "reserve_ru_foreign",
)
MIN_ACTIVE_ENDPOINTS = 4
MAX_ACTIVE_ENDPOINTS = 12
MAX_CANDIDATES_PER_SNAPSHOT = 128
MAX_AUTOMATIC_REPLACEMENT_FRACTION = 0.5
DEFAULT_VERIFICATION_MAX_AGE = timedelta(hours=24)
DEFAULT_CATALOG_LIFETIME = timedelta(days=7)
STAGING_DEDUPE_WINDOW = timedelta(hours=2)

_DIGEST_RE = re.compile(r"^[a-f0-9]{64}$")
_REVISION_RE = re.compile(r"^[a-f0-9]{40,64}$")
_SAFE_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,63}$")


class EmergencyCatalogServiceError(RuntimeError):
    """Fixed-code domain failure safe for logs and admin status surfaces."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class EndpointProbeResult:
    authenticated: bool
    payload_ok: bool
    payload_sha256: str
    exit_country: str
    latency_ms: int
    verified_at: datetime
    verification_source: str = "controlled_core"
    error_code: str = ""


@dataclass(frozen=True, slots=True)
class StageSnapshotResult:
    snapshot: EmergencyCatalogSnapshot
    created: bool


@dataclass(frozen=True, slots=True)
class PromotionResult:
    snapshot: EmergencyCatalogSnapshot
    selected_stable_ids: tuple[str, ...]
    replacement_fraction: float


@dataclass(frozen=True, slots=True)
class ServingEndpointMaterial:
    catalog: dict[str, Any]
    endpoint: EmergencyCatalogEndpoint
    record: dict[str, Any]


def _distribution_snapshot(session, *, for_update: bool = False) -> EmergencyCatalogSnapshot | None:
    query = (
        session.query(EmergencyCatalogSnapshot)
        .filter(EmergencyCatalogSnapshot.status.in_(("active", "disabled")))
        .order_by(
            EmergencyCatalogSnapshot.updated_at.desc(),
            EmergencyCatalogSnapshot.activated_at.desc(),
            EmergencyCatalogSnapshot.id.desc(),
        )
    )
    if for_update:
        query = query.with_for_update()
    rows = query.all()
    if len(rows) > 1:
        raise EmergencyCatalogServiceError("multiple_distribution_snapshots")
    return rows[0] if rows else None


def _selected_verified_rows(
    session,
    *,
    snapshot_id: str,
    current: datetime,
    verification_max_age: timedelta,
) -> list[EmergencyCatalogEndpoint]:
    min_verified_at = _naive_utc(current - verification_max_age)
    rows = (
        session.query(EmergencyCatalogEndpoint)
        .filter(
            EmergencyCatalogEndpoint.snapshot_id == str(snapshot_id),
            EmergencyCatalogEndpoint.probe_state == "healthy",
            EmergencyCatalogEndpoint.authenticated.is_(True),
            EmergencyCatalogEndpoint.payload_ok.is_(True),
            EmergencyCatalogEndpoint.verified_at >= min_verified_at,
        )
        .order_by(EmergencyCatalogEndpoint.latency_ms.asc(), EmergencyCatalogEndpoint.stable_id.asc())
        .all()
    )
    selected: list[EmergencyCatalogEndpoint] = []
    seen_hosts: set[str] = set()
    for row in rows:
        if str(row.exit_country or "").upper() == "RU":
            continue
        if row.endpoint_host_hash in seen_hosts:
            continue
        seen_hosts.add(row.endpoint_host_hash)
        selected.append(row)
        if len(selected) == MAX_ACTIVE_ENDPOINTS:
            break
    return selected


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(microsecond=value.microsecond)
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso_z(value: datetime) -> str:
    return _aware_utc(value).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_iso_z(value: object) -> datetime:
    raw = str(value or "").strip()
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EmergencyCatalogServiceError("catalog_time_invalid") from exc
    if parsed.tzinfo is None:
        raise EmergencyCatalogServiceError("catalog_time_invalid")
    return parsed.astimezone(timezone.utc)


def _safe_code(value: object, *, fallback: str) -> str:
    candidate = str(value or "").strip().lower()
    return candidate if _SAFE_CODE_RE.fullmatch(candidate) else fallback


def _material_record(material: EmergencyEndpointMaterial) -> dict[str, Any]:
    return {
        "stable_id": material.stable_id,
        "transport": material.transport,
        "outbound": material.managed_outbound_fields(),
    }


def _material_hash(record: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_catalog_bytes(record)).hexdigest()


def _endpoint_host_hash(material: EmergencyEndpointMaterial) -> str:
    return hashlib.sha256(
        b"pokrov-emergency-host-v1\0" + material.endpoint_host.encode("utf-8")
    ).hexdigest()


def _validate_probe_result(
    result: EndpointProbeResult,
    *,
    expected_payload_sha256: str,
) -> tuple[str, str]:
    country = str(result.exit_country or "").strip().upper()
    if re.fullmatch(r"[A-Z]{2}", country) is None:
        return "unavailable", "exit_country_invalid"
    if country == "RU":
        return "unavailable", "exit_country_ru"
    if not 0 <= int(result.latency_ms) <= 60_000:
        return "unavailable", "latency_invalid"
    if result.verified_at.tzinfo is None:
        return "unavailable", "verification_time_invalid"
    payload_sha256 = str(result.payload_sha256 or "").strip().lower()
    if _DIGEST_RE.fullmatch(payload_sha256) is None:
        return "unavailable", "payload_digest_invalid"
    if payload_sha256 != expected_payload_sha256:
        return "unavailable", "payload_mismatch"
    if not result.authenticated:
        return "unavailable", _safe_code(result.error_code, fallback="authentication_failed")
    if not result.payload_ok:
        return "unavailable", _safe_code(result.error_code, fallback="payload_failed")
    return "healthy", ""


def stage_snapshot(
    session,
    *,
    materials: Sequence[EmergencyEndpointMaterial],
    source_revision: str,
    source_digest: str,
    crypto: EmergencyCatalogCrypto,
    probes: Mapping[str, EndpointProbeResult] | None = None,
    expected_payload_sha256: str,
    now: datetime | None = None,
) -> StageSnapshotResult:
    """Create an encrypted staging snapshot; identical recent input is idempotent."""

    current = _aware_utc(now or datetime.now(timezone.utc))
    revision = str(source_revision or "").strip().lower()
    digest = str(source_digest or "").strip().lower()
    expected_digest = str(expected_payload_sha256 or "").strip().lower()
    if _REVISION_RE.fullmatch(revision) is None:
        raise EmergencyCatalogServiceError("source_revision_invalid")
    if _DIGEST_RE.fullmatch(digest) is None:
        raise EmergencyCatalogServiceError("source_digest_invalid")
    if _DIGEST_RE.fullmatch(expected_digest) is None:
        raise EmergencyCatalogServiceError("expected_payload_digest_invalid")

    unique: list[EmergencyEndpointMaterial] = []
    seen: set[str] = set()
    for material in materials:
        if material.stable_id in seen:
            continue
        seen.add(material.stable_id)
        unique.append(material)
    if not unique:
        raise EmergencyCatalogServiceError("snapshot_has_no_candidates")
    if len(unique) > MAX_CANDIDATES_PER_SNAPSHOT:
        raise EmergencyCatalogServiceError("too_many_snapshot_candidates")

    recent_after = _naive_utc(current - STAGING_DEDUPE_WINDOW)
    existing = (
        session.query(EmergencyCatalogSnapshot)
        .filter(
            EmergencyCatalogSnapshot.source_digest == digest,
            EmergencyCatalogSnapshot.status.in_(("staging", "active")),
            EmergencyCatalogSnapshot.created_at >= recent_after,
        )
        .order_by(EmergencyCatalogSnapshot.created_at.desc())
        .first()
    )
    if existing is not None:
        return StageSnapshotResult(existing, False)

    snapshot_id = str(uuid.uuid4())
    snapshot = EmergencyCatalogSnapshot(
        id=snapshot_id,
        catalog_version=f"emg-{uuid.uuid4().hex}",
        contract_version=SOURCE_CONTRACT,
        source_revision=revision,
        source_digest=digest,
        status="staging",
        candidate_count=len(unique),
        healthy_count=0,
        active_endpoint_count=0,
        created_at=_naive_utc(current),
        updated_at=_naive_utc(current),
    )
    session.add(snapshot)
    session.flush()

    probe_map = dict(probes or {})
    healthy_count = 0
    for ordinal, material in enumerate(unique, start=1):
        record = _material_record(material)
        probe = probe_map.get(material.stable_id)
        state = "pending"
        error_code = ""
        if probe is not None:
            state, error_code = _validate_probe_result(
                probe,
                expected_payload_sha256=expected_digest,
            )
            healthy_count += int(state == "healthy")
        endpoint = EmergencyCatalogEndpoint(
            snapshot_id=snapshot_id,
            stable_id=material.stable_id,
            ordinal=ordinal,
            transport=material.transport,
            endpoint_host_hash=_endpoint_host_hash(material),
            material_ciphertext=crypto.encrypt_json(record),
            material_hash=_material_hash(record),
            probe_state=state,
            exit_country=(str(probe.exit_country).strip().upper() if probe is not None else None),
            latency_ms=(int(probe.latency_ms) if probe is not None else None),
            authenticated=(bool(probe.authenticated) if probe is not None else False),
            payload_ok=(bool(probe.payload_ok) if probe is not None else False),
            payload_sha256=(str(probe.payload_sha256).strip().lower() if probe is not None else None),
            verification_source=(
                _safe_code(probe.verification_source, fallback="controlled_core")
                if probe is not None
                else None
            ),
            verified_at=(_naive_utc(probe.verified_at) if probe is not None else None),
            error_code=error_code or None,
            created_at=_naive_utc(current),
            updated_at=_naive_utc(current),
        )
        session.add(endpoint)
    snapshot.healthy_count = healthy_count
    session.flush()
    return StageSnapshotResult(snapshot, True)


def apply_probe_result(
    session,
    *,
    snapshot_id: str,
    stable_id: str,
    result: EndpointProbeResult,
    expected_payload_sha256: str,
    now: datetime | None = None,
) -> EmergencyCatalogEndpoint:
    current = _aware_utc(now or datetime.now(timezone.utc))
    snapshot = session.get(EmergencyCatalogSnapshot, str(snapshot_id))
    if snapshot is None or snapshot.status != "staging":
        raise EmergencyCatalogServiceError("snapshot_not_staging")
    endpoint = (
        session.query(EmergencyCatalogEndpoint)
        .filter_by(snapshot_id=snapshot.id, stable_id=str(stable_id))
        .with_for_update()
        .first()
    )
    if endpoint is None:
        raise EmergencyCatalogServiceError("endpoint_not_found")
    state, error_code = _validate_probe_result(
        result,
        expected_payload_sha256=str(expected_payload_sha256 or "").strip().lower(),
    )
    endpoint.probe_state = state
    endpoint.exit_country = str(result.exit_country or "").strip().upper() or None
    endpoint.latency_ms = int(result.latency_ms)
    endpoint.authenticated = bool(result.authenticated)
    endpoint.payload_ok = bool(result.payload_ok)
    endpoint.payload_sha256 = str(result.payload_sha256 or "").strip().lower() or None
    endpoint.verification_source = _safe_code(result.verification_source, fallback="controlled_core")
    endpoint.verified_at = _naive_utc(result.verified_at)
    endpoint.error_code = error_code or None
    endpoint.updated_at = _naive_utc(current)
    snapshot.healthy_count = (
        session.query(EmergencyCatalogEndpoint)
        .filter_by(snapshot_id=snapshot.id, probe_state="healthy")
        .count()
    )
    snapshot.updated_at = _naive_utc(current)
    session.flush()
    return endpoint


def _open_endpoint_record(
    endpoint: EmergencyCatalogEndpoint,
    *,
    crypto: EmergencyCatalogCrypto,
) -> dict[str, Any]:
    record = crypto.decrypt_json(endpoint.material_ciphertext)
    if _material_hash(record) != str(endpoint.material_hash or ""):
        raise EmergencyCatalogServiceError("endpoint_material_hash_mismatch")
    if record.get("stable_id") != endpoint.stable_id or record.get("transport") != endpoint.transport:
        raise EmergencyCatalogServiceError("endpoint_material_identity_mismatch")
    outbound = record.get("outbound")
    if not isinstance(outbound, dict) or outbound.get("type") != "vless":
        raise EmergencyCatalogServiceError("endpoint_material_invalid")
    return record


def _open_signed_snapshot(
    snapshot: EmergencyCatalogSnapshot,
    *,
    crypto: EmergencyCatalogCrypto,
) -> dict[str, Any]:
    if not snapshot.catalog_ciphertext or not snapshot.signature_b64:
        raise EmergencyCatalogServiceError("snapshot_unsigned")
    if snapshot.signing_key_id != crypto.key_id:
        raise EmergencyCatalogServiceError("snapshot_signing_key_unknown")
    try:
        payload = crypto.decrypt_json(snapshot.catalog_ciphertext)
        crypto.verify(payload, snapshot.signature_b64)
    except EmergencyCatalogCryptoError as exc:
        raise EmergencyCatalogServiceError(exc.code) from exc
    if catalog_sha256(payload) != str(snapshot.catalog_hash or ""):
        raise EmergencyCatalogServiceError("snapshot_catalog_hash_mismatch")
    if payload.get("schema_version") != CATALOG_SCHEMA_VERSION:
        raise EmergencyCatalogServiceError("snapshot_schema_invalid")
    if payload.get("catalog_version") != snapshot.catalog_version:
        raise EmergencyCatalogServiceError("snapshot_version_mismatch")
    endpoints = payload.get("endpoints")
    if not isinstance(endpoints, list) or not MIN_ACTIVE_ENDPOINTS <= len(endpoints) <= MAX_ACTIVE_ENDPOINTS:
        raise EmergencyCatalogServiceError("snapshot_endpoint_count_invalid")
    return payload


def promote_snapshot(
    session,
    *,
    snapshot_id: str,
    crypto: EmergencyCatalogCrypto,
    operator_approved: bool = False,
    now: datetime | None = None,
    verification_max_age: timedelta = DEFAULT_VERIFICATION_MAX_AGE,
    catalog_lifetime: timedelta = DEFAULT_CATALOG_LIFETIME,
) -> PromotionResult:
    current = _aware_utc(now or datetime.now(timezone.utc))
    snapshot = (
        session.query(EmergencyCatalogSnapshot)
        .filter(EmergencyCatalogSnapshot.id == str(snapshot_id))
        .with_for_update()
        .first()
    )
    if snapshot is None or snapshot.status != "staging":
        raise EmergencyCatalogServiceError("snapshot_not_staging")

    selected_rows = _selected_verified_rows(
        session,
        snapshot_id=snapshot.id,
        current=current,
        verification_max_age=verification_max_age,
    )
    snapshot.healthy_count = len(selected_rows)
    if len(selected_rows) < MIN_ACTIVE_ENDPOINTS:
        snapshot.rejection_code = "insufficient_healthy_endpoints"
        snapshot.updated_at = _naive_utc(current)
        session.flush()
        raise EmergencyCatalogServiceError("insufficient_healthy_endpoints")

    current_distribution = _distribution_snapshot(session, for_update=True)
    if (
        current_distribution is not None
        and current_distribution.status == "disabled"
        and not operator_approved
    ):
        snapshot.rejection_code = "catalog_distribution_disabled"
        snapshot.updated_at = _naive_utc(current)
        session.flush()
        raise EmergencyCatalogServiceError("catalog_distribution_disabled")
    current_active = (
        current_distribution
        if current_distribution is not None and current_distribution.status == "active"
        else None
    )
    selected_ids = tuple(row.stable_id for row in selected_rows)
    replacement_fraction = 0.0
    if current_active is not None:
        active_payload = _open_signed_snapshot(current_active, crypto=crypto)
        active_ids = {
            str(item.get("stable_id") or "")
            for item in active_payload.get("endpoints", [])
            if isinstance(item, dict)
        }
        removed = active_ids.difference(selected_ids)
        replacement_fraction = len(removed) / max(1, len(active_ids))
        if replacement_fraction > MAX_AUTOMATIC_REPLACEMENT_FRACTION and not operator_approved:
            fresh_active_ids = {
                row.stable_id
                for row in _selected_verified_rows(
                    session,
                    snapshot_id=current_active.id,
                    current=current,
                    verification_max_age=verification_max_age,
                )
                if row.stable_id in active_ids
            }
            if len(fresh_active_ids) >= MIN_ACTIVE_ENDPOINTS:
                snapshot.rejection_code = "automatic_churn_limit"
                snapshot.updated_at = _naive_utc(current)
                session.flush()
                raise EmergencyCatalogServiceError("automatic_churn_limit")

    signed_endpoints: list[dict[str, Any]] = []
    for row in selected_rows:
        record = _open_endpoint_record(row, crypto=crypto)
        signed_endpoints.append(
            {
                "stable_id": row.stable_id,
                "transport": row.transport,
                "country_code": str(row.exit_country or "").upper(),
                "verified_at": _iso_z(_aware_utc(row.verified_at)),
                "supported_chain_modes": list(SUPPORTED_CHAIN_MODES),
                "outbound": record["outbound"],
            }
        )

    expires_at = current + catalog_lifetime
    payload: dict[str, Any] = {
        "schema_version": CATALOG_SCHEMA_VERSION,
        "catalog_version": snapshot.catalog_version,
        "signing_key_id": crypto.key_id,
        "issued_at": _iso_z(current),
        "expires_at": _iso_z(expires_at),
        "source_revision": snapshot.source_revision,
        "source_digest": snapshot.source_digest,
        "endpoints": signed_endpoints,
    }
    snapshot.catalog_ciphertext = crypto.encrypt_json(payload)
    snapshot.catalog_hash = catalog_sha256(payload)
    snapshot.signature_b64 = crypto.sign(payload)
    snapshot.signing_key_id = crypto.key_id
    snapshot.active_endpoint_count = len(signed_endpoints)
    snapshot.operator_approved = bool(operator_approved)
    snapshot.rejection_code = None
    snapshot.parent_snapshot_id = current_distribution.id if current_distribution is not None else None
    snapshot.issued_at = _naive_utc(current)
    snapshot.expires_at = _naive_utc(expires_at)
    snapshot.activated_at = _naive_utc(current)
    snapshot.updated_at = _naive_utc(current)
    snapshot.status = "active"
    if current_distribution is not None:
        current_distribution.status = "superseded"
        current_distribution.superseded_at = _naive_utc(current)
        current_distribution.updated_at = _naive_utc(current)
    session.flush()
    return PromotionResult(snapshot, selected_ids, replacement_fraction)


def read_serving_catalog(
    session,
    *,
    crypto: EmergencyCatalogCrypto,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Read active or one of three retained valid LKG snapshots without mutation."""

    current = _aware_utc(now or datetime.now(timezone.utc))
    distribution = _distribution_snapshot(session)
    if distribution is not None and distribution.status == "disabled":
        raise EmergencyCatalogServiceError("catalog_distribution_disabled")
    rows = (
        session.query(EmergencyCatalogSnapshot)
        .filter(EmergencyCatalogSnapshot.status.in_(("active", "superseded")))
        .order_by(
            (EmergencyCatalogSnapshot.status == "active").desc(),
            EmergencyCatalogSnapshot.activated_at.desc(),
        )
        .limit(4)
        .all()
    )
    for snapshot in rows:
        try:
            payload = _open_signed_snapshot(snapshot, crypto=crypto)
            if _parse_iso_z(payload.get("expires_at")) <= current:
                continue
            return payload
        except EmergencyCatalogServiceError:
            continue
    raise EmergencyCatalogServiceError("no_valid_serving_catalog")


def safe_promotion_delta(
    session,
    *,
    snapshot_id: str,
    crypto: EmergencyCatalogCrypto,
    now: datetime | None = None,
    verification_max_age: timedelta = DEFAULT_VERIFICATION_MAX_AGE,
) -> dict[str, Any]:
    """Return count-only promotion impact; endpoint identifiers and material stay server-side."""

    current = _aware_utc(now or datetime.now(timezone.utc))
    target = session.get(EmergencyCatalogSnapshot, str(snapshot_id))
    if target is None or target.status != "staging":
        raise EmergencyCatalogServiceError("snapshot_not_staging")
    selected = _selected_verified_rows(
        session,
        snapshot_id=target.id,
        current=current,
        verification_max_age=verification_max_age,
    )
    next_ids = {row.stable_id for row in selected}
    distribution = _distribution_snapshot(session)
    current_ids: set[str] = set()
    if distribution is not None:
        payload = _open_signed_snapshot(distribution, crypto=crypto)
        current_ids = {
            str(item.get("stable_id") or "")
            for item in payload.get("endpoints", [])
            if isinstance(item, dict)
        }
    retained = current_ids.intersection(next_ids)
    removed = current_ids.difference(next_ids)
    added = next_ids.difference(current_ids)
    replacement_fraction = len(removed) / max(1, len(current_ids)) if current_ids else 0.0
    return {
        "distribution_state": str(distribution.status) if distribution is not None else "empty",
        "current_count": len(current_ids),
        "next_count": len(next_ids),
        "retained_count": len(retained),
        "removed_count": len(removed),
        "added_count": len(added),
        "replacement_percent": round(replacement_fraction * 100, 1),
        "automatic_limit_exceeded": replacement_fraction > MAX_AUTOMATIC_REPLACEMENT_FRACTION,
    }


def disable_active_catalog(
    session,
    *,
    snapshot_id: str,
    now: datetime | None = None,
) -> EmergencyCatalogSnapshot:
    """Stop server distribution until an operator explicitly promotes or rolls back."""

    current = _aware_utc(now or datetime.now(timezone.utc))
    distribution = _distribution_snapshot(session, for_update=True)
    if distribution is None or distribution.status != "active":
        raise EmergencyCatalogServiceError("active_snapshot_missing")
    if str(distribution.id) != str(snapshot_id):
        raise EmergencyCatalogServiceError("active_snapshot_changed")
    distribution.status = "disabled"
    distribution.operator_approved = True
    distribution.rejection_code = "operator_disabled"
    distribution.updated_at = _naive_utc(current)
    session.flush()
    return distribution


def read_serving_endpoint_material(
    session,
    *,
    stable_id: str,
    crypto: EmergencyCatalogCrypto,
    now: datetime | None = None,
) -> ServingEndpointMaterial:
    """Return one exact endpoint only after the serving catalog verifies."""

    current = _aware_utc(now or datetime.now(timezone.utc))
    catalog = read_serving_catalog(session, crypto=crypto, now=current)
    selected = None
    for item in catalog.get("endpoints", []):
        if isinstance(item, dict) and item.get("stable_id") == str(stable_id or ""):
            selected = item
            break
    if selected is None:
        raise EmergencyCatalogServiceError("reserve_not_in_serving_catalog")
    snapshot = (
        session.query(EmergencyCatalogSnapshot)
        .filter(EmergencyCatalogSnapshot.catalog_version == catalog["catalog_version"])
        .first()
    )
    if snapshot is None:
        raise EmergencyCatalogServiceError("serving_snapshot_missing")
    endpoint = (
        session.query(EmergencyCatalogEndpoint)
        .filter_by(snapshot_id=snapshot.id, stable_id=str(stable_id or ""))
        .first()
    )
    if endpoint is None:
        raise EmergencyCatalogServiceError("serving_endpoint_missing")
    if endpoint.probe_state != "healthy" or not endpoint.authenticated or not endpoint.payload_ok:
        raise EmergencyCatalogServiceError("serving_endpoint_unhealthy")
    if endpoint.verified_at is None:
        raise EmergencyCatalogServiceError("serving_endpoint_unverified")
    # The signed serving catalog is the last-known-good recovery set. Its own
    # bounded expiry is the authority for offline use; a 24-hour probe age is a
    # freshness signal, not a reason to strand an already entitled device when
    # the control plane is unreachable.
    record = _open_endpoint_record(endpoint, crypto=crypto)
    if record.get("outbound") != selected.get("outbound"):
        raise EmergencyCatalogServiceError("serving_endpoint_material_mismatch")
    return ServingEndpointMaterial(catalog=catalog, endpoint=endpoint, record=record)


def rollback_candidates(session, *, limit: int = 3) -> list[dict[str, Any]]:
    bounded_limit = max(1, min(int(limit), 3))
    rows = (
        session.query(EmergencyCatalogSnapshot)
        .filter(
            EmergencyCatalogSnapshot.status == "superseded",
            EmergencyCatalogSnapshot.catalog_ciphertext.is_not(None),
            EmergencyCatalogSnapshot.signature_b64.is_not(None),
        )
        .order_by(EmergencyCatalogSnapshot.activated_at.desc())
        .limit(bounded_limit)
        .all()
    )
    return [
        {
            "snapshot_id": row.id,
            "catalog_version": row.catalog_version,
            "endpoint_count": int(row.active_endpoint_count or 0),
            "activated_at": _iso_z(_aware_utc(row.activated_at)) if row.activated_at else None,
        }
        for row in rows
    ]


def rollback_to_snapshot(
    session,
    *,
    target_snapshot_id: str,
    crypto: EmergencyCatalogCrypto,
    now: datetime | None = None,
) -> PromotionResult:
    current = _aware_utc(now or datetime.now(timezone.utc))
    allowed_ids = {item["snapshot_id"] for item in rollback_candidates(session, limit=3)}
    if str(target_snapshot_id) not in allowed_ids:
        raise EmergencyCatalogServiceError("rollback_target_not_retained")
    target = session.get(EmergencyCatalogSnapshot, str(target_snapshot_id))
    if target is None:
        raise EmergencyCatalogServiceError("rollback_target_not_found")
    target_payload = _open_signed_snapshot(target, crypto=crypto)
    retained_ids = tuple(
        str(item.get("stable_id") or "")
        for item in target_payload.get("endpoints", [])
        if isinstance(item, dict)
    )
    if not MIN_ACTIVE_ENDPOINTS <= len(retained_ids) <= MAX_ACTIVE_ENDPOINTS:
        raise EmergencyCatalogServiceError("rollback_target_invalid")

    clone = EmergencyCatalogSnapshot(
        id=str(uuid.uuid4()),
        catalog_version=f"emg-{uuid.uuid4().hex}",
        contract_version=target.contract_version,
        source_revision=target.source_revision,
        source_digest=target.source_digest,
        status="staging",
        candidate_count=target.candidate_count,
        healthy_count=target.healthy_count,
        active_endpoint_count=0,
        rollback_of_snapshot_id=target.id,
        operator_approved=True,
        created_at=_naive_utc(current),
        updated_at=_naive_utc(current),
    )
    session.add(clone)
    session.flush()
    source_rows = (
        session.query(EmergencyCatalogEndpoint)
        .filter(
            EmergencyCatalogEndpoint.snapshot_id == target.id,
            EmergencyCatalogEndpoint.stable_id.in_(retained_ids),
        )
        .order_by(EmergencyCatalogEndpoint.ordinal.asc())
        .all()
    )
    if {row.stable_id for row in source_rows} != set(retained_ids):
        raise EmergencyCatalogServiceError("rollback_target_material_missing")
    for source in source_rows:
        session.add(
            EmergencyCatalogEndpoint(
                snapshot_id=clone.id,
                stable_id=source.stable_id,
                ordinal=source.ordinal,
                transport=source.transport,
                endpoint_host_hash=source.endpoint_host_hash,
                material_ciphertext=source.material_ciphertext,
                material_hash=source.material_hash,
                probe_state=source.probe_state,
                exit_country=source.exit_country,
                latency_ms=source.latency_ms,
                authenticated=source.authenticated,
                payload_ok=source.payload_ok,
                payload_sha256=source.payload_sha256,
                verification_source=source.verification_source,
                verified_at=source.verified_at,
                error_code=source.error_code,
                created_at=_naive_utc(current),
                updated_at=_naive_utc(current),
            )
        )
    session.flush()
    try:
        return promote_snapshot(
            session,
            snapshot_id=clone.id,
            crypto=crypto,
            operator_approved=True,
            now=current,
        )
    except Exception:
        session.delete(clone)
        session.flush()
        raise
