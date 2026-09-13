import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Keep tracing inside this app even if a parent folder has another lockfile.
  outputFileTracingRoot: path.join(__dirname),
};

export default nextConfig;
