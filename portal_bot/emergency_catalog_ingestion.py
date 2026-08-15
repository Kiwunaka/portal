"""Approved-mirror quorum fetch for the emergency catalog source."""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Mapping

import aiohttp

try:
    from emergency_catalog_source import (
        MAX_SOURCE_BYTES,
        EmergencyEndpointMaterial,
        EmergencyCatalogSourceError,
        parse_emergency_source,
    )
except ImportError:  # pragma: no cover - package import
    from .emergency_catalog_source import (
        MAX_SOURCE_BYTES,
        EmergencyEndpointMaterial,
        EmergencyCatalogSourceError,
        parse_emergency_source,
    )


MOBILE_FEED = "Vless-Reality-White-Lists-Rus-Mobile.txt"
SNI_FEED = "WHITE-SNI-RU-all.txt"
MIN_MIRROR_QUORUM = 2
MAX_HTTP_BODY_BYTES = MAX_SOURCE_BYTES


@dataclass(frozen=True, slots=True)
class ApprovedSourceMirror:
    name: str
    feed_name: str
    url: str = field(repr=False)


APPROVED_MIRRORS: tuple[ApprovedSourceMirror, ...] = tuple(
    ApprovedSourceMirror(name=name, feed_name=feed, url=url_template.format(feed=feed))
    for feed in (MOBILE_FEED, SNI_FEED)
    for name, url_template in (
        (
            "github",
            "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/{feed}",
        ),
        (
            "gitlab",
            "https://gitlab.com/igareck/vpn-configs-for-russia/-/raw/main/{feed}",
        ),
        (
            "codeberg",
            "https://codeberg.org/igareck/vpn-configs-for-russia/raw/branch/main/{feed}",
        ),
    )
)


class EmergencyCatalogIngestionError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class EmergencySourceBundle:
    materials: tuple[EmergencyEndpointMaterial, ...]
    source_revision: str
    source_digest: str
    feed_digests: Mapping[str, str]
    mirror_quorum: Mapping[str, tuple[str, ...]]
    candidate_line_count: int
    rejection_counts: Mapping[str, int]

    def safe_summary(self) -> dict[str, object]:
        return {
            "source_revision": self.source_revision,
            "source_digest": self.source_digest,
            "feed_count": len(self.feed_digests),
            "mirror_quorum": {key: len(value) for key, value in self.mirror_quorum.items()},
            "candidate_line_count": self.candidate_line_count,
            "accepted_count": len(self.materials),
            "rejection_counts": dict(self.rejection_counts),
        }


async def _read_bounded_response(response: aiohttp.ClientResponse) -> bytes:
    if response.status != 200:
        raise EmergencyCatalogIngestionError("mirror_http_status")
    content_type = str(response.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
    if content_type not in {"text/plain", "application/octet-stream", "text/x-text"}:
        raise EmergencyCatalogIngestionError("mirror_content_type_invalid")
    content_length = response.headers.get("Content-Length")
    if content_length:
        try:
            if int(content_length) > MAX_HTTP_BODY_BYTES:
                raise EmergencyCatalogIngestionError("mirror_body_too_large")
        except ValueError as exc:
            raise EmergencyCatalogIngestionError("mirror_content_length_invalid") from exc
    body = bytearray()
    async for chunk in response.content.iter_chunked(64 * 1024):
        body.extend(chunk)
        if len(body) > MAX_HTTP_BODY_BYTES:
            raise EmergencyCatalogIngestionError("mirror_body_too_large")
    return bytes(body)


async def fetch_approved_mirror(mirror: ApprovedSourceMirror) -> bytes:
    timeout = aiohttp.ClientTimeout(total=20, connect=8, sock_read=12)
    headers = {
        "Accept": "text/plain, application/octet-stream;q=0.8",
        "User-Agent": "POKROV-emergency-catalog/1",
    }
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        async with session.get(mirror.url, allow_redirects=False) as response:
            if str(response.url) != mirror.url:
                raise EmergencyCatalogIngestionError("mirror_url_changed")
            return await _read_bounded_response(response)


async def fetch_approved_source_bundle(
    *,
    fetcher: Callable[[ApprovedSourceMirror], Awaitable[bytes]] = fetch_approved_mirror,
) -> EmergencySourceBundle:
    """Require an exact 2/3 digest quorum for each hard-coded feed."""

    responses: dict[str, list[tuple[str, bytes]]] = defaultdict(list)
    for mirror in APPROVED_MIRRORS:
        try:
            payload = await fetcher(mirror)
            if not isinstance(payload, bytes) or len(payload) > MAX_HTTP_BODY_BYTES:
                raise EmergencyCatalogIngestionError("mirror_payload_invalid")
            responses[mirror.feed_name].append((mirror.name, payload))
        except (EmergencyCatalogIngestionError, EmergencyCatalogSourceError, TimeoutError, aiohttp.ClientError):
            continue

    selected_payloads: dict[str, bytes] = {}
    feed_digests: dict[str, str] = {}
    mirror_quorum: dict[str, tuple[str, ...]] = {}
    for feed_name in (MOBILE_FEED, SNI_FEED):
        digest_groups: dict[str, list[tuple[str, bytes]]] = defaultdict(list)
        for mirror_name, payload in responses.get(feed_name, []):
            digest_groups[hashlib.sha256(payload).hexdigest()].append((mirror_name, payload))
        quorum_groups = [
            (digest, values)
            for digest, values in digest_groups.items()
            if len(values) >= MIN_MIRROR_QUORUM
        ]
        if not quorum_groups:
            raise EmergencyCatalogIngestionError("mirror_quorum_missing")
        quorum_groups.sort(key=lambda item: (-len(item[1]), item[0]))
        selected_digest, selected = quorum_groups[0]
        selected_payloads[feed_name] = selected[0][1]
        feed_digests[feed_name] = selected_digest
        mirror_quorum[feed_name] = tuple(sorted(name for name, _payload in selected))

    combined_hasher = hashlib.sha256()
    for feed_name in sorted(feed_digests):
        combined_hasher.update(feed_name.encode("utf-8"))
        combined_hasher.update(b"\0")
        combined_hasher.update(feed_digests[feed_name].encode("ascii"))
        combined_hasher.update(b"\0")
    source_digest = combined_hasher.hexdigest()

    materials: list[EmergencyEndpointMaterial] = []
    seen_ids: set[str] = set()
    candidate_line_count = 0
    rejection_counts: Counter[str] = Counter()
    for feed_name in (MOBILE_FEED, SNI_FEED):
        parsed = parse_emergency_source(selected_payloads[feed_name])
        candidate_line_count += parsed.candidate_line_count
        rejection_counts.update(row.code for row in parsed.rejected)
        for material in parsed.accepted:
            if material.stable_id in seen_ids:
                rejection_counts["duplicate_across_feeds"] += 1
                continue
            seen_ids.add(material.stable_id)
            materials.append(material)
    if not materials:
        raise EmergencyCatalogIngestionError("source_has_no_accepted_candidates")

    return EmergencySourceBundle(
        materials=tuple(materials),
        source_revision=source_digest[:40],
        source_digest=source_digest,
        feed_digests=dict(feed_digests),
        mirror_quorum=dict(mirror_quorum),
        candidate_line_count=candidate_line_count,
        rejection_counts=dict(sorted(rejection_counts.items())),
    )
