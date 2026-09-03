# WO-013FH — candidate.25 signed supply and Gate F

Status: `EXACT_CANDIDATE25_GATE_F_BLOCKED_5_PASS_14_NON_PASS_0_FAIL`

Observed: `2026-09-03T02:31:00Z`–`2026-09-03T03:05:00Z`

Production/public mutation: `NONE`

## Outcome

Bind the successor platform correction from WO-013FG to private exact
candidate.25, validate its trusted release-index signature and regenerate
Gate F. The candidate uses platform `883cd1038a087fbf9f570cffcbfdfd5f5197ffd4`,
client `54259b0f84e16c58e2d1f5f04b369af4fd0834b2`, Core
`cd8f0f4169d570d693992a959d81d17c2c44884d` and signed release-index source
`18d9cb4c5541481c5e60713376904f962ec19a7c`.

Candidate.25 deliberately reuses the six exact build-4053 client artifacts
from candidate.24 because the only source change is the platform development
lock. The strict-v2 handoff, SBOM, provenance and offline validation bind that
reuse explicitly rather than claiming a new client byte build.

```text
BLOCKED
required=19
pass=5
non_pass=14
fail=0
validation_errors=0
candidate_validation=PASS
gate_g_authorized=false
```

`supply_chain_signature_sbom_provenance`, `release_docs_manifest_binding`,
`current_origin`, `brain_origin` and `hosted_required_checks` are `PASS`. The
fourteen remaining rows retain their exact `MANUAL_OWNER_TEST`, `NOT_RUN`,
`MISSING` or `SKIPPED_BY_OWNER` states. There is no candidate.25 runtime
failure, so the decision is `BLOCKED`, not `NO_GO`.

## Signed private supply

| Item | Identity |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.25`, app `1.2.0+4053` |
| Artifact set | `6b08f281571db3eee46ba13a043630aac4f76989bc74b18b6f92edfcb3dcfdd5` |
| SBOM | `f6d8ec5b7ab999bd8d7ca648aed4ff640543fef11c8176781922e82482779d70` |
| Provenance | `4f106a2ed15b37457816460d42db5706f79c377bf7671bb9ba58bd93cf414f0d` |
| Strict handoff | `b65b9e7ec16b85c55235f4f5b9481507e13dccd07f0ba2c0a74202d661702908` |
| Supply validation | `2eba8a01829d7fac5a505a9d7328fd7def936f944d60763fe18386acf9321996` |
| Signed manifest | `7161bae715d590fac0623561d147e4d9ee069da14a5e3645001cc4c39aa329b6` |
| Detached signature | `f83cf5acbfa8aa55a45a73f03a2f4e829661215a788f68e8b7b36764b1ff3d14` |
| Signing receipt | `2c18b318fb538eeec69a9226f4eacf5a19066b0c1d479d26a7b6a13325cdd2cf` |
| Signing key | `pokrov-release-2026-01` |
| Windows setup | size `29139238`, SHA-256 `ffc9b07c59f75372b48c5c1e94551d6d9af710ac0287cd1352142b0964707fb3` |
| Windows bundle manifest | `344b842cd0222aa642115c00f42810bf922492394435271d43d9837169f187c0`, `11/11 PASS` |

The main-only signer run `33709201344` succeeds. Its downloadable signed
artifact has id `9876331429` and service digest
`sha256:7dc9beb122c0315017835cad6877513754b9acc5bd0120d369dd16f2602e61bb`.
All ten attached hosted source/signing jobs are completed `SUCCESS`.

## Fresh headless CLI rehearsal

The full Windows release builder is replayed headlessly from the exact client
and Core source with the exact merged platform supplied as the shared-facts
root. The first invocation exits before building because that explicit root
was absent; no candidate or tracked source changes. The corrected invocation
exits `0` and passes platform/client/Core parity, source contracts, hygiene,
client widgets `413/413`, runtime engine `72 PASS` with one expected optional
real-DLL skip, Windows tests/analyze/release/Inno, Android shell tests and both
Android Gradle flavors.

The rehearsal setup is size `29138850`, SHA-256
`4881ba05e2700be5245332cd4f7de94e7354808b44dd0eabc400a39f9ef293f7`.
It is valid headless build-path evidence, not candidate bytes: the Inno output
differs from the immutable candidate.25 setup and is never substituted.

The exact candidate.25 Windows setup is copied to the isolated Windows 11 VM
through Guest Control. Guest size/hash and product metadata match the host;
Authenticode is `NotSigned` under the owner-approved SmartScreen exception.
The guest session is not elevated, so installation and live Windows runtime
remain `NOT_RUN`. No mouse, keyboard, screen, VPN runtime or foreground UI is
used. The temporary guest directories are removed after verification.

## Read-only origin refresh

Fresh candidate.25 Brain semantic parity passes `197/197`, readiness `23/23`,
subscription stability `5/5` and enabled delivery `7/7` in three samples.
Proxy-disabled current-origin public health and catalog probes pass 50-sample
p95 budgets at `48.8176 ms` and `51.3052 ms`. These bounded PASS rows do not
replace authenticated client egress or general RU-origin evidence.

## Remaining release boundary

Installed Windows lifecycle/network/uninstall/AWG/Smart-DNS, LDPlayer and
physical Android, authenticated client egress, general RU origin, guarded
runtime rollback, provider/PostgreSQL/outbox, authenticated Operator flow,
legal/commercial approval, comparable device/browser performance and final
live no-open-P0/false-green/privacy attestation remain open. Trusted Windows
signing and paid branch protection remain owner-skipped for the direct beta.

No tag, GitHub Release, public asset, Store submission, stable pointer, deploy
or production mutation occurs. Gate G remains unauthorized.

## Evidence digests

| File | SHA-256 |
|---|---|
| `013FH-candidate25-signed-binding.json` | `28bc92dec9bcfd14d790fc3bdbaf57135578d11e3e277096a4b39c508809c4d6` |
| `013FH-candidate25-hosted-checks.json` | `ab6a7c1b6cbd1b5abe72f9fbb4ad0191dfb0fcc71fdd1e0ef0d6ee0ce1fec3c3` |
| `013FH-candidate25-current-brain-origin.json` | `5adab8e6fab13622e9659591d24111c11bc2ddcf2bbbb1492b47c94e2f552901` |
| `013FH-candidate25-gate-f-evidence.json` | `a68180ebc95844ecdd067d199ebfb245b08c1c1ef861febb7ffb20e0a192f367` |
| `013FH-candidate25-gate-f-input.json` | `bcefd14957e28028e0cfc3d537cd033c3f2a38e1c548f5072df6817fa25142e3` |
| `013FH-candidate25-gate-f-decision.json` | `f00ad87f512c82472a9b9bad358e8fd28608157062474b58edf210fc62aee6b1` |

`REL_GATE/GATE-F` remains `I3`; the 378-row completion-level distribution is
unchanged.
