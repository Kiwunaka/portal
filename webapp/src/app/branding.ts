import {
  POKROV_LEGACY_THEME_STORAGE_KEYS,
  POKROV_THEME_STORAGE_KEY,
  pokrovBranding as sharedPokrovBranding,
} from "../../../shared/branding";

export { POKROV_LEGACY_THEME_STORAGE_KEYS, POKROV_THEME_STORAGE_KEY };

export const pokrovBranding = {
  ...sharedPokrovBranding,
  cabinetTagline: "Доступ, устройства, продление и помощь в одном кабинете.",
  entryEyebrow: "app.pokrov.space",
  supportTitle: "Поддержка POKROV",
  appFirstSummary: "Главный запуск живет в приложении POKROV, а кабинет помогает со входом, продлением, устройствами и поддержкой.",
} as const;

export type PokrovBranding = typeof pokrovBranding;
