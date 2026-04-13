import importlib.util
import sys
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
