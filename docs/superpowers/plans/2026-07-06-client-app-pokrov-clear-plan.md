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
