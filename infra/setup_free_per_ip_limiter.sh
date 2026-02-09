#!/usr/bin/env bash
set -euo pipefail

# Per-IP limiter for a dedicated Free inbound port.
# This is the closest practical approximation to "50 Mbps per user" on stock xray/3x-ui.
#
# IMPORTANT:
# - This limits per SOURCE IP (not strict per account UUID).
# - Enforcement is drop-based (not HTB shaping), so throughput can fluctuate near limit.
#
# Usage:
#   ./setup_free_per_ip_limiter.sh [PORT] [RATE_KBPS] [BURST_KB]
# Example (50 Mbps):
#   ./setup_free_per_ip_limiter.sh 8443 6250 512

PORT="${1:-8443}"
RATE_KBPS="${2:-6250}"  # 50 Mbps ~= 6250 KBytes/s
BURST_KB="${3:-512}"
TABLE="portal_free_rate"

if ! command -v nft >/dev/null 2>&1; then
  echo "ERROR: nft not found. Install nftables first."
  exit 2
fi

echo "Applying per-IP limiter: port=${PORT} rate=${RATE_KBPS}KB/s burst=${BURST_KB}KB"

# Recreate table idempotently.
nft list table inet "${TABLE}" >/dev/null 2>&1 && nft delete table inet "${TABLE}" || true
nft add table inet "${TABLE}"

nft "add chain inet ${TABLE} input { type filter hook input priority 0; policy accept; }"
nft "add chain inet ${TABLE} output { type filter hook output priority 0; policy accept; }"

# Client -> server (upload) on Free port.
nft add rule inet "${TABLE}" input tcp dport "${PORT}" meter free_in_v4 \
  "{ ip saddr limit rate over ${RATE_KBPS} kbytes/second burst ${BURST_KB} kbytes }" counter drop
nft add rule inet "${TABLE}" input tcp dport "${PORT}" meter free_in_v6 \
  "{ ip6 saddr limit rate over ${RATE_KBPS} kbytes/second burst ${BURST_KB} kbytes }" counter drop

# Server -> client (download) on Free port.
nft add rule inet "${TABLE}" output tcp sport "${PORT}" meter free_out_v4 \
  "{ ip daddr limit rate over ${RATE_KBPS} kbytes/second burst ${BURST_KB} kbytes }" counter drop
nft add rule inet "${TABLE}" output tcp sport "${PORT}" meter free_out_v6 \
  "{ ip6 daddr limit rate over ${RATE_KBPS} kbytes/second burst ${BURST_KB} kbytes }" counter drop

nft list table inet "${TABLE}"

