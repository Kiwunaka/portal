import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "remote_bootstrap_nodes.py"
    spec = importlib.util.spec_from_file_location("remote_bootstrap_nodes", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RemoteBootstrapNodesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_parse_passwords_supports_mini_russia_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "PASSWORDS.txt"
            path.write_text(
                "\n".join(
                    [
                        "RU SBER (Россия Москва ультра слабый)",
                        "",
                        "176.123.166.119",
                        "mini-secret-password",
                    ]
                ),
                encoding="utf-8",
            )

            result = self.module._parse_passwords(path)

        self.assertEqual(result.get("mini"), "mini-secret-password")


if __name__ == "__main__":
    unittest.main()
