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
            release_metadata_file="C:/tmp/release-handoff.json",
            release_env_file="C:/tmp/release-links.env",
            release_go_evidence_file="C:/tmp/runtime-sync.md",
            qdisc_node=[],
            qdisc_host=[],
            qdisc_profiles="C:/repo/infra/node-qdisc-profiles.json",
            qdisc_probe_url="https://1.1.1.1/cdn-cgi/trace",
            qdisc_heavy_url="https://speed.cloudflare.com/__down?bytes=50000000",
            qdisc_probe_attempts=8,
            qdisc_probe_pause_seconds=1.0,
            qdisc_heavy_duration_seconds=10.0,
            qdisc_min_heavy_bytes=1048576,
            qdisc_min_probe_successes=3,
            qdisc_max_probe_connect_p95_seconds=1.0,
            qdisc_max_probe_ttfb_p95_seconds=1.0,
            qdisc_max_probe_total_p95_seconds=2.0,
        )

        steps = self.module._build_steps(args, python="python")
        names = [name for name, _, _ in steps]

        self.assertEqual(names[0], "release handoff sync")
        self.assertEqual(names[-1], "post-deploy verify")
        self.assertIn("scripts/remote_brain_apply_release_handoff.py", " ".join(steps[0][1]))
        self.assertIn("--metadata-file", steps[0][1])
        self.assertIn("C:/tmp/release-handoff.json", steps[0][1])
        self.assertIn("--env-file", steps[0][1])
        self.assertIn("C:/tmp/release-links.env", steps[0][1])
        self.assertIn("--go-evidence-file", steps[0][1])
        self.assertIn("C:/tmp/runtime-sync.md", steps[0][1])

    def test_gates_only_mode_builds_and_runs_gate_steps(self) -> None:
        args = Namespace(
            brain_ip="",
            web_domain="pokrov.space",
            api_domain="api.pokrov.space",
            ssh_user="root",
            ssh_port=29374,
            passwords="C:/tmp/PASSWORDS.txt",
            quick_gate=False,
            skip_gates=False,
            skip_backend=False,
            skip_static=False,
            skip_verify=False,
            ensure_metrics_timer=False,
            ensure_observer_node=[],
            gates_only=True,
            verify_only=False,
            dry_run=False,
            release_metadata_file="",
            release_env_file="",
            qdisc_node=[],
            qdisc_host=[],
            qdisc_profiles="C:/repo/infra/node-qdisc-profiles.json",
            qdisc_probe_url="https://1.1.1.1/cdn-cgi/trace",
            qdisc_heavy_url="https://speed.cloudflare.com/__down?bytes=50000000",
            qdisc_probe_attempts=8,
            qdisc_probe_pause_seconds=1.0,
            qdisc_heavy_duration_seconds=10.0,
            qdisc_min_heavy_bytes=1048576,
            qdisc_min_probe_successes=3,
            qdisc_max_probe_connect_p95_seconds=1.0,
            qdisc_max_probe_ttfb_p95_seconds=1.0,
            qdisc_max_probe_total_p95_seconds=2.0,
        )
        gate_steps = [("release gates", ["python", "scripts/release_gate_check.py"], self.module.REPO_ROOT)]

        with patch.object(self.module.argparse.ArgumentParser, "parse_args", return_value=args):
            with patch.object(self.module, "_build_steps", return_value=gate_steps) as build_steps:
                with patch.object(self.module, "_run", return_value=0) as run_step:
                    exit_code = self.module.main()

        self.assertEqual(exit_code, 0)
        build_steps.assert_called_once()
        run_step.assert_called_once_with(
            "release gates",
            ["python", "scripts/release_gate_check.py"],
            self.module.REPO_ROOT,
            timeout_sec=None,
        )

    def test_gates_only_dry_run_prints_built_gate_steps(self) -> None:
        args = Namespace(
            brain_ip="",
            web_domain="pokrov.space",
            api_domain="api.pokrov.space",
            ssh_user="root",
            ssh_port=29374,
            passwords="C:/tmp/PASSWORDS.txt",
            quick_gate=True,
            skip_gates=False,
            skip_backend=False,
            skip_static=False,
            skip_verify=False,
            ensure_metrics_timer=False,
            ensure_observer_node=[],
            gates_only=True,
            verify_only=False,
            dry_run=True,
            release_metadata_file="",
            release_env_file="",
            qdisc_node=[],
            qdisc_host=[],
            qdisc_profiles="C:/repo/infra/node-qdisc-profiles.json",
            qdisc_probe_url="https://1.1.1.1/cdn-cgi/trace",
            qdisc_heavy_url="https://speed.cloudflare.com/__down?bytes=50000000",
            qdisc_probe_attempts=8,
            qdisc_probe_pause_seconds=1.0,
            qdisc_heavy_duration_seconds=10.0,
            qdisc_min_heavy_bytes=1048576,
            qdisc_min_probe_successes=3,
            qdisc_max_probe_connect_p95_seconds=1.0,
            qdisc_max_probe_ttfb_p95_seconds=1.0,
            qdisc_max_probe_total_p95_seconds=2.0,
        )
        gate_steps = [("release gates", ["python", "scripts/release_gate_check.py", "--quick"], self.module.REPO_ROOT)]

        with patch.object(self.module.argparse.ArgumentParser, "parse_args", return_value=args):
            with patch.object(self.module, "_build_steps", return_value=gate_steps) as build_steps:
                with patch.object(self.module, "_dry_run") as dry_run:
                    exit_code = self.module.main()

        self.assertEqual(exit_code, 0)
        build_steps.assert_called_once()
        dry_run.assert_called_once_with("release gates", ["python", "scripts/release_gate_check.py", "--quick"], self.module.REPO_ROOT)

    def test_build_steps_includes_explicit_qdisc_rollout_lane_before_verify(self) -> None:
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
            verify_only=False,
            dry_run=True,
            release_metadata_file="",
            release_env_file="",
            qdisc_node=["pl"],
            qdisc_host=["pl=203.0.113.10"],
            qdisc_profiles="C:/repo/infra/node-qdisc-profiles.json",
            qdisc_probe_url="https://1.1.1.1/cdn-cgi/trace",
            qdisc_heavy_url="https://speed.cloudflare.com/__down?bytes=50000000",
            qdisc_probe_attempts=6,
            qdisc_probe_pause_seconds=0.5,
            qdisc_heavy_duration_seconds=12.0,
            qdisc_min_heavy_bytes=2097152,
            qdisc_min_probe_successes=4,
            qdisc_max_probe_connect_p95_seconds=0.8,
            qdisc_max_probe_ttfb_p95_seconds=1.2,
            qdisc_max_probe_total_p95_seconds=2.5,
        )

        steps = self.module._build_steps(args, python="python")
        names = [name for name, _, _ in steps]

        self.assertIn("qdisc persistence install (pl)", names)
        self.assertIn("qdisc apply (pl)", names)
        self.assertIn("qdisc smoke gate (pl)", names)
        self.assertLess(names.index("qdisc persistence install (pl)"), names.index("post-deploy verify"))
        smoke_step = next(step for step in steps if step[0] == "qdisc smoke gate (pl)")
        self.assertIn("scripts/remote_node_qdisc_smoke.py", " ".join(smoke_step[1]))
        self.assertIn("--min-heavy-bytes", smoke_step[1])
        self.assertIn("2097152", smoke_step[1])
        self.assertIn("--max-probe-ttfb-p95-seconds", smoke_step[1])
        self.assertIn("1.2", smoke_step[1])

    def test_stage_static_runs_static_deploy_only(self) -> None:
        args = Namespace(
            brain_ip="82.21.114.104",
            web_domain="pokrov.space",
            api_domain="api.pokrov.space",
            ssh_user="root",
            ssh_port=29374,
            passwords="C:/tmp/PASSWORDS.txt",
            quick_gate=False,
            stage="static",
            skip_gates=False,
            skip_backend=False,
            skip_static=False,
            skip_verify=False,
            ensure_metrics_timer=False,
            ensure_observer_node=[],
            gates_only=False,
            verify_only=False,
            dry_run=False,
            release_metadata_file="",
            release_env_file="",
            step_timeout_sec=3600,
            gate_timeout_sec=7200,
            backend_timeout_sec=2400,
            static_timeout_sec=3600,
            verify_timeout_sec=900,
            qdisc_node=[],
            qdisc_host=[],
            qdisc_profiles="C:/repo/infra/node-qdisc-profiles.json",
            qdisc_probe_url="https://1.1.1.1/cdn-cgi/trace",
            qdisc_heavy_url="https://speed.cloudflare.com/__down?bytes=50000000",
            qdisc_probe_attempts=8,
            qdisc_probe_pause_seconds=1.0,
            qdisc_heavy_duration_seconds=10.0,
            qdisc_min_heavy_bytes=1048576,
            qdisc_min_probe_successes=3,
            qdisc_max_probe_connect_p95_seconds=1.0,
            qdisc_max_probe_ttfb_p95_seconds=1.0,
            qdisc_max_probe_total_p95_seconds=2.0,
        )

        with patch.object(self.module.argparse.ArgumentParser, "parse_args", return_value=args):
            with patch.object(self.module, "_run", return_value=0) as run_step:
                exit_code = self.module.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual([call.args[0] for call in run_step.call_args_list], ["static deploy"])
        self.assertEqual(run_step.call_args.kwargs["timeout_sec"], 3600)

    def test_build_steps_static_plan_only_uses_non_mutating_static_deploy_plan(self) -> None:
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
            skip_static=False,
            skip_verify=True,
            ensure_metrics_timer=False,
            ensure_observer_node=[],
            gates_only=False,
            verify_only=False,
            dry_run=False,
            static_plan_only=True,
            release_metadata_file="",
            release_env_file="",
            qdisc_node=[],
            qdisc_host=[],
            qdisc_profiles="C:/repo/infra/node-qdisc-profiles.json",
            qdisc_probe_url="https://1.1.1.1/cdn-cgi/trace",
            qdisc_heavy_url="https://speed.cloudflare.com/__down?bytes=50000000",
            qdisc_probe_attempts=8,
            qdisc_probe_pause_seconds=1.0,
            qdisc_heavy_duration_seconds=10.0,
            qdisc_min_heavy_bytes=1048576,
            qdisc_min_probe_successes=3,
            qdisc_max_probe_connect_p95_seconds=1.0,
            qdisc_max_probe_ttfb_p95_seconds=1.0,
            qdisc_max_probe_total_p95_seconds=2.0,
        )

        steps = self.module._build_steps(args, python="python")

        self.assertEqual([step[0] for step in steps], ["static deploy plan"])
        self.assertIn("scripts/remote_deploy_brain_static_sites.py", steps[0][1])
        self.assertIn("--plan-only", steps[0][1])

    def test_stage_static_plan_only_runs_static_plan_step(self) -> None:
        args = Namespace(
            brain_ip="82.21.114.104",
            web_domain="pokrov.space",
            api_domain="api.pokrov.space",
            ssh_user="root",
            ssh_port=29374,
            passwords="C:/tmp/PASSWORDS.txt",
            quick_gate=False,
            stage="static",
            skip_gates=False,
            skip_backend=False,
            skip_static=False,
            skip_verify=False,
            ensure_metrics_timer=False,
            ensure_observer_node=[],
            gates_only=False,
            verify_only=False,
            dry_run=False,
            static_plan_only=True,
            release_metadata_file="",
            release_env_file="",
            step_timeout_sec=3600,
            gate_timeout_sec=7200,
            backend_timeout_sec=2400,
            static_timeout_sec=3600,
            verify_timeout_sec=900,
            qdisc_node=[],
            qdisc_host=[],
            qdisc_profiles="C:/repo/infra/node-qdisc-profiles.json",
            qdisc_probe_url="https://1.1.1.1/cdn-cgi/trace",
            qdisc_heavy_url="https://speed.cloudflare.com/__down?bytes=50000000",
            qdisc_probe_attempts=8,
            qdisc_probe_pause_seconds=1.0,
            qdisc_heavy_duration_seconds=10.0,
            qdisc_min_heavy_bytes=1048576,
            qdisc_min_probe_successes=3,
            qdisc_max_probe_connect_p95_seconds=1.0,
            qdisc_max_probe_ttfb_p95_seconds=1.0,
            qdisc_max_probe_total_p95_seconds=2.0,
        )

        with patch.object(self.module.argparse.ArgumentParser, "parse_args", return_value=args):
            with patch.object(self.module, "_run", return_value=0) as run_step:
                exit_code = self.module.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual([call.args[0] for call in run_step.call_args_list], ["static deploy plan"])
        self.assertIn("--plan-only", run_step.call_args.args[1])
        self.assertEqual(run_step.call_args.kwargs["timeout_sec"], 3600)

    def test_build_steps_restarts_feedbackbot_in_backend_deploy(self) -> None:
        args = Namespace(
            brain_ip="82.21.114.104",
            web_domain="pokrov.space",
            api_domain="api.pokrov.space",
            ssh_user="root",
            ssh_port=29374,
            passwords="C:/tmp/PASSWORDS.txt",
            quick_gate=False,
            skip_gates=True,
            skip_backend=False,
            skip_static=True,
            skip_verify=True,
            ensure_metrics_timer=False,
            ensure_observer_node=[],
            gates_only=False,
            verify_only=False,
            dry_run=True,
            release_metadata_file="",
            release_env_file="",
            qdisc_node=[],
            qdisc_host=[],
            qdisc_profiles="C:/repo/infra/node-qdisc-profiles.json",
            qdisc_probe_url="https://1.1.1.1/cdn-cgi/trace",
            qdisc_heavy_url="https://speed.cloudflare.com/__down?bytes=50000000",
            qdisc_probe_attempts=8,
            qdisc_probe_pause_seconds=1.0,
            qdisc_heavy_duration_seconds=10.0,
            qdisc_min_heavy_bytes=1048576,
            qdisc_min_probe_successes=3,
            qdisc_max_probe_connect_p95_seconds=1.0,
            qdisc_max_probe_ttfb_p95_seconds=1.0,
            qdisc_max_probe_total_p95_seconds=2.0,
        )

        steps = self.module._build_steps(args, python="python")
        backend_step = next(step for step in steps if step[0] == "backend deploy")

        self.assertIn("--restart", backend_step[1])
        self.assertIn("portal-api,portal-bot,portal-helpbot,portal-feedbackbot", backend_step[1])

    def test_qdisc_smoke_failure_triggers_disable_and_rollback_cleanup(self) -> None:
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
            skip_verify=True,
            ensure_metrics_timer=False,
            ensure_observer_node=[],
            gates_only=False,
            verify_only=False,
            dry_run=False,
            release_metadata_file="",
            release_env_file="",
            qdisc_node=["pl"],
            qdisc_host=["pl=203.0.113.10"],
            qdisc_profiles="C:/repo/infra/node-qdisc-profiles.json",
            qdisc_probe_url="https://1.1.1.1/cdn-cgi/trace",
            qdisc_heavy_url="https://speed.cloudflare.com/__down?bytes=50000000",
            qdisc_probe_attempts=6,
            qdisc_probe_pause_seconds=0.5,
            qdisc_heavy_duration_seconds=12.0,
            qdisc_min_heavy_bytes=2097152,
            qdisc_min_probe_successes=4,
            qdisc_max_probe_connect_p95_seconds=0.8,
            qdisc_max_probe_ttfb_p95_seconds=1.2,
            qdisc_max_probe_total_p95_seconds=2.5,
        )

        with patch.object(self.module.argparse.ArgumentParser, "parse_args", return_value=args):
            with patch.object(self.module, "_run", side_effect=[0, 0, 7, 0, 0]) as run_step:
                exit_code = self.module.main()

        self.assertEqual(exit_code, 7)
        self.assertEqual(run_step.call_args_list[0].args[0], "qdisc persistence install (pl)")
        self.assertEqual(run_step.call_args_list[1].args[0], "qdisc apply (pl)")
        self.assertEqual(run_step.call_args_list[2].args[0], "qdisc smoke gate (pl)")
        self.assertEqual(run_step.call_args_list[3].args[0], "qdisc rollback-safe disable (pl)")
        self.assertEqual(run_step.call_args_list[4].args[0], "qdisc rollback (pl)")

    def test_observer_timer_ensure_requires_brain_ip(self) -> None:
        args = Namespace(
            brain_ip="",
            web_domain="pokrov.space",
            api_domain="api.pokrov.space",
            ssh_user="root",
            ssh_port=29374,
            passwords="C:/tmp/PASSWORDS.txt",
            quick_gate=False,
            skip_gates=True,
            skip_backend=True,
            skip_static=True,
            skip_verify=True,
            ensure_metrics_timer=False,
            ensure_observer_node=["pl"],
            gates_only=False,
            verify_only=False,
            dry_run=False,
            release_metadata_file="",
            release_env_file="",
            qdisc_node=[],
            qdisc_host=[],
            qdisc_profiles="C:/repo/infra/node-qdisc-profiles.json",
            qdisc_probe_url="https://1.1.1.1/cdn-cgi/trace",
            qdisc_heavy_url="https://speed.cloudflare.com/__down?bytes=50000000",
            qdisc_probe_attempts=8,
            qdisc_probe_pause_seconds=1.0,
            qdisc_heavy_duration_seconds=10.0,
            qdisc_min_heavy_bytes=1048576,
            qdisc_min_probe_successes=3,
            qdisc_max_probe_connect_p95_seconds=1.0,
            qdisc_max_probe_ttfb_p95_seconds=1.0,
            qdisc_max_probe_total_p95_seconds=2.0,
        )

        with patch.object(self.module.argparse.ArgumentParser, "parse_args", return_value=args):
            with self.assertRaises(SystemExit) as ctx:
                self.module.main()

        self.assertEqual(str(ctx.exception), "--brain-ip is required for deploy/verify steps")


if __name__ == "__main__":
    unittest.main()
