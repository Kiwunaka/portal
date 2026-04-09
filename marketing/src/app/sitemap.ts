import type { MetadataRoute } from "next";

import { buildMarketingSitemap } from "../lib/marketing-site";

export default function sitemap(): MetadataRoute.Sitemap {
  return buildMarketingSitemap();
}
