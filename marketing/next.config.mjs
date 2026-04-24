const exportDir = String(process.env.POKROV_MARKETING_EXPORT_DIR || "").trim();

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "export",
  trailingSlash: true,
  ...(exportDir ? { distDir: exportDir } : {})
};

export default nextConfig;
