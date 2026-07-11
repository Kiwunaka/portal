import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "shared" / "beta-known-limitations.json"

EXPECTED_IDS = {
    "outside_store_beta",
    "runtime_download_recheck",
    "windows_unsigned",
    "downloads_limited",
    "payment_beta",
    "ru_origin_not_claimed",
    "android_audit_attested",
    "support_best_effort",
    "apple_readiness_only",
}

EXPECTED_LIVE_MIRRORS = {
    "docs/product/beta-known-limitations.md",
    "docs/launch/known-issues.md",
}


def _contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _live_mirror_paths(payload: dict) -> tuple[Path, ...]:
    source_docs = payload["source_docs"]
    assert set(source_docs) == EXPECTED_LIVE_MIRRORS
    return tuple(ROOT / relative_path for relative_path in source_docs)


def test_beta_known_limitations_contract_has_required_ids() -> None:
    payload = _contract()
    limitations = payload["limitations"]
    ids = {item["id"] for item in limitations}

    assert payload["scope"] == "outside-store-public-beta"
    assert EXPECTED_IDS <= ids

    for item in limitations:
        assert item["id"]
        assert item["severity"] in {
            "beta_limit",
            "manual_gate",
            "release_check",
            "scope_limit",
        }
        assert item["summary"]
        assert item["operator_note"]


def test_beta_known_limitations_are_mirrored_in_live_source_docs() -> None:
    payload = _contract()
    doc_paths = _live_mirror_paths(payload)

    missing: list[str] = []
    for path in doc_paths:
        text = path.read_text(encoding="utf-8")
        if "shared/beta-known-limitations.json" not in text:
            missing.append(f"{path.relative_to(ROOT)} missing shared contract reference")
        for limitation_id in EXPECTED_IDS:
            if f"`{limitation_id}`" not in text:
                missing.append(f"{path.relative_to(ROOT)} missing `{limitation_id}`")

    assert not missing, "\n".join(missing)


def test_beta_known_limitations_preserve_claim_boundaries() -> None:
    payload = _contract()
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (CONTRACT, *_live_mirror_paths(payload))
    )

    required_boundary_phrases = [
        "outside-store",
        "RU-origin readiness claim",
        "trusted Windows signing",
        "Play/store",
        "Lava.top-only",
        "best-effort",
        "readiness tracks only",
    ]
    for phrase in required_boundary_phrases:
        assert phrase in combined

    forbidden_claims = [
        "stable 1.0.0",
        "Google Play release",
        "Microsoft Store release",
        "trusted Windows signing is complete",
        "RU-origin readiness is complete",
        "production WARP",
    ]
    for claim in forbidden_claims:
        assert claim not in combined
