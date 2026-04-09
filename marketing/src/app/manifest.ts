import type { MetadataRoute } from "next";

import { CANONICAL_CLIENT_BRAND, CANONICAL_MARKETING_SITE_URL } from "../lib/pokrov";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: CANONICAL_CLIENT_BRAND,
    short_name: "POKROV VPN",
    description: "VPN-приложение для Android и Windows с 5-дневным бесплатным тестом.",
    start_url: "/",
    display: "standalone",
    background_color: "#f5f7f3",
    theme_color: "#0d4a35",
    lang: "ru-RU",
    categories: ["security", "utilities", "productivity"],
    icons: [
      {
        src: "/icon.png",
        sizes: "512x512",
        type: "image/png",
      },
      {
        src: "/apple-icon.png",
        sizes: "512x512",
        type: "image/png",
      },
    ],
    scope: "/",
    id: `${CANONICAL_MARKETING_SITE_URL}/`,
  };
}
