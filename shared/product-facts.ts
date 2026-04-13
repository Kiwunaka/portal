import productFactsJson from "./product-facts.json";

export type ProductFacts = typeof productFactsJson;

export const productFacts: ProductFacts = productFactsJson;

export function getProductFacts(): ProductFacts {
  return productFacts;
}
