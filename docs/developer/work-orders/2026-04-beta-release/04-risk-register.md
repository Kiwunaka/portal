# Risk Register

| Risk | Probability | Impact | Area | Trigger | Detection | Mitigation | Beta decision |
|---|---:|---:|---|---|---|---|---|
| Android physical localhost audit missing | 4 | 5 | client/security | Android beta/public handoff | `android_localhost_audit.py`; W10 `adb devices -l` showed no attached device | Internal APK only, public blocked | beta internal only; public blocked |
| Android signing missing | 4 | 4 | client/release | APK handoff | signing evidence | Internal beta label, no store claim | accepted only for gated beta |
| Windows code signing missing | 4 | 3 | client/release | Windows artifact handoff | signing evidence; post-W10 Windows build gate passes for unsigned beta artifact | SmartScreen warning, gated download only, public approved remains no | accepted only for gated beta after handoff; public blocked |
| Payment callback double processing | 3 | 5 | payments | duplicate webhook | payment tests/live controlled test | idempotency key and audit record | local regression passed in W10; live provider proof still blocker |
| Payment provider category or product rejected | 3 | 5 | payments/legal | provider review/live low-volume checkout | provider acceptance evidence | pick alternate provider or manual beta risk approval | blocker: unknown after W10 |
| Unknown provider event grants access | 3 | 5 | payments/backend | unexpected webhook status/type | provider adapter tests | route to `manual_review`, never silent success | blocker |
| Refunded/cancelled payment remains active | 3 | 4 | payments/support | refund/cancel event | payment ledger/admin review | queue manual reconciliation or apply entitlement policy | blocker if policy absent |
| Manual reconciliation unavailable | 3 | 4 | admin/support | webhook fails but payment confirmed | admin smoke | admin extend/revoke with audit note | blocker for paid beta |
| Telegram bonus double claim | 3 | 4 | bonuses | repeated claim | bonus tests | claim policy and audit | blocker if unverified |
| App-first duplicate identity | 3 | 5 | backend | install/login/redeem mismatch | app-first tests | unify account/session mapping | blocker if confirmed |
| Fresh install trial abuse | 3 | 3 | backend/abuse | repeated install_id creation | beta invite audit | invite gate, rate limits, manual monitoring | P1 unless uncontrolled |
| Raw config leakage | 3 | 5 | cabinet/client | user opens dashboard/downloads/support | UI audit/security smoke | hide raw links, safe summaries | blocker if visible |
| Activation key leaks through URL/logs | 3 | 4 | checkout/security | key appears in query string/referrer/log | code review/security smoke | use one-time code reveal, POST/session handoff, redaction | P0/P1 |
| Support upload URL exposes private attachment | 3 | 4 | support/privacy | attachment URL shared or indexed | security audit | authenticated retrieval, expiry, retention | blocker if confirmed |
| Admin displays subscription URL/token in screenshots | 3 | 4 | admin/privacy | admin support/evidence capture | visual/security audit | admin-only detail drawer, redacted evidence policy | P1/P0 if public |
| Admin auth bypass | 2 | 5 | admin/security | unauthenticated admin access | E2E/admin tests | auth gate and smoke | blocker |
| Admin module is decorative | 4 | 4 | admin/product | admin shows fake counters/actions | admin E2E/live read-only checks | real backend data, unavailable state, or exclude from beta gate | blocker |
| Metrics fake or stale | 3 | 4 | observability | admin node views | observer tests/live read-only check | W08 added freshness states; admin must render real/unavailable states | P1/P0 by surface |
| Node delivery mismatch | 3 | 5 | backend/client | managed profile fetch/connect | API/client gates | pool-rule tests | blocker if core path broken |
| Public copy returns to direct VPN wording | 3 | 4 | copy | public UI pass | copy guardrails | shared copy fixes | blocker if public |
| Payment copy/test drift masks entitlement failure | 2 | 4 | payments/QA | payment callback suite fails on plan description | `tests/test_api_payments_callbacks.py` | W06 reconciled copy and added entitlement-state tests; rerun full gate in W10 | mitigated; release-gate rerun required |
| Public copy promises production SLA or 24/7 support | 4 | 4 | marketing/support | marketing/legal/support page | copy guardrails/manual audit | beta copy pack, best-effort 24h wording | blocker |
| Hardcoded public reviews lack approval provenance | 3 | 3 | marketing/legal | review JSON-LD indexed | SEO/manual audit | remove or source from moderated feedback | P1/P0 by legal risk |
| Old app-next or bridge treated as truth | 2 | 4 | docs/release | work order uses archive as canon | research review | archive-only labels | P1 |
| Deploy not verified from live origin | 3 | 4 | ops | release decision | release gate evidence | W08 added classification; W10 collected current-origin public host checks only; brain/RU remain blocked | blocker for deploy and paid onboarding |
| Rollback path unknown | 3 | 5 | ops/release | deploy or migration fails | deploy checklist | W08 documented rollback checklist; W10 did not deploy and could not capture current deployed version/path | blocker until captured |
| Backup or migration rollback missing | 3 | 5 | data/ops | DB migration included | migration evidence | backup timestamp, local/staging test, no destructive migration without approval | blocker |
| RU routing marketed before leak/DNS checks | 3 | 4 | product/client | marketing/cabinet copy | copy/release review | keep limitation | blocker if claimed |
| Email continuation shown as live | 3 | 3 | webapp/copy | cabinet entry | copy guardrails | keep `soon` | P1 |
| Live evidence exposes personal/payment data | 3 | 5 | privacy/release | screenshots/logs in wave evidence | evidence audit | redact emails, Telegram IDs, payment IDs, private links, full identifiers | blocker if leaked |
| Dirty baseline overwritten | 2 | 4 | git/process | work agent edits pre-dirty file | baseline diff comparison | record before/after intent, orchestrator conflict route | P1 |
| Behind-origin push overwrites remote changes | 2 | 5 | git/promotion | push/deploy from dirty local branch | local/remote HEAD capture | no force-push, orchestrator merge/rebase/cherry-pick decision | blocker for promotion |
