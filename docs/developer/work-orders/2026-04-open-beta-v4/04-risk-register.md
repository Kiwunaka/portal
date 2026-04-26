# Risk Register

Status: active  
Date: 2026-04-26

| ID | Risk | Severity | Label | Mitigation |
| --- | --- | --- | --- | --- |
| RISK-001 | Public checkout appears live while provider proof is missing. | P0 | confirmed | Runtime guard or unavailable copy until provider proof is redacted and attached. |
| RISK-002 | Android artifact is promoted without physical localhost/control-surface audit. | P0 | confirmed | Keep Android gated until release-installed physical-device audit passes. |
| RISK-003 | `1.0.0` label implies guarantees that current evidence does not support. | P0 | confirmed | Use Open Beta v4 / beta versioning until P0 evidence is green. |
| RISK-004 | Secrets leak into evidence while testing provider, Telegram, or SSH flows. | P0 | confirmed | Redact by default; store only hashes or last-four identifiers. |
| RISK-005 | Runtime app download gate cannot be reproduced because the documented script name is missing. | P0 | confirmed | Add a compatibility wrapper and point release docs to the real redacting command. |
| RISK-006 | Android audit checks a legacy package instead of the active shell package. | P0 | confirmed | Add package override/default and require evidence to show target package. |
| RISK-007 | Launch copy claims open downloads while release handoff URLs are blank. | P0 | confirmed | Keep install/download copy gated and support-routed until handoff proof exists. |
| RISK-008 | Payment webhook replay or failure states mutate entitlement incorrectly. | P0 | confirmed | Require state-machine tests and redacted provider proof before enabling paid checkout. |
| RISK-009 | RU-origin assumptions are inferred from `mini` or local checks. | P1 | confirmed | Label current-origin, brain-origin, and RU-origin separately; do not substitute one for another. |
| RISK-010 | Support answers drift during launch pressure. | P1 | confirmed | Add support macro pack and known-issues doc before announcement. |
| RISK-011 | Store/ASO materials lag behind technical beta. | P1 | confirmed | Keep store launch out of scope until metadata, screenshots, privacy answers, and approvals exist. |
