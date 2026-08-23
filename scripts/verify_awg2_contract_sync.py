from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


CONTRACT_FILENAME = "config/awg2-capability.json"
PLATFORM_FILENAME = "portal_bot/awg2_lab_service.py"
CLIENT_FILENAME = "packages/runtime_engine/lib/runtime_engine.dart"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract(pattern: str, text: str, *, label: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    if match is None:
        raise ValueError(f"missing {label}")
    return match.group(1)


def verify_awg2_contract_sync(
    *, platform_root: Path, core_root: Path, client_root: Path
) -> dict[str, object]:
    contract_path = core_root / CONTRACT_FILENAME
    platform_path = platform_root / PLATFORM_FILENAME
    client_path = client_root / CLIENT_FILENAME

    contract_bytes = contract_path.read_bytes()
    contract = json.loads(contract_bytes.decode("utf-8"))
    contract_id = str(contract.get("contract_id") or "")
    contract_sha256 = hashlib.sha256(contract_bytes).hexdigest()
    if not contract_id:
        raise ValueError("Core AWG2 contract_id is missing")

    platform_source = _read_text(platform_path)
    platform_id = _extract(
        r'^AWG2_CONTRACT_ID\s*=\s*"([^"]+)"$',
        platform_source,
        label="platform AWG2_CONTRACT_ID",
    )
    platform_sha = _extract(
        r'^AWG2_CONTRACT_SHA256\s*=\s*\(\s*"([0-9a-f]{64})"\s*\)',
        platform_source,
        label="platform AWG2_CONTRACT_SHA256",
    )

    client_source = _read_text(client_path)
    client_id = _extract(
        r"^const _pokrovAwg2ContractId\s*=\s*'([^']+)';$",
        client_source,
        label="client _pokrovAwg2ContractId",
    )
    client_sha = _extract(
        r"^const _pokrovAwg2ContractSha256\s*=\s*\n\s*'([0-9a-f]{64})';$",
        client_source,
        label="client _pokrovAwg2ContractSha256",
    )

    consumers = {
        "platform": {"contract_id": platform_id, "contract_sha256": platform_sha},
        "client": {"contract_id": client_id, "contract_sha256": client_sha},
    }
    mismatches = [
        name
        for name, value in consumers.items()
        if value["contract_id"] != contract_id
        or value["contract_sha256"] != contract_sha256
    ]
    if mismatches:
        joined = ", ".join(mismatches)
        raise ValueError(
            f"AWG2 contract drift in {joined}: expected {contract_id} "
            f"sha256={contract_sha256}"
        )

    return {
        "schema": "pokrov-awg2-contract-sync/v1",
        "status": "PASS",
        "contract_id": contract_id,
        "contract_sha256": contract_sha256,
        "core_contract": contract_path.as_posix(),
        "consumers": consumers,
        "evidence_ceiling": "LOCAL_SOURCE_CONTRACT_ONLY",
        "candidate_proven": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the pinned AWG2 contract across Core, platform and client."
    )
    parser.add_argument("--platform-root", type=Path, default=Path.cwd())
    parser.add_argument("--core-root", type=Path, required=True)
    parser.add_argument("--client-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = verify_awg2_contract_sync(
        platform_root=args.platform_root.resolve(),
        core_root=args.core_root.resolve(),
        client_root=args.client_root.resolve(),
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
