# POKROV Redesign — Sub-Project 3: Implementation Plan

- Date: 2026-07-06
- Spec: `docs/superpowers/specs/2026-07-06-client-app-pokrov-clear-design.md` (approved)
- Target repo: `C:/Users/kiwun/Documents/ai/POKROV-app`, commits land per phase on `main`
- Rule: every phase ends with green `flutter analyze` + `flutter test` in `packages/app_shell`; contract tests change in the same commit as the values they lock.

## Phase A — Palette alignment (light + dark)

- A.1 Swap `pokrov_palette.dart` light/dark token values per spec §5 (incl. new `accentSoft`, `connectedGreen`); keep client-specific reward/gold pair.
- A.2 Update `design_system_contract_test.dart` hex locks in the same commit; keep the no-pure-black rule test.
- A.3 Run app_shell suite + windows/android shell tests.

## Phase B — Golos Text

- B.1 Add static Golos Text TTFs (400–800, latin+cyrillic, OFL file) to `packages/app_shell/assets/fonts/`; declare in pubspec.
- B.2 Point `_buildPokrovTheme` `fontFamily` at the bundled family; drop the dead `SF Pro Display` stack.
- B.3 Suite + visual sanity on Windows shell.

## Phase C — Status semantics, switch, persistence

- C.1 Connect-disc connected fill → `connectedGreen` (`status_green`); verify settle keys/tests untouched.
- C.2 `SwitchThemeData` to the switch canon (on/off track, white thumb).
- C.3 Theme-mode file persistence (default `system`); wire into `_PokrovSeedAppState`.
- C.4 Suite green.

## Phase D — Docs, wording fix, closure

- D.1 Client `DESIGN.md`: palette values sourced from pokrov-clear; note alignment wave.
- D.2 `docs/product/client-product-contract.md`: replace the stale VPN-wording prohibition with the 2026-06-13 + platform 2026-06-01 rule.
- D.3 Full test run (app_shell, shells, gradle unit if touched); grep gates per spec §8.3.
- D.4 Findings recorded here; owner visual review on Windows shell run.

### Findings (2026-07-06, phases A–D landed)

- Commits on `POKROV-app` (local `master`/main line): `c87761e` palette alignment, `591f7e8` Golos Text bundle + theme wiring, `d85ffa8` status-green disc + switch canon + persisted theme, + docs commit (DESIGN.md/product-contract wording).
- Palette extension gained `accentSoft` and `connectedGreen` fields; `onAccent` dark label fixed to token `#101713`; dark set moved from blue-gray to the shared off-black greens.
- Golos Text: static TTFs 400–800 (latin+cyrillic) + OFL bundled in `pokrov_app_shell`; theme `fontFamily: 'packages/pokrov_app_shell/Golos Text'`; dead `SF Pro Display` reference removed.
- Theme persistence: `PokrovFileThemeModeStore` (best-effort file store, default system) wired into `PokrovSeedApp`; covered by a new contract test.
- Gates: app_shell 143/143, windows_shell 4/4, android_shell 4/4, contract greps clean (`connectedGreen` only in disc/switch/palette/test; no `0xFF0F725D`/`SF Pro`).

### Consilium backlog (2026-07-06, two review agents on features; ranked)

**Closed same-day** (9 commits `a189973..87337a5`, tests 149/149): interaction 1-10 (chat scroll-to-new + draft-on-failure, redeem sheet keyboard + inline validation, rewards hub live-reactive + awaited refresh + maybePop + in-sheet copy morph, device revoke confirm + result snacks, locations real error/retry, app-picker keyboard/clear/drag-dismiss, onboarding restore autofocus + Android back-to-choice, selected-apps AnimatedSize + inline invalid + autofocus); visual 11 (weight soup), 12 (one status-pill metric), 14 (16px tab gutter), 18 (WARP panel tokens), 19 (honest desktop header affordances); round-1 leftovers: dim disabled rows (`enabled` flag), full-row WARP toggle, Pressable Listener→GestureDetector (scroll twitch gone).

**Still open (next wave):**

Landed same-day quick fixes: white-on-mint → `onPrimary` (onboarding icon, chat user bubble), tabular figures in `labelLarge`, 44pt notifications CTA, plus round-1 items (Cupertino WARP switch, inset separators, readable snack icons + inset above tab bar, settled theme pick).

Interaction (files:lines in agent report wording):
1. Support chat: no scroll-to-new-message (`support_chat.dart:617`, append at 254/275) — add ScrollController+animateTo.
2. Redeem sheet ignores keyboard: `isScrollControlled` + `viewInsets` padding + submit-from-keyboard + validate before pop (`profile_sheets.dart:37,110-124`).
3. Rewards hub sheet is frozen-stateless with fake pull-to-refresh (`rewards_hub.dart:28,62-67,137,170`) — make reactive, await real refresh, `maybePop`.
4. Device revoke: destructive without confirm, silent failure, skeleton flash instead of animated row removal (`profile_sheets.dart:243-257,416-421`).
5. Locations: `locationsCatalogError`/`onRefreshLocationsCatalog` are dead props — no error state, no retry (`locations_surface.dart:24-25`).
6. Rules app-picker: fixed 0.82 height vs keyboard, no `keyboardDismissBehavior: onDrag`, no clear button (`rules_surface.dart:696,756-776,815`).
7. Copy-confirmation snack hides under the open rewards sheet (`rewards_hub.dart:842-870`) — in-sheet copy→check morph.
8. Chat composer clears text before await; failures lose the draft (`support_chat.dart:257,324-352`).
9. Onboarding restore: no autofocus/`textCapitalization.characters`, Android back exits instead of returning to choice (`onboarding_flow.dart:381-405`).
10. Selected-apps list: no insert/remove transitions, silent invalid manual input (`rules_surface.dart:450-461,300-307,369-401`).

Visual:
11. Weight soup: w700 title+value in settings rows, bold muted subtitles (`pokrov_controls.dart:805-813`, `home_surface.dart:986-994,1059-1063,1296-1302`).
12. Two status-pill components with different heights/sizes (`shell_widgets.dart:133-149` vs `pokrov_controls.dart:995-1013`) — unify.
13. Home rhythm off the 4pt grid (10/14/6/2 everywhere; `PokrovSpacing` barely used in features) — normalize to 8/12/16.
14. Page top padding jumps between tabs (12/24/18/34) and sheet gutters (18/20/22) — one token each.
15. Triple access-info repetition on Home; profile «Ваш доступ» duplicates pills vs rows (`home_surface.dart:266-340,693-699`, `profile_surface.dart:474-524`).
16. Leading-icon zoo (54/46/42/38/36/34 px, radius 18..11) — two sizes (44 hero / 36 row), one chevron alpha.
17. Radii off `PokrovRadii` in home/locations tiles; app-picker sheet radius 24 vs canonical 28.
18. WARP consent panel white-alpha colors → tokens (`warp_sheet.dart:44-49`).
19. Desktop Home header fake affordances: «Профиль» tooltip opens Rules, bell opens connection info (`home_surface.dart:415-426`).
20. Theme restore lands after first frame (flash when explicit theme set) — read store pre-`runApp` or gate first frame.

Round-1 leftovers still open: dim disabled rows (explicit `enabled` param), `RefreshIndicator`→Cupertino refresh, WARP tile full-row tappable, `PokrovPressable` Listener→GestureDetector (scroll twitch), consolidate four press implementations, typed state instead of string sniffing (`accessLabel.startsWith('5 ')`, `_isTerminalConnectMessage`).
- Foreign uncommitted work in the client repo (flutter_secure_storage bootstrap changes + release-doc edits) left untouched; the pubspec fonts commit excluded their dependency line.
- Remaining for owner: visual review on a Windows shell run (`flutter run` in `apps/windows_shell`), real-device captures stay `MANUAL_OWNER_TEST`.

### Phase E — iPhone-feel pass (2026-07-06, owner request, landed)

- `PokrovSwitch`: real `CupertinoSwitch` on every platform (status-green on-track, selection tick on toggle); replaced the Material switches in the WARP row and WARP consent sheet.
- `PokrovCheckRow`: iOS Settings picker row with a springy emerald checkmark; the theme picker (Системная/Светлая/Тёмная) now selects with checkmarks instead of «Выбрана» labels (ValueKeys preserved).
- `PokrovScrollBehavior`: iOS bouncing physics + no Android glow/stretch on every scrollable.
- Cupertino page transitions (slide-from-right with parallax) on all platforms; Material ripple replaced by transparent splash + quiet UIKit-style highlight (deliberately NOT `NoSplash.splashFactory` — it leaks a raw pending Timer in drag-heavy widget tests).
- Android high refresh rate: `flutter_displaymode` in `android_shell`, `setHighRefreshRate()` best-effort at boot — animations run at the panel's native 90/120Hz.
- Gates: app_shell 143/143, windows/android shells 4/4 each. Lock files intentionally NOT committed: they picked up the parallel session's uncommitted `flutter_secure_storage` transitives and will land with that work.
