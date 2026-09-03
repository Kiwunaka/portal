# WO-013FX — candidate.31 Brain single-file predecessor diagnosis

Status: `BRAIN_SINGLE_FILE_EXACT_PREDECESSOR_IDENTIFIED_GATE_F_UNCHANGED_NO_GO`

Observed: `2026-09-03T18:20:56Z`–`2026-09-03T19:13:13Z`

Production/public mutation: `NONE`

## Outcome

This append-only diagnosis corrects one statement in WO-013FV without rewriting
that historical record. The live `portal_bot/control_panel.py` is not unknown or
manual source. After applying the same CRLF-to-LF normalization to both sides,
its hash uniquely matches known Git revision
`1207b63f1574a15569594c5fdbb79e4c8dff553f` (`fix(api): bound managed profile
panel work`). The earlier no-match result compared the raw remote hash with
normalized Git blob hashes.

Candidate.31 expects the successor blob introduced by
`ca2aa1d300dd9ea90cfaf904df95c7b75dd412dc` (`fix first-run panel progress
persistence`). That revision is an ancestor of candidate.31 platform source
`84837ce68a028f0c81580a5f1beefddba584de6d`, and the expected blob does not
match the live file.

The deployed payload is therefore a mixed but fully identified Git state:
`196/197` files match candidate.31 and the remaining file exactly matches its
known predecessor. It is not the complete predecessor deploy: replay against
revision `1207b63…` matches only `193/197`, because four other live files already
contain later candidate.31 content.

This sharper diagnosis does not turn Brain green. Exact candidate.31 source
identity remains `FAIL 196/197`, so Gate F remains `NO_GO 2/17/1` with zero
validation errors. Candidate bytes do not change and this diagnosis alone does
not require a new candidate. Exact-source reconciliation still requires a
separately authorized production deploy followed by fresh source, readiness and
delivery probes.

## Exact boundary

| Item | Identity |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.31`, app `1.2.0+4053` |
| Operational id | `4ee73886c1a285526baf3b666d5845b426754d8bee9f48365d1550a6ece1dd79` |
| Platform | `84837ce68a028f0c81580a5f1beefddba584de6d` |
| Client | `7e3e771fe36333a75244cbfd828c60beb84c7ff1` |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release index | `6de47f0320c9262a5bd2d454f3edb83d557f33a4` |
| Manifest | `dd4e99166ac3ec2c566e7d44ee93324f15ae7b3b92df6b35ff35de7053691f9a` |

## File identity

| File/version | Normalized SHA-256 | Size / lines | Result |
|---|---|---:|---|
| Live Brain `control_panel.py` | `95491d3c4272c24bab38e81545b6c131572ea2b37240f89793f99ba1bb18e454` | `62104 / 1634` | observed |
| Git `1207b63…` | `95491d3c4272c24bab38e81545b6c131572ea2b37240f89793f99ba1bb18e454` | `62104 / 1634` | exact semantic-byte match |
| Candidate.31 / `ca2aa1d…` | `1444ea0342b68a3c724e9ac62a4f3bbfd2af849584f97d4c23d6c050a2474ebc` | `62739 / 1647` | mismatch |

All 21 unique known versions of the path were scanned. Exactly one normalized
hash matches the live file. The raw live SHA-256 is retained only as a digest;
remote content is not returned or stored.

## Whole-payload cross-check

| Source revision | Semantic matches | Mismatches | Result |
|---|---:|---:|---|
| Candidate.31 platform `84837ce…` | `196/197` | `control_panel.py` | `FAIL` |
| Predecessor `1207b63…` | `193/197` | four later API/catalog files | `FAIL` |

The second result prevents the broader but incorrect conclusion that Brain runs
the full predecessor revision. Together the probes prove a single-file lag
inside an otherwise candidate.31 payload.

## Gate and remediation

```text
brain_origin=FAIL
decision=NO_GO
required=19
pass=2
non_pass=17
fail=1
validation_errors=0
```

The current release action remains: under separate production authorization,
deploy the exact candidate.31 platform payload to Brain, then repeat exact
source, readiness, subscription and three consecutive enabled-delivery probes.
Only those fresh results can supersede the Gate F row. No production, database,
node, host-network, public-release or stable-pointer mutation occurs in this
work order.

## Verification

```text
candidate.31 Brain source probe -> 196/197; control_panel.py mismatch; FAIL
CRLF-normalized known-version scan -> 21 unique versions; one exact match at 1207b63
candidate expected blob -> ca2aa1d; 62739 bytes / 1647 lines; not live
live/predecessor blob -> 62104 bytes / 1634 lines; exact normalized hash match
whole predecessor payload probe -> 193/197; four later-file mismatches; FAIL
Git ancestry -> 1207b63 ancestor of ca2aa1d; ca2aa1d ancestor of candidate platform
Gate F -> unchanged NO_GO 2/17/1; validation_errors=0
```

## Evidence digest

| File | SHA-256 |
|---|---|
| `013FX-candidate31-brain-predecessor-diagnosis.json` | `234c00979c352c3ba431a015a17735d827797b7e2692096423ddd748328d06ee` |

Private raw probe reports remain under
`E:/POKROV-tools/release-evidence/1.2.0-candidate31-origin-refresh-2026-09-03/`.
Their retained digests are present in the tracked evidence record. No secret,
remote content, raw response body, address or credential is retained.
