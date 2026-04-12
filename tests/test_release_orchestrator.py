import importlib.util
import sys
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "release_orchestrator.py"
    spec = importlib.util.spec_from_file_location("release_orchestrator", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ReleaseOrchestratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def test_build_steps_includes_release_handoff_sync_before_verify(self) -> None:
        args = Namespace(
            brain_ip="82.21.114.104",
            web_domain="pokrov.space",
            api_domain="api.pokrov.space",
            ssh_user="root",
            ssh_port=29374,
            passwords="C:/tmp/PASSWORDS.txt",
            quick_gate=False,
            skip_gates=True,
            skip_backend=True,
            skip_static=True,
            skip_verify=False,
            ensure_metrics_timer=False,
            ensure_observer_node=[],
            gates_only=False,
            verify_only=True,
            dry_run=True,
            release_env_file="C:/tmp/release-links.env",
        )

        steps = self.module._build_steps(args, python="python")
        names = [name for name, _, _ in steps]

        self.assertEqual(names[0], "release handoff sync")
        self.assertEqual(names[-1], "post-deploy verify")
        self.assertIn("scripts/remote_brain_apply_release_handoff.py", " ".join(steps[0][1]))
        self.assertIn("--env-file", steps[0][1])
        self.assertIn("C:/tmp/release-links.env", steps[0][1])

    def test_main_gates_only_dry_run_builds_and_prints_gate_steps(self) -> None:
        steps = [("release gates", ["python", "scripts/release_gate_check.py"], self.module.REPO_ROOT)]
        with patch.object(self.module, "_build_steps", return_value=steps) as build_steps:
            with patch.object(self.module, "_dry_run") as dry_run:
                with patch.object(self.module, "_run") as run:
                    with patch.object(sys, "argv", ["release_orchestrator.py", "--gates-only", "--dry-run"]):
                        rc = self.module.main()

        self.assertEqual(rc, 0)
        build_steps.assert_called_once()
        dry_run.assert_called_once_with("release gates", ["python", "scripts/release_gate_check.py"], self.module.REPO_ROOT)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
