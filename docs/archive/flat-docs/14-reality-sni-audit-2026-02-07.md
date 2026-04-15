# Reality/SNI Audit (2026-02-07)

Superseded by `docs/15-reality-sni-dns-audit-2026-02-08.md` (full audit across `brain/pl/it/us` and free inbound `pl:8443`).

Command used for reachable nodes:

```bash
python scripts/inspect_reality_inbound_remote.py --only it,us --ssh-port 29374
```

Summary:
- `it`: `dest=www.cloudflare.com:443`, `server_names=["www.cloudflare.com"]`, inbound `443` enabled.
- `us`: `dest=www.cloudflare.com:443`, `server_names=["www.cloudflare.com"]`, inbound `443` enabled.

PL status:
- `python scripts/inspect_reality_inbound_remote.py --only pl --ssh-port 29374` failed with SSH banner/session error.
- This node is currently not auditable from the current management path and needs SSH reachability fix first.

DNS leak checks:
- Pending for all nodes in this pass; full DNS leak audit requires a client-side egress test path per node profile.
