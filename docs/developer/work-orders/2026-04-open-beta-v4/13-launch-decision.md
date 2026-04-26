# Launch Decision

Status: final for this branch as of 2026-04-26

Decision: Do not release publicly.

Reason: P0 gates remain blocked by missing external proof: Lava.top provider evidence, runtime download smoke with env-only Telegram init data, Android physical release-build audit, public artifact handoff URLs, and RU-origin probe evidence.

Allowed follow-up without changing this decision:

- merge documentation and release-gate hardening;
- run local platform, frontend, and client preflight gates;
- prepare gated beta support copy;
- keep checkout and direct public downloads unavailable unless the corresponding proof is attached.

Decision may be changed only after the evidence table below is updated.

| Gate | Current label | Evidence path |
| --- | --- | --- |
| Payment provider | blocked by missing access | `evidence/provider/` |
| Runtime app download | blocked by missing access | `evidence/logs/` |
| Android physical audit | blocked by missing access | `evidence/android/` |
| RU-origin probe | blocked by missing access | `evidence/ru-origin/` |
| Brain-origin deploy readiness | blocked by missing access | `evidence/logs/` |
| Public artifact handoff | blocked by missing access | client `artifacts/releases/` |
