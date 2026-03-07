# PL DNS Mitigation (2026-02-08)

> Historical snapshot: this document describes the February DNS incident and references `pl_free` as it existed then. For current production node roles and runtime truth, use `docs/36-node-source-of-truth-2026-03-07.md`.

## Incident

Users reported unstable Poland connectivity.

Live checks from control host showed:

- ports are open on `pl` (`443`, `8443`, `29374`);
- `pl` and `pl_free` inbounds are enabled and consistent (`dest/serverNames=www.orange.pl`);
- all worker DNS names (`pl/it/us`) shared the same IPv6 (`AAAA`) target.

Shared `AAAA` can route clients to the wrong endpoint when IPv6 is preferred.

## Runtime mitigation applied

Updated node hosts in brain DB to per-node IPv4 values (including `pl_free`) using:

```bash
python scripts/remote_brain_set_node_hosts_dns.py \
  --brain-ip 82.21.114.104 \
  --domain kiwunaka.space \
  --mode ip
```

Result (`nodes.host` on brain):

- `pl -> 82.40.38.84`
- `pl_free -> 82.40.38.84`
- `it -> 151.241.215.84`
- `us -> 82.21.92.142`
- `brain -> kiwunaka.space` (unchanged)

Subscription host check now returns IPv4 worker hosts:

- `82.40.38.84`
- `151.241.215.84`
- `82.21.92.142`
- `kiwunaka.space`

## Permanent fix

At DNS provider level:

1. Remove shared `AAAA` from `pl.kiwunaka.space`, `it.kiwunaka.space`, `us.kiwunaka.space`, or
2. assign unique IPv6 per corresponding node.

Then switch back to DNS hosts:

```bash
python scripts/remote_brain_set_node_hosts_dns.py \
  --brain-ip 82.21.114.104 \
  --domain kiwunaka.space \
  --mode dns
```

Recheck:

```bash
python scripts/audit_node_dns_matrix.py --domain kiwunaka.space --include-brain --out docs/audit-artifacts/dns_matrix_20260208.json
python scripts/audit_node_dns.py --domain kiwunaka.space --include-brain
python scripts/remote_inspect_brain_subscription_hosts.py --brain-ip 82.21.114.104 --domain kiwunaka.space
python scripts/verify_brain_ready.py --domain kiwunaka.space --brain-ip 82.21.114.104 --ssh-port 29374 --repeat 5
```

Done criteria for closure:

- `audit_node_dns.py` returns no `shared_aaaa_across_different_nodes`.
- `audit_node_dns_matrix.py` confirms the same across `system`, `1.1.1.1`, `8.8.8.8`, `9.9.9.9`.
- `verify_brain_ready.py --repeat 5` reports stable multi-host subscription responses.
- Manual smoke: `10/10` successful connects (`5 FREE + 5 PAID`).
