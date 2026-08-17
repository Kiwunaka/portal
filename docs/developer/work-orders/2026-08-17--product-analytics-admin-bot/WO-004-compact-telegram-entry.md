# WO-004 — Compact Telegram Entry

Status: `COMPLETED`

The main bot is reduced to one state-aware action, login/link code, Android and
Windows downloads, activation, short help and one external cabinet route.
Devices, payment history, referrals, QR/manual URL, settings and achievements
remain in the app/cabinet. Current UI contains no Stars pricing.

Owned stable download redirects prevent stale hard-coded release links.

Production Browser proof on 2026-08-17 sent `/start` to the owner's bot chat and
observed the compact returning-user menu: one primary device action, code login,
Help, code activation and one cabinet link. The new answer contains neither the
old `Мой доступ` nor `Ещё` panel. Help opens a short situation-first menu and
Back returns to the compact first level. Evidence
`evidence/35-telegram-production-compact-menu.png` captures the compact menu and
the tested Help state in one redacted-safe viewport.
