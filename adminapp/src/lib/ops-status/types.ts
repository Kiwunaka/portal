export type OpsStatusCode =
  | "ok"
  | "degraded"
  | "failed"
  | "stale"
  | "unavailable"
  | "missing"
  | "BLOCKED_BY_ACCESS";

export type OpsStatusTone = "success" | "warning" | "danger" | "neutral";

export interface OpsStatusPresentation {
  readonly label: string;
  readonly tone: OpsStatusTone;
  readonly explanation: string;
}

export const OPS_STATUS_CODES = [
  "ok",
  "degraded",
  "failed",
  "stale",
  "unavailable",
  "missing",
  "BLOCKED_BY_ACCESS"
] as const satisfies readonly OpsStatusCode[];
