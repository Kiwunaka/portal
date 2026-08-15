# Open Source Client Rollout Plan

Last updated: 2026-07-10

## Document Status

This is a future rollout plan for publishing the POKROV client app in a
separate public repository.

It is not a current release promise, not a store-readiness claim, and not a
change to the active client source of truth. Until the owner promotes a public
repository, `POKROV-app/main` remains the canonical private development lane.

## Goal

Publish the POKROV client app as an open-source project under a GPL-family
license while keeping the operational platform private.

The public release should make the client inspectable, buildable, forkable, and
contribution-ready without exposing private backend operations, billing flows,
admin surfaces, deployment material, release evidence, or secret-bearing
history.

## Scope

In scope:

- Android and Windows client source code.
- two public client product tracks:
  - operator / company client for teams that want a client for their own VPN
    service
  - personal key client for users who paste their own key or subscription and
    connect without POKROV account, billing, or subscriptions
- Client build instructions.
- Public client configuration examples.
- optional `Free VPN` catalog research lane based on third-party public config
  feeds when licensing, safety, freshness, and user-consent gates are met.
- Public issue and contribution workflow.
- Public release binaries, checksums, and changelog when a public distribution
  repo or delivery surface is ready.

Out of scope:

- `portal_bot/`, backend API internals, bots, workers, admin implementation,
  billing internals, deploy scripts, node-management scripts, and operator
  runbooks.
- Private release evidence under `ops-local/`, sensitive audit material, raw
  device logs, signing identities, and payment-provider evidence.
- Store availability, stable `1.0.0`, trusted Windows signing, raw Android
  physical-audit proof, RU-origin readiness, or production WARP claims unless
  current redacted evidence exists at publication time.

## Recommended Repository Model

Create a new public repository instead of opening the current working
`POKROV-app` repository directly.

Suggested names:

- `pokrov-client`
- `pokrov-app`

Recommended first mode:

- use a clean snapshot import
- start the public repository with a first sanitized commit
- do not preserve the private development history

Avoid an automated mirror for the first open-source launch. A mirror can come
later only after secret scanning, allowlisted path export, license checks, and
release gates are reliable.

## Public Product Tracks

The open-source client should support two public tracks without mixing their
promises.

### Track A: Operator / Company Client

Audience:

- companies, communities, or independent operators that already run their own
  VPN/control-plane service
- teams that want a branded client shell for their own subscription or access
  service

Core idea:

- publish a configurable client that can point at an operator-owned backend,
  catalog, support channel, and release metadata
- keep POKROV official service code private while making the client adaptable
  for other operators

Expected capabilities:

- configurable service base URL
- configurable branding and support links
- subscription/key import
- managed profile endpoint contract examples
- optional operator catalog endpoint examples
- build flavors for official POKROV vs custom operator builds
- clear fork/official-build boundary

Guardrails:

- forks must not imply they are official POKROV builds
- operator builds own their support, signing, backend compatibility, and
  release claims
- official POKROV domains, bots, signing identities, and release channels stay
  protected by the brand policy

### Track B: Personal Key Client

Audience:

- users who already have a key, config, or subscription URL
- users who want a simple client similar to Hiddify-style import-and-connect
  behavior

Core idea:

- publish a no-account client mode where the user can paste a key,
  subscription URL, or supported config and connect without POKROV billing,
  cabinet, or subscription management

Expected capabilities:

- paste/import key
- paste/import subscription URL
- QR import when available
- local profiles list
- manual refresh
- basic latency/connect checks
- clear unsupported/invalid config errors
- no POKROV account, payment, or premium-state dependency

Guardrails:

- local-only personal profiles are user-owned data
- the client must not silently upload user keys or subscriptions to POKROV
- POKROV support should be scoped to official builds and official service
  accounts, not arbitrary third-party configs
- personal key mode must not expose raw advanced internals in the first-layer
  UI unless the user opens advanced settings

## Optional Free VPN Catalog Track

Owner direction as of `2026-06-05`:

- research a `Free VPN` section inside the open-source client that can parse
  public third-party config feeds
- first candidate: `AvenCores/goida-vpn-configs`
  (`https://github.com/AvenCores/goida-vpn-configs`)

Observed candidate facts on `2026-06-05`:

- repository: `AvenCores/goida-vpn-configs`
- license: `GPL-3.0`
- public template repository
- README describes automatically updated public VPN config TXT subscriptions
  for `V2Ray`, `VLESS`, `Hysteria`, `Trojan`, `VMess`, `Reality`, and
  `Shadowsocks`
- README says configs update every `9 minutes` through GitHub Actions
- feed files are published under raw `githubmirror/*.txt` URLs

Product stance:

- this must be opt-in and visibly labeled as a third-party public-config
  catalog
- do not enable third-party free configs silently by default
- do not call the feeds official POKROV nodes
- do not mix free third-party configs with official POKROV paid delivery; POKROV consumer free-node delivery is retired
  pool
- do not promise safety, speed, privacy, legality, uptime, or availability for
  third-party public configs

Implementation stance:

- support parsing through a provider interface such as
  `PublicConfigCatalogProvider`
- keep feed definitions in a signed or reviewed public catalog file instead of
  hardcoding every raw URL throughout UI code
- store source, license, last fetch time, parser version, and feed URL for each
  imported entry
- cache results locally with expiry and manual refresh
- deduplicate configs before showing them
- reject malformed, unsupported, or obviously unsafe entries with visible
  reasons
- expose third-party source and freshness in UI
- provide a one-tap disable / clear imported public configs action

Required gates before shipping:

1. confirm license compatibility and attribution needs for each feed source
2. document failure behavior when GitHub raw URLs are unavailable
3. define parser limits for VLESS, VMess, Trojan, Shadowsocks, Hysteria, and
   subscription text formats
4. add tests with fixture feeds
5. add safety copy for third-party public configs
6. add release notes that distinguish POKROV official service from third-party
   free config feeds
7. verify the feature does not bypass POKROV official routing, node-pool, or
   release-gate honesty rules

## Licensing Direction

Preferred candidate:

- `GPL-3.0-or-later`

Why:

- it keeps distributed forks and derivative client builds under the same
  copyleft family
- it gives a standard SPDX identifier for tooling and package metadata
- it matches the intent to make the app genuinely open while limiting closed
  redistributed derivatives

Before final publication:

1. Audit dependency licenses.
2. Confirm generated assets, icons, fonts, and bundled binaries are publishable.
3. Confirm whether official POKROV brand assets are licensed with the code or
   kept under a separate trademark/brand policy.
4. Add the exact license text and SPDX headers or package metadata where
   practical.

Reference points:

- GNU GPL FAQ: `https://www.gnu.org/licenses/gpl-faq.en.html`
- SPDX license list: `https://spdx.org/licenses/`

## Brand And Trademark Boundary

The code can be GPL while the official POKROV brand remains protected.

Add a public `BRAND.md` or `TRADEMARKS.md` before launch that explains:

- official builds are published only by POKROV-owned release channels
- forks must not imply they are official POKROV builds
- logo, app name, signing identity, domains, and support bots are not
  automatically granted for redistributed forks
- security or support claims must not be copied from official builds unless the
  fork has its own evidence

## Phase 0: Private Repo Visibility Decision

Before public open-source work starts:

1. Keep the root platform repository private.
2. Keep `POKROV-app` private unless public binary delivery has already moved to
   a separate public surface.
3. Treat any previously public repository history as already observable.
4. Rotate secrets if there is any chance they were committed or exposed.
5. Check whether current public APK/EXE URLs depend on GitHub Releases from a
   repository that will become private.

Gate:

- public download URLs continue working after private repository visibility
  changes.

## Phase 1: Public Delivery Surface

Prepare a public distribution surface before closing or replacing any current
public GitHub Releases flow.

Acceptable models:

- separate public `pokrov-client` repository with release binaries
- website or CDN-backed download surface
- minimal public release repository that contains binaries, checksums,
  release notes, and install docs but not private development history

Required for every public binary:

- canonical filename
- current stable-direct label `v1.0.10`, backed by the exact client release
  handoff; later versions require the same artifact and runtime proof
- SHA-256 checksum
- install note
- beta warning where signing or store trust is not complete
- source-code reference if the binary corresponds to an open-source snapshot

Gate:

- marketing, cabinet, bot, app handoff, and install docs all point to the same
  public artifact set.

## Phase 2: Sanitized Source Snapshot

Create an export branch or temporary staging folder from `POKROV-app/main`, then
remove private-only material before creating the public repository.

Sanitize:

- API keys, tokens, secrets, signing config, and certificates
- private hostnames or internal-only endpoints
- payment-provider and admin-only references not needed by the client
- operator runbooks and release-evidence paths
- debug endpoints and local control surfaces
- absolute machine paths
- private screenshots, logs, telemetry dumps, and raw audit outputs
- generated assets without source, rights, or release-scope notes
- private package registries or local-only dependency paths

Keep, when intentional:

- public POKROV product name
- public site and support links
- app-first public client flow
- personal key mode
- operator/company client configuration examples
- configuration examples with placeholder values
- official production hosts only when they are meant to be public user-facing
  facts

Gate:

- a clean clone of the public snapshot builds without private files.

## Phase 3: Public Repository Setup

Minimum repository files:

- `LICENSE`
- `README.md`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `CHANGELOG.md`
- `BRAND.md` or `TRADEMARKS.md`
- `.github/ISSUE_TEMPLATE/*`
- `.github/PULL_REQUEST_TEMPLATE.md`
- CI workflow for analyze, tests, and build smoke

README must state:

- what the repository contains
- what is not included
- how to build Android and Windows
- how to configure a custom backend or development API
- which official services are operated by POKROV
- where official binaries are published
- how to report security issues privately

Gate:

- an outside contributor can understand the boundary between open client code
  and private POKROV service operation without reading private docs.

## Phase 4: License And Dependency Audit

Create a dependency inventory with:

- dependency name
- version
- license
- runtime or development-only use
- bundled or not bundled
- GPL compatibility decision
- required action

Check:

- Flutter and Dart packages
- Android native dependencies
- Windows native libraries
- hiddify-core and related runtime artifacts
- icons, fonts, images, sounds, and generated assets
- build tooling and CI actions

Gate:

- no known GPL-incompatible dependency is bundled into the public client
  distribution.

## Phase 5: Build And Release Verification

Run the public snapshot as if it were a third-party checkout.

Required checks:

1. Clone the public repository into a clean folder.
2. Run dependency install.
3. Run analyze/lint.
4. Run focused client tests.
5. Build Android smoke artifact.
6. Build Windows smoke artifact.
7. Confirm no private environment file is required for basic local build.
8. Confirm release metadata and updater/source-code URLs do not point to a
   private personal repository.

Gate:

- public repository CI is green and local clean-clone smoke passes.

## Phase 6: Announcement Preparation

Use precise language:

> The POKROV client app is open source under GPL. The official POKROV service
> backend remains operated by POKROV; the client code is available for review,
> builds, forks, and contributions.

Avoid:

- "the whole platform is open source"
- "stable 1.0"
- "available in stores"
- "trusted signed Windows release"
- "raw Android audit complete"
- "RU-origin readiness proven"
- production WARP claims without matching release-build evidence

Recommended channels:

- `@pokrov_vpn`
- `pokrov.space`
- GitHub release notes
- short developer-facing post

Gate:

- announcement copy matches current release evidence and public wording rules.

## Phase 7: Post-Launch Operations

Enable:

- GitHub secret scanning
- Dependabot or equivalent dependency alerts
- branch protection
- required CI checks
- issue labels for `android`, `windows`, `build`, `security`, `docs`,
  `good first issue`, and `help wanted`

Decide contribution policy:

- DCO is simpler and often enough for GPL projects.
- CLA is heavier but preserves more future relicensing control.

Operational rule:

- security reports go through `SECURITY.md`, not public issues.

## Ongoing Sync Policy

Start with manual sanitized snapshots.

Only consider an automated private-to-public export after:

- the export path is allowlisted
- secret scanning runs before publication
- dependency/license checks are automated
- public CI proves the exported snapshot
- release notes are generated from public-safe changelog entries
- an operator can stop publication before a bad snapshot goes public

## Completion Definition For The First OSS Release

The first open-source client rollout is complete when:

- the public repository exists
- the license and brand boundaries are explicit
- clean-clone build smoke passes
- dependency license audit has no unresolved blocker
- public binary delivery works independently of private repositories
- official download surfaces point to the intended public artifacts
- announcement copy is evidence-honest
- private platform and operational repositories remain private
