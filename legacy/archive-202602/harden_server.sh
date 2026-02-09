#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF'
DEPRECATED

This repo now uses a node bootstrap flow in:
- infra/bootstrap_node.sh

If you still need a one-off hardening pass for an existing server:
1) Restrict panel access (UFW allowlist to control-plane IP only)
2) Enable fail2ban
3) Keep SSH hardened (keys, non-root if possible, limited IPs)

See:
- docs/03-ops-node.md
- docs/02-ops-control-plane.md
EOF

