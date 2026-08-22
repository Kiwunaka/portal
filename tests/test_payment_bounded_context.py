from __future__ import annotations

import importlib
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_ROOT = REPO_ROOT / "portal_bot"
if str(PORTAL_ROOT) not in sys.path:
    sys.path.insert(0, str(PORTAL_ROOT))


def test_payment_routes_live_only_in_ordered_transport_slice() -> None:
    api = importlib.import_module("api")
    expected = [
        "/pay/success",
        "/pay/fail",
        "/api/payments/result/{provider}",
        "/api/payments/refund/{provider}",
        "/api/payments/chargeback/{provider}",
        "/api/payments/freekassa/notify",
        "/api/payments/providers",
        "/api/payments/orders/status",
        "/api/payments/orders/create",
        "/api/payments/orders/create-public",
        "/api/payments/start-99-eligibility",
        "/api/payments/freekassa/orders/create",
        "/api/payments/freekassa/orders/create-public",
        "/api/payments/freekassa/orders/{order_id}",
        "/api/payments/freekassa/orders/{order_id}/refund",
        "/api/payments/freekassa/currencies",
        "/api/payments/freekassa/currencies/{currency}/status",
    ]
    actual = [
        path
        for route in api.app.routes
        if (path := getattr(route, "path", None))
        and (path.startswith("/api/payments") or path in {"/pay/success", "/pay/fail"})
    ]

    assert actual == expected
    assert len(actual) == len(set(actual))


def test_payment_transport_and_callback_implementation_do_not_duplicate() -> None:
    root_source = (PORTAL_ROOT / "api.py").read_text(encoding="utf-8")
    public_source = (PORTAL_ROOT / "api_public_routes.py").read_text(encoding="utf-8")
    client_source = (PORTAL_ROOT / "api_client_routes.py").read_text(encoding="utf-8")
    transport_source = (PORTAL_ROOT / "api_payment_routes.py").read_text(
        encoding="utf-8"
    )
    callback_source = (PORTAL_ROOT / "payment_callback_application.py").read_text(
        encoding="utf-8"
    )
    root_wrapper = root_source.split("async def _handle_payment_callback", 1)[1].split(
        "async def _freekassa_api_request", 1
    )[0]

    assert '"/api/payments' not in public_source
    assert '"/api/payments' not in client_source
    assert '"/pay/success"' not in public_source
    assert '"/pay/fail"' not in public_source
    assert transport_source.count('"/api/payments') == 15
    assert "SessionLocal(" not in transport_source
    assert "record_provider_checkout(" not in transport_source
    assert "_record_external_payment_event(" not in transport_source
    assert "return await handle_payment_callback(" in root_wrapper
    assert "callback_record_event" not in root_wrapper
    assert "from api import" not in callback_source
    assert "bootstrap_slice" not in callback_source
    assert callback_source.count("async def handle_payment_callback") == 1
    assert root_source.count("async def _handle_payment_callback") == 1


def test_payment_application_modules_are_explicitly_wired() -> None:
    root_source = (PORTAL_ROOT / "api.py").read_text(encoding="utf-8")
    module_map = {
        "payment_order_service": PORTAL_ROOT / "payment_order_service.py",
        "payment_callback_application": PORTAL_ROOT / "payment_callback_application.py",
        "payment_providers": PORTAL_ROOT / "payment_providers.py",
        "payment_entitlement_outbox": PORTAL_ROOT / "payment_entitlement_outbox.py",
        "payment_db_runtime": PORTAL_ROOT / "payment_db_runtime.py",
    }

    for module_name, path in module_map.items():
        assert path.is_file()
        assert module_name in root_source or module_name in (
            "payment_order_service",
            "payment_providers",
            "payment_entitlement_outbox",
        )
    assert "api_payment_routes" in root_source
