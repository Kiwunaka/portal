import catalog from "../copy/catalog.ru.json";

export type CatalogItem = {
  surface: string;
  ru: string;
  variables: string[];
  tone: string;
  allowed_public: boolean;
  compliance_notes: string;
  ab_variant: string;
};

type CatalogShape = {
  catalog_version: string;
  locale: string;
  items: Record<string, CatalogItem>;
};

const typedCatalog = catalog as CatalogShape;

export function getCatalogItem(key: string): CatalogItem | null {
  return typedCatalog.items[key] || null;
}

export function getCopyText(
  key: string,
  fallback = "",
  variables?: Record<string, string | number | null | undefined>,
): string {
  const item = getCatalogItem(key);
  const base = item?.ru || fallback;
  if (!variables || !base) return base;
  return base.replace(/\{([a-zA-Z0-9_]+)\}/g, (_match, name: string) => {
    const value = variables[name];
    return value == null ? "" : String(value);
  });
}

export function getCopyCatalogVersion(): string {
  return typedCatalog.catalog_version;
}
