# WO-010 Public Beta Release Captain

Status: draft
Agent: W10
Lane: mixed
Priority: P0

## Goal

Own final gate report, launch runbook, rollback checklist, deploy checklist, support checklist, communications pack, artifact status, public go/no-go, and post-launch monitoring.

## Write Scope

- `docs/developer/work-orders/2026-04-public-beta-release/**`
- `docs/audit-artifacts/public_beta_release_gate_report.md`
- `docs/product/portal-vpn-product.md`
- `docs/operations/deployment-and-access.md`
- `docs/operations/monitoring-and-visibility.md`
- `docs/operations/publishing-and-signing-guide.md`
- `C:/Users/kiwun/Documents/ai/POKROV-app/docs/**` when client scope/signoff changes

## Acceptance

- Full public beta gate report exists.
- All P0 gates are green, or decision is blocked/limited with exact reasons.
- Noncore failures are classified.
- Public communications are ready but scoped to evidence.
- Rollback path is documented.
- Support path is documented.
- Launch decision recorded.

## Validation

```powershell
python scripts/release_gate_check.py --output docs/audit-artifacts/public_beta_release_gate_report.md
```

Optional full client platform gates require physical Android audit serial:

```powershell
set ANDROID_AUDIT_SERIAL=<physical-device-serial>
python scripts/release_gate_check.py --client-platform-gates windows,android-apk,android-aab --output docs/audit-artifacts/public_beta_release_gate_report.md
```

