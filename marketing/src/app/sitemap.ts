import type { MetadataRoute } from "next";

import { buildMarketingSitemap } from "../lib/marketing-site";

export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  return buildMarketingSitemap();
}
