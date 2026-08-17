from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

from models import Base, NewsDraft, NewsDraftRun  # noqa: E402
from news_draft_service import (  # noqa: E402
    MAX_FEED_BYTES,
    NewsDraftFetchError,
    NewsFeed,
    collect_news_drafts,
    configured_news_feeds,
    fetch_news_feed,
    parse_news_feed,
)


RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Test</title>
  <item><title>IPv6 and network routing update</title><link>https://habr.com/ru/articles/123456/</link><guid>https://habr.com/ru/articles/123456/</guid><pubDate>Mon, 17 Aug 2026 08:00:00 +0300</pubDate></item>
</channel></rss>"""


def _session_factory(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'news.db').as_posix()}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def test_feed_parser_accepts_only_owned_item_hosts_and_current_items() -> None:
    source = NewsFeed(
        name="Хабр",
        url="https://habr.com/ru/rss/hubs/network_technologies/articles/all/?fl=ru",
        item_hosts=("habr.com",),
    )
    parsed = parse_news_feed(RSS, source=source, now=datetime(2026, 8, 17, 12, 0, 0))
    assert len(parsed) == 1
    assert parsed[0].source_url == "https://habr.com/ru/articles/123456/"
    foreign = RSS.replace(
        b"https://habr.com/ru/articles/123456/", b"https://evil.example/item"
    )
    assert (
        parse_news_feed(foreign, source=source, now=datetime(2026, 8, 17, 12, 0, 0))
        == ()
    )
    try:
        parse_news_feed(
            b"<!DOCTYPE html><html></html>",
            source=source,
            now=datetime(2026, 8, 17, 12, 0, 0),
        )
    except NewsDraftFetchError as exc:
        assert exc.code == "feed_payload_invalid"
    else:
        raise AssertionError("HTML payload must fail closed")


def test_feed_fetch_consumes_every_chunk_and_keeps_the_size_cap() -> None:
    source = NewsFeed(
        name="Хабр",
        url="https://habr.com/feed",
        item_hosts=("habr.com",),
    )

    class FakeContent:
        def __init__(self, chunks):
            self.chunks = chunks

        async def iter_chunked(self, _size):
            for chunk in self.chunks:
                yield chunk

    class FakeResponse:
        status = 200
        headers = {"Content-Type": "text/xml; charset=utf-8"}

        def __init__(self, chunks):
            self.content = FakeContent(chunks)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

    class FakeClient:
        def __init__(self, chunks):
            self.response = FakeResponse(chunks)

        def get(self, *_args, **_kwargs):
            return self.response

    assert (
        asyncio.run(fetch_news_feed(FakeClient([b"one", b"two"]), source)) == b"onetwo"
    )
    try:
        asyncio.run(
            fetch_news_feed(
                FakeClient([b"x" * MAX_FEED_BYTES, b"y"]),
                source,
            )
        )
    except NewsDraftFetchError as exc:
        assert exc.code == "feed_too_large"
    else:
        raise AssertionError("Oversized feed must fail closed")


def test_daily_collection_deduplicates_cross_feed_items_and_retains_safe_run_status(
    tmp_path: Path,
) -> None:
    factory = _session_factory(tmp_path)

    async def fake_fetch(_client, _source):
        return RSS

    env = {
        "NEWS_DRAFT_FEEDS_JSON": """[
          {"name":"Сети","url":"https://habr.com/feed-one","item_hosts":["habr.com"]},
          {"name":"Безопасность","url":"https://habr.com/feed-two","item_hosts":["habr.com"]}
        ]""",
    }
    first = asyncio.run(
        collect_news_drafts(
            factory,
            env=env,
            now=datetime(2026, 8, 17, 12, 0, 0),
            fetcher=fake_fetch,
        )
    )
    assert first["status"] == "completed"
    assert first["drafts_created"] == 1
    assert first["duplicates_skipped"] == 1

    second = asyncio.run(
        collect_news_drafts(
            factory,
            env=env,
            now=datetime(2026, 8, 17, 13, 0, 0),
            fetcher=fake_fetch,
        )
    )
    assert second["drafts_created"] == 0
    assert second["duplicates_skipped"] == 2

    session = factory()
    try:
        assert session.query(NewsDraft).count() == 1
        runs = session.query(NewsDraftRun).order_by(NewsDraftRun.id).all()
        assert [row.status for row in runs] == ["completed", "completed"]
        assert all(row.failure_code is None for row in runs)
    finally:
        session.close()


def test_default_feed_configuration_is_bounded_https() -> None:
    feeds = configured_news_feeds({})
    assert 1 <= len(feeds) <= 6
    assert all(feed.url.startswith("https://") for feed in feeds)
    assert all(feed.item_hosts for feed in feeds)
