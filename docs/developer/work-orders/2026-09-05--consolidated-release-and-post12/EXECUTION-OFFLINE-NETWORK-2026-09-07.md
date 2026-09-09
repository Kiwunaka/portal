# Offline profile and automatic network diagnostics — 2026-09-07

Authority: [owner decisions](OWNER-DECISIONS-2026-09-07.md). Source: client
`98b425d` (offline cache), `550329f` (Android automatic network diagnostics);
platform implementation is the scoped diff/commit over `398b32f`; bound Core
`8dc57a8` is unchanged. This closes the missing implementation choices, not
all N02/N07/O03/V02 or release gates.

## Implemented

The encrypted client cache retains the latest downloaded and proven profiles,
bound to account/install/platform and current routing inputs. Offline validity
ends 24 hours after the original successful server download. Restarts, retries
and restaging do not renew it. A valid cache limits the fresh API attempt to
three seconds; transient failure permits cached connection. Explicit 401/403,
logout/revocation and binding changes do not grant fallback. A failed dataplane
alone does not delete the last usable record; repeated automatic failed-node
loops remain blocked. Every connection still requires current tunnel proof.

Android reports automatically on app open/connect/running/failure. A bounded
native HTTPS request uses a physical NOT_VPN network and the authenticated
device session. The receiving API supplies the IP. Carrier comes from Android's
default data subscription; no GPS/new permission is added. If this path fails,
the ordinary API can report carrier/network with unknown source IP. It never
substitutes the VPN exit. Source claims are diagnostic, not entitlement proof.

The platform reuses zero-risk AntiAbuseEvent rows, current identity checks,
sensitive-support RBAC and supervised retention. IP and coarse metadata last
at most 72 hours; existing HMAC windows remain seven/ninety days. User 360 shows
latest per-device observations and audits each sensitive read without logging
network values. L1 sees no values. API, monitoring, privacy copy and client
onboarding/storage/runtime owners are updated.

## Verification

- Client `flutter test` in app_shell: managed_profile_cache,
  cached_profile_fallback_gate, app_first_runtime_bootstrap, pokrov_seed_app:
  295 PASS. A separate stalled-HTTP deadline regression: 1 PASS.
- After automatic diagnostics: bootstrap/widget suite 287 PASS;
  `flutter analyze` PASS. Runtime-engine tests: 80 PASS, one pre-existing skip.
- Android `gradlew.bat :app:testDirectDebugUnitTest :app:testStoreDebugUnitTest`:
  PASS after the final carrier-selection change. Client `validate-seed.ps1`
  with explicit platform/Core worktrees: PASS.
- `python -B -m pytest -p no:cacheprovider` for antiabuse privacy, support work,
  client UI API, app-first API/service, auth/tickets, subscription preview and
  admin ops/payments: 239 PASS, one old expected-key assertion failed because
  the new retention counter was absent. Updated only that expectation;
  `tests/test_admin_ops_api.py::test_admin_v2_governance_roles_jit_audit_lineage_and_privacy`
  rerun: 1 PASS. Eight subtests also passed in the original regression.
- New authenticated network-context integration test: PASS. It exercises
  auth, throttle, rejection of client IP, server-derived IP, RBAC, audit,
  unavailable transport, read-time expiry and retained-row cleanup.
- Admin `npm.cmd run build`, `npm.cmd run lint`, `npm.cmd run test:e2e`:
  PASS / PASS / 80 PASS. After adding DB-IP attribution, build and
  `npm.cmd run test:e2e -- e2e/clients.spec.ts`: PASS / 10 PASS.
- Marketing build/SEO/responsive: PASS. Shared/copy/docs contracts: 59 PASS.
  Source-context audit and `git diff --check`: PASS.

[Retained receipt](evidence/offline-network-2026-09-07.json) binds local APKs,
source, screenshots and log hashes. Logs and APK rollback material remain in
`E:/r12-device-20260907` and the named `E:/r12-*.log` files; they contain no
exported profile, credentials or device identity.

## Physical Huawei scope

HUAWEI ADA-AL00U, Android 12 / API 31. Same-package same-signer update preserves
app data. Version 1.2.0+4053 is a local test build, not a published candidate.
Its ARM64 Flutter executable includes additional Core-only ABIs from the AAR;
therefore this is not the final primary-ARM64 packaging acceptance (D01).
The existing installed APK is retained for rollback. The normal API build
was restored after the fixture; installed SHA-256 matches. Final phone state:
Wi-Fi enabled, VPN disconnected, app data preserved.

Normal API build: Wi-Fi connection, force-stop/relaunch/reconnect, and mobile
connection each reached the app's confirmed tunnel/DNS/VPN-egress state.
An isolated build-time fixture sets the control-plane API to
`https://127.0.0.1:1`; no production configuration is changed. It connects using
the protected cached profile over the physical mobile network, also after
a further force-stop/relaunch. This is a
controlled API-outage test; it does not prove a specific carrier's allowlist,
RU-origin reachability, arbitrary IP blocks or the full D02 network matrix.

## Deployment and remaining gates

Automatic Android-to-deployed-API collection remains NOT_REQUESTED: the new
endpoint/admin code has not been deployed. Local tests do not establish live
carrier/geolocation accuracy. DB-IP City Lite September 2026 was downloaded
locally, published SHA-1/MD5 verified, and MMDB subdivision lookup exercised.
It is CC BY 4.0; the admin view includes DB-IP attribution. Before an authorized
deployment, place this database on the API host (suggested path
`/var/lib/pokrov-geoip/dbip-city-lite.mmdb`) and set
`CLIENT_NETWORK_GEOIP_CITY_DB_PATH`; preserve the current database/config as
rollback. No provider lookup receives customer IP.

Full Android Doze/handover/IPv6/MTU/UDP53/WARP matrix, Windows SCM/Win10,
exact candidate/privacy/licensing and named-origin acceptance remain open.
M01 seller/receipt and paid G04/G06 features are SKIPPED_BY_OWNER, never PASS.
No push, merge, public candidate, deployment, payment or provider mutation.
Rollback source changes through scoped commits; never erase retained evidence
or downgrade encrypted storage. Concurrent files remain untouched.
