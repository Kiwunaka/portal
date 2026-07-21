import type { MetadataRoute } from "next";

import { CANONICAL_MARKETING_SITE_URL, CANONICAL_PLATFORM_BRAND } from "../lib/pokrov";

export const dynamic = "force-static";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: CANONICAL_PLATFORM_BRAND,
    short_name: "POKROV",
    description: "Приложение POKROV для Android и Windows с бесплатным стартом, кабинетом и поддержкой.",
    start_url: "/",
    display: "standalone",
    background_color: "#ffffff",
    theme_color: "#12805a",
    lang: "ru-RU",
    categories: ["security", "utilities", "productivity"],
    icons: [
      {
        src: "/apple-icon.png?v=20260722",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/pokrov-logo.svg?v=20260722",
        sizes: "any",
        type: "image/svg+xml",
        purpose: "any",
      },
      {
        src: "/pokrov-logo.svg?v=20260722",
        sizes: "any",
        type: "image/svg+xml",
      },
    ],
    scope: "/",
    id: `${CANONICAL_MARKETING_SITE_URL}/`,
  };
}
