# WO-013AV — Candidate.5 Gate F, current-origin and Brain-origin

## Outcome

Signed `pokrov-1.2.0-candidate.5` remains immutable. Its digest-bound Gate F
decision is now `BLOCKED`, with `6/19 PASS`, `13/19 non-PASS`, `0 FAIL` and
zero validation errors. This is stronger than the historical candidate.3
`NO_GO`, but it is not release authorization and does not authorize Gate G.

The two origin rows closed independently:

- current-origin API health and public-catalog p95 budgets pass after the
  deploy;
- Brain matches the exact platform candidate payload `197/197`, readiness
  passes `23/23`, and all seven enabled delivery nodes expose their configured
  TCP port from Brain.

No tag, public release, store object or stable pointer was created.

## Exact identity

| Component | Revision or digest |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.5` |
| Operational ID | `ff8ab3bf0289f920c70adddbd0d33cf8d2f0d8fd8f5d4896300ab7c410074e2a` |
| Platform source | `6ea08e9222dff67c93ffa0bb9585a57c5ffe220c` |
| Client source | `6b596cefbc043c2da30b31007789cea7e30fc336` |
| Core source | `e8eb7721fc6eaac6813d3a888ac90d0da1f541a1` |
| Release-index input | `1d1b7eec05f311aad3044249982ed6fa0f3ace0d` |
| Signed manifest | `1f8d6ba056f66dc3f8ea76df16e42f5481fc17b111ea759f191eb4ad4af3c263` |
| Gate F decision | `e3f2f92f17951e489c5f768ecb9c3898c7728a2c2cd2711b4733007c9cf56cfa` |

## Fail-first and harness correction

The complete current-origin wrapper first passed 11 of 13 commands. The full
release pytest matrix found two calendar-dependent assertions in
`tests/test_admin_ops_api.py`: the fixture used day `28`, so on August 28 its
older sample fell outside the active provider cycle. The client security smoke
still pinned candidate.3 Core bytes.

Harness revision `e1b032a41c15097a620d63597242bc9996183bce` makes the
fixture relative to the current date and pins candidate.5 Core `e8eb7721...`
plus its exact AAR and DLL digests. The former failures pass, client-security
unit tests pass `7/7`, release harness contracts pass `39` plus `21` subtests,
and the corrected complete release pytest matrix reaches 100 percent with exit
code zero.

This does not create candidate.6. Comparison of all `197` deploy-selected paths
between candidate platform source and the newer harness revision found `4`
raw-exact matches, `193` CRLF-only differences and zero semantic differences.
The harness commit changes tests and release pins, not candidate runtime or
artifact bytes.

The retained fail-first wrapper has SHA-256
`1e77e49001ba8d041b4c572287645b21d661ed50323bd885b697873b5088f6e7`.

## Brain deploy and readback

The pre-deploy read-only source probe was intentionally retained as failure
evidence. Only `179/197` selected files matched candidate.5; 18 were different,
unreadable or absent. Readiness was already `23/23`, and enabled delivery was
`7/7`, so endpoint health alone would have produced a false source claim.

After the corrected full matrix passed, the owner-authorized canonical deploy
ran from the clean detached candidate platform worktree. It staged and compiled
the full tracked backend payload, retained the previous payload as a rollback
snapshot, restarted `portal-api`, `portal-bot`, `portal-helpbot`,
`portal-feedbackbot` and `portal-worker`, then passed delayed service and API
health. Automatic rollback was armed but was not triggered.

Post-deploy evidence:

| Check | Result | SHA-256 |
|---|---:|---|
| Exact Brain runtime source | `197/197 PASS` | `c932114aac2a6c7b314141cdd8922e6f9ce9caa9584e3313e136f2ee3f64ad19` |
| Brain readiness | `23/23 PASS` | `c5d2dd1bb62dd9535ee37f2bba8415e0dedad5a1e2019948ccbdc7da97e3a3ac` |
| Enabled node delivery | `7/7 PASS` | `df6b9542133accf1e1b49e0cbcac3f004fc78f5c243a7d0fe8944a741d697110` |

The delivery probe includes `ru_spb`, but proves only configured-port TCP
reachability from Brain. It does not prove every client transport, Beeline
reachability or RU-origin behavior.

## Current-origin budgets

The post-deploy source-bound direct-Ethernet probe disabled proxy discovery and
used 50 measured samples after five discarded warmups per endpoint.

| Budget | p95 | Limit | Status | Gate SHA-256 |
|---|---:|---:|---|---|
| API health | `51.4514 ms` | `100 ms` | `PASS` | `075e6fd7ea8187c3f5be354b26da06379675eec6c3d76805c1eb0655a28c61ac` |
| Public catalog | `48.1893 ms` | `200 ms` | `PASS` | `6ccb262b5c4146424e850858433b265cc7ec89d4bfd952a640b3a7ff770eb01c` |

Current-origin and Brain-origin remain separate evidence. Neither replaces
RU-origin.

## Gate F decision

The final decision-file SHA-256 is
`e3f2f92f17951e489c5f768ecb9c3898c7728a2c2cd2711b4733007c9cf56cfa`.
Current-origin and Brain-origin are `PASS`. Supply-chain signature/provenance,
manifest/docs binding, LDPlayer and one physical Android slice are also
`PASS`.

The decision remains `BLOCKED` because Windows live TUN/DNS/egress/recovery,
RU-origin, authenticated HTTP service egress, provider/PostgreSQL/outbox,
production Operator identity/RBAC/action-intent, legal/commercial approval,
comparable-device performance, post-public-promotion health and other manual
rows are not all closed. Hosted jobs are `SKIPPED_BY_OWNER` under
`OWNER_SOLO_EXCEPTION`; zero-step hosted jobs are not relabeled `PASS`.

## Verification

Commands executed against the exact source tuple or the product-identical
harness revision included:

```text
python scripts/release_gate_check.py --output ops-local/release-gates/candidate5-current-origin-full.md
python -B -m pytest -p no:cacheprovider <RELEASE_PYTEST_ARGS>
python scripts/client_security_smoke.py --client-root <exact-client> --core-root <exact-core>
python scripts/remote_deploy_brain_portal_code.py --brain-ip <brain> --passwords <owner-secret-location>
python scripts/remote_brain_runtime_source_probe.py --brain-ip <brain> --source-revision 6ea08e9... --passwords <owner-secret-location> --json-out <external-evidence>
python scripts/verify_brain_ready.py --brain-ip <brain> --passwords <owner-secret-location> --repeat 5 --json-out <external-evidence>
python scripts/remote_brain_network_probe.py --brain-ip <brain> --passwords <owner-secret-location> --live-enabled-nodes --redact --json-out <external-evidence>
python scripts/api_latency_probe.py <health-and-catalog-postdeploy-arguments>
python scripts/release_1_2_gate_f.py <signed-candidate5-inputs> --expect-blocked
```

Normalized evidence is under
`evidence/013AV-candidate5-gate-f/`. Raw runtime reports remain outside Git and
are referenced only by redacted path placeholders and SHA-256 digests.
