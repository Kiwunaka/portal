import type { MetadataRoute } from "next";

import { CANONICAL_MARKETING_SITE_URL, CANONICAL_PLATFORM_BRAND, getDesignTokens } from "../lib/pokrov";

export default function manifest(): MetadataRoute.Manifest {
  const tokens = getDesignTokens();
  const { canvas, emerald_strong: emeraldStrong } = tokens.theme.palette;

  return {
    name: CANONICAL_PLATFORM_BRAND,
    short_name: "POKROV",
    description: "Приложение POKROV для Android и Windows с бесплатным стартом, понятным кабинетом и живой поддержкой.",
    start_url: "/",
    display: "standalone",
    background_color: canvas,
    theme_color: emeraldStrong,
    lang: "ru-RU",
    categories: ["security", "utilities", "productivity"],
    icons: [
      {
        src: "/redesign/brand/pokrov-app-icon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/redesign/brand/pokrov-app-icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/redesign/brand/pokrov-maskable-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
    scope: "/",
    id: `${CANONICAL_MARKETING_SITE_URL}/`,
  };
}
