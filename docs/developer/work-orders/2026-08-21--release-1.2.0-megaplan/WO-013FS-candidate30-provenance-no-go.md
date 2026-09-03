# WO-013FS — candidate.30 CLI/Windows proof and supply metadata NO_GO

Status: `EXACT_CANDIDATE30_GATE_F_NO_GO_1_PASS_18_NON_PASS_2_FAIL`

Observed: `2026-09-03T13:35:00Z`–`2026-09-03T16:19:36Z`

Production/public mutation: `NONE`

## Outcome

Build and test the current all-platform release path entirely through CLI,
without taking host input focus or changing the owner's host networking. The
six application artifacts build successfully. Exact candidate.30 also passes
the bounded Windows 11 install, `11/11` installed identity, service, direct
TUN/DNS and connected-reboot checks.

The release cannot advance. The strict supply replay finds that the retained
CycloneDX root still identifies candidate.29 and carries a different
artifact-set digest. SLSA provenance also binds its `invocationId` to a stale
artifact-set digest and retains predecessor candidate references. The manifest
signature and all artifact bytes remain valid, but SBOM and provenance are
mandatory parts of the signed release contract. Candidate.30 is therefore
immutable rejected history and Gate F is exact `NO_GO`.

```text
NO_GO
required=19
pass=1
non_pass=18
fail=2
validation_errors=0
candidate_validation=PASS
gate_g_authorized=false
```

## Exact candidate boundary

| Item | Identity |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.30`, app `1.2.0+4053` |
| Operational id | `79d275f28b3aa8b96252112ead3ef72b307ad40216542b5c0cc3fc622fd53ec3` |
| Platform | `7c4133343871ed52257a850e829e906608412753` |
| Client | `7e3e771fe36333a75244cbfd828c60beb84c7ff1` |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release index | `b06fe143a83aca49c1779962ad526c54e2162e42` |
| Manifest | `33ceb44b445dd5f66d5b10e0e1c90da03d9a6efe3d1c4966dd2be72bf955230c` |
| Signature | `61169e29d521524663637c1747d7d5b70de6140332d4056b8d5c71f694c6f510` |
| Receipt | `2628ec258322c6a884f60b1ca9f6533eae0a68c1d170cf971c6051e82777bba0` |
| Hosted signer | Run `33765307625`, artifact `9897220950` |

## Headless build and runtime result

- Client application tests, Android production flavors and Windows packaging
  pass through CLI.
- The isolated Windows 11 guest receives the exact setup without host UI
  control. Install/upgrade identity passes `11/11`; service and direct
  TUN/DNS lifecycle pass; connected guest reboot restores the expected state.
- No physical Android device is visible to ADB, so physical Android remains
  `NOT_RUN`. LDPlayer is also `NOT_RUN` for this exact candidate.
- Managed-node, packaged AWG, Smart DNS and the full Windows network/lifecycle
  matrix are not claimed by this slice.

## Core reproducibility

The first fresh Core build used system MinGW GCC 16.1.0 and differed from the
candidate DLL. That build was rejected before candidate creation. CI pins Go
1.25.13 and MinGW GCC 13.2.0; two fresh builds with those exact tool versions
reproduce candidate.30 byte-for-byte:

```text
size=55426048
sha256=f284fa8841f1a45271874a7a05ed6093fb0e3efbdd03e00001edd046be708204
repeat=2/2 exact
proxy_start_stop=100/100 PASS
```

One exact proof build is retained under
`E:\POKROV-tools\builds\core-cd8f0f4-mingw13-validation2-20260903-a`.
Failed and duplicate temporary outputs were removed after their evidence was
captured.

## Supply metadata stop-ship

The strict validator recomputes the ordered six-artifact set from exact
`name|size|sha256` rows. Candidate.30 requires:

```text
pokrov-1.2.0-candidate.30/5076e81d795927e7432eeeea9cde5093e8bed71e1a2bf2e6d670eeb2520069d1
```

The retained CycloneDX root instead names candidate.29 and stores artifact-set
digest `79517b5c1e771be88851ad3b3644e49bfce1c619831db8db17de8a604fa89e87`.
The retained provenance contains:

```text
pokrov-1.2.0-candidate.30/8fe2ccb751694a0448ece6aec900b898ae7843223112b8f3033fb503eff20a79
```

It also retains candidate.29 and candidate.25 references in internal
parameters. The earlier supply validator checked artifact components but not
these root/current-candidate bindings, so its apparent PASS is withdrawn.
Platform PRs [198](https://github.com/Kiwunaka/portal/pull/198) and
[199](https://github.com/Kiwunaka/portal/pull/199) merge the fail-closed checks
as master `7e3c57ec390d8ebfa95c617e53f999e31a96b306`. Exact candidate.30 replay now
fails first with `sbom_root_bom_ref_mismatch`; exact-field inspection retains
the SBOM artifact-set, provenance invocation and internal-reference findings.

No candidate.30 signed file is edited. A successor may reuse identical
application bytes only if it regenerates SBOM, provenance and handoff metadata,
passes strict validation, and receives a new hosted signature and receipt.

## Gate F rows

| Check group | Status |
|---|---|
| Mandatory stop-ship and DoD | `FAIL` |
| Supply chain, signature, SBOM, provenance | `FAIL` |
| Release docs/manifest binding | `PASS` |
| Hosted required checks | `BLOCKED_BY_ACCESS_GITHUB_BILLING` |
| Remaining exact runtime, origin and approval rows | Explicit non-PASS statuses in retained Gate F evidence |

Seven of ten authoritative hosted jobs pass. The two platform jobs and one
client job have zero executed steps and remain access/billing blocked, not test
failures and not PASS. The owner-solo review exception remains the process
boundary.

## Verification

```text
validate_release_candidate_supply_chain.py exact candidate.30 replay
  -> FAIL sbom_root_bom_ref_mismatch

focused supply and Gate F tests -> 39 passed
release operation regression   -> 154 passed
docs/context contracts          -> 40 passed; PASS platform-context

release_1_2_gate_f.py
  -> exit 2 (expected NO_GO)
candidate_validation=PASS
required=19; pass=1; non_pass=18; fail=2
validation_errors=0
gate_g_authorized=false
```

## Evidence digests

| File | SHA-256 |
|---|---|
| `013FS-candidate30-signed-binding.json` | `291955e5e64287fe653b022e839415193a602a979f13ed5bd44b3f0e8735147b` |
| `013FS-candidate30-hosted-checks.json` | `ae4ca956b0745385af19e4fe51afe1ba035af97d9523862ffd659eec80b101c9` |
| `013FS-candidate30-provenance-stop-ship.json` | `5b8a85759663bb6814ff7f8f68d05b5f40417753dabb06c2ac33aac4ab6a8c9b` |
| `013FS-candidate30-gate-f-evidence.json` | `955a70504fadb8badd1a5d21f8b8dc88a10b224b204f46dafae9b52479642ae6` |
| `013FS-candidate30-gate-f-input.json` | `497854141ad84f547f662155691e1c2e813e6d55f48573bfbabb40d4152106d0` |
| `013FS-candidate30-gate-f-decision.json` | `2e7babf5cbb521ccd1718c3dfd86e424b3cf741976fc8d6deeb1715620248330` |
| External `core-windows-mingw13-reproducibility.json` | `063c6cfa202815a15b7dab615bb9c02831ffc4db8a2ab497542382c3d61e987a` |

`REL_GATE/GATE-F` remains `I3`. No tag, GitHub Release, public asset, Store
submission, production deploy or stable-pointer mutation occurs. The next
release action is a newly numbered, newly signed successor with regenerated
supply metadata.
