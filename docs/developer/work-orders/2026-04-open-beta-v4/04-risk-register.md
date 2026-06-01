# Risk Register

Status: active  
Date: 2026-05-26

Current risk interpretation:

- The `2026-05-15` evidence pack authorizes outside-store public beta, not stable/store/trusted release claims.
- Risks below remain active where they could cause overclaiming, stale operator wording, or production/payment trust drift.

| ID | Risk | Severity | Label | Mitigation |
| --- | --- | --- | --- | --- |
| RISK-001 | Public checkout appears live beyond the Lava.top beta proof or is described as production-mature before refund/chargeback/reconciliation evidence exists. | P0 | beta accepted / production risk | Keep Lava.top-only beta wording and retain provider/reconciliation evidence before stronger claims. |
| RISK-002 | Android artifact is promoted as raw-audited or store-safe when the beta relies on owner attestation rather than retained raw physical-device evidence. | P0 | OPERATOR_ATTESTED risk | Keep Android wording to outside-store beta; require raw physical-device evidence before stronger claims. |
| RISK-003 | `1.0.0` label implies guarantees that current evidence does not support. | P0 | confirmed | Use Open Beta v4 / beta versioning until P0 evidence is green. |
| RISK-004 | Secrets leak into evidence while testing provider, Telegram, or SSH flows. | P0 | confirmed | Redact by default; store only hashes or last-four identifiers. |
| RISK-005 | Runtime app download gate cannot be reproduced after future env/runtime changes. | P0 | regression watch | Keep `runtime_app_download_smoke.py --redact` evidence tied to exact runtime links and init-data origin. |
| RISK-006 | Android audit checks a legacy package instead of the active shell package. | P0 | resolved with regression watch | Keep `ANDROID_AUDIT_PACKAGE=space.pokrov.pokrov_android_shell` explicit in handoffs and validate retained evidence. |
| RISK-007 | Launch copy claims open downloads while release handoff URLs are stale, blank, or not the exact beta artifacts. | P0 | beta accepted / regression watch | Keep install/download copy tied to `/api/client/apps`, GitHub Releases APK/EXE, and dated handoff evidence. |
| RISK-008 | Payment webhook replay or failure states mutate entitlement incorrectly in later provider changes or production flows. | P0 | beta accepted / production risk | Require state-machine tests and redacted provider proof before each stronger payment claim. |
| RISK-009 | RU-origin assumptions are inferred from `mini`, brain, or local checks. | P1 | SKIPPED_BY_OPERATOR risk | Label current-origin, brain-origin, and RU-origin separately; do not substitute one for another or claim RU readiness. |
| RISK-010 | Support answers drift during launch pressure. | P1 | confirmed | Add support macro pack and known-issues doc before announcement. |
| RISK-011 | Store/ASO materials lag behind technical beta. | P1 | confirmed | Keep store launch out of scope until metadata, screenshots, privacy answers, and approvals exist. |
