# File Locks

Status: active

## Research Wave

Research agents may edit only their assigned file under `research/`.

| Agent | Write scope |
| --- | --- |
| R01 | `research/R01-product-release-truth.md` |
| R02 | `research/R02-design-system-visual-audit.md` |
| R03 | `research/R03-frontend-webapp-marketing.md` |
| R04 | `research/R04-backend-api-data-entitlements.md` |
| R05 | `research/R05-lavatop-payments-provider.md` |
| R06 | `research/R06-telegram-downloads-ru-origin.md` |
| R07 | `research/R07-client-android-windows-release.md` |
| R08 | `research/R08-security-privacy-abuse.md` |
| R09 | `research/R09-performance-infra-observability.md` |
| R10 | `research/R10-docs-launch-growth-support.md` |

## Implementation Wave

Implementation locks are advisory for this branch. Agents and the orchestrator must keep write scopes disjoint and must not revert another worker's edits.

| Agent | Write scope |
| --- | --- |
| W01 | `DESIGN.md`, `docs/design/*`, `shared/design-tokens.schema.json`, client design docs |
| W02 | `marketing/src/lib/marketing-site.ts`, marketing SEO tests/docs |
| W03 | `webapp/src/components/*`, cabinet responsive docs/tests |
| W04 | `webapp/src/app/(dashboard)/admin/*`, admin operator docs/tests |
| W05 | backend API/payment contract docs and tests |
| W06 | Lava.top provider docs/tests and runtime download smoke wrapper |
| W07 | Android/Windows client release gates and client release docs |
| W08 | infra/observability/release gate docs and origin evidence layout |
| W09 | security/privacy redaction and beta abuse-hardening docs/tests |
| W10 | launch decision, release notes, known issues, support macros, final handoff |

## Active Orchestrator Lock

The orchestrator owns cross-cutting release-gate code and work-order ledgers:

- `scripts/release_gate_check.py`
- `scripts/runtime_app_download_smoke.py`
- `tests/test_release_gate_check.py`
- `tests/test_runtime_app_download_smoke.py`
- `docs/developer/work-orders/2026-04-open-beta-v4/*`
