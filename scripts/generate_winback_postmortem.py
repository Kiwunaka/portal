from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_ROOT = REPO_ROOT / "portal_bot"
if str(PORTAL_ROOT) not in sys.path:
    sys.path.insert(0, str(PORTAL_ROOT))

from commercial_pilot_decision_service import build_winback_postmortem  # noqa: E402


def generate_postmortem(decision_pack: Mapping[str, Any]) -> dict[str, Any]:
    if str(decision_pack.get("schema") or "") != "pokrov-winback-decision-pack-v1":
        raise ValueError("winback_decision_pack_schema_invalid")
    return build_winback_postmortem(decision_pack)


def _read_json(path: Path) -> dict[str, Any]:
    decoded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("winback_decision_pack_must_be_object")
    return decoded


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a machine-readable winback postmortem from a decision pack.",
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--require-winner",
        action="store_true",
        help="Fail unless matured primary-metric and holdout evidence permit a winner.",
    )
    args = parser.parse_args(argv)
    try:
        postmortem = generate_postmortem(_read_json(args.input))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    if args.require_winner and postmortem.get("winner_state") != "ready":
        print(
            "BLOCKED: winner requires matured net_revenue_30d_per_capacity_unit, ready holdout evidence and a complete observation window",
            file=sys.stderr,
        )
        return 3
    rendered = json.dumps(postmortem, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    if args.output is None:
        sys.stdout.write(rendered)
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
