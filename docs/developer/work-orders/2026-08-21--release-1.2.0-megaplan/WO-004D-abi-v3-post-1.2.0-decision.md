# WO-004D — ABI v3 `ConnectionStatus` release decision

Status: `DEFERRED_POST_1_2_0`
Phase: `02`
Ledger row: `FE/P12-201`
Promotion: `NOT_APPLICABLE_TO_1_2_0`

## Decision

Do not implement Core ABI v3 as part of release 1.2.0.

This is not a scope cut invented during execution. The frontend source plan
states all three constraints explicitly:

- section 7.2 requires the 1.2.0 frontend adapter without waiting for ABI v3;
- section 23 keeps Core ABI v2 and labels the `ConnectionStatus` message as a
  proposal after 1.2.0;
- the P2 table places `P12-201` after blockers, while the exclusions section
  says ABI v3 must not be a 1.2.0 blocker.

The shipped-lane architecture already satisfies the intended user outcome with
one client-owned typed reducer, immutable proof-bearing snapshots, stable
reason codes, synthetic transition tests and raw-error redaction on desktop ABI
2 / event ABI 1.

## Compatibility evidence

- Core ABI contract and canonical Core release gate pass at desktop ABI 2.
- Runtime-engine passes 59 tests plus one declared exact-old-DLL skip,
  including released marker-only ABI 2, exact descriptor negotiation,
  fail-closed future ABI and unknown event/capability cases.
- Gate B and `OBS/OBS-047..050` are locally proved without fabricating v3.

`FE/P12-201` advances from captured `I0` to verified `I1` with an explicit
post-1.2.0 deferral. No implementation index is claimed.

Evidence:
`evidence/004D-abi-v3-decision/004D-abi-v3-decision.json`.

## Post-1.2.0 entry gate

A future ABI proposal must preserve a tested v2 fallback, add a separate v3
binding/capability fixture, version every new field and closed enum, prove Core
exports and actual artifacts, and define client migration/rollback before any
runtime advertises ABI 3.
