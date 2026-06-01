import type { MetadataRoute } from "next";

import { CANONICAL_MARKETING_SITE_URL } from "../lib/pokrov";

export default function robots(): MetadataRoute.Robots {
  const commonDisallow = ["/api/", "/_next/"];
  const aiAndSearchBots = [
    "GPTBot",
    "ChatGPT-User",
    "PerplexityBot",
    "ClaudeBot",
    "anthropic-ai",
    "Google-Extended",
    "Bingbot",
  ];

  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: commonDisallow,
      },
      ...aiAndSearchBots.map((userAgent) => ({
        userAgent,
        allow: "/",
        disallow: commonDisallow,
      })),
    ],
    sitemap: `${CANONICAL_MARKETING_SITE_URL}/sitemap.xml`,
    host: CANONICAL_MARKETING_SITE_URL,
  };
}
