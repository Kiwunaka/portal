# Support Helpbot Intake (2026-02-08)

## Goal

Enable a dedicated support bot (`@portal_privacy_helpbot`) that accepts user messages
and writes them into the same ticket queue used by the main bot admin workflow.

## What was deployed

- New process entrypoint: `portal_bot/helpbot.py`
  - uses `HELP_BOT_TOKEN`
  - stores ticket messages in shared DB (`support_tickets`, `support_ticket_messages`)
  - notifies operator (`ADMIN_ID`) about new ticket activity
- New env variable in template: `portal_bot/.env.example`
  - `HELP_BOT_TOKEN=`
- New systemd unit on brain:
  - `/etc/systemd/system/portal-helpbot.service`
  - `ExecStart=/root/portal_bot/venv/bin/python /root/portal_bot/helpbot.py`

## Runtime status

On brain (`2026-02-08`):

- `systemctl is-active portal-helpbot` -> `active`
- `systemctl is-enabled portal-helpbot` -> `enabled`
- journal confirms polling:
  - bot: `@portal_privacy_helpbot`

## Operational notes

- User intake can happen in `@portal_privacy_helpbot`.
- Operator can continue replying from the main bot admin ticket queue (shared DB).
- Secrets are stored only in `/root/portal_bot/.env` (`HELP_BOT_TOKEN`), not in repo.
