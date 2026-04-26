# WO-010 Release Captain, Docs, Launch

Status: pending research
Owner: W10

## Scope

- Final launch decision.
- User guide, release notes, launch copy, support macros, known issues, post-release monitoring.
- Final gate record.

## Acceptance

- `13-launch-decision.md` contains exactly one final decision from the superplan matrix.
- `14-final-git-promotion-record.md` records platform and client repo status separately.
- Support macros and launch copy do not overclaim.
- All P0 gates are green or the release scope is downgraded honestly.

## Verification

```powershell
python scripts/check-links.py
python scripts/release_gate_check.py --quick
```
