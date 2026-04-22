# Wave 0 Client Canon Cutover Design

Date: 2026-04-22
Status: approved for Wave 0 implementation
Scope: root canon, repo-policy, orchestration routing, and client-lane ownership

## Goal

Freeze the new client governance model before code and surface work continue under the old assumptions.

This wave establishes one new canonical client lane and rewrites the platform canon so later backend, app, marketing, webapp, and admin work all target the same world.

## Decision summary

- GitHub repository: `https://github.com/Kiwunaka/POKROV-app`
- Canonical client repo and branch: `POKROV-app/main`
- Expected local checkout path after bootstrap: `C:/Users/kiwun/Documents/ai/POKROV-app`
- `app-next/` is a temporary source workspace only. It feeds the initial migration into `POKROV-app`, but it is not a parallel canon once Wave 0 policy is in place.
- `external/client-fork/app/` becomes the retained `bridge/hotfix lane` until formal cutover.
- After formal cutover, `external/client-fork/app/` becomes `compatibility-only reference`.
- The root repository at `C:/Users/kiwun/Documents/ai/VPN` remains the canonical platform repository for `portal_bot`, `marketing`, `webapp`, `shared`, `infra`, `scripts`, and root docs.
- Public product scope for this rework remains `Android + Windows`.
- Apple hosts may remain in the new client repository as engineering lanes, but they are not public promise or release acceptance in this wave.
- Until formal cutover, public Android and Windows release builds, signing, packaging runbooks, and release evidence remain bridge-operational truth under `external/client-fork/app/`.

## Why this model

Current repo governance is internally inconsistent with the approved rework:

- root canon still says `external/client-fork/app/` is the current shipping client authority
- `app-next/` is documented as future-only and non-authoritative
- `external/client-fork/app/` is the only client lane with a real nested git truth today
- `app-next/` is structurally closer to the desired long-term client architecture but is not yet cutover-ready

Making `app-next/` the main client lane inside the root platform repo would keep platform truth and client truth mixed together.

Creating `POKROV-app` as the new dedicated client repository is the cleanest cut:

- the platform repo keeps one clear authority boundary
- the new client lane gets its own canonical git truth
- the legacy fork can remain rollback-safe without pretending to be future truth

## Wave 0 deliverables

### 1. Canon rewrite

Update root canonical docs so they all agree on the same lane model:

- `AGENTS.md`
- `docs/README.md`
- `docs/product/portal-vpn-product.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/app-first-and-bonus-flows.md`
- `docs/developer/developer-guide.md`
- `docs/developer/repository-map.md`
- `docs/operations/deployment-and-access.md`
- `docs/operations/publishing-and-signing-guide.md`

Required outcome:

- root canon must stop naming `external/client-fork/app/` as the default shipping client authority
- root canon must stop naming `app-next/` as future-only
- root canon must name `POKROV-app/main` as the new client truth
- root canon must describe `external/client-fork/app/` only as bridge/hotfix until formal cutover, then compatibility-only
- root canon must explicitly separate `development truth` from `current release/build/signing truth`

### 2. Client-doc authority move

Move client-doc authority into `POKROV-app/main` and demote the legacy client docs.

Required outcome:

- `POKROV-app` becomes the only canonical client repo and doc lane for new client work
- the initial client docs in `POKROV-app` should be bootstrapped from the current `app-next/docs/` set
- `app-next/docs/` is source material during migration only; it is not a parallel active canon after the bootstrap rule is satisfied
- `external/client-fork/app/docs/README.md` and related client docs must be relabeled as legacy bridge documentation
- client docs must distinguish `main development lane` from `public release truth`

Important wording rule:

- `POKROV-app/main` becoming the new client lane in Wave 0 does not mean Android or Windows are declared release-ready from that lane in Wave 0
- the new client repo becomes development truth first
- release truth remains gated by later cutover criteria
- until formal cutover, public Android and Windows release builds still ship from `external/client-fork/app`

### 3. Orchestration routing rewrite

Update the orchestration pack so future work orders follow the new lane model automatically.

Required touchpoints:

- `docs/developer/orchestration/README.md`
- `docs/developer/orchestration/orchestration-standard.md`
- `docs/developer/orchestration/roles/*`
- `docs/developer/orchestration/templates/*`
- `docs/developer/work-orders/README.md`

Required outcome:

- `client-only` work must no longer default to `external/client-fork/app/ -> PORTALapp/main`
- WOs must route new client work to `POKROV-app/main`
- WOs must call out when a task belongs to the legacy bridge lane instead

### 4. Repo-boundary clarification

Document the transition boundary between the platform repo, the new client repo, and the legacy bridge lane.

Required outcome:

- the root repo is platform truth
- `POKROV-app/main` is new client truth
- `C:/Users/kiwun/Documents/ai/POKROV-app` is the expected local checkout path once the repo is bootstrapped locally
- `external/client-fork/app/` is rollback-safe bridge truth only for hotfixes and compatibility maintenance during transition
- docs must not imply that changes in one repo automatically update the other
- docs must explicitly say that the new client repo must exist and contain the initial snapshot before normal new client work starts there

### 5. New client repo bootstrap rule

Do not create a ghost authority.

Required outcome:

- Wave 0 must treat the currently empty `POKROV-app` repository as a target that needs an initial client snapshot, not just a name in docs
- the initial `POKROV-app` content should come from the current `app-next/` workspace and its active docs set
- after that bootstrap snapshot lands, `POKROV-app/main` becomes the only canonical client repo/doc lane for new client work
- until that bootstrap snapshot lands, docs must describe `POKROV-app` as the immediate migration target and `app-next/` as source workspace only
- Wave 0 does not require deleting `app-next/` from the root repo yet, but it must make the migration target and temporary source relationship explicit

### 6. Bridge-period policy

Describe exactly what is still allowed in the legacy fork during the bridge period.

Allowed during bridge period:

- emergency hotfixes
- compatibility maintenance
- packaging continuity when cutover has not happened yet
- current public Android and Windows build commands
- current signing and publishing runbooks
- retained `out/` artifacts and release handoff evidence
- rollback-safe reference checks

Not allowed during bridge period:

- new product-direction work
- new primary UX work
- new source-of-truth contracts that should belong to the new client lane
- silent reuse of legacy release runbooks as if they still define the future client lane

Bridge-period release rule:

- until formal cutover, release/build/signing/runbook truth stays on `external/client-fork/app/`
- `POKROV-app/main` is development truth first, not current public release truth

### 7. Formal cutover definition

For this program, `formal cutover` means the later wave that declares all of the following true at once:

- `POKROV-app/main` already contains the bootstrapped `app-next` snapshot and is the active client development repo
- Android and Windows parity gates for the new client lane are closed
- release/build/signing/runbook truth has been rewritten to point to the new client repo
- root canon and client canon both stop treating the legacy fork as bridge-operational release truth

Only after that later wave is complete does `external/client-fork/app/` change from `bridge/hotfix lane` to `compatibility-only reference`.

## Explicit non-goals

- no backend contract redesign in this wave
- no tariff extraction in this wave
- no marketing or webapp product rebuild in this wave
- no formal public cutover in this wave
- no claim that `app-next` or `POKROV-app` is already release-ready
- no Apple publication commitment
- no deletion of the legacy fork

## Required follow-up waves after Wave 0

Wave 0 only freezes governance and canon. The next implementation waves remain separate:

1. shared truth extraction
2. backend identity and access redesign
3. new client lane product-shell alignment
4. marketing rebuild
5. webapp continuation cleanup
6. admin and backoffice work
7. formal cutover and legacy freeze

## Risks and controls

### Risk: repo drift during transition

If `app-next/` is promoted in docs without making `POKROV-app` the single real write target, workers can split changes between the root repo and the new client repo.

Control:

- root canon must say exactly where new client changes land
- bridge-period wording must be explicit

### Risk: false release implications

If docs say the new client repo is the new main lane without separating development truth from release truth, readers may infer that Android or Windows release acceptance moved automatically.

Control:

- every relevant doc must keep `Android + Windows public scope` while separately stating that release gates still apply
- the new client docs must stop saying `future-only`, but may still say `cutover blocked` or `release not yet approved`
- bridge-operational docs must still say that current public release flow remains on `external/client-fork/app` until formal cutover

### Risk: orchestration snap-back

If only the top-level docs change, future work orders can still silently route client work back into the legacy fork.

Control:

- update orchestration standard, role docs, and templates in the same wave

### Risk: packaging and runbook ambiguity

Legacy packaging and release evidence currently live around `external/client-fork/app/`.

Control:

- Wave 0 docs must explicitly say those runbooks are bridge-period artifacts until later migration waves relocate or replace them
- the new client canon must not imply that legacy packaging docs already apply unchanged to `POKROV-app`

## Validation

Wave 0 is complete when:

- no root canonical doc still calls `external/client-fork/app/` the default shipping client authority
- no root canonical doc still calls `app-next/` future-only
- root canon consistently names `POKROV-app/main` as the new client truth
- the new client canon makes it explicit whether `POKROV-app` already contains the initial `app-next` snapshot or is the immediate migration target for it
- the spec and rewritten docs explicitly say that current public Android and Windows release flow remains on `external/client-fork/app` until formal cutover
- orchestration docs route new client work to the new client repo
- legacy client docs are clearly relabeled as bridge/hotfix documentation
- the distinction between `main development lane` and `release truth` is explicit in the new client canon
- the expected local checkout path for the new client repo is documented

## Implementation order

1. rewrite root repo-policy and source-of-truth sections
2. rewrite client-doc entrypoints and lane descriptions
3. rewrite orchestration routing and templates
4. do one consistency pass across docs indexes and work-order references

## Handoff note

After Wave 0 lands, all later rework decisions should assume:

- platform truth lives in the root repo
- client truth lives in `POKROV-app/main`
- legacy fork work must be justified as bridge, hotfix, or compatibility work
