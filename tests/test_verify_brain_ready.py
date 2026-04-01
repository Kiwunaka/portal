import importlib.util
import sys
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "verify_brain_ready.py"
    spec = importlib.util.spec_from_file_location("verify_brain_ready", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class VerifyBrainReadyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_subscription_check_script_includes_connect_probe(self) -> None:
        script = self.module._build_subscription_check_script(
            api_domain="api.pokrov.space",
            connect_domain="connect.pokrov.space",
            repeat=3,
        )

        self.assertIn("https://connect.pokrov.space/s8Kx2mP7qR4wT/$SEL_TOK", script)
        self.assertIn('print(f"connect_json=1 outbounds={len(payload.get(\'outbounds\') or [])}")', script)
        self.assertIn('RAW_PAYLOAD="$RAW" python3 - <<\'PY\'', script)
        self.assertIn('RAW_CONNECT_PAYLOAD="$RAW_CONNECT" python3 - <<\'PY\'', script)
        self.assertIn("for i in $(seq 1 3); do", script)


if __name__ == "__main__":
    unittest.main()
