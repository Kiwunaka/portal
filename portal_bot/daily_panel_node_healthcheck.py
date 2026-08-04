from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import func, or_

from control_panel import ControlPanel
from db import SessionLocal
from models import Node, NodeHealthSample, User, UserNode
from node_policy import (
    FREE_SOFT_ROLE,
    FREE_STANDARD_ROLE,
    NodeAccessRoleError,
    free_pool_node_codes,
    paid_pool_node_codes,
    user_free_access_role,
    user_uses_free_pool,
    validate_node_access_roles,
)
from nodes_repo import enabled_nodes


REPORT_DIR = Path(os.getenv("DAILY_HEALTH_REPORT_DIR", "/root/portal_bot/health_reports"))
API_HEALTH_URL = os.getenv("DAILY_HEALTH_API_URL", "http://127.0.0.1:8080/api/health")
METRICS_STALE_AFTER_MINUTES = int(os.getenv("DAILY_HEALTH_METRICS_STALE_AFTER_MINUTES", "15"))
PANEL_HEALTHCHECK_MAX_CONCURRENCY = 4
PANEL_HEALTHCHECK_NODE_TIMEOUT_SECONDS = 45

_PREMIUM_PLAN_CODES = frozenset({"trial", "channel_bonus", "start_99"})
_EXPLICIT_PREMIUM_SUB_TYPES = frozenset(
    {
        "PAID",
        "BONUS",
        "CHANNEL_BONUS",
        "OPENING_BONUS",
        "FRIEND_GIFT",
        "VIP",
        "PRO",
        "BASIC",
        "MONTHLY",
        "QUARTERLY",
        "HALF_YEAR",
        "YEARLY",
    }
)
_FREE_PROFILE_STATES = frozenset(
    {"standard", "soft_transition_pending", "soft_active", "reset_pending", "error"}
)


@dataclass(frozen=True)
class PolicyIdentityScope:
    """Internal identity groups excluded from actionable access drift."""

    actionable_user_count: int = 0
    manual_tg_ids: frozenset[int] = frozenset()
    manual_uuid_to_tg: dict[str, int] = field(default_factory=dict)
    unresolved_tg_ids: frozenset[int] = frozenset()
    unresolved_uuid_to_tg: dict[str, int] = field(default_factory=dict)
    unresolved_reasons: dict[str, int] = field(default_factory=dict)

    def public_summary(self) -> dict[str, object]:
        """Return count-only policy evidence safe for the retained report."""

        return {
            "actionable_users": max(0, int(self.actionable_user_count)),
            "manual_users": len(self.manual_tg_ids),
            "policy_unresolved_users": len(self.unresolved_tg_ids),
            "policy_unresolved_reasons": {
                str(reason): max(0, int(count))
                for reason, count in sorted(self.unresolved_reasons.items())
                if str(reason) and int(count) > 0
            },
        }


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _systemctl_is_active(unit: str) -> str:
    try:
        result = subprocess.run(["systemctl", "is-active", unit], text=True, capture_output=True, timeout=10)
        return (result.stdout or result.stderr).strip() or f"exit_{result.returncode}"
    except Exception as exc:
        return f"error:{str(exc)[:200]}"


def _api_health() -> dict:
    try:
        with urllib.request.urlopen(API_HEALTH_URL, timeout=5) as response:
            body = response.read().decode("utf-8", errors="replace")
        return {"ok": True, "body": json.loads(body)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:300]}


def _panel_tg_id(row: dict) -> int | None:
    raw = str((row or {}).get("tgId") or "").strip()
    if raw.isdigit():
        return int(raw)
    match = re.fullmatch(r"User_(\d+)", str((row or {}).get("email") or "").strip())
    return int(match.group(1)) if match else None


def _panel_managed_identity(row: dict, expected_uuid_to_tg: dict[str, int]) -> int | None:
    tg_id = _panel_tg_id(row)
    if tg_id is not None:
        return tg_id
    client_uuid = str((row or {}).get("id") or "").strip()
    return expected_uuid_to_tg.get(client_uuid) if client_uuid else None


def _panel_client_enabled(row: dict) -> bool:
    raw = (row or {}).get("enable", True)
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return bool(raw)
    return str(raw or "").strip().lower() not in {"0", "false", "no", "off", "disabled"}


def _entitlement_policy_is_ambiguous(user: User) -> bool:
    """Reject compatibility fallbacks that are unsafe as remediation authority."""

    sub_type = str(getattr(user, "sub_type", "") or "").strip().upper()
    plan_code = str(getattr(user, "current_plan_code", "") or "").strip().lower()
    if plan_code in _PREMIUM_PLAN_CODES or sub_type == "FREE":
        return False
    if sub_type in _EXPLICIT_PREMIUM_SUB_TYPES:
        return False
    return not (
        sub_type.startswith("TRIAL")
        or sub_type.startswith("BONUS")
        or sub_type.startswith("PAID_")
        or sub_type.startswith("PREMIUM")
    )


def _free_profile_policy_is_ambiguous(user: User) -> bool:
    active_role = str(getattr(user, "free_profile_active_role", "") or "").strip().lower()
    state = str(getattr(user, "free_profile_state", "") or "").strip().lower()
    if active_role not in {FREE_STANDARD_ROLE, FREE_SOFT_ROLE} or state not in _FREE_PROFILE_STATES:
        return True
    if state in {"standard", "soft_transition_pending"}:
        return active_role != FREE_STANDARD_ROLE
    if state in {"soft_active", "reset_pending"}:
        return active_role != FREE_SOFT_ROLE
    return False


def _expected_codes_for_user(user: User, nodes: list, *, now: datetime) -> tuple[list[str], str | None]:
    """Resolve one active user's exact policy pool or a stable unresolved reason."""

    if _entitlement_policy_is_ambiguous(user):
        return [], "entitlement_ambiguous"
    try:
        uses_free_pool = user_uses_free_pool(user, now=now)
        if uses_free_pool:
            if _free_profile_policy_is_ambiguous(user):
                return [], "free_profile_ambiguous"
            access_role = user_free_access_role(user)
            if access_role not in {FREE_STANDARD_ROLE, FREE_SOFT_ROLE}:
                return [], "free_role_invalid"
            codes = free_pool_node_codes(nodes, access_role=access_role)
            missing_reason = f"{access_role}_pool_missing"
        else:
            codes = paid_pool_node_codes(nodes)
            missing_reason = "paid_pool_missing"
    except (NodeAccessRoleError, TypeError, ValueError):
        return [], "policy_evaluation_failed"

    normalized = sorted({str(code or "").strip() for code in codes if str(code or "").strip()})
    return (normalized, None) if normalized else ([], missing_reason)


async def _panel_rows(
    expected_by_node: dict[str, set[int]],
    expected_uuid_by_node: dict[str, dict[str, int]],
    policy_scope: PolicyIdentityScope | None = None,
) -> list[dict]:
    policy_scope = policy_scope or PolicyIdentityScope()
    panel = ControlPanel()
    try:
        nodes = await panel.refresh()
        semaphore = asyncio.Semaphore(PANEL_HEALTHCHECK_MAX_CONCURRENCY)

        async def panel_row(code: str, client) -> dict:
            # ControlPanel.refresh creates one PanelClient per node code. Each
            # worker uses only that node's client/session and no ORM state.
            try:
                if client is None:
                    return {"node": code, "error": "panel_unavailable"}
                async with semaphore:
                    inbounds = await asyncio.wait_for(
                        client._get_inbounds(),
                        timeout=PANEL_HEALTHCHECK_NODE_TIMEOUT_SECONDS,
                    )
                panel_clients: list[dict] = []
                for inbound in client._selected_inbounds(inbounds, include_disabled=True):
                    settings = client._decode_settings(inbound.get("settings", "{}"))
                    panel_clients.extend(settings.get("clients", []) or [])
                expected_uuid_to_tg = dict(expected_uuid_by_node.get(code, {}))
                known_uuid_to_tg = {
                    **policy_scope.manual_uuid_to_tg,
                    **policy_scope.unresolved_uuid_to_tg,
                    **expected_uuid_to_tg,
                }
                actual = {
                    tg
                    for tg in (_panel_managed_identity(row, known_uuid_to_tg) for row in panel_clients)
                    if tg is not None
                }
                enabled_clients = [row for row in panel_clients if _panel_client_enabled(row)]
                disabled_clients = [row for row in panel_clients if not _panel_client_enabled(row)]
                enabled_actual = {
                    tg
                    for tg in (_panel_managed_identity(row, known_uuid_to_tg) for row in enabled_clients)
                    if tg is not None
                }
                disabled_actual = {
                    tg
                    for tg in (_panel_managed_identity(row, known_uuid_to_tg) for row in disabled_clients)
                    if tg is not None
                }
                expected = set(expected_by_node.get(code, set()))
                manual_enabled = enabled_actual & set(policy_scope.manual_tg_ids)
                manual_disabled = disabled_actual & set(policy_scope.manual_tg_ids)
                unresolved_enabled = enabled_actual & set(policy_scope.unresolved_tg_ids)
                unresolved_disabled = disabled_actual & set(policy_scope.unresolved_tg_ids)
                excluded = set(policy_scope.manual_tg_ids) | set(policy_scope.unresolved_tg_ids)
                enabled_unexpected = enabled_actual - expected - excluded
                disabled_unexpected = disabled_actual - expected - excluded
                return {
                    "node": code,
                    "panel_clients_total": len(panel_clients),
                    "panel_clients_enabled": len(enabled_clients),
                    "panel_clients_disabled": len(disabled_clients),
                    "managed_actual": len(actual),
                    "managed_enabled": len(enabled_actual),
                    "managed_disabled": len(disabled_actual),
                    "expected": len(expected),
                    "missing": len(expected - enabled_actual),
                    "managed_unexpected": len(enabled_unexpected),
                    "managed_actionable_unexpected": len(enabled_unexpected),
                    "managed_unexpected_disabled": len(disabled_unexpected),
                    "managed_manual_enabled": len(manual_enabled),
                    "managed_manual_disabled": len(manual_disabled),
                    "managed_policy_unresolved_enabled": len(unresolved_enabled),
                    "managed_policy_unresolved_disabled": len(unresolved_disabled),
                    "unknown_rows": len(
                        [row for row in panel_clients if _panel_managed_identity(row, known_uuid_to_tg) is None]
                    ),
                    "_unexpected_enabled_identities": sorted(enabled_unexpected),
                }
            except Exception:
                return {"node": code, "error": "panel_unavailable"}

        work = [
            (code, panel._clients.get(code))
            for node in nodes
            if (code := str(getattr(node, "code", "") or "").strip()) and bool(getattr(node, "enabled", True))
        ]
        # gather preserves input order even when panel responses finish out of order.
        return await asyncio.gather(*(panel_row(code, client) for code, client in work))
    finally:
        await panel.close()


def _expected_node_sets(
    now: datetime,
) -> tuple[dict[str, set[int]], dict[str, dict[str, int]], list[dict], PolicyIdentityScope]:
    session = SessionLocal()
    try:
        nodes = enabled_nodes(session)
        active_users = (
            session.query(User)
            .filter(User.tg_id > 0, User.is_active == True, User.expiry_at.isnot(None), User.expiry_at > now)
            .all()
        )
        manual_users = (
            session.query(User)
            .filter(User.tg_id > 0)
            .filter(
                or_(
                    User.is_manual == True,
                    func.upper(func.coalesce(User.sub_type, "")) == "MANUAL",
                    User.created_by_admin.isnot(None),
                )
            )
            .all()
        )
        manual_by_id = {int(user.tg_id): user for user in manual_users}
        candidate_users = [user for user in active_users if int(user.tg_id) not in manual_by_id]
        expected_by_node: dict[str, set[int]] = {}
        expected_uuid_by_node: dict[str, dict[str, int]] = {}
        unresolved_by_id: dict[int, User] = {}
        unresolved_reasons: dict[str, int] = {}
        actionable_user_count = 0

        try:
            validate_node_access_roles(nodes)
            node_policy_valid = True
        except NodeAccessRoleError:
            node_policy_valid = False

        for user in candidate_users:
            target_codes, unresolved_reason = (
                _expected_codes_for_user(user, nodes, now=now)
                if node_policy_valid
                else ([], "node_roles_invalid")
            )
            if unresolved_reason:
                unresolved_by_id[int(user.tg_id)] = user
                unresolved_reasons[unresolved_reason] = unresolved_reasons.get(unresolved_reason, 0) + 1
                continue
            actionable_user_count += 1
            for code in target_codes:
                expected_by_node.setdefault(code, set()).add(int(user.tg_id))
                client_uuid = str(getattr(user, "uuid", "") or "").strip()
                if client_uuid:
                    expected_uuid_by_node.setdefault(code, {})[client_uuid] = int(user.tg_id)

        mapped_counts = {
            str(code): int(count or 0)
            for code, count in (
                session.query(Node.code, func.count(func.distinct(UserNode.tg_id)))
                .join(UserNode, UserNode.node_id == Node.id, isouter=True)
                .group_by(Node.code)
                .all()
            )
        }
        stale_after = timedelta(minutes=max(1, METRICS_STALE_AFTER_MINUTES))
        node_rows: list[dict] = []
        for node in session.query(Node).filter(Node.enabled == True).order_by(Node.code.asc()).all():
            latest = (
                session.query(NodeHealthSample.sampled_at)
                .filter(NodeHealthSample.node_code == node.code)
                .order_by(NodeHealthSample.sampled_at.desc())
                .first()
            )
            latest_at = latest[0] if latest else getattr(node, "last_health_at", None)
            expected_users = len(expected_by_node.get(str(node.code), set()))
            node_rows.append(
                {
                    "code": node.code,
                    "is_healthy": bool(node.is_healthy),
                    "health_score": float(node.health_score or 0.0),
                    "panel_latency_ms": node.panel_latency_ms,
                    "active_clients": int(node.active_clients or 0),
                    "last_health_at": latest_at.isoformat() if latest_at else None,
                    "stale": latest_at is None or (now - latest_at) > stale_after,
                    "mapped_users": mapped_counts.get(str(node.code), 0),
                    "expected_users": expected_users,
                }
            )
        policy_scope = PolicyIdentityScope(
            actionable_user_count=actionable_user_count,
            manual_tg_ids=frozenset(manual_by_id),
            manual_uuid_to_tg={
                client_uuid: tg_id
                for tg_id, user in manual_by_id.items()
                if (client_uuid := str(getattr(user, "uuid", "") or "").strip())
            },
            unresolved_tg_ids=frozenset(unresolved_by_id),
            unresolved_uuid_to_tg={
                client_uuid: tg_id
                for tg_id, user in unresolved_by_id.items()
                if (client_uuid := str(getattr(user, "uuid", "") or "").strip())
            },
            unresolved_reasons=unresolved_reasons,
        )
        return expected_by_node, expected_uuid_by_node, node_rows, policy_scope
    finally:
        session.close()


def _send_telegram_report(text: str) -> None:
    token = os.getenv("BOT_TOKEN", "").strip()
    admin_id = os.getenv("ADMIN_ID", "").strip()
    if not token or not admin_id:
        return
    data = urllib.parse.urlencode({"chat_id": admin_id, "text": text}).encode("utf-8")
    with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data=data, timeout=15) as response:
        response.read()


async def run() -> int:
    now = _utcnow()
    issues: list[str] = []
    report: dict = {"generated_at_utc": now.isoformat(), "checks": {}}

    report["checks"]["api"] = _api_health()
    if not report["checks"]["api"].get("ok"):
        issues.append("api_health_failed")

    timers = {
        "portal-api-healthcheck.timer": _systemctl_is_active("portal-api-healthcheck.timer"),
        "portal-node-metrics.timer": _systemctl_is_active("portal-node-metrics.timer"),
    }
    report["checks"]["timers"] = timers
    issues.extend(f"timer_{unit}_{state}" for unit, state in timers.items() if state != "active")

    expected_by_node, expected_uuid_by_node, node_rows, policy_scope = _expected_node_sets(now)
    report["checks"]["nodes"] = node_rows
    report["checks"]["access_policy"] = policy_scope.public_summary()
    unresolved_user_count = len(policy_scope.unresolved_tg_ids)
    if unresolved_user_count > 0:
        issues.append(f"panel_policy_unresolved_{unresolved_user_count}_users")
    for row in node_rows:
        if row["stale"]:
            issues.append(f"node_{row['code']}_metrics_stale")
        if not row["is_healthy"]:
            issues.append(f"node_{row['code']}_unhealthy")

    panel_rows = await _panel_rows(expected_by_node, expected_uuid_by_node, policy_scope)
    unexpected_enabled_identities: set[int] = set()
    unexpected_enabled_placements = 0
    for row in panel_rows:
        unexpected_enabled_placements += int(
            row.get("managed_actionable_unexpected", row.get("managed_unexpected")) or 0
        )
        unexpected_enabled_identities.update(
            int(value)
            for value in row.pop("_unexpected_enabled_identities", [])
            if str(value).isdigit()
        )
    report["checks"]["panels"] = panel_rows
    for row in panel_rows:
        if row.get("error"):
            issues.append(f"panel_{row.get('node')}_error")
        if int(row.get("missing") or 0) > 0:
            issues.append(f"panel_{row.get('node')}_missing_{row.get('missing')}")
    if unexpected_enabled_placements > 0:
        identity_count = len(unexpected_enabled_identities)
        identity_label = str(identity_count) if identity_count > 0 else "unknown"
        issues.append(
            f"panel_access_drift_enabled_{identity_label}_identities_"
            f"{unexpected_enabled_placements}_placements"
        )

    report["status"] = "ok" if not issues else "warn"
    report["issues"] = sorted(set(issues))
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"panel_node_health_{now.strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    summary = f"POKROV daily health: {report['status']} | issues={len(report['issues'])} | report={report_path}"
    print(summary)
    if report["issues"]:
        print("issues=" + ",".join(report["issues"][:30]))
    try:
        text = summary
        if report["issues"]:
            text += "\n" + "\n".join(f"- {issue}" for issue in report["issues"][:20])
        _send_telegram_report(text)
    except Exception as exc:
        print(f"telegram_report_failed={str(exc)[:200]}")
    return 0 if report["status"] == "ok" else 1


def main() -> int:
    return asyncio.run(run())


if __name__ == "__main__":
    raise SystemExit(main())
