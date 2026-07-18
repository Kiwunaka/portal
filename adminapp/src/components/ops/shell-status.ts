import type { OpsStatusCode } from "@/lib/ops-status/types";

export interface OpsShellStatus {
  api: OpsStatusCode;
  session: OpsStatusCode;
  oldestRequiredSourceAt: string | null;
}

export const EMPTY_OPS_SHELL_STATUS: OpsShellStatus = {
  api: "missing",
  session: "missing",
  oldestRequiredSourceAt: null
};
