from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
API_PATH = REPO_ROOT / "portal_bot" / "api.py"
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
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

    mutations = discover_admin_mutation_routes(API_PATH.read_text(encoding="utf-8"))
    exempt = {
        ("POST", "/api/admin/auth/session"),
        ("POST", "/api/admin/alerts/{alert_id}/ack"),
        ("POST", "/api/admin/alerts/{alert_id}/silence"),
        ("POST", "/api/admin/campaign-links/build"),
    }
    guarded = set(action_policy_route_keys())

    assert ("POST", "/api/admin/broadcast") in guarded
    assert mutations == guarded | exempt


def test_broadcast_non_dry_run_invokes_action_intent_guard() -> None:
    tree = ast.parse(API_PATH.read_text(encoding="utf-8"))
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
