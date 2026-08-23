from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts/generate_observability_support_reference.py"
SPEC = importlib.util.spec_from_file_location(
    "generate_observability_support_reference", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_generated_reference_contains_every_catalog_entry_once() -> None:
    catalog = json.loads(MODULE.CATALOG_PATH.read_text(encoding="utf-8"))
    rendered = MODULE.render_reference()
    for entry in catalog["entries"]:
        assert rendered.count(f"`{entry['code']}`") == 1
    assert f"- entries: `{len(catalog['entries'])}`" in rendered


def test_checked_in_reference_is_current() -> None:
    assert MODULE.OUTPUT_PATH.read_text(encoding="utf-8") == MODULE.render_reference()
