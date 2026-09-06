import unittest
from classify_evidence_inputs import classify_path, compare_evidence_inputs


def receipt():
    return {"inputs": {name: "a" * 64 for name in ("artifact", "configuration", "toolchain", "oracle", "scope")}, "environment": "synthetic-windows-vm", "origin": "current-origin"}


class EvidenceInputsTest(unittest.TestCase):
    def test_collector_change_invalidates_identical_runtime_bytes(self):
        previous, current = receipt(), receipt()
        current["inputs"]["oracle"] = "b" * 64
        result = compare_evidence_inputs(previous, current)
        self.assertEqual(result["status"], "INVALIDATED")
        self.assertEqual(result["changed"], ["inputs.oracle"])
        self.assertFalse(result["release_pass"])

    def test_equal_names_do_not_hide_config_or_origin_change(self):
        previous, current = receipt(), receipt()
        current["inputs"]["configuration"] = "b" * 64
        current["origin"] = "RU-origin"
        result = compare_evidence_inputs(previous, current)
        self.assertEqual(result["status"], "INVALIDATED")
        self.assertEqual(result["changed"], ["inputs.configuration", "origin"])

    def test_equal_declared_inputs_are_not_a_release_pass_and_missing_is_unknown(self):
        result = compare_evidence_inputs(receipt(), receipt())
        self.assertEqual(result["status"], "DECLARED_INPUTS_MATCH_REVIEW_REQUIRED")
        self.assertFalse(result["release_pass"])
        current = receipt()
        del current["inputs"]["scope"]
        self.assertEqual(compare_evidence_inputs(receipt(), current)["status"], "MISSING_OR_INVALID_INPUTS")

    def test_scoped_classification_keeps_harness_before_product_and_unknown_explicit(self):
        expected = {
            "docs/architecture/runtime.md": "documentation_only",
            "apps/android/app/src/test/RuntimeProfileTest.kt": "test_harness",
            "tests/test_api_profile.py": "test_harness",
            "config/runtime-profile.seed.json": "profile_policy",
            "portal_bot/api_client_routes.py": "api_schema",
            "engine/sing-box/daemon/started_service.go": "core_runtime",
            "apps/windows/runtime/pokrov-core.dll": "packaged_dependency_toolchain",
            "portal_bot/requirements.txt": "packaged_dependency_toolchain",
            "marketing/package-lock.json": "packaged_dependency_toolchain",
            "infra/runtime.service": "deployment_migration",
            "infra/owned-smart-dns/README.md": "documentation_only",
            "shared/copy.ts": "product_copy",
            "scripts/collect_client_evidence.py": "manual_classification_required",
        }
        for path, category in expected.items():
            with self.subTest(path=path): self.assertEqual(classify_path(path), category)
        with self.assertRaises(ValueError): classify_path("../outside")


if __name__ == "__main__": unittest.main()
