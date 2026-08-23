# WO-013C — Release known-limitations contract

Status: `COMPLETE_LOCAL_I3`
Phase: `11`
Row advanced: `REL_DOD/DOD-17`
Promotion: `NOT_REQUESTED`

## Outcome

Make the 1.2.0 Linux scope and Android OEM limitations explicit across the
structured platform owner, its canonical mirrors and the active-client release
owners. Do not turn missing physical evidence into a compatibility guarantee.

## Implemented boundary

- Linux is `NOT_SHIPPED_IN_1.2.0`. Android and Windows remain the only public
  release pair.
- Transitive Linux dependencies, third-party compatibility guidance, dormant
  Linux errors and PB-09 are explicitly non-evidence for an official Linux
  client. PB-09 remains `notShipped` with no Linux runtime action.
- Android OEM power/background behavior, VPN permission, notification delivery
  and cached tile state are known variables. The product does not promise
  uninterrupted background operation across OEMs.
- The bounded support/recovery contract uses PB-08 with
  `AND-BG-001/002/003` and `AND-VPN-004`; the exact candidate still needs the
  physical OEM matrix.
- Platform product/launch limitation docs and active-client product/cutover
  docs state the same boundary.

## Index decision

`REL_DOD/DOD-17` advances `I0 -> I3`. The known limitations are now explicit,
machine-bound and locally regression-tested. Exact-candidate release-note
projection and physical Android OEM observation belong to `I4`.

Distribution becomes `I3=300`, `I2=21`, `I1=40`, `I0=16`; `77` rows remain
below `I3`. Stage split becomes `6/33/17/21`.

## Local proof

- Platform canon and known-limitations contracts: `31/31` PASS.
- Focused observability plus limitations contracts: `21/21` PASS.
- Active-client docs contract: PASS.
- Active-client exact PB-08/PB-09 runtime contract: `7/7` PASS.
- Docs/candidate-preflight contracts: `37/37` PASS.
- Live explicit-root preflight: expected `BLOCKED`, seven blockers,
  `candidate_created=false`, pending stages `6/33/17/21`.

Machine evidence:
`evidence/013C-release-known-limitations-contract/013C-release-known-limitations-contract.json`.

## Evidence ceiling

No exact candidate exists. No Android physical OEM/background/lockscreen/tile
matrix ran, and no exact-candidate release notes, artifact, deployment,
publication or promotion were produced.
