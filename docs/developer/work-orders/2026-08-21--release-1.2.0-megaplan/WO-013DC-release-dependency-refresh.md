# WO-013DC — release dependency refresh for the candidate.13 successor

Status: `LOCAL_PASS_SUCCESSOR_REQUIRED; CANDIDATE13_NOT_PROMOTABLE`

Observed: `2026-08-31T01:26:17Z`

## Scope

Audit the exact Python dependency locks carried by signed candidate.13, refresh
the affected direct pins on current platform `master`, and prove the resulting
platform source without changing candidate artifacts, release pointers, DNS,
owned-node runtime or public/stable state.

The candidate.13 platform dependency paths are byte-identical to current base
`f10cec0de9fb10140ca29316d58e53c3a1761b32`, so the findings apply to the
signed candidate rather than only to a later documentation head.

## Findings and correction

The pre-change production lock contained three affected packages and four
advisory records: `cryptography 49.0.0`, `paramiko 4.0.0` and
`requests 2.32.3`. The pre-change test lock contained six affected packages
and 31 advisory records, adding `aiohttp 3.13.3`, `pytest 9.0.2` and
`python-dotenv 1.2.1` to the affected set.

The direct pins now resolve to:

- `aiohttp 3.14.3`;
- `cryptography 50.0.1`;
- `paramiko 5.0.0`;
- `requests 2.34.2`;
- `pytest 9.1.1`;
- `python-dotenv 1.2.3`.

Both universal Python 3.12 hash locks were regenerated with the canonical
`uv pip compile` commands. A no-op recompile over copies of the retained locks
returns `delta=0` for both files. Fresh audits return zero known findings over
27 production dependencies and 60 test dependencies. The unchanged
`webapp`, `adminapp` and `marketing` production npm trees retain zero audit
findings.

The full repository test collection also exposed undeclared direct test
imports. `httpx 0.28.1`, `httpx2 2.10.0`, `jsonschema 4.26.0` and
`pytest-asyncio 1.4.0` are now explicit test inputs, raising the audited test
lock to 60 dependencies without changing the production lock.

## Verification

An isolated Python 3.12.7 environment installs the exact updated test lock.
The focused release/runtime matrix passes:

- verified-loader/static-guard and rollback regression: `14 passed`;
- auth, Operator Center, node access and related boundaries:
  `249 passed`, `8 subtests passed`;
- payments: `125 passed`, `12 subtests passed`;
- support and observability: `131 passed`;
- release workflow, stop-ship and Gate F source checks: `25 passed`.

Total focused result: `544 passed`, `20 subtests passed`, zero failures. The
19 payment warnings are existing deprecation notices and are not converted to
failures or silently relabeled.

The complete root collection contains `3632` tests. A file-partitioned Windows
run covers that exact collection with `3622 passed`, `10 skipped`,
`274 subtests passed` and zero unresolved failures. The partition proof is:

- prefix through the corrected Android bundle guard: `414 passed`;
- shard 1: `714 passed`, `5 skipped`, `213 subtests passed`;
- shard 2: `898 passed`, `5 skipped`, `23 subtests passed`;
- shard 3: `760 passed`, `38 subtests passed` across a green prefix, the exact
  generated-inventory file, and a green post-inventory suffix;
- shard 4 plus the separately serialized observability file: `836 passed`.

The full collection exposed stale evidence/test contracts rather than hidden
product failures: moved API line references, current client release wording,
the Inno Setup Windows packaging contract, Windows CRLF handling for the
byte-pinned Telegram SDK mirror, and a stale imported ORM module graph in the
free-profile contract fixture. Those guards are synchronized and pass. The
generated source inventory is also current at `11660` symbols and honestly
retains its explicit review buckets; this work does not relabel those buckets
as release proof.

The current rollback harness intentionally evaluates only a Git-object source
that has already passed its exact object-id and blob-digest checks. Its static
guard exception is now restricted to the exact loader file, class, method and
`exec(code, module.__dict__)` call shape. Near-miss scope and argument tests
remain rejected; the general runtime guard still rejects other dynamic
evaluation, unsafe deserialization and `shell=True` use.

Two fresh read-only Smart DNS PLANs using `paramiko 5.0.0` prove key-auth
compatibility through the owned Brain and `it` node paths. Runtime preflight,
upstream DoT, HAProxy state and candidate frontend validation pass. Both plans
report `mutation_performed=false` and return no raw host, address, credential,
key, configuration or runtime material. Authoritative DNS is still absent, so
the service APPLY remains correctly closed.

`git diff --check` and the script-manifest check pass. No production Python,
service, DNS, candidate artifact, client/Core source or release pointer was
changed by this work order.

## Release decision

Candidate.13 remains immutable retained signed evidence, but it is not eligible
for promotion with the old platform dependency locks. This correction must be
merged and bound to a successor signed candidate before Gate F or any public or
stable action. The unchanged client/Core bytes do not transfer candidate.13
promotion credit to that successor.

`REL/DEP-001` remains `I3` with stronger current local evidence. It does not
reach `I4` until the updated locks are installed and rechecked from the exact
successor source in the hosted/frozen candidate flow. Gate F, Gate G, Store,
public release and stable pointers remain unchanged.

## Evidence

- `evidence/013DC-release-dependency-refresh/013DC-release-dependency-refresh.json`;
- production lock SHA-256:
  `f3ead265d884c66f58536ea71955c715f9294346cc8ffab98170448956c171ac`;
- test lock SHA-256:
  `c50dbbef6bdb74b5b967c1766dc0cf270f6518ba5a0a666b2f9b8fa364209223`;
- sanitized Paramiko 5 runtime PLAN SHA-256:
  `b9785f1c4d579e663f70bca6b75ab9c03cbf7edbc8923190f26906a36ecd1f37`;
- sanitized Paramiko 5 frontend PLAN SHA-256:
  `afb102b24321e9c1460f37b26303ab56494195032bdcef3bd91a6f65fc337594`.

## Rollback

Revert only the successor dependency-refresh commit before candidate assembly
and reinstall the preceding exact hash lock in an isolated environment. No
runtime rollback exists for this slice because no deployment or service
mutation occurred. Candidate.13 itself is retained and is not rewritten.
