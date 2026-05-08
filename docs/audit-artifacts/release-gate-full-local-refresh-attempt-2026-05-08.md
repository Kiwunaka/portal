# Full Local Gate Refresh Attempt

- Started: `2026-05-08 08:37:56 +03:00`
- Stopped: `2026-05-08 10:38:55 +03:00`
- Status: `TIMEOUT_NOT_PASS`
- Command: `python scripts\release_gate_check.py --output docs\audit-artifacts\release-gate-full-local-2026-05-08.md`

## Result

The command exceeded the 2-hour tool timeout and left a live `release_gate_check.py` process. That process was stopped manually with `Stop-Process -Id 56544 -Force`.

This attempt did **not** complete and should not be treated as a PASS. A later standard rerun did overwrite `docs/audit-artifacts/release-gate-full-local-2026-05-08.md` with the current PASS report generated at `2026-05-08 11:45:24`.

## Evidence Use

Do not treat this refresh attempt as a PASS.

Use the current standard full/default gate `docs/audit-artifacts/release-gate-full-local-2026-05-08.md` generated at `2026-05-08 11:45:24` plus the current brain-origin quick gate `docs/audit-artifacts/release-gate-brain-2026-05-08.md` generated at `2026-05-08 08:36:26` for the latest post-deploy state.
