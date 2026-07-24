# Selected VPN Features — Implementation Status

Last updated: 2026-07-23

Candidate:

- platform: `codex/selected-vpn-features-ios-ui` from `master@95febec`
- client: `codex/selected-vpn-features-ios-ui` from `main@60a6ca4`
- deploy, signing, publication and production mutation: `NOT_REQUESTED`
- current source-candidate verdict: `LOCAL_QA_PASS`; production `/guides/`
  remains `BLOCKED_BY_DEPLOY`; see
  [QA-RECHECK-2026-07-23.md](QA-RECHECK-2026-07-23.md)

Status vocabulary:

- `LOCAL_QA_PASS` — the source candidate passed the recorded local automated,
  browser and emulator checks; this is not production or signed-device proof;
- `IMPLEMENTED_LOCAL` — code and focused local proof exist in these worktrees;
- `BLOCKED_BY_DEPLOY` — the local artifact is ready, but the current production
  origin cannot be counted as fixed until deployment;
- `FOUNDATION_DISABLED` — contract/schema/UI foundation exists but user access is intentionally off;
- `DISCOVERY_ONLY` — no shipped control or claim;
- `MANUAL_OWNER_TEST` — exact signed artifact/device/store/origin proof is still required.

## MUST

| ID | Status | Local result |
| --- | --- | --- |
| MUST-01 | `IMPLEMENTED_LOCAL` | Protection sheet separates tunnel, DNS, POKROV HTTPS and route ownership; unknown evidence stays unknown. |
| MUST-02 | `IMPLEMENTED_LOCAL` | One bounded repair cycle: disconnect → resolve/stage fresh profile → connect → recheck; overlap and retry loops blocked. |
| MUST-03 | `IMPLEMENTED_LOCAL` | Bounded file cache for locations, inbox, favorites, recents, history, shortcuts and routing preferences with explicit stale/cached state. |
| MUST-04 | `IMPLEMENTED_LOCAL` | Video, AI, Social, Games and RU-direct purpose rules are injected into the runtime profile. |
| MUST-05 | `IMPLEMENTED_LOCAL` | Domain/IP/subnet decisions use the same validated preference model and show the matching reason. |
| MUST-06 | `IMPLEMENTED_LOCAL` | Persistent Favorites and Recent location groups. |
| MUST-07 | `IMPLEMENTED_LOCAL` | Measured ping/load/health plus measurement freshness; missing values are not fabricated. |
| MUST-08 | `IMPLEMENTED_LOCAL` | Cached client inbox plus incident/release/action projections. |
| MUST-09 | `IMPLEMENTED_LOCAL` | Operator-owned incidents, affected-account/window boundary, worker processing and idempotent ledger compensation. Production execution remains `NOT_REQUESTED`. |
| MUST-10 | `IMPLEMENTED_LOCAL` | Shared responsibility map on public trust surfaces and client legal/help continuation. |
| MUST-11 | `IMPLEMENTED_LOCAL` | Field-level privacy table with purpose, retention and deletion path; no false “collect nothing” claim. |
| MUST-12 | `IMPLEMENTED_LOCAL` | Public pre-auth status/help routes and client first-layer support continuation. |
| MUST-13 | `IMPLEMENTED_LOCAL` | Versioned official fallback matrix; own Apple Account is primary, while a temporary support-provided account is an explicitly non-guaranteed emergency path. |
| MUST-14 | `IMPLEMENTED_LOCAL` | Human route taxonomy shared across app, cabinet and public guide copy. |
| MUST-15 | `MANUAL_OWNER_TEST` | Local preflight, analysis, tests and debug builds can be proven here; signed exact-candidate, physical device, clean VM, store and origin gates remain open. |

## SHOULD

| IDs | Status | Local result |
| --- | --- | --- |
| SHOULD-01, 02 | `IMPLEMENTED_LOCAL` | Validated per-domain/IP/subnet VPN/direct overrides, persisted and applied before profile staging. |
| SHOULD-03 | `IMPLEMENTED_LOCAL` + emulator preflight | Automatic/Cloudflare/Google/AdGuard/custom DoH; LDPlayer is local evidence only. |
| SHOULD-04 | `IMPLEMENTED_LOCAL` guide/control | Always-on/Kill Switch guidance and Android VPN-settings handoff; no unsupported cross-platform claim. |
| SHOULD-05 | `IMPLEMENTED_LOCAL` + ADB retest | Exact-SSID detection and manual network add pass; the former `_dependents.isEmpty` lifecycle failure is covered by widget and fresh-APK ADB regression checks. |
| SHOULD-06, 07 | `IMPLEMENTED_LOCAL` | Short-lived one-time pairing code/QR continuation for phones and Android TV; own revocable session and device-limit enforcement. |
| SHOULD-09 | `IMPLEMENTED_LOCAL` | Referral code/link, anonymized conversion, transition history and privacy copy in app and cabinet. |
| SHOULD-10 | `FOUNDATION_DISABLED` | Affiliate capability is visible as not accepting; no application/reward path is enabled. |
| SHOULD-11, 12 | `IMPLEMENTED_LOCAL` | Team-pack application path and existing first-party campaign attribution contract. |
| SHOULD-13, 14 | `IMPLEMENTED_LOCAL` | Manually reviewed competitor-switch and research/quality-feedback applications; no automatic reward for a positive review. |
| SHOULD-16, 17 | `IMPLEMENTED_LOCAL` | Bounded local protection history and user-owned HTTPS post-connect shortcuts. |
| SHOULD-18, 19 | `IMPLEMENTED_LOCAL` | LAN toggle; Android Quick Settings and Windows tray delegate to the main connection state machine. |
| SHOULD-20 | `IMPLEMENTED_LOCAL` | Dirty-profile tracking and idempotent refresh/stage path. |

## CAN And Requested NO Equivalents

| ID | Status | Decision/result |
| --- | --- | --- |
| CAN-01 | `IMPLEMENTED_LOCAL` | Wheel adds 5/7/10% one-use non-stackable discounts; 30-day jackpot unchanged. A second pending discount becomes +1 day. |
| CAN-02 | `IMPLEMENTED_LOCAL` | Existing activity calendar remains backend-authoritative. |
| CAN-03, 04 | `IMPLEMENTED_LOCAL` | Server-evidence achievements and useful quests: first tunnel, second device, routing lesson, approved research. No automatic monetary entitlement. |
| CAN-05 | `DISCOVERY_ONLY` | Emergency reserve withheld until entitlement/economy design exists. |
| CAN-06 | `DISCOVERY_ONLY` | Multihop withheld until base route health/capacity proof exists. |
| CAN-15 | `DISCOVERY_ONLY` | No fake security-tool bundle; each future tool needs a separately maintained real function. |
| NO-01 equivalent | `IMPLEMENTED_LOCAL` | Rewardable private research/confirmed quality contribution, never payment for 5★ or a positive public review. |
| NO-05 | `IMPLEMENTED_LOCAL` policy/guide | The public page separates a user-owned Apple Account, VanyaVPN’s currently visible temporary-account issue action, other free shared sources, paid install help, app catalogs and a private regional-account seller. AppStops `/accounts/` is visibly inactive and no longer presented as available. Credentials are not stored; VanyaVPN login and external payment delivery remain untested. |
| NO-09 equivalent | `IMPLEMENTED_LOCAL` | Narrow “do not store visited-site history” statement plus honest field inventory. |

## Guides And Videos

- `46` task guides are in the shared registry and all `46` have prerequisites,
  numbered steps, expected result, failure steps, platform/version and
  last-verified metadata.
- `46/46` guide IDs have a visual target with client, platform, screen and a
  numbered outline whose explanation is outside the image. The fallback set
  covers Hiddify, Happ, v2rayN, v2rayNG, Streisand, V2Box and Shadowrocket;
  every fallback guide includes recommended first settings, a control glossary
  and explicit warnings. The seven fallback guides now use `18` real,
  source-linked screens: `2` existing captures for Hiddify/Happ plus `16`
  additional screens for v2rayN, v2rayNG, Streisand, V2Box and Shadowrocket.
- The public and cabinet `/guides/` pages have text search, category counts and
  reset controls. The separate `/guides/pokrov-app/` atlas uses `20` redacted
  real Android screenshots and explains every marked control below the image.
  The app links from Profile/Support to the canonical registry.
- The local route is implemented, but the current production
  `https://pokrov.space/guides/` handoff showed the ordinary homepage during the
  2026-07-23 recheck. Cross-surface production proof is therefore not closed.
- Video program status: `PLANNED_NOT_RECORDED`. The registry defines a clean
  LDPlayer/Windows shot order, 45-second ceiling and redaction rules. No video
  may be marked published before the matching clean capture exists.

## Automated Evidence Snapshot

Final local proof for this candidate:

- client release gate: `PASS` — app shell `189` tests, Android shell `5`,
  Windows shell `9`;
- runtime engine: `PASS` — `24` tests;
- Android `testDebugUnitTest`: `PASS` — Gradle `BUILD SUCCESSFUL`, `137`
  actionable tasks;
- client `flutter analyze`: `PASS`;
- selected platform/API/service pack: `PASS` — `216` tests and `2` subtests;
- webapp lint: `PASS` — zero errors and two pre-existing unrelated warnings;
- webapp production build: `PASS` — `40` pages;
- cabinet/rewards Playwright pack: `PASS` — `54/54`, including mobile guide
  search, fallback filtering, Happ content and the POKROV atlas;
- marketing production build: `PASS` — `32` pages;
- marketing SEO/brand and responsive packs: `PASS`;
- docs/public-copy contract pack: `PASS` — `46` tests;
- shared guide registry: `PASS` — `46` guides, `46` detail records, visual
  coverage for every guide ID, `7` proactive fallback guides and `20` atlas
  screenshots on each web surface;
- platform documentation contract: `PASS` — `30` tests;
- client documentation contract and seed validation: `PASS`;
- `git diff --check`: `PASS` in both worktrees.

API/admin proof used an isolated Starlette 0.46 path; the repository
requirement now pins `starlette>=0.40,<0.47` because the machine-global
Starlette 1.3.1 is incompatible with installed FastAPI 0.115.11. The successful
pytest run ended with a known Windows temporary-directory cleanup warning; its
test exit code was zero.

The focused LDPlayer ADB retest passed on a freshly installed debug APK:
manual trusted Wi-Fi add no longer raises the Flutter assertion, locked
location rows expose an explanation and ignore selection while favorites still
work, switch semantics are singular, and theme selection exposes
`selected=true`. Package `space.pokrov.pokrov_android_shell`, debug version
`1.0.0-beta.4` (`4`), ran on LDPlayer 14 instance `0`; only this app was
launched. The emulator was shut down, ADB was returned to its prior closed
state and test data was removed after the check.

Live connection on this exact run is `BLOCKED_BY_ACCESS`: the existing emulator
device identity was already registered by the backend, which requested a
session refresh or access restore. Signed release, physical-device, clean-VM,
store and origin proof remain `MANUAL_OWNER_TEST`; videos remain
`PLANNED_NOT_RECORDED`. Local proof never substitutes for these MUST-15 owner
gates. Full reproduction, motion evidence and limitations:
[QA-RECHECK-2026-07-23.md](QA-RECHECK-2026-07-23.md).
