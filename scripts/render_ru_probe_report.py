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


def _render_v2(payload: dict[str, Any]) -> str:
    probe_host = dict(payload.get("probe_host") or {})
    host_id = str(probe_host.get("id") or "unknown")
    host_label = str(probe_host.get("label") or "unknown")
    public_ip = str(probe_host.get("public_ip") or "unknown")
    lines = [
        "# RU Probe Report",
        "",
        f"- finished_at: `{payload.get('finished_at', 'unknown')}`",
        f"- probe_host: `{host_id}` — {host_label}",
        f"- probe_public_ip: `{public_ip}`",
        f"- execution_status: `{_status(payload.get('execution_status'))}`",
        f"- manifest_revision: `{payload.get('manifest_revision', 'unknown')}`",
        f"- runner_version: `{payload.get('runner_version', 'unknown')}`",
        "",
        "## Targets",
        "",
    ]
    targets = list(payload.get("targets") or [])
    if not targets:
        lines.append("- no target results were provided")
    for target in targets:
        endpoint = dict(target.get("endpoint") or {})
        stages = dict(target.get("stages") or {})
        stage_parts = [
            f"{stage_name}={_status(dict(stages.get(stage_name) or {}).get('status'))}"
            for stage_name in (
                "dns",
                "tcp",
                "tls",
                "http_large_body",
                "transport_handshake",
            )
        ]
        family_status = dict(target.get("address_family_status") or {})
        family_parts = [
            f"{family}={_status(family_status.get(family))}"
            for family in ("ipv4", "ipv6")
        ]
        row = (
            f"- `{target.get('target_id', 'unknown')}` "
            f"`{target.get('target_kind', 'target')}` "
            f"`{endpoint.get('host', 'unknown')}:{endpoint.get('port', 'unknown')}` "
            f"[{', '.join(stage_parts)}] "
            f"[{', '.join(family_parts)}]"
        )
        detail_code = target.get("detail_code")
        if detail_code:
            row += f" (`{detail_code}`)"
        lines.append(row)
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Stage states are shown exactly as `pass`, `fail`, `not_run`, or `not_applicable`.",
            "- Server-side verdicts remain authoritative because required stages come from the signed manifest.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render(payload: dict[str, Any]) -> str:
    if payload.get("schema_version") == 2:
        return _render_v2(payload)
    timestamp = payload.get("timestamp_utc") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    probe_host = payload.get("probe_host", "unknown")
    probe_ip = payload.get("probe_public_ip", "unknown")
    google_status = _status(payload.get("google_reachable"))
    notes = payload.get("notes", [])
    nodes = payload.get("nodes", {})
    classifications = payload.get("classifications", [])
    reserve = payload.get("reserve", {})
    targets = payload.get("targets", [])

    lines = [
        "# RU Probe Report",
        "",
        f"- timestamp_utc: `{timestamp}`",
        f"- probe_host: `{probe_host}`",
        f"- probe_public_ip: `{probe_ip}`",
        f"- google.com: `{google_status}`",
        "",
    ]

    if reserve or classifications:
        lines.extend(["## Reserve", ""])
        reserve_host = reserve.get("host", "unknown")
        lines.append(f"- reserve_host: `{reserve_host}`")
        lines.append(f"- xhttp: `{_status(reserve.get('xhttp_alive'))}`")
        lines.append(f"- hysteria2: `{_status(reserve.get('hysteria_alive'))}`")
        lines.append("")
        lines.append("## Classification")
        lines.append("")
        if classifications:
            for item in classifications:
                lines.append(f"- `{item}`")
        else:
            lines.append("- no classifications")
        lines.append("")

    if targets:
        lines.extend(["## Targets", ""])
        for item in targets:
            name = item.get("name", "unknown")
            kind = item.get("kind", "target")
            host = item.get("host", "unknown")
            port = item.get("port", "unknown")
            parts = [
                f"dns={_status(item.get('dns_ok'))}",
                f"tcp={_status(item.get('tcp_ok'))}",
                f"tls={_status(item.get('tls_ok'))}",
            ]
            if item.get("http_ok") is not None:
                parts.append(f"http={_status(item.get('http_ok'))}")
            if item.get("udp_ok") is not None:
                parts.append(f"udp={_status(item.get('udp_ok'))}")
            detail = str(item.get("detail") or "").strip()
            row = f"- `{name}` `{kind}` `{host}:{port}` -> `{_status(item.get('ok'))}` [{', '.join(parts)}]"
            if detail:
                row += f" ({detail})"
            lines.append(row)
        lines.append("")

    lines.extend([
        "## Nodes",
        "",
    ])

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
            "- If `google.com` is up but foreign nodes fail, treat it as a node or public-edge incident.",
            "- If legacy hosts still work while canonical `pokrov.space` paths fail, treat it as a hostname migration incident.",
            "- If `xhttp` is alive but `hysteria2` is not, keep the reserve bridge on the TCP path only.",
            "- If `hysteria2` is alive, treat it as a reserve-only contour until repeated RU probes confirm stability.",
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
