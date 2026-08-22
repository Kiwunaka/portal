# Observability And Support Access Review

Last updated: 2026-08-22

## Status And Scope

This is the operator playbook for reviewing access to release-health data,
support-bundle summaries and encrypted support-bundle objects. It covers the
production Operator Center role/session authority and the global legacy
support-bundle access audit exposed through Operator Center v2.

The playbook does not authorize a role change, bundle download, production
mutation or retention hold by itself. The assigned security owner must execute
each change through the stored Action Intent boundary and retain the resulting
audit lineage.

## Owners And Cadence

- Security owner: schedules the review, records the review ID and closes or
  escalates findings.
- Independent superadmin reviewer: approves standing-role changes and reviews
  any access by the security owner. A reviewer must not approve their own role.
- Support lead: confirms whether support-bundle access was tied to an active
  case and a permitted reason.
- Release captain: consumes the review outcome for release evidence but cannot
  relabel a missing review as a pass.

Required cadence:

- after every `jit` or `break_glass` grant: close the temporal access review no
  later than the next business day;
- weekly: inspect pending temporal reviews, expired roles, active sessions and
  support-bundle access since the previous review;
- monthly: reconcile all sensitive support-bundle access with case IDs, reason
  codes and download/hold audit rows;
- quarterly and before a release candidate: re-approve or revoke every standing
  role and confirm least privilege against the current role catalog;
- immediately after an incident, operator departure, suspected compromise or
  unexplained access: revoke affected sessions/roles and open a security
  incident before continuing the scheduled review.

## Operator Support Boundary

- L1 may read case timelines, allowlisted diagnostic facts, known-issue safe
  summaries and support-bundle status/TTL/audit aggregates. L1 must not receive
  a bundle-content control or `support.sensitive.read`.
- L2, SRE and Security may request ciphertext only after fresh step-up and one
  of `customer_case`, `incident_review`, `release_validation` or
  `security_review`. The grant stays in the request header, is actor/case/bundle
  scoped, expires and is single use.
- Search accepts case ID, opaque `bundle_…` ref or safe correlation code and
  returns only canonical ticket destinations. Raw upload IDs, object names,
  account/install/session identity and arbitrary event metadata are forbidden.
- Opening or downloading bundle content must produce audited actor, reason and
  UTC time. A scheduled review uses the audit projection; it does not download
  content merely to prove that access exists.

## Evidence Labels

Use exactly one outcome for each environment:

- `PASS`: the review ran against that environment, all findings were closed,
  and retained audit/evidence identifiers resolve.
- `OPEN_FINDINGS`: the review ran, but a role, session or access event still
  requires owner action.
- `BLOCKED_BY_ACCESS`: the reviewer could not authenticate or query the required
  production authority.
- `NOT_RUN`: no current review exists. A local test or older review is not a
  production pass.

Never put session tokens, CSRF values, access-grant tokens, token hashes,
Telegram IDs, bundle paths, object names or raw bundle content into retained
evidence. Use opaque operator/role/session/audit/intent IDs and aggregate counts.

## Review Procedure

1. Open Operator Center v2 in the exact environment and record the frontend
   build, API build, environment, UTC start time and reviewer identity as opaque
   audit IDs. Stop on a build/environment mismatch.
2. Read `/api/admin/v2/governance/roles` and
   `/api/admin/v2/governance/operators`. Confirm that every active role exists
   in the current catalog, belongs to an active operator, has the intended
   environment scope and has no expired `expires_at` value.
3. For every `pending_review` temporal role, reconcile grant reason, grantor,
   expiry, operator audit and command lineage. Close justified use with the
   `operator.access.review` Action Intent. Revoke unexplained or excessive
   access with `operator.role.revoke`; do not review it merely to clear the
   queue.
4. Inspect each operator detail. Revoke active sessions that are unexplained,
   stale for the local incident window, associated with a suspended operator or
   outside the expected environment. Session revocation uses
   `operator.session.revoke` through the Action Intent boundary.
5. Read `/api/admin/v2/governance/sensitive-access` for the review window.
   Reconcile every support-bundle grant, download and retention-hold action with
   one active case, permitted reason code, actor role and bounded TTL. The review
   must not download a bundle solely to prove access.
6. Read `/api/admin/v2/governance/audit` and the command-lineage endpoint for
   every change made during review. Confirm prepare/execute identity,
   idempotency, confirmation, result and resource binding. Export CSV only when
   the evidence owner requires it; the export is itself audited.
7. Read `/api/admin/v2/governance/privacy` and confirm the declared retention
   policy and diagnostic-bundle backlog have not drifted from the current data
   inventory. Retention backlog is a finding, not permission to delete data.
8. Record aggregate counts for active standing roles, active temporal roles,
   pending reviews, active sessions, sensitive-access rows, revoked roles,
   revoked sessions and open findings. Retain only opaque audit/intent IDs for
   changed resources.
9. A second reviewer checks the evidence, signs off the outcome and records the
   next due time. Release promotion remains blocked while the exact-candidate
   review is `NOT_RUN`, `BLOCKED_BY_ACCESS` or has open security findings.

## Fail-Closed Findings

Escalate and stop release promotion when any of these is observed:

- unknown role, permission or environment scope;
- active role for a suspended/unknown operator;
- expired temporal role still evaluated as active;
- temporal grant with no review, reason, grantor or bounded expiry;
- standing access with no current quarterly approval;
- unexplained active session or failed revocation;
- support-bundle access without an active case, allowed reason, actor binding,
  bounded TTL or audit row;
- reused access grant, non-null token material after use, bundle access by L1,
  or a download not linked to the reviewed case;
- missing/contradictory command lineage, environment mismatch or evidence from
  another candidate.

## Local Verification Boundary

The repository regression proves deny-by-default permissions, temporal grant
limits, pending review, review/revoke Action Intents, session revocation,
sensitive-access redaction and audited reads. It does not prove that the
production review ran on schedule. Until a current environment-specific review
is retained, report the operational result as `NOT_RUN` or
`BLOCKED_BY_ACCESS`, never `PASS`.
