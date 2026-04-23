# Legacy Bridge Retirement Summary

Last updated: 2026-04-23

`C:/Users/kiwun/Documents/ai/VPN/external/client-fork/app` was the retained bridge repo during the cutover period.

Retirement facts:

- active client canon moved to `C:/Users/kiwun/Documents/ai/POKROV-app`
- active release-gate, shared-facts sync, and release-handoff automation were repointed to `POKROV-app`
- retained bridge artifacts were mirrored into `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/`
- the bridge repo no longer appears in active must-read, promotion, or source-of-truth guidance
- use the archived bridge bundle lineage only for rollback forensics, evidence review, or checksum comparison

If a task still needs historical bridge evidence, prefer the mirrored bundle and versioned metadata under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/` instead of treating the old repo as a live workflow lane.
