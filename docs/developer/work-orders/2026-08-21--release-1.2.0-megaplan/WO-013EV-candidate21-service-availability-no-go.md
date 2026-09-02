# WO-013EV — candidate.21 service availability NO_GO and candidate.22 source projection

Status: `CANDIDATE21_IMMUTABLE_NO_GO_BUILD4051_CANDIDATE22_PRE_CANDIDATE`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `01`, `03`, `11`
Candidate: `pokrov-1.2.0-candidate.21`
Successor target: `pokrov-1.2.0-candidate.22`, `1.2.0+4051`
Production/external mutation: `NONE`

## Outcome

Candidate.21 remains byte-for-byte immutable. Its signed tuple binds client
`1e164586d741484b5ae8fb2ee267ef5dd813cadb`, whose production Windows pipe
loop returns an error to the SCM service entrypoint when a client is rejected
or disconnects before completing a valid request. This is a service
availability defect even though candidate.21's earlier bounded upgrade,
default TUN/DNS/egress and rollback checks passed.

Client fix `55461b5b9ca75217e94768360b6517dbe17ecf6f` changes the production loop to
isolate rejected, pre-hello and malformed sessions and adds a two-session
native regression. It is merged in client `main` at
`8cf428fe4fa8fbc391b42683bdd73e6eb6e88886`; hosted run `33617842048`, job
`100207721061`, completed `success`. The old and corrected
`service_server.cpp` blobs and SHA-256 values differ exactly as retained in the
evidence record.

The isolated Windows 11 VM currently reports the candidate.21 service stopped
with Win32 exit code `5` after an intentional untrusted-controller diagnostic.
The protected recovery result is still absent, so exact runtime attribution is
only `CONSISTENT_WITH_REJECTED_SESSION_PATH`. The source defect does not depend
on that attribution and is sufficient to reject the exact signed bytes.

Candidate.21 is therefore immutable `NO_GO`. Its last digest-bound Gate F
snapshot remains historical `BLOCKED 5 PASS / 14 non-PASS / 0 FAIL`; the
snapshot is not rewritten into a fabricated FAIL count. Gate G and publication
remain unauthorized.

## Evidence

| Record | SHA-256 |
|---|---|
| `evidence/013EV-candidate21-service-availability-no-go/013EV-candidate21-service-availability-no-go.json` | `e42db102d5c8daeea049dc2ca3055eb59faf23e4e549e3291bbe9345fa1dc83b` |

The record binds:

- the exact candidate.21 four-repository tuple and Gate F snapshot;
- candidate and corrected Windows service source blob identities;
- fix/main ancestry and the passing hosted job;
- the limited VM observation and explicit attribution ceiling;
- `1.2.0+4051` / candidate.22 as pre-candidate only.

## Verification

- `POKROV-app/scripts/run-tests.ps1 -OfflinePubGet`: `PASS` for the
  build-4051 client tree later committed as `b51b4cf`; Flutter package/app
  suites, Android Gradle unit tests and native Windows service tests completed.
- `POKROV-app/scripts/validate-seed.ps1` with this platform projection and
  bound Core `cd8f0f4169d570d693992a959d81d17c2c44884d`: `PASS_LOCAL`.
- `python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py
  tests/test_agent_context_packet_audit.py -q`: `32 passed`.
- `python scripts/agent_context_packet_audit.py --platform-context-root .`:
  `PASS platform-context`.
- Sibling-promotion-line tests and hosted exact-ref replay remain required
  after both coordinated commits exist remotely; they are not claimed here.

## Completion index and next boundary

`REL_GATE/GATE-F` stays `I3` and changes status from an active candidate.21
blocked snapshot to retained candidate.21 `NO_GO`. `REL/WIN-003` retains its
narrow candidate.21 `I4` history but transfers no credit to candidate.22.
The overall distribution remains `I4=7`, `I3=320`, `I2=19`, `I1=32`, `I0=0`
across `378` rows.

The next release action is to merge the coordinated build-4051 source
projection, freeze current platform/client/Core revisions and construct a new
private candidate.22. Only its exact Windows package may receive VM continuity
or recovery credit. No tag, public asset, Store object, stable pointer or
production runtime state changes in this work order.
