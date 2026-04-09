import type { MetadataRoute } from "next";

import { CANONICAL_MARKETING_SITE_URL } from "../lib/pokrov";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/api/", "/_next/"],
      },
    ],
    sitemap: `${CANONICAL_MARKETING_SITE_URL}/sitemap.xml`,
    host: CANONICAL_MARKETING_SITE_URL,
  };
}
