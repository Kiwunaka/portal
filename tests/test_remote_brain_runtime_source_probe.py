import importlib.util
import json
import subprocess
import sys
import unittest
from unittest import mock
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load_module():
    path = SCRIPTS_DIR / "remote_brain_runtime_source_probe.py"
    spec = importlib.util.spec_from_file_location("remote_brain_runtime_source_probe", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class RemoteBrainRuntimeSourceProbeTests(unittest.TestCase):
    def test_compare_bytes_allows_only_crlf_to_lf_normalization(self) -> None:
        module = _load_module()

        self.assertEqual(
            module._compare_bytes(b"one\ntwo\n", b"one\ntwo\n")["classification"],
            "EXACT_BYTES",
        )
        self.assertEqual(
            module._compare_bytes(b"one\ntwo\n", b"one\r\ntwo\r\n")["classification"],
            "CRLF_ONLY_DIFFERENCE",
        )
        mismatch = module._compare_bytes(b"one\ntwo\n", b"one\rthree\n")
        self.assertEqual(mismatch["classification"], "CONTENT_MISMATCH")
        self.assertFalse(mismatch["crlf_normalized_match"])

    def test_source_revision_requires_an_exact_full_commit(self) -> None:
        module = _load_module()
        head = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        self.assertEqual(module._resolve_source_revision(REPO_ROOT, head), head)
        for invalid in (head[:12], "G" * 40, "", "0" * 40):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                module._resolve_source_revision(REPO_ROOT, invalid)

    def test_git_blob_reads_committed_bytes_not_worktree_bytes(self) -> None:
        module = _load_module()
        head = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        blob = module._git_blob(REPO_ROOT, head, "copy/catalog.ru.json")

        self.assertTrue(blob.startswith(b"{"))
        self.assertNotEqual(blob, b"")

    def test_report_retains_no_remote_content_or_secret_material(self) -> None:
        module = _load_module()
        rows = [
            {
                "source_path": "portal_bot/api.py",
                "remote_target": "/root/portal_bot/api.py",
                "raw_match": False,
                "crlf_normalized_match": True,
                "classification": "CRLF_ONLY_DIFFERENCE",
            },
            {
                "source_path": "shared/product-facts.json",
                "remote_target": "/root/shared/product-facts.json",
                "raw_match": False,
                "crlf_normalized_match": False,
                "classification": "CONTENT_MISMATCH",
            },
        ]

        report = module._build_report(
            source_revision="a" * 40,
            auth_method="password#1",
            rows=rows,
            checked_at="2026-08-27T00:00:00+00:00",
        )

        self.assertFalse(report["ok"])
        self.assertEqual(report["raw_match_count"], 0)
        self.assertEqual(report["crlf_only_difference_count"], 1)
        self.assertEqual(report["normalized_match_count"], 1)
        self.assertEqual(report["mismatch_count"], 1)
        self.assertEqual(report["auth_method"], "password")
        self.assertFalse(report["remote_content_retained"])
        encoded = json.dumps(report)
        self.assertNotIn("password#1", encoded)
        self.assertNotIn("remote_bytes", encoded)

    def test_ssh_config_hash_probe_returns_only_comparisons(self) -> None:
        module = _load_module()
        source_payload = [
            ("portal_bot/api.py", "/root/portal_bot/api.py", b"secret-source\n"),
            ("shared/product-facts.json", "/root/shared/product-facts.json", b"one\ntwo\n"),
        ]
        response = {
            "schema": module.REMOTE_HASH_SCHEMA,
            "rows": [
                {
                    "index": 0,
                    "readable": True,
                    "raw_sha256": module._sha256(b"secret-source\n"),
                    "normalized_sha256": module._sha256(b"secret-source\n"),
                },
                {
                    "index": 1,
                    "readable": True,
                    "raw_sha256": module._sha256(b"one\r\ntwo\r\n"),
                    "normalized_sha256": module._sha256(b"one\ntwo\n"),
                },
            ],
        }
        completed = subprocess.CompletedProcess(
            args=["ssh"],
            returncode=0,
            stdout=json.dumps(response),
            stderr="",
        )

        with mock.patch.object(module.OpenSshConfigSession, "run", return_value=completed) as run:
            rows = module._probe_via_ssh_config_alias(
                alias="pokrov-brain",
                source_payload=source_payload,
            )

        self.assertEqual([row["classification"] for row in rows], ["EXACT_BYTES", "CRLF_ONLY_DIFFERENCE"])
        request = run.call_args.kwargs["input_text"]
        self.assertNotIn("secret-source", request)
        self.assertIn(module._sha256(b"secret-source\n"), request)

    def test_ssh_config_hash_probe_rejects_unsafe_alias_and_incomplete_rows(self) -> None:
        module = _load_module()
        payload = [("portal_bot/api.py", "/root/portal_bot/api.py", b"value")]

        with self.assertRaises(ValueError):
            module._probe_via_ssh_config_alias(alias="-unsafe", source_payload=payload)

        completed = subprocess.CompletedProcess(
            args=["ssh"],
            returncode=0,
            stdout=json.dumps({"schema": module.REMOTE_HASH_SCHEMA, "rows": []}),
            stderr="",
        )
        with mock.patch.object(module.OpenSshConfigSession, "run", return_value=completed):
            with self.assertRaises(RuntimeError):
                module._probe_via_ssh_config_alias(alias="pokrov-brain", source_payload=payload)

    def test_report_preserves_ssh_config_mode_without_alias_or_content(self) -> None:
        module = _load_module()
        report = module._build_report(
            source_revision="a" * 40,
            auth_method="ssh_config",
            rows=[
                {
                    "source_path": "portal_bot/api.py",
                    "remote_target": "/root/portal_bot/api.py",
                    "raw_match": True,
                    "crlf_normalized_match": True,
                    "classification": "EXACT_BYTES",
                }
            ],
            mode="READ_ONLY_SSH_HASHES",
        )

        self.assertTrue(report["ok"])
        self.assertEqual(report["auth_method"], "ssh_config")
        self.assertEqual(report["mode"], "READ_ONLY_SSH_HASHES")
        self.assertNotIn("alias", json.dumps(report))


if __name__ == "__main__":
    unittest.main()
