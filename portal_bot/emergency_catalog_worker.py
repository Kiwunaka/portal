"""Fail-closed periodic ingestion and promotion for emergency catalogs."""

from __future__ import annotations

import asyncio
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable, Mapping

try:
    from db import SessionLocal
    from emergency_catalog_crypto import EmergencyCatalogCrypto, EmergencyCatalogCryptoError
    from emergency_catalog_ingestion import EmergencySourceBundle, fetch_approved_source_bundle
    from emergency_catalog_probe import EmergencyProbeError, run_controlled_probe
    from emergency_catalog_service import (
        EmergencyCatalogServiceError,
        EndpointProbeResult,
        apply_probe_result,
        promote_snapshot,
        stage_snapshot,
    )
    from emergency_catalog_source import EmergencyEndpointMaterial
    from models import EmergencyCatalogSnapshot
except ImportError:  # pragma: no cover - package import
    from .db import SessionLocal
    from .emergency_catalog_crypto import EmergencyCatalogCrypto, EmergencyCatalogCryptoError
    from .emergency_catalog_ingestion import EmergencySourceBundle, fetch_approved_source_bundle
    from .emergency_catalog_probe import EmergencyProbeError, run_controlled_probe
    from .emergency_catalog_service import (
        EmergencyCatalogServiceError,
        EndpointProbeResult,
        apply_probe_result,
        promote_snapshot,
        stage_snapshot,
    )
    from .emergency_catalog_source import EmergencyEndpointMaterial
    from .models import EmergencyCatalogSnapshot


logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_SECONDS = 2 * 60 * 60
MIN_INTERVAL_SECONDS = 30 * 60
DEFAULT_PROBE_CONCURRENCY = 4
MAX_PROBE_CONCURRENCY = 8
DEFAULT_PROBE_TIMEOUT_SECONDS = 30.0
CONTROLLED_PROBE_URL = "https://api.pokrov.space/api/emergency-probe/payload-v1"
_DIGEST_RE = re.compile(r"^[a-f0-9]{64}$")
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"", "0", "false", "no", "off"})
_EXPECTED_PROMOTION_REJECTIONS = frozenset(
    {
        "insufficient_healthy_endpoints",
        "automatic_churn_limit",
        "catalog_distribution_disabled",
    }
)


class EmergencyCatalogWorkerError(RuntimeError):
    """Fixed-code worker failure safe for operational logs."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class EmergencyCatalogWorkerConfig:
    crypto: EmergencyCatalogCrypto = field(repr=False)
    adapter_path: str
    probe_url: str
    expected_payload_sha256: str
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS
    probe_concurrency: int = DEFAULT_PROBE_CONCURRENCY
    probe_timeout_seconds: float = DEFAULT_PROBE_TIMEOUT_SECONDS


@dataclass(frozen=True, slots=True)
class EmergencyCatalogWorkerSummary:
    source_digest: str
    snapshot_id: str
    candidate_count: int
    healthy_count: int
    failed_count: int
    promoted: bool
    promotion_code: str

    def safe_summary(self) -> dict[str, object]:
        return {
            "source_digest": self.source_digest,
            "snapshot_id": self.snapshot_id,
            "candidate_count": self.candidate_count,
            "healthy_count": self.healthy_count,
            "failed_count": self.failed_count,
            "promoted": self.promoted,
            "promotion_code": self.promotion_code,
        }


def _validate_runtime_config(config: EmergencyCatalogWorkerConfig) -> None:
    if not isinstance(config.crypto, EmergencyCatalogCrypto):
        raise EmergencyCatalogWorkerError("catalog_crypto_missing_or_invalid")
    adapter = Path(str(config.adapter_path or ""))
    if not adapter.is_absolute() or not adapter.is_file():
        raise EmergencyCatalogWorkerError("probe_adapter_missing_or_invalid")
    if config.probe_url != CONTROLLED_PROBE_URL:
        raise EmergencyCatalogWorkerError("probe_url_missing_or_invalid")
    if _DIGEST_RE.fullmatch(str(config.expected_payload_sha256 or "").lower()) is None:
        raise EmergencyCatalogWorkerError("expected_payload_digest_missing_or_invalid")
    if int(config.interval_seconds) < MIN_INTERVAL_SECONDS:
        raise EmergencyCatalogWorkerError("worker_interval_invalid")
    if not 1 <= int(config.probe_concurrency) <= MAX_PROBE_CONCURRENCY:
        raise EmergencyCatalogWorkerError("probe_concurrency_invalid")
    if not 1.0 <= float(config.probe_timeout_seconds) <= 60.0:
        raise EmergencyCatalogWorkerError("probe_timeout_invalid")


def emergency_catalog_worker_enabled(env: Mapping[str, str] | None = None) -> bool:
    values = os.environ if env is None else env
    raw = str(values.get("EMERGENCY_CATALOG_WORKER_ENABLED", "")).strip().lower()
    if raw in _TRUE_VALUES:
        return True
    if raw in _FALSE_VALUES:
        return False
    return False


def _bounded_int(
    raw: str,
    *,
    default: int,
    minimum: int,
    maximum: int | None,
    code: str,
) -> int:
    candidate = str(raw or "").strip()
    if not candidate:
        return default
    try:
        value = int(candidate)
    except ValueError as exc:
        raise EmergencyCatalogWorkerError(code) from exc
    if value < minimum or (maximum is not None and value > maximum):
        raise EmergencyCatalogWorkerError(code)
    return value


def _bounded_float(raw: str, *, default: float, minimum: float, maximum: float, code: str) -> float:
    candidate = str(raw or "").strip()
    if not candidate:
        return default
    try:
        value = float(candidate)
    except ValueError as exc:
        raise EmergencyCatalogWorkerError(code) from exc
    if not minimum <= value <= maximum:
        raise EmergencyCatalogWorkerError(code)
    return value


def load_emergency_catalog_worker_config() -> EmergencyCatalogWorkerConfig:
    """Load the complete runtime contract or reject it before any network/DB work."""

    if not emergency_catalog_worker_enabled():
        raise EmergencyCatalogWorkerError("worker_disabled")
    try:
        crypto = EmergencyCatalogCrypto.from_environment()
    except EmergencyCatalogCryptoError as exc:
        raise EmergencyCatalogWorkerError(exc.code) from exc

    raw_adapter = os.getenv("EMERGENCY_CATALOG_PROBE_ADAPTER_PATH", "").strip()
    adapter = Path(raw_adapter)
    if not raw_adapter or not adapter.is_absolute() or not adapter.is_file():
        raise EmergencyCatalogWorkerError("probe_adapter_missing_or_invalid")

    probe_url = os.getenv("EMERGENCY_CATALOG_PROBE_URL", "").strip()
    if probe_url != CONTROLLED_PROBE_URL:
        raise EmergencyCatalogWorkerError("probe_url_missing_or_invalid")

    expected_digest = os.getenv("EMERGENCY_CATALOG_EXPECTED_PAYLOAD_SHA256", "").strip().lower()
    if _DIGEST_RE.fullmatch(expected_digest) is None:
        raise EmergencyCatalogWorkerError("expected_payload_digest_missing_or_invalid")

    interval_seconds = _bounded_int(
        os.getenv("EMERGENCY_CATALOG_WORKER_INTERVAL_SECONDS", ""),
        default=DEFAULT_INTERVAL_SECONDS,
        minimum=MIN_INTERVAL_SECONDS,
        maximum=None,
        code="worker_interval_invalid",
    )
    concurrency = _bounded_int(
        os.getenv("EMERGENCY_CATALOG_PROBE_CONCURRENCY", ""),
        default=DEFAULT_PROBE_CONCURRENCY,
        minimum=1,
        maximum=MAX_PROBE_CONCURRENCY,
        code="probe_concurrency_invalid",
    )
    timeout_seconds = _bounded_float(
        os.getenv("EMERGENCY_CATALOG_PROBE_TIMEOUT_SECONDS", ""),
        default=DEFAULT_PROBE_TIMEOUT_SECONDS,
        minimum=1.0,
        maximum=60.0,
        code="probe_timeout_invalid",
    )
    config = EmergencyCatalogWorkerConfig(
        crypto=crypto,
        adapter_path=str(adapter),
        probe_url=probe_url,
        expected_payload_sha256=expected_digest,
        interval_seconds=interval_seconds,
        probe_concurrency=concurrency,
        probe_timeout_seconds=timeout_seconds,
    )
    _validate_runtime_config(config)
    return config


def _probe_failure(*, expected_payload_sha256: str, code: str) -> EndpointProbeResult:
    return EndpointProbeResult(
        authenticated=False,
        payload_ok=False,
        payload_sha256=expected_payload_sha256,
        exit_country="ZZ",
        latency_ms=60_000,
        verified_at=datetime.now(timezone.utc),
        verification_source="controlled_core",
        error_code=code,
    )


async def _probe_materials(
    materials: tuple[EmergencyEndpointMaterial, ...],
    *,
    config: EmergencyCatalogWorkerConfig,
    probe_runner: Callable[..., Awaitable[EndpointProbeResult]],
) -> dict[str, EndpointProbeResult]:
    semaphore = asyncio.Semaphore(config.probe_concurrency)

    async def one(material: EmergencyEndpointMaterial) -> tuple[str, EndpointProbeResult]:
        async with semaphore:
            try:
                result = await probe_runner(
                    material,
                    adapter_command=(sys.executable, config.adapter_path),
                    probe_url=config.probe_url,
                    expected_payload_sha256=config.expected_payload_sha256,
                    timeout_seconds=config.probe_timeout_seconds,
                )
            except asyncio.CancelledError:
                raise
            except EmergencyProbeError as exc:
                result = _probe_failure(
                    expected_payload_sha256=config.expected_payload_sha256,
                    code=exc.code,
                )
            except Exception:
                result = _probe_failure(
                    expected_payload_sha256=config.expected_payload_sha256,
                    code="probe_failed",
                )
            return material.stable_id, result

    rows = await asyncio.gather(*(one(material) for material in materials))
    return dict(rows)


async def run_emergency_catalog_once(
    *,
    config: EmergencyCatalogWorkerConfig,
    session_factory=SessionLocal,
    source_fetcher: Callable[[], Awaitable[EmergencySourceBundle]] = fetch_approved_source_bundle,
    probe_runner: Callable[..., Awaitable[EndpointProbeResult]] = run_controlled_probe,
) -> EmergencyCatalogWorkerSummary:
    _validate_runtime_config(config)
    bundle = await source_fetcher()

    with session_factory() as session:
        try:
            staged = stage_snapshot(
                session,
                materials=bundle.materials,
                source_revision=bundle.source_revision,
                source_digest=bundle.source_digest,
                crypto=config.crypto,
                expected_payload_sha256=config.expected_payload_sha256,
            )
            snapshot_id = str(staged.snapshot.id)
            snapshot_status = str(staged.snapshot.status)
            session.commit()
        except Exception:
            session.rollback()
            raise

    if snapshot_status == "active":
        return EmergencyCatalogWorkerSummary(
            source_digest=bundle.source_digest,
            snapshot_id=snapshot_id,
            candidate_count=len(bundle.materials),
            healthy_count=0,
            failed_count=0,
            promoted=False,
            promotion_code="already_active",
        )

    probes = await _probe_materials(
        bundle.materials,
        config=config,
        probe_runner=probe_runner,
    )
    with session_factory() as session:
        try:
            for stable_id, result in probes.items():
                apply_probe_result(
                    session,
                    snapshot_id=snapshot_id,
                    stable_id=stable_id,
                    result=result,
                    expected_payload_sha256=config.expected_payload_sha256,
                )
            snapshot = session.get(EmergencyCatalogSnapshot, snapshot_id)
            if snapshot is None:
                raise EmergencyCatalogWorkerError("staging_snapshot_missing")
            session.flush()
            healthy_count = int(snapshot.healthy_count or 0)
            session.commit()
        except Exception:
            session.rollback()
            raise

    promotion_code = "promoted"
    promoted = False
    with session_factory() as session:
        try:
            promote_snapshot(
                session,
                snapshot_id=snapshot_id,
                crypto=config.crypto,
            )
            session.commit()
            promoted = True
        except EmergencyCatalogServiceError as exc:
            if exc.code not in _EXPECTED_PROMOTION_REJECTIONS:
                session.rollback()
                raise
            session.commit()
            promotion_code = exc.code
        except Exception:
            session.rollback()
            raise

    return EmergencyCatalogWorkerSummary(
        source_digest=bundle.source_digest,
        snapshot_id=snapshot_id,
        candidate_count=len(bundle.materials),
        healthy_count=healthy_count,
        failed_count=len(probes) - healthy_count,
        promoted=promoted,
        promotion_code=promotion_code,
    )


def _safe_failure_code(exc: BaseException) -> str:
    code = str(getattr(exc, "code", "") or "").strip().lower()
    return code if re.fullmatch(r"[a-z0-9][a-z0-9._:-]{0,63}", code) else "worker_failed"


async def emergency_catalog_worker_job() -> None:
    while True:
        interval_seconds = DEFAULT_INTERVAL_SECONDS
        try:
            config = load_emergency_catalog_worker_config()
            interval_seconds = config.interval_seconds
            summary = await run_emergency_catalog_once(config=config)
            logger.info("emergency_catalog_worker result=%s", summary.safe_summary())
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("emergency_catalog_worker failed code=%s", _safe_failure_code(exc))
        await asyncio.sleep(interval_seconds)
