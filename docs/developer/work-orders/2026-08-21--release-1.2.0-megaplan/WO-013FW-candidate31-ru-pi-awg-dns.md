# WO-013FW — candidate.31 RU-Pi AWG3.1/AWG2 and Smart DNS

Status: `EXACT_CORE_AWG31_AWG2_AND_LIVE_SMART_DNS_RU_FIXED_PASS_PACKAGED_CLIENT_OPEN`

Observed: `2026-09-03T18:03:00Z`–`2026-09-03T18:11:50Z`

Production/public mutation: `NONE`

## Outcome

The owned Raspberry Pi 4 passes fresh exact-Core AWG3.1 followed by AWG2 over
its direct RU fixed-network route. The same origin also passes the existing
live default-off Smart DNS DoH policy and TLS paths for ChatGPT, Gemini and
Xbox. The owner workstation's mouse, keyboard, screen, route, DNS and active
tunnel are not used or changed.

This is exact candidate.31 Core source evidence plus current live Smart DNS lab
evidence. It is not a packaged Android/Windows run, not a candidate.31 Smart DNS
server/client binding, and not an authenticated application-session test.
WO-013FV remains the current Gate F authority at `NO_GO 2/17/1`.

## Exact boundary

| Item | Identity |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.31`, app `1.2.0+4053` |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Execution host | owned Raspberry Pi 4, Linux ARM64 |
| Origin | direct RU fixed network; physical location operator-attested |
| AWG order | `awg31_lab`, then `awg2_lab` |
| Client/runtime scope | source-level Core runner only |
| Smart DNS client state | disabled/default-off |

The interop runner materializes the exact committed Core module, compiles its
ARM64 test binary with the CI-pinned Go toolchain, loads only the current owned
lab material, verifies the direct route and exact remote binary digest, runs
the bounded test and removes all temporary Pi state. Raw material is never
returned or retained.

## AWG results

| Profile | Result | Binary SHA-256 |
|---|---:|---|
| AWG3.1 | `PASS` | `9596183b207e03e831778e01b7420d6fa8620aceb26ab3bd06745e8f699b915f` |
| AWG2 | `PASS` | `5a868a9683a126aea9948be07c8aaa43944dd533d4ff3eab72fe262f73186eba` |

Both reports bind the exact Core revision, Linux ARM64 host class, direct
default-route preflight, immutable tool identities, no runtime/server mutation,
no raw material return and successful temporary-state removal. The local temp
root is empty after both runs.

This supersedes candidate.29's later Pi observation for current availability
without erasing it. It does not transfer source-level PASS into packaged
candidate.31 Android or Windows runtime.

## Smart DNS result

The same Pi origin executes the retained live probe against the default-off
owned Smart DNS service:

| Check | Result |
|---|---:|
| Malformed DoH GET | `HTTP 400` |
| Allowlisted `A` | `HTTP 200`, `NOERROR`, one owned-proxy answer |
| Allowlisted `AAAA` | `HTTP 200`, `NOERROR/NODATA` |
| Outside-policy `A` | `HTTP 200`, `REFUSED` |
| ChatGPT TLS | verified; `HTTP 403` application-policy response |
| Gemini TLS | verified; `HTTP 200` |
| Xbox TLS | verified; `HTTP 301` |

The ChatGPT response proves successful TLS and application reachability, not
an authenticated session. The temporary probe file is removed and no matching
Pi temp file remains.

## Release interpretation

- Candidate.31 exact-Core AWG3.1 and AWG2 RU fixed-network source-level
  evidence: `PASS`.
- Live RU fixed-network Smart DNS transport/policy: `PASS` for the existing
  default-off lab.
- Packaged Android/Windows AWG and Smart DNS: still `NOT_RUN` or manual.
- General RU-origin manifest/authenticated-client row: unchanged non-PASS.
- Gate F: unchanged exact `NO_GO 2/17/1` because Brain source drift remains.

No deploy, service restart, database write, firewall change, public release,
Store submission, stable-pointer change or Gate G authorization occurs.

## Evidence

- normalized record:
  `evidence/013FW-candidate31-ru-pi-awg-dns/013FW-candidate31-ru-pi-awg-dns.json`;
- normalized record SHA-256:
  `b924dfe4902c665fe511243317f4f3b711a231d1ae1c959559e08d86f924af7d`;
- AWG3.1 external report SHA-256:
  `38c287c5fb4d51f2de687e1c2fc4848c1f918eeba2b6abf5b0dfcc757c5ba836`;
- AWG2 external report SHA-256:
  `b385a8055e7559f8ca246df79acce5a5f1ee638920929b94e769ba265fcf1817`;
- Smart DNS probe SHA-256:
  `37fa5ee0c518f829b6348e87661ed7e200fe1cf43473d74ad8dbbdf71774a5ed`.

Private raw AWG reports remain under
`E:/POKROV-tools/release-evidence/1.2.0-candidate31-pi-awg-core-interop-2026-09-03/`.
Tracked evidence contains no credentials, private key, raw connection material,
address, response body or device identifier.
