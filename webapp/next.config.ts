import path from "node:path";
import type { NextConfig } from "next";

const BASE_PATH = "";

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  basePath: BASE_PATH || undefined,
  assetPrefix: BASE_PATH || undefined,
  turbopack: {
    root: path.join(__dirname),
  },
};

export default nextConfig;
