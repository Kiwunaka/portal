# WO-003 — Telegram Delivery Reasons

Status: `COMPLETED`

One frozen recipient plan now produces durable bounded attempt rows. The admin
aggregate exposes sent/failed totals, safe reason categories, timings,
freshness and retryability without recipient IDs or raw Telegram text.

Terminal reasons include blocked, chat-not-found and deactivated. Only explicit
Telegram 429 is automatically retryable. 5xx and uncertain delivery stay
non-retryable because a blind resend could duplicate a successful message.
Failed-only retry excludes every confirmed or uncertain recipient.
