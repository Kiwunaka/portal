# WO-013AQ — Privacy-bounded client release-health baseline

Date: `2026-08-28`

Status: `IMPLEMENTED_SOURCE_ONLY / RUNTIME_COHORT_NOT_DEPLOYED`

## Objective

Close the source-level `OBS-087` gap without exposing operator aggregates or
pretending that one account or one device represents a healthy cohort. Give an
authenticated client an exact-same-build weekly comparison only when the
server has a minimum anonymous cohort, and keep diagnostics local, optional and
fail-closed when that baseline is unavailable.

## Exact source

- platform implementation:
  `3e52b7314a82758ad11a68e991b5e9f4a8f48a71` on
  `codex/obs087-client-baseline`;
- client implementation:
  `44c9cca2503f5280d7a977b46aaebd849b3dee44` on
  `codex/obs087-client-baseline`;
- Core authority used by the final cross-repository seed validation:
  `f44dbe89d6b89954032a1a798c2209d8c0aff90d`.

These are private pre-candidate branches. They are not merged source, a signed
candidate, a deployed platform or a stable/public release.

## Platform implementation

The server derives a cohort only from the complete build scope already carried
by release-health events: app version, build number, channel, candidate label,
git revision, Core ABI, platform and architecture. The projection uses one UTC
week and refuses partial or unknown scope values.

An HMAC keyed by `RELEASE_HEALTH_COHORT_SECRET` maps one authenticated account
to one of `4096` buckets for that exact cohort and week. Only the following are
persisted:

- SHA-256 cohort fingerprint;
- UTC-week start;
- bucket index;
- capped overall and crash/connect/update event/failure counters;
- last update timestamp.

Account, Telegram, install, device, session and stable contributor hashes are
not persisted in the cohort table. Bucket collisions can only undercount the
cohort, so they cannot make the minimum appear satisfied early. One bucket is
capped at `64` overall events and `32` events per family per week.

The authenticated read endpoint returns only closed bands. It requires at least
`10` distinct occupied buckets, at least `30` overall events and `10` events
for an individual family. It never returns an exact contributor count, exact
event count, exact failure count or percentage. Missing or shorter-than-32-byte
privacy secret makes the baseline unavailable. Retention removes cohort rows
after `14` days.

Only newly accepted event IDs contribute to the cohort. Idempotent ingest
replays remain duplicates and cannot inflate the comparison. Existing operator
aggregates stay operator-only and are not reused as a client response.

## Client implementation

The client adds a strict band-only DTO/parser and an authenticated GET over the
existing app session. It does not create a trial, session or account and does
not persist the response. It rejects extra identity, count and bucket fields,
scope mismatches, exact-number additions and unknown enums.

Local diagnostics still refresh immediately and never wait for the network.
The release-health comparison is requested only after the user explicitly
refreshes diagnostics. It remains hidden on transport/auth/server/schema
failure; an undersized cohort shows only that the anonymous sample is
insufficient. No exact count or percentage is shown.

The full client regression exposed a separate release defect: support code
`PSD1` encoded build numbers in one byte and crashed for the real build `4046`.
Backward compatibility is retained for builds through `255`; new `PSD2`
support codes preserve complete larger build numbers.

## Verification

- platform focused baseline/ingest/retention/API suite: `57 passed`;
- platform app-first/auth/ticket/subscription regression: `154 passed` plus
  `8` subtests;
- observability schema and data-inventory validation: `PASS`;
- platform documentation/contract suite: `45 passed`;
- new standalone Python modules: Ruff `PASS`; all `11` changed Python files:
  AST parse `PASS`;
- client Flutter analysis: no issues;
- complete app-shell suite: `411/411`;
- focused parser/transport/widget suite: `18/18`;
- support-bundle regression including `PSD1`/`PSD2`: `15/15`;
- client documentation contract: `PASS`;
- final cross-repository seed validation against exact platform/client/Core
  heads above: `PASS`;
- platform/client diff checks and secret-like scans: `PASS`.

The monolithic composed `portal_bot/api.py` is intentionally not reported as a
standalone Ruff pass: its bootstrap-fragment structure has pre-existing import
and unused-symbol findings. Runtime API regressions above are the applicable
gate for this slice.

## Ledger decision

`OBS/OBS-087` advances `I1 -> I2` as `IMPLEMENTED_SOURCE_ONLY`. The minimum
cohort contract, privacy-bounded store, authenticated band-only projection,
strict client consumer and focused regressions exist in source.

It does not reach `I3` because the platform code and privacy secret are not
deployed, the client code is not installed as an exact bound candidate and no
real `k >= 10` same-build weekly cohort exists. A single physical phone cannot
prove this requirement. Distribution becomes `I4=4`, `I3=314`, `I2=21`,
`I1=38`, `I0=0`; `318/377` rows remain at or above `I3`, while `59/377`
remain below.

## Remaining proof

1. Merge only after required hosted checks can actually start and pass.
2. Configure a generated 32-byte-or-longer secret in the authorized runtime;
   never copy it into Git or evidence.
3. Deploy the exact platform source through the guarded deployment path, then
   prove migrations, ingest replay resistance, retention and authenticated GET
   readback without recording user identity.
4. Build and bind an exact signed client candidate to that platform source.
5. Accumulate a real same-build weekly `k >= 10` cohort and retain only redacted
   band-level evidence.
6. Verify on Android and Windows that local diagnostics never wait on the
   baseline and unavailable/undersized cohorts remain truthful.

No phone mutation, merge, deployment, candidate creation, secret change,
production read, publication or promotion occurred in this work order.
