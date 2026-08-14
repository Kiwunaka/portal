# WO-003 — Public Release Contract And Direct Downloads

Status: `COMPLETE`

## Outcome

Официальные Android/Windows-файлы доступны анонимно с точными version, variant,
size, SHA-256 и approved URL; ни один public CTA не откатывается на login wall.

## Design Boundary

- создать bounded public release projection, а не раскрывать authenticated
  `/api/client/apps` или внутреннюю release/admin metadata;
- сервер возвращает только опубликованные allowlisted assets текущего handoff;
- marketing, bot and cabinet use one resolver/contract;
- fail-closed fallback points to an exact verified public release asset or a
  clear temporary-unavailable state, never to `/downloads/` behind auth.

## Acceptance Scenarios

1. Anonymous Android ARM64, ARMv7, universal and Windows links resolve and
   hashes match the current release handoff.
2. Missing runtime configuration cannot silently create an auth hop.
3. Unknown asset names, hosts, draft releases or mismatched hashes are absent.
4. Platform-aware primary CTA chooses Android only from reliable client-side
   platform evidence; Windows and explicit chooser remain reachable.
5. Bot continues to expose direct files before ToS; manual configuration stays
   recovery-only.

## Checks

API contract tests, public anonymous requests, link/release guards, marketing
build/responsive checks, bot menu checks and exact downloaded hash evidence.

## Completion Evidence — 2026-08-14

- `/api/client/apps` and anonymous `/api/public/client-apps` share one runtime
  response builder; the public projection strips mirrors and rejects any asset
  outside the exact versioned POKROV GitHub filenames, SHA-256 and positive
  byte size contract.
- `/install/` requests that anonymous projection without credentials. If both
  runtime and validated build-time values are missing, Android/Windows actions
  are disabled with an explicit unavailable state; login is never substituted.
- Existing Telegram Android choice remains direct-file-first with ARM64,
  ARMv7, universal and manual recovery branches. No payment/account mutation
  was used during Browser inspection.
- Focused API and brain-smoke tests: `11 passed`; marketing lint, production
  build, SEO and responsive checks: `PASS`; `git diff --check`: `PASS`.
- Current-origin deployment and exact post-deploy HTTP/hash proof remain owned
  by WO-011; this local completion is not a production-deploy claim.
