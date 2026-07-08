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

    def test_parse_password_candidates_keeps_multiple_near_marker(self) -> None:
        import node_passwords

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "PASSWORDS.txt"
            path.write_text(
                "\n".join(
                    [
                        "RFMINI",
                        "176.123.166.119",
                        "panel-pass",
                        "ssh-pass",
                    ]
                ),
                encoding="utf-8",
            )

            result = node_passwords.parse_password_candidates(path, requested_codes=["mini"])

        self.assertEqual(result.get("mini"), ["panel-pass", "ssh-pass"])

    def test_parse_passwords_supports_demax_alias(self) -> None:
        import node_passwords

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "PASSWORDS.txt"
            path.write_text(
                "\n".join(
                    [
                        "DEMAX Germany",
                        "46.247.109.132",
                        "de-secret-password",
                    ]
                ),
                encoding="utf-8",
            )

            result = node_passwords.parse_passwords(path, requested_codes=["de"])

        self.assertEqual(result.get("de"), "de-secret-password")

    def test_parse_passwords_supports_new_ru_node_aliases(self) -> None:
        import node_passwords

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "PASSWORDS.txt"
            path.write_text(
                "\n".join(
                    [
                        "RUnode",
                        "158.255.3.39",
                        "ru-secret-password",
                        "",
                        "RUnodeSPB",
                        "193.233.216.73",
                        "spb-secret-password",
                    ]
                ),
                encoding="utf-8",
            )

            result = node_passwords.parse_passwords(path, requested_codes=["ru", "ru_spb"])

        self.assertEqual(result.get("ru"), "ru-secret-password")
        self.assertEqual(result.get("ru_spb"), "spb-secret-password")


if __name__ == "__main__":
    unittest.main()
