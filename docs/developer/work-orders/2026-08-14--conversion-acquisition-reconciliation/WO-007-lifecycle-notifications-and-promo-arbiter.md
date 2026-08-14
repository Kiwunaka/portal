# WO-007 — Lifecycle Notifications And Promo Arbiter

Status: `COMPLETE`

## Outcome

Server/in-app, Android/Windows OS and Telegram deliver useful lifecycle and
incident information without duplicate noise; remote promo remains controllable
without an app update.

## Priority And Collision Policy

Highest wins for the same delivery window:

1. critical service/security incident affecting the user;
2. access/payment state: payment confirmed/failed, trial or paid expiry,
   recovery;
3. required product action/update;
4. onboarding/help based on an observed incomplete step;
5. operator-authored promo.

Lower priority waits. One logical notification has a durable dedupe key across
retries; each channel records scheduled/delivered/opened/dismissed/failed.
Channel fan-out is policy-driven, not three independent schedulers.

## Conservative Promo Defaults

- marketing opt-out applies to promo on all channels and does not suppress
  required access/security messages;
- Telegram promo only for users who interacted with the bot and did not opt
  out; no purchased lists or unsolicited users;
- quiet hours use the account/device timezone when known, otherwise Moscow
  fallback; lifecycle expiry may schedule for the next allowed window;
- no more than one promo campaign per user per 72 hours and no repeated
  impression of a dismissed campaign unless the campaign version changes;
- active incident/access warning suppresses promo; cross-channel repeat is
  avoided unless the campaign explicitly requires a secondary reminder after
  a bounded delay;
- admin preview shows audience, channels, priority, schedule, cap and exact
  sample before activation; kill switch stops future delivery.

## Acceptance

Trial 1-day-left/expiry, paid 3-day/1-day/expiry/recovery, payment status and
approved incident flows schedule/cancel from authoritative state. Android and
Windows preferences work; in-app inbox/card and current promo render safely;
Telegram copy is short and non-alarming. A state change cancels obsolete jobs.

## Checks

Clock-controlled scheduler tests, dedupe/retry/cancel/opt-out/quiet-hour tests,
channel adapter tests, safe promo payload tests, client local-notification tests,
admin preview E2E and one bounded production campaign dry-run before live proof.

## Current Evidence

- `PASS_LOCAL`: lifecycle timing is now access-aware: paid receives T-3/T-1/T0,
  trial and bonus receive only T-1/T0; IDs include access kind, stage and expiry
  date, so a read state cannot leak into a later entitlement.
- `PASS_LOCAL`: the in-app inbox no longer emits a permanent generic
  `Доступ активен` item; it shows a short actionable expiry card only inside an
  exact window.
- `PASS_LOCAL`: Telegram lifecycle/onboarding delivery respects 09:00–21:00 in
  the device timezone with Moscow fallback. Promo jobs yield to recent expiry
  messages and are capped by a shared `promo:` key; the old automatic 15%
  start-99 follow-up job is removed.
- `PASS_LOCAL`: app promo slots remain server-controlled, allowlisted,
  dismissible and previewable in admin without an APK update.
- `PASS`: final admin E2E, scheduler/channel regressions and current-origin
  readback passed. A live promo campaign was `NOT_REQUESTED`; the capability
  remains remotely configurable without enabling an unsolicited campaign.
