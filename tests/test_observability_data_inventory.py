from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts/validate_observability_data_inventory.py"
SPEC = importlib.util.spec_from_file_location(
    "validate_observability_data_inventory", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_inventory_matches_every_declared_source_field() -> None:
    inventory = MODULE.build_inventory()
    assert inventory["contract_id"] == "pokrov.observability-data-inventory.v1"
    assert len(inventory["threat_model"]["threats"]) == 6
    for group in inventory["field_groups"]:
        assert group["purpose"]
        assert group["modes"]
        assert group["retention"]
        assert group["owner"]
        assert group["fields"]


def test_checked_in_inventory_is_current() -> None:
    parsed = json.loads(MODULE.OUTPUT_PATH.read_text(encoding="utf-8"))
    assert parsed == MODULE.build_inventory()
