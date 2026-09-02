# WO-013EJ — candidate.21 Smart DNS signed-source and live direct-contract binding

Status: `CANDIDATE21_SIGNED_SOURCE_AND_LIVE_DIRECT_SMART_DNS_CONTRACT_PASS_IN_APP_MATRIX_OPEN`

Observed: `2026-09-02`

Production/public mutation: `NONE`

## Outcome

Bind the already live, default-off Smart DNS laboratory to the exact signed
candidate.21 source tuple without changing the server, DNS, client settings or
release state. WO-013DG remains the deployment and real rollback/re-apply
authority. WO-013EI remains the signed-supply authority. This work order adds
current post-signing source, live-readback and isolated Windows 11 direct
contract evidence only.

Candidate.21 platform `e2608130e85d9a0f8fa4b920f46cf3d7679332c3`,
client `1e164586d741484b5ae8fb2ee267ef5dd813cadb` and Core
`cd8f0f4169d570d693992a959d81d17c2c44884d` remain the exact signed tuple.
Manifest/signature/receipt `ce0b8586...` / `ef474e6e...` / `aaa027cc...`
remain unchanged and `promotion_authorized=false`.

## Server-source binding

The live Smart DNS bundle source `650dc3f...` is an ancestor of the exact
candidate.21 platform source. Two independent builds from exact
`e2608130...` produce the same candidate-bound bundle SHA-256
`2b6f1782641022f591fd6f00db0fee5ad3934396c611d03389c1643d3a9e1b46`.
The rebuild verifier passes.

The live release bundle `cda97da1...` and the candidate.21 rebuild contain
eleven members. Nine runtime-contract members match byte-for-byte, including
the executable `05a4b663...`, policy `b6977f6f...`, both configuration
templates, bundle contract, systemd unit, notices and licenses. Only the
source-bound bundle manifest and README differ. Therefore candidate.21 binds
the exact live runtime behavior without falsely claiming that the whole ZIP,
whose provenance names an older source revision, is the same byte sequence.

## Current live readback

The exact candidate.21 operator source runs in `PLAN` mode against the owned
`it` node. No mutation occurs. It reads back the live release
`cda97da1...`, active and enabled service, root-owned runtime material, one
loopback PROXY-v2 listener on TCP/18443 and no non-loopback backend listener.

An install PLAN against an already active frontend fails closed at the
duplicate-transform boundary. The correct receipt-bound rollback PLAN then
proves the existing applied receipt, current candidate config/service hashes,
active public TCP/443 frontend, active Smart DNS route, loopback backend and
valid receipt backup. The plan remains read-only and does not execute the
rollback already proved by WO-013DG.

All four delegated authoritative nameservers return the one owned frontend.
The public DoH endpoint keeps trusted TLS and rejects an empty request with
HTTP 400.

## Exact candidate.21 Windows VM direct contract

The isolated Windows 11 VM repeats the bounded Smart DNS probe after
candidate.21 is created and signed. It does not log into the desktop, launch a
VPN, change a setting or exercise client selection.

- malformed DoH: HTTP 400;
- allowlisted ChatGPT A: HTTP 200, DNS `NOERROR`, one answer matching the
  current frontend;
- allowlisted ChatGPT AAAA: HTTP 200, `NOERROR/NODATA`;
- outside-policy A: HTTP 200, DNS `REFUSED`;
- ChatGPT, Gemini and Xbox: trusted TLS plus HTTP 403, 200 and 301
  respectively.

The ChatGPT 403 is an application-origin policy response after successful TLS,
not a transport failure. No answer address, device identifier or connection
material is retained.

## Release and index effect

`FRKN_SMART_DNS/SMARTDNS-01` remains `I3` with stronger exact signed-candidate
evidence. It does not advance to `I4`: in-app Smart DNS selection, physical
DoH, authenticated ChatGPT/Gemini/Xbox sessions, attribution,
leak/privacy/load, lifecycle rollback and the fresh named-origin aggregate are
still open. Gate F remains `NOT_RUN`; Gate G, tag, public assets, Store object,
stable pointer and promotion remain unauthorized and unchanged.

The ledger distribution remains `I4=7`, `I3=320`, `I2=19`, `I1=32`, `I0=0`
across `378` unique rows.

## Verification

- exact-source ancestry check: `PASS`;
- two candidate.21 Smart DNS bundle builds: byte-identical;
- candidate.21 bundle verifier: `PASS_LOCAL_IMMUTABLE_BUNDLE`;
- live backend install PLAN: active exact release, `mutation_performed=false`;
- receipt-bound frontend rollback PLAN: current route and receipt verified,
  `mutation_performed=false`;
- isolated Windows 11 direct contract:
  `PASS_EXACT_WINDOWS_VM_LIVE_SMART_DNS_CONTRACT`;
- normalized JSON parse: `PASS`.

## Evidence

- normalized record:
  `evidence/013EJ-candidate21-smart-dns-binding/013EJ-candidate21-smart-dns-binding.json`;
- normalized record SHA-256:
  `0282180a1af00f8bb8a00385b8b086f13ef395d087fb7493a333e399bbdd9ca8`;
- external Windows VM evidence SHA-256:
  `4146e4a61e866aa9ec9e41ada2d5c4535405cd6799814960ca2e9840e87f1ad3`;
- external evidence root:
  `E:/POKROV-tools/temp/candidate21-smartdns-binding-20260902`.

Tracked evidence contains no credential, private key, raw runtime material,
raw host, device identifier, answer address or customer/provider payload.
