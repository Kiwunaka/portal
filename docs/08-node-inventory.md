# Node Inventory

> Updated: 2026-03-07

This file tracks the current node list and their roles. Do not put secrets here (passwords, private keys, panel paths).

## Current Nodes

| Code | Physical name | Country | Role | Runtime status | Plan | IP |
|---|---|---|---|---|---|---|
| `brain` | `BRAINnode` | `DE` | Brain / control-plane | x-ui installed, but node disabled in current delivery DB | `2 vCPU / 4 GB RAM / 60 GB NVMe` | `82.21.114.104` |
| `pl` | `PLnode` | `PL` | Premium delivery | enabled for delivery | `1 vCPU / 2 GB RAM / 40 GB NVMe` | `82.40.38.84` |
| `it` | `ITnode` | `IT` | Premium delivery | enabled for delivery | `1 vCPU / 2 GB RAM / 40 GB NVMe` | `151.241.215.84` |
| `us` | `USnode` | `US` | Premium delivery | enabled for delivery | `1 vCPU / 2 GB RAM / 40 GB NVMe` | `82.21.92.142` |
| `nl` | `NLnode` | `NL` | Premium delivery | enabled for delivery | `1 vCPU / 2 GB RAM / 40 GB NVMe` | `82.24.195.93` |
| `free` | `FREENLnode` | `NL` | Dedicated free pool | enabled for delivery | `1 vCPU / 1 GB RAM / 40 GB NVMe` | `151.245.217.23` |

## Ops Notes

- SSH port on new nodes: `29374`.
- Standard user traffic: `443/tcp` on worker nodes.
- 3x-ui panel port/path is randomized per node and restricted by UFW to brain IP only.
- Brain x-ui built-in subscription server must stay disabled (`subEnable=false`, `subPort=2097`) because portal owns `:2096`.
- Current standard delivery profile is `VLESS + TCP + Reality`.
- Current runtime free contour is the dedicated node code `free`. Physically this is the separate NL-based server `FREENLnode`, but in runtime and subscription logic it remains a standalone free pool.
- `pl:8443` (`PL Free Reality`) was retired on 2026-03-07: inbound `id=2` is disabled and UFW exposure for `8443/tcp` was removed. Keep it only as a disabled legacy row until final deletion.

## Checklist

1. Create DNS A-records:
   - `pl.kiwunaka.space -> 82.40.38.84`
   - `it.kiwunaka.space -> 151.241.215.84`
   - `us.kiwunaka.space -> 82.21.92.142`
   - `nl.kiwunaka.space -> 82.24.195.93`
   - `free.kiwunaka.space -> 151.245.217.23`
   - `kiwunaka.space -> 82.21.114.104`
2. Ensure each enabled delivery worker has a VLESS Reality inbound on port `443`.
3. Seed the control-plane runtime DB and sync users to enabled nodes.
