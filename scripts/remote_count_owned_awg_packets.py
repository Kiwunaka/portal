from __future__ import annotations

import argparse
import json
import os
import shlex
from pathlib import Path
from typing import Any

from node_access import DEFAULT_PASSWORDS, connect_node
from remote_activate_owned_awg_labs import _node_host


PROFILE_PORTS = {
    "awg2_lab": 4500,
    "awg31_lab": 3478,
}
PROFILE_INTERFACES = {
    "awg2_lab": "pokrovawg2",
    "awg31_lab": "pokrovawg31",
}


def _outer_size_classifier(profile: str) -> dict[str, Any]:
    if profile == "awg2_lab":
        return {
            "mode": "fixed_sizes_v1",
            "applicable": True,
            "awk": (
                "$NF >= 40 && $NF <= 70 { junk += 1 } "
                "$NF == 148 { initiation += 1 } "
                "$NF == 92 { response += 1 } "
            ),
        }
    if profile == "awg31_lab":
        return {
            "mode": "not_applicable_randomized_trailers",
            "applicable": False,
            "awk": "",
        }
    raise ValueError("unknown owned AWG profile")


def _run(client: Any, command: str, *, timeout: int) -> str:
    _stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    output = stdout.read().decode("utf-8", "replace").strip()
    error = stderr.read().decode("utf-8", "replace").strip()
    if code != 0:
        raise RuntimeError((error or "remote packet counter failed")[:240])
    return output


def _inner_capture_command(interface: str, duration: int) -> str:
    classifier = (
        'function from_client(line) { '
        'return (client4 != "" && index(line, "IP " client4 ".") > 0) || '
        '(client6 != "" && index(line, "IP6 " client6 ".") > 0) } '
        'function to_client(line) { '
        'return (client4 != "" && index(line, " > " client4 ".") > 0) || '
        '(client6 != "" && index(line, " > " client6 ".") > 0) } '
        '{ if (from_client($0)) from_count += 1; '
        'if (to_client($0)) to_count += 1; '
        'if ($0 ~ /Flags \\[S\\]/) syn += 1; '
        'if ($0 ~ /Flags \\[S\\.\\]/) syn_ack += 1; '
        'if ($0 ~ /Flags \\[R/) reset += 1; '
        'if ($0 ~ /ICMP/) icmp += 1; '
        'if ($0 ~ / UDP,/) udp += 1; '
        'if ($0 ~ /Flags \\[/) tcp += 1 } '
        'END { print NR+0, from_count+0, to_count+0, syn+0, '
        'syn_ack+0, reset+0, icmp+0, tcp+0, udp+0 }'
    )
    return (
        "client4=$(/usr/local/bin/awg show "
        + shlex.quote(interface)
        + " allowed-ips | awk 'NR==1 { count=split($2, values, \",\"); "
        "for (i=1; i<=count; i++) { if (values[i] ~ /^[0-9]+\\./) { "
        'sub(/\\/.*/, "", values[i]); print values[i]; exit } } }\'); '
        "client6=$(/usr/local/bin/awg show "
        + shlex.quote(interface)
        + " allowed-ips | awk 'NR==1 { count=split($2, values, \",\"); "
        "for (i=1; i<=count; i++) { if (values[i] ~ /:/) { "
        'sub(/\\/.*/, "", values[i]); print values[i]; exit } } }\'); '
        "test -n \"$client4$client6\"; "
        f"timeout -s INT {duration}s tcpdump -tt -nn -l -i "
        + shlex.quote(interface)
        + " 'ip or ip6' 2>/dev/null | awk "
        + '-v client4="$client4" -v client6="$client6" '
        + shlex.quote(classifier)
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Count packets on one owned AWG lab UDP port without returning addresses."
    )
    parser.add_argument("profile", choices=tuple(PROFILE_PORTS))
    parser.add_argument("--duration-seconds", type=int, default=55)
    parser.add_argument(
        "--capture-scope",
        choices=("outer", "inner"),
        default="outer",
        help="Count encrypted UDP packets or classified inner tunnel packets.",
    )
    parser.add_argument("--brain-ip", default="82.21.114.104")
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--known-hosts", required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    duration = int(args.duration_seconds)
    if duration < 5 or duration > 60:
        raise SystemExit("duration must be between 5 and 60 seconds")
    known_hosts = Path(args.known_hosts).resolve()
    passwords = Path(args.passwords).resolve()
    if not known_hosts.is_file() or not passwords.is_file():
        raise SystemExit("SSH trust or authentication input is missing")

    os.environ["POKROV_SSH_KNOWN_HOSTS"] = str(known_hosts)
    brain, _brain_auth = connect_node(
        code="brain",
        host=str(args.brain_ip),
        passwords_path=passwords,
    )
    node = None
    try:
        node_host = _node_host(brain)
        node, _node_auth = connect_node(
            code="de",
            host=node_host,
            passwords_path=passwords,
        )
        interface = PROFILE_INTERFACES[str(args.profile)]
        if str(args.capture_scope) == "inner":
            safe_counts = _run(
                node,
                _inner_capture_command(interface, duration),
                timeout=duration + 20,
            ).split()
            if len(safe_counts) != 9:
                raise RuntimeError("remote inner packet classification failed")
            (
                packet_count,
                from_client_packets,
                to_client_packets,
                syn_packets,
                syn_ack_packets,
                reset_packets,
                icmp_packets,
                tcp_packets,
                udp_packets,
            ) = map(int, safe_counts)
        else:
            port = PROFILE_PORTS[str(args.profile)]
            size_classifier = _outer_size_classifier(str(args.profile))
            capture = (
                f"timeout -s INT {duration}s tcpdump -tt -nn -l -i any "
                + shlex.quote(f"udp port {port}")
                + " 2>/dev/null | awk "
                + shlex.quote(
                    "$0 ~ / In / { inbound += 1 } "
                    "$0 ~ / Out / { outbound += 1 } "
                    + str(size_classifier["awk"])
                    + "END { print NR+0, inbound+0, outbound+0, junk+0, initiation+0, response+0 }"
                )
            )
            safe_counts = _run(node, capture, timeout=duration + 20).split()
            if len(safe_counts) != 6:
                raise RuntimeError("remote packet direction count failed")
            (
                packet_count,
                inbound_packets,
                outbound_packets,
                junk_sized_packets,
                initiation_sized_packets,
                response_sized_packets,
            ) = map(int, safe_counts)
        stats_command = (
            "latest=$(/usr/local/bin/awg show "
            + shlex.quote(interface)
            + " latest-handshakes | awk 'NR==1 { print $2+0 }'); "
            "set -- $(/usr/local/bin/awg show "
            + shlex.quote(interface)
            + " transfer | awk 'NR==1 { print $2+0, $3+0 }'); "
            "now=$(date +%s); "
            "if [ \"$latest\" -gt 0 ]; then age=$((now-latest)); else age=-1; fi; "
            "printf '%s %s %s' \"$age\" \"${1:-0}\" \"${2:-0}\""
        )
        safe_stats = _run(node, stats_command, timeout=20).split()
        if len(safe_stats) != 3:
            raise RuntimeError("remote AWG statistics readback failed")
        result = {
            "schema_version": "pokrov-owned-awg-packet-count-v1",
            "profile": str(args.profile),
            "capture_scope": str(args.capture_scope),
            "duration_seconds": duration,
            "packet_count": packet_count,
            "latest_handshake_age_seconds": int(safe_stats[0]),
            "received_bytes": int(safe_stats[1]),
            "sent_bytes": int(safe_stats[2]),
            "raw_addresses_returned": False,
        }
        if str(args.capture_scope) == "inner":
            result.update(
                {
                    "from_client_packets": from_client_packets,
                    "to_client_packets": to_client_packets,
                    "syn_packets": syn_packets,
                    "syn_ack_packets": syn_ack_packets,
                    "reset_packets": reset_packets,
                    "icmp_packets": icmp_packets,
                    "tcp_packets": tcp_packets,
                    "udp_packets": udp_packets,
                }
            )
        else:
            result.update(
                {
                    "inbound_packets": inbound_packets,
                    "outbound_packets": outbound_packets,
                    "unknown_direction_packets": max(
                        0, packet_count - inbound_packets - outbound_packets
                    ),
                    "junk_sized_packets": junk_sized_packets,
                    "initiation_sized_packets": initiation_sized_packets,
                    "response_sized_packets": response_sized_packets,
                    "packet_size_classification": size_classifier["mode"],
                    "fixed_size_classification_applicable": size_classifier[
                        "applicable"
                    ],
                }
            )
        print(json.dumps(result, sort_keys=True))
        return 0
    finally:
        if node is not None:
            node.close()
        brain.close()


if __name__ == "__main__":
    raise SystemExit(main())
