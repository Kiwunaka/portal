# POKROV 1.1.5 Final User Product Audit — 2026-08-19

Status: `PASS` for the public current-origin journey and exact local client regression suite; production access reconciliation is `PASS`. Authenticated cabinet visuals, exact-final physical-device networking and Windows TUN egress remain separately labelled below.

## Candidate and evidence

- public stable release: `v1.1.5`, Android and Windows `1.1.5+28`
- public surface: `https://pokrov.space/`
- current-origin screenshots: `E:\POKROV-ops-evidence\2026-08-19-final-user-audit\`
- node-readiness evidence: `E:\POKROV-ops-evidence\2026-08-19-final-user-audit\predeploy-node-readiness.json`
- audit contains aggregates only; no Telegram IDs, emails, UUIDs, endpoint material or credentials are retained here

## Numbered user journey

1. **Главная.** The first mobile viewport explains the outcome, names Android and Windows, exposes the primary download action, and states five free days without a card plus the one-time 99-ruble first month. Trust and privacy claims are visible without requiring account creation.
2. **Установка.** `/install/` presents direct Android and Windows actions, GitHub Releases provenance and SHA-256 guidance. Apple remains a clearly separate manual-client path rather than disappearing from the product.
3. **Вход и кабинет.** The unauthenticated cabinet entry is compact and offers email and Telegram. The current in-app browser run did not reuse an authenticated owner session, so the signed-in cabinet layout is not claimed as visually proven by this audit.
4. **Оплата.** The checkout first layer presents 99 rubles for the first month, explains that subsequent months cost 239 rubles, states the one-time condition and no automatic charge, and keeps longer plans in the same compact decision surface.
5. **Помощь и инструкции.** `/support/` now opens the support task instead of falling through to the full homepage. `/guides/` exposes 46 searchable instructions by category. The POKROV atlas uses collapsed steps and real application screenshots with callouts rather than mock-only cards.
6. **Статус.** `/status/` reports the current service state and active incidents in plain language without exposing operator internals.

## What works well

- consistent compact visual hierarchy across acquisition, install, checkout, support and status;
- clear primary actions and platform-specific delivery;
- real client screenshots in the guide atlas;
- truthful first-party privacy wording and no claim that all analytics are absent;
- skip link, semantic headings, keyboard-focus styles, native buttons and disclosure controls, and touch targets sized for mobile use.

## Defects found and fixed in this pass

- `/support/` incorrectly rendered the homepage; it now resolves to the compact installation/support surface;
- footer copy incorrectly said the Telegram bonus required payment; it now matches the available-before-payment contract;
- the atlas counter used `22 экранов`; corrected to `22 экрана`;
- illustration alt text carried a stale release number; version-specific text was removed;
- the scheduled announcement summary initially read Telegram counts from the wrong layer of the guarded result; it now reports the persisted per-recipient totals and reason categories.

## Access and server readback

- retired free delivery: zero active free keys, mappings, enabled memberships and queued/running free jobs;
- effective accounts: 22 `PAID`, 8 `TRIAL`, 37 `PENDING`;
- all 30 entitled accounts are enabled on all seven paid nodes; all 37 pending accounts are disabled everywhere;
- paid-node coverage: zero missing or disallowed mappings;
- Brain readiness: API, bots, worker, Caddy, rulesets, subscription render and current static surfaces passed two consecutive checks;
- node readiness: seven of seven paid nodes passed current DNS, TCP, TLS, target-TLS and drift checks.

## Verification and limits

- shared Flutter client: `flutter analyze` passed; all 311 widget/unit tests passed; seed and docs contracts passed;
- marketing: lint, production build, SEO checks and the responsive route sweep passed;
- current-origin public journey: visually inspected at a mobile viewport and retained as screenshots;
- `MANUAL_OWNER_TEST`: authenticated cabinet visual state, exact-final Huawei WARP/per-app/Wi-Fi-LTE cycles, Windows native TUN/DNS egress, Telegram account journey and RU-origin probe were not reclassified as automated passes;
- `BLOCKED_BY_ACCESS`: the former free node is unreachable, so its node-local Xray/MTProto shutdown state is not freshly attested. It is disabled and absent from all consumer delivery mappings.

No unresolved product decision was required for this pass, so no owner-question sidecar was created.
