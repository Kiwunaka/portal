from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "remote_prepare_emergency_catalog_env.py"
if str(SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT.parent))


def test_prepare_script_is_parseable_and_pins_safe_runtime_contract() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    ast.parse(source)

    assert "POKROV emergency probe payload v1\\n" in source
    assert "PROBE_DIGEST = hashlib.sha256(PROBE_PAYLOAD).hexdigest()" in source
    assert "/root/portal_bot/emergency_linux_probe_adapter.py" in source
    assert "partial_emergency_key_state" in source
    assert "public_key_b64" in source
    assert "SIGNING_PRIVATE_KEY_B64" in source
    assert "print(parsed" not in source
    assert "print(payload" not in source

    import importlib.util

    spec = importlib.util.spec_from_file_location("remote_prepare_emergency_catalog_env", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    compile(module._remote_script(enable_worker=False), "<remote-prepare>", "exec")


def test_prepare_script_defaults_worker_off_and_requires_explicit_enable() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert 'parser.add_argument("--enable-worker", action="store_true")' in source
    assert 'enabled = "1" if enable_worker else "0"' in source
    assert '"EMERGENCY_CATALOG_WORKER_ENABLED": enabled' in source
