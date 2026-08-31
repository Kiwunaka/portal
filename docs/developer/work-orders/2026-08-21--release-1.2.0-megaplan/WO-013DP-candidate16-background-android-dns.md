# WO-013DP — candidate.16 background Android DNS reachability

Status: `LDPLAYER_DIRECT_DOH_POLICY_PASS_PHYSICAL_OS_DNS_PASS_CLIENT_INTEGRATION_NOT_RUN`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `10/11`
Candidate: `pokrov-1.2.0-candidate.16`
Production/external mutation: `NONE`

## Outcome

Use only background Android SDK ADB shell commands on the owner phone and
LDPlayer. Do not launch POKROV, start a VPN, change a device setting, take
screen control or retain a raw device identifier.

Both authorized devices report installed `1.2.0+4049`, resolve the public
`dns.pokrov.space` name and complete one hostname ICMP control. The physical
Android 12 ARM64 device has no POKROV process and no `tun0`. It exposes only a
system `ping` tool, so a direct DoH request is honestly
`NOT_RUN_TOOL_ABSENT` rather than a connection failure.

LDPlayer Android 9/x86_64 has no `tun0`. Its existing package process is
present from prior state and is not launched or manipulated by this slice.
Direct `curl` over trusted TLS reaches the Smart-DNS DoH endpoint:

| Query class | HTTP | DNS result | Answers |
|---|---:|---|---:|
| outside-policy control | `200` | `REFUSED` | `0` |
| ChatGPT | `200` | `NOERROR` | `1` |
| Gemini | `200` | `NOERROR` | `1` |
| Xbox | `200` | `NOERROR` | `1` |

An intentionally empty DoH request returns HTTP `400`, confirming the existing
fail-closed malformed-request boundary. No answer address is retained.

## Evidence and ceiling

Normalized evidence:
`evidence/013DP-candidate16-background-android-dns/013DP-candidate16-background-android-dns.json`.

SHA-256:
`d55fcc6dcfb803c55649476868dec4f023d79baa44f79b1c94a0de67c8d30cb2`.

This proves direct Android-emulator DoH TLS reachability and the bounded
policy-response shape, plus physical-OS hostname reachability. It does not
prove the client Smart-DNS setting, VPN integration, an authenticated
ChatGPT/Gemini/Xbox session, physical-phone DoH, attribution, leak/privacy,
load, lifecycle, rollback or candidate binding of the post-sign server work.

`FRKN_SMART_DNS/SMARTDNS-01` stays `I3`. Candidate.16 Gate F remains
`NO_GO 2/17/2`; Gate G, publication, Store and stable state remain unchanged.

## Verification and mutation boundary

```text
physical Android package/process/tun readback -> PASS bounded clean state
physical hostname DNS+ICMP -> PASS
LDPlayer package/tun readback -> PASS bounded no-TUN state
LDPlayer malformed DoH -> expected HTTP 400
LDPlayer valid DoH policy matrix -> 4/4 expected response shapes
JSON parse -> PASS
git diff --check -> PASS
```

No app launch, VPN start, device setting, screen input, server, DNS, provider,
database, Operator, release artifact or stable pointer is changed. The next
client-integrated Smart-DNS test remains deferred until it can run without
taking the owner's active UI; physical DoH needs an existing non-UI network
tool or a separately approved test harness.
