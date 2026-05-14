import type { EmailAuthStatusResult } from "@/lib/api";

export function isEmailAuthPublicReady(payload?: EmailAuthStatusResult | null): boolean {
  return Boolean(
    payload?.enabled &&
      payload.public_enabled &&
      payload.delivery_configured &&
      payload.delivery_secret_configured &&
      !payload.debug_echo,
  );
}
