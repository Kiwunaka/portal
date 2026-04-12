from __future__ import annotations

import json
import unittest
from pathlib import Path


class WebappReleaseScriptsTests(unittest.TestCase):
    def test_default_e2e_script_covers_all_specs_including_oidc_fallback(self) -> None:
        package_json = Path(__file__).resolve().parents[1] / "webapp" / "package.json"
        data = json.loads(package_json.read_text(encoding="utf-8"))

        script = str(data["scripts"]["test:e2e"])

        self.assertEqual(script, "playwright test")
