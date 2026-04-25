# Fix-Cycle Ledger

Status: active

## FC-001 - Downloads E2E copy expectation

- Date/time: 2026-04-25
- Source: local Playwright E2E
- Finding: `webapp` E2E expected downloads copy to include the explicit word `неподписанный`; the first warning-copy pass used a different grammatical form.
- Fix: adjusted `webapp/src/components/cabinet/downloads-surface.tsx` so Windows beta warning text contains the exact explicit warning while preserving the release-risk meaning.
- Verification:
  - `python -m pytest tests/test_public_copy_guardrails.py -q` -> `6 passed`
  - `npm.cmd run test:e2e` in `webapp/` -> `31 passed`
- Residual risk: none for this local copy issue.

## FC-002 - Credentialed CORS wildcard regression

- Date/time: 2026-04-25
- Source: local TDD/security guardrail
- Finding: API middleware allowed `*` origins while credentials were enabled.
- Fix: added an explicit production/dev origin allowlist and a regression test that checks both allowed `https://app.pokrov.space` and blocked untrusted origins.
- Verification:
  - focused CORS test passed
  - `python -m pytest tests/test_api_auth_and_tickets.py -q` -> `58 passed`
- Residual risk: configured deployments must add any extra trusted origin through `API_CORS_ALLOWED_ORIGINS`; wildcard remains intentionally ignored.

## FC-003 - Worktree node-access key lookup

- Date/time: 2026-04-26
- Source: brain-origin gate run
- Finding: `scripts/node_access.py` parsed the root `PASSWORDS.txt` when explicitly provided, but still looked for private keys under the feature worktree's missing `VPN NODE SSH KEYS` directory.
- Fix: default private-key lookup to the provided password bundle's parent directory when no explicit key directory is supplied.
- Verification:
  - `python -m pytest tests/test_node_access.py -q` -> `3 passed`
  - `python -m pytest tests/test_predeploy_node_readiness.py -q` -> `5 passed`
  - brain-origin quick gate report -> `PASS`
- Residual risk: operational scripts still use SSH `AutoAddPolicy()` and should be hardened separately.

## FC-004 - RU Telegram reachability classification

- Date/time: 2026-04-26
- Source: RU-origin probe from `mini`
- Finding: the RU probe report showed Telegram targets failing but produced `no classifications`, making the evidence too easy to misread.
- Fix: added `telegram_reachability_problem` classification for failed `kind=telegram` targets.
- Verification:
  - `python -m pytest tests/test_ru_probe_runner.py tests/test_render_ru_probe_report.py -q` -> `7 passed`
  - regenerated `docs/audit-artifacts/ru_probe_2026-04-26.md`
- Residual risk: `mini` may not represent every RU user path; this remains an operational dependency.

## FC-005 - FreeKassa API probe worktree credentials

- Date/time: 2026-04-26
- Source: payment provider live-smoke prep
- Finding: `scripts/freekassa_api_probe.py` could not be run reliably from an isolated worktree because it did not accept an explicit password bundle path.
- Fix: added `--passwords` and threaded it into `connect_node`.
- Verification:
  - `python -m pytest tests/test_freekassa_api_probe.py -q` -> `1 passed`
  - `python -m pytest tests/test_api_payments_callbacks.py tests/test_admin_payments_api.py tests/test_freekassa_api_probe.py -q` -> `25 passed`
- Residual risk: FreeKassa itself still returns `Merchant not activated`; probe tooling is fixed, provider status is not.
