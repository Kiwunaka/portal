# WO-013BQ — candidate.6 LDPlayer IPv6 family-block proof

## Outcome

Use the exact signed candidate.6 x86_64 install to determine whether an
IPv4-only Android TUN can release IPv6 onto LDPlayer's underlying network.
This follows WO-013BP without changing the installed artifact or candidate.

The emulator had two global IPv6 addresses and 25 IPv6 default-route entries
across Android policy-routing tables before the run, so the structural check
was not performed on an IPv6-disabled host. WARP was enabled through the owner
UI and `Повторить` started the existing exact-candidate connection path.
POKROV service and TUN were both observed. The TUN had an IPv4 address and
IPv4 default route, but no IPv6 address and no IPv6 default route.

## Fail-closed contract

Exact client revision `b2497af7704d0aa6901541e175ce154b0eab05d7`
contains no `VpnService.Builder.allowFamily(...)` call. Its Android route
planner adds a family default route only when that family has a TUN address;
the IPv4-only plan is also covered by the focused route-planner test.

Android's official `VpnService.Builder.allowFamily` contract states that an
address family with no configured VPN address, route or DNS server is blocked
by default; explicit `allowFamily` is what permits fall-through to the
underlying network. The source and observed TUN shape therefore prove
`PASS_STRUCTURAL_ANDROID_IPV6_FAMILY_BLOCK` for this exact LDPlayer slice.

This is not an external IPv6 leak PASS. No external IPv6 endpoint, DNS/SNI
attribution, physical carrier or OEM behavior was exercised. WARP still ended
at the common LDPlayer current-origin egress boundary rather than a protocol
PASS or FAIL.

## Restore and evidence ceiling

After the failed egress check, POKROV stopped its service and removed the TUN.
WARP was explicitly disabled again. Final readback is WARP off, no service and
no TUN. The physical phone remained absent from ADB and was not mutated.

- `REL_GATE/GATE-C` remains `I2` with stronger exact-candidate structural
  IPv6 fail-closed evidence.
- `REL_GATE/GATE-F` remains `I3` at WO-013BM's
  `3 PASS / 16 non-PASS / 0 FAIL`.
- Physical candidate.6 DNS/IPv6 leak, WARP/AWG/per-app traffic, handoff,
  OEM/lifecycle/endurance and Windows parity remain open.

Normalized evidence is
`evidence/013BQ-candidate6-ldplayer-ipv6-family-block/013BQ-candidate6-ldplayer-ipv6-family-block.json`.
It retains no device serial, runtime address or runtime endpoint hostname,
credential, key, raw config, customer data or provider payload.

Official platform contract:
<https://developer.android.com/reference/android/net/VpnService.Builder#allowFamily(int)>.

## Validation

- Exact client direct-release `AndroidTunRoutePlannerTest`: `PASS`.
- Platform documentation contracts: `32/32 PASS`.
- Execution ledger: `378` rows, zero duplicate keys, zero invalid indexes.
- Context audit and public link check: `PASS`.
- New evidence secret-pattern and raw-IPv4 scan: zero matches.
- `git diff --check`: `PASS`.

The first generic Android unit-test task was rejected before test execution
because both direct and store flavors exist. The exact direct-release task was
then selected and passed; the rejected command is not a product failure.
