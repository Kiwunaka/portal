# WO-013DM — candidate.16 DE provider billing and host-identity boundary

Status: `OWNER_ATTESTED_BILLING_RESTORED; HOST_IDENTITY_MANUAL`

Observed: `2026-09-01`

## Scope

Record the owner's Datalix payment restoration, re-evaluate the safe resume
boundary for the owned `de` node, and prevent a billing change from being
misreported as node health or candidate.16 AWG interoperability.

No host key was accepted, no `known_hosts` entry was removed, strict checking
was not disabled, no remote command ran and no server or protocol state was
changed.

## Observation

The owner attests that the Datalix account is now paid. The latest strict SSH
check still stops with `HOST_KEY_CHANGED` and exit code `255`; the local
`known_hosts` file remains unchanged.

Payment restores provider entitlement, but it does not authenticate the
machine currently answering for the node. A changed host key may be expected
after a provider reinstall or reprovision, but it must be confirmed from the
provider console before local trust is updated.

## Decision

The owned DE node remains `BLOCKED_BY_HOST_IDENTITY` for automated alignment
and candidate.16 protocol tests. This does not change WO-013DH's classification:
candidate.16 AWG2 and AWG3.1 remain untested after provider recovery, rather
than failed or passed.

`FRKN_AWG/AWG-10` remains `I2`; `FRKN_PLAN/W3-02` and `W3-03` remain `I3`.
Gates B/C/E/F and the 378-row distribution do not advance. No public release,
stable pointer or Gate G action occurs.

## Required owner-console proof

Run on the Datalix provider console:

```text
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub -E sha256
```

The returned fingerprint must exactly match the expected fingerprint retained
separately from the network connection. A mismatch stops the DE lane. An exact
match authorizes a narrow backup and replacement of only that node's old host
key entry, followed by strict SSH and ordinary service readback.

## Evidence

- normalized record:
  `evidence/013DM-candidate16-de-host-identity/013DM-candidate16-de-host-identity.json`;
- normalized record SHA-256:
  `a0c9d85a36ab147c1563b5e2163ddae0d69483068c2e769db035781edfc6349e`.

## Next action

After exact provider-console fingerprint confirmation, prove strict SSH and
ordinary DE service health, run guarded AWG2/AWG3.1 alignment, then repeat the
exact candidate.16 Core runners from the owned RU Pi. Only a Core PASS reopens
the candidate.16 LDPlayer, physical Android and Windows protocol matrix.
