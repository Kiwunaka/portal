from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import time
from collections import OrderedDict
from datetime import datetime, timedelta, timezone, tzinfo
from pathlib import Path
from typing import Any
from urllib import error, request


ACCESS_LINE_RE = re.compile(
    r"^(?P<timestamp>(?:\d{4}/\d{2}/\d{2}\s+|\d{4}-\d{2}-\d{2}T)"
    r"\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})?)\s+"
    r"(?P<source_ip>[0-9A-Fa-f:.]+):\d+\s+"
    r"accepted\s+\S+\s+\[(?P<inbound>[^\]]+?)\s*->\s*[^\]]+\]\s+"
    r"email:\s*(?P<client_email>\S+)\s*$"
)
FIXED_OFFSET_RE = re.compile(r"^(?P<sign>[+-])(?P<hours>\d{2}):(?P<minutes>\d{2})$")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _load_cursor(cursor_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(cursor_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass
    return {"inode": 0, "offset": 0}


def _save_cursor(cursor_path: Path, payload: dict[str, Any]) -> None:
    cursor_path.parent.mkdir(parents=True, exist_ok=True)
    cursor_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def _source_timezone(value: str) -> tzinfo:
    name = str(value or "").strip()
    if not name:
        raise ValueError("source timezone is required for a naive xray timestamp")
    if name in {"UTC", "Z"}:
        return timezone.utc
    fixed_offset = FIXED_OFFSET_RE.fullmatch(name)
    if fixed_offset:
        hours = int(fixed_offset.group("hours"))
        minutes = int(fixed_offset.group("minutes"))
        if hours > 23 or minutes > 59:
            raise ValueError(f"invalid source timezone: {name}")
        delta = timedelta(hours=hours, minutes=minutes)
        if fixed_offset.group("sign") == "-":
            delta = -delta
        return timezone(delta)
    raise ValueError(f"invalid source timezone: {name}")


def _canonical_utc(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("observer timestamp must be timezone-aware")
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_xray_access_log_line(line: str, *, source_timezone: str = "") -> dict[str, Any] | None:
    match = ACCESS_LINE_RE.match(str(line or "").strip())
    if not match:
        return None
    timestamp_text = str(match.group("timestamp") or "").replace("/", "-").replace(" ", "T", 1)
    if timestamp_text.endswith("Z"):
        timestamp_text = f"{timestamp_text[:-1]}+00:00"
    occurred_at = datetime.fromisoformat(timestamp_text).replace(microsecond=0)
    if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
        occurred_at = occurred_at.replace(tzinfo=_source_timezone(source_timezone))
    inbound_full = str(match.group("inbound") or "").strip()
    inbound_tag = inbound_full.split(" ", 1)[0].strip()
    return {
        "occurred_at": _canonical_utc(occurred_at),
        "source_ip": str(match.group("source_ip") or "").strip(),
        "client_email": str(match.group("client_email") or "").strip(),
        "inbound_tag": inbound_tag or None,
    }


def collect_observations(*, log_path: Path, cursor_path: Path, source_timezone: str = "") -> dict[str, Any]:
    if not log_path.exists():
        raise FileNotFoundError(f"xray access log is missing: {log_path}")

    current_inode = int(log_path.stat().st_ino)
    previous = _load_cursor(cursor_path)
    offset = int(previous.get("offset", 0) or 0)
    previous_inode = int(previous.get("inode", 0) or 0)
    if previous_inode != current_inode or offset > int(log_path.stat().st_size):
        offset = 0

    aggregate: "OrderedDict[tuple[Any, ...], dict[str, Any]]" = OrderedDict()
    parse_error_count = 0
    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
        handle.seek(offset)
        for raw_line in handle:
            try:
                parsed = parse_xray_access_log_line(raw_line, source_timezone=source_timezone)
            except (ValueError, OverflowError):
                parsed = None
            if not parsed:
                if str(raw_line or "").strip():
                    parse_error_count += 1
                continue
            occurred_at = datetime.fromisoformat(parsed["occurred_at"].replace("Z", "+00:00")).replace(
                second=0,
                microsecond=0,
            )
            occurred_at_utc = _canonical_utc(occurred_at)
            key = (
                occurred_at_utc,
                str(parsed.get("client_email") or ""),
                str(parsed.get("source_ip") or ""),
                str(parsed.get("inbound_tag") or ""),
            )
            if key not in aggregate:
                aggregate[key] = {
                    "occurred_at": occurred_at_utc,
                    "client_email": str(parsed.get("client_email") or ""),
                    "source_ip": str(parsed.get("source_ip") or ""),
                    "inbound_tag": parsed.get("inbound_tag"),
                }
        next_offset = int(handle.tell())

    cursor_payload = {"inode": current_inode, "offset": next_offset}
    _save_cursor(cursor_path, cursor_payload)
    return {
        "observations": list(aggregate.values()),
        "cursor": cursor_payload,
        "parse_error_count": int(parse_error_count),
    }


def _sign_payload(*, node_code: str, secret: str, timestamp: int, body: bytes) -> str:
    canonical = f"{str(node_code).strip().lower()}\n{int(timestamp)}\n{body.decode('utf-8')}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), canonical, hashlib.sha256).hexdigest()


def push_observer_batch(
    *,
    api_url: str,
    node_code: str,
    secret: str,
    batch_payload: dict[str, Any],
    timeout_seconds: int = 20,
) -> dict[str, Any]:
    raw_body = json.dumps(batch_payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    timestamp = int(time.time())
    headers = {
        "Content-Type": "application/json",
        "X-Portal-Node": str(node_code).strip().lower(),
        "X-Portal-Timestamp": str(timestamp),
        "X-Portal-Signature": _sign_payload(node_code=node_code, secret=secret, timestamp=timestamp, body=raw_body),
    }
    req = request.Request(str(api_url).strip(), data=raw_body, headers=headers, method="POST")
    with request.urlopen(req, timeout=max(5, int(timeout_seconds))) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace") or "{}")
        return payload if isinstance(payload, dict) else {}


def run(
    *,
    log_path: Path,
    cursor_path: Path,
    api_url: str,
    node_code: str,
    secret: str,
    source_timezone: str = "",
) -> dict[str, Any]:
    collected = collect_observations(
        log_path=log_path,
        cursor_path=cursor_path,
        source_timezone=source_timezone,
    )
    observations = list(collected.get("observations") or [])
    cursor = dict(collected.get("cursor") or {})
    parse_error_count = int(collected.get("parse_error_count") or 0)
    minute_bucket = _utcnow().strftime("%Y%m%d%H%M")
    batch_id = (
        f"{str(node_code).strip().lower()}-"
        f"{int(cursor.get('inode', 0) or 0)}-"
        f"{int(cursor.get('offset', 0) or 0)}-"
        f"{minute_bucket}"
    )
    payload = {
        "batch_id": batch_id,
        "cursor": cursor,
        "observations": observations,
        "parse_error_count": parse_error_count,
    }
    response = push_observer_batch(
        api_url=api_url,
        node_code=node_code,
        secret=secret,
        batch_payload=payload,
    )
    return {"sent": True, "payload": payload, "response": response}


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect xray access.log observations and push them to POKROV brain.")
    parser.add_argument("--log-path", default=os.getenv("PORTAL_OBSERVER_LOG_PATH", "/var/log/xray/access.log"))
    parser.add_argument("--cursor-path", default=os.getenv("PORTAL_OBSERVER_CURSOR_PATH", "/var/lib/portal-node-observer/cursor.json"))
    parser.add_argument(
        "--api-url",
        default=os.getenv("PORTAL_OBSERVER_API_URL", "https://api.pokrov.space/api/internal/observer/batches"),
    )
    parser.add_argument("--node-code", default=os.getenv("PORTAL_OBSERVER_NODE_CODE", ""))
    parser.add_argument("--secret", default=os.getenv("PORTAL_OBSERVER_SECRET", ""))
    parser.add_argument(
        "--source-timezone",
        default=os.getenv("PORTAL_OBSERVER_SOURCE_TIMEZONE", ""),
        help="UTC, Z, or a signed fixed offset used only for naive xray log timestamps",
    )
    args = parser.parse_args()

    node_code = str(args.node_code or "").strip().lower()
    secret = str(args.secret or "").strip()
    if not node_code or not secret:
        raise SystemExit("PORTAL_OBSERVER_NODE_CODE and PORTAL_OBSERVER_SECRET are required")

    result = run(
        log_path=Path(args.log_path),
        cursor_path=Path(args.cursor_path),
        api_url=str(args.api_url or "").strip(),
        node_code=node_code,
        secret=secret,
        source_timezone=str(args.source_timezone or "").strip(),
    )
    sent = bool(result.get("sent"))
    payload = result.get("payload") or {}
    response = result.get("response") or {}
    print(
        json.dumps(
            {
                "sent": sent,
                "batch_id": payload.get("batch_id"),
                "observation_count": len(payload.get("observations") or []),
                "accepted_count": response.get("accepted_count"),
                "deduped_count": response.get("deduped_count"),
                "unmatched_count": response.get("unmatched_count"),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(body or str(exc))
        raise
