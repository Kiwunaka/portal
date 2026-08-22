import importlib
import sys
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT = ROOT / "portal_bot"


def test_composition_roots_and_slices_stay_bounded() -> None:
    expected = {
        "api.py": 10_000,
        "bot.py": 6_000,
        "api_public_routes.py": 2_500,
        "api_client_routes.py": 4_500,
        "api_commercial_offer_routes.py": 500,
        "api_payment_routes.py": 700,
        "api_observability_routes.py": 500,
        "api_support_bundle_routes.py": 700,
        "api_operator_observability_routes.py": 500,
        "api_surface_routes.py": 7_000,
        "api_admin_routes.py": 4_500,
        "api_admin_action_routes.py": 3_000,
        "api_admin_network_routes.py": 500,
        "api_subscription_routes.py": 7_000,
        "admin_action_intent_service.py": 7_000,
        "admin_action_intent_runtime.py": 2_300,
        "bot_user_handlers.py": 7_000,
        "bot_admin_handlers.py": 7_000,
        "bot_payment_handlers.py": 7_000,
        "bot_operator_handlers.py": 7_000,
    }

    for filename, limit in expected.items():
        path = PORTAL_BOT / filename
        line_count = len(path.read_text(encoding="utf-8-sig").splitlines())
        assert line_count <= limit, (
            f"{filename} grew to {line_count} lines (limit {limit})"
        )

    api_source = (PORTAL_BOT / "api.py").read_text(encoding="utf-8-sig")
    bot_source = (PORTAL_BOT / "bot.py").read_text(encoding="utf-8-sig")
    for module_name in (
        "api_public_routes",
        "api_client_routes",
        "api_commercial_offer_routes",
        "api_payment_routes",
        "api_observability_routes",
        "api_support_bundle_routes",
        "api_operator_observability_routes",
        "api_surface_routes",
        "api_admin_routes",
        "api_admin_action_routes",
        "api_admin_network_routes",
        "api_subscription_routes",
    ):
        assert module_name in api_source
    for module_name in (
        "bot_user_handlers",
        "bot_admin_handlers",
        "bot_payment_handlers",
        "bot_operator_handlers",
    ):
        assert module_name in bot_source


def test_action_intent_runtime_has_one_explicit_policy_owner() -> None:
    service_source = (PORTAL_BOT / "admin_action_intent_service.py").read_text(
        encoding="utf-8-sig"
    )
    runtime_source = (PORTAL_BOT / "admin_action_intent_runtime.py").read_text(
        encoding="utf-8-sig"
    )

    assert "ACTION_POLICIES" not in runtime_source
    assert "from admin_action_intent_service" not in runtime_source
    assert service_source.count("ACTION_POLICIES: dict[str, ActionPolicy] =") == 1
    assert service_source.count("policies=ACTION_POLICIES") == 2
    assert runtime_source.count("policies: Mapping[str, ActionPolicy]") == 4
    assert "it does not register actions or HTTP routes" in runtime_source


def test_public_and_client_routes_preserve_order_without_duplication() -> None:
    api_source = (PORTAL_BOT / "api.py").read_text(encoding="utf-8-sig")
    public_source = (PORTAL_BOT / "api_public_routes.py").read_text(
        encoding="utf-8-sig"
    )
    client_source = (PORTAL_BOT / "api_client_routes.py").read_text(
        encoding="utf-8-sig"
    )

    assert (
        api_source.index('f"{_slice_prefix}api_public_routes"')
        < api_source.index('f"{_slice_prefix}api_client_routes"')
        < api_source.index('f"{_slice_prefix}api_commercial_offer_routes"')
    )

    for route in (
        "/api/health",
        "/api/public/catalog",
        "/api/auth/email/login",
        "/api/client/session/start-trial",
        "/api/client/route-policy",
    ):
        assert route in public_source
        assert route not in client_source

    for route in (
        "/api/client/locations",
        "/api/client/subscription",
        "/api/client/profile/managed",
        "/api/client/nodes/select",
        "/api/client/warp/status",
        "/api/client/telegram/link",
        "/api/public/promo-media/{asset_id}",
    ):
        assert route in client_source
        assert route not in public_source


def test_admin_action_and_network_routes_preserve_order_without_duplication() -> None:
    api_source = (PORTAL_BOT / "api.py").read_text(encoding="utf-8-sig")
    admin_source = (PORTAL_BOT / "api_admin_routes.py").read_text(encoding="utf-8-sig")
    action_source = (PORTAL_BOT / "api_admin_action_routes.py").read_text(
        encoding="utf-8-sig"
    )
    network_source = (PORTAL_BOT / "api_admin_network_routes.py").read_text(
        encoding="utf-8-sig"
    )

    assert (
        api_source.index('f"{_slice_prefix}api_admin_routes"')
        < api_source.index('f"{_slice_prefix}api_admin_action_routes"')
        < api_source.index('f"{_slice_prefix}api_admin_network_routes"')
        < api_source.index('f"{_slice_prefix}api_subscription_routes"')
    )

    for route in (
        "/api/admin/action-intents",
        "/api/admin/action-intents/{intent_id}",
    ):
        assert route in action_source
        assert route not in admin_source
        assert route not in network_source

    for route in (
        "/api/admin/emergency-network/status",
        "/api/admin/emergency-network/stage",
        "/api/admin/emergency-network/snapshots/{snapshot_id}/promote",
        "/api/admin/emergency-network/snapshots/{snapshot_id}/disable",
        "/api/admin/emergency-network/snapshots/{snapshot_id}/rollback",
        "/api/admin/nodes/{node_code}/disable",
        "/api/admin/nodes/{node_code}/resync",
    ):
        assert route in network_source
        assert route not in admin_source
        assert route not in action_source


def test_slice_runtime_reexports_cross_slice_symbols_and_mirrors_patches(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.syspath_prepend(str(PORTAL_BOT))
    monkeypatch.syspath_prepend(str(tmp_path))
    runtime = importlib.import_module("module_slices")

    owner_name = "_pokrov_slice_contract_owner"
    first_name = "_pokrov_slice_contract_first"
    second_name = "_pokrov_slice_contract_second"
    for name in (owner_name, first_name, second_name):
        monkeypatch.delitem(sys.modules, name, raising=False)

    (tmp_path / f"{first_name}.py").write_text(
        "from module_slices import bootstrap_slice\n"
        "bootstrap_slice(globals())\n"
        "def read_shared():\n"
        "    return shared\n",
        encoding="utf-8",
    )
    (tmp_path / f"{second_name}.py").write_text(
        "from module_slices import bootstrap_slice\n"
        "bootstrap_slice(globals())\n"
        "def read_through_first():\n"
        "    return read_shared()\n",
        encoding="utf-8",
    )

    owner = ModuleType(owner_name)
    owner.shared = "first"
    monkeypatch.setitem(sys.modules, owner_name, owner)

    loaded = runtime.load_slices(vars(owner), (first_name, second_name))

    assert len(loaded) == 2
    assert owner.read_shared() == "first"
    assert owner.read_through_first() == "first"

    owner.shared = "patched"
    assert owner.read_shared() == "patched"
    assert owner.read_through_first() == "patched"

    reloaded = runtime.load_slices(vars(owner), (first_name, second_name))
    assert len(reloaded) == 2
    assert owner.read_through_first() == "patched"


def test_stale_owner_cleanup_cannot_mutate_replacement_slices(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.syspath_prepend(str(PORTAL_BOT))
    monkeypatch.syspath_prepend(str(tmp_path))
    runtime = importlib.import_module("module_slices")

    owner_name = "_pokrov_slice_replacement_owner"
    slice_name = "_pokrov_slice_replacement"
    monkeypatch.delitem(sys.modules, owner_name, raising=False)
    monkeypatch.delitem(sys.modules, slice_name, raising=False)
    (tmp_path / f"{slice_name}.py").write_text(
        "from module_slices import bootstrap_slice\n"
        "bootstrap_slice(globals())\n"
        "def read_shared():\n"
        "    return shared\n",
        encoding="utf-8",
    )

    stale_owner = ModuleType(owner_name)
    stale_owner.shared = "stale"
    monkeypatch.setitem(sys.modules, owner_name, stale_owner)
    runtime.load_slices(vars(stale_owner), (slice_name,))

    replacement = ModuleType(owner_name)
    replacement.shared = "current"
    monkeypatch.setitem(sys.modules, owner_name, replacement)
    runtime.load_slices(vars(replacement), (slice_name,))
    assert replacement.read_shared() == "current"

    stale_owner.shared = "late-cleanup"
    assert replacement.read_shared() == "current"


def test_restored_stale_slice_cannot_hide_a_registered_export(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.syspath_prepend(str(PORTAL_BOT))
    monkeypatch.syspath_prepend(str(tmp_path))
    runtime = importlib.import_module("module_slices")

    owner_name = "_pokrov_restored_slice_owner"
    slice_name = "_pokrov_restored_slice"
    monkeypatch.delitem(sys.modules, owner_name, raising=False)
    monkeypatch.delitem(sys.modules, slice_name, raising=False)
    (tmp_path / f"{slice_name}.py").write_text(
        "from module_slices import bootstrap_slice\n"
        "bootstrap_slice(globals())\n"
        "def exported_helper():\n"
        "    return 'current'\n",
        encoding="utf-8",
    )

    owner = ModuleType(owner_name)
    monkeypatch.setitem(sys.modules, owner_name, owner)
    registered = runtime.load_slices(vars(owner), (slice_name,))[0]
    assert owner.exported_helper() == "current"

    # Simulate a test fixture restoring an older slice object after the loader
    # registry already owns a newer one. The stale object sees the current owner
    # export during bootstrap and therefore cannot identify it as its own.
    monkeypatch.delitem(sys.modules, slice_name)
    stale = importlib.import_module(slice_name)
    assert stale is not registered
    assert not hasattr(stale, "_SLICE_OWN_NAMES")
    assert stale.exported_helper() == "current"

    runtime.load_slices(vars(owner), (slice_name,))
    assert owner.exported_helper() == "current"


def test_restored_stale_owner_cannot_poison_export_ownership(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.syspath_prepend(str(PORTAL_BOT))
    monkeypatch.syspath_prepend(str(tmp_path))
    runtime = importlib.import_module("module_slices")

    owner_name = "_pokrov_restored_owner"
    slice_name = "_pokrov_restored_owner_slice"
    monkeypatch.delitem(sys.modules, owner_name, raising=False)
    monkeypatch.delitem(sys.modules, slice_name, raising=False)
    (tmp_path / f"{slice_name}.py").write_text(
        "from module_slices import bootstrap_slice\n"
        "bootstrap_slice(globals())\n"
        "def exported_helper():\n"
        "    return 'current'\n",
        encoding="utf-8",
    )

    stale_owner = ModuleType(owner_name)
    monkeypatch.setitem(sys.modules, owner_name, stale_owner)
    runtime.load_slices(vars(stale_owner), (slice_name,))
    stale_export = stale_owner.exported_helper

    replacement = ModuleType(owner_name)
    monkeypatch.setitem(sys.modules, owner_name, replacement)
    runtime.load_slices(vars(replacement), (slice_name,))
    assert replacement.exported_helper is not stale_export

    # Simulate a fixture restoring the first owner object. Its export has the
    # right name but the wrong identity for the current registry instance.
    monkeypatch.setitem(sys.modules, owner_name, stale_owner)
    reloaded = runtime.load_slices(vars(stale_owner), (slice_name,))[0]
    assert stale_owner.exported_helper is vars(reloaded)["exported_helper"]
    assert "exported_helper" in reloaded._SLICE_OWN_NAMES

    # Ownership must also survive one more clean owner replacement; the old
    # implementation lost the symbol permanently at this point.
    final_owner = ModuleType(owner_name)
    monkeypatch.setitem(sys.modules, owner_name, final_owner)
    runtime.load_slices(vars(final_owner), (slice_name,))
    assert final_owner.exported_helper() == "current"
