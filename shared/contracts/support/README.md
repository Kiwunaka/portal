# Support bundle signing contracts

This directory owns the platform-to-client contract for support recipient keys
and short-lived extended collection policy. It contains no key material.

The platform signs the canonical UTF-8 JSON payload bytes with Ed25519 and puts
the unpadded base64url payload and signature in `signed-envelope.schema.json`.
The decoded payload must validate against exactly one of:

- `support-key-set.schema.json`: one to eight X25519 recipient keys, valid for
  no more than 31 days from `issued_at`; every `not_after` is no later than the
  key-set expiry;
- `support-collection-policy.schema.json`: a v2 `extended` profile with exact
  platform/app/build audience, category and collector allowlists, nonce,
  per-bundle/cumulative byte ceilings and a one- or two-bundle limit, valid for
  no more than 30 minutes from `issued_at`.

Clients pin the Ed25519 signing public key independently, reject unknown
fields/versions/algorithms, verify signature before decoding or use, and reject
future, expired or overlong contracts. Support payloads are encrypted with
X25519, HKDF-SHA256 and AES-256-GCM before any export.

`support.mode.issue` is the only operator issuance action. It is prepared and
executed through the v2 support Action Intent boundary for one existing case;
the stored row contains only the activation-code hash. A normal authenticated
client redeems the one-time `PSM1-*` code at
`POST /api/client/support/mode/redeem`, bound to the same owner and exact
platform/app/build. Redemption signs the v2 policy and consumes the code.
Recovery scope is rejected.

The policy is collection authority only. It cannot carry commands, change VPN,
routes or DNS, read user files, capture packets or destinations, reveal tokens
or configuration, hide its indicator, or extend itself. The client must ask for
explicit confirmation, keep a persistent indicator, remember consumed nonces,
enforce cumulative limits and auto-disable at expiry. Preview, redaction and
encryption remain mandatory for every extended bundle.

The client-local `PSD1-*` diagnostic code is a separate bounded, expiring fact
summary with CRC protection. `GET /api/admin/v2/support/diagnostic-codes/{code}`
decodes only platform, route/connection class, app/build, issue/expiry date and
a 16-bit diagnostic hash prefix; it uploads no file and carries no account,
installation, device, destination or package identity.

These contracts do not prove a production recipient, signing/private-key
custody, rotation, host permissions, physical-device export, deployment or
successful real upload. Those remain exact-candidate operator/release evidence.
