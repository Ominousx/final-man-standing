import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    root: process.cwd()
  },
  output: 'standalone',
  experimental: {
    serverComponentsExternalPackages: []
  }
};

export default nextConfig;
