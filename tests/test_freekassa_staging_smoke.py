import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest import mock


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "freekassa_staging_smoke.py"
    spec = importlib.util.spec_from_file_location("freekassa_staging_smoke", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FreekassaStagingSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_main_refuses_without_legacy_reconciliation_ack(self) -> None:
        with mock.patch.object(sys, "argv", ["freekassa_staging_smoke.py"]), mock.patch.object(self.module, "http_json") as http_json:
            code = self.module.main()

        self.assertEqual(code, 2)
        http_json.assert_not_called()

    def test_main_with_ack_requires_free_kassa_public_create_to_be_blocked(self) -> None:
        env = {
            "SMOKE_API_BASE_URL": "https://api.pokrov.test",
            "CHECKOUT_TICKET_SECRET": "checkout-secret",
            "SMOKE_TEST_TG_ID": "1001",
            "CHECKOUT_TICKET_TTL_SECONDS": "900",
        }
        with mock.patch.dict(os.environ, env, clear=False), mock.patch.object(
            sys,
            "argv",
            ["freekassa_staging_smoke.py", "--legacy-reconciliation"],
        ), mock.patch.object(
            self.module,
            "http_json",
            return_value=(
                503,
                '{"detail":"freekassa is not enabled for public beta RUB checkout"}',
                {"detail": "freekassa is not enabled for public beta RUB checkout"},
            ),
        ) as http_json, mock.patch.object(self.module, "http_text", return_value=(200, "ok")) as http_text:
            code = self.module.main()

        self.assertEqual(code, 0)
        self.assertEqual(http_json.call_args.args[0], "https://api.pokrov.test/api/payments/freekassa/orders/create-public")
        self.assertEqual(http_json.call_args.kwargs["method"], "POST")
        self.assertEqual(http_json.call_args.kwargs["payload"]["plan_code"], "1_month")
        self.assertEqual(http_text.call_count, 2)

    def test_main_with_ack_fails_if_free_kassa_public_create_succeeds(self) -> None:
        env = {
            "SMOKE_API_BASE_URL": "https://api.pokrov.test",
            "CHECKOUT_TICKET_SECRET": "checkout-secret",
            "SMOKE_TEST_TG_ID": "1001",
            "CHECKOUT_TICKET_TTL_SECONDS": "900",
        }
        with mock.patch.dict(os.environ, env, clear=False), mock.patch.object(
            sys,
            "argv",
            ["freekassa_staging_smoke.py", "--legacy-reconciliation"],
        ), mock.patch.object(
            self.module,
            "http_json",
            return_value=(200, '{"ok":true}', {"ok": True, "payment_url": "https://pay.example", "order_id": "fk_1"}),
        ), self.assertRaises(SystemExit) as raised:
            self.module.main()

        self.assertIn("Legacy FreeKassa public create was not blocked", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
