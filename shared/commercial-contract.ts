import commercialContractJson from "./commercial-contract.json";

export type CommercialContract = typeof commercialContractJson;
export type CommercialPlan = CommercialContract["plans"][number];
export type CommercialPlanProjection = {
  code?: string | null;
  amount_rub?: number | null;
  days?: number | null;
  duration_days?: number | null;
  device_limit?: number | null;
  is_active?: boolean | null;
  public_visibility?: string | null;
};

export const commercialContract: CommercialContract = commercialContractJson;
export const COMMERCIAL_REVISION = commercialContract.commercial_revision;
export const COMMERCIAL_CONTRACT_SHA256 = commercialContract.contract_sha256;

export function getCommercialContract(): CommercialContract {
  return commercialContract;
}

export function getCommercialPlan(code: string | null | undefined): CommercialPlan | null {
  const normalized = String(code || "").trim().toLowerCase();
  if (!normalized) return null;
  return commercialContract.plans.find((plan) => plan.code === normalized) || null;
}

export function commercialLaunchReady(): boolean {
  return commercialContract.legal.launch_ready;
}

export function assertCommercialPlanProjection(plans: readonly CommercialPlanProjection[]): void {
  const normalize = (plan: CommercialPlanProjection) => ({
    code: String(plan.code || "").trim().toLowerCase(),
    amount_rub: Number(plan.amount_rub || 0),
    duration_days: Number(plan.duration_days || plan.days || 0),
    device_limit: Number(plan.device_limit || 0),
  });
  const actual = plans
    .filter((plan) => plan.is_active !== false && plan.public_visibility !== "hidden")
    .map(normalize)
    .sort((left, right) => left.code.localeCompare(right.code));
  const expected = commercialContract.plans
    .filter((plan) => plan.is_active && plan.public_visibility !== "hidden")
    .map(normalize)
    .sort((left, right) => left.code.localeCompare(right.code));
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error("Commercial plan projection mismatch");
  }
}
