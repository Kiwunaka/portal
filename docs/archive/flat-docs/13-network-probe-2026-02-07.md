# Brain Network Probe (2026-02-07)

Script:

```bash
python scripts/remote_brain_network_probe.py
```

Result:

```json
{
  "pl": {
    "ip": "82.40.38.84",
    "port_443": "closed",
    "port_8443": "closed",
    "port_29374": "closed"
  },
  "it": {
    "ip": "151.241.215.84",
    "port_443": "open",
    "port_8443": "closed",
    "port_29374": "open"
  },
  "us": {
    "ip": "82.21.92.142",
    "port_443": "open",
    "port_8443": "closed",
    "port_29374": "open"
  }
}
```

Notes:
- From local workstation, PL ports were reachable on TCP (`443/8443/29374`), but SSH banner timed out.
- From brain, PL was unreachable on all tested ports.
- This currently blocks automated rollout to PL from brain (including Free limiter and panel sync paths).
