# POKROV Market-Ready CIS 1.0.0 Design

Date: 2026-07-10
Status: owner-approved execution design
Target: mass paid Android + Windows launch in 6-8 weeks

## Release Definition

- Build one immutable `1.0.0-rc.1` for 100 canary users.
- Require a seven-day soak with no open P0/P1 issue before stable promotion.
- Publish signed direct Android and Windows artifacts after store submissions;
  store moderation itself does not block direct release.
- North-star metric: an account with a successful first payment and a
  server-confirmed connection after payment.
- Minimum launch signal: `trial -> first paid >= 5%` after 200 trials.

## Foundation

- Introduce immutable `account_id` as the ownership root for identities,
  devices, sessions, payments, entitlements, referrals, tickets and notices.
- `tg_id` and `install_id` remain identifiers, never reusable credentials.
- Existing app/email/Telegram duplicates merge automatically. Preserve payment
  history, support history, maximum paid expiry and non-duplicated legitimate
  grants; ambiguous identity conflicts enter manual review.
- Device sessions use short access tokens and rotating server-revocable refresh
  tokens stored only in platform secure storage.
- Production cutover uses validated backfill plus a maximum 15-minute mutation
  freeze. Existing node credentials continue working during the control-plane
  migration.

## Identity And Recovery

- Email login uses a six-digit OTP valid for five minutes. Password login is a
  90-day compatibility path and is then removed.
- Recovery code format is `PKR-XXXX-XXXX-XXXX`, shown once after first connect,
  stored as versioned HMAC, consumed after use and replaced after fresh auth.
- A recovery exchange creates a 15-minute limited session that can register a
  new device, perform one audited reissue and revoke old sessions/devices.
- Reissue has two scopes: VPN credential rotation, or account lockdown that
  also revokes other sessions and devices.

## Entitlement Economy

- App/site/store and eligible bot users reserve a five-day premium trial for
  seven days. The clock starts from server-confirmed first connect.
- Telegram bot channel gate blocks only new-lead acquisition paths. Existing
  and former customers keep payment, renewal, recovery and support access.
- App/site-origin accounts can receive one `+5 day` Telegram grant. Bot-origin
  accounts do not receive it twice. Existing issued `+10 day` grants remain.
- Channel loss starts a 24-hour grace period, then reverses only unused channel
  grant time. Paid and free access are not revoked.
- Before first payment, trial + Telegram + friend referral grants cap at 15
  premium days.
- Referral: friend `+5` after server-confirmed first connect; referrer `+15`
  after first successful payment and a 72-hour antiabuse hold.
- Free tier: 5 GB per rolling 30 days, one device, ordinary free profile first,
  then an enforced 2 Mbps soft profile until cycle reset.

## Communications And Operations

- Persisted notices are the source for app inbox, cabinet and delivery history.
- Android uses FCM only to carry an opaque notice identifier, with first-party
  content fetch and polling fallback. Firebase analytics/ads are prohibited.
- Windows uses tray polling and native local toast; WNS is out of scope.
- Promo limit defaults to three per week with local quiet hours 22:00-09:00
  and a separate promo opt-out.
- One support ticket thread is shared by app, cabinet and Telegram entrypoints.
- Public content requires manual approval. Automatic lifecycle messages use
  approved templates. Master and per-surface kill switches are mandatory.

## Client And Trust

- Android package ID remains `space.pokrov.pokrov_android_shell`; migration
  from the debug-signed beta requires uninstall plus account recovery.
- Android `1.0.0` requires production signing, Play App Signing submission,
  Quick Settings tile, secure storage and exact-artifact physical proof.
- Windows requires signed direct MSIX/package, normal upgrade/uninstall and a
  matching Partner Center submission.
- WARP is stable scope. Failure must visibly fall back to baseline POKROV
  without claiming that WARP remains active.
- Version comes from the binary. Update metadata includes ABI and SHA-256.
  Critical updates block connect only after a 24-hour grace period.

## Privacy And Antiabuse

- Raw IP retention is at most 72 hours. Full-IP HMAC remains seven days;
  IPv4 `/24` and IPv6 `/64` HMAC prefixes remain 90 days.
- Trial uniqueness is account + device. IP and payment/referral/device clusters
  are risk signals, not automatic bans.
- Automation may warn, cool down, request review or force reissue. Only an
  operator applies an account hard lock.
- Never collect AD_ID, Android ID, IMEI, MAC, installed apps, DNS queries,
  visited URLs/SNI, traffic content or raw subscription URLs in analytics.

## Explicit Non-Goals For 1.0.0

- iOS, WNS, recurring billing, cash/crypto referral payouts.
- Full LLM autopost, autonomous public publishing and SEO auto-rewrites.
- Third-party subscription/QR import, custom DNS and ad-domain filtering.
