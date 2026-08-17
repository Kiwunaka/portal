# WO-004 — Compact Telegram Entry

Status: `COMPLETED_LOCAL_PENDING_PROD_READBACK`

The main bot is reduced to one state-aware action, login/link code, Android and
Windows downloads, activation, short help and one external cabinet route.
Devices, payment history, referrals, QR/manual URL, settings and achievements
remain in the app/cabinet. Current UI contains no Stars pricing.

Owned stable download redirects prevent stale hard-coded release links. The
post-deploy Browser readback must replace the old production menu captured in
WO-001 before the work order is marked exact production `PASS`.
