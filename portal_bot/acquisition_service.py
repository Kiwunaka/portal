from __future__ import annotations

import hashlib
import json
import re
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping
from urllib.parse import urlparse

from sqlalchemy.exc import IntegrityError

try:
    from .models import AcquisitionHandoff, AcquisitionSession, FunnelEvent
except ImportError:
    from models import AcquisitionHandoff, AcquisitionSession, FunnelEvent


ACQUISITION_RETENTION_DAYS = 180
ACQUISITION_HANDOFF_TTL_HOURS = 72
ACQUISITION_HANDOFF_PURPOSES = {
    "android_install",
    "windows_install",
    "account_continue",
    "checkout",
    "telegram_continue",
}
ACQUISITION_ASSETS = {
    "pokrov-android-arm64-v8a.apk",
    "pokrov-android-armeabi-v7a.apk",
    "pokrov-android-universal.apk",
    "pokrov-android-x86_64.apk",
    "pokrov-windows-setup-x64.exe",
}
_SESSION_KEY_RE = re.compile(r"^[A-Za-z0-9._:-]{8,96}$")
_SAFE_SLUG_RE = re.compile(r"[^a-z0-9_.:-]+")
_SAFE_ROUTE_RE = re.compile(r"^/[A-Za-z0-9/_-]*$")


class AcquisitionError(ValueError):
    def __init__(self, code: str, *, status_code: int = 400) -> None:
        super().__init__(code)
        self.code = code
        self.status_code = int(status_code)


@dataclass(frozen=True)
class AcquisitionTouch:
    source: str
    channel: str
    campaign: str
    content: str
    referral: str
    entry_route: str
    referrer_host: str


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def clean_acquisition_slug(value: object, *, default: str = "", max_len: int = 64) -> str:
    raw = str(value or "").strip().lower()
    raw = _SAFE_SLUG_RE.sub("_", raw).strip("._:-")
    return (raw or default)[:max_len]


def clean_entry_route(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "/"
    try:
        parsed = urlparse(raw)
    except ValueError:
        return "/"
    path = parsed.path or "/"
    if not path.startswith("/") or not _SAFE_ROUTE_RE.fullmatch(path):
        return "/"
    return path[:128]


def clean_referrer_host(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        parsed = urlparse(raw)
    except ValueError:
        return ""
    if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
        return ""
    host = str(parsed.hostname or "").strip().lower().rstrip(".")
    if not host or len(host) > 128 or not re.fullmatch(r"[a-z0-9.-]+", host):
        return ""
    return host


def normalize_acquisition_touch(
    *,
    source: object,
    channel: object,
    campaign: object = "",
    content: object = "",
    referral: object = "",
    entry_route: object = "/",
    referrer: object = "",
) -> AcquisitionTouch:
    normalized_channel = clean_acquisition_slug(channel, default="site", max_len=32)
    if normalized_channel not in {"site", "marketing", "checkout", "webapp", "bot", "app"}:
        normalized_channel = "site"
    referrer_host = clean_referrer_host(referrer)
    normalized_source = clean_acquisition_slug(source, default="", max_len=64)
    if not normalized_source and referrer_host:
        normalized_source = clean_acquisition_slug(referrer_host, default="unknown", max_len=64)
    return AcquisitionTouch(
        source=normalized_source or "unknown",
        channel=normalized_channel,
        campaign=clean_acquisition_slug(campaign, max_len=64),
        content=clean_acquisition_slug(content, max_len=64),
        referral=clean_acquisition_slug(referral, max_len=64),
        entry_route=clean_entry_route(entry_route),
        referrer_host=referrer_host,
    )


def session_key_hash(raw_session_id: object) -> str:
    raw = str(raw_session_id or "").strip()
    if not _SESSION_KEY_RE.fullmatch(raw):
        raise AcquisitionError("invalid_session_id")
    return hashlib.sha256(f"pokrov-acquisition-session-v1:{raw}".encode("utf-8")).hexdigest()


def handoff_token_hash(raw_handle: object) -> str:
    raw = str(raw_handle or "").strip()
    if len(raw) < 32 or len(raw) > 160 or not re.fullmatch(r"[A-Za-z0-9_-]+", raw):
        raise AcquisitionError("invalid_handoff")
    return hashlib.sha256(f"pokrov-acquisition-handoff-v1:{raw}".encode("utf-8")).hexdigest()


def _set_touch_fields(row: AcquisitionSession, touch: AcquisitionTouch, *, prefix: str) -> None:
    setattr(row, f"{prefix}_source", touch.source)
    setattr(row, f"{prefix}_channel", touch.channel)
    setattr(row, f"{prefix}_campaign", touch.campaign or None)
    setattr(row, f"{prefix}_content", touch.content or None)
    setattr(row, f"{prefix}_ref", touch.referral or None)
    setattr(row, f"{prefix}_entry_route", touch.entry_route)
    setattr(row, f"{prefix}_referrer_host", touch.referrer_host or None)


def upsert_acquisition_session(
    session,
    *,
    raw_session_id: object,
    touch: AcquisitionTouch,
    now: datetime | None = None,
) -> AcquisitionSession:
    observed_at = now or _utcnow()
    key_hash = session_key_hash(raw_session_id)
    row = (
        session.query(AcquisitionSession)
        .filter(AcquisitionSession.session_key_hash == key_hash)
        .with_for_update()
        .first()
    )
    if row is None:
        row = AcquisitionSession(
            id=str(uuid.uuid4()),
            session_key_hash=key_hash,
            created_at=observed_at,
            first_touch_at=observed_at,
            last_touch_at=observed_at,
            expires_at=observed_at + timedelta(days=ACQUISITION_RETENTION_DAYS),
        )
        _set_touch_fields(row, touch, prefix="first")
        _set_touch_fields(row, touch, prefix="last")
        try:
            with session.begin_nested():
                session.add(row)
                session.flush()
        except IntegrityError:
            row = (
                session.query(AcquisitionSession)
                .filter(AcquisitionSession.session_key_hash == key_hash)
                .with_for_update()
                .one()
            )
    _set_touch_fields(row, touch, prefix="last")
    row.last_touch_at = observed_at
    row.expires_at = max(
        row.expires_at or observed_at,
        observed_at + timedelta(days=ACQUISITION_RETENTION_DAYS),
    )
    return row


def sanitize_funnel_meta(event_name: str, meta: Mapping[str, Any] | None) -> dict[str, str]:
    raw = meta if isinstance(meta, Mapping) else {}
    out: dict[str, str] = {}
    for key in ("cta_id", "platform", "error_category"):
        value = clean_acquisition_slug(raw.get(key), max_len=64)
        if value:
            out[key] = value
    asset = str(raw.get("asset") or "").strip()
    if event_name == "download_click" and asset in ACQUISITION_ASSETS:
        out["asset"] = asset
    return out


def record_funnel_event(
    session,
    *,
    raw_session_id: object,
    event_name: str,
    stage: str,
    touch: AcquisitionTouch,
    meta: Mapping[str, Any] | None = None,
    now: datetime | None = None,
) -> tuple[AcquisitionSession, FunnelEvent]:
    observed_at = now or _utcnow()
    acquisition = upsert_acquisition_session(
        session,
        raw_session_id=raw_session_id,
        touch=touch,
        now=observed_at,
    )
    safe_meta = sanitize_funnel_meta(event_name, meta)
    row = FunnelEvent(
        session_id=acquisition.session_key_hash,
        tg_id=acquisition.bound_tg_id,
        channel=touch.channel,
        event_name=event_name,
        stage=stage,
        source=touch.source,
        path=touch.entry_route,
        referrer=touch.referrer_host or None,
        campaign=touch.campaign or None,
        meta_json=(json.dumps(safe_meta, ensure_ascii=True, separators=(",", ":")) if safe_meta else None),
        created_at=observed_at,
    )
    session.add(row)
    return acquisition, row


def create_acquisition_handoff(
    session,
    *,
    raw_session_id: object,
    touch: AcquisitionTouch,
    purpose: object,
    asset: object = "",
    now: datetime | None = None,
) -> tuple[str, AcquisitionHandoff]:
    observed_at = now or _utcnow()
    normalized_purpose = clean_acquisition_slug(purpose, max_len=32)
    if normalized_purpose not in ACQUISITION_HANDOFF_PURPOSES:
        raise AcquisitionError("invalid_handoff_purpose")
    normalized_asset = str(asset or "").strip()
    if normalized_asset and normalized_asset not in ACQUISITION_ASSETS:
        raise AcquisitionError("invalid_handoff_asset")
    acquisition = upsert_acquisition_session(
        session,
        raw_session_id=raw_session_id,
        touch=touch,
        now=observed_at,
    )
    raw_handle = secrets.token_urlsafe(32)
    handoff = AcquisitionHandoff(
        id=str(uuid.uuid4()),
        token_hash=handoff_token_hash(raw_handle),
        acquisition_session_id=acquisition.id,
        purpose=normalized_purpose,
        asset=normalized_asset or None,
        impression_public_id=f"imp_{secrets.token_hex(16)}",
        click_public_id=f"clk_{secrets.token_hex(16)}",
        created_at=observed_at,
        expires_at=observed_at + timedelta(hours=ACQUISITION_HANDOFF_TTL_HOURS),
    )
    session.add(handoff)
    session.flush()
    return raw_handle, handoff


def acquisition_snapshot(row: AcquisitionSession) -> dict[str, Any]:
    return {
        "first": {
            "source": row.first_source or "unknown",
            "channel": row.first_channel or "site",
            "campaign": row.first_campaign,
            "content": row.first_content,
            "ref": row.first_ref,
            "entry_route": row.first_entry_route or "/",
        },
        "last": {
            "source": row.last_source or "unknown",
            "channel": row.last_channel or "site",
            "campaign": row.last_campaign,
            "content": row.last_content,
            "ref": row.last_ref,
            "entry_route": row.last_entry_route or "/",
        },
    }


def consume_acquisition_handoff(
    session,
    *,
    raw_handle: object,
    expected_purpose: str,
    bound_tg_id: int | None = None,
    bound_account_id: str | None = None,
    bound_order_id: str | None = None,
    now: datetime | None = None,
) -> tuple[AcquisitionHandoff, AcquisitionSession, dict[str, Any]]:
    observed_at = now or _utcnow()
    token_hash = handoff_token_hash(raw_handle)
    handoff = (
        session.query(AcquisitionHandoff)
        .filter(AcquisitionHandoff.token_hash == token_hash)
        .with_for_update()
        .first()
    )
    if handoff is None:
        raise AcquisitionError("handoff_not_found", status_code=404)
    if handoff.purpose != expected_purpose:
        raise AcquisitionError("handoff_purpose_mismatch", status_code=409)
    if handoff.consumed_at is not None:
        raise AcquisitionError("handoff_already_consumed", status_code=409)
    if handoff.expires_at is None or handoff.expires_at <= observed_at:
        raise AcquisitionError("handoff_expired", status_code=410)
    acquisition = (
        session.query(AcquisitionSession)
        .filter(AcquisitionSession.id == handoff.acquisition_session_id)
        .with_for_update()
        .first()
    )
    if acquisition is None:
        raise AcquisitionError("handoff_session_missing", status_code=409)
    normalized_account_id = str(bound_account_id or "").strip() or None
    if acquisition.bound_tg_id is not None and bound_tg_id is not None and int(acquisition.bound_tg_id) != int(bound_tg_id):
        raise AcquisitionError("handoff_cross_account", status_code=409)
    if acquisition.bound_account_id and normalized_account_id and acquisition.bound_account_id != normalized_account_id:
        raise AcquisitionError("handoff_cross_account", status_code=409)
    handoff.consumed_at = observed_at
    handoff.bound_tg_id = int(bound_tg_id) if bound_tg_id is not None else None
    handoff.bound_account_id = normalized_account_id
    handoff.bound_order_id = str(bound_order_id or "").strip()[:128] or None
    if bound_tg_id is not None:
        acquisition.bound_tg_id = int(bound_tg_id)
    if normalized_account_id:
        acquisition.bound_account_id = normalized_account_id
    return handoff, acquisition, acquisition_snapshot(acquisition)
