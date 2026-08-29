# WO-013BJ — Smart DNS AI/gaming contract coverage

## Outcome

Close the source-level proof gap between the canonical Smart DNS policy and
the owned resolver tests. The policy and client already contained the selected
ChatGPT/OpenAI, Gemini and Xbox service domains, but the resolver's synthetic
`A` response test exercised only an OpenAI child domain.

Platform `84f16dd37ad406905c12de0425bdef7b95e77ed4` now proves that the
resolver loads the canonical policy, accepts exact and child Gemini/Xbox names,
returns the owned proxy IPv4 for representative OpenAI, Gemini and Xbox `A`
queries, refuses an outside lookalike and keeps the existing NOERROR/NODATA
behavior for `AAAA`, `HTTPS`, `SVCB` and other query types. No domain was added
and no production behavior, topology or cryptography changed.

## Exact source and artifact verification

- platform: `84f16dd37ad406905c12de0425bdef7b95e77ed4`;
- client: `b2497af7704d0aa6901541e175ce154b0eab05d7`;
- canonical/client policy SHA-256:
  `b6977f6f6a5ee48898116820d1db252b5b670cb7b86959c78f7bdbc7de90e0fa`;
- policy groups: `11` AI suffixes and `8` gaming-service suffixes;
- Go `1.25.13` test/vet: `PASS`;
- focused Smart DNS builder/installer/parity tests: `23/23 PASS`;
- client routing/preferences test: `17/17 PASS` on Flutter `3.38.5` and
  Dart `3.10.4`;
- cross-repository canonical policy parity: `PASS`;
- two exact-source bundles are byte-identical: `2912450` bytes, SHA-256
  `93d4a743666d231c41530ae751386983f7f995b3a295d8915321e58f7e31166a`.

## Release interpretation

- `FRKN_SMART_DNS/SMARTDNS-01` remains `I3`.
- This is `PASS_SOURCE_CONTRACT_ONLY`; it proves selected policy
  materialization, not real service availability.
- The strict v3 topology result from `WO-013BI` remains current: all active
  TCP/443 scopes are occupied and no safe zero-purchase deploy target exists
  without a separately reviewed frontend migration and rollback.
- No candidate, deploy, DNS/SNI relay, ChatGPT/Gemini/Xbox access, leak,
  lifecycle, rollback, origin or promotion proof is created.

Machine evidence:
`evidence/013BJ-smart-dns-ai-gaming-contract/013BJ-smart-dns-ai-gaming-contract.json`.
Its SHA-256 is
`a3a11b7a5a52621f0b338e27fe972b49c031e3fd1abe28d1b2be9cb33530f747`.
It contains no address, hostname, credential, key, runtime material, customer
data or raw provider response.
