"""Read-only R12 evidence input comparison; never a release PASS or promotion gate."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import PurePosixPath, Path

POLICY = "r12-declared-evidence-inputs-v1"
# Producer must identify every significant dependency, including the collector/oracle.
REQUIRED = frozenset({"artifact", "configuration", "toolchain", "oracle", "scope"})
DIGEST = re.compile(r"^[a-f0-9]{64}$")


def classify_path(path: str) -> str:
    p = PurePosixPath(path.replace("\\", "/"))
    if p.is_absolute() or ".." in p.parts or (p.parts and ":" in p.parts[0]):
        raise ValueError("relative_repository_path_required")
    text = p.as_posix().lower()
    parts = set(p.parts)
    if "test" in parts or "tests" in parts or "e2e" in parts or p.name.startswith("test_") or p.stem.endswith(("_test", ".test", ".spec")):
        return "test_harness"
    if text.startswith(("infra/", ".github/")) or "migration" in p.stem:
        return "deployment_migration"
    if p.suffix.lower() in {".aar", ".dll", ".exe", ".apk", ".aab", ".lock"} or p.name in {"go.mod", "go.sum", "pubspec.yaml", "package.json", "CMakeLists.txt"} or "gradle" in text:
        return "packaged_dependency_toolchain"
    if text.startswith(("shared/copy", "copy/")):
        return "product_copy"
    if p.suffix.lower() in {".md", ".txt"}:
        return "documentation_only"
    if text.startswith(("config/", "shared/contracts/")) or "profile" in p.stem or "policy" in p.stem:
        return "profile_policy"
    if text.startswith("portal_bot/") or "schema" in p.stem:
        return "api_schema"
    if text.startswith(("engine/", "apps/", "packages/", "daemon/")):
        return "core_runtime"
    # A path hint cannot decide whether a general collector or web edit is harmless.
    return "manual_classification_required"


def compare_evidence_inputs(previous: dict, current: dict) -> dict:
    """Compare declared significant inputs, not filenames or a global Git commit.

    The caller remains responsible for completeness and byte provenance. This
    utility cannot certify a device run, original evidence, or an omitted input.
    """
    invalid = []
    for label, receipt in (("previous", previous), ("current", current)):
        inputs = receipt.get("inputs")
        if not isinstance(inputs, dict) or not REQUIRED.issubset(inputs) or not all(
            isinstance(key, str) and isinstance(value, str) and DIGEST.fullmatch(value)
            for key, value in inputs.items()
        ):
            invalid.append(label + ".inputs")
        for field in ("environment", "origin"):
            value = receipt.get(field)
            if not isinstance(value, str) or not value.strip():
                invalid.append(label + "." + field)
    if invalid:
        return {"policy": POLICY, "status": "MISSING_OR_INVALID_INPUTS", "fields": invalid, "release_pass": False}
    previous_inputs, current_inputs = previous["inputs"], current["inputs"]
    changed = sorted(
        "inputs." + key for key in previous_inputs.keys() | current_inputs.keys()
        if previous_inputs.get(key) != current_inputs.get(key)
    )
    changed += [key for key in ("environment", "origin") if previous[key] != current[key]]
    return {
        "policy": POLICY,
        "status": "INVALIDATED" if changed else "DECLARED_INPUTS_MATCH_REVIEW_REQUIRED",
        "changed": changed,
        "release_pass": False,
        "limitation": "Supplied fingerprints only; verify dependency completeness and original evidence provenance separately.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("previous", type=Path)
    parser.add_argument("current", type=Path)
    args = parser.parse_args()
    result = compare_evidence_inputs(
        json.loads(args.previous.read_text(encoding="utf-8")),
        json.loads(args.current.read_text(encoding="utf-8")),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "DECLARED_INPUTS_MATCH_REVIEW_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
