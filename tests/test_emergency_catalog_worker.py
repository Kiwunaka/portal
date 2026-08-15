from __future__ import annotations

import asyncio
import base64
import hashlib
import os
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))

import models  # noqa: E402
from emergency_catalog_crypto import EmergencyCatalogCrypto  # noqa: E402
from emergency_catalog_ingestion import EmergencySourceBundle  # noqa: E402
from emergency_catalog_probe import EmergencyProbeError  # noqa: E402
from emergency_catalog_service import EndpointProbeResult  # noqa: E402
from emergency_catalog_source import parse_emergency_source  # noqa: E402
from emergency_catalog_worker import (  # noqa: E402
    CONTROLLED_PROBE_URL,
    DEFAULT_INTERVAL_SECONDS,
    EmergencyCatalogWorkerConfig,
    EmergencyCatalogWorkerError,
    emergency_catalog_worker_enabled,
    load_emergency_catalog_worker_config,
    run_emergency_catalog_once,
)


EXPECTED_DIGEST = hashlib.sha256(b"controlled-pokrov-payload").hexdigest()
NOW = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)


def _material(index: int):
    key_char = chr(ord("A") + index)
    parsed = parse_emergency_source(
        f"vless://{index:08x}-1111-4111-8111-{index:012x}"
        f"@reserve-{index}.example.com:443?type=tcp&security=reality"
        f"&pbk={key_char * 43}&sid={index:08x}&sni=cover-{index}.example.com"
        "&fp=chrome&flow=xtls-rprx-vision&encryption=none"
    )
    assert not parsed.rejected
    return parsed.accepted[0]


def _bundle(count: int = 4) -> EmergencySourceBundle:
    materials = tuple(_material(index) for index in range(1, count + 1))
    return EmergencySourceBundle(
        materials=materials,
        source_revision="a" * 40,
        source_digest="a" * 64,
        feed_digests={"mobile": "b" * 64, "sni": "c" * 64},
        mirror_quorum={"mobile": ("one", "two"), "sni": ("one", "two")},
        candidate_line_count=count,
        rejection_counts={},
    )


@pytest.fixture()
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'worker.db').as_posix()}")
    models.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    yield factory
    engine.dispose()


@pytest.fixture()
def adapter_path(tmp_path) -> Path:
    path = tmp_path / ("probe.exe" if os.name == "nt" else "probe")
    path.write_bytes(b"test-adapter-placeholder")
    return path.resolve()


@pytest.fixture()
def crypto() -> EmergencyCatalogCrypto:
    return EmergencyCatalogCrypto.generate_for_tests()


def _config(crypto: EmergencyCatalogCrypto, adapter_path: Path, *, concurrency: int = 2):
    return EmergencyCatalogWorkerConfig(
        crypto=crypto,
        adapter_path=str(adapter_path),
        probe_url=CONTROLLED_PROBE_URL,
        expected_payload_sha256=EXPECTED_DIGEST,
        probe_concurrency=concurrency,
    )


def test_worker_is_disabled_by_default_and_unknown_values_do_not_enable() -> None:
    assert emergency_catalog_worker_enabled({}) is False
    assert emergency_catalog_worker_enabled({"EMERGENCY_CATALOG_WORKER_ENABLED": "maybe"}) is False
    assert emergency_catalog_worker_enabled({"EMERGENCY_CATALOG_WORKER_ENABLED": "true"}) is True


def test_enabled_worker_requires_complete_fail_closed_environment(monkeypatch, adapter_path) -> None:
    monkeypatch.setenv("EMERGENCY_CATALOG_WORKER_ENABLED", "1")
    for key in (
        "EMERGENCY_CATALOG_SIGNING_KEY_ID",
        "EMERGENCY_CATALOG_MATERIAL_KEY_B64",
        "EMERGENCY_CATALOG_SIGNING_PRIVATE_KEY_B64",
        "EMERGENCY_CATALOG_PROBE_ADAPTER_PATH",
        "EMERGENCY_CATALOG_PROBE_URL",
        "EMERGENCY_CATALOG_EXPECTED_PAYLOAD_SHA256",
    ):
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(EmergencyCatalogWorkerError, match="material_key_missing_or_invalid"):
        load_emergency_catalog_worker_config()

    private_key = Ed25519PrivateKey.generate().private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    monkeypatch.setenv("EMERGENCY_CATALOG_SIGNING_KEY_ID", "worker-test-v1")
    monkeypatch.setenv(
        "EMERGENCY_CATALOG_MATERIAL_KEY_B64",
        base64.urlsafe_b64encode(b"m" * 32).decode().rstrip("="),
    )
    monkeypatch.setenv(
        "EMERGENCY_CATALOG_SIGNING_PRIVATE_KEY_B64",
        base64.urlsafe_b64encode(private_key).decode().rstrip("="),
    )
    monkeypatch.setenv("EMERGENCY_CATALOG_PROBE_ADAPTER_PATH", str(adapter_path))
    monkeypatch.setenv("EMERGENCY_CATALOG_PROBE_URL", CONTROLLED_PROBE_URL)
    monkeypatch.setenv("EMERGENCY_CATALOG_EXPECTED_PAYLOAD_SHA256", EXPECTED_DIGEST)

    loaded = load_emergency_catalog_worker_config()

    assert loaded.adapter_path == str(adapter_path)
    assert loaded.interval_seconds == DEFAULT_INTERVAL_SECONDS
    assert "crypto" not in repr(loaded)


def test_interval_below_thirty_minutes_is_rejected(monkeypatch, adapter_path) -> None:
    private_key = Ed25519PrivateKey.generate().private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    values = {
        "EMERGENCY_CATALOG_WORKER_ENABLED": "1",
        "EMERGENCY_CATALOG_SIGNING_KEY_ID": "worker-test-v1",
        "EMERGENCY_CATALOG_MATERIAL_KEY_B64": base64.urlsafe_b64encode(b"m" * 32).decode(),
        "EMERGENCY_CATALOG_SIGNING_PRIVATE_KEY_B64": base64.urlsafe_b64encode(private_key).decode(),
        "EMERGENCY_CATALOG_PROBE_ADAPTER_PATH": str(adapter_path),
        "EMERGENCY_CATALOG_PROBE_URL": CONTROLLED_PROBE_URL,
        "EMERGENCY_CATALOG_EXPECTED_PAYLOAD_SHA256": EXPECTED_DIGEST,
        "EMERGENCY_CATALOG_WORKER_INTERVAL_SECONDS": "1799",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)

    with pytest.raises(EmergencyCatalogWorkerError, match="worker_interval_invalid"):
        load_emergency_catalog_worker_config()


@pytest.mark.asyncio
async def test_invalid_runtime_contract_fails_before_source_fetch(crypto, adapter_path) -> None:
    source_called = False

    async def source_fetcher():
        nonlocal source_called
        source_called = True
        return _bundle()

    invalid = replace(_config(crypto, adapter_path), probe_url="https://example.test/probe")
    with pytest.raises(EmergencyCatalogWorkerError, match="probe_url_missing_or_invalid"):
        await run_emergency_catalog_once(config=invalid, source_fetcher=source_fetcher)

    assert source_called is False


@pytest.mark.asyncio
async def test_worker_bounds_probes_and_atomically_promotes(
    session_factory,
    crypto,
    adapter_path,
) -> None:
    bundle = _bundle()
    current = 0
    maximum = 0
    lock = asyncio.Lock()

    async def source_fetcher():
        return bundle

    async def probe_runner(material, **kwargs):
        nonlocal current, maximum
        assert kwargs["adapter_command"] == (str(adapter_path),)
        assert kwargs["probe_url"] == CONTROLLED_PROBE_URL
        assert kwargs["expected_payload_sha256"] == EXPECTED_DIGEST
        async with lock:
            current += 1
            maximum = max(maximum, current)
        await asyncio.sleep(0.01)
        async with lock:
            current -= 1
        return EndpointProbeResult(
            authenticated=True,
            payload_ok=True,
            payload_sha256=EXPECTED_DIGEST,
            exit_country="FR",
            latency_ms=25,
            verified_at=NOW,
        )

    summary = await run_emergency_catalog_once(
        config=_config(crypto, adapter_path, concurrency=2),
        session_factory=session_factory,
        source_fetcher=source_fetcher,
        probe_runner=probe_runner,
    )

    assert maximum == 2
    assert summary.promoted is True
    assert summary.healthy_count == 4
    assert "vless://" not in repr(summary.safe_summary())
    with session_factory() as session:
        snapshot = session.get(models.EmergencyCatalogSnapshot, summary.snapshot_id)
        assert snapshot.status == "active"
        assert snapshot.active_endpoint_count == 4


@pytest.mark.asyncio
async def test_probe_errors_remain_staged_and_never_promote(
    session_factory,
    crypto,
    adapter_path,
) -> None:
    async def source_fetcher():
        return _bundle()

    async def failed_probe(_material, **_kwargs):
        raise EmergencyProbeError("probe_adapter_failed")

    summary = await run_emergency_catalog_once(
        config=_config(crypto, adapter_path),
        session_factory=session_factory,
        source_fetcher=source_fetcher,
        probe_runner=failed_probe,
    )

    assert summary.promoted is False
    assert summary.promotion_code == "insufficient_healthy_endpoints"
    assert summary.failed_count == 4
    with session_factory() as session:
        snapshot = session.get(models.EmergencyCatalogSnapshot, summary.snapshot_id)
        assert snapshot.status == "staging"
        assert snapshot.rejection_code == "insufficient_healthy_endpoints"
        assert session.query(models.EmergencyCatalogSnapshot).filter_by(status="active").count() == 0
