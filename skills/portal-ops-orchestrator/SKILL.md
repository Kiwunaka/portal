---
name: portal-ops-orchestrator
description: Orchestrate recurring Portal operations across support, network, and backend flows. Use for incident triage (PL/IT/US node health), support ticket workflow checks, broadcast/admin sanity, and post-change verification with scripts in scripts/ and docs/audit-artifacts.
---

# Portal Ops Orchestrator

## Runbook

1. Run network checks:
- `python scripts/remote_brain_network_probe.py`
- `python scripts/inspect_reality_inbound_remote.py --only pl,it,us --ssh-port 29374 --inbound-id 1`
- `python scripts/audit_node_dns.py --domain kiwunaka.space --include-brain --out docs/audit-artifacts/dns_audit_<date>.json`

If DNS has shared `AAAA` and users report country instability, apply temporary IPv4 host mitigation:

- `python scripts/remote_brain_set_node_hosts_dns.py --brain-ip <brain_ip> --domain kiwunaka.space --mode ip`

2. Run control-plane consistency checks:
- `python scripts/remote_brain_nodes_sanity.py --brain-ip <brain_ip>`
- `python scripts/remote_inspect_brain_subscription_hosts.py --brain-ip <brain_ip> --domain kiwunaka.space`

3. Validate support flow:
- Ensure `portal_bot/helpbot.py` and `portal_bot/bot.py` ticket labels are in Russian.
- Confirm admin queue is available via callback `admin_tickets`.

4. Validate admin direct messaging:
- In user card, verify button `✉️ Сообщение` exists and callback `adm_msg_user_<tg_id>` is wired.

5. Save artifacts and document:
- Write/update docs under `docs/` and `docs/audit-artifacts/`.
- Include concrete command outputs and date.
