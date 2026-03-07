# Ops: Node (Country Server)

Each delivery node is an independent server in a specific country:
- runs `3x-ui + xray`
- exposes user traffic on `:443`
- exposes panel only to control-plane IP (recommended)

Current production note (verified 7 March 2026):
- active delivery nodes: `free`, `it`, `nl`, `pl`, `us`;
- `brain` also has x-ui installed, but is disabled in the current delivery pool;
- all standard delivery nodes use the same protocol profile: `vless/tcp/reality` on `443`.

## Bootstrap

Run on the new node (manual):

```bash
CONTROL_PLANE_IP=<your control plane public ip> bash infra/bootstrap_node.sh
```

Or run from your local machine via SSH:

```bash
python scripts/remote_bootstrap_nodes.py --add-pubkeys
```

After bootstrap:
1. (Optional) Move SSH to `29374`:
   - `python scripts/configure_ssh_additional_port.py --only brain,pl,it,us,nl,free --add-port 29374`
2. Create a standard VLESS Reality inbound on each worker node:
   - `python scripts/create_reality_inbounds.py --only pl,it,us,nl,free`
3. Seed the runtime DB from generated facts using the actual runtime `DATABASE_URL`:
   - `set -a; . /root/portal_bot/.env; set +a; python scripts/seed_nodes_from_facts.py`

## Standard Inbound Settings (Workers)

Created by `scripts/create_reality_inbounds.py`:
- Port: `443/tcp`
- Protocol: `vless`
- Transport: `tcp`
- TLS security: `reality`
- Flow: `xtls-rprx-vision`
- uTLS fingerprint (client): `firefox` (configurable in DB per node)
- Reality:
  - `dest`: operator-specific HTTPS host
  - `serverNames`: same as chosen `dest` host
  - `shortIds`: random 8-byte hex id (stored as `reality_sid` in runtime DB)
  - `privateKey`: generated per-node and stays on the node; control-plane stores only the derived `publicKey`
- Sniffing: enabled, `destOverride=["http","tls","quic"]`

Then (production flow):
1. Set up DNS: `<code>.<your-domain> -> node ip`
2. Sync users to this node (run on brain/control-plane where panels are allowlisted):
   - `python scripts/migrate_to_nodes.py --node <code>`

## Legacy note: extra PL inbound

On 7 March 2026 `pl` also has a second inbound:
- `id=2`
- port `8443`
- remark `PL Free Reality`

This extra inbound exists on the node, but it is not the primary control-plane source of truth for current user delivery. Treat it as a legacy/manual contour until it is explicitly brought back into the runtime DB and sync policy.
