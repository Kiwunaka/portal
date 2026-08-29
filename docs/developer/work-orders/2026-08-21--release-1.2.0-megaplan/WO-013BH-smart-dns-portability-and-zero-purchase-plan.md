# WO-013BH — Smart DNS portability and zero-purchase topology PLAN

## Outcome

Make the owned Smart DNS bundle portable across the Windows release worktree
and run the guarded, read-only installer PLAN against every active delivery
node before considering any deployment.

The source fixes are complete and locally proved. Packaged text members now
use one explicit UTF-8/LF canonical form, so Git LF policy and a Windows CRLF
checkout produce the same contract digest. The policy parity checker applies
the same normalization and fails closed on BOM, invalid UTF-8 or lone carriage
returns. The remote installer also accepts the canonical underscore-bearing
node code `ru_spb` while continuing to reject unsafe path components.

Two clean Linux/amd64 builds from exact platform source
`8bdc21f9b89f4db037754ce6287dbfe21a1cc84f` are byte-identical. The resulting
inactive ZIP is `2912132` bytes with SHA-256
`dbd39d758b16ba433d6557e163cb3a538e19d40ad5145b1e4871a6a659f7afef`.
Its canonical policy SHA-256 is
`b6977f6f6a5ee48898116820d1db252b5b670cb7b86959c78f7bdbc7de90e0fa`.

The exact bundle was then used only for a no-mutation `install` PLAN against
all seven active node codes: `de`, `us`, `ru`, `ru_spb`, `pl`, `it` and `nl`.
Each PLAN resolved one owned public IPv4, found UFW active and no occupied
Smart DNS targets, but found TCP/443 already owned and runtime material absent.
Every report returned `mutation_performed=false`; no server, firewall,
frontend, routing, DNS or client state changed.

## Why there is no live zero-purchase deployment yet

The Smart DNS listener and opaque SNI relay require exclusive ownership of one
public TCP/443 endpoint. All currently active delivery addresses already use
that port. Overlaying the lab onto an existing frontend, adding an unreviewed
SNI multiplexer, or silently moving a live service would risk an outage and
would violate the guarded installer contract.

The owner's no-purchase decision is preserved. A purchase is not required by
this work order. The remaining zero-purchase route is to identify an already
owned address that can be deliberately freed, then approve a separate
receipt-bound migration/rollback plan. Until such an address exists, the safe
result is `NO_SAFE_ZERO_PURCHASE_TARGET_CURRENT_TOPOLOGY`, not a failed deploy.

## Exact source and checks

| Item | Exact identity/result |
|---|---|
| Text canonicalization fix | platform `64982d94dcbc71c39d685c2a5710438a5db3ad4f` |
| Canonical node-code fix | platform `8bdc21f9b89f4db037754ce6287dbfe21a1cc84f` |
| Client policy truth | client `b2497af7704d0aa6901541e175ce154b0eab05d7` |
| Focused builder/parity/installer tests | `20/20 PASS` |
| Focused Ruff | `PASS` |
| Go version | `go1.25.13 windows/amd64` |
| Go unit/source gate | `go test ./...` and `go vet ./...` `PASS` |
| Cross-repository policy parity | `PASS`, canonical SHA above |
| Deterministic bundle | two builds, same size and SHA above |
| Guarded active-node PLAN matrix | `7/7` contacted; `7/7` TCP/443 busy; `0/7` runtime material ready; `0` mutations |

The rejected aliases `free` and `mini` did not resolve to one enabled Brain
node and are not counted as active-node PLAN results.

## Release interpretation

- `FRKN_SMART_DNS/SMARTDNS-01` remains `I3`; source, immutable bundle and
  read-only topology evidence do not prove live service access or a candidate.
- This checkpoint removes the previous portability and active-node discovery
  unknowns. It does not remove the dedicated-address/runtime-material gate.
- No candidate, deployment, public artifact, tag, stable pointer, DNS answer,
  SNI relay, access, leak, rollback or origin claim is created.
- No purchase, billing change or repository-visibility change occurred.

## Required next evidence

1. Prove that one already owned public IPv4 can be freed without disrupting an
   active frontend, or leave the lab undeployed under the no-purchase policy.
2. For an approved address, retain the exact service-migration rollback plan,
   root-only runtime material and a fresh sanitized no-mutation PLAN.
3. Only after separate owner authorization, run guarded APPLY/rollback and
   retain distinct DoH, SNI attribution, service-access, leak, lifecycle and
   current/Brain/RU-origin evidence.

Machine evidence:
`evidence/013BH-smart-dns-zero-purchase-plan/013BH-smart-dns-zero-purchase-plan.json`.
Its SHA-256 is
`7758402ac727fe7602de02d7f07c6d3b4add0aee58f67d6fcabc653e43166eb0`.
It retains no address, hostname, credential, key, runtime configuration,
customer data or raw provider response.
