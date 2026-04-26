# Research Synthesis

Status: complete  
Date: 2026-04-26  
Scope: R01-R10 research wave for Open Beta v4

## Release Truth

The release cannot be called `1.0.0` and cannot be promoted as a broad public launch. The current truthful scope is an Open Beta v4 preparation branch with a possible gated beta only after local gates pass and blocked external gates stay clearly labeled.

Allowed public stance before new proof:

- do not announce broad public availability;
- keep Android gated/internal until signing and the physical release-build localhost/control-surface audit pass;
- keep Windows as gated unsigned beta unless trusted signing and handoff evidence are attached;
- keep paid checkout disabled or unavailable unless Lava.top proof is attached;
- keep downloads hidden or support-routed unless runtime handoff URLs are present and verified.

## Findings By Area

| Area | Label | Summary | Required action |
| --- | --- | --- | --- |
| Product/release truth | confirmed | `1.0.0` is not supported by evidence. Current artifacts are beta evidence, not public distribution. | Use Open Beta v4 wording and keep final decision blocked unless every P0 gate has evidence. |
| Design system | confirmed | Root `DESIGN.md`, design-token schema, and client design docs were added in this branch. Marketing/cabinet/admin still contain visible mojibake and client colors are not yet generated from shared tokens. | Keep shared design contract and schema; defer broad visual refresh and generated Flutter token sync to dedicated UI work. |
| Frontend surfaces | confirmed | No P0 frontend blocker found, but `/checkout/` is missing from sitemap and narrow-viewport coverage is incomplete. | Add checkout sitemap coverage, keep install noindex unless public artifact URLs are approved, and add responsive gate notes. |
| Backend contracts | confirmed | Paid fulfillment is direct-entitlement-first, not key-first. Refund/chargeback and order-level idempotency are not complete. | Do not claim activation-key-safe paid launch until payment state machine and reconciliation are implemented or explicitly scoped out. |
| Lava.top payments | confirmed | Lava.top can plausibly support invoices and webhooks, but live/sandbox proof is missing and refunds/chargebacks are not webhook-backed. | Keep provider unavailable until credentials, order, webhook auth, replay, and reconciliation evidence are attached. |
| Telegram/download/RU | confirmed | Runtime download smoke wrapper and redaction were added in this branch; live env-only Telegram init data, approved handoff URLs, and RU-origin probe evidence remain external blockers. | Use the wrapper for retained evidence and keep runtime/RU gates blocked until proof is attached. |
| Client release | confirmed | Android gate defaults to a legacy package identifier and cannot audit the active app package without override. Windows remains unsigned/gated. | Add Android audit package override/default, document physical-audit command, and keep public Android blocked. |
| Security/privacy | confirmed | No confirmed P0 security issue, but support attachments, local app tokens, provider payload retention, and callback throttles need hardening. | Add beta security backlog and improve release evidence redaction immediately. |
| Performance/infra | confirmed | Prior JS budgets are acceptable, but p95 API/app and current-origin/brain-origin/RU-origin evidence are incomplete. | Treat perf gates as `needs local run` or `blocked by missing access`; require labeled origin evidence. |
| Docs/launch/support | confirmed | Docs are strong enough for a truthful gated beta, but broad launch copy, ASO/store pack, and operator macros are incomplete. | Add launch notes, known issues, support macros, and keep launch decision at "do not release publicly" until gate proof changes. |

## P0 Blockers

| ID | Blocker | Current state | Unblock proof |
| --- | --- | --- | --- |
| P0-001 | Public payment path | Blocked by missing Lava.top credential/live or sandbox evidence. | Redacted provider order, authenticated webhook, replay behavior, failed-payment state, reconciliation note. |
| P0-002 | Android public safety | Blocked by signing and physical release-build audit. | Release-installed physical device audit with localhost/control-surface evidence attached. |
| P0-003 | Runtime download availability | Blocked by missing approved public handoff URLs and Telegram runtime token proof. | Release handoff URLs, `/api/client/apps` agreement, redacted runtime download smoke. |
| P0-004 | RU-origin confidence | Blocked by unavailable/untested external RU probe. | Separate RU-origin probe report for POKROV and Telegram reachability. |
| P0-005 | Stable release label | Blocked by all above gates. | All P0 gates green and launch decision revised before deploy. |

## Implementation Scope For This Branch

This branch should implement the work that is safe without live secrets:

- documentation canon for Open Beta v4;
- design source-of-truth and generated-asset policy;
- release gate hardening and redaction;
- script compatibility wrapper for runtime app download smoke;
- Android audit package override/default;
- checkout sitemap coverage;
- launch, known-issue, support, and provider operation runbooks;
- client docs for Android/Windows beta limitations.

This branch must not fabricate:

- payment provider proof;
- Telegram init-data smoke evidence;
- Android physical-device audit evidence;
- RU-origin evidence;
- public download URLs;
- store approval or production signing state.
