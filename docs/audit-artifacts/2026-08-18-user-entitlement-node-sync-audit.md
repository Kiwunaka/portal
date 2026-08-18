# User entitlement and node-sync audit — 2026-08-18

Status: `REMEDIATION_IN_PROGRESS`

Scope: production database projections and all seven enabled paid delivery
nodes. This artifact intentionally contains aggregate counts only; no Telegram
ids, account ids, UUIDs, panel emails, connection material, or credentials are
retained.

## Product invariant

The effective user-facing status vocabulary is exactly:

- `TRIAL`: an active, unexpired trial window;
- `PAID`: any other active, unexpired premium window, including admin grants,
  gifts, promos, bonuses, referral/channel rewards, compensation, and provider
  payments;
- `PENDING`: no current usable entitlement.

Historical `FREE` storage labels are migration/audit detail and are not a live
product tier. All `TRIAL` and `PAID` identities must be enabled on every enabled
paid node. `PENDING` identities must be disabled on every node.

## Pre-remediation production readback

Observed at `2026-08-18T13:59:54Z`:

| Check | Result |
|---|---:|
| Real non-manual user projections | 67 |
| Effective `TRIAL` | 9 |
| Effective `PAID` | 22 |
| Effective `PENDING` | 36 |
| Legacy raw `FREE` rows | 41 |
| Enabled paid delivery nodes | 7 |
| Active access keys | 31 |
| Inactive access keys | 7 |
| Revoked access keys | 35 |

Every paid node exposed 21 enabled `PAID` users although the desired set was
22. Exactly one effective `PAID` projection was absent from all seven nodes.
Between five and eight `PENDING` projections remained enabled per node, and
between five and eight enabled panel rows per node had no current database
projection. Database mapping coverage was complete for 30 entitled users,
incomplete for one, with seven missing node slots. Eight `PENDING` projections
still had paid-node mappings.

The mismatch was systemic rather than regional: the old reconciliation script
used raw `FREE` versus non-`FREE` labels, admin day grants did not run a
post-commit panel sync, and the expiry worker warned users without reliably
disabling expired panel clients.

## Remediation contract

- effective status is derived from active window plus plan/grant semantics;
- admin and broadcast surfaces display/filter `TRIAL`, `PAID`, and `PENDING`;
- positive admin extension normalizes the projection and synchronizes panels
  after commit;
- the expiry worker disables panel access first, then atomically marks the same
  unchanged expired projection inactive; partial panel failure stays retryable;
- guarded reconciliation defaults to dry-run and requires exact confirmation
  `RECONCILE_TRIAL_PAID_PENDING` for apply;
- reconciliation output is aggregate-only and never prints user identifiers;
- stale client notifications can be dismissed without deleting retained source
  history;
- Android and Windows production builds require one exact shared package
  version before packaging.

Post-deploy reconciliation and readback evidence will be appended after the
platform deployment. Client publication remains a separate exact-candidate gate.
