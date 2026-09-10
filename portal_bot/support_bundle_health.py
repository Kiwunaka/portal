"""Bounded worker signals for the existing operator alert lifecycle."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HEALTH_FILE_NAME = "support-worker-health.json"


def write_support_bundle_health(accepted_root: Path, observations: dict) -> bool:
    """The worker owns the parent directory; the API gets group read access."""
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=accepted_root.parent,
            prefix=".support-worker-health-", delete=False,
        ) as handle:
            temporary = handle.name
            json.dump({"schema_version": 1, **observations}, handle, separators=(",", ":"))
        os.chmod(temporary, 0o640)
        os.replace(temporary, accepted_root.parent / HEALTH_FILE_NAME)
        temporary = None
        return True
    except OSError:
        return False
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except OSError:
                pass


def support_bundle_health_alerts(*, now: datetime) -> list[dict[str, Any]]:
    configured = str(os.getenv("POKROV_SUPPORT_BUNDLE_ACCEPTED_DIR") or "").strip()
    if not configured:
        return []
    path = Path(configured).resolve().parent / HEALTH_FILE_NAME
    timestamp = now.replace(tzinfo=timezone.utc).timestamp()
    try:
        with path.open("rb") as handle:
            raw = handle.read(4097)
        if len(raw) > 4096:
            raise ValueError("oversized health signal")
        value = json.loads(raw)
        if not isinstance(value, dict) or value.get("schema_version") != 1:
            raise ValueError("unknown health signal")
        retention_interval = max(3600, int(os.getenv("TELEMETRY_RETENTION_INTERVAL_SECONDS", "21600")))
        stale_limits = {"ingest": 600, "retention": retention_interval * 2}
        signals = {}
        for stage, stale_after in stale_limits.items():
            item = value.get(stage)
            if not isinstance(item, dict):
                started = value.get("started_at")
                if type(started) is int and 0 <= timestamp - started <= 60:
                    continue
                raise ValueError("missing health signal")
            observed = item.get("observed_at")
            errors = item.get("errors")
            if type(observed) is not int or type(errors) is not int or not 0 <= errors <= 1000:
                raise ValueError("invalid health signal")
            age = timestamp - observed
            signals[stage] = {
                "state": "stale" if age < -60 or age > stale_after else "failed" if errors else "ok",
                "errors": errors,
            }
    except (OSError, ValueError, TypeError, RecursionError):
        return [_candidate("unavailable", "Состояние обработки диагностики неизвестно",
                           "Нет корректного сигнала worker. Проверьте службу и доступ к хранилищу.", {})]
    candidates = []
    for stage, item in signals.items():
        if item["state"] == "ok":
            continue
        title = "Обработка диагностики требует проверки" if stage == "ingest" else "Удаление диагностических архивов требует проверки"
        body = "Сигнал worker устарел. Проверьте службу." if item["state"] == "stale" else "Worker сообщил об ошибке. Проверьте его журнал и права хранилища."
        candidates.append(_candidate(stage, title, body, item))
    return candidates


def _candidate(kind: str, title: str, body: str, metadata: dict) -> dict[str, Any]:
    return {
        "fingerprint": "support_bundle_health_" + kind,
        "source": "support_bundle",
        "severity": "warning",
        "title": title,
        "body": body,
        "metadata": metadata,
    }
