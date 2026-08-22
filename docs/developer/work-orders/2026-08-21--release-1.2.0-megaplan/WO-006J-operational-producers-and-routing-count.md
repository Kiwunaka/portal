# WO-006J — Operational producers and Android routing count

Status: `COMPLETE_LOCAL_MIXED_INDEX`
Phase: `04`
Rows advanced: `OBS/OBS-029`, `OBS_DOD/DOD-08`, `OBS_PB/PB-02`,
`PB-10`, `PB-12`, `PB-13`, `FE_PR/PR-08`
Row strengthened without advancement: `OBS_PB/PB-14`
Promotion: `NOT_REQUESTED`

## Outcome

Close the remaining local producer gaps for auth, entitlement, performance and
encrypted support delivery, then add the one explicitly permitted remote
Android per-app routing fact: a bounded count with no package identity.

## Implemented contract

- `PokrovClientObservability` now emits closed start/finish events around auth,
  entitlement refresh, live performance sampling and encrypted support-bundle
  delivery. The active shell wires these producers to the existing operations;
  it does not create another analytics, auth, entitlement or support authority.
- Android selected-app changes emit one deduplicated
  `app.routing.selection.finished` event with integer
  `selected_app_count=0..128`. Windows never emits this projection. Package
  names and selected-app lists remain in the existing device-local routing
  state and managed-profile request.
- The release-health mirror removes every attribute except that count on the
  exact Android routing terminal event. Platform ingest independently enforces
  the same component/subsystem/stage/name/outcome/platform tuple and rejects
  missing, extra, identifying, non-integer and out-of-range values.
- `release_health_events` gains one nullable additive integer column for the
  count. SQLite and PostgreSQL migrations cover new and existing tables.
  Operator health exposes only `routing_count_events` and
  `selected_app_count_total`; it cannot reconstruct package identity.
- Event-schema SHA-256 is now
  `24ae72442f778d7f1334ae0a4bf4d774738e4de275707b29420ec733af65cc17`.
  Platform, client and Core snapshots agree; the schema and event ABI versions
  remain `1`, desktop ABI remains `2`.
- Support/recovery proof covers encrypted-only bundle retention, bounded
  polling lifecycle, safe reason codes and the disconnect/profile/verify repair
  stages required by `PR-08`.

## Index decisions

- `OBS/OBS-029`: `I0 -> I3`. Client projection, strict server ingest,
  persistence, migration and count-only operator aggregate are locally tested.
- `OBS_PB/PB-02`, `PB-10`, `PB-12`, `PB-13`: `I2 -> I3`. Their previously
  closed mappings now have concrete active producers and focused local proof.
- `FE_PR/PR-08`: `I0 -> I3`. Bundle, reason-code, polling and repair-stage
  paths all have focused widget/runtime proof.
- `OBS_DOD/DOD-08`: `I0 -> I1` only. The Windows service owns a bounded,
  sanitized journal slice, but Linux is explicitly not shipped in 1.2.0 and no
  Linux daemon slice exists. A current native rebuild was not credited because
  CMake is unavailable in this shell.
- `OBS_PB/PB-14` remains `I2`. Local aggregates and candidate-scoped known
  issues exist, but signed-manifest cohort binding and an exact health-breach
  promotion stop are not yet proven as one candidate path.

## Local proof

- Platform release-health, operator aggregate, inventory, schema, handoff and
  remote-apply regression: `118/118` PASS.
- Client observability producers: `3/3` PASS; contract snapshot: `3/3` PASS;
  runtime/privacy/timeline: `23/23` PASS.
- Support polling and encrypted outbox: `7/7` PASS; focused Protection Center
  repair paths: `4/4` PASS.
- App-shell library plus producer test analyzer: PASS with no issues.
- Platform/client/Core observability parity validators: PASS with the exact new
  event-schema hash and the unchanged 121-entry error catalog.

Machine evidence:
`evidence/006J-operational-producers-and-routing-count/006J-operational-producers-and-routing-count.json`.

## Evidence ceiling

This is local source/test evidence from dirty development worktrees. No frozen
revision, exact candidate, physical Android device, Windows clean host, Linux
daemon, production operator observation, signed-manifest health cohort,
deployment, publication or promotion was created. Local `I3` rows require
exact-candidate proof before `I4`; `DOD-08` remains only `I1`.
