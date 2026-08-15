"""Atomically refresh the local DB-IP Country Lite MMDB file."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

import geoip2.database


DOWNLOAD_HOST = "download.db-ip.com"
MAX_COMPRESSED_BYTES = 24 * 1024 * 1024
MAX_DATABASE_BYTES = 64 * 1024 * 1024
MIN_DATABASE_BYTES = 1024 * 1024


class _RestrictedRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        from urllib.parse import urlsplit

        parsed = urlsplit(newurl)
        if parsed.scheme != "https" or parsed.hostname != DOWNLOAD_HOST:
            raise HTTPError(newurl, code, "geoip_redirect_forbidden", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _month_candidates(now: datetime) -> tuple[str, str]:
    current = now.astimezone(timezone.utc)
    first = current.strftime("%Y-%m")
    previous_day = current.replace(day=1).timestamp() - 24 * 60 * 60
    previous = datetime.fromtimestamp(previous_day, tz=timezone.utc).strftime("%Y-%m")
    return first, previous


def _download(month: str) -> bytes:
    url = f"https://{DOWNLOAD_HOST}/free/dbip-country-lite-{month}.mmdb.gz"
    request = Request(url, headers={"User-Agent": "POKROV-GeoIP-Refresh/1"})
    opener = build_opener(_RestrictedRedirectHandler())
    with opener.open(request, timeout=60) as response:
        if response.geturl() != url:
            raise RuntimeError("geoip_download_redirected")
        payload = response.read(MAX_COMPRESSED_BYTES + 1)
    if len(payload) > MAX_COMPRESSED_BYTES:
        raise RuntimeError("geoip_download_too_large")
    return payload


def _validate_database(path: Path) -> None:
    size = path.stat().st_size
    if not MIN_DATABASE_BYTES <= size <= MAX_DATABASE_BYTES:
        raise RuntimeError("geoip_database_size_invalid")
    with geoip2.database.Reader(str(path)) as reader:
        database_type = str(reader.metadata().database_type or "").lower()
        if "country" not in database_type:
            raise RuntimeError("geoip_database_type_invalid")
        probe = reader.country("8.8.8.8")
        if not str(probe.country.iso_code or "").strip():
            raise RuntimeError("geoip_database_probe_failed")


def refresh_database(output: Path, *, now: datetime | None = None) -> dict[str, object]:
    selected_month = ""
    compressed = b""
    last_error: BaseException | None = None
    for month in _month_candidates(now or datetime.now(timezone.utc)):
        try:
            compressed = _download(month)
            selected_month = month
            break
        except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
    if not compressed:
        raise RuntimeError("geoip_download_failed") from last_error

    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".dbip-country-lite-",
        suffix=".mmdb.next",
        dir=str(output.parent),
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        written = 0
        with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as source:
            with temporary.open("wb") as destination:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > MAX_DATABASE_BYTES:
                        raise RuntimeError("geoip_database_too_large")
                    destination.write(chunk)
        _validate_database(temporary)
        digest = hashlib.sha256(temporary.read_bytes()).hexdigest()
        os.chmod(temporary, 0o644)
        os.replace(temporary, output)
        return {
            "schema_version": "pokrov-emergency-geoip-refresh-v1",
            "source": "dbip-country-lite",
            "source_month": selected_month,
            "database_bytes": output.stat().st_size,
            "database_sha256": digest,
        }
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="/var/lib/pokrov-geoip/dbip-country-lite.mmdb",
    )
    args = parser.parse_args()
    result = refresh_database(Path(args.output))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
