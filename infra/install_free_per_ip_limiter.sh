#!/usr/bin/env bash
set -euo pipefail

# Install a systemd unit for per-IP limiter on Free inbound port.
#
# Usage:
#   PORT=8443 RATE_KBPS=6250 BURST_KB=512 ./install_free_per_ip_limiter.sh
#
# Defaults map to ~50 Mbps per IP.

PORT="${PORT:-8443}"
RATE_KBPS="${RATE_KBPS:-6250}"
BURST_KB="${BURST_KB:-512}"

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

install -m 0755 "${SRC_DIR}/setup_free_per_ip_limiter.sh" /usr/local/sbin/portal-free-per-ip-limiter

cat >/etc/systemd/system/portal-free-per-ip-limiter.service <<EOF
[Unit]
Description=Portal Free per-IP limiter (${RATE_KBPS}KB/s on port ${PORT})
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/portal-free-per-ip-limiter ${PORT} ${RATE_KBPS} ${BURST_KB}
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now portal-free-per-ip-limiter.service
systemctl --no-pager status portal-free-per-ip-limiter.service || true

