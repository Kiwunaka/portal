from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from generate_marketing_governance import (  # noqa: E402
    CATALOG_PATH,
    OUTPUT_PATH,
    SOURCE_PATH,
    MarketingGovernanceError,
    _digest,
    _file_digest,
    _read_object,
    build_contract,
)


PUBLIC_SCAN_ROOTS = (
    Path("marketing/src"),
    Path("webapp/src"),
    Path("copy/catalog.ru.json"),
    Path("shared/support-ai-knowledge.json"),
    Path("portal_bot/bot_texts.py"),
)
TEXT_SUFFIXES = frozenset({".json", ".md", ".py", ".ts", ".tsx"})


def _text_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in TEXT_SUFFIXES
        and not any(part in {".next", "node_modules", "archive"} for part in path.parts)
    )


def scan_text(
    text: str,
    *,
    patterns: Sequence[str],
    markers: Sequence[str] = (),
) -> list[str]:
    issues: list[str] = []
    for pattern in patterns:
        if re.search(pattern, text):
            issues.append(f"prohibited_claim:{pattern}")
    lowered = text.casefold()
    for marker in markers:
        normalized = str(marker).strip().casefold()
        if normalized and normalized in lowered:
            issues.append(f"trust_led_marker:{marker}")
    return issues


def validate_repository(
    *,
    repo_root: Path = REPO_ROOT,
    contract: Mapping[str, Any] | None = None,
) -> list[str]:
    root = repo_root.resolve()
    source_path = root / SOURCE_PATH.relative_to(REPO_ROOT)
    catalog_path = root / CATALOG_PATH.relative_to(REPO_ROOT)
    output_path = root / OUTPUT_PATH.relative_to(REPO_ROOT)
    issues: list[str] = []
    try:
        source = _read_object(source_path)
        catalog = _read_object(catalog_path)
        expected = build_contract(source, catalog)
        observed = dict(contract or _read_object(output_path))
    except MarketingGovernanceError as exc:
        return [str(exc)]

    if observed != expected:
        issues.append("generated_contract_stale")
    unsigned = dict(observed)
    observed_hash = str(unsigned.pop("contract_sha256", ""))
    if observed_hash != _digest(unsigned):
        issues.append("contract_sha256_mismatch")
    if str(observed.get("source_sha256") or "") != _file_digest(source_path):
        issues.append("source_sha256_mismatch")
    if str(observed.get("copy_catalog_sha256") or "") != _file_digest(catalog_path):
        issues.append("copy_catalog_sha256_mismatch")

    profiles = {
        str(item.get("profile_id") or ""): item
        for item in list(observed.get("profiles") or [])
        if isinstance(item, Mapping)
    }
    service_profile = profiles.get("service_rf") or {}
    if service_profile.get("approval") is not None:
        issues.append("service_profile_sample_approval_forbidden")
    if list(service_profile.get("allowed_channels") or []):
        issues.append("service_profile_channels_must_remain_empty")
    if "blocked" not in str(service_profile.get("campaign_launch_state") or ""):
        issues.append("service_profile_launch_not_blocked")

    patterns = [str(item) for item in list(observed.get("prohibited_claim_patterns") or [])]
    for relative in PUBLIC_SCAN_ROOTS:
        path = root / relative
        for candidate in _text_files(path):
            try:
                text = candidate.read_text(encoding="utf-8")
            except OSError:
                issues.append(f"unreadable_public_copy:{candidate.relative_to(root)}")
                continue
            for issue in scan_text(text, patterns=patterns):
                issues.append(f"{candidate.relative_to(root).as_posix()}:{issue}")

    markers = [str(item) for item in list(observed.get("trust_led_forbidden_markers") or [])]
    for raw in list(observed.get("trust_led_files") or []):
        relative = Path(str(raw))
        candidate = root / relative
        try:
            text = candidate.read_text(encoding="utf-8")
        except OSError:
            issues.append(f"missing_trust_led_file:{relative.as_posix()}")
            continue
        for issue in scan_text(text, patterns=patterns, markers=markers):
            issues.append(f"{relative.as_posix()}:{issue}")

    commercial_path = root / "shared" / "commercial-contract.json"
    try:
        commercial = json.loads(commercial_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        issues.append("commercial_contract_unreadable")
    else:
        legal = commercial.get("legal") if isinstance(commercial, dict) else {}
        if not isinstance(legal, dict) or legal.get("launch_ready") is not False:
            issues.append("repository_legal_launch_must_remain_blocked")
        if list((legal or {}).get("allowed_launch_channels") or []):
            issues.append("repository_launch_channels_must_remain_empty")
    return sorted(set(issues))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate claim evidence and fail-closed marketing copy governance."
    )
    parser.parse_args()
    issues = validate_repository()
    if issues:
        for issue in issues:
            print(f"FAIL marketing-governance {issue}")
        return 1
    contract = _read_object(OUTPUT_PATH)
    print(
        "PASS marketing-governance-validation "
        f"revision={contract['revision']} claims={len(contract['claims'])} "
        f"profiles={len(contract['profiles'])} launch=blocked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
