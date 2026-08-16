"""Trial/paid and RU/manual eligibility without retaining user IP addresses."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

try:
    from models import EmergencyEligibilityCache
except ImportError:  # pragma: no cover - package import
    from .models import EmergencyEligibilityCache


ELIGIBLE_ACCESS_STATES = frozenset({"trial_premium", "paid_unlimited"})
RU_CACHE_TTL = timedelta(days=7)
_SAFE_SOURCE_RE = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,31}$")


class EmergencyEligibilityError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class EmergencyEligibility:
    eligible: bool
    access_eligible: bool
    network_eligible: bool
    source: str
    country_code: str | None
    valid_until: datetime | None


def _naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def install_id_hash(install_id: str) -> str:
    value = str(install_id or "").strip()
    if not 8 <= len(value) <= 128:
        raise EmergencyEligibilityError("install_id_invalid")
    return hashlib.sha256(b"pokrov-emergency-install-v1\0" + value.encode("utf-8")).hexdigest()


def record_trusted_country(
    session,
    *,
    account_id: str,
    install_id: str,
    country_code: str,
    source: str,
    now: datetime | None = None,
) -> EmergencyEligibilityCache:
    account = str(account_id or "").strip()
    country = str(country_code or "").strip().upper()
    safe_source = str(source or "").strip().lower()
    if not account or len(account) > 36:
        raise EmergencyEligibilityError("account_id_invalid")
    if re.fullmatch(r"[A-Z]{2}", country) is None:
        raise EmergencyEligibilityError("country_code_invalid")
    if _SAFE_SOURCE_RE.fullmatch(safe_source) is None or safe_source == "client":
        raise EmergencyEligibilityError("eligibility_source_invalid")
    current = now or datetime.now(timezone.utc)
    hashed_install = install_id_hash(install_id)
    row = (
        session.query(EmergencyEligibilityCache)
        .filter_by(account_id=account, install_id_hash=hashed_install)
        .first()
    )
    if row is None:
        row = EmergencyEligibilityCache(
            account_id=account,
            install_id_hash=hashed_install,
            created_at=_naive_utc(current),
        )
        session.add(row)
    row.country_code = country
    row.source = safe_source
    row.observed_at = _naive_utc(current)
    row.expires_at = _naive_utc(current + RU_CACHE_TTL)
    row.updated_at = _naive_utc(current)
    session.flush()
    return row


def resolve_emergency_eligibility(
    session,
    *,
    account_id: str,
    install_id: str,
    access_state: str,
    manual_limited_network: bool,
    now: datetime | None = None,
) -> EmergencyEligibility:
    current = _naive_utc(now or datetime.now(timezone.utc))
    access_eligible = str(access_state or "").strip().lower() in ELIGIBLE_ACCESS_STATES
    if not access_eligible:
        return EmergencyEligibility(False, False, False, "access_denied", None, None)
    if manual_limited_network:
        return EmergencyEligibility(
            True,
            True,
            True,
            "manual_limited_network",
            None,
            current + RU_CACHE_TTL,
        )
    try:
        hashed_install = install_id_hash(install_id)
    except EmergencyEligibilityError:
        return EmergencyEligibility(False, True, False, "install_unknown", None, None)
    row = (
        session.query(EmergencyEligibilityCache)
        .filter(
            EmergencyEligibilityCache.account_id == str(account_id or "").strip(),
            EmergencyEligibilityCache.install_id_hash == hashed_install,
            EmergencyEligibilityCache.expires_at > current,
        )
        .first()
    )
    if row is None:
        return EmergencyEligibility(False, True, False, "country_unknown", None, None)
    country = str(row.country_code or "").strip().upper()
    return EmergencyEligibility(
        country == "RU",
        True,
        country == "RU",
        "cached_server_country",
        country,
        row.expires_at,
    )
