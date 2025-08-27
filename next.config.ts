import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  trailingSlash: true,
  basePath: '/final-man-standing',
  images: {
    unoptimized: true
  }
};

export default nextConfig;
