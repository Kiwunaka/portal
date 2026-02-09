# PL Incident Postmortem (2026-02-08)

## Summary

Poland connectivity degraded because worker DNS hosts (`pl/it/us`) shared one `AAAA` record.  
When clients preferred IPv6, traffic could land on the wrong worker.

## Impact

- Free users on PL were affected first.
- Paid profiles with multi-country subscriptions also observed intermittent failures.
- Incident was amplified by client-side IPv6 preference and resolver variance.

## Timeline

1. Incident detected from connection failures and support tickets.
2. Runtime mitigation applied: forced worker `nodes.host` to IPv4 (`--mode ip`).
3. Added DNS matrix audit script for multi-resolver verification.
4. Defined closure steps to restore `--mode dns` only after provider-side `AAAA` correction.

## Root Cause

- DNS provider had shared `AAAA` target across different worker FQDNs.
- Control-plane initially trusted DNS hostnames for all workers.

## Corrective Actions

1. Added `scripts/audit_node_dns_matrix.py` to verify DNS consistency across:
   - system resolver
   - `1.1.1.1`
   - `8.8.8.8`
   - `9.9.9.9`
2. Updated runbook `docs/19-pl-dns-mitigation-2026-02-08.md` with strict closure gates.
3. Kept safe fallback procedure:
   - temporary `--mode ip`,
   - return to `--mode dns` only after clean audit.

## Preventive Measures

- Include DNS matrix audit in every node/domain rollout.
- Do not consider single-resolver check sufficient for closure.
- Keep support runbooks aligned with network diagnostics artifacts.
