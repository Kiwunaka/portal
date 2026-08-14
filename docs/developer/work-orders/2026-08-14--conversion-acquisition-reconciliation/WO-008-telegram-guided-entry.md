# WO-008 — Telegram Guided Entry

Status: `COMPLETE`

## Outcome

Первый экран бота отвечает на вопрос «что мне делать сейчас», а не показывает
панель из всех возможностей.

## Exact Baseline

Current Browser audit on 2026-08-14:

- returning start: explanatory card plus eight buttons;
- help: explanatory card plus six buttons;
- Android branch: correct concise steps and three exact release variants;
- no payment, message-send or account mutation was used during audit.

## Target Hierarchy

For a new user: direct `Android` and `Windows` actions first, then `Тарифы` and
one short `Как проверить POKROV` explanation. Price/trial is shown once;
cabinet, diagnostics, referrals and support do not become a first-screen panel.

For a returning user: choose the primary action from state (`Продлить`,
`Подключить устройство` or `Открыть кабинет`), show at most two secondary
actions, move diagnostics, low speed, codes, referral and settings under
`Помощь`/`Ещё`.

## Acceptance

- no first-level grid of six/eight equal buttons;
- Android/Windows direct downloads remain before ToS and use WO-003 catalog;
- iOS/macOS clearly say no native POKROV app and offer only approved compatible
  manual path; they never look like public native releases;
- `/start`, returning, referral, campaign, pay and app-link payloads preserve
  correct intent and WO-004 attribution;
- help offers one recommended next step before human support;
- Telegram promo/lifecycle messages follow WO-007 and never masquerade as
  personal support;
- Browser current-run screenshots verify new and returning surfaces.

## Checks

Focused handler/menu tests, exact callback/deep-link tests, public binary guard,
bot smoke and Browser audit in authorized Telegram Web. Do not create an order
or send free text during visual verification.

## Current Evidence

- `PASS_LOCAL`: new-user keyboard is exactly Android, Windows, Tariffs and one
  short verification explanation; the old free-offer/features panel is gone.
- `PASS_LOCAL`: returning keyboard contains one state-aware primary action plus
  `Мой доступ`, `Помощь` and `Ещё`; Android keeps ARM64 primary and alternatives
  secondary.
- `PASS_LOCAL`: focused rich-message, menu and callback tests pass.
- `PASS`: production Browser proof shows the four-action returning menu,
  Android/Windows-only picker, split APK and Windows links, and an active user
  reaching access status without a duplicate paywall.
