import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://16.171.196.203:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
