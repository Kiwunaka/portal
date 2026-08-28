# WO-013AW — Free GitHub policy and repository-publication preflight

## Outcome

The owner's final policy is retained: buy no GitHub plan, require no protected
branch, and use `OWNER_SOLO_EXCEPTION`. The intent is to make the POKROV
repositories public, but it does not make an unsafe direct visibility flip a
release prerequisite.

`Kiwunaka/pokrov-core` and `Kiwunaka/pokrov` are already public.
`Kiwunaka/portal` and `Kiwunaka/POKROV-app` remain private because a redacting
all-reachable-history preflight found unresolved publication hazards. No
matched value or source snippet was retained in evidence.

## Evidence and interpretation

The dedicated local scanner covered fetched refs and every reachable blob up
to a four-MiB content cap. It is deliberately conservative. A pattern hit is a
review signal, not an assertion that a real live credential exists.

- Platform: 18,849 reachable objects, 10,047 blobs, 157 conservative blocker
  patterns, 144 review findings and 11 oversized blobs. Test fixtures account
  for most high-confidence shapes, but operational documents, raw historical
  datasets and private facts still need an allowlisted export review. The
  repository has no publication license.
- Client: 6,787 reachable objects, 3,026 blobs, 16 conservative blocker
  patterns, 99 review findings, six oversized blobs and 80 tracked release
  artifact paths across APK/AAB/EXE/DLL/SO/ZIP classes. The high-confidence
  paths observed are tests, but bundled binaries, asset rights, dependency
  licenses and the missing root license still block a direct visibility flip.
- Core: already public with a license. Its conservative matches are confined
  to parser/generator/test/testdata paths and are retained for maintenance
  triage; nothing here is represented as a newly discovered live secret.
- Release index: already public and passes this pattern gate with zero
  findings.

The normalized evidence is
`evidence/013AW-publication-preflight/013AW-publication-preflight.json`.
Detailed local scanner reports remain outside Git because even redacted
history inventories should not enlarge the public surface without need.

## Decision

Do not turn the two current private repositories public wholesale. This does
not reverse the owner's public-source direction. Use the existing rollout
order:

1. finish the exact 1.2.0 release gate under the free solo policy;
2. create a sanitized, source-only public client successor;
3. add `GPL-3.0-or-later` plus an explicit POKROV brand/trademark boundary,
   after dependency and asset-rights review;
4. prove a clean-clone build and visible public CI;
5. publish a sanitized platform successor later instead of exposing its
   operational history.

No billing, repository, visibility, branch-protection, tag, release or stable
pointer mutation occurred in this work order.
