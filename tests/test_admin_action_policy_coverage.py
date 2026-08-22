from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
ADMIN_API_PATH = PORTAL_BOT_DIR / "api_admin_routes.py"
API_ROUTE_PATHS = (
    PORTAL_BOT_DIR / "api.py",
    PORTAL_BOT_DIR / "api_public_routes.py",
    PORTAL_BOT_DIR / "api_client_routes.py",
    PORTAL_BOT_DIR / "api_surface_routes.py",
    ADMIN_API_PATH,
    PORTAL_BOT_DIR / "api_admin_action_routes.py",
    PORTAL_BOT_DIR / "api_admin_network_routes.py",
    PORTAL_BOT_DIR / "api_subscription_routes.py",
)
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


_ADMIN_MUTATION_DECORATOR = re.compile(
    r'^\s*@app\.(post|put|patch|delete)\("(/api/admin[^"?]*)"\)\s*$'
)
_INTENT_CONTROL_ROUTE = ("POST", "/api/admin/action-intents")


def discover_admin_mutation_routes(source: str) -> set[tuple[str, str]]:
    routes = {
        (match.group(1).upper(), match.group(2))
        for line in source.splitlines()
        if (match := _ADMIN_MUTATION_DECORATOR.fullmatch(line)) is not None
    }
    # This endpoint creates guard metadata; it cannot recursively require an intent.
    routes.discard(_INTENT_CONTROL_ROUTE)
    return routes


def test_every_admin_mutation_is_guarded_or_explicitly_low_risk() -> None:
    from admin_action_intent_service import action_policy_route_keys

    mutations = set().union(
        *(
            discover_admin_mutation_routes(path.read_text(encoding="utf-8"))
            for path in API_ROUTE_PATHS
        )
    )
    exempt = {
        ("POST", "/api/admin/auth/session"),
        ("POST", "/api/admin/alerts/{alert_id}/silence"),
        ("POST", "/api/admin/campaign-links/build"),
        # Content-addressed, bounded, admin-authenticated and independently audited;
        # an identical upload is an idempotent no-op and cannot replace another asset.
        ("POST", "/api/admin/promo-media"),
    }
    audited_l1: set[tuple[str, str]] = set()
    domain_confirmed: set[tuple[str, str]] = set()
    guarded = set(action_policy_route_keys())

    assert ("POST", "/api/admin/broadcast") in guarded
    assert mutations == guarded | exempt | audited_l1 | domain_confirmed


def test_confirmed_mutations_keep_their_intent_and_domain_guards() -> None:
    source = ADMIN_API_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    handlers = {
        node.name: ast.get_source_segment(source, node) or ""
        for node in tree.body
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef))
    }

    for handler_name in (
        "admin_service_incident_create",
        "admin_service_incident_resolve",
        "admin_service_incident_compensate",
        "admin_ops_alert_ack",
    ):
        assert "_execute_admin_guarded_action(" in handlers[handler_name]

    compensation = handlers["admin_service_incident_compensate"]
    assert "payload.dry_run" in compensation

    review = handlers["admin_program_application_review"]
    assert "_execute_admin_guarded_action(" in review
    assert 'action="program_application.review"' in review
    assert "int(payload.reward_days or 0) > 0" in review
    assert "secrets.compare_digest(" in review
    assert "payload.confirm_application_id" in review


def test_broadcast_non_dry_run_invokes_action_intent_guard() -> None:
    tree = ast.parse(ADMIN_API_PATH.read_text(encoding="utf-8"))
    handler = next(
        node
        for node in tree.body
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef))
        and node.name == "admin_broadcast"
    )
    non_dry_branch = next(
        node
        for node in handler.body
        if isinstance(node, ast.If)
        and ast.unparse(node.test) == "not bool(payload.dry_run)"
    )

    guarded_calls = [
        node
        for node in ast.walk(non_dry_branch)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_execute_admin_guarded_action"
    ]
    assert len(guarded_calls) == 1


def test_remaining_write_families_have_exact_l2_l3_contracts() -> None:
    from admin_action_intent_service import ACTION_POLICIES

    expected_l3 = {
        "plan.delete": "exact_plan_code",
        "live_update.delete": "exact_live_update_id",
        "start_link.delete": "exact_start_link_id",
        "warp_material.replace": "exact_tg_id",
        "awg2_lab_material.replace": "exact_tg_id",
        "campaign.delete": "exact_campaign_id",
        "template.delete": "exact_template_key",
        "access_key.issue": "exact_plan_code",
        "gift_code.create": "exact_card_type",
        "node.sync_global": "exact_phrase",
    }
    expected_l2 = {
        "plan.create",
        "plan.update",
        "live_update.create",
        "live_update.update",
        "start_link.create",
        "start_link.update",
        "wheel_config.update",
        "network_rollout_config.update",
        "promo_slots.update",
        "loyalty_config.update",
        "campaign.create",
        "campaign.update",
        "template.create",
        "template.update",
    }

    assert {
        action: ACTION_POLICIES[action].challenge_kind
        for action in expected_l3
        if ACTION_POLICIES[action].risk_level == "L3"
    } == expected_l3
    assert {
        action
        for action in expected_l2
        if ACTION_POLICIES[action].risk_level == "L2"
        and ACTION_POLICIES[action].challenge_kind == "exact_phrase"
    } == expected_l2
