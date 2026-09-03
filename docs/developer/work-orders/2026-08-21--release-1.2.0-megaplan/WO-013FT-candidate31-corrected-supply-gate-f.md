# WO-013FT — candidate.31 corrected supply and Gate F

Status: `EXACT_CANDIDATE31_SIGNED_SUPPLY_PASS_GATE_F_BLOCKED_2_PASS_17_NON_PASS_0_FAIL`

Observed: `2026-09-03T16:53:42Z`–`2026-09-03T17:05:41Z`

Production/public mutation: `NONE`

## Outcome

Candidate.31 replaces candidate.30 as the current private signed candidate.
It reuses the exact six application files whose hashes and bounded CLI/Windows
evidence were already retained, but it does not reuse candidate.30's rejected
SBOM, provenance or handoff. All candidate-bound supply metadata is regenerated
from the exact current source tuple and passes the strict offline validator
before signing.

```text
BLOCKED
required=19
pass=2
non_pass=17
fail=0
validation_errors=0
candidate_validation=PASS
gate_g_authorized=false
```

## Exact candidate boundary

| Item | Identity |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.31`, app `1.2.0+4053` |
| Operational id | `4ee73886c1a285526baf3b666d5845b426754d8bee9f48365d1550a6ece1dd79` |
| Platform | `84837ce68a028f0c81580a5f1beefddba584de6d` |
| Client | `7e3e771fe36333a75244cbfd828c60beb84c7ff1` |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release index | `6de47f0320c9262a5bd2d454f3edb83d557f33a4` |
| Manifest | `dd4e99166ac3ec2c566e7d44ee93324f15ae7b3b92df6b35ff35de7053691f9a` |
| Signature | `959328f891a5dfa5c7c5c3f1cf2463b77137d5a7ca0812bab0b746e0a9c5c01a` |
| Receipt | `8e47f3e9f298aa8e67c5d07ff5ad2be976f09091863aa42cd49c3e0ff8e8ff89` |
| Hosted signer | Run `33781982978`, artifact `9903927218` |

## Corrected supply binding

The strict validator passes all six artifact descriptors and all eleven
Windows runtime files. The exact metadata identities are:

```text
artifact_set=dce1c4e43aa1729e87f6620da9f655482dd3a6113bb67006e319c090e0b02b9e
sbom=e5d9eb85bacb778e225d5d909832cd3e7d42c9d19fa1ebc44092456ec9da56a5
provenance=1075c286fea33b7ddc5451d3d3da47e63f9c9077d4543dd7e0b498c830ad8dc0
handoff=095af12c8b335e86b8e8590259946a33cec5c356eaaacc9e93f2e09698193a48
```

The CycloneDX root identifies candidate.31, its artifact-set property equals
the canonical strict-v2 handoff digest, the provenance invocation binds the
same candidate and digest, and predecessor candidate references are absent.
The main-only signer validates the exact tracked template and emits a detached
Ed25519 signature without exposing the private key locally.

## Candidate.30 append-only correction

WO-013FS used a provisional line-based artifact-set calculation and stated the
expected digest as `5076e81d...`. The canonical handoff descriptor algorithm
includes architecture, Core ABI/artifact identity, filename, kind, platform,
artifact hash and size in sorted canonical JSON. Its correct candidate.30
expected digest is the same `dce1c4e4...` because the six application bytes and
descriptors are unchanged.

This correction changes only that expected digest and algorithm description.
Candidate.30 still carries SBOM digest `79517b5c...`, provenance invocation
digest `8fe2ccb7...`, a candidate.29 CycloneDX root and predecessor references.
Its immutable `NO_GO 1/18/2` decision is unchanged.

## Runtime and host boundary

- No host mouse, keyboard, screen focus, route, tunnel or DNS setting was used.
- ADB listed no devices, so physical Android and LDPlayer remain `NOT_RUN`.
- Candidate.31 application bytes match the retained CLI-built files exactly.
- The identical Windows setup bytes retain headless Windows 11 `11/11` install,
  service, synthetic direct TUN/DNS and connected-reboot evidence. This does
  not become a new managed-runtime PASS merely because the candidate label
  changed.
- Exact candidate.31 managed default/AWG3.1/AWG2/Smart-DNS, connected uninstall,
  broader lifecycle and authenticated-egress checks remain open.

## Hosted checks

The exact source tuple has ten attached authoritative jobs. Five Core jobs and
the two release-index jobs pass. Two platform jobs and one client job execute
zero steps and remain `BLOCKED_BY_ACCESS_GITHUB_BILLING`; they are not test
failures and are not PASS. The owner-solo review exception remains explicit.

## Gate F rows

| Check group | Status |
|---|---|
| Supply chain, signature, SBOM, provenance | `PASS` |
| Release docs/manifest binding | `PASS` |
| Mandatory stop-ship/DoD and final no-open-P0 attestation | `MISSING` |
| Hosted required checks | `BLOCKED_BY_ACCESS_GITHUB_BILLING` |
| Android, managed Windows, origins and remaining approval rows | Explicit non-PASS statuses in retained Gate F evidence |

There are no explicit exact-candidate FAIL rows. Gate F is still `BLOCKED`, not
`GO`, because seventeen required rows remain non-PASS.

## Verification

```text
validate_release_candidate_supply_chain.py candidate.31 -> PASS
  artifacts=6
  windows_runtime_files=11

release-index source tests -> 7 passed
release-index tracked-source validator -> PASS
hosted signer and independent signature revalidation -> PASS

release_1_2_gate_f.py --expect-blocked
  -> BLOCKED
candidate_validation=PASS
required=19; pass=2; non_pass=17; fail=0
validation_errors=0
gate_g_authorized=false
```

## Evidence digests

| File | SHA-256 |
|---|---|
| `013FT-candidate31-signed-binding.json` | `70e71cc65b5e9f40bf92fa2b1f0b1039ff5bc4d178e779f720e822b324edfde6` |
| `013FT-candidate31-hosted-checks.json` | `dbfb375973b6ce38a4493880e257bc1079442aa84e39c27e67291175639d84a0` |
| `013FT-candidate30-artifact-set-correction.json` | `955c5e6b6961464a286e83e8b0b476f5b34f431991d51b5663662334d576dee7` |
| `013FT-candidate31-gate-f-evidence.json` | `86dd4f04ec8ec4858d43b95ab998e05d2171b121bd04872015e3077570bfd700` |
| `013FT-candidate31-gate-f-input.json` | `9080766361c554d05aae3c2bac3cd9dee1bb8731fb38462bc0bbd9e347d6f5ef` |
| `013FT-candidate31-gate-f-decision.json` | `dc2732d8ccae13b67b2a7cd4d104423699daa9a0ce76af84a2a622a742bad809` |

`REL_GATE/GATE-F` remains `I3`. No tag, GitHub Release, public asset, Store
submission, production deploy or stable-pointer mutation occurs. The next
release work is exact candidate.31 Android and managed Windows runtime proof,
followed by current/Brain/RU origins, rollback, provider/Operator/legal and the
final aggregate.
