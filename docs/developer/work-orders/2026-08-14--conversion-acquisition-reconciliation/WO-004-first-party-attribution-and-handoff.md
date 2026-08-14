# WO-004 — First-party Attribution And Install Handoff

Status: `IN_PROGRESS`

## Outcome

POKROV честно отвечает: откуда человек пришёл, куда дошёл, что сделал и где
остановился — без сторонних trackers и без выдуманной склейки устройств.

## Event And Privacy Contract

Capture bounded fields: `utm_source`, `utm_campaign`, `utm_content`, `ref`,
entry route, first touch, last touch, actual asset `download_click`, bot intent,
checkout start, provider-confirmed paid, app/account open, trial activation,
first confirmed connect, retry/error category and returning connect.

Never capture browsing history through VPN, destination domains, raw IP,
user-agent retention, message bodies, credentials, subscription material or
provider payloads. Campaign values are length/charset bounded; unknown values
are normalized, not echoed into logs/UI.

## Cross-device Handoff

- issue an opaque, random, short-lived acquisition handle separate from auth;
- store attribution server-side; token contains no PII and grants no access;
- bind once through an explicit post-install continue/deep-link or Telegram
  start/account-link action; replay and cross-account rebinding fail closed;
- Android direct APK and Windows direct EXE flows receive an actual post-install
  continuation path; absence of that user action remains `unknown`;
- TTL, one-time consumption and deletion/retention are tested and documented;
- never fingerprint a device or infer identity from IP/UA.

## Acceptance Scenarios

1. Site campaign → exact asset click → install continuation → account → first
   connect preserves first/last touch and campaign.
2. Telegram referral/campaign → bot → download → account preserves its start
   intent without treating ordinary bot users as site sessions.
3. Checkout/order records immutable source snapshot; signed callback cannot
   overwrite source or campaign.
4. Expired/replayed/tampered tokens do not link; product still works without
   attribution.
5. Admin can aggregate steps but cannot enumerate raw anonymous identifiers.

## Checks

Schema migration/rollback review, API unit/integration tests, expiry/replay
tests, marketing E2E, bot deep-link tests, client deep-link tests where changed,
privacy/source audit and retention job proof.

## Current Evidence

- `PASS_LOCAL`: bounded first/last touch, SHA-256 browser-session storage,
  `180-day` retention and `72-hour` one-time handoff are implemented with
  expiry/replay/cross-account tests.
- `PASS_LOCAL`: Android, Windows, Telegram, account and checkout handoffs bind
  exact server-side lineage; external orders and Telegram Stars attempts retain
  the acquisition-session foreign key.
- `PASS_LOCAL`: worker cleanup removes expired sessions/handoffs without
  deleting active lineage.
- `PENDING`: final marketing/bot E2E, migration rehearsal, full regression and
  post-deploy current-origin proof in WO-011.
