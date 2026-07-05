#!/usr/bin/env bash
set -euo pipefail

# Bootstrap a fresh Ubuntu node for a multi-location "Portal" setup.
# This script is intentionally conservative and documents manual steps where
# provider-specific behavior is common (3x-ui installer URLs, etc).
#
# Run as root on the NEW node.

CONTROL_PLANE_IP="${CONTROL_PLANE_IP:-}"
PANEL_PORT="${PANEL_PORT:-8444}"           # panel reverse-proxy port
XRAY_PORT="${XRAY_PORT:-443}"              # user traffic port
SSH_PORT="${SSH_PORT:-29374}"              # optional

if [[ -z "${CONTROL_PLANE_IP}" ]]; then
  echo "ERROR: set CONTROL_PLANE_IP env var to the public IP of your control-plane node"
  exit 1
fi

echo "[1/8] System update"
apt-get update -y
apt-get upgrade -y

echo "[2/8] Firewall baseline (UFW)"
apt-get install -y ufw
ufw default deny incoming
ufw default allow outgoing
ufw allow 80/tcp
ufw allow 443/tcp

echo "[3/8] SSH hardening (optional port change)"
apt-get install -y openssh-server
ufw allow "${SSH_PORT}/tcp"
sed -i "s/^#Port 22/Port ${SSH_PORT}/" /etc/ssh/sshd_config
sed -i "s/^Port 22/Port ${SSH_PORT}/" /etc/ssh/sshd_config
grep -q '^PermitEmptyPasswords no' /etc/ssh/sshd_config || printf '\nPermitEmptyPasswords no\n' >> /etc/ssh/sshd_config
grep -q '^KbdInteractiveAuthentication no' /etc/ssh/sshd_config || printf 'KbdInteractiveAuthentication no\n' >> /etc/ssh/sshd_config
systemctl restart ssh || systemctl restart sshd

echo "[4/8] Fail2Ban"
apt-get install -y fail2ban
cat > /etc/fail2ban/jail.local <<EOF
[sshd]
enabled = true
port = ${SSH_PORT}
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
findtime = 10m
bantime = 1h
bantime.increment = true
bantime.factor = 2
bantime.maxtime = 24h
EOF
systemctl enable fail2ban
systemctl restart fail2ban

echo "[5/8] Install 3x-ui"
echo "NOTE: 3x-ui install method changes over time. Install it now, then continue."
echo "Recommended: install 3x-ui, then ensure panel listens on localhost only."
echo "After install, ensure xray inbound for VLESS Reality is on ${XRAY_PORT}."
echo "Also enable xray access logging to /var/log/xray/access.log for observer-lite."

echo "[6/8] Panel access restriction"
echo "Goal: expose panel ONLY to control-plane IP, via a reverse proxy on port ${PANEL_PORT}."
echo "Options:"
echo "- bind 3x-ui to 127.0.0.1 and proxy it with Caddy/Nginx on :${PANEL_PORT}"
echo "- allow UFW only from CONTROL_PLANE_IP to :${PANEL_PORT}"

ufw allow from "${CONTROL_PLANE_IP}" to any port "${PANEL_PORT}" proto tcp

echo "[7/8] Enable UFW"
ufw --force enable

echo "[8/8] Next manual actions"
cat <<EOF

1) In 3x-ui:
   - Create/confirm inbound (VLESS Reality) on port ${XRAY_PORT}
   - Note these values for the control-plane DB:
     - host: <subdomain> (e.g. us.<your-domain>)
     - reality_sni
     - reality_pbk
     - reality_sid
     - inbound_id
     - panel_path (the random path prefix used in panel URLs)

2) Configure DNS:
   - Add A record: <code>.<your-domain> -> this node IP

3) Add node to DB on control-plane:
   - Run scripts/add_node.py with the collected parameters.

4) Sync users to the new node:
   - Run scripts/migrate_to_nodes.py --node <code>

5) Install observer-lite collector after the node exists in control-plane:
   - Run scripts/remote_install_node_observer.py --brain-ip ${CONTROL_PLANE_IP} --node-code <code> --run-now

EOF
