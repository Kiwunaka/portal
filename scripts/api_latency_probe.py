"""Collect bounded latency samples for allowlisted POKROV API budgets.

Use only against an owned controlled environment. State-changing endpoints need
an explicit flag and an input body; the probe never prints headers or bodies.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from functools import partial
import hashlib
from http.client import HTTPConnection, HTTPSConnection
from ipaddress import ip_address
import json
import os
import platform
import re
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import (
    HTTPHandler,
    HTTPSHandler,
    ProxyHandler,
    Request,
    build_opener,
    urlopen,
)

from performance_budget_gate import (
    DEFAULT_CONTRACT,
    ContractError,
    _load_json,
    contract_sha256,
    evaluate_evidence,
    validate_budget_contract,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
COLLECTOR_ID = "pokrov.api-latency"
COLLECTOR_VERSION = "1.1.0"
ENV_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
MAX_BODY_BYTES = 64 * 1024


@dataclass(frozen=True)
class Endpoint:
    method: str
    path: str
    requires_auth: bool
    state_changing: bool


ENDPOINTS = {
    "api.health.current_origin_ms": Endpoint("GET", "/api/health", False, False),
    "api.public_catalog.current_origin_ms": Endpoint(
        "GET", "/api/public/catalog", False, False
    ),
    "api.client_start_trial_ms": Endpoint(
        "POST", "/api/client/session/start-trial", True, True
    ),
    "api.client_managed_profile_ms": Endpoint(
        "GET", "/api/client/profile/managed", True, False
    ),
    "api.access_key_redeem_ms": Endpoint(
        "POST", "/api/access-keys/redeem", True, True
    ),
}


def _git_identity(repo_root: Path) -> tuple[str, str]:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip().lower()
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip()
    return revision, "dirty" if status else "clean"


def _validate_base_url(base_url: str, *, allow_http_localhost: bool) -> str:
    parsed = urlsplit(base_url)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ContractError("base URL cannot contain credentials, query or fragment")
    if parsed.scheme == "https" and parsed.netloc:
        return base_url.rstrip("/") + "/"
    if (
        allow_http_localhost
        and parsed.scheme == "http"
        and parsed.hostname in {"127.0.0.1", "localhost", "::1"}
        and parsed.netloc
    ):
        return base_url.rstrip("/") + "/"
    raise ContractError("base URL must use HTTPS or explicitly allowed localhost HTTP")


def _secret_from_env(name: str | None, *, required: bool) -> str | None:
    if name is None:
        if required:
            raise ContractError("authenticated endpoint requires --authorization-env")
        return None
    if not ENV_NAME_RE.fullmatch(name):
        raise ContractError("authorization environment variable name is invalid")
    value = os.getenv(name, "")
    if not value:
        raise ContractError("authorization environment variable is unset")
    return value


def _request_body(path: Path | None, *, required: bool) -> bytes | None:
    if path is None:
        if required:
            raise ContractError("state-changing endpoint requires --body-file")
        return None
    body = path.read_bytes()
    if not body or len(body) > MAX_BODY_BYTES:
        raise ContractError("request body must be 1..65536 bytes")
    try:
        value = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ContractError("request body must be valid JSON") from exc
    if not isinstance(value, dict):
        raise ContractError("request body must be a JSON object")
    return body


def _validate_source_address(source_address: str | None) -> str | None:
    """Validate that an optional literal IP address is assigned locally."""

    if source_address is None:
        return None
    try:
        parsed = ip_address(source_address)
    except ValueError as exc:
        raise ContractError(
            "source address must be a literal IPv4 or IPv6 address"
        ) from exc
    if parsed.is_unspecified or parsed.is_multicast:
        raise ContractError("source address cannot be unspecified or multicast")
    family = socket.AF_INET6 if parsed.version == 6 else socket.AF_INET
    normalized = str(parsed)
    try:
        with socket.socket(family, socket.SOCK_STREAM) as probe:
            probe.bind((normalized, 0))
    except OSError as exc:
        raise ContractError("source address is not assigned to this host") from exc
    return normalized


class _SourceAddressHTTPHandler(HTTPHandler):
    """Open direct HTTP connections from one explicit local address."""

    def __init__(self, source_address: str) -> None:
        super().__init__()
        self._source_address = source_address

    def http_open(self, request: Request) -> Any:
        connection = partial(
            HTTPConnection,
            source_address=(self._source_address, 0),
        )
        return self.do_open(connection, request)


class _SourceAddressHTTPSHandler(HTTPSHandler):
    """Open direct HTTPS connections from one explicit local address."""

    def __init__(self, source_address: str) -> None:
        super().__init__()
        self._source_address = source_address

    def https_open(self, request: Request) -> Any:
        connection = partial(
            HTTPSConnection,
            source_address=(self._source_address, 0),
        )
        return self.do_open(
            connection,
            request,
            context=self._context,
        )


def _build_source_bound_opener(source_address: str) -> Callable[..., Any]:
    """Build a proxy-free URL opener bound to one validated local address."""

    return build_opener(
        ProxyHandler({}),
        _SourceAddressHTTPHandler(source_address),
        _SourceAddressHTTPSHandler(source_address),
    ).open


def _sample_once(
    request: Request,
    *,
    timeout_seconds: float,
    opener: Callable[..., Any] = urlopen,
) -> float:
    started = time.perf_counter_ns()
    try:
        with opener(request, timeout=timeout_seconds) as response:
            status = int(getattr(response, "status", response.getcode()))
            response.read(1)
    except HTTPError as exc:
        raise ContractError(f"API probe returned HTTP {exc.code}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ContractError("API probe request failed") from exc
    if status < 200 or status >= 300:
        raise ContractError(f"API probe returned HTTP {status}")
    return (time.perf_counter_ns() - started) / 1_000_000


def collect(
    *,
    contract_path: Path,
    budget_id: str,
    base_url: str,
    origin: str,
    network_profile: str,
    source_address: str | None,
    candidate_label: str,
    release_version: str,
    repo_root: Path,
    authorization_env: str | None,
    body_file: Path | None,
    allow_state_changing_probe: bool,
    allow_http_localhost: bool,
    timeout_seconds: float,
    sample_count: int | None,
    warmup_count: int | None,
    opener: Callable[..., Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    contract = _load_json(contract_path)
    budgets = validate_budget_contract(contract)
    budget = budgets.get(budget_id)
    endpoint = ENDPOINTS.get(budget_id)
    if budget is None or endpoint is None or budget["scope"] != "controlled_origin":
        raise ContractError("budget id is not an allowlisted API latency metric")
    if budget["collector_id"] != COLLECTOR_ID:
        raise ContractError("budget collector owner mismatch")
    if budget_id.endswith(".current_origin_ms") and origin != "current":
        raise ContractError("current-origin budget requires --origin current")
    if endpoint.state_changing and not allow_state_changing_probe:
        raise ContractError("state-changing probe requires explicit authorization flag")
    normalized_base = _validate_base_url(
        base_url, allow_http_localhost=allow_http_localhost
    )
    authorization = _secret_from_env(
        authorization_env, required=endpoint.requires_auth
    )
    body = _request_body(body_file, required=endpoint.state_changing)
    normalized_source_address = _validate_source_address(source_address)
    request_opener = opener or (
        _build_source_bound_opener(normalized_source_address)
        if normalized_source_address is not None
        else urlopen
    )
    minimum_samples = int(budget["sampling"]["min_samples"])
    minimum_warmups = int(budget["sampling"]["warmups"])
    samples_required = sample_count if sample_count is not None else minimum_samples
    warmups_required = warmup_count if warmup_count is not None else minimum_warmups
    if samples_required < minimum_samples or warmups_required < minimum_warmups:
        raise ContractError("requested sample/warmup counts are below the budget method")
    if timeout_seconds <= 0 or timeout_seconds > 60:
        raise ContractError("timeout must be within 0..60 seconds")

    headers = {
        "Accept": "application/json",
        "User-Agent": f"POKROV-Performance-Probe/{COLLECTOR_VERSION}",
    }
    if authorization is not None:
        headers["Authorization"] = f"Bearer {authorization}"
    if body is not None:
        headers["Content-Type"] = "application/json"
    target = urljoin(normalized_base, endpoint.path.lstrip("/"))
    request = Request(target, data=body, headers=headers, method=endpoint.method)
    for _ in range(warmups_required):
        _sample_once(
            request,
            timeout_seconds=timeout_seconds,
            opener=request_opener,
        )
    samples = [
        _sample_once(
            request,
            timeout_seconds=timeout_seconds,
            opener=request_opener,
        )
        for _ in range(samples_required)
    ]

    revision, working_tree_state = _git_identity(repo_root)
    environment = {
        "architecture": platform.machine() or "unknown",
        "build_mode": "controlled-release-environment",
        "captured_at_utc": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "collector_id": COLLECTOR_ID,
        "collector_version": COLLECTOR_VERSION,
        "device_model": "api-probe-host",
        "network_profile": network_profile,
        "origin": origin,
        "os_version": platform.platform(),
        "platform": "web",
        "toolchain": f"python@{platform.python_version()}",
    }
    if normalized_source_address is not None:
        environment.update(
            {
                "proxy_policy": "disabled_for_source_bound_probe",
                "source_address": normalized_source_address,
            }
        )
    evidence = {
        "schema_version": contract["evidence_schema_version"],
        "budget_contract": {
            "id": contract["contract_id"],
            "sha256": contract_sha256(contract_path),
            "version": contract["contract_version"],
        },
        "release": {
            "candidate_label": candidate_label,
            "source_revision": revision,
            "version": release_version,
            "working_tree_state": working_tree_state,
        },
        "environment": environment,
        "measurements": [
            {
                "baseline": None,
                "budget_id": budget_id,
                "samples": samples,
                "state": "MEASURED",
                "unit": budget["unit"],
                "warmup_samples_discarded": warmups_required,
            }
        ],
    }
    outcome = evaluate_evidence(
        contract, evidence, contract_path=contract_path, required_scopes=set()
    )
    return evidence, outcome.summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--budget-id", choices=sorted(ENDPOINTS), required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--network-profile", required=True)
    parser.add_argument(
        "--source-address",
        help=(
            "Optional locally assigned literal IP. The probe disables URL proxy "
            "discovery and binds every request socket to this address."
        ),
    )
    parser.add_argument("--candidate-label", required=True)
    parser.add_argument("--release-version", default="1.2.0")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--authorization-env")
    parser.add_argument("--body-file", type=Path)
    parser.add_argument("--allow-state-changing-probe", action="store_true")
    parser.add_argument("--allow-http-localhost", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=10)
    parser.add_argument("--samples", type=int)
    parser.add_argument("--warmups", type=int)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gate-output", type=Path)
    return parser


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        evidence, summary = collect(
            contract_path=args.contract.resolve(),
            budget_id=args.budget_id,
            base_url=args.base_url,
            origin=args.origin,
            network_profile=args.network_profile,
            source_address=args.source_address,
            candidate_label=args.candidate_label,
            release_version=args.release_version,
            repo_root=args.repo_root.resolve(),
            authorization_env=args.authorization_env,
            body_file=args.body_file.resolve() if args.body_file else None,
            allow_state_changing_probe=args.allow_state_changing_probe,
            allow_http_localhost=args.allow_http_localhost,
            timeout_seconds=args.timeout_seconds,
            sample_count=args.samples,
            warmup_count=args.warmups,
        )
    except (ContractError, OSError, subprocess.CalledProcessError) as exc:
        print(f"API_LATENCY_PROBE_FAILED: {exc}", file=sys.stderr)
        return 2
    output_path = args.output.resolve()
    _write(output_path, evidence)
    if args.gate_output:
        _write(args.gate_output.resolve(), summary)
    print(
        json.dumps(
            {
                "budget_id": args.budget_id,
                "gate_status": summary["results"][0]["gate_status"],
                "output": str(output_path),
                "sample_count": summary["results"][0]["sample_count"],
                "value": summary["results"][0]["value"],
            },
            sort_keys=True,
        )
    )
    return 1 if summary["overall_status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
