# Node Inventory

> Updated: 2026-02-14

This file tracks the current node list and their roles. Do not put secrets here (passwords, private keys, panel paths).

## Current Nodes

| Code | Role | Plan | IP |
|---|---|---|---|
| `brain` | Brain / control-plane candidate | `v3-pico` (1 vCPU, 2 GB RAM) | `82.21.114.104` |
| `pl` | Worker | `v2-pico1` (1 vCPU, 1 GB RAM) | `82.40.38.84` |
| `it` | Worker | `v2-pico1` (1 vCPU, 1 GB RAM) | `151.241.215.84` |
| `us` | Worker | `v2-pico1` (1 vCPU, 1 GB RAM) | `82.21.92.142` |
| `nl` | Worker (premium pool) | `v3-pico` (1 vCPU, 1 GB RAM) | `82.24.195.93` |
| `free` | Worker (dedicated FREE pool) | `v2-pico` (1 vCPU, 1 GB RAM) | `151.245.217.23` |

## Ops Notes

- SSH port on new nodes: `29374`.
- User traffic: `443/tcp` on worker nodes.
- 3x-ui panel port/path is randomized per node and restricted by UFW to brain IP only.

## Checklist

1. Create DNS A-records (recommended):
   - `pl.kiwunaka.space -> 82.40.38.84`
   - `it.kiwunaka.space -> 151.241.215.84`
   - `us.kiwunaka.space -> 82.21.92.142`
   - `nl.kiwunaka.space -> 82.24.195.93`
   - `free.kiwunaka.space -> 151.245.217.23`
   - Cutover root domain to brain when ready: `kiwunaka.space -> 82.21.114.104`
   - (Optional) `de.kiwunaka.space -> 82.21.114.104` (alias for Germany)
2. Ensure each worker has a VLESS Reality inbound on port `443`.
3. Seed the control-plane `nodes` table and sync users to all nodes.
