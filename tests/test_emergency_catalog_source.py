from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from portal_bot.emergency_catalog_source import (
    EmergencyCatalogSourceError,
    EndpointVerification,
    MAX_SOURCE_BYTES,
    parse_emergency_source,
    select_verified_non_ru_candidates,
)


FIXTURE = Path(__file__).parent / "fixtures" / "emergency_catalog" / "source-v1.txt"


def test_source_fixture_accepts_only_bounded_tcp_and_grpc_reality() -> None:
    result = parse_emergency_source(FIXTURE.read_bytes())

    assert result.candidate_line_count == 8
    assert [item.transport for item in result.accepted] == ["tcp", "grpc"]
    assert all(item.stable_id.startswith("emg_") for item in result.accepted)
    assert len({item.stable_id for item in result.accepted}) == 2
    assert [row.code for row in result.rejected] == [
        "duplicate_endpoint",
        "insecure_not_allowed",
        "unsupported_transport",
        "unsupported_scheme",
        "invalid_uuid",
        "unsupported_fingerprint",
    ]


def test_source_identity_ignores_fragment_and_normalizes_raw_to_tcp() -> None:
    base = (
        "vless://11111111-1111-4111-8111-111111111111@reserve.example.com:443"
        "?type=raw&security=reality&pbk=BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
        "&sid=A1B2&sni=Cover.Example.com.&fp=chrome&flow=xtls-rprx-vision"
    )
    tcp = base.replace("type=raw", "type=tcp").replace("#first", "")
    first = parse_emergency_source(base + "#first").accepted[0]
    second = parse_emergency_source(tcp + "#second").accepted[0]

    assert first.stable_id == second.stable_id
    assert first.transport == "tcp"
    assert "reserve.example.com" not in repr(first)
    assert first.safe_projection() == {
        "stable_id": first.stable_id,
        "transport": "tcp",
        "source_contract": "pokrov-emergency-vless-reality-v1",
    }


def test_managed_outbound_contains_no_source_defined_routes_dns_or_inbounds() -> None:
    grpc = parse_emergency_source(FIXTURE.read_bytes()).accepted[1]

    outbound = grpc.managed_outbound_fields()

    assert set(outbound) == {
        "type",
        "server",
        "server_port",
        "uuid",
        "packet_encoding",
        "tls",
        "transport",
    }
    assert outbound["transport"] == {"type": "grpc", "service_name": "pokrov.test"}
    assert set(outbound["tls"]) == {"enabled", "server_name", "utls", "reality"}


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ("&sni=second.example.com", "duplicate_query_key"),
        ("&route=direct", "unknown_query_key"),
        ("&insecure=0", "insecure_not_allowed"),
        ("&extra=%7B%7D", "unknown_query_key"),
        ("&__rand=1", "unknown_query_key"),
    ],
)
def test_query_contract_fails_closed(mutation: str, code: str) -> None:
    line = (
        "vless://11111111-1111-4111-8111-111111111111@reserve.example.com:443"
        "?type=tcp&security=reality&pbk=BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
        "&sid=a1b2&sni=cover.example.com&fp=chrome"
        + mutation
    )

    result = parse_emergency_source(line)

    assert not result.accepted
    assert [item.code for item in result.rejected] == [code]
    assert line not in repr(result)


def test_grpc_mode_and_endpoint_ports_are_exact_allowlists() -> None:
    base = (
        "vless://11111111-1111-4111-8111-111111111111@reserve.example.com:{port}"
        "?type=grpc&security=reality&pbk=BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
        "&sid=a1b2&sni=cover.example.com&fp=chrome&serviceName=pokrov&mode={mode}"
    )

    assert parse_emergency_source(base.format(port=4443, mode="gun")).accepted
    assert [
        row.code for row in parse_emergency_source(base.format(port=4443, mode="multi")).rejected
    ] == ["unsupported_grpc_mode"]
    assert [
        row.code for row in parse_emergency_source(base.format(port=22, mode="gun")).rejected
    ] == ["invalid_port"]


def test_source_size_encoding_and_line_limits_are_whole_source_rejections() -> None:
    with pytest.raises(EmergencyCatalogSourceError, match="source_too_large"):
        parse_emergency_source(b"x" * (MAX_SOURCE_BYTES + 1))
    with pytest.raises(EmergencyCatalogSourceError, match="invalid_source_encoding"):
        parse_emergency_source(b"\xff")
    with pytest.raises(EmergencyCatalogSourceError, match="too_many_source_lines"):
        parse_emergency_source("\n" * 1_001)


def test_verified_selection_rejects_ru_stale_missing_and_invalid_results() -> None:
    parsed = parse_emergency_source(FIXTURE.read_bytes()).accepted
    now = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
    verifications = {
        parsed[0].stable_id: EndpointVerification("RU", now - timedelta(minutes=1)),
        parsed[1].stable_id: EndpointVerification("NL", now - timedelta(hours=25)),
    }

    selected = select_verified_non_ru_candidates(parsed, verifications, now=now)

    assert not selected.accepted
    assert [row.code for row in selected.rejected] == [
        "exit_country_ru",
        "verification_stale",
    ]


def test_verified_selection_accepts_only_fresh_trusted_non_ru_exit() -> None:
    parsed = parse_emergency_source(FIXTURE.read_bytes()).accepted
    now = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
    verifications = {
        item.stable_id: EndpointVerification("fr" if index == 0 else "NL", now)
        for index, item in enumerate(parsed)
    }

    selected = select_verified_non_ru_candidates(parsed, verifications, now=now)

    assert selected.accepted == parsed
    assert not selected.rejected
