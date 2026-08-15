"""Redacted admin read model for the emergency catalog lifecycle."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func

try:
    from emergency_catalog_service import rollback_candidates
    from emergency_catalog_worker import (
        emergency_catalog_worker_enabled,
        load_emergency_catalog_worker_config,
    )
    from models import EmergencyCatalogEndpoint, EmergencyCatalogSnapshot
except ImportError:  # pragma: no cover - package import
    from .emergency_catalog_service import rollback_candidates
    from .emergency_catalog_worker import (
        emergency_catalog_worker_enabled,
        load_emergency_catalog_worker_config,
    )
    from .models import EmergencyCatalogEndpoint, EmergencyCatalogSnapshot


def _iso_z(value: datetime | None) -> str | None:
    if value is None:
        return None
    aware = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    return aware.isoformat(timespec="seconds").replace("+00:00", "Z")


def _snapshot_row(row: EmergencyCatalogSnapshot) -> dict[str, Any]:
    return {
        "snapshot_id": str(row.id),
        "catalog_version": str(row.catalog_version),
        "source_revision": str(row.source_revision),
        "status": str(row.status),
        "candidate_count": int(row.candidate_count or 0),
        "healthy_count": int(row.healthy_count or 0),
        "active_endpoint_count": int(row.active_endpoint_count or 0),
        "rejection_code": str(row.rejection_code) if row.rejection_code else None,
        "operator_approved": bool(row.operator_approved),
        "issued_at": _iso_z(row.issued_at),
        "expires_at": _iso_z(row.expires_at),
        "activated_at": _iso_z(row.activated_at),
        "created_at": _iso_z(row.created_at),
        "updated_at": _iso_z(row.updated_at),
    }


def _worker_status() -> dict[str, Any]:
    enabled = emergency_catalog_worker_enabled()
    if not enabled:
        return {
            "enabled": False,
            "configuration_state": "disabled",
            "interval_seconds": None,
            "probe_concurrency": None,
        }
    try:
        config = load_emergency_catalog_worker_config()
    except Exception:
        return {
            "enabled": True,
            "configuration_state": "invalid",
            "interval_seconds": None,
            "probe_concurrency": None,
        }
    return {
        "enabled": True,
        "configuration_state": "ready",
        "interval_seconds": int(config.interval_seconds),
        "probe_concurrency": int(config.probe_concurrency),
    }


def build_emergency_catalog_admin_status(session, *, limit: int = 20) -> dict[str, Any]:
    bounded_limit = max(1, min(int(limit), 50))
    status_counts = {
        str(status): int(count or 0)
        for status, count in session.query(
            EmergencyCatalogSnapshot.status,
            func.count(EmergencyCatalogSnapshot.id),
        ).group_by(EmergencyCatalogSnapshot.status).all()
    }
    snapshots = (
        session.query(EmergencyCatalogSnapshot)
        .order_by(EmergencyCatalogSnapshot.created_at.desc())
        .limit(bounded_limit)
        .all()
    )
    active = (
        session.query(EmergencyCatalogSnapshot)
        .filter(EmergencyCatalogSnapshot.status == "active")
        .order_by(EmergencyCatalogSnapshot.activated_at.desc())
        .first()
    )
    distribution = (
        session.query(EmergencyCatalogSnapshot)
        .filter(EmergencyCatalogSnapshot.status.in_(("active", "disabled")))
        .order_by(
            EmergencyCatalogSnapshot.updated_at.desc(),
            EmergencyCatalogSnapshot.id.desc(),
        )
        .first()
    )
    probe_snapshot = (
        session.query(EmergencyCatalogSnapshot)
        .filter(EmergencyCatalogSnapshot.status == "staging")
        .order_by(EmergencyCatalogSnapshot.created_at.desc())
        .first()
        or active
    )
    probe_counts: Counter[str] = Counter()
    if probe_snapshot is not None:
        probe_counts.update(
            {
                str(state): int(count or 0)
                for state, count in session.query(
                    EmergencyCatalogEndpoint.probe_state,
                    func.count(EmergencyCatalogEndpoint.id),
                )
                .filter(EmergencyCatalogEndpoint.snapshot_id == probe_snapshot.id)
                .group_by(EmergencyCatalogEndpoint.probe_state)
                .all()
            }
        )
    return {
        "generated_at": _iso_z(datetime.now(timezone.utc)),
        "worker": _worker_status(),
        "snapshot_counts": status_counts,
        "active": _snapshot_row(active) if active is not None else None,
        "distribution": _snapshot_row(distribution) if distribution is not None else None,
        "probe_summary": {
            "snapshot_id": str(probe_snapshot.id) if probe_snapshot is not None else None,
            "pending": int(probe_counts.get("pending", 0)),
            "healthy": int(probe_counts.get("healthy", 0)),
            "unavailable": int(probe_counts.get("unavailable", 0)),
            "total": int(sum(probe_counts.values())),
        },
        "rollback_candidates": rollback_candidates(session, limit=3),
        "snapshots": [_snapshot_row(row) for row in snapshots],
    }
