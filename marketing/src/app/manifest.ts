import type { MetadataRoute } from "next";

import { CANONICAL_MARKETING_SITE_URL, CANONICAL_PLATFORM_BRAND } from "../lib/pokrov";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: CANONICAL_PLATFORM_BRAND,
    short_name: "POKROV",
    description: "Умное ускорение интернета для Android и Windows с 5-дневным бесплатным тестом.",
    start_url: "/",
    display: "standalone",
    background_color: "#f5f1e8",
    theme_color: "#143627",
    lang: "ru-RU",
    categories: ["security", "utilities", "productivity"],
    icons: [
      {
        src: "/pokrov-logo.svg",
        sizes: "any",
        type: "image/svg+xml",
        purpose: "any",
      },
      {
        src: "/pokrov-logo.svg",
        sizes: "any",
        type: "image/svg+xml",
      },
    ],
    scope: "/",
    id: `${CANONICAL_MARKETING_SITE_URL}/`,
  };
}
