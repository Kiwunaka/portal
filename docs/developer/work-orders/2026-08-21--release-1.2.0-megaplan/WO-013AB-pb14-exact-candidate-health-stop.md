# WO-013AB — PB-14 exact-candidate health stop and rollback request

Status: `COMPLETE_LOCAL_EXACT_CANDIDATE_CONTROL`
Phase: `11`
Ledger row advanced: `OBS_PB/PB-14 I2 -> I3`
Deployment: `NOT_REQUIRED`
Public promotion: `NOT_AUTHORIZED`

## Outcome

Bind the already retained signed candidate manifest to the real release-health
and guarded rollout services, then prove locally that one candidate-scoped
health regression stops observation close and that a guarded rollback request
drives candidate distribution to zero.

This closes the local PB-14 control gap. It does not claim a production cohort,
public candidate, external artifact switch, stable-pointer rollback or
post-promotion health.

## Exact candidate binding

- release label: `pokrov-1.2.0-candidate.1`;
- signed manifest SHA-256:
  `84695f6e318814bc2d1e9de1c9adc3aa4277015d551c5462b197664e574c28d6`;
- detached signature SHA-256:
  `718cc5b8033d1f48d3dcb236561db0c5218b05d9581f472f232dc4f44e3adb56`;
- manifest-bound release-index revision:
  `c1d617093692b05d2a12ae8ad8394e5570b0df8a`;
- client revision:
  `a74d2aea5aed62f5c31d3a0bbc258e408cebe3bd`;
- exact Android x86_64 APK SHA-256:
  `7d7a22b23a33811326c452fdd23d19bbb02aae0b3f6bd74a6753e38f222675ed`;
- operational candidate descriptor ID:
  `d65315ace9cb1f79da880532cb3fdb11bb21dd7cfa1eef691af058e8178f0aa9`.

`scripts/release_1_2_pb14_candidate_gate.py` reads the retained manifest,
signature, receipt and 013Y evidence. It rechecks their sizes and hashes,
loads `trusted/release-signing-keys.json` from the exact release-index Git
object named by the manifest and independently verifies the detached Ed25519
signature with active key `pokrov-release-2026-01`.

## Isolated control

The gate creates a temporary SQLite database and uses the production
`ReleaseCandidate`, `ReleaseHealthEvent`, release-rollout registry and guarded
Action Intent services. The database is destroyed after the run.

The local control fixture:

1. stages the exact signed candidate at 10 percent with zero tolerated update
   regressions and an elapsed observation window;
2. retains a clearly fixture-only `1.1.6` rollback state;
3. inserts one identity-free `update.failed` / `UPD-004` operational event for
   Android build `4030`, architecture `x86_64`;
4. proves `release.observation.close` fails with
   `release_health_gate_failed` and preserves the staged state;
5. executes the real L3 `release.rollout.rollback` Action Intent;
6. proves the exact candidate becomes `rollback_requested` with rollout `0`,
   the retained rollback state becomes `current` with rollout `100`, and the
   public policy returns zero for the candidate configuration.

The action result deliberately says
`external_artifact_switch=NOT_PERFORMED`. That is fail-closed control-plane
proof, not evidence that a public asset or stable pointer was switched.

## Verification

- focused regression:
  `python -B -m pytest -p no:cacheprovider tests/test_release_1_2_pb14_candidate_gate.py -q`
  -> `3 passed`;
- exact gate:
  `python -B scripts/release_1_2_pb14_candidate_gate.py --release-index-root C:/Users/kiwun/Documents/ai/pokrov-release-index --output <013AB evidence>`
  -> `PASS_LOCAL_EXACT_CANDIDATE_HEALTH_STOP_AND_ROLLBACK_REQUEST`;
- signature verification: `PASS`, Ed25519 public-key SHA-256
  `651d1bcfbedecc4e50d21f3ad3bf3cc990a6cfc97ad355f0e0e76972b8ba8024`;
- retained evidence:
  `evidence/013AB-pb14-exact-candidate-health-stop/013AB-pb14-exact-candidate-health-stop.json`,
  2636 bytes, SHA-256
  `106c0b7a6442c2c453ebfe792d37fd0f6a57d4fd347be94d7c8ac18a2c0d7eb0`.

## Ledger decision

`OBS_PB/PB-14` advances from `I2` to `I3`. The row now has exact signed
candidate identity, a candidate-scoped operational health breach, a retained
promotion-stop result and guarded rollback-request proof through the real local
services.

No row reaches `I4`: a real candidate cohort, deployed ingest/readback,
external artifact rollback completion and post-promotion observation remain
absent. Distribution becomes `I4=1`, `I3=310`, `I2=15`, `I1=37`, `I0=14`;
311 rows are at or above `I3`, 66 remain below `I3`, and the pending stage split
becomes `0/31/14/21`.
