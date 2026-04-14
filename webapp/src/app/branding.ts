import {
  POKROV_LEGACY_THEME_STORAGE_KEYS,
  POKROV_THEME_STORAGE_KEY,
  pokrovBranding as sharedPokrovBranding,
} from "../../../shared/branding";

export { POKROV_LEGACY_THEME_STORAGE_KEYS, POKROV_THEME_STORAGE_KEY };

export const pokrovBranding = {
  ...sharedPokrovBranding,
  cabinetTagline: "Доступ, устройства и служба заботы в одном кабинете.",
  entryEyebrow: "app.pokrov.space",
  supportTitle: "Служба заботы",
  appFirstSummary: "Подключение продолжается через приложения POKROV, а кабинет помогает с доступом и поддержкой.",
} as const;

export type PokrovBranding = typeof pokrovBranding;
