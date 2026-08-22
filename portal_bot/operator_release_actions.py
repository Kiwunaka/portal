"""Stored action-intent policies for release rollout control."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

try:
    from .models import ReleaseCandidate
    from .operator_observability_service import release_health_snapshot
    from .operator_release_service import (
        RELEASE_PLATFORMS,
        load_release_rollout_registry,
        release_gate_matrix,
        release_health_gate,
        rollout_state,
        store_release_rollout_registry,
    )
    from .release_evidence_service import get_release_readiness
except ImportError:
    from models import ReleaseCandidate
    from operator_observability_service import release_health_snapshot
    from operator_release_service import (
        RELEASE_PLATFORMS,
        load_release_rollout_registry,
        release_gate_matrix,
        release_health_gate,
        rollout_state,
        store_release_rollout_registry,
    )
    from release_evidence_service import get_release_readiness


RELEASE_ACTIONS = frozenset(
    {
        "release.rollout.start",
        "release.rollout.change",
        "release.rollout.pause",
        "release.rollout.rollback",
        "release.min_supported.set",
        "release.observation.close",
    }
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_VERSION_RE = re.compile(r"[0-9A-Za-z][0-9A-Za-z._+-]{0,63}")
_THRESHOLD_NAMES = ("crash_failures", "connect_failures", "update_failures")


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _iso(value: datetime) -> str:
    return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (TypeError, ValueError, OverflowError):
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed.replace(microsecond=0)


def _error(error_type, code: str, message: str, *, status_code: int = 422):
    raise error_type(code, status_code=status_code, message=message)


def _registry_hash(registry: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        dict(registry), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _thresholds(error_type, value: object) -> dict[str, int]:
    source = value if isinstance(value, Mapping) else {}
    extra = sorted(set(source) - set(_THRESHOLD_NAMES))
    if extra:
        _error(error_type, "invalid_payload", f"Unsupported thresholds: {', '.join(extra)}")
    result: dict[str, int] = {}
    for name in _THRESHOLD_NAMES:
        try:
            normalized = int(source.get(name) or 0)
        except (TypeError, ValueError):
            _error(error_type, "invalid_payload", "Regression threshold is invalid.")
        if not 0 <= normalized <= 10000:
            _error(error_type, "invalid_payload", "Regression threshold is out of range.")
        result[name] = normalized
    return result


def _payload(error_type, action: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    fields = {
        "release.rollout.start": {
            "platform",
            "rollout_percent",
            "min_supported_version",
            "observation_hours",
            "thresholds",
        },
        "release.rollout.change": {"platform", "rollout_percent"},
        "release.rollout.pause": {"platform"},
        "release.rollout.rollback": {"platform", "rollback_candidate_id"},
        "release.min_supported.set": {"platform", "min_supported_version"},
        "release.observation.close": {"platform"},
    }
    allowed = fields[action] | {"_environment", "_operator_id", "_actor_tg_id"}
    extra = sorted(set(payload) - allowed)
    if extra:
        _error(error_type, "invalid_payload", f"Unsupported payload fields: {', '.join(extra)}")
    platform = str(payload.get("platform") or "").strip().lower()
    if platform not in RELEASE_PLATFORMS:
        _error(error_type, "invalid_payload", "Release platform is invalid.")
    try:
        actor_tg_id = int(payload.get("_actor_tg_id"))
    except (TypeError, ValueError):
        _error(error_type, "invalid_payload", "Operator identity is invalid.")
    if actor_tg_id <= 0:
        _error(error_type, "invalid_payload", "Operator identity is invalid.")
    result: dict[str, Any] = {
        "_environment": str(payload.get("_environment") or "unknown").strip().lower()[:32],
        "_operator_id": str(payload.get("_operator_id") or "").strip()[:128],
        "_actor_tg_id": actor_tg_id,
        "platform": platform,
    }
    if action in {"release.rollout.start", "release.rollout.change"}:
        try:
            percent = int(payload.get("rollout_percent"))
        except (TypeError, ValueError):
            _error(error_type, "invalid_payload", "Rollout percent is invalid.")
        if not 1 <= percent <= 100:
            _error(error_type, "invalid_payload", "Rollout percent must be between 1 and 100.")
        result["rollout_percent"] = percent
    if action in {"release.rollout.start", "release.min_supported.set"}:
        version = str(payload.get("min_supported_version") or "").strip()
        if _VERSION_RE.fullmatch(version) is None:
            _error(error_type, "invalid_payload", "Minimum supported version is invalid.")
        result["min_supported_version"] = version
    if action == "release.rollout.start":
        try:
            observation_hours = int(payload.get("observation_hours") or 24)
        except (TypeError, ValueError):
            _error(error_type, "invalid_payload", "Observation window is invalid.")
        if not 1 <= observation_hours <= 168:
            _error(error_type, "invalid_payload", "Observation window must be 1-168 hours.")
        result["observation_hours"] = observation_hours
        result["thresholds"] = _thresholds(error_type, payload.get("thresholds"))
    if action == "release.rollout.rollback":
        rollback_candidate_id = str(payload.get("rollback_candidate_id") or "").strip().lower()
        if _SHA256_RE.fullmatch(rollback_candidate_id) is None:
            _error(error_type, "invalid_payload", "Rollback candidate id is invalid.")
        result["rollback_candidate_id"] = rollback_candidate_id
    return result


def _state(EntityState, error_type, action: str, session, target_id: str, payload, for_update: bool):
    candidate_id = str(target_id or "").strip().lower()
    if _SHA256_RE.fullmatch(candidate_id) is None:
        _error(error_type, "invalid_target", "Release candidate id is invalid.")
    query = session.query(ReleaseCandidate).filter(ReleaseCandidate.candidate_id == candidate_id)
    if for_update and str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    candidate = query.one_or_none()
    if candidate is None:
        _error(error_type, "target_not_found", "Release candidate was not found.", status_code=404)
    row, registry = load_release_rollout_registry(session, for_update=for_update)
    platform = str(payload["platform"])
    state = rollout_state(registry, candidate_id=candidate_id, platform=platform)
    active_candidate_id = str((registry.get("active_by_platform") or {}).get(platform) or "")
    readiness_gate: dict[str, Any] | None = None
    health_gate: dict[str, Any] | None = None

    if action == "release.rollout.start":
        if state is not None or active_candidate_id == candidate_id:
            _error(error_type, "release_rollout_exists", "Candidate rollout already exists.", status_code=409)
        readiness_gate = release_gate_matrix(get_release_readiness(session, candidate_id))
        if not readiness_gate["ready"]:
            _error(error_type, "release_gates_incomplete", "Release evidence gates are incomplete.", status_code=409)
    else:
        if state is None or active_candidate_id != candidate_id:
            _error(error_type, "release_rollout_not_active", "Candidate is not the active platform rollout.", status_code=409)

    rollback_state: dict[str, Any] | None = None
    if action == "release.rollout.rollback":
        rollback_candidate_id = str(payload["rollback_candidate_id"])
        if rollback_candidate_id == candidate_id:
            _error(error_type, "invalid_payload", "Rollback candidate must differ from the active candidate.")
        rollback_candidate = (
            session.query(ReleaseCandidate)
            .filter(ReleaseCandidate.candidate_id == rollback_candidate_id)
            .one_or_none()
        )
        rollback_state = rollout_state(
            registry, candidate_id=rollback_candidate_id, platform=platform
        )
        if rollback_candidate is None or rollback_state is None:
            _error(
                error_type,
                "rollback_candidate_unavailable",
                "Rollback candidate has no retained rollout state.",
                status_code=409,
            )

    if action == "release.observation.close":
        observation_ends_at = _parse_time((state or {}).get("observation_ends_at"))
        if observation_ends_at is None or observation_ends_at > _now():
            _error(error_type, "observation_window_open", "Observation window is still open.", status_code=409)
        health = release_health_snapshot(
            session,
            hours=int((state or {}).get("observation_hours") or 24),
            now=_now(),
        )
        health_gate = release_health_gate(
            health,
            version=str(candidate.version),
            thresholds=(state or {}).get("thresholds") or {},
        )
        if health_gate["status"] != "PASS":
            _error(error_type, "release_health_gate_failed", "Release health gate did not pass.", status_code=409)

    before = state or {
        "candidate_id": candidate_id,
        "platform": platform,
        "status": "candidate",
        "rollout_percent": 0,
        "paused": True,
    }
    version = {
        "candidate_id": candidate_id,
        "descriptor_sha256": str(candidate.descriptor_sha256),
        "registry_sha256": _registry_hash(registry),
        "readiness_gate": readiness_gate,
        "health_gate": health_gate,
    }
    return EntityState(
        entity=candidate,
        version_snapshot=version,
        public_snapshot=dict(before),
        context={
            "action": action,
            "candidate_id": candidate_id,
            "candidate_version": str(candidate.version),
            "platform": platform,
            "setting_row": row,
            "registry": registry,
            "rollback_state": rollback_state,
        },
    )


def _after(state, payload) -> dict[str, Any]:
    action = str(state.context["action"])
    before = dict(state.public_snapshot)
    if action == "release.rollout.start":
        return {
            **before,
            "status": "staged",
            "rollout_percent": int(payload["rollout_percent"]),
            "paused": False,
            "min_supported_version": str(payload["min_supported_version"]),
            "observation_hours": int(payload["observation_hours"]),
            "thresholds": dict(payload["thresholds"]),
        }
    if action == "release.rollout.change":
        return {**before, "status": "staged", "rollout_percent": int(payload["rollout_percent"]), "paused": False}
    if action == "release.rollout.pause":
        return {**before, "status": "paused", "rollout_percent": 0, "paused": True}
    if action == "release.rollout.rollback":
        return {
            **before,
            "status": "rollback_requested",
            "rollout_percent": 0,
            "paused": True,
            "rollback_candidate_id": str(payload["rollback_candidate_id"]),
        }
    if action == "release.min_supported.set":
        return {**before, "min_supported_version": str(payload["min_supported_version"])}
    return {**before, "status": "current", "rollout_percent": 100, "paused": False}


def _preview(state, payload) -> dict[str, Any]:
    action = str(state.context["action"])
    warnings: list[str] = []
    if action in {"release.rollout.start", "release.rollout.change", "release.rollout.pause"}:
        warnings.append("Команда меняет процент выдачи обновления клиентским API.")
    if action == "release.min_supported.set":
        warnings.append("Команда меняет обязательность обновления для старых версий клиента.")
    if action == "release.rollout.rollback":
        warnings.append(
            "Команда блокирует выдачу нового артефакта и фиксирует rollback request; внешний указатель артефакта не переключается автоматически."
        )
    return {
        "title": "Управление релизом",
        "summary": "Состояние rollout изменится атомарно только при совпадении candidate и registry snapshot.",
        "candidate_id": str(state.context["candidate_id"]),
        "candidate_version": str(state.context["candidate_version"]),
        "platform": str(state.context["platform"]),
        "before": state.public_snapshot,
        "after": _after(state, payload),
        "warnings": warnings,
    }


def _execute(error_type, session, state, payload) -> dict[str, Any]:
    action = str(state.context["action"])
    candidate_id = str(state.context["candidate_id"])
    platform = str(state.context["platform"])
    registry = dict(state.context["registry"])
    registry["active_by_platform"] = dict(registry.get("active_by_platform") or {})
    registry["states"] = dict(registry.get("states") or {})
    registry["history"] = list(registry.get("history") or [])
    key = f"{platform}:{candidate_id}"
    current = _now()
    before = dict(registry["states"].get(key) or state.public_snapshot)
    after = _after(state, payload)
    after.update(
        {
            "candidate_id": candidate_id,
            "candidate_version": str(state.context["candidate_version"]),
            "platform": platform,
            "updated_at": _iso(current),
            "updated_by": int(payload["_actor_tg_id"]),
        }
    )
    external_artifact_switch = "NOT_REQUIRED"
    if action == "release.rollout.start":
        after["previous_candidate_id"] = str(registry["active_by_platform"].get(platform) or "") or None
        after["observation_started_at"] = _iso(current)
        after["observation_ends_at"] = _iso(current + timedelta(hours=int(payload["observation_hours"])))
        registry["active_by_platform"][platform] = candidate_id
    elif action == "release.rollout.rollback":
        rollback_candidate_id = str(payload["rollback_candidate_id"])
        rollback_key = f"{platform}:{rollback_candidate_id}"
        rollback_state = dict(registry["states"].get(rollback_key) or {})
        if not rollback_state:
            _error(error_type, "rollback_candidate_unavailable", "Rollback state disappeared.", status_code=409)
        rollback_state.update(
            {
                "status": "current",
                "paused": False,
                "rollout_percent": 100,
                "updated_at": _iso(current),
                "updated_by": int(payload["_actor_tg_id"]),
            }
        )
        registry["states"][rollback_key] = rollback_state
        registry["active_by_platform"][platform] = rollback_candidate_id
        after["rollback_requested_at"] = _iso(current)
        external_artifact_switch = "NOT_PERFORMED"
    elif action == "release.observation.close":
        after["observation_closed_at"] = _iso(current)
    registry["states"][key] = after
    registry["history"].append(
        {
            "action": action,
            "candidate_id": candidate_id,
            "platform": platform,
            "actor_tg_id": int(payload["_actor_tg_id"]),
            "environment": str(payload["_environment"]),
            "before_status": str(before.get("status") or "candidate"),
            "after_status": str(after.get("status") or "candidate"),
            "rollout_percent": int(after.get("rollout_percent") or 0),
            "occurred_at": _iso(current),
        }
    )
    registry["history"] = registry["history"][-100:]
    store_release_rollout_registry(
        session,
        row=state.context["setting_row"],
        registry=registry,
        now=current,
    )
    return {
        "rollout": after,
        "external_artifact_switch": external_artifact_switch,
    }


def _audit_meta(state, payload) -> dict[str, Any]:
    return {
        "candidate_id": str(state.context["candidate_id"]),
        "candidate_version": str(state.context["candidate_version"]),
        "platform": str(state.context["platform"]),
        "environment": str(payload["_environment"]),
        "rollout_percent": payload.get("rollout_percent"),
        "rollback_candidate_id": payload.get("rollback_candidate_id"),
        "min_supported_version": payload.get("min_supported_version"),
    }


def build_release_action_policies(*, ActionPolicy, EntityState, ActionIntentError) -> dict[str, Any]:
    policies: dict[str, Any] = {}
    for action in sorted(RELEASE_ACTIONS):
        high_risk = action in {
            "release.rollout.start",
            "release.rollout.change",
            "release.rollout.rollback",
            "release.min_supported.set",
        }
        policies[action] = ActionPolicy(
            action=action,
            target_type="release_candidate",
            risk_level="L3" if high_risk else "L2",
            payload_normalizer=lambda payload, selected=action: _payload(
                ActionIntentError, selected, payload
            ),
            entity_state_builder=lambda session, target_id, payload, for_update, selected=action: _state(
                EntityState,
                ActionIntentError,
                selected,
                session,
                target_id,
                payload,
                for_update,
            ),
            preview_builder=_preview,
            challenge_kind="exact_candidate_id" if high_risk else "exact_phrase",
            challenge_builder=(
                (lambda state, _payload: str(state.context["candidate_id"]))
                if high_risk
                else (lambda _state, _payload: "ПРИМЕНИТЬ")
            ),
            executor_kind="db",
            audit_action=action,
            db_executor=lambda session, state, payload: _execute(
                ActionIntentError, session, state, payload
            ),
            audit_meta_builder=_audit_meta,
        )
    return policies


__all__ = ["RELEASE_ACTIONS", "build_release_action_policies"]
