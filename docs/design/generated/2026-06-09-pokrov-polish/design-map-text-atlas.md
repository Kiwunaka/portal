# POKROV Design Map Text Atlas

Date: 2026-06-09

This file describes the generated visual maps in words for reviewers/models that cannot inspect images. The maps are internal references, not final UI specs. Text inside generated images is not canonical; use the descriptions below.

## Global Visual Direction Across All Maps

The desired POKROV style is a calm premium utility product, not a flashy VPN toy and not a corporate admin dump. The shared visual grammar:

- white / off-white canvas with very soft ivory and mint sections;
- deep green as the main action color;
- charcoal text, muted gray secondary text;
- subtle line icons, no emoji-like icons;
- rounded but not childish surfaces;
- cards only where they frame a real object or action, not endless nested explanation panels;
- iOS Settings-like rows for account/settings/support;
- one obvious primary action per surface;
- short first-layer copy, with longer explanation only in sheets, support articles, or help rows;
- motion should feel quiet and tactile: press scale, row highlight, status crossfade, connect ring sweep, skeletons without layout shift.

Reject all generated-image microcopy if it conflicts with repo canon or release truth. Reject fake flags/city names where they imply unverified node facts. Reject English labels if the surface is Russian-first.

## Map 1: Client App Map

File:

`C:\Users\kiwun\Documents\ai\VPN\docs\design\generated\2026-06-09-pokrov-polish\client-app-map.png`

Purpose:

This map is about the Android/Windows client shape: one-tap connection, trial visibility, WARP placement, locations, rules, account, support chat, and motion tokens.

### Overall Layout

The image is a large white design board with the POKROV mark and wordmark at top left. It is split into five numbered product zones across the top/middle, then a motion/philosophy strip at the bottom.

The board shows both mobile screens and Windows desktop variants. The design language is mostly white with mint-green active states, deep green controls, light gray dividers, and rounded cards.

### Zone 1: Main Screen

The mobile home screen has:

- a compact top bar with menu icon, centered POKROV wordmark/logo, and notification icon;
- a small trial row near the top: `Пробный период: 5 дней`;
- a green Telegram bonus banner: `Telegram +10 дней`, with a short subtitle and action;
- a large central circular connect button with the POKROV mark/lightning-like icon in the center;
- a visible status just below the ring (`Отключено` in the generated example);
- small chips below: current IP and region/location;
- a WARP/advanced privacy row at the bottom as a real toggle/card, not a disabled “soon” CTA;
- bottom nav with four items: Home/Location/Rules/Account.

What to keep:

- the main screen must make the connect button unmistakable;
- trial days and Telegram bonus must be visible before the user hunts in Account;
- WARP belongs on the main screen only if it is testable and honest;
- IP/current state can be a small chip, not a huge diagnostics block.

What to reject/fix:

- the generated map includes country flags and fake city-like rows in locations; do not use flags as the core UX;
- generated examples show a location chip like Moscow/RF; only show real data from backend/runtime;
- avoid too many small chips around the connect button if they reduce clarity.

### Zone 2: Locations

The mobile Locations screen shows:

- title `Локации`;
- search field;
- filter chips: all/premium/free;
- an `Авто-узел` / smart node row at the top;
- several node rows with name, latency/load bars, and optional favorite icon;
- a split between premium and free sections.

The Windows desktop variant shows a left sidebar, a list of locations, auto node first, and node rows with ping/load.

What to keep:

- user should be able to choose a location after trial/premium activation;
- auto selection remains the recommended first row;
- rows should show only the useful facts: availability, load/ping, premium/free, selected state;
- selection should be direct and reversible.

What to reject/fix:

- do not show fake flags, fake city names, or unverified location inventory;
- if backend only has auto/free, hide premium selection or show a clear “available after access sync” state, not `Скоро`;
- do not make location selection a modal-only explanation.

### Zone 3: Rules

The Rules screen shows three large but compact mode cards:

- `Все, кроме РФ`: Russian/local services go direct, the rest through POKROV;
- `Все устройство`: whole-device routing;
- `Выбранные приложения`: only selected apps/processes go through POKROV.

Below those cards, the generated image shows a Windows-specific selected-processes list with items like browser/game executables and an `Добавить процесс` row.

What to keep:

- Rules should answer one question: “what goes through POKROV?”;
- first-layer labels must be short and user-oriented;
- selected-app/process mode should have a working picker or manual entry;
- Windows should say “процессы” rather than mobile “приложения” when relevant.

What to reject/fix:

- no huge explanatory cards on first layer;
- no “soon” rows for selected processes if the picker exists;
- advanced raw routing should stay behind a warning in Advanced, not mixed into ordinary Rules.

### Zone 4: Account

The Account mobile screen is a clean list/card layout:

- access card: trial status, remaining days, readiness/connected status;
- activation code row;
- Telegram +10 days row;
- payment/subscription row;
- devices row;
- support row;
- about/version row;
- sign-out or account action at bottom.

The Windows account variant uses the same content in a desktop shell with sidebar and compact cards.

What to keep:

- Account should be grouped into simple tasks: access, recovery/linking, payment, support, devices;
- the user should immediately understand how to link an existing Telegram/bot/site account: enter activation code or open Telegram/cabinet;
- every row should have a clear action (`Ввести`, `Открыть`, `Продлить`, `Написать`), not vague `Детали` everywhere.

What to reject/fix:

- do not expose bonus calendar/wheel as dead previews on first layer;
- do not make Account a long technical settings dump;
- no disconnected “Soon” features inside the normal flow.

### Zone 5: Support In App

The support chat screen resembles a messenger:

- top bar `Поддержка`;
- chat bubbles: user problem, support/AI reply;
- diagnostic card with checkmarks: internet connection, POKROV service, device configuration;
- attached log file card with size and download/attach affordance;
- input row at bottom;
- separate AI assistant hint card.

What to keep:

- support should be an in-app chat, not only a browser link;
- “attach logs” must be one tap and understandable;
- AI assistant should help with setup and diagnostics, but operator escalation must be available;
- support copy must be short and human.

What to reject/fix:

- do not pretend AI solved things if backend support lifecycle is not connected;
- do not hide support under advanced/settings;
- avoid technical protocol jargon unless in diagnostics.

### Bottom Motion Strip

The motion strip shows:

- connect button press scale: 0.96 -> 1.0, about 120 ms;
- ring sweep around the connect disc, around 2 seconds while connecting;
- status crossfade / small slide around 200 ms;
- skeleton rows matching final row sizes;
- row feedback highlight around 120 ms;
- sidebar collapse around 240 ms;
- palette swatches.

What to keep:

- motion should be tactile and light;
- use transform/opacity where possible;
- reduce layout shifts;
- provide reduced-motion fallback;
- focus on 60 FPS by avoiding expensive blur/large repaints on Windows.

## Map 2: Web Cabinet And Admin Map

File:

`C:\Users\kiwun\Documents\ai\VPN\docs\design\generated\2026-06-09-pokrov-polish\web-cabinet-admin-map.png`

Purpose:

This map defines the web cabinet and operator admin split. It is useful because it shows “cabinet for user tasks” and “admin for operational control” as separate worlds.

### Cabinet Desktop

The cabinet desktop screen has:

- left sidebar with POKROV mark, user block, and navigation;
- top notice/banner row for maintenance or important backend-owned announcements;
- main access card with trial state, remaining days, progress bar, renewal button, and “how it works” secondary action;
- Telegram +10 days card next to access;
- activation code input card;
- devices card;
- downloads card;
- support card.

What to keep:

- the cabinet first screen should answer: access status, how many days left, how to extend, how to get +10 days, how to recover/link, how to get help;
- no long narrative blocks on the dashboard;
- banners/notices should be backend-managed but plain JSON content only;
- support should be visible from the first screen.

What to reject/fix:

- generated English labels are not final;
- do not show fake iPhone or device names unless backend has them;
- do not overuse progress bars if they do not clarify state.

### Cabinet Mobile

The mobile phone mock shows:

- same top notice compacted;
- access card first;
- Telegram +10 card second;
- activation code input;
- bottom navigation.

What to keep:

- mobile cabinet must stack into a clear order;
- no desktop tables on mobile;
- controls should remain 44 px+ touch-friendly;
- primary task must be visible without scrolling too much.

### Component Panel For Cabinet

Right side shows reusable components:

- cards;
- info/success/warning/error status boxes;
- status chips;
- primary/secondary/tertiary buttons;
- iOS-style rows;
- empty state;
- activation error state;
- backend notice/banner.

What to keep:

- build a small reusable primitive set instead of each page inventing its own card/list style;
- error/empty/loading states should look as intentional as success states;
- backend banner should have open/dismiss behavior and not break layout.

### Admin Desktop

The admin desktop screen has:

- dark left sidebar;
- top KPI cards: total users, active subscriptions, trial ending soon, open tickets;
- users table with filters/search;
- subscription donut chart;
- recent tickets list;
- notices panel;
- banner editor preview;
- release/version panel.

What to keep:

- admin can be denser than consumer surfaces, but still scannable;
- tables need filters, status chips, audit trail, and clear row actions;
- dynamic content management (notices/banners/releases) belongs in admin;
- support tickets and user subscription state should be close enough for operator context.

What to reject/fix:

- do not invent metrics;
- do not hide critical warnings behind decorative panels;
- do not make admin mobile a broken table.

### Admin Mobile

The mobile admin mock turns KPI cards and recent tickets into stacked cards. Tables collapse into list items.

What to keep:

- mobile admin should be functional for quick checks, not full heavy operations;
- table rows become cards with the same primary facts;
- filters stay reachable.

### Bottom Design System Strip

The strip shows:

- component principles: correct rows, clear hierarchy, icon style, status first, responsive;
- spacing and radius examples;
- color tokens;
- typography scale.

What to keep:

- apply shared design tokens consistently across webapp/admin/marketing;
- normalize spacing and typography;
- enforce mobile breakpoints.

## Map 3: Marketing Site And Telegram Bot Map

File:

`C:\Users\kiwun\Documents\ai\VPN\docs\design\generated\2026-06-09-pokrov-polish\marketing-bot-map.png`

Purpose:

This map is about public acquisition and bot/copy clarity: concise landing, pricing/access, support, copy rules, and a simplified Telegram bot.

### Landing Desktop

The landing hero shows:

- top navigation: POKROV logo, features/devices/support/rules, cabinet button;
- backend-managed banner slot at top;
- large headline: “Защита рядом. Доступ без лишнего.”;
- short supporting copy;
- four short benefit rows: Russian services direct, no speed/traffic limits, 5-day trial, Telegram +10 days;
- primary CTA `Попробовать бесплатно`;
- secondary proof/feature row;
- central visual showing app/cabinet screenshots, not abstract art;
- Telegram +10 banner at bottom.

What to keep:

- public site should sell clarity and trust, not huge feature encyclopedias;
- first viewport should show actual product surfaces;
- one primary CTA;
- dynamic banner slot can show important notices or promos.

What to reject/fix:

- no fake awards, no “best VPN” unsupported claims;
- no hidden/stuffed SEO copy;
- no “coming soon” public product promises;
- do not overdo long paragraphs.

### Landing Mobile

The mobile landing keeps:

- top bar;
- trial row;
- Telegram +10 card;
- connect-button visual;
- short bullets;
- primary CTA.

What to keep:

- mobile site should be as direct as app home: trial, bonus, CTA, short proof;
- avoid “everything stacked forever” before the action.

### Pricing / Access Section

Shows plan cards:

- Premium and Ultra-like columns;
- price per month;
- included features;
- return/refund and support text.

What to keep:

- pricing must be honest and tied to real provider availability;
- plan differences should be understandable in 5 seconds;
- use beta truth for what is not production-mature.

What to reject/fix:

- do not show plan tiers that backend/payment cannot fulfill;
- no unsupported unlimited/safety claims if not evidence-backed.

### Support Section

Shows two cards:

- in-app support;
- Telegram support.

What to keep:

- support should feel available and concrete;
- public site should explain where to get help without dumping technical instructions.

### Copy Rules Panel

Shows rules:

- speak honestly and simply;
- no loud promises;
- say beta where it matters;
- use VPN wording only where useful;
- short, clear sentences;
- no stars/awards as decoration.

What to keep:

- this panel is the clearest copy direction: human, plain, no hype.

### Telegram Bot Flow

The bottom shows several Telegram-like screens:

- main bot menu: access active, trial 5 days, mode, device; buttons for open app, cabinet, support, get code, payment;
- “get code” flow: user asks for app login/recovery code;
- code sent state, with resend/change email/open app actions;
- cabinet/status summary state;
- support request state;
- payment actions state.

What to keep:

- bot should be a short command center, not a second app with confusing nested menus;
- remove decorative star buttons from normal user flow;
- keep Telegram Stars wording only inside payment/admin contexts where it literally means the Telegram payment unit;
- reviews can use numeric 1-5 buttons or neutral labels instead of star glyph spam;
- every bot screen should have one obvious next step.

What to reject/fix:

- no emoji-heavy menus;
- no `⭐` as decoration for feedback/admin sections;
- no long markdown blocks with mixed account/payment/support concepts.

## Map 4: Unified Surface Map

File:

`C:\Users\kiwun\.codex\generated_images\019e88e5-9867-74d2-afaf-6a047cd8b13f\ig_0d3091cf68ee90b6016a274a8326b481919033bfdcabdbe71a.png`

Purpose:

This earlier generated map is less specific than the three maps above, but it is useful as a whole-product overview: app, cabinet, admin, marketing, support bot, UX rules, motion, and philosophy on one board.

### Useful Parts

- six-zone whole-product composition;
- UX rules: one main action, first layer short, details in sheets, mobile priority, support visible;
- motion examples: press scale, ring sweep, crossfade, skeleton, row feedback, sidebar collapse;
- philosophy: POKROV as calm control over connection, not a technical toy.

### Reject/Fix

- generated domains/microcopy may be wrong;
- do not copy labels blindly;
- use current three maps as more precise references.

## Consolidated Design Rules From Maps

Client app:

1. Home: connect button, trial days, Telegram +10, current status, selected mode/location, WARP only if testable.
2. Locations: auto first, selectable nodes when access allows, clear selected state, no fake flags/cities.
3. Rules: three modes only on first layer; selected processes picker must work or be hidden.
4. Account: task groups, not a huge settings list.
5. Support: in-app chat, attach logs, AI + operator route.
6. No visible `Скоро` on primary surfaces.

Web cabinet:

1. First screen: access, days left, renew, Telegram +10, activation code, devices, downloads, support.
2. Mobile: stacked cards, no broken tables, one primary action.
3. Dynamic notices/banners are plain backend JSON and dismissible.

Admin:

1. Dashboard: users/subscriptions/tickets/releases/notices/banners/nodes.
2. Tables desktop, cards mobile.
3. Audit/status chips everywhere important.
4. Dense but not visually chaotic.

Marketing:

1. Actual product screenshots over abstract decoration.
2. One clear CTA.
3. Concise benefit bullets.
4. Honest plan/trial/support copy.
5. Telegram bonus banner.

Bot:

1. Main menu: open app, cabinet, support, get code, payment.
2. No decorative stars.
3. Numeric/neutral review buttons.
4. Telegram Stars only as payment unit where needed.
5. Short messages; one action per screen.

Motion:

1. Press feedback: 100-140 ms.
2. Status crossfade/slide: 160-220 ms.
3. Connect ring sweep: smooth, not layout-changing.
4. Skeletons sized like final content.
5. Sidebar collapse: width + label opacity, no content jumping.
6. Respect reduced motion.
