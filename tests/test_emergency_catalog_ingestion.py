from __future__ import annotations

import hashlib

import pytest

from portal_bot.emergency_catalog_ingestion import (
    MOBILE_FEED,
    SNI_FEED,
    EmergencyCatalogIngestionError,
    fetch_approved_source_bundle,
)


def _line(index: int) -> str:
    key_char = chr(ord("A") + index)
    return (
        f"vless://{index:08x}-1111-4111-8111-{index:012x}@reserve-{index}.example.com:443"
        f"?type=tcp&security=reality&pbk={key_char * 43}&sid={index:08x}"
        f"&sni=cover-{index}.example.com&fp=chrome&flow=xtls-rprx-vision"
    )


@pytest.mark.asyncio
async def test_bundle_requires_exact_quorum_and_deduplicates_across_feeds() -> None:
    mobile = ("\n".join((_line(1), _line(2))) + "\n").encode()
    sni = ("\n".join((_line(2), _line(3))) + "\n").encode()

    async def fetcher(mirror):
        return mobile if mirror.feed_name == MOBILE_FEED else sni

    bundle = await fetch_approved_source_bundle(fetcher=fetcher)

    assert len(bundle.materials) == 3
    assert bundle.rejection_counts == {"duplicate_across_feeds": 1}
    assert bundle.mirror_quorum == {
        MOBILE_FEED: ("codeberg", "github", "gitlab"),
        SNI_FEED: ("codeberg", "github", "gitlab"),
    }
    assert bundle.feed_digests[MOBILE_FEED] == hashlib.sha256(mobile).hexdigest()
    assert bundle.safe_summary()["accepted_count"] == 3
    assert "vless://" not in repr(bundle.safe_summary())


@pytest.mark.asyncio
async def test_one_bad_mirror_does_not_override_two_matching_mirrors() -> None:
    good = (_line(1) + "\n").encode()
    bad = (_line(9) + "\n").encode()

    async def fetcher(mirror):
        return bad if mirror.name == "codeberg" else good

    bundle = await fetch_approved_source_bundle(fetcher=fetcher)

    assert len(bundle.materials) == 1
    assert bundle.mirror_quorum[MOBILE_FEED] == ("github", "gitlab")
    assert bundle.mirror_quorum[SNI_FEED] == ("github", "gitlab")


@pytest.mark.asyncio
async def test_split_mirrors_fail_closed_without_quorum() -> None:
    async def fetcher(mirror):
        return (_line({"github": 1, "gitlab": 2, "codeberg": 3}[mirror.name]) + "\n").encode()

    with pytest.raises(EmergencyCatalogIngestionError, match="mirror_quorum_missing"):
        await fetch_approved_source_bundle(fetcher=fetcher)


@pytest.mark.asyncio
async def test_failed_mirror_still_allows_two_mirror_quorum() -> None:
    good = (_line(1) + "\n").encode()

    async def fetcher(mirror):
        if mirror.name == "github":
            raise EmergencyCatalogIngestionError("mirror_http_status")
        return good

    bundle = await fetch_approved_source_bundle(fetcher=fetcher)

    assert bundle.mirror_quorum[MOBILE_FEED] == ("codeberg", "gitlab")
    assert bundle.mirror_quorum[SNI_FEED] == ("codeberg", "gitlab")
