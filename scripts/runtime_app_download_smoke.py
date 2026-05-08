#!/usr/bin/env python3
"""Compatibility wrapper for the runtime client app download smoke gate."""

from __future__ import annotations

import contextlib
import io
import re
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from release_gate_check import _redact_text  # noqa: E402
import smoke_client_apps  # noqa: E402

_GITHUB_RELEASE_ASSET_SIGNED_URL_RE = re.compile(
    r"(https://release-assets\.githubusercontent\.com/[^\s?`]+)\?([^\s`]+)",
    re.IGNORECASE,
)


def _parse_wrapper_args(argv: list[str]) -> tuple[bool, list[str]]:
    redact = False
    passthrough: list[str] = []
    for arg in argv:
        if arg == "--redact":
            redact = True
            continue
        passthrough.append(arg)
    return redact, passthrough


def _redact_runtime_text(text: str) -> str:
    redacted = _redact_text(text)
    return _GITHUB_RELEASE_ASSET_SIGNED_URL_RE.sub(r"\1?<redacted-query>", redacted)


def _run_smoke(argv: list[str]) -> int:
    previous_argv = sys.argv[:]
    try:
        sys.argv = ["smoke_client_apps.py", *argv]
        return int(smoke_client_apps.main())
    finally:
        sys.argv = previous_argv


def main(argv: list[str] | None = None) -> int:
    redact, passthrough = _parse_wrapper_args(list(sys.argv[1:] if argv is None else argv))
    if not redact:
        return _run_smoke(passthrough)

    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = _run_smoke(passthrough)

    out = stdout.getvalue()
    err = stderr.getvalue()
    if out:
        print(_redact_runtime_text(out), end="")
    if err:
        print(_redact_runtime_text(err), end="", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
