# WO-013CX — candidate.13 signing and LDPlayer lifecycle

## Outcome

Bind the Android lifecycle event-fence correction to a new immutable signed
candidate; prove AWG 3.1, AWG2 and ordinary Auto across consecutive
`VpnService` lifecycles without restarting the application process; retain
secret-free artifact and runtime evidence; and keep every physical, Windows,
origin and publication boundary explicit.

## Exact boundary

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.13`, immutable, internal only |
| Version | `1.2.0+4049` |
| Platform source | `7d983c0ab52e9c01f94da8916a6bca6a0039be8d` |
| Client source | `ce2581dd16d276d20eace7a56f0337c4b9319168` |
| Core source | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release-index source | `440f3be1a5f3ae5c6c78c62036858884e5bc3c94` |
| Receipt-recording release-index source | `289e887c7ba0463ecdf357bd5e7fd531ace9de8f` |
| Strict-v2 handoff | `32abc15c05e7b94f61047300e03b64b7c0e2834bb1d0feefcd2bf87c95fc2e9c` |
| Signed manifest | `b8a10cf8fbc1683cc9a1540edf74f29fd417f422bc3d2be97f4deae85075190c` |
| Detached signature | `ede7844c2b2a94b0d89b7aa72b75c5ff3eec5e5662ec907c0b181ff08d5c0e4d` |
| Signing receipt | `fc3b1319812df374c27e34c9698af8bcf9a67b66ada95bb4e1be1906d82bb295` |
| Runtime | exact x86_64 APK on LDPlayer Android 9, current origin |

The source seed deliberately remains `PRE_CANDIDATE_LOCAL` and is not
candidate authority. Candidate identity comes from the generated strict-v2
handoff and the separately signed public-index receipt. The signer produced
an `ACTIONS_ARTIFACT_ONLY` output with `promotion_authorized=false`.

## Candidate.12 rejection and source correction

Candidate.12 proved AWG 3.1 first, then exposed a deterministic warm-switch
defect when AWG2 started in the same application process. A new Core run began
its event sequence again, while the process-wide Android fence still compared
that sequence with the preceding run. Valid events from the new lifecycle were
rejected and the UI stayed transitional.

The successor correction resets the accepted sequence whenever the active
`runId` changes, including the case where a newly created `VpnService` reuses
the same local generation number. The fence continues to reject late callbacks
from the previous run. The focused JVM regression proves both halves, and the
exact client source passes the full local release gate, including Flutter,
Android direct/store, Windows and `162` Gradle tasks. Candidate.12 remains
immutable rejected history; no successful result is transferred into
candidate.13.

## Supply-chain result

All six build-4049 artifacts were rebuilt from the exact client source. Four
APK variants and the Store AAB use the production Android certificate and are
non-debuggable; the AAB also passes JAR integrity. The Windows setup is
intentionally `NotSigned` / `SKIPPED_BY_OWNER` under
`OWNER_ACCEPTED_UNSIGNED_WINDOWS_BETA_1_2_0`, direct beta only, with
SmartScreen and `Unknown publisher` expected.

The strict offline validators pass `6/6` release artifacts and `8/8` Windows
runtime-manifest files. CycloneDX 1.5 contains `349` components, provenance
binds six subjects, the hosted main-only Ed25519 signer passes, and a local
independent readback validates the exact manifest, signature and receipt. No
tag, GitHub Release, public asset, Store submission, stable pointer or runtime
handoff sync was created.

## Exact LDPlayer lifecycle result

The installed `base.apk` SHA-256 equals candidate.13 x86_64 artifact
`73c43e21dfc984c474941e14800c551f9545fe423b8f11458f6d41b8cb9af5ff`.
The exact sequence then passes without `force-stop` and without changing the
application process:

1. AWG 3.1 control-plane selection, runtime-profile match, tunnel, managed DNS
   and authenticated VPN egress are green.
2. A normal disconnect destroys the first VPN lifecycle. AWG2 then starts in
   the same process and independently passes the same profile and network
   checks.
3. Another normal disconnect returns to `default`; ordinary Auto stages a
   non-AWG profile with `33` VLESS outbounds and independently passes tunnel,
   managed DNS and authenticated VPN egress.

Two short exact-serial ADB reconnects occurred during VPN teardown polling.
Immediate readback recovered with the unchanged application process and the
requested disconnected state. This remains an emulator-environment
observation, not a hidden perfect run and not a client failure. The bounded
result is `PASS_EXACT_CANDIDATE_LDPLAYER_BOUNDED`.

Final cleanup is explicit: `default` is selected, the app is disconnected,
lab cohort/allowlist and AWG material are absent, and Android reports neither
an active VPN service nor a tunnel interface. The physical phone was not
addressed by any command and supplies no candidate.13 evidence.

## Gate and protocol decision

Gate F is not generated for candidate.13. The current verifier requires an
exact physical Android install binding to the candidate ARM64 artifact; that
binding does not exist. Weakening the verifier or transferring older physical
evidence would manufacture a result, so the honest status is
`NOT_RUN_MISSING_EXACT_ARM64_INSTALL_BINDING`.

Candidate.13 therefore reaches `I4` only for signed supply and the bounded
LDPlayer AWG lifecycle slice. Physical Android, clean Windows connected
TUN/DNS/recovery, current/Brain/RU origin refresh, provider payment E2E,
Operator OIDC/RBAC, legal/commercial approval, rollback and broader
performance remain non-PASS. Gate G is `NOT_AUTHORIZED`.

VLESS/Reality remains the stable baseline. AWG 3.1 remains the preferred
closed UDP lab transport and AWG2 its compatibility rollback. XHTTP is a
post-1.2.0 TLS/CDN reserve lane. Hysteria2 remains default-off and advances
only if a bounded post-release lab shows measurable value over the baseline;
neither protocol is required to call the current base transport functional.

Normalized secret-free evidence is retained at
`evidence/013CX-candidate13-signing-and-ldplayer-lifecycle/013CX-candidate13-signing-and-ldplayer-lifecycle.json`,
SHA-256 `050d7746b8ddc1a9826cf51508879c59bf59082ff57dbb377475424df0c23bbe`.
