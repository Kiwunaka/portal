#!/usr/bin/env python3
"""Fail closed when the platform and client Smart DNS policies differ."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLATFORM_POLICY = ROOT / "shared" / "contracts" / "network" / "smart-dns-policy.v1.json"
CLIENT_POLICY_RELATIVE = Path("config") / "smart-dns-policy.v1.json"


class PolicyParityError(ValueError):
    pass


def _load_policy(path: Path) -> tuple[bytes, dict[str, Any]]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise PolicyParityError(f"policy file unavailable: {path}") from exc
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PolicyParityError(f"policy JSON invalid: {path}") from exc
    if not isinstance(document, dict):
        raise PolicyParityError(f"policy root must be an object: {path}")
    return raw, document


def check_policy_parity(platform_policy: Path, client_policy: Path) -> str:
    platform_raw, platform = _load_policy(platform_policy)
    client_raw, client = _load_policy(client_policy)
    if platform != client:
        raise PolicyParityError("platform and client Smart DNS policy documents differ")
    if platform_raw != client_raw:
        raise PolicyParityError("platform and client Smart DNS policy bytes differ")
    if platform.get("schema_version") != "pokrov-smart-dns-policy-v1":
        raise PolicyParityError("unsupported Smart DNS policy schema")
    if platform.get("state") != "owner_lab_default_off":
        raise PolicyParityError("Smart DNS policy must remain owner-lab default-off")
    if platform.get("recursive_dns") is not False:
        raise PolicyParityError("recursive Smart DNS is forbidden")
    groups = platform.get("groups")
    if not isinstance(groups, dict) or set(groups) != {"ai", "gaming_services"}:
        raise PolicyParityError("Smart DNS groups must be exactly ai and gaming_services")
    digest = hashlib.sha256(platform_raw).hexdigest()
    return digest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--platform-policy",
        type=Path,
        default=PLATFORM_POLICY,
    )
    parser.add_argument(
        "--client-root",
        type=Path,
        required=True,
        help="root of the POKROV-app checkout",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    digest = check_policy_parity(
        args.platform_policy.resolve(),
        (args.client_root.resolve() / CLIENT_POLICY_RELATIVE),
    )
    print(f"Smart DNS policy parity passed: sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
