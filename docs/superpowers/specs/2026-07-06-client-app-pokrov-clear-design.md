# POKROV Redesign — Sub-Project 3: Client App pokrov-clear Alignment

- Date: 2026-07-06
- Status: Approved by owner 2026-07-06 (blanket approval; open questions via menu)
- Parent effort: global redesign wave `0 → 1 → 2 → 3`; sub-projects 0–2 landed in the platform repo (`fbe332e` … checkout rebuild)
- Target repo: `C:/Users/kiwun/Documents/ai/POKROV-app` (melos monorepo; the whole UI lives in `packages/app_shell`), promotion line `POKROV-app/main`

## 1. Context And Goal

The client already went through a strong June redesign: the active `docs/design/2026-06-13-pokrov-product-ui-direction.md` locks 12 owner decisions (flat iOS-like quiet consumer UI, one tactile connect disc, mandatory off-black dark theme, honest states, Support as a separate screen), and the implementation is guarded by ~119 widget tests plus contract tests that pin the palette, motion tokens, disc phases, and copy rules. **This wave is not an IA rebuild.** It aligns the client's brand foundation with the `pokrov-clear` canon that marketing and the cabinet now ship: the emerald/white token set, Golos Text, the status-green "connected" semantics, the iOS switch canon, plus two hygiene gaps found in grounding (theme choice does not persist; a stale VPN-wording clause contradicts the newer owner decision).

## 2. Owner Decisions (locked)

| # | Question | Decision |
|---|---|---|
| 1 | Scope | **Brand-foundation alignment only** — palette, type, status semantics, switch, persistence, wording fix. IA, navigation, connect-disc behavior, motion system stay per the active 2026-06-13 direction |
| 2 | Icons | Material icons stay (root DESIGN.md: client canon is flutter-material; lucide is a web-only rule) |
| 3 | Dark theme | Stays mandatory (2026-06-13), realigned to the shared off-black-green dark tokens |
| 4 | VPN wording | The 2026-06-13 UI direction + platform `2026-06-01` owner rule win: «POKROV is presented as a VPN» is allowed in client UI; the stale prohibition in `docs/product/client-product-contract.md` is corrected in this wave |
| 5 | Checkout | Stays an external handoff to `pay.pokrov.space` — no in-app paywall |

## 3. Scope

In scope (all inside `POKROV-app`):

- `packages/app_shell/lib/src/design_system/pokrov_palette.dart` — full light+dark palette swap to shared tokens (§5) with `design_system_contract_test.dart` updated in the same commit
- Golos Text bundled into `pokrov_app_shell` (OFL, static weights 400–800, latin+cyrillic) and wired through the theme factory in `seed_shell.dart`
- Switch styling aligned to the `component.switch` canon (status-green on-track, `rgba(120,120,128,.16/.32)` off-track, white thumb)
- Connect-disc "connected" fill moves to `status_green` (`#34C759` / dark `#30D158`) — the only place besides switches that may use it (web canon parity)
- Theme-mode persistence (file store, same pattern as `PokrovFileFirstLaunchStore`; default stays `system`)
- Docs same-wave: client root `DESIGN.md` palette note, `docs/product/client-product-contract.md` wording clause fix

Out of scope:

- `runtime_engine`, `app_first_runtime_bootstrap.dart` contracts, routing semantics, update-check, release metadata (`release-handoff*`), onboarding logic
- Navigation/IA, connect-disc phase machine and settle keys, motion token values (client scale 120/180/240/280/480 stays — churn without benefit), haptics tiers
- Rewards gold accents (client-specific token pair stays; web `gold_soft` deprecation does not apply to the client rewards surface)
- iOS/macOS shells (readiness-only), store/signing claims

## 4. Hard Constraints (client repo canon)

- Contract tests are the palette lock: `design_system_contract_test.dart` changes in the same commit as `pokrov_palette.dart`; `no pure black` rule stays enforced.
- Connect-disc settle keys (`connect-disc-*-settle`), phase timings, and `PokrovMotionScope` reduced-motion behavior untouched.
- `ui_copy_contract_test.dart` rules stay: no raw hosts/ports/configs/route jargon in UI strings; free access never labeled "free node"; beta status only in diagnostics.
- Release gates honesty: no store / stable `1.0.0` / trusted-signing / RU-origin claims; startup update-check flow untouched.
- Package boundaries per `docs/architecture/package-boundaries.md`; host apps stay thin.

## 5. Token Mapping (exact values, from `shared/design-tokens.json`)

Light (`PokrovPaletteTokens.light`):

| Client token | Old | New | Source |
|---|---|---|---|
| canvas | #F7F8FA | **#F5F7F6** | `canvas_alt` (grouped-list canvas; surfaces stay white on it) |
| surface | #FFFFFF | #FFFFFF | `surface` |
| surfaceMuted | #F2F5F4 | **#EEF4F1** | `surface_muted` |
| ink | #10131A | **#16181D** | `text` |
| muted | #697080 | **#5E6772** | `text_soft` (readable secondary; #9AA1A9 only decorative) |
| accent | #0F725D | **#12805A** | `emerald` |
| accentBright | #16A27B | **#0F6B47** (hover/pressed role) | `emerald_strong` |
| accentSoft | — | **#E6F4ED** | `emerald_soft` |
| success | #159A68 | **#174F3D** on **#E6F4ED** | `semantic.success` |
| warning | #E29A1F | **#765D23** on **#F7EFD9** | `semantic.warning` |
| danger | #D94D4D | **#8D352E** on **#F8E7E3** | `semantic.danger` |
| line | rgba(16,19,26,.10) | **rgba(17,24,20,0.08)** | `line` |
| connectedGreen (new) | — | **#34C759** | `status_green` — connect-disc connected + switch on only |

Dark (`PokrovPaletteTokens.dark`) — off-black greens replace the blue-gray set:

| Client token | Old | New |
|---|---|---|
| canvas | #11161D | **#111715** |
| canvasAlt | — | **#151C19** |
| surface | #171D25 | **#161D1A** |
| surfaceRaised | — | **#182019** |
| ink | — | **#F3F2EC** |
| soft/muted | — | **#ABB6AE** / **#78857E** |
| accent | #34C79A | **#8AC4AB** (text on accent: **#101713**) |
| accentHover | — | **#A5D3BF** |
| line | — | **rgba(239,243,241,0.12)** |
| connectedGreen | — | **#30D158** |

Switch canon: on-track `#34C759`/`#30D158`, off-track `rgba(120,120,128,0.16)`/`0.32`, thumb `#FFFFFF`, transition feel ≈ `220ms cubic-bezier(0.34,1.3,0.64,1)` (Material `SwitchThemeData` approximation; exact 51×31 geometry documented as variance).

## 6. Typography

- Bundle **Golos Text** static TTFs (400/500/600/700/800, latin+cyrillic, OFL license file included) under `packages/app_shell/assets/fonts/` + pubspec `fonts:` section.
- `_buildPokrovTheme` sets `fontFamily: "Golos Text"` (with `package: pokrov_app_shell`) replacing the non-functional `SF Pro Display` stack; existing size/weight/letter-spacing scale stays.
- Fallbacks remain system (Segoe UI / Roboto) automatically.

## 7. Theme Persistence

Persist explicit theme choice (`system|light|dark`) via a small file store in app-support dir (pattern: `PokrovFileFirstLaunchStore`); load on boot before first frame where possible; default `system`. No sensitive data.

## 8. Verification And DoD

1. `flutter analyze` + `flutter test` in `packages/app_shell` (contract tests updated in-commit; ~119 widget tests stay green, including responsive width matrix and reduced-motion).
2. `apps/windows_shell` + `apps/android_shell` test suites green (`windows_release_contract_test`, manifest guard untouched).
3. Grep gates: old accent `#0F725D`/`0xFF0F725D` gone; no `SF Pro` family reference; `status_green` used only in disc-connected + switch.
4. Docs updated: client `DESIGN.md` (palette source note → pokrov-clear values), `client-product-contract.md` VPN clause aligned to 2026-06-13.
5. Commits land per phase on `POKROV-app/main`; platform-repo plan file records findings.
6. Manual visual pass: Windows shell run (light+dark) — owner review; real device captures stay `MANUAL_OWNER_TEST` per capture plan.

## 9. Risks

| Risk | Handling |
|---|---|
| Contract tests pin dozens of hex values | Palette and test change in one commit; run full app_shell suite per phase |
| Variable-font weight rendering quirks | Use static TTF instances per weight, not the variable font |
| Dark accent flip (bright green → mint) changes CTA feel | Matches web cabinet dark canon exactly; owner review on Windows shell |
| Theme persistence touches boot path | Read is async-safe with system default until loaded; no blocking of first frame |
| client-product-contract edit drifts from platform canon | Quote the platform `2026-06-01` rule + 2026-06-13 client decision in the doc change |
