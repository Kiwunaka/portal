# Plans And Decisions Closure Audit

Date: 2026-06-06
Last updated: 2026-06-07
Status: repo-side closure / manual-gate boundary

## Scope

This audit reconciles the active `POKROV-app/main` decision set, implementation
plans, and the root `webapp` cabinet reset after the latest owner request:
close everything that can be closed in code/docs, leaving only local
exact-artifact checks, owner/operator live checks, signing, store/trust, and
similar external gates.

## Audited Active Inputs

Active client decisions:

- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/decisions/2026-06-03-client-ux-account-rewards-master-brief.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/decisions/2026-06-03-client-best-mvp-consilium.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/decisions/2026-06-03-client-chat-responsive-warp-motion-review.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/decisions/2026-06-03-hiddify-karing-happ-client-base-review.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/decisions/2026-06-03-hiddify-core-warp-status.md`

Active client implementation plans:

- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/implementation/2026-06-04-decisions-implementation-map.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/implementation/2026-06-05-p6-overload-correction-plan.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/implementation/client-release-backlog.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/superpowers/plans/2026-06-05-premium-client-ai-assistant-architecture.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/operations/2026-06-05-final-beta-closure-except-manual-tests-signing.md`

Active root WebApp plan:

- `C:/Users/kiwun/Documents/ai/VPN/docs/design/2026-06-05-webapp-cabinet-ux-reset-plan.md`
- `C:/Users/kiwun/Documents/ai/VPN/docs/design/2026-06-06-web-admin-site-density-plan.md`

Explicitly ignored archive inputs per owner direction:

- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/decisions/2026-06-02-karing-base-reopen.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/decisions/2026-04-18-karing-vs-clean-room-gate.md`

## Repo-Side Closure

Closed for the current `1.0.0-beta` repo scope:

- client P0-P6 implementation map through guarded WARP beta, selected-apps,
  support polling lifecycle, rewards flags, responsive matrix, and premium
  motion foundation;
- Premium Client AI Assistant architecture plan phases 0-6;
- P6 overload correction plan phases P0-P3;
- GitHub prerelease and checksum handoff evidence recorded in the client repo;
- Android build-tool warning closure recorded in client readiness docs;
- root WebApp cabinet reset through visible IA
  `Главная / Доступ / Помощь / Аккаунт`;
- WebApp task/detail routes for devices, statistics, downloads, redeem,
  checkout continuation, support thread, and legal docs converted to compact
  row-first continuation surfaces;
- root canonical docs updated so the cabinet IA no longer points at the old
  five-item English first layer.
- web/admin/site density pass closed through P3 cleanup: marketing homepage and
  reusable SEO landings are compacted, admin shell uses token-backed density
  helpers, marketing route ownership is documented, and public logo rendering is
  centralized through one `next/image` component.

## Remaining External Gates

These remain intentionally open and must not be treated as repo-side blockers:

- owner/operator exact-artifact install checks on Android and Windows;
- Android physical release-build localhost/control-surface raw audit
  replacement evidence, if the owner wants to replace the retained operator
  attestation;
- real app-session smoke for start-trial, managed profile, connect/disconnect,
  dashboard, cabinet handoff, redeem, checkout, Telegram bonus, and support;
- Android/Windows DNS split, leak, route-mode, reconnect/recovery, and
  production WARP runtime proof;
- production Android signing, Play/store readiness, trusted Windows signing,
  SmartScreen reputation, Microsoft Store/WinGet, and Apple signing/store work;
- RU-origin probe evidence only when a public RU-origin readiness claim is
  needed;
- live deploy/runtime `APP_*` sync proof after any future artifact URL change.

## Safe Claim Boundary

Safe now:

- `POKROV-app/main` is the active Android + Windows client repo.
- `1.0.0-beta` repo-side product contour is implemented for outside-store beta.
- WebApp personal cabinet is compact, continuation-first, and aligned to the
  current four-item visible IA.
- Public marketing and admin density guardrails are repo-side closed through
  the `2026-06-07` P3 cleanup pass.
- WARP/enhanced protection is implemented as a guarded beta feature with
  backend lifecycle and redaction contracts.

Not safe until external gates pass:

- stable `1.0.0`;
- store availability;
- trusted Windows signing;
- raw Android audit proof;
- production WARP;
- RU-origin readiness;
- anonymous public download proof from the current private GitHub repository.
