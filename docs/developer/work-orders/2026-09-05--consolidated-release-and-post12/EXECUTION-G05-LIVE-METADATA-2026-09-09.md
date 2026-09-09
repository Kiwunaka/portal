# G05 — actual public, private candidate and development metadata

**VERIFIED / I3 for R12-G05.** Current-origin production HTTP and GitHub API
readback on 2026-09-09. Twenty-nine checks passed; no production or source
behavior was changed. [Receipt and exact retained bytes](evidence/g05-live-metadata-20260909/receipt.json)
bind the responses, collector and results.

## Observed owners

| Owner/surface | Observed state |
| --- | --- |
| Production `/api/public/client-apps` | Android/Windows 1.1.6, four APK variants and one Windows installer; ARM64 primary; no Play URL |
| GitHub `Kiwunaka/pokrov/releases/latest` | Public, non-draft, non-prerelease `v1.1.6`; six seeded binaries match URLs, reported SHA-256 and sizes; eight total assets including manifest/checksums |
| Client `release-handoff.seed.json` | Public 1.1.6; development 1.2.0+4053, `PRE_CANDIDATE_LOCAL`, `candidate_created=false` |
| Client `artifacts/releases/release-handoff.json` | Retained schema-v1 public pointer at 1.1.6; SHA captured, no modification |
| Client `cutover-readiness.seed.json` | Separate existing private candidate.33/build4053 with its old four-source tuple; public/promotion/stable-pointer flags false |
| Candidate signer artifact `9928470408` | Present, unexpired, digest and index source match that private candidate owner |
| Client `runtime-artifacts.seed.json` | Untagged Core 1.1.0 bound to `02a091c`, not the private candidate's `cd8f0f4`; candidate/promotion flags false |
| GitHub Core public release | `v1.0.3`; lookup of tag `v1.1.0` returns 404 |

The authenticated release listing returned 23 entries in one complete page,
including drafts visible to the owner. None belongs to 1.2.0/candidate.33.
The full listing remains locally retained; the committed scoped projection
records its hash, count and empty target match without copying unrelated draft
metadata. The new development candidate is not created by this audit.

The same build number in the development owner and candidate.33 does not imply
the same bytes. Their source identities and owner purposes stay separate.
The continuing source heads observed here were platform `1bfb33e` and client
`de5d478`; neither is represented as the old candidate's build source or the
deployed production source. Runtime deployment identity was not audited here.

## Production checks

The public catalog's four Android variants and Windows installer match the
client public owner by URL, digest and byte size. Its release version and notes
point to the observed public release; no private candidate appears in the
response. Android ARM64 and Windows current-download routes return HTTP 307 to
the same public assets; redirects were inspected without downloading binaries.

A Windows query from development version 1.2.0 still reports public latest
1.1.6 with `update_policy=none`, avoiding a forced downgrade. An Android query
from 1.1.5 reports required update to the actual public 1.1.6. These are anonymous
production metadata reads, not authenticated install/update tests.

Production `release_manifest=null` is consistent with the retained legacy-v1
public pointer. It does not pretend that the private strict-v2 candidate
manifest is the public release. The new strict-v2 release still requires its
own future candidate and publication gates.

Windows candidate EXE `250622f7…3580` was read with `Get-AuthenticodeSignature`:
**NotSigned**, signature type **None**. Its SHA matches the candidate owner,
which says `SKIPPED_BY_OWNER_DIRECT_BETA_ONLY`. The separately retained Ed25519
manifest signature is not represented as Windows Authenticode or trusted
Windows signing. No signing key was read and no signing operation was run.

## Scope and commands

`python -B E:/r12-g05-live-metadata-20260909/readback.py` — **29 PASS**. Three
public catalog responses, two redirect targets, GitHub release/artifact/tag
readbacks and the owner/pointer hashes are retained. The named Authenticode
result binds the exact EXE SHA. API response bytes are preserved without text
normalization; no customer session or private profile was used.

The earlier G05 report left production readback and a new candidate readback
open together. The original G05 DoD requires accurate current state; it does
not require creating a successor candidate to prove `candidate_created=false`.
This observation closes G05 only. G07 final provenance/license obligations,
cross-repository CI, new candidate supply, runtime acceptance and release
promotion remain separate open requirements. No release, deploy, stable-pointer
mutation, binary upload or change of public version was performed.

Documentation checks: `python -B -m pytest -p no:cacheprovider
tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`
— 33 PASS; `python -B scripts/agent_context_packet_audit.py
--platform-context-root .` — PASS; work-order `validate_package.py` — 83 R12 IDs,
378 retained legacy IDs and 417 local links PASS; `git diff --check` — PASS.
