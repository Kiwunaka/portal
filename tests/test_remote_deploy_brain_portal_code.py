import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load_module():
    path = SCRIPTS_DIR / "remote_deploy_brain_portal_code.py"
    spec = importlib.util.spec_from_file_location("remote_deploy_brain_portal_code", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class RemoteDeployBrainPortalCodeTests(unittest.TestCase):
    def test_iter_upload_mappings_includes_shared_runtime_assets(self) -> None:
        module = _load_module()
        mappings = module.iter_upload_mappings(REPO_ROOT)
        targets = {target for _source, target in mappings}

        self.assertIn("/root/shared/product-facts.json", targets)
        self.assertIn("/root/shared/public-urls.json", targets)
        self.assertIn("/root/shared/design-tokens.json", targets)

    def test_restart_default_includes_feedbackbot(self) -> None:
        module = _load_module()
        self.assertIn("portal-feedbackbot", module.DEFAULT_RESTART_UNITS)

    def test_main_fails_when_requested_unit_is_not_active_after_restart(self) -> None:
        module = _load_module()
        ssh = MagicMock()
        sftp = MagicMock()
        ssh.open_sftp.return_value = sftp
        run_results = [
            (0, "", ""),
            (0, "", ""),
            (1, "", "restart failed"),
            (3, "", "inactive"),
        ]

        with patch.object(module.argparse.ArgumentParser, "parse_args") as parse_args:
            parse_args.return_value = module.argparse.Namespace(
                brain_ip="82.21.114.104",
                ssh_user="root",
                ssh_port=29374,
                passwords="C:/tmp/PASSWORDS.txt",
                restart="portal-feedbackbot",
            )
            with patch.object(module, "connect_node", return_value=(ssh, "password")):
                with patch.object(module, "_run", side_effect=run_results):
                    exit_code = module.main()

        self.assertEqual(exit_code, 1)
        ssh.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
