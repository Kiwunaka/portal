# WO-013CY — candidate.13 final promotion audit

## Outcome

Revalidate the immutable candidate.13 supply chain against the current
promotion branches, make one honest promotion decision, and reconcile stale
candidate references in the execution ledger without transferring older
runtime evidence or weakening Gate F.

## Exact boundary

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.13` |
| Version | `1.2.0+4049` |
| Platform source | `7d983c0ab52e9c01f94da8916a6bca6a0039be8d` |
| Client source | `ce2581dd16d276d20eace7a56f0337c4b9319168` |
| Core source | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Current platform promotion head | `713079389b4056e8be89e4fea63925c787654d1a` |
| Current client promotion head | `75ba7e721cfee486f7189edd51de97aba2746722` |
| Current Core promotion head | `c1185faa998c69fd5164af415249c96c68ab61bd` |
| Current release-index head | `289e887c7ba0463ecdf357bd5e7fd531ace9de8f` |

The platform and client promotion-head deltas after the candidate source are
documentation/evidence only. The current Core promotion tree is byte-identical
to candidate Core even though the merge commit differs. None of these heads
silently replaces the signed source tuple.

## Revalidation

- the signed public-index manifest and detached signature validate against the
  current trusted key set;
- public-index unit tests pass `7/7`;
- the exact six-artifact supply-chain validator returns `PASS`, including the
  `349`-component SBOM, six-subject provenance and `8/8` Windows runtime files;
- the source preflight returns `READY_LOCAL_FREEZE` with zero pre-freeze
  blockers. Its `candidate_created=false` result is expected because that tool
  validates the source seed, not the separately signed candidate authority;
- candidate.13 remains `ACTIONS_ARTIFACT_ONLY` with
  `promotion_authorized=false`.

## Promotion decision

The decision is `PROMOTION_BLOCKED_GATE_F_NOT_RUN`, not `GO` and not a
manufactured `NO_GO` run. Gate F requires an exact ARM64 physical-install
binding and candidate.13 has none. Clean Windows connected TUN/DNS/recovery,
physical Android, current/Brain/RU origin refresh, provider payment E2E,
Operator OIDC/RBAC, legal/commercial approval, rollback and comparable
performance also remain non-PASS. Gate G is not authorized.

No tag, GitHub Release, public app asset, Store submission, runtime handoff or
stable pointer is created by this audit.

## Ledger reconciliation

Rows whose status or next action still named candidate.3, candidate.10 or
candidate.11 are rebound to candidate.13 where current evidence exists. Older
candidate results remain explicitly historical. The only bounded Phase 10
advances are the already-proved candidate.13 LDPlayer rows:

- `FRKN_PLAN/W3-02 -> I4` for exact AWG 3.1 -> AWG2 warm lifecycle proof;
- `FRKN_PLAN/W3-03 -> I4` for the bounded emulator traffic slice.

The broader physical, Windows, dual-stack, UDP, leak, endurance and origin
requirements remain open. XHTTP stays a post-1.2.0 TLS/CDN reserve lane;
Hysteria2 stays a default-off conditional lab.

Normalized evidence is retained at
`evidence/013CY-candidate13-final-promotion-audit/013CY-candidate13-final-promotion-audit.json`.
