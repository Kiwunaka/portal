# WO-003C — Reproducible dependency contract

Status: `LOCALLY_PROVED_I3`
Phase: `01`
Ledger rows: `REL/DEP-001`
Promotion: `NOT_REQUESTED`

## Intent

Make the platform backend, operator tooling and all three web frontends install
from reviewed, deterministic dependency inputs. CI must not repair missing
dependencies with ad-hoc install commands, and a lock/toolchain drift must fail
before product tests run.

## Implemented contract

- `portal_bot/requirements.in`, `requirements-test.in` and
  `requirements-ops.in` are the reviewed direct inputs. The corresponding
  `.txt` files are universal Python 3.12 compiled locks with exact transitive
  versions and SHA-256 artifact hashes.
- `requests` is now an explicit runtime dependency because
  `portal_bot/sync_clients.py` imports it; it is no longer obtained accidentally
  through `geoip2`.
- Starlette 1.6 prefers `httpx2` for `TestClient`. The test lock therefore owns
  exact `httpx2==2.10.0`; the defect was the untracked CI install, not the
  package name. The deprecated `httpx` fallback is no longer installed by the
  platform test workflow.
- `shared/dependency-contract.json` pins Python `3.12.5`, pip `26.1.2`, uv
  `0.9.26`, Node `22.14.0`, npm `11.7.0`, npm lockfile v3 and the shared
  Next/React/Tailwind/TypeScript/Playwright versions.
- Admin, cabinet and marketing manifests use exact direct versions. All three
  lock roots and resolved packages must match their manifests.
- `scripts/check_dependency_contract.py` fails on unpinned Python locks,
  frontend ranges, manifest/lock drift, divergent shared toolchains, ad-hoc
  pytest/httpx workflow installs or workflow runtime drift. Guardrails,
  release-v2, weekly snapshot and manual orchestrator run the check.
- CI installs Python test/ops locks with `--require-hashes` and all frontends
  with `npm ci`.

Next `16.3.2` changed static-export segment requests. The existing cabinet
alias repair still passes; marketing now applies the same deterministic
dot-joined segment-payload copies. Its responsive gate builds the production
export and serves `out/` through the pinned Python runtime rather than treating
Fast Refresh/HMR as release evidence.

## Retained local proof

- Python test and ops locks: pip `--dry-run --ignore-installed
  --require-hashes` `PASS`; dependency validator and script-manifest tests:
  `7/7`; checker CLI: `PASS`.
- Backend/API compatibility after adopting `httpx2`: `139` tests plus `8`
  subtests, with Starlette deprecation promoted to an error.
- Fresh `npm ci` and top-level tree resolution: `PASS` for adminapp, webapp and
  marketing.
- `npm audit --audit-level=low`: `PASS`, zero vulnerabilities in adminapp,
  webapp and marketing after the compatible Next `16.3.2` upgrade and a normal
  lockfile-only audit repair without `--force`.
- Adminapp lint/build/cutover and full Playwright: `PASS`, `30` static pages,
  `28` routes and `75/75` browser tests.
- Webapp lint/public-error/build and full Playwright: `PASS`, `40` static pages
  and `85/85` browser tests.
- Marketing lint/SEO/build/production-responsive: `PASS`, `35` static pages and
  the complete `19 routes × 3 viewports` matrix plus no-JS, reduced-motion,
  keyboard and axe checks.

Evidence:
`evidence/003C-reproducible-dependencies/003C-dependency-contract.json`.

## Evidence ceiling

This is local source/install/browser proof, not hosted CI or exact-candidate
reproduction. The dependency snapshot itself has zero npm audit findings, but
the platform worktree is still dirty and has not been reproduced by hosted CI
from a clean frozen revision. No deploy, signing or promotion is claimed.
Hosted gates and a clean frozen candidate are required before `I4`.
