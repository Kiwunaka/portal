import type { MetadataRoute } from "next";

import { CANONICAL_MARKETING_SITE_URL } from "../lib/pokrov";

export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  const commonDisallow = ["/api/"];
  const aiAndSearchBots = [
    "OAI-SearchBot",
    "GPTBot",
    "ChatGPT-User",
    "Googlebot",
    "Bingbot",
    "PerplexityBot",
    "Perplexity-User",
    "ClaudeBot",
    "Claude-SearchBot",
    "Claude-User",
    "anthropic-ai",
    "Google-Extended",
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
