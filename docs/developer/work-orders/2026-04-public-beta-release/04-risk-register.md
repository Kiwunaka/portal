# Risk Register

Status: draft

| ID | Severity | Risk | Public Beta Impact | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|
| RISK-001 | P0 | Payment fulfillment is not proven idempotent against live provider behavior. | Double or false access grants. | Keep checkout disabled or manual_review until verified. | W06 | open |
| RISK-002 | P0 | Android is claimed publicly before physical release audit. | Unsafe local-control surface exposure. | Block Android public downloads until audit/signing pass. | W07/W09 | open |
| RISK-003 | P0 | Admin modules are decorative or lack backend truth. | Operators cannot control incidents. | Require real API data or honest unavailable states. | W04 | open |
| RISK-004 | P0 | Support flow is fake or decorative. | Users cannot recover payment/access failures. | Verify `/api/tickets` lifecycle and fallback copy. | W03/W06 | open |
| RISK-005 | P1 | Windows unsigned artifact triggers SmartScreen. | Trust and support burden. | Explicit unsigned beta warning and checksum. | W07/W10 | open |
| RISK-006 | P1 | RU-origin probe unavailable. | RU-specific reachability remains unknown. | Mark `BLOCKED_BY_ACCESS` or degraded. | W08 | open |

