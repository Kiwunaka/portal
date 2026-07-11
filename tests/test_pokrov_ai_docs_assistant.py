from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "pokrov_ai_docs_assistant.py"
    spec = importlib.util.spec_from_file_location("pokrov_ai_docs_assistant", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_inventory_uses_allowlisted_canonical_sources_only() -> None:
    module = _load_module()

    inventory = module.build_inventory()
    paths = {source["path"] for source in inventory["sources"]}

    assert "AGENTS.md" in paths
    assert "docs/product/portal-vpn-product.md" in paths
    assert "docs/product/beta-known-limitations.md" in paths
    assert "docs/launch/known-issues.md" in paths
    assert {
        "docs/product/platform-availability.md",
        "docs/product/public-beta-prd.md",
        "docs/developer/work-orders/2026-04-open-beta-v4/13-launch-decision.md",
        "docs/launch/open-beta-release-notes.md",
    }.isdisjoint(paths)
    assert "portal_bot/.env" not in paths
    assert not any(path.startswith("ops-local/") for path in paths)
    assert not any("VPN NODE SSH KEYS" in path for path in paths)
    assert inventory["source_count"] == len(paths)
    assert inventory["total_bytes"] > 0


def test_every_default_source_path_resolves() -> None:
    module = _load_module()
    assert all(
        (module.REPO_ROOT / relative_path).exists()
        for relative_path in module.DEFAULT_SOURCE_PATHS
    )


def test_default_sources_keep_current_owners_and_exclude_dated_evidence() -> None:
    module = _load_module()
    paths = set(module.DEFAULT_SOURCE_PATHS)

    assert {
        "docs/product/portal-vpn-product.md",
        "docs/product/beta-known-limitations.md",
        "docs/launch/known-issues.md",
    } <= paths
    assert paths.isdisjoint(
        {
            "docs/product/platform-availability.md",
            "docs/product/public-beta-prd.md",
            "docs/developer/work-orders/2026-04-open-beta-v4/13-launch-decision.md",
            "docs/launch/open-beta-release-notes.md",
        }
    )


def test_inventory_rejects_out_of_repo_and_secret_paths() -> None:
    module = _load_module()

    try:
        module.resolve_sources(["../outside.md"])
    except ValueError as exc:
        assert "out-of-repo" in str(exc)
    else:
        raise AssertionError("expected out-of-repo path to be rejected")

    try:
        module.resolve_sources(["portal_bot/.env"])
    except ValueError as exc:
        assert "blocked source" in str(exc)
    else:
        raise AssertionError("expected secret path to be rejected")


def test_openai_instructions_preserve_release_and_secret_boundaries() -> None:
    module = _load_module()

    instructions = module.OPENAI_INSTRUCTIONS

    assert "Never ask for, print, infer, or preserve secrets" in instructions
    assert "RU-origin readiness" in instructions
    assert "indexed POKROV canon" in instructions
    for required in (
        "SEO/search-intent",
        "VPN",
        "ВПН",
        "Hidden text",
        "cloaking",
        "keyword stuffing",
        "unsupported release, payment, or store claims",
    ):
        assert required in instructions
    assert "direct-meaning public" not in instructions
