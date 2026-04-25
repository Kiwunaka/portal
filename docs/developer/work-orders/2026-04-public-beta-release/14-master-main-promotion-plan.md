# Master/Main Promotion Plan

Status: blocked-until-release-gates-close

## Goal

Collapse the public-beta candidate back into the canonical promotion lanes without keeping long-lived worktrees or alias branches:

- platform/root repo -> `master` / `origin/master`
- active client repo -> `main` / `origin/main`

## Current State

- Platform candidate branch: `codex/public-beta-release-wave`
- Platform baseline branch: `master`
- Client candidate branch: `codex/beta-release-client`
- Client promotion branch: `main`
- Push/deploy status: blocked

## Why Not Merge Yet

Promotion is intentionally blocked because the release gate matrix still has real external blockers:

- Payment provider live order creation reaches FreeKassa but returns `Merchant not activated`.
- Runtime app-download smoke needs a live `TELEGRAM_INIT_DATA` token.
- Android physical-device release-build localhost/control-surface audit has no connected physical device / `ANDROID_AUDIT_SERIAL`.
- RU-origin probe from `mini` reaches POKROV canonical hosts and foreign nodes, but Telegram is unreachable from that origin.
- The root and client repositories both contain inherited dirty candidate changes, so staging all files would mix unrelated edits.

## Safe Promotion Sequence

1. Keep the feature worktrees as evidence workspaces until the blocked gates are closed.
2. On the platform repo, update local `master` from `origin/master`.
3. Apply only reviewed platform deltas from `codex/public-beta-release-wave` to `master`.
4. Run the root verification set from `13-final-git-promotion-record.md`.
5. Commit the reviewed platform delta on `master`.
6. Push `master` to `origin/master`.
7. Deploy platform/static surfaces only after the pushed commit is green.
8. On `POKROV-app`, update `main` from `origin/main`.
9. Apply only reviewed client deltas from `codex/beta-release-client` to `main`.
10. Re-run client tests/builds and the Android physical audit.
11. Commit and push reviewed client delta on `main`.
12. Remove the temporary worktrees and feature branches only after both canonical branches contain the reviewed commits and rollback evidence is retained.

## Commands To Use After Gates Close

Platform:

```powershell
git -C C:\Users\kiwun\Documents\ai\VPN switch master
git -C C:\Users\kiwun\Documents\ai\VPN fetch origin
git -C C:\Users\kiwun\Documents\ai\VPN pull --ff-only origin master
```

Client:

```powershell
git -C C:\Users\kiwun\Documents\ai\POKROV-app switch main
git -C C:\Users\kiwun\Documents\ai\POKROV-app fetch origin
git -C C:\Users\kiwun\Documents\ai\POKROV-app pull --ff-only origin main
```

## Do Not Do

- Do not `git reset --hard` either repository while inherited dirty work is still unresolved.
- Do not stage the whole worktree with `git add -A` until the dirty candidate wave is reviewed.
- Do not push/deploy the public beta while provider, token, Android physical audit, or RU Telegram reachability blockers remain open.
