# Public Beta Scope

Status: draft

## Intended Scope

Open public beta for POKROV on production domains:

- marketing public entry
- public checkout when safe
- cabinet continuation
- activation-key redeem
- support ticket flow
- admin operator surface
- beta-labeled Android/Windows download states
- monitoring, rollback, emergency controls, and public communications

## Truthful Platform Availability

Android:

- Public state defaults to blocked/internal-only until production signing and physical release-build localhost/control-surface audit pass.
- If the audit/signing is missing, Android must be `coming soon`, `internal testing only`, or `blocked`.

Windows:

- Public state may be beta only if artifact metadata, checksum, download path, and unsigned/trust warning are truthful.
- Stable/public-approved wording is forbidden while unsigned.

Apple:

- Readiness only. No public Apple ship promise.

## Public Copy Rules

- Use POKROV as the public product line.
- Do not use `VPN` as direct public product meaning.
- No stable/SLA wording.
- No guaranteed worldwide availability.
- No public Apple promise.
- No fake counters, fake reviews, fake support, or pretend success.

## Release Decision States

- `blocked`
- `public-beta-ready`
- `public-beta-ready with accepted limitations`
- `deployed`
- `rollback-required`

