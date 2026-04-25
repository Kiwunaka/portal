# R01 Product Public Beta Scope

Status: [confirmed] complete

## Scope

- [confirmed] Research scope: product scope, public beta definition, canonical docs, inherited paid-beta evidence, P0 product blockers, docs impact, and public scope recommendation.
- [confirmed] This is a research-only pass. Only this assigned file was created.

## Files/docs inspected

- [confirmed] `AGENTS.md`.
- [confirmed] `docs/README.md`.
- [confirmed] `docs/product/portal-vpn-product.md`.
- [confirmed] `docs/architecture/system-overview.md`.
- [confirmed] `docs/architecture/app-first-and-bonus-flows.md`.
- [confirmed] `docs/operations/deployment-and-access.md`.
- [confirmed] `docs/operations/monitoring-and-visibility.md`.
- [confirmed] `docs/developer/developer-guide.md`.
- [confirmed] `docs/developer/repository-map.md`.
- [confirmed] `shared/product-facts.json`.
- [confirmed] `shared/public-urls.json`.
- [confirmed] `docs/audit-artifacts/release_gate_report.md` first 120 lines, for local gate classification only.
- [confirmed] Public-beta wave control docs were inspected from the root checkout because they are absent from the requested worktree at the time of this pass: `C:/Users/kiwun/Documents/ai/VPN/docs/developer/work-orders/2026-04-public-beta-release/INDEX.md`, `00-orchestrator-context.md`, `02-public-beta-scope.md`, `04-risk-register.md`, and `05-release-gate-plan.md`.
- [probable] The worktree/root mismatch is a process risk for R01 handoff: the assigned worktree has the evidence scaffold, while the root checkout has the public-beta control docs and other agents' research/work-order files.
- [confirmed] Prior paid-beta wave files compared only as inherited evidence: `docs/developer/work-orders/2026-04-beta-release/INDEX.md`, `00-orchestrator-context.md`, `01-research-synthesis.md`, `02-beta-scope.md`, `04-risk-register.md`, `05-release-gate-plan.md`, `06-paid-beta-signoff.md`, and `research/R01-product-scope.md`.

## Public beta definition

- [confirmed] Canonical product line is `POKROV`, consumer-first and app-first, with public wording avoiding direct-meaning `VPN` except legacy identifiers and unavoidable technical compatibility labels.
- [confirmed] Canonical full public release target remains `Android + Windows`; `iOS` and `macOS` are readiness-only for this wave.
- [confirmed] Core user promise remains: open app, tap `Try free`, receive a real working subscription source, choose route mode, and connect.
- [confirmed] Trial is fixed at `5 days`; Telegram reward is `+10 days`; free fallback is `5 GB / 30 days / 1 device` on `NL-free`; premium-grade access uses enabled non-free nodes.
- [confirmed] Public acquisition belongs to `marketing`; session continuation, redeem, renewal, downloads, support, and admin belong to `webapp`.
- [confirmed] Commerce direction is hosted checkout plus activation-key redemption into the same app-first account; raw subscription links stay recovery/manual-only.
- [probable] "Open public beta" must mean publicly reachable acquisition and onboarding with beta limitations disclosed, not merely the prior invite-limited paid beta with a larger audience.
- [probable] Public beta removes the paid-beta safety assumption of max 25 invite-controlled users, so abuse throttles, emergency switches, support capacity, public artifact truth, and live observability become P0 rather than beta polish.
- [confirmed] Public beta still must not claim stable production, public store cutover, production SLA, Apple availability, public `Blocked only`, guaranteed RU/DNS/leak behavior, or trusted signed artifacts without evidence.
- [confirmed] The public-beta orchestrator definition says this is an open public beta release candidate, not a closed or invite-limited paid beta; every public claim must be backed by evidence.
- [confirmed] The public-beta scope doc allows Android to be `coming soon`, `internal testing only`, or `blocked` when audit/signing are missing, and allows Windows beta only with truthful metadata, checksum, download path, and unsigned/trust warning.

## What must change versus invite/paid beta

- [confirmed] The previous paid-beta scope was capped at 25 active users, invite-controlled, cabinet-gated, and explicitly not a public stable launch.
- [confirmed] Previous paid-beta signoff ended `blocked` despite local gates passing, because live/provider/operator proofs were missing.
- [confirmed] Open public beta needs a public no-go model, not just invite-list acceptance. Payment, downloads, trial issuance, artifact exposure, and support entrypoints must be safe when reached by arbitrary public users.
- [confirmed] Public marketing can no longer rely on "approved testers understand the caveats"; artifact status, beta limitations, support expectations, refund/manual reconciliation, and platform availability must be visible before checkout or download.
- [confirmed] Trial issuance and access-key/redeem flows need public-abuse guardrails beyond an invite list, including backend rate limits and clear disable switches.
- [confirmed] Emergency controls from the paid-beta plan remain required, but their blast radius is larger: disable checkout, new trials, artifact downloads, Telegram bonus claims, payment webhook fulfillment, and show honest maintenance/unavailable states.
- [confirmed] The public-beta wave adds more explicit emergency controls than the paid-beta scope: pause managed profile issuance, pause node/location, pause activation-key redemption, manual access extend/revoke, manual payment reconcile, and broadcast incident/update.
- [probable] Public beta should require a live support load model and user-facing triage wording because anonymous public acquisition will create more support demand than 25 known beta users.
- [probable] Public beta needs explicit public release-note and docs language separating `public beta`, `public v1`, `store release`, and `stable production`.

## P0 product blockers

- [confirmed] Android public distribution remains blocked until production signing and physical-device release-build localhost/control-surface audit pass. Green repo/static gates are necessary but not sufficient.
- [confirmed] Android audit must cover proxy, DNS, command-server, Clash/API, and equivalent local admin/control surfaces before connect, after connect, and after disconnect.
- [confirmed] Windows public trust remains blocked without signing/handoff/runtime verification. An unsigned Windows artifact can only be a gated beta artifact with explicit warning, not a trusted public release.
- [confirmed] Latest local default release gate report is `PASS`, but it explicitly classifies brain-origin, RU-origin, Android physical audit, runtime app-download smoke, and client platform builds as blocked, skipped, or not requested.
- [confirmed] `release_orchestrator.py --gates-only` and `release_gate_check.py` do not publish binaries, do not deploy by themselves, do not prove live node enablement, and do not replace origin-specific evidence.
- [confirmed] Live deploy, runtime download URL sync, static redeploy, backup/rollback evidence, and emergency-switch verification remain public promotion blockers.
- [confirmed] Payment/provider live proof remains a P0 blocker inherited from paid beta: provider acceptance, signed webhook behavior, controlled low-volume or sandbox proof, idempotency, failed/refunded/manual-review handling, and admin-visible reconciliation.
- [confirmed] Managed profile delivery, app-first start-trial, checkout/redeem, support ticket creation, Telegram linking/bonus claim, `/api/client/apps`, and canonical `connect.pokrov.space` delivery must be verified against the public candidate before onboarding public users.
- [confirmed] Public UI must not expose raw config bodies, personal connection links, hostnames/ports, public IPs, raw subscription edit/share/regenerate actions, first-layer protocol jargon, or local-control surfaces.
- [confirmed] Public copy must not drift into direct-meaning `VPN`, stable-production, 24/7 SLA, Apple launch, public `Blocked only`, guaranteed RU/DNS/leak, or unsupported transport/security claims.
- [confirmed] The public-beta critical blocker policy also blocks readiness if admin auth or critical modules are fake/broken, support ticket flow is fake/broken, emergency controls are missing/unverified, rollback path is unknown, or both Android and Windows public client paths are blocked.
- [confirmed] The public-beta gate plan requires at least one public client path to work; however, public copy must only claim Android and/or Windows availability where that specific platform's gates support the claim.
- [probable] The dirty platform candidate and behind-`origin/master` baseline are promotion blockers until W10 decides merge/rebase/cherry-pick strategy and records local/remote HEAD safety.
- [blocked by missing access] Physical Android audit, brain-origin check, RU-origin check, live payment/provider proof, live app-download smoke, and deploy/rollback proof require access or devices not used in this research pass.

## Docs impact

- [confirmed] `docs/product/portal-vpn-product.md` needs the final public-beta cut line: public beta versus paid invite beta versus public v1/stable production, including what platforms and artifact types are public.
- [confirmed] `docs/architecture/system-overview.md` needs any public-beta architecture decision that changes acquisition, trial issuance, checkout, app downloads, public support, or rollout defaults.
- [confirmed] `docs/architecture/app-first-and-bonus-flows.md` needs updates if public beta changes trial throttles, activation-key rules, Telegram reward exposure, support flow, node-pool assignment, or route-mode contract.
- [confirmed] `docs/operations/deployment-and-access.md` needs the public-beta release runbook: deploy, artifact publication, release handoff, runtime URL sync, static rebuild, rollback, emergency switches, and evidence classification.
- [confirmed] `docs/operations/monitoring-and-visibility.md` needs public-beta monitoring acceptance: current-origin, brain-origin, RU-origin, metrics freshness, public hostname health, node visibility, support context, and RU probe degradation rules.
- [confirmed] `docs/developer/developer-guide.md` and `docs/developer/repository-map.md` need command/gate alignment if the public-beta gate pack differs from paid beta.
- [confirmed] `docs/user/portal-vpn-user-guide-ru.md` should receive public-beta user onboarding, limitations, platform artifact status, support path, and refund/manual reconciliation wording before public launch.
- [confirmed] `C:/Users/kiwun/Documents/ai/POKROV-app/docs/*` must be updated for active Android/Windows client truth when public artifact status, route-mode UX, signing/audit state, or release metadata changes.
- [confirmed] The public-beta wave control docs already define open public beta scope, P0 gates, risk register, and blocker policy in the root checkout. The assigned worktree should be synchronized or the handoff should explicitly name the root copies as the source used for this R01 pass.

## Public scope recommendation

- [confirmed] Recommendation: do not open a broad public beta from the current documented state.
- [confirmed] Safe current label is `public beta candidate / blocked for public onboarding` until live/operator P0 evidence is closed or explicitly accepted by the orchestrator.
- [probable] If the team needs a public-facing step before P0 closure, limit it to a public interest/waitlist or install-help/coming-soon surface with checkout and downloads disabled or honestly unavailable. Do not call it open public beta.
- [probable] The first acceptable public beta cut should be narrow and explicitly beta-labeled:
  - Android: unavailable publicly unless production signing and physical release-build audit pass; otherwise internal-only.
  - Windows: available only if artifact handoff, runtime download smoke, and unsigned/trusted-signing status are truthful before download.
  - Checkout: public only after provider acceptance/webhook proof or a documented manual-risk policy with admin reconciliation.
  - Support: cabinet ticket first, Telegram/support email fallback, best-effort wording only.
  - Routing: public `All except RU` and `Full tunnel`; keep `Blocked only` internal.
  - Email continuation: keep marked `soon` unless sender and delivery gates are live.
- [confirmed] Public beta go/no-go should require all P0s classified as `PASS`, `FAIL`, `BLOCKED_BY_ACCESS`, `SKIPPED`, or `NOT_REQUESTED`; unknowns should not be interpreted as green.

## Highest-risk findings

1. [confirmed] Android is still public-blocked by missing production signing and physical release-build localhost/control-surface audit; public Android beta would violate canonical release constraints.
2. [confirmed] The latest local gate report is green only for local/default checks; brain-origin, RU-origin, Android physical audit, runtime app-download smoke, and client platform builds are not proven in that report.
3. [confirmed] Prior paid beta was already blocked by live/provider/operator gaps; open public beta raises the bar because checkout, trials, downloads, and support are no longer invite-contained.
4. [confirmed] Payment/provider live proof and admin reconciliation remain P0 before public checkout can be safely opened.
5. [probable] Dirty baseline plus behind-origin state is a promotion risk: public beta should not be pushed/deployed until W10 records the merge/promotion strategy and rollback-safe patch state.

## Validation notes

- [confirmed] This pass was document research only; no release gates, live probes, deploys, payment flows, or device audits were run.
- [needs local run] Re-run `python scripts/release_gate_check.py --client-platform-gates windows,android-apk,android-aab` only when public artifact builds are intentionally in scope and required devices/secrets are available.
- [needs local run] Run `python scripts/android_localhost_audit.py --serial <physical-device-serial>` against a release-installed Android build before any Android public distribution.
- [needs local run] Run public-beta post-deploy checks from current-origin, brain-origin, and RU-origin when deploy/live proof is authorized.
- [blocked by missing access] Live provider verification, brain SSH/API checks, RU probe checks, production signing proof, and physical-device audit were outside this R01 access.
