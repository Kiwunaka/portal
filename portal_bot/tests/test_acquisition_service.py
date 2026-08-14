from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1]
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

NOW = datetime(2026, 8, 14, 12, 0, 0)


def _session(tmp_path: Path):
    from models import Base

    engine = create_engine(f"sqlite:///{(tmp_path / 'acquisition.db').as_posix()}")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


def _touch(**overrides):
    from acquisition_service import normalize_acquisition_touch

    values = {
        "source": "telegram_ads",
        "channel": "marketing",
        "campaign": "aug_launch",
        "content": "video_03",
        "referral": "creator_17",
        "entry_route": "/mobile/?secret=must-not-stay",
        "referrer": "https://search.example/path?q=must-not-stay",
    }
    values.update(overrides)
    return normalize_acquisition_touch(**values)


def test_first_touch_is_immutable_and_last_touch_updates(tmp_path: Path) -> None:
    from acquisition_service import upsert_acquisition_session

    engine, session = _session(tmp_path)
    try:
        first = upsert_acquisition_session(
            session,
            raw_session_id="browser-session-0001",
            touch=_touch(),
            now=NOW,
        )
        session.commit()
        second = upsert_acquisition_session(
            session,
            raw_session_id="browser-session-0001",
            touch=_touch(source="direct", campaign="return_visit", entry_route="/pricing/"),
            now=NOW + timedelta(hours=2),
        )
        session.commit()

        assert first.id == second.id
        assert second.first_source == "telegram_ads"
        assert second.first_campaign == "aug_launch"
        assert second.first_entry_route == "/mobile/"
        assert second.last_source == "direct"
        assert second.last_campaign == "return_visit"
        assert second.last_entry_route == "/pricing/"
        assert second.first_referrer_host == "search.example"
    finally:
        session.close()
        engine.dispose()


def test_funnel_event_hashes_session_and_drops_raw_urls_and_meta(tmp_path: Path) -> None:
    from acquisition_service import record_funnel_event
    from models import FunnelEvent

    engine, session = _session(tmp_path)
    try:
        raw_session_id = "browser-session-private-0002"
        _, event = record_funnel_event(
            session,
            raw_session_id=raw_session_id,
            event_name="download_click",
            stage="download",
            touch=_touch(),
            meta={
                "asset": "pokrov-android-arm64-v8a.apk",
                "platform": "android",
                "href": "https://example.test/private?token=secret",
                "text": "raw button copy",
            },
            now=NOW,
        )
        session.commit()
        stored = session.query(FunnelEvent).filter(FunnelEvent.id == event.id).one()

        assert stored.session_id != raw_session_id
        assert len(stored.session_id) == 64
        assert stored.path == "/mobile/"
        assert stored.referrer == "search.example"
        assert json.loads(stored.meta_json) == {
            "platform": "android",
            "asset": "pokrov-android-arm64-v8a.apk",
        }
        serialized = " ".join(str(value or "") for value in vars(stored).values())
        assert "secret" not in serialized
        assert "raw button copy" not in serialized
    finally:
        session.close()
        engine.dispose()


def test_handoff_is_opaque_one_time_and_cross_account_closed(tmp_path: Path) -> None:
    from acquisition_service import AcquisitionError, consume_acquisition_handoff, create_acquisition_handoff

    engine, session = _session(tmp_path)
    try:
        raw_handle, handoff = create_acquisition_handoff(
            session,
            raw_session_id="browser-session-0003",
            touch=_touch(),
            purpose="android_install",
            asset="pokrov-android-arm64-v8a.apk",
            now=NOW,
        )
        session.commit()
        assert len(raw_handle) >= 32
        assert handoff.token_hash != raw_handle

        _, acquisition, snapshot = consume_acquisition_handoff(
            session,
            raw_handle=raw_handle,
            expected_purpose="android_install",
            bound_tg_id=7001,
            bound_account_id="account-a",
            now=NOW + timedelta(minutes=10),
        )
        session.commit()
        assert acquisition.bound_tg_id == 7001
        assert snapshot["first"]["campaign"] == "aug_launch"

        with pytest.raises(AcquisitionError, match="handoff_already_consumed"):
            consume_acquisition_handoff(
                session,
                raw_handle=raw_handle,
                expected_purpose="android_install",
                bound_tg_id=7002,
                bound_account_id="account-b",
                now=NOW + timedelta(minutes=11),
            )
    finally:
        session.rollback()
        session.close()
        engine.dispose()


def test_expired_and_wrong_purpose_handoffs_fail_closed(tmp_path: Path) -> None:
    from acquisition_service import AcquisitionError, consume_acquisition_handoff, create_acquisition_handoff

    engine, session = _session(tmp_path)
    try:
        raw_handle, _ = create_acquisition_handoff(
            session,
            raw_session_id="browser-session-0004",
            touch=_touch(),
            purpose="checkout",
            now=NOW,
        )
        session.commit()
        with pytest.raises(AcquisitionError, match="handoff_purpose_mismatch"):
            consume_acquisition_handoff(
                session,
                raw_handle=raw_handle,
                expected_purpose="account_continue",
                now=NOW + timedelta(minutes=1),
            )
        with pytest.raises(AcquisitionError, match="handoff_expired"):
            consume_acquisition_handoff(
                session,
                raw_handle=raw_handle,
                expected_purpose="checkout",
                now=NOW + timedelta(hours=73),
            )
    finally:
        session.rollback()
        session.close()
        engine.dispose()
