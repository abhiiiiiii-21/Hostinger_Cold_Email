import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: process.env.NODE_ENV === "development" 
          ? "http://127.0.0.1:8000/api/:path*" 
          : "http://16.171.196.203:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
