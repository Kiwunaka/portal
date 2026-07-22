# Telegram Bot Profile Growth

Last updated: 2026-07-22

This runbook keeps `@pokrov_vpnbot` ready for Telegram's native `Similar bots` surface without gray automation.

## Current Goal

Make the main bot profile clear enough for users and consistent enough for Telegram-side clustering:

- bot: `@pokrov_vpnbot`
- profile name: `POKROV VPN`
- short description: `POKROV VPN для Android и Windows. 5 дней без карты.`
- profile description:

```text
POKROV VPN (ВПН) для Android и Windows.

5 дней бесплатно без карты. Установите приложение, войдите в аккаунт и нажмите «Подключить».

Поддержка: @pokrov_supportbot
Отзывы: @pokrov_feedbackbot
Новости: @pokrov_vpn
```

The source of truth for this copy, public commands, and the WebApp menu button is `portal_bot/telegram_profile.py`.

## What Telegram Controls

Telegram's `Similar channels and bots` surface is automatic. The official API note says similar public channels and bots are selected by similarities in subscriber bases.

For bots, Telegram clients can request recommendations with MTProto method `bots.getBotRecommendations`, but that method is user-only. Bot-token Bot API cannot call it, force inclusion, or query the native profile row.

Operational rule:

- do not build fake user-session automation to manipulate recommendations
- do not treat absence of `Similar bots` as a deploy failure
- do improve profile clarity, user growth, and overlap with the intended RU VPN audience

Official references:

- [Similar channels and bots](https://core.telegram.org/api/recommend)
- [`bots.getBotRecommendations`](https://core.telegram.org/method/bots.getBotRecommendations)
- [Telegram Mini Apps profile launch button](https://core.telegram.org/bots/webapps)
- [Bot API profile and menu methods](https://core.telegram.org/bots/api)
- [Bot API changelog](https://core.telegram.org/bots/api-changelog)
- [Rich-message guide](https://core.telegram.org/bots/features#rich-messages)

## Current Bot UX Contract

The candidate runtime targets `aiogram >=3.30,<4` and the current Bot API rich
message surface. Capability use remains progressive rather than mandatory:

- `/help` and the durable Stars success receipt prefer `InputRichMessage` and
  fall back to equivalent HTML when the installed Telegram runtime is older or
  rejects a rich payload.
- Primary, success, and danger button styles are used only when the runtime
  exposes them. Custom button emoji require operator-provided
  `TG_BTN_EMOJI_*_ID` values; the bot never invents an emoji ID.
- `copy_text` is preferred for the real subscription link. Older runtimes keep
  the existing callback fallback, so a client update is not required to copy a
  link.
- Context cleanup applies only to transient navigation messages. Payment
  receipts and other retained facts are explicitly preserved.
- A connection QR is a separate transient message with its own timer and
  `qr_close` action. Closing it deletes only that QR and does not erase the
  source link or the surrounding instructions.
- The main CTA is derived from current account/access state. Happ remains the
  recommended manual client path; stale Karing guidance must not reappear.

## Check And Apply

Read-only profile drift check:

```powershell
python scripts/brain_telegram_bot_profile_check.py --brain-ip 82.21.114.104
```

Apply the expected profile, commands, and WebApp menu button:

```powershell
python scripts/brain_telegram_bot_profile_check.py --brain-ip 82.21.114.104 --apply
```

Write a redacted report:

```powershell
python scripts/brain_telegram_bot_profile_check.py --brain-ip 82.21.114.104 --output docs/audit-artifacts/telegram-bot-profile-check.json
```

The checker reads `BOT_TOKEN` from the live `portal-bot` process on brain and never writes the token into stdout or JSON.

The bot runtime still configures public commands and the chat menu button on startup. It does not apply profile name, short description, or description on startup, so manual BotFather experiments are not overwritten by a restart.

## Weekly Similar Bots Snapshot

Every week, manually record the native Telegram profile state:

1. Open `@pokrov_vpnbot` in Telegram.
2. Record `monthly users`.
3. Record whether the `Similar bots` row is present.
4. If present, record the count and the first visible neighbors.
5. Save a screenshot path in the report.

Example report command with manual fields:

```powershell
python scripts/brain_telegram_bot_profile_check.py --brain-ip 82.21.114.104 --similar-bots-present absent --similar-bots-count 0 --similar-bots-screenshot docs/audit-artifacts/telegram-similar-bots/2026-07-08.png
```

When the row appears:

```powershell
python scripts/brain_telegram_bot_profile_check.py --brain-ip 82.21.114.104 --similar-bots-present present --similar-bots-count 19 --similar-bots-neighbor "КОСМИЧЕСКИЙ VPN" --similar-bots-neighbor "ГРОЗА VPN"
```

`telegram_similar_bots_manual` is always reported as `MANUAL_OWNER_TEST`. It is evidence, not an automated local pass.

## BotFather Checklist

Keep these manual settings aligned for `@pokrov_vpnbot`:

- profile photo/logo is current POKROV artwork
- name is `POKROV VPN`
- about/short description matches `portal_bot/telegram_profile.py`
- description matches `portal_bot/telegram_profile.py`
- Main Mini App opens `https://app.pokrov.space/`
- Mini App profile media/screenshots show the real Android/Windows app flow
- allowed URLs include `https://pokrov.space/` and `https://app.pokrov.space/`
- Telegram OAuth/Web Login origins match deployment docs

Backlog trust track:

- verified organization may help trust, but it is a separate Telegram/business process
- do not promise a date for organization verification

## Analytics

The main bot records `bot_entry_opened` for:

- `/start`
- `/cabinet`
- `/help`
- `/support`

`/start` metadata is coarse only:

- `start_arg_present`
- `start_arg_kind`: `plain`, `referral`, `promo`, `campaign`, `campaign_promo`, `friend_gift`, `opening_bonus`, `app_link`, `payment`, or `other`
- `created_new`

Raw `start` payloads are not written to the event metadata.
