# Reality/SNI + DNS Audit (2026-02-08)

Scope:
- Nodes: `brain`, `pl`, `it`, `us`
- Inbounds checked: `id=1` on all nodes (`:443`), plus `id=2` on `pl` (`:8443`, free inbound)

Commands used:

```bash
python scripts/inspect_nodes_inbounds.py --only brain,pl,it,us --ssh-port 29374 --out docs/audit-artifacts/node_inbounds_all_20260208.json
python scripts/inspect_reality_inbound_remote.py --only brain,pl,it,us --ssh-port 29374 --inbound-id 1 > docs/audit-artifacts/reality_inbound1_20260208_post_apply.json
python scripts/inspect_reality_inbound_remote.py --only brain,pl,it,us --ssh-port 29374 --inbound-id 2 > docs/audit-artifacts/reality_inbound2_20260208_post_apply.json
```

## Current Reality state

- `brain` inbound `1` (`443`): `dest=www.telekom.de:443`, `serverNames=["www.telekom.de"]`
- `pl` inbound `1` (`443`): `dest=www.orange.pl:443`, `serverNames=["www.orange.pl"]`
- `pl` inbound `2` (`8443`, free): `dest=www.orange.pl:443`, `serverNames=["www.orange.pl"]`
- `it` inbound `1` (`443`): `dest=www.tim.it:443`, `serverNames=["www.tim.it"]`
- `us` inbound `1` (`443`): `dest=www.microsoft.com:443`, `serverNames=["www.microsoft.com"]`

All checked inbounds are `protocol=vless`, `network=tcp`, `security=reality`, `enable=true`.

## DNS baseline on nodes

All nodes use `systemd-resolved` stub (`127.0.0.53`) with uplink resolvers:
- `8.8.8.8`
- `8.8.4.4`

## Country profile probe (live TLS from each node)

Probe artifact: `docs/audit-artifacts/sni_probe_20260208.json`

Result summary:
- `brain` candidates OK: `www.telekom.de`, `www.spiegel.de`, `www.zdf.de`, `www.cloudflare.com`
- `pl` candidates OK: `www.orange.pl`, `www.wp.pl`, `www.onet.pl`, `www.cloudflare.com`; failed: `www.allegro.pl` (timeout)
- `it` candidates OK: `www.tim.it`, `www.repubblica.it`, `www.rai.it`, `www.enel.it`, `www.cloudflare.com`
- `us` candidates OK: `www.microsoft.com`, `www.amazon.com`, `www.apple.com`, `www.cloudflare.com`

## Applied country profile (approved)

- `brain` (DE):
  - primary: `www.telekom.de:443`
  - fallback: `www.spiegel.de:443`
- `pl` (PL):
  - primary: `www.orange.pl:443`
  - fallback: `www.wp.pl:443`
- `it` (IT):
  - primary: `www.tim.it:443`
  - fallback: `www.repubblica.it:443`
- `us` (US):
  - primary: `www.microsoft.com:443`
  - fallback: `www.amazon.com:443`

Global fallback (if country profile fails): `www.cloudflare.com:443`.

## Free 50 Mbps per-user rollout status

Applied on `pl` free inbound `:8443` as per-IP limiter (closest practical model to per-user on stock xray/3x-ui):

```bash
python scripts/remote_install_free_per_ip_limiter.py --code pl --ssh-port 29374 --port 8443 --rate-kbps 6250 --burst-kb 512
```

Verification artifact: `docs/audit-artifacts/free_limiter_status_20260208.txt`

Observed state:
- `portal-free-per-ip-limiter.service`: `enabled`, `active (exited)`
- nft table `inet portal_free_rate` present with rules:
  - `input tcp dport 8443 ... limit rate over 6250 kbytes/second ... drop`
  - `output tcp sport 8443 ... limit rate over 6250 kbytes/second ... drop`

Notes:
- This is per source IP, not strict per account UUID.
- With `FREE_LIMIT_IP=2`, one free account can use up to 2 parallel source IPs.
