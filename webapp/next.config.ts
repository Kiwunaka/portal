import path from "node:path";
import type { NextConfig } from "next";

const BASE_PATH = "/webapp";

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  basePath: BASE_PATH,
  assetPrefix: BASE_PATH,
  turbopack: {
    root: path.join(__dirname),
  },
};

export default nextConfig;
