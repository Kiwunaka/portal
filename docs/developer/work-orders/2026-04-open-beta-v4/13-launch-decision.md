# Launch Decision

Status: superseded GO for public beta as of 2026-05-15

Decision: release POKROV as a public Android + Windows beta outside app stores.

Reason: the previously blocked P0 gates now have current redacted evidence or an explicit owner-accepted limitation. Lava.top invoice/payment evidence, email auth and paid key delivery probes, runtime app-download smoke, GitHub APK/EXE reachability, brain-origin readiness, and local release gates are green. Android physical audit is operator-attested for this beta pass. RU-origin was explicitly skipped and must not be claimed publicly.

Allowed follow-up without changing this decision:

- keep Telegram channel launch copy prepared-only until the owner posts it;
- continue design polish, cabinet UX fixes, and client improvements after the beta opens;
- keep Windows unsigned-warning copy visible until trusted signing exists;
- keep RU-origin and app-store claims out of public copy until separate evidence exists.

Decision changes require a new dated launch-decision artifact.

| Gate | Current label | Evidence path |
| --- | --- | --- |
| Payment provider | PASS | `docs/audit-artifacts/paid-checkout-launch-evidence-brain-2026-05-15.json` |
| Runtime app download | PASS | `docs/audit-artifacts/brain-runtime-app-download-smoke-2026-05-15.json` |
| Android physical audit | OPERATOR_ATTESTED | owner attestation, 2026-05-15 |
| RU-origin probe | SKIPPED_BY_OPERATOR | `docs/audit-artifacts/ru-origin-skip-accepted-2026-05-15.md` |
| Brain-origin deploy readiness | PASS | `docs/audit-artifacts/release-gate-brain-2026-05-15.md` |
| Public artifact handoff | PASS | `docs/audit-artifacts/staged-client-apps-reachability-2026-05-15.md` |

Machine-readable decision: `docs/audit-artifacts/public-beta-launch-decision-2026-05-15.json`.
