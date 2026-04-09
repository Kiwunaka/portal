import path from "node:path";
import type { NextConfig } from "next";

const BASE_PATH = "";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["127.0.0.1", "localhost"],
  output: "export",
  trailingSlash: true,
  basePath: BASE_PATH || undefined,
  assetPrefix: BASE_PATH || undefined,
  experimental: {
    externalDir: true,
  },
  turbopack: {
    root: path.join(__dirname, ".."),
  },
};

export default nextConfig;
