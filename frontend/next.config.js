/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Allow external images
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'blocks.mvp-subha.me',
        pathname: '/assets/**',
      },
    ],
  },
  // Allow connection to local OCaml backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8080/api/:path*',
      },
      {
        source: '/ws',
        destination: 'http://localhost:8080/ws',
      },
    ];
  },
};

module.exports = nextConfig;
