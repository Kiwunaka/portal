# WO-013DG — Smart DNS `it` live deployment and rollback proof

Status: `LIVE_CURRENT_RUNTIME_PASS; FULL_ROLLBACK_PASS; CANDIDATE16_BINDING_OPEN`

Observed: `2026-08-31T17:46:27Z`

## Scope

Publish the owner-authorized `dns.pokrov.space` DNS-only record, prepare a
trusted certificate and root-only runtime material on the owned foreign `it`
node, install the exact immutable Smart DNS backend behind the existing owned
HAProxy TCP/443 frontend, prove bounded DoH and Smart Access behavior from
three distinct origins, execute a real receipt-bound rollback/re-apply drill,
and retain the final live state without enabling client selection.

No physical device, client rollout, Store object, public `v1.2.0`, stable
pointer, unrelated frontend, ordinary VPN route or release promotion is in
scope.

## Exact boundary

| Item | Value |
|---|---|
| Signed release context | `pokrov-1.2.0-candidate.16`, `1.2.0+4049` |
| Candidate.16 platform source | `719e23dc49407beb9ae30d98d17d4b73d18ae37c` |
| Current platform source after operation corrections | `6ab381aafa9ea0564aa41399272331f0474c67f4` |
| Smart DNS bundle source | `650dc3fab8053736cfb976d4a34ea1f2f0b40349` |
| Bundle | `pokrov-smart-dns-650dc-a.zip`, `2916305` bytes |
| Bundle SHA-256 | `cda97da16a892c1a8563bd20434cd749a2174c192ba722147091a3e1c14a0225` |
| Policy SHA-256 | `b6977f6f6a5ee48898116820d1db252b5b670cb7b86959c78f7bdbc7de90e0fa` |
| Owned node | `it` |
| Public endpoint | `dns.pokrov.space` on shared TCP/443 |
| Backend contract | loopback TCP/18443, mandatory PROXY protocol v2 |
| Client state | external Smart DNS selection disabled/default-off |

The user explicitly authorized the DNS record, ACME certificate, runtime
preparation, service installation, frontend route, rollback drill and live
probes. That authorization did not authorize client rollout or release
promotion.

## DNS and runtime material

All four delegated Timeweb authoritative nameservers returned the single
owned-node A value. The guarded runtime APPLY then proved unique DNS-to-node
matching, reachable authenticated DoT upstream, temporary TCP/80 handling,
server-side certificate issuance, at least fourteen days of remaining
certificate validity, installed Certbot renewal support and root-only runtime
material. The private key and raw runtime material never left the node.

Runtime receipt: `20260831T170628Z-458712-cda97da16a89`.

## Installation corrections and fail-closed retries

Three early backend APPLY attempts failed before a live route was exposed.
Each automatic cleanup returned the service boundary to its safe state. The
observed causes were fixed as narrow operator-contract changes:

- platform PR 132 resolves public DNS through the authenticated Brain origin
  instead of the operator workstation's ambient resolver;
- platform PR 133 permits reuse only of a fully verified retained exact
  release and records root-only phase markers;
- platform PR 134 exposes the listener-check phase without returning runtime
  material;
- platform PR 135 waits for one exact loopback listener for at most ten
  seconds and still fails immediately on multiple listeners.

The focused final source pack passes `80/80`. Hosted jobs for these platform
PRs exposed zero executable steps because of GitHub billing and are retained
as `HOSTED_CHECK_BLOCKED_BY_BILLING`; each merge used the authorized
`OWNER_SOLO_EXCEPTION` after local proof. No hosted result is called PASS.

## Final live topology

The backend installation passes with the exact retained release, active and
enabled service, one loopback TCP/18443 listener, mandatory PROXY v2, local
TLS/DoH negative probe and no public-firewall mutation. Final backend receipt:
`20260831T174516Z-461080-cda97da16a89`.

HAProxy validates and applies runtime candidate configuration
`1b5b0be8ab45b2ca8d5a3ea39f8c1dbfefbe5eea85b8b822a956e0c569cf1eac`
over verified base
`e7097ec42d41d06533cb535d8a0ef8234f852e11cf01cbfbce837c6b83317239`.
The route contains 19 application suffixes, 20 exact SNI entries and 19 child
SNI entries while preserving the existing default backend. Final frontend
receipt: `20260831T174557Z-459908-1b5b0be8ab45`.

The final rollback PLAN proves the frontend and service active, public TCP/443
listening, the Smart DNS route present, the backend listening only on loopback,
the exact release digest loaded and the receipt backup valid.

## Full rollback and re-apply

The real drill removed the frontend route using its applied receipt, rolled
back the backend using its exact successful receipt, and proved the service
inactive with TCP/18443 free while retaining only the immutable release.
The retained release was reverified before reuse. Backend and frontend were
then re-applied under new receipts, followed by the final rollback PLAN above.

This is a real deployed-environment rollback proof for the exact current
bundle and current frontend state. It is not candidate.16 application/client
rollback proof.

## Live behavior from three origins

Fresh post-drill probes passed from `current-origin`, `brain-origin` and the
owned Raspberry Pi `RU-origin`:

- malformed DoH GET returns HTTP 400;
- allowlisted `chatgpt.com A` returns DNS `NOERROR` with one owned-proxy
  answer;
- allowlisted `AAAA` returns `NOERROR/NODATA`;
- outside-policy `example.com A` returns `REFUSED`;
- SNI passthrough verifies TLS 1.3 for ChatGPT, Gemini and Xbox;
- Gemini returns HTTP 200, Xbox returns HTTP 301, and ChatGPT reaches the
  application origin but receives its HTTP 403 policy response.

The HTTP 403 is not transport failure: certificate verification, TLS and the
application response all complete. It does not prove an authenticated ChatGPT
session or every application endpoint.

The production node record remains enabled and healthy after the drill with
healthy capacity, edge reachability and dataplane. This bounds the change
against the existing ordinary `it` route; it is not a broad user-session or
load test.

## Release decision

`FRKN_SMART_DNS/SMARTDNS-01` remains `I3`, with status advanced from local
readiness to `LIVE_CURRENT_RUNTIME_PROVEN_CANDIDATE16_BINDING_OPEN`. The live
server source and bundle were created after the immutable candidate.16
platform source, and client selection remains disabled. Therefore this result
cannot be relabelled as candidate.16 `I4`, cannot clear Gate F and does not
authorize Gate G, public assets, Store publication or the stable pointer.

The next release-bound Smart DNS step is to bind the exact server/client
contract into a successor candidate if Smart DNS is required for 1.2.0, then
repeat the candidate-specific client, leak/privacy, authenticated-service and
rollback matrices. Otherwise the proven service remains a default-off live
lab and candidate.16 proceeds on its already declared base release gates.

## Evidence

- normalized record:
  `evidence/013DG-smart-dns-it-live-and-rollback/013DG-smart-dns-it-live-and-rollback.json`;
- normalized record SHA-256:
  `5a54f6d2e7a58d5595ee2c6b202f2bcad9303845c2f5ea09667fdac4adc00ea8`;
- authoritative DNS SHA-256:
  `d53f57cb5f3fbfaf224e8b4e8aec4a5f17c6a72c63050a7bbb2b5682d79a5939`;
- runtime APPLY SHA-256:
  `0ee584b42c05acc4d744fe93ae21753258ddc13294a234bc5f2643c9190e39e3`;
- final backend re-APPLY SHA-256:
  `ab4302f8f6642a9d61cbb2ed66f6834b9fa037aaa4a8e1644ea0468b7f92f79a`;
- final frontend re-APPLY SHA-256:
  `5ca48f5fb25fc923a76114ea3284d9dab1c9212cd728a3ff8ec8175d6a101c1e`;
- final rollback PLAN SHA-256:
  `c6ded1261cfd4e75c980d694cf4971ec287df8b8a8b2f5facdda30485c3b7a66`;
- current/Brain/RU final probe SHA-256:
  `0770af3e3088c1f29ea93b076a37e28c80c92fba1c0e058b56206d013810a6fc` /
  `75df7d1eae47431ecdbe28bad0f526e5deddf522194344ee6efa4cefbdccb99d` /
  `ff00a7bd8f09d40e83b3d971313df31cdb97b8e3ec6f16c34d5293c3e4b43254`;
- post-drill node-health SHA-256:
  `c960578c7f18562495424c5479aa43a535a0ce0a337feece196ef0967ae5b82b`.

The external evidence root remains outside Git. Tracked evidence contains no
credential, private key, raw runtime material or device identifier.

## Collision and handoff

The isolated platform worktree started clean at current `origin/master`. The
root checkout contains an unrelated older-base edit to the private-chat
section of `docs/operations/deployment-and-access.md`; this WO changes only the
later Smart DNS section and preserves that checkout untouched.

Final live state: Smart DNS backend and frontend route are active on `it`, the
exact rollback receipts are retained, and client selection is disabled.
