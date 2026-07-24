# WO-001 Protection Core

## Metadata

| Field | Value |
| --- | --- |
| WO id | `WO-001-protection-core` |
| Title | Проверяемый центр защиты и восстановление соединения |
| Ceremony | `bounded_wo` |
| WO status | `implemented_local` |
| Orchestrator | Codex primary agent |
| Repository lane | `mixed` |
| Working branch or worktree | platform and active-client `codex/selected-vpn-features-ios-ui` worktrees from the wave index |
| Intended promotion state | Reviewable commits for platform `master` and active client `main`; integration remains owner-controlled |
| Created / updated | 2026-07-23 |

## Goal

На Android/Windows пользователь открывает спокойный iOS-like центр защиты, видит честные отдельные состояния tunnel, DNS, internet/HTTPS and route ownership, может одной кнопкой выполнить ограниченный staged repair и видит последние локальные события защиты. Локации показывают измеренный ping/load/health с freshness, favorites и recent.

## Non-Goals

- Не утверждать внешний IP, отсутствие утечек или production-grade route proof без соответствующего измерения.
- Не менять runtime core, WARP architecture, signing, release artifacts или публичные download URLs.
- Не включать purpose/domain/DNS-policy controls из W2 в этом WO.

## Write Scope

- `C:/Users/kiwun/Documents/ai/POKROV-app/.worktrees/selected-vpn-features-ios-ui/packages/app_shell/`
- focused client tests under the same package
- `C:/Users/kiwun/Documents/ai/POKROV-app/.worktrees/selected-vpn-features-ios-ui/docs/product/client-product-contract.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/.worktrees/selected-vpn-features-ios-ui/docs/design/2026-06-13-pokrov-product-ui-direction.md`
- platform client-state API/tests only if an existing response must expose freshness or incident metadata
- matching cabinet read-only surfaces and focused E2E/unit tests

Collision gate result: both new worktrees were clean and dedicated at 2026-07-23 creation; dirty neighboring worktrees are no-touch.

## No-Touch Scope

- `artifacts/releases/**`, production signing material, provider secrets and live production state
- runtime core replacement, low-level tunnel/WARP lifecycle redesign, deploy/push/promotion
- other platform/client worktrees and their uncommitted files

## Authority Anchors

| Anchor | Why authoritative for this outcome |
| --- | --- |
| platform router `Active client repository`, `Web cabinet`, `Backend/API/bots` rows | lane, checks and docs impact |
| client `docs/product/client-product-contract.md` | intended client behavior |
| client `DESIGN.md` and current product UI direction | `pokrov-clear` iOS-like visual contract |
| `RuntimeSnapshot`, Android runtime state and current connection UI | implemented host truth and available diagnostics |
| `/api/client/locations`, `/api/client/notifications` | current server-owned location/inbox data |

## Acceptance Oracle

- Authoritative boundary: client widget/runtime behavior plus existing authenticated platform API.
- Success observation: focused tests prove independent status rows, bounded repair order/idempotency, no green healthy state on degraded diagnostics, persistent favorites/recent, measured metrics/freshness labels and retained last-known content during an API failure.
- Negative cases: no raw config/token/host/IP exposure; no endless retry; repair cannot run concurrently; unknown measurements display as unknown instead of fabricated values.
- Proof mechanism: Flutter unit/widget tests, focused platform tests, seed validation, then LDPlayer launch/connect/disconnect/failure smoke with UI-tree-derived taps and screenshots.
- Limitations: LDPlayer is local preflight; production signing, physical-device, clean-VM, DNS leak and RU-origin gates remain manual.
- Triggered proof blocks: runtime risk, MREP, validation attribution and manual gates.

## Docs Impact

| Canonical owner | Required change | Closure evidence |
| --- | --- | --- |
| client product contract | protection center, repair semantics, metrics/favorites/history behavior | focused diff and tests |
| client design direction | protection-center component/state language | focused diff and screenshot |
| platform app-first/API contract | only if response fields change | API schema/test diff |
| cabinet README/user guide | matching read-only state/help behavior | build/E2E and docs diff |

## Validation And Evidence

| Check | Command or manual gate | Oracle reached | Required target scope |
| --- | --- | --- | --- |
| client static analysis | `flutter analyze` in `packages/app_shell` | yes, source shape | local |
| focused client behavior | `flutter test` in `packages/app_shell` | yes, widget/service semantics | local |
| Android host regression | focused `scripts/run-tests.ps1`/Gradle tests when host code changes | yes for changed host contract | local |
| platform API | focused pytest for changed client endpoints | yes for schema/authorization | local |
| cabinet | `npm.cmd run build`, lint and focused E2E | yes for browser surface | local |
| Android runtime smoke | LDPlayer via adb/UI tree/screenshots/logcat | partial runtime oracle | local emulator |
| exact release/physical device | owner gate | no in this WO | `MANUAL_OWNER_TEST` |

## Status And Handoff

- Current WO status: `implemented_local`
- Result delivered: protection checks, bounded repair, persisted cache/favorites/recents/history/shortcuts, measured location freshness and matching cabinet explanation
- Open findings: live-account connect/disconnect, exact signed-candidate and
  physical-device/store/origin owner gates
- Blockers and accepted risks: external route/leak truth cannot be inferred from local host fields; emulator evidence is not signing or physical-device proof
- Conditional `FLOW_STATE` v2: not triggered
- Lane and commit state: two dedicated feature branches; implementation uncommitted and unpushed
- Deploy and promotion state: `NOT_REQUESTED`
- Next action: owner reviews the retained evidence and both worktree diffs before
  any commit/promotion
