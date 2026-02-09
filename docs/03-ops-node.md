# Ops: Node (Country Server)

Each node is an independent server in a specific country:
- runs 3x-ui + xray
- exposes user traffic on `:443`
- exposes panel only to control-plane IP (recommended)

## Bootstrap

Run on the new node (manual):

```bash
CONTROL_PLANE_IP=<your control plane public ip> bash infra/bootstrap_node.sh
```

Or run from your local machine via SSH (recommended for batches):

```bash
python scripts/remote_bootstrap_nodes.py --add-pubkeys
```

After bootstrap:
1. (Optional) Move SSH to `29374`:
   - `python scripts/configure_ssh_additional_port.py --only brain,pl,it,us --add-port 29374`
2. Create a standard VLESS Reality inbound on each worker node:
   - `python scripts/create_reality_inbounds.py --only pl,it,us`
3. Seed the `nodes` table from generated facts:
   - `DATABASE_URL=sqlite:///portal.db.cluster.db python scripts/seed_nodes_from_facts.py`

## Standard Inbound Settings (Workers)

Created by `scripts/create_reality_inbounds.py`:
- Port: `443/tcp`
- Protocol: `vless`
- Transport: `tcp`
- TLS security: `reality`
- Flow: `xtls-rprx-vision` (client link includes `flow=...`)
- uTLS fingerprint (client): `firefox` (configurable in DB per node)
- Reality:
  - `dest`: `www.cloudflare.com:443`
  - `serverNames`: `["www.cloudflare.com"]`
  - `shortIds`: 1 random 8-byte hex id (stored as `reality_sid` in control-plane DB)
  - `privateKey`: generated per-node (never leaves the node); control-plane stores only the derived `publicKey` (`reality_pbk`)
- Sniffing: enabled, `destOverride=["http","tls","quic"]`

Then (production flow):
1. Set up DNS: `<code>.<your-domain> -> node ip`
2. Sync users to this node (run on brain/control-plane where panels are allowlisted):
   - `python scripts/migrate_to_nodes.py --node <code>`
