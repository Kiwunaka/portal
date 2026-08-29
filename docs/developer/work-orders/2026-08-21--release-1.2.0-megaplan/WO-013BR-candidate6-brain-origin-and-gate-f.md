# WO-013BR — candidate.6 Brain-origin and Gate F

## Outcome

Close the false candidate.6 Brain access blocker with the owner's already
trusted OpenSSH configuration, retain three fresh read-only runtime proofs and
regenerate Gate F without changing candidate bytes or Brain runtime state.

Brain now passes the exact bounded origin slice:

| Check | Result | External report SHA-256 |
|---|---:|---|
| Exact runtime source | `197/197 PASS` | `0f20bedcd3e79430aee6e2f72a9f080373286a3c2f4e94538f06c719b8c701f4` |
| Runtime readiness | `23/23 PASS` | `494cec4b5a6e74b285231019194895d41359399609b1dc3150b21bc671cbddcf` |
| Enabled delivery | `7/7 PASS` | `4b9eeaf256b22e76723ad26605135a0a37d4b9e148ed10cd0aa4ad90cd1bb937` |

This proves Brain-origin only. It does not prove RU-origin, Beeline reachability,
every client transport or physical-device egress.

## Exact identity

| Component | Revision or digest |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.6` |
| Operational ID | `62526fdbf0f86c2a7083eb9d2cff4f8645949a31c59032fa593dad9bc68cae05` |
| Platform source | `5713324c1c0c2566befadf527bc09ec0ecf84a4e` |
| Client source | `b2497af7704d0aa6901541e175ce154b0eab05d7` |
| Core source | `a45d69e40ed7d892619a2b5c4592a527f630665e` |
| Release-index source | `8d09ae5e8ec0c8347bcd4e2659944bdf7c9c9db3` |
| Signed manifest | `8aac2458f8c43c0ef2955719dcede44f495d60acf681bc804bd6bf9828ee9054` |
| Signature | `2307906a920fb9b4dcd4c0025bf7628972668905d13897c553ddf27a81592dfa` |
| Receipt | `85dd34504d876086aa8bfe3533ad4db964e4f0a9106f9085657dc08c2c7afcaa` |

The release-probe harness is a post-candidate tooling correction at
`426444e0c759fd64b7f8d521ed8571085796c315`. It does not rebuild or mutate the
signed candidate.

## Access correction and fail-first evidence

WO-013BM's address/password probes were honest for that harness but incomplete:
they did not consult the owner's working SSH configuration. A bounded adapter
now accepts a validated SSH alias, requires batch mode and strict host-key
checking, disables forwarding and TTY allocation, and never writes the alias,
address, key or remote content into evidence.

The source probe sends only fixed target paths and local hashes. Brain returns
only raw and CRLF-normalized hashes. The result is four raw-exact files, 193
CRLF-only differences and zero semantic mismatches across all 197
deploy-selected files.

The first readiness pass reached `22/23`: Windows text-mode stdin converted LF
to CRLF and the remote shell rejected `pipefail`. That report is retained as
fail-first evidence with SHA-256
`4fbf7a755d42c4666508d08bc2e17ad4cb7c066d634a4cc9d0987b5b1fdaa22e`.
The adapter now normalizes and transmits UTF-8 bytes; the same readiness matrix
then passes `23/23`. The subscription script streams to `bash -s`, so no
temporary remote file is created in the SSH-config path.

## Gate F result

The successor digest-bound Gate F validates all 19 evidence pointers with zero
validation errors and returns `BLOCKED`: `4/19 PASS`, `15/19 non-PASS`,
`0 FAIL`. Supply chain, release-doc/manifest binding, current-origin and
Brain-origin pass.

`REL_GATE/GATE-F` remains `I3` with status
`SIGNED_CANDIDATE6_GATE_F_BLOCKED_4_PASS_15_NONPASS`. `FRKN_PLAN/W9-02`
remains `I1` because RU-origin is still `NOT_RUN`, although current-origin and
Brain-origin now have separate PASS evidence. No ledger row advances.

The remaining Gate F blockers include exact Gates A–E/manual stop-ship proof,
the no-open-P0 aggregate, physical Android, isolated Windows, RU-origin,
authenticated client egress, live Smart-DNS access, provider, Operator,
legal/commercial, comparable performance and post-public-promotion health.
Hosted zero-step checks remain `SKIPPED_BY_OWNER` under the no-purchase
`OWNER_SOLO_EXCEPTION`; they are not PASS.

## Physical Android boundary

After the owner reported the phone returned, both local ADB servers still saw
only the authorized emulator and zero physical-like devices. No serial was
retained. The physical candidate.6 AWG2/AWG3.1, WARP, per-app, Wi-Fi/LTE,
Private DNS/IPv6, OEM/Doze, leak, endurance and cleanup matrix remains manual.

## Evidence and mutation boundary

Normalized evidence/input/decision SHA-256 values are respectively
`8a1d1e82e3f2447d39329ad7b33e62e405e12bc227645dae65a5ac1a492ae7fc`,
`c88044e2af6c80ce2d5f8d9e00020959f96c5d310729fedc03c73e9b29dae25e`
and `c1ca2f016556272d17088493ec6ba67ce9c94f72856508702bf5a2387e48da9f`.

No deploy, restart, entitlement/payment action, repository visibility change,
tag, public release, store object, stable pointer or Gate G authorization
occurred. No address, hostname, SSH alias, credential, key, raw configuration,
customer/provider payload or device serial is retained in normalized evidence.

## Verification

```text
python -B -m pytest -q -p no:cacheprovider tests/test_ssh_host_keys.py tests/test_remote_brain_runtime_source_probe.py tests/test_verify_brain_ready.py tests/test_remote_brain_network_probe.py
# 34 passed, 9 subtests passed
python -B -m ruff check <changed probe and focused test files>
python -B -m py_compile <changed probe modules>
python -B scripts/remote_brain_runtime_source_probe.py --ssh-config-alias <trusted-owner-alias> --source-revision 5713324... --json-out <external-evidence>
python -B scripts/verify_brain_ready.py --ssh-config-alias <trusted-owner-alias> --repeat 5 --json-out <external-evidence>
python -B scripts/remote_brain_network_probe.py --ssh-config-alias <trusted-owner-alias> --live-enabled-nodes --redact --json-out <external-evidence>
python -B scripts/release_1_2_gate_f.py <signed-candidate6-inputs> --expect-blocked
```

Machine evidence is under
`evidence/013BR-candidate6-brain-origin-and-gate-f/`. Raw secret-free runtime
reports remain outside Git and are referenced only by labels and SHA-256.
