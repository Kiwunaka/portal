# Local Worktree Cleanup - 2026-04-26

This note records the repository-facing result of the local cleanup that followed the public beta promotion.
It does not contain secret material or the contents of any local stash.

## Promoted Git Truth

- Platform repository: `C:\Users\kiwun\Documents\ai\VPN`
- Platform branch: `master`
- Platform remote: `origin/master`
- Platform promoted HEAD before this note: `39de3222300408295aea668a628e2df2fb852f38`
- Client repository: `C:\Users\kiwun\Documents\ai\POKROV-app`
- Client branch: `main`
- Client remote: `origin/main`
- Client promoted HEAD: `0231bd6968bec4881897e3e74548a96ed7e4b375`

## Cleanup Result

- The root platform checkout was reset to `origin/master`.
- The active client checkout was reset to `origin/main`.
- Temporary `codex/*` worktrees used for public beta integration were removed.
- Temporary local `codex/*` branches used for public beta integration were removed.
- After cleanup, the normal local checkouts were:
  - `VPN`: clean `master...origin/master`
  - `POKROV-app`: clean `main...origin/main`

## Local Stash Note

Before the root platform checkout was reset, the old dirty local root workspace was preserved in a machine-local git stash:

- stash message: `pre-cleanup root dirty wave before origin-master sync 2026-04-26`
- stash object recorded locally: `03d14434b4dcf1b8d17a98e7de4fd979f5799e66`

This stash is local operator safety evidence only. It is not a source of truth and should not be applied directly over current `master`.
If it ever needs review, inspect it first or restore it onto a separate recovery branch.

Recommended inspection commands:

```powershell
git stash list --date=local
git stash show --stat "stash@{0}"
git stash show --name-status "stash@{0}"
```

Recommended recovery command:

```powershell
git stash branch recover-root-dirty-wave-2026-04-26 "stash@{0}"
```

