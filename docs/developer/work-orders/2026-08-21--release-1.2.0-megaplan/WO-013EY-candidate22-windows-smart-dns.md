# WO-013EY — candidate.22 Windows in-app Smart DNS split path

Status: `PASS_EXACT_CANDIDATE22_WINDOWS_SMART_DNS_SPLIT_PATH_PHYSICAL_AND_AUTHENTICATED_OPEN`

Observed: `2026-09-02`

Production/public mutation: `NONE`

## Outcome

Exercise the existing default-off Smart DNS laboratory through the installed
candidate.22 Windows UI in the isolated Windows 11 VM. The test uses headless
guest control and does not take the host mouse. It selects the validated custom
DoH endpoint, direct DNS, external Smart DNS and both AI and Games purpose
routes, relaunches the application, connects the ordinary Germany profile and
proves the resulting split path.

The exact installed candidate remains `pokrov-1.2.0-candidate.22`, app
`1.2.0+4051`. Installed UI, service and Core hashes match the immutable Windows
manifest. The POKROV service is running, `tun0` and its default route are up,
an established selected-Germany gateway session exists, and an independent
general-traffic control uses the selected Germany exit.

For `openai.com`, `chatgpt.com`, `gemini.google.com` and `xbox.com`, the public
DoH endpoint returns one allowlisted answer with DNS `RCODE=0`, HTTPS 200,
`application/dns-message` and a trusted certificate. The connected Windows
system resolver returns the same owned Smart-DNS proxy for each selected
domain. TLS through that proxy validates for all four targets; observed status
codes are 403, 403, 200 and 301 respectively. The two 403 responses prove TLS
and target reachability only, not authenticated ChatGPT or OpenAI access.

The outside control `example.com` is refused by the dedicated Smart-DNS
endpoint with `RCODE=5` and zero answers, while the connected system resolver
returns ordinary non-proxy answers. This proves the bounded allowlist rather
than a second recursive DNS service. The application crash buffer stays empty.

After the run, the VM returns to `DNS=automatic`, VPN DNS transport, external
Smart DNS off, zero purpose routes and no `tun0`; the automatic service remains
running. No server, DNS zone, provider, candidate byte, public asset, Store
object or stable pointer changes.

## Exact evidence

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.22`, `1.2.0+4051` |
| UI SHA-256 | `40ce4cc4520709aa4714737776aea2ada4a2043d7a346ce3d708a07160b7d66c` |
| Service SHA-256 | `18191f195309460b9d72a4a91a3fc817f3b3610d32891858a0ddddedaae11fb6` |
| Core SHA-256 | `f284fa8841f1a45271874a7a05ed6093fb0e3efbdd03e00001edd046be708204` |
| Normalized evidence | `71af85512e29f2b573f8cca8295fbabd8ad2c586fa18d7fbadf3883a2d742592` |

The normalized record retains only exact public candidate identities, hashes,
booleans, counts and public HTTP/DNS result classes. It exports no raw profile,
credential, connection material, customer identifier or raw address.

## UI refresh observation

The runtime disconnect itself passes: the service removes the TUN, restores
the baseline and writes successful rollback/stop events. After the headless
test woke a sleeping VM display, the already-open Home screen retained its
green connected rendering for more than ten seconds; navigating to Rules and
back immediately rebuilt it as disconnected. Because this was observed after
headless window-message input and display wake, physical-input reproduction is
`NOT_RUN`. It remains an explicit manual false-green check and is not silently
converted into either a product PASS or a confirmed production defect.

## Completion index and next boundary

`FRKN_SMART_DNS/SMARTDNS-01` stays `I3` but advances from source/direct-endpoint
proof to exact candidate.22 Windows in-app selection, persistence and connected
split-path proof. `REL/WIN-003` and `REL_DOD/DOD-04` gain the same bounded
Windows evidence without changing their level. Gate F remains the immutable
WO-013EX `BLOCKED 3 PASS / 16 non-PASS / 0 FAIL`; this narrow slice does not
close the complete Windows, Android or cross-platform authenticated-session
rows and does not regenerate the decision.

Next priority remains exact candidate.22 packaged AWG3.1, then AWG2, on Android
and Windows, followed by physical Wi-Fi/Beeline Smart-DNS and authenticated
ChatGPT/Gemini/Xbox sessions. Reproduce the Home refresh observation with
normal physical input before the final false-green attestation.

## Evidence

- `evidence/013EY-candidate22-windows-smart-dns/013EY-candidate22-windows-smart-dns.json`;
- SHA-256
  `71af85512e29f2b573f8cca8295fbabd8ad2c586fa18d7fbadf3883a2d742592`.
