# Copy And UX Consilium Audit

Date: 2026-06-09

Scope: post-polish review of bot, web cabinet, admin, marketing site, and client app copy / information architecture.

Models used through OpenCode Go:

- `opencode-go/qwen3.7-max`
- `opencode-go/mimo-v2.5-pro`
- `opencode-go/deepseek-v4-pro`
- `opencode-go/minimax-m3`
- `opencode-go/glm-5.1`

The models were used as reviewers, not product authority. Final synthesis below resolves their feedback against POKROV canon and the current repo state.

## Verdict

The recent pass moved the product in the right direction: fake "soon" states are mostly gone, WARP is no longer exposed as a dead CTA, cabinet entry is clearer, and the marketing hero is more product-like. The remaining quality gap is not one big missing feature; it is a layer of language and hierarchy that still feels too technical, too bot-like, or too repetitive.

The strongest consensus:

- remove Telegram-casino visual noise from bot/worker copy;
- remove engineering terms from user-facing client/web copy;
- stop repeating the 5-day trial several times above the fold;
- make each surface expose one obvious action at a time;
- keep fallback/advanced paths deep, not on the first layer.

## Top Issues Still Left

1. Bot and worker still feel too emoji-heavy.
   Verified examples: `portal_bot/worker.py` still has `⌛`, `⚡`, `📅`, `🚨`, and `🟦` CTA prefixes. This clashes with the desired calm premium utility tone.

2. `RETENTION_BUTTONS` is defined twice.
   Verified in `portal_bot/worker.py`. The second definition overwrites the first, with slightly different wording. This is both copy drift and a small maintainability bug.

3. User-facing tech terms remain.
   The models repeatedly flagged `пресет`, `маршруты`, `checkout`, `расчёт`, `T-1/T-3/T0`, `роллаут`, and ambiguous routing labels as cheap or internal.

4. Marketing repeats the same trial message too many times above the fold.
   On mobile, `5 дней` appears in the kicker/body/CTA/chips. The structure is stable, but the message feels pushy and less premium.

5. The H1 "POKROV для YouTube, TikTok и нужных вам сайтов" works, but "нужных вам сайтов" feels generic.
   Suggested direction: keep YouTube/TikTok specificity, replace the tail with a more concrete promise or shorten the H1.

6. Cabinet entry still gives email too much visual weight when email is unavailable.
   The yellow note is honest, but it competes with the primary Telegram login.

7. Dashboard status copy is vague.
   `Нужна скорость` and `Лимит обновится после следующего расчета` do not immediately tell the user what happened or what to do.

8. App routing labels are still mentally expensive.
   `Все, кроме РФ`, `Российский регион`, `Маршруты Windows`, `Выбранные приложения/процессы`, and `Все устройство` make users reason about implementation instead of outcome.

9. Fallback clients should stay deep.
   Karing/Happ/manual-link copy is useful as a recovery path, but showing it early makes POKROV feel fragile.

10. Gamification should not be primary.
   Wheel/calendar/achievements can exist in Rewards, but the models agreed they should not appear as first-layer navigation or onboarding claims.

## Surface-Specific Decisions

### Bot

Keep:

- short Telegram-friendly flows;
- `Оставить отзыв`;
- numeric ratings;
- direct payment/access actions.

Fix next:

- remove `🟦` from CTA labels;
- remove emoji prefixes from retention messages unless they are essential status marks;
- rename `Я запутался` to a less self-blaming action, preferably `Помощь` or `Не подключается`;
- reduce `Полный доступ` in user copy where `Продлить`, `Платный срок`, or `Все страны` is clearer;
- hide Karing/Happ/manual-link instructions behind fallback help.

### Web Cabinet

Keep:

- Telegram as the primary entry path while email is not fully public-ready;
- compact mobile login card;
- honest email readiness.

Fix next:

- demote the yellow email note on entry;
- replace `Нужна скорость` with `Скорость ограничена` or a more exact state;
- replace `после следующего расчета` with `после обновления лимита` or a concrete date when available;
- shorten nav subtitles like `Продление, коды и установка`.

### Admin

Keep:

- operator density;
- release/evidence detail where it is genuinely operator-facing;
- mobile auth fallback screen.

Fix next:

- remove or reduce `пресет`, `роллаут`, and similar jargon from visible admin text;
- on expired session screen, make `Войти` the only strong action;
- hide low-priority service fields on mobile admin cards.

### Marketing Site

Keep:

- direct app-first CTA;
- Android/Windows beta honesty;
- visible 5-day no-card offer.

Fix next:

- one primary CTA above the fold, not duplicated;
- reduce repeated `5 дней` mentions in the hero;
- replace "нужных вам сайтов" with a more concrete phrase or shorter headline;
- avoid "beta-касса", "beta-контур", or other beta-as-excuse phrasing;
- change defensive copy like "публичная страница не выдает случайные файлы" into user action copy.

### Client App

Keep:

- one central connect action;
- WARP hidden unless backend/runtime offers it;
- selected app/process capability;
- Telegram bonus and access status visible.

Fix next:

- choose one public label for WARP/advanced protection, preferably `Расширенная защита`;
- keep `WARP` as technical detail inside help/diagnostics;
- replace `Все устройство` with `Весь трафик устройства`;
- replace `Выбранные приложения/процессы` with `Только выбранные приложения` on first layer;
- replace `Маршруты Windows` with a result-oriented title;
- remove `пресет` from user-facing text;
- split "country/server choice" from "what opens directly" so `Все, кроме РФ` does not fight `Российский регион`.

## Copy Replacement Candidates

| Current | Candidate |
| --- | --- |
| `🟦 Продлить сейчас` | `Продлить` |
| `⌛ До окончания доступа осталось около 3 дней` | `До конца доступа - 3 дня` |
| `⚡ T-1: срок доступа заканчивается` | `Завтра доступ закончится` |
| `Я запутался` | `Помощь` / `Не подключается` |
| `Полный доступ закончился` | `Платный срок закончился` |
| `Нужна скорость` | `Скорость ограничена` |
| `после следующего расчета` | `после обновления лимита` |
| `Email: Недоступен, пока доставка писем не прошла проверку` | `Email-вход временно недоступен` |
| `Маршруты Windows` | `Что идет через POKROV` |
| `Все устройство` | `Весь трафик устройства` |
| `Выбранные приложения/процессы` | `Только выбранные приложения` |
| `пресет пройдет проверку` | `настройка пройдет проверку` |
| `POKROV для YouTube, TikTok и нужных вам сайтов` | `POKROV открывает YouTube, TikTok и другие сервисы` |
| `Бета-сборки открываются через кабинет` | `Файлы установки - в кабинете` |

## Final Quality Gate

Before the next public/user-test build:

1. No user-facing `пресет`, `маршруты`, `T-1`, `T-3`, `T0`, `checkout`, or `роллаут`.
2. No `🟦` CTA prefixes in bot/worker copy.
3. `RETENTION_BUTTONS` exists once.
4. Marketing hero has one primary CTA and no repeated trial claim spam.
5. Cabinet entry has one dominant action: Telegram login.
6. Dashboard status tells the user what happened and what to do next.
7. WARP/advanced protection has one public name and is hidden when not runtime-ready.
8. Fallback clients and manual links live in help/recovery, not primary onboarding.
