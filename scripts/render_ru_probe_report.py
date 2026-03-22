from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _status(value: Any) -> str:
    if isinstance(value, bool):
        return "ok" if value else "fail"
    if value is None:
        return "unknown"
    text = str(value).strip()
    return text or "unknown"


def _render(payload: dict[str, Any]) -> str:
    timestamp = payload.get("timestamp_utc") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    probe_host = payload.get("probe_host", "unknown")
    probe_ip = payload.get("probe_public_ip", "unknown")
    google_status = _status(payload.get("google_reachable"))
    notes = payload.get("notes", [])
    nodes = payload.get("nodes", {})

    lines = [
        "# RU Probe Report",
        "",
        f"- timestamp_utc: `{timestamp}`",
        f"- probe_host: `{probe_host}`",
        f"- probe_public_ip: `{probe_ip}`",
        f"- google.com: `{google_status}`",
        "",
        "## Nodes",
        "",
    ]

    if not nodes:
        lines.append("- no node results were provided")
    else:
        for name in sorted(nodes):
            item = nodes[name] or {}
            reachability = _status(item.get("reachable"))
            address = item.get("address", "unknown")
            detail = item.get("detail", "")
            row = f"- `{name}` `{address}` -> `{reachability}`"
            if detail:
                row += f" ({detail})"
            lines.append(row)

    lines.extend(["", "## Notes", ""])
    if notes:
        for note in notes:
            lines.append(f"- {note}")
    else:
        lines.append("- no extra notes")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- If `google.com` is down here, treat this run as a probe-host problem first.",
            "- If `google.com` is up but nodes fail, treat it as a node or public-edge incident.",
            "- If legacy hosts still work while canonical `pokrov.space` paths fail, treat it as a hostname migration incident.",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a compact markdown report from an RU probe JSON payload.")
    parser.add_argument("--input", required=True, help="Path to probe JSON file.")
    parser.add_argument("--output", default="", help="Optional path to write markdown output.")
    args = parser.parse_args()

    payload = _load_payload(Path(args.input))
    report = _render(payload)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
