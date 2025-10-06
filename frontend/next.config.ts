import type { NextConfig } from 'next';
const webpack = require('webpack');

const nextConfig = (): NextConfig => ({
  // web构建使用默认模式支持SSR
  skipTrailingSlashRedirect: true,
  images: {
    unoptimized: true
  },
  // 添加这一行以启用standalone输出
  output: 'standalone',
  webpack: (config) => {
    // 处理不同环境的文件后缀优先级
    const buildTarget = process.env.BUILD_TARGET || 'web';
    
    // 根据构建目标设置文件扩展名优先级
    if (buildTarget === 'electron') {
      config.resolve.extensions = [
        '.electron.ts',
        '.electron.tsx',
        '.ts',
        '.tsx',
        '.js',
        '.jsx',
        ...(config.resolve.extensions || [])
      ];
    } else {
      config.resolve.extensions = [
        '.web.ts',
        '.web.tsx',
        '.ts',
        '.tsx',
        '.js',
        '.jsx',
        ...(config.resolve.extensions || [])
      ];
    }
    
    // 当构建目标为web时，排除client目录
    if (buildTarget === 'web') {
      config.plugins.push(new webpack.IgnorePlugin({
        resourceRegExp: /^src\/client\//,
      }));
    }
    
    return config;
  },
});

export default nextConfig;
