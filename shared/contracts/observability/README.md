# Operational observability contracts

This directory is the canonical owner for the POKROV operational event
envelope and stable error catalog. The contracts are secret-free and apply to
local runtime diagnostics, aggregate release health, user-initiated support
bundles and server security/audit events.

They do not replace Product Event Envelope V1. Product analytics may receive
only a separately reviewed, allowlisted aggregate projection. Individual
runtime events, correlation identifiers, support-case identifiers and bundle
contents are not product analytics input.

## Release binding

Release-handoff v2 requires two descriptors in `compatibility.contracts`:

- `observability-event` version `1.0.0`, whose SHA-256 is computed from
  `observability-event.schema.json`;
- `error-catalog` version `1.2.0`, whose SHA-256 is computed from
  `error-catalog.json`.

Both digests use UTF-8 text with CRLF and lone CR normalized to LF, so the
contract identity is stable across Windows and Linux checkouts.

- `SUPPORT-REFERENCE.md` is generated from that exact catalog and gives support
  the safe Russian message, owner, action and release-blocking flag for every
  current code. `generate_observability_support_reference.py --check` rejects
  stale documentation.
- `data-inventory.json` records the purpose, allowed modes, retention and owner
  inherited by every field in the event envelope and every persisted
  release-health, known-issue, encrypted-upload and privileged-access table.
  `validate_observability_data_inventory.py --check` compares the inventory to
  the JSON schema and live SQLAlchemy model columns and fails on any drift.
- `release-health-baseline.v1.schema.json` is the authenticated client read
  contract. It exposes only exact-build scope, an aligned UTC-week window and
  closed sample/failure-rate bands after at least ten unlinkable contributor
  buckets. A contributor is capped at 64 events per week; subminimum counts,
  bucket indexes and exact event/failure totals are never returned.

The active client generator derives both descriptors from these files. It does
not accept caller-supplied values for them. Client and Core keep hash snapshots
only for compatibility checks; these platform files remain the source of
truth.

## Privacy boundary

Event objects are closed. Arbitrary metadata is forbidden. The attributes map
contains only bounded, typed operational facts. Raw network targets, request
headers/bodies, profiles, local paths, account identifiers, credentials and
cryptographic material have no field in the contract.

The sole release-health attribute in 1.2.0 is
`attributes.selected_app_count` for the exact Android
`app.routing.selection.finished` event. It is an integer from `0` through
`128`. Package names, executable names, selected-app lists and other routing
identifiers remain device-local and are rejected by the remote ingest.

Client baseline contributions use a dedicated deployment secret to map one
authenticated account into a 12-bit bucket scoped to one exact build and one
UTC week. Only that bucket index and capped aggregate counters are persisted;
the account/install/device/session value and its hash are not. Collisions can
only reduce the observed cohort and delay projection availability. Missing or
invalid secret configuration leaves the projection unavailable.

Run `python -B scripts/validate_observability_contracts.py` after any schema or
catalog edit. A contract change also requires updating the client and Core hash
snapshots before a release candidate can validate.
