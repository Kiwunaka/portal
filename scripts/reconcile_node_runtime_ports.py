"""Guarded DB-only repair for an attested direct Reality listener-port drift.

Dry-run is the default.  ``--apply`` never changes a panel, Xray process, or
client record: it updates only the canonical node transport inventory after a
fresh live-panel comparison, explicit compare-and-swap confirmations, and a
separate operator attestation that no L4 frontend maps the public port to a
different internal Xray listener port.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))

from control_panel import ControlPanel
from db import SessionLocal
from models import Node
from nodes_repo import enabled_nodes
from transport_catalog import LEGACY_REALITY_FALLBACK, transport_profile_by_name


# These are the persisted Node values that can be consumed directly or as
# legacy fallbacks while resolving a transport profile.  They are retained in
# the in-memory plan solely as CAS material; public output must never expose
# them.
_PROFILE_SOURCE_FIELDS = (
    "enabled",
    "vless_port",
    "inbound_id",
    "host",
    "reality_sni",
    "reality_pbk",
    "reality_sid",
    "fingerprint",
    "flow",
    "transport_profiles_json",
)


@dataclass(frozen=True)
class PortConfirmation:
    code: str
    expected_db_port: int
    expected_runtime_port: int


@dataclass(frozen=True)
class DirectListenerAttestation:
    code: str
    expected_runtime_port: int


class RepairGuardError(ValueError):
    """The requested operation is not a proven port-only repair."""


def _profile_source(node: Any) -> dict[str, Any]:
    """Capture every persisted input used while resolving a profile."""

    return {
        field: (True if field == "enabled" and not hasattr(node, field) else getattr(node, field, None))
        for field in _PROFILE_SOURCE_FIELDS
    }


def _filter_equals(query, column, value: Any):
    return query.filter(column.is_(None)) if value is None else query.filter(column == value)


def _filter_profile_source_cas(query, source: dict[str, Any]):
    for field in _PROFILE_SOURCE_FIELDS:
        query = _filter_equals(query, getattr(Node, field), source.get(field))
    return query


def _port(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return parsed if 1 <= parsed <= 65535 else 0


def _positive_int(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return parsed if parsed > 0 else 0


def _codes(value: str) -> list[str]:
    return sorted({part.strip().lower() for part in str(value or "").split(",") if part.strip()})


def parse_confirmations(values: Iterable[str]) -> dict[str, PortConfirmation]:
    confirmations: dict[str, PortConfirmation] = {}
    for value in values:
        parts = str(value or "").strip().split(":")
        if len(parts) != 3 or not parts[0].strip():
            raise RepairGuardError("confirmation must be code:expected_db_port:expected_runtime_port")
        code = parts[0].strip().lower()
        confirmation = PortConfirmation(code, _port(parts[1]), _port(parts[2]))
        if not confirmation.expected_db_port or not confirmation.expected_runtime_port or code in confirmations:
            raise RepairGuardError("confirmation must contain unique valid ports")
        confirmations[code] = confirmation
    return confirmations


def parse_direct_listener_attestations(values: Iterable[str]) -> dict[str, DirectListenerAttestation]:
    attestations: dict[str, DirectListenerAttestation] = {}
    for value in values:
        parts = str(value or "").strip().split(":")
        if len(parts) != 2 or not parts[0].strip():
            raise RepairGuardError("direct-listener attestation must be code:expected_runtime_port")
        code = parts[0].strip().lower()
        attestation = DirectListenerAttestation(code, _port(parts[1]))
        if not attestation.expected_runtime_port or code in attestations:
            raise RepairGuardError("direct-listener attestation must contain a unique valid port")
        attestations[code] = attestation
    return attestations


def _profile_port(node: Node, profile_name: str) -> tuple[dict[str, Any], int]:
    profile = transport_profile_by_name(node, profile_name, include_disabled=False, allow_operator_lab=True)
    if str(profile.get("name") or "") != profile_name:
        return {}, 0
    return profile, _port(profile.get("port") or getattr(node, "vless_port", 0))


def _runtime_checks(*, profile: dict[str, Any], snapshot: dict[str, Any] | None) -> dict[str, bool]:
    runtime = snapshot or {}
    expected_inbound_id = _positive_int(profile.get("inbound_id"))
    expected_sni = str(profile.get("tls_server_name") or "").strip()
    expected_sid = str(profile.get("reality_short_id") or "").strip()
    expected_pbk = str(profile.get("reality_public_key") or "").strip()
    server_names = [str(value or "").strip() for value in runtime.get("server_names") or []]
    short_ids = [str(value or "").strip() for value in runtime.get("short_ids") or []]
    dest = str(runtime.get("dest") or "").strip()
    return {
        "inbound_present": bool(runtime),
        "inbound_id": expected_inbound_id > 0 and _positive_int(runtime.get("inbound_id")) == expected_inbound_id,
        "enabled": bool(runtime.get("enable")),
        "protocol": str(runtime.get("protocol") or "").lower() == "vless",
        "network": str(runtime.get("network") or "").lower() == "tcp",
        "security": str(runtime.get("security") or "").lower() == "reality",
        "sni_dest": bool(expected_sni) and (expected_sni in server_names or dest.startswith(f"{expected_sni}:")),
        "short_id": bool(expected_sid) and expected_sid in short_ids,
        "public_key": bool(expected_pbk) and expected_pbk == str(runtime.get("public_key") or "").strip(),
    }


def plan_node_port_repair(node: Node, snapshot: dict[str, Any] | None, *, profile_name: str) -> dict[str, Any]:
    """Build one redacted drift row; this helper never mutates ``node``."""
    profile, current_port = _profile_port(node, profile_name)
    runtime_port = _port((snapshot or {}).get("port"))
    checks = _runtime_checks(profile=profile, snapshot=snapshot) if profile else {"profile": False}
    checks["port"] = bool(current_port and runtime_port and current_port == runtime_port)
    mismatches = sorted(name for name, matched in checks.items() if not matched)
    # A public profile port may intentionally differ from the Xray listener
    # when HAProxy or another L4 frontend owns the public socket.  The panel
    # snapshot alone cannot distinguish that valid topology from stale DB
    # inventory, so dry-run must not call the difference repairable.
    status = "ok" if not mismatches else ("topology_unattested" if mismatches == ["port"] else "blocked")
    return {
        "code": str(getattr(node, "code", "") or "").strip().lower(),
        "node_id": int(getattr(node, "id", 0) or 0),
        "current_port": current_port or None,
        "runtime_port": runtime_port or None,
        "status": status,
        "mismatches": mismatches,
        "profile_name": profile_name,
        "profiles_before": getattr(node, "transport_profiles_json", None),
        "profile_source_before": _profile_source(node),
    }


def _profiles_with_port(raw: str | None, *, profile_name: str, runtime_port: int) -> str | None:
    if not raw:
        if profile_name == LEGACY_REALITY_FALLBACK:
            return raw
        raise RepairGuardError("requested profile is absent from transport inventory")
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise RepairGuardError("transport inventory is not valid JSON") from exc

    changed = False
    if isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, dict) and str(item.get("name") or "") == profile_name:
                item["port"] = runtime_port
                changed = True
                break
    elif isinstance(parsed, dict):
        item = parsed.get(profile_name)
        if isinstance(item, dict):
            item["port"] = runtime_port
            changed = True
    else:
        raise RepairGuardError("transport inventory has unsupported shape")

    if not changed:
        if profile_name == LEGACY_REALITY_FALLBACK:
            return raw
        raise RepairGuardError("requested profile is absent from transport inventory")
    return json.dumps(parsed, ensure_ascii=True, separators=(",", ":"))


def validate_apply_plan(
    plan: Iterable[dict[str, Any]],
    *,
    only: Iterable[str],
    confirmations: dict[str, PortConfirmation],
    direct_listener_attestations: dict[str, DirectListenerAttestation],
) -> list[dict[str, Any]]:
    rows = list(plan)
    requested = set(only)
    row_codes = {str(row.get("code") or "") for row in rows}
    if (
        not requested
        or requested != row_codes
        or requested != set(confirmations)
        or requested != set(direct_listener_attestations)
    ):
        raise RepairGuardError(
            "--apply requires matching --only, --confirm, and --attest-direct-listener entries"
        )
    for row in rows:
        code = str(row["code"])
        confirmation = confirmations[code]
        if row.get("status") != "topology_unattested":
            raise RepairGuardError(f"{code}: only a port-only drift is eligible")
        if _port(row.get("current_port")) != confirmation.expected_db_port:
            raise RepairGuardError(f"{code}: database port no longer matches confirmation")
        if _port(row.get("runtime_port")) != confirmation.expected_runtime_port:
            raise RepairGuardError(f"{code}: runtime port no longer matches confirmation")
        if direct_listener_attestations[code].expected_runtime_port != confirmation.expected_runtime_port:
            raise RepairGuardError(f"{code}: direct-listener attestation no longer matches runtime")
    return rows


def _source_after_repair(row: dict[str, Any]) -> dict[str, Any]:
    source = dict(row["profile_source_before"])
    profile_name = str(row["profile_name"])
    source["transport_profiles_json"] = _profiles_with_port(
        source.get("transport_profiles_json"),
        profile_name=profile_name,
        runtime_port=_port(row["runtime_port"]),
    )
    if profile_name == LEGACY_REALITY_FALLBACK:
        source["vless_port"] = _port(row["runtime_port"])
    return source


def _readback_port_repairs(session, rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    read_back: list[dict[str, Any]] = []
    for row in rows:
        node = session.query(Node).filter(Node.id == int(row["node_id"])).one_or_none()
        profile, current_port = _profile_port(node, str(row["profile_name"])) if node is not None else ({}, 0)
        source_matches = node is not None and _profile_source(node) == _source_after_repair(row)
        applied = bool(profile and source_matches and current_port == _port(row["runtime_port"]))
        read_back.append(
            {
                "code": row["code"],
                "current_port": current_port or None,
                "runtime_port": row["runtime_port"],
                "status": "applied" if applied else "readback_mismatch",
                "mismatches": [] if applied else ["readback_port"],
            }
        )
    return read_back


def _compensate_port_repairs(session, rows: Iterable[dict[str, Any]]) -> dict[str, str]:
    """Best-effort guarded rollback; never overwrite a post-commit change."""

    statuses: dict[str, str] = {}
    try:
        for row in rows:
            after = _source_after_repair(row)
            before = dict(row["profile_source_before"])
            query = session.query(Node).filter(Node.id == int(row["node_id"]))
            query = _filter_profile_source_cas(query, after)
            values: dict[Any, Any] = {Node.transport_profiles_json: before["transport_profiles_json"]}
            if str(row["profile_name"]) == LEGACY_REALITY_FALLBACK:
                values[Node.vless_port] = before["vless_port"]
            statuses[str(row["code"])] = "rolled_back" if query.update(values, synchronize_session=False) == 1 else "rollback_conflict"
        session.commit()
    except Exception:
        session.rollback()
        return {str(row["code"]): "rollback_failed" for row in rows}
    return statuses


def apply_port_repairs(session, plan: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """CAS-update all rows, then compensate with their guarded preimages on a failed readback."""
    rows = list(plan)
    try:
        for row in rows:
            runtime_port = _port(row["runtime_port"])
            profile_name = str(row["profile_name"])
            after = _source_after_repair(row)
            query = session.query(Node).filter(Node.id == int(row["node_id"]))
            query = _filter_profile_source_cas(query, dict(row["profile_source_before"]))
            values: dict[Any, Any] = {Node.transport_profiles_json: after["transport_profiles_json"]}
            if profile_name == LEGACY_REALITY_FALLBACK:
                values[Node.vless_port] = runtime_port
            if query.update(values, synchronize_session=False) != 1:
                raise RepairGuardError(f"{row['code']}: concurrent inventory change")
        session.commit()
    except Exception:
        session.rollback()
        raise

    session.expire_all()
    try:
        read_back = _readback_port_repairs(session, rows)
    except Exception:
        rollback_statuses = _compensate_port_repairs(session, rows)
        return [
            {
                "code": row["code"],
                "current_port": row["current_port"],
                "runtime_port": row["runtime_port"],
                "status": "readback_error",
                "mismatches": ["readback"],
                "rollback_status": rollback_statuses.get(str(row["code"]), "rollback_failed"),
            }
            for row in rows
        ]
    if any(row["status"] != "applied" for row in read_back):
        rollback_statuses = _compensate_port_repairs(session, rows)
        for row in read_back:
            row["rollback_status"] = rollback_statuses.get(str(row["code"]), "rollback_failed")
    return read_back


async def collect_plan(*, only: list[str], profile_name: str) -> list[dict[str, Any]]:
    session = SessionLocal()
    try:
        nodes = enabled_nodes(session)
        if only:
            nodes = [node for node in nodes if str(node.code or "").strip().lower() in set(only)]
            found_codes = {str(node.code or "").strip().lower() for node in nodes}
            if found_codes != set(only):
                raise RepairGuardError("--only contains an unknown or disabled node")
        snapshots_nodes = list(nodes)
    finally:
        session.close()

    panel = ControlPanel()
    try:
        await panel.refresh()
        plan: list[dict[str, Any]] = []
        for node in snapshots_nodes:
            profile, _current_port = _profile_port(node, profile_name)
            snapshot = None
            if profile:
                client = panel._clients.get(str(node.code or ""))
                if client is not None:
                    try:
                        snapshot = await client.get_inbound_snapshot(_positive_int(profile.get("inbound_id")))
                    except Exception:
                        snapshot = None
            plan.append(plan_node_port_repair(node, snapshot, profile_name=profile_name))
        return plan
    finally:
        await panel.close()


def _public_row(row: dict[str, Any]) -> dict[str, Any]:
    public = {key: row.get(key) for key in ("code", "current_port", "runtime_port", "status", "mismatches")}
    if "rollback_status" in row:
        public["rollback_status"] = row.get("rollback_status")
    return public


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Guarded reconciliation of a node profile port to a live Reality inbound.")
    parser.add_argument("--only", default="", help="comma-separated exact node-code allowlist")
    parser.add_argument("--profile", default=LEGACY_REALITY_FALLBACK, help="exact enabled Reality transport profile")
    parser.add_argument("--apply", action="store_true", help="apply after explicit confirmation; dry-run is the default")
    parser.add_argument("--confirm", action="append", default=[], help="repeat code:expected_db_port:expected_runtime_port")
    parser.add_argument(
        "--attest-direct-listener",
        action="append",
        default=[],
        help="repeat code:expected_runtime_port only after proving no L4 frontend owns the public endpoint",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    only = _codes(args.only)
    profile_name = str(args.profile or "").strip()
    try:
        plan = asyncio.run(collect_plan(only=only, profile_name=profile_name))
    except RepairGuardError:
        print(
            json.dumps(
                {"mode": "apply" if args.apply else "dry-run", "status": "blocked", "results": []},
                ensure_ascii=True,
            )
        )
        return 2
    if not args.apply:
        print(json.dumps({"mode": "dry-run", "results": [_public_row(row) for row in plan]}, ensure_ascii=True))
        return 0

    # A separate dry-run may be minutes old. Rebuild from live panel state and
    # current DB inventory immediately before the DB transaction instead of
    # treating its output as a still-valid mutation plan.
    try:
        confirmations = parse_confirmations(args.confirm)
        direct_listener_attestations = parse_direct_listener_attestations(args.attest_direct_listener)
        fresh_plan = asyncio.run(collect_plan(only=only, profile_name=profile_name))
        approved = validate_apply_plan(
            fresh_plan,
            only=only,
            confirmations=confirmations,
            direct_listener_attestations=direct_listener_attestations,
        )
        session = SessionLocal()
        try:
            read_back = apply_port_repairs(session, approved)
        finally:
            session.close()
    except RepairGuardError:
        print(json.dumps({"mode": "apply", "status": "blocked", "results": []}, ensure_ascii=True))
        return 2
    print(json.dumps({"mode": "apply", "results": [_public_row(row) for row in read_back]}, ensure_ascii=True))
    return 0 if all(row.get("status") == "applied" for row in read_back) else 3


if __name__ == "__main__":
    raise SystemExit(main())
