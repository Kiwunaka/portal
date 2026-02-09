#!/usr/bin/env bash
set -euo pipefail

# Install a systemd unit that applies the free tier egress shaper on boot.
#
# Usage (as root):
#   PORT=8443 RATE=50mbit ./install_free_egress_shaper.sh
#
# Defaults:
#   PORT=8443
#   RATE=50mbit

PORT="${PORT:-8443}"
RATE="${RATE:-50mbit}"

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

install -m 0755 "${SRC_DIR}/setup_free_egress_shaper.sh" /usr/local/sbin/portal-free-egress-shaper

cat >/etc/systemd/system/portal-free-egress-shaper.service <<EOF
[Unit]
Description=Portal free tier egress shaper (aggregate bandwidth on port ${PORT})
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/portal-free-egress-shaper ${PORT} ${RATE}
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now portal-free-egress-shaper.service
systemctl --no-pager status portal-free-egress-shaper.service || true

