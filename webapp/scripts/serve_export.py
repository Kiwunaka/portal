from __future__ import annotations

import argparse
import os
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


class ExportThreadingHTTPServer(ThreadingHTTPServer):
    request_queue_size = 128
    daemon_threads = True


class ExportStaticHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str, **kwargs):
        self._export_directory = Path(directory).resolve()
        super().__init__(*args, directory=str(self._export_directory), **kwargs)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def copyfile(self, source, outputfile) -> None:  # type: ignore[override]
        try:
            super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return

    def _normalized_candidates(self, request_path: str) -> list[Path]:
        raw_path = unquote(urlsplit(request_path).path)
        raw_path = raw_path if raw_path.startswith("/") else f"/{raw_path}"
        parts = [part for part in raw_path.split("/") if part not in ("", ".", "..")]
        clean_path = Path(*parts) if parts else Path()

        candidates: list[Path] = []
        if clean_path == Path():
            candidates.append(Path("index.html"))
        elif raw_path.endswith("/"):
            candidates.append(clean_path / "index.html")
        else:
            candidates.append(clean_path)
            if clean_path.suffix == "":
                candidates.append(clean_path / "index.html")
                candidates.append(clean_path.with_suffix(".html"))
        return candidates

    def _open_candidate(self, candidate: Path):
        full_path = (self._export_directory / candidate).resolve()
        try:
            full_path.relative_to(self._export_directory)
        except ValueError:
            return None
        if not full_path.is_file():
            return None
        return full_path.open("rb")

    def send_head(self):  # type: ignore[override]
        for candidate in self._normalized_candidates(self.path):
            handle = self._open_candidate(candidate)
            if handle is None:
                continue
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", self.guess_type(str(candidate)))
            self.send_header("Content-Length", str(os.fstat(handle.fileno()).st_size))
            self.end_headers()
            return handle

        fallback = self._open_candidate(Path("404.html"))
        if fallback is None:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None

        self.send_response(HTTPStatus.NOT_FOUND)
        self.send_header("Content-Type", self.guess_type("404.html"))
        self.send_header("Content-Length", str(os.fstat(fallback.fileno()).st_size))
        self.end_headers()
        return fallback


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve a Next.js static export with 404.html fallback.")
    parser.add_argument("--port", type=int, default=3100)
    parser.add_argument("--directory", default="out")
    args = parser.parse_args()

    handler = partial(ExportStaticHandler, directory=args.directory)
    with ExportThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
