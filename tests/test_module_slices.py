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
        "api_public_routes.py": 7_000,
        "api_surface_routes.py": 7_000,
        "api_admin_routes.py": 7_000,
        "api_subscription_routes.py": 7_000,
        "bot_user_handlers.py": 7_000,
        "bot_admin_handlers.py": 7_000,
        "bot_payment_handlers.py": 7_000,
        "bot_operator_handlers.py": 7_000,
    }

    for filename, limit in expected.items():
        path = PORTAL_BOT / filename
        line_count = len(path.read_text(encoding="utf-8-sig").splitlines())
        assert line_count <= limit, f"{filename} grew to {line_count} lines (limit {limit})"

    api_source = (PORTAL_BOT / "api.py").read_text(encoding="utf-8-sig")
    bot_source = (PORTAL_BOT / "bot.py").read_text(encoding="utf-8-sig")
    for module_name in (
        "api_public_routes",
        "api_surface_routes",
        "api_admin_routes",
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
