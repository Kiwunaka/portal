# Source Plan Crosswalk and Decisions

Last updated: 2026-08-21

The five supplied documents are planning inputs. Current canonical owners, code/tests and exact runtime evidence remain authoritative.

| Plan | Durable ledger coverage | Primary phases | Authority handoff |
|---|---|---|---|
| Technical/release audit | `REL` findings, `REL_GATE` A–F, `REL_DOD` 01–20 | 01–06, 11 | release, architecture, security and subsystem owners from the task router |
| Client logging addendum | `OBS` 001–090, `OBS_DOD` 01–30, `OBS_PB` 01–14 | 02, 04, 07, 11 | observability/support/privacy owners and current schemas/code |
| Operator Center v2 | `OC` 000–640 | 07 | canonical `admin.pokrov.space` surface in `portal/adminapp`, with API/client/core evidence boundaries |
| Frontend audit | `FE_BUG` P0-CONN-001–003, `FE` P12-001–210, `FE_PR` 00–10 | 02, 06, 08, 11 | active client and platform frontend owners; release contract remains cross-repo |
| Marketing audit | `MKT` 000–900, `MKT_STAGE` 0–6 | 06, 07, 09 | commercial catalog, legal review, capacity and attribution owners |
| FRKN dossier | `FRKN_ADOPT`, `FRKN_AWG`, `FRKN_HY2`, `FRKN_MONITOR`, `FRKN_REJECT`, `FRKN_PLAN`, `FRKN_UNCERTAINTY` | 02, 04, 10 | core/client architecture plus exact owned test evidence |

## Capability ownership

| Capability | Implementation owner | Canonical owner / required handoff |
|---|---|---|
| Release contract and promotion | platform release scripts plus client/core/release consumers | `docs/operations/publishing-and-signing-guide.md`, matching delivery/readiness owners and exact candidate evidence |
| Product facts and public claims | `shared/**`, affected platform frontends and active client consumers | `docs/product/portal-vpn-product.md`, `DESIGN.md`, affected surface README and active client docs |
| Payments, access and checkout | `portal_bot` payment services/API plus cabinet/marketing projections | `docs/product/payment-and-access-key-contract.md`, `docs/architecture/payment-state-machine.md`, payment operations playbooks |
| Client connection truth and platform hosts | `POKROV-app/main` | active client `docs/README.md` and its architecture/operations owners; platform docs only for changed API/product contracts |
| Core ABI and protocol capability | `pokrov-core/main` with active client compatibility consumers | core release contract plus active client compatibility/release evidence |
| Observability and support | client/core structured events plus portal ingest/admin projections | `docs/operations/monitoring-and-visibility.md`, `docs/architecture/support-feedback-flow.md`, active client support/privacy owners |
| Operator Center | `adminapp`, Admin API and related models/services | `adminapp/README.md`, `docs/architecture/system-overview.md`, monitoring owner |
| Cabinet continuation | `webapp` and its API projection | `webapp/README.md`, app-first flow and user guide |
| Acquisition, SEO and public copy | `marketing`, shared copy/facts | `marketing/README.md`, product overview, design contract and user guide |
| Campaigns, capacity and attribution | portal commercial/analytics services plus adminapp | product/commercial contracts, monitoring truth and an owner-approved legal decision record |
| RU-origin and transport experiments | core/client/operator-lab paths only | monitoring/origin playbooks and candidate-scoped evidence; no public claim owner is implied |

## Reconciled decisions

1. **Release contract before broad feature work.** One machine-readable manifest must bind source commits, versions, core ABI, schemas, assets, checksums, signer/provenance and channels. Promotion reuses immutable artifacts.
2. **Frontend adapter before ABI v3.** The 1.2.0 client first centralizes connection experience on the current typed contract. ABI v3 advances only through compatibility tests and cannot silently block the initial reducer/presenter work.
3. **Linux is conditional beta.** No stable/public support claim until daemon, non-root UI, packages, signing, rollback and distro/runtime matrix exist for the exact candidate.
4. **One canonical Operator Center.** Target is `admin.pokrov.space` backed by `portal/adminapp`; old admin surfaces are retained only until capability inventory, cutover smoke and rollback are proved.
5. **FRKN is pattern input, not code authority.** Adopt proof-driven connection truth, transport diversity, immutable provenance, sanitized diagnostics and centralized product facts. Do not fork Dopamine/Amnezia, add a second Xray core, expose raw configs, or ship secret-bearing diagnostics.
6. **AWG2 is an isolated PoC.** Use a typed `awg` endpoint inside the existing managed core graph, synthetic fixtures, fail-closed capability handling and the ten explicit gates. Until exact RU-origin canary evidence exists, its status is `MANUAL_OWNER_TEST`, never “works in Russia”.
7. **Hysteria2 comes later.** It may be evaluated as a bounded UDP/QUIC selector/fallback after the same evidence loop, not as the sole bootstrap.
8. **Marketing is legally and operationally gated.** No broad RF advertising, external campaign launch or spend is authorized without current legal qualification, explicit owner authorization, capacity guard and campaign-to-revenue evidence. The first recommended test remains a bounded winback pilot.
9. **Public platform truth stays narrow.** Android and Windows are public; Apple remains readiness-only unless its canonical evidence changes. Linux remains beta-only if Phase 03 is actually proved.
10. **Manual gates stay manual.** Windows trusted signing, physical-device, clean-host TUN/DNS, RU-origin, provider-dashboard and production-origin checks cannot be promoted by local automation or documentation.

## Exclusions without a new owner decision

- giant cross-repository merge or big-bang rewrite;
- raw customer/provider payloads or secret-bearing evidence;
- production deploy, payment mutation, campaign launch or external communication;
- store/public Linux/Apple claims without exact current evidence;
- speculative protocols or third-party client stacks outside the bounded R&D lane.
