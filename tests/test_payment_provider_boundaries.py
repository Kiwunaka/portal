from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException


ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT = ROOT / "portal_bot"
if str(PORTAL_BOT) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT))

providers = importlib.import_module("payment_providers")


@pytest.mark.parametrize(
    "payload",
    [
        {"location": "https://pay.fk.money/order/one"},
        {"paymentUrl": "https://pay.fk.money/order/two"},
        {"data": {"url": "https://pay.fk.money/order/three"}},
        {"result": {"link": "https://pay.fk.money/order/four"}},
    ],
)
def test_freekassa_parser_accepts_known_shapes_on_exact_https_host(
    monkeypatch,
    payload: dict,
) -> None:
    monkeypatch.setenv("FREEKASSA_PAY_HOST", "pay.fk.money")
    result = providers.parse_freekassa_payment_url(payload, "ignored", source="bot")
    assert result.startswith("https://pay.fk.money/order/")


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"location": ""},
        {"location": "http://pay.fk.money/order/one"},
        {"location": "https://pay.fk.money.evil.example/order/one"},
        {"location": "https://user@pay.fk.money/order/one"},
        {"location": "https://pay.fk.money"},
    ],
)
def test_freekassa_parser_fails_closed_without_synthetic_fallback(
    monkeypatch,
    payload: dict,
) -> None:
    monkeypatch.setenv("FREEKASSA_PAY_HOST", "pay.fk.money")
    with pytest.raises(HTTPException) as caught:
        providers.parse_freekassa_payment_url(
            payload,
            "must-not-be-used",
            source="site",
        )
    assert caught.value.status_code == 502
    assert "oa=0" not in str(caught.value.detail)


def test_api_composition_has_no_duplicate_or_zero_amount_parser_fallback() -> None:
    api_source = (PORTAL_BOT / "api.py").read_text(encoding="utf-8-sig")
    provider_source = (PORTAL_BOT / "payment_providers.py").read_text(
        encoding="utf-8-sig"
    )
    assert "def _parse_freekassa_payment_url" not in api_source
    assert provider_source.count("def parse_freekassa_payment_url(") == 1
    assert "oa=0" not in api_source
    assert "oa=0" not in provider_source
