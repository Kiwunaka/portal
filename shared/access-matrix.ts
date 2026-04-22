import accessMatrixJson from "./access-matrix.json";

export type AccessMatrix = typeof accessMatrixJson;
export type AccessStateCode = keyof AccessMatrix["states"];

export const accessMatrix: AccessMatrix = accessMatrixJson;

export function getAccessMatrix(): AccessMatrix {
  return accessMatrix;
}

export function getAccessStateConfig(state: string | null | undefined) {
  const normalized = String(state || "").trim() as AccessStateCode;
  return accessMatrix.states[normalized] || null;
}
