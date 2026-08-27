# WO-013AH — Exact candidate.3 current-origin release gate

Status: `EXACT_CANDIDATE_CURRENT_ORIGIN_LOCAL_AGGREGATE_PASS`
Phase: `11`
Candidate: `pokrov-1.2.0-candidate.3`
Rows: `REL/PERF-001`, `REL_GATE/GATE-E`, `REL_DOD/DOD-13`, `FRKN_PLAN/W9-02`
Deployment: `NOT_REQUIRED_NOT_RUN`
Recorded: `2026-08-27`

## Goal

Retain one exact-candidate current-origin aggregate without changing signed
candidate bytes, production runtime, entitlement, public assets or the stable
pointer. The aggregate combines the default local release gate with clean
source-bound health/catalog latency. Brain-origin remains owned by WO-013AG;
RU-origin and authenticated client egress remain separate and unproved.

The owner removed the physical phone and directed Android work to LDPlayer
only. The installed exact APK has no active entitlement, so emulator catalog,
TUN, DNS and owned egress remain `BLOCKED_BY_ACCESS`. No temporary commercial
grant was created.

## Exact target and reviewed harness

| Component | Exact source |
|---|---|
| Signed candidate platform target | `eafaca3e64c0619dea7f58fc9c430682b4520559` |
| Signed candidate client target | `ac22825e857a313c9e4eba61030eb548d6346ead` |
| Signed candidate Core target | `344b317a7a09eca7943a93866b193553538bd8f6` |
| Signed candidate release index | `6a1afa95fe52da2d559ba7b1da88715cd0344bb2` |
| Post-candidate release harness | `c9b34276fd42b4ef4a670caf4a630a77232271cc` |

Manifest/signature/receipt SHA-256 remain
`a2752b6a3b95faacf13a68edb708c560966a0f5eb8727e109d7f1603fdc81090`,
`926f0b4667a58ba9cc5ace5c4e6c3c8129d1ec3d4d449b3f0831a8c527cd7121`
and `fb4d0d5dd272b8d3e7ea2303e2ffa93e332f54ac3e92f245400decc6c06e4b53`.
WO-013AE remains the candidate identity authority.

The signed platform checkout is immutable. A later reviewed harness targets
it through `POKROV_PLATFORM_ROOT`; evidence retains both commits. Harness
changes are not described as changes to candidate bytes.

## Fail-first harness correction

The first exact-source quick run is retained as `FAIL`, SHA-256
`4f8ae32d9a5ad9c0f03742e6af836cb3d34ab9e214112db066d85ff57757b6e3`.
Product code, production builds and portal Flutter tests passed, but three
harness/input defects prevented an aggregate pass:

- the invocation supplied the wrong Core override name; the strict wrapper
  requires `POKROV_CORE_ROOT`;
- platform `client_security_smoke.py` still pinned retired Core `v1.0.3`
  bytes instead of the active exact `v1.1.0` seed bytes;
- WebApp E2E ran from a source directory without lockfile-installed
  dependencies after production builds had used isolated copies.

Harness commit `c9b3427...` aligns the static Core pin and pre-candidate seed
provenance, runs build and E2E commands in independent `npm ci` copies and
allows a reviewed harness to target an immutable platform checkout. Focused
verification passes `51` tests plus `21` subtests. The strict exact
client/Core contract and static client smoke also pass independently.

## Current-origin result

| Slice | Result | Exact observation | Private raw SHA-256 |
|---|---|---|---|
| Quick release gate | `PASS` | `12/12` commands, including strict client/Core, portal Flutter, three production builds and Playwright `88 passed` | `e49949bee41c685c83fe7ac570d2702cbca69a78768b1fa3e3a3cff261111a68` |
| Default release gate | `PASS` | `13/13` commands; release pytest `675 passed + 38 subtests`, admin/auth `96 passed + 8 subtests`, full Flutter, production builds and Playwright `88 passed` | `5bcbcb8cbfe69c9249257d7c571e8e47a94c882c9afc5a86872fb0334874e2a8` |
| Health latency | `PASS` | source-bound `Ethernet 2`, proxy discovery disabled, `50` samples after `5` warmups, p95 `42.5337 ms <= 100 ms` | `5c458195a4188bb0573304c7a9ae672f847c7f232893be60c73fc3a0b819c2bc` |
| Public catalog latency | `PASS` | same connection policy, `50` samples after `5` warmups, p95 `43.3626 ms <= 200 ms` | `23687a05744f84d00cd215c7a912e05149dc2f053cb372fa1289ec4530efb074` |

The latency collector binds the physical interface's preferred RFC1918 source
address and disables proxy discovery, so ambient `tun0` does not define the
evidence method. The raw local files remain under ignored `ops-local/`; the
tracked gate summaries retain no literal source address.

This proves the exact candidate platform/client/Core source tuple passes the
current-origin local default release aggregate and controlled public API
performance budgets. It does not prove an installed client's authenticated
VPN egress, Windows live TUN/DNS, LDPlayer catalog/TUN/DNS, physical Android,
Brain-origin (separate WO-013AG), RU-origin, provider, Operator or public/stable
promotion.

## Hosted check boundary

Platform PR `#48` binds harness head `c9b3427...`. GitHub created Guardrails
run `33041906127` / check `98417162613` and Release v2 run `33041906160` /
check `98417162629`, but started neither job because the repository owner's
account billing/spending limit blocked Actions. Both are recorded as
`BLOCKED_BY_ACCESS_GITHUB_BILLING`, not test `FAIL` and not `PASS`.

`OWNER_SOLO_EXCEPTION` waives the unavailable second reviewer only. It does
not waive required successful GitHub App checks, so PR `#48` is intentionally
not merged while this access block remains.

## Mutation and ledger decision

No deploy, restart, route/pointer change, entitlement grant, payment action,
public asset publication or stable promotion occurred.

No ledger row advances. `REL/PERF-001`, `REL_GATE/GATE-E` and
`REL_DOD/DOD-13` gain exact-candidate current-origin evidence at their existing
levels. `FRKN_PLAN/W9-02` remains `I1`: exact current-origin and Brain-origin
are now retained separately, but an authorized distinct RU-origin result is
still absent. Distribution remains `I4=4`, `I3=308`, `I2=15`, `I1=38`,
`I0=12`; `312` rows are at or above `I3`, `65` remain below, and the pending
stage split remains `0/30/14/21`.

## Retained evidence

- `evidence/013AH-exact-candidate-current-origin/013AH-current-origin-quick.json`
- `evidence/013AH-exact-candidate-current-origin/013AH-current-origin-full.json`
- `evidence/013AH-exact-candidate-current-origin/013AH-health-gate.json`
- `evidence/013AH-exact-candidate-current-origin/013AH-catalog-gate.json`
- `evidence/013AH-exact-candidate-current-origin/013AH-exact-candidate-current-origin.json`

## Next action

Restore GitHub Actions billing access and require successful app-bound checks
before merging PR `#48`. Separately obtain an explicitly authorized distinct
RU-origin probe and a valid owned LDPlayer entitlement before device network
tests. Continue the Windows live TUN/DNS/egress/connected-rollback matrix.
Public `v1.2.0` and stable promotion remain prohibited.
