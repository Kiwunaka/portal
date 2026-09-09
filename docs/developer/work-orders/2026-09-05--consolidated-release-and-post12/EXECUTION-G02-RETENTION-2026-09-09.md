# G02 — candidate.33 preserved with per-artifact retention

**VERIFIED / I3 for R12-G02.** Current-origin read-only inventory and GitHub
artifact downloads on 2026-09-09. This fulfills the preservation DoD; the full
release remains blocked. Candidate.33 is not a substitute for the new source
tuple or a new exact candidate.

Client-owned evidence is retained at
`POKROV-app/docs/operations/evidence/2026-09-09-r12-candidate33-retention/`.
[Receipt binding](evidence/g02-retention-20260909.json) pins its client commit
and exact receipt SHA-256. The canonical client cutover document links it.

- All 24 files in the original local candidate directory remain. Twenty-one
  match previously pinned hashes, including six binaries, handoff, manifest,
  signature, receipt, SBOM, provenance and signing/supply evidence. Three
  auxiliary files are inventoried with newly observed hashes only.
- All five named CI artifacts were available and downloaded. Each archive
  SHA-256 matches GitHub; eight members passed CRC and local hashing. Signer
  manifest/signature/receipt match the old local files byte for byte.
- Both Core SBOM files match the exact candidate provenance. Five dependency
  manifests remain recoverable from the retained source commits without new
  worktrees: two match Git blob bytes, three match original Windows CRLF bytes.
- Client CI run `33849479969` currently lists zero artifacts. No remote client
  build artifact is claimed available; no prior expiry/deletion is inferred
  from that empty listing. Its exact local candidate binaries remain present.

## Individual hosted deadlines

| Artifact ID | Content | Actual expiry UTC |
| --- | --- | --- |
| 9928470408 | Signed manifest, detached signature, receipt | 2026-09-18 08:01:25 |
| 9729751245 | Core source SBOMs | 2026-09-13 09:17:34 |
| 9729813473 | Core Apple receipt | 2026-09-13 09:22:10 |
| 9729818862 | Core Windows receipt | 2026-09-13 09:22:34 |
| 9729821940 | Core Android receipt | 2026-09-13 09:22:47 |

These are fresh API values, not one deadline extrapolated across all artifacts.
Original archives and extracted bytes remain at `E:/r12-g02-retention-20260909`;
candidate files remain at
`E:/POKROV-tools/release-candidates/pokrov-1.2.0-candidate.33`. Preserve both
directories during cleanup. GitHub expiry does not describe local file lifetime;
indefinite local retention is not claimed. Only 67,934 archive bytes were
downloaded; existing candidate binaries were neither copied nor rebuilt.

## Commands and limits

`python -B E:/r12-g02-retention-20260909/retain-remote.py` completed five
downloads. `python -B E:/r12-g02-retention-20260909/check-local.py` passed all
21 pinned files, three remote/local signer matches and seven dependency
bindings. The actual collectors and hash reports are preserved in client evidence.

Client `scripts/validate-seed.ps1` with explicit platform/Core roots passed,
including hygiene/docs contracts. The existing clean Core checkout selected
the client-bound `02a091c` temporarily and was restored to `c7a11f7`; no new
checkout was made. Client `git diff --check` passed and `artifacts/releases/**`
has no delta. The client evidence commit remains local because the branch's
required LFS upload is still subject to the owner's $0 limit.

No private signing key access/copy, signing, Ed25519 re-verification, native
build, release publication, production mutation or transfer of old runtime
PASS to a new candidate. The private signed manifest and signature stay in
local retained storage; only reports/hashes are added to source documentation.

Platform docs checks: `python -B -m pytest -p no:cacheprovider
tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`
— 33 PASS; `python -B scripts/agent_context_packet_audit.py
--platform-context-root .` — PASS; work-order `validate_package.py` — 83 R12 IDs,
378 retained legacy IDs and 414 local file links PASS. `git diff --check` PASS.
