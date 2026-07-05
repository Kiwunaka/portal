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
  - non-default port is fine.
  - root password access is retained only as a break-glass path; keep fail2ban enabled and move to key-only when the owner approves it.
  - Paramiko scripts must use the shared host-key helper and reject unknown host keys by default.
  - `POKROV_SSH_TRUST_ON_FIRST_USE=1` is allowed only for deliberate first bootstrap or reviewed host-key rotation, then must be disabled again.
- Add fail2ban and UFW default-deny with explicit allow rules.
- Public brain exposure should be `80/tcp`, `443/tcp`, and the active SSH port only.
  - Caddy `:8444`, API `:8080`, legacy `:2096`, and panel ports must stay loopback or allowlisted.
- HAProxy TCP frontends should keep per-IP stick-table limits to absorb cheap connection bursts before Caddy/API.
- API abuse controls must use the backend rate-limit contract:
  - `429` response
  - `Retry-After` header
  - JSON detail with `code=rate_limited`, `scope`, and `retry_after_seconds`
  - durable DB buckets with in-memory fallback for dev/test
- Reverse-proxy IP headers are trusted only from loopback or `TRUSTED_PROXY_IPS`; direct clients must not be able to spoof `X-Forwarded-For` / `X-Real-IP`.
- Support attachments are private.
  - New uploads are served through authenticated `/api/tickets/attachments/{stored_name}`.
  - Allowed user upload types are PNG, JPEG, WebP, PDF, and UTF-8 TXT after magic-byte checks.
  - SVG, HTML, video, and opaque octet-stream user uploads are rejected.
- Web sessions should prefer `Secure; HttpOnly` cookie handoff.
  - Bearer/localStorage remains compatibility only for the current transition window.
- Payment callbacks must cap body size before parsing, rate-limit invalid signatures, and persist redacted payloads only.
- Client state JSON must not contain session tokens; Android/Windows session material belongs in the client secure secret store.
