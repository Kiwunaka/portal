from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


RE_IPV4 = re.compile(r"(\d{1,3}(?:\.\d{1,3}){3})")
RE_IPV6 = re.compile(r"\b(?:[0-9a-fA-F]{0,4}:){2,}[0-9a-fA-F]{0,4}\b")
RE_ROW = re.compile(r"^\|\s*`(?P<code>[^`]+)`\s*\|.*\|\s*`(?P<ip>[^`]+)`\s*\|\s*$")


@dataclass
class NodeHost:
    code: str
    host: str
    expected_ipv4: str | None = None


def _parse_inventory_ipv4(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = RE_ROW.match(line.strip())
        if not m:
            continue
        code = m.group("code").strip().lower()
        ip = m.group("ip").strip()
        if code and RE_IPV4.fullmatch(ip):
            out[code] = ip
    return out


def _resolve(host: str, resolver: str | None) -> tuple[list[str], list[str], str]:
    cmd = ["nslookup", host]
    if resolver:
        cmd.append(resolver)
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    raw = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    section = raw.split("Name:", 1)[1] if "Name:" in raw else raw

    ips_v4: list[str] = []
    ips_v6: list[str] = []
    for ip4 in RE_IPV4.findall(section):
        if ip4 not in ips_v4:
            ips_v4.append(ip4)
    for ip6 in RE_IPV6.findall(section):
        if ip6 not in ips_v6:
            ips_v6.append(ip6)
    return ips_v4, ips_v6, raw


def _build_hosts(*, domain: str, include_brain: bool, inventory: dict[str, str]) -> list[NodeHost]:
    hosts = [
        NodeHost(code="pl", host=f"pl.{domain}", expected_ipv4=inventory.get("pl")),
        NodeHost(code="it", host=f"it.{domain}", expected_ipv4=inventory.get("it")),
        NodeHost(code="us", host=f"us.{domain}", expected_ipv4=inventory.get("us")),
    ]
    if include_brain:
        hosts.append(NodeHost(code="brain", host=domain, expected_ipv4=inventory.get("brain")))
    return hosts


def main() -> int:
    ap = argparse.ArgumentParser(description="Run DNS audit against multiple resolvers for node hosts.")
    ap.add_argument("--domain", required=True, help="Root domain, e.g. kiwunaka.space")
    ap.add_argument("--inventory", default="docs/08-node-inventory.md")
    ap.add_argument("--include-brain", action="store_true")
    ap.add_argument("--resolvers", default="system,1.1.1.1,8.8.8.8,9.9.9.9")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    inventory = _parse_inventory_ipv4(Path(args.inventory))
    hosts = _build_hosts(domain=args.domain.strip().lower(), include_brain=args.include_brain, inventory=inventory)
    resolvers = [r.strip() for r in args.resolvers.split(",") if r.strip()]

    matrix: dict[str, dict] = {}
    global_warnings: list[dict] = []

    for resolver in resolvers:
        resolver_key = resolver
        resolver_addr = None if resolver.lower() == "system" else resolver
        report = {"hosts": [], "warnings": []}
        aaaa_to_hosts: dict[str, list[str]] = defaultdict(list)
        host_to_expected: dict[str, str | None] = {}

        for node in hosts:
            host_to_expected[node.host] = node.expected_ipv4
            a_records, aaaa_records, raw = _resolve(node.host, resolver_addr)
            for ip6 in aaaa_records:
                aaaa_to_hosts[ip6].append(node.host)

            warnings: list[str] = []
            if not a_records:
                warnings.append("missing_a_record")
            if node.expected_ipv4 and node.expected_ipv4 not in a_records:
                warnings.append(f"expected_ipv4_not_found:{node.expected_ipv4}")
            if aaaa_records:
                warnings.append("has_aaaa_records")

            report["hosts"].append(
                {
                    "code": node.code,
                    "host": node.host,
                    "expected_ipv4": node.expected_ipv4,
                    "a_records": a_records,
                    "aaaa_records": aaaa_records,
                    "warnings": warnings,
                    "raw_nslookup": raw,
                }
            )

        for ip6, bound_hosts in aaaa_to_hosts.items():
            if len(bound_hosts) < 2:
                continue
            expected_set = {host_to_expected.get(h) for h in bound_hosts}
            if len(expected_set) > 1:
                warning = {
                    "type": "shared_aaaa_across_different_nodes",
                    "resolver": resolver_key,
                    "ip6": ip6,
                    "hosts": bound_hosts,
                }
                report["warnings"].append(warning)
                global_warnings.append(warning)

        matrix[resolver_key] = report

    result = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "domain": args.domain.strip().lower(),
        "inventory_path": args.inventory,
        "resolvers": resolvers,
        "matrix": matrix,
        "warnings": global_warnings,
    }

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Report saved: {out_path}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
