import designTokensJson from "./design-tokens.json";

export type DesignTokens = typeof designTokensJson;

export const designTokens: DesignTokens = designTokensJson;

export function getDesignTokens(): DesignTokens {
  return designTokens;
}
