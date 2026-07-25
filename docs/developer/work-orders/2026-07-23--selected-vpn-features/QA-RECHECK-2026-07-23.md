# Selected VPN Features — Full QA Recheck

Date: 2026-07-23

Status: `LOCAL_QA_PASS`

Production guides destination: `BLOCKED_BY_DEPLOY`

## Verdict

QA-01, QA-03, QA-04, QA-05 и QA-06 исправлены и повторно проверены в текущих
worktree. QA-01 и QA-03 дополнительно пройдены на свежем debug APK в LDPlayer
через ADB; красного Flutter-экрана, fatal logcat и молчащего клика по серверу
больше нет.

Локальный `/guides/` теперь содержит 42 инструкции и 42 визуальных сценария:
HTML-схемы POKROV, проверенные снимки fallback-клиентов и выделенный элемент
нажатия. Marketing build и браузерная проверка прошли. Текущий production
`https://pokrov.space/guides/` по-прежнему нельзя считать исправленным до
развёртывания этого кандидата. Deploy не запрашивался и не выполнялся.

## Candidate

| Lane | Branch and base | Worktree |
| --- | --- | --- |
| Platform | `codex/selected-vpn-features-ios-ui` from `master@95febec` | `C:/Users/kiwun/Documents/ai/VPN/.worktrees/selected-vpn-features-ios-ui` |
| Client | `codex/selected-vpn-features-ios-ui` from `main@60a6ca4` | `C:/Users/kiwun/Documents/ai/POKROV-app/.worktrees/selected-vpn-features-ios-ui` |

Commit, push, deploy, signing and production mutation: `NOT_REQUESTED`.

Android artifact under test:

`C:/Users/kiwun/Documents/ai/POKROV-app/.worktrees/selected-vpn-features-ios-ui/apps/android_shell/build/app/outputs/flutter-apk/app-debug.apk`

Package: `space.pokrov.pokrov_android_shell`. Environment: LDPlayer 14,
instance `0`, 1920×1080. Во время текущего ADB-прохода запускался только один
эмулятор и только POKROV.

## Recheck Matrix

| # | Flow | Result | What was checked |
| --- | --- | --- | --- |
| 1 | Full automation | `PASS` | Client, Android host, Windows host, runtime engine, platform services, cabinet E2E, marketing build/SEO/responsive |
| 2 | First launch | `PASS` | New/returning user actions, layouts, back navigation |
| 3 | Restore access | `PASS` | Empty-code validation, invalid code, busy state and recovery |
| 4 | Protection/connect | `BLOCKED_BY_ACCESS` | UI and staged state render; live tunnel is blocked by existing backend device registration |
| 5 | Locations | `PASS` | До Smart Connect показано объяснение и замок; строка сервера не принимает выбор, поиск и избранное остаются доступны |
| 6 | Route modes/apps | `PASS` | Mode changes, installed-app picker, search, details, add/remove and manual app validation |
| 7 | DNS/LAN/trusted Wi-Fi | `PASS` | DNS/LAN покрыты тестами; ручной SSID добавлен на свежем APK без Flutter/fatal ошибки |
| 8 | Profile/cabinet | `PASS` | Subscription sheet, cabinet handoff, diagnostics and profile controls |
| 9 | Guides handoff | `IMPLEMENTED_LOCAL` / `BLOCKED_BY_DEPLOY` | Локальный `/guides/` собран и проверен; production всё ещё требует отдельного deploy |
| 10 | Rewards hub | `PARTIAL` | Empty/unavailable state, referral/Telegram/achievements shell; live populated wheel/calendar/quests blocked by session state |
| 11 | Theme and motion | `PASS_WITH_MANUAL_OWNER_TEST` | Light/dark/system работают, выбранная тема имеет `selected=true`; финальный физический TalkBack/contrast pass остаётся ручным |
| 12 | Android Quick Settings | `PASS` | Tile and VPN service registration, add/remove tile |
| 13 | Cold restart/cleanup | `PASS` | Clean cold launch, no fresh fatal log, test state reverted, emulator stopped |

## Findings

### QA-01 — manual trusted Wi-Fi add

Resolution: `RESOLVED_LOCAL`, former severity `P1`.

`routing_controls.dart::_addManually` no longer owns and disposes a
`TextEditingController` across the bottom-sheet teardown. The sheet returns a
plain validated string, and the parent state is updated only after the route
has closed and the widget is still mounted.

Proof:

- widget regression: manual `POKROV-QA-TEST` persists and
  `tester.takeException()` is null;
- fresh APK installed with `adb install -r`;
- the same SSID was added through the real LDPlayer UI;
- UI tree contained the saved SSID;
- final logcat scan found no `_dependents.isEmpty`, `FlutterError`,
  `Unhandled Exception`, `RenderFlex overflow` or `FATAL EXCEPTION`;
- test SSID was removed after capture.

### QA-02 — production guides handoff

Resolution: `IMPLEMENTED_LOCAL`; production remains `BLOCKED_BY_DEPLOY`.

The canonical URL stays `https://pokrov.space/guides/`. The current candidate
exports a searchable route with 42 guide summaries, 42 detail records and a
visual spec for every guide ID. Each card identifies client, platform, screen
and exact control. POKROV uses HTML simulations; Hiddify and Happ use reviewed
screenshots; v2rayN uses a labelled reconstruction based on its official wiki.

Local production build, desktop/mobile browser pass and runtime visual coverage
check passed. The existing production origin still serves the old marketing
homepage until deployment. Deployment remains `NOT_REQUESTED`.

### QA-03 — location rows before provisioning

Resolution: `RESOLVED_LOCAL`, former severity `P2`.

Selection is available only when provisioned access and Smart Connect both
exist. Before that, the page shows «Выбор откроется после первого подключения»,
the selection affordance becomes a lock, and the row has no press surface.
Favorites and search remain usable.

ADB proof: tapping the Frankfurt row left the UI tree byte-for-byte unchanged,
opened no dialog and produced no Flutter/fatal error; the favorite control
changed independently and was then restored.

### QA-04 — duplicate switch semantics

Resolution: `RESOLVED_LOCAL`, former severity `P2`.

WARP and routing rows now expose one explicit semantics container and exclude
the nested visual switch. Widget semantics tests pass. Android UIAutomator saw
exactly one WARP node, one LAN node and one trusted-Wi-Fi pause node, each as a
single `android.widget.Switch`. A physical TalkBack listening pass remains
`MANUAL_OWNER_TEST`.

### QA-05 — theme picker selected state

Resolution: `RESOLVED_LOCAL`, former severity `P2`.

`PokrovCheckRow` now exposes `Semantics(selected: selected)`. Widget tests pass.
ADB UI trees reported `selected=true` first for «Системная», then for
«Светлая» after selection. The test restored «Системная».

### QA-06 — cabinet static accessibility gaps

Resolution: `RESOLVED_LOCAL`, former severity `P2`.

- Program selectors expose `aria-pressed`, `aria-describedby` and the shared
  focus ring.
- Quest progress exposes `role="progressbar"`, min/max/current/value text and
  the task label.

Webapp lint/build pass and the cabinet Playwright pack passes `53/53`, including
the new ARIA assertions.

### QA-07 — dark-theme secondary contrast needs measurement

Severity: `MANUAL_OWNER_TEST`.

The dark screen is visually coherent, but some secondary text appears close to
the minimum readable contrast. This was not promoted to a defect without a
measured contrast check on a physical display.

## Automated Evidence

| Surface | Command/result |
| --- | --- |
| Client full gate | `pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1` — `PASS` |
| Client suites | app shell `189`, Android `5`, Windows `9`, runtime engine `24` — `PASS` |
| Client analysis | app shell, runtime engine, Android shell and Windows shell — no issues |
| Android build | `flutter build apk --debug` — `PASS` |
| ADB focused retest | manual trusted Wi-Fi, locked locations, favorite isolation, switch-node counts and theme `selected` state — `PASS` |
| Platform focused pack | `216 passed, 2 subtests passed` — `PASS` |
| Docs/public copy | `45 passed` — `PASS` |
| Cabinet lint/build/E2E | lint `PASS` with two unrelated pre-existing warnings; build `39` pages; E2E `53/53` |
| Marketing | build `31` pages; SEO/brand `PASS`; responsive `PASS` |
| Guide registry | `42` summaries, `42` details, runtime visual coverage for every ID — `PASS` |
| Quick Settings | manifest/service registration and temporary add/remove tile — `PASS` |

The successful platform pytest process ended with the known Windows temporary
directory cleanup warning after exit code `0`; it is not counted as a test
failure.

One intermediate cabinet rerun had a single 5-second timeout while waiting for
the existing login heading; the changed program-selector test passed in that
run. With no source change in between, the immediate full rerun passed `53/53`.

## Motion Evidence

The real LDPlayer recording covered navigation between tabs and the WARP state
change. A 3×3 contact sheet showed stable intermediate states with no clipped
screen, blank frame or corrupted transition. Source and widget tests also cover
finite animation and reduced-motion paths.

Current-run local evidence directory:

`C:/Users/kiwun/AppData/Local/Temp/pokrov-qa-recheck-2026-07-23`

Important files:

- `motion-tabs-warp.mp4`
- `motion-contact-sheet.png`
- `debug-after-wifi-add.png`
- `25-guides-link.png`
- `27-dark-theme.png`
- `28-rewards-hub.png`

This directory is temporary evidence and is not a tracked release artifact.

Tracked focused evidence:

- `evidence/pokrov-trusted-wifi-adb.png`
- `evidence/pokrov-locked-locations-adb.png`
- `evidence/guides-hiddify-visual.png`
- `evidence/guides-v2rayn-visual.png`
- `evidence/guides-trusted-wifi-visual.png`
- `evidence/guides-hiddify-mobile.png`

## Honest Limitations

- Live tunnel on this exact run: `BLOCKED_BY_ACCESS`. Backend returned
  `Устройство уже зарегистрировано. Обновите сессию или восстановите доступ.`
- Live populated rewards state: `BLOCKED_BY_ACCESS`; automated state coverage
  passed.
- Local visual browser pass for the guide catalog: `PASS` on desktop and
  mobile, including Hiddify, v2rayN and POKROV trusted-Wi-Fi visuals.
- Production `https://pokrov.space/guides/`: `BLOCKED_BY_DEPLOY`. The local
  artifact does not prove the current origin.
- Signed candidate, physical Android device, TalkBack, Windows clean VM, store
  and external-origin proof: `MANUAL_OWNER_TEST`.
- Payment, deploy, publication and production flags/data: `NOT_REQUESTED`.

## Cleanup

- WARP restored off.
- Route mode restored to Smart.
- Favorite and selected Chrome app removed.
- LAN/DNS/theme restored.
- `NEARBY_WIFI_DEVICES` test permission revoked.
- `POKROV-QA-TEST` removed.
- Quick Settings tile restored to the original list.
- No runtime VPN service left active.
- LDPlayer stopped; local ADB setting restored to its previous value and ports
  `5037`, `5554`, `5555` closed.

## Guide Expansion Supplement

The earlier `42`-guide counts in this report are retained as evidence for the
pre-expansion candidate. This supplement supersedes only the current guide
catalog, guide UI and related build/E2E counts.

Current local candidate:

- shared catalog: `46` summaries and `46` matching detail records;
- fallback clients with proactive setup/control/warning sections: Hiddify,
  Happ, v2rayN, v2rayNG, Streisand, V2Box and Shadowrocket;
- fallback visual coverage: `18` real, source-linked screens. Hiddify/Happ keep
  their existing clean captures; v2rayN, v2rayNG, Streisand, V2Box and
  Shadowrocket now use `16` additional step screens instead of labelled
  reconstructions;
- public and cabinet guide pages: text search, category filters with counts,
  clear/reset actions and result announcements;
- POKROV atlas: `20` redacted real Android screens/panels with exact numbered
  outlines, explanations below the image, recommended setup and cautions;
- the former filled Happ annotation was replaced by a hollow outline, so
  `Добавить подписку` remains readable;
- the mobile guide-card min-content overflow was fixed; `390 × 844` browser
  proof shows no horizontal overflow.

Focused verification:

- marketing lint: `PASS`;
- marketing production build: `PASS`, `32` static pages;
- marketing SEO/brand: `PASS`;
- marketing responsive pack: `PASS`;
- webapp lint: `PASS` with the same two unrelated pre-existing warnings;
- webapp production build: `PASS`, `40` static pages;
- cabinet/rewards Playwright pack: `PASS`, `54/54`, including the new mobile
  guide and atlas scenario;
- docs/public-copy contract pack: `PASS`, `46/46`;
- guide/asset contract: `PASS` — `46` unique guide IDs, `46` detail records,
  `7` complete fallback guides, all `18` fallback screenshots and all `20`
  atlas images present in both public asset trees; matching fallback assets are
  byte-identical between marketing and cabinet and return HTTP `200`;
- in-app browser pass: `PASS` for search, category counts, all seven fallback
  galleries, v2rayNG/Shadowrocket image loading, readable desktop grids and
  `390 × 844` mobile rendering without horizontal overflow.

### Apple Account Policy Supplement

Owner decision after the guide recheck:

- own Apple Account remains the primary path;
- support may send the user to either
  `https://familypro.io/shared-apple-id` or the reserve
  `https://appstops.ru/accounts/` as voluntary temporary fallbacks;
- availability, lifetime, recovery, updates and replacement are not promised
  and the fallback is not part of the tariff or compensation policy;
- credentials remain on the external source page and are not retained in
  POKROV source, static content, logs or cache;
- the guide requires login through the profile inside the App Store
  application, never through system Apple Account/iCloud settings, no payment
  data or purchases, and immediate sign-out after install;
- failure branches cover blocked account, invalid credentials and lost Family
  Sharing access without claiming guaranteed recovery.
- the public fallback page presents both sources as equal-height responsive
  cards with external-source actions and a shared non-guarantee warning.
- production-render proof: desktop cards are `480 × 371` each; mobile cards
  are `358` pixels wide, stack in one column and do not create horizontal
  overflow. Both external links use a new tab and `rel=noreferrer`.

Focused supplement verification:

- shared catalog JSON and six-step Apple guide contract: `PASS`;
- public-copy guardrails: `PASS`, `13/13`;
- marketing lint/build/SEO/responsive: `PASS`, `32` pages;
- webapp lint/build: `PASS`, `40` pages, with the same two unrelated warnings;
- focused mobile guides/atlas Playwright scenario: `PASS`, `1/1`;
- `git diff --check`: `PASS` with existing line-ending warnings only.

Tracked visual evidence:

- `evidence/guides-happ-overlay-fixed.png`
- `evidence/guides-happ-overlay-mobile-fixed.png`
- `evidence/guides-pokrov-atlas-desktop.png`
- `evidence/guides-pokrov-atlas-card.png`
- `evidence/guides-pokrov-atlas-mobile.png`
- `evidence/apple-account-options-desktop.png`
- `evidence/apple-account-familypro-mobile.png`
- `evidence/apple-account-appstops-mobile.png`

Production `https://pokrov.space/guides/` and
`https://pokrov.space/guides/pokrov-app/` remain `BLOCKED_BY_DEPLOY`.

### Apple Source Availability Correction

The earlier two-card proof above is retained as evidence for the pre-correction
candidate. It is superseded for current source status and public copy.

Current review on 2026-07-23:

- AppStops `/accounts/` explicitly says there is no active account and asks the
  user to wait for a new giveaway. It is now a visibly inactive monitor, not a
  reserve source.
- The active-route grid separates the official own-account path, VanyaVPN’s
  currently visible temporary US-account action, FamilyPro, iZakStore, paid
  Happ installation help, the paid AppStops catalog and a private US-account
  seller.
- The AppStops paid catalog remains distinct from its free giveaway: the
  provider publishes immediate delivery after payment, a three-day guaranteed
  access window and a later-update caveat.
- Public pages and published terms were reviewed. No third-party login or
  payment was tested, so successful issuance is not claimed.
- Credentials are still excluded from source, documentation, screenshots,
  logs and cache.

The retained source matrix and rejected low-evidence candidates are documented
in [APPLE-ACCOUNT-SOURCES-2026-07-23.md](APPLE-ACCOUNT-SOURCES-2026-07-23.md).
