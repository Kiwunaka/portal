import sys
import tempfile
import unittest
from pathlib import Path


class NodePasswordsTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        scripts_dir = str(repo_root / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

    def test_parse_passwords_supports_mini_russia_alias(self) -> None:
        import node_passwords

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

            result = node_passwords.parse_passwords(path, requested_codes=["mini"])

        self.assertEqual(result.get("mini"), "mini-secret-password")


if __name__ == "__main__":
    unittest.main()
