"""Local-only country lookup for emergency-network eligibility.

The raw client address is read in memory, looked up in an operator-owned MMDB
file and discarded. Only the resulting country code and a hashed install ID are
stored by :mod:`emergency_eligibility_service`.
"""

from __future__ import annotations

import ipaddress
import os
import threading
from pathlib import Path
from typing import Any

try:
    import geoip2.database
    from geoip2.errors import AddressNotFoundError
except ImportError:  # pragma: no cover - optional until runtime dependency install
    geoip2 = None  # type: ignore[assignment]
    AddressNotFoundError = LookupError  # type: ignore[assignment,misc]

try:
    from emergency_eligibility_service import (
        EmergencyEligibilityError,
        record_trusted_country,
    )
except ImportError:  # pragma: no cover - package import
    from .emergency_eligibility_service import (
        EmergencyEligibilityError,
        record_trusted_country,
    )


DEFAULT_COUNTRY_DB_PATH = "/var/lib/pokrov-geoip/dbip-country-lite.mmdb"
DEFAULT_TRUSTED_PROXY_CIDRS = "127.0.0.0/8,::1/128"

_reader_lock = threading.Lock()
_reader: Any | None = None
_reader_identity: tuple[str, int, int] | None = None


def _trusted_proxy_networks(
    raw: str | None = None,
) -> tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...]:
    value = raw if raw is not None else os.getenv(
        "EMERGENCY_TRUSTED_PROXY_CIDRS",
        DEFAULT_TRUSTED_PROXY_CIDRS,
    )
    networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    for item in str(value or "").split(","):
        candidate = item.strip()
        if not candidate:
            continue
        try:
            networks.append(ipaddress.ip_network(candidate, strict=True))
        except ValueError:
            return ()
    return tuple(networks)


def _public_ip(value: object) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        address = ipaddress.ip_address(str(value or "").strip())
    except ValueError:
        return None
    return address if address.is_global else None


def request_public_ip(request: Any) -> str | None:
    """Return a public IP only when proxy provenance is locally trusted."""

    peer = _public_ip(getattr(getattr(request, "client", None), "host", ""))
    raw_peer = str(getattr(getattr(request, "client", None), "host", "") or "").strip()
    try:
        peer_address = ipaddress.ip_address(raw_peer)
    except ValueError:
        return None
    trusted_proxy = any(
        peer_address.version == network.version and peer_address in network
        for network in _trusted_proxy_networks()
    )
    if trusted_proxy:
        forwarded = str(getattr(request, "headers", {}).get("x-forwarded-for", ""))
        candidate = _public_ip(forwarded.split(",", 1)[0])
        return str(candidate) if candidate is not None else None
    return str(peer) if peer is not None else None


def _country_reader(path: Path) -> Any:
    global _reader, _reader_identity

    resolved = path.resolve(strict=True)
    stat = resolved.stat()
    identity = (str(resolved), int(stat.st_mtime_ns), int(stat.st_size))
    with _reader_lock:
        if _reader is not None and _reader_identity == identity:
            return _reader
        if geoip2 is None:
            raise RuntimeError("geoip_runtime_unavailable")
        next_reader = geoip2.database.Reader(str(resolved))
        previous = _reader
        _reader = next_reader
        _reader_identity = identity
        if previous is not None:
            previous.close()
        return next_reader


def lookup_country_code(ip_value: str, *, database_path: str | None = None) -> str | None:
    address = _public_ip(ip_value)
    if address is None:
        return None
    path = Path(
        database_path
        or os.getenv("EMERGENCY_GEOIP_COUNTRY_DB_PATH", DEFAULT_COUNTRY_DB_PATH)
    )
    try:
        response = _country_reader(path).country(str(address))
        country = str(response.country.iso_code or "").strip().upper()
    except (AddressNotFoundError, FileNotFoundError, OSError, RuntimeError, ValueError):
        return None
    return country if len(country) == 2 and country.isalpha() else None


def observe_request_country(
    session: Any,
    *,
    request: Any,
    account_id: str,
    install_id: str,
) -> str | None:
    """Cache a local lookup result without persisting or logging the raw IP."""

    ip_value = request_public_ip(request)
    if ip_value is None:
        return None
    country = lookup_country_code(ip_value)
    if country is None:
        return None
    try:
        record_trusted_country(
            session,
            account_id=account_id,
            install_id=install_id,
            country_code=country,
            source="dbip_local",
        )
    except EmergencyEligibilityError:
        return None
    return country
