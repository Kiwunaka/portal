"""Bounded runtime self-report for operator diagnostics, never connection authority."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


Protocol = Literal["vless", "awg2", "awg31", "hysteria2", "unknown"]
ProofStage = Literal["unknown", "not_running", "tunnel", "dns", "egress", "degraded"]


class ClientConnectivityIn(BaseModel):
    model_config = {"extra": "forbid"}

    fetched_revision: str | None = Field(default=None, min_length=1, max_length=128)
    staged_revision: str | None = Field(default=None, min_length=1, max_length=128)
    effective_revision: str | None = Field(default=None, min_length=1, max_length=128)
    fetched_protocol: Protocol = "unknown"
    staged_protocol: Protocol = "unknown"
    effective_protocol: Protocol = "unknown"
    proof_stage: ProofStage
    observed_at_ms: int | None = Field(default=None, ge=0, le=253402300799999)


def protocol_from_policy(policy: dict[str, Any]) -> str:
    kind = policy.get("transport_kind")
    if kind in {"awg2", "awg31", "hysteria2"}:
        return str(kind)
    return "vless" if kind in {"reality", "grpc", "xhttp", "ru_bridge"} else "unknown"


def _revision_ref(value: str | None) -> str | None:
    revision = str(value or "").strip()
    return "rev_" + hashlib.sha256(revision.encode()).hexdigest()[:20] if revision else None


def record_connectivity(
    report: ClientConnectivityIn, *, assignment: dict[str, Any], sequence: int,
) -> dict[str, Any]:
    """Raw revisions are discarded before Event metadata is persisted."""
    result = report.model_dump(exclude_none=True)
    result["sequence"] = sequence
    for source in ("fetched", "staged", "effective"):
        result.pop(source + "_revision", None)
        ref = _revision_ref(getattr(report, source + "_revision"))
        if ref is not None:
            result[source + "_revision"] = ref
        else:
            result[source + "_protocol"] = "unknown"
    result["assignment_revision"] = _revision_ref(assignment.get("profile_revision"))
    result["assignment_protocol"] = protocol_from_policy(assignment)
    return result


def runtime_attempt_trace(run_id: str, attempt_number: int | None) -> str | None:
    return hashlib.sha256(f"{run_id}:{attempt_number or 0}".encode()).hexdigest()[:32]


def project_connectivity(
    meta_json: str | None, *, received_at: datetime | None, now: datetime,
) -> dict[str, Any] | None:
    """Re-allowlist stored metadata; old or malformed rows cannot expose raw data."""
    try:
        meta = json.loads(meta_json or "{}")
    except (TypeError, ValueError):
        return None
    value = meta.get("connectivity") if isinstance(meta, dict) else None
    if not isinstance(value, dict):
        return None
    protocols = {"vless", "awg2", "awg31", "hysteria2", "unknown"}
    sources: dict[str, Any] = {}
    for source in ("assignment", "fetched", "staged", "effective"):
        revision = value.get(source + "_revision")
        valid_revision = (
            isinstance(revision, str) and len(revision) == 24
            and revision.startswith("rev_")
            and all(char in "0123456789abcdef" for char in revision[4:])
        )
        protocol = value.get(source + "_protocol")
        sources[source] = {
            "revision": revision if valid_revision else None,
            "protocol": protocol if valid_revision and isinstance(protocol, str) and protocol in protocols else "unknown",
        }
    proof_stage = value.get("proof_stage")
    if not isinstance(proof_stage, str) or proof_stage not in {"not_running", "tunnel", "dns", "egress", "degraded"}:
        proof_stage = "unknown"
    now_ms = int(now.replace(tzinfo=timezone.utc).timestamp() * 1000)
    observed_ms = value.get("observed_at_ms")
    age_seconds = (
        (now_ms - observed_ms) // 1000
        if type(observed_ms) is int and 0 < observed_ms <= now_ms else None
    )
    received = received_at.replace(tzinfo=timezone.utc).isoformat() if received_at else None
    requested = sources["assignment"]["revision"]
    effective = sources["effective"]["revision"]
    protocols_disagree = (
        sources["assignment"]["protocol"] != "unknown"
        and sources["effective"]["protocol"] != "unknown"
        and sources["assignment"]["protocol"] != sources["effective"]["protocol"]
    )
    alignment = (
        "unknown" if not requested or not effective
        else "match" if requested == effective and not protocols_disagree else "mismatch"
    )
    next_action = (
        "refresh_profile" if alignment == "mismatch"
        else "request_diagnostics" if not sources["staged"]["revision"]
        else "refresh_proof"
    )
    return {
        **sources,
        "sequence": value.get("sequence") if type(value.get("sequence")) is int else 0,
        "assignment_authority": "server_policy_at_report",
        "runtime_authority": "client_reported",
        "proof_stage": proof_stage,
        "proof_age_seconds": age_seconds,
        "received_at": received,
        "alignment": alignment,
        "next_action": next_action,
    }
