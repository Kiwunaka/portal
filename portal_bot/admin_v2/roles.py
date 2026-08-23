"""Static role registry for the deny-by-default Operator Center boundary."""

from __future__ import annotations

from collections.abc import Iterable


PERMISSIONS = frozenset(
    {
        "system.meta.read",
        "session.self.read",
        "session.self.revoke",
        "session.bootstrap",
        "session.step_up",
        "legacy.admin.access",
        "shift.read",
        "shift.manage",
        "support.read",
        "support.write",
        "support.sensitive.read",
        "network.read",
        "network.write",
        "incident.read",
        "incident.manage",
        "money.read",
        "money.write",
        "growth.read",
        "growth.write",
        "releases.read",
        "releases.write",
        "governance.operators.read",
        "governance.operators.manage",
        "governance.audit.read",
        "governance.sources.read",
        "command.high_risk",
    }
)


ROLE_REGISTRY: dict[str, frozenset[str]] = {
    "readonly": frozenset(
        {
            "system.meta.read",
            "session.self.read",
            "session.self.revoke",
            "shift.read",
        }
    ),
    "support_l1": frozenset(
        {
            "system.meta.read",
            "session.self.read",
            "session.self.revoke",
            "shift.read",
            "shift.manage",
            "support.read",
            "support.write",
        }
    ),
    "support_l2": frozenset(
        {
            "system.meta.read",
            "session.self.read",
            "session.self.revoke",
            "session.step_up",
            "shift.read",
            "shift.manage",
            "support.read",
            "support.write",
            "support.sensitive.read",
            "incident.read",
        }
    ),
    "sre": frozenset(
        {
            "system.meta.read",
            "session.self.read",
            "session.self.revoke",
            "session.step_up",
            "shift.read",
            "shift.manage",
            "support.read",
            "support.write",
            "support.sensitive.read",
            "network.read",
            "network.write",
            "incident.read",
            "incident.manage",
            "releases.read",
            "governance.sources.read",
            "command.high_risk",
        }
    ),
    "network_operator": frozenset(
        {
            "system.meta.read",
            "session.self.read",
            "session.self.revoke",
            "session.step_up",
            "shift.read",
            "shift.manage",
            "network.read",
            "network.write",
            "incident.read",
            "command.high_risk",
        }
    ),
    "payments_operator": frozenset(
        {
            "system.meta.read",
            "session.self.read",
            "session.self.revoke",
            "session.step_up",
            "shift.read",
            "shift.manage",
            "money.read",
            "money.write",
            "incident.read",
            "command.high_risk",
        }
    ),
    "growth_operator": frozenset(
        {
            "system.meta.read",
            "session.self.read",
            "session.self.revoke",
            "session.step_up",
            "shift.read",
            "shift.manage",
            "growth.read",
            "growth.write",
            "command.high_risk",
        }
    ),
    "release_manager": frozenset(
        {
            "system.meta.read",
            "session.self.read",
            "session.self.revoke",
            "session.step_up",
            "shift.read",
            "shift.manage",
            "releases.read",
            "releases.write",
            "network.read",
            "governance.sources.read",
            "command.high_risk",
        }
    ),
    "security_auditor": frozenset(
        {
            "session.step_up",
            "system.meta.read",
            "session.self.read",
            "session.self.revoke",
            "shift.read",
            "support.read",
            "support.sensitive.read",
            "governance.operators.read",
            "governance.audit.read",
            "governance.sources.read",
        }
    ),
    "incident_commander": frozenset(
        {
            "system.meta.read",
            "session.self.read",
            "session.self.revoke",
            "session.step_up",
            "shift.read",
            "shift.manage",
            "support.read",
            "network.read",
            "incident.read",
            "incident.manage",
            "releases.read",
            "command.high_risk",
        }
    ),
    "superadmin": PERMISSIONS,
}


def permissions_for_roles(role_codes: Iterable[str]) -> frozenset[str]:
    permissions: set[str] = set()
    for role_code in role_codes:
        permissions.update(ROLE_REGISTRY.get(str(role_code), frozenset()))
    return frozenset(permissions)


def validate_role_registry() -> None:
    if not ROLE_REGISTRY:
        raise RuntimeError("Admin v2 role registry is empty")
    unknown = {
        permission
        for role_permissions in ROLE_REGISTRY.values()
        for permission in role_permissions
        if permission not in PERMISSIONS
    }
    if unknown:
        raise RuntimeError(f"Admin v2 role registry has unknown permissions: {sorted(unknown)}")
    if ROLE_REGISTRY.get("superadmin") != PERMISSIONS:
        raise RuntimeError("Admin v2 superadmin must enumerate every permission")


validate_role_registry()
