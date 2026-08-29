# WO-013CF — candidate.8 Brain, RU-terminal and Windows evidence

## Outcome

Bind fresh Brain-origin, direct RU-terminal and owner-current-host Windows
evidence to the immutable `pokrov-1.2.0-candidate.8`, then regenerate the
digest-bound Gate F decision without deploying production or authorizing
public promotion.

Exact Brain source/readiness/delivery advances `brain_origin` to `PASS`.
The RU and Windows slices materially reduce uncertainty but remain
`MANUAL_OWNER_TEST`: the canonical RU probe contour is not installed, and the
Windows run proves a clean application-state lifecycle on the owner's current
host rather than the connected-network and clean-VM matrix. Gate F therefore
returns `BLOCKED` with `5 PASS`, `14 non-PASS`, `0 FAIL` and zero validation
errors.

## Exact candidate identity

| Component | Revision or digest |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.8` |
| Operational ID | `eeedbaf8540a83649a7143d6c7097336429e466118ed4f9ca2b732b7e6e2195a` |
| Platform source | `241a83b4dca00799b39696a4ae0c3c97e087ec39` |
| Client source | `3459438f02bd774e722b1b858e7f7f16d57a9f5c` |
| Core source | `a45d69e40ed7d892619a2b5c4592a527f630665e` |
| Signed release-index source | `b242e0a3060b04f9b71641a0524bf251a75ce2a8` |
| Manifest SHA-256 | `f0006cec90c84e401e9920d9098102c7f50ab5ace5242e0d7683c3df709a6fbc` |
| Signature SHA-256 | `5fcae0675ea45e79baf495859fd170661f5d6dd3a8535275acd4d62680d324f6` |
| Receipt SHA-256 | `4109bb3417b32a780604300055f5308acf7dc810e7ea9c547075e1da41cc21fc` |

No artifact was rebuilt or relabelled.

## Brain-origin

Fresh read-only checks use the owner's trusted `pokrov-brain` SSH alias and
the exact detached platform source.

- readiness is `23/23 PASS`, including required services, listeners, public
  endpoints and five subscription-stability samples;
- all `7/7` live enabled delivery nodes accept their configured TCP port;
- the deployed payload is a semantic byte match for all `197/197` selected
  source members: `4` raw matches and `193` CRLF-only differences normalized
  by the declared `CRLF_TO_LF_ONLY` rule;
- no mismatch, deploy, restart or runtime mutation occurred.

This is exact-source Brain-origin `PASS`, not a claim about RU client access,
post-public-promotion health or an undeployed Smart DNS runtime.

## Direct RU-terminal evidence

The trusted `pokrov-mini` terminal is observed as a direct RU-origin operator
host. The canonical persistent probe package is absent: `0/10` source/unit
members, `0/4` loaded units, no runtime configuration, spool or archive.
Consequently this row cannot be promoted to `PASS`.

A transient no-remote-file helper ran four bounded read-only samples from the
terminal against exact public URL contracts and live enabled control-plane
node rows. It retained only redacted status and node codes.

- marketing, cabinet and API health pass `3/3` in every sample;
- `de`, `it`, `pl`, `ru`, `ru_spb` and `us` pass in every sample;
- `nl` passes `2/4` and times out at TCP in the other two;
- `ru_spb` passes `4/4`, so the prior mobile-only SPB failure is not evidence
  of a general SPB outage;
- Telegram bot/channel diagnostics fail TCP in all samples, but third-party
  Telegram is excluded from the POKROV-owned reachability verdict.

The retained classification is
`MANUAL_OWNER_TEST_CANONICAL_PROBE_CONTOUR_NOT_INSTALLED`. No remote file,
raw endpoint material or runtime mutation was retained.

## Windows owner-current-host smoke

The exact unsigned setup has SHA-256
`26ec26d8989d61415f07cbf9707f336ebba0b947fa4ba0ee93d3078fa3984668`
and size `28929376`. Under the owner-approved direct-beta exception, an
elevated current-host run proves:

- clean application-state baseline;
- exact machine-wide install and `8/8` installed-file identity;
- automatic LocalSystem service identity and install-owner binding;
- authenticated UI/service IPC and status request;
- service stop/restart;
- uninstall of service, application files and owner registry record;
- identical idle route/DNS fingerprints and zero remaining POKROV/Wintun
  adapters.

The protected service evidence under ProgramData is intentionally retained.
The run does not claim a clean OS/VM, connected TUN/full-tunnel traffic, DNS
capture/leak protection, owned-profile egress, sleep/reboot/crash recovery,
connected uninstall or interactive SmartScreen observation. Therefore
`windows_live_network` remains `MANUAL_OWNER_TEST`.

The reusable candidate.8 harness was merged to client `main` by PR `36` at
`5bfc96fb81ee9a7f4003ffb698e3f0c8041f1b35`. Hosted run `33273837482`
executed zero steps and is `SKIPPED_BY_OWNER` under the no-purchase solo
policy, not `PASS`.

## Gate F

Only `brain_origin` advances from the immutable WO-013CC snapshot:

| Check | Previous | Current | Reason |
|---|---|---|---|
| `brain_origin` | `NOT_RUN` | `PASS` | exact source `197/197`, readiness `23/23`, delivery `7/7` |
| `ru_origin` | `NOT_RUN` | `MANUAL_OWNER_TEST` | direct RU support evidence exists; canonical contour absent |
| `windows_live_network` | `NOT_RUN` | `MANUAL_OWNER_TEST` | current-host app lifecycle passes; connected/clean-VM matrix open |

The successor decision validates all `19/19` pointers and returns `BLOCKED`:
`5 PASS / 14 non-PASS / 0 FAIL / 0 validation errors`. No completion-index
row advances to `I4` and Gate G remains unauthorized.

## Evidence

Machine summaries are under
`evidence/013CF-candidate8-brain-ru-windows-evidence/`:

| Evidence | SHA-256 |
|---|---|
| Brain summary | `70c5798740c5e6139ecfa2e365b71ace59d050cfd8369555240d874f25006ae1` |
| RU summary | `e2e33e523372bad5f92f872f25f8dcfd82187974ba731c6d5683a5ec5980b02d` |
| Windows summary | `7c83a9cb1e47f5362459c7ec003f8831331a296b83549417d16647240abd350c` |
| Gate F evidence | `28bd75b78b079bcc31c27fb70228048542c8f33ba3ba3549a1fdf35d85628bb1` |
| Gate F input | `1ba3ea779ccb48f8dd93e36545c5ddde460bbae271aceb9c7e1299f6d05deb4a` |
| Gate F decision | `88c0e26021b1decb15b8a2c87b3080da841ff5c60469cb8e286b0437334fc96a` |

External local evidence is digest-bound from the summaries. No secret, raw
endpoint, device identifier, private key, credential or customer data is
tracked.

## Mutation boundary

Brain and RU checks are read-only. The owner-current-host Windows mutation is
bounded to install/service/IPC/restart/uninstall and ends with independent
absence/readback checks. No production deploy, payment action, repository
visibility change, tag, public release, Store submission, stable pointer or
Gate G authorization occurred.

## Verification

```text
python -B scripts/release_1_2_gate_f.py <candidate.8 exact inputs> --expect-blocked
# BLOCKED: 5 PASS / 14 non-PASS / 0 FAIL / 0 validation errors

python -B -m pytest -p no:cacheprovider tests/test_release_1_2_gate_f.py -q
# PASS
```
