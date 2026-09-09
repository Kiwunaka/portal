"""Release cockpit read models and the server-owned client rollout registry."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from sqlalchemy import func

try:
    from .models import AccountDevice, AppSetting, ReleaseCandidate, SupportBundleUpload
    from .operator_observability_service import known_issues, release_health_snapshot
    from .release_evidence_service import (
        ReleaseEvidenceNotFound,
        ReleaseEvidenceReadError,
        get_release_readiness,
        list_release_candidates,
    )
except ImportError:
    from models import AccountDevice, AppSetting, ReleaseCandidate, SupportBundleUpload
    from operator_observability_service import known_issues, release_health_snapshot
    from release_evidence_service import (
        ReleaseEvidenceNotFound,
        ReleaseEvidenceReadError,
        get_release_readiness,
        list_release_candidates,
    )


RELEASE_ROLLOUT_SETTING_KEY = "release_rollout_v1"
RELEASE_ROLLOUT_SCHEMA = 1
RELEASE_PLATFORMS = frozenset({"android", "windows"})
RELEASE_GATE_POLICY_VERSION = "pokrov.operator-cockpit-gates/v1"
RELEASE_GATE_NAMES = (
    "app_tests",
    "core_tests",
    "backend_tests",
    "admin_tests",
    "android_proof",
    "windows_proof",
    "payment_proof",
    "update_proof",
    "signing",
    "public_url",
    "docs_support_readiness",
)
_ROLLOUT_STATES = frozenset(
    {"candidate", "staged", "paused", "current", "rollback_requested", "deprecated"}
)


class OperatorReleaseError(ValueError):
    def __init__(self, code: str, *, status_code: int = 422, message: str | None = None) -> None:
        super().__init__(code)
        self.code = str(code)
        self.status_code = int(status_code)
        self.message = str(message or code)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _as_utc_naive(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(microsecond=0)
    return value.astimezone(timezone.utc).replace(tzinfo=None, microsecond=0)


def _iso(value: datetime | None) -> str | None:
    normalized = _as_utc_naive(value)
    if normalized is None:
        return None
    return normalized.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (TypeError, ValueError, OverflowError):
        return None
    return _as_utc_naive(parsed)


def _empty_registry() -> dict[str, Any]:
    return {
        "schema_version": RELEASE_ROLLOUT_SCHEMA,
        "active_by_platform": {},
        "states": {},
        "history": [],
    }


def _state_key(candidate_id: str, platform: str) -> str:
    return f"{platform}:{candidate_id}"


def _safe_registry(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or int(value.get("schema_version") or 0) != RELEASE_ROLLOUT_SCHEMA:
        return _empty_registry()
    active = value.get("active_by_platform")
    states = value.get("states")
    history = value.get("history")
    if not isinstance(active, dict) or not isinstance(states, dict) or not isinstance(history, list):
        return _empty_registry()
    safe_states: dict[str, dict[str, Any]] = {}
    for key, item in states.items():
        if not isinstance(key, str) or not isinstance(item, dict):
            continue
        candidate_id = str(item.get("candidate_id") or "")
        platform = str(item.get("platform") or "")
        status = str(item.get("status") or "candidate")
        if (
            len(candidate_id) != 64
            or platform not in RELEASE_PLATFORMS
            or status not in _ROLLOUT_STATES
            or key != _state_key(candidate_id, platform)
        ):
            continue
        safe_states[key] = dict(item)
    return {
        "schema_version": RELEASE_ROLLOUT_SCHEMA,
        "active_by_platform": {
            str(platform): str(candidate_id)
            for platform, candidate_id in active.items()
            if str(platform) in RELEASE_PLATFORMS and len(str(candidate_id)) == 64
        },
        "states": safe_states,
        "history": [dict(item) for item in history[-100:] if isinstance(item, dict)],
    }


def load_release_rollout_registry(session, *, for_update: bool = False) -> tuple[AppSetting | None, dict[str, Any]]:
    query = session.query(AppSetting).filter(AppSetting.key == RELEASE_ROLLOUT_SETTING_KEY)
    if for_update and str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    row = query.one_or_none()
    if row is None or not str(row.value_json or "").strip():
        return row, _empty_registry()
    try:
        parsed = json.loads(str(row.value_json))
    except (TypeError, ValueError):
        raise OperatorReleaseError(
            "release_rollout_registry_invalid",
            status_code=503,
            message="Release rollout registry is invalid.",
        ) from None
    registry = _safe_registry(parsed)
    if registry == _empty_registry() and parsed != registry:
        raise OperatorReleaseError(
            "release_rollout_registry_invalid",
            status_code=503,
            message="Release rollout registry is invalid.",
        )
    return row, registry


def rollout_state(
    registry: Mapping[str, Any],
    *,
    candidate_id: str,
    platform: str,
) -> dict[str, Any] | None:
    states = registry.get("states") if isinstance(registry.get("states"), Mapping) else {}
    value = states.get(_state_key(candidate_id, platform))
    return dict(value) if isinstance(value, Mapping) else None


def release_gate_matrix(readiness: Mapping[str, Any]) -> dict[str, Any]:
    latest: dict[str, str] = {}
    for origin in readiness.get("origins") or []:
        if not isinstance(origin, Mapping):
            continue
        for check in list(origin.get("checks") or []) + list(origin.get("diagnostics") or []):
            if isinstance(check, Mapping):
                latest.setdefault(str(check.get("check_name") or ""), str(check.get("status") or "MISSING"))
    gates = [
        {"check_name": name, "status": latest.get(name, "MISSING")}
        for name in RELEASE_GATE_NAMES
    ]
    origins_pass = bool(readiness.get("ready"))
    all_pass = origins_pass and all(item["status"] == "PASS" for item in gates)
    return {
        "status": "PASS" if all_pass else "MISSING" if not any(item["status"] == "FAIL" for item in gates) else "FAIL",
        "ready": all_pass,
        "origin_readiness_status": str(readiness.get("status") or "MISSING"),
        "policy_version": RELEASE_GATE_POLICY_VERSION,
        # These operational checks do not load the separate exact-candidate
        # Gate F decision or authorize an external artifact switch.
        "gate_f_decision": "NOT_EVALUATED",
        "checks": gates,
    }


def release_candidates(session, *, limit: int = 50, cursor: str | None = None, now: datetime | None = None) -> dict[str, Any]:
    return list_release_candidates(session, limit=limit, cursor=cursor, now=now or _utcnow())


def version_adoption(session, *, days: int = 30, now: datetime | None = None) -> dict[str, Any]:
    window_days = max(1, min(int(days), 90))
    current = _as_utc_naive(now) or _utcnow()
    cutoff = current - timedelta(days=window_days)
    rows = (
        session.query(
            AccountDevice.platform,
            AccountDevice.app_version,
            func.count(func.distinct(AccountDevice.install_id)),
            func.max(AccountDevice.last_seen_at),
        )
        .filter(
            AccountDevice.state == "active",
            AccountDevice.last_seen_at >= cutoff,
            AccountDevice.platform.isnot(None),
            AccountDevice.app_version.isnot(None),
        )
        .group_by(AccountDevice.platform, AccountDevice.app_version)
        .all()
    )
    cohorts = [
        {
            "platform": str(platform or "unknown").lower(),
            "app_version": str(version or "unknown"),
            "observed_installations": int(count or 0),
            "last_seen_at": _iso(last_seen),
        }
        for platform, version, count, last_seen in rows
    ]
    totals: dict[str, int] = {}
    for item in cohorts:
        totals[item["platform"]] = totals.get(item["platform"], 0) + int(item["observed_installations"])
    for item in cohorts:
        denominator = totals.get(item["platform"], 0)
        item["share_percent"] = round(100 * int(item["observed_installations"]) / denominator, 2) if denominator else 0.0
    cohorts.sort(key=lambda item: (str(item["platform"]), -int(item["observed_installations"]), str(item["app_version"])))
    return {
        "window_days": window_days,
        "window_start": _iso(cutoff),
        "authority": "active_account_devices_last_seen",
        "cohorts": cohorts,
        "platform_totals": totals,
    }


def support_delta(session, *, version: str, hours: int, now: datetime | None = None) -> dict[str, Any]:
    window_hours = max(1, min(int(hours), 168))
    current = _as_utc_naive(now) or _utcnow()
    start = current - timedelta(hours=window_hours)
    previous_start = start - timedelta(hours=window_hours)
    rows = (
        session.query(SupportBundleUpload.created_at)
        .filter(
            SupportBundleUpload.app_version == str(version),
            SupportBundleUpload.created_at >= previous_start,
        )
        .all()
    )
    current_count = sum(1 for (created_at,) in rows if _as_utc_naive(created_at) and _as_utc_naive(created_at) >= start)
    previous_count = len(rows) - current_count
    return {
        "authority": "version_bound_support_bundles",
        "current": current_count,
        "previous": previous_count,
        "delta": current_count - previous_count,
        "window_hours": window_hours,
    }


def release_health_gate(
    health: Mapping[str, Any],
    *,
    version: str,
    thresholds: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    limits = {
        "crash_failures": max(0, int((thresholds or {}).get("crash_failures", 0))),
        "connect_failures": max(0, int((thresholds or {}).get("connect_failures", 0))),
        "update_failures": max(0, int((thresholds or {}).get("update_failures", 0))),
    }
    groups = [
        dict(group)
        for group in health.get("groups") or []
        if isinstance(group, Mapping) and str(group.get("app_version") or "") == str(version)
    ]
    if not groups:
        return {"status": "MISSING", "reason": "no_version_health", "thresholds": limits, "groups": []}
    breaches: list[dict[str, Any]] = []
    for group in groups:
        delta = group.get("delta") if isinstance(group.get("delta"), Mapping) else {}
        for name, limit in limits.items():
            observed = int(delta.get(name) or 0)
            if observed > limit:
                breaches.append(
                    {
                        "platform": str(group.get("platform") or "unknown"),
                        "architecture": str(group.get("architecture") or "unknown"),
                        "metric": name,
                        "observed_delta": observed,
                        "threshold": limit,
                    }
                )
    return {
        "status": "FAIL" if breaches else "PASS",
        "reason": "regression_threshold_breached" if breaches else "within_thresholds",
        "thresholds": limits,
        "groups": groups,
        "breaches": breaches,
    }


def candidate_cockpit(
    session,
    *,
    candidate_id: str,
    hours: int = 24,
    now: datetime | None = None,
) -> dict[str, Any]:
    current = _as_utc_naive(now) or _utcnow()
    readiness = get_release_readiness(session, candidate_id, now=current)
    candidate = dict(readiness["candidate"])
    component_rows = (
        session.query(ReleaseCandidate)
        .filter(ReleaseCandidate.version == str(candidate.get("version") or ""))
        .order_by(ReleaseCandidate.component.asc(), ReleaseCandidate.imported_at.desc())
        .all()
    )
    health = release_health_snapshot(session, hours=hours, now=current)
    _, registry = load_release_rollout_registry(session)
    states = [
        rollout_state(registry, candidate_id=candidate_id, platform=platform)
        for platform in sorted(RELEASE_PLATFORMS)
    ]
    states = [state for state in states if state is not None]
    active_by_platform = dict(registry.get("active_by_platform") or {})
    thresholds = next((state.get("thresholds") for state in states if isinstance(state.get("thresholds"), Mapping)), {})
    return {
        "candidate": candidate,
        "components": [
            {
                "candidate_id": str(row.candidate_id),
                "component": str(row.component),
                "version": str(row.version),
                "revision": str(row.revision),
                "artifact_sha256": str(row.artifact_sha256),
                "descriptor_sha256": str(row.descriptor_sha256),
                "imported_at": _iso(row.imported_at),
            }
            for row in component_rows
        ],
        "readiness": readiness,
        "gate_matrix": release_gate_matrix(readiness),
        "rollout": {
            "states": states,
            "active_by_platform": active_by_platform,
            "source": RELEASE_ROLLOUT_SETTING_KEY,
        },
        "adoption": version_adoption(session, days=30, now=current),
        "health": health,
        "health_gate": release_health_gate(
            health,
            version=str(candidate.get("version") or ""),
            thresholds=thresholds if isinstance(thresholds, Mapping) else {},
        ),
        "support_delta": support_delta(
            session,
            version=str(candidate.get("version") or ""),
            hours=hours,
            now=current,
        ),
        "known_issues": [
            issue
            for issue in known_issues(session, limit=200)
            if str(issue.get("app_version") or "") == str(candidate.get("version") or "")
        ],
        "generated_at": _iso(current),
    }


def store_release_rollout_registry(
    session,
    *,
    row: AppSetting | None,
    registry: Mapping[str, Any],
    now: datetime | None = None,
) -> AppSetting:
    current = _as_utc_naive(now) or _utcnow()
    if row is None:
        row = AppSetting(key=RELEASE_ROLLOUT_SETTING_KEY, updated_at=current)
        session.add(row)
    row.value_json = json.dumps(dict(registry), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    row.updated_at = current
    session.flush()
    return row


def public_client_rollout_policy(
    session,
    *,
    platform: str,
    configured_version: str,
    configured_min_supported_version: str,
) -> dict[str, Any]:
    normalized_platform = str(platform or "").strip().lower()
    if normalized_platform not in RELEASE_PLATFORMS:
        return {
            "source": "static_release_settings",
            "rollout_percent": 100,
            "min_supported_version": str(configured_min_supported_version or ""),
            "paused": False,
            "candidate_id": None,
            "status": "legacy_current",
        }
    _, registry = load_release_rollout_registry(session)
    candidate_id = str((registry.get("active_by_platform") or {}).get(normalized_platform) or "")
    if not candidate_id:
        return {
            "source": "static_release_settings",
            "rollout_percent": 100,
            "min_supported_version": str(configured_min_supported_version or ""),
            "paused": False,
            "candidate_id": None,
            "status": "legacy_current",
        }
    state = rollout_state(registry, candidate_id=candidate_id, platform=normalized_platform)
    candidate = session.query(ReleaseCandidate).filter(ReleaseCandidate.candidate_id == candidate_id).one_or_none()
    if state is None or candidate is None or str(candidate.version) != str(configured_version or ""):
        return {
            "source": RELEASE_ROLLOUT_SETTING_KEY,
            "rollout_percent": 0,
            "min_supported_version": str(configured_min_supported_version or ""),
            "paused": True,
            "candidate_id": candidate_id,
            "status": "artifact_configuration_mismatch",
        }
    paused = bool(state.get("paused")) or str(state.get("status")) in {"paused", "rollback_requested"}
    return {
        "source": RELEASE_ROLLOUT_SETTING_KEY,
        "rollout_percent": 0 if paused else max(0, min(int(state.get("rollout_percent") or 0), 100)),
        "min_supported_version": str(state.get("min_supported_version") or configured_min_supported_version or ""),
        "paused": paused,
        "candidate_id": candidate_id,
        "status": str(state.get("status") or "candidate"),
    }


__all__ = [
    "OperatorReleaseError",
    "RELEASE_GATE_NAMES",
    "RELEASE_PLATFORMS",
    "RELEASE_ROLLOUT_SETTING_KEY",
    "candidate_cockpit",
    "load_release_rollout_registry",
    "public_client_rollout_policy",
    "release_candidates",
    "release_gate_matrix",
    "release_health_gate",
    "rollout_state",
    "store_release_rollout_registry",
    "version_adoption",
]
