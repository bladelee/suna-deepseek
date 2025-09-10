import type { NextConfig } from 'next';

const nextConfig = (): NextConfig => ({
  output: process.env.NEXT_OUTPUT === 'standalone' ? 'standalone' : 'export',
  // assetPrefix: process.env.NODE_ENV === 'production' ? './' : undefined,
  skipTrailingSlashRedirect: true,
  images: {
    unoptimized: true
  },
});

export default nextConfig;
