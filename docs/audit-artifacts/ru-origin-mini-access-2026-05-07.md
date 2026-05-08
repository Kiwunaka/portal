# RU-Origin Mini Access Check

Generated: 2026-05-07 19:25 MSK

## Verdict

RU-origin refresh remains `BLOCKED_BY_ACCESS`.

## Evidence

- `ssh_alias_mini` -> `BLOCKED_BY_ACCESS`: ssh could not resolve hostname `mini`.
- `ssh_direct_root_22` -> `BLOCKED_BY_ACCESS`: root@176.123.166.119: Permission denied (publickey,password).
- `ssh_direct_root_29374` -> `BLOCKED_BY_ACCESS`: kex_exchange_identification: read: Connection reset Connection reset by 176.123.166.119 port 29374
- `node_access_mini` -> `BLOCKED_BY_ACCESS`: RuntimeError: SSH auth failed for node mini: Authentication failed.

## Classification

- RU-origin host reachability/auth: `BLOCKED_BY_ACCESS`.
- No private key, password, or known-host material was recorded in this artifact.
