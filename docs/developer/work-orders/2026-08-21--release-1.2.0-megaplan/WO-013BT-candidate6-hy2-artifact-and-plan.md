# WO-013BT — candidate.6 HY2 artifact and remote PLAN

## Outcome

Replace the stale pre-candidate Hysteria2 server-artifact binding with an exact
candidate.6 Core build, then repeat the owned-node preflight without mutation.

The old builder failed first with `core_revision_mismatch` because it allowed
only Core `e8eb772...`. That is correct fail-closed behavior: candidate.6 binds
security-fixed Core `a45d69e...`, so the old server bundle must not be installed
as exact-candidate evidence.

Release tooling now requires Core
`a45d69e40ed7d892619a2b5c4592a527f630665e` and identifies the rebuilt server
binary as `1.13.0-pokrov-hy2-lab.2`. Candidate bytes are unchanged; this is a
post-candidate lab artifact and read-only deployment-plan correction.

## Exact artifact

| Field | Result |
|---|---|
| Core source | `a45d69e40ed7d892619a2b5c4592a527f630665e` |
| Go | `go1.25.13` |
| Bundle size | `15232131` bytes |
| Bundle SHA-256 | `fe9f082f3ad7e7e2a45db8257fc1fec202c63fe0ce43e0b25fc4620c827bd93e` |
| Embedded ELF SHA-256 | `e877237c919cb7c0b12df1ccd6a358eb206dbeefe3516e9a7d421e199d352901` |
| HY2 contract SHA-256 | `c96b38e58ea33f838f23b80a65f3a9a264e932b7248f206798df9a0b8fa0fb98` |
| Independent repeat | `PASS_BYTE_IDENTICAL` |
| Bundle verification | `PASS` twice |
| Runtime material included | `false` |

Each invocation internally compiles the Linux/amd64 binary twice and requires
byte equality. A separate complete build produced the same bundle and embedded
binary hashes. The exact synthetic `sing-box check`, license/provenance and
placeholder-only bundle contract pass.

## Owned-node read-only PLAN

The exact rebuilt bundle passed the guarded remote installer without `--apply`:

| Precondition | Result |
|---|---:|
| Brain/device-node authentication | `PASS_KEY` |
| Brain HY2 kill-switch | `ENGAGED` |
| root and required tools | `PASS` |
| UFW installed and active | `PASS` |
| exact UDP port | `FREE` |
| existing release/config/unit targets | `0` |
| service | `inactive / not-found` |
| runtime material | `NOT_READY` |
| mutation | `false` |

The old WO-013AR PLAN saw the Brain kill-switch as unavailable because its
control-plane code was not deployed then. Current Brain source/readiness is
already exact candidate.6, and the current PLAN now reads the kill-switch as
engaged. Infrastructure is ready for a guarded install; owner-only runtime
material is intentionally absent.

## Evidence ceiling

`FRKN_HY2/HY2-01` remains `I3` with the stronger status
`CANDIDATE6_EXACT_ARTIFACT_REMOTE_PLAN_READY_RUNTIME_MATERIAL_MISSING`.
This is not a deployed server, endpoint-material, handshake, traffic,
performance, physical-device, current/Brain/RU-origin or release PASS.

Candidate.6 and Gate F remain unchanged at `4 PASS / 15 non-PASS / 0 FAIL`.
No Gate F row advances and no Gate F regeneration is warranted.

## Required owner-authorized continuation

APPLY changes an owned delivery node and consumes secret runtime material, so
it requires explicit owner authorization. The next sequence is:

1. generate receipt-bound TLS/password/optional-obfs material outside Git;
2. run guarded APPLY with exact bundle/source/node/material confirmations while
   the Brain kill-switch remains engaged;
3. provision encrypted device-bound client material;
4. run a bounded candidate.6 handshake/traffic/DNS/leak/teardown matrix across
   current-, Brain- and RU-origin where applicable;
5. execute exact-receipt rollback on any failed post-start check.

## Evidence and mutation boundary

Normalized evidence is under
`evidence/013BT-candidate6-hy2-artifact-and-plan/` with SHA-256
`3c693e4b6ed9cc96d5416c01d42f2153052f0a3f2950e8257a3e935b5a8e4b6f`.
The external sanitized remote PLAN report SHA-256 is
`249a1c8fd4cf32a6d454f3a5cf6aa0ae620ed70c1f7d898794d2f81c79908aa5`.

No Brain or delivery-node file, config, service, firewall, pointer, database,
client material or runtime state changed. No raw host, address, credential,
key, TLS material, password, endpoint config, provider data or device identity
is retained. No tag, public release, store object or stable pointer changed.

## Verification

```text
python -B -m pytest -q -p no:cacheprovider tests/test_build_owned_hy2_server_bundle.py tests/test_remote_install_owned_hy2_lab.py tests/test_check_script_manifest.py
# 17 passed
python -B -m ruff check scripts/build_owned_hy2_server_bundle.py tests/test_build_owned_hy2_server_bundle.py tests/test_remote_install_owned_hy2_lab.py
python -B -m py_compile scripts/build_owned_hy2_server_bundle.py
python -B scripts/build_owned_hy2_server_bundle.py build --core-root <candidate6-core> --go-executable <go1.25.13> --output <external-bundle-a>
python -B scripts/build_owned_hy2_server_bundle.py build --core-root <candidate6-core> --go-executable <go1.25.13> --output <external-bundle-b>
python -B scripts/build_owned_hy2_server_bundle.py verify --bundle <external-bundle-a>
python -B scripts/build_owned_hy2_server_bundle.py verify --bundle <external-bundle-b>
python -B scripts/remote_install_owned_hy2_lab.py --bundle <external-bundle-a> --brain-host <owned-brain> --node-code de --known-hosts <owner-known-hosts> --passwords <owner-secret-bundle> --operation install --json-out <external-report>
# PLAN only; mutation_performed=false
```
