import type { DashboardSnapshot, UserPayload } from "@/lib/api";
import { getAccessMatrix, getTariffPlan } from "./portal";

type AccessState =
  | "paid_unlimited"
  | "trial_premium"
  | "bonus_premium"
  | "free_monthly"
  | "free_soft_mode"
  | "expired_or_blocked";

type TrafficPolicy = NonNullable<DashboardSnapshot["traffic_policy"]>;

const ACCESS_MATRIX = getAccessMatrix();
const FREE_TIER = ACCESS_MATRIX.free_tier;

export function getAccessState(
  dash?: DashboardSnapshot | null,
  user?: UserPayload | null,
): AccessState | "" {
  return String(dash?.access_state || user?.access_state || "") as AccessState | "";
}

export function getTrafficPolicy(
  dash?: DashboardSnapshot | null,
  user?: UserPayload | null,
): TrafficPolicy | null {
  return (dash?.traffic_policy || user?.traffic_policy || null) as TrafficPolicy | null;
}

export function getTrafficLimitGb(
  dash?: DashboardSnapshot | null,
  user?: UserPayload | null,
): number | null {
  const direct = dash?.traffic_limit_gb ?? user?.traffic_limit_gb;
  if (direct != null) return Number(direct);
  const policy = getTrafficPolicy(dash, user);
  if (policy?.limit_gb != null) return Number(policy.limit_gb);
  const state = getAccessState(dash, user);
  if (state === "free_monthly" || state === "free_soft_mode") {
    return Number(FREE_TIER.traffic_limit_gb || 0);
  }
  return null;
}

export function getTrafficRemainingGb(
  dash?: DashboardSnapshot | null,
  user?: UserPayload | null,
): number | null {
  const direct = dash?.traffic_remaining_gb ?? user?.traffic_remaining_gb;
  if (direct != null) return Number(direct);
  const policy = getTrafficPolicy(dash, user);
  if (policy?.remaining_gb != null) return Number(policy.remaining_gb);
  return null;
}

export function getNextResetAt(
  dash?: DashboardSnapshot | null,
  user?: UserPayload | null,
): string | null {
  return (
    String(
      dash?.next_reset_at ||
        user?.next_reset_at ||
        dash?.free_next_reset_at ||
        user?.free_cycle?.next_reset_at ||
        "",
    ).trim() || null
  );
}

export function getDeviceLimit(
  dash?: DashboardSnapshot | null,
  user?: UserPayload | null,
): number {
  return Math.max(1, Number(dash?.device_limit || user?.limits?.device_limit || FREE_TIER.device_limit || 1));
}

export function isPaidUnlimitedState(state: string): boolean {
  return state === "paid_unlimited";
}

export function isTrialPremiumState(state: string): boolean {
  return state === "trial_premium" || state === "bonus_premium";
}

export function isFreeMonthlyState(state: string): boolean {
  return state === "free_monthly" || state === "free_soft_mode";
}

export function isSoftModeState(state: string): boolean {
  return state === "free_soft_mode";
}

export function resolveTrafficStatusText(
  dash?: DashboardSnapshot | null,
  user?: UserPayload | null,
): string {
  const state = getAccessState(dash, user);
  const limitGb = getTrafficLimitGb(dash, user);

  if (isPaidUnlimitedState(state) || isTrialPremiumState(state)) {
    return "Полный доступ без лимита трафика";
  }
  if (isSoftModeState(state) && limitGb != null) {
    return `Базовый режим: ${formatTrafficGb(limitGb)} уже использованы`;
  }
  if (limitGb != null) {
    return `${formatTrafficGb(limitGb)} в базовом режиме на ${Number(FREE_TIER.cycle_days || 30)} дней`;
  }
  return "По текущему режиму";
}

export function resolvePlanLabel(
  dash?: DashboardSnapshot | null,
  user?: UserPayload | null,
): string {
  const state = getAccessState(dash, user);
  const planCode = String(dash?.current_plan_code || user?.current_plan_code || dash?.sub_type || user?.sub_type || "").trim();
  const catalogLabel = getTariffPlan(planCode)?.label;

  if (state === "paid_unlimited") return catalogLabel || "Премиум";
  if (state === "trial_premium") return "Пробный премиум";
  if (state === "bonus_premium") return "Бонусный премиум";
  if (state === "free_monthly") return "Базовый режим";
  if (state === "free_soft_mode") return "Базовый режим";
  return catalogLabel || planCode || "—";
}

export function formatTrafficGb(value?: number | null): string {
  if (!Number.isFinite(Number(value))) return "0 ГБ";
  return `${Number(value || 0).toLocaleString("ru-RU", { maximumFractionDigits: 1 })} ГБ`;
}
