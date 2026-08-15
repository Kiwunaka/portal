from __future__ import annotations

import gzip
from pathlib import Path
from types import SimpleNamespace

from portal_bot import emergency_geoip_refresh, emergency_geoip_service


def _request(peer: str, forwarded: str = "") -> SimpleNamespace:
    return SimpleNamespace(
        client=SimpleNamespace(host=peer),
        headers={"x-forwarded-for": forwarded} if forwarded else {},
    )


def test_request_ip_trusts_only_the_local_proxy_and_rejects_private_values(monkeypatch) -> None:
    monkeypatch.setenv("EMERGENCY_TRUSTED_PROXY_CIDRS", "127.0.0.0/8,::1/128")

    assert emergency_geoip_service.request_public_ip(_request("127.0.0.1", "8.8.8.8")) == "8.8.8.8"
    assert emergency_geoip_service.request_public_ip(_request("127.0.0.1", "10.0.0.1")) is None
    assert emergency_geoip_service.request_public_ip(_request("1.1.1.1", "8.8.8.8")) == "1.1.1.1"
    assert emergency_geoip_service.request_public_ip(_request("not-an-ip", "8.8.8.8")) is None


def test_observation_persists_country_only_and_never_passes_raw_ip(monkeypatch) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(emergency_geoip_service, "lookup_country_code", lambda value: "RU")
    monkeypatch.setattr(
        emergency_geoip_service,
        "record_trusted_country",
        lambda session, **values: captured.update(values),
    )

    country = emergency_geoip_service.observe_request_country(
        object(),
        request=_request("127.0.0.1", "8.8.8.8"),
        account_id="account-1",
        install_id="install-12345678",
    )

    assert country == "RU"
    assert captured == {
        "account_id": "account-1",
        "install_id": "install-12345678",
        "country_code": "RU",
        "source": "dbip_local",
    }
    assert "8.8.8.8" not in repr(captured)


def test_geoip_refresh_is_atomic_and_bounded(monkeypatch, tmp_path: Path) -> None:
    database = b"safe-mmdb-fixture"
    compressed = gzip.compress(database)
    monkeypatch.setattr(emergency_geoip_refresh, "_download", lambda month: compressed)
    monkeypatch.setattr(emergency_geoip_refresh, "_validate_database", lambda path: None)
    output = tmp_path / "country.mmdb"

    result = emergency_geoip_refresh.refresh_database(output)

    assert output.read_bytes() == database
    assert result["source"] == "dbip-country-lite"
    assert result["database_bytes"] == len(database)

    monkeypatch.setattr(emergency_geoip_refresh, "MAX_DATABASE_BYTES", 8)
    monkeypatch.setattr(
        emergency_geoip_refresh,
        "_download",
        lambda month: gzip.compress(b"x" * 32),
    )
    oversized = tmp_path / "oversized.mmdb"
    try:
        emergency_geoip_refresh.refresh_database(oversized)
    except RuntimeError as exc:
        assert str(exc) == "geoip_database_too_large"
    else:  # pragma: no cover - explicit negative oracle
        raise AssertionError("oversized database was accepted")
    assert not oversized.exists()
