# Public Beta PRD

Status: draft

## Decision Bias

Release as Open Beta only when public truth, support, downloads, admin, monitoring, and platform availability are honest and verified.

## Beta Scope

- Brand: `POKROV`.
- Public version line: `0.10.0-open-beta.N`.
- Public platform scope: Android and Windows only when their gate labels are truthful.
- Apple platforms: readiness only.
- Payments: enabled only after active provider proof; otherwise checkout must show an unavailable state.
- Android: public download blocked until physical release-build audit passes.
- Windows: public artifact requires checksum, signing or explicit unsigned beta warning, and release handoff evidence.

## Beta Non-Goals

- No `1.0.0` claim while P0 gates are blocked.
- No public promise for iOS or macOS.
- No raw subscription-link-first commerce story.
- No public wording that uses `VPN` as a direct product description outside legacy or technical identifiers.
