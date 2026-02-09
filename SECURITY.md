# Security Checklist (Mandatory)

## Immediate Actions (do now)

1. Rotate all exposed credentials that were previously stored in code or sample env files:
   - Telegram bot token
   - 3x-ui admin password(s)
   - SSH/root passwords or keys
2. Ensure `.env` files are not committed (see `.gitignore`).

## Repository Rules

- No secrets in `*.py`, `*.md`, `*.html`.
- Deployment scripts must read credentials from environment variables (or a local untracked `.env`).

## Recommended Server Posture

- 3x-ui panel must not be publicly accessible.
  - Bind to localhost or protect by firewall allowlist to the control-plane IP.
- SSH:
  - non-default port is fine, but use key-based auth and disable password auth when possible.
- Add fail2ban and UFW default-deny with explicit allow rules.

