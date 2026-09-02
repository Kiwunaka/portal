# WO-013FA — candidate.22 connected-uninstall NO_GO and build-4052 correction

Status: `CANDIDATE22_IMMUTABLE_NO_GO_BUILD4052_PREFLIGHT_PASS_CANDIDATE23_PENDING`

Observed: `2026-09-02`

Production/public mutation: `NONE`

## Outcome

Run connected uninstall against the exact candidate.22 Windows setup after its
default, recovery, Smart-DNS and packaged-AWG slices passed. The immutable
candidate enters the run with the ordinary UI, automatic LocalSystem service,
one verified TUN and authenticated Germany egress.

The uninstaller returns `0`, removes the service and TUN, clears its uninstall
registry entry and restores ordinary RU egress. It does not terminate the
running UI. Thirteen loaded EXE/DLL files remain under the installation root.
Repeating with the setup-only force-close flag has the same result. This is an
exact-candidate failure, so candidate.22 is `NO_GO`; its earlier narrow PASS
results remain valid evidence but cannot authorize promotion.

## Source correction and VM preflight

Client commit `0a1ae312aed840174f3867357bb7ecfac5264f3b` on PR 67 adds a
bounded Inno uninstall contract:

- terminate the exact configured UI image before uninstall begins;
- abort initialization when that command cannot start or returns an unexpected
  result;
- stop the SCM service and wait up to 30 seconds for `Stopped` before deletion;
- remove the application directory only when it is empty.

Static packaging contracts and the complete local client test suite pass. The
exact local pre-candidate setup
`9aa6b0fd7e43338786a25c7f14b0bd06e04aed01e92e5f21869eb334b5973152`
is then installed in the isolated Windows 11 VM, launches the ordinary UI and
reaches one TUN. Connected silent uninstall leaves zero UI/service processes,
zero service registrations, zero TUN adapters, zero installed files, no app
directory and no uninstall registry entry, while ordinary RU egress returns.

This result is `PASS_PRE_CANDIDATE`, not candidate.23 credit. PR 67 must merge,
the platform truth must merge, and a new immutable signed candidate must be
built from those exact merged sources before the same scenario is repeated.

## Explicit environment boundaries

The VM exposes no usable guest sleep transition, so sleep/resume is
`BLOCKED_BY_ENVIRONMENT`, not PASS or FAIL. It has no global IPv6 address or
IPv6 default route, so the external IPv6/leak slice is
`BLOCKED_NO_IPV6_PATH`. Windows 10 and interactive SmartScreen remain
`NOT_RUN`.

## Completion index and next boundary

`REL/WIN-003` and `REL_DOD/DOD-04` retain `I4` because their earlier exact
candidate.22 network slices remain valid, but now carry the connected-uninstall
NO_GO boundary. `REL/WIN-004`, `REL_GATE/GATE-C`, `REL_GATE/GATE-F` and
`REL_DOD/DOD-20` remain `I3`; `OBS/OBS-036` records the sleep environment
block; `FRKN_AWG/AWG-07` and `FRKN_PLAN/W9-05` remain `I1`. Distribution stays
`I4=7`, `I3=320`, `I2=19`, `I1=32`, `I0=0` across `378` unique rows.

The WO-013EX Gate F snapshot remains immutable `BLOCKED 3 PASS / 16 non-PASS /
0 FAIL`; it is not regenerated for rejected candidate.22. Candidate.23 does
not yet exist. Gate G, public assets, Store upload and stable promotion remain
unauthorized.

## Evidence

- `evidence/013FA-candidate22-connected-uninstall-no-go/013FA-candidate22-connected-uninstall-no-go.json`;
- SHA-256
  `f4ef3356c1bdb9971568e0ed3c19efb4990002a0e81ce320a7985f75ea8944af`.
