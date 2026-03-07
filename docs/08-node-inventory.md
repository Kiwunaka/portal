# Node Inventory

> Updated: 2026-03-07

This file tracks the current node list and their roles. Do not put secrets here (passwords, private keys, panel paths).

## Current Nodes

| Code | Role | Runtime status | Plan | IP |
|---|---|---|---|---|
| `brain` | Brain / control-plane | x-ui installed, but node disabled in current delivery DB | `v3-pico` (1 vCPU, 2 GB RAM) | `82.21.114.104` |
| `pl` | Worker | enabled for delivery | `v2-pico1` (1 vCPU, 1 GB RAM) | `82.40.38.84` |
| `it` | Worker | enabled for delivery | `v2-pico1` (1 vCPU, 1 GB RAM) | `151.241.215.84` |
| `us` | Worker | enabled for delivery | `v2-pico1` (1 vCPU, 1 GB RAM) | `82.21.92.142` |
| `nl` | Worker | enabled for delivery | `v3-pico` (1 vCPU, 1 GB RAM) | `82.24.195.93` |
| `free` | Worker (dedicated FREE pool) | enabled for delivery | `v2-pico` (1 vCPU, 1 GB RAM) | `151.245.217.23` |

## Ops Notes

- SSH port on new nodes: `29374`.
- Standard user traffic: `443/tcp` on worker nodes.
- 3x-ui panel port/path is randomized per node and restricted by UFW to brain IP only.
- Brain x-ui built-in subscription server must stay disabled (`subEnable=false`, `subPort=2097`) because portal owns `:2096`.
- Current standard delivery profile is `VLESS + TCP + Reality`.
- `pl` currently also has a legacy extra inbound `8443` (`PL Free Reality`); treat it as manual/legacy until it is reflected in runtime DB and sync docs.

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
