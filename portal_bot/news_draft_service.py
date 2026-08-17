from __future__ import annotations

import asyncio
import hashlib
import html
import json
import os
import re
import time
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Awaitable, Callable, Mapping, Sequence
from urllib.parse import urlparse

import aiohttp
from sqlalchemy.exc import IntegrityError

from models import NewsDraft, NewsDraftRun


MAX_FEEDS = 6
MAX_FEED_BYTES = 1_048_576
MAX_ITEMS_PER_FEED = 25
MAX_NEW_DRAFTS_PER_RUN = 6
DEFAULT_INTERVAL_SECONDS = 86_400
MIN_INTERVAL_SECONDS = 21_600
DEFAULT_FEEDS = (
    {
        "name": "Хабр · сетевые технологии",
        "url": "https://habr.com/ru/rss/hubs/network_technologies/articles/all/?fl=ru",
        "item_hosts": ["habr.com"],
    },
    {
        "name": "Хабр · информационная безопасность",
        "url": "https://habr.com/ru/rss/hubs/infosecurity/articles/all/?fl=ru",
        "item_hosts": ["habr.com"],
    },
)


class NewsDraftConfigError(ValueError):
    pass


class NewsDraftFetchError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class NewsFeed:
    name: str
    url: str
    item_hosts: tuple[str, ...]


@dataclass(frozen=True)
class NewsCandidate:
    source_name: str
    source_url: str
    title: str
    item_key: str
    published_at: datetime | None


def _env_bool(value: object, *, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def news_draft_worker_enabled(env: Mapping[str, str] | None = None) -> bool:
    source = os.environ if env is None else env
    return _env_bool(source.get("NEWS_DRAFT_WORKER_ENABLED"), default=False)


def news_draft_interval_seconds(env: Mapping[str, str] | None = None) -> int:
    source = os.environ if env is None else env
    try:
        value = int(str(source.get("NEWS_DRAFT_INTERVAL_SECONDS") or DEFAULT_INTERVAL_SECONDS))
    except ValueError as exc:
        raise NewsDraftConfigError("interval_invalid") from exc
    return max(MIN_INTERVAL_SECONDS, min(172_800, value))


def configured_news_feeds(env: Mapping[str, str] | None = None) -> tuple[NewsFeed, ...]:
    source = os.environ if env is None else env
    raw = str(source.get("NEWS_DRAFT_FEEDS_JSON") or "").strip()
    try:
        items = list(json.loads(raw)) if raw else list(DEFAULT_FEEDS)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise NewsDraftConfigError("feeds_json_invalid") from exc
    if not 1 <= len(items) <= MAX_FEEDS:
        raise NewsDraftConfigError("feeds_count_invalid")
    feeds: list[NewsFeed] = []
    for item in items:
        if not isinstance(item, dict):
            raise NewsDraftConfigError("feed_invalid")
        name = " ".join(str(item.get("name") or "").split())
        url = str(item.get("url") or "").strip()
        parsed = urlparse(url)
        if not 2 <= len(name) <= 64 or parsed.scheme != "https" or not parsed.hostname:
            raise NewsDraftConfigError("feed_invalid")
        item_hosts = tuple(
            sorted(
                {
                    str(value or "").strip().lower().rstrip(".")
                    for value in list(item.get("item_hosts") or [parsed.hostname])
                    if str(value or "").strip()
                }
            )
        )
        if not item_hosts or any(re.fullmatch(r"[a-z0-9.-]{3,253}", host) is None for host in item_hosts):
            raise NewsDraftConfigError("feed_item_hosts_invalid")
        feeds.append(NewsFeed(name=name, url=url, item_hosts=item_hosts))
    return tuple(feeds)


def _clean_title(value: object) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    return " ".join(text.split())[:300]


def _parse_datetime(value: object) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    parsed: datetime | None = None
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError, OverflowError):
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _child_text(element: ET.Element, names: Sequence[str]) -> str:
    wanted = {name.lower() for name in names}
    for child in list(element):
        local = child.tag.rsplit("}", 1)[-1].lower()
        if local in wanted and child.text:
            return child.text.strip()
    return ""


def _entry_link(element: ET.Element) -> str:
    direct = _child_text(element, ("link",))
    if direct:
        return direct
    for child in list(element):
        if child.tag.rsplit("}", 1)[-1].lower() != "link":
            continue
        href = str(child.attrib.get("href") or "").strip()
        rel = str(child.attrib.get("rel") or "alternate").strip().lower()
        if href and rel in {"", "alternate"}:
            return href
    return ""


def parse_news_feed(payload: bytes, *, source: NewsFeed, now: datetime) -> tuple[NewsCandidate, ...]:
    if not payload or len(payload) > MAX_FEED_BYTES or b"<!DOCTYPE" in payload[:4096].upper():
        raise NewsDraftFetchError("feed_payload_invalid")
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise NewsDraftFetchError("feed_xml_invalid") from exc
    elements = [
        item
        for item in root.iter()
        if item.tag.rsplit("}", 1)[-1].lower() in {"item", "entry"}
    ][:MAX_ITEMS_PER_FEED]
    candidates: list[NewsCandidate] = []
    for element in elements:
        title = _clean_title(_child_text(element, ("title",)))
        link = _entry_link(element)
        parsed_link = urlparse(link)
        host = str(parsed_link.hostname or "").lower().rstrip(".")
        if len(title) < 8 or parsed_link.scheme != "https" or host not in source.item_hosts:
            continue
        published_at = _parse_datetime(
            _child_text(element, ("pubdate", "published", "updated", "date"))
        )
        if published_at and (published_at < now - timedelta(days=14) or published_at > now + timedelta(hours=6)):
            continue
        item_id = _child_text(element, ("guid", "id")) or link
        candidates.append(
            NewsCandidate(
                source_name=source.name,
                source_url=link,
                title=title,
                item_key=item_id,
                published_at=published_at,
            )
        )
    candidates.sort(key=lambda item: item.published_at or datetime.min, reverse=True)
    return tuple(candidates)


async def fetch_news_feed(client: aiohttp.ClientSession, source: NewsFeed) -> bytes:
    try:
        async with client.get(
            source.url,
            allow_redirects=False,
            timeout=aiohttp.ClientTimeout(total=20),
            headers={"Accept": "application/rss+xml, application/atom+xml, text/xml"},
        ) as response:
            if response.status != 200:
                raise NewsDraftFetchError("feed_http_error")
            content_type = str(response.headers.get("Content-Type") or "").split(";", 1)[0].lower()
            if content_type not in {"application/rss+xml", "application/atom+xml", "application/xml", "text/xml"}:
                raise NewsDraftFetchError("feed_content_type_invalid")
            body = await response.content.read(MAX_FEED_BYTES + 1)
            if len(body) > MAX_FEED_BYTES:
                raise NewsDraftFetchError("feed_too_large")
            return body
    except asyncio.TimeoutError as exc:
        raise NewsDraftFetchError("feed_timeout") from exc
    except aiohttp.ClientError as exc:
        raise NewsDraftFetchError("feed_network_error") from exc


def ingest_news_candidates(
    session,
    *,
    run: NewsDraftRun,
    candidates: Sequence[NewsCandidate],
    now: datetime,
    max_new: int = MAX_NEW_DRAFTS_PER_RUN,
) -> dict[str, int]:
    created = 0
    duplicates = 0
    for candidate in candidates:
        item_hash = hashlib.sha256(candidate.item_key.encode("utf-8")).hexdigest()
        if session.query(NewsDraft.id).filter(NewsDraft.source_item_sha256 == item_hash).first():
            duplicates += 1
            continue
        if created >= max_new:
            break
        session.add(
            NewsDraft(
                source_name=candidate.source_name,
                source_url=candidate.source_url,
                source_title=candidate.title,
                source_item_sha256=item_hash,
                fetch_run_id=run.run_id,
                source_published_at=candidate.published_at,
                status="pending",
                discovered_at=now,
            )
        )
        try:
            session.flush()
        except IntegrityError:
            session.rollback()
            raise
        created += 1
    return {"created": created, "duplicates": duplicates}


async def collect_news_drafts(
    session_factory,
    *,
    env: Mapping[str, str] | None = None,
    now: datetime | None = None,
    fetcher: Callable[[aiohttp.ClientSession, NewsFeed], Awaitable[bytes]] = fetch_news_feed,
) -> dict[str, object]:
    started_clock = time.monotonic()
    observed_at = now or datetime.now(timezone.utc).replace(tzinfo=None)
    feeds = configured_news_feeds(env)
    run_id = str(uuid.uuid4())
    session = session_factory()
    run = NewsDraftRun(
        run_id=run_id,
        status="running",
        sources_total=len(feeds),
        started_at=observed_at,
    )
    session.add(run)
    session.commit()
    source_succeeded = 0
    source_failed = 0
    candidates: list[NewsCandidate] = []
    try:
        async with aiohttp.ClientSession() as client:
            for feed in feeds:
                try:
                    body = await fetcher(client, feed)
                    parsed = parse_news_feed(body, source=feed, now=observed_at)
                    source_succeeded += 1
                    if parsed:
                        candidates.append(parsed[0])
                except NewsDraftFetchError:
                    source_failed += 1
        ingest = ingest_news_candidates(
            session,
            run=run,
            candidates=candidates,
            now=observed_at,
        )
        run.sources_succeeded = source_succeeded
        run.sources_failed = source_failed
        run.candidates_seen = len(candidates)
        run.drafts_created = int(ingest["created"])
        run.duplicates_skipped = int(ingest["duplicates"])
        run.status = "failed" if source_succeeded == 0 else "partial" if source_failed else "completed"
        run.failure_code = "all_sources_failed" if source_succeeded == 0 else "some_sources_failed" if source_failed else None
        run.finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
        run.duration_ms = max(0, int((time.monotonic() - started_clock) * 1000))
        session.commit()
        return {
            "run_id": run_id,
            "status": run.status,
            "sources_total": len(feeds),
            "sources_succeeded": source_succeeded,
            "sources_failed": source_failed,
            "candidates_seen": len(candidates),
            "drafts_created": run.drafts_created,
            "duplicates_skipped": run.duplicates_skipped,
            "duration_ms": run.duration_ms,
        }
    except Exception:
        session.rollback()
        run = session.query(NewsDraftRun).filter(NewsDraftRun.run_id == run_id).first()
        if run is not None:
            run.status = "failed"
            run.failure_code = "internal"
            run.finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
            run.duration_ms = max(0, int((time.monotonic() - started_clock) * 1000))
            session.commit()
        raise
    finally:
        session.close()
