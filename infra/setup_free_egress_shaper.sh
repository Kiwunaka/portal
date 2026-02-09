#!/usr/bin/env bash
set -euo pipefail

# Shape egress traffic for clients connected to a dedicated inbound port (default: 8443).
# This limits the TOTAL bandwidth for that port (shared across all clients on that inbound).
#
# Usage:
#   ./setup_free_egress_shaper.sh [PORT] [RATE]
# Examples:
#   ./setup_free_egress_shaper.sh 8443 50mbit
#
# Notes:
# - This is best-effort. Exact rates may vary.
# - For per-user limits you need a more complex per-IP classifier.

PORT="${1:-8443}"
RATE="${2:-50mbit}"

DEV="${DEV:-}"
if [[ -z "${DEV}" ]]; then
  DEV="$(ip route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}' || true)"
fi

if [[ -z "${DEV}" ]]; then
  echo "ERROR: could not auto-detect network interface. Set DEV=eth0 (or ens3, etc)."
  exit 2
fi

echo "Applying egress shaper on dev=${DEV} port=${PORT} rate=${RATE}"

# Reset existing root qdisc if any.
tc qdisc del dev "${DEV}" root 2>/dev/null || true

tc qdisc add dev "${DEV}" root handle 1: htb default 30
tc class add dev "${DEV}" parent 1: classid 1:1 htb rate 1000mbit ceil 1000mbit

# Free tier class.
tc class add dev "${DEV}" parent 1:1 classid 1:10 htb rate "${RATE}" ceil "${RATE}" prio 1
tc qdisc add dev "${DEV}" parent 1:10 handle 10: fq_codel

# Default class for everything else.
tc class add dev "${DEV}" parent 1:1 classid 1:30 htb rate 1000mbit ceil 1000mbit prio 2
tc qdisc add dev "${DEV}" parent 1:30 handle 30: fq_codel

# Classify by server source port (inbound port).
tc filter add dev "${DEV}" protocol ip parent 1: prio 1 u32 match ip sport "${PORT}" 0xffff flowid 1:10
tc filter add dev "${DEV}" protocol ipv6 parent 1: prio 1 u32 match ip6 sport "${PORT}" 0xffff flowid 1:10 2>/dev/null || true

tc -s qdisc show dev "${DEV}"
tc -s class show dev "${DEV}"

