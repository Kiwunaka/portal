from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "remote_select_owned_awg_lab.py"


def _load_module():
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location("remote_select_owned_awg_lab", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_selection_is_an_explicit_supported_operation() -> None:
    module = _load_module()

    assert module.ALLOWED_PROFILES == ("default", "awg2_lab", "awg31_lab")


def test_default_selection_removes_only_the_exact_lab_identity() -> None:
    module = _load_module()
    helper = module._REMOTE_HELPER

    assert 'if profile == "default":' in helper
    assert 'cohorts.pop("candidate4-awg-lab", None)' in helper
    assert 'if value != install_id' in helper
    assert 'if int(value) != tg_id' in helper
    assert 'for lab_name in ("awg2_lab", "awg31_lab")' in helper
    assert '"cohort_identity_present": identity_present' in helper
    assert '"lab_allowlist_identity_present": lab_identity_present' in helper


def test_default_readback_requires_cohort_and_lab_allowlists_to_be_clear() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert 'if args.profile == "default":' in source
    assert 'not report["cohort_identity_present"]' in source
    assert 'not report[\n                "lab_allowlist_identity_present"\n            ]' in source
