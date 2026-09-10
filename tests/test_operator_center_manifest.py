from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
ADMINAPP = ROOT / "adminapp"
MANIFEST_PATH = ADMINAPP / "operator-center.manifest.json"
CUTOVER_PATH = ADMINAPP / "operator-center.cutover.json"


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_operator_center_manifest_freezes_one_canonical_destination() -> None:
    manifest = _manifest()
    assert manifest["schema"] == "pokrov-operator-center-manifest-v1"
    assert manifest["app"] == "pokrov-operator-center"
    assert manifest["canonical_domain"] == "admin.pokrov.space"
    assert manifest["expected_api_schema"] == "admin-v2.1"
    assert manifest["implementation_state"] == "local-capability-parity-cutover-gated"
    assert manifest["cutover_matrix"] == CUTOVER_PATH.name
    assert manifest["legacy_policy"] == {
        "adminapp": "canonical-v2-local-parity",
        "webapp_admin": "compatibility-source-no-new-features",
        "public_legacy_shell": "remove-only-after-authenticated-cutover-proof",
        "write_strategy": "single-domain-action-intent-no-dual-write",
    }

    workspaces = manifest["workspaces"]
    assert [item["id"] for item in workspaces] == [
        "shift",
        "support",
        "network",
        "money",
        "growth",
        "releases",
        "governance",
    ]
    assert len({item["path"] for item in workspaces}) == 7


def test_operator_center_route_inventory_contains_workspaces_and_frozen_legacy_routes() -> None:
    manifest = _manifest()
    routes = manifest["routes"]
    assert {item["path"] for item in routes} == {
        "/",
        "/shift",
        "/support",
        "/network",
        "/money",
        "/growth",
        "/releases",
        "/governance",
        "/nodes",
        "/traffic",
        "/alerts",
        "/incidents",
        "/provider-caps",
        "/emergency-network",
        "/free-tier",
        "/access",
        "/users",
        "/online",
        "/tickets",
        "/payments",
        "/funnel",
        "/promos",
        "/bonuses",
        "/programs",
        "/referrals",
        "/release",
        "/broadcast",
        "/news",
    }
    workspace_routes = [item for item in routes if item["state"] == "workspace-route-active"]
    legacy_routes = [item for item in routes if item["state"] == "legacy-route-active"]
    operator_work_routes = [item for item in routes if item["state"] == "operator-work-route-active"]
    support_work_routes = [item for item in routes if item["state"] == "support-work-v2-active"]
    network_work_routes = [item for item in routes if item["state"] == "network-work-v2-active"]
    money_work_routes = [item for item in routes if item["state"] == "money-work-v2-active"]
    growth_access_routes = [item for item in routes if item["state"] == "growth-access-v2-active"]
    growth_messaging_routes = [item for item in routes if item["state"] == "growth-messaging-v2-active"]
    release_work_routes = [item for item in routes if item["state"] == "release-work-v2-active"]
    governance_work_routes = [item for item in routes if item["state"] == "governance-work-v2-active"]
    shift_overview_routes = [item for item in routes if item["state"] == "shift-overview-v2-active"]
    growth_work_routes = [item for item in routes if item["state"] == "growth-work-v2-active"]
    assert len(workspace_routes) == 6
    assert legacy_routes == []
    assert shift_overview_routes == [
        {"path": "/", "capability": "overview", "workspace": "shift", "state": "shift-overview-v2-active"}
    ]
    assert operator_work_routes == [
        {"path": "/incidents", "capability": "incident-room", "workspace": "network", "state": "operator-work-route-active"}
    ]
    assert support_work_routes == [
        {"path": "/users", "capability": "users", "workspace": "support", "state": "support-work-v2-active"},
        {"path": "/online", "capability": "online", "workspace": "support", "state": "support-work-v2-active"},
        {"path": "/tickets", "capability": "tickets", "workspace": "support", "state": "support-work-v2-active"},
    ]
    assert network_work_routes == [
        {"path": "/nodes", "capability": "nodes", "workspace": "network", "state": "network-work-v2-active"},
        {"path": "/traffic", "capability": "traffic", "workspace": "network", "state": "network-work-v2-active"},
        {"path": "/alerts", "capability": "alerts", "workspace": "network", "state": "network-work-v2-active"},
        {"path": "/provider-caps", "capability": "provider-caps", "workspace": "network", "state": "network-work-v2-active"},
        {"path": "/emergency-network", "capability": "emergency-network", "workspace": "network", "state": "network-work-v2-active"},
    ]
    assert money_work_routes == [
        {"path": "/free-tier", "capability": "free-archive", "workspace": "money", "state": "money-work-v2-active"},
        {"path": "/access", "capability": "access-entitlements", "workspace": "money", "state": "money-work-v2-active"},
        {"path": "/payments", "capability": "payments", "workspace": "money", "state": "money-work-v2-active"},
        {"path": "/promos", "capability": "promocodes", "workspace": "money", "state": "money-work-v2-active"},
    ]
    assert growth_access_routes == [
        {"path": "/bonuses", "capability": "bonuses", "workspace": "growth", "state": "growth-access-v2-active"},
        {"path": "/programs", "capability": "program-applications", "workspace": "growth", "state": "growth-access-v2-active"},
    ]
    assert growth_messaging_routes == [
        {"path": "/broadcast", "capability": "broadcasts", "workspace": "growth", "state": "growth-messaging-v2-active"},
        {"path": "/news", "capability": "news", "workspace": "growth", "state": "growth-messaging-v2-active"},
    ]
    assert growth_work_routes == [
        {"path": "/funnel", "capability": "funnel", "workspace": "growth", "state": "growth-work-v2-active"},
        {"path": "/referrals", "capability": "referrals", "workspace": "growth", "state": "growth-work-v2-active"},
    ]
    assert release_work_routes == [
        {"path": "/release", "capability": "release", "workspace": "releases", "state": "release-work-v2-active"}
    ]
    assert governance_work_routes == [
        {"path": "/governance", "capability": "workspace-governance", "workspace": "governance", "state": "governance-work-v2-active"}
    ]
    assert {item["workspace"] for item in workspace_routes + governance_work_routes} == {
        "shift",
        "support",
        "network",
        "money",
        "growth",
        "releases",
        "governance",
    }
    assert manifest["unique_legacy_capabilities"] == []


def test_operator_center_cutover_matrix_covers_every_route_and_keeps_external_gates_closed() -> None:
    manifest = _manifest()
    cutover = json.loads(CUTOVER_PATH.read_text(encoding="utf-8"))
    assert cutover["schema"] == "pokrov-operator-center-cutover-v1"
    assert cutover["candidate_id"] == "NOT_CREATED"
    summary = cutover["local_parity"]
    assert summary == {
        "status": "PASS",
        "route_count": 28,
        "workspace_count": 7,
        "capability_group_count": 7,
        "legacy_route_state_count": 0,
        "browser_v2_projection_count": 4,
        "browser_legacy_read_pattern_count": 7,
        "direct_domain_dual_write_count": 0,
    }
    covered_routes = {
        route
        for capability in cutover["capabilities"]
        for route in capability["routes"]
    }
    assert covered_routes == {route["path"] for route in manifest["routes"]}
    assert all(capability["status"] == "LOCALLY_PROVED" for capability in cutover["capabilities"])
    assert all(capability["actions"] for capability in cutover["capabilities"])
    assert all(capability["redaction_check"] for capability in cutover["capabilities"])
    assert cutover["legacy_runtime"]["new_features_allowed"] is False
    assert cutover["cutover_gates"] == {
        "canonical_redirects": "BLOCKED_BY_EXACT_CANDIDATE_AUTHENTICATED_PROOF",
        "public_legacy_shell_removal": "BLOCKED_BY_EXACT_CANDIDATE_AUTHENTICATED_PROOF",
        "authenticated_staging_smoke": "BLOCKED_BY_ACCESS",
        "authenticated_production_smoke": "BLOCKED_BY_ACCESS",
        "exact_build_api_fingerprints": "BLOCKED_BY_CANDIDATE",
        "production_static_rollback": "BLOCKED_BY_CANDIDATE",
        "local_static_rollback_rehearsal": "READY",
    }


def test_admin_build_contract_generator_emits_exact_identity(tmp_path: Path) -> None:
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is required for the adminapp build contract")
    output_dir = tmp_path / "operator-build"
    env = dict(os.environ)
    env.update(
        {
            "POKROV_ADMIN_FRONTEND_COMMIT": "a" * 40,
            "POKROV_ADMIN_SOURCE_STATE": "clean",
            "POKROV_ADMIN_BUILT_AT": "2026-08-21T12:00:00Z",
        }
    )
    completed = subprocess.run(
        [node, str(ADMINAPP / "scripts" / "generate-build-contract.mjs"), "--out-dir", str(output_dir)],
        cwd=ADMINAPP,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr

    manifest = _manifest()
    expected_hash = hashlib.sha256(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    cutover = json.loads(CUTOVER_PATH.read_text(encoding="utf-8"))
    expected_cutover_hash = hashlib.sha256(
        json.dumps(cutover, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    build = json.loads((output_dir / "__build.json").read_text(encoding="utf-8"))
    routes = json.loads((output_dir / "__routes.json").read_text(encoding="utf-8"))
    assert build == {
        "schema": "pokrov-operator-build-v1",
        "app": "pokrov-operator-center",
        "version": "0.1.0",
        "frontend_commit": "a" * 40,
        "built_at": "2026-08-21T12:00:00Z",
        "source_state": "clean",
        "route_manifest_hash": expected_hash,
        "cutover_matrix_hash": expected_cutover_hash,
        "expected_api_schema": "admin-v2.1",
        "canonical_domain": "admin.pokrov.space",
    }
    assert routes["schema"] == "pokrov-operator-route-manifest-v1"
    assert routes["app"] == "pokrov-operator-center"
    assert routes["manifest_hash"] == expected_hash
    assert routes["cutover_matrix_hash"] == expected_cutover_hash
    assert routes["local_parity"] == cutover["local_parity"]
    assert routes["cutover_gates"] == cutover["cutover_gates"]
    assert len(routes["workspaces"]) == 7


def test_guardrail_requires_adminapp_candidate() -> None:
    workflow = (ROOT / ".github" / "workflows" / "guardrails.yml").read_text(encoding="utf-8")
    package = json.loads((ADMINAPP / "package.json").read_text(encoding="utf-8"))
    assert "adminapp/package-lock.json" in workflow
    assert "Install adminapp dependencies" in workflow
    assert "Validate canonical adminapp candidate" in workflow
    assert "npm run lint" in workflow
    assert "npm run build" in workflow
    assert "npm run verify:cutover" in workflow
    assert "npm run test:e2e" in workflow
    assert package["scripts"]["prebuild"] == "npm run check:sdk && npm run build:contract"
    assert package["scripts"]["verify:cutover"] == "node scripts/verify-cutover.mjs"


def test_operator_v2_browser_auth_uses_cookie_and_memory_only() -> None:
    client_source = (ADMINAPP / "src" / "lib" / "admin-api" / "client.ts").read_text(encoding="utf-8")
    boundary_source = (ADMINAPP / "src" / "components" / "ops" / "route-boundary.tsx").read_text(
        encoding="utf-8"
    )
    intent_source = (ADMINAPP / "src" / "components" / "ops" / "action-intent-dialog.tsx").read_text(
        encoding="utf-8"
    )
    router_source = (ROOT / "portal_bot" / "admin_v2" / "router.py").read_text(encoding="utf-8")

    assert "/api/admin/v2/auth/me" in client_source
    assert "/api/admin/v2/auth/oidc/start" in client_source
    assert "/api/admin/v2/auth/oidc/finish" in client_source
    assert "/api/admin/v2/auth/bootstrap" in client_source
    assert 'credentials: "include"' in client_source
    assert "X-Pokrov-Admin-CSRF" in client_source
    assert "localStorage?.getItem" not in client_source
    assert "sessionStorage?.getItem" not in client_source
    assert 'headers.set("Authorization"' not in client_source
    assert "X-Web-Auth-Token" not in client_source
    assert "/api/admin/auth/session" not in client_source
    assert "Telegram WebApp initData" not in boundary_source
    assert "<textarea" not in boundary_source
    assert "bootstrap_slice" not in router_source
    assert 'startAdminOidc("step_up")' in intent_source
    assert "operator_step_up_required" in intent_source
    assert "__Host-pokrov_admin_session" in (ROOT / "portal_bot" / "admin_v2" / "security.py").read_text(
        encoding="utf-8"
    )


def test_operator_v2_every_route_has_an_explicit_permission() -> None:
    portal_bot = ROOT / "portal_bot"
    if str(portal_bot) not in sys.path:
        sys.path.insert(0, str(portal_bot))

    from admin_v2.roles import PERMISSIONS
    from admin_v2.router import ROUTE_PERMISSIONS

    assert ROUTE_PERMISSIONS == {
        "GET /auth/oidc/start": "session.bootstrap",
        "POST /auth/oidc/finish": "session.bootstrap",
        "POST /auth/bootstrap": "session.bootstrap",
        "GET /auth/me": "session.self.read",
        "GET /auth/sessions": "session.self.read",
        "POST /auth/sessions/{session_id}/revoke": "session.self.revoke",
        "POST /auth/step-up": "session.step_up",
        "POST /auth/logout": "session.self.revoke",
        "GET /meta": "system.meta.read",
        "GET /shift": "shift.read",
        "GET /shift/overview": "shift.read",
        "GET /tasks": "shift.read",
        "POST /shift/action-intents": "shift.manage",
        "POST /shift/action-intents/{intent_id}/execute": "shift.manage",
        "GET /incidents": "incident.read",
        "GET /incidents/{incident_id}": "incident.read",
        "POST /incidents/action-intents": "incident.manage",
        "POST /incidents/action-intents/{intent_id}/execute": "incident.manage",
        "GET /support/tickets": "support.read",
        "GET /support/tickets/{ticket_id}": "support.read",
        "GET /support/macros": "support.read",
        "GET /support/users/{tg_id}": "support.read",
        "GET /support/attempts": "support.sensitive.read",
        "GET /support/search": "support.read",
        "GET /support/known-issues": "support.read",
        "GET /support/diagnostic-codes/{code}": "support.read",
        "POST /support/tickets/{ticket_id}/bundles/{bundle_ref}/access-grants": "support.sensitive.read",
        "GET /support/tickets/{ticket_id}/bundles/{bundle_ref}/content": "support.sensitive.read",
        "GET /support/online": "support.read",
        "POST /support/action-intents": "support.write",
        "POST /support/action-intents/{intent_id}/execute": "support.write",
        "GET /network/fleet": "network.read",
        "GET /network/nodes/{node_code}": "network.read",
        "GET /network/traffic": "network.read",
        "GET /network/alerts": "network.read",
        "GET /network/providers": "network.read",
        "GET /network/ru/latest": "network.read",
        "GET /network/ru/runs": "network.read",
        "GET /network/ru/uploader": "network.read",
        "GET /network/emergency": "network.read",
        "POST /network/action-intents": "network.write",
        "POST /network/action-intents/{intent_id}/execute": "network.write",
        "GET /money/payments/summary": "money.read",
        "GET /money/payments/orders": "money.read",
        "GET /money/payments/orders/{provider}/{order_id}": "money.read",
        "GET /money/access": "money.read",
        "GET /money/free-archive": "money.read",
        "GET /money/promos": "money.read",
        "POST /money/action-intents": "money.write",
        "POST /money/action-intents/{intent_id}/execute": "money.write",
        "GET /growth/bonuses": "growth.read",
        "GET /growth/programs": "growth.read",
        "GET /growth/funnel": "growth.read",
        "GET /growth/referrals": "growth.read",
        "GET /growth/broadcasts/{intent_id}/delivery": "growth.read",
        "GET /growth/news-drafts": "growth.read",
        "GET /growth/live-updates": "growth.read",
        "GET /growth/action-intents/{intent_id}": "growth.read",
        "POST /growth/action-intents": "growth.write",
        "POST /growth/action-intents/{intent_id}/execute": "growth.write",
        "GET /releases/candidates": "releases.read",
        "GET /releases/candidates/{candidate_id}/cockpit": "releases.read",
        "GET /releases/adoption": "releases.read",
        "POST /releases/action-intents": "releases.write",
        "POST /releases/action-intents/{intent_id}/execute": "releases.write",
        "GET /governance/roles": "governance.operators.read",
        "GET /governance/operators": "governance.operators.read",
        "GET /governance/operators/{operator_id}": "governance.operators.read",
        "GET /governance/audit": "governance.audit.read",
        "GET /governance/audit/export": "governance.audit.read",
        "GET /governance/audit/commands/{intent_id}": "governance.audit.read",
        "GET /governance/sensitive-access": "governance.audit.read",
        "GET /governance/privacy": "governance.sources.read",
        "POST /governance/action-intents": "governance.operators.manage",
        "POST /governance/action-intents/{intent_id}/execute": "governance.operators.manage",
    }
    assert set(ROUTE_PERMISSIONS.values()) <= PERMISSIONS
    assert all("*" not in permission for permission in ROUTE_PERMISSIONS.values())


def test_support_bundle_access_is_role_separated_and_step_up_capable() -> None:
    portal_bot = ROOT / "portal_bot"
    if str(portal_bot) not in sys.path:
        sys.path.insert(0, str(portal_bot))

    from admin_v2.roles import ROLE_REGISTRY

    assert "support.sensitive.read" not in ROLE_REGISTRY["support_l1"]
    for role in ("support_l2", "sre", "security_auditor"):
        assert "support.sensitive.read" in ROLE_REGISTRY[role]
        assert "session.step_up" in ROLE_REGISTRY[role]
